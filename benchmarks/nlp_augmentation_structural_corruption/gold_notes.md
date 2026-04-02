The load-bearing failure is structural, not just "NER quality."

Strong answers should say some version of:

- `Limp` is being misread as a name because sentence-initial capitalization is leaking into the entity signal.
- Literary prose makes this worse because titles and epithets such as `the First Enchantress` are much easier to mis-handle than standard newswire names.
- The fix should be position-aware or syntax-aware:
  - skip or heavily validate sentence-initial single-token replacements
  - only replace spans that are supported elsewhere in the document or lexicon as actual recurring character mentions
  - optionally confirm with POS, noun-phrase, or dependency information
- The source and summary should share the same replacement logic and mapping.
- Validation should include regression examples that specifically cover sentence starts, titles, and summary consistency.

Weak answers usually fail by:

- saying `use a better NER model`
- suggesting regex tweaks without naming the capitalization trigger
- ignoring the summary side
- treating literary prose like ordinary newswire text
