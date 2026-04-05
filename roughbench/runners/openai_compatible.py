from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
import re

from openai import BadRequestError, OpenAI

from roughbench.openai_compat import (
    build_reasoning_extra_body,
    normalize_message_content,
    normalize_reasoning_content,
)
from roughbench.runners.base import TaskOutput
from roughbench.runners.structured_output import build_task_output_from_text
from roughbench.subjects import (
    default_timeout_seconds_for_endpoint,
    is_lan_base_url,
    resolve_max_tokens,
    resolve_reasoning_effort,
)
from roughbench.tasks.models import TaskDefinition


DEFAULT_BASE_URL = "http://localhost:8000/v1"
DEFAULT_MODEL = "openai/gpt-oss-20b"
DEFAULT_TIMEOUT_SECONDS = default_timeout_seconds_for_endpoint(
    provider="openai-compatible",
    base_url=DEFAULT_BASE_URL,
)
DIRECT_ANSWER_RETRY_PREAMBLE = (
    "Answer directly in the requested format. "
    "Do not think step by step. "
    "Do not emit hidden reasoning.\n\n"
)
OUTPUT_CAP_RETRY_PREAMBLE = (
    "Your previous answer hit the output limit. "
    "Retry with a much more concise final answer only. "
    "Do not restate the prompt. "
    "Do not include hidden reasoning. "
    "Compress aggressively while still satisfying every requirement.\n\n"
)
CONTEXT_ERROR_PATTERN = re.compile(r"maximum context length is (\d+) tokens", re.I)
MIN_RETRY_MAX_TOKENS = 256
PROMPT_TOKEN_ESTIMATE_DIVISOR = 4.0
PROMPT_TOKEN_ESTIMATE_OVERHEAD = 32
CONTEXT_BUDGET_SAFETY_MARGIN = 32


class OutputCapExceededError(RuntimeError):
    def __init__(
        self,
        *,
        attempts: list[dict],
        used_direct_answer_retry: bool,
        used_output_cap_retry: bool,
    ) -> None:
        self.payload = {
            "attempts": attempts,
            "used_direct_answer_retry": used_direct_answer_retry,
            "used_output_cap_retry": used_output_cap_retry,
            "output_cap_exhausted": True,
        }
        last_attempt = attempts[-1] if attempts else {}
        finish_reason = last_attempt.get("finish_reason")
        used_max_tokens = last_attempt.get("used_max_tokens")
        super().__init__(
            "response hit output cap after "
            f"{len(attempts)} attempt(s) (finish_reason={finish_reason}, used_max_tokens={used_max_tokens})"
        )


@dataclass
class OpenAICompatibleRunner:
    model: str
    base_url: str
    api_key: str = "dummy"
    temperature: float = 0.0
    max_tokens: int = 2000
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    reasoning_effort: str = ""
    reasoning_effort_profile: str = ""
    reasoning_effort_overrides: tuple[tuple[str, str], ...] = ()
    max_tokens_profile: str = ""
    max_tokens_overrides: tuple[tuple[str, int], ...] = ()
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

    def run(self, prompt: str, *, task: TaskDefinition | None = None) -> tuple[str, dict]:
        resolved_reasoning_effort = self._reasoning_effort_for_task(task)
        resolved_max_tokens = self._max_tokens_for_task(task)
        if self.direct_answer_first:
            answer_text, metadata = self._run_once(
                DIRECT_ANSWER_RETRY_PREAMBLE + prompt,
                prompt_variant="direct_answer_first",
                reasoning_effort=resolved_reasoning_effort,
                max_tokens=resolved_max_tokens,
            )
            if self._is_output_cap_hit(metadata):
                retry_answer, retry_meta = self._run_once(
                    OUTPUT_CAP_RETRY_PREAMBLE + DIRECT_ANSWER_RETRY_PREAMBLE + prompt,
                    prompt_variant="output_cap_retry",
                    reasoning_effort=resolved_reasoning_effort,
                    max_tokens=resolved_max_tokens,
                )
                attempts = [metadata, retry_meta]
                if self._is_output_cap_hit(retry_meta):
                    raise OutputCapExceededError(
                        attempts=attempts,
                        used_direct_answer_retry=False,
                        used_output_cap_retry=True,
                    )
                return retry_answer, {
                    "attempts": attempts,
                    "used_direct_answer_retry": False,
                    "used_output_cap_retry": True,
                }
            return answer_text, {"attempts": [metadata], "used_direct_answer_retry": False}

        first_answer, first_meta = self._run_once(
            prompt,
            prompt_variant="original",
            reasoning_effort=resolved_reasoning_effort,
            max_tokens=resolved_max_tokens,
        )
        if self._is_output_cap_hit(first_meta):
            retry_answer, retry_meta = self._run_once(
                OUTPUT_CAP_RETRY_PREAMBLE + DIRECT_ANSWER_RETRY_PREAMBLE + prompt,
                prompt_variant="output_cap_retry",
                reasoning_effort=resolved_reasoning_effort,
                max_tokens=resolved_max_tokens,
            )
            attempts = [first_meta, retry_meta]
            if self._is_output_cap_hit(retry_meta):
                raise OutputCapExceededError(
                    attempts=attempts,
                    used_direct_answer_retry=False,
                    used_output_cap_retry=True,
                )
            return retry_answer, {
                "attempts": attempts,
                "used_direct_answer_retry": False,
                "used_output_cap_retry": True,
            }
        if first_answer:
            return first_answer, {"attempts": [first_meta], "used_direct_answer_retry": False}

        reasoning_len = int(first_meta.get("reasoning_len", 0))
        if reasoning_len <= 0:
            return first_answer, {"attempts": [first_meta], "used_direct_answer_retry": False}

        retry_prompt = DIRECT_ANSWER_RETRY_PREAMBLE + prompt
        retry_answer, retry_meta = self._run_once(
            retry_prompt,
            prompt_variant="direct_answer_retry",
            reasoning_effort=resolved_reasoning_effort,
            max_tokens=resolved_max_tokens,
        )
        if self._is_output_cap_hit(retry_meta):
            cap_retry_answer, cap_retry_meta = self._run_once(
                OUTPUT_CAP_RETRY_PREAMBLE + DIRECT_ANSWER_RETRY_PREAMBLE + prompt,
                prompt_variant="output_cap_retry",
                reasoning_effort=resolved_reasoning_effort,
                max_tokens=resolved_max_tokens,
            )
            attempts = [first_meta, retry_meta, cap_retry_meta]
            if self._is_output_cap_hit(cap_retry_meta):
                raise OutputCapExceededError(
                    attempts=attempts,
                    used_direct_answer_retry=True,
                    used_output_cap_retry=True,
                )
            return cap_retry_answer, {
                "attempts": attempts,
                "used_direct_answer_retry": True,
                "used_output_cap_retry": True,
            }
        return retry_answer, {
            "attempts": [first_meta, retry_meta],
            "used_direct_answer_retry": True,
            "used_output_cap_retry": False,
        }

    def _run_once(
        self,
        prompt: str,
        *,
        prompt_variant: str,
        reasoning_effort: str,
        max_tokens: int,
    ) -> tuple[str, dict]:
        prompt_token_estimate = self._estimate_prompt_tokens(prompt)
        requested_max_tokens = self._initial_completion_budget(
            prompt_token_estimate,
            max_tokens=max_tokens,
        )
        retry_count = 0
        while True:
            create_kwargs: dict[str, object] = {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": requested_max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            }
            if reasoning_effort:
                create_kwargs["extra_body"] = build_reasoning_extra_body(reasoning_effort)
            if self.thinking_type:
                extra_body = dict(create_kwargs.get("extra_body", {}))
                extra_body["thinking"] = {"type": self.thinking_type}
                create_kwargs["extra_body"] = extra_body

            try:
                response = self.client.chat.completions.create(
                    **create_kwargs,
                )
            except BadRequestError as exc:
                next_max_tokens = self._next_context_retry_max_tokens(
                    exc,
                    current_max_tokens=requested_max_tokens,
                    prompt_token_estimate=prompt_token_estimate,
                )
                if next_max_tokens is None:
                    raise
                requested_max_tokens = next_max_tokens
                retry_count += 1
                continue

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
                "requested_max_tokens": max_tokens,
                "max_tokens_mode": (
                    "total_context_budget" if self._treat_max_tokens_as_total_context_budget else "completion_cap"
                ),
                "prompt_token_estimate": prompt_token_estimate,
                "estimated_completion_budget": self._initial_completion_budget(
                    prompt_token_estimate,
                    max_tokens=max_tokens,
                ),
                "used_max_tokens": requested_max_tokens,
                "context_retry_count": retry_count,
                "finish_reason": choice.finish_reason,
                "reasoning_effort": reasoning_effort,
                "reasoning_effort_profile": self.reasoning_effort_profile,
                "max_tokens_profile": self.max_tokens_profile,
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

    def _is_output_cap_hit(self, metadata: dict) -> bool:
        finish_reason = str(metadata.get("finish_reason") or "").casefold()
        completion_tokens = int(metadata.get("completion_tokens") or 0)
        used_max_tokens = int(
            metadata.get("used_max_tokens") or metadata.get("requested_max_tokens") or 0
        )
        return finish_reason == "length" or (used_max_tokens > 0 and completion_tokens >= used_max_tokens)

    @property
    def _treat_max_tokens_as_total_context_budget(self) -> bool:
        return is_lan_base_url(self.base_url)

    def _estimate_prompt_tokens(self, prompt: str) -> int:
        if not prompt:
            return PROMPT_TOKEN_ESTIMATE_OVERHEAD
        char_estimate = math.ceil(len(prompt) / PROMPT_TOKEN_ESTIMATE_DIVISOR)
        return max(PROMPT_TOKEN_ESTIMATE_OVERHEAD, char_estimate + PROMPT_TOKEN_ESTIMATE_OVERHEAD)

    def _initial_completion_budget(self, prompt_token_estimate: int, *, max_tokens: int) -> int:
        if not self._treat_max_tokens_as_total_context_budget:
            return max_tokens
        available = max_tokens - prompt_token_estimate - CONTEXT_BUDGET_SAFETY_MARGIN
        return max(MIN_RETRY_MAX_TOKENS, available)

    def _next_context_retry_max_tokens(
        self,
        exc: BadRequestError,
        *,
        current_max_tokens: int,
        prompt_token_estimate: int,
    ) -> int | None:
        message = str(exc)
        if "maximum context length" not in message.lower():
            return None
        if current_max_tokens <= MIN_RETRY_MAX_TOKENS:
            return None

        match = CONTEXT_ERROR_PATTERN.search(message)
        limit = int(match.group(1)) if match else 0
        candidates = [
            current_max_tokens - max(1024, current_max_tokens // 5),
            current_max_tokens - 2048,
            int(current_max_tokens * 0.75),
        ]
        if limit:
            candidates.extend(
                [
                    limit - 512,
                    limit - 1024,
                    limit - 2048,
                ]
            )
            if self._treat_max_tokens_as_total_context_budget:
                candidates.extend(
                    [
                        limit - prompt_token_estimate - CONTEXT_BUDGET_SAFETY_MARGIN,
                        limit - prompt_token_estimate - 2 * CONTEXT_BUDGET_SAFETY_MARGIN,
                    ]
                )
        next_max_tokens = max(MIN_RETRY_MAX_TOKENS, min(value for value in candidates if value > 0))
        if next_max_tokens >= current_max_tokens:
            return None
        return next_max_tokens

    def collect(self, task: TaskDefinition) -> TaskOutput:
        try:
            answer_text, metadata = self.run(task.prompt, task=task)
        except OutputCapExceededError as exc:
            self._persist_metadata(task, exc.payload)
            raise
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
    reasoning_effort_profile: str | None = None,
    reasoning_effort_overrides: tuple[tuple[str, str], ...] | None = None,
    max_tokens_profile: str | None = None,
    max_tokens_overrides: tuple[tuple[str, int], ...] | None = None,
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
        timeout_override = os.getenv("ROUGHBENCH_TIMEOUT_SECONDS")
        if timeout_override is not None:
            resolved_timeout_seconds = int(timeout_override)
        else:
            inferred_base_url = base_url or os.getenv("ROUGHBENCH_BASE_URL", DEFAULT_BASE_URL)
            resolved_timeout_seconds = default_timeout_seconds_for_endpoint(
                provider="openai-compatible",
                base_url=inferred_base_url,
            )

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
        reasoning_effort_profile=reasoning_effort_profile or "",
        reasoning_effort_overrides=reasoning_effort_overrides or (),
        max_tokens_profile=max_tokens_profile or reasoning_effort_profile or "",
        max_tokens_overrides=max_tokens_overrides or (),
        thinking_type=resolved_thinking_type,
        direct_answer_first=resolved_direct_answer_first,
        save_responses_dir=save_responses_dir,
    )
