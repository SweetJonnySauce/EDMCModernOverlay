# Task: Run Automated Merge Validation and Integrity Review

## Description

Validate the active, resolved circle-feature merge on
`backend-refactor-implementation` using every approved automated gate, then
independently inspect the staged merge for integrity. Record command-backed
results in the approved plan, progress tracker, and execution dashboard. This
task is validation-only: it must not perform a live-overlay check, create a
merge commit, alter `overlay_groupings.json`, or make product-code changes.

## Background

Step 3 resolved the two expected conflicts against the backend baseline and
reviewed the auto-merged processor/paint paths. Focused GUI suites passed
(40 and 50 tests), with one scoped processor transform-snapshot correction.
The no-commit merge remains active and `overlay_groupings.json` has been
restored to the target version. Step 4 must now prove the integration across
the public API, raw/TCP processing, Qt painting, EDMC Python compatibility,
and the repository baseline before the user is asked to perform the separate
manual overlay gate in Step 5.

## Reference Documentation

**Required:**
- Design: `docs/plans/2026-08-27-circle-feature-backend-merge/design/detailed-design.md`
- Approved plan: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/plan.md`
- Orchestration constraints: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/orchestration-prompt.md`

**Additional References (if relevant to this task):**
- Merge assessment: `docs/plans/2026-08-27-circle-feature-backend-merge/research/merge-assessment.md`
- Current merge evidence: `docs/plans/2026-08-27-circle-feature-backend-merge/progress.md`
- Execution dashboard: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/execution-status.md`
- Completed Step 3 tasks: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/tasks/step03/`
- Repository instructions: `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read the approved plan, orchestration prompt, merge assessment,
progress tracker, dashboard, and the three Step 3 task handoffs completely
before running validation. Reconcile their claims with the current Git state
and command output; Git state and command output are authoritative.

## Technical Requirements

1. Work only while the current branch is `backend-refactor-implementation` and
   the existing no-commit merge remains active. First capture `git status
   --short`, `git diff --name-only --diff-filter=U`, and
   `git diff --cached --name-only`. An unresolved path, unexpected branch, or
   missing merge state is a blocker: make no corrective Git or code change and
   record exact evidence for the main orchestrator.
2. Run these required validation gates exactly, in this order, recording each
   complete command, exit status, and concise outcome. Do not rerun an
   unchanged failed command; a failed gate blocks Step 5 and must be handed
   back for a fresh, task-scoped remediation context or explicit user deferral.

   ```bash
   PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
     overlay_client/tests/test_render_surface_mixin.py \
     overlay_client/tests/test_paint_commands.py \
     tests/test_edmcoverlay_shapes.py \
     tests/test_legacy_processor.py \
     tests/test_harness_legacy_tcp_ingestion.py \
     tests/test_shape_gallery.py -q
   python3 scripts/check_edmc_python.py
   make check
   git diff --check
   ```
3. Treat the pytest set as mixed validation: the deterministic renderer,
   paint-command, public-payload, processor, and gallery cases are unit tests;
   `tests/test_harness_legacy_tcp_ingestion.py` is the required harness test
   for the raw/TCP lifecycle boundary. Do not add or alter tests in this task.
   If environment or dependency availability prevents a gate from running,
   record it as a failed/blocked gate with the exact cause, not as a pass or a
   discretionary skip.
4. Independently review the staged merge diff after the required gates. Use
   `git diff --cached --name-status`, `git diff --cached --stat`, and
   `git diff --cached` to inspect the staged paths and actual hunks. Confirm
   the backend refactor remains the structural baseline and that the staged
   content is limited to the approved circle integration, its tests,
   documentation, and gallery utility. Do not edit or stage product paths as
   part of this review.
5. Reconfirm managed-configuration preservation with all of the following:
   `git diff --exit-code -- overlay_groupings.json`,
   `git diff --cached --exit-code -- overlay_groupings.json`, and verification
   that `overlay_groupings.json` is absent from both
   `git diff --cached --name-only` and `git diff --cached --stat`. Any diff or
   presence is a merge blocker. Do not restore, edit, or substitute the file.
6. Run an independent staged conflict-marker scan with:

   ```bash
   git grep --cached -n -I -e '^<<<<<<< ' -e '^=======$' -e '^>>>>>>> ' --
   ```

   Exit status 1 means no markers and is the expected result; any output is a
   blocker. Also run `git diff --cached --check`; it must pass independently
   of the required `git diff --check` gate. Record both exact outcomes.
7. Do not run a live overlay, start the gallery against an overlay, perform
   manual visual inspection, create a commit, push, fetch, reset, abort the
   merge, switch branches, or modify `overlay_groupings.json`. Do not fix a
   failure in this context. This task has no product-code or test-file changes.
8. Record results only in the approved tracking files:
   `implementation/plan.md`, `progress.md`, and
   `implementation/execution-status.md`. Mark Phase 4 Stage 4.1 complete only
   when the focused unit/harness command passes; mark Stage 4.2 complete only
   when the EDMC compatibility script, `make check`, and both whitespace checks
   pass; keep Stage 4.3 Ready because manual overlay verification is outside
   this task. Do not mark Phase 4, Step 4, or any Phase 5 stage complete:
   automated validation alone does not satisfy the manual gate. Add the fresh
   code-assist context row and exact evidence without changing ordering or
   stage numbering.
9. Finish with exactly this five-part handoff, with no additional sections:
   `Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`
   The next exact action must be the main orchestrator asking the user to
   perform or explicitly authorize Step 5 manual overlay inspection, but only
   if every automated and integrity gate passed. If any gate failed or blocked,
   the next exact action must identify the required fresh remediation context
   or user decision instead.

## Dependencies

- Step 3 is complete: both known conflicts are resolved and staged, and the
  processor/paint command review has focused-test evidence.
- A no-commit merge of `feature/circle-shape-pyqt-rendering` into
  `backend-refactor-implementation` is still active.
- `overlay_groupings.json` is target-owned, already restored, and must remain
  absent from the staged merge diff.
- Step 5 owns live-overlay inspection and the local merge commit; neither is
  authorized here.

## Implementation Approach

1. Read the governing artifacts and completed Step 3 evidence, then reconcile
   branch, merge, staged-path, and unresolved-path state without mutation.
2. Run the four mandated gates once in the stated order. Capture exact
   command/result evidence; stop further progression on a failure rather than
   changing code or concealing it.
3. Independently inspect staged names, statistics, and hunks; run staged
   whitespace, conflict-marker, and grouping-configuration-absence checks.
4. Update only the three approved tracking documents from command-backed
   evidence, leaving Phase 4's manual stage and all commit work pending.
5. Produce the exact five-part handoff and return control to the main
   orchestrator for the user-gated Step 5 decision.

## Acceptance Criteria

1. **Required automated gates are completely evidenced**
   - Given the resolved active merge and available project environments
   - When the prescribed GUI-enabled pytest command, EDMC Python check,
     `make check`, and `git diff --check` run in their required order
   - Then every command, exit status, and pass/fail/blocked result is recorded
     exactly once, with no unchanged failing command rerun or silently skipped.

2. **Unit and harness coverage is selected explicitly**
   - Given the validation command includes deterministic rendering/processing
     tests and the raw/TCP lifecycle test
   - When the test evidence is recorded
   - Then unit coverage and the harness coverage are both identified, and no
     test is added or modified because this task validates integrated behavior
     rather than changing it.

3. **Staged merge integrity is independently confirmed**
   - Given all expected merge content is staged after Step 3
   - When staged names, statistics, and hunks are reviewed together with
     cached whitespace and conflict-marker checks
   - Then there are no unresolved paths, no staged conflict markers, no cached
     whitespace errors, and no unapproved scope or backend-boundary regression;
     otherwise the task reports the exact blocker without editing code.

4. **Managed configuration remains excluded**
   - Given `overlay_groupings.json` is target-owned
   - When staged and worktree path-scoped diffs plus cached path/stat listings
     are inspected
   - Then both diffs are empty and the file is absent from the staged merge;
     any deviation blocks handoff and is recorded without modifying the file.

5. **Tracking preserves the manual gate**
   - Given automated and integrity results are available
   - When the approved plan, progress tracker, and dashboard are updated
   - Then only successful automated stages receive command-backed completion,
     Stage 4.3 stays Ready, Phase 4 and Step 4 stay incomplete pending manual
     validation, and Phase 5 remains uncommitted.

6. **No manual or merge-finalization action occurs**
   - Given this Step 4 validation task completes
   - When repository state and the handoff are reviewed
   - Then no live overlay was started, no manual result was claimed, no merge
     commit or push occurred, and the next action is precisely the user-gated
     Step 5 manual inspection when all automated gates pass.

## Metadata

- **Complexity**: Medium
- **Labels**: Merge Validation, Qt Tests, Harness Tests, EDMC Compatibility, Git Integrity
- **Required Skills**: Test-gate execution, PyQt validation, harness validation, staged-diff review, merge-integrity auditing
