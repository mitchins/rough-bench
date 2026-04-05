# Methodology

## Meta Categories

The current POC groups tasks into six top-level axes:

1. Build & Systems
2. ML & NLP Engineering
3. Search & Analytics
4. Language & Localization
5. Planning & Product
6. Judgment & Creative

These are data-driven groupings derived from each task's `domain`.

## Category Quality

Category charts use normalized quality, not raw demerits:

```text
quality = 100 * (1 - category_demerits / category_max_demerits)
```

Higher is better.

## Radar Modes

The model radar supports two views:

- `Absolute quality`: the raw normalized category quality used by the benchmark
- `Relative to best clean`: each category is scaled so the best clean recorded run in that category is `100`

The absolute view is the benchmark truth. The relative view is a shape view.
It is useful when one category is structurally harder than the others and would
otherwise flatten every model's radar.

## Headline Eligibility

Production leaderboards exclude runs that are not headline-ready. A run must be:

- complete
- have zero failed tasks

Partial and failed runs remain in the exported data for debugging and historical
inspection, but they do not appear in the main overall or category leaderboards.

## Efficiency Leaderboard

The efficiency table is gated. A run only appears if it is:

- complete
- untainted
- has token usage recorded
- meets the configured quality floor

The current quality floor is shown in the generated data file and defaults to `60`.

## Token Composition

The overview also shows token composition for substantial complete runs. The
colors are:

- `Prompt`: grey
- `Reasoning`: purple
- `Answer`: green

When a provider does not expose reasoning-token telemetry, completion is shown
as an unsplit segment instead of being guessed.

## Quantization Policy

Local weight format is treated pragmatically rather than dogmatically:

- models smaller than `8B` should use original or FP16 weights where feasible
- models `8B` and larger may use trusted `Q8` or `NVFP8` variants

The reason for the split is practical. Smaller models tend to degrade more
under quantization, while `8B+` models often show negligible benchmark-relevant
drift at high-fidelity quantization levels. Quantized runs should still note
their format in subject metadata, but they are not treated as a major caveat by
default unless there is evidence of material benchmark impact.

## Awards

The overview page includes fun auto-calculated badges. These are recomputed on
every docs-data rebuild from the current saved runs.

Awards currently use clean headline-eligible runs by default:

- `Most Efficient`: fewest total tokens above the efficiency quality floor
- `Noisiest`: most total tokens among clean runs
- `Underdog`: best overall quality per billion parameters
- `Fatcat`: worst overall quality per billion parameters
- `All-Rounder`: best harmonic mean across the six category scores
- `Specialist`: biggest gap between best and worst category
- `Nitpicker`: highest weighted total of rare rubric signals passed
- `The Linguist`: best aggregate quality across the counted language and localization task set
- `The Sentry`: best aggregate quality across the explicit Home Assistant-style household oversight set: occupancy, ambiguous security triage, tool-call notification triage, and aquarium monitoring

Parameter-based awards rely on explicit `params_billion` metadata in the subject
config when available.

## Taint

Runs that hit the output cap are marked as tainted. They can still be useful,
but they should not be treated as clean headline measurements.
