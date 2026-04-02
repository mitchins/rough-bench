# Gold Notes

This task is not about generic RAG upgrades.

The main diagnostic is whether the answer says, early and explicitly, that the
system is over-collapsing broad queries:

- k=20 on a 200k-document corpus is already thin for thematic retrieval
- reranking those 20 and exposing only top-5 throws away 75% of the candidate set
- broad queries need coverage and diversity before precision narrowing

The strongest answers will say some version of:

- the reranker is not the core problem
- the cutoff is
- broad and narrow queries should not share the same policy

This task should reward:

- explicit engagement with the given metrics
- explicit discussion of k=20 to top-5 truncation
- query-type-aware routing or handling
- diversity-preserving broad-query retrieval such as larger k, no rerank, or MMR-like objectives
- measurement before and after reranking, not just final hit-rate
- concrete guardrails and ship criteria

This task should punish:

- "try a better reranker"
- "use ColBERT" as the main answer
- "use hybrid retrieval" without talking about truncation
- vague monitoring language instead of thresholds
- answers that never engage the broad-versus-narrow asymmetry
