## Assumptions and Constraints

- This is a single-user desktop-first tool, not a collaborative platform.
- Local-first is mandatory. The POC should store project data on disk and work without a backend.
- The first version should stay small: tree navigation, editing, metadata, notes, and a thin AI-completion seam are in scope. Publishing, sync, and plugin systems are not.
- The bundle format should stay inspectable in a normal file browser and avoid one monolithic project file.

## POC Scope

Build a first working version that can open a project bundle, show a node tree, edit the selected node, edit per-node metadata and notes, and save everything back to disk. Include an interface for AI completion, but keep the provider layer minimal so the UI and data model do not depend on one model vendor.

## Non-Goals

- No real-time collaboration
- No cloud sync
- No auth or multi-user accounts
- No plugin marketplace
- No publishing/export pipeline beyond basic markdown or plain-text export

## Repo Layout

```text
story-ide/
  app/
    ui/
    state/
    models/
    storage/
    ai/
  tests/
  scripts/
  docs/
```

## Bundle Format

- One project directory per writing project
- `manifest.json` at the root for project metadata and node ordering
- one file per node under `nodes/`
- `notes/` for per-node notes keyed by node id
- metadata stored per node rather than embedded in one giant blob

## Implementation Milestones

### Phase 1

- Define project, node, metadata, and note models
- Implement bundle load/save for the directory format
- Add a basic tree view and node selection state

### Phase 2

- Add the document editor for node content
- Add metadata inspector and notes panel
- Wire save, rename, create, and delete operations

### Phase 3

- Add a minimal AI completion adapter interface
- Implement one provider-backed completion path behind that interface
- Add error handling so AI failures do not corrupt local documents

## Deliverables

- working desktop app POC
- bundle format spec in `docs/`
- load/save implementation for project bundles
- navigator, editor, metadata inspector, and notes UI
- minimal AI completion interface and one concrete implementation
- basic tests for bundle round-trip and core state operations

## Acceptance Criteria

- User can create and open a project bundle from local disk
- User can create, rename, reorder, and delete nodes in the tree
- User can edit node content, metadata, and notes and see those changes persist after reload
- Project data is saved as a directory bundle, not one giant file
- App remains usable with AI features disabled or unavailable
- Core load/save and node state tests pass
