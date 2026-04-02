You’re building RoughBench to stress‑test LLMs for *your* kind of work, not for generic coding‑contest or MMLU‑style bread‑and‑butter. From your history, here’s what RoughBench should interrogate:

***

## 1. What your work actually looks like

Based on your memory bank and past threads, your real work patterns cluster around:

- **Applied ML engineering and research**  
  - Building real‑world models (e.g., `minilm‑fiction`, CNN classifiers, VLM‑based stacks) on messy, non‑benchmark‑clean data.
  - Caring about data quality, labeling strategies (e.g., using GPT‑OSS‑20B to label negatives), and distributional artifacts.
  - Preferring sub‑20B or 20B‑class models (e.g., GPT‑OSS‑20B, Qwen/GLM) for local deployment, spec‑decoding, NVFP4, vLLM, and avoiding “universe‑scale” waste.

- **Heavy local inference and tooling**  
  - Running vLLM, NVFP4, MX‑FP4, speculative decoding on RTX 3090/5090, aiming for 200–300+ tokens/sec.
  - Debugging and optimizing tooling stacks (OpenWebUI, Florence 2, VLM‑for‑reasoning, etc.), not just “chat” use.

- **Strong taste and aversion to autopilot**  
  - Being annoyed when models default to BERT‑style transformers when you explicitly say “no BERT” or “use CRF‑style modeling”.
  - Disliking hype‑driven answers, performative compliance, and “safe‑corporate” boilerplate.
  - Wanting models to *argue* with you about tradeoffs, not just recite recipes.

- **Debugging, failure‑mode analysis, and “real‑world” failure**  
  - You obsess over how failures *happen*: slow reasoning, hallucinated specs, ignoring instructions, unsafe patterns, or “correct‑on‑paper, wrong‑in‑practice”.
  - You care about artifacts that can be audited later (configs, eval scripts, logs, diffs, weight‑decay tables).

- **Writing, critique, and “taste” for technical work**  
  - You read and critique papers, posts, and tutorials, and you’d rather a model *critique* a design than reprint a best‑practice template.
  - You’re allergic to “write me a blog post” or “explain this like I’m five” fluff.

Given all that, RoughBench should feel like:

- A senior SWE/ML engineer asking a model to *own* a real‑world slice of a messy project, not solve a toy.
- Tests that expose:
  - shallow “template” reasoning,
  - autopilot grabs at the easiest modeling choice,
  - blindness to latent constraints (latency, cost, revision, safety, re‑runability),
  - and especially, *how* a model fails when it doesn’t know the right answer.

***

## 2. 20 candidate RoughBench tasks

Below are 20 concrete tasks that I infer from your history and style. Each is designed to be high‑stress, opinionated, and hard to game with benchmark‑rut behavior.

***

### 2.1 `id: swe_ml_debugging_cascade`

- **title:** `swe_ml_debugging_cascade`  
- **why_this_reflects_my_real_work:** You routinely debug subtle training‑pipeline or inference bugs where local models behave differently than “paper” setups, and you care about how models propose narrowing failure modes. [arxiv](https://arxiv.org/html/2408.05006v1)
- **prompt:**
  ```
  You are debugging a production ML pipeline that trains a CNN classifier on messy, real‑world images. The model trains fine on the dev set, but its validation accuracy keeps dropping over epochs, and the training loss curves are noisy and bumpy. You suspect data leakage, broken augmentation, or a NaN somewhere, but the logs are sparse.

  Act as a senior engineer debugging this pipeline. Without access to live training, reconstruct a *plausible* failure cascade consistent with the symptoms, then propose a concrete debugging plan (code snippets, log snippets, and experiments) that systematically eliminates the most likely causes. Avoid generic “try learning rate” boilerplate; be specific to CNNs, data‑centric bugs, and your own stack.
  ```  
- **what_a_weak_model_will_do:**  
  - Lists generic hyper‑parameter tweaks (lr, batch size, optimizer) and “maybe check the data” without concrete checks.
  - Ignores CNN‑specific failure modes (e.g., augmentation bugs, imbalanced classes, label leakage).
  - Produces vague “run more epochs” or “add more regularization” without a focused diagnostic sequence. [youtube](https://www.youtube.com/watch?v=ZHjulqB-4A0)
- **what_a_strong_model_will_do:**  
  - Proposes a narrowing sequence: first check data splits, then augmentations, then normalization, then gradient clipping/NANs, then label leakage.
  - Writes concrete code for: assertion checks on data splits, logging per‑epoch stats, and ablation experiments.
  - Respects the “local, messy‑data” context and avoids “buy a bigger GPU” or “switch to a transformer”.
- **latent_requirements:**  
  - Understands CNNs, data‑centric bugs, and debugging as a search process.
  - Can infer that the user cares about reproducibility and local‑GPU constraints.
- **hard_failures:**  
  - Ignores data leakage or augmentation bugs.
  - Defaults to “use a transformer” or “train longer” without first ruling out simpler issues.
- **expected_artifacts:**  
  - A short debugging plan (bullet list).
  - 2–3 concrete code snippets for checks or experiments.
- **why_it_is_hard_to_game:**  
  - Generic “hyper‑parameter advice” is easy to generate but irrelevant; the model must correctly prioritize CNN‑specific diagnostics over general tips.

***

### 2.2 `id: ml_data_cleaning_pipeline_design`

- **title:** `ml_data_cleaning_pipeline_design`  
- **why_this_reflects_my_real_work:** You’ve worked with messy fandom data, scraped datasets, and tagged lore; you care how data is cleaned and structured before modeling. [reddit](https://www.reddit.com/r/MachineLearning/comments/1p37y8c/d_how_do_ml_teams_handle_cleaning_structuring/)
- **prompt:**
  ```
  You have a scraped dataset of ~100k text snippets from fandoms and game wikis, with inconsistent tagging, duplicate entries, and noisy labels. Many tags are underspecified (e.g., “hero” vs “anti‑hero”) and some entries are near‑duplicates.

  You want to build a data‑cleaning pipeline that is:
  - audit‑able,
  - cheap to run on a single machine,
  - preserves the “interesting” edge cases.

  Design the pipeline architecture (stages, data formats, tools) and sketch a config‑driven cleaning script. Prefer Python, SQLite, or simple file‑based indices over heavy frameworks. Capture the core tradeoffs: how much you dedup vs keep; how you reconcile noisy tags; how you document cleaning decisions.
  ```  
- **what_a_weak_model_will_do:**  
  - Suggests dumping everything into a big transformer‑based “noise‑removal” model.
  - Recommends heavy frameworks (e.g., Spark, Ray, Luigi) without considering single‑machine constraints.
  - Ignores auditability and instead just talks about “removing noise”. [dev](https://dev.to/kamya_shah_e69d5dd78f831c/7-ways-to-create-high-quality-evaluation-datasets-for-llms-2e4m)
- **what_a_strong_model_will_do:**  
  - Proposes a staged pipeline: dedup (minhash/LSH), label‑reconciliation (label‑mapping config), auditing logs to file or SQLite.
  - Writes a small Python script that is readable, config‑driven, and respects resource limits.
  - Articulates tradeoffs: “I’ll keep more duplicates if they differ in tags, but remove text‑only duplicates.”
- **latent_requirements:**  
  - Understands lightweight data processing, config‑driven pipelines, and “messy” text data.
  - Infers that you care about local, single‑machine, and audit‑ability.
- **hard_failures:**  
  - Recommends GPU‑heavy cleaning models when you said “cheap to run on a single machine”.
  - Ignores labeling consistency or audit logs.
- **expected_artifacts:**  
  - Pipeline architecture description.
  - A small Python script or config structure.
- **why_it_is_hard_to_game:**  
  - Heavy “ML‑heavy” answers are easy to generate, but wrong for your constraints; the model must correctly avoid autopilot ML‑for‑everything.

***

### 2.3 `id: ml_embedding_model_design_fiction`

- **title:** `ml_embedding_model_design_fiction`  
- **why_this_reflects_my_real_work:** This is basically your `minilm‑fiction`‑style project: building a general fiction embedding model on messy fandom data. [nature](https://www.nature.com/articles/s41586-025-09962-4)
- **prompt:**
  ```
  You want to build a general fiction embedding model for narrative characters and concepts (e.g., “hero” vs “anti‑hero”) that generalizes across many fandoms and traditional settings like Lord of the Rings. You have scraped fandom lore data, metadata tags, and lore‑universe labels, plus GPT‑OSS‑20B‑generated labels for negatives.

  Propose an embedding model architecture and training setup that:
  - Runs efficiently on a single RTX 3090‑class GPU.
  - Uses contrastive learning or another embedding‑friendly objective.
  - Avoids transformer‑heavy BERT‑style text‑encoders as the default.

  Describe the model, loss, data‑sampling strategy, and a minimal eval setup (e.g., few‑shot retrieval or similarity tasks). Also sketch how you would sanity‑check that the model is not just memorizing fandom‑specific trivia.
  ```  
- **what_a_weak_model_will_do:**  
  - Defaults to “use Sentence‑BERT” or “fine‑tune BERT” despite your anti‑BERT hints.
  - Ignores single‑GPU constraints and suggests “just train larger” without ablation proposals.
  - Proposes overly abstract evals (“run on MMLU‑style tasks”). [nature](https://www.nature.com/articles/s41586-025-09962-4)
- **what_a_strong_model_will_do:**  
  - Sketches a lightweight architecture (e.g., CNN + Bi‑LSTM + contrastive loss) suitable for your GPU.
  - Suggests concrete sampling strategies (hard negatives, cross‑fandom negatives) and evals (e.g., cluster anti‑heroes vs heroes).
  - Proposes sanity‑checks: inspecting nearest neighbors, checking cross‑fandom recall.
- **latent_requirements:**  
  - Grasps embedding‑style learning, contrastive objectives, and data‑sampling.
  - Infers that you care about efficiency, generalization, and not defaulting to BERT.
- **hard_failures:**  
  - Recommends “fine‑tune BERT‑base” or “buy more GPUs”.
  - Ignores concrete evals or sanity‑checks.
- **expected_artifacts:**  
  - Model description.
  - Training and loss description.
  - Eval setup and sanity‑checks.
- **why_it_is_hard_to_game:**  
  - Generic “BERT‑based” embeddings are easy to generate; the model must correctly resist that and propose a lightweight, efficient alternative.

***

### 2.4 `id: ml_inference_pipeline_design_speculative`

- **title:** `ml_inference_pipeline_design_speculative`  
- **why_this_reflects_my_real_work:** You’re deep into vLLM, NVFP4, speculative decoding, and maximizing performance on RTX 3090/5090.
- **prompt:**
  ```
  You are serving a 20B‑class model via vLLM on a single RTX 3090, and you want to maximize throughput under a latency tail constraint (e.g., p95 < 1.5s). You are considering speculative decoding with a smaller draft model.

  Design an inference pipeline that:
  - Uses vLLM primitives,
  - incorporates speculative decoding (e.g., EAGLE‑style head or small draft model),
  - runs under NVFP4 or MX‑FP4 quantization,
  - and includes a simple benchmark script that measures median, p95, and tokens/sec for a fixed prompt.

  Sketch the config, the speculative‑decoding loop, and the benchmark loop. Also outline the main failure modes (e.g., draft model quality, queueing, or memory) and how you’d detect them.
  ```  
- **what_a_weak_model_will_do:**  
  - Describes speculative decoding in generic terms without integrating vLLM‑style constructs.
  - Ignores quantization and instead talks about “just add more GPUs”.
  - Writes a benchmark that just reports average tokens/sec, not p95. [youtube](https://www.youtube.com/watch?v=aId-UDaJSXg)
- **what_a_strong_model_will_do:**  
  - Describes a concrete vLLM‑style harness with speculative decoding loop, batch size, and warm‑up.
  - Writes a small benchmark script that measures TTFT, TPOT, median, and p95.
  - Anticipates realistic failure modes: draft model lagging, queueing delays, or memory pressure.
- **latent_requirements:**  
  - Understands vLLM, speculative decoding, and quantization.
  - Infers that you care about latency tails and local deployment.
- **hard_failures:**  
  - Ignores p95 or tail latency.
  - Recommends “just use a bigger model” or “run on cloud”.
- **expected_artifacts:**  
  - Pipeline description.
  - Speculative‑decoding loop sketch.
  - Benchmark script outline.
- **why_it_is_hard_to_game:**  
  - Generic “speculative decoding” explanations are easy to generate; the model must integrate concrete vLLM‑style constructs and metrics.

***

### 2.5 `id: ml_vlm_integration_for_reasoning`

- **title:** `ml_vlm_integration_for_reasoning`  
- **why_this_reflects_my_real_work:** You’re integrating Florence 2 with GPT‑OSS in OpenWebUI stacks, preferring VLMs to do more than just captioning. [arxiv](https://arxiv.org/abs/2412.14161)
- **prompt:**
  ```
  You want to build a local “home AI stack” where a VLM (e.g., Florence 2) is used not just for image captioning, but for richer reasoning (e.g., “is this a safe scene?”, “are there any odd objects?”, “is this a meme?”). The stack runs via OpenWebUI, with user‑submitted images.

  Design a tool‑calling‑style integration where the LLM invokes the VLM with specific analysis types, not just “describe this image”. Propose:
  - A small set of reusable “analysis types” (e.g., safety, object novelty, meme‑ness).
  - A structured format for the LLM to request those analyses.
  - How the final response is composed from the VLM‑analysis and LLM reasoning.

  Also sketch how you’d log and audit these interactions for safety and consistency.
  ```  
- **what_a_weak_model_will_do:**  
  - Reduces everything to “describe this image” or generic “analyze”.
  - Ignores auditability and logging.
  - Proposes overly complex or cloud‑only setups. [arxiv](https://arxiv.org/abs/2412.14161)
- **what_a_strong_model_will_do:**  
  - Defines concrete analysis types with clear semantics.
  - Sketches a simple JSON‑style tool call format and compose logic.
  - Proposes logging and safety checks (e.g., flagging “potentially unsafe” outputs).
- **latent_requirements:**  
  - Understands tool calling, VLMs, and local stacks.
  - Infers that you care about safety, auditability, and not over‑engineering.
- **hard_failures:**  
  - Ignores logging or safety.
  - Defaults to “just describe the image”.
- **expected_artifacts:**  
  - Analysis types.
  - Tool call format.
  - Compose logic and audit plan.
- **why_it_is_hard_to_game:**  
  - Generic “VLMakey” answers are easy; the model must propose concrete analysis types and auditable workflows.

***

### 2.6 `id: ml_coding_model_choice_critique`

- **title:** `ml_coding_model_choice_critique`  
- **why_this_reflects_my_real_work:** You compare models (Qwen, GPT‑OSS, Gemini, etc.) and you care about how models critique tradeoffs, not just regurgitate specs. [linkedin](https://www.linkedin.com/posts/hackerrank_how-far-have-llms-come-in-real-world-software-activity-7323707816135864321-5Jw3)
- **prompt:**
  ```
  You are comparing two coding‑focused models: one is a 20B‑class local model (e.g., GPT‑OSS‑20B) and the other is a 3.5‑class Qwen variant. You want to decide which to use for a local agentic coding workflow that involves tool calling, code generation, and debugging.

  Critique the tradeoffs between these two models for your use case. Do not just repeat specs; instead, discuss:
  - how they differ in tool‑calling reliability,
  - how they handle messy codebases,
  - how they behave when they don’t know the answer,
  - and how they might affect your local stack (e.g., VRAM usage, latency, fallback workflows).

  Propose a concrete, small benchmark you would run to distinguish between them on your own stack.
  ```  
- **what_a_weak_model_will_do:**  
  - Lists specs and generic “Qwen is faster, GPT‑OSS is better at X” without concrete examples.
  - Ignores tool‑calling reliability and debugging.
  - Ignores your local stack constraints.
- **what_a_strong_model_will_do:**  
  - Gives a nuanced critique: “GPT‑OSS‑20B is better at tool‑calling, but VRAM usage is higher; Qwen‑3.5‑flash is fast but may hallucinate more.”
  - Proposes a benchmark: e.g., “run a set of tight debugging tasks with mixed syntax and type errors.”
  - Anticipates how they behave when uncertain.
- **latent_requirements:**  
  - Understands local coding‑model tradeoffs and tool calling.
  - Infers that you care about local‑stack constraints and failure modes.
- **hard_failures:**  
  - Ignores tool‑calling reliability