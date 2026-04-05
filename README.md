# RoughBench

RoughBench is a personal, opinionated benchmark for whether a model can actually do useful work outside sanitized leaderboard grooves.

v0 is intentionally small:

- local CLI
- YAML task folders
- deterministic rubric judge with scorecards
- artifact-aware scoring
- penalty-first aggregation where lower is better

The design target is hackable extension, not benchmark theater.

## Philosophy

- Real work has latent constraints. Good answers infer them without being handheld.
- Artifacts matter. A benchmark case can score plain text, files, code, plans, or mixed outputs.
- Penalties are more informative than gold-star points. RoughBench starts from `0` and gets worse as a model misses reality.
- Definitions, outputs, and judgments stay separate so you can swap in better judges later.

## Repo Layout

- `roughbench/`: package code for loading tasks, collecting local outputs, and judging them
- `benchmarks/`: benchmark definitions, one folder per case
- `examples/`: mocked local outputs used by `demo`
- `STATUS.md`: current counted release-set policy, promotion rationale, and build burndown

## Quick Start

Create a virtualenv, install the package, then run the demo:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
python -m roughbench demo
```

List tasks:

```bash
python -m roughbench list
```

Score a local set of outputs:

```bash
python -m roughbench run --responses-dir /path/to/outputs
```

Outputs should be arranged as:

```text
responses/
  agent_task_spec_not_handwave/
    response.md
  critique_without_sandwich/
    response.md
  lang_japanese_translation_kaze_no_tayori/
    response.md
  lang_japanese_keigo_hierarchy_inference/
    response.md
  lang_japanese_implied_uchi_soto/
    response.md
  lang_korean_politeness_level_switch/
    response.md
  lang_korean_translation_nunchi_eopda/
    response.md
  lang_korean_translation_ssitgo_wa/
    response.md
  lang_korean_sarcastic_nunchi_pparune/
    response.md
  lang_korean_webtoon_register_preservation/
    response.md
  analytics_ab_test_mix_shift_decision/
    response.md
  medical_cannabis_risk_straight_talk/
    response.md
  medical_straight_talk_ldl_148/
    response.md
  reasoning_settled_blame_purdue_opioid/
    response.md
  design_magic_system_tractable_constraints/
    response.md
  design_cardgame_blight_mechanics/
    response.md
  writing_prose_critique_gritty_fantasy/
    response.md
  ux_multirole_service_hub_ia/
    response.md
  nlp_augmentation_structural_corruption/
    response.md
  nlp_seqeval_vs_token_f1/
    response.md
  rag_broad_search_regression_audit/
    response.md
  t5_relpebias_failure_mode/
    response.md
  train_inference_mismatch_audit/
    response.md
  ml_distributed_eval_debug/
    response.md
  ml_t5_seq2seq_data_collator_mismatch/
    response.md
  swe_scraper_persistent_resumable/
    response.md
    artifacts/
      scraper.py
  swe_realtime_buzzer_server/
    response.md
    artifacts/
      server.py
      client.py
  swe_existing_code_http_cache_bugfix/
    response.md
    artifacts/
      http_cache.py
  hf_datasets_streaming_rewrite_under_caps/
    response.md
    artifacts/
      rewrite_dataset.py
  nlp_bio_off_axis_crf/
    response.md
  tool_planning_migration_plan_concrete/
    response.md
  tool_planning_search_diagnose_patch/
    response.md
```

`response.md`, `response.txt`, `answer.md`, and `answer.txt` are recognized as the primary answer file. Any other files in the task folder are treated as artifacts. Text-like artifacts are also scanned by the judge.

## Task Format

Each case lives in its own folder:

- `task.yaml`
- `prompt.txt`
- `rubric.yaml`
- optional `fixtures/`
- optional `gold_notes.md`

`task.yaml` can carry descriptive fields such as:

- `id`
- `title`
- `domain`
- `family`
- `prompt`
- `intent`
- `counted`
- `execution_backed`
- `execution_gated_signals`
- `latent_requirements`
- `hard_failures`
- `strong_signals`
- `penalties`
- `expected_artifacts`
- `visible_constraints`
- `hidden_stressors`
- `judge_instructions`

`family` groups related leaves for release planning, and `counted` marks whether a
task is currently part of the counted release set. The counted set is now
family-balanced rather than fixed to a hard cap: promote leaves when they add
meaningful coverage or sibling depth, and keep overlaps or weaker variants as
reference leaves with `counted: false`.

Execution-backed fields are task metadata. The local `demo` still scores mocked outputs with the rubric judge, and execution-backed tasks can additionally expose a real harness through `sandbox` and `execute`.

`rubric.yaml` is the machine-judged layer. v0 supports:

- signal rules: `any`, `all`, `groups`, `artifact_any`
- signal rules: `artifact_text_any`, `artifact_text_all`, `artifact_text_groups`
- penalty triggers: `present_any`, `present_all`, `present_groups`
- penalty triggers: `missing_any`, `missing_all`, `missing_groups`, `missing_artifacts_any`
- penalty triggers: `present_artifact_text_any`, `present_artifact_text_all`, `present_artifact_text_groups`
- penalty triggers: `missing_artifact_text_any`, `missing_artifact_text_all`, `missing_artifact_text_groups`

`groups` means “at least one match from each group.”

## Scoring

Each task produces a scorecard with:

- `total_penalty`
- `max_penalty_possible`
- `demerit_pct`
- `triggered_penalties`
- `passed_signals`
- `judge_summary`

RoughBench aggregates by summing task penalties into a demerit total:

```text
roughbench_demerits = sum(task.total_penalty)
```

Lower is better. `0` is a perfect run against the current rubrics.

RoughBench also exposes a suite-relative percentage when the denominator is known:

```text
suite_demerit_pct = roughbench_demerits / suite_max_demerits
```

That percentage is only comparable within the current suite definition. The canonical
metric is still raw demerits.

v0 uses a deterministic local judge so the whole stack is runnable without an external model dependency. The scorecard interface is deliberately simple so an LLM judge can replace or augment it later.

## Adding A New Case

1. Create `benchmarks/<new_task_id>/`.
2. Add `task.yaml`, `prompt.txt`, and `rubric.yaml`.
3. Put example local outputs under `examples/<new_task_id>/` if you want them included in `demo`.
4. Run `python -m roughbench list` and `python -m roughbench demo`.

## Docs POC

There is now a static MkDocs-style visualization POC under `docs/`.

Build the JSON payload from saved compare runs:

```bash
make docs-generate
```

Then serve the site:

```bash
make docs-install
make docs-serve
```

Useful docs targets:

```bash
make docs-clear
make docs-generate
make docs-build
make docs-serve
```

Current POC pages:

- `Overview`
  - overall leaderboard
  - efficiency leaderboard with a quality floor
  - single-model category radar and breakdown
- `Compare`
  - side-by-side category comparison
  - biggest per-task deltas
- `Methodology`
  - category and efficiency rules

The site is data-driven from `docs/assets/data/docs_data.json`, so later visual
axes such as perception / VLM categories can be added without changing the page
structure.

## Seed Tasks

- `swe_scraper_persistent_resumable`
- `hf_datasets_streaming_rewrite_under_caps`
- `agent_task_spec_not_handwave`
- `critique_without_sandwich`
- `lang_japanese_translation_kaze_no_tayori`
- `lang_japanese_keigo_hierarchy_inference`
- `lang_japanese_implied_uchi_soto`
- `lang_korean_politeness_level_switch`
- `lang_korean_translation_nunchi_eopda`
- `lang_korean_translation_ssitgo_wa`
- `lang_korean_sarcastic_nunchi_pparune`
- `lang_korean_webtoon_register_preservation`
- `analytics_ab_test_mix_shift_decision`
- `analytics_guardrail_tradeoff_launch_decision`
- `agent_rubric_false_competence_spec`
- `medical_cannabis_risk_straight_talk`
- `medical_straight_talk_ldl_148`
- `reasoning_settled_blame_purdue_opioid`
- `design_magic_system_tractable_constraints`
- `design_cardgame_blight_mechanics`
- `swe_realtime_buzzer_server`
- `swe_existing_code_http_cache_bugfix`
- `retrieval_local_search_stack_practicality`
- `ux_multirole_service_hub_ia`
- `ux_story_ide_nimble_architecture`
- `ml_distributed_eval_debug`
- `ml_t5_seq2seq_data_collator_mismatch`
- `nlp_augmentation_structural_corruption`
- `nlp_seqeval_vs_token_f1`
- `applied_nlp_label_normalization`
- `applied_nlp_sentiment_batch`
- `applied_nlp_ner_span_audit`
- `applied_nlp_conflicting_summary`
- `applied_nlp_bio_sequence_cleanup`
- `applied_nlp_annotation_quality_gate`
- `rag_broad_search_regression_audit`
- `t5_relpebias_failure_mode`
- `train_inference_mismatch_audit`
- `nlp_bio_off_axis_crf`
- `tool_planning_migration_plan_concrete`
- `tool_planning_search_diagnose_patch`

The `applied_nlp` family is the core batch-processing lane: it is built around small multi-row labeling, normalization, span-audit, synthesis, and QA tasks so a single sample cannot dominate the conclusion.

The `tool_planning` family focuses on whether models can produce concrete, executable plans for coding agents. These are prompt-only tasks (no sandbox required) that evaluate plan structure and specificity: rewriting vague requirements into bounded execution briefs, and structuring tool-call sequences with explicit branching and fallback handling.

The sample outputs in `examples/` are mocked and slightly imperfect on purpose, so the demo shows non-zero penalties instead of a fake all-green result.
Reference leaves can also live in `examples/` with `counted: false`; they stay runnable and regression-tested without blocking the counted set from growing when family coverage warrants promotion.

## Execution-Backed Tasks

RoughBench can now scaffold and execute the `hf_datasets_streaming_rewrite_under_caps`
task in a host sandbox plus a Docker evaluator.

Create a sandbox with a visible local fixture:

```bash
python -m roughbench sandbox \
  --task hf_datasets_streaming_rewrite_under_caps \
  --run-dir runs/hf-datasets-dev
```

This creates:

- `runs/hf-datasets-dev/sandbox/prompt.txt`
- `runs/hf-datasets-dev/sandbox/visible_input/`
- `runs/hf-datasets-dev/sandbox/submission/hf_datasets_streaming_rewrite_under_caps/`

Develop inside the sandbox submission folder. Host-side smoke tests are fine, but
they do not count for scoring.

Evaluate the frozen submission in Docker:

```bash
python -m roughbench execute \
  --task hf_datasets_streaming_rewrite_under_caps \
  --submission-dir runs/hf-datasets-dev/sandbox/submission/hf_datasets_streaming_rewrite_under_caps \
  --input-dir runs/hf-datasets-dev/sandbox/visible_input
```

`execute` freezes the submission, builds the Docker runner image if needed, runs the
artifact under visible plus hidden stress tiers with memory and CPU limits, verifies
the output on the host, and writes logs under the generated work directory. Only the
Docker evaluation counts for scoring.

For this task, the evaluator accepts either positional CLI args or
`--input_dir/--output_dir` style args. Interface trivia should not decide the score.

## Live Model Runs

`run` supports either saved local outputs or a live OpenAI-compatible `/v1` endpoint.

Score previously saved outputs:

```bash
python -m roughbench run --responses-dir /path/to/outputs
```

Query a live vLLM-style endpoint directly:

```bash
export ROUGHBENCH_BASE_URL=http://192.168.1.14:8000/v1
export ROUGHBENCH_MODEL=openai/gpt-oss-20b
export ROUGHBENCH_API_KEY=dummy
export ROUGHBENCH_TEMPERATURE=0.0
export ROUGHBENCH_MAX_TOKENS=10000

python -m roughbench run --live
```

Optionally persist the generated answers for later inspection:

```bash
python -m roughbench run --live --save-responses-dir runs/first-pass
```

For tasks that declare `expected_artifacts`, the live runners now do a minimal
artifact extraction pass before scoring. If the model labels sections such as
`**response.md**`, `**artifacts/server.py**`, or fenced blocks whose first line is
`# artifacts/server.py`, RoughBench will materialize those files under the saved
task directory and include them in the immediate score. This is intentionally
narrow: it is meant to unblock artifact-first tasks without turning the runner
into a general file-system interpreter.

Use the exact model id returned by `GET /v1/models`; many vLLM deployments expose ids such as `openai/gpt-oss-20b`, not the shorter alias you might expect.

## Comparing Subjects

You can define multiple live subject models in YAML and compare them under the same tasks and judge:

```bash
python -m roughbench compare \
  --subjects-file subjects/seed_subjects.yaml \
  --judge-mode hybrid \
  --judge-provider openai-compatible \
  --judge-base-url http://192.168.2.216:8080/v1 \
  --judge-model gpt-oss-120b-MXFP4-00001-of-00002.gguf \
  --retry-attempts 2 \
  --retry-backoff-seconds 5 \
  --save-runs-dir runs/compare
```

The bundled [subjects/seed_subjects.yaml](/Users/mitchellcurrie/Projects/rough-bench/subjects/seed_subjects.yaml) includes:

- `gpt_oss_20b_local`
- `qwen3_4b_local`

For long local runs, you can queue `run` or `compare` in the background and inspect
them later:

```bash
python -m roughbench compare \
  --subjects-file subjects/seed_subjects.yaml \
  --judge-mode hybrid \
  --judge-provider openai-compatible \
  --judge-base-url http://192.168.2.216:8080/v1 \
  --judge-model gpt-oss-120b-MXFP4-00001-of-00002.gguf \
  --background

python -m roughbench jobs
python -m roughbench jobs --job-id <job_id>
```

This persists lightweight metadata plus a log under `.roughbench_jobs/` in the
current working directory. It is intentionally primitive: queue, inspect status,
and inspect logs, without adding an external service dependency.

`compare` is no longer fail-fast by default. It retries each task a small number
of times, records per-task failures explicitly, and keeps partial subject reports
instead of aborting the whole batch on the first timeout. When `--save-runs-dir`
is set, RoughBench also writes progress snapshots to:

- `runs/compare/.roughbench_compare.json` for the whole compare run
- `runs/compare/<subject_storage_name>/.roughbench_compare_subject.json` for each subject

Use `--fail-fast` if you want the older abort-on-first-error behavior.

Subject file format:

```yaml
subjects:
  - id: qwen3_4b_local
    title: Qwen3 4B local
    provider: openai-compatible
    base_url: http://192.168.4.224:1234/v1
    model: qwen/qwen3-4b-2507
    api_key: dummy
    temperature: 0.0
    max_tokens: 10000
    timeout_seconds: 180
    reasoning_effort: low
    direct_answer_first: true
```

Supported subject providers are:

- `openai-compatible` for local `/v1` servers such as vLLM or llama.cpp
- `openai` for the official OpenAI API
- `anthropic` for the official Anthropic API

For official providers, use `api_key_env` in the subject file instead of storing secrets directly. See [subjects/frontier_reference_subjects.yaml](/Users/mitchellcurrie/Projects/rough-bench/subjects/frontier_reference_subjects.yaml) for a minimal frontier example.

## Judge Modes

RoughBench defaults to deterministic rule-based judging:

```bash
python -m roughbench demo
```

You can also use an LLM judge over saved outputs:

```bash
python -m roughbench run \
  --responses-dir examples \
  --judge-mode llm \
  --judge-provider openai-compatible \
  --judge-base-url http://192.168.2.216:8080/v1 \
  --judge-model gpt-oss-120b-MXFP4-00001-of-00002.gguf
```

Or use the local authenticated Copilot CLI through the bundled Copilot SDK:

```bash
python -m roughbench run \
  --responses-dir examples \
  --judge-mode llm \
  --judge-provider copilot-sdk \
  --judge-model claude-sonnet-4.6
```

For a two-stage production path, use a draft judge plus a final judge:

```bash
python -m roughbench run \
  --responses-dir examples \
  --judge-mode stacked \
  --draft-judge-provider openai-compatible \
  --draft-judge-base-url http://192.168.2.216:8080/v1 \
  --draft-judge-model gpt-oss-120b-MXFP4-00001-of-00002.gguf \
  --judge-provider anthropic \
  --judge-model claude-opus-4-1
```

For artifact-heavy tasks where you want deterministic scoring plus an LLM review summary, use `hybrid`:

```bash
python -m roughbench run \
  --responses-dir examples \
  --judge-mode hybrid \
  --judge-provider openai-compatible \
  --judge-base-url http://192.168.2.216:8080/v1 \
  --judge-model gpt-oss-120b-MXFP4-00001-of-00002.gguf
```

Anthropic support is optional:

```bash
pip install -e '.[anthropic]'
```

`copilot-sdk` is judge-only for now. It uses your local Copilot CLI auth and auto-discovers the `@github/copilot` package from a local npm install or `npx` cache when possible. If auto-discovery fails, set `ROUGHBENCH_COPILOT_PACKAGE_ROOT` to the `@github/copilot` package directory.

For some local reasoning-heavy `/v1` subjects, a chat completion may return hidden
reasoning but no visible final answer before hitting the token limit. In practice
this shows up in several shapes across local servers: `message.reasoning`,
`message.reasoning_content`, `message.thinking`, content-part arrays, or a
leading `<think>...</think>` block in `message.content`. The OpenAI-compatible
live runner now normalizes those patterns, retries once with a direct-answer
preamble when it sees reasoning without an answer, and writes non-scored metadata
under `.roughbench_live_meta/` in the save directory.

If a local subject predictably exhibits that behavior, set `direct_answer_first:
true` in the subject YAML or pass `--direct-answer-first` to `run --live` so the
first request already includes the preamble. For GPT-OSS-style local engines that
support it, also set `reasoning_effort: low` to reduce hidden-reasoning burn on
straight answer tasks.

Environment variables are also supported for judge configuration:

- `ROUGHBENCH_JUDGE_MODE`
- `ROUGHBENCH_JUDGE_PROVIDER`
- `ROUGHBENCH_JUDGE_MODEL`
- `ROUGHBENCH_JUDGE_REASONING_EFFORT`
- `ROUGHBENCH_JUDGE_BASE_URL`
- `ROUGHBENCH_JUDGE_API_KEY`
- `ROUGHBENCH_JUDGE_TEMPERATURE`
- `ROUGHBENCH_JUDGE_MAX_TOKENS`
- `ROUGHBENCH_JUDGE_TIMEOUT_SECONDS`
- `ROUGHBENCH_DRAFT_JUDGE_PROVIDER`
- `ROUGHBENCH_DRAFT_JUDGE_MODEL`
- `ROUGHBENCH_DRAFT_JUDGE_REASONING_EFFORT`
- `ROUGHBENCH_DRAFT_JUDGE_BASE_URL`
- `ROUGHBENCH_DRAFT_JUDGE_API_KEY`
- `ROUGHBENCH_DRAFT_JUDGE_TEMPERATURE`
- `ROUGHBENCH_DRAFT_JUDGE_MAX_TOKENS`
- `ROUGHBENCH_DRAFT_JUDGE_TIMEOUT_SECONDS`
- `ROUGHBENCH_COPILOT_PACKAGE_ROOT`

For live OpenAI-compatible runs, `ROUGHBENCH_TIMEOUT_SECONDS` sets the request timeout when `run --live` is used without an explicit CLI flag.
`ROUGHBENCH_DIRECT_ANSWER_FIRST=1` enables the same first-request preamble behavior from the environment.
`ROUGHBENCH_REASONING_EFFORT` sets the live OpenAI-compatible reasoning effort when the engine supports that field.

The draft/final pattern is intentionally simple: the final judge re-scores the raw submission while reviewing the draft judge's structured ids and summary.
