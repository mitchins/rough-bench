Good. I have solid signal from your history. Let me build this.

---

## What I infer about your actual work

**From conversation history and memory:**

You're building a CV toolkit centered on a clean perception/reasoning split — specialist CV models as structured tool calls, LLMs reasoning over dense text. You're designing and training a lightweight image captioning model (NanoCaption) with a specific, opinionated architecture. You've caught real bugs (T5 relative position bias clamp overflow at ≥24 tokens, missing BOS prepend). You made a deliberate architectural simplification — replacing a Perceiver-style VisualResampler with a Linear+LayerNorm projection — and validated it correctly. You use Claude Code for executing diffs. You've been deep in CRFs and BIO tagging as part of the NLP toolkit layer.

**Inferred work patterns:**

- You design architectures from first principles and validate intuitions via smoke tests, not vibes. You care about parameter counts, gradient flow, and whether a component actually does what it claims.
- You catch training/inference mismatch bugs — the kind that only surface if you're reading the training loop carefully and thinking about what the model sees at each phase.
- You are suspicious of complexity. You replaced a ~1.43M param Perceiver with a 493k Linear projection and were right to do it. You resist the autopilot toward "bigger = better."
- You think about system-level constraints: routing, gating, tool invocation decisions, not just model internals.
- You care about evaluation honesty — you used BLEU-4, CIDEr, METEOR, BERTScore and you noticed caption length as a confound.
- You're comfortable with messy, under-specified real-world problems and can identify what a solution actually needs versus what it sounds like it needs.
- Your aversions: BERT autopilot, overparameterized components without justification, benchmark theater, shallow "just use a pretrained model" answers, models that sound authoritative while being operationally wrong.

---

## 20 Candidate RoughBench Tasks

---

### 1. `cv_architecture_projection_vs_resampler`

**Title:** Justify or reject a cross-modal projection simplification

**Why this reflects your real work:** You made exactly this decision — VisualResampler vs. Linear+LN — and had clear reasoning. Most models will default to "Perceiver is more expressive" without engaging the actual tradeoffs.

**Prompt:**
> You have a vision encoder that outputs 256 tokens of dimension 768. Your decoder expects cross-attention keys/values of dimension 640. You're considering two options: (A) a Perceiver-style resampler with 64 learned queries, (B) a Linear(768→640) + LayerNorm projection that preserves all 256 tokens. Your model is lightweight (sub-50M params), training budget is tight, and you care about gradient flow. Compare them. Make a recommendation. Justify it concretely, including parameter counts, information bottleneck behavior, and what each option changes about the cross-attention computation.

**What a weak model will do:** Say "Perceiver is more flexible and can learn to attend selectively, so it's generally preferred." Give no parameter counts. Not mention the 256 → 64 token compression as a lossy bottleneck. Not address gradient flow or training dynamics.

**What a strong model will do:** Compute approximate parameter counts for both. Identify that the Perceiver introduces a 4x information bottleneck (256→64 tokens) which may matter for dense captioning. Note that Linear projection preserves full spatial resolution at lower parameter cost. Flag that for a tight budget and per-layer cross-attention, preserving all 256 tokens likely wins. Mention that Perceivers need more training to converge because learned queries start random.

**Latent requirements:** Knows parameter arithmetic. Understands cross-attention key/value dimensionality. Can reason about information compression vs. computational cost tradeoffs. Understands training dynamics, not just theoretical capacity.

**Hard failures:** Recommending Perceiver without noting the bottleneck. Ignoring parameter counts entirely. Not connecting the decision to the downstream cross-attention behavior.

**Expected artifacts:** Rough parameter estimates, explicit tradeoff table or structured comparison, a concrete recommendation with stated assumptions.

**Why it's hard to game:** The correct answer is counter-intuitive (simpler wins). Boilerplate ML writing defaults to "more expressive = better." The prompt contains enough specifics to expose whether the model can actually reason about them.

---

### 2. `train_inference_mismatch_audit`

**Title:** Find the training/inference mismatch in this code

**Why this reflects your real work:** You caught the missing BOS prepend bug. This kind of bug is invisible unless you're carefully reading both the training loop and the generation function and comparing them.

**Prompt:**
> Here is a simplified training loop and inference function for a sequence-to-sequence captioning model. Find every training/inference mismatch. For each mismatch, explain what it causes during inference and how severe it is.
>
> ```python
> # Training
> def forward(self, image, captions):
>     vis_feat = self.encoder(image)          # (B, 256, 768)
>     proj = self.proj(vis_feat)              # (B, 256, 640)
>     tokens = self.tokenizer.encode(captions)
>     input_ids = tokens[:, :-1]              # teacher forcing
>     target_ids = tokens[:, 1:]
>     logits = self.decoder(input_ids, proj)
>     return F.cross_entropy(logits.view(-1, self.vocab_size), target_ids.view(-1))
>
> # Inference
> def generate(self, image, max_len=64):
>     vis_feat = self.encoder(image)
>     proj = self.proj(vis_feat)
>     ids = [self.tokenizer.eos_id()]
>     for _ in range(max_len):
>         logits = self.decoder(torch.tensor([ids]), proj)
>         next_id = logits[0, -1].argmax()
>         if next_id == self.tokenizer.eos_id(): break
>         ids.append(next_id.item())
>     return self.tokenizer.decode(ids[1:])
> ```

**What a weak model will do:** Notice the EOS vs BOS issue superficially or miss it entirely. Not notice that dropout/LayerNorm eval mode isn't set. Maybe flag that greedy decoding differs from beam search (which is a valid note but not a mismatch per se).

**What a strong model will do:** (1) Flag that inference starts with EOS not BOS — the decoder has never seen EOS as a generation prefix during training, so the distribution is corrupted from step 1. (2) Note that `self.encoder.eval()` / `self.decoder.eval()` is not called, so BatchNorm/Dropout behavior diverges. (3) Optionally note that `ids[1:]` strip in decode will silently include the EOS-as-start token in decoded text if tokenizer doesn't filter it. Rank by severity.

**Latent requirements:** Understands teacher forcing and what the model's first token distribution is trained to condition on. Knows about eval mode and its effect on BatchNorm/Dropout. Can think about tokenizer behavior.

**Hard failures:** Not finding the BOS/EOS mismatch. Treating greedy vs beam search as a "mismatch." Not ranking severities.

**Expected artifacts:** Numbered list of mismatches, severity ranking, fix for each.

**Why it's hard to game:** The bug is subtle and specific. Models that haven't internalized the training loop logic will miss it or identify superficial issues.

---

### 3. `eval_metric_confound_captioning`

**Title:** Critique this captioning evaluation setup

**Why this reflects your real work:** You noticed caption length as a confound in your own NanoCaption results (9.9 vs 15.3 words). This is exactly the kind of evaluation hygiene issue that leaderboard-focused models ignore.

**Prompt:**
> I trained two captioning models. On 200 COCO val2017 images:
> - Model A: BLEU-4=0.257, CIDEr=0.729, METEOR=0.444, BERTScore=0.918. Avg caption length: 9.9 tokens.
> - Model B: BLEU-4=0.151, CIDEr=0.427, METEOR=0.422, BERTScore=0.901. Avg caption length: 15.3 tokens.
>
> My conclusion: Model A is strictly better. Is this conclusion valid? What are the confounds? What additional analysis would you run before claiming victory?

**What a weak model will do:** Confirm the conclusion. Maybe note "200 samples is small." Not engage with length as a structural confound.

**What a strong model will do:** Explain that BLEU-4 is heavily length-penalized via brevity penalty, and shorter outputs can score artificially high if they're precise enough. Note CIDEr also has length bias via TF-IDF weighting of shorter, rarer n-grams. Recommend: length-stratified evaluation, recall-oriented metrics, human evaluation of specificity at matched length, checking if Model A is systematically abstracting or hallucinating fewer details.

**Latent requirements:** Understands BLEU brevity penalty. Knows CIDEr's sensitivity to length and frequency. Can distinguish precision-oriented vs recall-oriented behavior.

**Hard failures:** Confirming the conclusion uncritically. Flagging only sample size. Not connecting metric properties to the length differential.

**Expected artifacts:** List of confounds with mechanism, suggested follow-up experiments.

**Why it's hard to game:** Requires knowing metric internals, not just "BLEU is a bad metric."

---

### 4. `router_design_media_type`

**Title:** Design a media type router for heterogeneous image inputs

**Why this reflects your real work:** You're building exactly this — an EfficientNet-B0 router classifying renders, anime/illustration, physical art, 2D digital, screenshots, documents — to gate downstream tool invocation.

**Prompt:**
> You are designing a lightweight image type classifier that will sit at the front of a CV pipeline. Its job is to classify incoming images into: renders/3D, anime/illustration, physical art, 2D digital graphics, screenshots, and document scans. The classifier gates which downstream CV tools are invoked (OCR, object detection, captioning, etc.). Design the system: architecture choice and why, training data strategy, ambiguous/boundary cases, failure modes, and what happens when the router is wrong.

**What a weak model will do:** "Use a CNN or ViT, train on ImageNet, fine-tune on a labeled dataset." No mention of class imbalance. No discussion of what mis-classification costs downstream. No mention of soft routing or confidence thresholds.

**What a strong model will do:** Justify a lightweight backbone (EfficientNet-B0 range), discuss data sourcing difficulty for physical art vs illustration boundary, propose confidence thresholding with fallback to multi-tool invocation for low-confidence cases, enumerate costly mis-classifications (e.g. routing a document as a photograph suppresses OCR), suggest calibration evaluation over raw accuracy.

**Latent requirements:** Understands the downstream cost asymmetry of different error types. Knows about calibration. Can reason about the boundary case distribution in practice.

**Hard failures:** Not discussing router error costs. Suggesting ImageNet fine-tuning without addressing domain gap. Not mentioning confidence or soft routing.

**Expected artifacts:** System design with architecture choice, data strategy, failure mode analysis.

**Why it's hard to game:** The interesting question isn't the classifier, it's the error cost analysis and the soft routing fallback. Boilerplate answers will ignore this entirely.

---

### 5. `nano_model_budget_allocation`

**Title:** Allocate a parameter budget across a vision-language model

**Why this reflects your real work:** You've been making exactly these tradeoffs — 15 layers vs more, GQA ratios, tied embeddings, projection vs resampler — all within a tight parameter budget.

**Prompt:**
> You are building a vision-language captioning model with a hard limit of 30M total parameters (excluding the frozen vision encoder). You have: a cross-modal projection, a decoder-only transformer, and an output head. The vision encoder outputs 256 tokens at dim 768. Your target vocabulary is 20k tokens. You want to maximize captioning quality on COCO-style short captions. How do you allocate the budget? Show your parameter arithmetic. Justify every tradeoff.

**What a weak model will do:** Give vague guidance ("use more layers if you have budget"). Not show parameter arithmetic. Not address tied embeddings. Not think about the token embedding table size.

**What a strong model will do:** Compute that a 20k vocab embedding table at dim D costs 20k×D params. Show that tying input/output embeddings halves this. Compute per-layer transformer costs. Show concrete allocations (e.g. projection 0.5M, 12-layer decoder 22M, embeddings 3M tied). Reason about depth vs width tradeoffs at this scale.

**Latent requirements:** Can do parameter arithmetic. Knows about tied embeddings. Understands scaling behavior of transformers at small sizes.

**Hard failures:** No arithmetic. Ignoring the embedding table cost. Not mentioning tied embeddings. Proposing 24+ layers on a 30M budget without checking the math.

**Expected artifacts:** Parameter budget table, explicit tradeoff justifications.

**Why it's hard to game:** Requires actual arithmetic. The model either does it or doesn't.

---

### 6. `t5_relpebias_failure_mode`

**Title:** Diagnose this T5 relative position bias anomaly

**Why this reflects your real work:** You caught a T5 relative position bias clamp overflow corrupting sequences ≥24 tokens. This is a very specific, real bug class.

**Prompt:**
> A T5-style model performs well on sequences up to 24 tokens but degrades sharply beyond that. Perplexity roughly doubles at length 25 and continues worsening. The architecture uses learned relative position biases with a fixed number of buckets. Training and validation loss were both healthy. The bug was introduced when the model was ported from a reference implementation. What are the candidate failure modes? Walk through how you would isolate the cause.

**What a weak model will do:** "Maybe the model wasn't trained on longer sequences." Suggest increasing max_seq_len. Not engage with the position bias mechanism at all.

**What a strong model will do:** Immediately identify the relative position bias bucket clamping as a strong candidate — if the clamp is misconfigured (e.g. max_distance wrong, or integer overflow in bucket computation), all positions ≥N map to the same bucket, collapsing positional information. Walk through how to isolate: visualize the bias matrix, check bucket assignments at length 25, diff against reference implementation. Also mention: off-by-one in attention masking, causal mask width mismatch, KV cache rollover bug.

**Latent requirements:** Knows the T5 relative position bias mechanism (buckets, log-spaced ranges, clamping). Can think about what "porting from a reference implementation" typically breaks.

**Hard failures:** Not mentioning position bias at all. Suggesting "train on longer sequences" as the fix. Not proposing a diagnostic path.

**Expected artifacts:** Ranked list of candidate causes with mechanism, diagnostic steps.

**Why it's hard to game:** Very specific mechanism. Models without real T5 internals knowledge will give generic "check your positional encodings" answers.

---

### 7. `cv_tool_invocation_chain_design`

**Title:** Design a tool-routing chain for a visual question answering query

**Why this reflects your real work:** Your entire framework is about routing queries to specialist CV tools and reasoning over structured outputs. This tests whether a model can actually design that chain.

**Prompt:**
> A user uploads an image and asks: "Is there a dog in this image, and if so, what breed is it and approximately how old is it?" You have access to: a general-purpose image captioner, YOLO object detection, a breed classifier (fine-grained, head-crop input), an age estimator (head-crop input), and PaddleOCR. Design the invocation chain. Show exactly what each tool receives and returns, how you handle missing detections, and how you compose the final answer. Do not use a VLM directly — you must route through tools.

**What a weak model will do:** "Run YOLO, then classify breed." Not handle the case where YOLO doesn't detect a dog. Not specify what crop the breed classifier needs. Not distinguish breed vs age tool inputs.

**What a strong model will do:** YOLO → dog detection check → if no detection, caption fallback to check if captioner mentions a dog → if detected, crop bounding box + padding → breed classifier on crop → age estimator on crop → compose structured answer with confidence. Handle: overlapping bounding boxes for multiple dogs, confidence thresholding on YOLO, graceful "cannot determine" when confidence is low.

**Latent requirements:** Understands tool input requirements (head crop ≠ full image). Can reason about fallback chains. Knows that OCR is irrelevant here (and shouldn't be invoked).

**Hard failures:** Invoking OCR. Not handling missing detection. Not specifying crop inputs. Proposing to just "ask the VLM."

**Expected artifacts:** Explicit invocation chain with inputs/outputs, failure handling, answer composition logic.

**Why it's hard to game:** Requires system-level thinking, not just "use YOLO." The crop input requirement and fallback handling are easy to miss.

---

### 8. `sentencepiece_tokenizer_domain_mismatch`

**Title:** Diagnose tokenizer coverage problems for a domain-specific corpus

**Why this reflects your real work:** You trained a domain-specific SentencePiece tokenizer on COCO and Flickr30k. This is a non-trivial choice that creates real failure modes.

**Prompt:**
> I trained a SentencePiece tokenizer with 20k vocab on COCO captions and Flickr30k. I now want to use it for captioning scientific diagrams and medical images. I'm seeing high UNK rates and degraded generation quality. Diagnose the problem. What specifically goes wrong, and what are my options? I do not want to retrain from scratch.

**What a weak model will do:** "Fine-tune the model on the new domain." Not engage with tokenizer-level failure. Not distinguish between tokenizer coverage and model distribution shift.

**What a strong model will do:** Explain that SentencePiece tokenizers trained on COCO (short, object-centric captions) will have poor coverage for scientific/medical terminology, causing: (1) high fertility (many subwords per domain term), (2) UNK tokens for truly out-of-vocabulary terms, (3) incoherent subword splits degrading generation. Options without full retrain: vocabulary extension with domain terms + embedding initialization from nearest neighbors, using a larger pre-trained tokenizer as a base, or training a separate domain tokenizer and composing at inference. Flag that changing the tokenizer mid-training is very painful — this is an architectural debt that compounds.

**Latent requirements:** Understands SentencePiece BPE behavior. Knows what COCO caption vocabulary looks like. Can distinguish tokenizer failure from model failure.

**Hard failures:** "Just fine-tune." Not engaging with the tokenizer level at all. Not mentioning fertility or subword fragmentation.

**Expected artifacts:** Diagnosis of failure mechanism, ranked options with tradeoffs.

**Why it's hard to game:** Requires knowing what COCO vocabulary actually looks like and what domain shift means at the tokenizer level specifically.

---

### 9. `gradient_flow_audit`

**Title:** Identify the gradient flow problem in this architecture

**Why this reflects your real work:** You validated the Linear projection replacement via smoke test for gradient bypass behavior. You clearly think about gradient flow as a first-class concern.

**Prompt:**
> Here is a simplified forward pass. Identify any gradient flow problems. Explain what each problem causes during training and how you would detect it.
>
> ```python
> class Model(nn.Module):
>     def forward(self, image, text_ids):
>         vis = self.encoder(image)                  # frozen, no_grad
>         proj = self.projection(vis)                 # Linear + LN
>         text_emb = self.embedding(text_ids)
>         text_emb = text_emb.detach()               # detached for "stability"
>         fused = self.cross_attn(text_emb, proj)
>         out = self.head(fused)
>         return out
> ```

**What a weak model will do:** "The encoder is frozen, which may limit performance." Not notice that `text_emb.detach()` breaks gradient flow to the embedding table. Not connect this to what actually fails.

**What a strong model will do:** (1) `text_emb.detach()` is catastrophic — the embedding table receives no gradient, so it never trains. The model will appear to train (loss decreases due to cross_attn and head updates) but the embedding table is frozen at initialization. Detection: check `embedding.weight.grad` is None after backward. (2) The frozen encoder is noted but correct if intentional. (3) Flag that projection's gradient is fine (it receives gradient from cross_attn), but cross_attn is receiving a detached key/query which means the attention pattern itself is shaped by random embeddings permanently.

**Latent requirements:** Understands PyTorch autograd graph. Knows that `.detach()` stops gradient propagation. Can reason about what trains and what doesn't.

**Hard failures:** Not identifying the detach as the critical bug. Treating the frozen encoder as the main problem.

**Expected artifacts:** Numbered bugs, mechanism explanation, detection method for each.

**Why it's hard to game:** The detach bug is easy to miss. Models that understand autograd will find it immediately; others will fixate on the frozen encoder.

---

### 10. `gqa_head_ratio_tradeoff`

**Title:** Justify a GQA query/key-value head ratio

**Why this reflects your real work:** You chose 10Q/2KV for NanoCaption's GQA. This is an opinionated choice with real tradeoffs.

**Prompt:**
> I'm using Grouped Query Attention with 10 query heads and 2 KV heads (5:1 ratio) in a 15-layer decoder at dim 640. Model is ~25M params, training on COCO/Flickr. Critique this configuration. Is 5:1 aggressive? What does it cost and what does it buy? Under what conditions would you change it?

**What a weak model will do:** "GQA reduces memory and speeds up inference. Your ratio looks reasonable." No quantification. No analysis of when the approximation hurts.

**What a strong model will do:** Compute KV cache size savings (5x reduction in KV memory). Note that at small model scale and short sequences, the KV cache is not actually the bottleneck, so GQA's primary benefit diminishes. Flag that with 2 KV heads, each KV head serves 5 query heads — at 15 layers and dim 640, per-head dim is 64. Ask whether the model has enough capacity to represent sufficient key/value diversity. Suggest that 4 KV heads (2.5:1) might be a more conservative choice at this scale. Note that GQA at 5:1 on a 25M model is unusual — it's a technique optimized for large inference contexts.

**Latent requirements:** Understands GQA mechanics and where its benefits actually apply. Can do per-head dimension arithmetic. Knows the difference between training efficiency and inference efficiency benefits.

**Hard failures:** Calling it "reasonable" without analysis. Not computing the per-head dimension. Not questioning whether the KV cache is actually a bottleneck at this scale.

**Expected artifacts:** Analysis with arithmetic, recommendation, conditions for revision.

**Why it's hard to game:** Requires knowing why GQA was invented (KV cache at inference scale) and whether that applies at 25M params/short sequences.

---

### 11. `bleu_gaming_detection`

**Title:** Detect metric gaming in these captioning results

**Why this reflects your real work:** BLEU/CIDEr sensitivity is something you've encountered in your own eval setup.

**Prompt:**
> A researcher reports these captioning results on COCO val: BLEU-4=0.38, CIDEr=1.2, but BERTScore=0.88. The reference average BERTScore for strong models is around 0.92. What might explain this pattern? Is this evidence of metric gaming? How would you investigate?

**What a weak model will do:** "The model might be overfitting to BLEU." No mechanism. No specific investigation path.

**What a strong model will do:** Identify that high BLEU-4 + high CIDEr + low BERTScore is a classic signal of n-gram optimized generation that lacks semantic coherence — the model may be repeating high-frequency COCO phrases (e.g. "a man riding a horse on a field") that match reference n-grams but produce generic, semantically flat outputs. BERTScore penalizes this because it evaluates semantic embedding similarity. Investigation: look at actual output samples, check output length distribution (BLEU brevity gaming), check vocabulary diversity (type-token ratio), compare against reference corpus top-k phrases.

**Latent requirements:** Understands the BLEU/BERTScore gap as a signal. Knows about COCO caption bias toward high-frequency phrases. Can propose concrete diagnostic steps.

**Hard failures:** "Retrain with BERTScore as a loss." Not identifying the mechanism. Not connecting n-gram optimization to semantic flatness.

**Expected artifacts:** Mechanism hypothesis, investigation steps, sample analysis recommendation.

---

### 12. `system_design_tool_orchestration`

**Title:** Design the tool invocation state machine for a CV reasoning agent

**Why this reflects your real work:** Your framework is fundamentally about orchestrating tool calls from LLM reasoning chains.

**Prompt:**
> Design the state machine for a CV reasoning agent that: (1) receives an image + natural language query, (2) decides which CV tools to invoke, (3) iterates if the first tool call doesn't resolve the query, (4) returns a structured answer. Tools available: captioner, YOLO, OCR, face detector, classifier. The agent must handle: tool unavailability, conflicting tool outputs, low-confidence results, and queries that require no tools at all.

**What a weak model will do:** Describe a linear pipeline. Not handle failure states. Not describe the state machine explicitly.

**What a strong model will do:** Define states: QUERY_ANALYSIS → TOOL_SELECT → TOOL_INVOKE → RESULT_EVAL → (ITERATE | COMPOSE). Handle: no-tool path (query answerable from caption alone), confidence threshold gating, conflict resolution (YOLO says "cat", captioner says "dog"), retry with different tool on low confidence, max_iterations guard. Note that the LLM reasoning step between RESULT_EVAL and TOOL_SELECT is the core intelligence layer.

**Latent requirements:** Can think in state machine terms. Understands that tool results need to be evaluated before deciding to compose or iterate. Can reason about failure modes in a production context.

**Hard failures:** Flat pipeline. Not handling low-confidence. Not handling tool unavailability. Not specifying the max_iterations guard.

**Expected artifacts:** State machine diagram or structured description, failure mode handling, concrete example trace.

---

### 13. `crf_transition_matrix_interpretation`

**Title:** Interpret what a trained CRF transition matrix is encoding

**Why this reflects your real work:** You've internalized the CRF-as-soft-grammar analogy and understand transition weights at a conceptual level.

**Prompt:**
> You have a trained CRF for BIO NER on a medical domain corpus. You extract the transition matrix. You notice: T[O→B-DRUG]=+4.2, T[B-DRUG→I-DRUG]=+3.8, T[I-DRUG→O]=+2.1, T[O→I-DRUG]=-8.7, T[B-DRUG→B-DRUG]=-6.1, T[I-DRUG→I-ORG]=-9.2. Interpret these values. Are any of them surprising? What do they tell you about the model's learned grammar?

**What a weak model will do:** "Positive values mean likely transitions, negative values mean unlikely transitions." Not engage with what specifically each value encodes or whether any are surprising.

**What a strong model will do:** Walk through each: O→B-DRUG positive (entity starts correctly), B→I continuation positive (valid extension), I→O positive (entity closes), O→I very negative (illegal BIO — inside without begin, model learned this hard constraint), B→B negative (one entity immediately starting another without O is unusual in medical text), I-DRUG→I-ORG very negative (entity type switching mid-span is illegal). Note that the O→I value and I-ORG transition are the most diagnostic — they show the model learned the hard BIO grammar. Note whether B→B being only -6.1 (not more negative) might indicate some contiguous entity annotations in training.

**Latent requirements:** Understands BIO constraint grammar. Can interpret CRF transition values as learned soft constraints. Can notice when a value is surprising relative to the grammar.

**Hard failures:** Just explaining positive vs negative. Not identifying O→I as the illegal transition. Not engaging with B→B as potentially surprising.

**Expected artifacts:** Interpretation of each transition, identification of surprises, inference about training data.

**Why it's hard to game:** Requires actually knowing BIO grammar and what violations look like. Models with shallow NLP exposure will give generic answers.

---

### 14. `ocr_pipeline_failure_mode_audit`

**Title:** Audit this OCR pipeline for production failure modes

**Why this reflects your real work:** PaddleOCR is in your toolkit. You care about operational robustness.

**Prompt:**
> Here is an OCR pipeline for extracting structured data from scanned invoices:
> ```
> 1. Resize image to 1024px longest edge
> 2. Run PaddleOCR
> 3. Filter results with confidence < 0.5
> 4. Join all text with spaces
> 5. Send to LLM: "Extract invoice number, date, total from: {text}"
> ```
> Find all failure modes. Prioritize by frequency and severity.

**What a weak model will do:** "Low confidence threshold might miss text." Generic list. Not think about the spatial layout being destroyed in step 4.

**What a strong model will do:** (1) Joining text with spaces destroys spatial layout — invoice data is spatial (columns, tables, line items), and flat text loses row/column relationships. This is the critical failure for structured extraction. (2) Fixed resize to 1024px loses context for dense small-text invoices at high DPI. (3) Confidence threshold of 0.5 is too aggressive for low-quality scans — may drop correct but degraded text. (4) No preprocessing for skew/rotation correction — rotated invoices degrade OCR significantly. (5) No handling for multi-page invoices. (6) The LLM prompt has no schema enforcement — output format is unspecified.

**Latent requirements:** Knows that invoice data is spatial. Understands that OCR text reading order is not guaranteed to match semantic structure. Can think about preprocessing needs.

**Hard failures:** Not identifying the spatial layout destruction as the critical issue. Treating the confidence threshold as the primary problem.

**Expected artifacts:** Prioritized failure mode list with mechanisms and suggested fixes.

---

### 15. `model_ablation_design`

**Title:** Design an ablation study for this VLM component

**Why this reflects your real work:** You've been thinking about what the VisualResampler vs Linear projection decision actually tests and what a proper validation looks like.

**Prompt:**
> I replaced a Perceiver-style VisualResampler (64 learned queries) with a Linear(768→640) + LayerNorm projection in a vision-language model. I want to run an ablation that cleanly attributes any performance difference to the projection change specifically. Design the ablation. What do you control for, what do you measure, and what would confound your results?

**What a weak model will do:** "Train both versions and compare BLEU." Not control for anything. Not mention parameter count differences. Not think about training dynamics confounds.

**What a strong model will do:** Control for: total parameter count (adjust decoder depth if needed to equate params), training steps, learning rate schedule, batch size, random seed. Measure: held-out BLEU-4/CIDEr, training curve shape (does one converge faster?), gradient norms through projection layer, KV attention entropy in cross-attention (does Linear lead to more/less uniform attention?). Confounds: Linear projection converges faster initially due to simpler optimization landscape — need sufficient training steps or the comparison isn't fair. Resampler needs learned queries to warm up. Consider training curves, not just final checkpoint.

**Latent requirements:** Understands confound control. Knows that Perceiver learned queries need warmup. Can think about what metrics actually attribute the change.

**Hard failures:** Not controlling for parameter count. Not mentioning training dynamics as a confound. Just "run both and compare."

**Expected artifacts:** Controlled experiment design, confound analysis, measurement plan.

---

### 16. `sparse_dense_caption_mode_token`

**Title:** Design the training objective for a dual-mode captioner

**Why this reflects your real work:** Your tokenizer has `<cap>` and `<dense>` mode tokens. This is a multi-task training design decision.

**Prompt:**
> I have a captioning model with two generation modes controlled by a mode token: `<cap>` for short COCO-style captions, `<dense>` for longer dense descriptions. The model is trained on a mix of COCO short captions and Flickr30k longer descriptions, routed by mode token. What can go wrong? What training dynamics should I monitor? How would I verify the mode token is actually doing work versus being ignored?

**What a weak model will do:** "Ensure your training mix is balanced." Not engage with mode token attribution or verification.

**What a strong model will do:** (1) Mode token interference — if the model learns that COCO images tend to have `<cap>` and Flickr images tend to have `<dense>`, it may partially route by image content rather than mode token, making the token partially redundant. (2) Verify via intervention: force `<dense>` on COCO images — does output length/detail increase? Force `<cap>` on Flickr images — does output shorten? (3) Monitor: output length distribution per mode, token attribution (attention weight to mode token across layers), train loss decomposed by mode. (4) Hard failure: mode token has low attention weight in cross-attention layers — it's being ignored.

**Latent requirements:** Understands multi-task mode token training dynamics. Can think about identifiability vs confoundment. Knows how to audit whether a conditioning signal is actually doing work.

**Hard failures:** Not proposing the intervention test. Not mentioning image-content correlation as a confound. "Make sure the loss is balanced" type answers.

**Expected artifacts:** Failure mode analysis, monitoring plan, verification experiments.

---

### 17. `lightweight_model_deployment_constraint`

**Title:** Identify all deployment constraints this model violates

**Why this reflects your real work:** You care about lightweight models, parameter budgets, and operational constraints, not just benchmark scores.

**Prompt:**
> A team built a captioning model for a mobile deployment target: 50ms inference latency, 200MB model size limit, no GPU. The model: 48-layer transformer decoder, 512 dim, 16 attention heads, BFloat16 weights, batch size 1, no KV cache, greedy decoding, outputs up to 128 tokens. Identify every constraint this model violates and estimate by how much.

**What a weak model will do:** "The model might be too large." No estimation. No analysis of which constraints interact.

**What a strong model will do:** (1) Parameter estimate: 48-layer, dim 512, 16 heads ≈ ~340M params → at BF16 = ~680MB → violates 200MB limit by ~3.4x. (2) Latency: 48 layers × 128 tokens, CPU, no KV cache = sequential attention recalculation → easily 5-20s on mobile CPU, violating 50ms by ~100-400x. (3) No KV cache at 128 tokens means O(n²) attention per step on CPU. (4) BF16 may not be supported on all mobile hardware (ARM CPUs often prefer FP16 or INT8). (5) Fix direction: quantize to INT8 (~170MB for 340M params), reduce to 6-12 layers, add KV cache, consider INT4.

**Latent requirements:** Can do rough parameter counting. Understands KV cache impact on autoregressive generation. Knows BF16 hardware support landscape.

**Hard failures:** Not estimating magnitude of violations. Treating "too large" as sufficient. Not addressing latency at depth.

**Expected artifacts:** Constraint violation analysis with estimates, fix directions.

---

### 18. `dataset_leakage_audit`

**Title:** Find the evaluation leakage in this benchmark setup

**Why this reflects your real work:** You ran your own evals on COCO val2017 with a model trained on COCO. This is a real risk you navigated.

**Prompt:**
> A researcher reports BLEU-4=0.31 on "COCO val" using a model trained on "COCO train". Their tokenizer was trained on the full COCO caption corpus. Their validation split was created by randomly sampling 10% of all COCO images. What are all the sources of leakage?

**What a weak model will do:** "The tokenizer might have seen val data." Correct but incomplete.

**What a strong model will do:** (1) Tokenizer trained on full corpus including val captions — vocabulary and BPE splits are directly informed by val caption text. (2) Random 10% split doesn't respect COCO's official val/train split — images may appear in both splits (COCO has official splits; ignoring them is not standard). (3) Multiple captions per image: if one caption for an image is in train and another is in val, the model has seen the image. (4) COCO images are not IID across splits — scene and object distributions are correlated by collection source. (5) The reported "COCO val" is not comparable to published results using the official split.

**Latent requirements:** Knows COCO data structure (5 captions per image, official splits). Understands tokenizer-level leakage. Can identify correlation leakage beyond direct data overlap.

**Hard failures:** Only identifying tokenizer leakage. Not mentioning COCO's official split structure. Not identifying the multi-caption per image issue.

**Expected artifacts:** Numbered leakage sources, severity ranking, fix for each.

---

### 19. `llm_vision_text_reasoning_separation`

**Title:** Critique this vision-language reasoning design

**Why this reflects your real work:** Your entire framework's thesis is that perception and reasoning should be separated, and that LLMs can reason over text descriptions rather than raw image features.

**Prompt:**
> I'm building a system where a non-vision LLM reasons about images. My current design: (1) run a dense captioner to produce a text description, (2) pass description to the LLM as context, (3) LLM answers queries about the image. A colleague says "this will fail for anything requiring spatial reasoning, counting, or fine-grained attribute comparison — just use a VLM." Evaluate this critique. Where is your colleague right? Where are they wrong? What are the actual failure modes of your design?

**What a weak model will do:** "Your colleague is right, you should use a VLM." Give up the design without analysis.

**What a strong model will do:** Agree that spatial reasoning (left/right, above/below), precise counting (>5-6 objects), and fine-grained visual comparison (two similar faces) are real failure modes — not because of LLM reasoning limits but because text descriptions lose spatial topology and precise attribute encoding. But: push back that VLMs are not obviously better here — they also struggle with counting and precise spatial reasoning, and they add opacity. Argue that the text-based approach is more auditable, cheaper, and correctable (you can improve the captioner independently). Propose: specialist tools for counting (YOLO), spatial relationship extraction as structured fields, not prose. The captioner doesn't have to do everything — it's one tool in a chain.

**Latent requirements:** Understands where the failure is actually located (captioner vs LLM reasoning). Knows VLM limitations. Can defend a design position while acknowledging its real weaknesses.

**Hard failures:** Agreeing with the colleague entirely. Not proposing specialist tool augmentation as the fix. Not noting VLM limits.

**Expected artifacts:** Structured critique, failure mode analysis, defense/revision of the design.

---

### 20. `ml_code_review_silent_bug`

**Title:** Find the silent correctness bug in this training loop

**Why this reflects your real work:** You caught real training bugs. This tests whether a model can read training code critically.

**Prompt:**
> Find any correctness bugs in this training loop. Silent bugs that affect training without crashing are worth more than crashes.
>
> ```python
> for epoch in range(num_epochs):
>     model.train()
>     for batch in train_loader:
>         images, captions = batch
>         optimizer.zero_grad()
>         loss = model(images, captions)
>         loss.backward()
>         optimizer.step()
>     
>     model.eval()
>     val_losses = []
>     for batch in val_loader:
>         images, captions = batch
>         loss = model(images, captions)
>         val_losses.append(loss.item())
>     print(f"Val loss: {sum(val_losses)/len(val_losses)}")
> ```

**What a weak model will do:** "You should use `torch.no_grad()` in validation." Correct but this is the obvious answer.

**What a strong model will do:** (1) Missing `torch.no_grad()` in validation (yes, obvious but critical — gradients accumulate, memory blows up). (2) Missing gradient clipping before `optimizer.step()` — not a crash but training instability in transformers. (3) `sum(val_losses)/len(val_losses)` computes unweighted average of batch losses — if batches have different sizes (last batch smaller), this is biased. (4) No learning rate scheduler step. (5) The model is called identically in train and eval but if it has different behavior in those modes (dropout etc.), the val loss includes dropout — it's higher than true val loss. Actually: `model.eval()` is set, but the val forward pass will use eval-mode behavior which is correct... but if dropout is in the model, train loss and val loss aren't comparable because train loss includes dropout noise. This is subtle. (6) No best-model checkpointing.

**Latent requirements:** Can read training loops critically. Knows about batch size bias in loss averaging. Understands the dropout noise effect on train vs val loss comparability.

**Hard failures:** Only finding `no_grad`. Not finding the loss averaging bias. Not identifying the dropout/train-eval comparability issue.

**Expected artifacts:** Numbered bugs, severity ranking, silent vs crashing classification.

---

## Top 8 Ranked (Most Diagnostic)

**1. `train_inference_mismatch_audit`** — Most diagnostic. The BOS/EOS bug is real, specific, and easy to miss. Tests whether the model actually reads training loops or just talks about them.

**2. `gradient_flow_audit`** — The `detach()` bug is a silent killer. Models with real autograd knowledge find it instantly; others fixate on the frozen encoder.

**3. `t5_relpebias_failure_mode`** — Extremely specific. You caught this in real life. No one answers this correctly without knowing T5 internals.

**4. `eval_metric_confound_captioning`** — Your own result set is the test case. Tests whether the model knows metric internals, not just "BLEU is bad."

**5. `cv_architecture_projection_vs_resampler`** — Counter-intuitive correct answer. Boilerplate defaults to Perceiver. The model needs real reasoning to get to "Linear wins here."

**6. `dataset_leakage_audit`** — COCO's multi-caption structure is the trap. Most models will stop at tokenizer leakage.

**7. `sparse_dense_caption_mode_token`** — Mode token attribution verification is subtle and practical. Tests operational thinking, not textbook knowledge.

**8. `router_design_media_type`** — Tests systems thinking. The interesting question is error cost asymmetry, which boilerplate ignores.

---

## Top 5 in Near-RoughBench-Ready Form

---

### Task 1: `train_inference_mismatch_audit`

**task.yaml**
```yaml
id: train_inference_mismatch_audit
title: "Find the training/inference mismatch bugs"
category: ml_engineering
difficulty: hard
artifact_type: structured_list
requires_execution: false
anti_autopilot: true
created: 2026-03-31
tags: [pytorch, training, inference, seq2seq, captioning, bugs]
```

**prompt.txt**
```
Here is a simplified training loop and inference function for a sequence-to-sequence image captioning model. Find every training/inference mismatch. For each mismatch, explain: (1) what the bug is, (2) what it causes during inference, (3) how severe it is (critical/moderate/minor), and (4) the fix.

```python
# Training
def forward(self, image, captions):
    vis_feat = self.encoder(image)          # (B, 256, 768)
    proj = self.proj(vis_feat)              # (B, 256, 640)
    tokens = self.tokenizer.encode(captions)
    input_ids = tokens[:, :-1]              # teacher forcing
    target_ids = tokens[:, 1:]
    logits = self.decoder(input_ids, proj)
    return F.cross_entropy(logits.view(-1, self.vocab_size), target_ids.view(-1))

# Inference
def generate(self, image, max_len=64):
    vis_feat = self.encoder(image)
    proj = self.proj(vis_feat)
    ids = [self.tokenizer.eos_id()]
    for _ in range(max_len):
        logits = self.decoder(torch.tensor([ids]), proj)
        next_id = logits[0, -1].argmax()
        if next_id == self.tokenizer.eos_id(): break
        ids.append(next_id.item())
    return self.tokenizer.decode(ids[1:])
```

List only real mismatches. Do not list style issues, missing features, or things that are different but correct (e.g. greedy vs beam). Rank by severity.
```

**rubric.yaml**
```yaml
criteria:
  bos_eos_mismatch:
    weight: 0.40
    description: "Identifies that inference starts with EOS, training starts with BOS (or whatever token starts the input_ids sequence). Model has never seen EOS as a generation-start token. Corrupts output distribution from step 1."
    levels:
      full: "Correctly identifies the BOS/EOS mismatch, explains the distribution corruption, classifies as critical."
      partial: "Identifies there is a token mismatch but doesn't fully explain the mechanism."
      fail: "Misses this entirely or misidentifies the issue."

  eval_mode_missing:
    weight: 0.30
    description: "Identifies that model.eval() / torch.no_grad() is not called at inference. Dropout and BatchNorm behave differently in training mode."
    levels:
      full: "Identifies eval mode missing, explains which components are affected (dropout, BN), classifies as moderate-critical depending on model."
      partial: "Mentions eval mode but vaguely."
      fail: "Misses it."

  severity_ranking:
    weight: 0.15
    description: "Correctly ranks BOS/EOS as most severe. Does not rank greedy-vs-beam as a mismatch."
    levels:
      full: "BOS/EOS ranked critical and first. No false positives in the mismatch list."
      partial: "Finds real bugs but ranking is wrong or has false positives."
      fail: "Wrong ranking or treats non-mismatches as mismatches."

  fix_quality:
    weight: 0.15
    description: "Provides correct, concrete fixes for each identified mismatch."
    levels:
      full: "Fix for BOS/EOS: initialize ids with BOS token. Fix for eval mode: call model.eval() and torch.no_grad() at start of generate()."
      partial: "Correct direction but incomplete."
      fail: "Wrong fixes."
```

**Scoring notes:**
- A model that only finds the eval mode issue and misses BOS/EOS gets at most ~35%.
- A model that raises greedy vs beam as a "mismatch" loses points — this is a false positive that indicates the model is pattern-matching on "differences" rather than reasoning about mismatches.
- The BOS/EOS bug is the critical signal. If a model finds it, explains the corruption, and provides the fix, it understands teacher forcing at a real level.

**Likely judge failure modes:**
- Giving partial credit to "the generation starts with the wrong token" without the model explaining *why* this corrupts the distribution (the decoder's learned first-step distribution is conditioned on BOS; giving it EOS puts it entirely out of distribution).
- Penalizing models for noting greedy vs beam is a "philosophical choice not a bug" — this is correct and should be credited.
- Over-crediting vague answers like "the tokenizer handling might differ."

**Execution-backed check:**
Run the code as-is and observe that the first generated token is nearly always EOS (triggering immediate termination) or garbage, confirming the BOS/EOS mismatch is critical. Can be verified with a toy model in < 20 lines.

---

### Task 2: `gradient_flow_audit`

**task.yaml**
```yaml
id: gradient_flow_audit
title: "Identify the gradient flow problem in this model"
category: ml_engineering
difficulty: hard
artifact_type: structured_list
requires_execution: false
anti_autopilot: true
created: 2026-03-31
tags: [pytorch, autograd, gradient_flow, training, embeddings]
```

**prompt.txt**
```
Here is a model forward pass. Identify all gradient flow problems. For each problem: (1) describe what fails to train or trains incorrectly, (2) explain how you would detect it during training, (3) classify as silent (training continues but is wrong) or crash (training fails).

```python
class Model(nn.Module):
    def forward(self, image, text_ids):
        vis = self.encoder(image)                  # frozen pretrained encoder
        proj = self.projection(vis)                 # Linear + LayerNorm
        text_emb = self.embedding(text_ids)
        text_emb = text_emb.detach()               # "for stability"
        fused = self.cross_attn(text_emb, proj)
        out = self.head(fused)
        return out
```

Focus on correctness bugs, not style. The frozen encoder is intentional — do not flag it unless you believe it causes a specific secondary problem in this code. Silent bugs are more important than crashes.
```

**rubric.yaml**
```yaml
criteria:
  detach_bug:
    weight: 0.55
    description: "Identifies that text_emb.detach() stops gradient propagation to the embedding table. The embedding table never trains. This is silent — loss will still decrease because cross_attn and head train, but embeddings stay at initialization."
    levels:
      full: "Identifies detach as catastrophic, explains embedding table receives no gradient, explains why loss still decreases (masking the bug), proposes detection (check embedding.weight.grad is None after backward)."
      partial: "Identifies detach as a problem but doesn't explain why loss still decreases or provide detection method."
      fail: "Misses the detach bug or calls it benign."

  cross_attn_consequence:
    weight: 0.20
    description: "Notes that cross_attn receives a detached, randomly-initialized text_emb as query — attention patterns are shaped by random embeddings permanently, degrading cross-modal fusion."
    levels:
      full: "Explicitly notes this consequence."
      partial: "Vaguely notes cross_attn is affected."
      fail: "Doesn't connect detach to cross_attn quality."

  frozen_encoder_analysis:
    weight: 0.10
    description: "Handles the frozen encoder correctly — notes it's intentional (per instructions) OR correctly identifies any secondary issue it causes specifically in this code."
    levels:
      full: "Either correctly treats it as intentional or notes a specific secondary issue."
      partial: "Flags it as a problem without specific justification beyond 'frozen=bad'."
      fail: "Focuses on frozen encoder as the primary issue while missing detach."

  silence_classification:
    weight: 0.15
    description: "Correctly classifies the detach bug as silent (training continues, loss decreases, but embeddings don't train)."
    levels:
      full: "Explicitly calls it silent and explains why."
      partial: "Identifies it as a bug but doesn't classify silent vs crash."
      fail: "Calls it a crash."
```

**Scoring notes:**
- A model that focuses on the frozen encoder as the primary issue while missing the detach bug is demonstrating exactly the failure mode this task is designed to catch — it found the visible thing and missed the invisible thing.
- The comment "for stability" is a red herring. Strong models should recognize this as rationalization for a bug, not a valid technique.
- Detection method quality matters: `embedding.weight.grad is None` after a backward pass is the precise detection method.

**Likely judge failure modes:**
- Crediting "detach can cause training issues" without the mechanism (embedding table never trains).
- Not penalizing models that focus on the frozen encoder without mentioning detach.

---

### Task 3: `t5_relpebias_failure_mode`

**task.yaml**
```yaml
id: t5_relpebias_failure_mode
title: "Diagnose the T5 relative position bias length degradation"
category: ml_engineering
difficulty: very_hard
artifact_type: diagnostic_report
requires_execution: false
anti_autopilot: true
created: 2026-03-31
tags: [t5, position_encoding, relative_position_bias, debugging, sequence_length]
```

**prompt.txt**
```
A T5-style decoder performs well on sequences up to 24 tokens but shows sharp perplexity degradation at length 25 and beyond. The model was ported from a reference implementation. Training and validation loss on short sequences were healthy. The architecture uses learned relative position biases with a fixed number of distance buckets.

1. List the most likely candidate failure modes, ordered by prior probability.
2. For your top candidate, explain the mechanism in detail.
3. Describe exactly how you would isolate and confirm the cause.
4. What is the fix?

Do not say "train on longer sequences." The model was trained on sequences up to 128 tokens. The issue is in the ported code, not the training data.
```

**rubric.yaml**
```yaml
criteria:
  identifies_relpebias_primary:
    weight: 0.45
    description: "Identifies T5 relative position bias bucket clamping as the primary candidate. Specifically: if the max_distance or num_buckets parameter was ported incorrectly, all positions ≥N map to the same bucket, collapsing positional diversity at the threshold."
    levels:
      full: "Names T5 RPE clamping as primary, explains bucket overflow mechanism, explains why this causes sharp threshold degradation (not gradual)."
      partial: "Mentions RPE but doesn't explain the clamping/overflow mechanism."
      fail: "Doesn't identify RPE as primary candidate."

  mechanism_detail:
    weight: 0.20
    description: "Explains the T5 RPE bucket assignment: log-spaced buckets, clamping behavior, and why a porting error would manifest at a specific length threshold."
    levels:
      full: "Correct description of log-spaced buckets, correct explanation of how a wrong clamp value causes the threshold behavior."
      partial: "Some correct detail but incomplete."
      fail: "Wrong mechanism or generic 'positional encoding bug' answer."

  diagnostic_path:
    weight: 0.20
    description: "Proposes a concrete diagnostic path: visualize the bias matrix at length 24 vs 25, check bucket assignments for positions 24 and 25, diff the porting code against reference."
    levels:
      full: "Proposes at least two concrete diagnostic steps, including bias matrix visualization or bucket assignment check."
      partial: "Suggests checking the position encoding code generally."
      fail: "No concrete diagnostic path."

  other_candidates:
    weight: 0.10
    description: "Lists plausible secondary candidates: attention mask width mismatch, causal mask bug at boundary, KV cache rollover."
    levels:
      full: "Lists 2+ specific secondary candidates with mechanisms."
      partial: "Lists 1 secondary candidate."
      fail: "No secondary candidates or lists generic/implausible issues."

  fix:
    weight: 0.05
    description: "States the fix: correct the max_distance/num_buckets parameter in the RPE bucket assignment function to match the reference implementation."
    levels:
      full: "Correct and specific fix."
      partial: "Correct direction."
      fail: "Wrong or missing fix."
```

**Scoring notes:**
- This task has a very high floor — most models will get some partial credit on diagnostic path. The discriminator is whether the model immediately identifies RPE clamping as the mechanism.
- "Check your positional encoding" is a 10% answer. "The T5 RPE bucket assignment clamps distances; if the clamp threshold is N=24, all positions ≥25 are assigned to the same bucket, collapsing positional structure" is a 90% answer.
- Treat any answer that mentions "train on longer sequences" as a hard failure regardless of other content.

**Likely judge failure modes:**
- Crediting generic "position encoding bug" answers that don't name the mechanism.
- Not penalizing "train on longer sequences" answers (the prompt explicitly excludes this).

---

### Task 4: `eval_metric_confound_captioning`

**task.yaml**
```yaml
id: eval_metric_confound_captioning
title: "Identify confounds in captioning evaluation results"
category: ml_evaluation
difficulty: medium_hard
artifact_type: analysis_with_experiments
requires_execution: false
anti_autopilot: false
created: 2026-03-31
tags: [bleu, cider, meteor, bertscore, captioning, evaluation, length_bias]
```

**prompt.txt**
```
I trained two image captioning models on COCO. Evaluated on 200 COCO val2017 images:

Model A: BLEU-4=0.257, CIDEr=0.729, METEOR=0.444, BERTScore=0.918. Avg caption length: 9.9 tokens.
Model B: BLEU-4=0.151, CIDEr=0.427, METEOR=0.422, BERTScore=0.901. Avg caption length: 15.3 tokens.

My conclusion: "Model A is strictly better across all metrics."

1. Is this conclusion valid? What are the confounds?
2. For each metric, explain exactly how the length differential affects the score.
3. What additional analysis would you run before claiming victory?
4. Under what conditions would Model B actually be the better model despite lower scores?
```

**rubric.yaml**
```yaml
criteria:
  bleu_brevity_penalty:
    weight: 0.25
    description: "Explains BLEU brevity penalty: outputs shorter than references are penalized, but Model A (9.9 tokens) may be closer to average reference length than Model B (15.3 tokens), potentially avoiding or reducing the brevity penalty. Or: shorter outputs have higher precision if correct."
    levels:
      full: "Correct mechanistic explanation of how 9.9 vs 15.3 token length affects BLEU-4 score via brevity penalty and precision computation."
      partial: "Notes length affects BLEU but doesn't explain the mechanism."
      fail: "Doesn't engage with length-BLEU connection."

  cider_length_bias:
    weight: 0.20
    description: "Explains CIDEr TF-IDF weighting: shorter, more specific outputs may have higher TF-IDF weights for key terms. Shorter captions may also score higher on consensus-based retrieval."
    levels:
      full: "Correct explanation of CIDEr's TF-IDF weighting and how shorter, more precise outputs can score higher."
      partial: "Notes CIDEr has length sensitivity but doesn't explain the mechanism."
      fail: "Doesn't engage with CIDEr specifically."

  bertscore_interpretation:
    weight: 0.20
    description: "Notes that BERTScore gap (0.918 vs 0.901) is small but meaningful, and that BERTScore is less length-sensitive because it uses soft token matching via embeddings — making it a more honest comparison."
    levels:
      full: "Identifies BERTScore as the most length-independent metric and uses it to hedge the conclusion."
      partial: "Notes BERTScore exists but doesn't interpret its length-independence."
      fail: "Treats all metrics equally."

  follow_up_experiments:
    weight: 0.20
    description: "Proposes concrete follow-up: length-stratified eval (compare models at matched output lengths), recall-oriented captioning (can Model B describe details Model A omits?), sample inspection for specificity."
    levels:
      full: "Proposes 2+ concrete experiments, at least one addressing length stratification."
      partial: "Proposes experiments but they are generic or wouldn't isolate the length confound."
      fail: "No concrete experiments."

  model_b_defense:
    weight: 0.15
    description: "Articulates conditions where Model B is better: tasks requiring detail, dense captioning mode, downstream retrieval where recall matters more than precision."
    levels:
      full: "Specific conditions named with reasoning."
      partial: "Vague 'Model B might be better in some contexts.'"
      fail: "Doesn't engage."
```

**Scoring notes:**
- The conclusion is not valid, but a model that says "the conclusion is wrong" without mechanism gets low marks.
- The BERTScore being the least length-confounded metric is the key insight that makes this task hard.
- Sample size (200 images) is a valid secondary concern but should not be the primary answer.

---

### Task 5: `cv_architecture_projection_vs_resampler`

**task.yaml**
```yaml
id: cv_architecture_projection_vs_resampler
title: "Justify a cross-modal projection choice: Linear vs Perceiver"
category: ml_architecture
difficulty: hard
artifact_type: structured_comparison_with_recommendation
requires_execution: false
anti_autopilot: true
created: 2026-03-31
tags: [vision_language, cross_attention, perceiver, projection, parameter_budget, gradient_flow]
```

**prompt.txt**
```
You have a frozen vision encoder outputting 256 tokens at dimension 768. Your decoder expects cross-attention keys/values at dimension 640. You are choosing between two projection designs:

Option A: VisualResampler — Perceiver-style, 64 learned queries, cross-attention to encoder tokens, output is 64 tokens at dim 640. (~1.43M params)
Option B: Linear(768→640) + LayerNorm, applied per-token. Output is 256 tokens at dim 640. (~0.49M params)

Your constraints:
- Total model budget: ~30M params (excluding frozen encoder)
- Training budget: tight (50k steps, batch size 16)
- Task: short image captions (COCO-style, ~10-15 tokens)
- Per-layer cross-attention in the decoder (not just top-layer)

Compare them. Make a concrete recommendation. Show parameter arithmetic. Do not recommend "it depends" without a final answer.
```

**rubric.yaml**
```yaml
criteria:
  parameter_arithmetic:
    weight: 0.20
    description: "Produces correct or close-to-correct parameter counts for both options. Option A: ~1.43M (64 queries × 640 dim + attention weights). Option B: ~0.49M (768×640 + 640 bias)."
    levels:
      full: "Both estimates within ~20% of correct values."
      partial: "One estimate correct, one wrong or missing."
      fail: "No parameter arithmetic."

  bottleneck_analysis:
    weight: 0.25
    description: "Identifies that Option A compresses 256 tokens to 64 — a 4x information bottleneck. For per-layer cross-attention, this means every decoder layer sees only 64 context vectors. Option B preserves all 256."
    levels:
      full: "Explicitly names the 4x bottleneck, connects it to per-layer cross-attention quality."
      partial: "Notes compression but doesn't quantify or connect to per-layer CA."
      fail: "Doesn't identify the bottleneck."

  training_dynamics:
    weight: 0.25
    description: "Notes that Perceiver learned queries start random and require warmup. With tight training budget, this is a meaningful cost. Linear projection has a flatter optimization landscape."
    levels:
      full: "Explicitly addresses learned query warmup cost and tight training budget interaction."
      partial: "Notes training dynamics matter but is vague."
      fail: "Doesn't address training dynamics."

  recommendation:
    weight: 0.20
    description: "Recommends Option B (Linear). The correct answer given the constraints: tight budget, per-layer CA, short captions where 64 tokens might suffice but the bottleneck risk isn't worth it."
    levels:
      full: "Recommends Option B with stated reasoning tied to the specific constraints."
      partial: "Recommends Option B but reasoning is weak or generic."
      fail: "Recommends Option A or refuses to commit."

  no_false_precision:
    weight: 0.10
    description: "Does not claim that Option A is universally better for expressiveness without addressing the specific constraints. Anti-autopilot signal."
    levels:
      full: "Does not default to 'more expressive = better.'"
      fail: "Says 'Option A is generally preferred for its expressiveness' without engaging the constraints."
```

**Scoring notes:**
- A model that recommends Option A because "it's more expressive and can learn to focus on relevant regions" without engaging the parameter budget, training dynamics, or per-layer CA constraint is demonstrating exactly the shallow autopilot this task is designed to catch.
- The correct answer is non-obvious. The task earns its place in the suite by having a counter-intuitive answer that requires constraint-aware reasoning.

**Likely judge failure modes:**
- Giving partial credit to Option A recommendations that "acknowledge both sides." The task specifies concrete constraints; Option B is the correct answer under those constraints.
- Over-crediting vague "it depends on your data" answers.

---

## Gaps In The Current Suite

The three existing seed tasks cover: operational Python engineering (`swe_scraper`), literary knowledge accuracy (`literary_booker`), and NLP modeling judgment (`nlp_bio_crf`). Together they leave substantial gaps relative to your actual work:

**1. No ML training loop critique.** Your most diagnostic failure mode — silent training bugs from mismatches, detached tensors, wrong token initialization — is entirely absent. You caught real bugs in real code. The suite doesn't test this at all.

**2. No evaluation hygiene.** You think carefully about metric confounds, length bias, and what benchmarks actually measure. The current tasks test knowledge and design, but not the ability to audit evaluation claims critically. This is a core skill for your work and completely absent.

**3. No architecture tradeoff reasoning under constraint.** The NLP task asks about modeling choices, but doesn't ask the model to reason about parameter arithmetic, training budget, and specific architectural decisions. This is the most diagnostic test of whether a model can actually be useful in your design loop.

**4. No system-level design.** Your framework is fundamentally about routing, tool orchestration, and error propagation across components. None of the existing tasks pressure system-level thinking — they're all within a single model or task.

**5. No gradient flow or PyTorch internals.** You validated the projection change with a smoke test checking gradient bypass. This kind of reasoning about what trains and what doesn't is a recurring concern in your work and not touched in the current suite.

**6. The existing tasks are knowledge-oriented; yours is judgment-oriented.** `literary_booker` tests recall. `nlp_bio_crf` tests whether the model avoids the BERT autopilot. `swe_scraper` tests engineering inference. Your real work is much more about: "is this tradeoff analysis correct," "is this evaluation honest," "is this architecture choice justified given these constraints." The suite needs more judgment-under-constraint tasks, not more knowledge-recall tasks.