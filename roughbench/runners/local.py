from __future__ import annotations

from pathlib import Path

from roughbench.runners.base import Artifact, TaskOutput
from roughbench.tasks.models import TaskDefinition


TEXT_EXTENSIONS = {
    ".csv",
    ".json",
    ".md",
    ".py",
    ".sql",
    ".sh",
    ".toml",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}

RESPONSE_NAMES = ("response.md", "response.txt", "answer.md", "answer.txt")


class LocalDirectoryRunner:
    def __init__(self, responses_dir: Path | str) -> None:
        self.responses_dir = Path(responses_dir)

    def collect(self, task: TaskDefinition) -> TaskOutput:
        task_dir = self.responses_dir / task.id
        return collect_task_output(task.id, task_dir)


def collect_task_output(task_id: str, task_dir: Path | str) -> TaskOutput:
    task_dir = Path(task_dir)
    if not task_dir.exists():
        return TaskOutput(task_id=task_id, source_dir=task_dir, answer_text="")

    answer_path = _detect_answer_path(task_dir)
    answer_text = ""
    if answer_path is not None:
        answer_text = answer_path.read_text(encoding="utf-8").strip()

    artifacts: list[Artifact] = []
    for path in sorted(path for path in task_dir.rglob("*") if path.is_file()):
        if answer_path is not None and path == answer_path:
            continue
        relative_path = path.relative_to(task_dir).as_posix()
        text = None
        if path.suffix.lower() in TEXT_EXTENSIONS:
            text = path.read_text(encoding="utf-8", errors="ignore")
        artifacts.append(Artifact(path=path, relative_path=relative_path, text=text))

    return TaskOutput(
        task_id=task_id,
        source_dir=task_dir,
        answer_text=answer_text,
        artifacts=tuple(artifacts),
    )


def _detect_answer_path(task_dir: Path) -> Path | None:
    for name in RESPONSE_NAMES:
        candidate = task_dir / name
        if candidate.exists():
            return candidate

    top_level_files = sorted(path for path in task_dir.iterdir() if path.is_file())
    for path in top_level_files:
        if path.suffix.lower() in TEXT_EXTENSIONS:
            return path
    return None
