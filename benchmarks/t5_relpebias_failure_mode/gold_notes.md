# Gold Notes

This task is intentionally narrow.

The main discriminator is not whether the answer says "positional bug." It is
whether the answer names the T5 relative-position bucket function as the primary
suspect and explains the threshold mechanically.

The right answer shape is:

- the failure is content-independent, so it is positional rather than semantic
- the bucket function or clamp logic was likely ported incorrectly
- beyond a threshold, positions collapse into the same bucket or an invalid
  bucket path
- that produces identical or corrupted relative position bias for longer spans
- the first direct check is to print bucket ids for a short range directly from
  the function, not to start with a full forward pass

Reward answers that know T5 bucket structure:

- 32 buckets
- first half exact-ish / second half logarithmic
- max distance 128

Do not require the answer to assert that the canonical exact/log split itself is
at 24 or 25. Under standard T5 it is not. The important thing is that the model
recognizes a discrete bucket-function error rather than generic transformer
instability.

Punish:

- training-length advice
- generic "check positional encoding" language
- no direct bucket inspection
- vague fix language
