# Context

## Task and test selection

This is a deterministic, backend-owned Python bundle policy correction. Unit
tests are sufficient because it changes neither `load.py` nor EDMC lifecycle
or hook wiring; a harness test is not required.

## Requirements

- `keep_overlay_visible` is the sole authorization for an unfocused
  Shell-raster target.
- A full-monitor fullscreen target with the preference disabled sends
  `allow_unfocused_target=False`; the helper's existing `target_not_focused`
  response remains a focus-risk suspension with no visible managed-PyQt
  fallback.
- The same unfocused target sends `True` and can present when the preference
  is enabled.
- Fullscreen eligibility, geometry, transitions, helper schema, and X11 /
  xcompat behavior remain untouched.

## Relevant implementation path

`run_gnome_shell_helper_presentation_cycle` builds the request in
`overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`, then
passes its authorization flag to `_shell_raster_bridge_request`. The current
fullscreen-geometry helper bypasses the preference. The existing runtime unit
tests inject helper request/results and cover both the request flag and
focus-risk classification.

## Existing documentation

`AGENTS.md` requires a small, backend-boundary-preserving change and unit
tests for pure helpers. The detailed and fullscreen-routing designs establish
that Shell-raster presentation is native-GNOME bundle owned, fails closed, and
must not leak compositor policy into generic runtime code. No `CODEASSIST.md`
or `CONTRIBUTING.md` exists; `README.md` identifies this as a cross-platform
EDMC overlay plugin.

## Dependencies and risks

The helper protocol already accepts the flag and classifies an unauthorized
unfocused target as `target_not_focused`; no protocol change is needed. The
only behavioral risk is accidentally broadening scope into presentation
eligibility or transition policy, avoided by deleting the obsolete helper and
passing the existing preference directly.
