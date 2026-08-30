# Task 4.2: Reconcile Documentation and Refactoring Moves

## Description

Reconcile the active, uncommitted merge's public rendering/API documentation
and the four `docs/refactoring/` deletion-versus-edit paths. Preserve the
merged public circle and optional-thickness contract, retain substantive
current guidance only in an appropriate current location, and leave obsolete
refactoring documents deleted unless the documented ownership review proves a
specific replacement is required. This is documentation and merge-metadata
work only; it must not change behavior or make a release decision.

## Background

Tasks 3.1--3.3 and 4.1 established the integration contract that the public
documentation must describe consistently:

- `rect` and `circle` are supported shape primitives; circles use centre
  `x`/`y` and a required positive `radius`.
- Explicit valid `thickness` for either shape is a logical Qt-pixel width,
  rounded and clamped to at least one pixel without viewport or group scaling.
  Omitting it preserves the client-controlled legacy default.
- Circle geometry flows through the existing bounded-shape/group/viewport
  mapping, so non-uniform mapping can intentionally render an ellipse.
- The `fix219` backend boundary remains intact; this task must not touch its
  implementation or make claims that imply a new runtime architecture.

The prior circle documentation task established the expected public-document
locations and the normalization-versus-client-validation wording. The later
unified-width plan supersedes its older logical-width language. The merge plan
also records four `docs/refactoring/` paths where `main` deleted a document
that the target edited. They must be identified from the active merge and
reviewed individually; do not guess from the full refactoring directory or
revive files wholesale.

## Required reading order

1. `AGENTS.md`
2. `docs/plans/2026-08-30-main-branch-merge/implementation/orchestration-prompt.md`
3. `docs/plans/2026-08-30-main-branch-merge/plan.md`
4. `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
5. This task brief and
   `implementation/handoffs/task-4-1-shape-gallery-union.md`
6. `docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step04/task-02-document-circle-shape-support.code-task.md`
   and its `implementation/task-records/step04-task02/{context,progress,plan}.md`
7. `docs/plans/2026-08-30-unify-shape-thickness-pixels/implementation/plan.md`
   and the current candidate public pages below.

## Exact boundary

### Candidate public documentation

Review only these pages, and edit only a page whose current merge result
conflicts with the established contract or whose public wording is made stale
by the documented reconciliation:

- `docs/wiki/send_shape-API.md`
- `docs/wiki/send_raw-API.md`
- `docs/wiki/Getting-Started.md`
- `docs/wiki/Concepts.md`
- `docs/wiki/Developer-FAQs.md`
- `docs/wiki/APIs.md`
- `docs/rendering-pipeline.md`

### Candidate refactoring documents

Use **read-only local Git merge/history inspection** to enumerate the exact
four deletion-versus-edit paths recorded in the governing plan. Those exact
paths, not every file under `docs/refactoring/`, are the only refactoring
documents in scope. For each one, record its target-side guidance, `main`'s
deletion intent, any current replacement/archival location, and the resulting
decision: retain, move/condense into a named current document, or leave
deleted. A move or condensation must preserve only still-current guidance;
do not recreate an obsolete plan merely to avoid a deletion.

### Allowed record updates

- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-4-2-documentation.md`

Do not change source, tests, gallery files, configuration, `version.py`,
release metadata, unrelated documentation, or any Task 5 artifact. Do not
touch `overlay_groupings.json` or `overlay_settings.json`. Do not run a live
overlay, send live payloads, use the network, fetch, commit, push, reset,
abort, rebase, stash, clean, or make a release/version decision. Stage only
the exact documentation paths resolved by this task when staging is necessary
for the active merge; do not stage a broad directory.

## Plan and stages

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 4 | 4.2.1 | Freeze the exact documentation/refactoring candidate inventory from the active merge. | Pending |
| 4 | 4.2.2 | Reconcile public API/rendering wording with the accepted merged contract. | Pending |
| 4 | 4.2.3 | Decide each deletion-versus-edit path and retain only current guidance in its intended home. | Pending |
| 4 | 4.2.4 | Perform documentation-only validation and write the required handoff. | Pending |

Phase 4 remains **In progress** until Tasks 4.2 and 4.3 are completed.

## Technical requirements

1. Before any edit, make a small path-and-decision ledger. The ledger must
   name every public page actually changed and each of the four refactoring
   candidates, show the authoritative prior/current document, and explain why
   no other `docs/refactoring/` path is in scope.
2. Retain the positional rectangle `send_shape` form and distinguish a
   first-class `shape="circle"` from a vector `marker: "circle"`. Do not
   restore rectangle-only statements or claim that vector markers are shapes.
3. Keep all public examples and field tables aligned: circle `x`/`y` are its
   centre; circles require positive `radius`; both shapes may omit
   `thickness`; explicit valid width is the shared unscaled pixel policy; and
   raw normalization versus client-side invalid-geometry handling remains
   accurately bounded.
4. Keep rendering prose behavior-scoped: describe the derived circle square,
   shared mapping, bounded `QPainter.drawEllipse`, and intentional
   non-uniform ellipse result. Do not invent trace stages, backend-specific
   behavior, or additional compatibility guarantees.
5. Treat archived/refactoring material as historical unless it carries a
   still-applicable operational or architectural invariant that has no current
   owner. If that occurs, transfer the minimal guidance into the named current
   plan, design, or documentation page and state why that destination owns it.
   Preserve links and references only when their target remains valid; update
   a link only when it is in an otherwise in-scope document.
6. Resolve documentation as a semantic union, not with blanket ours/theirs or
   a whole-directory deletion/restore. Do not use an old `0.9.2` compatibility
   statement to decide the unresolved `version.py` conflict; Task 4.3 owns
   the release-version assumption.

## Test selection and validation

**Test type selected before edits: no new automated test type.** This task
changes Markdown and merge-document ownership only; it changes neither a pure
helper/service nor EDMC lifecycle wiring. Do not add or edit tests. Manually
compare every changed API example or behavior assertion with the accepted
Tasks 3.1--3.3/4.1 handoffs and the two required historical documentation
records above. The residual risk is prose/example copy drift, which Task 5's
existing product suites cannot parse.

Run and record these narrow checks after the documentation decisions:

```bash
rg -n -i 'only.*rect|rectangles? supported|logical.*thickness|scale[sd]?.*thickness' \
  docs/wiki/send_shape-API.md docs/wiki/send_raw-API.md \
  docs/wiki/Getting-Started.md docs/wiki/Concepts.md \
  docs/wiki/Developer-FAQs.md docs/wiki/APIs.md docs/rendering-pipeline.md
git diff --check -- <each exact documentation path changed by Task 4.2>
rg -n '^(<<<<<<<|=======|>>>>>>>)' <each exact documentation path changed by Task 4.2>
```

The search is a review aid, not a pass/fail substitute: classify each match as
correct, corrected, or a remaining stale claim. If a command cannot run,
record the exact failure and remaining documentation risk; do not substitute a
broader test suite or retry an unchanged failure. Task 5 still owns all
product, mixed unit/harness, backend-boundary, compatibility, and project
gate execution.

## Acceptance criteria

1. **Candidate inventory is bounded**
   - Given the active merge and its local history
   - When Task 4.2 begins resolution
   - Then its ledger identifies the exact four deletion-versus-edit paths and
     the reviewed public pages, with no whole-directory refactoring sweep.

2. **Public shape documentation is contract-accurate**
   - Given a plugin author reads any changed public API or rendering page
   - When they follow its rectangle or circle guidance
   - Then the page preserves positional rectangles, distinguishes vector
     markers, and accurately states circle geometry, optional thickness, and
     the shared explicit pixel-width rule.

3. **Rendering claims remain bounded**
   - Given a reader follows a documented circle through rendering
   - When mapping or painting is described
   - Then the documentation explains the bounded ellipse/shared mapping and
     non-uniform result without inventing trace stages, backend behavior, or
     a release compatibility promise.

4. **Refactoring deletions are intentional**
   - Given each exact refactoring deletion-versus-edit candidate
   - When its target-side guidance and `main` deletion are compared
   - Then the task records a per-path retain, named move/condensation, or
     leave-deleted decision and preserves only current substantive guidance.

5. **Documentation-only evidence is complete**
   - Given Task 4.2 is ready to hand off
   - When its scoped searches, whitespace check, and conflict-marker check
     run
   - Then their exact outcomes, changed paths, manual contract comparison, and
     copy-drift risk are recorded without claiming unrun product tests passed.

6. **The merge remains correctly scoped**
   - Given Task 4.2 completes
   - When the task records are reviewed
   - Then Phase 4 remains in progress, `version.py` and Task 4.3 remain
     untouched, no configuration or product path changed, and the handoff
     names Task 4.3 as the exact next task.

## Handoff requirements

Create `implementation/handoffs/task-4-2-documentation.md` with the exact
candidate inventory, per-path ownership decisions, public wording decisions,
files changed, commands and outcomes, test-type selection, residual risks,
and the explicit next task: Task 4.3 release-version resolution. Update Stage
4.2 and the Task 4.2 dashboard row only after that evidence is complete.
