from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable
import re

import yaml


def _read_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    return slug or "subject"


@dataclass(frozen=True)
class SubjectDefinition:
    id: str
    title: str
    model: str
    provider: str = "openai-compatible"
    base_url: str = ""
    api_key: str = ""
    api_key_env: str = ""
    temperature: float = 0.0
    max_tokens: int = 2000
    timeout_seconds: int = 180
    direct_answer_first: bool = False
    reasoning_effort: str = ""
    thinking_type: str = ""
    notes: str = ""
    storage_name: str = ""

    @property
    def resolved_api_key(self) -> str:
        if self.api_key.startswith("env:"):
            env_name = self.api_key.split(":", 1)[1].strip()
            return os.getenv(env_name, "")
        if self.api_key:
            return self.api_key
        if self.api_key_env:
            return os.getenv(self.api_key_env, "")
        if self.provider == "openai":
            return os.getenv("OPENAI_API_KEY", "")
        if self.provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY", "")
        return "dummy"

    @classmethod
    def from_mapping(cls, data: dict) -> "SubjectDefinition":
        subject_id = str(data["id"])
        title = str(data.get("title", subject_id))
        storage_name = str(data.get("storage_name", _slugify(subject_id)))
        return cls(
            id=subject_id,
            title=title,
            provider=str(data.get("provider", "openai-compatible")),
            base_url=str(data.get("base_url", "")),
            model=str(data["model"]),
            api_key=str(data.get("api_key", "")),
            api_key_env=str(data.get("api_key_env", "")),
            temperature=float(data.get("temperature", 0.0)),
            max_tokens=int(data.get("max_tokens", 2000)),
            timeout_seconds=int(data.get("timeout_seconds", 180)),
            direct_answer_first=bool(data.get("direct_answer_first", False)),
            reasoning_effort=str(data.get("reasoning_effort", "")),
            thinking_type=str(data.get("thinking_type", "")),
            notes=str(data.get("notes", "")),
            storage_name=storage_name,
        )


def load_subjects(
    path: Path | str,
    subject_ids: Iterable[str] | None = None,
) -> list[SubjectDefinition]:
    yaml_path = Path(path)
    data = _read_yaml(yaml_path)
    wanted = set(subject_ids or [])
    subjects_data = data.get("subjects", [])
    if not isinstance(subjects_data, list):
        raise ValueError(f"{yaml_path} must define a top-level 'subjects' list")

    subjects: list[SubjectDefinition] = []
    for item in subjects_data:
        if not isinstance(item, dict):
            raise ValueError(f"{yaml_path} contains a non-mapping subject entry")
        subject = SubjectDefinition.from_mapping(item)
        if wanted and subject.id not in wanted:
            continue
        subjects.append(subject)

    return subjects
