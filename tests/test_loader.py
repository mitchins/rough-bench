from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from roughbench.tasks.loader import load_task


class LoadTaskTests(unittest.TestCase):
    def test_load_task_reads_explicit_family_and_counted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task_dir = Path(temp_dir) / "demo_task"
            task_dir.mkdir()
            (task_dir / "prompt.txt").write_text("Prompt body\n", encoding="utf-8")
            (task_dir / "task.yaml").write_text(
                textwrap.dedent(
                    """
                    id: demo_task
                    title: Demo
                    domain: demo_domain
                    family: demo_family
                    intent: Demo intent
                    counted: false
                    expected_artifacts:
                      - report.md
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (task_dir / "rubric.yaml").write_text(
                textwrap.dedent(
                    """
                    signals:
                      - id: s1
                        description: Has alpha
                        any: [alpha]
                    penalties:
                      - id: p1
                        description: Missing beta
                        points: 2
                        missing_any: [beta]
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            task = load_task(task_dir)

        self.assertEqual(task.id, "demo_task")
        self.assertEqual(task.family, "demo_family")
        self.assertFalse(task.counted)
        self.assertEqual(task.prompt, "Prompt body")
        self.assertEqual(task.expected_artifacts, ("report.md",))
        self.assertEqual(task.rubric.signals[0].id, "s1")
        self.assertEqual(task.rubric.penalties[0].id, "p1")

    def test_load_task_defaults_family_to_domain_and_counted_to_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task_dir = Path(temp_dir) / "demo_task"
            task_dir.mkdir()
            (task_dir / "prompt.txt").write_text("Prompt body\n", encoding="utf-8")
            (task_dir / "task.yaml").write_text(
                textwrap.dedent(
                    """
                    id: demo_task
                    title: Demo
                    domain: demo_domain
                    intent: Demo intent
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (task_dir / "rubric.yaml").write_text("{}\n", encoding="utf-8")

            task = load_task(task_dir)

        self.assertEqual(task.family, "demo_domain")
        self.assertTrue(task.counted)

    def test_load_task_requires_a_prompt_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task_dir = Path(temp_dir) / "demo_task"
            task_dir.mkdir()
            (task_dir / "task.yaml").write_text(
                textwrap.dedent(
                    """
                    id: demo_task
                    title: Demo
                    domain: demo_domain
                    intent: Demo intent
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (task_dir / "rubric.yaml").write_text("{}\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing prompt.txt and task.yaml prompt"):
                load_task(task_dir)


if __name__ == "__main__":
    unittest.main()
