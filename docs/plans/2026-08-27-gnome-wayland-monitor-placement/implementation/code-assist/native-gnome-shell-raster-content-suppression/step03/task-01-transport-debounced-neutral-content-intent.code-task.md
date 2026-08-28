# Task: Transport Debounced Neutral Content Intent Through the Runtime Contract

## Description

Extend the existing backend-owned runtime contract so the already-computed,
backend-neutral foreground-visibility decision can be retained and supplied to
the selected presentation bundle on a subsequent refresh. The task must not
add compositor-specific policy to generic follow/runtime code and must not
directly manipulate a GNOME actor. It establishes the neutral transport needed
for the native GNOME bundle to request safe Shell-raster content suppression in
the next task.

## Background

The generic policy already owns the debounced decision and exposes
`BackendPresentationContentVisibility.VISIBLE` or `.SUPPRESSED`. It is made
only after a backend presentation cycle returns its neutral visibility
snapshot. The existing runtime request transports the raw user preference but
does not transport that resolved intent, so a Shell-raster actor cannot safely
match the same debounce without duplicating it.

The unsafe historical implementation mapped the user preference directly to
`allow_unfocused_target=false`, causing the helper to enter its focus-risk
clear/suspend path. That plan is invalid. The replacement must retain the
fullscreen continuity guard and carry only a neutral content intent. Generic
code must remain unaware of GNOME helper protocol fields, capability names, or
backend/helper enums.

## Reference Documentation

**Required:**

- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/native-gnome-shell-raster-content-suppression.md`

**Additional References (if relevant to this task):**

- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/native-gnome-shell-raster-content-suppression-lessons.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-shell-raster-content-suppression-plan.md` (Step 3)
- `overlay_client/backend/presentation_policy.py`
- `overlay_client/backend/presentation_runtime.py`
- `overlay_client/backend/consumers.py`
- `overlay_client/follow_surface.py`
- `overlay_client/tests/test_backend_presentation_policy.py`
- `overlay_client/tests/test_follow_surface_mixin.py`
- `overlay_client/tests/test_backend_architecture_boundary.py`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. Add or use one typed, backend-neutral runtime-request field for the
   resolved content intent. Its vocabulary must remain exactly `visible` and
   `suppressed`; generic code must not import `HelperRasterContentVisibility`,
   GNOME helper IPC, GNOME bundles, or GNOME backend/helper enums.
2. Use the existing `decide_backend_presentation_visibility` output and its
   existing state as the sole foreground debounce authority. Do not add a
   second sample counter, timer, target-focus classifier, or preference-derived
   focus rule in the generic or GNOME path.
3. Retain the resolved intent in the generic follow/runtime seam in a way that
   is safe for the first cycle, hard lifecycle loss, reset, backend fallback,
   and focus return. The initial/unknown and hard-loss behavior must remain
   `visible` for any valid retained raster actor; a hard target loss must still
   use its existing hide/clear lifecycle rather than content suppression.
4. When the resolved intent changes, arrange a normal backend presentation
   refresh so the selected bundle can apply it promptly. Do not call GNOME
   helper APIs directly from `follow_surface`, remap/hide the Qt surface merely
   to communicate the intent, or create a recursive/unbounded refresh loop.
5. Preserve all existing X11, xcompat, non-GNOME Wayland, windowed managed-PyQt,
   overview, placement, and click-through behavior. Other bundles may ignore
   the neutral field without behavior changes.
6. Keep `allow_unfocused_target` out of generic code. This task must never map
   the unchecked preference, neutral suppressed intent, or target focus to
   that field.
7. Add tests in the existing unit/follow/architecture suites. Cover the
   debounce-to-intent transition, checked preference remaining visible,
   focus-return restoring visible intent, hard target loss/reset not leaving a
   stale suppressed intent, and source-level proof that generic code contains
   no GNOME-specific dispatch or helper protocol import.

## Dependencies

- Completed Step 1 neutral `BackendPresentationContentVisibility` policy and
  Step 2 helper content operation. This task does not activate the helper
  operation itself.
- The existing generic `BackendPresentationRuntimeRequest`,
  `run_backend_presentation_cycle`, and follow-surface visibility state.
- The selected bundle interface, which may receive the neutral field but must
  own all compositor-specific interpretation.

## Implementation Approach

1. Trace one refresh from `follow_surface` through the generic runtime request
   and back to the existing visibility decision. Identify the smallest stored
   neutral-intent state and refresh trigger that uses the already calculated
   decision without changing debounce ownership.
2. Write RED tests for normal focus loss after the existing debounce, checked
   preference, focus return, reset/hard loss, and no-op non-GNOME behavior.
   Include architecture assertions covering every newly touched generic file.
3. Add the neutral field and make the generic consumer transport it to the
   selected runtime. Persist/update it only from the existing decision, and
   request one ordinary follow refresh on a meaningful change if required by
   the current lifecycle.
4. Confirm that generic code uses only neutral types and that no source path
   changes `allow_unfocused_target`, calls a GNOME helper, or branches on a
   GNOME backend/helper enum. Record exact focused validation results in the
   task handoff; do not stage, commit, reload GNOME Shell, or perform live
   D-Bus actions.

## Acceptance Criteria

1. **Debounced decision becomes a neutral runtime input**
   - Given a valid backend presentation whose target loses focus while the
     preference is unchecked
   - When the existing policy reaches its configured debounce threshold
   - Then the next selected-runtime request receives neutral `suppressed`
     intent, with no second debounce or GNOME-specific logic in the generic
     caller.

2. **Visible intent is restored and checked preference remains visible**
   - Given an earlier suppressed neutral intent
   - When target focus returns
   - Then the existing policy produces and the next runtime request receives
     neutral `visible` intent; given the keep-visible preference is checked,
     it remains `visible` while unfocused.

3. **Hard lifecycle and reset remain separate**
   - Given a stale suppressed intent followed by target loss, minimization,
     off-workspace state, backend reset, or legacy fallback
   - When generic visibility handling runs
   - Then normal hard hide/clear/reset behavior remains in force and no stale
     content-suppression request is used as a lifecycle substitute.

4. **Generic boundary remains neutral**
   - Given all touched generic runtime/follow files
   - When architecture-boundary tests inspect their source
   - Then they contain no GNOME helper IPC import, GNOME protocol/capability
     symbol, direct helper call, or raw GNOME backend/helper-enum dispatch.

5. **Focused automated evidence is recorded**
   - Given the completed neutral transport
   - When selected policy, follow-surface, consumer/runtime, and architecture
     tests run through `overlay_client/.venv`
   - Then they pass, `git diff --check` passes, and the task handoff records
     exact commands/results and defers live GNOME validation.

## Metadata

- **Complexity**: High
- **Labels**: backend-runtime, neutral-contract, focus-debounce, fix219-boundary, regression-safety, unit-tests
- **Required Skills**: Python dataclasses/contracts, Qt follow lifecycle, pytest, backend-boundary design, regression-safe refactoring
