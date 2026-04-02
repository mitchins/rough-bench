## Core Information Model
Use a tree of nodes with two categories: leaf nodes are editable documents, while non-leaf structural nodes organize scenes, chapters, or note groups. Keep content separate from metadata so the inspector can hold tags, status, POV, and notes without polluting the prose body.

## Editor And Navigator Behaviour
The navigator handles structure. The editor opens only leaf nodes as primary documents. Non-leaf nodes show summaries, children, and notes, but folders are not editable documents. The inspector is the third surface for metadata and node notes.

## Bundle Format
Use a bundle directory with a manifest plus per-node files. `index.json` tracks hierarchy and ids, each leaf node stores content in its own file, and metadata lives in `metadata.json` or equivalent per-node records. This keeps the project inspectable without collapsing storage into a monolithic container.

## AI Attachment Points
AI completion attaches to the active node, selected text, or node notes. Context assembly can pull nearby nodes and metadata, but AI should stay attached to writing moments rather than becoming the center of the product.

## Anti-Bloat Guardrails
Non-goals: no collaboration, no plugin system, no publishing pipeline, no autonomous agents. Keep it nimble and local-first. The first version is a focused writing tool, not a giant productivity suite.

## First Implementation Slice
Ship one tree view, one editor view, one inspector, manifest-based bundle save/load, and node-level notes. That is enough to prove the model without collapsing the project into a monolithic bundle or AI gimmick sprawl.
