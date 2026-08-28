# Context: GNOME Content-Visibility Capability Contract

## Scope

Add only client-side native-GNOME helper IPC types, negotiation, serialization,
and parsed diagnostics. Do not wire the preference, change
`allow_unfocused_target`, or mutate GNOME Shell actors.

## Existing documentation

- The approved design requires a neutral `visible`/`suppressed` content intent
  and a helper-owned capability gate, while ordinary fullscreen focus changes
  retain actor continuity.
- The lessons record that using `allow_unfocused_target=false` caused the
  helper to clear/suspend actors and black-screen on focus return. That field
  is therefore outside this task's behavior change.
- Task 01 added `BackendPresentationContentVisibility` to the generic policy;
  it deliberately has no GNOME imports or helper protocol knowledge.

## Implementation paths and dependency map

`presentation_policy` (neutral intent, already present) -> native GNOME helper
IPC negotiation -> `HelperRasterFrameRequest` optional payload -> helper
presentation result parser. The final runtime wiring and extension actor work
remain deferred to later plan steps.

Relevant code:

- `overlay_client/backend/helper_ipc.py`: GNOME-owned wire models, validation,
  and request signatures.
- `overlay_client/backend/__init__.py`: public backend-contract exports.
- `overlay_client/tests/test_gnome_shell_helper_presentation_state.py`: pure
  request/result contract tests.
- `overlay_client/tests/test_backend_architecture_boundary.py`: generic policy
  ownership guard.

## Requirements and invariants

1. The optional capability is not part of baseline required capabilities, so
   existing helpers remain healthy and visible.
2. Only a healthy helper explicitly advertising the capability may receive a
   `suppressed` content request.
3. Absent, malformed, legacy, or unsupported capability input resolves to an
   omitted visibility wire field and effective visible behavior with a
   diagnostic reason.
4. Supported `visible` and `suppressed` values are serializable and distinct in
   request signatures. The default visible request retains the exact existing
   wire payload and signature.
5. Parsed malformed result values fail closed to a degraded, non-supported
   status; no actor lifecycle behavior is added.

## Test selection

This is deterministic data/validation logic, so unit/contract tests are
required. No `load.py` or plugin lifecycle path is touched; harness testing is
not applicable.

## Uncertainty resolved autonomously

The helper protocol remains version 3: an optional capability-advertised field
is backward compatible and does not require a protocol-wide version bump.
