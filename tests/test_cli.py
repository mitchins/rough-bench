from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from roughbench.cli import _evaluate_task_with_retries, _run_compare_subject, main
from roughbench.judging import TaskScorecard
from roughbench.runners import TaskOutput
from roughbench.subjects import SubjectDefinition
from roughbench.tasks.models import TaskDefinition


ROOT = Path(__file__).resolve().parents[1]


class _RetryRunner:
    def __init__(self) -> None:
        self.calls = 0

    def collect(self, task: TaskDefinition) -> TaskOutput:
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("timed out")
        return TaskOutput(task_id=task.id, source_dir=Path("live") / task.id, answer_text="ok")


class _PartialCompareRunner:
    def __init__(self) -> None:
        self.calls = 0

    def collect(self, task: TaskDefinition) -> TaskOutput:
        self.calls += 1
        if task.id == "task-b":
            raise ConnectionError("subject unreachable")
        return TaskOutput(task_id=task.id, source_dir=Path("live") / task.id, answer_text="ok")


class _StubJudge:
    def evaluate(self, task: TaskDefinition, output: TaskOutput) -> TaskScorecard:
        return TaskScorecard(
            task_id=task.id,
            title=task.title,
            total_penalty=0,
            max_penalty_possible=3,
            triggered_penalties=(),
            passed_signals=(),
            judge_summary=f"Scored {output.task_id}",
        )


class CliSmokeTests(unittest.TestCase):
    def test_list_command_prints_known_task(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["list", "--benchmarks-dir", str(ROOT / "benchmarks")])

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("agent_task_spec_not_handwave", output)
        self.assertIn("agentic_specification", output)

    def test_demo_json_supports_single_task_and_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "demo-report.json"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "demo",
                        "--benchmarks-dir",
                        str(ROOT / "benchmarks"),
                        "--examples-dir",
                        str(ROOT / "examples"),
                        "--task",
                        "critique_without_sandwich",
                        "--json",
                        "--output",
                        str(output_path),
                    ]
                )

            payload = json.loads(stdout.getvalue())
            file_payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["roughbench_demerits"], file_payload["roughbench_demerits"])
        self.assertEqual(len(payload["task_results"]), 1)
        self.assertEqual(payload["task_results"][0]["task_id"], "critique_without_sandwich")

    def test_run_json_scores_local_responses_dir(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(
                [
                    "run",
                    "--benchmarks-dir",
                    str(ROOT / "benchmarks"),
                    "--responses-dir",
                    str(ROOT / "examples"),
                    "--task",
                    "lang_japanese_translation_kaze_no_tayori",
                    "--json",
                ]
            )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(payload["task_results"]), 1)
        self.assertEqual(payload["task_results"][0]["task_id"], "lang_japanese_translation_kaze_no_tayori")

    def test_jobs_json_lists_persisted_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            job_dir = jobs_dir / "job-123"
            job_dir.mkdir(parents=True)
            (job_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "job_id": "job-123",
                        "status": "queued",
                        "argv": ["compare", "--background"],
                        "cwd": str(ROOT),
                        "created_at": "2026-01-01T00:00:00+00:00",
                        "started_at": None,
                        "finished_at": None,
                        "pid": None,
                        "exit_code": None,
                        "log_path": str(job_dir / "job.log"),
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["jobs", "--jobs-dir", str(jobs_dir), "--json"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload[0]["job_id"], "job-123")

    def test_run_background_queues_job(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir) / ".roughbench_jobs"
            stdout = io.StringIO()
            with patch("roughbench.cli.create_job") as create_job_mock, patch(
                "roughbench.cli.launch_job"
            ) as launch_job_mock:
                create_job_mock.return_value = {"job_id": "job-123"}
                launch_job_mock.return_value = {"job_id": "job-123", "pid": 999}
                with contextlib.redirect_stdout(stdout):
                    exit_code = main(
                        [
                            "run",
                            "--benchmarks-dir",
                            str(ROOT / "benchmarks"),
                            "--responses-dir",
                            str(ROOT / "examples"),
                            "--task",
                            "critique_without_sandwich",
                            "--background",
                            "--jobs-dir",
                            str(jobs_dir),
                        ]
                    )

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Queued run as job-123", output)
        create_job_mock.assert_called_once()
        launch_job_mock.assert_called_once()

    def test_evaluate_task_with_retries_retries_then_succeeds(self) -> None:
        task = TaskDefinition(
            id="task-a",
            title="Task A",
            domain="demo",
            prompt="Prompt",
            intent="Intent",
        )
        subject = SubjectDefinition(id="demo-subject", title="Demo subject", model="demo/model")
        runner = _RetryRunner()
        judge = _StubJudge()

        with patch("roughbench.cli.time.sleep") as sleep_mock:
            scorecard, failure = _evaluate_task_with_retries(
                task,
                runner,
                judge,
                subject=subject,
                retry_attempts=2,
                retry_backoff_seconds=1.5,
            )

        self.assertIsNotNone(scorecard)
        self.assertIsNone(failure)
        self.assertEqual(runner.calls, 2)
        sleep_mock.assert_called_once_with(1.5)

    def test_run_compare_subject_persists_partial_progress(self) -> None:
        tasks = [
            TaskDefinition(
                id="task-a",
                title="Task A",
                domain="demo",
                prompt="Prompt A",
                intent="Intent A",
            ),
            TaskDefinition(
                id="task-b",
                title="Task B",
                domain="demo",
                prompt="Prompt B",
                intent="Intent B",
            ),
        ]
        subject = SubjectDefinition(
            id="demo-subject",
            title="Demo subject",
            model="demo/model",
            storage_name="demo_subject",
        )
        judge = _StubJudge()

        with tempfile.TemporaryDirectory() as temp_dir:
            args = type(
                "Args",
                (),
                {
                    "save_runs_dir": Path(temp_dir),
                    "retry_attempts": 1,
                    "retry_backoff_seconds": 0.0,
                    "fail_fast": False,
                },
            )()
            with patch("roughbench.cli._runner_for_subject", return_value=_PartialCompareRunner()):
                payload = _run_compare_subject(tasks, subject, args, judge=judge)

            progress_path = Path(temp_dir) / "demo_subject" / ".roughbench_compare_subject.json"
            progress_payload = json.loads(progress_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["completed_task_count"], 1)
        self.assertEqual(payload["failed_task_count"], 1)
        self.assertEqual(len(payload["report"]["task_results"]), 1)
        self.assertEqual(payload["failures"][0]["task_id"], "task-b")
        self.assertEqual(progress_payload["status"], "partial")
        self.assertEqual(progress_payload["failed_task_count"], 1)


if __name__ == "__main__":
    unittest.main()
