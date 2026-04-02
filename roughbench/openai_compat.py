from __future__ import annotations

import re
from typing import Any


THINK_BLOCK_RE = re.compile(
    r"^\s*(?:<(?:think|thinking)>\s*.*?\s*</(?:think|thinking)>\s*)+",
    re.DOTALL | re.IGNORECASE,
)


def normalize_message_content(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return _strip_thinking_blocks(content).strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            text = _extract_content_part_text(item)
            if text:
                parts.append(text)
        return "\n".join(part.strip() for part in parts if part and part.strip()).strip()
    return _strip_thinking_blocks(str(content)).strip()


def normalize_reasoning_content(message: Any) -> str:
    direct_values = (
        getattr(message, "reasoning", None),
        getattr(message, "reasoning_content", None),
        getattr(message, "thinking", None),
    )
    for value in direct_values:
        text = _extract_text(value)
        if text:
            return text

    content = getattr(message, "content", None)
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            text = _extract_reasoning_part_text(item)
            if text:
                parts.append(text)
        if parts:
            return "\n".join(parts).strip()

    return _extract_leading_think_block(_extract_text(content))


def build_reasoning_extra_body(reasoning_effort: str) -> dict[str, object]:
    return {
        "reasoning_effort": reasoning_effort,
        "reasoning": {"effort": reasoning_effort},
    }


def _extract_content_part_text(item: object) -> str:
    if isinstance(item, str):
        return _strip_thinking_blocks(item).strip()
    if isinstance(item, dict):
        item_type = str(item.get("type", "")).lower()
        if item_type in {"reasoning", "thinking"}:
            return ""
        text = _extract_text(item.get("text"))
        if text:
            return _strip_thinking_blocks(text).strip()
        nested_content = item.get("content")
        if isinstance(nested_content, list):
            parts = [_extract_content_part_text(part) for part in nested_content]
            joined = "\n".join(part for part in parts if part)
            if joined:
                return joined.strip()
        nested_text = _extract_text(nested_content)
        if nested_text:
            return _strip_thinking_blocks(nested_text).strip()
        return ""
    text = getattr(item, "text", None)
    if isinstance(text, str):
        return _strip_thinking_blocks(text).strip()
    return ""


def _extract_reasoning_part_text(item: object) -> str:
    if isinstance(item, dict):
        item_type = str(item.get("type", "")).lower()
        if item_type not in {"reasoning", "thinking"}:
            return ""
        for key in ("text", "thinking", "reasoning", "content"):
            text = _extract_text(item.get(key))
            if text:
                return text
        return ""
    for attr in ("thinking", "reasoning", "text"):
        text = _extract_text(getattr(item, attr, None))
        if text:
            return text
    return ""


def _extract_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [_extract_text(item) for item in value]
        return "\n".join(part for part in parts if part).strip()
    if isinstance(value, dict):
        for key in ("text", "content", "thinking", "reasoning", "summary"):
            text = _extract_text(value.get(key))
            if text:
                return text
        return ""
    text = getattr(value, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    return str(value).strip()


def _extract_leading_think_block(text: str) -> str:
    if not text:
        return ""
    match = THINK_BLOCK_RE.match(text)
    if not match:
        return ""
    block = match.group(0)
    block = re.sub(r"^\s*<(?:think|thinking)>\s*", "", block, flags=re.IGNORECASE | re.DOTALL)
    block = re.sub(r"\s*</(?:think|thinking)>\s*$", "", block, flags=re.IGNORECASE | re.DOTALL)
    return block.strip()


def _strip_thinking_blocks(text: str) -> str:
    stripped = THINK_BLOCK_RE.sub("", text)
    return stripped.strip()
