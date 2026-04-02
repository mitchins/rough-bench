Expected synthesis:

- Confirmed: 18,000 rows, 212 conflicts, late-arriving shards, empty token arrays, 14% throughput improvement, tag-length mismatches
- Unclear: tokenizer drift is only a suspicion
- Next checks: compare shard-level duplicates, inspect token/tag mismatch rows, and validate the disk-backed merge path on a small held-out slice

The answer should not present tokenizer drift as a settled root cause.
