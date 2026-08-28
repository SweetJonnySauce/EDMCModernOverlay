# Task: Wire Capability-Gated Content Visibility in the Native GNOME Bundle

## Description

Consume the neutral runtime content intent only inside the native GNOME
presentation bundle and map it through the completed capability contract to
the existing Shell-raster frame request. A supported helper must receive
`visible` or `suppressed` while an eligible fullscreen actor keeps
`allow_unfocused_target=true` throughout ordinary focus loss. Unsupported,
malformed, unhealthy, or rejecting helpers must retain visibly stable content
and expose a gated diagnostic without actor lifecycle changes or presenter
fallback.

## Background

Step 1 established the neutral `visible`/`suppressed` intent and the
capability-gated helper IPC model. Step 2 added the reversible helper-owned
opacity operation for both single-frame and region actors. The user-visible
behavior remains inactive because the native GNOME runner still constructs
Shell-raster requests without that intent.

The previous attempt directly turned the unchecked preference into
`allow_unfocused_target=false`. On an unfocused fullscreen target, the helper
classified the request as `target_not_focused` and cleared/suspended actors,
causing a live black screen on focus return. This task must retain the
restored fullscreen/full-monitor continuity authorization. It must not create
or hide a managed PyQt overlay for a valid native fullscreen raster route.

## Reference Documentation

**Required:**

- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/native-gnome-shell-raster-content-suppression.md`

**Additional References (if relevant to this task):**

- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/native-gnome-shell-raster-content-suppression-lessons.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-shell-raster-content-suppression-plan.md` (Step 3)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-fullscreen-focus-visibility-regression-plan.md` (invalid historical evidence)
- `overlay_client/backend/bundles/gnome_shell_wayland.py`
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`
- `overlay_client/backend/helper_ipc.py`
- `overlay_client/backend/presentation_runtime.py`
- `overlay_client/tests/test_gnome_helper_presentation_runtime.py`
- `overlay_client/tests/test_gnome_shell_helper_presentation_state.py`
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`
- `overlay_client/tests/test_presentation_transition.py`
- `overlay_client/tests/test_backend_architecture_boundary.py`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. Receive the neutral runtime intent through the bundle interface and perform
   all `HelperRasterContentVisibility`, helper-health capability, request-wire,
   and result-diagnostic mapping inside the native GNOME bundle implementation.
   Do not add raw GNOME protocol types or helper capability checks to generic
   follow/runtime code.
2. For an eligible fullscreen/full-monitor Shell-raster target, preserve the
   restored continuity calculation: `allow_unfocused_target` remains true
   through ordinary unfocused cycles regardless of whether neutral content
   intent is `visible` or `suppressed`. Never derive it directly from the user
   preference or neutral intent.
3. Attach `content_visibility=suppressed` only if the current healthy helper
   explicitly advertises the Step 1 capability. On absent/older/malformed/
   unhealthy capability data, omit the wire field, retain visible content,
   retain continuity authorization, and surface a deduplicated diagnostic that
   explains the stable-visible fallback.
4. On focus return, pass `visible` for the retained actor/session rather than
   clearing, remapping, rebuilding, re-parenting, or swapping to managed PyQt.
   The request signature/no-op cache must recognize a content-visibility
   transition so a necessary suppression/restoration call cannot be skipped.
5. Preserve ordinary hard lifecycle behavior. Target loss, minimization,
   off-workspace state, invalid geometry/session, shutdown, overview, and
   managed-windowed transitions must retain their existing clear/transition
   handling and must not be reclassified as content-only suppression.
6. Preserve X11, xcompat, all other native Wayland bundles, windowed
   managed-PyQt behavior, placement, stacking, click-through, and follow
   behavior. A valid native fullscreen Shell-raster capability failure must not
   trigger a PyQt presenter swap.
7. Add focused test coverage for supported focused, supported unchecked-
   unfocused, checked-unfocused, focus-return, unsupported/malformed helper,
   hard target-loss, cached request/signature transition, presenter-transition,
   follow-surface, and architecture-boundary cases. Tests must prove both
   `allow_unfocused_target` continuity and the expected optional wire value.

## Dependencies

- Completed Task 01 neutral runtime transport in this Step 3 directory.
- Completed Step 1 helper IPC capability resolver and Step 2 helper-owned
  content operation.
- Existing GNOME presentation runner, Shell-raster request signature/cache,
  fullscreen transition guard, and no-PyQt-fallback rule.

## Implementation Approach

1. Trace the neutral intent from `BackendPresentationRuntimeRequest` into
   `GnomeShellPresentationRuntime`, then through
   `run_gnome_shell_helper_presentation_cycle`, `_shell_raster_bridge_request`,
   and `_request_with_shell_raster_frame`. Add the smallest bundle-owned
   adapter that uses the Step 1 resolver and leaves non-raster/unsupported
   requests stable-visible.
2. Write RED tests for a supported eligible fullscreen actor sequence
   `visible -> suppressed -> visible`, keeping the same target/session/frame
   identity and `allow_unfocused_target=True`. Include checked preference,
   unsupported/malformed health, hard loss, and presentation transition cases.
3. Implement capability-gated mapping and diagnostic propagation. Ensure the
   frame signature changes with supported content intent and that cache reuse
   cannot suppress a required helper update. Never add a focus-risk lifecycle
   call to the ordinary content path.
4. Extend source/boundary tests as needed: GNOME-owned code may use helper
   protocol types; generic files must remain neutral. Run focused tests through
   `overlay_client/.venv`, inspect the scoped diff for unsafe calls, document
   results in the handoff, and stop before live D-Bus/extension actions.

## Acceptance Criteria

1. **Supported unchecked unfocused route suppresses only content**
   - Given an eligible fullscreen/full-monitor native GNOME Shell-raster
     target, a healthy helper advertising the capability, and a debounced
     neutral `suppressed` intent
   - When the GNOME bundle constructs and applies its raster request
   - Then the request carries `content_visibility=suppressed` and
     `allow_unfocused_target=true`, the helper result remains on the raster
     presenter, and no `target_not_focused`, clear, suspend, hide, actor
     recreation, or managed-PyQt fallback occurs.

2. **Focus return and keep-visible preference restore/retain visibility**
   - Given the retained actor has been sent supported `suppressed` intent
   - When neutral intent becomes `visible` on focus return
   - Then the next GNOME request carries `visible` for the same raster actor
     identity and continuity authorization; given a checked keep-visible
     preference while unfocused, it sends or retains `visible` throughout.

3. **Unsupported helpers fail closed to stable visible**
   - Given missing, malformed, older, unhealthy, or capability-missing helper
     health/status data and a neutral `suppressed` intent
   - When the native GNOME bundle processes the request
   - Then it omits the optional wire value, keeps visible content and
     fullscreen continuity, reports a gated diagnostic/degrade reason, and
     does not select managed PyQt or any focus-risk actor lifecycle path.

4. **Hard lifecycle and transition behavior are unchanged**
   - Given target loss, minimization, off-workspace state, overview, invalid
     geometry/session, or a genuine fullscreen-to-managed transition
   - When the existing runtime handles it
   - Then its established clear/transition behavior remains distinct from
     ordinary content suppression, and no stale `suppressed` value keeps an
     invalid actor alive.

5. **Required updates are not cache-skipped and boundaries are preserved**
   - Given two otherwise matching raster requests whose supported neutral
     intents differ
   - When the runner evaluates its request signature/cache
   - Then the helper is called for the visibility transition; source and
     architecture tests also prove generic consumers/follow surfaces still do
     not import or dispatch GNOME helper implementation/protocol enums.

6. **Focused automated evidence is recorded**
   - Given the completed native GNOME integration
   - When focused GNOME runtime, helper presentation-state, helper extension
     source, presentation-transition, follow-surface, policy, and boundary
     tests run through `overlay_client/.venv`
   - Then they pass, `git diff --check` passes, and the handoff lists exact
     commands/results while deferring live GNOME validation to Step 4 and user
     approval.

## Metadata

- **Complexity**: High
- **Labels**: native-wayland, gnome-shell, shell-raster, capability-gate, actor-continuity, focus-visibility, regression-safety
- **Required Skills**: Python backend bundles, GNOME helper IPC, presentation cache/transition behavior, pytest, architecture boundaries, regression-safe refactoring
