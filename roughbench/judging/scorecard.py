from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PenaltyHit:
    id: str
    points: int
    description: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "points": self.points,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PenaltyHit":
        return cls(
            id=str(data["id"]),
            points=int(data["points"]),
            description=str(data["description"]),
        )


@dataclass(frozen=True)
class SignalHit:
    id: str
    description: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SignalHit":
        return cls(
            id=str(data["id"]),
            description=str(data["description"]),
        )


@dataclass(frozen=True)
class TaskScorecard:
    task_id: str
    title: str
    total_penalty: int
    max_penalty_possible: int | None
    triggered_penalties: tuple[PenaltyHit, ...]
    passed_signals: tuple[SignalHit, ...]
    judge_summary: str
    artifacts_seen: tuple[str, ...] = ()

    @property
    def demerit_pct(self) -> float | None:
        if self.max_penalty_possible in (None, 0):
            return None
        return round((self.total_penalty / self.max_penalty_possible) * 100.0, 1)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "total_penalty": self.total_penalty,
            "max_penalty_possible": self.max_penalty_possible,
            "demerit_pct": self.demerit_pct,
            "triggered_penalties": [item.to_dict() for item in self.triggered_penalties],
            "passed_signals": [item.to_dict() for item in self.passed_signals],
            "judge_summary": self.judge_summary,
            "artifacts_seen": list(self.artifacts_seen),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskScorecard":
        return cls(
            task_id=str(data["task_id"]),
            title=str(data["title"]),
            total_penalty=int(data["total_penalty"]),
            max_penalty_possible=(
                None
                if data.get("max_penalty_possible") is None
                else int(data["max_penalty_possible"])
            ),
            triggered_penalties=tuple(
                PenaltyHit.from_dict(item)
                for item in data.get("triggered_penalties", [])
            ),
            passed_signals=tuple(
                SignalHit.from_dict(item)
                for item in data.get("passed_signals", [])
            ),
            judge_summary=str(data.get("judge_summary", "")),
            artifacts_seen=tuple(str(item) for item in data.get("artifacts_seen", [])),
        )


@dataclass(frozen=True)
class BenchmarkReport:
    roughbench_demerits: int
    judged_at: str
    summary: str
    task_results: tuple[TaskScorecard, ...]
    suite_max_demerits: int | None = None
    lower_is_better: bool = True

    @property
    def roughbench_score(self) -> int:
        return self.roughbench_demerits

    @property
    def suite_demerit_pct(self) -> float | None:
        if self.suite_max_demerits in (None, 0):
            return None
        return round((self.roughbench_demerits / self.suite_max_demerits) * 100.0, 1)

    def to_dict(self) -> dict:
        return {
            "roughbench_demerits": self.roughbench_demerits,
            "roughbench_score": self.roughbench_score,
            "suite_max_demerits": self.suite_max_demerits,
            "suite_demerit_pct": self.suite_demerit_pct,
            "lower_is_better": self.lower_is_better,
            "judged_at": self.judged_at,
            "summary": self.summary,
            "task_results": [item.to_dict() for item in self.task_results],
        }
