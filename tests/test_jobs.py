from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from roughbench.jobs import create_job, inspect_job, list_jobs, mark_finished, mark_running


class JobPersistenceTests(unittest.TestCase):
    def test_create_and_update_job_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            metadata = create_job(
                jobs_dir=jobs_dir,
                argv=["compare", "--background"],
                cwd=Path("/tmp/work"),
            )
            self.assertEqual(metadata["status"], "queued")

            running = mark_running(jobs_dir=jobs_dir, job_id=metadata["job_id"], pid=12345)
            self.assertEqual(running["status"], "running")
            self.assertEqual(running["pid"], 12345)

            finished = mark_finished(jobs_dir=jobs_dir, job_id=metadata["job_id"], exit_code=0)
            self.assertEqual(finished["status"], "completed")
            self.assertEqual(finished["exit_code"], 0)

    def test_inspect_job_includes_log_tail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            metadata = create_job(
                jobs_dir=jobs_dir,
                argv=["run", "--background"],
                cwd=Path("/tmp/work"),
            )
            job_dir = jobs_dir / metadata["job_id"]
            log_path = Path(metadata["log_path"])
            log_path.write_text("line1\nline2\nline3\n", encoding="utf-8")

            payload = inspect_job(jobs_dir=jobs_dir, job_id=metadata["job_id"], log_lines=2)

        self.assertEqual(payload["log_tail"], ["line2", "line3"])

    def test_list_jobs_reads_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            first = create_job(jobs_dir=jobs_dir, argv=["run"], cwd=Path("/tmp/a"))
            second = create_job(jobs_dir=jobs_dir, argv=["compare"], cwd=Path("/tmp/b"))
            mark_finished(jobs_dir=jobs_dir, job_id=first["job_id"], exit_code=1)
            mark_running(jobs_dir=jobs_dir, job_id=second["job_id"], pid=1)

            payload = list_jobs(jobs_dir)

        self.assertEqual(len(payload), 2)
        self.assertTrue(all("job_id" in item for item in payload))


if __name__ == "__main__":
    unittest.main()
