# Task: Freeze and Verify the Backend Baseline

## Description

Establish a current, recoverable baseline for the approved circle-feature merge
before any merge state exists. Fetch the remote references, verify that the
checked-out target branch is clean and still matches the assessed topology,
create a local backup ref at the verified target tip, and record the resulting
evidence in the approved tracking documents. This task deliberately stops
before creating a merge.

## Background

The approved integration merges `feature/circle-shape-pyqt-rendering` into
`backend-refactor-implementation`, with the backend refactor remaining the
structural baseline. The merge assessment identified target `40d3a40`, source
`0d789cb`, and merge base `8e375cc`; the subsequent documentation preflight
advanced the target to `9856ff9` without changing the reviewed source or merge
base. A fresh fetch and topology check are required before manipulating refs,
so an out-of-date or materially changed source cannot silently enter the
merge.

This is a Git/documentation-only task. It must not start a merge, change source
code, stage a merge result, or modify `overlay_groupings.json`.

## Reference Documentation

**Required:**
- Design: `docs/plans/2026-08-27-circle-feature-backend-merge/design/detailed-design.md`
- Approved plan: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/plan.md`
- Orchestration constraints: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/orchestration-prompt.md`

**Additional References (if relevant to this task):**
- Merge assessment: `docs/plans/2026-08-27-circle-feature-backend-merge/research/merge-assessment.md`
- Decisions and caveat: `docs/plans/2026-08-27-circle-feature-backend-merge/idea-honing.md`
- Repository instructions: `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read the approved plan, orchestration constraints, and merge
assessment completely before performing Git operations.

## Technical Requirements

1. Work only while `git branch --show-current` reports
   `backend-refactor-implementation`; do not switch branches, create a merge,
   or alter the source branch.
2. Run `git fetch origin` once, then capture the current target/source tips,
   merge base, current branch, short worktree status, staged-path status, and
   merge-state status. Do not rerun an unchanged failing command.
3. Require a clean target worktree and no `MERGE_HEAD` before creating the
   backup ref. If either condition is not met, stop with the exact evidence and
   request direction; do not clean, reset, restore, or overwrite anything.
4. Compare fetched topology with the assessment. A target-only documentation
   advance is acceptable when it is explainable from history; a materially
   changed source tip or merge base requires a refreshed merge assessment
   before any later merge stage.
5. Create one uniquely named local backup ref under
   `refs/backup/circle-feature-backend-merge/` that points exactly to the
   verified target SHA. Record its full ref name and resolved object SHA, and
   do not move or delete an existing backup ref.
6. Record the evidence and outcome in the approved plan/progress/dashboard
   only after the commands succeed: mark Phase 1 stages 1.1 and 1.2 completed,
   retain 1.3 and 1.4 as already completed only if the fetched evidence still
   supports them, and set Phase 1 to Completed only when all four stages are
   supported. Preserve the existing ordering and stage numbering.
7. Do not run `git merge`, `git merge --abort`, `git reset`, `git checkout --`,
   `git restore`, `git add`, `git commit`, or any command that changes
   `overlay_groupings.json`. The configuration must have no worktree or staged
   diff when this task ends.
8. No unit or harness test is required because this task changes no executable
   behavior. Git preflight checks are the required validation; record that test
   selection and its residual risk in the handoff.

## Dependencies

- The Step 0 documentation preflight is complete and the target branch is
  already checked out.
- `origin` is reachable for the required fetch; a fetch failure blocks this
  task rather than permitting use of stale refs.
- The tracking files named by the orchestration prompt are available and may
  be updated only with command-backed evidence.

## Git Preflight Evidence

Read-only evidence captured while generating this task, before the required
fresh fetch:

- Current branch: `backend-refactor-implementation`, tracking
  `origin/backend-refactor-implementation`.
- Worktree: clean (`git status --short` produced no paths); staged-path listing
  was empty; `MERGE_HEAD` was absent.
- Target tip: `9856ff9fa066bf973f9f8b94b4454afbb006c60c`
  (`docs(plan): record merge orchestration preflight`).
- Source tip: `0d789cbbea77dac500eb7b249d71df67c1dbde9c`
  (`feat(render): use square corners for explicit rectangle strokes`).
- Merge base: `8e375cce40acc0d9400bde43d6aa01070929adb4`.
- Both `origin/backend-refactor-implementation` and
  `origin/feature/circle-shape-pyqt-rendering` refs existed locally.

This evidence is a starting point, not a substitute for the required
post-fetch evidence. Do not proceed to Step 2 if the fetched source tip or
merge base materially differs from the assessment until the assessment has
been refreshed.

## Implementation Approach

1. Read the required references and inspect the current Git state without
   modifying it. Emit the orchestration status line for the Step 1 task.
2. Fetch `origin` once. Re-run the specified read-only preflight commands and
   compare their output with the Git Preflight Evidence and merge assessment.
3. If the branch, clean state, no-merge state, source tip, and merge base pass
   the guard conditions, create a timestamped backup ref with an explicit
   target SHA, for example:
   `git update-ref refs/backup/circle-feature-backend-merge/backend-refactor-implementation-YYYYMMDDTHHMMSSZ <verified-target-sha>`.
   Verify it with `git rev-parse`.
4. Update only the approved plan, progress tracker, and execution dashboard
   with the exact commands, output-derived SHAs, backup-ref name, and stage
   outcomes. Leave all implementation files and managed configuration
   untouched.
5. Finish with the required concise handoff structure exactly: `Status; Files
   changed; Validation commands/results; Decisions; Risks; Next exact action.`
   The next action must be the main-orchestrator review of this task's evidence
   and scope before generating Step 2 tasks.

## Acceptance Criteria

1. **Current target topology is verified**
   - Given the repository is on `backend-refactor-implementation`
   - When `git fetch origin` and the required post-fetch status, tip, and
     merge-base commands run successfully
   - Then the recorded branch, target SHA, source SHA, and merge-base SHA are
     command-backed and are compared to the approved merge assessment.

2. **Unsafe preflight state blocks progress**
   - Given the target worktree is dirty, a merge is in progress, the checked-out
     branch is not the target, or the fetch/topology check materially disagrees
     with the assessment
   - When the preflight guard is evaluated
   - Then no backup ref or merge is created, no files are cleaned or restored,
     and the task stops with the exact blocking evidence and required next
     decision.

3. **Recoverable target backup exists**
   - Given the fetched target worktree is clean and no merge is in progress
   - When the backup-ref command runs with the verified target SHA
   - Then a unique ref beneath
     `refs/backup/circle-feature-backend-merge/` resolves exactly to that SHA
     and its name and target are recorded.

4. **No merge or managed-configuration change occurs**
   - Given the Step 1 preflight completes
   - When Git status, staged paths, merge state, and the configuration path are
     checked before handoff
   - Then no merge has been started, `overlay_groupings.json` has no staged or
     worktree diff, and no source implementation file has changed.

5. **Tracking reflects verified evidence only**
   - Given the Git evidence and backup-ref verification succeeded
   - When the approved plan, progress tracker, and execution dashboard are
     updated
   - Then Phase 1 stages and status are changed only as supported by that
     evidence, and the records include exact commands/results and the backup
     ref.

6. **Test selection is explicit**
   - Given this task contains no executable behavior change
   - When validation is recorded
   - Then no unit or harness test is added or run, the reason is documented as
     Git/documentation-only scope, and the residual risk is limited to stale or
     changed Git topology detected by the required preflight checks.

## Metadata

- **Complexity**: Low
- **Labels**: Git, Preflight, Merge Preparation, Documentation, Backend Refactor
- **Required Skills**: Git topology inspection, safe ref management, evidence-based documentation, repository workflow compliance
