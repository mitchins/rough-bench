from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Sequence

from roughbench.execution import evaluate_hf_datasets_submission, prepare_hf_datasets_sandbox
from roughbench.jobs import (
    create_job,
    default_jobs_dir,
    inspect_job,
    launch_job,
    list_jobs,
    mark_finished,
    mark_running,
)
from roughbench.judging import (
    AnthropicJudgeClient,
    CopilotSDKJudgeClient,
    HybridJudge,
    Judge,
    LLMScorecardJudge,
    OpenAICompatibleJudgeClient,
    RuleBasedJudge,
    StackedJudge,
    TaskScorecard,
    aggregate_scorecards,
)
from roughbench.runners import AnthropicRunner, LocalDirectoryRunner, OpenAIRunner
from roughbench.runners.base import Runner
from roughbench.runners.openai_compatible import OpenAICompatibleRunner
from roughbench.runners.openai_compatible import from_env as live_runner_from_env
from roughbench.subjects import SubjectDefinition, load_subjects
from roughbench.tasks import TaskDefinition, load_tasks


JUDGE_PROVIDER_CHOICES = ("openai-compatible", "anthropic", "copilot-sdk")
REASONING_EFFORT_CHOICES = ("low", "medium", "high", "xhigh")


def _source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_path(dirname: str) -> Path:
    cwd_candidate = Path.cwd() / dirname
    if cwd_candidate.exists():
        return cwd_candidate
    return _source_root() / dirname


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run RoughBench locally.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available benchmark tasks.")
    list_parser.add_argument(
        "--benchmarks-dir",
        type=Path,
        default=_default_path("benchmarks"),
        help="Directory containing benchmark task folders.",
    )

    sandbox_parser = subparsers.add_parser(
        "sandbox",
        help="Create a local sandbox with a visible fixture for an execution-backed task.",
    )
    sandbox_parser.add_argument(
        "--benchmarks-dir",
        type=Path,
        default=_default_path("benchmarks"),
        help="Directory containing benchmark task folders.",
    )
    sandbox_parser.add_argument(
        "--task",
        required=True,
        help="Task id to scaffold.",
    )
    sandbox_parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Directory to create for the sandbox run.",
    )
    sandbox_parser.add_argument(
        "--visible-rows",
        type=int,
        default=192,
        help="Approximate number of visible fixture rows to generate.",
    )
    sandbox_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing run directory if it already exists.",
    )

    demo_parser = subparsers.add_parser("demo", help="Run the built-in mocked example outputs.")
    _add_run_arguments(demo_parser)
    demo_parser.add_argument(
        "--examples-dir",
        type=Path,
        default=_default_path("examples"),
        help="Directory containing mocked local outputs.",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Score local outputs or query a live OpenAI-compatible endpoint.",
    )
    _add_run_arguments(run_parser)
    run_mode_group = run_parser.add_mutually_exclusive_group(required=True)
    run_mode_group.add_argument(
        "--responses-dir",
        type=Path,
        help="Directory containing one output folder per task id.",
    )
    run_mode_group.add_argument(
        "--live",
        action="store_true",
        help="Generate answers from an OpenAI-compatible /v1 endpoint before judging.",
    )
    run_parser.add_argument(
        "--base-url",
        help="Base URL for the OpenAI-compatible API, for example http://host:8000/v1.",
    )
    run_parser.add_argument(
        "--model",
        help="Exact model id exposed by the OpenAI-compatible server.",
    )
    run_parser.add_argument(
        "--api-key",
        help="API key for the OpenAI-compatible API. Defaults to ROUGHBENCH_API_KEY or dummy.",
    )
    run_parser.add_argument(
        "--temperature",
        type=float,
        help="Sampling temperature for live runs.",
    )
    run_parser.add_argument(
        "--max-tokens",
        type=int,
        help="Maximum completion tokens for live runs.",
    )
    run_parser.add_argument(
        "--reasoning-effort",
        choices=REASONING_EFFORT_CHOICES,
        help="Reasoning effort for live OpenAI-compatible runs when the engine supports it.",
    )
    run_parser.add_argument(
        "--save-responses-dir",
        type=Path,
        help="Optional directory to write generated responses under each task id.",
    )
    run_parser.add_argument(
        "--timeout-seconds",
        type=int,
        help="Request timeout for live OpenAI-compatible runs.",
    )
    run_parser.add_argument(
        "--direct-answer-first",
        action="store_true",
        help="Prepend the direct-answer preamble on the first live OpenAI-compatible request.",
    )
    _add_background_arguments(run_parser)

    compare_parser = subparsers.add_parser(
        "compare",
        help="Run the same benchmark tasks across multiple live subject models.",
    )
    _add_run_arguments(compare_parser)
    compare_parser.add_argument(
        "--subjects-file",
        type=Path,
        default=_default_path("subjects/seed_subjects.yaml"),
        help="YAML file defining live subject models to compare.",
    )
    compare_parser.add_argument(
        "--subject",
        action="append",
        default=[],
        help="Limit comparison to a subject id from the subjects file. Repeat to select multiple.",
    )
    compare_parser.add_argument(
        "--save-runs-dir",
        type=Path,
        help="Optional root directory to persist generated responses under each subject id.",
    )
    compare_parser.add_argument(
        "--retry-attempts",
        type=int,
        default=2,
        help="Additional retries per task after the first live subject failure.",
    )
    compare_parser.add_argument(
        "--retry-backoff-seconds",
        type=float,
        default=5.0,
        help="Base backoff between compare retries. Later retries wait longer.",
    )
    compare_parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Abort compare on the first task failure instead of recording a partial report.",
    )
    _add_background_arguments(compare_parser)

    execute_parser = subparsers.add_parser(
        "execute",
        help="Run an execution-backed task submission inside Docker and score it.",
    )
    execute_parser.add_argument(
        "--benchmarks-dir",
        type=Path,
        default=_default_path("benchmarks"),
        help="Directory containing benchmark task folders.",
    )
    execute_parser.add_argument(
        "--task",
        required=True,
        help="Task id to execute.",
    )
    execute_parser.add_argument(
        "--submission-dir",
        type=Path,
        required=True,
        help="Directory containing the task submission artifacts.",
    )
    execute_parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Input dataset directory for the Docker evaluation.",
    )
    execute_parser.add_argument(
        "--work-dir",
        type=Path,
        help="Directory for frozen submission, output, and Docker logs.",
    )
    execute_parser.add_argument(
        "--memory",
        default="512m",
        help="Docker memory limit, for example 512m or 1g.",
    )
    execute_parser.add_argument(
        "--cpus",
        default="1",
        help="Docker CPU quota passed to --cpus.",
    )
    execute_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="Hard timeout for the Docker execution.",
    )
    execute_parser.add_argument(
        "--soft-time-seconds",
        type=float,
        default=15.0,
        help="Soft runtime budget used for additional penalties.",
    )
    execute_parser.add_argument(
        "--docker-image",
        default="roughbench-hf-datasets-runner:latest",
        help="Docker image tag to use for the evaluator container.",
    )
    execute_parser.add_argument(
        "--visible-only",
        action="store_true",
        help="Run only the provided visible fixture instead of the default visible plus hidden tiers.",
    )
    execute_parser.add_argument(
        "--rebuild-image",
        action="store_true",
        help="Force a Docker image rebuild before execution.",
    )
    execute_parser.add_argument(
        "--no-build",
        action="store_true",
        help="Do not build the Docker image automatically if it is missing.",
    )
    execute_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the execution report as JSON.",
    )
    execute_parser.add_argument(
        "--output",
        type=Path,
        help="Write the execution report JSON to a file.",
    )

    jobs_parser = subparsers.add_parser("jobs", help="List or inspect detached RoughBench jobs.")
    jobs_parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=default_jobs_dir(),
        help="Directory containing persisted RoughBench job metadata.",
    )
    jobs_parser.add_argument(
        "--job-id",
        help="Inspect one job id instead of listing all jobs.",
    )
    jobs_parser.add_argument(
        "--log-lines",
        type=int,
        default=20,
        help="Number of log lines to include when inspecting one job.",
    )
    jobs_parser.add_argument(
        "--json",
        action="store_true",
        help="Print jobs as JSON.",
    )

    return parser


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--benchmarks-dir",
        type=Path,
        default=_default_path("benchmarks"),
        help="Directory containing benchmark task folders.",
    )
    parser.add_argument(
        "--task",
        action="append",
        default=[],
        help="Limit scoring to a task id. Repeat to select multiple tasks.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full report as JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the JSON report to a file.",
    )
    parser.add_argument(
        "--judge-mode",
        choices=("rule", "llm", "stacked", "hybrid"),
        default=os.getenv("ROUGHBENCH_JUDGE_MODE", "rule"),
        help="Judge backend to use. Default is deterministic rule-based judging.",
    )
    parser.add_argument(
        "--judge-provider",
        choices=JUDGE_PROVIDER_CHOICES,
        help="Provider for the final LLM judge.",
    )
    parser.add_argument(
        "--judge-model",
        help="Model name for the final LLM judge.",
    )
    parser.add_argument(
        "--judge-reasoning-effort",
        choices=REASONING_EFFORT_CHOICES,
        help="Reasoning effort for judge providers that support it.",
    )
    parser.add_argument(
        "--judge-base-url",
        help="Base URL for an OpenAI-compatible final judge endpoint.",
    )
    parser.add_argument(
        "--judge-api-key",
        help="API key for the final judge. Defaults to provider-specific env vars.",
    )
    parser.add_argument(
        "--judge-temperature",
        type=float,
        help="Sampling temperature for the final judge.",
    )
    parser.add_argument(
        "--judge-max-tokens",
        type=int,
        help="Maximum completion tokens for the final judge.",
    )
    parser.add_argument(
        "--judge-timeout-seconds",
        type=int,
        help="Request timeout for the final judge.",
    )
    parser.add_argument(
        "--draft-judge-provider",
        choices=JUDGE_PROVIDER_CHOICES,
        help="Provider for the draft judge when --judge-mode stacked is used.",
    )
    parser.add_argument(
        "--draft-judge-model",
        help="Model name for the draft judge.",
    )
    parser.add_argument(
        "--draft-judge-reasoning-effort",
        choices=REASONING_EFFORT_CHOICES,
        help="Reasoning effort for the draft judge when supported by the provider.",
    )
    parser.add_argument(
        "--draft-judge-base-url",
        help="Base URL for an OpenAI-compatible draft judge endpoint.",
    )
    parser.add_argument(
        "--draft-judge-api-key",
        help="API key for the draft judge.",
    )
    parser.add_argument(
        "--draft-judge-temperature",
        type=float,
        help="Sampling temperature for the draft judge.",
    )
    parser.add_argument(
        "--draft-judge-max-tokens",
        type=int,
        help="Maximum completion tokens for the draft judge.",
    )
    parser.add_argument(
        "--draft-judge-timeout-seconds",
        type=int,
        help="Request timeout for the draft judge.",
    )


def _add_background_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--background",
        action="store_true",
        help="Queue this command as a detached local job and return immediately.",
    )
    parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=default_jobs_dir(),
        help="Directory used to persist detached job metadata and logs.",
    )
    parser.add_argument(
        "--job-id",
        help=argparse.SUPPRESS,
    )


def main(argv: Sequence[str] | None = None) -> int:
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(raw_argv)

    if args.command == "jobs":
        return _print_jobs(args)

    if args.command in {"run", "compare"} and getattr(args, "background", False):
        return _launch_background_job(raw_argv, args)

    job_id = getattr(args, "job_id", None)
    jobs_dir = getattr(args, "jobs_dir", None)
    if job_id and isinstance(jobs_dir, Path):
        mark_running(jobs_dir=jobs_dir, job_id=job_id)

    exit_code = 1
    try:
        exit_code = _dispatch(args, parser)
        return exit_code
    except BaseException as exc:
        if isinstance(exc, SystemExit) and isinstance(exc.code, int):
            exit_code = exc.code
        else:
            exit_code = 1
        raise
    finally:
        if job_id and isinstance(jobs_dir, Path):
            mark_finished(jobs_dir=jobs_dir, job_id=job_id, exit_code=exit_code)


def _dispatch(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    if args.command == "list":
        return _list_tasks(args.benchmarks_dir)
    if args.command == "sandbox":
        task = _load_single_task(args.benchmarks_dir, args.task, parser)
        try:
            payload = prepare_hf_datasets_sandbox(
                task,
                run_dir=args.run_dir,
                force=args.force,
                visible_rows=args.visible_rows,
            )
        except (RuntimeError, ValueError) as exc:
            parser.error(str(exc))
        print(json.dumps(payload, indent=2))
        return 0
    if args.command == "execute":
        task = _load_single_task(args.benchmarks_dir, args.task, parser)
        try:
            return _execute_task(task, args)
        except (RuntimeError, ValueError) as exc:
            parser.error(str(exc))

    tasks = load_tasks(args.benchmarks_dir, task_ids=args.task)
    if not tasks:
        parser.error("No tasks found for the given benchmarks directory or task filters.")

    try:
        judge = _build_judge(args)
    except ValueError as exc:
        parser.error(str(exc))

    if args.command == "compare":
        return _run_compare(tasks, args, judge=judge)

    if args.command == "demo":
        report = _run_with_runner(tasks, LocalDirectoryRunner(args.examples_dir), judge=judge)
    elif args.command == "run" and args.live:
        report = _run_live(tasks, args, judge=judge)
    else:
        report = _run_with_runner(tasks, LocalDirectoryRunner(args.responses_dir), judge=judge)

    if args.output:
        args.output.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        _print_human_report(report)

    return 0


def _list_tasks(benchmarks_dir: Path) -> int:
    tasks = load_tasks(benchmarks_dir)
    if not tasks:
        print(f"No tasks found in {benchmarks_dir}")
        return 1

    for task in tasks:
        print(f"{task.id}\t{task.domain}\t{task.title}")
    return 0


def _load_single_task(
    benchmarks_dir: Path,
    task_id: str,
    parser: argparse.ArgumentParser,
) -> TaskDefinition:
    tasks = load_tasks(benchmarks_dir, task_ids=[task_id])
    if not tasks:
        parser.error(f"No task found for id {task_id!r}.")
    return tasks[0]


def _run_with_runner(tasks: list[TaskDefinition], runner: Runner, *, judge: Judge) -> object:
    scorecards = [judge.evaluate(task, runner.collect(task)) for task in tasks]
    return aggregate_scorecards(scorecards)


def _run_live(tasks: list[TaskDefinition], args: argparse.Namespace, *, judge: Judge) -> object:
    runner = live_runner_from_env(
        model=args.model,
        base_url=args.base_url,
        api_key=args.api_key,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout_seconds=args.timeout_seconds,
        reasoning_effort=args.reasoning_effort,
        direct_answer_first=args.direct_answer_first,
        save_responses_dir=args.save_responses_dir,
    )
    return _run_with_runner(tasks, runner, judge=judge)


def _run_compare(tasks: list[TaskDefinition], args: argparse.Namespace, *, judge: Judge) -> int:
    subjects = load_subjects(args.subjects_file, subject_ids=args.subject)
    if not subjects:
        raise SystemExit(f"No subjects found in {args.subjects_file} for the requested filters.")

    compared: list[dict] = []
    for subject in subjects:
        compared.append(_run_compare_subject(tasks, subject, args, judge=judge))
        _persist_compare_payload(args, compared)

    payload = {
        "subjects_file": str(args.subjects_file),
        "benchmarks_dir": str(args.benchmarks_dir),
        "judge_mode": args.judge_mode,
        "retry_attempts": args.retry_attempts,
        "retry_backoff_seconds": args.retry_backoff_seconds,
        "subjects": compared,
    }
    payload["summary"] = _summarize_compare_payload(compared)
    _persist_compare_payload(args, compared)

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        _print_compare_report(compared)

    if any(item["failed_task_count"] > 0 for item in compared):
        return 1
    return 0


def _run_compare_subject(
    tasks: list[TaskDefinition],
    subject: SubjectDefinition,
    args: argparse.Namespace,
    *,
    judge: Judge,
) -> dict[str, Any]:
    runner = _runner_for_subject(subject, args.save_runs_dir)
    subject_save_dir = _subject_save_dir(subject, args.save_runs_dir)
    scorecards: list[TaskScorecard] = []
    failures: list[dict[str, Any]] = []
    for task in tasks:
        scorecard, failure = _evaluate_task_with_retries(
            task,
            runner,
            judge,
            subject=subject,
            retry_attempts=args.retry_attempts,
            retry_backoff_seconds=args.retry_backoff_seconds,
        )
        if scorecard is not None:
            scorecards.append(scorecard)
        if failure is not None:
            failures.append(failure)
            if args.fail_fast:
                _persist_compare_subject_progress(
                    subject=subject,
                    subject_save_dir=subject_save_dir,
                    requested_task_count=len(tasks),
                    scorecards=scorecards,
                    failures=failures,
                )
                raise RuntimeError(
                    f"Compare aborted for subject {subject.id!r} on task {task.id!r}: "
                    f"{failure['error_type']}: {failure['error_message']}"
                )
        _persist_compare_subject_progress(
            subject=subject,
            subject_save_dir=subject_save_dir,
            requested_task_count=len(tasks),
            scorecards=scorecards,
            failures=failures,
        )
    return _build_compare_subject_payload(
        subject=subject,
        requested_task_count=len(tasks),
        scorecards=scorecards,
        failures=failures,
        subject_save_dir=subject_save_dir,
    )


def _evaluate_task_with_retries(
    task: TaskDefinition,
    runner: Runner,
    judge: Judge,
    *,
    subject: SubjectDefinition,
    retry_attempts: int,
    retry_backoff_seconds: float,
) -> tuple[TaskScorecard | None, dict[str, Any] | None]:
    attempts: list[dict[str, Any]] = []
    total_attempts = max(1, retry_attempts + 1)
    for attempt_number in range(1, total_attempts + 1):
        try:
            return judge.evaluate(task, runner.collect(task)), None
        except Exception as exc:
            error_entry = {
                "attempt": attempt_number,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": "".join(traceback.format_exception(exc)).strip(),
            }
            attempts.append(error_entry)
            print(
                f"[compare] {subject.id} {task.id} attempt {attempt_number}/{total_attempts} failed: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            if attempt_number >= total_attempts:
                return None, {
                    "task_id": task.id,
                    "title": task.title,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "attempt_count": len(attempts),
                    "attempts": attempts,
                }
            if retry_backoff_seconds > 0:
                time.sleep(retry_backoff_seconds * attempt_number)
    return None, {
        "task_id": task.id,
        "title": task.title,
        "error_type": "RuntimeError",
        "error_message": "unreachable retry state",
        "attempt_count": len(attempts),
        "attempts": attempts,
    }


def _subject_save_dir(subject: SubjectDefinition, save_runs_dir: Path | None) -> Path | None:
    if save_runs_dir is None:
        return None
    return save_runs_dir / subject.storage_name


def _build_compare_subject_payload(
    *,
    subject: SubjectDefinition,
    requested_task_count: int,
    scorecards: list[TaskScorecard],
    failures: list[dict[str, Any]],
    subject_save_dir: Path | None,
) -> dict[str, Any]:
    completed_task_count = len(scorecards)
    failed_task_count = len(failures)
    if completed_task_count == requested_task_count and failed_task_count == 0:
        status = "complete"
    elif completed_task_count > 0:
        status = "partial"
    else:
        status = "failed"
    report = _build_compare_report_dict(
        scorecards,
        requested_task_count=requested_task_count,
        failed_task_count=failed_task_count,
    )
    payload = {
        "subject_id": subject.id,
        "title": subject.title,
        "provider": subject.provider,
        "base_url": subject.base_url,
        "model": subject.model,
        "reasoning_effort": subject.reasoning_effort,
        "notes": subject.notes,
        "status": status,
        "requested_task_count": requested_task_count,
        "completed_task_count": completed_task_count,
        "failed_task_count": failed_task_count,
        "failures": failures,
        "report": report,
    }
    if subject_save_dir is not None:
        payload["progress_path"] = str(subject_save_dir / ".roughbench_compare_subject.json")
    return payload


def _build_compare_report_dict(
    scorecards: list[TaskScorecard],
    *,
    requested_task_count: int,
    failed_task_count: int,
) -> dict[str, Any]:
    completed_task_count = len(scorecards)
    if scorecards:
        report = aggregate_scorecards(scorecards).to_dict()
    else:
        report = {
            "roughbench_demerits": 0,
            "roughbench_score": 0,
            "suite_max_demerits": None,
            "suite_demerit_pct": None,
            "lower_is_better": True,
            "judged_at": datetime.now(UTC).isoformat(),
            "summary": "No tasks completed successfully.",
            "task_results": [],
        }
    completion_line = (
        f"Completed {completed_task_count} of {requested_task_count} task(s)"
    )
    if failed_task_count:
        completion_line += f"; {failed_task_count} failed."
    else:
        completion_line += "; no task failures."
    report["summary"] = f"{completion_line} {report['summary']}"
    return report


def _persist_compare_subject_progress(
    *,
    subject: SubjectDefinition,
    subject_save_dir: Path | None,
    requested_task_count: int,
    scorecards: list[TaskScorecard],
    failures: list[dict[str, Any]],
) -> None:
    if subject_save_dir is None:
        return
    subject_save_dir.mkdir(parents=True, exist_ok=True)
    payload = _build_compare_subject_payload(
        subject=subject,
        requested_task_count=requested_task_count,
        scorecards=scorecards,
        failures=failures,
        subject_save_dir=subject_save_dir,
    )
    (subject_save_dir / ".roughbench_compare_subject.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def _persist_compare_payload(args: argparse.Namespace, compared: list[dict[str, Any]]) -> None:
    payload = {
        "subjects_file": str(args.subjects_file),
        "benchmarks_dir": str(args.benchmarks_dir),
        "judge_mode": args.judge_mode,
        "retry_attempts": args.retry_attempts,
        "retry_backoff_seconds": args.retry_backoff_seconds,
        "summary": _summarize_compare_payload(compared),
        "subjects": compared,
    }
    if args.output:
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.save_runs_dir is not None:
        args.save_runs_dir.mkdir(parents=True, exist_ok=True)
        (args.save_runs_dir / ".roughbench_compare.json").write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )


def _summarize_compare_payload(compared: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "subject_count": len(compared),
        "complete_subject_count": sum(1 for item in compared if item["status"] == "complete"),
        "partial_subject_count": sum(1 for item in compared if item["status"] == "partial"),
        "failed_subject_count": sum(1 for item in compared if item["status"] == "failed"),
        "failed_task_count": sum(item["failed_task_count"] for item in compared),
    }


def _runner_for_subject(
    subject: SubjectDefinition,
    save_runs_dir: Path | None,
) -> Runner:
    save_dir = None
    if save_runs_dir is not None:
        save_dir = save_runs_dir / subject.storage_name
    if subject.provider == "openai":
        return OpenAIRunner(
            model=subject.model,
            api_key=subject.resolved_api_key,
            temperature=subject.temperature,
            max_tokens=subject.max_tokens,
            reasoning_effort=subject.reasoning_effort,
            save_responses_dir=save_dir,
        )
    if subject.provider == "anthropic":
        return AnthropicRunner(
            model=subject.model,
            api_key=subject.resolved_api_key,
            temperature=subject.temperature,
            max_tokens=subject.max_tokens,
            save_responses_dir=save_dir,
        )
    return OpenAICompatibleRunner(
        model=subject.model,
        base_url=subject.base_url,
        api_key=subject.resolved_api_key,
        temperature=subject.temperature,
        max_tokens=subject.max_tokens,
        timeout_seconds=subject.timeout_seconds,
        reasoning_effort=subject.reasoning_effort,
        direct_answer_first=subject.direct_answer_first,
        save_responses_dir=save_dir,
    )


def _build_judge(args: argparse.Namespace) -> Judge:
    if args.judge_mode == "rule":
        return RuleBasedJudge()

    final_judge = LLMScorecardJudge(_build_judge_client(args, prefix="judge"))
    if args.judge_mode == "llm":
        return final_judge
    if args.judge_mode == "hybrid":
        return HybridJudge(anchor_judge=RuleBasedJudge(), review_judge=final_judge)

    draft_judge = LLMScorecardJudge(_build_judge_client(args, prefix="draft_judge"))
    return StackedJudge(draft_judge=draft_judge, final_judge=final_judge)


def _build_judge_client(
    args: argparse.Namespace,
    *,
    prefix: str,
) -> OpenAICompatibleJudgeClient | AnthropicJudgeClient | CopilotSDKJudgeClient:
    env_prefix = prefix.upper()
    provider = _resolve_setting(
        getattr(args, f"{prefix}_provider", None),
        f"ROUGHBENCH_{env_prefix}_PROVIDER",
        default="openai-compatible",
    )
    model = _resolve_setting(
        getattr(args, f"{prefix}_model", None),
        f"ROUGHBENCH_{env_prefix}_MODEL",
    )
    if not model:
        raise ValueError(f"Missing model for {prefix.replace('_', ' ')}.")

    temperature_value = _resolve_setting(
        getattr(args, f"{prefix}_temperature", None),
        f"ROUGHBENCH_{env_prefix}_TEMPERATURE",
        default="0.0",
    )
    max_tokens_value = _resolve_setting(
        getattr(args, f"{prefix}_max_tokens", None),
        f"ROUGHBENCH_{env_prefix}_MAX_TOKENS",
        default="2000",
    )
    timeout_seconds_value = _resolve_setting(
        getattr(args, f"{prefix}_timeout_seconds", None),
        f"ROUGHBENCH_{env_prefix}_TIMEOUT_SECONDS",
        default="180",
    )
    reasoning_effort = _resolve_setting(
        getattr(args, f"{prefix}_reasoning_effort", None),
        f"ROUGHBENCH_{env_prefix}_REASONING_EFFORT",
    )
    temperature = float(temperature_value)
    max_tokens = int(max_tokens_value)
    timeout_seconds = int(timeout_seconds_value)

    if provider == "anthropic":
        api_key = _resolve_setting(
            getattr(args, f"{prefix}_api_key", None),
            f"ROUGHBENCH_{env_prefix}_API_KEY",
            fallback_env="ANTHROPIC_API_KEY",
        )
        if not api_key:
            raise ValueError(f"Missing API key for {prefix.replace('_', ' ')}.")
        return AnthropicJudgeClient(
            model_name=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "copilot-sdk":
        package_root = _resolve_setting(
            None,
            "ROUGHBENCH_COPILOT_PACKAGE_ROOT",
        )
        return CopilotSDKJudgeClient(
            model_name=model,
            reasoning_effort=reasoning_effort,
            timeout_seconds=timeout_seconds,
            copilot_package_root=package_root,
        )

    base_url = _resolve_setting(
        getattr(args, f"{prefix}_base_url", None),
        f"ROUGHBENCH_{env_prefix}_BASE_URL",
    )
    if not base_url:
        raise ValueError(f"Missing base URL for {prefix.replace('_', ' ')}.")

    api_key = _resolve_setting(
        getattr(args, f"{prefix}_api_key", None),
        f"ROUGHBENCH_{env_prefix}_API_KEY",
        default="dummy",
    )
    return OpenAICompatibleJudgeClient(
        model_name=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds,
        reasoning_effort=reasoning_effort or "",
    )


def _resolve_setting(
    cli_value: object,
    env_name: str,
    *,
    fallback_env: str | None = None,
    default: str | None = None,
) -> str | None:
    if cli_value is not None:
        return str(cli_value)
    if env_name in os.environ:
        return os.environ[env_name]
    if fallback_env and fallback_env in os.environ:
        return os.environ[fallback_env]
    return default


def _print_human_report(report: object) -> None:
    data = report.to_dict()
    if data.get("suite_max_demerits") is not None:
        pct = data.get("suite_demerit_pct")
        pct_bit = f", {pct}% of current suite max" if pct is not None else ""
        print(
            f"RoughBench demerits: {data['roughbench_demerits']} / "
            f"{data['suite_max_demerits']}{pct_bit} (lower is better)"
        )
    else:
        print(f"RoughBench demerits: {data['roughbench_demerits']} (lower is better)")
    print(f"Summary: {data['summary']}")
    print(f"Judged at: {data['judged_at']}")

    for task in data["task_results"]:
        print()
        print(f"{task['task_id']} [{task['title']}]")
        if task.get("max_penalty_possible") is not None:
            pct = task.get("demerit_pct")
            pct_bit = f", {pct}%" if pct is not None else ""
            print(
                f"  demerits: {task['total_penalty']} / "
                f"{task['max_penalty_possible']}{pct_bit}"
            )
        else:
            print(f"  demerits: {task['total_penalty']}")
        if task["triggered_penalties"]:
            penalty_bits = ", ".join(
                f"{item['id']} (+{item['points']})"
                for item in task["triggered_penalties"]
            )
            print(f"  triggered_penalties: {penalty_bits}")
        else:
            print("  triggered_penalties: none")
        if task["passed_signals"]:
            signal_bits = ", ".join(item["id"] for item in task["passed_signals"])
            print(f"  passed_signals: {signal_bits}")
        else:
            print("  passed_signals: none")
        if task["artifacts_seen"]:
            print(f"  artifacts_seen: {', '.join(task['artifacts_seen'])}")
        print(f"  judge_summary: {task['judge_summary']}")


def _print_compare_report(compared: list[dict]) -> None:
    print("RoughBench compare (lower is better)")
    for item in compared:
        report = item["report"]
        task_bits = ", ".join(
            f"{task['task_id']}={task['total_penalty']}" for task in report["task_results"]
        )
        if not task_bits:
            task_bits = "none"
        score_line = f"{report['roughbench_demerits']}"
        if report.get("suite_max_demerits") is not None:
            pct = report.get("suite_demerit_pct")
            pct_bit = f", {pct}% of suite max" if pct is not None else ""
            score_line = f"{report['roughbench_demerits']} / {report['suite_max_demerits']}{pct_bit}"
        print()
        print(f"{item['subject_id']} [{item['title']}]")
        print(f"  provider: {item['provider']}")
        print(f"  model: {item['model']}")
        print(
            "  status: "
            f"{item['status']} "
            f"({item['completed_task_count']}/{item['requested_task_count']} completed, "
            f"{item['failed_task_count']} failed)"
        )
        if item.get("reasoning_effort"):
            print(f"  reasoning_effort: {item['reasoning_effort']}")
        if item.get("base_url"):
            print(f"  base_url: {item['base_url']}")
        print(f"  demerits: {score_line}")
        print(f"  summary: {report['summary']}")
        print(f"  task_penalties: {task_bits}")
        if item["failures"]:
            failure_bits = ", ".join(
                f"{failure['task_id']} ({failure['error_type']})" for failure in item["failures"]
            )
            print(f"  failures: {failure_bits}")


def _launch_background_job(raw_argv: list[str], args: argparse.Namespace) -> int:
    jobs_dir = args.jobs_dir
    metadata = create_job(jobs_dir=jobs_dir, argv=raw_argv, cwd=Path.cwd())
    child_argv = _background_child_argv(raw_argv, jobs_dir=jobs_dir, job_id=metadata["job_id"])
    launched = launch_job(
        jobs_dir=jobs_dir,
        job_id=metadata["job_id"],
        child_argv=child_argv,
        cwd=Path.cwd(),
    )
    print(
        f"Queued {args.command} as {launched['job_id']} "
        f"(pid {launched['pid']}). Jobs dir: {jobs_dir}"
    )
    return 0


def _background_child_argv(raw_argv: list[str], *, jobs_dir: Path, job_id: str) -> list[str]:
    child_argv: list[str] = []
    skip_next = False
    saw_jobs_dir = False
    for index, token in enumerate(raw_argv):
        if skip_next:
            skip_next = False
            continue
        if token == "--background":
            continue
        if token == "--job-id":
            skip_next = True
            continue
        if token == "--jobs-dir":
            saw_jobs_dir = True
        child_argv.append(token)
        if token == "--jobs-dir" and index + 1 < len(raw_argv):
            child_argv.append(raw_argv[index + 1])
            skip_next = True
    if not saw_jobs_dir:
        child_argv.extend(["--jobs-dir", str(jobs_dir)])
    child_argv.extend(["--job-id", job_id])
    return child_argv


def _print_jobs(args: argparse.Namespace) -> int:
    if args.job_id:
        payload = inspect_job(jobs_dir=args.jobs_dir, job_id=args.job_id, log_lines=args.log_lines)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"{payload['job_id']} [{payload['status']}]")
            print(f"  pid: {payload.get('pid')}")
            print(f"  pid_running: {payload.get('pid_running')}")
            print(f"  created_at: {payload.get('created_at')}")
            if payload.get("started_at"):
                print(f"  started_at: {payload['started_at']}")
            if payload.get("finished_at"):
                print(f"  finished_at: {payload['finished_at']}")
            if payload.get("exit_code") is not None:
                print(f"  exit_code: {payload['exit_code']}")
            print(f"  log_path: {payload['log_path']}")
            if payload["log_tail"]:
                print("  log_tail:")
                for line in payload["log_tail"]:
                    print(f"    {line}")
        return 0

    payload = list_jobs(args.jobs_dir)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        if not payload:
            print(f"No jobs found in {args.jobs_dir}")
            return 0
        for item in payload:
            print(
                f"{item['job_id']}\t{item['status']}\t"
                f"pid={item.get('pid')}\talive={item.get('pid_running')}\t"
                f"created={item.get('created_at')}"
            )
    return 0


def _execute_task(task: TaskDefinition, args: argparse.Namespace) -> int:
    if args.work_dir is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        args.work_dir = Path("runs") / task.id / f"exec-{timestamp}"

    scorecard, execution_result = evaluate_hf_datasets_submission(
        task,
        submission_dir=args.submission_dir,
        input_dir=args.input_dir,
        work_dir=args.work_dir,
        image=args.docker_image,
        memory=args.memory,
        cpus=args.cpus,
        timeout_seconds=args.timeout_seconds,
        soft_time_seconds=args.soft_time_seconds,
        rebuild_image=args.rebuild_image,
        no_build=args.no_build,
        include_hidden=not args.visible_only,
    )

    payload = {
        "task_id": task.id,
        "title": task.title,
        "submission_dir": str(Path(args.submission_dir).resolve()),
        "input_dir": str(Path(args.input_dir).resolve()),
        "work_dir": str(Path(args.work_dir).resolve()),
        "scorecard": scorecard.to_dict(),
        "execution": execution_result.to_dict(),
    }

    if args.output:
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        _print_execution_report(payload)

    return 0


def _print_execution_report(payload: dict) -> None:
    scorecard = payload["scorecard"]
    execution = payload["execution"]
    print(f"Task: {payload['task_id']} [{payload['title']}]")
    print(f"Submission: {payload['submission_dir']}")
    print(f"Input: {payload['input_dir']}")
    print(f"Work dir: {payload['work_dir']}")
    print(f"Total penalty: {scorecard['total_penalty']}")
    print(f"Summary: {scorecard['judge_summary']}")
    print(
        f"Docker status: {execution['status']} "
        f"(exit_code={execution['exit_code']}, timed_out={execution['timed_out']}, "
        f"runtime={execution['wall_time_seconds']})"
    )
    print(f"Logs: {execution['logs_dir']}")
    tier_bits = []
    for tier in execution.get("details", {}).get("tiers", []):
        tier_bits.append(
            f"{tier['name']}="
            f"{'ok' if tier['output_verified'] else 'fail'}"
            f"({tier['wall_time_seconds']})"
        )
    if tier_bits:
        print(f"Tiers: {', '.join(tier_bits)}")
