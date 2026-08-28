# Task: Activate Native GNOME Fullscreen Real-Content Raster Route

## Description
Activate fullscreen Shell-raster presentation and fail-closed fallback
suppression in the selected `gnome_shell_wayland` bundle profile. This restores
the approved Step 2 behavior after Step 1 deliberately left the native profile
capable but inactive. Reuse the existing real-content frame-provider route;
do not duplicate or redesign the raster bridge.

## Background
The bundle-owned runtime seam is present and the legacy
`gnome_shell_raster` compatibility/development identity remains active. The
normal native GNOME profile currently forwards both raster activation and
fullscreen fallback suppression as `False`. As a result, the existing
selected-native real-content contract fails: an eligible fullscreen target
falls through to managed PyQt rather than submitting a
`gnome_shell_raster_frame`. Mutter has been shown to keep that external PyQt
surface on the wrong monitor, so the fullscreen route must instead use the
existing compositor-owned real-content actor and fail closed if it cannot be
proven.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/fullscreen-shell-raster-routing.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-plan.md` (Step 2)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-orchestration-prompt.md` (Step 2 guardrails)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/mutter-placement-probe-and-raster-inventory.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/existing-code-and-runtime-evidence.md`
- `AGENTS.md` (fix219 boundary and test-type policy)

**Note:** You MUST read the detailed routing design document before beginning
implementation. Historical Step 2 task `task-01-enable-native-gnome-fullscreen-shell-raster-route.code-task.md` is evidence only; do not overwrite it or trust its completion claim.

## Technical Requirements
1. Change only the selected normal `gnome_shell_wayland` bundle runtime profile so `fullscreen_shell_raster_active` and `suppress_managed_pyqt_fallback_on_shell_raster_failure` are enabled; keep the generic consumer interface neutral and retain the legacy `GNOME_SHELL_RASTER` identity, override, and status surface unchanged.
2. Reuse the existing neutral raster-frame-provider callback and `_build_backend_shell_raster_content_frame` flow so an eligible fullscreen/full-monitor native-GNOME target sends a real-content, cropped, validated `gnome_shell_raster_frame`. Static proof frames must remain development-only and must not be selected in production.
3. Keep existing strict eligibility intact. Windowed, partial-screen, malformed-rectangle, ambiguous, unhealthy-helper, minimized, invisible, or otherwise ineligible targets must send no raster frame and remain on managed PyQt only when that non-fullscreen path is safe.
4. An eligible fullscreen target with a provider exception/failure, no visible content, invalid frame, or unproven raster response must clear/suppress presentation with existing diagnostics. It must not attach, map, or reveal a fullscreen PyQt fallback.
5. Preserve the existing diagnostics surface and helper protocol/schema. Do not change target discovery, payload semantics, `load.py`, EDMC hooks, X11/xcompat bundles, sleeps, coordinate guesses, or monitor-transfer fallback behavior.
6. Explicitly select unit tests: this task changes bundle-owned runtime policy and injected callback behavior only, with no `load.py`, plugin startup/shutdown, or EDMC lifecycle change. Add/update focused unit tests; no harness test is required.

## Dependencies
- Step 1 bundle-owned `BackendPresentationRuntimeProfile` seam and generic neutral callback transport.
- Existing helper-cycle eligibility, real-content frame validation, clear/degrade path, and diagnostics in `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`.
- Existing real-content render-surface provider and raster-frame cache/validation implementation.
- Existing focused tests in `overlay_client/tests/test_backend_consumers.py`, `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, `overlay_client/tests/test_shell_raster_frame.py`, and `overlay_client/tests/test_repaint_debounce.py`.

## Implementation Approach
1. Start RED by updating/adding selected-native profile and runtime-cycle assertions that distinguish active native fullscreen raster from the legacy compatibility identity. Confirm the current native real-content test fails before the profile change.
2. Make the smallest profile-only activation change in the GNOME bundle. Do not move any compositor policy into `consumers.py` or modify the frame builder/helper protocol.
3. Make GREEN with focused native selected-backend tests: eligible fullscreen submits real content; windowed/partial/ambiguous cases submit no raster; provider/no-visible-content cases clear/degrade while managed fullscreen PyQt stays suppressed.
4. REFACTOR only for naming or test clarity. Review the scoped diff for static proof-frame production use, altered diagnostics schema, generic raw enum/helper dispatch, any X11/xcompat import/behavior change, or an unsafe fullscreen fallback.

## Acceptance Criteria

1. **Eligible Native Fullscreen Uses a Real-Content Shell Raster**
   - Given a healthy selected `gnome_shell_wayland` runtime and a visible, non-minimized fullscreen target whose target/request content rectangles match its monitor within the established tolerance
   - When its bundle runtime receives the existing real-content frame provider for a presentation cycle
   - Then it submits a validated cropped `gnome_shell_raster_frame`, identifies the raster presenter through the existing diagnostics, and does not map managed PyQt for that fullscreen cycle

2. **Windowed, Partial, and Ambiguous Targets Remain Managed PyQt**
   - Given the selected native GNOME bundle sees a windowed, partial-screen, malformed, or ambiguous target
   - When it processes the presentation cycle
   - Then it sends no raster frame and preserves the existing safe managed-PyQt behavior only for a genuinely non-fullscreen target, without changing target discovery or geometry semantics

3. **Fullscreen Raster Failure Fails Closed**
   - Given an otherwise eligible selected native-GNOME fullscreen target
   - When the frame provider fails or returns no visible content, frame validation rejects it, or the helper cannot prove the raster result
   - Then the existing clear/degraded route suppresses the actor and fullscreen presentation, reports its existing actionable reason, and does not attach, map, or expose a PyQt fullscreen fallback

4. **Protocol and Backend Boundary Stay Intact**
   - Given the native profile is active
   - When the changed source and focused architecture tests are inspected
   - Then `consumers.py` remains generic and neutral, diagnostics/helper protocol remain unchanged, `native_x11` and `xwayland_compat` receive no GNOME helper/raster imports or behavior, and the legacy `GNOME_SHELL_RASTER` selector/override/status behavior remains available

5. **Focused Unit Validation Passes**
   - Given the scoped implementation and its updated unit coverage
   - When running `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_shell_raster_frame.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_architecture_boundary.py -q` and `git diff --check`
   - Then both commands pass, all changed test files and exact outcomes are recorded, and no lifecycle harness is claimed because `load.py` and EDMC hook flow are untouched

6. **Step Demonstration Is Reproducible**
   - Given controlled helper-runtime inputs for the same selected native GNOME target
   - When it is first fullscreen/full-monitor and then windowed, and separately when fullscreen content export fails
   - Then the first cycle yields an actual-content raster request, the second yields the ordinary managed-PyQt attach only after any existing required clear, and the failure yields clear/suppression with neither actor nor fullscreen PyQt visible

## Metadata
- **Complexity**: Medium
- **Labels**: GNOME Wayland, Shell Raster, Fullscreen, Fail Closed, fix219, Unit Tests
- **Required Skills**: Python backend-runtime design, GNOME helper presentation, PyQt render-surface integration, pytest, source-contract testing
