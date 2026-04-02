**8 Proposed RoughBench Tasks – Language / Pragmatic & Cultural Inference Layer**

These are built exactly to the standard you set in the seed tasks and Claude’s ML suite: messy real-world loads, latent constraints, zero hand-holding, easy for weak models to sound plausible while being operationally tone-deaf. They stress-test whether an LLM actually *feels* social context the way a competent human (or a production multilingual agent) would, rather than pattern-matching on “polite Japanese = ですます”.

I anchored them in the same philosophy as your existing suite: the judge will have secret rubrics checking for things like correct keigo level given *implied* hierarchy, Korean speech-level switching that survives real conversational drift, and Latin that isn’t just “correct grammar” but carries the exact cultural weight the context demands. No clean-room translation tasks. These are the linguistic equivalents of “build a resumable scraper” — the model has to infer unspoken rules or it fails in revealing ways.

### 1. lang_japanese_keigo_hierarchy_inference
**id**: `lang_japanese_keigo_hierarchy_inference`  
**title**: Infer and apply correct keigo level from subtle social cues (no explicit roles given)  
**why this reflects your real work**: Your NLP toolkit already uses CRFs/BIO for structured extraction; this is the pragmatic layer on top — the model must infer latent social graph the same way your CV router infers tool chain from ambiguous queries. You hate autopilot “just be polite”.  
**prompt**:  
A Japanese colleague you have never met before emails you in casual business Japanese: “今週の会議資料、共有いただけますか？ 急ぎでお願いします。” (no honorifics on your name, uses いただけますか but drops keigo on their own action). Draft a reply that is professionally correct. Do not explain your reasoning.  
**what a weak model will do**: Default to ですます throughout, maybe throw in one ございます for “extra politeness”.  
**what a strong model will do**: Recognise the colleague is senior (casual self-reference + 急ぎでお願い + no honorific on recipient) → use sonkeigo for their request, kenjougo for own actions, and teineigo baseline. Output the exact reply an experienced Japanese salaryman would send.  
**latent requirements**: Understands uchi/soto, honne/tatemae bleed, and that keigo choice signals perceived hierarchy even when not stated.  
**hard failures**: Uniform politeness level; explaining the choice in the output.  
**expected artifacts**: Single clean email reply only.  
**why it is hard to game**: Most models default to “safe polite” and miss the hierarchy signal hidden in the colleague’s own casualness.

### 2. lang_korean_politeness_level_switch
**id**: `lang_korean_politeness_level_switch`  
**title**: Detect and continue correct speech-level drift in Korean chat  
**prompt**:  
Continue this KakaoTalk conversation naturally. The other person has just switched from 해요체 to 반말 mid-sentence after you mentioned you’re the same age:  
[full chat log provided with age hint buried naturally]  
Output only the next 2–3 messages from you.  
**what a weak model will do**: Stays in 해요체 or flips to 반말 too aggressively.  
**what a strong model will do**: Matches the exact switch moment, uses appropriate 반말 contractions, and adds the tiny softening particles that Koreans actually use when age-matching for the first time.  
**latent requirements**: Real-time politeness calculus (age, relationship length, context, power differential).  
**hard failures**: Ignoring the age cue or over-correcting to jondaemal.

### 3. lang_japanese_implied_uchi_soto
**id**: `lang_japanese_implied_uchi_soto`  
**title**: Spot and correct uchi/soto violation in a group chat excerpt  
**prompt**:  
Here is a Slack thread in Japanese between your company’s Tokyo team and a client. One of your Japanese colleagues wrote: “弊社の田中がそう言ってましたよ〜” (referring to a client-side person). That sentence is wrong. Rewrite the entire thread with the correct version and explain nothing.  
**what a strong model will do**: Immediately changes it to 田中さんが (client is soto) and adjusts the whole tone accordingly.

### 4. lang_latin_motto_heraldic_weight
**id**: `lang_latin_motto_heraldic_weight`  
**title**: “Weird Latin shit” – craft a motto that carries the exact classical cultural payload  
**prompt**:  
A client wants a Latin motto for their new venture capital fund that invests in “contrarian, high-conviction bets against consensus.” They hate anything that sounds like “carpe diem” boilerplate. Give them the final motto only (no translation, no explanation). It must be grammatically flawless classical Latin and carry the precise vibe they want.  
**latent requirements**: Knows the cultural flavour of different Latin registers (Ciceronian vs Silver Age vs medieval), allusion density, and how a single word can shift the entire social signalling.  
**hard failures**: “Audentes fortuna iuvat” or any modern motivational Latin. Strong model will produce something like “Contra opinionem communem, audacia vincit” with the exact classical flavour.

### 5. lang_korean_banmal_gradation
**id**: `lang_korean_banmal_gradation`  
**title**: Navigate partial banmal in a mixed-age Korean workplace  
**prompt**:  
You are the youngest person in a Korean game studio. The lead designer (10 years older) just said to you in the company Kakao group: “야, 이 버그 좀 봐봐” (full banmal). Reply in the exact politeness level a Korean 20-something would actually use in that situation. Output only your reply.  
**what a strong model will do**: Uses “half-banmal” (반말 + softening 요 at sentence end) — the real move Koreans actually make.

### 6. lang_japanese_internet_tatemae_honne
**id**: `lang_japanese_internet_tatemae_honne`  
**title**: Detect tatemae vs honne in Japanese Twitter/X drama  
**prompt**:  
Here is a Japanese Twitter thread that looks polite on the surface. One reply is actually a savage indirect diss. Quote the exact sentence that is the diss and rewrite it in plain honne (no explanation).  
**latent requirements**: Knows the specific indirect patterns (e.g. “さすがですね〜” used sarcastically, ですます + ね with falling tone implication, etc.).

### 7. lang_latin_legal_maxim_misuse
**id**: `lang_latin_legal_maxim_misuse`  
**title**: Catch and correct Latin legal maxim used out of context  
**prompt**:  
A junior lawyer in your firm wrote in an email: “We should invoke the doctrine of caveat emptor here.” The situation is actually about fiduciary duty in a trust, not a simple sale. Rewrite the sentence using the correct Latin maxim (or none at all) that a real contracts partner would use. Output only the corrected sentence.  
**strong model**: Replaces with “uberrima fides” or drops Latin entirely and uses plain English — because real lawyers know when Latin signals incompetence.

### 8. lang_multilingual_code_switch_implication
**id**: `lang_multilingual_code_switch_implication`  
**title**: Infer social signalling from Japanese–English code-switch density  
**prompt**:  
A Japanese engineer in your Slack just wrote: “このPR、LGTMだけど、edge caseで死ぬかも。reviewお願いします〜”  
Reply in the exact register he is signalling (he is using light English loanwords + 〜). Output only your reply.  
**latent requirements**: Code-switch density is a status/age/nerd-culture signal in Japanese tech circles.

---

**Top 3 Most Diagnostic (my ranking)**  
1. `lang_japanese_keigo_hierarchy_inference` – purest “latent constraint” test; exactly parallel to your scraper task (model must infer persistence/politeness without being told).  
2. `lang_korean_politeness_level_switch` – forces real-time pragmatic reasoning; weak models collapse to one level.  
3. `lang_latin_motto_heraldic_weight` – the “weird Latin shit” you asked for; tests taste and cultural payload, not just grammar.

These slots straight into your existing rubric style. The judge can auto-score with secret ground-truth replies written by native speakers who actually live the culture (same way you’ll have secret SQLite choice for the scraper task).

Want me to write the full `task.yaml` + `prompt.txt` + `rubric.yaml` for the top 3 in the exact format you used for the ML tasks? Or expand to 20 total language tasks? Just say the word. This is the missing pragmatic dimension your benchmark needed.