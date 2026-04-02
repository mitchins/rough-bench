## Candidate Failure Modes

1. **Relative position bucket function bug in the ported implementation**. This is the highest-probability cause because the failure is content-independent and appears as a hard threshold at length 25. In a T5-style model, that strongly suggests a discrete error in bucket assignment or clamping rather than a learned semantic weakness.
2. **Boundary bug in the causal or attention mask**. An off-by-one mask width error could also create a hard threshold, though it is less T5-specific than the bucket-function hypothesis.
3. **Indexing or cache rollover bug at the first length that exceeds an internal boundary**. Possible, but lower prior than the relative-position path given the architecture details.

## Top Candidate

The most likely cause is a bug in the **relative position bias bucket function**.

T5 does not use absolute position embeddings here. It maps relative distances into a fixed set of buckets, with 32 buckets total and a standard split between exact buckets at short ranges and logarithmically spaced buckets at larger distances up to max distance 128. If the ported bucket function has an off-by-one, wrong boundary constant, incorrect clamp, or wrong log-bucket computation, positions beyond some threshold can collapse into the same bucket or an invalid bucket path.

That explains the symptom shape. This is not smooth degradation. It is a **discrete threshold** because the model is fine until it hits the first distance that exercises the broken part of the bucket assignment. After that, multiple distinct positions receive the same or corrupted bias, so the model effectively loses positional information beyond that point.

## Isolation Plan

1. **Direct check without a full forward pass**: call the bucket function directly and print bucket ids for relative positions `0..30`, especially around `24` and `25`. If the ids flatten, jump, or clamp unexpectedly there, the hypothesis is confirmed immediately.
2. Compare the ported bucket ids against the reference implementation for the same positions.
3. Visualize the relative position bias matrix for sequence lengths `24` and `25`. The first bad length should show a discrete structural change rather than a gradual drift.
4. As a secondary check, inspect the causal mask at lengths `24` and `25` to rule out an off-by-one masking bug.

## Fix

Diff the ported bucket assignment function against the reference implementation and correct the bucket logic to match it exactly.

The likely concrete fixes are:
- correct an off-by-one in the boundary between exact and logarithmic buckets
- correct the clamp or max-distance handling
- correct the log-bucket computation so positions beyond the boundary do not collapse to the same bucket or to an invalid index

In practice I would first make the bucket ids for `0..30` identical to the reference implementation, then rerun the `24` vs `25` bias-matrix check before doing a full model forward pass.
