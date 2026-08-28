# Progress: Native GNOME Helper-Unavailable Fallback

## Setup

- [x] Read code-assist workflow, `AGENTS.md`, approved task/design/plans,
  orchestration prompt, fullscreen routing records, iteration checklist, and
  focused source/tests.
- [x] Created this isolated artifact directory and `logs/`.
- [x] Chose unit tests; no harness is required because no lifecycle wiring or
  `load.py` path changes.
- [x] Capture RED evidence before production edits.

## TDD ledger

| Cycle | Status | Evidence |
| --- | --- | --- |
| RED | Completed | Focused backend-consumer selection: 3 failed as expected: missing profile policy on both profiles and native helper loss returned a non-`None` handled cycle. |
| GREEN | Completed | Added the neutral profile field; native is false, legacy raster true; the missing-helper branch uses only this field. Targeted test rerun: 3 passed. |
| REFACTOR | Completed | Kept the minimal readable branch and expanded profile docstring; no further refactor was warranted. Focused architecture coverage passed. |

## Command record

| Command | Outcome |
| --- | --- |
| `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_consumers.py -q -k 'native_gnome_bundle_owns_an_active_fullscreen_shell_raster_profile_with_nonterminal_helper_loss or legacy_shell_raster_bundle_owns_an_active_shell_raster_profile or selected_native_gnome_without_helper_falls_through_to_legacy_follow'` | RED: 3 failed as expected. |
| Same focused selection after production edit | GREEN: 3 passed, 37 deselected. |
| `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_architecture_boundary.py -q` | Passed: 157 passed. |
| `overlay_client/.venv/bin/python -m ruff check overlay_client/backend/presentation_runtime.py overlay_client/backend/bundles/gnome_shell_wayland.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_consumers.py` | Passed: all checks passed. |
| `git diff --check` | Passed. |
| `make PYTHON=overlay_client/.venv/bin/python check` | Code assertions passed: 1,649 passed, 21 skipped. Five errors are sandbox-blocked `127.0.0.1:0` socket fixture setup in `tests/test_harness_pressure_ab_snapshot.py`; no task assertion failure remains. |

Detailed outputs are in `logs/`.

## Commit

No staging or commit: main thread owns Git reconciliation.
