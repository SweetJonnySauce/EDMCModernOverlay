# Task: Run Controlled Helper Pressure A/B

## Description
Validate the integrated stable-query and unchanged-repaint reductions with the approved four-cell quiet A/B. Produce a privacy-safe reviewed report containing pressure-reduction acceptance bounds. These bounds are specific to this A/B and must never populate or modify `thresholds.json`.

## Background
The A/B separates extension-idle cost from client-driven helper-loop cost by independently varying client and helper state. Incident samples and shortened exploratory runs may guide investigation but cannot establish acceptance. This is authoritative Stage 1.9 and working Stage 3.13.

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
1. Run A1 client stopped/helper disabled, A2 client running/helper disabled, B1 client stopped/helper enabled, and B2 both running/helper enabled.
2. Hold stable windowed monitor A at 100% scale with fixed environment and workload inputs; keep capture diagnostics off in all cells.
3. Use a five-minute warm-up and three 60-second samples per cell, interleaving order where practical and recording the order.
4. Collect only approved helper-query, repaint/frame-work, and idle-CPU measures with bounded privacy-safe diagnostics.
5. Stop immediately on visible GNOME Shell instability and leave the task incomplete; do not reproduce the Firefox failure as an acceptance activity.
6. Derive and review pressure-reduction acceptance bounds from the repeated quiet A/B, not from intuition, incident data, or one favorable sample.
7. Store those bounds and provenance only in the A/B report; do not create or change migration `thresholds.json`.
8. Short exploratory samples may be recorded as non-acceptance diagnostics but do not replace the required run unless an explicit plan amendment changes the gate.
9. Run the integrated query/repaint automated gate before accepting live A/B evidence.
10. Do not resume the old matrix or create the clean post-optimization evidence identity.

## Dependencies
- Tasks 04–06 must be complete.
- The 12 reduced-v2 and two superseded full-v1 captures remain immutable and excluded from this A/B population.
- Task 08 begins only after the A/B result is reviewed and accepted.

## Implementation Approach
1. Re-run the focused query/repaint tests and the integrated project checks under the tiered policy.
2. Fix the environment and capture the four cells with required warm-up, repetitions, ordering, and safety observation.
3. Produce a sanitized deterministic report, calculate pressure bounds, and review attribution and visible behavior.
4. Record pass, investigate, blocked, or incomplete status without weakening a required gate silently.

## Acceptance Criteria

1. **Complete Controlled Design**
   - Given the approved A1/A2/B1/B2 protocol
   - When acceptance evidence is collected
   - Then all four cells contain three post-warm-up 60-second samples under fixed quiet conditions

2. **Material Pressure Reduction**
   - Given the repeated A/B results
   - When query, repaint/frame-work, and idle-CPU deltas are reviewed
   - Then the amended implementation satisfies explicitly recorded pressure-reduction acceptance bounds without an invariant or visible-behavior failure

3. **Threshold Separation**
   - Given the reviewed A/B bounds
   - When artifacts are inspected
   - Then the bounds exist only in the A/B report and no migration-regression `thresholds.json` has been created or modified

4. **Safety and Privacy**
   - Given a measurement run
   - When Shell instability or prohibited data appears
   - Then measurement stops or the artifact is rejected, and the stage cannot pass

5. **Tiered Automated Gate**
   - Given the integrated Task 05 and Task 06 changes
   - When the focused suites, `make check PYTHON=overlay_client/.venv/bin/python`, `make test PYTHON=overlay_client/.venv/bin/python`, and `git diff --check` are run
   - Then exact pass/fail/skip outcomes are recorded before A/B acceptance

6. **No Silent Shortcut**
   - Given only shortened exploration or missing required cells/repetitions
   - When completion is evaluated
   - Then Stage 3.13 remains incomplete unless an explicit plan amendment changes the gate and records residual risk

## Metadata
- **Complexity**: High
- **Labels**: fix219, gnome-wayland, ab-validation, performance, evidence, stage-1.9
- **Required Skills**: GNOME/Wayland validation, controlled experiment design, performance analysis, privacy review
