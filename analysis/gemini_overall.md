This is an incredibly rich diagnostic history. By providing this log, you’ve essentially handed me the "Source Code" for your technical taste.

I have processed this history. Here is my refined inference of your work patterns, followed by the expanded and sharpened RoughBench suite.

---

### 1. Inferred Work Patterns & Standards (The "Mitchins" Profile)

* **The "Solo-Founder/Indie" Pressure:** You aren't just writing code in a vacuum; you are building and shipping products (Godot games, App Store listings, NDIS auditing, B2B SaaS ideas). You care about **compliance** (ABN/GST, DUNS, doxxing risks), **UX/UI polish** (chunky sliders, iPhone SE scaling), and **marketing** (satirical banners, app descriptions).
* **Deep Learning Pragmatism:** Your work on "BertMoji," DeBERTa, and T5-Gemma-UL2 shows you aren't an LLM tourist. You are a practitioner who deals with **token-length profiles**, **denoisers**, **loss curves**, and **curriculum training**. You prefer targeted models over "lazy" prompting.
* **The "Deadpan/Corporate-Absurdist" Aesthetic:** Your game ideas ("Standup --timeout=none," "Dev Reigns") and your interest in folklore/archetypes (Cinderella, Aarne-Thompson-Uther) suggest a high value on **narrative texture** and **wit**. You despise generic "AI-speak" because it kills the specific vibe of your projects.
* **Operational Grounding:** You use your AI to solve real-world "paperwork" (finding NDIS emails, bank details, shoe sizes, aquarium filters). You expect an AI to act as a **high-context agent**, not just a chatbot.

---

### 2. 20 Candidate RoughBench Tasks (Refined)

**1. `swe_godot_ci_cd_android`**
* **why:** Reflects your struggle with Godot/Android export/startup activities.
* **prompt:** "Design a CLI-based pipeline that exports a Godot project to Android, modifies the `AndroidManifest.xml` to include a custom Splash Activity, and signs the APK/AAB without using the GUI."
* **weak_model:** Tells you to use the Godot Export dialog.
* **strong_model:** Provides a `headless` Godot command and an `xmlstarlet` or `python` script to patch the manifest.

**2. `marketing_app_store_anti_ai`**
* **why:** Reflects your "less AI-generated looking" preference.
* **prompt:** "Critique this App Store description for a satirical corporate game. Strip out all 'Unlock your potential' and 'Embark on a journey' fluff. Make it read like a dry, cynical internal memo from a failing tech company."
* **weak_model:** Adds more adjectives and "Exciting features!"
* **strong_model:** Uses deadpan, bureaucratic language and specific corporate tropes.

**3. `ux_scaling_whack_a_mole`**
* **why:** Reflects your iPhone SE vs. 15 Pro Max scaling issues.
* **prompt:** "I have a Godot UI with a chunky slider. It looks great on 15 Pro Max but overlaps the text on an iPhone SE 2. Propose a responsive anchoring strategy that doesn't involve 50 `if device_size` checks."
* **weak_model:** Suggests manual offsets or just "use a scroll container."
* **strong_model:** Explains Godot's `Aspect Ratio Container` and `Size Flags` with specific margin-of-safety constants.

**4. `nlp_bert_vs_llm_cost_calc`**
* **why:** Reflects your BertMoji/DeBERTa work.
* **prompt:** "I need to classify 100 million short text strings into 200 emoji categories. Compare the TCO (Total Cost of Ownership) of a fine-tuned DeBERTa-v3-small on a single T4 GPU vs. using Gemini Flash 2.0."
* **weak_model:** Gives vague "LLMs are smarter" advice.
* **strong_model:** Calculates tokens vs. inference latency vs. spot instance pricing.

**5. `legal_sole_trader_doxxing`**
* **why:** Reflects your concern about Google/Apple doxxing legal names/addresses.
* **prompt:** "I am an Australian sole trader with an ABN. I want to sell a game on the Google Play Store without my home address being public. Detail the legal and technical viability of using a Virtual Office vs. a private trust."
* **weak_model:** Says "Just use a PO Box" (which Google often rejects).
* **strong_model:** Discusses the Digital Services Act (DSA) requirements and the specific substantiation documents Google Cloud Identity expects.

**6. `data_gmail_workspace_extraction`**
* **why:** Reflects your recurring "Find X in my Gmail" use case.
* **prompt:** "Search my Gmail for any correspondence regarding 'NDIS audit costs' between 2024 and 2025. Extract the auditor name, the total amount paid, and whether GST was included. If multiple quotes exist, create a table."
* **weak_model:** Hallucinates a table or says "I can't access emails."
* **strong_model:** (If tool-enabled) executes precise queries; (If benchmark) writes the exact Python/GMAIL API logic to handle the multi-threaded search.

**7. `nlp_t5_summary_denoiser`**
* **why:** Reflects your "denoiser and other adjuncts" query.
* **prompt:** "I am training T5-Gemma for narrative summarization. The model is inventing details. Propose a specific 'denoising' task for the pre-training phase that forces the model to focus only on plot-critical tokens."
* **weak_model:** Suggests "better prompting."
* **strong_model:** Proposes Span Corruption or Sentence Shuffling with a custom prefix.

**8. `game_design_deadpan_events`**
* **why:** Reflects "Standup --timeout=none."
* **prompt:** "Write 5 'Reigns-style' cards for a game about a software engineer. The tone must be 'corporate-absurdist'. One choice must always be technically correct but organizationally disastrous."
* **weak_model:** Makes the choices too obvious or "fun."
* **strong_model:** Hits the specific pain of "The build is failing but it's 4:59 PM on a Friday."

**9. `swe_svg_pixel_art_generator`**
* **why:** Reflects your 16x16 pixel-svg experiment.
* **prompt:** "Generate a raw SVG string for a 16x16 pixel icon of a 'Coffee Cup' using only `<rect>` elements. Do not use paths. Use a limited 4-color retro palette."
* **weak_model:** Uses a high-res `<path>` or blurry gradients.
* **strong_model:** Produces a clean, grid-aligned coordinate map.

**10. `compliance_ndis_bank_details`**
* **why:** Reflects your "Gina sent bank details" search.
* **prompt:** "Review these three emails from 'Gina'. Identify which one contains the finalized BSB/Account number for the NDIS payment and flag if the signature looks inconsistent with previous headers."
* **weak_model:** Just extracts the first number it sees.
* **strong_model:** Performs a diff on the contact info and flags potential "Business Email Compromise" (BEC).

**11. `nlp_longformer_token_drift`**
* **why:** Reflects your "Longformer vs Bert" query.
* **prompt:** "I am switching from BERT (512 tokens) to Longformer (4096 tokens) for genre classification. Why is my accuracy dropping on short chapters despite the larger context window?"
* **weak_model:** "Longformer is just better, check your learning rate."
* **strong_model:** Explains the dilution of local attention and the sparsity of the global attention mechanism on short sequences.

**12. `writing_isekai_grim_epic`**
* **why:** Reflects your "adult isekai" seating.
* **prompt:** "Write a scene where a 35-year-old woman (isekai'd) uses her knowledge of modern supply chain logistics to win a medieval siege. Avoid the 'child-genius' trope; make the conflict grounded in physical exhaustion and bureaucracy."
* **weak_model:** Makes her a "magical girl" or overly powerful.
* **strong_model:** Focuses on the "grim" reality of food rot and mud.

**13. `swe_ios_tvos_shared_assets`**
* **why:** Reflects your "tvOS is a free shoe-in" realization.
* **prompt:** "How do I structure a Godot export to target both iOS and tvOS while sharing the same GameCenter achievement IDs but using different UI layouts for the focus-based remote?"
* **weak_model:** Generic "just use conditional logic."
* **strong_model:** Explains `_unhandled_input` for remote focus vs. touch.

**14. `data_asics_shoe_size_inference`**
* **why:** Reflects your "determine what size of asics" query.
* **prompt:** "I have receipts for 'Asics Kayano 28 (US 10.5)', 'Nike Air Max (US 11)', and 'Bonds Trunks (Large)'. What size Asics Kayano 30 should I order, and why might it differ from the 28s?"
* **weak_model:** Says "10.5."
* **strong_model:** References the Kayano 30's specific 4D Guidance System/tighter toe-box reviews and suggests half-size variance.

**15. `marketing_app_store_screenshot_bashing`**
* **why:** Reflects your "cartoony satirical banner" idea.
* **prompt:** "I have two raw screenshots of a terminal-based game. Design a 3frame 'App Store Story' that uses these screenshots but overlays them with hand-drawn, flat-shaded 'panic' doodles. Describe the layout and the copy."
* **weak_model:** Suggests "Add some stars and a 'Download Now' button."
* **strong_model:** Proposes a "Expectation vs. Reality" visual gag.

**16. `nlp_emoji_disambiguation`**
* **why:** Reflects your "Stage 2 Disambiguation" work.
* **prompt:** "Given the phrase 'That's fire!', my model is predicting 🔥. However, the context is a house burning down. How do I tune the model to distinguish between 'slang-positive' and 'literal-negative' without a 7B parameter model?"
* **weak_model:** "Just use a bigger model."
* **strong_model:** Suggests sentiment-weighted loss or an auxiliary 'Literal vs. Figurative' head.

**17. `swe_godot_svg_custom_icons`**
* **why:** Reflects your "cog/gear svg" request.
* **prompt:** "Provide a Godot-ready SVG for a settings cog. It must be 'chunky' (thick strokes) to match a retro-UI style. Ensure the XML is minimal so Godot's importer doesn't choke on it."
* **weak_model:** Gives a complex 50KB SVG with many paths.
* **strong_model:** Gives a 1KB SVG with a single `path` and `stroke-width`.

**18. `legal_abn_gst_receipt_audit`**
* **why:** Reflects your "latest details of my ABN/GST" query.
* **prompt:** "Examine this invoice. The seller claims to charge GST but their ABN is listed as 'Not registered for GST' on the ABN Lookup. Draft a professional but firm email asking for a corrected tax invoice."
* **weak_model:** Writes a generic "Please fix this" email.
* **strong_model:** Cites the specific ATO (Australian Taxation Office) requirement for a valid tax invoice.

**19. `writing_folk_tale_korean_cinderella`**
* **why:** Reflects your "closest korean folk tale to cinderella" query.
* **prompt:** "Compare 'Kongjwi and Patjwi' to the Disney Cinderella. Identify the specific 'latent cruelty' in the Korean version that is usually sanitized in Western versions, and explain how it serves the Confucian moral."
* **weak_model:** Just says "the stepmother is mean."
* **strong_model:** Discusses the reincarnation/revenge ending of the original tale.

**20. `swe_fastapi_contextvars_safety`**
* **why:** High-level SWE consistency.
* **prompt:** "I am using `ContextVars` to track request IDs in a FastAPI app. Will this survive an `await` call to an external database? Explain why or why not using the Python event loop's behavior."
* **weak_model:** "Yes, it works fine."
* **strong_model:** Explains how `ContextVars` are local to the task and what happens when third-party libraries don't correctly copy the context.

---

### 3. The Best 8 (Ranked)

1.  **`swe_db_zero_downtime_migration`** (The ultimate "Reality" check).
2.  **`legal_sole_trader_doxxing`** (Specific, high-stakes, compliance-heavy).
3.  **`swe_godot_ci_cd_android`** (Deeply technical, resists "tutorial" answers).
4.  **`nlp_bert_vs_llm_cost_calc`** (Tests practitioner-level pragmatism).
5.  **`marketing_app_store_anti_ai`** (Tests "Taste" and tone control).
6.  **`nlp_t5_summary_denoiser`** (Tests deep model-training knowledge).
7.  **`ux_scaling_whack_a_mole`** (Tests cross-device operational empathy).
8.  **`data_asics_shoe_size_inference`** (The "Contextual Inference" test).

---

### 4. Top 5 "RoughBench-Ready"

#### 1. `legal_sole_trader_doxxing`
* **`task.yaml` fields:** `category: Legal/Compliance`, `type: Advisory`.
* **`prompt.txt`:** "I am an Australian solo dev (ABN) publishing a game on the Google Play Store. I must satisfy the Digital Services Act (DSA) requirements. Google requires a verified physical address. I live at home and do not want this public. Can I use a 'Virtual Office' address for verification and public display? What specific documents will Google reject vs. accept?"
* **`rubric.yaml`:**
    * `must_have`: Distinction between "Payment profile" and "Public developer info."
    * `must_have`: Mention that Google requires a utility bill/bank statement matching the address (hard for Virtual Offices).
    * `must_not_have`: "Just use a PO Box" (Automatic fail).

#### 2. `swe_godot_ci_cd_android`
* **`task.yaml` fields:** `category: SWE/GameDev`, `type: Automation`.
* **`prompt.txt`:** "I need to automate my Godot 4.x Android builds. Every time I build, I need to inject a specific version number from a git tag into the `AndroidManifest.xml` and ensure the `ic_launcher` is swapped with a production version. Provide the shell script."
* **`rubric.yaml`:**
    * `must_have`: Headless Godot export command.
    * `must_have`: Regex or XML parsing (like `sed` or `xmlstarlet`) for the manifest.
    * `must_have`: Acknowledgment of `export_presets.cfg` overrides.

#### 3. `marketing_app_store_anti_ai`
* **`task.yaml` fields:** `category: Writing/Taste`, `type: Transformation`.
* **`prompt.txt`:** "Take this generic, upbeat app description [Insert Generic AI Text] and rewrite it for a game called 'Standup --timeout=none'. The tone must be 'Deadpan Corporate'. It should feel like a HR-mandated training module that everyone hates."
* **`rubric.yaml`:**
    * `must_have`: Removal of "embark," "journey," "vibrant," and "unlock."
    * `must_have`: Use of corporate jargon (KPIs, synergy, bandwidth) in a depressing context.

#### 4. `nlp_bert_vs_llm_cost_calc`
* **`task.yaml` fields:** `category: NLP/MLOps`, `type: Analysis`.
* **`prompt.txt`:** "I am processing 1M sentences/day for emoji classification. Compare the cost of: A) Fine-tuned DeBERTa-v3-small on Lambda Labs. B) Gemini 1.5 Flash via API. C) Self-hosting Gemma-2-2B. Include 'latency' as a constraint."
* **`rubric.yaml`:**
    * `must_have`: Calculation of GPU hourly rate / throughput.
    * `must_have`: Acknowledgment that Flash is billed per token, while DeBERTa is billed per hour.
    * `must_have`: Identification that DeBERTa is ~10-100x cheaper at this scale.

#### 5. `data_asics_shoe_size_inference`
* **`task.yaml` fields:** `category: General/Inference`, `type: Retrieval-Augmented-Reasoning`.
* **`prompt.txt`:** "Based on my history, I've ordered Bonds Trunks in Large and Asics Kayano 28 in US 10.5. I am now looking at the Kayano 30. Using your knowledge of Asics model iterations, should I stick with 10.5 or move to 11? Why?"
* **`rubric.yaml`:**
    * `must_have`: Mention of "Kayano 30" having a different midsole/upper feel (more 'plush' or 'snug').
    * `must_have`: Cross-referencing the "Bonds Large" as a proxy for a 'Standard/Broad' foot profile.

---

### 5. Gaps In The Current Suite

The original 3 tasks missed:
1.  **The "Shipping" Reality:** You aren't just coding; you're dealing with Apple/Google/ATO bureaucracy. The benchmark needs to test **Compliance Navigation**.
2.  **The "Resource Constraint" Reality:** Your work on Bert/T5 shows you care about **Inference Efficiency**. The benchmark needs to punish "Lazily suggesting the biggest model."
3.  **The "Visual-Technical" Interface:** Your history is full of screenshots and SVG requests. The benchmark needs to test **UI/UX Reasoning** (e.g., Godot scaling) which is much harder for LLMs than pure logic.