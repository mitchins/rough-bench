from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from roughbench.tasks.models import TaskDefinition


@dataclass(frozen=True)
class Artifact:
    path: Path
    relative_path: str
    text: str | None = None


@dataclass(frozen=True)
class TaskOutput:
    task_id: str
    source_dir: Path
    answer_text: str
    artifacts: tuple[Artifact, ...] = ()

    @property
    def artifact_names(self) -> tuple[str, ...]:
        return tuple(artifact.relative_path for artifact in self.artifacts)

    @property
    def artifact_text(self) -> str:
        return "\n\n".join(
            artifact.text for artifact in self.artifacts if artifact.text is not None
        ).strip()

    @property
    def combined_text(self) -> str:
        parts = [self.answer_text]
        if self.artifact_text:
            parts.append(self.artifact_text)
        return "\n\n".join(part for part in parts if part).strip()


class Runner(Protocol):
    def collect(self, task: TaskDefinition) -> TaskOutput:
        ...
