# Task: Review Auto-merged Legacy Processor and Paint Command Contracts

## Description

Review the auto-merged `overlay_client/legacy_processor.py` and
`overlay_client/paint_commands.py` paths against the approved circle/stroke
contract. Run focused processor and paint tests. Make code changes only when
the review identifies a concrete merge defect; this is not permission for
cleanup, refactoring, or feature expansion.

## Background

These paths auto-merged textually, but they sit on the runtime path from public
payload normalization through legacy storage, render-surface dispatch, and Qt
painting. A clean merge does not establish behavior. The processor must retain
positive circle geometry/thickness validation, warning-and-drop behavior that
does not replace an existing same-ID item, optional rectangle thickness, fill,
opacity/transform semantics, and trace coverage. The paint command must retain
circle drawing, opacity-adjusted copies, transparent pen/brush behavior, and
cycle-anchor registration without shared-pen mutation.

## Reference Documentation

**Required:**
- Design: `docs/plans/2026-08-27-circle-feature-backend-merge/design/detailed-design.md`
- Approved plan: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/plan.md`
- Orchestration constraints: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/orchestration-prompt.md`

**Additional References (if relevant to this task):**
- Merge assessment: `docs/plans/2026-08-27-circle-feature-backend-merge/research/merge-assessment.md`
- Decisions and visual caveat: `docs/plans/2026-08-27-circle-feature-backend-merge/idea-honing.md`
- Current merge evidence: `docs/plans/2026-08-27-circle-feature-backend-merge/progress.md`
- Prior Step 3 tasks: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/tasks/step03/task-01-resolve-render-surface-backend-circle-contract.code-task.md` and `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/tasks/step03/task-02-resolve-render-surface-tests-circle-stroke-coverage.code-task.md`
- Repository instructions: `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read the approved plan, orchestration prompt, merge assessment,
and both prior Task 3 handoffs before evaluating whether a code change is
actually required.

## Technical Requirements

1. Review `overlay_client/legacy_processor.py` for circle payload validation:
   center coordinates, positive radius, positive thickness, default/optional
   fill, preserved transform and opacity data, first-class stored circle items,
   and warning-and-drop behavior that preserves an existing item with the same
   ID on invalid input.
2. Review the same processor path for optional explicit rectangle thickness:
   valid positive values are preserved, invalid values warn and do not replace
   an existing item, and omitted thickness remains absent so legacy rectangle
   rendering stays unchanged.
3. Review `overlay_client/paint_commands.py` for the circle command's Qt draw
   operation, offset bounds, trace/anchor conventions, payload opacity copies,
   transparent pen/brush behavior, and no mutation of shared source pens or
   brushes.
4. Make no code change unless a review finding is a specific divergence from
   the approved design, task evidence, or focused-test expectation. If a defect
   is found, make the smallest behavior-scoped correction and add/update the
   focused unit test that proves it. Do not perform unrelated cleanup or
   refactoring.
5. Explicitly select unit tests: processor parsing/storage and paint command
   drawing can run under injected stubs and do not require `load.py` lifecycle
   wiring. Run `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest
   tests/test_legacy_processor.py overlay_client/tests/test_paint_commands.py
   -q`. If a merge defect requires code/test changes, rerun the same focused
   command once after the correction; do not rerun an unchanged failure.
6. Do not edit, stage, restore, regenerate, or otherwise change
   `overlay_groupings.json`. It must remain the target-HEAD version and absent
   from the staged merge diff. Do not edit render-surface source/tests, public
   API/docs, grouping behavior, plan/progress/dashboard, or Git topology.
7. Do not resolve conflicts by wholesale source-file selection. Keep the
   backend refactor as baseline in every reviewed path, and preserve the
   `fix219` backend boundary.
8. Before handoff, report whether the review found a defect, scan core runtime
   paths for conflict markers, and confirm the grouping configuration is
   unchanged. Do not claim the full Step 4 test gate has run; that is a later
   task. If a proven merge defect required an edit, stage only the affected
   reviewed runtime/test path after focused validation; otherwise do not change
   staging.

## Dependencies

- Tasks 1 and 2 have resolved the renderer and test-file conflicts and recorded
  their focused validation evidence.
- The no-commit merge remains active; all auto-merged source changes are still
  reviewable and `overlay_groupings.json` is already restored to target state.
- Step 4 owns the complete integration, harness, EDMC compatibility, and
  project-wide test gates.

## Implementation Approach

1. Read the auto-merged diffs and the final source files side by side with the
   design/assessment contracts. Enumerate validation, same-ID, fill/opacity,
   transparency, trace, anchor, and pen-isolation observations before editing.
2. Run the focused GUI-enabled processor/paint test command. If it passes and
   review finds no divergence, leave code unchanged and report that outcome.
3. If review finds an actual merge defect, use RED → GREEN → REFACTOR for the
   smallest correction and focused regression test, then rerun the exact
   focused command once. Preserve all unrelated merge content.
4. Verify no core-path conflict markers and no grouping diff. Finish with
   exactly this five-part handoff, with no additional sections:
   `Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`
   Direct the next action to the main orchestrator's Step 3 scope review and
   then fresh Step 4 task generation.

## Acceptance Criteria

1. **Processor validation and replacement contracts are reviewed**
   - Given valid and invalid circle or explicitly thick rectangle payloads,
     including an existing item with the same ID
   - When the processor review and focused tests run
   - Then valid values are normalized/stored as intended, invalid geometry or
     thickness warns and drops without replacement, and omitted rectangle
     thickness preserves legacy behavior.

2. **Paint command styling and isolation contracts are reviewed**
   - Given circle commands with opaque or transparent pen/brush styles and
     reduced payload opacity
   - When paint-command tests run
   - Then circles draw with offset bounds and trace/anchor behavior, opacity
     uses copies, transparent styles remain transparent, and shared styles are
     not mutated.

3. **Focused processor and paint validation passes**
   - Given the auto-merged processor and paint-command paths
   - When `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest
     tests/test_legacy_processor.py overlay_client/tests/test_paint_commands.py
     -q` runs
   - Then it passes and the exact result is recorded; a failure is either fixed
     only as a proven merge defect with a focused regression test or handed off
     with precise blocker evidence.

4. **No speculative code change is made**
   - Given the review finds no contract divergence
   - When the task completes
   - Then no source or test file is modified merely for cleanup; if a concrete
     defect is found, only the minimal affected runtime/test files change and
     the reason is recorded.

5. **Protected merge scope remains intact**
   - Given the review is complete
   - When grouping-diff and conflict-marker checks run
   - Then `overlay_groupings.json` remains absent from staged/worktree diffs,
     no file is selected wholesale, no renderer conflict is reopened, and the
     task makes no plan/progress/dashboard/configuration change.

## Metadata

- **Complexity**: Medium
- **Labels**: Merge Review, Legacy Processor, Paint Commands, Circle Rendering, Unit Tests
- **Required Skills**: Runtime contract review, PyQt paint inspection, payload validation, focused unit testing
