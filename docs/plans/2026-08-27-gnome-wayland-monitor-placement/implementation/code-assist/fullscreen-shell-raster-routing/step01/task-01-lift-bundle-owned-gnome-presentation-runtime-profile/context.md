# Context

## Scope

Step 1 is a behavior-preserving backend-boundary extraction. The normal native
GNOME bundle advertises future fullscreen Shell-raster support but leaves it
inactive; the legacy raster bundle retains its active raster and fail-closed
fallback-suppression settings. Native X11 and XWayland have no GNOME runtime.

## Existing structure

- `overlay_client/backend/contracts.py` defines `BackendBundle` composition.
- `overlay_client/backend/consumers.py` resolves bundles and adapts runtime
  results for follow-surface consumers. It currently contains GNOME-specific
  selection and runner loading that this task moves behind the bundle.
- `overlay_client/backend/bundles/gnome_shell_wayland.py` builds both GNOME
  bundle identities and is the allowed owner of helper-presentation imports.
- `overlay_client/tests/test_backend_consumers.py` provides pure unit coverage;
  `test_backend_architecture_boundary.py` provides source-boundary coverage.

## Requirements and decisions

- Test type: unit. This is pure bundle/runtime selection with injected runners;
  no `load.py` or EDMC lifecycle path changes, so no harness test is required.
- A neutral runtime profile/request/result contract will be attached to
  `BackendBundle`. Generic consumers may invoke it but must not inspect GNOME
  helper/backend identities or import the GNOME presentation implementation.
- The existing helper runner is lifted intact, including its unavailable-helper
  handling and the legacy-raster flags. No target, payload, protocol, X11, or
  XWayland behavior changes are permitted.

## Existing documentation

`README.md` identifies the plugin and `tests/HARNESS_README.md` describes
vendored lifecycle tests; neither changes this pure-helper test choice.
`CODEASSIST.md` was not present. The routing design, plan, research, task, and
orchestration prompt govern this implementation.
