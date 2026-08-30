# Task: Prove Normal Circle Bounds

## Description
Add a focused regression test that defines the Fill-mode grouping geometry for a
legacy circle payload before production code changes. The test must prove that
the circle contributes its enclosing square to `GroupBounds`, rather than the
centre point currently contributed by the generic fallback.

## Background
`FillGroupingHelper.prepare()` rebuilds group bounds from `LegacyItem` values
through `payload_transform.accumulate_group_bounds()`. Circle rendering already
uses a centre-plus-radius model, but the bounds helper currently has explicit
message, rectangle, and vector cases only. A circle therefore falls through to
the generic point case. This test anchors the expected untransformed geometry
so the subsequent implementation can be behavior-scoped and verified.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-29-circle-group-bounds/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-29-circle-group-bounds/implementation/plan.md` (Step 1 requirements and demo)
- `docs/plans/2026-08-29-circle-group-bounds/research/existing-code.md` (current fallback and renderer contract)
- `overlay_client/tests/test_payload_bounds.py` (existing bounds-test patterns)
- `overlay_client/payload_transform.py` (`accumulate_group_bounds()` contract)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Update only `overlay_client/tests/test_payload_bounds.py` for this task; do not change production code.
2. Construct a `LegacyItem` with `kind="circle"`, centre `(100, 200)`, and positive radius `25`, using the same test fixture style as the module.
3. Call `payload_transform.accumulate_group_bounds()` with deterministic injected dependencies and assert valid bounds of `(75, 175)` through `(125, 225)`.
4. Keep the test independent of EDMC lifecycle hooks and of a running PyQt event loop beyond the module's established test environment.
5. The new test must fail against the current production fallback, documenting the red baseline for the Step 2 implementation task.
6. Preserve all existing tests and existing uncommitted workspace changes; do not stage, commit, push, reset, stash, or switch branches.

## Dependencies
- The approved detailed design and implementation plan cited above.
- The existing `GroupBounds`, `LegacyItem`, and `accumulate_group_bounds()` test interfaces.
- A test environment with `PYQT_TESTS=1`; this test module intentionally skips when that flag is absent.

## Implementation Approach
1. Read the detailed design, current bounds test module, and bounds helper to confirm the established import and fixture patterns.
2. Add one clearly named circle-bounds test beside the current bounds tests, creating a circle item without transform metadata.
3. Accumulate its bounds and assert every min/max edge using `pytest.approx` where consistent with module conventions.
4. Run the focused test module with `PYQT_TESTS=1` and record that the new assertion fails only because circles currently use the generic centre-point fallback.

## Acceptance Criteria

1. **Circle Bounds Contract Is Explicit**
   - Given a `LegacyItem` with `kind="circle"`, `x=100`, `y=200`, and `radius=25`
   - When `accumulate_group_bounds()` processes the item without transform metadata
   - Then the test asserts valid group bounds with `min_x=75`, `min_y=175`, `max_x=125`, and `max_y=225`.

2. **Regression Is Reproducible Before the Fix**
   - Given the production bounds helper has not been changed in this task
   - When the focused test is run with `PYQT_TESTS=1`
   - Then the new circle-bounds assertion fails against the current centre-point fallback while no unrelated test behavior is changed.

3. **Focused Unit-Test Scope**
   - Given the new test runs in `overlay_client/tests/test_payload_bounds.py`
   - When it exercises the circle contract
   - Then it requires no EDMC harness lifecycle, socket, renderer, or BioScan integration setup.

## Metadata
- **Complexity**: Low
- **Labels**: Circle, Fill-Mode, Group-Bounds, Regression-Test, PyQt
- **Required Skills**: Python, pytest, geometric coordinate reasoning, regression-test design
