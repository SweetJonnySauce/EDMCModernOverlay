# Task 1: Refresh Topology and Freeze the Baseline

## Scope

Refresh the approved merge assessment for local `main` into
`backend-refactor-implementation`. Confirm that no merge is active, detect any
unexpected unrelated workspace changes, and create a verified local backup ref
at the exact target tip. Do not begin the merge or modify source files.

## Required reading

- `AGENTS.md`
- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/orchestration-prompt.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`

## Preconditions and authority

- Target branch must be `backend-refactor-implementation`; source must be local
  `main`.
- `overlay_groupings.json` is the known user-managed modification. Stop if any
  other unexpected unrelated path is modified.
- No fetch, commit, amend, push, reset, abort, merge start, or source edit.
- A local backup ref at the verified target SHA is authorized only when no merge
  is active.
- The assessment baseline is source `main` at `d19d9f7`, merge base `f93d7b7`,
  and target divergence of 158 commits ahead and 11 commits behind `main`.
  Its predicted review scope includes the legacy shape pipeline, renderer and
  geometry paths, shape tests/gallery tooling, `version.py`, rendering/API
  documentation, and four `docs/refactoring/` deletion-versus-edit paths.
  These values are stale after any source or target movement; record the new
  assessment and stop for user direction if the drift or scope is materially
  different rather than making merge-resolution decisions.

## Procedure

1. Run and record the exact output of these read-only checks before any write:

   ```bash
   git status --short --branch
   git rev-parse HEAD
   git rev-parse main
   git merge-base main HEAD
   git rev-list --left-right --count main...HEAD
   git diff --name-only "$(git merge-base main HEAD)..main"
   git rev-parse -q --verify MERGE_HEAD
   ```

   Treat a nonzero result from the final command as the expected evidence that
   no merge is active; record it rather than treating it as a task failure.
2. Recalculate the source-side changed-path scope and compare it with the
   assessment baseline above. Stop and ask the user if the topology or scope
   differs materially.
3. Create and verify a clearly named local backup ref pointing to the exact
   verified `HEAD` SHA; record both the ref name and the output that proves it
   resolves to that SHA.
4. Update the plan and dashboard with commands, results, ref name/SHA, risks,
   changed files, and the exact next task.

## Acceptance criteria

1. Given the current local repository, when the checks run, then the recorded
   source/target topology is current and no merge is active.
2. Given the known configuration edit, when status is reviewed, then no other
   unrelated modification is accepted silently.
3. Given a verified target SHA and no active merge, when the backup is created,
   then the backup ref resolves exactly to that SHA.
4. Given the assessment snapshot has drifted, when the required checks expose a
   material topology or scope difference, then the task records the evidence
   and stops before creating a merge state or resolving any path.

## Validation

Use Git inspection only. No test command is required because this task makes no
behavioral source change.
