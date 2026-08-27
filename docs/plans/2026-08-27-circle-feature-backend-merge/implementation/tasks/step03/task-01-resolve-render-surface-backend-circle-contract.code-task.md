# Task: Resolve the Render Surface Conflict with the Backend Circle Contract

## Description

Resolve only the `overlay_client/render_surface.py` merge conflict. Retain the
backend-refactor branch as the structural baseline and integrate the bounded
shape/stroke and circle behavior needed for the approved feature: scaled
explicit stroke widths, circle dispatch and command construction, and mitered
joins for explicitly thick rectangles. This task must not resolve the separate
test-file conflict or broaden the merge scope.

## Background

The active no-commit merge has exactly two unresolved paths. The target branch
refactored render-surface architecture, while the source branch added
`_StrokeWidthSpec`, bounded-shape command construction, circle dispatch, and
explicit rectangle stroke handling. The merged result must preserve the target
architecture and all existing non-circle rendering behavior. Explicit
rectangle thickness is an opt-in physical-width contract after group scaling;
rectangles without a thickness field must retain their existing default width
and join behavior.

The render-surface test file intentionally remains conflicted until Task 2.
Consequently, this task can run a syntax check and focused paint-command tests,
but the focused render-surface pytest command belongs to Task 2 immediately
after that test conflict is resolved.

## Reference Documentation

**Required:**
- Design: `docs/plans/2026-08-27-circle-feature-backend-merge/design/detailed-design.md`
- Approved plan: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/plan.md`
- Orchestration constraints: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/orchestration-prompt.md`

**Additional References (if relevant to this task):**
- Merge assessment: `docs/plans/2026-08-27-circle-feature-backend-merge/research/merge-assessment.md`
- Decisions and visual caveat: `docs/plans/2026-08-27-circle-feature-backend-merge/idea-honing.md`
- Current merge evidence: `docs/plans/2026-08-27-circle-feature-backend-merge/progress.md`
- Repository instructions: `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read the approved plan and orchestration prompt completely,
then use the assessment and progress evidence to keep this resolution within
Step 3.

## Technical Requirements

1. Resolve only `overlay_client/render_surface.py`; retain the backend
   refactor's organization, backend-owned interfaces, imports, and non-circle
   dispatch behavior. Do not select either whole conflict side or wholesale
   replace the source file.
2. Integrate a narrow bounded-shape stroke policy that distinguishes an
   explicit logical width from legacy default pixel widths. Resolve explicit
   rectangle and circle thickness after the active group scale, with a fresh
   pen rather than mutation of a shared source pen.
3. Dispatch stored `LegacyItem(kind="circle")` values through a circle command
   builder. Build a square ellipse bounds rectangle from transformed center and
   radius, propagate the same group-transform metadata/cycle anchor conventions
   as bounded legacy shapes, and preserve transparent pen/brush semantics.
4. Preserve the explicit rectangle stroke contract: a supplied positive
   thickness uses its resolved width and `Qt.PenJoinStyle.MiterJoin`; an omitted
   thickness retains the target branch's legacy width and join behavior.
5. Preserve existing shape validation boundaries. This render-surface task must
   not add payload normalization, processor validation, public API, grouping,
   or configuration behavior.
6. Do not edit, stage, restore, regenerate, or otherwise change
   `overlay_groupings.json`. It must remain the target-HEAD version and absent
   from the staged merge diff.
7. Do not edit `overlay_client/tests/test_render_surface_mixin.py`; it remains
   the unresolved input to Task 2. Do not resolve any other path, modify merge
   tracking documents, commit, abort/restart the merge, or alter Git topology.
8. Choose unit tests explicitly: render-surface command construction is
   deterministic, but its only focused test module is currently conflicted.
   Run `overlay_client/.venv/bin/python -m py_compile
   overlay_client/render_surface.py` and run the focused, GUI-enabled paint
   command suite below. Record the renderer-test deferral and have Task 2 run
   the focused renderer/paint suites once both conflict paths are resolved.
9. Before handoff, inspect the resolved file for conflict markers and verify
   `overlay_groupings.json` has no staged or worktree diff. Stage only the
   fully resolved `overlay_client/render_surface.py` after those checks; do not
   stage, alter, or mask any other merge path.

## Dependencies

- Step 2's no-commit merge is active on `backend-refactor-implementation` and
  has exactly the known render-surface and render-surface-test conflicts.
- The target-owned `overlay_groupings.json` has already been restored in index
  and worktree and must remain untouched.
- Task 2 is pending and exclusively owns the test-file conflict and the first
  focused renderer pytest execution.

## Implementation Approach

1. Inspect the three-way conflict and the target/source variants. Identify the
   backend baseline seams that own transform handling and command dispatch;
   lift only the source circle/stroke behavior into those seams.
2. Resolve the source file manually: add the bounded stroke specification and
   resolver, preserve pen isolation, route circles to a square ellipse command,
   and make only explicit rectangle strokes mitered.
3. Run `overlay_client/.venv/bin/python -m py_compile
   overlay_client/render_surface.py` and `PYQT_TESTS=1
   overlay_client/.venv/bin/python -m pytest
   overlay_client/tests/test_paint_commands.py -q`. Do not try the conflicted
   render-surface test module; Task 2 must run it after its resolution.
4. Check the resolved file for conflict markers and confirm the grouping file
   remains unchanged, then stage only `overlay_client/render_surface.py`.
   Produce exactly this five-part handoff, with no additional sections:
   `Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`
   Leave the test conflict and all unrelated merge paths for their designated
   tasks.

## Acceptance Criteria

1. **Backend render-surface architecture is retained**
   - Given the target and source variants of `render_surface.py`
   - When the conflict is resolved
   - Then the target backend structure remains governing, neither side is
     selected wholesale, and no compositor-specific behavior crosses the
     backend boundary.

2. **Circle and bounded stroke behavior is integrated**
   - Given a valid stored circle with transformed coordinates, radius, colors,
     and thickness
   - When the render surface builds its bounded-shape command
   - Then it produces the appropriate circle command with square transformed
     bounds, resolved stroke width, and existing metadata/anchor conventions.

3. **Rectangle stroke compatibility is preserved**
   - Given a rectangle with explicit positive thickness and a rectangle without
     a thickness field
   - When their render commands are built under a group scale
   - Then only the explicit stroke scales and uses `MiterJoin`, while the
     omitted-thickness rectangle keeps its target-branch legacy width and join.

4. **Focused validation respects the remaining test conflict**
   - Given `test_render_surface_mixin.py` is intentionally unresolved for
     Task 2
   - When validation runs
   - Then `py_compile` for the resolved renderer and the GUI-enabled focused
     paint-command pytest suite pass, and the renderer pytest suite is
     explicitly deferred to Task 2 rather than run against a conflicted file.

5. **Managed configuration and merge scope remain protected**
   - Given the renderer resolution is complete
   - When the grouping diff and conflict-marker checks run
   - Then `overlay_groupings.json` has no staged/worktree diff, only the
     renderer conflict has been resolved, and no source/test/configuration
     file was selected wholesale or changed outside this task's scope.

## Metadata

- **Complexity**: High
- **Labels**: Merge Conflict, Render Surface, Circle Rendering, Stroke Width, Qt
- **Required Skills**: Three-way conflict resolution, PyQt painting, backend-boundary preservation, focused unit testing
