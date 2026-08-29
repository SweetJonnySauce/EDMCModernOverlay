# Explicit Rectangle Miter Joins: Progress

## Checklist

- [x] Create documentation artifacts and inspect the render path.
- [x] Add a failing explicit/omitted join-style unit test.
- [x] Implement the explicit-rectangle-only miter join.
- [x] Run focused and GUI-enabled validation.
- [x] Record final results; do not commit or push.

## Setup Notes

- Mode: auto. The user requested the change directly, so no additional
  confirmation is needed.
- Documentation path was created successfully.
- Existing uncommitted circle-related work is preserved. No commit, push,
  version change, or unrelated configuration change is authorized.

## TDD Evidence

| Step | Result |
| --- | --- |
| Explore | `QPen(QColor)` defaults to `BevelJoin`; rectangle commands do not currently override it. |
| RED | `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py -k 'explicit_rect_thickness_uses_miter_join' -q` — failed as expected: the explicit rectangle pen was `BevelJoin`. |
| GREEN | The same focused test plus scaling and omitted-thickness coverage — 8 passed. |
| GUI-enabled renderer coverage | `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py overlay_client/tests/test_paint_commands.py -q` — 34 passed. |
| Lint | `overlay_client/.venv/bin/python -m ruff check overlay_client/render_surface.py overlay_client/tests/test_render_surface_mixin.py` — passed. |
| EDMC Python baseline | `python3 scripts/check_edmc_python.py` — passed with the expected 64-bit development-host warning. (`python scripts/check_edmc_python.py` could not run because this environment has no `python` executable.) |
| Project gate | `make check` — Ruff and mypy passed; GUI-enabled pytest: 780 passed, 21 skipped. |
| Diff hygiene | `git diff --check` — passed. |

## Result

- Explicit-thickness rectangles now use `MiterJoin`, producing sharp square
  corners after the existing physical-pixel stroke-width resolution.
- Omitted-thickness rectangles retain the default `BevelJoin` and their
  existing unscaled legacy stroke behavior.
- The rectangle pen is constructed per command and then copied by the existing
  explicit-width resolver; no cached/shared pen is mutated.
- Circles remain on their existing default join style, covered by the shared
  explicit-thickness scale test.
- No commit, push, release, version, or unrelated configuration change was
  made.
