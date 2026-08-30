# Task 2: Create the Non-Committing Merge State

## Scope

Create the approved, reversible merge state for local `main` into
`backend-refactor-implementation`, while replacing the known user-managed
`overlay_groupings.json` edit with the `main` version. Capture the complete
index/worktree merge scope before resolving any code conflict.

## Required reading

- `AGENTS.md`
- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/orchestration-prompt.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/tasks/task-2-create-merge-state.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-1-topology-freeze.md`

## Preconditions and authority

- `refs/backup/backend-refactor-implementation-pre-main-merge-20260830-ec66ba6e`
  must resolve to `ec66ba6ec110907d8c8cc1f2c5d3e9e1d0297e41`.
- No merge may already be active. Stop with evidence if topology changed since
  Task 1 or any unexpected unrelated worktree path appears.
- The user explicitly authorized discarding the current local
  `overlay_groupings.json` content and using local `main` as the source of
  truth. Do not inspect or preserve that content.
- Do not resolve code/test/documentation conflicts, commit, amend, push, reset,
  abort, fetch, or alter `overlay_settings.json` unless it is affected by Git.

## Procedure

Run the commands exactly and record their outcome:

```bash
git restore --source=HEAD --staged --worktree overlay_groupings.json
git merge --no-commit --no-ff main
git restore --source=main --staged --worktree overlay_groupings.json
git status --short
git diff --name-only --diff-filter=U
git diff --cached --name-only
git diff --name-only
```

If `overlay_settings.json` is an affected path, set it from `main` using the
same staged/worktree restore, then record that disposition. Do not apply a
blanket conflict-resolution strategy to any core path.

## Acceptance criteria

1. Given the verified backup ref and no active merge, when the merge command
   runs, then Git remains in an active uncommitted merge state with no commit.
2. Given the known local grouping edit, when Task 2 completes, then
   `overlay_groupings.json` is staged/worktree content from `main` without
   behavioral review.
3. Given the new merge state, when status and diff scopes are captured, then
   all unmerged, staged, and unstaged paths are recorded before any core
   conflict is changed.

## Validation

Git-state inspection only. No tests are required before code conflict
resolution begins.
