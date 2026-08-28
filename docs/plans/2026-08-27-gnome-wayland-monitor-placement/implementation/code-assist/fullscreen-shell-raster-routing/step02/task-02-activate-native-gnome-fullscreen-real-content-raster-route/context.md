# Context: Activate native GNOME fullscreen real-content raster route

## Task and scope

Task file: `implementation/tasks/fullscreen-shell-raster-routing/step02/task-02-activate-native-gnome-fullscreen-real-content-raster-route.code-task.md`.

This is a unit-test-only Step 2 policy activation. It must change only the normal `gnome_shell_wayland` bundle runtime profile so eligible fullscreen presentation reaches the existing real-content raster provider and suppresses an unsafe managed-PyQt fullscreen fallback. The legacy `GNOME_SHELL_RASTER` profile remains active and unchanged. `load.py`, EDMC lifecycle wiring, helper protocol/schema, target discovery, X11, and xcompat are outside scope.

## Existing documentation

- `AGENTS.md`: preserve fix219 boundary; choose unit tests for this pure bundle/runtime policy change; record exact validation.
- Routing design and Step 2 plan: full-monitor eligible targets use the existing cropped real-content Shell actor; windowed/ineligible targets keep existing managed-PyQt behavior; fullscreen raster failure fails closed.
- Orchestration prompt: isolated code-assist artifacts, RED → GREEN → REFACTOR, source-level evidence, no live GNOME/DBus/EDMC action, and a scoped local commit only.
- `README.md`: Python EDMC overlay plugin with an `overlay_client` runtime and pytest suite. No `CODEASSIST.md` was discovered.

## Dependency map

`consumers.py` supplies neutral `BackendPresentationRuntimeRequest` inputs → selected bundle owns a `GnomeShellPresentationRuntime` profile → existing `_gnome_shell_helper_presentation.run_gnome_shell_helper_presentation_cycle` receives profile flags and neutral raster provider → existing `shell_raster_frame` validation/helper request handling produces `gnome_shell_raster_frame` or clear/degraded behavior.

The generic consumer does not select GNOME behavior by raw backend/helper enum. Native X11/xcompat remain without a GNOME presentation runtime.

## Acceptance mapping

1. Existing selected-native runtime test supplies a cropped real-content frame provider and expects a `gnome_shell_raster_frame` with managed PyQt hidden.
2. Existing helper-runtime tests cover windowed/partial/ambiguous exclusion and managed-PyQt routing; profile activation only exposes the same runner flags to normal native GNOME.
3. Existing helper-runtime failure tests prove clear/degrade with fallback suppression; profile activation must forward the suppression flag for normal native GNOME.
4. Existing architecture-boundary tests and native X11/xcompat bundle tests protect the boundary; no changes are planned there.

## Test selection

Unit tests are selected. The change is deterministic bundle-owned runtime policy and injected callback forwarding. No `load.py`, startup/shutdown, journal/dashboard callback, or EDMC lifecycle state is touched, so no harness test is required.
