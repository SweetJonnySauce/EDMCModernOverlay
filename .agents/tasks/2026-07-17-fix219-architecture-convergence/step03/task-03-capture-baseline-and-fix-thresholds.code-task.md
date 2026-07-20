# Task: Capture Baseline and Fix Thresholds

## Description
Capture and publish the required sanitized pre-migration performance baseline on GNOME Shell 46 with Ubuntu 24.04.4 using the shipped architecture, then derive and record fixed investigation thresholds from repeated variance. This evidence gate must be complete before Step 5 changes production routing.

## Background
The current architecture is the behavioral and performance oracle for later migration comparisons. Automated tooling alone cannot establish compositor-visible smoothness, Alt-Tab/Overview behavior, black/intermediate-surface absence, or the actual baseline distribution on the target environment. This task combines repeatable capture execution, artifact validation, manual invariant review, and immutable threshold selection; it must remain incomplete if the target environment is unavailable.

## Reference Documentation
**Required:**
- Design: docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/planning/2026-07-17-fix219-architecture-convergence/research/performance-baseline.md (target environment, scenarios, measures, comparison policy, and evidence artifacts)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Run the validated scenario manifest on Ubuntu 24.04.4 LTS with GNOME Shell 46 using the current shipped architecture before any Step 5 production-routing change.
2. Capture uniform 100% and 125% scale; two horizontal monitors; both transition and fullscreen-handoff directions; one negative-coordinate arrangement; stable modes; Alt-Tab; and Overview using the fixed fixture, warm-up, duration, repetitions, and diagnostic toggles.
3. Record plugin/client/helper versions, environment key, display layout, scenario result, safe diagnostic reference, and manual invariant checklist without screenshots, secrets, personal paths, arbitrary titles, commands, raw IDs, or broad environment dumps.
4. Store raw sanitized captures, deterministic summaries, manual observations, and comparison-ready metadata under the versioned release validation evidence tree defined by the detailed design.
5. Use repeated baseline distributions to choose both relative investigation thresholds and absolute noise floors for latency, work, and idle CPU before the first migrated comparison.
6. Record threshold rationale and provenance in a versioned artifact that candidate comparison treats as read-only; later changes require explicit documented re-review.
7. Treat every Phase 19 invariant failure, dual-visible presenter, title-bar/monitor-relative intermediate, black surface, focus trap, unexpected identity, or material hitch as a blocking baseline problem.
8. Add or update validation tests that load every committed capture/summary/threshold artifact, verify manifest linkage and bounds, and assert privacy exclusions.
9. Do not mark Step 3 complete or permit Step 5 routing work if the target environment, required scenario, sanitized artifact, or threshold record is missing.

## Dependencies
- Step 3 Tasks 1 and 2 provide the validated scenario manifest, summary generator, comparison semantics, and privacy enforcement.
- Existing developer diagnostics for presentation, helper, raster, repaint, transition, and CPU work must be enabled consistently without changing release defaults.
- A maintainer-accessible GNOME Shell 46/Ubuntu 24.04.4 environment with the required two-monitor layouts and scale settings is mandatory.

## Implementation Approach
1. Prove the manifest and summary tool against synthetic fixtures, then record the exact capture command/workflow and target-environment metadata.
2. Execute every required scenario for the configured repetitions, reviewing visible behavior and the invariant checklist during capture.
3. Sanitize and validate raw evidence before committing it, generate deterministic summaries, and rerun privacy/manifest-link tests.
4. Analyze repeated variance, select conservative relative thresholds plus absolute noise floors, record the rationale, and freeze the artifact before Step 5 begins.

## Acceptance Criteria

1. **Complete Target Baseline**
   - Given GNOME Shell 46 on Ubuntu 24.04.4 with the required display arrangements
   - When the approved manifest is executed
   - Then every required 100% and 125% scenario has the configured repetitions, sanitized raw evidence, deterministic summary, and manual checklist

2. **Phase 19 Invariants Remain the Oracle**
   - Given each stable mode, transition, handoff, Alt-Tab, and Overview scenario
   - When its evidence is reviewed
   - Then no dual-visible presenter, title-bar/monitor-relative intermediate, black surface, focus trap, unexpected identity, premature commitment, or material hitch is accepted

3. **Fixed Threshold Provenance**
   - Given repeated baseline variance for latency, work, and idle CPU
   - When investigation thresholds are selected
   - Then each relative limit and absolute noise floor has recorded data provenance and rationale and is fixed before candidate comparison

4. **Reviewable Privacy-Safe Evidence**
   - Given the complete evidence tree
   - When automated privacy checks and a human review inspect it
   - Then it contains no token, raw owner ID, target handle, personal path, arbitrary title, command line, screenshot, or broad environment dump

5. **Automated Artifact Validation**
   - Given all committed manifests, raw captures, summaries, and thresholds
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_performance_summary.py tests/test_debug_collectors.py -q` and `git diff --check` are run
   - Then both commands pass and every artifact resolves to the approved manifest and schema

6. **Routing Gate Enforcement**
   - Given the target environment or any mandatory scenario/evidence/threshold is unavailable
   - When Step 3 completion is evaluated
   - Then Step 3 remains incomplete with the blocker documented; Steps 1–2 may stand, but Step 5 production routing does not begin

7. **Step Demo Artifact**
   - Given the completed pre-migration capture set
   - When the summary tool processes it
   - Then it produces a sanitized comparison-ready baseline for every required scenario using the shipped architecture

## Metadata
- **Complexity**: High
- **Labels**: fix219, performance-baseline, manual-validation, evidence, thresholds, phase-1
- **Required Skills**: GNOME/Wayland validation, performance capture, statistical interpretation, privacy review, pytest
