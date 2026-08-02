# Task: Establish Quiet Measurement State

## Description
Establish and prove the diagnostics-off normal-use state required before Step 3 pressure work. Back up the user-local GNOME helper configuration, disable capture-only diagnostics without disturbing unrelated fields, restore client settings to documented quiet values, and verify that stable operation does not emit per-query journal events. Do not change runtime code or create a post-optimization evidence identity in this task.

## Background
The retained reduced-v2 matrix was captured with diagnostics enabled and is paused at 12/42. Those captures and the two superseded full-v1 captures are immutable historical evidence. Pressure measurements need a quiet configuration so diagnostic overhead is not mistaken for helper or repaint cost. This is authoritative Stage 1.6 and working Stage 3.10; executing it requires separate implementation authorization.

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

**Note:** Read the detailed design and the current-state/supersession sections of the additional references before execution.

## Technical Requirements
1. Read and make a recoverable backup of the user-local GNOME helper configuration before changing it; preserve every unrelated field.
2. Restore `overlay_settings.json`, `dev_settings.json`, and helper diagnostic controls to the documented quiet normal-use values.
3. Verify high-frequency query/repaint diagnostics are disabled while bounded aggregate counters, state changes, and normalized failures remain available where designed.
4. Demonstrate that a stable quiet observation produces no per-query journal event stream.
5. Record exact before/after configuration facts and verification commands without tokens, paths, raw handles, titles, command lines, or broad environment dumps.
6. Do not modify runtime code, resume either historical matrix, create captures, or create a new manifest/evidence identity.
7. Preserve all 12 reduced-v2 captures and both superseded full-v1 captures exactly.
8. Keep the stage incomplete if configuration cannot be backed up or quiet state cannot be proven.

## Dependencies
- Step 3 Tasks 01–03 remain historical predecessors and must not be edited.
- The synchronization review is approved, but task execution begins only with explicit Stage 1.6 authorization.
- Task 05 depends on this quiet-state precondition.

## Implementation Approach
1. Record the current configuration and historical-evidence inventory without modifying either.
2. Back up the helper configuration, then make the smallest reversible diagnostic-setting changes.
3. Run a bounded stable observation and inspect allowlisted diagnostics for absence of per-query events.
4. Record the result and rollback instructions in the Step 03 progress/evidence documentation.

## Acceptance Criteria

1. **Recoverable Configuration Change**
   - Given the existing client and helper settings
   - When quiet state is established
   - Then the helper configuration has a recoverable backup and unrelated settings are unchanged

2. **Quiet Diagnostic Proof**
   - Given stable normal use with capture diagnostics disabled
   - When a bounded journal observation is reviewed
   - Then no per-query event stream is present and only approved bounded diagnostics remain

3. **Historical Evidence Preservation**
   - Given the 12 reduced-v2 and two superseded full-v1 captures
   - When this task completes
   - Then their identities and contents are unchanged and neither matrix has resumed

4. **Scope Boundary**
   - Given this operational preparation task
   - When its diff and evidence are reviewed
   - Then it contains no runtime-code change, new capture, new evidence identity, or premature threshold artifact

## Metadata
- **Complexity**: Medium
- **Labels**: fix219, diagnostics, configuration, performance-preflight, privacy, stage-1.6
- **Required Skills**: GNOME helper operations, configuration safety, privacy-safe diagnostics
