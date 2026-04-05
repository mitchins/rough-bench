from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from openai import OpenAI

from roughbench.runners.base import TaskOutput
from roughbench.runners.structured_output import build_task_output_from_text
from roughbench.subjects import resolve_max_tokens, resolve_reasoning_effort
from roughbench.tasks.models import TaskDefinition


def _source_dir(save_responses_dir: Path | None, task: TaskDefinition) -> Path:
    if save_responses_dir is None:
        return Path("live") / task.id
    return save_responses_dir / task.id


def _persist_metadata(save_responses_dir: Path | None, task: TaskDefinition, metadata: dict) -> None:
    if save_responses_dir is None:
        return
    meta_dir = save_responses_dir / ".roughbench_live_meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / f"{task.id}.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


@dataclass
class OpenAIRunner:
    model: str
    api_key: str
    temperature: float = 0.0
    max_tokens: int = 3000
    reasoning_effort: str = ""
    reasoning_effort_profile: str = ""
    reasoning_effort_overrides: tuple[tuple[str, str], ...] = ()
    max_tokens_profile: str = ""
    max_tokens_overrides: tuple[tuple[str, int], ...] = ()
    save_responses_dir: Path | None = None
    _client: OpenAI | None = field(default=None, init=False, repr=False)

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def run(self, prompt: str, *, task: TaskDefinition | None = None) -> tuple[str, dict]:
        resolved_reasoning_effort = self._reasoning_effort_for_task(task)
        resolved_max_tokens = self._max_tokens_for_task(task)
        create_kwargs: dict[str, object] = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": resolved_max_tokens,
        }
        if resolved_reasoning_effort:
            create_kwargs["reasoning"] = {"effort": resolved_reasoning_effort}
        elif self.temperature != 0.0:
            create_kwargs["temperature"] = self.temperature

        response = self.client.responses.create(**create_kwargs)
        usage = getattr(response, "usage", None)
        answer_text = (response.output_text or "").strip()
        metadata = {
            "attempts": [
                {
                    "model": self.model,
                    "prompt_variant": "original",
                    "finish_reason": getattr(response, "status", None),
                    "reasoning_effort": resolved_reasoning_effort,
                    "reasoning_effort_profile": self.reasoning_effort_profile,
                    "requested_max_tokens": resolved_max_tokens,
                    "max_tokens_profile": self.max_tokens_profile,
                    "content_present": bool(answer_text),
                    "content_len": len(answer_text),
                    "reasoning_present": False,
                    "reasoning_len": 0,
                    "request_id": getattr(response, "id", None),
                    "prompt_tokens": getattr(usage, "input_tokens", None),
                    "completion_tokens": getattr(usage, "output_tokens", None),
                    "total_tokens": getattr(usage, "total_tokens", None),
                    "reasoning_tokens": getattr(usage, "output_tokens_details", None) and getattr(getattr(usage, "output_tokens_details", None), "reasoning_tokens", None),
                    "cached_prompt_tokens": getattr(usage, "input_tokens_details", None) and getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", None),
                }
            ],
            "used_direct_answer_retry": False,
        }
        return answer_text, metadata

    def _reasoning_effort_for_task(self, task: TaskDefinition | None) -> str:
        if task is None:
            return self.reasoning_effort
        return resolve_reasoning_effort(
            base_effort=self.reasoning_effort,
            profile=self.reasoning_effort_profile,
            overrides=self.reasoning_effort_overrides,
            task_id=task.id,
        )

    def _max_tokens_for_task(self, task: TaskDefinition | None) -> int:
        if task is None:
            return self.max_tokens
        return resolve_max_tokens(
            base_max_tokens=self.max_tokens,
            profile=self.max_tokens_profile or self.reasoning_effort_profile,
            overrides=self.max_tokens_overrides,
            task_id=task.id,
        )

    def collect(self, task: TaskDefinition) -> TaskOutput:
        answer_text, metadata = self.run(task.prompt, task=task)
        source_dir = _source_dir(self.save_responses_dir, task)
        _persist_metadata(self.save_responses_dir, task, metadata)
        return build_task_output_from_text(
            task,
            source_dir,
            answer_text,
            persist=self.save_responses_dir is not None,
        )


@dataclass
class AnthropicRunner:
    model: str
    api_key: str
    temperature: float = 0.0
    max_tokens: int = 3000
    save_responses_dir: Path | None = None

    def __post_init__(self) -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Anthropic subject support requires the 'anthropic' package. "
                "Install it with `pip install anthropic` or `pip install -e '.[anthropic]'`."
            ) from exc

        self._client = anthropic.Anthropic(api_key=self.api_key)

    def run(self, prompt: str) -> tuple[str, dict]:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        parts: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        answer_text = "\n".join(parts).strip()
        usage = getattr(response, "usage", None)
        metadata = {
            "attempts": [
                {
                    "model": self.model,
                    "prompt_variant": "original",
                    "finish_reason": getattr(response, "stop_reason", None),
                    "reasoning_effort": "",
                    "content_present": bool(answer_text),
                    "content_len": len(answer_text),
                    "reasoning_present": False,
                    "reasoning_len": 0,
                    "request_id": getattr(response, "id", None),
                    "prompt_tokens": getattr(usage, "input_tokens", None),
                    "completion_tokens": getattr(usage, "output_tokens", None),
                    "total_tokens": (
                        None
                        if usage is None
                        else int(getattr(usage, "input_tokens", 0) or 0)
                        + int(getattr(usage, "output_tokens", 0) or 0)
                    ),
                    "reasoning_tokens": None,
                    "cached_prompt_tokens": getattr(usage, "cache_read_input_tokens", None),
                }
            ],
            "used_direct_answer_retry": False,
        }
        return answer_text, metadata

    def collect(self, task: TaskDefinition) -> TaskOutput:
        answer_text, metadata = self.run(task.prompt)
        source_dir = _source_dir(self.save_responses_dir, task)
        _persist_metadata(self.save_responses_dir, task, metadata)
        return build_task_output_from_text(
            task,
            source_dir,
            answer_text,
            persist=self.save_responses_dir is not None,
        )
