# Shape Stroke Thickness: Progress

## Setup

- Mode: auto; user supplied the approved implementation prompt and prohibited
  commits, pushes, version changes, and unrelated edits.
- Documentation location: this plan directory, because `.agents` is read-only
  in this workspace.
- Existing circle implementation changes are deliberately retained.

## Checklist

- [x] Create implementation artifacts and inspect repository guidance.
- [x] Document requirements, dependency map, risks, and test-type choice.
- [x] Add all tests and capture expected failures.
- [x] Implement helper/ingress/processor/render changes.
- [x] Update public documentation.
- [x] Run focused and full validation.
- [x] Record completion evidence and scoped review.

## TDD Log

| Cycle | Status | Notes |
| --- | --- | --- |
| Plan | Complete | Omitted rectangle default remains an isolated physical-width path; explicit widths are logical and scaled at the shared bounded-shape boundary. |
| RED | Complete | Focused GUI-enabled collection failed as expected because `_StrokeWidthSpec` is not implemented. |
| GREEN | Complete | The full focused helper/processor/harness/PyQt suite passed after implementation. |

## Validation Evidence

| Command | Result |
| --- | --- |
| `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest tests/test_edmcoverlay_shapes.py tests/test_legacy_processor.py tests/test_harness_legacy_tcp_ingestion.py overlay_client/tests/test_render_surface_mixin.py -q` | Expected RED: collection could not import `_StrokeWidthSpec`. |
| `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest tests/test_edmcoverlay_shapes.py tests/test_legacy_processor.py tests/test_harness_legacy_tcp_ingestion.py overlay_client/tests/test_render_surface_mixin.py -q` | 79 passed. |
| `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest tests/test_edmcoverlay_shapes.py tests/test_legacy_processor.py tests/test_harness_legacy_tcp_ingestion.py overlay_client/tests/test_paint_commands.py overlay_client/tests/test_render_surface_mixin.py -q` | 88 passed. |
| `overlay_client/.venv/bin/python scripts/check_edmc_python.py` | Passed; Python 3.12.3 64-bit meets the configured minimum. The tool warned that the preferred EDMC baseline architecture is 32-bit. |
| `make check` | Passed: Ruff, mypy (91 source files), and GUI-enabled pytest (775 passed, 21 skipped). |
| `make test` | Passed: GUI-enabled pytest (775 passed, 21 skipped). |
| `git diff --check` | Passed after correcting one documentation trailing-space finding. |

## Completion Notes

- Explicit `circle` and `rect` widths now remain logical legacy-canvas units
  until the shared bounded-shape rendering boundary, which scales, rounds, and
  clamps them without mutating the input pen.
- Rectangles that omit thickness continue to omit that key end-to-end and use
  their existing client-configured `legacy_rect` physical width.
- No release, version change, commit, or push was performed.
- Remaining release-only checks: exercise the change in the actual Python
  3.10.3 32-bit Windows EDMC runtime and review EDMC releases/discussions before
  shipping.
