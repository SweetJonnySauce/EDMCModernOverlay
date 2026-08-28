# Task: Add GNOME Content-Visibility Capability Contract

## Description

Extend the native GNOME helper IPC models with an optional, capability-gated
content-visibility request/result contract. This task establishes safe
serialization and validation only: it must preserve the current visible
behavior for every existing or unsupported helper and must not yet change the
GNOME Shell extension actor state or wire user preference behavior.

## Background

The native GNOME fullscreen renderer uses `HelperRasterFrameRequest` and
helper health/presentation status models. A future helper implementation needs
an explicit capability before it can safely honor `visible`/`suppressed`
content intent. Older, malformed, unsupported, or rejecting helpers must stay
on the proven stable-visible path; the capability fallback must never become
`allow_unfocused_target=false` or a managed-PyQt presenter swap.

## Reference Documentation

**Required:**

- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/native-gnome-shell-raster-content-suppression.md`

**Additional References (if relevant to this task):**

- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/native-gnome-shell-raster-content-suppression-lessons.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-shell-raster-content-suppression-plan.md` (Step 1)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-fullscreen-focus-visibility-regression-plan.md` (invalid historical evidence)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. Define a native-GNOME-owned capability identifier and a narrowly validated
   optional request/result representation for `visible` and `suppressed`
   raster content visibility.
2. Extend `HelperRasterFrameRequest` serialization/signature and the parsed
   helper health/presentation model only as necessary to carry the optional
   contract and a diagnosable support/degraded state.
3. Preserve compatibility: an absent, older, malformed, or capability-missing
   helper must result in the existing visible request/state, not an attempted
   suppression request.
4. Keep `allow_unfocused_target` semantically separate and unchanged for the
   eligible fullscreen continuity route. Do not use the user preference to set
   it false.
5. Do not add extension-side actor mutation, `hide`, clear/suspend/detach/
   destroy behavior, a helper protocol version bump without an explicit
   compatibility rationale, or user-preference wiring. Those belong to later
   plan steps.
6. Keep generic policy neutral. Any helper-capability inspection and protocol
   serialization must stay under native GNOME backend-owned seams.
7. Add unit/contract tests for supported, unsupported, absent, malformed, and
   legacy capability responses, including request serialization, status
   parsing, no-op visible fallback, signature/no-op behavior, and boundary
   ownership.

## Dependencies

- Task 01 neutral intent contract, which this task may accept as input but
  must not yet use to change live request behavior.
- `overlay_client/backend/helper_ipc.py` models and validators.
- Native GNOME presentation bundle/runtime under `overlay_client/backend/bundles/`.
- Existing tests in `overlay_client/tests/test_gnome_shell_helper_presentation_state.py`,
  `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, and
  `overlay_client/tests/test_backend_architecture_boundary.py`.

## Implementation Approach

1. Identify how helper health capabilities are validated and how raster frame
   request/status mappings are parsed. Choose one backward-compatible
   capability identifier and one narrow typed content-visibility value.
2. Write RED contract tests for a helper advertising the capability and for
   absent/older/malformed/capability-missing health or presentation payloads.
3. Implement only the client-side types, serialization, parsing, and
   capability gate. Default every unsupported case to stable visible behavior
   with a machine-readable diagnostic/degrade reason where the current status
   model permits it.
4. Prove that signatures distinguish intentional supported contract values but
   preserve current no-op request behavior when capability is unavailable.
5. Refactor for small, readable boundaries; record exact test evidence in the
   handoff and do not stage or commit changes.

## Acceptance Criteria

1. **Supported contract is representable without actor behavior change**
   - Given a healthy helper that explicitly advertises the new capability
   - When the native GNOME request/result models are constructed and serialized
   - Then a validated optional `visible` or `suppressed` content value can be
     represented without changing actor lifecycle behavior or
     `allow_unfocused_target`.

2. **Unsupported and older helpers remain visibly stable**
   - Given a helper with absent, older, malformed, or missing capability data
   - When a suppressed content intent reaches the native GNOME capability gate
   - Then no suppression request is emitted, the effective behavior remains
     visible, and a diagnosable unsupported/degraded result is available.

3. **Invalid payloads fail closed**
   - Given a malformed content-visibility value or malformed capability/result
     payload
   - When helper IPC validation runs
   - Then it cannot be interpreted as supported suppression and cannot alter
     fullscreen actor-continuity authorization.

4. **Continuity authorization is unchanged**
   - Given an eligible fullscreen Shell-raster request with any capability
     outcome
   - When its payload and signature are inspected
   - Then `allow_unfocused_target` remains governed by the restored continuity
     guard and is never derived from the unchecked preference in this task.

5. **Boundary and unit test evidence**
   - Given the completed IPC-contract change
   - When selected helper presentation, runtime, policy, and architecture
     tests run through `overlay_client/.venv`
   - Then all selected tests pass and the task handoff records exact commands,
     results, and any intentionally deferred live validation.

## Metadata

- **Complexity**: High
- **Labels**: native-wayland, gnome, helper-ipc, capability-gate, fix219-boundary, unit-tests
- **Required Skills**: Python protocol modeling, compatibility design, pytest, GNOME helper IPC, architecture-boundary testing
