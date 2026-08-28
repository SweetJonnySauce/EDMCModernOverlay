# Task: Lift Bundle-Owned GNOME Presentation Runtime Profile

## Description
Move GNOME helper-presentation runtime selection from generic backend-consumer
dispatch into a narrow runtime/profile interface owned by the selected backend
bundle. This creates the seam required for a later native-GNOME fullscreen
Shell-raster route while preserving every current presentation behavior in this
task.

## Background
`consumers.py` currently recognizes raw GNOME backend and helper identities,
loads the GNOME helper-presentation runner, and turns the legacy
`GNOME_SHELL_RASTER` selection into raster runtime and PyQt-fallback flags.
That leaks compositor-specific presentation policy across the fix219 backend
boundary. The selected GNOME bundle must instead own its presentation runtime
and profile. The normal `gnome_shell_wayland` bundle may declare the future
fullscreen-raster capability, but it must keep the capability inactive in this
Step 1 increment; its ordinary presentation remains managed PyQt. The legacy
`gnome_shell_raster` identity remains compatibility/development scaffolding
and must retain its existing enabled-raster behavior, selector, override, and
status surface.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/fullscreen-shell-raster-routing.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-plan.md` (Step 1 only)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/mutter-placement-probe-and-raster-inventory.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/existing-code-and-runtime-evidence.md`
- `AGENTS.md` (fix219 boundary and required test-selection policy)

**Note:** You MUST read the detailed routing design document before beginning
implementation. Read additional references as needed for context. Historical
monitor-transfer artifacts are evidence only and are not implementation scope.

## Technical Requirements
1. Add a small, explicit presentation-runtime/profile contract under `overlay_client/backend/` and attach it to `BackendBundle` (or an equally narrow bundle-owned consumer interface). It must express helper-presentation ownership, fullscreen-raster capability/activation, and whether raster failure suppresses managed-PyQt fallback without exposing raw GNOME enums to generic dispatch.
2. Move the existing GNOME helper runner loading, helper-availability decision, legacy raster-enabled flags, and unavailable-helper result behind the GNOME bundle-owned runtime. `overlay_client/backend/consumers.py` may resolve the selected bundle and invoke its neutral runtime interface, but must not choose GNOME presentation behavior by `BackendInstance`, `HelperKind`, or direct GNOME helper-presentation imports.
3. Keep native `gnome_shell_wayland` behavior unchanged in Step 1: it owns a profile that advertises future fullscreen-raster support but passes inactive raster and inactive fallback-suppression settings to the existing runner. Do not select raster for native GNOME targets, change eligibility, send raster frames, or alter PyQt presentation.
4. Preserve `GNOME_SHELL_RASTER` compatibility/development behavior exactly: its selected bundle still enables the existing shell-raster runtime and failure-suppression flags, including its unavailable-helper fail-closed result and visible selector/override/status identity.
5. Ensure native X11 and XWayland compatibility bundles expose no GNOME presentation runtime/profile, do not import GNOME helper or raster modules, and retain their current no-runtime presentation behavior. Do not modify target discovery, payloads, helper protocol/schema, `load.py`, EDMC hooks, or fullscreen transition behavior.
6. Extend focused unit coverage in `overlay_client/tests/test_backend_consumers.py` for native GNOME, legacy raster, native X11, and XWayland bundle/profile/runtime resolution. Extend `overlay_client/tests/test_backend_architecture_boundary.py` (or its direct successor) to reject raw GNOME/raster enum dispatch and direct compositor-presentation imports in generic runtime consumers. A harness test is not required because no `load.py` or EDMC lifecycle wiring changes.

## Dependencies
- Existing `BackendBundle` composition and the explicit GNOME, native-X11, and XWayland bundle builders.
- Existing `_gnome_shell_helper_presentation` cycle behavior, including its managed-PyQt and legacy-raster flags, which must be lifted intact rather than reshaped.
- Step 2 depends on this seam; it is the only later step authorized to activate fullscreen raster for the normal native GNOME bundle.

## Implementation Approach
1. Add RED unit/architecture tests describing the bundle runtime/profile contract: native GNOME advertises but does not activate the future fullscreen-raster route; legacy raster remains active; X11/xcompat receive no GNOME runtime; and generic consumers contain no raw GNOME helper/raster dispatch.
2. Introduce the minimal runtime request/profile/result seam under `overlay_client/backend/` and bind GNOME implementations from `overlay_client/backend/bundles/gnome_shell_wayland.py`; keep compositor-specific imports and runner adaptation within that bundle-owned path.
3. Replace generic consumer predicates with selected-bundle runtime invocation, retaining the existing `BackendPresentationCycleResult` behavior and no-runtime fast path for unrelated bundles.
4. Refactor only after green tests: remove superseded generic GNOME/raster helper predicates and imports, inspect X11/xcompat imports, and confirm the normal native-GNOME runner still receives both raster-related flags as `False`.
5. Run the required focused unit suite and `git diff --check`; review the scoped diff for accidental activation, direct compositor imports outside the GNOME bundle boundary, protocol changes, or edits to excluded backends.

## Acceptance Criteria

1. **Native GNOME owns an inactive future-raster profile**
   - Given a selected `gnome_shell_wayland` backend with a healthy GNOME helper
   - When generic presentation code invokes the selected bundle runtime
   - Then unit tests prove the bundle-owned profile advertises fullscreen-raster capability while the existing runner receives inactive raster and inactive fallback-suppression flags, preserving managed-PyQt behavior

2. **Legacy raster behavior is preserved**
   - Given the selected `gnome_shell_raster` compatibility/development backend
   - When its bundle runtime runs a presentation cycle
   - Then unit tests prove it preserves the current enabled shell-raster and fallback-suppression settings, including the existing fail-closed helper-unavailable result

3. **X11 and XWayland remain isolated**
   - Given selected native-X11 and XWayland-compatibility bundles
   - When their bundles and presentation paths are resolved
   - Then unit and architecture-boundary tests prove they expose no GNOME presentation runtime and import neither GNOME helper-presentation nor raster implementation modules

4. **Generic dispatch has no compositor-specific policy**
   - Given the completed bundle runtime seam
   - When architecture-boundary tests inspect generic backend consumer source
   - Then they reject raw GNOME/raster backend or helper enum predicates and direct imports of GNOME helper-presentation implementation while permitting only neutral bundle-runtime invocation

5. **No native-GNOME raster route is enabled early**
   - Given a normal native GNOME fullscreen or windowed target in Step 1
   - When the presentation cycle is exercised through the existing fake runner
   - Then no raster frame is requested and no fullscreen PyQt fallback-suppression behavior is activated; Step 2 remains responsible for enabling the route

6. **Focused validation passes**
   - Given the completed seam and focused tests
   - When running `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_architecture_boundary.py -q` and `git diff --check`
   - Then both commands pass with no whitespace errors

## Metadata
- **Complexity**: High
- **Labels**: GNOME Wayland, Backend Boundary, Runtime Profile, fix219, Refactor, Unit Tests
- **Required Skills**: Python dataclasses and protocols, backend bundle design, dependency-boundary refactoring, pytest
