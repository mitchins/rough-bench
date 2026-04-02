I can’t see every raw prior chat transcript in full, but I can see a lot of persistent memory and recent project context, and it is enough to infer a pretty distinctive work profile.

1. What I infer about your actual work patterns

You do not use models for generic “assistant” tasks. You use them as force multipliers inside messy, real, constrained workflows where shallow competence is actively harmful.

What keeps recurring:

You work in ugly reality, not clean demos.
You care about resumability, persistence, artifact integrity, operational safety, mount/ACL weirdness, dataset corruption, packaging conflicts, driver skew, broken auth, brittle clients, rate limits, and the difference between something that sounds right and something that survives restart, scale, or OOD data.

You punish autopilot.
A recurring annoyance in your history is models defaulting to the prestige answer instead of the asked answer:
	•	defaulting to transformers when you asked for CRF/CNN-CRF
	•	defaulting to LoRA/QLoRA when you care about full fine-tune
	•	defaulting to generic RAG recipes when your broad-search evaluator says they regress
	•	defaulting to “enterprise best practices” when you want a rough, local, personal system that actually works on your hardware

You care about latent constraints more than explicit ones.
Your real tasks usually have hidden requirements like:
	•	dual 3090 / 48 GB total VRAM
	•	personal infra, local-first, OSS-friendly
	•	must survive ugly inputs and partial failure
	•	should avoid unnecessary complexity
	•	should not silently violate your intent
	•	artifact shape matters, not just idea quality

You care about evaluation and failure analysis, not just building.
A lot of your work is benchmark-adjacent already:
	•	evaluator design for RAG search quality
	•	ablation thinking
	•	confusion auditing
	•	threshold sweeps
	•	support/lift vs tag-based CF reasoning
	•	OOD/holdout sanity
	•	checking whether a “better” reranker is actually worse

You use models for technically opinionated critique.
Not just “write code”, but:
	•	identify hidden failure modes
	•	cut through hand-waving
	•	detect missing workload details
	•	compare approaches under operational constraints
	•	pressure-test a proposal against likely breakage

You use models for artifact-producing technical design.
The output often needs to be one of:
	•	a CLI script
	•	config
	•	pipeline skeleton
	•	schema
	•	training plan
	•	evaluation rubric
	•	POC task spec for a coding agent
	•	concrete folder/bundle layout
	•	executable benchmark task

You also use models for taste-sensitive literary and creative work, but in an anti-slop way.
You care about:
	•	prose quality ranking
	•	voice consistency
	•	character extraction
	•	story structure with concrete beats
	•	not being boxed into rigid outlining
	•	gritty but not cartoonishly grim tone
	•	models failing by sounding literary while missing the actual emotional or structural job

You are unusually sensitive to false competence.
Weak models that:
	•	sound polished
	•	cite standard techniques
	•	skip the actual constraint
	•	miss one killer operational detail
	•	optimize the wrong layer
are worse than models that just plainly fail.

That suggests RoughBench should heavily weight:
	•	hidden-constraint inference
	•	anti-autopilot behavior
	•	robustness under messy context
	•	artifact realism
	•	judgment under tradeoffs
	•	critique/debugging quality
	•	taste with operational grounding

⸻

2. Twenty candidate RoughBench tasks

⸻

1. rag_broad_search_regression_audit

title: Broad Search RAG Fix That Must Beat a Known Baseline

why_this_reflects_my_real_work
You repeatedly work on retrieval systems where “obvious improvements” regress broad-search performance. You care about evaluator-backed fixes, not generic RAG dogma.

prompt
“My arXiv-style RAG system has a current baseline with weighted_hit_rate=0.828 and broad_macro_hit_rate=0.600. Two MiniLM rerankers reduced these to 0.672/0.100 and 0.688/0.150. I need a concrete plan to improve broad search without regressing narrow search. Do not give me generic RAG advice. Diagnose why this likely happened, propose a replacement strategy, define ablations, and specify how you would validate whether the fix is real.”

what_a_weak_model_will_do
Recommend a stronger reranker, hybrid BM25+dense, query expansion, Reciprocal Rank Fusion, and maybe “try ColBERT” with no explanation of why the current failure occurred.

what_a_strong_model_will_do
Infer that broad search is being over-collapsed by overly precise reranking, frame the problem as candidate-set diversity vs semantic narrowing, propose stage-specific retrieval policies for broad vs narrow queries, define evaluator splits, guard against judge leakage, and suggest failure-preserving ablations rather than cargo-cult upgrades.

latent_requirements
	•	Must engage the numbers
	•	Must explain why broad cases died
	•	Must not assume reranking is always net-positive
	•	Must preserve query diversity and candidate recall
	•	Must propose measurable validation

hard_failures
	•	“Use a better embedding model”
	•	“Use ColBERT” with no task-specific reasoning
	•	ignores broad/narrow split
	•	no ablation plan
	•	no regression guardrails

expected_artifacts
	•	evaluation plan
	•	retrieval pipeline proposal
	•	ablation matrix
	•	decision criteria

why_it_is_hard_to_game
Boilerplate RAG advice looks plausible but fails because the prompt already contains evidence that standard reranking instincts were wrong.

⸻

2. openwebui_perception_sandbox_poc

title: Perception Sandbox POC for Fast Text Models

why_this_reflects_my_real_work
You think in system architecture terms: orchestration vs heavy inference, local tooling, extension boundaries, tool APIs, image isolation, configurable classifier thresholds.

prompt
“Design a POC for an Open WebUI ‘Perception Sandbox’ extension. The goal is to let a fast text-only model call local perception tools for image tasks without shoving torch or ONNX directly into the Open WebUI process. Images should stay isolated in a sandbox-like temp store. The system should support multiple tool types such as captioning, tagging, and classifier variants with configurable thresholds. Give me the architecture, component boundaries, failure modes, API shape, and a concrete repo/task spec suitable for handing to a coding agent.”

what_a_weak_model_will_do
Suggest a plugin that directly loads models, blur server/process boundaries, and ignore model lifecycle, thresholds, sandboxing, and failure isolation.

what_a_strong_model_will_do
Separate orchestrator from inference service, define tool registration and metadata, explain temp storage/jailing, address timeouts and cancellation, make thresholds config-driven, and produce a coding-agent-ready task structure.

latent_requirements
	•	Must respect process boundaries
	•	Must isolate heavy inference
	•	Must model multiple tool variants
	•	Must treat images as controlled attachments, not raw prompt stuffing
	•	Must produce artifact-grade architecture

hard_failures
	•	inline torch inside Open WebUI
	•	hand-wavy “use Docker” without boundaries
	•	no tool schema
	•	no threshold/config discussion
	•	no failure containment

expected_artifacts
	•	architecture diagram in text
	•	endpoint schema
	•	repo layout
	•	coding-agent task spec

why_it_is_hard_to_game
A weak model can sound architectural, but the moment it collapses orchestrator/inference separation, it reveals that it didn’t understand the real constraint.

⸻

3. anime_overlay_classifier_ood_pipeline

title: Overlay-Text Anime Classifier With OOD Discipline

why_this_reflects_my_real_work
You have real history building a practical anime image text-overlay classifier and explicitly rejected some fashionable but bad modeling choices.

prompt
“I need a binary classifier for anime images that detects text overlays of interest: subtitles, promo text, bubbles, watermarks, UI overlays. This is not generic OCR and not just ‘any text’. The dataset includes matched clean images and synthetic paired positives made by adding overlays. I care about precision-first deployment, OOD behavior, thresholding, and practical inference tricks. Propose the full training and evaluation pipeline. Be careful not to recommend methods that add avoidable label noise.”

what_a_weak_model_will_do
Recommend OCR-first pipelines, MIL, generic augmentation, and standard accuracy metrics.

what_a_strong_model_will_do
Recognize the task as precision-first binary classification, avoid MIL, discuss pair leakage risks, recommend threshold calibration on holdout/OOD, use PR-AUC and recall-at-precision, consider tile-max inference, and discuss hard-negative audits.

latent_requirements
	•	Must understand “overlay text of interest” != OCR
	•	Must avoid MIL trap
	•	Must prioritize precision
	•	Must discuss OOD and threshold calibration
	•	Must think about paired data leakage

hard_failures
	•	optimize accuracy
	•	recommend transformers/autopilot without justification
	•	ignore OOD
	•	ignore pair contamination
	•	OCR-only solution

expected_artifacts
	•	training plan
	•	eval protocol
	•	threshold strategy
	•	error-audit plan

why_it_is_hard_to_game
It punishes generic vision boilerplate because the key mistake is choosing methods that sound advanced but are wrong for this label structure.

⸻

4. full_finetune_dual_3090_plan

title: Full Fine-Tune Plan Under Dual 3090 Constraints

why_this_reflects_my_real_work
Your history is full of model-training plans constrained by actual local hardware, with an explicit aversion to being railroaded into LoRA when you want a deeper tune.

prompt
“I have a dual RTX 3090 machine with 48 GB total VRAM. I want to improve a model for literary assistance: generation, plot understanding, inconsistency detection, character suggestions, and boring-section detection. I prefer full fine-tuning over LoRA if at all possible. Give me a realistic training plan, including model size selection, data shape, sequence strategy, memory tradeoffs, eval design, and what I should not do. Do not default to generic cloud-scale advice.”

what_a_weak_model_will_do
Say full fine-tuning is impossible, recommend LoRA, mention QLoRA, DeepSpeed, gradient checkpointing, and call it done.

what_a_strong_model_will_do
Respect the full-tune preference, reason about what model sizes are actually feasible, propose a staged plan, distinguish deep-tune vs adapter fallback, match tasks to data formats, and identify where full fine-tune is worth it vs not.

latent_requirements
	•	Must respect local hardware
	•	Must not autopilot to LoRA
	•	Must trade off task goals vs feasible model size
	•	Must discuss eval beyond loss
	•	Must be practical

hard_failures
	•	default LoRA
	•	recommend 7–9B full tune as trivial with no caveats
	•	ignore sequence packing and dataset shape
	•	no eval plan tied to real tasks

expected_artifacts
	•	training plan
	•	resource table
	•	eval plan
	•	fallback strategy

why_it_is_hard_to_game
The common “safe” answer is exactly the failure mode: ignore the user’s real preference and constraints.

⸻

5. literary_prose_ranker_dataset_design

title: Build a Prose-Quality Ranker Dataset That Won’t Collapse Into Style Mimicry

why_this_reflects_my_real_work
You repeatedly work on prose-quality ranking, literary grading, and downstream distillation, with concern for what a model is actually learning.

prompt
“I want to build a prose-quality ranking dataset from fiction paragraphs at scale, using a stronger model as teacher and a smaller model downstream. I do not want the target to collapse into superficial style mimicry or popularity bias. Design the labeling rubric, dataset construction, filtering strategy, and validation plan so that the resulting ranker tracks actual prose quality rather than genre, famous-author fingerprinting, or obvious lexical signals.”

what_a_weak_model_will_do
Suggest pairwise ranking with GPT labels and standard train/val/test split.

what_a_strong_model_will_do
Define separable dimensions of prose quality, discuss teacher disagreement and confidence filtering, handle author leakage, genre balance, anti-shortcut tests, and recommend adversarial controls.

latent_requirements
	•	Must think about label validity
	•	Must defend against shortcut learning
	•	Must separate prose quality from fame/genre
	•	Must consider distillation risks

hard_failures
	•	naive teacher-label everything
	•	random split that leaks author signals
	•	no adversarial controls
	•	vague rubric

expected_artifacts
	•	labeling rubric
	•	dataset protocol
	•	split policy
	•	anti-shortcut tests

why_it_is_hard_to_game
Because it is easy to sound “ML correct” while quietly producing a dataset that only learns author/style fingerprinting.

⸻

6. character_extraction_mvp_no_alias_magic

title: Character Extraction MVP Without Pretending Coreference Is Solved

why_this_reflects_my_real_work
You have a very specific, non-glamorous extraction workflow: paragraph/chunk-level extraction, no alias resolution magic at first, realistic MVP scope.

prompt
“I have fiction paragraphs and want an MVP character extraction system. Input is paragraph-to-chunk-sized text. Output is structured mentions like {name, summary, type} where type is character/place/lore, or a simpler character-only format if justified. Do not pretend cross-paragraph coreference is solved. Design the MVP pipeline, training data shape, evaluation, and how alias resolution should be deferred or approximated.”

what_a_weak_model_will_do
Recommend a giant end-to-end transformer with coreference, entity linking, and graph postprocessing.

what_a_strong_model_will_do
Keep scope tight, define local extraction first, design structure around named entities and chunk-level evidence, propose pragmatic alias mapping later, and define evaluation that doesn’t fake global resolution.

latent_requirements
	•	Must constrain scope honestly
	•	Must resist doing too much too early
	•	Must match output shape to use case
	•	Must avoid fake certainty

hard_failures
	•	claims end-to-end coreference
	•	no evaluation nuance
	•	unclear output schema
	•	ignores chunk-level limits

expected_artifacts
	•	schema
	•	MVP pipeline
	•	evaluation spec
	•	staged roadmap

why_it_is_hard_to_game
Weak models overbuild and hallucinate solved coreference. Strong models know where to stop.

⸻

7. vndb_hybrid_recommender_design

title: Hybrid VN Recommender From Dirty Vote Data

why_this_reflects_my_real_work
You’ve already worked through actual VNDB schema/votes, support/lift queries, tag flattening, and hybrid recommender design.

prompt
“I have VNDB-style explicit vote data plus metadata such as tags, producers, staff, and descriptive attributes. I want a recommender that works well for both warm users and cold-start visual novels. Design a hybrid approach that combines collaborative and content-based signals, explain the SQL-friendly baseline, and then propose a trainable retrieval model. Be specific about what should be built first.”

what_a_weak_model_will_do
Describe matrix factorization, LightFM, or a two-tower model with no grounding in the actual dirty vote setup.

what_a_strong_model_will_do
Start with SQL baselines that are inspectable, define like/dislike thresholds, use tag-based user profiles, then layer in a two-tower or graph-aware model for cold start, with explicit prioritization.

latent_requirements
	•	Must respect inspectable baseline-first philosophy
	•	Must handle explicit vote thresholds
	•	Must account for cold start
	•	Must distinguish what to build now vs later

hard_failures
	•	jump straight to deep learning
	•	no baseline
	•	no cold-start discussion
	•	no concrete thresholding

expected_artifacts
	•	baseline SQL design
	•	feature plan
	•	hybrid scoring plan
	•	staged roadmap

why_it_is_hard_to_game
The easy answer is “use a recommender model.” The real task is sequencing and inspectability.

⸻

8. hf_massive_dataset_mirror_resume

title: Mirror a Massive Hugging Face Dataset Without Cache Lies or Restart Pain

why_this_reflects_my_real_work
This is exactly your kind of operational task: large public corpora, xet/LFS weirdness, local disk realities, need for a real mirror, resumability, and cache control.

prompt
“I need to mirror a very large Hugging Face dataset repository locally. I care about resumability, avoiding surprise cache bloat on the wrong volume, no fake-success states, and ending up with an actual usable mirror in the target directory. Design the approach, environment variables, verification steps, and restart-safe workflow. Assume internet interruptions and a multi-terabyte destination.”

what_a_weak_model_will_do
Say “use git lfs clone” or hf download with no cache or verification details.

what_a_strong_model_will_do
Discuss hf CLI vs git-lfs/xet tradeoffs, redirect caches intentionally, specify verification of target vs cache usage, plan for resumed downloads and integrity checks, and define a workflow that proves the mirror is real.

latent_requirements
	•	Must care where bytes actually land
	•	Must be restart-safe
	•	Must verify real success
	•	Must handle multi-terabyte practicalities

hard_failures
	•	rely on default cache behavior blindly
	•	no verification
	•	no resume strategy
	•	no distinction between local mirror and cached indirection

expected_artifacts
	•	shell workflow
	•	environment setup
	•	verification checklist

why_it_is_hard_to_game
Looks simple, but weak answers ignore the exact operational traps that make these jobs miserable.

⸻

9. proxmox_bind_mount_acl_debug

title: Diagnose Proxmox Container Mount/ACL Weirdness

why_this_reflects_my_real_work
You spend time in real infra debugging not-fully-clean permission, ACL, idmap, and bind mount issues.

prompt
“I have a Proxmox unprivileged container with bind-mounted ZFS datasets. Inside the container, writes fail or ownership changes behave strangely. I need a diagnosis and remediation plan that accounts for idmaps, ACL support, dataset properties, mount options, and whether the root cause is the host or container side. Give me a structured debug flow and likely fixes.”

what_a_weak_model_will_do
Say chown -R, use privileged container, or disable ACLs.

what_a_strong_model_will_do
Walk through uid/gid mapping, host-side ownership implications, ACL support on dataset/mount, mount flags, pct config, and host/container verification steps.

latent_requirements
	•	Must understand unprivileged mapping
	•	Must distinguish host/container responsibility
	•	Must include verification, not just fixes

hard_failures
	•	naive chmod/chown
	•	no idmap discussion
	•	no host-side checks
	•	“just use privileged”

expected_artifacts
	•	debug checklist
	•	command sequence
	•	probable fix matrix

why_it_is_hard_to_game
Infra boilerplate fails fast here. Real competence shows in sequencing and avoiding destructive advice.

⸻

10. cuda_skew_vllm_postmortem

title: Diagnose a Broken Local vLLM/CUDA Stack

why_this_reflects_my_real_work
Your actual work includes painful local inference stack breakage: CUDA driver mismatch, packaging conflicts, OOM, toolkit skew.

prompt
“My local vLLM deployment is failing across a mess of symptoms: PyTorch reports CUDA driver initialization failure, package conflicts around CUDA libs, and when it finally starts it may OOM under tensor parallel or long context. I want a postmortem-style diagnosis plan, not generic install advice. Tell me how to separate driver issues, userspace/toolkit issues, packaging conflicts, and actual memory pressure.”

what_a_weak_model_will_do
Recommend reinstalling CUDA, reinstalling drivers, and reducing batch size.

what_a_strong_model_will_do
Decompose layers, define diagnostic checkpoints, separate nvidia-smi/driver/runtime questions from Python wheel/toolkit problems, and address OOM as a separate class.

latent_requirements
	•	Must separate problem classes
	•	Must not mix packaging with runtime with memory
	•	Must produce a disciplined debug flow

hard_failures
	•	shotgun reinstall advice
	•	no layered diagnosis
	•	no distinction between initialization and OOM

expected_artifacts
	•	diagnostic decision tree
	•	prioritized fix order
	•	sanity-check commands

why_it_is_hard_to_game
The temptation is generic CUDA folk wisdom. That misses the actual diagnostic skill.

⸻

11. ocr_or_not_decision_task

title: Know When OCR Is the Wrong Tool

why_this_reflects_my_real_work
You frequently resist the obvious tool when it is the wrong abstraction.

prompt
“I need to detect whether anime images contain intrusive text overlays that would make them bad training samples. Should I use OCR? Answer with a design, but first decide whether OCR should be central, auxiliary, or avoided. Explain why.”

what_a_weak_model_will_do
Say yes, OCR is essential.

what_a_strong_model_will_do
Say OCR may be auxiliary at best, but the deployment target is a visual binary classification problem with precision-first behavior.

latent_requirements
	•	Must identify wrong abstraction
	•	Must reason from deployment goal, not surface keyword

hard_failures
	•	OCR-first solution
	•	no precision discussion

expected_artifacts
	•	decision memo
	•	pipeline sketch

why_it_is_hard_to_game
The surface text screams OCR. The real task does not.

⸻

12. story_ide_for_writers_architecture

title: Story IDE Architecture That Stays Nimble

why_this_reflects_my_real_work
Promptual is exactly this: flexible node/document architecture, notes, metadata, leaf-vs-nonleaf handling, AI completion, bundle storage.

prompt
“Design the architecture for a local-first story-writing IDE. It needs a tree/navigator, document editor, metadata/inspector, AI-assisted completion, notes per node, and a document bundle format that scales better than one giant file. The design should stay nimble rather than becoming an overengineered productivity monster.”

what_a_weak_model_will_do
Invent a generic note app or Scrivener clone.

what_a_strong_model_will_do
Define tri-view architecture, leaf/non-leaf behavior, bundle layout, metadata boundaries, AI completion attachment points, and anti-bloat guardrails.

latent_requirements
	•	Must value nimbleness
	•	Must separate content from metadata
	•	Must avoid monolith storage
	•	Must think like a product builder, not just coder

hard_failures
	•	giant database blob
	•	rigid structure
	•	no bundle reasoning
	•	no editing constraints for non-leaf nodes

expected_artifacts
	•	architecture spec
	•	data model
	•	bundle format
	•	UI behavior rules

why_it_is_hard_to_game
It requires taste and product judgment, not just software architecture words.

⸻

13. agent_task_spec_not_handwave

title: Rewrite a Hand-Wavy Idea Into an Agent-Executable Spec

why_this_reflects_my_real_work
You repeatedly convert rough ideas into coding-agent-ready POCs and you care a lot about whether the framing actually captures the important nuance.

prompt
“I have a half-formed product or infra idea. Convert it into a task spec for a coding agent. The output must be specific enough to execute but not so overprescribed that it kills good implementation judgment. Include scope, repo layout, deliverables, non-goals, constraints, and success criteria.”

what_a_weak_model_will_do
Produce a generic PRD with fluff.

what_a_strong_model_will_do
Surface implied boundaries, define execution units, separate must-have from nice-to-have, and write it in a way an agent could actually follow.

latent_requirements
	•	Must understand what coding agents need
	•	Must preserve nuance without ambiguity
	•	Must avoid PM fluff

hard_failures
	•	corporate PRD voice
	•	vague deliverables
	•	no constraints/non-goals
	•	no artifact structure

expected_artifacts
	•	task spec
	•	repo skeleton
	•	acceptance criteria

why_it_is_hard_to_game
Good-sounding product language is not enough. This task exposes whether the model can make work executable.

⸻

14. benchmark_cut_through_handwaving

title: Identify the Missing Workload Behind a Dubious Benchmark Claim

why_this_reflects_my_real_work
You often want the model to cut through vague benchmark discussions and point out what is missing.

prompt
“Someone says model X failed badly in production while model Y succeeded, but they do not describe the workload, latency constraints, tool use, context shape, or failure criterion. Analyze the claim and explain exactly what is missing, what could make the conclusion meaningless, and what specific questions would let us assess it properly.”

what_a_weak_model_will_do
Say more data is needed.

what_a_strong_model_will_do
Pinpoint missing workload definition, task structure, tool requirements, latency budgets, judge criteria, and confounders like prompt quality.

latent_requirements
	•	Must critique precisely
	•	Must know what details matter in model comparison

hard_failures
	•	generic skepticism
	•	no concrete missing variables

expected_artifacts
	•	critique memo
	•	question checklist

why_it_is_hard_to_game
It rewards sharpness, not niceness.

⸻

15. local_search_stack_practicality

title: Choose a Practical Local Search/Answer Stack Without Fantasy Reliability

why_this_reflects_my_real_work
You care about real breakage modes: auth expiry, backend changes, multi-user use, notifications, mobile/web practicality.

prompt
“I want a local or self-hosted search-answer stack for occasional but high-value use. Evaluate the realistic options with these metrics: does it work in most cases, can multiple users/clients use it, and how likely is it to break due to auth expiry, backend changes, or ecosystem churn? Focus on operational practicality, not just feature lists.”

what_a_weak_model_will_do
Compare products by features or star counts.

what_a_strong_model_will_do
Evaluate robustness, dependency fragility, auth lifecycle, maintenance surface, client support, and the cost of breakage.

latent_requirements
	•	Must think operationally
	•	Must rank by reliability, not shininess

hard_failures
	•	feature checklist
	•	ignores auth/backend churn
	•	no multi-user discussion

expected_artifacts
	•	tradeoff matrix
	•	recommendation memo

why_it_is_hard_to_game
Because it resists consumer-tech review patterns.

⸻

16. style_adapter_not_ip_adapter

title: One-Shot Style Conditioning for Anime DiT Without LoRA or Naive IP-Adapter

why_this_reflects_my_real_work
This is an unusually specific research taste area you care about deeply: one-shot style conditioning without entangling style and concept.

prompt
“I want an anime generation model in the 0.6B–2.0B range with style conditioning, optionally character conditioning, but I do not want a fixed-style LoRA. I have already tried IP-adapters and cross/joint attention and found them too entangled with the main concept. Propose better architectural directions and training strategies for flexible one-shot style control.”

what_a_weak_model_will_do
Recommend LoRA, IP-adapter tuning, textual inversion, or ControlNet.

what_a_strong_model_will_do
Engage the failure of entangled conditioning, propose residual modulation / side-channel conditioning / FiLM-like tokenwise biasing / dedicated embedding paths, and discuss training implications honestly.

latent_requirements
	•	Must respect excluded methods
	•	Must reason about entanglement
	•	Must stay within realistic scale

hard_failures
	•	recommend LoRA or IP-adapter again
	•	no architecture-level reasoning

expected_artifacts
	•	research design memo
	•	ablation ideas
	•	training plan

why_it_is_hard_to_game
Common diffusion advice is explicitly the wrong answer.

⸻

17. book_structure_without_prescriptive_slop

title: Generate Story Notes That Preserve Global Intent Without Overconstraining Prose

why_this_reflects_my_real_work
You care about note generation for training and writing assistance, but hate notes that become overprescriptive or degrade prose.

prompt
“I want high-level story notes that help prose completion and chapter writing, but they should preserve global intent rather than micromanage scenes. Design a note format and generation policy that is useful for model conditioning without turning into rigid beat-by-beat sludge.”

what_a_weak_model_will_do
Generate detailed scene outlines and call it structure.

what_a_strong_model_will_do
Keep notes abstract enough to steer intent, allow selective specificity for major twists, and define how notes should scale by level.

latent_requirements
	•	Must balance usefulness vs prescription
	•	Must think as training input, not just writing advice

hard_failures
	•	over-detailed outline
	•	vague motivational fluff
	•	no format discipline

expected_artifacts
	•	note schema
	•	generation policy
	•	examples by granularity

why_it_is_hard_to_game
Weak models equate usefulness with more detail. That is exactly the trap.

⸻

18. character_prompt_rag_voice_consistency

title: Build a Character Conditioning Prompt That Preserves Voice Under World-Context Pressure

why_this_reflects_my_real_work
You are actively experimenting with role-simulation, fake RAG, persona conditioning, and in-character response fidelity.

prompt
“Design a character conditioning prompt format for local LLM role-simulation. It should combine persona facts, world-context RAG, and dialogue style cues while keeping the model in character under off-axis questions. The goal is not raw roleplay flourish but stable voice and context adherence.”

what_a_weak_model_will_do
Stuff the prompt with backstory and example dialogue.

what_a_strong_model_will_do
Separate persona from world facts, control salience, avoid conflicting instruction layers, define what is canonical vs contextual, and include failure tests.

latent_requirements
	•	Must think about prompt salience and conflict
	•	Must care about voice under pressure, not just lore stuffing

hard_failures
	•	giant undifferentiated prompt blob
	•	no failure tests
	•	no hierarchy of facts

expected_artifacts
	•	prompt schema
	•	example template
	•	adversarial test set

why_it_is_hard_to_game
It exposes prompt-design understanding rather than mere creativity.

⸻

19. dynamic_range_compression_real_solution

title: Solve Movie Loud/Quiet Audio for Real, Not in Theory

why_this_reflects_my_real_work
You often pressure tools against real UX pain, especially where clients, extensions, and “just works” behavior matter more than theoretical purity.

prompt
“I’m sick of movies where dialogue is too quiet and explosions are too loud. I want the most practical solution across Plex/Jellyfin/web/macOS clients, with strong bias toward ‘just works’ on loudspeakers. Evaluate real options by whether they work in most cases, support multiple clients, and are likely to survive updates.”

what_a_weak_model_will_do
Explain DRC conceptually or suggest transcoding filters without client reality.

what_a_strong_model_will_do
Compare client-side DRC, OS/audio middleware, browser constraints, server preprocessing, and breakage risk, then pick the least-bad real solution.

latent_requirements
	•	Must prioritize practicality
	•	Must handle multiple clients
	•	Must consider maintenance breakage

hard_failures
	•	theory-only answer
	•	no recommendation hierarchy
	•	ignores client reality

expected_artifacts
	•	solution matrix
	•	recommended path
	•	implementation notes

why_it_is_hard_to_game
Boilerplate DSP advice misses the product/integration problem.

⸻

20. benchmark_judge_for_false_competence

title: Design a Judge Rubric That Penalizes Plausible-Sounding Wrongness

why_this_reflects_my_real_work
This is meta, but very aligned with your annoyance profile: the real enemy is plausible but wrong competence.

prompt
“Design a scoring rubric for a benchmark meant to expose models that sound capable while missing hidden constraints, making unsafe assumptions, or defaulting to prestige boilerplate. The rubric should strongly penalize plausible but operationally wrong answers.”

what_a_weak_model_will_do
Produce a generic rubric with accuracy/clarity/completeness.

what_a_strong_model_will_do
Include hidden-constraint recovery, anti-autopilot behavior, unsafe-omission penalties, artifact validity, and distinguishing shallow polish from real competence.

latent_requirements
	•	Must understand the benchmark philosophy
	•	Must design for revealing failure

hard_failures
	•	generic eval categories
	•	no asymmetry against false competence

expected_artifacts
	•	rubric
	•	judge notes
	•	examples of deceptive failure

why_it_is_hard_to_game
It is hard to write a good rubric unless the model actually understands what kind of failure you hate.

⸻

3. Best 8, ranked

These are the most diagnostic for your actual use and standards.

1. rag_broad_search_regression_audit

Most diagnostic because it pressures judgment, anti-autopilot behavior, evaluator thinking, and the ability to explain why “improvement” made things worse.

2. openwebui_perception_sandbox_poc

Very diagnostic because it tests system architecture, local-first instincts, artifact quality, and whether the model respects process boundaries.

3. anime_overlay_classifier_ood_pipeline

Excellent because it kills generic CV boilerplate and exposes whether the model can reason from label structure and deployment goals.

4. full_finetune_dual_3090_plan

Strong diagnostic of whether the model actually listens to your constraints and preferences rather than steering you back to mainstream advice.

5. hf_massive_dataset_mirror_resume

Very “you”. Operational realism, persistence, real bytes on disk, resume behavior, and verification. Easy for weak models to fake badly.

6. story_ide_for_writers_architecture

Good because it combines technical architecture with product taste and anti-bloat judgment.

7. style_adapter_not_ip_adapter

Very revealing for research judgment and anti-autopilot behavior, though it is more niche and harder to judge automatically.

8. benchmark_cut_through_handwaving

Valuable as a critique/judgment task. Less artifact-heavy, but very aligned with your standards.

⸻

4. Top 5 in near-RoughBench-ready form
