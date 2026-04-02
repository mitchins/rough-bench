from __future__ import annotations

import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from roughbench.runners.openai_compatible import from_env
from roughbench.subjects import load_subjects


class SubjectLoadingTests(unittest.TestCase):
    def test_load_subjects_reads_timeout_and_direct_answer_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            subjects_path = Path(temp_dir) / "subjects.yaml"
            subjects_path.write_text(
                textwrap.dedent(
                    """
                    subjects:
                      - id: local_subject
                        title: Local subject
                        provider: openai-compatible
                        base_url: http://localhost:8000/v1
                        model: demo/model
                        api_key: dummy
                        timeout_seconds: 240
                        reasoning_effort: low
                        direct_answer_first: true
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            subjects = load_subjects(subjects_path)

        self.assertEqual(len(subjects), 1)
        self.assertEqual(subjects[0].timeout_seconds, 240)
        self.assertEqual(subjects[0].reasoning_effort, "low")
        self.assertTrue(subjects[0].direct_answer_first)

    def test_live_runner_from_env_reads_timeout_and_direct_answer_flags(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ROUGHBENCH_TIMEOUT_SECONDS": "240",
                "ROUGHBENCH_REASONING_EFFORT": "low",
                "ROUGHBENCH_DIRECT_ANSWER_FIRST": "1",
            },
            clear=False,
        ):
            runner = from_env(
                model="demo/model",
                base_url="http://localhost:8000/v1",
                api_key="dummy",
            )

        self.assertEqual(runner.timeout_seconds, 240)
        self.assertEqual(runner.reasoning_effort, "low")
        self.assertTrue(runner.direct_answer_first)


if __name__ == "__main__":
    unittest.main()
