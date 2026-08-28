# Task: Enable Native GNOME Fullscreen Shell-Raster Route

## Description
Activate the selected `gnome_shell_wayland` bundle's existing real-content
GNOME Shell-raster presenter for eligible fullscreen, full-monitor targets.
Keep managed PyQt presentation for windowed targets and fail closed if a
fullscreen raster frame cannot be built or proven. This implements the
backend-owned policy capability prepared in Step 1 without changing public
helper protocol, target discovery, or X11/XWayland behavior.

## Background
Mutter can report successful placement operations while leaving an externally
managed PyQt overlay on the prior monitor. The project already has a validated
Shell-raster transport: the render surface exports cropped, real overlay
content and the GNOME helper presents it through a non-reactive actor above the
target. Step 1 moved presenter policy behind the selected bundle runtime, but
the normal native-GNOME profile intentionally left raster disabled. This task
enables that profile only when the existing strict eligibility rules prove that
the selected native-GNOME target is fullscreen and fills its monitor.

The legacy `gnome_shell_raster` identity remains compatibility/development
scaffolding. Native X11 and XWayland compatibility remain isolated. Later
Step 3 owns any additional transition and lifecycle hardening; do not broaden
this task into coordinator redesign, monitor-transfer retries, coordinate
heuristics, static proof-frame production use, or a fullscreen PyQt fallback.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/fullscreen-shell-raster-routing.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-plan.md` (Step 2 only)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-orchestration-prompt.md` (Step 2 guardrails and validation)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/mutter-placement-probe-and-raster-inventory.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/existing-code-and-runtime-evidence.md`
- `AGENTS.md` (fix219 boundary and required test-selection policy)

**Note:** You MUST read the detailed routing design document before beginning
implementation. Read additional references as needed for context. Historical
monitor-transfer artifacts are evidence only and are not implementation scope.

## Technical Requirements
1. Activate `fullscreen_raster_enabled` and `suppress_managed_fallback_on_raster_failure` only in the selected native `gnome_shell_wayland` bundle runtime profile; preserve the Step 1 neutral generic consumer boundary so generic code still supplies neutral callbacks and does not branch on GNOME/helper/backend enums.
2. Reuse `_build_backend_shell_raster_content_frame` and the existing cropped real-content `gnome_shell_raster_frame` request path for a healthy, visible, non-minimized, eligible fullscreen/full-monitor native-GNOME target. Do not enable static proof-frame production behavior or alter the DBus helper protocol/schema.
3. Preserve the existing strict raster eligibility checks. Windowed, partial-screen, malformed-rectangle, ambiguous, unavailable-helper, or otherwise ineligible targets must remain on the existing managed-PyQt path only when that path is safe for their non-fullscreen state; they must not submit a raster frame.
4. For an eligible fullscreen target, a frame-provider exception/failure, no-visible-content result, invalid frame validation result, or unproven raster result must clear or suppress the presentation using the existing fail-closed result path. It must not attach or reveal the known-misplaced PyQt fullscreen surface as fallback.
5. Use the existing presentation diagnostics surface to record a concise presenter mode and degradation reason. Do not add live probes, sleeps, monitor-placement variants, coordinate guesses, target-discovery changes, payload changes, `load.py` changes, or EDMC lifecycle wiring.
6. Preserve `GNOME_SHELL_RASTER` compatibility/development selector, override, status identity, and existing behavior. Native X11 and XWayland compatibility bundles must receive no GNOME helper/raster imports or runtime behavior.
7. Select unit tests before implementation: this task changes injected backend/runtime policy and helper-cycle behavior but does not touch `load.py`, startup/shutdown hooks, or EDMC lifecycle wiring, so update focused unit tests only; a harness test is not required. Record this choice, files changed, exact commands, and outcomes in the code-assist artifact, plan, dashboard, and required handoff.

## Dependencies
- Step 1 bundle-owned presentation runtime/profile seam and its neutral frame-provider callback contract.
- Existing `_gnome_shell_helper_presentation` eligibility, fail-closed, diagnostics, and helper-cycle behavior.
- Existing render-surface real-content frame provider and `shell_raster_frame.py` validation/cache constraints.
- Existing focused tests in `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, `overlay_client/tests/test_shell_raster_frame.py`, and `overlay_client/tests/test_repaint_debounce.py`.

## Implementation Approach
1. Start RED by extending the focused helper-runtime tests to select the normal native-GNOME bundle and demonstrate: an eligible fullscreen/full-monitor target emits a real-content `gnome_shell_raster_frame`; windowed and ineligible fullscreen targets emit no raster frame and retain their safe managed-PyQt behavior; and frame-provider/no-visible-content failures clear or degrade without fullscreen PyQt fallback.
2. Make the smallest bundle-owned profile/configuration change needed to activate the existing bridge and fallback suppression for native GNOME. Keep compositor-specific behavior inside the GNOME backend-owned runtime path; do not move it back into generic consumers.
3. Reuse the existing content-frame builder and request validation path intact. Feed it through the existing neutral provider callback and preserve cache, crop, checksum, visibility, helper-health, and eligibility guards.
4. Make GREEN by exercising the real native-GNOME selected-backend route and all exclusions/failure cases. Confirm diagnostics identify the selected presenter/degradation reason without a protocol change.
5. REFACTOR only for clarity after GREEN. Review the scoped diff for accidental static proof-frame activation, any fullscreen PyQt fallback, direct GNOME presentation imports or raw enum dispatch in generic consumers, and any change to X11/xcompat or legacy-raster scaffolding. Run the focused suite and `git diff --check`.

## Acceptance Criteria

1. **Eligible Native-GNOME Fullscreen Uses Real Content Raster**
   - Given a healthy selected `gnome_shell_wayland` backend and a visible, non-minimized fullscreen target whose target and request content rectangles match its monitor under the existing tolerance
   - When the selected bundle runtime runs a presentation cycle with a real-content frame provider
   - Then it submits a validated `gnome_shell_raster_frame` request made from actual cropped overlay content, records the raster presenter mode, and keeps managed PyQt suppressed for that fullscreen cycle

2. **Windowed and Ineligible Targets Remain Non-Raster**
   - Given the selected native-GNOME bundle has a windowed, partial-screen, ambiguous, malformed, or otherwise ineligible target
   - When the bundle runtime processes its presentation cycle
   - Then it sends no raster-frame request and preserves the existing safe managed-PyQt handling for genuinely windowed targets without changing target discovery or geometry semantics

3. **Fullscreen Raster Failure Fails Closed**
   - Given an otherwise eligible native-GNOME fullscreen target
   - When the real-content provider fails, produces no visible content, returns an invalid frame, or the raster request cannot be proven
   - Then the presentation result clears or suppresses the Shell actor, emits an actionable degraded reason through existing diagnostics, and does not attach, map, or expose a PyQt fullscreen fallback

4. **Backend Boundary and Compatibility Are Preserved**
   - Given the completed native-GNOME profile activation
   - When generic consumers and all backend bundles are inspected and exercised by focused tests
   - Then generic runtime code still delegates only through the selected bundle's neutral interface, native X11 and XWayland compatibility import and receive no GNOME runtime behavior, and the legacy `gnome_shell_raster` selector/override/status behavior remains intact

5. **Focused Unit Validation Passes**
   - Given the scoped implementation and updated unit tests
   - When running `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_shell_raster_frame.py overlay_client/tests/test_repaint_debounce.py -q` and `git diff --check`
   - Then both commands pass, the code-assist records exact results and test-file changes, and no lifecycle harness test is claimed or required because `load.py` and EDMC hook flow remain untouched

6. **Step Demonstration Is Reproducible**
   - Given controlled helper-runtime test inputs for the same target
   - When the target is first fullscreen/full-monitor and then made windowed
   - Then the first cycle records an actual-content raster request and the second records the ordinary managed-PyQt attach path with no stale or duplicate raster request

## Metadata
- **Complexity**: High
- **Labels**: GNOME Wayland, Shell Raster, Fullscreen, Fail Closed, Backend Boundary, fix219, Unit Tests
- **Required Skills**: Python backend-runtime design, GNOME helper presentation, PyQt render-surface integration, pytest, failure-mode testing
