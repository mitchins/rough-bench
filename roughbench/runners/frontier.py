from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from openai import OpenAI

from roughbench.runners.base import TaskOutput
from roughbench.runners.structured_output import build_task_output_from_text
from roughbench.tasks.models import TaskDefinition


def _source_dir(save_responses_dir: Path | None, task: TaskDefinition) -> Path:
    if save_responses_dir is None:
        return Path("live") / task.id
    return save_responses_dir / task.id


@dataclass
class OpenAIRunner:
    model: str
    api_key: str
    temperature: float = 0.0
    max_tokens: int = 3000
    reasoning_effort: str = ""
    save_responses_dir: Path | None = None
    _client: OpenAI | None = field(default=None, init=False, repr=False)

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def run(self, prompt: str) -> str:
        create_kwargs: dict[str, object] = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": self.max_tokens,
        }
        if self.reasoning_effort:
            create_kwargs["reasoning"] = {"effort": self.reasoning_effort}
        elif self.temperature != 0.0:
            create_kwargs["temperature"] = self.temperature

        response = self.client.responses.create(**create_kwargs)
        return (response.output_text or "").strip()

    def collect(self, task: TaskDefinition) -> TaskOutput:
        answer_text = self.run(task.prompt)
        source_dir = _source_dir(self.save_responses_dir, task)
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

    def run(self, prompt: str) -> str:
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
        return "\n".join(parts).strip()

    def collect(self, task: TaskDefinition) -> TaskOutput:
        answer_text = self.run(task.prompt)
        source_dir = _source_dir(self.save_responses_dir, task)
        return build_task_output_from_text(
            task,
            source_dir,
            answer_text,
            persist=self.save_responses_dir is not None,
        )
