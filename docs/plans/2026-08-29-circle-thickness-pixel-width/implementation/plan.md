# Implementation plan: pixel-width circle strokes

## Checklist

- [x] Step 1: Prove the separate rectangle and circle contracts.
- [x] Step 2: Add the explicit pixel-width policy and wire circles to it.
- [x] Step 3: Run focused and repository-wide validation.

## Phase status

| Phase | Stage | Status |
| --- | --- | --- |
| 1 | 1.1 Contract tests for unscaled circles and scaled rectangles | Completed |
| 2 | 2.1 Add and wire explicit pixel stroke policy | Completed |
| 3 | 3.1 Focused and full validation | Completed |

## Step 1: Prove the separate rectangle and circle contracts

**Objective:** Replace the shared shape scaling assertion with focused tests
that encode the intended per-shape policies before runtime behavior changes.

**Guidance:** In `overlay_client/tests/test_render_surface_mixin.py`, retain
the existing rectangle scale matrix for `thickness=2`. Add a circle scale
matrix using `thickness=1` and expected pen width 1 at scales 0.5, 1.0, and
2.0. Add a non-unit circle case (for example `thickness=3`, scale 2.0) with
expected width 3. The circle assertions should initially fail under current
production code; rectangle assertions must pass.

**Tests:**
`PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py -k thickness`

**Integration:** This establishes the public rendering contract at the
existing `_build_circle_command()` seam without changing payload processing or
paint commands.

**Demo:** At the test level, scale 2.0 shows the distinction: rectangle
`thickness=2` yields 4 pixels while circle `thickness=1` must yield 1.

## Step 2: Add and wire explicit pixel stroke policy

**Objective:** Make circles resolve supplied thickness as a stable Qt logical
pixel width while preserving rectangle scaling.

**Guidance:** Extend `_StrokeWidthSpec` with a clearly named explicit pixel
field. In `_build_bounded_shape_command()`, resolve pixel width without the
group scale and preserve the current clamp/copy/set-width behavior. Keep the
logical branch intact. Change only `_build_circle_command()` to supply the
payload thickness through the new pixel field. Do not alter geometry,
transforms, public API validation, or line-width config.

**Tests:** Rerun the focused thickness filter and then the entire
`test_render_surface_mixin.py` module with `PYQT_TESTS=1`; both must pass.

**Integration:** Circles still use the shared bounded-shape painter, so
opacity and Qt drawing remain common. Only the width-resolution policy differs.

**Demo:** On a 1920×1080 Fill overlay, a circle payload with `thickness=1`
draws using a one-pixel Qt pen and visually matches a legacy vector whose
`vector_line` config is 1.

## Step 3: Validate no wider regression

**Objective:** Verify shape ingestion, circle rendering, and the project gate
without expanding scope.

**Guidance:** Review the diff to confirm it is limited to stroke policy and
tests. Preserve prior committed circle geometry/grouping behavior and avoid
changing payload inspector code.

**Tests:**

```bash
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
  overlay_client/tests/test_render_surface_mixin.py \
  tests/test_legacy_processor.py \
  tests/test_edmcoverlay_shapes.py
make check
git diff --check
```

**Integration:** Confirms the legacy processor’s required positive thickness,
the circle command, and renderer remain compatible.

**Demo:** Automated validation passes; manual overlay comparison shows the new
circle ring as thin as the legacy-vector ring.
