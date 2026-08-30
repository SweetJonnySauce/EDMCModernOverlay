# Task: Accumulate Transformed Circle Bounds

## Description
Implement the smallest circle-specific path in
`payload_transform.accumulate_group_bounds()` so Fill-mode grouping uses the
same full circle footprint as the renderer. Extend the focused unit coverage
with a transformed-circle case that proves all four extent corners, rather than
only the centre, participate in bounds aggregation.

## Background
Step 1 added a deliberately red regression test: a circle centred at `(100,
200)` with radius `25` must contribute `(75, 175)` through `(125, 225)` to
`GroupBounds`. The current generic fallback records only the centre point.

`overlay_client/render_surface.py` defines the visual contract by expanding a
circle to `left=x-radius`, `top=y-radius`, and a diameter of `2 * radius`.
`accumulate_group_bounds()` already follows the required transform convention
for rectangles: transform each of four logical corners with its local
`transform_point()` helper, then aggregate the transformed min/max rectangle.
The circle branch must use that same convention so `FillGroupingHelper.prepare()`
gets stable geometry without changes to public payloads or rendering.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-29-circle-group-bounds/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-29-circle-group-bounds/implementation/plan.md` (Step 2 requirements and demo)
- `docs/plans/2026-08-29-circle-group-bounds/research/existing-code.md` (renderer contract and current fallback)
- `docs/plans/2026-08-29-circle-group-bounds/implementation/task-records/step01-task01/progress.md` (intentional red baseline)
- `overlay_client/payload_transform.py` (`accumulate_group_bounds()` rectangle branch)
- `overlay_client/render_surface.py` (circle `x-radius`, `y-radius`, `2*radius` geometry)
- `overlay_client/tests/test_payload_bounds.py` (current normal-circle regression and test style)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Change only `overlay_client/payload_transform.py` and
   `overlay_client/tests/test_payload_bounds.py`, plus the task's own record
   files under `docs/plans/2026-08-29-circle-group-bounds/implementation/task-records/step02-task01/`.
2. Add an `item.kind == "circle"` branch in `accumulate_group_bounds()` before
   the generic fallback. Read `x`, `y`, and `radius` using the function's
   current logical/raw fallback convention.
3. Derive the circle's four logical square corners:
   `(x-radius, y-radius)`, `(x+radius, y-radius)`,
   `(x-radius, y+radius)`, and `(x+radius, y+radius)`.
4. Pass every derived corner through the existing local `transform_point()`
   helper, then call `bounds.update_rect()` with the transformed min/max
   values. Do not duplicate or replace the transform-metadata implementation.
5. Keep the message, rectangle, vector, generic fallback, exception handling,
   `determine_group_anchor()`, legacy payload schema, `send_shape` API, and
   circle paint commands unchanged.
6. Retain Step 1's untransformed test and add one transformed-circle test. Use
   non-uniform transform metadata (for example scale and offset) and assert
   all four final bounds. Its expected bounds must differ from a transformed
   centre point, proving radius extents were transformed.
7. Preserve all existing uncommitted work, including `version.py`,
   `utils/payload_inspector.py`, `tests/test_payload_inspector.py`, and
   `docs/plans/2026-08-29-payload-inspector-circle-preview/`. Do not stage,
   commit, push, amend, reset, checkout, switch, stash, clean, restore, or
   otherwise alter Git history or the index.

## Dependencies
- Step 1's normal-circle contract is present and intentionally red before this
  production change.
- `GroupBounds`, `LegacyItem`, and `apply_transform_meta_to_point()` remain the
  existing interfaces; no new public API is needed.
- `PYQT_TESTS=1` is required for `overlay_client/tests/test_payload_bounds.py`;
  the module otherwise skips by design.

## Implementation Approach
1. Inspect the current scoped diff and confirm Step 1's test is the only
   pre-existing change in the target test module. Read the approved design and
   the rectangle branch before editing.
2. Add the narrow `circle` branch beside the existing explicit shape branches.
   Convert the three numeric fields inside the existing `try` containment,
   transform all four extent corners with `transform_point()`, and aggregate
   their enclosing rectangle.
3. Add a focused transformed-circle test. A circle at `(100, 200)` with radius
   `25` and `__mo_transform__={"scale": {"x": 2.0, "y": 0.5}, "offset":
   {"x": 10.0, "y": -20.0}}` should assert bounds `(160, 67.5)` through
   `(260, 92.5)`. Those values demonstrate transformed extents, not merely a
   transformed centre `(210, 80)`.
4. Run the focused PyQt-enabled bounds module. First use the existing red
   baseline as TDD evidence; after the branch and test are in place, it must be
   green. Record exact commands and results in the task record. Run only
   scoped, non-destructive checks during this task; Step 3 owns repository-wide
   validation.

## Acceptance Criteria

1. **Normal Circle Contract Turns Green**
   - Given Step 1's circle centred at `(100, 200)` with radius `25`
   - When `accumulate_group_bounds()` processes it without transform metadata
   - Then `GroupBounds` is valid with minimum `(75, 175)` and maximum
     `(125, 225)`.

2. **Transformed Extents Are Aggregated**
   - Given a circle centred at `(100, 200)` with radius `25` and metadata with
     `scale=(2.0, 0.5)` and `offset=(10.0, -20.0)`
   - When `accumulate_group_bounds()` processes it
   - Then its transformed bounds are minimum `(160, 67.5)` and maximum
     `(260, 92.5)`, rather than a zero-area transformed centre point.

3. **Existing Shape Behavior Is Preserved**
   - Given messages, rectangles, vectors, and unsupported kinds continue
     through their existing branches
   - When the focused bounds module runs
   - Then their existing tests still pass without source changes to those
     branches.

4. **Focused Unit Validation Is Green**
   - Given the implementation and both circle regression tests are complete
   - When `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest
     overlay_client/tests/test_payload_bounds.py` runs
   - Then the command passes, including normal and transformed circle cases.

5. **Workspace Safety Is Maintained**
   - Given the repository began with unrelated uncommitted work
   - When this task completes
   - Then only its allowed source, test, and task-record paths have changed;
     no Git index or history operation was performed.

## Metadata
- **Complexity**: Medium
- **Labels**: Circle, Fill-Mode, Group-Bounds, Transform, Regression-Test, PyQt
- **Required Skills**: Python, pytest, geometric coordinate reasoning, TDD
