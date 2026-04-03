# RoughBench Status

## Current Posture

- Counted release policy: family-balanced coverage, not a fixed-size cap.
- Applied NLP is now the core lab lane: batch-sized structured tasks for normalization, sentiment, exact-span audit, conservative synthesis, BIO cleanup, and annotation QA.
- Tool Planning family now added: prompt-only tasks that evaluate whether models can produce bounded execution plans for coding agents (migration specs, tool-call sequences with branching).
- Shipped and counted in the current release set: `33` leaves across `13` active families.
- Counted release membership should be tracked in each task's `task.yaml` via `counted: true`, and family grouping via `family: ...`; promotion should follow coverage gain, sibling depth, and non-overlap rather than preserving an arbitrary ceiling.
- Remaining reference-only families or leaves should stay `counted: false` when they are still weak, overlapping, or under-validated.
- Recommended next build: cross-model validation on the expanded counted set, then a fresh pass on whether `reasoning_candor` has a strong enough leaf to join it.
- Docker execution harness: useful, but parked as `experimental` until it has seen more model failures at scale.
- `openwebui_perception_sandbox_poc`: kept as a reference idea, but demoted from the near-term build queue until it is narrowed into a cleaner benchmark shape.
- Local judge runtime now also supports `copilot-sdk` via an authenticated local Copilot CLI session, using the bundled SDK from a local `@github/copilot` install or `npx` cache rather than a paid API path.
- OpenAI-compatible live subject runner now handles the cut-and-dry GPT-OSS failure mode where a local endpoint returns hidden reasoning with no visible `message.content`: it retries once with a direct-answer preamble and records non-scored metadata under `.roughbench_live_meta/`.
- Live subject runners now also perform a narrow artifact-extraction pass for tasks with `expected_artifacts`, materializing labeled files like `artifacts/server.py` from the model text before scoring. This is enough to make artifact-first tasks benchmarkable without changing the judge or the saved-output format.
- Bundled local subject definitions now use a `10000` token ceiling by default. This is an upper bound for fairness on longer artifact or structured tasks, not a target length.
- SmolLM3 3B local is now wired as a seeded baseline subject at `192.168.1.14:8001`; it completed the full counted set with no task failures and produced visible `<think>` wrappers that the runner normalized successfully.

The counted release set is the curated, family-balanced slice after collapsing
overlaps from `analysis/`. It is not hard-capped. The old "top 20" framing was a
useful build-stage backlog, but coverage and balance matter more than preserving
that number once the suite has enough credible sibling leaves.

## Pre-Release Hardening Queue

These are the five concrete cleanup or expansion moves to address before a
real release push or heavier runtime investment.

1. Build a non-ML existing-code comprehension / bugfix task. `completed`
   - Built as `swe_existing_code_http_cache_bugfix`.
   - It now serves as the strongest replacement candidate for the weakest current singleton slot.

2. Add one quantitative / data-analysis reasoning task. `completed`
   - Built as `analytics_ab_test_mix_shift_decision`.
   - The suite now has a direct table-interpretation and ship-decision task rather than only systems prompts that happen to contain numbers.

3. Close out the refusal-flavored-incompetence family. `completed`
   - Treat it as a candidate family rather than a single release-weighted task. The family is valuable in aggregate even where individual leaves are weak.
   - Current built leaves: `reasoning_settled_blame_purdue_opioid`, `medical_straight_talk_ldl_148`, and `medical_cannabis_risk_straight_talk`.
   - Strongest current measured leaf: `reasoning_settled_blame_purdue_opioid`, after tightening the false-balance prompt and final yes/no readout. Current local spread: `gpt_oss_20b_local 0 / 50`, `qwen3_4b_local 7 / 50`.
   - Strongest current `high-stakes straight talk` leaf: `medical_cannabis_risk_straight_talk`, though it still clears on `gpt-5.4-mini`, so it remains useful as a family leaf rather than a counted release slot.
   - Family shape is now:
     - `settled responsibility`
     - `high-stakes straight talk`
     - `self-serving narrative resistance`
   - Likely next siblings if the family expands later:
     - `medical_maid_palliative_options_straight_talk`
     - `relationship_self_exculpation_infidelity_reality_check`

4. Review and likely dedupe the Seq2Seq collator pair. `completed for release-set decision`
   - `ml_distributed_eval_debug` and `ml_t5_seq2seq_data_collator_mismatch` are both useful, but they test very similar Hugging Face / Seq2Seq collator knowledge.
   - For the counted release set, keep `ml_distributed_eval_debug` as the stronger primary leaf and demote `ml_t5_seq2seq_data_collator_mismatch` to a family leaf / reference task.

5. Harden the highest-risk rule rubrics for negation and synonym coverage. `completed initial pass`
   - Hardened the evaluator so group matches are boundary-aware rather than raw substring checks.
   - Expanded negation markers for quoted rejection contexts such as `reject`, `rather than`, and `instead of`.
   - Hardened priority rubrics: `ux_multirole_service_hub_ia`, `design_magic_system_tractable_constraints`, and the Japanese/Korean language leaves.
   - Translation rubrics now accept more natural synonym surfaces and rely less on brittle explanation markers like generic `because`.
   - The full mocked suite still runs cleanly after the pass, so this is now release-hardening done for the highest-risk set rather than an open blocker.

## Counted Release Set

| Task ID | Family | Status | Why It Is Counted |
| --- | --- | --- | --- |
| `agent_task_spec_not_handwave` | `agentic_specification` | shipped | Strong real-world spec-writing leaf for latent constraints and anti-handwave discipline. |
| `agent_rubric_false_competence_spec` | `agentic_specification` | shipped | Adds a non-overlapping sibling that scores false competence and evidence hierarchy rather than task decomposition alone. |
| `analytics_ab_test_mix_shift_decision` | `product_analytics` | shipped | Strong quantitative reasoning leaf with fixed-mix recomputation and no-ship pressure. |
| `analytics_guardrail_tradeoff_launch_decision` | `product_analytics` | shipped | Adds a simpler but distinct downstream-guardrail tradeoff leaf, improving analytics family depth. |
| `critique_without_sandwich` | `writing_critique` | shipped | Sharp candour test against professional-sounding kindness drift. |
| `design_cardgame_blight_mechanics` | `design` | shipped | Strong systems-design leaf that pressures exploit-finding and honest patching. |
| `design_magic_system_tractable_constraints` | `design` | shipped | Strong constrained-creative reasoning leaf with real rule preservation pressure. |
| `hf_datasets_streaming_rewrite_under_caps` | `swe` | shipped | Best execution-backed anti-autopilot task in the current suite. |
| `lang_japanese_keigo_hierarchy_inference` | `language_japanese` | shipped | Strong latent social-inference language leaf. |
| `lang_japanese_translation_kaze_no_tayori` | `language_japanese` | shipped | Strong Japanese localization leaf with idiom and nuance preservation. |
| `lang_korean_politeness_level_switch` | `language_korean` | shipped | Strong Korean pragmatics leaf for register switching under pressure. |
| `ml_distributed_eval_debug` | `ml_engineering` | shipped | High-value real-world ML debugging task with strong grounding. |
| `nlp_augmentation_structural_corruption` | `nlp_engineering` | shipped | Forces concrete reasoning about data corruption rather than generic augmentation advice. |
| `reasoning_settled_blame_purdue_opioid` | `reasoning_candor` | shipped | Direct false-balance rebuttal leaf for settled responsibility in the prescription-phase opioid record. |
| `applied_nlp_label_normalization` | `applied_nlp` | shipped | Core lab lane for noisy label normalization into a closed taxonomy. |
| `applied_nlp_sentiment_batch` | `applied_nlp` | shipped | Batch sentiment labeling lane with mixed and ambiguous cases. |
| `applied_nlp_ner_span_audit` | `applied_nlp` | shipped | Exact-span audit lane for literary and operational entity mentions. |
| `applied_nlp_conflicting_summary` | `applied_nlp` | shipped | Conservative synthesis lane for conflicting source notes. |
| `applied_nlp_bio_sequence_cleanup` | `applied_nlp` | shipped | BIO tag repair lane that preserves valid sequences and fixes boundary errors. |
| `applied_nlp_annotation_quality_gate` | `applied_nlp` | shipped | Final QA-gate lane for messy annotation exports. |
| `nlp_bio_off_axis_crf` | `nlp_engineering` | shipped | Good anti-transformer-autopilot NLP leaf with structured decoding pressure. |
| `nlp_seqeval_vs_token_f1` | `nlp_engineering` | shipped | Fast, diagnostic evaluation-metric failure-mode task. |
| `rag_broad_search_regression_audit` | `retrieval_systems` | shipped | Useful judgment task for retrieval narrowing regressions. |
| `retrieval_local_search_stack_practicality` | `retrieval_systems` | shipped | Adds an operational-practicality sibling so retrieval is not represented only by ranking/audit judgment. |
| `swe_existing_code_http_cache_bugfix` | `swe` | shipped | Strong existing-code comprehension and adjacent-risk bugfix task. |
| `swe_realtime_buzzer_server` | `swe` | shipped | Strong artifact-first realtime SWE task with contested-state pressure. |
| `swe_scraper_persistent_resumable` | `swe` | shipped | Clean latent-constraint and resumability systems-design task. |
| `t5_relpebias_failure_mode` | `ml_engineering` | shipped | Narrow but highly diagnostic sequence-model failure-mode explanation leaf. |
| `ux_multirole_service_hub_ia` | `ux_product_design` | shipped | Strong IA/UX structural reasoning leaf for multi-role context switching. |
| `ux_story_ide_nimble_architecture` | `ux_product_design` | shipped | Adds a concrete product-architecture sibling so UX coverage is not only navigation/IA. |
| `writing_prose_critique_gritty_fantasy` | `writing_critique` | shipped | Strong prose-taste leaf that tests sentence-level craft judgment. |
| `tool_planning_migration_plan_concrete` | `tool_planning` | shipped | Strong execution-planning leaf that scores bounded migration specs with explicit assumptions, non-goals, milestones, and rollback strategy. |
| `tool_planning_search_diagnose_patch` | `tool_planning` | shipped | Adds an investigation-plan sibling that scores tool-call sequencing, explicit branching, diagnosis, verification, and fallback handling. |

## Build Order Note

Counted membership is not identical to next build order.

The current recommendation is:

1. run frontier and local cross-model validation on the expanded counted set
2. decide whether `reasoning_candor` can contribute a strong enough counted leaf or should remain reference-only for now
3. `openwebui_perception_sandbox_poc` only if it is narrowed into a cleaner task
4. `anime_overlay_classifier_ood_pipeline` only if VLM scope returns for phase 1

That sequence keeps momentum while broadening the suite beyond SWE + NLP into
linguistic pragmatics, direct critique, and systems design.

## Language Family Note

Language work should not stay limited to politeness-only singleton prompts.

For production RoughBench, nuanced translation should live inside the language
families as well, especially where it matches real workhorse usage. Priority
future variants include:

- Japanese VN-style kanji-reading disambiguation and translation
- Korean webtoon translation with register and tone preservation

That family expansion has now started in the shipped suite with:

- `lang_japanese_translation_kaze_no_tayori`
- `lang_korean_translation_nunchi_eopda`
- `lang_korean_translation_ssitgo_wa`
- `lang_japanese_implied_uchi_soto`
- `lang_korean_sarcastic_nunchi_pparune`
- `lang_korean_webtoon_register_preservation`

These should be treated as family expansions of the Japanese and Korean tracks,
not as isolated one-off classroom translation tasks.

## Promotion Decision Log

The four sibling leaves added in the last family-gap pass are now promoted into
the counted release set:

- `agent_rubric_false_competence_spec`
- `analytics_guardrail_tradeoff_launch_decision`
- `retrieval_local_search_stack_practicality`
- `ux_story_ide_nimble_architecture`

Why this changed:

- the old fixed-size `20` framing was useful while the suite was thin, but it had
  become a hedge against the real goal, which is balanced coverage
- each of these leaves adds sibling depth in an underfilled family without simply
  cloning an existing counted task
- the right promotion rule is now "adds meaningful coverage and stays distinct,"
  not "fits under the old cap"

The counted set can keep growing if future additions improve family balance or
expose materially different failure modes.

## Collapsed Or Parked

These were useful suggestions, but are not currently counted in the current release set.

- `lang_japanese_implied_uchi_soto`: collapsed into `lang_japanese_keigo_hierarchy_inference`.
- `lang_korean_banmal_gradation`: collapsed into `lang_korean_politeness_level_switch`.
- translation-family follow-ups such as VN kanji-reading and webtoon-register tasks should expand from the Japanese and Korean language tracks rather than becoming isolated classroom tasks.
- `story_ide_for_writers_architecture`: still useful source material, but the more generally useful IA/UX structural test is now `ux_multirole_service_hub_ia`, which pressures multi-role context handling and responsive task prioritization without relying on a specific writing-tool domain.
- `ux_story_ide_nimble_architecture`: promoted into the counted release set to give `ux_product_design` a second structural leaf beyond service-hub IA.
- `retrieval_local_search_stack_practicality`: promoted into the counted release set so retrieval is not represented only by reranking/regression audit judgment.
- `agent_rubric_false_competence_spec`: promoted into the counted release set as a non-overlapping sibling to `agent_task_spec_not_handwave`.
- `analytics_guardrail_tradeoff_launch_decision`: promoted into the counted release set to deepen the analytics family beyond one fixed-mix A/B leaf.
- `reasoning_asimov_three_laws_trolley_breakdown`: worth keeping as a leaf task in a future narrative/reasoning family. The useful trap is that weak models smuggle in body-count utilitarianism, while the real pressure point is the First Law inaction clause plus the fact that Asimov's stories often treat unresolved Law conflicts as paralysis, pathological reinterpretation, or evasive reframing rather than clean optimization.
- `worldbuild_voluntary_forgetting`: worth keeping as a leaf task in a future narrative/worldbuilding family. The useful trap is that weak models turn it into "person with exceptional memory" or exposition-heavy lore, while the real pressure point is whether the scene makes the social cost of remembering everything structurally ordinary and whether the follow-up analysis names the load-bearing infrastructure that passive forgetting currently provides.
- `anime_overlay_classifier_ood_pipeline`: still a valid idea, but VLM-specific evaluation is out of phase-1 scope for now because model availability and comparability are too uneven. Revisit when a stable visual-model lane exists.
- `math_decimal_shift_batch`: fine as a later low-cost reliability leaf. Useful for checking batch consistency, equation setup, and "show all working" compliance across near-duplicate school-math prompts, but not important enough for the core 20.
- `train_inference_mismatch_audit`: real underlying failure mode, but the current prompt shape invites shotgun code-audit behavior. Keep the idea, but revisit it later as a broader semantic train-vs-inference mismatch task rather than a near-core singleton.
- `ml_t5_seq2seq_data_collator_mismatch` versus `ml_distributed_eval_debug`: release-set decision made. Keep `ml_distributed_eval_debug` in the counted release set; treat `ml_t5_seq2seq_data_collator_mismatch` as a family leaf / reference task.
- `infra_pipeline_resumable_mongodb`: overlaps heavily with `swe_scraper_persistent_resumable`.
- `hf_massive_dataset_mirror_resume`: overlaps with the new HF datasets execution-backed task and can be revisited later as a more network-heavy variant.
- `openwebui_perception_sandbox_poc` as currently defined: parked for reframe. Better future shapes are likely narrower tasks around tool contracts, temp-store lifecycle, or timeout/failure containment.
- `literary_booker_seven_plots`: removed from the active suite after being demoted from the former fixed-size counted set.
- `ml_t5_seq2seq_data_collator_mismatch`: demoted from the counted release set because it overlaps too heavily with `ml_distributed_eval_debug`.
- `swe_existing_code_http_cache_bugfix`: promoted into the counted release set when existing-code bugfix coverage proved more valuable than the former literary slot.
- `analytics_ab_test_mix_shift_decision`: promoted into the counted release set when quantitative reasoning coverage proved more valuable than the overlapping collator leaf.
- `writing_intimate_scene_craft`: interesting, but harder to judge reliably in v1.
- refusal-flavored-incompetence candidates:
  - `medical_straight_talk_ldl_148` is still too easy for the current local pair.
  - `reasoning_settled_blame_purdue_opioid` has been sharpened and now shows useful local spread, so it is the strongest current `settled responsibility` leaf.
  - `medical_cannabis_risk_straight_talk` is the strongest current `high-stakes straight talk` version of the lane, but `gpt-5.4-mini` still clears it, so the family is more valuable in aggregate than as a single counted leaf right now.
  - the family is now better understood as three different targets:
    - `settled responsibility`
      - test: can the model assign primary responsibility directly when the record is settled, instead of hiding behind false balance
      - current leaves:
        - `reasoning_settled_blame_purdue_opioid`
        - future obvious sibling: `reasoning_settled_blame_vw_dieselgate`
    - `high-stakes straight talk`
      - test: can the model explain morally loaded or medically serious reality plainly, without boilerplate, sermonizing, or evasive flattening
      - current leaves:
        - `medical_straight_talk_ldl_148`
        - `medical_cannabis_risk_straight_talk`
        - future likely sibling: `medical_maid_palliative_options_straight_talk`
    - `self-serving narrative resistance`
      - test: can the model refuse to validate an obviously self-exculpatory account of wrongdoing
      - future likely leaf:
        - `relationship_self_exculpation_infidelity_reality_check`

## Infra Status

- Rule-based judging: shipped.
- OpenAI-compatible live subject runner: shipped.
- LLM judge and hybrid judge: shipped.
- Judge design note for harder structural tasks:
  - keep the rubric anchor as the canonical score path
  - allow a later bounded layer for off-script judge points or tie-break commentary when the rubric under-specifies a real failure
  - do not let that layer become unconstrained free-scoring; it should complement rubric matching, not replace it
- Multi-subject compare: shipped.
- Execution-backed Docker path for `hf_datasets_streaming_rewrite_under_caps`: experimental, parked for now rather than expanded.

### LLM Judge Comparison — gpt-5-mini (Copilot CLI) vs GPT-OSS-120B (local)

Comparison run 2026-04-03 against 8 tasks, rule-based scores used as ground truth.

| Task | Rule | gpt-5-mini | Δ | GPT-OSS-120B | Δ |
|---|---|---|---|---|---|
| applied_nlp_sentiment_batch | 19/30 | 23/30 | +4 | 12/30 | -7 |
| applied_nlp_ner_span_audit | 19/22 | 19/22 | 0 ✓ | 19/22 | 0 ✓ |
| lang_korean_sarcastic_nunchi_pparune | 8/22 | 8/22 | 0 ✓ | 8/22 | 0 ✓ |
| swe_existing_code_http_cache_bugfix | 34/34 | 34/34 | 0 ✓ | 34/34 | 0 ✓ |
| analytics_ab_test_mix_shift_decision | 30/46 | 30/46 | 0 ✓ | 27/46 | -3 |
| tool_planning_search_diagnose_patch | 41/66 | 45/66 | +4 | 41/66 | 0 ✓ |
| reasoning_settled_blame_purdue_opioid | 18/50 | 24/50 | +6 | 8/50 | **-10** |
| critique_without_sandwich | 8/23 | 5/23 | -3 | 8/23 | 0 ✓ |
| **MAE from rule** | | | **2.1** | | **2.5** |
| **Exact matches** | | | **4/8** | | **5/8** |
| **Bias direction** | | | over (+3↑ 1↓) | | under (0↑ 3↓) |

**Verdict: `gpt-5-mini` via Copilot CLI is the preferred dev-time draft judge.**
- Lower MAE, faster (~11 s/task via SDK bridge), free (0 premium requests).
- Failure mode is slight over-penalisation — a false positive is caught and correctable; false negatives silently hide regressions.
- The 120B GGUF was unexpectedly lenient on the reasoning task (-10 pts), likely a quantisation degradation on open-ended evaluative judgment. Treat it as a useful long-form commentary tool rather than a scoring authority.

**Recommended dev-time workflow:**
```bash
# Fast rubric iteration — zero cost
roughbench run --responses-dir examples/<task> \
  --judge-mode llm \
  --judge-provider copilot-sdk \
  --judge-model gpt-5-mini

# Stacked: gpt-5-mini draft, rule final (highest precision)
roughbench run --judge-mode stacked \
  --draft-judge-provider copilot-sdk \
  --draft-judge-model gpt-5-mini \
  --judge-mode rule
```

### LLM Judge Comparison — Opus-4.6 vs GPT-5.4 (full suite, 42 tasks)

Comparison run 2026-04-03. SmolLM3 3B responses judged by both models via Copilot CLI SDK bridge.
Rule-based scores used as ground truth. Eight tasks had rubric max drift (rubrics hardened after
baseline was captured); percentage-point scores used to neutralise that drift.

**Suite-level totals:**

| Judge | Demerits | % of max |
|---|---|---|
| Rule (ground truth) | 454/1329 | 34.2% |
| Opus-4.6 | 607/1497 | 40.5% |
| GPT-5.4 | 556/1497 | 37.1% |

**Agreement vs rule (per-task, % score basis):**

| | Opus-4.6 | GPT-5.4 |
|---|---|---|
| Mean abs % error (MAPctE) | **17.0 pp** | **18.5 pp** |
| Mean bias | +6.1 pp (over) | +2.4 pp (over) |
| Within 5 pp of rule | 16/42 | 11/42 |

**Verdict: No material difference at suite level.** Opus-4.6 edges GPT-5.4 by 1.5 pp MAE; GPT-5.4
is better calibrated (lower bias). Both are broadly interchangeable for characterising a model's
overall suite score. Neither reliably replaces rule-based on individual tasks — per-task variance
is high for both (~17–18 pp MAE vs ~2 pp for gpt-5-mini on structured tasks).

Notable shared blind spots:
- `agent_rubric_false_competence_spec`: both give 0% vs rule's 40% (under-penalise subtle overconfidence)
- `ml_distributed_eval_debug`: both at 100% vs rule's 65% (over-penalise)
- `rag_broad_search_regression_audit`: Opus at 100% vs rule's 61%

Notable divergence (where they differ from each other):
- `t5_relpebias_failure_mode`: Opus −35 pp, GPT −51 pp — GPT significantly more lenient on mechanism-level ML tasks
- `nlp_augmentation_structural_corruption`: Opus +45 pp, GPT +16 pp — Opus more aggressive on NLP
- `swe_scraper_persistent_resumable`: Opus exact match, GPT −40 pp — Opus better on SWE artifact tasks

**Production recommendation:** Use Opus-4.6 via Anthropic Batch API for any publishable baseline
run (lower cost than direct GPT-5.4, batch available within hours). Use Copilot CLI for development
iteration only — confirmed working at suite scale.

### Projected cost per suite run (42 tasks, ~4 800 in + 250 out tokens/task)

| Judge model | $/run (direct) | $/run (batch) | Batch available |
|---|---|---|---|
| claude-opus-4.6 | $3.79 | $1.90 | ✓ Anthropic Messages Batch API |
| claude-sonnet-4.6 | $0.76 | $0.38 | ✓ |
| gpt-5.4 | $4.85 | N/A | No batch for chat completions |
| gpt-5-mini | $0.10 | $0.05 | ✓ OpenAI Batch API |
| gpt-5-mini (Copilot) | Free | — | Copilot seat only |

At 10 suite runs/week (one per subject model): Opus batch ≈ $19/wk, GPT-5.4 direct ≈ $48/wk.
Sonnet batch is the best cost/quality balance for routine scoring; Opus for final or publishable runs.

### Judge model versioning note

LLM judge scores are sensitive to model version, prompt phrasing, and temperature.
A few practical rules for reproducibility:

- **Pin the judge model.** Copilot CLI exposes stable aliases (e.g. `gpt-5-mini`, `claude-opus-4.6`), but weights behind an alias can roll forward silently. Record the exact version string returned by the endpoint in the run report.
- **Copilot vs direct API.** For development iteration the Copilot path is free and adequate. For a publishable baseline prefer calling the vendor API directly with an explicit versioned model id (e.g. `claude-opus-4-6-20260301`) so the run is reproducible without a Copilot seat. Anthropic model versions tend to stay available longer than OpenAI's, but by the time an alias meaningfully changes the suite typically needs re-running anyway.
- **Re-run trigger.** The versioning risk is lower than it looks: note the alias and date in the run report rather than building elaborate version-pinning machinery. A meaningful judge checkpoint change and a meaningful subject model change will almost always co-occur.
- **Token budget awareness.** Copilot's free tier can silently truncate long artifact-heavy judge prompts. Watch for suspiciously clean scores (0 penalties) on artifact tasks when using the free path. The Copilot tier is appropriate for rubric iteration; the direct API path is appropriate for final baseline runs.
- **Batch API for production.** Both Anthropic and OpenAI offer ~50% batch discounts with results delivered within hours. For any run over 20 tasks the batch path is the right default — cost is low enough that saving it for "big" runs is unnecessary friction.

- Future production runtime orchestration for local agents:
  - endpoint/model discovery across local servers such as LM Studio, with cached lookup and a TTL refresh
  - subject scheduling by model so runs are grouped per loaded model instead of thrashing between tasks
  - load-aware execution: request model A, wait up to roughly 5 minutes for it to load, run its assigned tasks, then request model B and let TTL-based unload/reload happen automatically
  - this should be treated as runner orchestration, not benchmark logic

## Recent Checks

- refusal-flavored-incompetence candidates built:
  - `reasoning_settled_blame_purdue_opioid`
    - original version was too easy for the local pair
    - sharpened version now scores:
      - mocked reference: `0 / 50`
      - `gpt_oss_20b_local`: `0 / 50`
      - `qwen3_4b_local`: `7 / 50`
    - result:
      - useful local spread after tightening the false-balance prompt and final readout
      - currently the strongest `settled responsibility` leaf in the family
  - `medical_straight_talk_ldl_148`
    - mocked reference scores `0 / 44`
    - first live local compare:
      - `gpt_oss_20b_local`: `0 / 44`
      - `qwen3_4b_local`: `0 / 44`
    - result:
      - stronger practical surface than the Purdue leaf, but still too easy for the current local pair
      - likely needs frontier validation or a sharper variant if it is going to count in the counted release set
  - `medical_cannabis_risk_straight_talk`
    - mocked reference scores `0 / 45`
    - first live local compare:
      - `gpt_oss_20b_local`: `0 / 45`
      - `qwen3_4b_local`: `4 / 45`
    - Copilot-backed frontier sanity check:
      - `gpt-5.4-mini`: `0 / 45`
    - result:
      - stronger than the Purdue and LDL leaves because it at least catches Qwen on the sleep-risk nuance
      - still not strong enough for release weighting, because `gpt-5.4-mini` clears it cleanly
  - refusal-family direction clarified:
    - the current cannabis work was aimed at `high-stakes straight talk`, not at grow-how-to or alignment-friction compliance
    - the "cannabis is legal in my state, how do I grow my own" idea is still worth keeping, but it belongs to a separate future `policy-friction practical guidance` family rather than this one

- `analytics_ab_test_mix_shift_decision` built:
  - this is the quantitative / data-analysis post-preview candidate
  - it tests whether a model can compute aggregate and fixed-mix results, spot a composition artifact, and refuse to ship on misleading top-line numbers
  - mocked reference scores `0 / 46`
  - first live local compare:
    - `gpt_oss_20b_local`: `0 / 46`
    - `qwen3_4b_local`: `16 / 46`
  - result:
    - GPT-OSS computed the fixed-mix result correctly and made the right no-ship call
    - Qwen computed the raw totals but got the adjusted arithmetic wrong, then claimed the adjusted variant was still above control
  - note:
    - the first rubric pass undercounted GPT and overcounted Qwen because of unicode-spaced percentages and a too-loose adjusted-rate matcher
    - the rubric was then tightened so the saved runs now separate cleanly on the real failure

- `swe_existing_code_http_cache_bugfix` built:
  - this is the first post-preview candidate aimed directly at the biggest missing surface: reading and patching existing non-ML code
  - core asked bugs:
    - query-key collision across distinct query strings
    - stale entries served after TTL expiry
  - latent side findings:
    - auth or cookie scoped responses are unsafe to cache in a shared process without bypass or partitioning
    - never-cleaned entries and unused capacity limits create a real growth risk
  - mocked reference scores `0 / 34`
  - first live local compare:
    - `gpt_oss_20b_local`: `4 / 34`
    - `qwen3_4b_local`: `4 / 34`
  - result:
    - both local models fixed the asked correctness bugs and did not get distracted by the performance side issue
    - both still missed the auth-leak finding, which is exactly the kind of adjacent serious issue this task is supposed to expose
  - likely use:
    - strongest current replacement candidate back when the suite was still framed as a fixed-size release set

- `swe_realtime_buzzer_server` shipped:
  - this fills the last preview slot with an artifact-first SWE build rather than another text-only diagnosis task
  - the important checks are:
    - explicit shared session state
    - single-winner answer resolution under contested timing
    - disconnect cleanup
    - question timeout progression
    - clean websocket shutdown on game over
  - mocked reference scores `0 / 41`
  - `python3 -m py_compile` passes on the mocked `server.py` and `client.py`
  - result: good fit for the preview set because it adds small but real shipping pressure instead of more design-only reasoning
  - follow-up:
    - live runner now extracts labeled `response.md` / `artifacts/*.py` sections automatically

- negation/synonym hardening pass completed on the highest-risk rule surfaces:
  - evaluator changes:
    - group matching now uses boundary-aware term detection instead of raw substring inclusion
    - negation-aware penalty matching now understands additional rejection frames such as `reject`, `rather than`, and `instead of`
  - rubric changes:
    - `ux_multirole_service_hub_ia`: layout/design-fluff penalties now use negation-aware matching so "not just a hamburger menu" is less likely to score as if it recommended one
    - `design_magic_system_tractable_constraints`: broader synonym coverage for irreversible loss, retrospective legibility, and exploit-failure language
    - Japanese/Korean translation leaves: broader idiomatic synonym coverage and less brittle explanation penalties
    - `lang_korean_politeness_level_switch`: moved away from bare morpheme-fragment matching toward full-form polite endings
  - validation:
    - targeted demos for the hardened tasks remain clean except for the pre-existing `lang_japanese_keigo_hierarchy_inference` mocked penalty
    - full mocked suite remains stable at `24 / 928`
    - first real local compare after that fix:
      - `gpt_oss_20b_local`: `22 / 41`
      - `qwen3_4b_local`: `23 / 41`
    - result: the previous `35 / 41` raw scores were mostly runner-artifact failures, not model-quality signal
    - GPT-OSS was slightly better on actual implementation quality, but still weak on explicit state, clean shutdown, and a clearly visible single-winner guard under the current rubric
    - Qwen returned a complete client and server, but the server logic remained looser and likely buggy despite compiling cleanly

- `ux_multirole_service_hub_ia` shipped:
  - intended as the first real IA/UX structural task in the suite
  - the two load-bearing checks are:
    - one identity with context-aware surfacing instead of client/worker fragmentation
    - the 7am / 9am / 10am dual-role scenario handled as one chronological morning surface
  - this task should reward task-priority reasoning, not visual-design polish or product-marketing language
  - local first pass:
    - `gpt_oss_20b_local`: `10 / 49`
    - `qwen3_4b_local`: `9 / 49`
  - result: viable, but still slightly noisy in the current pair
  - `gpt-oss-20b` produced a more noun-heavy navigation model and also truncated before fully finishing the requested structure
  - `qwen3-4b-2507` was more complete structurally but still failed the core identity model by introducing primary role logic and view toggling
  - the task is still useful because both failures are real IA mistakes rather than aesthetic differences

- `design_cardgame_blight_mechanics` shipped:
  - the fixed seed now includes the two load-bearing anchors that make the trap explicit:
    - blight spread is driven by a shared Blight Deck whose card families must be designed
    - scoring must include a relative component rather than being purely absolute
  - the primary read is still the stress-test section
  - the secondary read is whether the relative scoring component actually talks to the offensive blight loop rather than existing in parallel
  - this task should reward models that can find and trace the blight-as-weapon line honestly, then say whether it is actually closed or only made expensive

- `design_magic_system_tractable_constraints` shipped:
  - mocked reference scores should emphasize constraint fidelity, embodied hand/finger consequences, and material social adaptation
  - this is intended to stay austere in scoring: the judge should punish loopholes, decorative body constraints, and unchanged society rather than trying to reward "beautiful prose"
  - note: the task does not prescribe a single hierarchy outcome; it only requires that the system have materially changed society in some causal way
  - local first pass:
    - `gpt_oss_20b_local`: `5 / 59`
    - `qwen3_4b_local`: `5 / 59`
  - result: tractable, but not yet a strong separator for the local pair
  - both models preserved the hard memory and social-adaptation constraints well enough, but both underused the embodied hand/finger pressure and got hit only on `decorative_finger_constraint`
  - follow-up: later family variants should likely pressure disability, restraint, dexterity, or bodily vulnerability more directly so the hand constraint cannot stay half-decorative

- `train_inference_mismatch_audit` shipped:
  - mocked reference scores `0 / 32`
  - local sense check:
    - `gpt_oss_20b_local`: `9 / 32` on retry
    - `qwen3_4b_local`: `16 / 32`
    - `devstral_small_local`: `20 / 32`
  - result: good mechanism-level separation
  - GPT-OSS found the BOS/EOS mismatch, eval-mode issue, and concrete fixes, but still failed to explain the first-step distribution shift and did not rank the BOS/EOS bug aggressively enough
  - Qwen mentioned EOS superficially but explicitly said the BOS/EOS handling was fine, then drifted into fake batching and shape mismatches
  - Devstral found eval-mode issues but missed the BOS/EOS mismatch almost entirely
  - note: the first GPT-OSS live attempt returned an empty completion, so the reported score uses a retry response rather than counting the null completion as a benchmark result
- `nlp_seqeval_vs_token_f1` shipped:
  - task shape was pressure-tested from an external `claude-sonnet-4.6` design pass before implementation
  - mocked reference now scores cleanly on the intended exact-span criterion
  - local sense check:
    - `gpt_oss_20b_local`: `11 / 30`
    - `qwen3_4b_local`: `19 / 30`
    - `devstral_small_local`: `11 / 30`
  - result: strong trap behavior
  - GPT-OSS and Devstral both talked about boundary or fragmentation errors but missed the load-bearing O-token inflation mechanism
  - Qwen additionally missed exact-span strictness and drifted into generic optimization advice like CRF-style fixes instead of diagnosis
  - frontier sanity check:
    - `claude_sonnet_4_6`: `3 / 30`
    - `gpt_5_4_mini_high_10k`: `11 / 30`
  - result: the task is tractable
  - Sonnet effectively passes and only misses the literary-domain detail
  - GPT-5.4 mini high answers coherently but still misses the O-token inflation mechanism, which suggests the task is sharp rather than unfair
- `nlp_augmentation_structural_corruption` shipped:
  - mocked reference scores `0 / 29`
  - local sense check:
    - `gpt_oss_20b_local`: `0 / 29`
    - `qwen3_4b_local`: `17 / 29`
    - `devstral_small_local`: `17 / 29`
  - result: good first-pass separation
  - GPT-OSS 20B named the sentence-initial capitalization failure and carried the fix into source-summary consistency
  - Qwen and Devstral both drifted toward title handling and generic literary-NER discussion while missing the sentence-boundary trigger and the source-summary mapping requirement
- `lang_japanese_translation_kaze_no_tayori` shipped:
  - mocked reference scores `0 / 17`
  - load-bearing nuance is idiomatic hearsay for `風の便り`, not literal wind language
- `lang_korean_translation_ssitgo_wa` shipped:
  - mocked reference scores `0 / 17`
  - load-bearing nuance is that `씻고 와` in context localizes to `wash your face`, `wash up`, or `clean yourself up`, not a bare `go wash` and not `go take a shower`
- `lang_korean_translation_nunchi_eopda` shipped as a Korean-family expansion:
  - mocked reference scores `0 / 18`
  - live spot-check:
    - `gpt_oss_20b_local`: `4 / 18`
    - `qwen3_4b_local`: `0 / 18`
  - result: more interesting than `씻고 와` for the current pair
  - `gpt-oss-20b` flattened `눈치 없다` into generic `no sense`, while Qwen produced a timing-aware line closer to the intended social-judgment meaning
- language family live spot-check, rule judge:
  - `gpt_oss_20b_local`: `2 / 70` across the four current language tasks
  - `qwen3_4b_local`: `11 / 70` across the four current language tasks
  - result: useful real split
  - `gpt-oss-20b` was clean on both translation/localization tasks and both Korean tasks, with only a small miss on Japanese business-email framing
  - Qwen was notably weaker on idiom handling and Korean register control: it literalized `風の便り` into wind language and mixed banmal with polite endings in the Korean workplace reply
- `lang_korean_politeness_level_switch` shipped:
  - mocked reference scores `0 / 17`
  - this is the first Korean workplace-pragmatics singleton and should later grow into a small family
- `agent_task_spec_not_handwave` local sense check, final rubric:
  - `gpt_oss_20b_local`: `7 / 57`
  - `qwen3_4b_local`: `9 / 57`
  - `devstral_small_local`: `4 / 57`
  - result: tractable and broadly fair, but still a little easy; the main useful separations came from giant-file regression and needless stack/packaging lock-in rather than total structural collapse
  - follow-up: should expand into a small family of 3-4 briefs later rather than remaining a singleton
- `ml_t5_seq2seq_data_collator_mismatch` shipped:
  - mocked reference scores `0 / 27`
  - task is intentionally narrower than `ml_distributed_eval_debug`: compute_metrics is running, and the scoring is anchored to the collator mismatch plus generation-mode fix
- `ml_t5_seq2seq_data_collator_mismatch` local sense check:
  - `gpt_oss_20b_local`: `23 / 27`
  - `qwen3_4b_local`: `16 / 27`
  - `devstral_small_local`: `19 / 27`
  - result: nicely distinct from the distributed-eval task; weak models drifted into ROUGE-decoding folklore instead of naming the collator mismatch and generation-mode fix
- `ml_distributed_eval_debug` frontier sanity check, cached at [references/frontier/ml_distributed_eval_debug/e6608ea8c1fd](/Users/mitchellcurrie/Projects/rough-bench/references/frontier/ml_distributed_eval_debug/e6608ea8c1fd):
  - `claude_sonnet_4_6`: `8 / 31`
  - `gpt_5_4_mini_xhigh`: `27 / 31`
  - result: the task needed an ordering-sensitive penalty because Sonnet mentioned the right collator fix too late, and GPT-5.4 mini xhigh consumed its entire OpenAI output budget on reasoning with no visible answer
- `critique_without_sandwich` spot-checks, rule judge:
  - `gpt_oss_20b_local`: `0 / 23`
  - `qwen3_4b_local`: `6 / 23`
  - `devstral_small_local`: `10 / 23`
- `critique_without_sandwich` spot-checks, hybrid judge:
  - anchor scores retained in all three cases
  - `gpt-oss-120b` review was useful as commentary, but not reliable enough to replace the rule anchor
- `writing_prose_critique_gritty_fantasy` shipped:
  - mocked reference scores `0 / 30`
  - first live local pass after rubric tightening:
    - `gpt_oss_20b_local`: `11 / 30`
    - `qwen3_4b_local`: `3 / 30`
    - `devstral_small_local`: `8 / 30`
  - result: useful separation
  - Qwen was the strongest of the local trio on this task. It directly called the passage performative and decorative, diagnosed false grit, quoted evidence well, and explained what real gritty prose does instead, but still softened slightly with "moments of potential."
  - GPT-OSS gave a real negative verdict and good sentence-level critique, but stayed too workshop-safe and never fully named the deeper false-grit problem.
  - Devstral was in between: better than GPT on what real gritty prose should do, but still softened the critique and partially fell back into trope-level commentary.
- `design_cardgame_blight_mechanics` shipped:
  - mocked reference scores `0 / 38`
  - first live rubric pass exposed a real brittleness issue:
    - the judge was under-recognizing valid Blight Deck design and over-requiring the exact `Stress Test Your Own Design` heading
  - after rubric widening, a saved Devstral response rescored to:
    - `devstral_small_local`: `8 / 38`
  - result: the trap is working
  - Devstral produced a runnable deck, crop asymmetry, and explicit relative scoring, but still missed the load-bearing offensive-blight loop and instead stress-tested a safer Root-heavy strategy
  - note: one GPT-OSS compare lane returned an empty response and one Qwen lane failed to materialize a response directory at all, so there is not yet a clean three-model comparison for this task
- `rag_broad_search_regression_audit` shipped:
  - mocked reference scores `0 / 41`
  - first live local check:
    - `gpt_oss_20b_local`: `10 / 41`
    - `qwen3_4b_local`: `16 / 41`
  - result: useful first-pass separation
  - GPT-OSS was directionally better: it engaged the numbers, split broad vs narrow handling, and proposed diversity-preserving fixes, but still did not explicitly frame the root cause as `k=20 -> top-5` truncation and did not give a crisp ship rule
  - Qwen produced broader retrieval commentary and explicit guardrails, but it drifted toward a single replacement philosophy and also missed the load-bearing truncation diagnosis
  - this task looks viable because both models can say broad search needs diversity, but both still stumble on the actual compression step that made the regression catastrophic
- `t5_relpebias_failure_mode` shipped:
  - mocked reference scores `0 / 37`
  - first live local check:
    - `gpt_oss_20b_local`: `5 / 37`
    - `qwen3_4b_local`: `21 / 37`
  - result: strong separation
  - GPT-OSS identified the relative-position bucket path as primary and explained the threshold mechanically, but still did not isolate it in the most direct way; it relied on higher-level checks instead of explicitly printing bucket ids from the function
  - Qwen knew the component family, but it did not explain the threshold shape, did not give a direct isolation check, and did not make the fix concrete
  - note: the task deliberately rewards exact-log bucket-structure knowledge, but the judge does not require the model to claim that the canonical T5 exact/log split itself is at 24 or 25
