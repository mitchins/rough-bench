Diagnosis

The failure is not just "bad NER." Your augmenter is over-trusting sentence-initial capitalization as evidence that a token is a character name. `Limp` is capitalized only because it starts the sentence, but the pipeline is treating it like a replaceable entity span. Literary prose makes this worse because title-like phrases such as `the First Enchantress` can also look entity-like even when a naive replacer has not identified the true character span correctly.

Fix

Make the replacement step position-aware. Do not replace a sentence-initial capitalized token just because it is capitalized. Only replace a span if it is supported elsewhere as a recurring character mention, for example mid-sentence mentions, a character lexicon, or a syntax-aware check that confirms it is functioning as a name span rather than an adjective or descriptive fragment. Apply the same mapping consistently to both the source passage and the summary so you do not create source-summary drift.

Validation

Build a small regression set with sentence-initial traps like `Limp as rags`, title phrases like `the First Enchantress`, and paired source-summary examples. After augmentation, run sanity checks on span boundaries and do spot checks or POS or dependency-based validation on changed examples before admitting them into training.
