from __future__ import annotations

import unittest
from types import SimpleNamespace

from roughbench.openai_compat import (
    build_reasoning_extra_body,
    normalize_message_content,
    normalize_reasoning_content,
)


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


if __name__ == "__main__":
    unittest.main()
