# Gold Notes

This task is about analytical interpretation, not analytics vocabulary.

The arithmetic:

- Control total activations = `200 + 160 + 120 + 120 = 600`
- Control total sessions = `10000`
- Control overall = `600 / 10000 = 6.0%`

- Variant total activations = `95 + 117 + 145 + 413 = 770`
- Variant total sessions = `10000`
- Variant overall = `770 / 10000 = 7.7%`

That raw aggregate looks better, but every segment is worse:

- New mobile: `4.0% -> 3.8%`
- Returning mobile: `8.0% -> 7.8%`
- New desktop: `6.0% -> 5.8%`
- Returning desktop: `12.0% -> 11.8%`

Using the control segment mix as weights:

- `0.50 * 3.8% = 1.9%`
- `0.20 * 7.8% = 1.56%`
- `0.20 * 5.8% = 1.16%`
- `0.10 * 11.8% = 1.18%`

Mix-adjusted variant = `5.8%`

So the apparent win is a composition artifact / mix shift / Simpson's paradox style result, not a real per-segment improvement.

A strong answer should:

- compute both raw overall rates correctly
- compute the `5.8%` fixed-mix variant rate correctly
- note that every segment regressed
- say do not ship from this evidence
- flag that the wildly different segment mix is suspicious under an intended 50/50 random split
- suggest concrete follow-ups such as checking assignment/bucketing logs and rerunning with a balanced or stratified split
