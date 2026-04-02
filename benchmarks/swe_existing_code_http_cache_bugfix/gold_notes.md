# Gold Notes

This task is intentionally messy in a realistic way:

- two concrete correctness bugs are explicitly reported
- one serious security problem is latent in the shared-cache context
- one performance or memory-growth issue is latent in the unused retention model

The response should fix the asked bugs first, then show enough engineering judgment
to flag the adjacent serious risks without getting lost in redesign.

The two required correctness fixes are:

1. Cache key must stop collapsing distinct queries into the same path-only key.
2. Expired entries must not be returned as if they were still fresh.

The two side findings are:

1. A shared process cache should not blindly cache authenticated or cookie-scoped
   GET responses under a user-agnostic key.
2. Entries need some cleanup or bounded-retention story; otherwise expired entries
   accumulate forever and `max_entries` is a lie.

A strong answer preserves the module shape, makes a bounded patch, and is explicit
about what it is not solving, such as in-flight request coalescing or persistent
cache storage.
