from __future__ import annotations

from pathlib import Path

from roughbench.judging.scorecard import PenaltyHit, SignalHit, TaskScorecard
from roughbench.runners.base import TaskOutput
from roughbench.tasks.models import PenaltyRule, SignalRule, TaskDefinition

HEAD_TEXT_LIMIT = 1000


def _normalize(text: str) -> str:
    hyphen_variants = {
        ord("\u2010"): "-",
        ord("\u2011"): "-",
        ord("\u2012"): "-",
        ord("\u2013"): "-",
        ord("\u2014"): "-",
        ord("\u2015"): "-",
        ord("\u2212"): "-",
    }
    return " ".join(text.translate(hyphen_variants).casefold().split())


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
    return _signal_matches_with_artifacts(rule, text, artifact_names, "")


def _signal_matches_with_artifacts(
    rule: SignalRule,
    text: str,
    artifact_names: tuple[str, ...],
    artifact_text: str,
) -> bool:
    matched = False
    if rule.any:
        matched = _contains_any(text, rule.any)
        if not matched:
            return False
    if rule.all:
        matched = True
        if not _contains_all(text, rule.all):
            return False
    if rule.groups:
        matched = True
        if not _matches_groups(text, rule.groups):
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
    return _penalty_triggered_with_artifacts(rule, text, artifact_names, "")


def _penalty_triggered_with_artifacts(
    rule: PenaltyRule,
    text: str,
    artifact_names: tuple[str, ...],
    artifact_text: str,
) -> bool:
    head_text = text[:HEAD_TEXT_LIMIT]
    if rule.present_any and _contains_any(text, rule.present_any):
        return True
    if rule.present_unnegated_any and _contains_any_unnegated(text, rule.present_unnegated_any):
        return True
    if rule.present_all and _contains_all(text, rule.present_all):
        return True
    if rule.present_groups and _matches_groups(text, rule.present_groups):
        return True
    if rule.present_head_any and _contains_any(head_text, rule.present_head_any):
        return True
    if rule.present_head_all and _contains_all(head_text, rule.present_head_all):
        return True
    if rule.present_head_groups and _matches_groups(head_text, rule.present_head_groups):
        return True
    if rule.missing_any and not _contains_any(text, rule.missing_any):
        return True
    if rule.missing_all and not _contains_all(text, rule.missing_all):
        return True
    if rule.missing_groups and not _matches_groups(text, rule.missing_groups):
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
        normalized_text = _normalize(output.combined_text)
        normalized_artifact_text = _normalize(output.artifact_text)

        passed_signals = tuple(
            SignalHit(id=rule.id, description=rule.description)
            for rule in task.rubric.signals
            if _signal_matches_with_artifacts(
                rule,
                normalized_text,
                output.artifact_names,
                normalized_artifact_text,
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
