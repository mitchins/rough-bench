The load-bearing insight is not merely `boundary errors happen`.

Strong answers should say some version of:

- token-level F1 is inflated because O dominates the label distribution
- seqeval span-F1 requires exact span boundaries, so one wrong boundary token can zero out an otherwise almost-correct entity
- the 0.89 vs 0.61 gap means the model is probably locating entities roughly near the right region but failing exact start or end boundaries often enough to crush span-F1
- the right next step is to compute specific diagnostics:
  - span precision vs span recall
  - illegal BIO transitions
  - truncation vs extension breakdown
  - exact-match vs partial-overlap rate
- literary multi-token names, titles, and epithets are a realistic source of these boundary errors

Weak answers usually fail by:

- calling the model good because token-F1 is high
- talking about boundary errors without naming O-token inflation
- recommending CRFs or more data before diagnosing the gap
- saying only `inspect the errors`
