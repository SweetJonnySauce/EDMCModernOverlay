# Task 05 Plan: Stable Target Query Pressure

## Phase status

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Explore approved design, task, existing cache, transition, refresh, and invalidation paths | Completed |
| 1.2 | Select unit-test seams and record unchanged contracts | Completed |
| 2.1 | Add focused stable-cycle, deadline, and transition-guard tests | Completed |
| 2.2 | Add/strengthen explicit-refresh, failure/recovery, target/signature, stale-raster, exposure, and post-remap coverage | Completed |
| 3.1 | Capture expected RED evidence | Completed |
| 3.2 | Apply the smallest backend-owned correction | Completed |
| 3.3 | Reach focused GREEN and refactor without widening interfaces | Completed |
| 4.1 | Run the query/follow regression slice and patch hygiene | Completed |
| 4.2 | Synchronize Task 05 and Step 03 progress artifacts | Completed |

Phase 1 status: **Completed**

Phase 2 status: **Completed**

Phase 3 status: **Completed**

Phase 4 status: **Completed**

## Touchpoints

- Runtime: `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`
- Tests: `overlay_client/tests/test_gnome_helper_presentation_runtime.py`
- Expected unchanged wiring: `overlay_client/backend/consumers.py`, `overlay_client/follow_surface.py`
- Progress records: this directory plus the authoritative/working fix219 plan artifacts

## Test-type selection

Unit tests are required and selected because the helper functions, runtime state, clock, target
payloads, and presentation calls are injectable without EDMC/plugin lifecycle wiring. Harness
tests are not selected because Task 05 does not touch `load.py`, EDMC hooks, lifecycle state, or
Tk wiring.

## Test scenarios

1. **Guarded stable cycle**
   - Input: successful mapped-suppressed target/presentation state, transition guard enabled, clock inside 1.5-second deadline.
   - Output: cached result, zero additional target or presentation calls.
2. **Bounded deadline refresh**
   - Input: same guarded stable state at the deadline, followed by another cycle inside the renewed deadline.
   - Output: exactly one target query at expiry, no redundant presentation apply, then target-query suppression resumes.
3. **Explicit one-shot refresh**
   - Input: stable cached state plus `presentation_refresh_requested=True`, then an unchanged cycle.
   - Output: one target query and presentation apply bypass, then cached steady state resumes.
4. **Failure and recovery**
   - Input: unhealthy helper or failed/non-matching presentation followed by recovery.
   - Output: stable suppression is cleared; required recovery work is not delayed by the old deadline.
5. **Target/presentation invalidations**
   - Input: refreshed target identity, focus, monitor/output/scale, frame/buffer/content geometry, workspace/showing, minimize, fullscreen, or renderer/mode state.
   - Output: signature mismatch performs required presentation work and successful recovery rearms suppression.
6. **Exposure and surface state**
   - Input: caller-visible surface action change or surface recovery/preparation work.
   - Output: suppression is bypassed where cached visibility/preparation state is no longer valid.
7. **Stale raster**
   - Input: cached Shell raster frame at its lease-refresh point.
   - Output: stale refresh work bypasses a target-query cache hit.
8. **Cold-start remap one-shot**
   - Input: deferred-remap refresh request from the generic follow layer.
   - Output: matching and mismatch caches are bypassed exactly once; next stable cycle is a no-op.

## Implementation strategy

Preserve the existing runtime-state seam and monotonic deadline. Remove only the transition guard
as an unconditional blocker of the stable mapped-suppressed target-query cache. Keep the cache
predicate responsible for requiring a complete matching success, and strengthen the backend
presentation signature for any named target facts not already represented. Do not change generic
consumer parameters, add a second throttle, or alter transition decisions.

## Validation commands

- RED/GREEN task command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py -q`
- Narrow cache iteration when useful:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py -k 'target_query or suppressed_target or refresh_request or hard_signature' -q`
- Syntax/static build check for touched Python:
  `overlay_client/.venv/bin/python -m compileall -q overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`
- Hygiene: `git diff --check`

Full `make check` and `make test` are deferred by the approved Step 03 plan until Task 06 completes
the integrated query-plus-repaint milestone.

## Rollback

Revert only the Task 05 test additions, signature fields, and cache-condition correction. No
generic interface, configuration, helper protocol, evidence identity, or historical capture is
changed.
