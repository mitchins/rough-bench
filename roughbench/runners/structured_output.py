from __future__ import annotations

import re
from pathlib import Path

from roughbench.runners.base import Artifact, TaskOutput
from roughbench.tasks.models import TaskDefinition


RESPONSE_LABELS = ("response.md", "response.txt", "answer.md", "answer.txt")
LABEL_LINE_PATTERN = re.compile(r"(?m)^\s*\*\*(?P<label>[^*\n]+)\*\*\s*$")
FENCED_BLOCK_PATTERN = re.compile(r"```(?:[A-Za-z0-9_+.-]+)?\n(.*?)\n```", re.S)


def build_task_output_from_text(
    task: TaskDefinition,
    source_dir: Path,
    answer_text: str,
    *,
    persist: bool,
) -> TaskOutput:
    if not task.expected_artifacts:
        if persist:
            source_dir.mkdir(parents=True, exist_ok=True)
            (source_dir / "response.md").write_text(answer_text + "\n", encoding="utf-8")
        return TaskOutput(task_id=task.id, source_dir=source_dir, answer_text=answer_text)

    sections = _extract_sections(answer_text, task.expected_artifacts)
    extracted_answer = _select_answer_text(sections, answer_text)
    artifacts = _build_artifacts(source_dir, sections, task.expected_artifacts, persist=persist)

    if persist:
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "response.md").write_text(extracted_answer + "\n", encoding="utf-8")

    return TaskOutput(
        task_id=task.id,
        source_dir=source_dir,
        answer_text=extracted_answer,
        artifacts=tuple(artifacts),
    )


def _extract_sections(answer_text: str, expected_artifacts: tuple[str, ...]) -> dict[str, str]:
    labels = RESPONSE_LABELS + expected_artifacts
    canonical_by_casefold = {label.casefold(): label for label in labels}
    sections: dict[str, str] = {}

    marker_matches = [
        (match.start(), match.end(), canonical_by_casefold[match.group("label").strip().casefold()])
        for match in LABEL_LINE_PATTERN.finditer(answer_text)
        if match.group("label").strip().casefold() in canonical_by_casefold
    ]

    for index, (_, marker_end, label) in enumerate(marker_matches):
        next_start = marker_matches[index + 1][0] if index + 1 < len(marker_matches) else len(answer_text)
        segment = answer_text[marker_end:next_start]
        body = _unwrap_segment(segment)
        if body and label not in sections:
            sections[label] = body

    for match in FENCED_BLOCK_PATTERN.finditer(answer_text):
        block = match.group(1).strip()
        if not block:
            continue
        lines = block.splitlines()
        first_line = lines[0].strip().lstrip("#").strip()
        canonical = canonical_by_casefold.get(first_line.casefold())
        if canonical and canonical not in sections:
            body = "\n".join(lines[1:]).strip()
            if body:
                sections[canonical] = body

    return sections


def _unwrap_segment(segment: str) -> str:
    text = segment.strip()
    if not text:
        return ""
    if text.startswith("---"):
        text = text[3:].lstrip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
            last_fence = text.rfind("\n```")
            if last_fence != -1:
                text = text[:last_fence]
    return text.strip()


def _select_answer_text(sections: dict[str, str], fallback: str) -> str:
    for label in RESPONSE_LABELS:
        content = sections.get(label)
        if content:
            return content.strip()
    return fallback.strip()


def _build_artifacts(
    source_dir: Path,
    sections: dict[str, str],
    expected_artifacts: tuple[str, ...],
    *,
    persist: bool,
) -> list[Artifact]:
    artifacts: list[Artifact] = []
    for relative_path in expected_artifacts:
        content = sections.get(relative_path, "").strip()
        if not content:
            continue
        artifact_path = source_dir / relative_path
        if persist:
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(content + "\n", encoding="utf-8")
        artifacts.append(Artifact(path=artifact_path, relative_path=relative_path, text=content))
    return artifacts
