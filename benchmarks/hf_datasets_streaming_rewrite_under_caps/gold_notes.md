The canonical fixture should be derived from a well-known Hugging Face dataset rather than a bespoke synthetic schema from scratch. A CoNLL-style sentence corpus is a good anchor because:

- the row shape is familiar
- token and tag arrays create visible validation work
- the dataset is small enough to understand but easy to scale synthetically

Recommended fixture shape:

- start from sentence rows derived from `conll2003`
- replicate and perturb them to create hidden tiers
- inject duplicate groups with different `score`, `updated_at`, and `example_id`
- ensure some winning rows arrive late so a greedy first-hit dedupe is wrong
- include invalid rows with token-tag length mismatches and empty token arrays

What this task is trying to catch:

- models that reach for `dataset.sort()` or pandas because the API feels convenient
- models that say "streaming" in prose but still materialize the full dataset
- models that can filter but fall apart once dedupe plus mutation plus final ordering are required
- models that produce code with correct logic on toy data but pathological scaling under hidden caps

The right pattern is usually:

1. stream or iterate from disk
2. rewrite to spill partitions
3. dedupe within bounded partitions
4. merge the partition outputs into a final globally ordered dataset
