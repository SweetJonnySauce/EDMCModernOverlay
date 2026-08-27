# Task: Resolve Render-Surface Test Coverage for Circle and Stroke Contracts

## Description

Resolve only the conflict in `overlay_client/tests/test_render_surface_mixin.py`
as a union of the backend-refactor test baseline and the source feature's
circle/stroke coverage. The result must prove the merged render-surface
contract without discarding backend vector/screen tests or relying on a
wholesale source-file selection.

## Background

Task 1 resolves the render-surface implementation while leaving this test file
intentionally conflicted. The target brought backend test dependencies and
coverage, including vector/screen behavior; the source added `QPen`,
`_CirclePaintCommand`, `_StrokeWidthSpec`, and tests for scaled explicit shape
thickness, explicit rectangle miter joins, pen-copy isolation, circle command
construction, transparent styling, and dispatch metadata. Both sets are needed
to anchor the Step 3 merge before the processor/paint auto-merge review.

## Reference Documentation

**Required:**
- Design: `docs/plans/2026-08-27-circle-feature-backend-merge/design/detailed-design.md`
- Approved plan: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/plan.md`
- Orchestration constraints: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/orchestration-prompt.md`

**Additional References (if relevant to this task):**
- Merge assessment: `docs/plans/2026-08-27-circle-feature-backend-merge/research/merge-assessment.md`
- Current merge evidence: `docs/plans/2026-08-27-circle-feature-backend-merge/progress.md`
- Renderer-resolution task: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/tasks/step03/task-01-resolve-render-surface-backend-circle-contract.code-task.md`
- Repository instructions: `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read the approved plan, orchestration prompt, and Task 1
handoff before resolving tests so the assertions match the final renderer API.

## Technical Requirements

1. Resolve only `overlay_client/tests/test_render_surface_mixin.py`. Retain the
   target branch's backend imports, helpers, fixtures, vector/screen coverage,
   and assertions; merge in only the source imports/helpers/tests that exercise
   the approved circle and stroke contract. Do not select either side or
   wholesale replace the test file.
2. Reconcile imports so all referenced test symbols are present and unused
   imports are avoided, including `QPen`, `_CirclePaintCommand`, existing
   vector command coverage, `_ScreenBounds`, and `_StrokeWidthSpec` where the
   final renderer interface requires them.
3. Preserve or add focused unit coverage proving that explicit rectangle and
   circle thickness scale with group context; explicit rectangles use
   `MiterJoin`; omitted-thickness rectangles retain legacy width/join; and
   resolved explicit pens do not mutate their source pen.
4. Preserve or add focused unit coverage proving a circle command has square
   transformed bounds, correct transparent pen/brush handling, transformed
   group metadata, cycle anchor behavior, and render-surface dispatch.
5. Test-only changes must not adjust runtime behavior to satisfy assertions.
   If Task 1's renderer API differs from an expected test helper, update the
   helper to the approved interface or stop with evidence of an actual
   implementation defect for a fresh remediation context.
6. Do not edit, stage, restore, regenerate, or otherwise change
   `overlay_groupings.json`; it must remain target-owned and absent from the
   staged merge diff. Do not modify source runtime files, merge tracking
   documents, public API/docs, or Git topology in this task.
7. Use unit tests, not harness tests: the render-surface builder and paint
   command behavior is deterministic under existing stubs. Run both focused
   GUI-enabled suites after resolving this conflict:
   `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest
   overlay_client/tests/test_render_surface_mixin.py
   overlay_client/tests/test_paint_commands.py -q`.
8. Before handoff, scan both formerly conflicted paths for markers and confirm
   the grouping configuration has no staged/worktree diff. Do not attempt the
   processor/paint-command contract review; Task 3 owns that work. Stage only
   the fully resolved `overlay_client/tests/test_render_surface_mixin.py` after
   its focused validation succeeds.

## Dependencies

- Task 1 has resolved `overlay_client/render_surface.py` and handed off its
  exact API/validation evidence.
- The active merge still contains this one unresolved test-file path; no other
  source or configuration path may be substituted or discarded.
- Task 3 is pending and owns review of auto-merged
  `overlay_client/legacy_processor.py` and `overlay_client/paint_commands.py`.

## Implementation Approach

1. Compare the three-way test conflict with the completed renderer interface.
   Assemble a union of imports and helpers, keeping target backend tests as the
   baseline and adding only circle/stroke dependencies that the final code uses.
2. Resolve the conflict manually and retain the targeted assertions for stroke
   scaling, miter-vs-legacy joins, pen isolation, circle square bounds,
   transparent styling, metadata, and dispatch.
3. Run the GUI-enabled focused render-surface and paint-command pytest command.
   Treat any failure as a merge defect: diagnose against the approved contract,
   apply only a task-scoped test correction, or hand off exact evidence rather
   than hiding it.
4. Confirm no conflict markers remain in either formerly unresolved file and
   the grouping file has no diff, then stage only
   `overlay_client/tests/test_render_surface_mixin.py`. Finish with exactly
   this five-part handoff, with no additional sections:
   `Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`
   Direct the next action to Task 3.

## Acceptance Criteria

1. **Backend and circle test baselines coexist**
   - Given the target/backend and source/circle variants of the test module
   - When the test conflict is resolved
   - Then backend vector/screen coverage and circle/stroke coverage both remain
     present, their imports/helpers compile together, and neither full variant
     was selected wholesale.

2. **Stroke compatibility is proved**
   - Given explicit rectangle/circle thickness and an omitted rectangle
     thickness under group transforms
   - When focused render-surface tests run
   - Then explicit widths scale, explicit rectangles use `MiterJoin`, legacy
     omitted rectangles retain their target behavior, and source pens are not
     mutated.

3. **Circle render-surface contract is proved**
   - Given circle items with transformed placement and opaque or transparent
     border/fill styles
   - When circle builder and dispatch tests run
   - Then square bounds, transparent style semantics, command type, group
     metadata, cycle anchor, and dispatch contribution are asserted.

4. **Focused GUI-enabled validation passes**
   - Given both prior conflicts have been resolved
   - When `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest
     overlay_client/tests/test_render_surface_mixin.py
     overlay_client/tests/test_paint_commands.py -q` runs
   - Then it passes and the exact command/result is recorded; any failure is
     reported as unresolved merge evidence rather than ignored.

5. **Scope and managed configuration stay intact**
   - Given test resolution is complete
   - When conflict-marker and path-scoped grouping diff checks run
   - Then no markers remain in the two resolved paths,
     `overlay_groupings.json` has no staged/worktree diff, and no runtime,
     configuration, or unrelated documentation file changed in this task.

## Metadata

- **Complexity**: Medium
- **Labels**: Merge Conflict, Unit Tests, Render Surface, Circle Rendering, Stroke Width
- **Required Skills**: Three-way test conflict resolution, PyQt test design, deterministic unit testing, merge-scope auditing
