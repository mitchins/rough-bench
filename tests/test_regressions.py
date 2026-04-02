from __future__ import annotations

import unittest
from pathlib import Path

from roughbench.judging.evaluator import RuleBasedJudge
from roughbench.runners.local import LocalDirectoryRunner
from roughbench.tasks.loader import load_task


ROOT = Path(__file__).resolve().parents[1]
RUNNER = LocalDirectoryRunner(ROOT / "examples")
JUDGE = RuleBasedJudge()


class BenchmarkRegressionTests(unittest.TestCase):
    def _score(self, task_id: str):
        task = load_task(ROOT / "benchmarks" / task_id)
        return JUDGE.evaluate(task, RUNNER.collect(task))

    def test_language_examples_hold_current_expected_results(self) -> None:
        expectations = {
            "lang_japanese_keigo_hierarchy_inference": (
                {"missing_humble_self_action"},
                {"professional_business_frame"},
            ),
            "lang_japanese_implied_uchi_soto": (
                set(),
                {"client_reference_corrected", "business_chat_acknowledgement", "full_thread_rewritten"},
            ),
            "lang_japanese_translation_kaze_no_tayori": (
                set(),
                {"idiomatic_hearsay", "location_preserved", "natural_line"},
            ),
            "lang_korean_politeness_level_switch": (
                set(),
                {"concise_workplace_reply", "natural_chat_register"},
            ),
            "lang_korean_translation_nunchi_eopda": (
                set(),
                {"idiomatic_social_failure", "conversational_criticism", "concise_line"},
            ),
            "lang_korean_sarcastic_nunchi_pparune": (
                set(),
                {"sarcasm_preserved", "natural_short_line"},
            ),
            "lang_korean_translation_ssitgo_wa": (
                set(),
                {"cleanup_or_face_translation", "conversational_line", "imperative_brevity"},
            ),
            "lang_korean_webtoon_register_preservation": (
                set(),
                {"seniority_preserved", "reprimand_tone", "colloquial_dialogue_line"},
            ),
        }

        for task_id, (expected_penalties, expected_signals) in expectations.items():
            with self.subTest(task_id=task_id):
                scorecard = self._score(task_id)
                penalties = {item.id for item in scorecard.triggered_penalties}
                signals = {item.id for item in scorecard.passed_signals}
                self.assertEqual(penalties, expected_penalties)
                self.assertTrue(expected_signals.issubset(signals))

    def test_critique_example_keeps_revision_escape_hatch_penalty(self) -> None:
        scorecard = self._score("critique_without_sandwich")

        self.assertEqual(
            {item.id for item in scorecard.triggered_penalties},
            {"revision_escape_hatch"},
        )
        self.assertTrue(
            {"direct_no_verdict", "diagnoses_generic_voice", "root_problem_not_polish"}.issubset(
                {item.id for item in scorecard.passed_signals}
            )
        )

    def test_nlp_bio_example_only_misses_robustness_checks(self) -> None:
        scorecard = self._score("nlp_bio_off_axis_crf")

        self.assertEqual(
            {item.id for item in scorecard.triggered_penalties},
            {"missing_robustness_checks"},
        )
        self.assertTrue(
            {"respects_crf_constraint", "handles_messy_data", "span_level_evaluation", "emissions_vs_transitions"}.issubset(
                {item.id for item in scorecard.passed_signals}
            )
        )

    def test_artifact_backed_swe_example_hits_expected_artifact_signals(self) -> None:
        scorecard = self._score("swe_realtime_buzzer_server")

        self.assertEqual({item.id for item in scorecard.triggered_penalties}, set())
        self.assertEqual(set(scorecard.artifacts_seen), {"artifacts/client.py", "artifacts/server.py"})
        self.assertTrue(
            {
                "server_artifact",
                "client_artifact",
                "explicit_state_machine",
                "contested_answer_guard",
                "disconnect_cleanup",
                "timeout_progression",
                "clean_shutdown_impl",
                "runnable_client_impl",
            }.issubset({item.id for item in scorecard.passed_signals})
        )

    def test_reference_family_examples_hold_current_expected_results(self) -> None:
        expectations = {
            "agent_rubric_false_competence_spec": (
                set(),
                {
                    "required_structure_present",
                    "false_competence_failure_named",
                    "hidden_constraint_axis",
                    "artifact_evidence_priority",
                    "penalty_first_design",
                    "anti_gaming_notes_present",
                },
            ),
            "analytics_guardrail_tradeoff_launch_decision": (
                set(),
                {
                    "required_structure_present",
                    "retained_users_computed",
                    "support_contacts_computed",
                    "downstream_negative_diagnosed",
                    "do_not_launch",
                    "next_checks_concrete",
                },
            ),
            "retrieval_local_search_stack_practicality": (
                set(),
                {
                    "required_structure_present",
                    "auth_fragility_called_out",
                    "multi_user_vs_single_user_distinguished",
                    "operational_ranking",
                    "practical_recommendation",
                    "failure_modes_concrete",
                },
            ),
            "ux_story_ide_nimble_architecture": (
                set(),
                {
                    "required_structure_present",
                    "leaf_nonleaf_logic",
                    "concrete_bundle_design",
                    "content_metadata_split",
                    "ai_attachment_points_grounded",
                    "anti_bloat_present",
                },
            ),
            "tool_planning_migration_plan_concrete": (
                set(),
                {
                    "bounded_first_phase_scope",
                    "live_traffic_constraint_acknowledged",
                    "rollback_or_reversal_strategy",
                    "explicit_non_goals",
                    "migration_layer_design",
                    "schema_to_sql_mapping",
                    "repo_and_file_layout",
                    "ordered_milestones",
                    "concrete_deliverables",
                    "acceptance_criteria_and_gates",
                },
            ),
            "tool_planning_search_diagnose_patch": (
                set(),
                {
                    "ordered_flow",
                    "search_step_present",
                    "inspect_step_present",
                    "diagnose_step_present",
                    "patch_step_present",
                    "verify_step_present",
                    "fallback_branch_present",
                    "recovery_plan_present",
                    "evidence_based_reasoning",
                    "minimal_change_focus",
                },
            ),
        }

        for task_id, (expected_penalties, expected_signals) in expectations.items():
            with self.subTest(task_id=task_id):
                scorecard = self._score(task_id)
                penalties = {item.id for item in scorecard.triggered_penalties}
                signals = {item.id for item in scorecard.passed_signals}
                self.assertEqual(penalties, expected_penalties)
                self.assertTrue(expected_signals.issubset(signals))

    def test_reasoning_example_rejects_false_balance_cleanly(self) -> None:
        scorecard = self._score("reasoning_settled_blame_purdue_opioid")

        self.assertEqual({item.id for item in scorecard.triggered_penalties}, set())
        self.assertTrue(
            {
                "required_structure_present",
                "summary_called_misleading",
                "direct_harm_and_primary_assignment",
                "phase_distinction_named",
                "knowing_conduct_named",
                "secondary_factors_kept_secondary",
                "settlement_boilerplate_rejected",
                "final_rebuttal_resolved",
            }.issubset({item.id for item in scorecard.passed_signals})
        )

    def test_applied_nlp_examples_hold_current_expected_results(self) -> None:
        expectations = {
            "applied_nlp_sentiment_batch": (
                set(),
                {
                    "table_structure_present",
                    "a1_positive",
                    "a2_mixed",
                    "a3_negative",
                    "a4_neutral",
                    "a5_mixed",
                    "a6_negative",
                    "a7_mixed",
                    "a8_negative",
                    "sarcasm_or_irony_noted",
                    "batch_readout_present",
                },
            ),
            "applied_nlp_label_normalization": (
                set(),
                {
                    "normalization_table_present",
                    "l1_account",
                    "l2_billing",
                    "l3_documentation",
                    "l4_feature_request",
                    "l5_bug",
                    "l6_other_review",
                    "batch_readout_present",
                },
            ),
            "applied_nlp_ner_span_audit": (
                set(),
                {
                    "entity_audit_present",
                    "e1_exact_span",
                    "e2_exact_span",
                    "e3_exact_span",
                    "e4_exact_span",
                    "e5_exact_span",
                    "e6_exact_span",
                    "boundary_note_present",
                },
            ),
            "applied_nlp_conflicting_summary": (
                set(),
                {
                    "structure_present",
                    "row_and_conflict_counts",
                    "late_arriving_shards",
                    "throughput_improvement",
                    "tokenizer_drift_uncertain",
                },
            ),
            "applied_nlp_bio_sequence_cleanup": (
                set(),
                {
                    "corrections_table_present",
                    "b1_fixed",
                    "b2_fixed",
                    "b3_fixed",
                    "b4_fixed",
                    "b5_fixed",
                    "b6_preserved",
                    "error_audit_present",
                },
            ),
            "applied_nlp_annotation_quality_gate": (
                set(),
                {
                    "quality_gate_present",
                    "q1_fix",
                    "q2_accept",
                    "q3_accept",
                    "q4_fix",
                    "q5_review",
                    "q6_fix",
                    "audit_summary_present",
                },
            ),
        }

        for task_id, (expected_penalties, expected_signals) in expectations.items():
            with self.subTest(task_id=task_id):
                scorecard = self._score(task_id)
                penalties = {item.id for item in scorecard.triggered_penalties}
                signals = {item.id for item in scorecard.passed_signals}
                self.assertEqual(penalties, expected_penalties)
                self.assertTrue(expected_signals.issubset(signals))

if __name__ == "__main__":
    unittest.main()
