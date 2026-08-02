# Task: Suppress Proven Unchanged Repaint Work

## Description
Attribute repeated repaint work using bounded per-reason evidence, then suppress only requests proven to leave rendered output unchanged. Extend the existing visual-snapshot/deduplication seams instead of assuming dedupe is absent, and keep request, Qt update/paint, frame construction, and Shell raster presentation as separately measured contracts.

## Background
Incident-era evidence showed roughly follow-cadence repaint activity, but it did not prove which layer created material work. Existing payload snapshots can refresh TTL or metadata without necessarily changing pixels. This task performs the smallest test-driven correction after attribution. It is authoritative Stage 1.8 and working Stage 3.12.

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

## Technical Requirements
1. Use bounded aggregate counters to identify the repaint-request sources and distinguish scheduling, Qt paint, frame build, raster reuse, and presentation work before changing behavior.
2. Add focused RED tests before implementation; keep tests and implementation in this functional task.
3. Define or extend a deterministic visual fingerprint at the smallest pure seam without leaking backend-private behavior into generic consumers.
4. Allow TTL-only and metadata-only refreshes to update lifecycle state without scheduling Qt update, rebuilding an identical frame, or refreshing backend presentation.
5. Preserve repaint for every supported content, style, geometry, grouping, override, expiry, animation, scale, mode, monitor, transition, visibility/recovery, and explicit-refresh change that affects output or correctness.
6. Preserve a safe repaint fallback for unknown, incomplete, or unprovable payload state.
7. Preserve startup, focus, click-through, Phase 19 atomic presentation, recovery, and privacy behavior.
8. Keep diagnostics low-overhead, dev-gated where detailed, and free of per-cycle journal spam.
9. Add a harness test only if `load.py`, EDMC hooks, lifecycle, or Tk wiring is touched; pure/runtime changes require unit tests.

## Dependencies
- Task 05 must stabilize helper-query behavior so attribution is not confounded by the known query loop.
- Existing payload dedupe and repaint debounce behavior must be audited before selecting the seam.
- Task 07 measures the integrated query and repaint result.

## Implementation Approach
1. Instrument bounded per-reason counts at existing seams and collect a short attribution observation.
2. Add RED cases for identical visuals, TTL-only and metadata-only updates, every required visual trigger, and unknown-state fallback.
3. Implement the narrowest no-op suppression that satisfies those tests.
4. Run the payload/repaint/follow regression slice and record exact RED/GREEN evidence.

## Acceptance Criteria

1. **Evidence-Led Attribution**
   - Given stable repeated payloads
   - When bounded counters are reviewed
   - Then the responsible request, paint, frame, raster, and presentation layers are distinguishable without per-cycle logs

2. **Unchanged-Output Suppression**
   - Given a payload whose rendered output is identical and whose change is TTL-only or metadata-only
   - When it is processed
   - Then lifecycle metadata may refresh but unnecessary update, frame-build, and presentation work is not scheduled

3. **Required Repaint Preservation**
   - Given any supported visual, expiry, animation, scale, transition, monitor, visibility, recovery, or explicit-refresh change
   - When it is processed
   - Then the necessary repaint and presentation path still runs

4. **Safe Unknown Fallback**
   - Given payload state whose visual equivalence cannot be proven
   - When it is processed
   - Then the system repaints safely instead of silently dropping work

5. **Focused RED/GREEN Evidence**
   - Given the new repaint behavior tests
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_payload_dedupe.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py -q` is run
   - Then the intended pre-fix failures and post-fix passing result are recorded

6. **Boundary Preservation**
   - Given the completed diff
   - When architecture and behavior tests are reviewed
   - Then no compositor-specific behavior has leaked into generic code and all established invariants remain intact

## Metadata
- **Complexity**: High
- **Labels**: fix219, repaint, deduplication, performance, tdd, stage-1.8
- **Required Skills**: Python rendering pipelines, deterministic fingerprints, performance attribution, pytest
