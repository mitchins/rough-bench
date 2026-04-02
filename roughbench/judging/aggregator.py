from __future__ import annotations

from datetime import datetime, UTC
from typing import Sequence

from roughbench.judging.scorecard import BenchmarkReport, TaskScorecard


def aggregate_scorecards(scorecards: Sequence[TaskScorecard]) -> BenchmarkReport:
    total_penalty = sum(item.total_penalty for item in scorecards)
    suite_max_demerits: int | None = None
    if scorecards and all(item.max_penalty_possible is not None for item in scorecards):
        suite_max_demerits = sum(int(item.max_penalty_possible or 0) for item in scorecards)
    penalized_tasks = sum(1 for item in scorecards if item.total_penalty > 0)
    passed_signals = sum(len(item.passed_signals) for item in scorecards)
    summary = (
        f"{penalized_tasks} of {len(scorecards)} task(s) triggered penalties; "
        f"{passed_signals} signal(s) passed."
    )
    return BenchmarkReport(
        roughbench_demerits=total_penalty,
        judged_at=datetime.now(UTC).isoformat(),
        summary=summary,
        task_results=tuple(scorecards),
        suite_max_demerits=suite_max_demerits,
    )
