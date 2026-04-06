from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import os
from pathlib import Path
from typing import Iterable
import re
from urllib.parse import urlparse

import yaml


DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_LAN_TIMEOUT_SECONDS = 600
DEFAULT_BALANCED_AUTO_REASONING_EFFORT = "medium"
BALANCED_AUTO_REASONING_EFFORT_OVERRIDES: dict[str, str] = {
    "swe_scraper_persistent_resumable": "high",
    "ux_multirole_service_hub_ia": "high",
    "nutrition_multi_component_meal_servings": "high",
    "retrieval_local_search_stack_practicality": "high",
    "train_inference_mismatch_audit": "high",
}
BALANCED_AUTO_MAX_TOKENS_OVERRIDES: dict[str, int] = {
    "swe_scraper_persistent_resumable": 50000,
    "nutrition_multi_component_meal_servings": 50000,
    "train_inference_mismatch_audit": 50000,
}


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


def _as_reasoning_effort_overrides(value: object) -> tuple[tuple[str, str], ...]:
    if value is None:
        return ()
    if not isinstance(value, dict):
        raise ValueError("reasoning_effort_overrides must be a mapping of task_id -> effort")
    pairs: list[tuple[str, str]] = []
    for task_id, effort in value.items():
        key = str(task_id).strip()
        level = str(effort).strip()
        if not key or not level:
            continue
        pairs.append((key, level))
    return tuple(sorted(pairs))


def _as_max_tokens_overrides(value: object) -> tuple[tuple[str, int], ...]:
    if value is None:
        return ()
    if not isinstance(value, dict):
        raise ValueError("max_tokens_overrides must be a mapping of task_id -> integer")
    pairs: list[tuple[str, int]] = []
    for task_id, max_tokens in value.items():
        key = str(task_id).strip()
        if not key:
            continue
        level = int(max_tokens)
        if level <= 0:
            continue
        pairs.append((key, level))
    return tuple(sorted(pairs))


def resolve_reasoning_effort(
    *,
    base_effort: str,
    profile: str,
    overrides: tuple[tuple[str, str], ...],
    task_id: str,
) -> str:
    for override_task_id, override_effort in overrides:
        if override_task_id == task_id:
            return override_effort
    if profile == "balanced_auto":
        if task_id in BALANCED_AUTO_REASONING_EFFORT_OVERRIDES:
            return BALANCED_AUTO_REASONING_EFFORT_OVERRIDES[task_id]
        return base_effort or DEFAULT_BALANCED_AUTO_REASONING_EFFORT
    return base_effort


def resolve_max_tokens(
    *,
    base_max_tokens: int,
    profile: str,
    overrides: tuple[tuple[str, int], ...],
    task_id: str,
) -> int:
    for override_task_id, override_max_tokens in overrides:
        if override_task_id == task_id:
            return override_max_tokens
    if profile == "balanced_auto":
        return BALANCED_AUTO_MAX_TOKENS_OVERRIDES.get(task_id, base_max_tokens)
    return base_max_tokens


def is_lan_base_url(base_url: str) -> bool:
    if not base_url:
        return False
    parsed = urlparse(base_url if "://" in base_url else f"http://{base_url}")
    host = (parsed.hostname or "").strip().casefold()
    if not host:
        return False
    if host == "localhost" or host.endswith(".local"):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local


def default_timeout_seconds_for_endpoint(*, provider: str, base_url: str) -> int:
    if provider == "openai-compatible" and is_lan_base_url(base_url):
        return DEFAULT_LAN_TIMEOUT_SECONDS
    return DEFAULT_TIMEOUT_SECONDS


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
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    direct_answer_first: bool = False
    reasoning_effort: str = ""
    reasoning_effort_profile: str = ""
    reasoning_effort_overrides: tuple[tuple[str, str], ...] = ()
    max_tokens_profile: str = ""
    max_tokens_overrides: tuple[tuple[str, int], ...] = ()
    thinking_type: str = ""
    params_billion: float | None = None
    params_billion_backbone: float | None = None
    loaded_size_gb: float | None = None
    notes: str = ""
    storage_name: str = ""

    def reasoning_effort_for_task(self, task_id: str) -> str:
        return resolve_reasoning_effort(
            base_effort=self.reasoning_effort,
            profile=self.reasoning_effort_profile,
            overrides=self.reasoning_effort_overrides,
            task_id=task_id,
        )

    def max_tokens_for_task(self, task_id: str) -> int:
        return resolve_max_tokens(
            base_max_tokens=self.max_tokens,
            profile=self.max_tokens_profile or self.reasoning_effort_profile,
            overrides=self.max_tokens_overrides,
            task_id=task_id,
        )

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
        provider = str(data.get("provider", "openai-compatible"))
        base_url = str(data.get("base_url", ""))
        timeout_seconds = int(
            data.get(
                "timeout_seconds",
                default_timeout_seconds_for_endpoint(provider=provider, base_url=base_url),
            )
        )
        return cls(
            id=subject_id,
            title=title,
            provider=provider,
            base_url=base_url,
            model=str(data["model"]),
            api_key=str(data.get("api_key", "")),
            api_key_env=str(data.get("api_key_env", "")),
            temperature=float(data.get("temperature", 0.0)),
            max_tokens=int(data.get("max_tokens", 2000)),
            timeout_seconds=timeout_seconds,
            direct_answer_first=bool(data.get("direct_answer_first", False)),
            reasoning_effort=str(data.get("reasoning_effort", "")),
            reasoning_effort_profile=str(data.get("reasoning_effort_profile", "")),
            reasoning_effort_overrides=_as_reasoning_effort_overrides(
                data.get("reasoning_effort_overrides")
            ),
            max_tokens_profile=str(
                data.get("max_tokens_profile", data.get("reasoning_effort_profile", ""))
            ),
            max_tokens_overrides=_as_max_tokens_overrides(data.get("max_tokens_overrides")),
            thinking_type=str(data.get("thinking_type", "")),
            params_billion=(
                None if data.get("params_billion") in (None, "") else float(data.get("params_billion"))
            ),
            params_billion_backbone=(
                None
                if data.get("params_billion_backbone") in (None, "")
                else float(data.get("params_billion_backbone"))
            ),
            loaded_size_gb=(
                None if data.get("loaded_size_gb") in (None, "") else float(data.get("loaded_size_gb"))
            ),
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
