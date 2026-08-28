# Step 3.1 Context: Neutral Content-Intent Transport

## Scope

Transport the existing generic policy's `visible` / `suppressed` decision to
the next bundle-owned presentation request. This task does not interpret that
intent for GNOME, change helper protocol fields, or alter actor lifecycle.

## Requirements

- The policy remains the only focus debounce authority.
- The initial, reset, and hard-hide transport value is `visible`.
- A meaningful policy intent change requests one normal subsequent presentation
  refresh; unchanged intent must not keep requesting refreshes.
- Generic follow/runtime code uses only `BackendPresentationContentVisibility`.
- Existing Qt content suppression and hard hide behavior stay unchanged.

## Dependency map

`FollowSurfaceMixin._refresh_backend_presentation` sends a generic request via
`run_backend_presentation_cycle`. The selected bundle receives
`BackendPresentationRuntimeRequest`. The follow surface computes the next
intent only after it receives the neutral visibility snapshot and policy
decision. The next task may consume that request in the GNOME-owned bundle.

## Existing patterns

- `BackendPresentationRuntimeRequest` is the typed neutral runtime contract.
- `_backend_presentation_refresh_requested` is already a one-shot request
  consumed at the next runtime cycle.
- `_reset_backend_presentation_surface_state` is the existing hard/reset
  boundary and resets visibility state.

## Test selection

Unit tests cover typed request transport. Follow-surface tests cover lifecycle
wiring and reset behavior. No harness test is required: `load.py` hooks and
EDMC plugin lifecycle are untouched.
