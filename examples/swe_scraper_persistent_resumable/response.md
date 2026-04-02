# Persistent and resumable scraper

I would structure this as a small Python service rather than a one-shot script.

- Persist crawl state in `sqlite` so restarts are safe.
- Keep a checkpoint table with the last successful cursor or page token for each source.
- Make requests resumable with retries, exponential backoff, explicit timeout values, and rate limiting per host.
- Write scraped records idempotently with a unique constraint plus an upsert path so reruns do not duplicate rows.
- Emit structured logging for fetch attempts, parse failures, checkpoint advances, and retry exhaustion.

The core loop is:

1. Read the next pending unit of work from sqlite.
2. Fetch with timeout and retries.
3. Parse and normalize.
4. Write idempotently.
5. Commit the checkpoint only after the write succeeds.

This gives durable state, resumable progress, and lightweight local persistence without requiring a heavier database.
