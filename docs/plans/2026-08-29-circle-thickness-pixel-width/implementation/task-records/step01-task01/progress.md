# Step 1 progress

- [x] Read the approved design, plan, orchestration prompt, task, and governing instructions.
- [x] Inspected the existing bounded-shape test and renderer seam.
- [x] Replaced the shared test with separate rectangle and circle contracts.
- [x] Run the required focused test once and record its expected RED result.
- [x] Run `git diff --check`.

## Decision

The circle test uses a single three-column matrix so the three unit-width
scales and one non-unit case share the same command-construction seam and
join-style assertion.

## Required RED evidence

Command run exactly once:

```text
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py -k thickness
```

Result: exit 1; `2 failed, 7 passed, 17 deselected in 0.20s`.

The two expected failures are both at group scale `2.0` in
`test_explicit_circle_thickness_uses_unscaled_logical_pixels`:

- `thickness=1`: actual pen width `2`, expected `1`.
- `thickness=3`: actual pen width `6`, expected `3`.

The unit-circle cases at scales `0.5` and `1.0` passed because the existing
logical-width calculation rounds/clamps to one pixel there. The rectangle
matrix passed, preserving its scale-aware contract.

## Diff integrity

`git diff --check` passed. The scoped diff contains only the intended test
file and this task record; runtime source was not edited.
