# Task: Add Helper-Owned Reversible Raster Content Suppression

## Description

Implement the GNOME Shell helper side of the already capability-gated raster
content-visibility contract. For a supported request, suppress or restore
content on the existing single-frame or region-raster actor records without
treating ordinary target focus loss as target/session loss. This task is
limited to helper-owned actor content state and its result diagnostics; it
must not wire the user preference or change generic follow/runtime policy.

## Background

The previous attempt represented the unchecked foreground-visibility
preference by setting `allow_unfocused_target=false`. The helper classified an
ordinary unfocused fullscreen target as `target_not_focused`, then entered its
clear/suspend path and hid the compositor actors. That caused a black screen
when focus returned and was rolled back.

Step 1 added a neutral `visible`/`suppressed` request value and a GNOME-owned
capability contract. `allow_unfocused_target` remains the fullscreen actor
continuity authorization and must remain true for the eligible route during
ordinary focus loss. This task makes the helper honor a supported
`content_visibility` value while retaining the same actor identity and
attachment. The target is the existing Clutter actor content state (for
example, an opacity/content-state mutation) only; the exact reversible
mechanism is acceptable only if it leaves lifecycle and input invariants
intact.

## Reference Documentation

**Required:**

- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/native-gnome-shell-raster-content-suppression.md`

**Additional References (if relevant to this task):**

- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/native-gnome-shell-raster-content-suppression-lessons.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-shell-raster-content-suppression-plan.md` (Step 2)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-fullscreen-focus-visibility-regression-plan.md` (invalid historical evidence)
- `helpers/gnome_shell_extension/extension.js` (`_handleShellRasterFrame`, single-frame and region reuse/update paths, clear/suspend methods)
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`
- `overlay_client/tests/test_gnome_shell_helper_presentation_state.py`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. Add one helper-owned, explicitly capability-gated content-visibility
   operation for `visible` and `suppressed` requests. It must operate only on
   an existing valid Shell-raster actor/session after normal target/geometry
   eligibility checks; omitted legacy requests retain current visible behavior.
2. Apply the operation to both actor forms: the single-frame
   `_shellRasterFrame` record and every retained member of
   `_shellRasterRegions`. A `visible -> suppressed -> visible` cycle must use
   the same actor objects and the same attached parents; it must not remap,
   recreate, replace, re-parent, or restack actors merely to change content
   visibility.
3. Preserve, and assert in diagnostics/tests, actor identity, parentage,
   target/session token, monitor placement, target/frame geometry, stacking
   relationship, `reactive:false`/click-through state, and stale-timeout
   ownership across an ordinary focus transition. Refreshing the existing
   timeout or normal stacking refresh is permitted only when it retains those
   identities and does not make the actor visible by calling `show` as a
   suppression substitute.
4. For ordinary focus-driven suppression, prohibit every lifecycle operation:
   `_clearShellRasterFrame`, `_suspendShellRasterFrame`, actor `hide`,
   `remove_child`, `destroy`, detach, clear, session replacement, or
   managed-PyQt fallback. In particular, do not invoke or reclassify the
   `target_not_focused` path.
5. Keep existing hard lifecycle cleanup unchanged for explicit clear, target
   loss, invalid geometry, session invalidation, timeout, shutdown, overview,
   and genuine actor replacement. Do not broaden ordinary-focus behavior into
   these cleanup paths.
6. Extend the helper result payload only as needed to report requested and
   effective content visibility plus supported/applied/degraded state. On
   malformed/unsupported content values, missing actor/session identity, or
   mutation failure, retain or restore the last known-safe **visible** content
   state, report a diagnosable degraded/unsupported result, and do not use
   focus-risk lifecycle handling.
7. Do not wire the unchecked preference, edit generic presentation policy,
   duplicate debounce, change `allow_unfocused_target`, bump protocol versions
   without an explicit compatibility rationale, or alter X11/xcompat/windowed
   managed-PyQt behavior. Preference wiring belongs exclusively to Step 3.
8. Add focused extension source/contract and helper-runtime/mock coverage.
   Source assertions must bind the new ordinary content-suppression method to
   the update path and prove it cannot call the clear/suspend/hide/detach/
   destroy operations. Runtime/contract tests must prove both single and
   region paths keep the same actor identity/parent/session/placement/
   stacking/non-reactivity/timeout state through `visible -> suppressed ->
   visible`, while genuine hard-loss clear behavior remains unchanged.

## Dependencies

- Completed Step 1 neutral intent and capability contract in
  `overlay_client/backend/presentation_policy.py` and
  `overlay_client/backend/helper_ipc.py`.
- The GNOME Shell extension’s existing single-frame and multi-region actor
  records, reuse logic, diagnostics, stale timeout, and lifecycle cleanup.
- Existing extension source tests and helper IPC/presentation-state contract
  tests. No `load.py` wiring is in scope, so unit/source/contract tests—not an
  EDMC lifecycle harness—are required.

## Implementation Approach

1. Trace `_handleShellRasterFrame` from request parsing through eligibility,
   actor reuse/create, result payload construction, and hard-loss clear
   behavior. Identify a narrow helper method that receives only a normalized
   supported `visible`/`suppressed` value and validates the retained actor
   records before any mutation.
2. Write RED tests first. Add source-level assertions that distinguish the new
   content-only method from lifecycle methods, and contract/runtime fixtures
   for single and region actor state transitions, mutation failure, unsupported
   legacy requests, and unchanged hard-loss cleanup.
3. Implement one reversible content-only mutation with explicit state recorded
   on each actor record. Prefer an actor-content/opacity state mutation that
   preserves parentage and reactivity; do not use `hide`. Ensure the visible
   operation restores the same record state without decoding or replacing the
   image/region actors.
4. Report request/effective visibility and capability/degrade evidence in the
   Shell-raster payload, preserving existing diagnostic fields. Keep every
   unsupported or failure path visibly stable and actor-continuous.
5. Run focused tests using `source overlay_client/.venv/bin/activate`, inspect
   the diff for prohibited lifecycle calls in the ordinary suppression path,
   and record exact results in the task handoff. Do not run live D-Bus, reload
   GNOME Shell, stage, commit, or proceed to Step 3.

## Acceptance Criteria

1. **Single-frame suppression retains actor continuity**
   - Given a healthy helper advertising raster-content-visibility support and
     an eligible fullscreen single-frame actor already attached to its parent
   - When the helper receives `visible`, then `suppressed`, then `visible`
     for the same target/session/frame identity
   - Then the same actor remains attached to the same parent with unchanged
     target/session/monitor/frame metadata, stacking relationship,
     non-reactivity, and timeout ownership; only raster content visibility
     changes and the visible state is restored without recreation or remap.

2. **Region-raster suppression retains every region actor**
   - Given a supported helper with an eligible multi-region frame already
     attached
   - When it receives `visible -> suppressed -> visible` for the same region
     identities
   - Then every existing region actor retains its identity, parent, target and
     session metadata, geometry/placement, stacking, non-reactivity, and
     timeout state; no region is detached, destroyed, or decoded solely for
     the visibility transition.

3. **Ordinary focus suppression cannot use the unsafe lifecycle path**
   - Given a supported ordinary-focus content suppression request with
     fullscreen continuity authorization retained
   - When the helper executes the content-only operation
   - Then source/contract tests prove it cannot call
     `_clearShellRasterFrame`, `_suspendShellRasterFrame`, `hide`,
     `remove_child`, `destroy`, or the `target_not_focused` flow, and it does
     not cause a PyQt presenter fallback.

4. **Failure and legacy compatibility fail closed to visible**
   - Given an omitted, unsupported, malformed, actor-identity-invalid, or
     mutation-failing content-visibility request
   - When the helper processes the update
   - Then it returns an explicit unsupported/degraded diagnostic and retains
     or restores safe visible content on the existing valid actor; it does not
     clear/suspend/recreate the actor or change `allow_unfocused_target`.

5. **Hard lifecycle cleanup remains intact**
   - Given explicit clear, target loss, invalid geometry, session replacement,
     timeout, shutdown, or overview cleanup
   - When existing lifecycle handling runs
   - Then its current clear/suspend/destroy behavior remains confined to that
     hard lifecycle reason and is not reused for ordinary content suppression.

6. **Focused automated evidence is recorded**
   - Given the completed helper-only change
   - When targeted extension-source, helper presentation-state, and helper
     runtime tests run through `overlay_client/.venv`
   - Then they pass, `git diff --check` passes, the handoff lists exact
     commands/results, and live GNOME testing is explicitly deferred pending
     Step 4 and user approval.

## Metadata

- **Complexity**: High
- **Labels**: native-wayland, gnome-shell, shell-raster, actor-continuity, content-suppression, safety-regression, unit-tests
- **Required Skills**: GNOME Shell/Clutter actor lifecycle, JavaScript, helper IPC contracts, pytest source/contract testing, regression-safe refactoring
