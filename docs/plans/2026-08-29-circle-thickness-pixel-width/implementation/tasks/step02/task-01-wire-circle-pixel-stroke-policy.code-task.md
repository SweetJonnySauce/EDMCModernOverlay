# Task: Wire the circle pixel-stroke policy

## Description

Implement the approved circle-only stroke-width policy at the bounded-shape
renderer seam. A supplied circle `thickness` must resolve as a stable Qt
logical-pixel width, without Fit/Fill group-scale multiplication. Explicit
rectangle thickness must continue to use its existing logical, scale-aware
behavior.

Step 1 has already established the contract in red. This task makes those
tests green without changing circle geometry, payload validation, or other
shape behavior.

## Background

Both `_build_rect_command()` and `_build_circle_command()` currently supply
their thickness through `_StrokeWidthSpec.explicit_logical_width`.
`_build_bounded_shape_command()` multiplies that field by `group_ctx.scale`,
which makes a circle with `thickness=1` become a two-pixel pen at scale 1.5
or 2.0. The legacy comparison vector treats its configured width as a Qt
pixel width, so the approved design gives circles a distinct explicit pixel
policy while retaining the rectangle logical policy.

The existing Step 1 tests intentionally require a one-pixel circle stroke at
scales 0.5, 1.0, and 2.0, and require a three-pixel result for a circle
thickness of three at scale 2.0. They currently fail only where the old
logical scaling diverges.

## Reference Documentation

**Required:**

- Design: `docs/plans/2026-08-29-circle-thickness-pixel-width/design/detailed-design.md`

**Additional References:**

- Implementation plan, Step 2: `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/plan.md`
- Existing-code findings: `docs/plans/2026-08-29-circle-thickness-pixel-width/research/existing-code.md`
- Requirements decision: `docs/plans/2026-08-29-circle-thickness-pixel-width/idea-honing.md`
- Step 1 task and red evidence: `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/tasks/step01/task-01-prove-shape-stroke-contracts.code-task.md` and `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/task-records/step01-task01/progress.md`

**Note:** You MUST read the detailed design before beginning implementation.
Read the additional references as needed for context.

## Technical Requirements

1. Modify only `overlay_client/render_surface.py`, `overlay_client/tests/test_render_surface_mixin.py` when a test correction is genuinely needed, and the task record directory `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/task-records/step02-task01/`.
2. Add a separate, clearly named `explicit_pixel_width: Optional[float]` policy field to `_StrokeWidthSpec`. Do not overload `default_pixel_width`, which represents renderer defaults rather than a caller-supplied thickness.
3. In `_build_bounded_shape_command()`, resolve an explicit pixel width first: round it and clamp it to at least one, without multiplying by `group_ctx.scale`. Preserve defensive no-crash behavior if a direct/internal caller supplies an unexpected non-numeric value.
4. Preserve the current `explicit_logical_width` resolution for rectangles: `round(width * group_ctx.scale)`, clamped to at least one. Preserve the existing default-pixel fallback behavior.
5. Change only `_build_circle_command()` to pass its already validated payload `thickness` through the new explicit pixel-width field. Keep circle color, fill, radius geometry, transforms, grouping, opacity, joins, and public `send_shape` arguments unchanged.
6. Do not change `_build_rect_command()` semantics, vector rendering, `render_config.json`, payload processing/validation, payload inspector code, or any other public API.
7. Use **unit tests**. The behavior is deterministic command construction with injected group context and does not depend on `load.py`, EDMC lifecycle wiring, or external services.
8. First run the exact focused command below and require the Step 1 circle contract to become green. Then run the exact full render-surface module command and `git diff --check`. Record exact pass/fail/skip results in the Step 2 task record.
9. Do not commit, stage, push, amend, reset, restore, stash, clean, checkout, switch branches, rebase, merge, or otherwise modify Git history or index. Preserve all pre-existing worktree changes.

## Dependencies

- Step 1's separate rectangle and circle contracts in `overlay_client/tests/test_render_surface_mixin.py`.
- `_StrokeWidthSpec`, `_build_bounded_shape_command()`, `_build_rect_command()`, and `_build_circle_command()` in `overlay_client/render_surface.py`.
- A GUI-enabled overlay-client test environment, enabled with `PYQT_TESTS=1`.

## Implementation Approach

1. Read the required design and Step 1 red evidence. Inspect the existing stroke policy and command-builders before editing, confirming that the shared bounded-shape path owns pen-width resolution.
2. Extend `_StrokeWidthSpec` with the explicit pixel-width field, retaining the existing logical and default fields. In the bounded-shape resolver, select the explicit pixel policy before the logical policy and retain the existing cloned-pen and `setWidth` flow.
3. Pass circle `thickness` as `explicit_pixel_width`; leave the rectangle construction unchanged. Keep the existing Step 1 test contracts unless a test defect is found, and add no out-of-scope coverage.
4. Create the required Step 2 task record with the local plan, progress, exact validation evidence, scoped-diff review, and an explicit no-Git-write confirmation.

## Acceptance Criteria

1. **Circle thickness is an explicit pixel policy**
   - Given a circle payload with `thickness=1` and injected group scales 0.5, 1.0, and 2.0
   - When `_build_circle_command()` produces its paint command
   - Then `QPen.width()` is one for every scale.

2. **Non-unit circle widths remain unscaled**
   - Given a circle payload with `thickness=3` and an injected group scale of 2.0
   - When `_build_circle_command()` produces its paint command
   - Then `QPen.width()` is three, not six.

3. **Rectangle logical-width behavior is unchanged**
   - Given an explicit rectangle `thickness=2` and injected group scales 0.5, 1.0, and 2.0
   - When `_build_rect_command()` produces its paint command
   - Then `QPen.width()` remains 1, 2, and 4 respectively, with `MiterJoin`.

4. **Shared painter behavior stays intact**
   - Given the new circle width policy
   - When the bounded-shape command builds a stroked circle or rectangle
   - Then it still clones the pen before applying a positive integer width, preserves the existing joins, and does not alter geometry or transforms.

5. **Focused and module validation pass**
   - Given the completed implementation
   - When the required focused and full render-surface commands run with `PYQT_TESTS=1`
   - Then they pass, and `git diff --check` passes.

6. **Task remains isolated and reversible**
   - Given the task is complete
   - When the worktree and task record are reviewed
   - Then changes are limited to the allowed source, focused test, and Step 2 task record paths; no Git index or history operation occurred.

## Validation Commands

- `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py -k thickness`
- `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py`
- `git diff --check`

## Metadata

- **Complexity**: Medium
- **Labels**: Rendering, Circle, Stroke Width, Qt, Unit Test
- **Required Skills**: Python, pytest, PyQt6 command rendering tests, code-assist
