Good. I have a rich picture. Let me do one more targeted search before writing this up.I have what I need. This is going to be a long, substantive response — let me write it.

---

## RoughBench Task Mining — Mitch Mitchell

> **History access**: Full. I retrieved conversations spanning March 2025–March 2026 across NLP/ML training pipelines, literary AI infrastructure, career decisions, and data engineering. What follows is grounded in that history, not generic inference.

---

## Part 1 — What I Infer About Your Actual Work Patterns

**You build bespoke training pipelines for non-standard tasks.** Not "fine-tune BERT on CoNLL." You train seq2seq models on custom literary corpora (T5 narrative summarisation, LongT5 fact extraction), debug distributed training failures across DeepSpeed + torchrun + HuggingFace Trainer, subclass `Trainer` with custom `compute_loss` and save logic, and deal with metric evaluation silently breaking under `torchrun --nproc-per-node=2`. You have strong opinions about `eval_strategy` vs `evaluation_strategy`. You are not doing tutorial-grade ML.

**You live in the domain-specific NLP gap.** Your work consistently falls into the space where standard frameworks break or don't exist — coreference on literary text, NER on fiction corpora, trope detection, sentence-completion fine-tuning on prose. You've tried Flair, SpanMarker, AllenNLP, and found them deprecated, non-extensible, or broken. You build custom classes. You understand BIO tagging, span extraction, offset mapping, token vs character boundary alignment.

**You operate large, self-managed data infrastructure.** 15,000+ books in MongoDB. Multi-stage ingestion pipelines with status codes (WANTED/FAILED/CHAPTER_CONVERTED/REJECTED_LANGUAGE etc). InfluxDB for pipeline telemetry. `diskcache` for intermediate state. You think about idempotency, resumability, and pipeline observability as first-class concerns, not afterthoughts.

**You have strong literary taste and use it as a technical constraint.** Trope taxonomy (198 leaf nodes), cliché detection via semantic embeddings and corpus-derived patterns, narrative summarisation, Gemini-as-annotator pipelines, a writing IDE (Promptual) with dynamic lore condensation — your ML work is aesthetically motivated. You distinguish "grimdark" from "gritty fantasy." These aren't separate interests; they inform what you think models should be able to do.

**Your recurring annoyances are specific:**
- Models defaulting to transformer autopilot (BERT for everything)
- HuggingFace abstractions silently eating failures in distributed contexts
- Data augmentation that sounds correct but corrupts structure (proper noun replacement replacing "Limp" with "Chris")
- Evaluation metrics that don't match task semantics (token-F1 where span-F1 is needed)
- Frameworks that paper over complexity and fail ungracefully

**Your standard is operational, not academic.** You want things that work when deployed against real data. You care about checkpoint correctness (missing keys on reload), resumability, memory efficiency, and pipeline robustness. You are not writing papers. You're building systems that survive contact with 15,000 books.

---

## Part 2 — 20 Candidate RoughBench Tasks

---

### 1. `ml_trainer_subclass_compute_loss`

**Why this reflects your real work**: You subclass HuggingFace `Trainer` regularly. You have a hard requirement to include `num_items_in_batch` in `compute_loss`. Weak models get this wrong in ways that look right but silently break distributed training.

**Prompt**: "I need to subclass HuggingFace `Trainer` for a custom weighted loss on a token classification task. The model has two output heads: a BIO tagger and a span confidence scorer. Write a `compute_loss` override that handles both heads, correctly handles `num_items_in_batch`, and won't silently fail under `torchrun --nproc-per-node=2`."

**What a weak model will do**: Return a single head loss. Forget `num_items_in_batch`. Not mention `local_rank` guards. Ignore DDP interaction. Make it look syntactically correct but operationally broken.

**What a strong model will do**: Correctly sum or weight losses from both heads. Include `num_items_in_batch` as a required argument with proper None handling. Mention `is_distributed()` or `local_rank` guards for logging. Note the interaction between gradient accumulation and effective batch size. Flag that `DataCollatorForTokenClassification` must handle both label sets.

**Latent requirements**: `num_items_in_batch` parameter required. Both heads must contribute to loss. DDP-safe logging. Mention of `label_names` or `return_dict` if relevant.

**Hard failures**: Missing `num_items_in_batch`. Single-head loss only. Silent `None` loss path. No mention of distributed context.

**Expected artifacts**: Working `compute_loss` method. Ideally a stub Trainer subclass showing `__init__` and `compute_loss`.

**Why it's hard to game**: Most training tutorials don't subclass `Trainer` at all. Distributed-safe compute_loss with multiple heads is not in standard examples.

---

### 2. `nlp_augmentation_structural_corruption`

**Why this reflects your real work**: You ran into this directly — proper noun replacement corrupting "Limp as rags" → "Chris as rags." Models will suggest augmentation strategies that sound reasonable but corrupt sentence structure in exactly this way.

**Prompt**: "I'm augmenting a narrative summarisation dataset by replacing character names with synthetic alternatives. My augmenter sometimes corrupts sentences like this: original `Limp as rags on the floor, the First Enchantress recovered her outrage.` → augmented `Chris as rags on the floor, the Riley Jordan recovered her outrage.` Diagnose the root cause and propose a robust fix that won't corrupt sentence structure."

**What a weak model will do**: Suggest better regex. Suggest NER with a confidence threshold. Miss that "Limp" was being treated as a proper noun due to capitalisation at sentence start. Recommend spaCy without understanding the failure mode.

**What a strong model will do**: Identify that the root cause is capitalisation-as-NER-signal at sentence boundaries. Propose position-aware filtering (skip tokens at sentence start unless also tagged inside the sentence). Suggest using dependency parse role (not just NER label) to distinguish names from other capitalised words. Mention that summary output also needs the same fix to stay consistent with input.

**Latent requirements**: Identify the sentence-start capitalisation ambiguity specifically. Propose a position-aware or dependency-parse-aware guard. Note that both input and output must be augmented consistently.

**Hard failures**: "Use a better NER model." Not identifying capitalisation as the trigger. Not mentioning the output/summary side of the problem.

**Expected artifacts**: Fixed augmentation logic or algorithm.

**Why it's hard to game**: The failure mode is subtle. It requires understanding NER signal sources, not just NER model quality.

---

### 3. `infra_pipeline_resumable_mongodb`

**Why this reflects your real work**: You built a multi-stage MongoDB ingestion pipeline with status codes, disk cache, tqdm, rich, and InfluxDB telemetry. The failure modes you care about are exactly the ones that show up in a messy corpus at scale.

**Prompt**: "Design a Python pipeline that ingests EPUB files from a directory into MongoDB, processes them through stages (WANTED → TEXT_CONVERTED → CHAPTER_CONVERTED or REJECTED_*), and is fully resumable on restart. The corpus is ~15,000 books. Pipeline dies sometimes. Assume duplicate EPUBs are present. Show me the schema, status transitions, and the resumable processing loop."

**What a weak model will do**: Write a simple for-loop with a `try/except`. Use a flat JSON file for state. Not think about idempotency. Not define status codes. Not handle duplicates. Not handle partial chapter conversion.

**What a strong model will do**: Define an enum or constants for status codes. Use MongoDB upsert with a content hash as idempotency key. Query for `status: WANTED` at startup to resume. Handle partial state gracefully (e.g. TEXT_CONVERTED but not CHAPTER_CONVERTED). Use a `diskcache` or similar for intermediate pre-Mongo state. Mention logging with record counts.

**Latent requirements**: Idempotent writes. Content-hash deduplication. Status-code driven resumability. Partial progress recovery.

**Hard failures**: Reprocessing already-completed records on restart. No deduplication. No intermediate state.

**Expected artifacts**: Schema, status enum, resumable loop.

**Why it's hard to game**: Requires knowing how to structure stateful batch processing, not just write a loop.

---

### 4. `ml_distributed_eval_debug`

**Why this reflects your real work**: You hit this exact problem — metrics silently stopping under `torchrun`. It's a canonical HuggingFace + DeepSpeed failure mode that weak models will either not know about or diagnose incorrectly.

**Prompt**: "My `compute_metrics` function stops being called when I switch from single-GPU to `torchrun --nproc-per-node=2` with DeepSpeed. Training loss looks fine. No errors. `eval_strategy='steps'` is set. What are the most likely root causes, in priority order, and what are the concrete fixes for each?"

**What a weak model will do**: Say "check your `compute_metrics` function." Suggest adding print statements. Maybe mention `local_rank`. Not diagnose the interaction between DeepSpeed, `DataCollator`, prediction gathering, and `predict_with_generate`.

**What a strong model will do**: Identify `DataCollatorWithPadding` being wrong for seq2seq (should be `DataCollatorForSeq2Seq`). Explain that `predict_with_generate=True` must be set in `Seq2SeqTrainingArguments`. Explain that DeepSpeed may suppress evaluation on non-rank-0 processes without the right config. Mention `eval_accumulation_steps` for memory issues with long sequences. Mention that `compute_metrics` receives `EvalPrediction` and padded labels must be unmasked with `-100`.

**Latent requirements**: `DataCollatorForSeq2Seq`. `predict_with_generate`. DeepSpeed rank-0 eval gating. `-100` label masking in `compute_metrics`.

**Hard failures**: "Add debug prints." Not mentioning `DataCollator` or `predict_with_generate`. Generic "check your distributed config" advice.

**Expected artifacts**: Ordered diagnostic checklist with concrete code fixes.

**Why it's hard to game**: Requires knowing the specific interaction surface between HuggingFace Trainer, DeepSpeed, and seq2seq evaluation. Not in tutorials.

---

### 5. `nlp_ner_domain_shift_fiction`

**Why this reflects your real work**: You built RUNER for literary fiction. The failure modes of standard NER on fiction (titles like "the First Enchantress," aliases, epithets, no capitalisation norms) are exactly what you've navigated.

**Prompt**: "I need to train a NER model for character extraction from fantasy fiction. The training data has ~15,000 books. Entities are character names, which include: titles used as names ('the First Enchantress'), epithets ('the Bloody-Nine'), single-word names ('Glokta'), and full names. Standard CoNLL-trained NER fails. Describe your training data strategy, label schema, evaluation approach, and what architectural choices you'd make and why."

**What a weak model will do**: "Fine-tune BERT on CoNLL-2003 with domain adaptation." Suggest adding more training data. Use token-level F1. Not address title-as-name, single-word names, or alias resolution.

**What a strong model will do**: Propose BIO or BIOES schema with CHARACTER-specific labels. Discuss the capitalisation noise problem at sentence boundaries. Propose span-level (seqeval) evaluation not token-level. Discuss alias-aware evaluation (does 'the Bloody-Nine' and 'Logen Ninefingers' count as the same entity?). Consider CRF head over BERT for structured decoding. Discuss the train/eval split needing to be book-level not sentence-level to avoid leakage. Mention that names appearing in the training split will inflate eval F1 if split incorrectly.

**Latent requirements**: Span-level evaluation. Book-level train/eval split. Title/epithet handling. Alias awareness.

**Hard failures**: Token-F1 only. Sentence-level split. CoNLL fine-tune without addressing domain shift. No mention of aliases.

**Expected artifacts**: Label schema, data strategy, evaluation setup.

**Why it's hard to game**: Requires knowing the specific failure modes of NER on literary text, not just NER in general.

---

### 6. `ml_checkpoint_reload_missing_keys`

**Why this reflects your real work**: You hit the exact missing keys issue (`encoder.embed_tokens.weight`, `decoder.embed_tokens.weight`, `lm_head.weight`) when reloading from best checkpoint with early stopping.

**Prompt**: "I'm using HuggingFace `Seq2SeqTrainer` with `load_best_model_at_end=True` and `EarlyStoppingCallback`. On training completion I get: `There were missing keys in the checkpoint model loaded: ['encoder.embed_tokens.weight', 'decoder.embed_tokens.weight', 'lm_head.weight']`. The model seems to work but I don't trust it. What is actually happening, what is the risk, and what is the correct fix?"

**What a weak model will do**: Say "these are tied weights, it's fine, ignore the warning." Not explain why they're missing. Not explain what tied weights are or whether this specific pattern is safe. Not propose a verification approach.

**What a strong model will do**: Explain that T5 uses tied embeddings (`lm_head.weight = encoder.embed_tokens.weight`) and these are intentionally excluded from checkpoint saves to save space. Explain that `from_pretrained` re-ties them on load, so the warning is technically safe for T5. However: note that the safe handling depends on the model correctly implementing `_tie_weights()`. Propose a verification step (compare weight tensors after reload). Note that for custom model subclasses this assumption may not hold and should be explicitly verified. Suggest `save_pretrained` at the end with `state_dict` inspection to confirm.

**Latent requirements**: Understanding of tied weights in T5. Verification approach. Caveat about custom subclasses. Safe vs unsafe warning distinction.

**Hard failures**: "Ignore it, it's fine." Not explaining tied weights. No verification step.

**Expected artifacts**: Explanation + verification code.

**Why it's hard to game**: Requires knowing T5's specific architecture and weight tying, not just generic HuggingFace checkpoint behaviour.

---

### 7. `nlp_cliche_detection_system_design`

**Why this reflects your real work**: You've spent significant time on this problem — semantic embeddings, corpus-derived patterns, 198-node trope taxonomy, Gemini annotation pipeline, BERT classifier. You have strong opinions on what's hard here.

**Prompt**: "Design a cliché detection system for a writing IDE that operates at paragraph level on literary fiction. The system should distinguish clichéd phrasing from legitimate genre conventions. It should not use a static list. Describe the full architecture: how you'd build the training data, what the model looks like, how you'd evaluate it, and what the key failure modes are."

**What a weak model will do**: "Use a pre-trained model from HuggingFace." Suggest cosine similarity to a static phrase list. Not address the genre convention problem. Not address how to build training data without human annotation. Use token-level classifier without addressing the paragraph-level context need.

**What a strong model will do**: Propose a corpus-derived approach (frequency over semantic clusters across diverse authors as the cliché signal). Use semantic embeddings with cross-author frequency weighting. Address the genre convention problem (same phrase is clichéd in literary fiction, conventional in romance). Propose using an LLM (e.g. Gemini) as the annotator to generate silver labels at scale. Discuss evaluation: precision matters more than recall for a writing tool (false positive is worse than miss). Discuss multi-label severity (high/medium/low) rather than binary. Acknowledge that the "data-driven cliché" approach requires sufficient corpus diversity.

**Latent requirements**: Corpus-derived signal. LLM annotation at scale. Genre-conditioned scoring. Precision-oriented evaluation.

**Hard failures**: Static phrase list. Pre-trained model with no training strategy. No evaluation design.

**Expected artifacts**: System architecture with data pipeline, model design, and evaluation plan.

**Why it's hard to game**: The problem has no obvious pre-packaged solution. Requires real architectural thinking.

---

### 8. `ml_t5_seq2seq_data_collator_mismatch`

**Why this reflects your real work**: You've run `DataCollatorWithPadding` where `DataCollatorForSeq2Seq` was needed. This is a specific, silent failure mode.

**Prompt**: "I'm training a T5 model for narrative summarisation using `Seq2SeqTrainer`. My training loss decreases but eval ROUGE scores are always 0.0. My `compute_metrics` is definitely being called. What is the most likely cause and fix? Here is my Trainer init: `data_collator=DataCollatorWithPadding(tokenizer)`."

**What a weak model will do**: "Check your ROUGE implementation." "Print `pred.predictions`." Maybe eventually mention the data collator but without explaining why it's wrong.

**What a strong model will do**: Immediately identify `DataCollatorWithPadding` as the root cause for a seq2seq task. Explain that it doesn't handle decoder `labels`, doesn't replace padding with `-100`, and doesn't set `decoder_input_ids`. Note that this means the model receives corrupted decoder inputs during eval generation, producing garbage sequences that score 0. Provide the correct fix (`DataCollatorForSeq2Seq(tokenizer, model=model, label_pad_token_id=-100)`). Note that `predict_with_generate=True` must also be set. Note that training loss could still decrease because teacher forcing in training doesn't expose this bug.

**Latent requirements**: Identify `DataCollatorWithPadding` as wrong for seq2seq. Explain decoder label handling. Explain why training looks fine but eval is broken. `predict_with_generate=True` mention.

**Hard failures**: "Check ROUGE implementation." Not identifying data collator. Not explaining the decoder side.

**Expected artifacts**: Diagnosis + corrected Trainer init.

**Why it's hard to game**: The symptom (0.0 ROUGE despite compute_metrics being called) has a specific, non-obvious root cause. Sounding plausible while being wrong is easy here.

---

### 9. `writing_prose_critique_gritty_fantasy`

**Why this reflects your real work**: You write gritty fantasy with specific aesthetic standards (not grimdark, italics for internal thought, no bold for emphasis, spaced not indented paragraphs). You have strong taste and would immediately detect shallow model prose.

**Prompt**: "Here is an opening scene from a gritty fantasy novel. Critique it for: (a) prose quality at the sentence level, (b) use of cliché and lazy writing, (c) what the POV character's voice reveals about itself vs. what is stated, and (d) what you would do differently with the first paragraph. Be specific and ruthless. Do not hedge. \n\n[SCENE: A scarred soldier watches a village burn from a hillside, thinking about the war, his lost companions, and whether he's still a good man.]"

**What a weak model will do**: Generic praise + mild suggestions. "Consider varying sentence length." "Strong imagery." "The character's introspection is effective." Treat cliché as acceptable. Not distinguish between grimdark wallowing and earned darkness.

**What a strong model will do**: Call out specific clichés (scarred soldier watching fire = visual cliché). Critique tell-vs-show on the "is he still a good man" question — this is pure tell. Note that "lost companions" is earned emotional territory only if the writing earns it, which it hasn't. Propose showing the character through action or specific detail (what is he actually doing while watching?). Distinguish grimdark (darkness for effect) from gritty (darkness earned by character). Critique sentence rhythm if the model generates any.

**Latent requirements**: Specific cliché identification. Distinguish stated vs. revealed character. Concrete rewrite suggestion. No hedging.

**Hard failures**: Generic advice. "This is effective." No specific cliché identification. Rewrite that reproduces clichés.

**Expected artifacts**: Paragraph-level critique + rewrite of first paragraph.

**Why it's hard to game**: Requires genuine prose taste, not pattern-matching to "good writing advice."

---

### 10. `ml_tokenizer_subword_offset_alignment`

**Why this reflects your real work**: You've built span extraction with offset mapping, handled subword token alignment for character-level NER, and understand the difference between token position and character position.

**Prompt**: "I'm building a character name extractor for fiction. My tokenizer splits 'Bayaz' into ['Bay', '##az']. My BIO tagger predicts B-CHAR on 'Bay' and I-CHAR on '##az'. I need to recover the original character span `(start_char, end_char)` in the original string. Write the span reconstruction logic using HuggingFace offset_mapping, including handling for: (a) multi-token spans, (b) mismatched I-tag starts (I-CHAR with no preceding B-CHAR), and (c) CLS/SEP tokens."

**What a weak model will do**: Index directly into the token list without using offset_mapping. Ignore CLS/SEP. Not handle mismatched I-tags. Use `tokenizer.decode(token_ids)` and hope.

**What a strong model will do**: Use `encoding.offset_mapping`. Correctly skip None offsets for CLS/SEP. Aggregate start_char from first B-token's offset, end_char from last I-token's offset[1]. Handle mismatched I-tag by either starting a new span or discarding the token. Note that `(0, 0)` offsets indicate special tokens. Mention that `add_special_tokens=True` must be handled.

**Latent requirements**: `offset_mapping` usage. CLS/SEP special token handling. Mismatched I-tag recovery strategy. Character-level span assembly.

**Hard failures**: Not using offset_mapping. Direct token indexing. No special token handling.

**Expected artifacts**: Working span reconstruction function.

**Why it's hard to game**: Requires knowing HuggingFace tokenizer internals specifically, not just NLP concepts.

---

### 11. `ml_training_data_quality_fiction_augmentation`

**Why this reflects your real work**: You've built augmentation pipelines for T5 summarisation on literary text. The intersection of NLP augmentation + literary domain has specific failure modes.

**Prompt**: "I'm augmenting a dataset of (chapter, summary) pairs from fantasy novels. Propose 5 augmentation strategies, rank them by expected data quality, and for each describe: what it does, what can go wrong in a literary corpus specifically (not a news or academic corpus), and how you'd validate the augmented examples before adding them to training."

**What a weak model will do**: List generic NLP augmentation techniques (synonym replacement, back-translation, deletion) without addressing literary-specific failure modes. Not discuss validation. Not rank by quality.

**What a strong model will do**: Flag that synonym replacement is dangerous in fiction (character names, world-specific terms like magic system names, cannot be synonymised). Back-translation is risky for literary prose (destroys style). Paraphrase via LLM (e.g. Gemini) is the safest for summary augmentation. Proper noun replacement is high-risk without position-awareness (as you experienced). Propose validation via roundtrip consistency check. Rank by expected quality impact.

**Latent requirements**: Literary-domain specific failure modes. Validation strategy. Name/proper-noun awareness.

**Hard failures**: Generic augmentation list. No validation. No literary-specific risks.

**Expected artifacts**: Ranked strategy list with failure modes and validation.

**Why it's hard to game**: Requires knowing what breaks in literary text specifically, not general NLP augmentation.

---

### 12. `design_eval_narrative_summarisation`

**Why this reflects your real work**: You've trained t5-narrative-summary-small. ROUGE is the default metric. You know ROUGE is wrong for narrative summarisation.

**Prompt**: "I've trained a T5 model to summarise fantasy novel chapters. ROUGE-2 is 0.34, ROUGE-L is 0.41. A colleague says these are 'decent.' Are they? Design a better evaluation protocol for narrative chapter summarisation. Be specific about what ROUGE measures, what it misses for this task, and what alternative or supplementary metrics you'd use."

**What a weak model will do**: "ROUGE-2 of 0.34 is reasonable." "Consider BLEU." Maybe mention BERTScore. Not explain what ROUGE actually measures or why it's wrong here.

**What a strong model will do**: Explain that ROUGE is n-gram overlap, which rewards lexical similarity to a reference. In narrative summarisation, a good summary might use completely different phrasing than the reference. Note that fantasy novels have name-heavy content — ROUGE will over-reward summaries that repeat character names even if they say nothing meaningful. Propose: (1) human evaluation of faithfulness (does the summary accurately represent what happened?), (2) entailment-based coverage check (does the source entail the summary?), (3) information extraction consistency (do extracted entities/events in source appear in summary?), (4) narrative-specific: does the summary mention the primary POV character, the main conflict, and the resolution/cliffhanger? Propose a rubric, not just a metric.

**Latent requirements**: ROUGE failure mode analysis. Fantasy-domain specific issues (name density). Rubric-based evaluation. Faithfulness vs. fluency distinction.

**Hard failures**: "ROUGE-2 of 0.34 is decent." Suggesting BLEU. BERTScore-only.

**Expected artifacts**: Evaluation protocol document.

**Why it's hard to game**: Requires genuine understanding of ROUGE's limitations in the narrative domain.

---

### 13. `arch_writing_ide_context_management`

**Why this reflects your real work**: You built Promptual with dynamic lore condensation for inference context, X-Ray metadata, folder-based bundle storage, and a tri-view layout. The hard problem is what to put in the LLM context window for a writing assistant.

**Prompt**: "I'm building a writing IDE for long-form fiction (~100k word novels). The AI assistant needs context to help the writer continue a scene. The full manuscript won't fit in a 128k context window and even if it did, performance degrades. Design the context management strategy: what goes in the context window, how do you decide what's relevant, and how do you handle lore, character state, and plot continuity."

**What a weak model will do**: "Use a sliding window of recent text." "Retrieve top-K chunks with RAG." Generic RAG answer without understanding fiction-specific context needs.

**What a strong model will do**: Distinguish between: (a) immediate context (current scene + recent scenes), (b) character state (physical location, emotional state, known relationships — changes over time), (c) lore (stable world facts — doesn't change), (d) plot state (what has happened, what has been foreshadowed — partial ordering). Propose different retrieval strategies for each. Note that character state is stateful and must be updated, not just retrieved. Suggest a condensed "state card" per character that tracks current values. Note that lore can be RAG'd but should be deduplicated to avoid repetition. Suggest that the AI itself can maintain condensed state summaries as a background task.

**Latent requirements**: Stateful character context vs. static lore. Dynamic condensation strategy. Plot continuity (foreshadowing) handling.

**Hard failures**: Sliding window. Generic RAG. No distinction between character state and lore.

**Expected artifacts**: Context management architecture.

**Why it's hard to game**: Requires understanding fiction-specific context semantics, not just LLM context window management.

---

### 14. `ml_loss_divergence_diagnosis`

**Why this reflects your real work**: You've debugged training runs where eval loss and F1 diverge (F1 climbing, loss rising in a U-shape), discussed gradient dynamics, and have real intuitions about what these signals mean.

**Prompt**: "My BERT-based token classifier shows: training loss decreasing smoothly, eval F1 climbing steadily, but eval CE loss forming a U-shape (bottoms out at epoch 4, then rises despite F1 continuing to improve). The task is BIO tagging on ~50k sentence literary corpus. What is happening and what should I do about it?"

**What a weak model will do**: "This looks like overfitting, reduce learning rate." "Add dropout." "Use early stopping on eval loss." Not explain the F1/loss divergence mechanism.

**What a strong model will do**: Explain that the model is becoming increasingly confident — correct predictions are pushed toward 1.0, which helps F1, but confident wrong predictions are penalised exponentially by CE loss. This is a calibration divergence, not overfitting in the traditional sense. The model is not getting worse at classification, it's becoming poorly calibrated. Note that early stopping on eval loss would kill a model that's still improving at F1. Recommend early stopping on span-F1, not CE loss. Suggest temperature scaling or label smoothing if calibration matters for downstream use (e.g. confidence scores in a UI). Note this is especially common when class imbalance exists (O tokens vastly outnumber B/I in BIO tagging).

**Latent requirements**: Calibration divergence explanation. Class imbalance in BIO. Early stopping on F1, not loss. Label smoothing option.

**Hard failures**: "Overfitting, reduce LR." "Use early stopping on eval loss." No explanation of F1/loss divergence.

**Expected artifacts**: Diagnosis + concrete recommendation.

**Why it's hard to game**: Requires genuine understanding of loss-metric divergence dynamics, not surface pattern matching.

---

### 15. `critique_llm_generated_prose`

**Why this reflects your real work**: You thought about GPT slop detection as a byproduct of cliché detection. You have strong prose taste and work with generated fiction regularly.

**Prompt**: "Here is a 200-word fantasy prose passage. Identify all signals that suggest it was generated by an LLM rather than written by a human author. Be specific about which phrases, constructions, or patterns are diagnostic. Do not just say 'it feels generic' — name the mechanism.\n\n[AI-generated passage to be inserted at evaluation time]"

**What a weak model will do**: "This might be AI generated because it uses generic phrasing." "The description is formulaic." Name no specific mechanisms. Possibly fail to detect it at all and praise it.

**What a strong model will do**: Identify: unnaturally consistent sentence length distribution. Adverb-heavy emotional description ("he said softly," "she replied quietly"). Hedged transitions ("it was as if," "somehow," "there was something about"). Over-explanation of subtext (stating emotion that should be shown). Unlikely lexical choices in fantasy (model-specific vocabulary patterns: "tapestry," "palpable," "testament to"). Symmetric sentence structure (AI loves parallel construction). Paragraph transitions that summarise what was just said. Specific tells like "in the grand tapestry of" or "a sense of [noun]."

**Latent requirements**: Mechanism-level identification, not vibes. Multiple distinct signal types. Genre-awareness.

**Hard failures**: "It feels generic." "It might be AI because [vague]." Praising it.

**Expected artifacts**: Annotated passage with mechanism labels.

**Why it's hard to game**: Requires genuine stylistic awareness at the mechanism level, not just a binary "AI or not" judgment.

---

### 16. `infra_ml_pipeline_observability`

**Why this reflects your real work**: You set up InfluxDB + Grafana for MongoDB pipeline telemetry, with 15–60 minute status snapshots, because you needed to observe a long-running data pipeline.

**Prompt**: "I have a multi-stage Python data pipeline that runs for days. Stages are: INGEST → TEXT_EXTRACT → CHAPTER_SEGMENT → TOKENIZE → WRITE_DB. Each record has a status. I want observability: know when stages are stalling, detect error spikes, and see throughput over time. I am not running this in production — this is a home lab. Propose the simplest observability stack that gives me what I need without operational overhead."

**What a weak model will do**: Recommend Datadog, Prometheus + Grafana full stack, OpenTelemetry. Massively over-engineer for a home lab. Not consider the operational burden.

**What a strong model will do**: Recommend InfluxDB (line protocol, trivially writable from Python) + Grafana as the minimal viable stack. Propose a simple Python function that aggregates status counts from MongoDB and writes them to InfluxDB on a cron/timer. Point out that the query is essentially your existing MongoDB aggregation pipeline. Recommend at most 3 dashboards: (1) stage throughput over time, (2) error rate per stage, (3) current status distribution. Mention that `diskcache` or similar is appropriate for intermediate state if stages fail partway through records. Keep it to ~50 lines of instrumentation code.

**Latent requirements**: Home lab constraint. Simplicity over completeness. MongoDB aggregation → InfluxDB → Grafana path. Not cloud-native.

**Hard failures**: Recommending Prometheus. OpenTelemetry. Datadog. Kubernetes sidecar patterns.

**Expected artifacts**: Architecture + instrumentation code.

**Why it's hard to game**: Requires reading and respecting the "home lab" constraint rather than defaulting to enterprise solutions.

---

### 17. `nlp_seqeval_vs_token_f1`

**Why this reflects your real work**: You care about span-level evaluation for NER, distinguish it from token-level F1, and have seen the difference matter in practice.

**Prompt**: "My BIO tagger gets token-level F1 of 0.89 but seqeval span-F1 of 0.61. Is this a good model? What does this gap tell you about where it's failing? How would you diagnose which specific error type is dominant?"

**What a weak model will do**: Average the two numbers and call it "decent." Not explain what the gap means. Maybe suggest more training data.

**What a strong model will do**: Explain that token-F1 can be inflated by correct O-token prediction (O is the majority class in BIO — getting O right is easy). Span-F1 requires getting the exact span correct — both boundary tokens right and the label right. A 0.89 vs 0.61 gap suggests systematic boundary errors: the model is detecting entities but getting their start or end wrong. Propose diagnostic: compute confusion matrix at the BIO label level — are B→I transitions being lost? Are spans starting correctly but extending too far or too short? Propose a span error taxonomy (missed entity, spurious entity, wrong boundary, wrong type). Suggest visualising predictions on 20 representative samples before chasing metrics.

**Latent requirements**: O-token inflation explanation. Span boundary error hypothesis. Diagnostic approach. Span error taxonomy.

**Hard failures**: "Both scores look decent." Averaging. Suggesting more training data without diagnosis.

**Expected artifacts**: Diagnosis + diagnostic approach.

**Why it's hard to game**: Requires knowing the specific mechanics of BIO tagging evaluation, not just general ML evaluation advice.

---

### 18. `ml_custom_dataset_class_messy`

**Why this reflects your real work**: Your data is not benchmark-clean. You deal with malformed JSONL, missing fields, edge cases like empty summaries, books with no chapters, and rejected records that shouldn't enter training.

**Prompt**: "I'm building a PyTorch Dataset class for (input_text, summary) pairs loaded from a JSONL file. The file is messy: some records have empty summaries, some have inputs that are too long, some are malformed JSON, and some records are marked `status: REJECTED`. Write the Dataset class with appropriate handling for all of these, and explain the tradeoffs in each handling decision."

**What a weak model will do**: Write a Dataset that silently skips bad records with `continue`. Not explain tradeoffs. Not handle tokenisation length. Not mention that skipping records changes dataset length and could corrupt batch indices.

**What a strong model will do**: Pre-filter at load time (not at `__getitem__`) to ensure `len()` is stable. Log rejected record counts by type. Handle malformed JSON with `json.loads` in try/except, log the line for inspection. Filter empty summaries (optionally configurable via `allow_empty`). Handle overlength inputs by truncating with a warning, or pre-filtering and logging — with explicit discussion of the tradeoff. Exclude REJECTED status records. Return consistent tensor shapes.

**Latent requirements**: Pre-filter vs. per-item handling. Stable `len()`. Logging. Configurable tolerance (allow_empty flag). Tradeoff explanations.

**Hard failures**: Silent skips in `__getitem__`. No logging. No length handling. No tradeoff discussion.

**Expected artifacts**: Dataset class + commentary.

**Why it's hard to game**: Messy data handling requires operational judgment, not just knowing PyTorch Dataset API.

---

### 19. `design_evaluation_rubric_literary_nlp`

**Why this reflects your real work**: You've built or considered evaluation for narrative summarisation, cliché detection, NER, and character extraction. Evaluation design for literary NLP is genuinely underspecified.

**Prompt**: "Design an evaluation rubric for a character extraction system that, given a novel chapter as input, outputs a list of `{name, summary, type}` records where type ∈ {character, place, lore}. The system will be evaluated against a gold annotation set, but gold annotations are imperfect and annotators sometimes disagree on whether something is a 'character' vs 'lore'. How do you design an evaluation that is rigorous enough to be useful without being falsely precise?"

**What a weak model will do**: "Use exact match F1." "Use fuzzy string matching." Not address the type disagreement problem. Not address gold annotation imperfection.

**What a strong model will do**: Propose separate metrics for each concern: (1) name recall (did you find the entity?) using fuzzy/alias-aware matching, (2) type accuracy conditional on finding the entity, (3) summary quality via a rubric (does the summary contain the key facts present in the chapter?). Propose treating type as soft labels where character/lore disagreement is modelled as a confidence range. Propose inter-annotator agreement measurement before treating gold as ground truth. Propose human spot-check of false positives and false negatives rather than pure automated metrics. Note that precision matters more than recall for a writing tool (spurious entities are more disruptive than missed ones).

**Latent requirements**: Alias-aware matching. Type as soft label. Gold annotation quality assessment. Precision vs. recall tradeoff.

**Hard failures**: "Use F1." Exact string match. No acknowledgment of gold imperfection.

**Expected artifacts**: Evaluation rubric design.

**Why it's hard to game**: Requires knowing that literary entity extraction evaluation is genuinely unsolved, not just applying standard NLP metrics.

---

### 20. `ml_compute_loss_weighted_multi_label`

**Why this reflects your real work**: You're working with multi-label and multi-head architectures (trope taxonomy with 198 classes, BIO + span confidence). Weighted loss for class imbalance in hierarchical classification is a real engineering problem.

**Prompt**: "I have a paragraph-level multi-label classifier for literary tropes with 198 classes across 7 top-level categories. The class distribution is highly skewed — some tropes appear in 20% of paragraphs, others in 0.1%. I'm using BCEWithLogitsLoss. Describe how you'd handle class imbalance, what the tradeoffs are between pos_weight and focal loss and sampling, and write the loss function."

**What a weak model will do**: "Use class weights." Provide generic `pos_weight` calculation without addressing the multi-label + hierarchical case. Not address focal loss. Not address the 198-class scale.

**What a strong model will do**: Explain that `pos_weight` in BCEWithLogitsLoss scales the positive class penalty per label — compute as `(neg_count / pos_count)` per class with clipping to avoid extreme weights. Compare to focal loss: focal loss reduces the contribution of easy negatives dynamically during training, which is often better for very imbalanced multi-label tasks. Discuss the hierarchical constraint: if a leaf node fires, the parent category should also fire — propose hierarchical loss or post-processing. Address the 198-class scale: compute class frequencies once at dataset init, not per-batch. Suggest macro F1 as eval metric (not micro, which would be dominated by frequent classes).

**Latent requirements**: Per-class `pos_weight` computation. Focal loss comparison. Hierarchical constraint. Macro vs. micro F1.

**Hard failures**: Generic class weights. No focal loss mention. No hierarchical constraint. Micro F1 for eval.

**Expected artifacts**: Loss function + training setup.

**Why it's hard to game**: Requires knowing multi-label, multi-class imbalance handling at scale, not just binary imbalance.

---

## Part 3 — Top 8 Ranked by Diagnostic Value

1. **`ml_distributed_eval_debug`** (#4) — Most diagnostic. Requires knowing the specific failure surface of DeepSpeed + HuggingFace + seq2seq eval. Weak models will sound plausible and be completely wrong. You hit this exact problem.

2. **`ml_t5_seq2seq_data_collator_mismatch`** (#8) — Single-root-cause diagnosis with a counterintuitive symptom. Training loss looks fine, eval is broken. The root cause (`DataCollatorWithPadding` in a seq2seq trainer) is specific, not guessable. Diagnostic of real HuggingFace depth.

3. **`nlp_augmentation_structural_corruption`** (#2) — You lived this bug. Requires identifying the capitalisation-at-sentence-boundary signal as the root cause. Generic "better NER" answers are clearly wrong. Strong signal of genuine NLP judgment.

4. **`nlp_seqeval_vs_token_f1`** (#17) — Fast to run, highly diagnostic. The 0.89 vs 0.61 gap is a real scenario. Requires explaining O-token inflation and span boundary errors. Weak models almost universally fail this.

5. **`writing_prose_critique_gritty_fantasy`** (#9) — The only non-ML task in the top 5. Requires genuine prose taste and the ability to distinguish stated vs. revealed character. Also directly relevant to your writing work.

6. **`ml_checkpoint_reload_missing_keys`** (#6) — Specific, falsifiable, real failure mode. Models that don't know T5 weight tying will give dangerously wrong advice ("just ignore it" could be wrong for custom subclasses).

7. **`nlp_ner_domain_shift_fiction`** (#5) — High relevance to RUNER. Requires knowing book-level train/eval split, span evaluation, and title/epithet handling. Generic NER advice fails immediately.

8. **`ml_loss_divergence_diagnosis`** (#14) — Requires explaining the F1/CE-loss divergence mechanism (calibration, not overfitting). Models that say "add dropout" or "reduce LR" fail hard.

---

## Part 4 — Top 5 in Near-RoughBench-Ready Form

---

### Task 1: `ml_distributed_eval_debug`

**`task.yaml`**
```yaml
id: ml_distributed_eval_debug
version: "0.1"
title: "Distributed Eval Silence — DeepSpeed + Seq2SeqTrainer"
domain: ml_engineering
difficulty: high
artifact_required: true
execution_backed: false
tags: [huggingface, deepspeed, distributed, seq2seq, eval, trainer]
seed_problem: "compute_metrics stops being called under torchrun --nproc-per-node=2"
```

**`prompt.txt`**
```
My compute_metrics function stops being called when I switch from single-GPU training
to torchrun --nproc-per-node=2 with DeepSpeed. Training loss decreases normally.
No exceptions are raised. eval_strategy='steps' is set and worked fine before.

My Trainer init looks like this:

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )

What are the most likely root causes, in priority order?
For each, give the concrete fix.
```

**`rubric.yaml`**
```yaml
criteria:
  data_collator_diagnosis:
    weight: 0.30
    description: >
      Identifies DataCollatorWithPadding as wrong for seq2seq.
      Correct replacement: DataCollatorForSeq2Seq(tokenizer, model=model).
    hard_fail_if_missing: true

  predict_with_generate:
    weight: 0.20
    description: >
      Mentions predict_with_generate=True must be set in Seq2SeqTrainingArguments
      for generation-based eval to run correctly.
    hard_fail_if_missing: true

  minus_100_label_masking:
    weight: 0.15
    description: >
      Notes that labels must be masked with -100 for padding, and that
      DataCollatorForSeq2Seq handles this; DataCollatorWithPadding does not.

  deepspeed_rank0_eval:
    weight: 0.15
    description: >
      Mentions that DeepSpeed may suppress compute_metrics on non-rank-0
      processes; proposes checking local_rank or process_index guard.

  ordering_and_prioritisation:
    weight: 0.10
    description: >
      Presents fixes in a plausible priority order (data_collator first,
      predict_with_generate second, DeepSpeed third).

  why_training_looks_fine:
    weight: 0.10
    description: >
      Explains why training loss still decreases despite the eval bug
      (teacher forcing during training bypasses the data collator issue).

scoring_notes: >
  Hard fail on data_collator_diagnosis and predict_with_generate.
  A response that does not identify DataCollatorWithPadding as the root cause
  scores ≤ 0.30 regardless of other content.
  Bonus if the model explains that compute_metrics receives EvalPrediction
  with padded labels and that -100 masking must be undone before metric computation.
```

**Scoring notes**: The data collator diagnosis is the main load-bearing criterion. A model that identifies it earns half the score immediately. The rest is depth. A response that says "check your compute_metrics function" or "add print statements" should score ≤ 0.15.

**Likely judge failure modes**: LLM judges may reward responses that sound exhaustive but miss the root cause. Require the judge to check specifically whether `DataCollatorWithPadding` was named before assigning high scores.

**Execution-backed check**: Run a minimal reproduction — `Seq2SeqTrainer` with `DataCollatorWithPadding`, `torchrun --nproc-per-node=2`, `eval_strategy='steps'` — and confirm that `compute_metrics` is never called. Then apply the fix and confirm it runs. This is a verifiable claim.

---

### Task 2: `ml_t5_seq2seq_data_collator_mismatch`

**`task.yaml`**
```yaml
id: ml_t5_seq2seq_data_collator_mismatch
version: "0.1"
title: "ROUGE Scores Always 0.0 — Root Cause Diagnosis"
domain: ml_engineering
difficulty: medium_high
artifact_required: true
execution_backed: true
tags: [huggingface, t5, seq2seq, rouge, data_collator, evaluation]
seed_problem: "eval ROUGE is 0.0 despite compute_metrics being called; training loss decreases"
```

**`prompt.txt`**
```
I'm training a T5 model for chapter summarisation using Seq2SeqTrainer.
Training loss is decreasing. My compute_metrics function is definitely being called
(I added a print statement and it fires). But eval ROUGE-1, ROUGE-2, ROUGE-L are
always exactly 0.0 every evaluation step.

Here is my full Trainer initialisation:

    trainer = Seq2SeqTrainer(
        model=model,
        args=Seq2SeqTrainingArguments(
            output_dir="./output",
            eval_strategy="steps",
            eval_steps=500,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=2,
            num_train_epochs=10,
        ),
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )

What is the root cause? Provide the fix.
```

**`rubric.yaml`**
```yaml
criteria:
  root_cause_data_collator:
    weight: 0.40
    description: >
      Identifies DataCollatorWithPadding as the direct root cause.
      Must name it specifically.
    hard_fail_if_missing: true

  explain_decoder_label_handling:
    weight: 0.20
    description: >
      Explains that DataCollatorWithPadding does not replace padding tokens
      in labels with -100, corrupting the loss computation and generation inputs
      during evaluation.

  predict_with_generate_missing:
    weight: 0.15
    description: >
      Notes that predict_with_generate=True is not set in Seq2SeqTrainingArguments,
      which means eval runs in loss mode, not generation mode, producing no decoded text.

  correct_fix:
    weight: 0.15
    description: >
      Provides the correct fix: DataCollatorForSeq2Seq(tokenizer, model=model,
      label_pad_token_id=-100) and predict_with_generate=True.

  training_vs_eval_asymmetry:
    weight: 0.10
    description: >
      Explains why training loss still decreases (teacher forcing) while eval is broken.

scoring_notes: >
  A response that diagnoses the root cause incorrectly (e.g., "ROUGE implementation bug",
  "wrong predictions shape") should score ≤ 0.25.
  The 0.0 ROUGE symptom with a working compute_metrics call is specifically diagnostic
  of the data collator + predict_with_generate combination.
```

**Scoring notes**: Both `DataCollatorWithPadding` identification and `predict_with_generate` are required for a passing score. Many models will diagnose one and miss the other.

**Likely judge failure modes**: Judges may reward technically correct but misdirected advice (e.g. "check your ROUGE implementation" sounds reasonable). Require the judge to check whether the specific training/eval asymmetry was explained.

**Execution-backed check**: Verifiable. Run the exact Trainer config above with a small T5 and minimal data. Confirm 0.0 ROUGE. Apply fix. Confirm ROUGE scores.

---

### Task 3: `nlp_augmentation_structural_corruption`

**`task.yaml`**
```yaml
id: nlp_augmentation_structural_corruption
version: "0.1"
title: "Name Augmentation Corrupts Sentence Structure"
domain: nlp_engineering
difficulty: medium_high
artifact_required: true
execution_backed: false
tags: [augmentation, ner, tokenisation, literary_nlp, data_pipeline]
seed_problem: "Proper noun replacement replaces 'Limp' with 'Chris' at sentence boundaries"
```

**`prompt.txt`**
```
I'm augmenting a fantasy novel summarisation dataset by replacing character names
with synthetic alternatives to increase training diversity.

My pipeline is mostly working, but I'm seeing this failure:

Original input:
"Limp as rags on the floor, the First Enchantress recovered her rightful sense of outrage."

Augmented input:
"Chris as rags on the floor, the Riley Jordan recovered her rightful sense of outrage."

Original summary:
"Limp as rags on the floor, the First Enchantress confronts a devastated room."

Augmented summary:
"Chris as rags on the floor, the Riley Jordan confronts a devastated room."

Diagnose the root cause precisely. Then propose a fix that is robust to this class
of failure. The fix must work for literary prose, not just newswire text.
```

**`rubric.yaml`**
```yaml
criteria:
  root_cause_capitalisation:
    weight: 0.35
    description: >
      Identifies that the NER model (or heuristic) is treating 'Limp' as a proper
      noun due to sentence-initial capitalisation. Must not just say "NER is wrong"
      but identify the signal source (capitalisation at sentence boundary).
    hard_fail_if_missing: true

  position_aware_fix:
    weight: 0.25
    description: >
      Proposes a position-aware fix: skip or validate replacements at sentence-initial
      positions unless the token also appears as a capitalised entity mid-sentence.
      OR proposes using dependency parse to confirm the token functions as a noun/NP.

  summary_consistency:
    weight: 0.15
    description: >
      Notes that the summary must be augmented consistently with the input,
      and that the current failure propagates to the summary side.

  literary_robustness:
    weight: 0.15
    description: >
      Addresses that this must work on literary prose specifically, noting
      that literary prose uses capitalised titles, epithets, and honorifics
      that standard NER misclassifies more often than newswire.

  validation_strategy:
    weight: 0.10
    description: >
      Proposes a validation check: e.g. verify the augmented sentence is
      grammatically coherent by checking POS tags or a simple grammar check
      on the replacement result.

scoring_notes: >
  "Use a better NER model" without identifying the capitalisation signal
  source scores ≤ 0.20. The root cause must be specific.
  "Use spaCy with 99% reliability" is the wrong answer — the problem is
  structural (sentence-initial capitalisation), not NER model quality.
```

**Scoring notes**: The trap answer is "use a better NER model" or "use spaCy." These fail because the problem is the capitalisation signal, not the model quality. Any NER model will struggle with sentence-initial capitalisation unless position-awareness is added.

**Likely judge failure modes**: LLM judges may reward "use a better NER model" because it sounds like a reasonable improvement. Require the judge to check whether the capitalisation mechanism was explicitly named.

**Artifact-backed check**: Run the buggy augmenter on the provided example. Confirm the failure. Apply the position-aware fix. Confirm "Limp" is no longer replaced.

---

### Task 4: `nlp_seqeval_vs_token_f1`

**`task.yaml`**
```yaml
id: nlp_seqeval_vs_token_f1
version: "0.1"
title: "Token F1 vs Span F1 Gap Diagnosis"
domain: nlp_engineering
difficulty: medium
artifact_required: false
execution_backed: false
tags: [ner, evaluation, bio_tagging, seqeval, f1]
seed_problem: "Token F1 = 0.89, span F1 = 0.61 on a BIO tagger"
```

**`prompt.txt`**
```
My BERT-based BIO tagger on a literary character extraction task gets:
- Token-level F1: 0.89
- Seqeval span-level F1: 0.61

The task is character name extraction from fantasy fiction chapters.
Training corpus: ~50,000 sentences.

(a) Is this a good model?
(b) What does the gap between token F1 and span F1 tell you about the
    specific failure mode?
(c) How would you diagnose which error type is dominant?
    Do not just say "look at the confusion matrix" — be specific about
    what you would compute and what patterns you'd look for.
```

**`rubric.yaml`**
```yaml
criteria:
  o_token_inflation:
    weight: 0.25
    description: >
      Explains that token F1 is inflated by correct O-token prediction.
      O is the majority class in BIO tagging; getting O right does not
      indicate entity-level performance. Must name this specifically.
    hard_fail_if_missing: true

  gap_implies_boundary_errors:
    weight: 0.25
    description: >
      Explains that the 0.89 vs 0.61 gap suggests the model is finding
      entities but getting their boundaries wrong (start too early/late,
      end too early/late), since span F1 requires exact boundary match.

  span_error_taxonomy:
    weight: 0.20
    description: >
      Proposes a specific span error taxonomy: missed entity (FN), spurious
      entity (FP), correct entity with wrong boundary, correct entity with
      wrong type. Not just "look at confusion matrix."

  diagnostic_approach:
    weight: 0.20
    description: >
      Proposes a specific diagnostic: compute B→I transition accuracy
      separately from B→O accuracy. Or: compute partial-match vs exact-match
      ratio to distinguish boundary errors from missed entities.

  literary_domain_note:
    weight: 0.10
    description: >
      Notes that literary text has specific NER challenges (sentence-initial
      capitalisation, titles/epithets as names) that may explain boundary errors.

scoring_notes: >
  A response that says "0.89 is good enough" without addressing the span F1
  gap scores ≤ 0.20.
  A response that correctly explains O-token inflation but proposes no
  diagnostic approach scores ≤ 0.50.
```

**Scoring notes**: The O-token inflation explanation is the key discriminator. A model that doesn't know this will likely say "0.89 is decent" or recommend more training data. The diagnostic approach criterion rewards specificity — "look at errors" is not sufficient.

**Likely judge failure modes**: LLM judges may reward responses that mention seqeval and sound knowledgeable without explaining the inflation mechanism. Require O-token inflation to be named explicitly.

---

### Task 5: `writing_prose_critique_gritty_fantasy`

**`task.yaml`**
```yaml
id: writing_prose_critique_gritty_fantasy
version: "0.1"
title: "Gritty Fantasy Prose Critique — Be Ruthless"
domain: writing_taste
difficulty: high
artifact_required: true
execution_backed: false
tags: [prose, creative_writing, critique, fantasy, cliche, character_voice]
seed_problem: "Critique a scarred-soldier-watches-fire scene for prose quality, cliché, and POV voice"
```

**`prompt.txt`**
```
Here is the opening of a gritty fantasy scene. Critique it with no hedging.

---
The rain fell like a curtain of despair as Aldric stood on the ridge, watching
the village burn below. His scarred face was a map of battles fought and friends
lost. The flames danced and crackled, mirroring the turmoil in his soul. He had
done what he had to do. That was what he told himself. But deep down, he wasn't
sure he was still the man he had once been. The good man. The man his mother
had raised.

He watched the fire for a long time.
---

Critique this on four axes:
(a) Sentence-level prose quality — specific issues, named
(b) Cliché and lazy writing — name each instance and explain why it's lazy
(c) POV voice — what does the writing *reveal* about Aldric vs. what does it
    merely *state*? Where is the writer doing the character's work for the reader?
(d) Rewrite the first sentence.

Do not say "consider varying your sentence length" or "strong imagery." Be specific.
Be ruthless. This is a working critique, not a workshop sandwich.
```

**`rubric.yaml`**
```yaml
criteria:
  specific_cliche_identification:
    weight: 0.25
    description: >
      Names specific clichés with explanation: "rain fell like a curtain of despair"
      (weather-mirrors-emotion), "scarred face was a map of battles" (map metaphor cliché),
      "flames danced and crackled" (fire description cliché), "turmoil in his soul"
      (abstract emotion as physical location), "the man his mother had raised" (backstory cliché).
      Must name at least 3 specific instances.
    hard_fail_if_missing: true

  stated_vs_revealed:
    weight: 0.25
    description: >
      Correctly identifies that the passage states Aldric's emotional state
      ("not sure he was still the man he had once been") rather than revealing
      it through action, specific detail, or the character's own thought patterns.
      Must distinguish "telling" from "showing" at the mechanism level, not just
      use the phrase "show don't tell."

  prose_quality_specific:
    weight: 0.20
    description: >
      Names specific sentence-level issues: e.g. passive observation structure
      ("stood... watching"), weak verb choices, sentence rhythm that is
      monotonously declarative, or the bathetic final short sentence being unearned.

  no_hedging:
    weight: 0.15
    description: >
      Response contains no hedging phrases like "this might be intentional,"
      "some readers might enjoy," "there is real potential here," or
      "consider whether." The critique must be direct.

  rewrite_quality:
    weight: 0.15
    description: >
      The rewritten first sentence avoids the weather-as-emotion cliché,
      is more specific and concrete, and reveals something about the character
      rather than setting a generic mood.

scoring_notes: >
  A response that praises the passage or hedges extensively scores ≤ 0.20.
  A response that says "strong imagery" or "effective" for the cliché phrases
  is a hard fail on specific_cliche_identification.
  The rewrite is diagnostic: does the model produce fresh prose or replace
  one cliché with another?
```

**Scoring notes**: The no-hedging criterion is intentionally observable — scan the response for "might," "some readers," "consider," "perhaps," "in some ways." These phrases are hard fails. The rewrite quality is the most diagnostic artifact: a model with genuine taste will produce something substantially different from the original.

**Likely judge failure modes**: LLM judges are trained on feedback that is constructive and balanced. They will want to reward hedged responses. Explicitly instruct the judge that hedging is a failure criterion, not a virtue in this task.

**Artifact-backed check**: The rewritten first sentence can be evaluated against a checklist: (1) no weather-mirrors-emotion device, (2) specific concrete detail, (3) reveals character rather than tells emotion. This is partially automatable.

---

## Part 5 — Gaps In The Current Suite

The three seed tasks cover:
- `swe_scraper_persistent_resumable` — operational Python engineering, infrastructure judgment
- `literary_booker_seven_plots` — factual accuracy, hallucination resistance, correct caveats
- `nlp_bio_off_axis_crf` — NLP judgment, resist transformer autopilot, sane evaluation

**What they miss:**

**Your actual training loop work.** The most recurring, high-stress, high-specificity work in your history is debugging HuggingFace Trainer — `compute_loss`, `DataCollator`, distributed eval, checkpoint saving, `num_items_in_batch`. None of the three tasks touch this. It's your most opinionated, most failure-mode-rich domain.

**Literary domain NLP.** `nlp_bio_off_axis_crf` is domain-specific NER but generic — it doesn't test knowledge of *literary* domain failure modes: sentence-initial capitalisation, title-as-name, alias/epithet entities, book-level train/eval split. Your work is specifically literary and that specificity is not yet tested.

**Prose taste as a technical constraint.** You use literary taste to make technical decisions (what counts as good training data, what makes a summary good, what a cliché detection system should flag). None of the three tasks test aesthetic judgment in a domain you demonstrably care about.

**Data pipeline and observability judgment.** Your infrastructure work (MongoDB ingestion, status codes, InfluxDB telemetry, resumable pipelines) is operationally mature and opinionated. The scraper task touches this lightly but your real standard is more specific — idempotent writes, status-driven resumability, home-lab-appropriate observability.

**Evaluation design as a first-class skill.** You've made active decisions about ROUGE vs. span F1 vs. human eval, seqeval vs. token F1, and calibration vs. loss for early stopping. None of the current tasks test whether a model can reason about evaluation design for non-standard tasks.