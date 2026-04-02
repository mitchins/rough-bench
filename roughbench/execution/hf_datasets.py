from __future__ import annotations

import json
import random
import shutil
import subprocess
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from roughbench.execution.models import ExecutionResult
from roughbench.judging.scorecard import PenaltyHit, SignalHit, TaskScorecard
from roughbench.judging.evaluator import RuleBasedJudge
from roughbench.runners import collect_task_output
from roughbench.tasks import TaskDefinition


TASK_ID = "hf_datasets_streaming_rewrite_under_caps"

OUTPUT_FIELDS = (
    "example_id",
    "source",
    "tokens",
    "ner_tags",
    "score",
    "updated_at",
    "text",
)

SOURCE_NAMES = ("conll.train", "conll.dev", "conll.mirror")

FALLBACK_BASE_ROWS: tuple[dict[str, Any], ...] = (
    {
        "tokens": ["EU", "rejects", "German", "call", "to", "boycott", "British", "lamb", "."],
        "ner_tags": [3, 0, 7, 0, 0, 0, 7, 0, 0],
    },
    {
        "tokens": ["Peter", "Blackburn"],
        "ner_tags": [1, 2],
    },
    {
        "tokens": ["President", "Obama", "visited", "Berlin", "today", "."],
        "ner_tags": [0, 1, 0, 5, 0, 0],
    },
    {
        "tokens": ["Google", "opened", "a", "new", "office", "in", "London", "."],
        "ner_tags": [3, 0, 0, 0, 0, 0, 5, 0],
    },
    {
        "tokens": ["The", "U", ".", "N", ".", "Security", "Council", "met", "in", "New", "York", "."],
        "ner_tags": [0, 3, 0, 3, 0, 3, 4, 0, 0, 5, 6, 0],
    },
    {
        "tokens": ["Japan", "won", "the", "match", "against", "Brazil", "."],
        "ner_tags": [5, 0, 0, 0, 0, 5, 0],
    },
)


@dataclass(frozen=True)
class TierSpec:
    name: str
    label: str
    target_rows: int | None
    soft_time_seconds: float
    hard_penalty: int
    runtime_penalty: int
    memory: str | None = None


DEFAULT_TIER_SPECS: tuple[TierSpec, ...] = (
    TierSpec(
        name="visible_smoke",
        label="visible smoke",
        target_rows=None,
        soft_time_seconds=15.0,
        hard_penalty=20,
        runtime_penalty=4,
        memory=None,
    ),
    TierSpec(
        name="hidden_medium",
        label="hidden medium",
        target_rows=8000,
        soft_time_seconds=15.0,
        hard_penalty=12,
        runtime_penalty=4,
        memory="256m",
    ),
    TierSpec(
        name="hidden_large",
        label="hidden large",
        target_rows=40000,
        soft_time_seconds=20.0,
        hard_penalty=18,
        runtime_penalty=6,
        memory="160m",
    ),
)


def prepare_hf_datasets_sandbox(
    task: TaskDefinition,
    run_dir: Path | str,
    *,
    force: bool = False,
    visible_rows: int = 192,
) -> dict[str, str]:
    _ensure_supported_task(task)

    run_dir = Path(run_dir)
    sandbox_dir = run_dir / "sandbox"
    visible_input_dir = sandbox_dir / "visible_input"
    submission_dir = sandbox_dir / "submission" / task.id

    if run_dir.exists():
        has_content = any(run_dir.iterdir())
        if has_content and not force:
            raise ValueError(f"{run_dir} already exists. Use --force to replace it.")
        if has_content and force:
            shutil.rmtree(run_dir)

    submission_dir.mkdir(parents=True, exist_ok=True)

    (sandbox_dir / "prompt.txt").write_text(task.prompt.strip() + "\n", encoding="utf-8")
    (submission_dir / "README.md").write_text(
        textwrap.dedent(
            f"""\
            Submission folder for `{task.id}`.

            Required deliverables:
            - `rewrite_dataset.py`
            - `README.md`

            RoughBench will ignore host-side smoke tests for scoring. Only the Docker
            execution result counts.
            """
        ),
        encoding="utf-8",
    )

    fixture_metadata = _build_visible_fixture(visible_input_dir, visible_rows=visible_rows)
    (sandbox_dir / "README.md").write_text(
        textwrap.dedent(
            f"""\
            RoughBench sandbox for `{task.id}`.

            Layout:
            - `prompt.txt`: task prompt
            - `visible_input/`: local Hugging Face dataset saved with `save_to_disk`
            - `submission/{task.id}/`: put your final deliverables here

            Visible fixture:
            - source: {fixture_metadata["source_name"]}
            - rows: {fixture_metadata["row_count"]}

            Hidden evaluation will run the frozen submission in Docker with memory and
            runtime caps. Host-side runs here are only for development.
            """
        ),
        encoding="utf-8",
    )
    (sandbox_dir / "visible_fixture.json").write_text(
        json.dumps(fixture_metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "run_dir": str(run_dir),
        "sandbox_dir": str(sandbox_dir),
        "visible_input_dir": str(visible_input_dir),
        "submission_dir": str(submission_dir),
    }


def evaluate_hf_datasets_submission(
    task: TaskDefinition,
    submission_dir: Path | str,
    input_dir: Path | str,
    work_dir: Path | str,
    *,
    image: str,
    memory: str,
    cpus: str,
    timeout_seconds: int,
    soft_time_seconds: float,
    rebuild_image: bool = False,
    no_build: bool = False,
    include_hidden: bool = True,
) -> tuple[TaskScorecard, ExecutionResult]:
    _ensure_supported_task(task)

    submission_dir = Path(submission_dir).resolve()
    input_dir = Path(input_dir).resolve()
    work_dir = Path(work_dir).resolve()

    frozen_dir = work_dir / "frozen_submission"
    outputs_dir = work_dir / "outputs"
    scratch_root = work_dir / "scratch"
    logs_dir = work_dir / "logs"
    generated_inputs_dir = work_dir / "generated_inputs"

    if work_dir.exists():
        shutil.rmtree(work_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    scratch_root.mkdir(parents=True, exist_ok=True)
    generated_inputs_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(submission_dir, frozen_dir)

    build_log = logs_dir / "docker-build.log"
    image_built = _ensure_docker_image(
        image=image,
        rebuild_image=rebuild_image,
        no_build=no_build,
        build_log=build_log,
    )

    tiers = _prepare_tiers(
        input_dir=input_dir,
        generated_inputs_dir=generated_inputs_dir,
        include_hidden=include_hidden,
        visible_soft_time_seconds=soft_time_seconds,
    )

    penalties: list[PenaltyHit] = []
    signals: list[SignalHit] = []
    tier_results: list[dict[str, Any]] = []
    summary_bits: list[str] = []
    representative_command: tuple[str, ...] = ()
    representative_stdout_log = logs_dir / "visible_smoke" / "stdout.log"
    representative_stderr_log = logs_dir / "visible_smoke" / "stderr.log"

    overall_timed_out = False
    overall_verified = True
    last_exit_code: int | None = 0
    max_wall_time_seconds = 0.0

    for tier in tiers:
        tier_result = _run_tier(
            tier=tier,
            visible_input_dir=input_dir,
            submission_dir=frozen_dir,
            outputs_dir=outputs_dir,
            scratch_root=scratch_root,
            logs_dir=logs_dir,
            image=image,
            memory=memory,
            cpus=cpus,
            timeout_seconds=timeout_seconds,
        )
        tier_results.append(tier_result["details"])
        representative_command = tier_result["command"]
        if tier.name == "visible_smoke":
            representative_stdout_log = tier_result["stdout_log"]
            representative_stderr_log = tier_result["stderr_log"]

        penalties.extend(tier_result["penalties"])
        signals.extend(tier_result["signals"])
        summary_bits.append(tier_result["summary_bit"])

        overall_timed_out = overall_timed_out or tier_result["timed_out"]
        overall_verified = overall_verified and tier_result["verified"]
        last_exit_code = tier_result["exit_code"]
        if tier_result["wall_time_seconds"] is not None:
            max_wall_time_seconds = max(max_wall_time_seconds, tier_result["wall_time_seconds"])

    status = "passed" if not penalties else "failed"
    summary = _build_execution_summary(summary_bits=summary_bits, logs_dir=logs_dir)

    execution_result = ExecutionResult(
        task_id=task.id,
        status=status,
        summary=summary,
        image=image,
        command=representative_command,
        memory=memory,
        cpus=cpus,
        timeout_seconds=timeout_seconds,
        soft_time_seconds=soft_time_seconds,
        wall_time_seconds=max_wall_time_seconds if tier_results else None,
        exit_code=last_exit_code,
        timed_out=overall_timed_out,
        output_verified=overall_verified,
        frozen_submission_dir=frozen_dir,
        output_dir=outputs_dir,
        scratch_dir=scratch_root,
        logs_dir=logs_dir,
        stdout_log=representative_stdout_log,
        stderr_log=representative_stderr_log,
        build_log=build_log if image_built else None,
        image_built=image_built,
        triggered_penalties=tuple(penalties),
        passed_signals=tuple(signals),
        details={"tiers": tier_results},
    )

    static_output = collect_task_output(task.id, frozen_dir)
    static_scorecard = RuleBasedJudge().evaluate(task, static_output)
    combined_scorecard = _combine_static_and_execution(task, static_scorecard, execution_result)
    return combined_scorecard, execution_result


def _ensure_supported_task(task: TaskDefinition) -> None:
    if task.id != TASK_ID:
        raise ValueError(
            f"Docker execution is currently implemented only for {TASK_ID}, not {task.id}."
        )


def _require_datasets() -> tuple[Any, Any, Any]:
    try:
        from datasets import Dataset, load_dataset, load_from_disk
    except ImportError as exc:
        raise RuntimeError(
            "The execution harness requires the `datasets` package. Install it with `pip install -e .`."
        ) from exc
    return Dataset, load_dataset, load_from_disk


def _build_visible_fixture(output_dir: Path, *, visible_rows: int) -> dict[str, Any]:
    Dataset, load_dataset, _ = _require_datasets()
    try:
        from datasets import disable_progress_bars

        disable_progress_bars()
    except Exception:
        pass
    rows, source_name = _load_base_rows(load_dataset)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    dataset = _dataset_from_fixture_rows(
        load_dataset=load_dataset,
        temp_parent=output_dir.parent,
        base_rows=rows,
        target_rows=visible_rows,
        seed=7,
        heavy_mode=False,
    )
    dataset.save_to_disk(str(output_dir))

    return {
        "source_name": source_name,
        "row_count": visible_rows,
    }


def _load_base_rows(load_dataset: Any) -> tuple[list[dict[str, Any]], str]:
    try:
        dataset = load_dataset("conll2003", split="train[:24]")
        rows: list[dict[str, Any]] = []
        for row in dataset:
            rows.append(
                {
                    "tokens": list(row["tokens"]),
                    "ner_tags": [int(value) for value in row["ner_tags"]],
                }
            )
        if rows:
            return rows, "conll2003"
    except Exception:
        pass

    return [dict(row) for row in FALLBACK_BASE_ROWS], "fallback_conll_like"


def _build_generated_fixture(
    output_dir: Path,
    *,
    target_rows: int,
    seed: int,
) -> dict[str, Any]:
    Dataset, load_dataset, _ = _require_datasets()
    try:
        from datasets import disable_progress_bars

        disable_progress_bars()
    except Exception:
        pass
    rows, source_name = _load_base_rows(load_dataset)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    dataset = _dataset_from_fixture_rows(
        load_dataset=load_dataset,
        temp_parent=output_dir.parent,
        base_rows=rows,
        target_rows=target_rows,
        seed=seed,
        heavy_mode=True,
    )
    dataset.save_to_disk(str(output_dir))
    return {"source_name": source_name, "row_count": target_rows}


def _dataset_from_fixture_rows(
    *,
    load_dataset: Any,
    temp_parent: Path,
    base_rows: list[dict[str, Any]],
    target_rows: int,
    seed: int,
    heavy_mode: bool,
) -> Any:
    temp_jsonl = temp_parent / f".fixture-{seed}-{target_rows}.jsonl"
    if temp_jsonl.exists():
        temp_jsonl.unlink()
    with temp_jsonl.open("w", encoding="utf-8") as handle:
        for row in _fixture_generator(
            base_rows,
            target_rows=target_rows,
            seed=seed,
            heavy_mode=heavy_mode,
        ):
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    try:
        return load_dataset("json", data_files=str(temp_jsonl), split="train")
    finally:
        temp_jsonl.unlink(missing_ok=True)


def _prepare_tiers(
    *,
    input_dir: Path,
    generated_inputs_dir: Path,
    include_hidden: bool,
    visible_soft_time_seconds: float,
) -> list[TierSpec]:
    tiers: list[TierSpec] = [
        TierSpec(
            name="visible_smoke",
            label="visible smoke",
            target_rows=None,
            soft_time_seconds=visible_soft_time_seconds,
            hard_penalty=20,
            runtime_penalty=4,
        )
    ]
    if include_hidden:
        tiers.extend(DEFAULT_TIER_SPECS[1:])

    for tier in tiers:
        if tier.target_rows is None:
            continue
        tier_dir = generated_inputs_dir / tier.name
        _build_generated_fixture(
            tier_dir,
            target_rows=tier.target_rows,
            seed=100 + tier.target_rows,
        )
    return tiers


def _fixture_generator(
    base_rows: list[dict[str, Any]],
    *,
    target_rows: int,
    seed: int,
    heavy_mode: bool,
) -> Iterator[dict[str, Any]]:
    rng = random.Random(seed)
    serial = 0
    cycle = 0

    def make_row(
        prefix: str,
        *,
        source: str,
        tokens: list[str],
        ner_tags: list[int],
        score: float,
        updated_at_base: int,
    ) -> dict[str, Any] | None:
        nonlocal serial
        if serial >= target_rows:
            return None
        row = {
            "example_id": f"{prefix}-{serial:07d}",
            "source": source,
            "tokens": tokens,
            "ner_tags": ner_tags,
            "score": round(score, 3),
            "updated_at": updated_at_base + serial,
        }
        serial += 1
        return row

    while serial < target_rows:
        for base_index, base in enumerate(base_rows):
            if serial >= target_rows:
                break
            source = SOURCE_NAMES[(cycle + base_index) % len(SOURCE_NAMES)]
            tokens = list(base["tokens"])
            ner_tags = list(base["ner_tags"])
            dup_suffix = [f"group{cycle:06d}", f"b{base_index:02d}"]
            dup_tags = ner_tags + [0] * len(dup_suffix)

            lower_variant = [token.lower() if token.isalpha() else token for token in tokens]
            row = make_row(
                "lo",
                source=source,
                tokens=lower_variant + dup_suffix,
                ner_tags=dup_tags,
                score=0.2 + (base_index % 5) * 0.1,
                updated_at_base=1000,
            )
            if row is not None:
                yield row
            row = make_row(
                "hi",
                source=source,
                tokens=list(tokens) + dup_suffix,
                ner_tags=dup_tags,
                score=0.75 + (base_index % 3) * 0.05,
                updated_at_base=2000,
            )
            if row is not None:
                yield row
            row = make_row(
                "zz",
                source=source,
                tokens=list(tokens) + dup_suffix,
                ner_tags=dup_tags,
                score=0.75 + (base_index % 3) * 0.05,
                updated_at_base=2000,
            )
            if row is not None:
                yield row

            unique_repeats = 3 if heavy_mode else 1
            for unique_index in range(unique_repeats):
                if serial >= target_rows:
                    break
                unique_source = (
                    f"{source}.u{cycle % 17}"
                    if heavy_mode
                    else f"{source}.unique"
                )
                extra = [
                    f"uniq{cycle:06d}",
                    f"slot{unique_index}",
                    "x" * ((cycle + unique_index) % 9 + 1),
                ]
                if heavy_mode:
                    extra.extend([f"tail{base_index}", f"m{cycle % 31}"])
                row = make_row(
                    "uniq",
                    source=unique_source,
                    tokens=tokens + extra,
                    ner_tags=ner_tags + [0] * len(extra),
                    score=0.35 + rng.random() * 0.6,
                    updated_at_base=3000,
                )
                if row is not None:
                    yield row

            if serial >= target_rows:
                break

            if cycle % (11 if heavy_mode else 5) == 0:
                row = make_row(
                    "bad-empty",
                    source=source,
                    tokens=[],
                    ner_tags=[],
                    score=0.0,
                    updated_at_base=4000,
                )
                if row is not None:
                    yield row
            if serial >= target_rows:
                break

            if cycle % (7 if heavy_mode else 3) == 0:
                row = make_row(
                    "bad-mismatch",
                    source=source,
                    tokens=tokens,
                    ner_tags=ner_tags[:-1] if len(ner_tags) > 1 else [],
                    score=0.1,
                    updated_at_base=5000,
                )
                if row is not None:
                    yield row
        cycle += 1


def _ensure_docker_image(
    *,
    image: str,
    rebuild_image: bool,
    no_build: bool,
    build_log: Path,
) -> bool:
    docker_bin = shutil.which("docker")
    if docker_bin is None:
        raise RuntimeError("Docker is not installed or not on PATH.")

    inspect = subprocess.run(
        [docker_bin, "image", "inspect", image],
        check=False,
        capture_output=True,
        text=True,
    )
    image_exists = inspect.returncode == 0
    if image_exists and not rebuild_image:
        return False
    if no_build and not image_exists:
        raise RuntimeError(f"Docker image {image} does not exist and --no-build was set.")

    dockerfile = Path(__file__).resolve().parents[2] / "docker" / "hf_datasets_runner.Dockerfile"
    context_dir = Path(__file__).resolve().parents[2]
    build_cmd = [
        docker_bin,
        "build",
        "-t",
        image,
        "-f",
        str(dockerfile),
        str(context_dir),
    ]
    proc = subprocess.run(build_cmd, check=False, capture_output=True, text=True)
    build_log.write_text(
        f"$ {' '.join(build_cmd)}\n\nSTDOUT\n{proc.stdout}\n\nSTDERR\n{proc.stderr}",
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed to build Docker image {image}. See {build_log} for details."
        )
    return True


def _run_tier(
    *,
    tier: TierSpec,
    visible_input_dir: Path,
    submission_dir: Path,
    outputs_dir: Path,
    scratch_root: Path,
    logs_dir: Path,
    image: str,
    memory: str,
    cpus: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    input_dir = (
        logs_dir.parent / "generated_inputs" / tier.name
        if tier.target_rows is not None
        else visible_input_dir
    )

    tier_output_dir = outputs_dir / tier.name
    tier_scratch_dir = scratch_root / tier.name
    tier_logs_dir = logs_dir / tier.name
    tier_logs_dir.mkdir(parents=True, exist_ok=True)
    tier_output_dir.mkdir(parents=True, exist_ok=True)
    tier_scratch_dir.mkdir(parents=True, exist_ok=True)

    stdout_log = tier_logs_dir / "stdout.log"
    stderr_log = tier_logs_dir / "stderr.log"
    primary_command = _docker_command(
        image=image,
        submission_dir=submission_dir,
        input_dir=input_dir,
        output_dir=tier_output_dir,
        scratch_dir=tier_scratch_dir,
        memory=tier.memory or memory,
        cpus=cpus,
        use_flag_args=False,
    )
    timed_out = False
    exit_code: int | None = None
    wall_time_seconds: float | None = None
    invocation_mode = "positional"
    command = primary_command
    run_result = _run_docker_command(command=primary_command, timeout_seconds=timeout_seconds)
    if (
        not run_result["timed_out"]
        and run_result["exit_code"] == 2
        and _looks_like_cli_argument_mismatch(run_result["stderr"])
    ):
        invocation_mode = "flag_fallback"
        tier_output_dir = outputs_dir / f"{tier.name}-flag-fallback"
        tier_scratch_dir = scratch_root / f"{tier.name}-flag-fallback"
        shutil.rmtree(tier_output_dir, ignore_errors=True)
        shutil.rmtree(tier_scratch_dir, ignore_errors=True)
        tier_output_dir.mkdir(parents=True, exist_ok=True)
        tier_scratch_dir.mkdir(parents=True, exist_ok=True)
        command = _docker_command(
            image=image,
            submission_dir=submission_dir,
            input_dir=input_dir,
            output_dir=tier_output_dir,
            scratch_dir=tier_scratch_dir,
            memory=tier.memory or memory,
            cpus=cpus,
            use_flag_args=True,
        )
        fallback_result = _run_docker_command(command=command, timeout_seconds=timeout_seconds)
        stdout_log.write_text(
            _combine_attempt_logs(
                primary_command,
                run_result["stdout"],
                command,
                fallback_result["stdout"],
            ),
            encoding="utf-8",
        )
        stderr_log.write_text(
            _combine_attempt_logs(
                primary_command,
                run_result["stderr"],
                command,
                fallback_result["stderr"],
            ),
            encoding="utf-8",
        )
        run_result = fallback_result
    else:
        stdout_log.write_text(run_result["stdout"], encoding="utf-8")
        stderr_log.write_text(run_result["stderr"], encoding="utf-8")

    timed_out = run_result["timed_out"]
    wall_time_seconds = run_result["wall_time_seconds"]
    exit_code = run_result["exit_code"]

    penalties: list[PenaltyHit] = []
    signals: list[SignalHit] = []

    verified = False
    verification_details: dict[str, Any] | None = None

    if timed_out:
        penalties.append(
            PenaltyHit(
                id=f"{tier.name}_timeout",
                points=tier.hard_penalty,
                description=f"{tier.label.title()} Docker evaluation hit the hard timeout.",
            )
        )
    elif exit_code != 0:
        description = f"{tier.label.title()} Docker evaluation exited with a non-zero status."
        if exit_code == 137:
            description = (
                f"{tier.label.title()} Docker evaluation was likely OOM-killed under the "
                "configured memory cap."
            )
        penalties.append(
            PenaltyHit(
                id=f"{tier.name}_nonzero_exit",
                points=tier.hard_penalty,
                description=description,
            )
        )
    else:
        signals.append(
            SignalHit(
                id=f"{tier.name}_docker_execution_passed",
                description=f"{tier.label.title()} tier ran successfully inside Docker.",
            )
        )
        verified, verification_details = _verify_output_dataset(input_dir, tier_output_dir)
        if verified:
            signals.append(
                SignalHit(
                    id=f"{tier.name}_output_verified",
                    description=f"{tier.label.title()} output matched the independently verified expected rewrite.",
                )
            )
        else:
            penalties.append(
                PenaltyHit(
                    id=f"{tier.name}_output_invalid",
                    points=tier.hard_penalty,
                    description=f"{tier.label.title()} output did not match the expected filtered, deduped, sorted rewrite.",
                )
            )

    if (
        wall_time_seconds is not None
        and not timed_out
        and exit_code == 0
        and verified
    ):
        if wall_time_seconds <= tier.soft_time_seconds:
            signals.append(
                SignalHit(
                    id=f"{tier.name}_runtime_within_soft_limit",
                    description=f"{tier.label.title()} tier completed within the configured soft runtime budget.",
                )
            )
        else:
            penalties.append(
                PenaltyHit(
                    id=f"{tier.name}_runtime_soft_limit_exceeded",
                    points=tier.runtime_penalty,
                    description=f"{tier.label.title()} tier completed, but missed the soft runtime budget.",
                )
            )

    if timed_out:
        summary_bit = f"{tier.name}=timeout"
    elif exit_code == 137:
        summary_bit = f"{tier.name}=oom:137"
    elif exit_code != 0:
        summary_bit = f"{tier.name}=exit:{exit_code}"
    elif verified:
        summary_bit = f"{tier.name}=ok:{wall_time_seconds:.2f}s"
    else:
        summary_bit = f"{tier.name}=invalid:{wall_time_seconds:.2f}s"

    return {
        "penalties": penalties,
        "signals": signals,
        "summary_bit": summary_bit,
        "timed_out": timed_out,
        "exit_code": exit_code,
        "verified": verified,
        "wall_time_seconds": wall_time_seconds,
        "command": tuple(command),
        "stdout_log": stdout_log,
        "stderr_log": stderr_log,
        "details": {
            "name": tier.name,
            "label": tier.label,
            "input_dir": str(input_dir),
            "output_dir": str(tier_output_dir),
            "scratch_dir": str(tier_scratch_dir),
            "logs_dir": str(tier_logs_dir),
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
            "soft_time_seconds": tier.soft_time_seconds,
            "memory": tier.memory or memory,
            "invocation_mode": invocation_mode,
            "max_penalty_possible": tier.hard_penalty,
            "wall_time_seconds": wall_time_seconds,
            "timed_out": timed_out,
            "exit_code": exit_code,
            "oom_likely": exit_code == 137,
            "output_verified": verified,
            "verification": verification_details,
            "triggered_penalties": [item.to_dict() for item in penalties],
            "passed_signals": [item.to_dict() for item in signals],
        },
    }


def _docker_command(
    *,
    image: str,
    submission_dir: Path,
    input_dir: Path,
    output_dir: Path,
    scratch_dir: Path,
    memory: str,
    cpus: str,
    use_flag_args: bool,
) -> list[str]:
    docker_bin = shutil.which("docker")
    assert docker_bin is not None
    command = [
        docker_bin,
        "run",
        "--rm",
        "--memory",
        memory,
        "--memory-swap",
        memory,
        "--cpus",
        cpus,
        "--network",
        "none",
        "--pids-limit",
        "256",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,size=64m",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
        "-e",
        "PYTHONUNBUFFERED=1",
        "-e",
        "HF_DATASETS_CACHE=/scratch/hf-cache",
        "-e",
        "TMPDIR=/scratch/tmp",
        "-v",
        f"{submission_dir}:/submission:ro",
        "-v",
        f"{input_dir}:/input:ro",
        "-v",
        f"{output_dir}:/output",
        "-v",
        f"{scratch_dir}:/scratch",
        image,
        "python",
        "/submission/rewrite_dataset.py",
    ]
    if use_flag_args:
        command.extend(["--input_dir", "/input", "--output_dir", "/output"])
    else:
        command.extend(["/input", "/output"])
    return command


def _run_docker_command(*, command: list[str], timeout_seconds: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
            "timed_out": False,
            "wall_time_seconds": time.monotonic() - started,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "exit_code": None,
            "timed_out": True,
            "wall_time_seconds": time.monotonic() - started,
        }


def _looks_like_cli_argument_mismatch(stderr: str) -> bool:
    normalized = stderr.casefold()
    return (
        "usage:" in normalized
        and (
            "the following arguments are required" in normalized
            or "unrecognized arguments" in normalized
        )
    )


def _combine_attempt_logs(
    first_command: list[str],
    first_output: str,
    second_command: list[str],
    second_output: str,
) -> str:
    return (
        f"$ {' '.join(first_command)}\n{first_output}\n\n"
        f"$ {' '.join(second_command)}\n{second_output}"
    )


def _normalize_text(tokens: list[str]) -> str:
    return " ".join(" ".join(tokens).strip().casefold().split())


def _choose_better(current: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    current_key = (
        float(current["score"]),
        int(current["updated_at"]),
        tuple(-ord(ch) for ch in str(current["example_id"])),
    )
    candidate_key = (
        float(candidate["score"]),
        int(candidate["updated_at"]),
        tuple(-ord(ch) for ch in str(candidate["example_id"])),
    )
    return candidate if candidate_key > current_key else current


def _expected_rows(input_dir: Path) -> list[dict[str, Any]]:
    _, _, load_from_disk = _require_datasets()
    dataset = load_from_disk(str(input_dir))
    winners: dict[tuple[str, str], dict[str, Any]] = {}

    for row in dataset:
        tokens = [str(token) for token in row["tokens"]]
        ner_tags = [int(value) for value in row["ner_tags"]]
        if not tokens:
            continue
        if len(tokens) != len(ner_tags):
            continue
        normalized_text = _normalize_text(tokens)
        if not normalized_text:
            continue

        candidate = {
            "example_id": str(row["example_id"]),
            "source": str(row["source"]),
            "tokens": tokens,
            "ner_tags": ner_tags,
            "score": float(row["score"]),
            "updated_at": int(row["updated_at"]),
            "text": " ".join(tokens),
        }
        key = (candidate["source"], normalized_text)
        existing = winners.get(key)
        if existing is None:
            winners[key] = candidate
        else:
            winners[key] = _choose_better(existing, candidate)

    return sorted(
        winners.values(),
        key=lambda row: (row["source"], row["updated_at"], row["example_id"]),
    )


def _project_output_row(row: dict[str, Any]) -> dict[str, Any]:
    projected: dict[str, Any] = {}
    for field in OUTPUT_FIELDS:
        if field not in row:
            raise ValueError(f"Missing required field {field!r} in output row.")
        if field in {"tokens", "ner_tags"}:
            projected[field] = list(row[field])
        elif field == "score":
            projected[field] = float(row[field])
        elif field == "updated_at":
            projected[field] = int(row[field])
        else:
            projected[field] = str(row[field])
    return projected


def _verify_output_dataset(input_dir: Path, output_dir: Path) -> tuple[bool, dict[str, Any]]:
    _, _, load_from_disk = _require_datasets()
    if not output_dir.exists():
        return False, {"reason": "output_dir_missing"}

    try:
        output_dataset = load_from_disk(str(output_dir))
    except Exception as exc:
        return False, {"reason": "output_load_failed", "error": str(exc)}

    expected = _expected_rows(input_dir)
    actual: list[dict[str, Any]] = []
    try:
        for row in output_dataset:
            actual.append(_project_output_row(row))
    except Exception as exc:
        return False, {"reason": "output_projection_failed", "error": str(exc)}

    if len(expected) != len(actual):
        return False, {
            "reason": "row_count_mismatch",
            "expected_rows": len(expected),
            "actual_rows": len(actual),
        }

    for index, (want, got) in enumerate(zip(expected, actual)):
        if want != got:
            return False, {
                "reason": "row_mismatch",
                "first_mismatch_index": index,
                "expected": want,
                "actual": got,
            }

    return True, {"rows_verified": len(actual)}


def _combine_static_and_execution(
    task: TaskDefinition,
    static_scorecard: TaskScorecard,
    execution_result: ExecutionResult,
) -> TaskScorecard:
    penalties = static_scorecard.triggered_penalties + execution_result.triggered_penalties
    verified_tiers = [
        tier
        for tier in execution_result.details.get("tiers", [])
        if tier.get("output_verified")
    ]
    static_signals = static_scorecard.passed_signals
    suppressed_signal_ids: tuple[str, ...] = ()
    if task.execution_gated_signals and not verified_tiers:
        gated_ids = set(task.execution_gated_signals)
        suppressed_signal_ids = tuple(
            signal.id for signal in static_signals if signal.id in gated_ids
        )
        static_signals = tuple(
            signal for signal in static_signals if signal.id not in gated_ids
        )

    signals = static_signals + execution_result.passed_signals
    total_penalty = sum(item.points for item in penalties)
    execution_max_penalty = sum(
        int(tier.get("max_penalty_possible", 0))
        for tier in execution_result.details.get("tiers", [])
    )
    judge_summary = f"{static_scorecard.judge_summary} Execution: {execution_result.summary}"
    if suppressed_signal_ids:
        suppressed_bits = ", ".join(suppressed_signal_ids)
        judge_summary += (
            " Static signals suppressed until at least one execution tier verifies output: "
            f"{suppressed_bits}."
        )
    return TaskScorecard(
        task_id=static_scorecard.task_id,
        title=static_scorecard.title,
        total_penalty=total_penalty,
        max_penalty_possible=(static_scorecard.max_penalty_possible or 0) + execution_max_penalty,
        triggered_penalties=penalties,
        passed_signals=signals,
        judge_summary=judge_summary,
        artifacts_seen=static_scorecard.artifacts_seen,
    )


def _build_execution_summary(
    *,
    summary_bits: list[str],
    logs_dir: Path,
) -> str:
    joined = ", ".join(summary_bits) if summary_bits else "no tiers ran"
    return f"Tier results: {joined}. Logs: {logs_dir}."
