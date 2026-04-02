I would treat this as an external-memory rewrite problem rather than a normal in-memory `datasets` transform.

The implementation reads the saved dataset with `load_from_disk`, switches to an iterable path, validates and normalizes rows on the way in, then hashes each dedupe key into spill buckets under a temp directory. Each bucket is reloaded independently, deduped with the exact `(score, updated_at, example_id)` tie-break, sorted locally, and written back out as a sorted JSONL partition. A bounded heap merge then emits the final globally ordered records into a new Hugging Face dataset written to `output_dir`.

That keeps the input immutable, avoids full-corpus materialization, and makes the expensive mutation steps happen against bounded partitions instead of the whole dataset at once.
