# Task: Capture Clean Baseline and Freeze Migration Thresholds

## Description
After all pressure-reduction and manual gates pass, create a new post-optimization evidence identity, execute the clean 14-scenario by three-repetition baseline from 0/42, review it, and freeze versioned migration-regression thresholds. Finish Step 3 evidence synchronization and the final test gate without altering historical captures.

## Background
The 12 reduced-v2 captures and two superseded full-v1 captures describe the pre-optimization/incident era and cannot serve as the migrated comparison oracle. The clean baseline must be a coherent population collected after pressure reduction. Its migration-regression thresholds are distinct from Task 07's A/B pressure-reduction bounds. This covers authoritative Stage 1.11 and working Stages 3.15–3.16, and supersedes the execution intent—not the immutable file—of historical Task 03.

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
1. Verify Stages 3.10–3.14 are complete before creating any new manifest or evidence identity.
2. Create a unique post-optimization manifest/evidence identity and begin it at 0/42; do not relabel, copy into, or mix any historical capture.
3. Capture all 14 representative scenarios at three repetitions on the required GNOME Shell 46/Ubuntu 24.04.4 environment with fixed fixture, geometry, scale, warm-up, duration, diagnostic, and clock-domain inputs.
4. Cover uniform 100% and 125%, stable windowed/fullscreen, both transition directions, both fullscreen monitor handoffs, Alt-Tab, Overview, and the required negative-coordinate arrangement.
5. Validate every capture against its new manifest and privacy schema; reject incomplete, incompatible, unsanitized, or invariant-failing evidence.
6. Generate deterministic JSON and human-readable summaries only after all 42 required captures exist and manual review passes.
7. Derive versioned migration-regression thresholds from the coherent repeated baseline variance, with a positive absolute noise floor and relative investigation limit for every required latency, work, repaint/frame, and idle-CPU metric.
8. Record threshold provenance, rationale, capture date, three-repetition basis, reviewed/frozen state, and sanitized diagnostic references in `thresholds.json`.
9. Never infer, auto-tune, or overwrite migration thresholds during later candidate comparison; never import Task 07 A/B bounds into `thresholds.json`.
10. Preserve every cold-start, one-shot refresh, Phase 19, focus, click-through, recovery, privacy, and fix219 backend-boundary invariant.
11. Run the focused performance/artifact tests, full integrated gates, and patch hygiene before Step 3 completion.
12. Update authoritative plan/evidence and chronological progress records without rewriting historical entries; commit the reviewed completed increment without pushing.
13. If the target environment, any capture, manual review, threshold record, or required test is missing, leave Task 09 and Step 3 incomplete unless an explicit plan amendment changes the gate.

## Dependencies
- Tasks 04–08 must be complete and accepted.
- Existing Tasks 01–02 provide manifest, capture, summary, comparison, and privacy tooling.
- Existing Task 03 and its partial execution history remain unchanged historical context.
- Step 5 production routing remains blocked until this task completes.

## Implementation Approach
1. Audit prerequisite stage status and snapshot the immutable historical evidence inventory.
2. Create and validate the new identity, then execute the fixed matrix from 0/42 with per-capture manual review.
3. Validate privacy and manifest linkage, generate deterministic summaries, and review the coherent distribution.
4. Select and freeze migration-regression thresholds with explicit provenance and rationale.
5. Run final tests, update authoritative status/evidence, review the complete diff, and commit without pushing.

## Acceptance Criteria

1. **New Identity Gate**
   - Given completed Tasks 04–08
   - When clean baseline work begins
   - Then a unique post-optimization identity starts at 0/42 and all historical capture identities and contents remain unchanged

2. **Complete Coherent Baseline**
   - Given the approved target environment and manifest
   - When capture completes
   - Then all 42 repetitions validate under one fixed post-optimization identity with required scenario, scale, geometry, and manual coverage

3. **Invariant-First Review**
   - Given any capture with a Phase 19, focus, click-through, recovery, privacy, black/intermediate-surface, or visible-hitch failure
   - When baseline acceptance is evaluated
   - Then the baseline is blocked regardless of aggregate timing

4. **Migration-Threshold Provenance**
   - Given the complete reviewed 42-capture distribution
   - When `thresholds.json` is frozen
   - Then every required metric has a relative limit, positive absolute noise floor, provenance, and rationale derived only from that clean baseline

5. **Threshold-Type Separation**
   - Given Task 07's pressure-reduction acceptance bounds and this task's migration-regression thresholds
   - When artifacts are reviewed
   - Then they remain separately named, separately sourced, and only the latter appear in `thresholds.json`

6. **Automated Evidence Gate**
   - Given the complete evidence tree
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_performance_capture.py overlay_client/tests/test_backend_performance_summary.py tests/test_debug_collectors.py -q`, `make check PYTHON=overlay_client/.venv/bin/python`, `make test PYTHON=overlay_client/.venv/bin/python`, and `git diff --check` are run
   - Then exact pass/fail/skip outcomes are recorded and every artifact resolves to the approved manifest and schema

7. **Completion and Routing Gate**
   - Given any missing required capture, review, threshold, or test
   - When Step 3 status is evaluated
   - Then Step 3 remains incomplete and Step 5 production routing does not begin unless an explicit approved amendment changes the gate

## Metadata
- **Complexity**: High
- **Labels**: fix219, performance-baseline, migration-thresholds, evidence, manual-validation, stage-1.11
- **Required Skills**: GNOME/Wayland validation, performance capture, statistical interpretation, privacy review, pytest
