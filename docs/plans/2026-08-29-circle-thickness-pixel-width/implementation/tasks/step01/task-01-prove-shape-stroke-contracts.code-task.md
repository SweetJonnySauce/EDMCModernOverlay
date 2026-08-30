# Task: Prove independent rectangle and circle stroke contracts

## Description

Replace the shared bounded-shape thickness assertion with independent
rectangle and circle contract tests. This establishes the intended behavior
before production code changes: rectangle thickness remains scale-aware,
whereas circle thickness is a stable Qt logical-pixel width.

This is a deliberately test-first task. Do not change runtime source; the new
circle assertions are expected to fail against the current renderer.

## Background

`_build_rect_command()` and `_build_circle_command()` both currently provide
their explicit thickness through `_StrokeWidthSpec.explicit_logical_width`.
The shared test consequently asserts that both shapes multiply thickness by
the group scale. The approved design changes that contract only for circles:
their supplied thickness must not be multiplied by the Fit/Fill scale. This
task makes the two policies explicit without changing renderer behavior.

## Reference Documentation

**Required:**

- Design: `docs/plans/2026-08-29-circle-thickness-pixel-width/design/detailed-design.md`

**Additional References:**

- Implementation plan, Step 1:
  `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/plan.md`
- Existing code findings:
  `docs/plans/2026-08-29-circle-thickness-pixel-width/research/existing-code.md`
- Requirements decision:
  `docs/plans/2026-08-29-circle-thickness-pixel-width/idea-honing.md`

**Note:** Read the detailed design before beginning implementation. Read the
additional references as needed for context.

## Technical Requirements

1. Modify only `overlay_client/tests/test_render_surface_mixin.py`; do not
   modify runtime source in this task.
2. Replace the current parameterized test that treats `rect` and `circle` as
   sharing one scale policy with independent, clearly named unit-test
   contracts at the existing command-builder seam.
3. Preserve the rectangle matrix for `thickness=2`: group scales `0.5`,
   `1.0`, and `2.0` must resolve to pen widths `1`, `2`, and `4`.
4. Add a circle matrix for `thickness=1`: group scales `0.5`, `1.0`, and
   `2.0` must each resolve to a pen width of `1`.
5. Add a non-unit circle assertion: `thickness=3` at group scale `2.0` must
   resolve to a pen width of `3`, proving the policy is generally unscaled.
6. Preserve the existing join-style assertions in the appropriate separate
   shape tests: explicit rectangles use `MiterJoin`; circles use `BevelJoin`.
7. Select **unit tests**: the behavior is deterministic command construction
   with an injected group context and does not depend on `load.py` or the EDMC
   lifecycle.
8. Run exactly:

   ```bash
   PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py -k thickness
   ```

   The expected baseline is red because circle thickness currently scales.
   Capture the precise failing assertions/results in the task record; do not
   "fix" the production implementation as part of this task.
9. Do not commit, stage, push, amend, reset, restore, stash, clean, checkout,
   switch branches, rebase, merge, or otherwise modify Git history or index.
   Preserve unrelated worktree changes.

## Dependencies

- The existing `_RectSurface`, `_CircleSurface`, `_StubGroupContext`,
  `_build_rect_command`, and `_build_circle_command` test helpers in
  `overlay_client/tests/test_render_surface_mixin.py`.
- A GUI-enabled overlay-client test environment, enabled by `PYQT_TESTS=1`.
- Step 2 will consume these intentionally red circle assertions to implement
  the explicit pixel-width policy.

## Implementation Approach

1. Inspect the existing shared `test_explicit_shape_thickness_scales_with_group_context`
   parameterization and its helpers to preserve its rectangle coverage and
   join-style expectations.
2. Refactor it into a rectangle-only parameterized test with the existing
   `thickness=2` scale matrix and a circle-only parameterized test for
   `thickness=1` with expected width one at every specified scale.
3. Add the non-unit circle case at scale `2.0`, then run the required focused
   command once. Record the expected red result in
   `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/task-records/step01-task01/`
   when executing this task; do not change any other file or behavior.

## Acceptance Criteria

1. **Rectangle logical-width contract remains explicit**
   - Given an explicit rectangle `thickness=2` and injected group scales
     `0.5`, `1.0`, and `2.0`
   - When `_build_rect_command()` produces its paint command
   - Then its pen widths are `1`, `2`, and `4`, respectively, and its join is
     `MiterJoin`.

2. **Unit circle thickness is independent of scale**
   - Given an explicit circle `thickness=1` and injected group scales `0.5`,
     `1.0`, and `2.0`
   - When `_build_circle_command()` produces its paint command
   - Then each assertion requires pen width `1` and `BevelJoin`.

3. **Non-unit circle thickness is independently unscaled**
   - Given an explicit circle `thickness=3` with group scale `2.0`
   - When `_build_circle_command()` produces its paint command
   - Then the assertion requires pen width `3`, not `6`.

4. **Red baseline proves the current mismatch**
   - Given the new circle assertions and unmodified production renderer
   - When the required focused `PYQT_TESTS=1` pytest command is run
   - Then rectangle cases pass and the circle cases fail because the current
     logical-width implementation still applies group scale.

5. **Task remains behavior-safe and isolated**
   - Given this Step 1 task is complete
   - When its diff and Git status are reviewed
   - Then only the focused test and its required task record are changed, with
     no production edit and no Git index/history mutation.

## Metadata

- **Complexity**: Low
- **Labels**: Rendering, Circle, Stroke Width, Unit Test, Test First
- **Required Skills**: Python, pytest, PyQt6 command rendering tests, code-assist
