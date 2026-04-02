from __future__ import annotations

from typing import Protocol

from roughbench.judging.scorecard import TaskScorecard
from roughbench.runners.base import TaskOutput
from roughbench.tasks.models import TaskDefinition


class Judge(Protocol):
    def evaluate(self, task: TaskDefinition, output: TaskOutput) -> TaskScorecard:
        ...
