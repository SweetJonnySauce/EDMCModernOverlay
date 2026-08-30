# Task: Validate integrated circle pixel-stroke policy

## Description

Perform the approved final validation for the circle-only pixel stroke-width
change. This is a validation-only task: it must establish that the completed
implementation makes explicit circle thickness a stable Qt logical-pixel
width, while explicit rectangle thickness remains group-scale-aware.

Do not edit source, tests, documentation, task records, dashboard, or Git
state. If review or validation finds a scoped defect, stop and report the
evidence for a new implementation task; do not fix it during this task.

## Background

Step 1 separated the rectangle and circle width contracts. Step 2 introduced
`_StrokeWidthSpec.explicit_pixel_width` and wired only circle thickness to it.
The completed focused tests show that circle widths no longer multiply by the
Fit/Fill group scale, whereas rectangle widths continue through the existing
logical-width branch. This task validates the integration boundary without
expanding the approved scope.

## Reference Documentation

**Required:**

- Design: `docs/plans/2026-08-29-circle-thickness-pixel-width/design/detailed-design.md`

**Additional References (if relevant to this task):**

- Implementation plan, Step 3: `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/plan.md`
- Orchestration guardrails: `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/orchestration-prompt.md`
- Step 1 red evidence: `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/task-records/step01-task01/progress.md`
- Step 2 implementation and focused validation: `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/task-records/step02-task01/progress.md`

**Note:** You MUST read the detailed design document before beginning
validation. Read the additional references as needed for context.

## Technical Requirements

1. This is validation-only. Do not change any source, test, documentation,
   task-record, dashboard, generated-task, configuration, or dependency file.
2. Review the scoped diff before and after commands. Confirm that the only
   behavior change is a circle-only explicit pixel-width policy and its
   focused tests; confirm explicit rectangle thickness still uses the existing
   group-scale-aware logical-width behavior.
3. Confirm the diff does not alter circle geometry, radius, grouping,
   transforms, payload validation, public `send_shape` arguments, vectors,
   `render_config.json`, or payload-inspector behavior.
4. Run these commands exactly, once each unless a command is interrupted by an
   external/environmental failure:

   ```bash
   PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py tests/test_legacy_processor.py tests/test_edmcoverlay_shapes.py
   make check
   git diff --check
   git status --short
   ```

5. Report the exact command outcomes, including pass/fail/skip counts and any
   environment limitations. Do not rerun an unchanged failing command.
6. If a scoped defect, failed in-scope test, or scope violation is found,
   stop immediately and report the command output/diff evidence. Do not apply
   a correction during validation.
7. Do not commit, stage, push, amend, reset, restore, stash, clean, checkout,
   switch branches, rebase, merge, or otherwise alter Git history or index.
   `git diff --check` and `git status --short` are read-only verification only.

## Dependencies

- The completed Step 1 circle/rectangle unit-test contracts.
- The completed Step 2 circle-only `explicit_pixel_width` renderer policy.
- The existing GUI-enabled overlay-client test environment, enabled with
  `PYQT_TESTS=1`.

## Implementation Approach

1. Read the required design, plan, guardrails, and Step 1/2 evidence. Inspect
   `git status --short` and the scoped diff without making any edits.
2. Review `overlay_client/render_surface.py` and
   `overlay_client/tests/test_render_surface_mixin.py` to verify the policy
   split: circles use unscaled explicit pixels; rectangles retain scaled
   explicit logical widths.
3. Run the required validation commands exactly and record their results in
   the execution handoff only. If all pass, report the scoped-diff review and
   no-Git-mutation confirmation. If any scoped defect is found, stop and
   request a new implementation task.

## Acceptance Criteria

1. **Circle pixel policy remains isolated**
   - Given the scoped implementation diff
   - When the renderer and focused tests are reviewed
   - Then only circles supply explicit pixel widths, those widths are not
     multiplied by group scale, and the test matrix proves widths one at
     scales 0.5, 1.0, and 2.0 plus a non-unit unscaled case.

2. **Rectangle scaling remains unchanged**
   - Given an explicit rectangle `thickness=2` at group scales 0.5, 1.0, and
     2.0
   - When the focused renderer tests run
   - Then its pen widths remain 1, 2, and 4 through the existing
     logical-width path.

3. **Integrated rendering and payload compatibility pass**
   - Given the completed circle stroke policy
   - When the required GUI-enabled pytest command is run
   - Then `test_render_surface_mixin.py`, `test_legacy_processor.py`, and
     `test_edmcoverlay_shapes.py` pass with all skip results reported.

4. **Repository validation is clean**
   - Given the scoped implementation is complete
   - When `make check` and `git diff --check` run
   - Then both pass, or any failure is reported with evidence and no edit is
     made during this task.

5. **Git and scope safety are preserved**
   - Given the validation task has finished
   - When `git status --short` and the scoped diff are reviewed
   - Then no Git index/history operation occurred, no file was edited by this
     task, and any pre-existing worktree changes are reported without
     alteration.

## Metadata

- **Complexity**: Low
- **Labels**: Validation, Rendering, Circle, Stroke Width, Regression
- **Required Skills**: pytest, PyQt6 rendering tests, Git diff review,
  code-assist
