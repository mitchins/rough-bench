# Tool Plan

1. Search the repository for the search command, cache layer, and path-handling code with a narrow query first.
2. Inspect the matching files and the nearest call sites to confirm whether the empty-result bug comes from indexing, stale cache state, or path normalization.
3. Diagnose the root cause from the file contents and logs, and write down the evidence before changing anything.
4. Patch only the minimal file or files that implement the broken lookup path.
5. Verify the fix with a targeted test and one CLI smoke run.
6. If search returns nothing, broaden the query to adjacent symbols and inspect neighboring modules before patching.
7. If the evidence conflicts, stop and compare the competing code paths rather than guessing.
8. If the patch does not apply cleanly, re-open the current file state and adjust the change to the smallest safe diff.
9. If verification fails, revert the patch, inspect the failing output, and retry with the narrowest correction.
