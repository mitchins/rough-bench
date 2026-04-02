from __future__ import annotations

import unittest
from pathlib import Path

from roughbench.tasks.models import PenaltyRule, Rubric, SignalRule, TaskDefinition


class SignalRuleTests(unittest.TestCase):
    def test_from_mapping_reads_text_and_artifact_fields(self) -> None:
        rule = SignalRule.from_mapping(
            {
                "id": "signal",
                "description": "example",
                "any": ["alpha", "beta"],
                "all": "gamma",
                "groups": [["one", "two"], ["three"]],
                "artifact_any": ["report"],
                "artifact_text_any": ["needle"],
                "artifact_text_all": ["must", "have"],
                "artifact_text_groups": [["x"], ["y", "z"]],
            }
        )

        self.assertEqual(rule.any, ("alpha", "beta"))
        self.assertEqual(rule.all, ("gamma",))
        self.assertEqual(rule.groups, (("one", "two"), ("three",)))
        self.assertEqual(rule.artifact_any, ("report",))
        self.assertEqual(rule.artifact_text_any, ("needle",))
        self.assertEqual(rule.artifact_text_all, ("must", "have"))
        self.assertEqual(rule.artifact_text_groups, (("x",), ("y", "z")))


class PenaltyRuleTests(unittest.TestCase):
    def test_from_mapping_reads_present_missing_and_artifact_fields(self) -> None:
        rule = PenaltyRule.from_mapping(
            {
                "id": "penalty",
                "description": "example",
                "points": 3,
                "present_any": ["alpha"],
                "present_unnegated_any": ["beta"],
                "present_all": ["gamma", "delta"],
                "present_groups": [["one"], ["two", "three"]],
                "present_head_any": ["head"],
                "present_head_all": ["top"],
                "present_head_groups": [["start"]],
                "missing_any": ["miss"],
                "missing_all": ["all"],
                "missing_groups": [["g1"], ["g2"]],
                "missing_head_any": ["head-miss"],
                "missing_head_all": ["head-all"],
                "missing_head_groups": [["head-group"]],
                "missing_artifacts_any": ["artifact.py"],
                "present_artifact_text_any": ["needle"],
                "present_artifact_text_all": ["must", "exist"],
                "present_artifact_text_groups": [["x"], ["y"]],
                "missing_artifact_text_any": ["nope"],
                "missing_artifact_text_all": ["gone"],
                "missing_artifact_text_groups": [["g"]],
            }
        )

        self.assertEqual(rule.points, 3)
        self.assertEqual(rule.present_any, ("alpha",))
        self.assertEqual(rule.present_unnegated_any, ("beta",))
        self.assertEqual(rule.present_all, ("gamma", "delta"))
        self.assertEqual(rule.present_groups, (("one",), ("two", "three")))
        self.assertEqual(rule.missing_artifacts_any, ("artifact.py",))
        self.assertEqual(rule.present_artifact_text_groups, (("x",), ("y",)))
        self.assertEqual(rule.missing_artifact_text_groups, (("g",),))


class RubricAndTaskDefinitionTests(unittest.TestCase):
    def test_rubric_from_mapping_builds_rules(self) -> None:
        rubric = Rubric.from_mapping(
            {
                "signals": [{"id": "s1", "description": "signal", "any": ["alpha"]}],
                "penalties": [{"id": "p1", "description": "penalty", "points": 2, "missing_any": ["beta"]}],
            }
        )

        self.assertEqual(len(rubric.signals), 1)
        self.assertEqual(len(rubric.penalties), 1)
        self.assertEqual(rubric.signals[0].id, "s1")
        self.assertEqual(rubric.penalties[0].id, "p1")

    def test_task_definition_carries_family_and_counted_metadata(self) -> None:
        task = TaskDefinition(
            id="task",
            title="Task",
            domain="demo",
            family="demo_family",
            prompt="Prompt",
            intent="Intent",
            counted=False,
            path=Path("benchmarks/task"),
        )

        self.assertEqual(task.family, "demo_family")
        self.assertFalse(task.counted)


if __name__ == "__main__":
    unittest.main()
