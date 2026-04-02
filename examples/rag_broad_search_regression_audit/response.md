## Diagnosis

The regression is mostly self-inflicted narrowing, not a mystery about MiniLM quality. On a 200k-document corpus, `k=20` is already thin for broad thematic queries. You then rerank those 20 and expose only `top-5`, which means the user sees only 25% of the original candidate set. That is enough precision pressure to help narrow fact queries, but it is exactly how broad queries lose coverage.

## Why Broad Search Died

Broad queries need candidate diversity across subtopics. Your rerankers are optimizing semantic similarity to a single query representation, so after dense retrieval they cluster the output around one aspect of the theme. The mechanical failure is the `k=20 -> top-5` truncation step: even if the first-stage retriever found useful breadth, the reranker cutoff discards the other 15 candidates before the user sees them. That is why `broad_macro_hit_rate` collapsed from `0.600` to `0.100` and `0.150`.

## Replacement Strategy

Do not make a better reranker the primary fix. Split policy by query type.

- Narrow queries: keep a precision-oriented path. `k=20` plus reranking to `top-5` is defensible here.
- Broad queries: increase first-stage retrieval depth substantially, for example `k=80` or `k=100`, and do not immediately collapse to a pure similarity top-5. Either:
  - skip reranking entirely for broad queries and return a larger candidate window, or
  - apply a diversity-preserving rerank such as MMR and expose more than five results

The point is to preserve candidate diversity before presentation. If you later add hybrid BM25+dense, do it after fixing the truncation problem, not instead of fixing it.

## Ablation Plan

Step 1: measure broad and narrow slices separately with **no reranker** while sweeping first-stage `k` from 20 to 50 to 100.  
Success criteria: broad slice improves materially over the current reranked systems without dragging weighted hit rate below baseline.

Step 2: for broad queries only, compare:
- no rerank, return top-10 or top-12
- MMR or other diversity-preserving rerank, return top-10 or top-12
- current rerank path as control

Success criteria: pre-rerank candidate recall and post-rerank retained coverage both improve on the broad slice.

Step 3: add a simple broad-vs-narrow router and compare routed policy versus a single pipeline.  
Success criteria: routed policy beats a single-policy system on broad queries while narrow metrics stay stable.

## Regression Guardrails

- `weighted_hit_rate` must be no worse than baseline by more than `0.01`
- broad slice must recover to at least `broad_macro_hit_rate >= 0.600`
- narrow slice must stay within `0.01` of its no-reranker baseline after recomputing metrics by slice
- measure both **pre-rerank** candidate recall and **post-rerank** retained coverage so you can see where loss is happening

## Decision Rule

Ship only if the routed policy restores `broad_macro_hit_rate` to at least the `0.600` baseline, keeps `weighted_hit_rate` within `0.01` of `0.828` or better, and shows that coverage loss is no longer happening at the rerank cutoff. Otherwise do not ship.
