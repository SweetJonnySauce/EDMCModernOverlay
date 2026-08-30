# Task 3.1: Integrate the Legacy Payload Contract

## Scope

Resolve the merge changes in `EDMCOverlay/edmcoverlay.py` and
`overlay_client/legacy_processor.py`. Retain the target branch's `fix219`
backend ownership while integrating `main`'s public circle and optional
rectangle/circle shape-thickness semantics through legacy normalization,
validation, item replacement, and deduplication snapshots. Do not resolve
`version.py` or edit renderer, gallery, documentation, configuration, or
unrelated implementation paths.

## Exact file boundary

Implementation files to resolve:

- `EDMCOverlay/edmcoverlay.py`
- `overlay_client/legacy_processor.py`

Focused unit-test files to read and update only if the integrated contract
would otherwise be uncovered:

- `tests/test_edmcoverlay_shapes.py`
- `tests/test_legacy_processor.py`

At handoff, the orchestration documentation contract additionally requires
updates to `docs/plans/2026-08-30-main-branch-merge/plan.md`,
`docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`,
and `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-1-payload-contract.md`.
No other files are in scope. In particular, leave `version.py` unresolved for
Task 4.3 and do not alter either configuration path.

## Required reading

- `AGENTS.md`
- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/orchestration-prompt.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-2-create-merge-state.md`
- This task brief.
- The two in-scope modules and their directly relevant tests before editing.

## Constraints

1. Preserve the `fix219` boundary: generic follow/runtime code must not import
   compositor-specific helpers or present behavior via raw backend/helper enums.
2. Preserve circle geometry and optional rectangle/circle thickness supplied by
   `main` from raw legacy normalization through processing, replacement, and
   dedupe snapshots, without selecting blanket ours/theirs for core code.
3. Maintain existing legacy payload compatibility and deterministic dedupe/item
   replacement behavior.
4. Leave `version.py` unmerged for Task 4.3 and do not change any configuration
   path or make a version/release decision.
5. Do not run `git merge`, `git merge --continue`, `git commit`, `git amend`,
   `git push`, `git fetch`, `git pull`, `git rebase`, `git reset`, `git restore`,
   `git checkout`, `git switch`, `git stash`, `git clean`, or `git merge --abort`.
   Stage only the two resolved implementation files and any justified focused
   test updates with explicit paths; do not use blanket `--ours`/`--theirs`.
6. Do not launch live overlays, send live payloads, access external services,
   or resolve any other merge conflict.

## Test type and validation

This is deterministic payload processing, so it requires focused unit tests.
Run the smallest relevant existing tests, normally:

```bash
source .venv/bin/activate
python -m pytest tests/test_edmcoverlay_shapes.py tests/test_legacy_processor.py
```

Add or update tests only if the merge would otherwise leave a contract branch
uncovered. Record the exact command/outcome; do not weaken a test to conceal a
behavioral conflict.

## Acceptance criteria

1. Given a legacy circle payload with valid radius/colour/opacity, when it is
   normalized and processed, then its geometry and optional thickness survive
   under the target architecture.
2. Given a rectangle or circle with optional thickness, when it is normalized,
   processed, replaced, and deduplicated, then the optional stroke semantics
   remain stable without altering previous payload behavior.
3. Given generic follow/runtime code, when architecture-boundary tests inspect
   dependencies, then it contains no compositor-specific presentation imports
   or raw-enum dispatch introduced by this resolution.
4. Given the active merge, when Task 3.1 completes, then the two scoped modules
   have an intentional integrated result and `version.py` remains unmerged.
