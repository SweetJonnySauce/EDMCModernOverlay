# Task: Create and Inspect the Non-committing Merge

## Description

Materialize the approved circle-feature merge into
`backend-refactor-implementation` without creating a commit, and preserve the
target-owned `overlay_groupings.json` immediately in both the index and
worktree. This task establishes a reviewable merge state only. It must inspect
and record the complete initial staged and conflicted scope before anyone
attempts conflict resolution; resolving, staging, or editing conflicts belongs
exclusively to Step 3.

## Background

Phase 1 completed a local topology check and created backup ref
`refs/backup/circle-feature-backend-merge/backend-refactor-implementation-20260827T163928Z`
at target `6d308e6df0107f440b601bfb571341e0286c1b80`. The approved direction is
to merge `feature/circle-shape-pyqt-rendering` into the checked-out
`backend-refactor-implementation` branch, retaining the backend refactor as
the architectural baseline.

The merge assessment predicts conflicts in
`overlay_client/render_surface.py` and
`overlay_client/tests/test_render_surface_mixin.py`, plus auto-merged runtime
paths that Step 3 must review. `overlay_groupings.json` is externally managed
and must remain exactly the target `HEAD` version, with no staged entry in the
eventual merge. This is Git-state work only; it must not change product code,
resolve a conflict, or create a merge commit.

## Reference Documentation

**Required:**
- Design: `docs/plans/2026-08-27-circle-feature-backend-merge/design/detailed-design.md`
- Approved plan: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/plan.md`
- Orchestration constraints: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/orchestration-prompt.md`

**Additional References (if relevant to this task):**
- Merge assessment: `docs/plans/2026-08-27-circle-feature-backend-merge/research/merge-assessment.md`
- Decisions and caveat: `docs/plans/2026-08-27-circle-feature-backend-merge/idea-honing.md`
- Progress evidence: `docs/plans/2026-08-27-circle-feature-backend-merge/progress.md`
- Execution dashboard: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/execution-status.md`
- Repository instructions: `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read the approved plan, orchestration prompt, merge assessment,
progress tracker, and dashboard completely before performing Git operations.

## Technical Requirements

1. Run non-network pre-merge guards immediately before the merge. Confirm the
   current branch is exactly `backend-refactor-implementation`; `MERGE_HEAD` is
   absent; `git status --short` is empty; `git diff --cached --name-only` is
   empty; the local target/source tips and merge base still match the recorded
   Phase 1 evidence; and the required backup ref resolves to the current target
   `HEAD`. Do not fetch, push, switch branches, clean, reset, or overwrite
   anything. If any guard fails, stop with exact evidence and request direction.
2. The only merge command is exactly:
   `git merge --no-commit --no-ff feature/circle-shape-pyqt-rendering`.
   Do not add merge strategies, use fast-forward mode, commit, abort, retry a
   failed unchanged command, or start a second merge if `MERGE_HEAD` appears.
3. Immediately after the merge command returns—whether it reports the expected
   conflicts or a clean merge—run exactly:
   `git restore --source=HEAD --staged --worktree overlay_groupings.json`.
   This restore is mandatory before any conflict inspection or other file
   action. Do not edit `overlay_groupings.json`.
4. Confirm the managed configuration has no worktree or staged difference from
   target `HEAD`, using path-scoped non-mutating diff commands. Confirm it is
   absent from both `git diff --cached --name-only` and
   `git diff --cached --stat`. A presence, diff, restore error, or unexpected
   content is a blocker; do not substitute a source version or manually edit it.
5. Before resolving, staging, editing, or choosing any conflict, inspect and
   record the **full initial merge scope**: short/porcelain status, unmerged
   paths (`git diff --name-only --diff-filter=U`), staged paths and staged
   statistics, unstaged paths/statistics, and a conflict-marker scan across the
   relevant non-documentation merge paths. Record whether the predicted two
   conflicts occurred and enumerate every additional conflict or unexpected
   changed path.
6. Do not resolve conflicts in this task. Specifically, do not edit,
   `git add`, `git rm`, `git checkout --ours/--theirs`, `git restore` (except
   the mandated target-HEAD grouping restore), `git merge --abort`, `git reset`,
   or otherwise modify any conflicted source/test file. Leave all non-grouping
   merge state intact for Step 3.
7. Run `git diff --check` after the initial scope inspection. It must be run
   and its exact result recorded. Also record conflict-marker scan results;
   expected unresolved markers must be identified by their unmerged paths and
   must not be treated as resolved. Any whitespace error or unexpected marker
   outside the known unresolved paths blocks handoff to Step 3.
8. Update only the approved plan, progress tracker, and execution dashboard
   after recording command-backed evidence: mark Phase 2 Stage 2.1 and 2.2
   completed only if the merge and immediate restore succeeded; mark Stage 2.3
   completed only after the full-scope inspection and grouping-absence checks
   pass. Keep Phase 2 otherwise in progress until all its stages are evidenced.
   Preserve existing ordering and stage numbering.
9. No unit or harness tests are added or run because this task changes no
   executable behavior. The required validation is Git-state inspection and
   `git diff --check`; state that selection and the remaining unvalidated
   renderer/runtime risk in the handoff.

## Dependencies

- Phase 1 is complete, including the verified target/source topology and the
  local backup ref at the target tip.
- The task artifact and all prior documentation must be committed or otherwise
  absent from the worktree before the clean-worktree guard; this task may not
  hide, stage, or discard them.
- The source branch remains available locally as
  `feature/circle-shape-pyqt-rendering`; no network operation is authorized.
- Step 3 has not begun and is the exclusive owner of conflict resolution and
  runtime-path review.

## Implementation Approach

1. Read all required references, emit the required Step 2 task status line,
   and run the non-network guards. Stop without side effects if Git state,
   topology, or backup-ref evidence no longer matches the approved baseline.
2. Execute the specified no-commit, no-fast-forward merge once. Immediately
   restore `overlay_groupings.json` from target `HEAD` in index and worktree.
3. Verify grouping-configuration absence, then capture the complete initial
   staged, unstaged, and unmerged scope before modifying any other path. Run
   `git diff --check` and the conflict-marker scan as observations only.
4. Record only command-backed Phase 2 evidence in the approved tracking files.
   Leave expected conflicts unresolved and all non-grouping merge content for
   the dedicated Step 3 contexts.
5. Finish with this exact five-part handoff, and no additional handoff sections:
   `Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`
   The next exact action must be main-orchestrator scope review followed by a
   fresh Step 3 task-generator context; it must not be conflict resolution in
   the current context.

## Acceptance Criteria

1. **Non-network pre-merge guard passes or blocks safely**
   - Given no merge has yet been started for Step 2
   - When the branch, clean-worktree, empty-index, no-`MERGE_HEAD`, local
     topology, and backup-ref guards are inspected without network access
   - Then the merge starts only on `backend-refactor-implementation` with the
     recorded Phase 1 baseline intact, or the task stops without changing Git
     state and reports the exact blocking evidence.

2. **Specified non-committing merge is created exactly once**
   - Given all pre-merge guards pass
   - When `git merge --no-commit --no-ff feature/circle-shape-pyqt-rendering`
     is executed
   - Then the source changes are materialized without a merge commit or branch
     switch, and any returned conflicts remain unresolved.

3. **Managed grouping configuration is immediately restored and absent**
   - Given the merge command has returned
   - When `git restore --source=HEAD --staged --worktree overlay_groupings.json`
     runs before any other file action
   - Then `overlay_groupings.json` exactly matches target `HEAD`, has neither
     a staged nor a worktree diff, and appears in neither cached path list nor
     cached stat output.

4. **Entire initial merge scope is inspected before resolution**
   - Given the grouping configuration has been restored
   - When status, staged, unstaged, unmerged, stat, and conflict-marker checks
     are run before any conflict-file modification
   - Then every changed and unmerged path is recorded, the expected render
     surface and render-surface-test conflicts are confirmed or discrepancy is
     reported, and unexpected scope is treated as a blocker for orchestrator
     review.

5. **Whitespace and conflict state are preserved for Step 3**
   - Given the initial merge scope has been recorded
   - When `git diff --check` and the conflict-marker scan run
   - Then their results are recorded, no whitespace error or unexpected marker
     is ignored, no conflict is resolved or staged, and all non-grouping merge
     state remains available unchanged for Step 3.

6. **Tracking and test selection are evidence-based**
   - Given merge, restoration, and inspection commands have completed
   - When Phase 2 records and the handoff are prepared
   - Then plan/progress/dashboard stages reflect only successful command-backed
     outcomes; no unit or harness test is claimed because no executable code
     changed; and residual runtime validation risk is explicitly deferred to
     Steps 3 and 4.

## Metadata

- **Complexity**: Medium
- **Labels**: Git, Merge Preparation, Configuration Preservation, Inspection, Backend Refactor
- **Required Skills**: Safe Git merge-state handling, index/worktree inspection, conflict-scope auditing, evidence-based documentation
