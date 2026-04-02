# Overall Result

Control overall activation is `600 / 10000 = 6.0%`.

Variant overall activation is `770 / 10000 = 7.7%`.

# Mix-Adjusted Result

Using the control segment mix as weights:

- New mobile: `50% * 3.8% = 1.9%`
- Returning mobile: `20% * 7.8% = 1.56%`
- New desktop: `20% * 5.8% = 1.16%`
- Returning desktop: `10% * 11.8% = 1.18%`

So the variant under the control segment mix is:

`1.9% + 1.56% + 1.16% + 1.18% = 5.8% = 580 / 10000 = 0.058`

That is worse than the control's `6.0%`.

# Diagnosis

Every segment is down in the variant even though the raw aggregate is up. This is a traffic mix / composition effect, essentially a Simpson's paradox style result: the variant received far more high-converting returning desktop traffic, which inflates the top-line number. Under an intended 50/50 random split, that segment skew is suspicious and suggests an assignment, bucketing, or targeting problem rather than a real product improvement.

# Ship Decision

Do not ship from this evidence. The apparent aggregate win is not a real per-segment improvement; once you control for mix, the variant is worse.

# Next Checks

1. Check assignment and bucketing logs to verify the split was actually random and not biased by channel, device, or returning-user status.
2. Audit targeting or eligibility rules to see why returning desktop users were overrepresented in the variant.
3. Rerun the experiment with a stratified or otherwise balanced split, and compare fixed-mix results before making a rollout decision.
