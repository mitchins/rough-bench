from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from roughbench.judging.scorecard import PenaltyHit, SignalHit, TaskScorecard
from roughbench.runners.base import TaskOutput
from roughbench.tasks.models import PenaltyRule, SignalRule, TaskDefinition

HEAD_TEXT_LIMIT = 1000

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_UNCLOSED_THINK_RE = re.compile(r"<think>.*", re.DOTALL | re.IGNORECASE)
_SECTION_RE = re.compile(r"(?m)^##\s+(.+?)\s*$")

_HYPHEN_VARIANTS = {
    ord("\u2010"): "-",
    ord("\u2011"): "-",
    ord("\u2012"): "-",
    ord("\u2013"): "-",
    ord("\u2014"): "-",
    ord("\u2015"): "-",
    ord("\u2212"): "-",
}
_SUBSCRIPT_DIGITS = str.maketrans({
    "\u2080": "0",
    "\u2081": "1",
    "\u2082": "2",
    "\u2083": "3",
    "\u2084": "4",
    "\u2085": "5",
    "\u2086": "6",
    "\u2087": "7",
    "\u2088": "8",
    "\u2089": "9",
})
_SUPERSCRIPT_DIGITS = str.maketrans({
    "\u2070": "0",
    "\u00B9": "1",
    "\u00B2": "2",
    "\u00B3": "3",
    "\u2074": "4",
    "\u2075": "5",
    "\u2076": "6",
    "\u2077": "7",
    "\u2078": "8",
    "\u2079": "9",
})
_CHEMICAL_ALIASES = (
    ("carbon dioxide", "co2"),
    ("carbonic acid", "h2co3"),
    ("sodium bicarbonate", "nahco3"),
    ("calcium carbonate", "caco3"),
)


def _strip_think_blocks(text: str) -> str:
    """Remove <think>…</think> reasoning traces so only the actual answer is scored."""
    result = _THINK_RE.sub("", text)
    result = _UNCLOSED_THINK_RE.sub("", result)
    return result.strip()


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_HYPHEN_VARIANTS)
    text = text.translate(_SUBSCRIPT_DIGITS)
    text = text.translate(_SUPERSCRIPT_DIGITS)
    text = text.casefold()
    # Strip thousand-separator commas in numbers (e.g. 3,264 → 3264)
    text = re.sub(r"(?<=\d),(?=\d{3})", "", text)
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)
    text = re.sub(r"`{1,3}", "", text)
    text = re.sub(r"\*{1,3}", "", text)
    for alias, canonical in _CHEMICAL_ALIASES:
        text = text.replace(alias, canonical)
    return " ".join(text.split())


def _section_key(name: str) -> str:
    return _normalize(name)


def _extract_sections(text: str) -> dict[str, str]:
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        return {}

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        heading = _section_key(match.group(1))
        body = text[start:end].strip()
        sections[heading] = _normalize(body)
    return sections


def _rule_text(
    section: str,
    text: str,
    sections: dict[str, str],
) -> str:
    if not section:
        return text
    return sections.get(_section_key(section), "")


def _iter_term_spans(text: str, term: str):
    needle = term.casefold()
    if not needle:
        return

    search_from = 0
    while True:
        start = text.find(needle, search_from)
        if start == -1:
            return
        end = start + len(needle)
        left_ok = not needle[0].isalnum() or start == 0 or not text[start - 1].isalnum()
        right_ok = (
            not needle[-1].isalnum() or end == len(text) or not text[end].isalnum()
        )
        if left_ok and right_ok:
            yield start, end
        search_from = start + 1


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(any(_iter_term_spans(text, term)) for term in terms)


def _contains_any_unnegated(text: str, terms: tuple[str, ...]) -> bool:
    prefix_negation_markers = (
        "no ",
        "not ",
        "cannot ",
        "can't ",
        "never ",
        "won't ",
        "without ",
        "impossible to ",
        "non-goal",
        "non goal",
        "out of scope",
        "avoid ",
        "exclude ",
        "excluded ",
        "reject ",
        "rejects ",
        "rejected ",
        "rather than ",
        "instead of ",
        "instead ",
    )
    suffix_negation_markers = (
        " is impossible",
        " are impossible",
        " is not possible",
        " are not possible",
        " is forbidden",
        " are forbidden",
        " is prohibited",
        " are prohibited",
        " is disallowed",
        " are disallowed",
        " fails",
        " fail",
    )
    for term in terms:
        for start, end in _iter_term_spans(text, term):
            prefix = text[max(0, start - 160):start]
            suffix = text[end:min(len(text), end + 64)]
            if not any(marker in prefix for marker in prefix_negation_markers) and not any(
                marker in suffix for marker in suffix_negation_markers
            ):
                return True
    return False


def _contains_all(text: str, terms: tuple[str, ...]) -> bool:
    return all(any(_iter_term_spans(text, term)) for term in terms)


def _matches_groups(text: str, groups: tuple[tuple[str, ...], ...]) -> bool:
    return all(_contains_any(text, group) for group in groups)


def _artifact_match_any(artifact_names: tuple[str, ...], patterns: tuple[str, ...]) -> bool:
    normalized_names = {
        value.casefold() for name in artifact_names for value in (name, Path(name).name)
    }
    return any(
        pattern.casefold() in name
        for pattern in patterns
        for name in normalized_names
    )


def _signal_matches(rule: SignalRule, text: str, artifact_names: tuple[str, ...]) -> bool:
    return _signal_matches_with_artifacts(rule, text, artifact_names, "", {})


def _signal_matches_with_artifacts(
    rule: SignalRule,
    text: str,
    artifact_names: tuple[str, ...],
    artifact_text: str,
    sections: dict[str, str] | None = None,
) -> bool:
    sections = sections or {}
    scoped_text = _rule_text(rule.section, text, sections)
    matched = False
    if rule.any:
        matched = _contains_any(scoped_text, rule.any)
        if not matched:
            return False
    if rule.all:
        matched = True
        if not _contains_all(scoped_text, rule.all):
            return False
    if rule.groups:
        matched = True
        if not _matches_groups(scoped_text, rule.groups):
            return False
    if rule.artifact_any:
        matched = True
        if not _artifact_match_any(artifact_names, rule.artifact_any):
            return False
    if rule.artifact_text_any:
        matched = True
        if not _contains_any(artifact_text, rule.artifact_text_any):
            return False
    if rule.artifact_text_all:
        matched = True
        if not _contains_all(artifact_text, rule.artifact_text_all):
            return False
    if rule.artifact_text_groups:
        matched = True
        if not _matches_groups(artifact_text, rule.artifact_text_groups):
            return False
    return matched


def _penalty_triggered(rule: PenaltyRule, text: str, artifact_names: tuple[str, ...]) -> bool:
    return _penalty_triggered_with_artifacts(rule, text, artifact_names, "", {})


def _penalty_triggered_with_artifacts(
    rule: PenaltyRule,
    text: str,
    artifact_names: tuple[str, ...],
    artifact_text: str,
    sections: dict[str, str] | None = None,
) -> bool:
    sections = sections or {}
    scoped_text = _rule_text(rule.section, text, sections)
    head_text = scoped_text[:HEAD_TEXT_LIMIT]
    if rule.present_any and _contains_any(scoped_text, rule.present_any):
        return True
    if rule.present_unnegated_any and _contains_any_unnegated(
        scoped_text, rule.present_unnegated_any
    ):
        return True
    if rule.present_all and _contains_all(scoped_text, rule.present_all):
        return True
    if rule.present_groups and _matches_groups(scoped_text, rule.present_groups):
        return True
    if rule.present_head_any and _contains_any(head_text, rule.present_head_any):
        return True
    if rule.present_head_all and _contains_all(head_text, rule.present_head_all):
        return True
    if rule.present_head_groups and _matches_groups(head_text, rule.present_head_groups):
        return True
    if rule.missing_any and not _contains_any(scoped_text, rule.missing_any):
        return True
    if rule.missing_all and not _contains_all(scoped_text, rule.missing_all):
        return True
    if rule.missing_groups and not _matches_groups(scoped_text, rule.missing_groups):
        return True
    if rule.missing_head_any and not _contains_any(head_text, rule.missing_head_any):
        return True
    if rule.missing_head_all and not _contains_all(head_text, rule.missing_head_all):
        return True
    if rule.missing_head_groups and not _matches_groups(head_text, rule.missing_head_groups):
        return True
    if rule.missing_artifacts_any and not _artifact_match_any(
        artifact_names, rule.missing_artifacts_any
    ):
        return True
    if rule.present_artifact_text_any and _contains_any(
        artifact_text, rule.present_artifact_text_any
    ):
        return True
    if rule.present_artifact_text_all and _contains_all(
        artifact_text, rule.present_artifact_text_all
    ):
        return True
    if rule.present_artifact_text_groups and _matches_groups(
        artifact_text, rule.present_artifact_text_groups
    ):
        return True
    if rule.missing_artifact_text_any and not _contains_any(
        artifact_text, rule.missing_artifact_text_any
    ):
        return True
    if rule.missing_artifact_text_all and not _contains_all(
        artifact_text, rule.missing_artifact_text_all
    ):
        return True
    if rule.missing_artifact_text_groups and not _matches_groups(
        artifact_text, rule.missing_artifact_text_groups
    ):
        return True
    return False


class RuleBasedJudge:
    def evaluate(self, task: TaskDefinition, output: TaskOutput) -> TaskScorecard:
        cleaned_text = _strip_think_blocks(output.combined_text)
        cleaned_artifact_text = _strip_think_blocks(output.artifact_text)
        normalized_text = _normalize(cleaned_text)
        normalized_artifact_text = _normalize(cleaned_artifact_text)
        normalized_sections = _extract_sections(cleaned_text)

        passed_signals = tuple(
            SignalHit(id=rule.id, description=rule.description)
            for rule in task.rubric.signals
            if _signal_matches_with_artifacts(
                rule,
                normalized_text,
                output.artifact_names,
                normalized_artifact_text,
                normalized_sections,
            )
        )

        triggered_penalties = tuple(
            PenaltyHit(id=rule.id, points=rule.points, description=rule.description)
            for rule in task.rubric.penalties
            if _penalty_triggered_with_artifacts(
                rule,
                normalized_text,
                output.artifact_names,
                normalized_artifact_text,
                normalized_sections,
            )
        )

        total_penalty = sum(item.points for item in triggered_penalties)
        judge_summary = self._build_summary(output, triggered_penalties, passed_signals)
        return TaskScorecard(
            task_id=task.id,
            title=task.title,
            total_penalty=total_penalty,
            max_penalty_possible=sum(item.points for item in task.rubric.penalties),
            triggered_penalties=triggered_penalties,
            passed_signals=passed_signals,
            judge_summary=judge_summary,
            artifacts_seen=output.artifact_names,
            task_content_hash=task.content_hash,
        )

    def _build_summary(
        self,
        output: TaskOutput,
        penalties: tuple[PenaltyHit, ...],
        signals: tuple[SignalHit, ...],
    ) -> str:
        parts: list[str] = []
        if not output.answer_text and not output.artifacts:
            parts.append("No submission files found for this task.")
        if penalties:
            penalty_bits = ", ".join(f"{item.id} (+{item.points})" for item in penalties)
            parts.append(f"Triggered penalties: {penalty_bits}.")
        else:
            parts.append("No penalties triggered.")
        if signals:
            signal_bits = ", ".join(item.id for item in signals)
            parts.append(f"Passed signals: {signal_bits}.")
        if output.artifacts:
            artifact_bits = ", ".join(output.artifact_names)
            parts.append(f"Artifacts seen: {artifact_bits}.")
        return " ".join(parts)
