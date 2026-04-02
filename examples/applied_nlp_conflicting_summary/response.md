## Confirmed Facts

- The ingest job processed 18,000 rows and found 212 label conflicts.
- Late-arriving shards contributed duplicates, and one shard had empty token arrays.
- Throughput improved 14% after switching to disk-backed merging.
- The logs confirm tag-length mismatches.

## Unclear / Contested

- Tokenizer drift is a suspicion from one reviewer, not a settled diagnosis.

## Conservative Synthesis

The evidence supports a noisy ingest and dedupe problem with bounded-disk processing helping throughput, but it does not settle tokenizer drift as the root cause.

## Next Checks

- Compare duplicate rows by shard and arrival order.
- Inspect the tag-length mismatch rows directly.
- Re-run the merge on a small held-out slice to confirm the throughput improvement stays stable.
