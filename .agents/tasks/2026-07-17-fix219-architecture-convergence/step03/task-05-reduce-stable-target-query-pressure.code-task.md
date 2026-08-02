# Task: Reduce Stable Target Query Pressure

## Description
Test and correct the existing GNOME stable-target suppression so matching stable state does not synchronously enumerate Shell windows every generic follow cycle. Use the existing backend-owned cache seam, explicit state, and an injected monotonic clock while preserving immediate invalidation, recovery, and the cold-start deferred-remap exactly-once refresh.

## Background
Current research found an existing 1.5-second suppression mechanism whose transition-guard interaction can still permit target queries at the 500 ms follow cadence. The correction must be a small backend-owned change, not a second generic throttle. This is authoritative Stage 1.7 and working Stage 3.11.

## Reference Documentation
**Required:**
- Design: docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md

**Additional References:**
- docs/planning/2026-07-17-fix219-architecture-convergence/research/gnome-helper-pressure-and-repaint.md
- docs/planning/2026-07-17-fix219-architecture-convergence/research/performance-baseline.md
- docs/planning/2026-07-17-fix219-architecture-convergence/iteration-checklist.md
- .code-assist/2026-07-17-fix219-architecture-convergence/step03/plan.md
- .code-assist/2026-07-17-fix219-architecture-convergence/step03/progress.md
- docs/support/validation/fix219-pre-migration/performance/README.md

**Note:** Read the detailed design before implementation and preserve the fix219 backend boundary.

## Technical Requirements
1. Add focused RED unit tests before modifying stable-query behavior; keep tests and implementation in this task.
2. Model stable matching state explicitly behind the GNOME backend with an injected monotonic clock and bounded deadline.
3. Ensure stable matching follow cycles inside the deadline do not issue synchronous helper target enumeration solely because the transition guard is active.
4. Permit the required query at deadline expiry and promptly re-establish stable suppression after success.
5. Immediately invalidate or bypass suppression for explicit presentation refresh, failed/unavailable results, target loss/recovery, presenter or mode transitions, stale raster state, and relevant focus, monitor, geometry, workspace, minimize, fullscreen, or exposure changes.
6. Preserve the cold-start deferred-remap refresh so it bypasses matching-success and mismatch suppression exactly once and then returns to steady no-op behavior.
7. Preserve startup, unfocused attachment, focus, placement, transitions, Alt-Tab, Overview, click-through, recovery, privacy, and all Phase 19 invariants.
8. Do not add compositor-private imports or enum dispatch to generic follow/runtime consumers.
9. Keep high-frequency diagnostics dev-gated and aggregated; do not add per-cycle release logging.
10. If `load.py`, EDMC hooks, lifecycle, or Tk wiring is touched unexpectedly, add a harness test before landing; otherwise use unit tests.

## Dependencies
- Task 04 must have established and proven quiet state.
- Existing cold-start and one-shot refresh behavior is an unchanged contract, not a redesign target.
- Task 06 builds on the stabilized query path; Task 07 measures the integrated result.

## Implementation Approach
1. Trace the existing suppression, transition guard, force-refresh, and invalidation paths without changing them.
2. Add RED cases for stable cycles, deadline expiry, transition-guard interaction, forced refresh, failure/recovery, every named invalidation input, and post-remap exactly-once refresh.
3. Apply the smallest backend-owned correction and drive the focused suite GREEN.
4. Run the query/follow regression slice and record exact commands and results.

## Acceptance Criteria

1. **Stable-Cycle Suppression**
   - Given a matching successful target/presentation snapshot inside the monotonic deadline
   - When repeated generic follow cycles run with the transition guard active
   - Then no synchronous helper target query occurs

2. **Bounded Refresh**
   - Given otherwise unchanged stable state
   - When the deadline expires
   - Then exactly the required refresh query occurs and successful state returns to suppression

3. **Immediate Invalidation and Recovery**
   - Given any named failure, target, presentation, raster, focus, geometry, workspace, visibility, or explicit-refresh condition
   - When the next relevant cycle runs
   - Then stale suppression is bypassed and recovery is not delayed behind the stable deadline

4. **Cold-Start One-Shot Contract**
   - Given a deferred-remap presentation refresh request
   - When follow cycles continue
   - Then it bypasses suppression exactly once and subsequent stable cycles are no-ops

5. **Focused RED/GREEN Evidence**
   - Given the new behavior tests
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py -q` is run
   - Then the intended pre-fix failures and post-fix passing result are recorded

6. **Architecture and Behavior Preservation**
   - Given the completed diff
   - When imports and behavior assertions are reviewed
   - Then the cache remains backend-owned and all cold-start, Phase 19, focus, click-through, recovery, and privacy invariants remain intact

## Metadata
- **Complexity**: High
- **Labels**: fix219, gnome-wayland, target-cache, performance, tdd, stage-1.7
- **Required Skills**: Python state machines, monotonic-clock testing, GNOME helper integration, pytest
