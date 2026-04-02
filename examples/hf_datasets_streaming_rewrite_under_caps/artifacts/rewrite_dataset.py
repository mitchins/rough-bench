from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Iterator

from datasets import Dataset, load_from_disk


WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(tokens: list[str]) -> str:
    text = " ".join(token.strip() for token in tokens if token and token.strip())
    return WHITESPACE_RE.sub(" ", text).strip().casefold()


def choose_better(current: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    if float(candidate["score"]) > float(current["score"]):
        return candidate
    if float(candidate["score"]) < float(current["score"]):
        return current
    if int(candidate["updated_at"]) > int(current["updated_at"]):
        return candidate
    if int(candidate["updated_at"]) < int(current["updated_at"]):
        return current
    if str(candidate["example_id"]) < str(current["example_id"]):
        return candidate
    return current


def iter_validated_rows(input_dir: Path) -> Iterator[dict[str, Any]]:
    dataset = load_from_disk(str(input_dir))
    iterable = dataset.to_iterable_dataset()
    for row in iterable:
        tokens = list(row["tokens"])
        ner_tags = list(row["ner_tags"])
        if not tokens:
            continue
        if len(tokens) != len(ner_tags):
            continue

        normalized_text = normalize_text(tokens)
        if not normalized_text:
            continue

        yield {
            "example_id": str(row["example_id"]),
            "source": str(row["source"]),
            "tokens": tokens,
            "ner_tags": ner_tags,
            "score": float(row["score"]),
            "updated_at": int(row["updated_at"]),
            "text": " ".join(tokens),
            "normalized_text": normalized_text,
        }


def bucket_name(source: str, normalized_text: str, bucket_count: int) -> str:
    payload = f"{source}\t{normalized_text}".encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8).hexdigest()
    return f"bucket-{int(digest, 16) % bucket_count:04d}.jsonl"


def spill_input_rows(input_dir: Path, scratch_dir: Path, bucket_count: int) -> list[Path]:
    bucket_dir = scratch_dir / "buckets"
    bucket_dir.mkdir(parents=True, exist_ok=True)

    handles: dict[Path, Any] = {}
    try:
        for row in iter_validated_rows(input_dir):
            path = bucket_dir / bucket_name(
                row["source"], row["normalized_text"], bucket_count
            )
            handle = handles.get(path)
            if handle is None:
                handle = path.open("a", encoding="utf-8")
                handles[path] = handle
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    finally:
        for handle in handles.values():
            handle.close()

    return sorted(bucket_dir.glob("bucket-*.jsonl"))


def dedupe_bucket(path: Path, out_dir: Path) -> Path:
    best_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            dedupe_key = (row["source"], row["normalized_text"])
            existing = best_by_key.get(dedupe_key)
            if existing is None:
                best_by_key[dedupe_key] = row
            else:
                best_by_key[dedupe_key] = choose_better(existing, row)

    rows = sorted(
        best_by_key.values(),
        key=lambda row: (row["source"], row["updated_at"], row["example_id"]),
    )

    out_path = out_dir / f"{path.stem}.sorted.jsonl"
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            row.pop("normalized_text", None)
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    return out_path


def iter_sorted_rows(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


def merge_sorted_partitions(paths: list[Path]) -> Iterator[dict[str, Any]]:
    heap: list[tuple[tuple[str, int, str], int, dict[str, Any], Iterator[dict[str, Any]]]] = []
    for index, path in enumerate(paths):
        iterator = iter_sorted_rows(path)
        first = next(iterator, None)
        if first is None:
            continue
        key = (first["source"], int(first["updated_at"]), str(first["example_id"]))
        heapq.heappush(heap, (key, index, first, iterator))

    while heap:
        _, index, row, iterator = heapq.heappop(heap)
        yield row
        nxt = next(iterator, None)
        if nxt is None:
            continue
        key = (nxt["source"], int(nxt["updated_at"]), str(nxt["example_id"]))
        heapq.heappush(heap, (key, index, nxt, iterator))


def build_output_dataset(sorted_paths: list[Path]) -> Dataset:
    def generator() -> Iterator[dict[str, Any]]:
        yield from merge_sorted_partitions(sorted_paths)

    return Dataset.from_generator(generator)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--bucket-count", type=int, default=128)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with tempfile.TemporaryDirectory(prefix="roughbench-datasets-") as temp_dir:
        scratch_dir = Path(temp_dir)
        bucket_paths = spill_input_rows(args.input_dir, scratch_dir, args.bucket_count)

        sorted_dir = scratch_dir / "sorted"
        sorted_dir.mkdir(parents=True, exist_ok=True)
        sorted_paths = [dedupe_bucket(path, sorted_dir) for path in bucket_paths]

        output_dataset = build_output_dataset(sorted_paths)
        output_dataset.save_to_disk(str(args.output_dir))


if __name__ == "__main__":
    main()
