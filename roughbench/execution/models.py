from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from roughbench.judging.scorecard import PenaltyHit, SignalHit


@dataclass(frozen=True)
class ExecutionResult:
    task_id: str
    status: str
    summary: str
    image: str
    command: tuple[str, ...]
    memory: str
    cpus: str
    timeout_seconds: int
    soft_time_seconds: float
    wall_time_seconds: float | None
    exit_code: int | None
    timed_out: bool
    output_verified: bool
    frozen_submission_dir: Path
    output_dir: Path
    scratch_dir: Path
    logs_dir: Path
    stdout_log: Path
    stderr_log: Path
    build_log: Path | None = None
    image_built: bool = False
    triggered_penalties: tuple[PenaltyHit, ...] = ()
    passed_signals: tuple[SignalHit, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def total_penalty(self) -> int:
        return sum(item.points for item in self.triggered_penalties)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "summary": self.summary,
            "image": self.image,
            "command": list(self.command),
            "memory": self.memory,
            "cpus": self.cpus,
            "timeout_seconds": self.timeout_seconds,
            "soft_time_seconds": self.soft_time_seconds,
            "wall_time_seconds": self.wall_time_seconds,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "output_verified": self.output_verified,
            "total_penalty": self.total_penalty,
            "triggered_penalties": [item.to_dict() for item in self.triggered_penalties],
            "passed_signals": [item.to_dict() for item in self.passed_signals],
            "frozen_submission_dir": str(self.frozen_submission_dir),
            "output_dir": str(self.output_dir),
            "scratch_dir": str(self.scratch_dir),
            "logs_dir": str(self.logs_dir),
            "stdout_log": str(self.stdout_log),
            "stderr_log": str(self.stderr_log),
            "build_log": str(self.build_log) if self.build_log is not None else None,
            "image_built": self.image_built,
            "details": self.details,
        }
