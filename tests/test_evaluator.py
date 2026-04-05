from __future__ import annotations

import unittest
from pathlib import Path

from roughbench.judging.evaluator import (
    HEAD_TEXT_LIMIT,
    _artifact_match_any,
    _contains_any,
    _contains_any_unnegated,
    _extract_sections,
    _iter_term_spans,
    _normalize,
    _penalty_triggered_with_artifacts,
    _signal_matches_with_artifacts,
    _strip_think_blocks,
)
from roughbench.tasks.models import PenaltyRule, SignalRule


class StripThinkBlocksTests(unittest.TestCase):
    def test_closed_think_block_is_removed(self) -> None:
        text = "<think>reasoning here</think>The actual answer."
        self.assertEqual(_strip_think_blocks(text), "The actual answer.")

    def test_unclosed_think_block_is_removed(self) -> None:
        text = "<think>reasoning that never closes and goes on forever"
        self.assertEqual(_strip_think_blocks(text), "")

    def test_text_before_unclosed_think_is_kept(self) -> None:
        text = "Preamble\n<think>reasoning forever"
        self.assertEqual(_strip_think_blocks(text), "Preamble")

    def test_no_think_block_passes_through(self) -> None:
        text = "A normal response without any reasoning."
        self.assertEqual(_strip_think_blocks(text), text)

    def test_case_insensitive(self) -> None:
        text = "<Think>Some reasoning</Think>Answer"
        self.assertEqual(_strip_think_blocks(text), "Answer")

    def test_multiple_think_blocks(self) -> None:
        text = "<think>first</think>Middle<think>second</think>End"
        self.assertEqual(_strip_think_blocks(text), "MiddleEnd")


class NormalizeTests(unittest.TestCase):
    def test_normalize_flattens_case_spacing_and_hyphen_variants(self) -> None:
        text = "Alpha\u2014Beta  \n  GAMMA"
        self.assertEqual(_normalize(text), "alpha-beta gamma")

    def test_normalize_flattens_unicode_formula_digits_and_aliases(self) -> None:
        text = "CO\u2082 and Carbon Dioxide"
        self.assertEqual(_normalize(text), "co2 and co2")


class TermSpanTests(unittest.TestCase):
    def test_iter_term_spans_respects_word_boundaries(self) -> None:
        spans = list(_iter_term_spans("bert roberta albert", "bert"))
        self.assertEqual(spans, [(0, 4)])

    def test_contains_any_uses_boundary_aware_matching(self) -> None:
        self.assertFalse(_contains_any("roberta only", ("bert",)))
        self.assertTrue(_contains_any("use bert here", ("bert",)))


class NegationTests(unittest.TestCase):
    def test_contains_any_unnegated_rejects_prefixed_negation(self) -> None:
        self.assertFalse(_contains_any_unnegated("do not use bert here", ("bert",)))
        self.assertFalse(_contains_any_unnegated("reject bert rather than fine-tuning it", ("bert",)))

    def test_contains_any_unnegated_rejects_suffix_negation(self) -> None:
        self.assertFalse(_contains_any_unnegated("bert is forbidden", ("bert",)))

    def test_contains_any_unnegated_accepts_positive_mention(self) -> None:
        self.assertTrue(_contains_any_unnegated("use bert as the baseline", ("bert",)))


class ArtifactTests(unittest.TestCase):
    def test_artifact_match_any_checks_full_path_and_basename_case_insensitively(self) -> None:
        artifacts = ("artifacts/Server.PY", "notes/report.md")
        self.assertTrue(_artifact_match_any(artifacts, ("server.py",)))
        self.assertTrue(_artifact_match_any(artifacts, ("report",)))
        self.assertFalse(_artifact_match_any(artifacts, ("client.py",)))


class SignalAndPenaltyRuleTests(unittest.TestCase):
    def test_signal_matches_with_artifact_text(self) -> None:
        rule = SignalRule(
            id="artifact-signal",
            description="example",
            artifact_any=("server.py",),
            artifact_text_groups=(("asyncio.lock",), ("current_question_open",)),
        )

        matched = _signal_matches_with_artifacts(
            rule,
            text="summary text",
            artifact_names=("artifacts/server.py",),
            artifact_text="asyncio.lock guards current_question_open",
        )

        self.assertTrue(matched)

    def test_penalty_triggered_uses_head_text_limit(self) -> None:
        rule = PenaltyRule(
            id="head-only",
            description="example",
            points=2,
            present_head_any=("danger",),
        )

        late_text = ("filler " * (HEAD_TEXT_LIMIT // 7 + 50)) + " danger"

        self.assertFalse(
            _penalty_triggered_with_artifacts(rule, late_text, artifact_names=(), artifact_text="")
        )
        self.assertTrue(
            _penalty_triggered_with_artifacts(
                rule,
                "danger appears early",
                artifact_names=(),
                artifact_text="",
            )
        )

    def test_penalty_triggered_checks_artifact_text_groups(self) -> None:
        rule = PenaltyRule(
            id="artifact-penalty",
            description="example",
            points=3,
            missing_artifact_text_groups=(("await websocket.close",), ("wait_closed",)),
        )

        self.assertFalse(
            _penalty_triggered_with_artifacts(
                rule,
                text="answer",
                artifact_names=("artifacts/server.py",),
                artifact_text="await websocket.close()\nawait websocket.wait_closed()",
            )
        )
        self.assertTrue(
            _penalty_triggered_with_artifacts(
                rule,
                text="answer",
                artifact_names=("artifacts/server.py",),
                artifact_text="await websocket.close()",
            )
        )

    def test_penalty_triggered_can_scope_to_named_section(self) -> None:
        rule = PenaltyRule(
            id="section-penalty",
            description="example",
            points=4,
            section="Immediate Action",
            present_unnegated_any=("stop the co2 injection",),
        )
        text = """## Rejected Hypothesis
Stop the CO2 injection is the wrong move.

## Immediate Action
Stop the CO2 injection immediately.
"""

        self.assertTrue(
            _penalty_triggered_with_artifacts(
                rule,
                _normalize(text),
                artifact_names=(),
                artifact_text="",
                sections=_extract_sections(text),
            )
        )

    def test_missing_penalty_uses_target_section_not_later_mentions(self) -> None:
        rule = PenaltyRule(
            id="missing-water-change",
            description="example",
            points=4,
            section="Primary Diagnosis",
            missing_any=("water change",),
        )
        text = """## Primary Diagnosis
CO2 solenoid fault.

## Rejected Hypothesis
Water change dilution.
"""

        self.assertTrue(
            _penalty_triggered_with_artifacts(
                rule,
                _normalize(text),
                artifact_names=(),
                artifact_text="",
                sections=_extract_sections(text),
            )
        )


if __name__ == "__main__":
    unittest.main()
