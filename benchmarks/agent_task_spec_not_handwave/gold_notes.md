This task is not about picking one blessed stack. It is about whether the model
can turn a fuzzy idea into executable work without either:

- retreating into clarifying questions
- inflating the project into a whole platform
- writing polished PRD sludge

The load-bearing requirements are:

- preserve the local-first / anti-bloat constraint
- define a bounded first working POC
- specify a bundle format that avoids one giant file
- include non-goals, repo layout, milestones, deliverables, and acceptance criteria

The bundle-format point matters. A response that falls back to a single
`project.json` blob, flat JSON bundle, or another giant-file design should be
penalized even if the rest of the spec sounds clean.

The brief should also preserve implementation judgment. Locking the task to
React/Vite, Ollama, Electron/Tauri, or packaging/installers is usually a sign
that the model is designing for itself rather than writing a bounded agent
spec.

A strong answer should read like a brief you could hand to a coding agent and
actually expect useful implementation work from.
