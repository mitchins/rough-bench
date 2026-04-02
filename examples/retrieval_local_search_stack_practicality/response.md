## Option Review
- A. Browser wrappers around hosted AI web UIs are fragile. Auth expiry, cookie churn, and backend changes make them unreliable for high-value use.
- B. OpenWebUI with local-only models is robust from an auth perspective, but answer quality and retrieval depth may be weaker depending on the local models.
- C. A small internal web app with local retrieval plus an API-backed answer model is the best balance: one stable multi-user surface, controllable retrieval, and fewer moving pieces than browser automation.
- D. A personal desktop note-search tool is fine for one machine, but it is not a real multi-user or multi-client answer stack.

## Ranking
1. Option C
2. Option B
3. Option D
4. Option A

## Recommended Path
I would choose C. It is the most practical operating point: local retrieval keeps data handling under your control, the internal web app serves multiple users or clients, and the API-backed answer model avoids the quality ceiling of local-only setups. The tradeoff is API dependency, but that is a cleaner failure surface than auth-fragile browser wrappers.

## Failure Modes To Watch
- API churn or model endpoint outages
- maintenance burden in the retrieval pipeline
- auth expiry if anyone tries to smuggle browser-wrapper tricks back into the stack
- quality regressions if the local retrieval index drifts or stops updating cleanly
