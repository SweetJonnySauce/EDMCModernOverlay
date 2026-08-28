# Step 3.1 Handoff

Status: Completed; neutral runtime transport is implemented and does not activate GNOME helper behavior.

Files changed: `overlay_client/backend/presentation_runtime.py`, `overlay_client/backend/consumers.py`, `overlay_client/follow_surface.py`, `overlay_client/setup_surface.py`, `overlay_client/tests/test_backend_consumers.py`, `overlay_client/tests/test_follow_surface_mixin.py`, `overlay_client/tests/test_backend_architecture_boundary.py`, and this task's `context.md`, `plan.md`, `progress.md`, and `handoff.md`.

Validation commands/results: RED command `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py -q` produced the expected 5 failures; GREEN rerun passed `82 passed`; headless command `source overlay_client/.venv/bin/activate && QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_setup_surface.py -q` passed `105 passed`; focused `ruff check` and `git diff --check` passed.

Decisions: `BackendPresentationRuntimeRequest.content_visibility` uses only `BackendPresentationContentVisibility`; the follow surface sends retained intent on the next cycle, updates it solely from the existing policy decision, resets it to `visible` on hard hide/reset, and requests exactly one ordinary follow refresh only for changed shown-content intent outside the existing managed-windowed remap flow.

Risks: No GNOME bundle/helper protocol or actor operation is wired yet, so the user preference remains behaviorally unchanged for native Shell raster until Step 3 Task 2; live GNOME/Mutter validation remains deferred. The GUI-enabled test command requires `QT_QPA_PLATFORM=offscreen` in this headless environment.

Next exact action: Independently review this neutral diff and handoff, then execute the separate Step 3 Task 2 GNOME-owned capability wiring context; do not commit, stage, reload GNOME Shell, or run live D-Bus actions.
