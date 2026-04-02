# Bugs fixed

- The cache key no longer collapses every `GET` on the same path into one entry. It now canonicalizes query parameters before building the key.
- Expired entries are no longer returned as fresh data. The patch evicts expired entries and refetches.

# Patch summary

The patched module keeps the same `HTTPCache`, `_cache_key`, and `get_json` API. Query handling is normalized with `parse_qsl` and `urlencode` so equivalent query strings map to the same key. `get_json` now removes stale entries before refetching, only caches successful unauthenticated `GET` responses, and performs opportunistic cleanup so expired entries and over-capacity growth do not accumulate forever.

# Deferred serious issues

- I did not implement in-flight request coalescing, so hot keys can still stampede upstream under concurrency.
- The important security risk here is shared-cache leakage for authenticated requests. I mitigated that by bypassing caching when `Authorization` or `Cookie` is present, but a richer system might instead partition by an explicit user context.
