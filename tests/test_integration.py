from __future__ import annotations

import unittest
from pathlib import Path

from roughbench.judging.evaluator import RuleBasedJudge
from roughbench.runners.local import LocalDirectoryRunner
from roughbench.tasks.loader import load_task


ROOT = Path(__file__).resolve().parents[1]


class RuleJudgeIntegrationTests(unittest.TestCase):
    def test_real_task_and_example_produce_a_scorecard(self) -> None:
        task = load_task(ROOT / "benchmarks" / "critique_without_sandwich")
        runner = LocalDirectoryRunner(ROOT / "examples")

        scorecard = RuleBasedJudge().evaluate(task, runner.collect(task))

        self.assertEqual(scorecard.task_id, "critique_without_sandwich")
        self.assertEqual(scorecard.title, task.title)
        self.assertGreaterEqual(scorecard.total_penalty, 0)
        self.assertGreater(scorecard.max_penalty_possible, 0)
        self.assertTrue(scorecard.triggered_penalties)
        self.assertTrue(scorecard.passed_signals)


if __name__ == "__main__":
    unittest.main()
