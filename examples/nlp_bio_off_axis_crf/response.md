I would start with a compact `CNN-CRF` or `BiLSTM-CRF` pipeline instead of defaulting to a transformer, because the dataset is messy and domain-specific.

Key modeling choices:

- Normalize inconsistent whitespace, punctuation, and casing before feature extraction.
- Treat annotation noise and tokenization drift as first-class problems during data cleaning.
- Use character CNN features plus token features to produce emission scores.
- Let the linear-chain CRF handle transition scores so invalid BIO label transitions are discouraged directly.
- Keep the label inventory task-specific instead of forcing it into a CoNLL-style NER mold.

Evaluation:

- Report span-level entity F1, not only token accuracy.
- Inspect boundary mistakes separately from label confusions.
- Compare exact span match with a looser overlap-oriented error breakdown for ambiguous annotations.

This keeps the modeling aligned with messy BIO data while respecting the CRF constraint and avoiding transformer autopilot.
