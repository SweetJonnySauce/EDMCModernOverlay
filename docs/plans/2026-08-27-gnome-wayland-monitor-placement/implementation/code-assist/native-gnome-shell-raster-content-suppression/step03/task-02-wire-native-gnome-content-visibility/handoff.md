# Step 3.2 Handoff

Status: Completed — awaiting the orchestration main-context review; no commit, staging, D-Bus call, extension reload, or live validation occurred.

Files changed: `overlay_client/backend/bundles/gnome_shell_wayland.py`, `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`, `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, and this task's context, plan, progress, validation log, and handoff artifacts.

Validation commands/results: RED `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py -k 'content_visibility' -q` failed as expected before wiring; focused rerun passed `2 passed`; `source overlay_client/.venv/bin/activate && QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_presentation_transition.py overlay_client/tests/test_backend_architecture_boundary.py -q` passed `228 passed`; focused Ruff and `git diff --check` passed.

Decisions: The GNOME runtime forwards the neutral value to its bundle-owned runner. The runner resolves the helper protocol value only after health validation; supported requests send `visible` or `suppressed`, while an unsupported suppressed request omits the field and records stable-visible fallback metadata. Fullscreen actor continuity remains independently calculated. The existing frame signature already includes the optional wire value, and the runtime test proves a supported visible-to-suppressed change is not cache-skipped.

Risks: Live Mutter/GNOME actor behavior remains untested and must remain user-gated. Existing helper-unhealthy/hard-lifecycle handling intentionally remains unchanged; an unreachable helper cannot safely receive a new content request. No project-wide `make` gates were run because they are Step 4 validation.

Next exact action: Run the orchestration main-context Step 3 review, inspect the combined Step 3.1/3.2 diff and handoffs, then update the dashboard to Step 3 complete only if that review passes; do not deploy or live-test the extension without explicit user approval.

