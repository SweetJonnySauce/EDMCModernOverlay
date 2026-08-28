# Step 3.2 Context: Native GNOME Content-Visibility Wiring

## Requirements

- The generic runtime transports only `BackendPresentationContentVisibility`.
- GNOME-owned code translates that neutral value to the helper protocol after a
  healthy-helper capability check.
- A valid fullscreen/full-monitor Shell-raster route keeps
  `allow_unfocused_target=True` independently of content visibility.
- Unsupported capability keeps the optional wire field absent and the actor
  visibly stable. The diagnostic is metadata, not a lifecycle/degrade request.
- Shell-raster request signatures must include the supported wire value.

## Integration map

`BackendPresentationRuntimeRequest.content_visibility` flows to
`GnomeShellPresentationRuntime`, then to
`run_gnome_shell_helper_presentation_cycle`. That GNOME-owned runner obtains
health, resolves the optional helper value, and adds it only while constructing
a Shell-raster frame request. `HelperRasterFrameRequest.signature()` already
includes the optional field, so the existing cache observes supported
visibility transitions.

## Constraints

No generic follow/runtime GNOME protocol imports; no focus-risk clear, actor
hide, managed-PyQt fallback, D-Bus, extension reload, staging, or commit.
Existing unhealthy-helper and hard-lifecycle handling is outside this task.

