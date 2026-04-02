## Failure Model
This benchmark should target false competence: answers that sound capable but miss hidden constraints, make unsafe assumptions, or describe work they did not actually demonstrate.

## Penalty-First Philosophy
Start at 0 and add demerits. Lower is better. The point is to punish operational wrongness, not reward polished prose.

## Evidence Hierarchy
Artifact-backed evidence should outrank prose claims and explanation. If a file, patch, or concrete output contradicts the prose, trust the artifact. Fluent claims without demonstrated work should score weakly.

## Signal Categories
- Hidden-constraint recovery
- Operationally correct task decomposition
- Artifact validity
- Honest scope boundaries

## Penalty Categories
- Prestige boilerplate without execution
- Unsafe omission of load-bearing constraints
- Plausible but wrong implementation claims
- Keyword mimicry of the rubric without matching substance

## Scoring Procedure
Apply structural penalties first, then constraint-recovery penalties, then artifact-validity penalties. Keep the summary grounded in what was actually demonstrated.

## Anti-Gaming Notes
This cannot be gamed by generic polish, benchmark jargon, or keyword mimicry. Treat prestige boilerplate as suspicious when it is not backed by artifacts or concrete operational detail.
