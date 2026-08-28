# Context: Clear First Native GNOME Presenter Transitions

## Scope and test type

This is a unit-only helper-cycle repair. It changes neither `load.py` nor any
EDMC lifecycle hook, so a harness test is not required. The selected GNOME
bundle already passes neutral callbacks to this module; generic consumers and
follow-surface remain outside this task.

## Requirements

- A successful Shell-raster clear must precede all managed surface preparation
  and managed attach after a stable raster-to-windowed transition.
- A failed clear must suppress the managed path and retain no competing
  presenter state.
- Loss and token-replacement exits must clear/reset safely without changing
  helper protocol, target discovery, payloads, X11, or xcompat.
- Fullscreen raster failures remain clear/suppress only; no fullscreen PyQt
  fallback is allowed.

## Existing pattern and defect

`run_gnome_shell_helper_presentation_cycle` owns the selected GNOME helper
presentation loop and uses injected fetcher/preparer/provider callbacks for
deterministic tests. Its guarded managed commit currently calls the managed
preparer and attach probe before `_clear_shell_raster_frame_for_managed_pyqt_transition`.
The repair moves that acknowledgement gate ahead of either operation while
retaining the existing transition-policy grace/sample guards and cache bounds.

## Dependency map

`gnome_shell_wayland` bundle runtime -> neutral helper-cycle inputs ->
`_gnome_shell_helper_presentation.run_gnome_shell_helper_presentation_cycle`
-> injected helper presentation request / preparation callback. The selected
cycle continues to own compositor-specific decisions. `presentation_transition`
remains the pure policy source.

## Uncertainties resolved

The helper clear fetcher returns an acknowledgement payload or raises; the
current helper-side clear utility already treats a non-raising response as a
successful acknowledgement. No DBus/schema change is needed.
