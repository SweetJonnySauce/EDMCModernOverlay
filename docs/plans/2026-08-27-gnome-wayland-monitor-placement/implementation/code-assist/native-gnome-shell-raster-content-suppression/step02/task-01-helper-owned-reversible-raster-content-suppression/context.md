# Context: Helper-Owned Reversible Raster Content Suppression

## Scope

Implement only the GNOME Shell helper's capability advertisement and
content-only `visible`/`suppressed` operation for retained Shell-raster actor
records. Preference wiring, generic policy, protocol versions, and
`allow_unfocused_target` are out of scope.

## Existing pattern and dependency map

`HelperRasterFrameRequest.content_visibility` is already an optional,
GNOME-owned wire field. The helper's `HELPER_CAPABILITIES` must advertise that
the implementation is available. `HelperHealthService._handleShellRasterFrame`
validates target and geometry before creating or reusing either a single actor
record (`_shellRasterFrame`) or region records (`_shellRasterRegions`).

The new helper operation runs only after that normal successful update path.
It mutates actor opacity and a record-local content-visibility value. It must
not call lifecycle/cleanup methods. Existing clear/suspend behavior remains
solely for hard lifecycle reasons.

## Invariants

- Actor objects, parents, target/session metadata, placement, stacking,
  `reactive:false`, and stale timeout ownership remain unchanged through a
  visibility cycle.
- `suppressed` means opacity zero on the existing actor; it is not `hide`.
- Malformed input or mutation failure restores/retains visible opacity and
  returns a degraded diagnostic without clearing or recreating actors.
- The extension advertises the optional capability only because this task
  implements it; no protocol version changes are needed.

## Tests

The extension has source-contract pytest coverage rather than a Shell actor
runtime harness. Add focused assertions for capability advertisement, update
path binding, result diagnostics, both actor-record collections, and the
absence of lifecycle calls inside the content-only method. Parse the extension
with `gjs --check` as the JavaScript syntax gate.
