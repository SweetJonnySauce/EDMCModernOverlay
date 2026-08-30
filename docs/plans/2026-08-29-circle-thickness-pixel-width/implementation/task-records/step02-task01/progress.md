# Step 2 progress

- [x] Read the approved design, plan, orchestration prompt, task, Step 1 red
  evidence, and governing instructions.
- [x] Confirmed this is a unit-test change at the bounded-shape construction
  seam; no harness test is required.
- [x] Added the separate explicit pixel-width policy and wired only circles to
  it.
- [x] Run the required focused and full module tests.
- [x] Run `git diff --check` and review the scoped diff.

## Decision

`explicit_pixel_width` is separate from `default_pixel_width`: the former is a
caller-supplied circle thickness while the latter remains a renderer default.
The pixel branch precedes the existing logical branch, so the rect path is
unchanged.

## Git safety

No Git index or history operation has been performed.

## Validation evidence

```text
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py -k thickness
9 passed, 17 deselected in 0.13s

PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py
26 passed in 0.17s

git diff --check
passed (no output)
```

## Scoped-diff review

The runtime diff adds only `explicit_pixel_width`, resolves it without group
scale before the unchanged logical/default branches, and passes that policy
only from `_build_circle_command()`. The retained Step 1 test diff separately
proves circle pixel widths and rectangle scale-aware widths. No unrelated
source, test, or Git-index change was made.
