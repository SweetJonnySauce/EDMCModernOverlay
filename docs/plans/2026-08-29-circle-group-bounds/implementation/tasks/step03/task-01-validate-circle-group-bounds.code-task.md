# Task: Validate Integrated Circle Group Bounds

## Description
Perform the final, validation-only check of the circle group-bounds regression
fix. Confirm that the focused bounds contract, its grouping/rendering
integration surfaces, and the repository-wide quality gate remain green. This
task must not change production or test behavior.

## Background
Steps 1 and 2 established and implemented the geometry contract: a circle is
bounded by its centre plus/minus radius, and all four resulting corners use the
same transform path as rectangles. The focused PyQt-enabled bounds module is
already green after the narrow `accumulate_group_bounds()` change. This final
step verifies that the implementation remains aligned with the existing
renderer model (`x-radius`, `y-radius`, `2 * radius`) and that the surrounding
Fill-mode/group-transform and rendering test surfaces remain healthy.

The target worktree is intentionally dirty. In particular, unrelated payload
inspector, version, and prior planning work must be preserved exactly as found.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-29-circle-group-bounds/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-29-circle-group-bounds/implementation/plan.md` (Step 3 requirements)
- `docs/plans/2026-08-29-circle-group-bounds/implementation/task-records/step01-task01/progress.md` (red-baseline evidence)
- `docs/plans/2026-08-29-circle-group-bounds/implementation/task-records/step02-task01/progress.md` (implementation and focused-green evidence)
- `overlay_client/payload_transform.py` (`accumulate_group_bounds()` circle branch)
- `overlay_client/render_surface.py` (existing circle renderer geometry)
- `overlay_client/tests/test_payload_bounds.py`, `overlay_client/tests/test_grouping_helper.py`, `overlay_client/tests/test_group_transform.py`, and `overlay_client/tests/test_render_surface_mixin.py`

**Note:** You MUST read the detailed design document before beginning
validation. Read additional references as needed for context.

## Technical Requirements
1. This is validation-only: do not edit production source, tests, task records,
   execution status, or planning documents.
2. Before validation, inspect the scoped diff for
   `overlay_client/payload_transform.py` and
   `overlay_client/tests/test_payload_bounds.py`. Confirm the circle branch
   derives `x +/- radius` and `y +/- radius`, transforms all four corners, and
   does not alter existing message, rectangle, vector, or generic-fallback
   behavior.
3. Run exactly these validation commands from the repository root:
   - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_payload_bounds.py`
   - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_grouping_helper.py overlay_client/tests/test_group_transform.py overlay_client/tests/test_render_surface_mixin.py`
   - `make check`
4. Run `git diff --check`, inspect `git diff --check` output, and inspect
   `git status --short` plus the scoped diff after validation. These are
   read-only safety checks only.
5. Preserve all existing uncommitted work, including `version.py`,
   `utils/payload_inspector.py`, `tests/test_payload_inspector.py`, and
   `docs/plans/2026-08-29-payload-inspector-circle-preview/`.
6. Do not stage, commit, push, amend, reset, checkout, switch, stash, clean,
   restore, rebase, merge, or otherwise alter Git index, history, branches, or
   unrelated files. If a scoped defect is discovered, stop and report it in the
   handoff; do not fix it in this validation task.
7. Document each command's exact pass/fail/skip result in the final handoff,
   along with the scoped-diff and worktree inspection outcome. Do not create or
   update files to record that information.

## Dependencies
- Step 1's normal-circle regression test and Step 2's transformed-circle test
  and implementation are present.
- The local `overlay_client/.venv` has the PyQt-enabled test environment.
- `make check` remains the repository's lint, typecheck, and full-test gate.

## Implementation Approach
1. Read the approved design, Step 3 plan, and Step 1/2 progress records, then
   inspect the target source/test diff against the renderer's established
   square-footprint model.
2. Run the focused bounds module first, followed by the grouping,
   group-transform, and render-surface modules, then the repository-wide
   `make check` gate.
3. Perform the whitespace, scoped-diff, and worktree safety checks after the
   commands complete. Return concise evidence; make no edits.

## Acceptance Criteria

1. **Circle Regression Contract Is Green**
   - Given the Step 2 circle bounds implementation is present
   - When `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_payload_bounds.py` runs
   - Then the normal and transformed circle-bounds cases pass.

2. **Grouping and Rendering Surfaces Remain Green**
   - Given Fill grouping consumes `accumulate_group_bounds()` and the renderer
     remains the visual authority
   - When the specified grouping, group-transform, and render-surface test
     modules run with `PYQT_TESTS=1`
   - Then they pass without changes to public payloads or circle paint commands.

3. **Repository Quality Gate Is Green**
   - Given the scoped implementation is complete
   - When `make check` runs
   - Then linting, type checking, and the configured test suite pass, with any
     skips reported exactly as emitted by the command.

4. **Scoped Change and Worktree Safety Are Confirmed**
   - Given the validation task began with unrelated uncommitted work
   - When the final scoped diff, `git diff --check`, and `git status --short`
     are inspected
   - Then the circle changes remain limited to the approved source/test paths,
     no whitespace errors appear, and unrelated work remains preserved.

5. **Validation Does Not Expand Scope**
   - Given the task is final validation only
   - When a potential issue outside the approved circle-bounds scope is found
   - Then it is reported without modifying production code, tests, records, or
     Git state.

## Metadata
- **Complexity**: Low
- **Labels**: Validation, Circle, Fill-Mode, Group-Bounds, Regression-Test, PyQt
- **Required Skills**: Python, pytest, static-analysis interpretation, scoped-diff review
