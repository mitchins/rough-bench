from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from openai import OpenAI

from roughbench.openai_compat import (
    build_reasoning_extra_body,
    normalize_message_content,
    normalize_reasoning_content,
)
from roughbench.runners.base import TaskOutput
from roughbench.runners.structured_output import build_task_output_from_text
from roughbench.tasks.models import TaskDefinition


DEFAULT_BASE_URL = "http://localhost:8000/v1"
DEFAULT_MODEL = "openai/gpt-oss-20b"
DIRECT_ANSWER_RETRY_PREAMBLE = (
    "Answer directly in the requested format. "
    "Do not think step by step. "
    "Do not emit hidden reasoning.\n\n"
)


@dataclass
class OpenAICompatibleRunner:
    model: str
    base_url: str
    api_key: str = "dummy"
    temperature: float = 0.0
    max_tokens: int = 2000
    timeout_seconds: int = 180
    reasoning_effort: str = ""
    thinking_type: str = ""
    direct_answer_first: bool = False
    save_responses_dir: Path | None = None
    _client: OpenAI | None = field(default=None, init=False, repr=False)

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                base_url=self.base_url.rstrip("/"),
                api_key=self.api_key,
                timeout=self.timeout_seconds,
            )
        return self._client

    def run(self, prompt: str) -> tuple[str, dict]:
        if self.direct_answer_first:
            answer_text, metadata = self._run_once(
                DIRECT_ANSWER_RETRY_PREAMBLE + prompt,
                prompt_variant="direct_answer_first",
            )
            return answer_text, {"attempts": [metadata], "used_direct_answer_retry": False}

        first_answer, first_meta = self._run_once(prompt, prompt_variant="original")
        if first_answer:
            return first_answer, {"attempts": [first_meta], "used_direct_answer_retry": False}

        reasoning_len = int(first_meta.get("reasoning_len", 0))
        if reasoning_len <= 0:
            return first_answer, {"attempts": [first_meta], "used_direct_answer_retry": False}

        retry_prompt = DIRECT_ANSWER_RETRY_PREAMBLE + prompt
        retry_answer, retry_meta = self._run_once(
            retry_prompt,
            prompt_variant="direct_answer_retry",
        )
        return retry_answer, {
            "attempts": [first_meta, retry_meta],
            "used_direct_answer_retry": True,
        }

    def _run_once(self, prompt: str, *, prompt_variant: str) -> tuple[str, dict]:
        create_kwargs: dict[str, object] = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }
        if self.reasoning_effort:
            create_kwargs["extra_body"] = build_reasoning_extra_body(self.reasoning_effort)
        if self.thinking_type:
            extra_body = dict(create_kwargs.get("extra_body", {}))
            extra_body["thinking"] = {"type": self.thinking_type}
            create_kwargs["extra_body"] = extra_body

        response = self.client.chat.completions.create(
            **create_kwargs,
        )
        choice = response.choices[0]
        message = choice.message
        answer_text = normalize_message_content(message.content)
        reasoning_text = normalize_reasoning_content(message)
        usage = getattr(response, "usage", None)
        completion_details = getattr(usage, "completion_tokens_details", None)
        prompt_details = getattr(usage, "prompt_tokens_details", None)
        metadata = {
            "model": self.model,
            "base_url": self.base_url,
            "prompt_variant": prompt_variant,
            "finish_reason": choice.finish_reason,
            "reasoning_effort": self.reasoning_effort,
            "content_present": bool(answer_text),
            "content_len": len(answer_text),
            "reasoning_present": bool(reasoning_text),
            "reasoning_len": len(reasoning_text),
            "request_id": getattr(response, "request_id", None),
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
            "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
            "cached_prompt_tokens": getattr(prompt_details, "cached_tokens", None),
        }
        return answer_text, metadata

    def collect(self, task: TaskDefinition) -> TaskOutput:
        answer_text, metadata = self.run(task.prompt)
        source_dir = self._source_dir(task)
        output = build_task_output_from_text(
            task,
            source_dir,
            answer_text,
            persist=self.save_responses_dir is not None,
        )
        self._persist_metadata(task, metadata)
        return output

    def _source_dir(self, task: TaskDefinition) -> Path:
        if self.save_responses_dir is None:
            return Path("live") / task.id
        return self.save_responses_dir / task.id

    def _persist_metadata(self, task: TaskDefinition, metadata: dict) -> None:
        if self.save_responses_dir is None:
            return
        meta_dir = self.save_responses_dir / ".roughbench_live_meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        (meta_dir / f"{task.id}.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def from_env(
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout_seconds: int | None = None,
    reasoning_effort: str | None = None,
    thinking_type: str | None = None,
    direct_answer_first: bool | None = None,
    save_responses_dir: Path | None = None,
) -> OpenAICompatibleRunner:
    resolved_temperature = temperature
    if resolved_temperature is None:
        resolved_temperature = float(os.getenv("ROUGHBENCH_TEMPERATURE", "0.0"))

    resolved_max_tokens = max_tokens
    if resolved_max_tokens is None:
        resolved_max_tokens = int(os.getenv("ROUGHBENCH_MAX_TOKENS", "2000"))

    resolved_timeout_seconds = timeout_seconds
    if resolved_timeout_seconds is None:
        resolved_timeout_seconds = int(os.getenv("ROUGHBENCH_TIMEOUT_SECONDS", "180"))

    resolved_reasoning_effort = reasoning_effort
    if resolved_reasoning_effort is None:
        resolved_reasoning_effort = os.getenv("ROUGHBENCH_REASONING_EFFORT", "")

    resolved_direct_answer_first = direct_answer_first
    if resolved_direct_answer_first is None:
        resolved_direct_answer_first = os.getenv("ROUGHBENCH_DIRECT_ANSWER_FIRST", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    resolved_thinking_type = thinking_type
    if resolved_thinking_type is None:
        resolved_thinking_type = os.getenv("ROUGHBENCH_THINKING_TYPE", "")

    return OpenAICompatibleRunner(
        model=model or os.getenv("ROUGHBENCH_MODEL", DEFAULT_MODEL),
        base_url=base_url or os.getenv("ROUGHBENCH_BASE_URL", DEFAULT_BASE_URL),
        api_key=api_key or os.getenv("ROUGHBENCH_API_KEY", "dummy"),
        temperature=resolved_temperature,
        max_tokens=resolved_max_tokens,
        timeout_seconds=resolved_timeout_seconds,
        reasoning_effort=resolved_reasoning_effort,
        thinking_type=resolved_thinking_type,
        direct_answer_first=resolved_direct_answer_first,
        save_responses_dir=save_responses_dir,
    )
