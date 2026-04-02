from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml

from roughbench.tasks.models import Rubric, TaskDefinition


def _read_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def _read_prompt(task_dir: Path, task_data: dict) -> tuple[str, Path]:
    prompt_path = task_dir / "prompt.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip(), prompt_path

    prompt_value = task_data.get("prompt")
    if not prompt_value:
        raise ValueError(f"{task_dir} is missing prompt.txt and task.yaml prompt")
    return str(prompt_value).strip(), prompt_path


def load_task(task_dir: Path) -> TaskDefinition:
    task_path = task_dir / "task.yaml"
    rubric_path = task_dir / "rubric.yaml"

    task_data = _read_yaml(task_path)
    rubric_data = _read_yaml(rubric_path)
    prompt, prompt_path = _read_prompt(task_dir, task_data)

    return TaskDefinition(
        id=str(task_data["id"]),
        title=str(task_data["title"]),
        domain=str(task_data["domain"]),
        family=str(task_data.get("family", task_data["domain"])),
        prompt=prompt,
        intent=str(task_data["intent"]),
        counted=bool(task_data.get("counted", True)),
        execution_backed=bool(task_data.get("execution_backed", False)),
        execution_gated_signals=tuple(
            str(item) for item in task_data.get("execution_gated_signals", [])
        ),
        latent_requirements=tuple(str(item) for item in task_data.get("latent_requirements", [])),
        hard_failures=tuple(str(item) for item in task_data.get("hard_failures", [])),
        strong_signals=tuple(str(item) for item in task_data.get("strong_signals", [])),
        penalty_notes=tuple(str(item) for item in task_data.get("penalties", [])),
        expected_artifacts=tuple(str(item) for item in task_data.get("expected_artifacts", [])),
        visible_constraints=tuple(
            str(item) for item in task_data.get("visible_constraints", [])
        ),
        hidden_stressors=tuple(
            str(item) for item in task_data.get("hidden_stressors", [])
        ),
        judge_instructions=str(task_data.get("judge_instructions", "")),
        path=task_dir,
        prompt_path=prompt_path,
        rubric_path=rubric_path,
        rubric=Rubric.from_mapping(rubric_data),
    )


def load_tasks(benchmarks_dir: Path | str, task_ids: Iterable[str] | None = None) -> list[TaskDefinition]:
    root = Path(benchmarks_dir)
    wanted = set(task_ids or [])

    tasks: list[TaskDefinition] = []
    for task_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if not (task_dir / "task.yaml").exists():
            continue
        task = load_task(task_dir)
        if wanted and task.id not in wanted:
            continue
        tasks.append(task)

    return tasks
