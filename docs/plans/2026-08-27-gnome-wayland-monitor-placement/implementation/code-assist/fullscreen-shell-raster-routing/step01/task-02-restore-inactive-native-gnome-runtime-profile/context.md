# Context: Restore inactive native-GNOME runtime profile

## Scope and mode

- Task source: `implementation/tasks/fullscreen-shell-raster-routing/step01/task-02-restore-inactive-native-gnome-runtime-profile.code-task.md`.
- Mode: auto. Standing approval permits this in-scope, local implementation without further interaction.
- Test selection: unit. The behavior is deterministic profile-to-injected-runner forwarding; it does not touch `load.py`, EDMC hooks, or lifecycle wiring.

## Requirements

1. Keep the bundle-owned `PresentationRuntimeBackend` seam and neutral consumer invocation.
2. Keep `gnome_shell_wayland` helper-owned and raster-capable, but forward inactive raster and fallback-suppression flags.
3. Retain the active `gnome_shell_raster` compatibility/development profile and its unavailable-helper fail-closed behavior.
4. Preserve fix219: no generic raw GNOME/helper/raster policy, and no GNOME runtime/imports for native X11 or XWayland.
5. Do not change helper protocol/schema, target discovery, payloads, extension source, `load.py`, EDMC hooks, X11, or xcompat.

## Existing patterns and dependency map

`consumers.run_backend_presentation_cycle` builds the neutral request, resolves the selected bundle, and delegates to `presentation_runtime`. `GnomeShellPresentationRuntime` maps its bundle profile into the injected runner's keyword arguments. The normal and legacy GNOME bundles share that adapter but own distinct profiles. Tests in `test_backend_consumers.py` inject the runner; `test_backend_architecture_boundary.py` source-checks generic dispatch and X11/xcompat isolation.

The audited starting source has the seam already and is clean under `git diff --check`, but the normal native profile incorrectly sets both active flags to `True`. The narrow repair is profile values plus focused expectation updates.

## Existing documentation

- `AGENTS.md`: preserve fix219; unit tests required for pure helpers; record exact validation.
- `README.md`: project overview; no task-specific build instructions.
- No `CODEASSIST.md` was found. A project-specific one could be added later if repeated SOP constraints need codifying; it is not in this task's scope.

## Risks and guardrails

- Do not change the public helper runner signature or generic runtime dispatcher.
- The native profile must remain capable (`owns_helper_presentation` and `supports_fullscreen_shell_raster`) while inactive only for Step 1.
- Existing dirty planning/history paths are user-owned and excluded from staging.
