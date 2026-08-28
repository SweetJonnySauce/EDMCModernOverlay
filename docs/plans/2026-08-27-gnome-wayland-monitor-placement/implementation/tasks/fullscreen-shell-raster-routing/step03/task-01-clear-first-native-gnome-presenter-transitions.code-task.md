# Task: Clear First for Native GNOME Presenter Transitions

## Description

Complete the native `gnome_shell_wayland` presenter-transition contract so one
presenter owns the overlay at a time. A raster-to-managed-PyQt transition must
clear the GNOME Shell actor before preparing, attaching, or mapping managed
PyQt. Target loss, helper loss, and trusted-target-token replacement must clear
or reset the locally owned presentation state safely. Eligible fullscreen
raster failures must stay fail-closed: clear/suppress the actor and never show
the known-misplaced PyQt fullscreen surface.

This is a repair of incomplete Step 3 wiring already present in the helper
cycle; it is not a new presenter or a protocol change.

## Background

Step 2 activates the normal native GNOME bundle's existing real-content Shell
raster route. The current helper-cycle code has a transition policy, cached
runtime state, and clear requests, but source review found that the guarded
managed commit probes/prepares and attaches managed PyQt before issuing the
clear request. It also resets local cache on helper-unhealthy and generic
target-loss paths without a contract proving stale raster cleanup/reset for
every required exit. Existing transition tests pass without proving the
required event order or every loss route.

The GNOME Shell extension already owns actor parenting, stacking, non-reactive
input behavior, and destructive clear. Retain that implementation and its
source-contract coverage. The generic `follow_surface` and `consumers.py`
paths must continue to provide only neutral callbacks through the selected
bundle runtime.

## Reference Documentation

**Required:**

- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/fullscreen-shell-raster-routing.md`

**Additional References (if relevant to this task):**

- Approved Step 3 plan: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-plan.md`
- Orchestration guardrails: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-orchestration-prompt.md`
- Raster inventory and live evidence: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/mutter-placement-probe-and-raster-inventory.md`
- Existing helper-cycle implementation: `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`
- Existing actor contract: `helpers/gnome_shell_extension/extension.js`

**Note:** You MUST read the detailed design and the required routing design
before beginning implementation. Read the additional references and the Step 2
handoff before changing transition logic.

## Technical Requirements

1. Keep presenter ownership and transition decisions in the selected GNOME
   bundle/helper-cycle boundary. `follow_surface.py` and generic
   `consumers.py` must not import compositor helper/presentation modules or
   choose behavior by raw GNOME/helper/backend enums.
2. When a previously presented Shell raster reaches a stable windowed target,
   issue and prove a successful Shell-raster clear before any managed-PyQt
   surface preparation, helper attach, or client-visible managed commit. If
   clear cannot be proven, return a degraded/suppressed result and do not map
   or attach managed PyQt.
3. For a target becoming unavailable, minimized, hidden/off-workspace, or a
   helper becoming unhealthy, clear stale local presentation state and request
   a raster clear whenever the helper call remains safely possible. Do not
   retain a stale raster success/cache or permit managed presentation. A helper
   that is unavailable cannot be contacted; its result must still reset local
   ownership and fail closed.
4. For trusted target-token replacement, clear/reset the old presenter before
   a new target can be presented. A failed clear must remain visibly
   suppressed and produce an actionable transition/degrade reason.
5. Preserve strict fullscreen failure behavior: provider/no-visible-content,
   invalid frame, clear failure, or degraded raster attach must clear/suppress
   rather than use managed PyQt for fullscreen. Preserve existing bounded
   retries, cache/lease bounds, and transition/handoff guards; do not add a
   sleep, arbitrary timer, coordinate/primary-monitor heuristic,
   monitor-transfer variant, static proof frame, or fullscreen-PyQt fallback.
6. Do not change the public helper DBus protocol/schema, target discovery,
   payload semantics, X11, or XWayland-compatibility behavior. Do not remove
   `GNOME_SHELL_RASTER` compatibility/development selector, override, or
   status surface.
7. Retain extension source contracts that raster actors are non-reactive,
   parented/stacked above the target, click-through/focus-safe, and removed or
   destroyed on non-transient clear. Do not alter the extension unless a
   source-level contract defect is required for the transition repair.

## Dependencies

- Step 1 bundle-owned runtime seam and Step 2 native-GNOME profile activation
  are present in current source; re-audit them rather than trusting historical
  task artifacts or commits.
- `PresentationTransitionState` and the GNOME helper-cycle's injected fetcher,
  surface-preparer, and raster-frame-provider form the deterministic unit-test
  seam.
- This task has no `load.py`, EDMC hook, startup/shutdown lifecycle, or live
  GNOME-session change. Select **unit tests only**; a harness test is not
  required unless implementation expands into those prohibited touchpoints.

## Implementation Approach

1. Add focused RED unit contracts around the helper cycle for clear-first
   raster-to-managed ordering, target/helper loss, token replacement, clear
   failure, fullscreen raster failure, and repeated monitor/fullscreen
   handoff. Record request/preparation order rather than only final state.
2. Refine the existing transition/lifecycle wiring behind the GNOME bundle so
   clear acknowledgement gates managed preparation/attach, loss paths reset
   state fail-closed, and fullscreen failure remains suppressed. Keep the
   pure transition policy deterministic and retain bounded existing guards.
3. Extend only necessary Shell-extension source-contract assertions to anchor
   non-reactivity, target-relative above-target attachment, focus/click-through
   safety, and clear/detach behavior. Do not execute GNOME, DBus, EDMC, or
   Elite actions.
4. Review the scoped diff for fix219 neutrality, accidental protocol changes,
   prohibited fallback/heuristic additions, cache regressions, X11/xcompat
   imports, and secrets. Update the routing plan/dashboard and create the
   required scoped local commit only after validation.

## Acceptance Criteria

1. **Raster to Managed PyQt Clears First**
   - Given an active native-GNOME Shell-raster presentation and a target that
     becomes stably, genuinely windowed under the existing transition guard
   - When the helper cycle commits the managed presenter
   - Then a clear request acknowledged by the helper occurs before managed
     surface preparation and before the managed-PyQt attach request; exactly
     one presenter can be visible, and an unacknowledged/failed clear returns
     degraded/suppressed with no managed attach or mapping

2. **Target and Helper Loss Reset Safely**
   - Given a cached successful Shell-raster actor and runtime state
   - When the target is unavailable, minimized, hidden/off-workspace, or the
     helper becomes unhealthy
   - Then the result is `HIDE_ALL`/suppressed, stale local request/status/cache
     and transition ownership are reset, no managed presenter is prepared or
     attached, and a clear is issued where the healthy helper can safely
     receive it

3. **Target Token Replacement Clears Old Ownership**
   - Given a raster actor associated with trusted token A
   - When the helper reports a valid replacement target with token B
   - Then the actor for A is cleared/reset before B can be presented, the
     result records the replacement transition reason, and clear failure keeps
     both actors/managed PyQt presentation suppressed

4. **Fullscreen Failures Remain Fail Closed**
   - Given an eligible fullscreen/full-monitor native-GNOME target
   - When real-content export has no visible content, validates an unsafe
     frame, helper raster attach/readback degrades, or actor clear fails
   - Then the helper receives a clear/degraded request with an actionable
     reason, no static proof frame is selected, and no fullscreen managed-PyQt
     fallback, preparation, attach, or mapping occurs

5. **Transitions Remain Bounded and Deterministic**
   - Given fullscreen-to-windowed handoff samples, monitor changes, and a
     repeated fullscreen monitor handoff
   - When the pure policy and helper cycle run with injected monotonic time
   - Then the existing grace/sample guards and bounded retry/cache behavior
     are preserved, stable fullscreen resumes raster without duplicate actors,
     and the changed implementation introduces no sleep, coordinate guess,
     primary-monitor logic, monitor-transfer retry, or timing-based fallback

6. **Extension Actor and fix219 Boundaries Stay Intact**
   - Given the changed helper/runtime source and the GNOME Shell extension
   - When source-contract and architecture-boundary tests inspect them
   - Then raster actors remain non-reactive, target-parented/raised above
     Elite, click-through/focus-safe, and detached/destroyed on clear;
     `consumers.py`/`follow_surface.py` remain neutral; `native_x11` and
     `xwayland_compat` gain no GNOME helper/raster imports or runtime behavior;
     and helper protocol/schema and legacy `GNOME_SHELL_RASTER` compatibility
     surfaces are unchanged

7. **Focused Unit Validation Passes**
   - Given the scoped implementation and updated unit/source-contract tests
   - When running the exact Step 3 command below and `git diff --check`
   - Then both pass, the final report records every changed test file and exact
     command/result, and it explicitly records that no harness test was added
     because no `load.py` or EDMC lifecycle touchpoint changed

   ```bash
   PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
     overlay_client/tests/test_gnome_helper_presentation_runtime.py \
     overlay_client/tests/test_presentation_transition.py \
     overlay_client/tests/test_gnome_shell_helper_extension_source.py \
     overlay_client/tests/test_backend_architecture_boundary.py -q
   git diff --check
   ```

8. **Step Demonstration Is Reproducible Without Live Actions**
   - Given deterministic helper fetchers, a recording surface preparer, and a
     real-content-style raster provider
   - When a fullscreen target becomes windowed, a target/helper loss or token
     replacement occurs, and a fullscreen frame failure is simulated
   - Then recorded calls prove clear-before-managed order, all loss/failure
     paths suppress stale/competing presentation, and no GNOME extension,
     DBus, EDMC, or Elite live action is needed for the contract proof

## Metadata

- **Complexity**: High
- **Labels**: GNOME Wayland, Shell Raster, Presenter Transition, Fail Closed, fix219, Unit Tests
- **Required Skills**: Python runtime-state design, deterministic pytest, GNOME Shell actor contracts, backend-boundary review
