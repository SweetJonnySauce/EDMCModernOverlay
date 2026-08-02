# Task: Validate Manual Regressions and Quiet Soak

## Description
Run the amended Step 3 manual compositor regression and quiet-soak gate after the controlled A/B passes. Prove that pressure reduction preserves cold start, attachment, focus, click-through, transitions, monitor placement, Alt-Tab, Overview, recovery, privacy, and Phase 19 presentation invariants.

## Background
Unit tests and counters cannot prove compositor-visible behavior. The manual gate requires two terminal-focused clean starts, one game-focused start, transition and monitor coverage, interaction checks, and a quiet soak. Deferral is allowed operationally, but it leaves this task incomplete. This is authoritative Stage 1.10 and working Stage 3.14.

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
1. Perform two terminal-focused clean starts and one game-focused clean start with diagnostics in quiet normal-use state.
2. Validate windowed and borderless-fullscreen transitions, both monitor directions, correct placement, focus behavior, click-through, Alt-Tab, and Overview.
3. Prove no dual-visible presenters, title-bar or monitor-relative intermediate, black surface, focus trap, unexpected task-list/Overview identity, premature renderer commitment, or material hitch.
4. Validate target loss/recovery, helper failure/recovery where safely supported, and the cold-start deferred-remap one-shot refresh contract.
5. Run the planned quiet soak and record bounded resource/work evidence and normalized failures.
6. Stop on Shell instability; do not intentionally reproduce unrelated application failures.
7. Record sanitized results without screenshots, secrets, personal paths, arbitrary titles, command lines, raw IDs/handles, or broad environment dumps.
8. Do not resume the old matrix or create a post-optimization evidence identity.
9. If any mandatory check is deferred or unavailable, leave Stage 3.14 incomplete unless an explicit plan amendment changes the gate.

## Dependencies
- Task 07's controlled A/B must be complete and reviewed.
- Tasks 05–06 supply the implementation under validation.
- Task 09 cannot create a new evidence identity until this gate passes.

## Implementation Approach
1. Confirm the quiet configuration and approved A/B result.
2. Execute clean-start, transition, monitor, interaction, recovery, and soak checks in the documented order.
3. Stop and diagnose at the first invariant or Shell-stability failure.
4. Append a sanitized per-check outcome and exact deferral reason, if any, to the working progress/evidence record.

## Acceptance Criteria

1. **Clean-Start Coverage**
   - Given quiet GNOME Shell operation
   - When two terminal-focused and one game-focused clean starts are performed
   - Then attachment, placement, exposure, focus, click-through, and exactly-once refresh behavior pass each required observation

2. **Phase 19 and Interaction Preservation**
   - Given mode transitions, monitor handoffs, Alt-Tab, and Overview
   - When each scenario is exercised
   - Then presentation remains atomic and none of the named visible, focus, identity, or commitment regressions occurs

3. **Recovery and Soak**
   - Given supported target/helper recovery cases and the planned quiet soak
   - When validation completes
   - Then recovery is prompt, stable work remains bounded, and no normalized failure or Shell instability blocks acceptance

4. **Privacy-Safe Traceability**
   - Given the manual validation record
   - When it is reviewed
   - Then every required check has a result and the record contains no prohibited personal or runtime-identifying data

5. **Incomplete Means Incomplete**
   - Given any deferred mandatory compositor or soak check
   - When stage status is updated
   - Then the task and Stage 3.14 remain incomplete unless an explicit approved plan amendment changes the gate

## Metadata
- **Complexity**: High
- **Labels**: fix219, gnome-wayland, manual-validation, phase19, soak, stage-1.10
- **Required Skills**: GNOME/Wayland compositor validation, UI behavior testing, operational safety, evidence review
