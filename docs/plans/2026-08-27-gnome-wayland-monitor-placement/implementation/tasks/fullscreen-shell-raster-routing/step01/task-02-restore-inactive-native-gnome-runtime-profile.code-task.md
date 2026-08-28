# Task: Restore the Inactive Native-GNOME Runtime Profile for Step 1

## Description
Bring the existing bundle-owned GNOME presentation runtime/profile seam back
into Step 1's behavior-preserving state. The normal
`gnome_shell_wayland` profile currently activates fullscreen Shell raster and
suppresses managed-PyQt fallback; that is Step 2 behavior and must not be
present while independently satisfying Step 1. Keep the extracted seam intact,
keep the legacy `gnome_shell_raster` compatibility/development identity active,
and make the normal native-GNOME profile advertise capability without enabling
the route.

## Background
The current source already contains the Step 1 bundle-owned runtime seam:
`BackendBundle.presentation_runtime`, the neutral runtime request/result
contracts, and `GnomeShellPresentationRuntime` in the GNOME bundle. The source
audit also found that `_NATIVE_GNOME_PRESENTATION_PROFILE` has both
`fullscreen_shell_raster_active=True` and
`suppress_managed_pyqt_fallback_on_shell_raster_failure=True`, and the focused
consumer test expects those active values. This violates the approved Step 1
acceptance criterion that native GNOME must not request raster frames or
suppress its managed-PyQt path until Step 2. This is a remediation task for the
current source state; do not recreate the runtime seam or alter the historical
Step 1 task artifact.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/fullscreen-shell-raster-routing.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-plan.md` (Step 1 only)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-orchestration-prompt.md` (Step 1 guardrails and validation)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/mutter-placement-probe-and-raster-inventory.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/existing-code-and-runtime-evidence.md`
- `AGENTS.md` (fix219 boundary and required test-selection policy)

**Note:** You MUST read the detailed routing design before beginning
implementation. Standing user approval in the orchestration request authorizes
this generated in-scope task; no per-task approval gate is required. Historical
monitor-transfer artifacts are evidence only and are not implementation scope.

## Technical Requirements
1. Retain the bundle-owned `PresentationRuntimeBackend` seam and neutral invocation from `overlay_client/backend/consumers.py`; generic follow/runtime code must not select compositor presentation behavior from raw GNOME/helper/backend enums or import compositor-specific presentation implementations.
2. Change only the normal `gnome_shell_wayland` runtime profile so it declares `owns_helper_presentation=True` and `supports_fullscreen_shell_raster=True`, but passes inactive raster and inactive fullscreen fallback-suppression settings to the existing runner.
3. Preserve the `GNOME_SHELL_RASTER` compatibility/development identity exactly: its selector, override/status surface, active Shell-raster flag, fallback-suppression flag, and unavailable-helper fail-closed result must remain available and unchanged.
4. Do not modify the public helper protocol/schema, target discovery, payload semantics, extension source, `load.py`, EDMC hooks, X11, or XWayland compatibility behavior. Native X11 and XWayland must continue to expose no GNOME presentation runtime and import no GNOME helper/raster implementation.
5. Update focused unit tests in `overlay_client/tests/test_backend_consumers.py` to prove the normal native-GNOME runner receives false for both raster-related settings while legacy raster still receives true for both. Retain or extend `overlay_client/tests/test_backend_architecture_boundary.py` coverage for generic-dispatch and X11/xcompat isolation. Test type is **unit**: this is deterministic bundle/profile selection with injected runners and touches no `load.py` or EDMC lifecycle hook, so no harness test is required.
6. Run the required validation exactly: `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_architecture_boundary.py -q`, followed by `git diff --check`.

## Dependencies
- The existing Step 1 runtime/profile extraction in `overlay_client/backend/presentation_runtime.py`, `overlay_client/backend/contracts.py`, `overlay_client/backend/bundles/gnome_shell_wayland.py`, and `overlay_client/backend/consumers.py`.
- The existing injected-runner tests in `overlay_client/tests/test_backend_consumers.py` and source-boundary tests in `overlay_client/tests/test_backend_architecture_boundary.py`.
- Step 2 depends on this correction: only after Step 1 acceptance evidence is complete may a fresh Step 2 task deliberately activate the normal native-GNOME profile for established eligible fullscreen targets.

## Implementation Approach
1. Start RED by changing/adding focused unit assertions that distinguish the normal native-GNOME profile (capable but inactive) from the active legacy raster profile, including exact forwarded runner flags.
2. Make the minimal profile-only production change under the GNOME bundle so the normal native bundle forwards inactive raster and inactive fallback-suppression settings; do not reshape the generic seam or runner.
3. Run the focused architecture and consumer tests, then inspect the scoped diff to prove no direct GNOME policy reappeared in generic consumers and no X11/xcompat source changed.
4. Record RED/GREEN/REFACTOR outcomes, exact command results, source-level acceptance evidence, scoped-diff review, and the reason no harness test applies in the task's fresh code-assist documentation and handoff.

## Acceptance Criteria

1. **Native GNOME remains capable but inactive in Step 1**
   - Given the selected `gnome_shell_wayland` backend and a healthy GNOME helper
   - When generic presentation code invokes the selected bundle runtime with an injected runner
   - Then the profile advertises fullscreen Shell-raster capability, but the runner receives `shell_raster_runtime_enabled=False` and `suppress_pyqt_fallback_on_shell_raster_failure=False`, preserving managed-PyQt behavior and requesting no raster frame

2. **Legacy raster compatibility behavior remains active**
   - Given the selected `gnome_shell_raster` compatibility/development backend and a healthy GNOME helper
   - When its bundle runtime invokes the injected presentation runner
   - Then the runner still receives active Shell-raster and fallback-suppression settings, and the existing unavailable-helper fail-closed behavior remains covered

3. **fix219 and X11/xcompat isolation are retained**
   - Given the completed profile correction
   - When focused architecture and bundle-resolution tests inspect generic consumers and resolve native X11 and XWayland bundles
   - Then generic runtime dispatch contains no raw GNOME/helper/raster presentation policy, while native X11 and XWayland expose no GNOME runtime and import neither GNOME helper-presentation nor raster modules

4. **No early native-GNOME routing or protocol change occurs**
   - Given a normal native-GNOME fullscreen or windowed target during Step 1
   - When its presentation cycle is exercised through the injected runner and the scoped diff is reviewed
   - Then Step 1 makes no raster request, activates no fullscreen PyQt-fallback suppression, changes no target/payload/helper protocol behavior, and leaves Step 2 as the first authorized native-GNOME activation increment

5. **Focused unit validation passes**
   - Given the corrected profile and updated focused tests
   - When running `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_architecture_boundary.py -q` and `git diff --check`
   - Then both commands pass, and the implementation report records exact results and the unit-only test selection rationale

## Metadata
- **Complexity**: Medium
- **Labels**: GNOME Wayland, Backend Boundary, Runtime Profile, fix219, Step 1 Remediation, Unit Tests
- **Required Skills**: Python dataclasses and protocols, backend bundle design, dependency-boundary refactoring, pytest
