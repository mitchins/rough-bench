Visible development fixture guidance:

- derive rows from a canonical CoNLL-style corpus such as `conll2003`
- save the fixture locally with `datasets.save_to_disk`
- keep the visible fixture small enough for local smoke tests

Hidden evaluation fixture guidance:

- use larger replicated and perturbed tiers so the dataset no longer fits comfortably in RAM
- include duplicate-heavy workloads with skewed key distributions
- include late-arriving better rows so one-pass "keep first" logic fails
- include uneven sentence sizes so bucket balance is imperfect

Suggested hidden tiers:

- small: validates correctness quickly
- medium: exposes greedy list materialization
- large: exposes repeated global passes, OOMs, and pathological runtime
