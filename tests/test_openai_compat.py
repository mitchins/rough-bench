from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from roughbench.openai_compat import (
    build_reasoning_extra_body,
    normalize_message_content,
    normalize_reasoning_content,
)
from roughbench.runners.openai_compatible import OpenAICompatibleRunner, OutputCapExceededError
from roughbench.tasks.models import TaskDefinition


def _fake_response(
    text: str,
    *,
    finish_reason: str = "stop",
    prompt_tokens: int = 8,
    completion_tokens: int = 16,
) -> SimpleNamespace:
    message = SimpleNamespace(reasoning=None, reasoning_content=None, thinking=None, content=text)
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    usage = SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        completion_tokens_details=None,
        prompt_tokens_details=None,
    )
    return SimpleNamespace(choices=[choice], usage=usage, request_id=None)


class _FakeChatCompletions:
    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return self._responses.pop(0)


class _FakeOpenAIClient:
    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self.chat = SimpleNamespace(completions=_FakeChatCompletions(responses))


class OpenAICompatNormalizationTests(unittest.TestCase):
    def test_normalize_message_content_strips_leading_think_blocks(self) -> None:
        content = (
            "<think>quiet chain of thought</think>\n"
            "<thinking>more hidden trace</thinking>\n"
            "Final answer here."
        )
        self.assertEqual(normalize_message_content(content), "Final answer here.")

    def test_normalize_message_content_ignores_reasoning_parts_in_content_arrays(self) -> None:
        content = [
            {"type": "reasoning", "text": "hidden reasoning"},
            {"type": "text", "text": "Visible answer"},
        ]
        self.assertEqual(normalize_message_content(content), "Visible answer")

    def test_normalize_message_content_supports_nested_content_lists(self) -> None:
        content = [
            {
                "type": "output_text",
                "content": [
                    {"type": "reasoning", "text": "hidden"},
                    {"type": "text", "text": "Visible answer"},
                ],
            }
        ]
        self.assertEqual(normalize_message_content(content), "Visible answer")

    def test_normalize_reasoning_content_reads_thinking_field(self) -> None:
        message = SimpleNamespace(reasoning=None, reasoning_content="", thinking="hidden trace")
        self.assertEqual(normalize_reasoning_content(message), "hidden trace")

    def test_normalize_reasoning_content_extracts_leading_think_block_when_no_reasoning_field(self) -> None:
        message = SimpleNamespace(
            reasoning=None,
            reasoning_content=None,
            thinking=None,
            content="<think>hidden trace</think>\nVisible answer",
        )
        self.assertEqual(normalize_reasoning_content(message), "hidden trace")

    def test_build_reasoning_extra_body_sets_root_and_nested_fields(self) -> None:
        self.assertEqual(
            build_reasoning_extra_body("low"),
            {
                "reasoning_effort": "low",
                "reasoning": {"effort": "low"},
            },
        )


class OpenAICompatibleRunnerTests(unittest.TestCase):
    def test_runner_balanced_auto_profile_raises_effort_on_allowlisted_tasks(self) -> None:
        runner = OpenAICompatibleRunner(
            model="demo/model",
            base_url="https://example.invalid/v1",
            max_tokens=1024,
            reasoning_effort="medium",
            reasoning_effort_profile="balanced_auto",
        )
        fake_client = _FakeOpenAIClient(
            [
                _fake_response("ok", finish_reason="stop", completion_tokens=8),
                _fake_response("ok", finish_reason="stop", completion_tokens=8),
            ]
        )
        runner._client = fake_client

        high_task = TaskDefinition(
            id="swe_scraper_persistent_resumable",
            title="Scraper",
            domain="swe",
            prompt="Do the scraper task.",
            intent="Test",
        )
        medium_task = TaskDefinition(
            id="critique_without_sandwich",
            title="Critique",
            domain="writing",
            prompt="Do the critique task.",
            intent="Test",
        )

        runner.collect(high_task)
        runner.collect(medium_task)

        calls = fake_client.chat.completions.calls
        self.assertEqual(calls[0]["extra_body"]["reasoning_effort"], "high")
        self.assertEqual(calls[0]["max_tokens"], 50000)
        self.assertEqual(calls[1]["extra_body"]["reasoning_effort"], "medium")
        self.assertEqual(calls[1]["max_tokens"], 1024)

    def test_runner_retries_capped_output_with_compacting_prompt(self) -> None:
        runner = OpenAICompatibleRunner(
            model="demo/model",
            base_url="https://example.invalid/v1",
            max_tokens=58000,
        )
        fake_client = _FakeOpenAIClient(
            [
                _fake_response(
                    "too long",
                    finish_reason="length",
                    completion_tokens=58000,
                ),
                _fake_response(
                    "final concise answer",
                    finish_reason="stop",
                    completion_tokens=120,
                ),
            ]
        )
        runner._client = fake_client

        answer_text, metadata = runner.run("Solve the task.")

        self.assertEqual(answer_text, "final concise answer")
        self.assertEqual(len(metadata["attempts"]), 2)
        self.assertTrue(metadata["used_output_cap_retry"])
        self.assertEqual(len(fake_client.chat.completions.calls), 2)
        second_prompt = fake_client.chat.completions.calls[1]["messages"][0]["content"]
        self.assertIn("Your previous answer hit the output limit.", second_prompt)

    def test_collect_persists_metadata_and_raises_when_cap_retry_still_truncates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = OpenAICompatibleRunner(
                model="demo/model",
                base_url="https://example.invalid/v1",
                max_tokens=58000,
                save_responses_dir=Path(temp_dir),
            )
            fake_client = _FakeOpenAIClient(
                [
                    _fake_response(
                        "first too long",
                        finish_reason="length",
                        completion_tokens=58000,
                    ),
                    _fake_response(
                        "still too long",
                        finish_reason="length",
                        completion_tokens=58000,
                    ),
                ]
            )
            runner._client = fake_client
            task = TaskDefinition(
                id="demo_task",
                title="Demo task",
                domain="demo",
                prompt="Solve the task.",
                intent="Test prompt.",
            )

            with self.assertRaises(OutputCapExceededError):
                runner.collect(task)

            meta_path = Path(temp_dir) / ".roughbench_live_meta" / "demo_task.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))

        self.assertTrue(meta["output_cap_exhausted"])
        self.assertEqual(len(meta["attempts"]), 2)
        self.assertTrue(meta["used_output_cap_retry"])


if __name__ == "__main__":
    unittest.main()
