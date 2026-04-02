from __future__ import annotations

import unittest

from roughbench.judging.scorecard import BenchmarkReport, PenaltyHit, SignalHit, TaskScorecard


class TaskScorecardTests(unittest.TestCase):
    def test_round_trips_through_dict(self) -> None:
        scorecard = TaskScorecard(
            task_id="task",
            title="Task",
            total_penalty=4,
            max_penalty_possible=10,
            triggered_penalties=(PenaltyHit(id="p1", points=4, description="Penalty"),),
            passed_signals=(SignalHit(id="s1", description="Signal"),),
            judge_summary="Summary",
            artifacts_seen=("artifact.py",),
        )

        restored = TaskScorecard.from_dict(scorecard.to_dict())

        self.assertEqual(restored, scorecard)
        self.assertEqual(scorecard.demerit_pct, 40.0)

    def test_demerit_pct_is_none_without_denominator(self) -> None:
        self.assertIsNone(
            TaskScorecard(
                task_id="task",
                title="Task",
                total_penalty=1,
                max_penalty_possible=None,
                triggered_penalties=(),
                passed_signals=(),
                judge_summary="Summary",
            ).demerit_pct
        )
        self.assertIsNone(
            TaskScorecard(
                task_id="task",
                title="Task",
                total_penalty=1,
                max_penalty_possible=0,
                triggered_penalties=(),
                passed_signals=(),
                judge_summary="Summary",
            ).demerit_pct
        )


class BenchmarkReportTests(unittest.TestCase):
    def test_suite_demerit_pct_uses_suite_max(self) -> None:
        report = BenchmarkReport(
            roughbench_demerits=5,
            judged_at="2025-01-01T00:00:00Z",
            summary="Summary",
            task_results=(),
            suite_max_demerits=20,
        )

        payload = report.to_dict()

        self.assertEqual(report.roughbench_score, 5)
        self.assertEqual(report.suite_demerit_pct, 25.0)
        self.assertEqual(payload["suite_demerit_pct"], 25.0)


if __name__ == "__main__":
    unittest.main()
