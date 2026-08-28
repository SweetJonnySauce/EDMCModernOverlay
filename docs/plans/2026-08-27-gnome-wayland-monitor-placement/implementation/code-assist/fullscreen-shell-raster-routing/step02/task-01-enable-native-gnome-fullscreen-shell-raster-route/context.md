# Context

## Scope

Step 2 activates the already extracted native `gnome_shell_wayland` runtime
profile. It must make the existing real-content provider available for strict
fullscreen/full-monitor targets, retain windowed managed PyQt, and fail closed
for fullscreen raster failures. It does not change helper protocol, target
discovery, `load.py`, X11, or XWayland.

## Existing structure

- `overlay_client/backend/bundles/gnome_shell_wayland.py` owns the GNOME
  runtime profiles. Native GNOME is currently capability-only: raster and
  fallback suppression are both inactive; legacy raster is active.
- `overlay_client/backend/consumers.py` supplies only neutral surface and
  frame-provider callbacks to the selected bundle runtime.
- `_gnome_shell_helper_presentation.py` already enforces eligibility,
  real-content frame bridging, windowed managed-PyQt handling, clear/degrade
  behavior, and diagnostics.
- `render_surface.py` owns `_build_backend_shell_raster_content_frame`; the
  focused repaint tests cover its cropped real-content output.

## Requirements and test choice

- Unit tests only: this changes bundle policy and injected helper-cycle
  behavior, with no EDMC startup, shutdown, `load.py`, or lifecycle wiring.
  A harness test is not required.
- Native GNOME must forward `True` for the existing raster and fallback
  suppression flags. Generic consumers must stay neutral.
- Tests must demonstrate native selection with a real-content-style frame,
  windowed/ineligible no-raster handling, and provider/no-visible-content
  fullscreen suppression without PyQt fallback.

## Dependency map

`follow_surface` → neutral `consumers.run_backend_presentation_cycle` →
selected GNOME bundle runtime/profile → existing helper-cycle bridge →
real-content provider → Shell raster request. Windowed paths remain on the
helper cycle's managed-PyQt preparation branch.

## Existing documentation

No `CODEASSIST.md` exists. The approved routing orchestration prompt, design,
research, Step 2 task, `AGENTS.md`, and Step 1 handoff govern this task.
`README.md` and `tests/HARNESS_README.md` were discovered; this task has no
lifecycle wiring and therefore uses the focused unit suite rather than the
harness.
