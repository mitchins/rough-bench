`rewrite_dataset.py` uses a spill-bucket rewrite pipeline:

- `load_from_disk(...).to_iterable_dataset()` for the first pass
- per-key hashing into temp JSONL buckets
- per-bucket dedupe with the exact tie-break
- heap-based final merge into a new dataset saved to disk

The intent is to stay bounded under hidden memory caps instead of assuming the full dataset can be loaded eagerly.
