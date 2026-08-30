# Task 4.1: Integrate Public Shape Tests and Gallery

## Scope

Resolve the public shape-test and developer-gallery merge surface as an
intentional union. Reconcile `tests/test_edmcoverlay_shapes.py`,
`tests/test_shape_gallery.py`, and `utils/shape_gallery.py` so the integrated
branch retains both branches' distinct supported public shape API coverage and
the gallery's developer-facing labeled inspection behavior.

The merged result must preserve the Task 3 public circle and optional
rectangle/circle-thickness contract. This is not payload-inspector work, a
renderer-contract rework, documentation reconciliation, or a version decision.

## Exact file boundary

Resolve or update only these shape/gallery paths:

- `tests/test_edmcoverlay_shapes.py`
- `tests/test_shape_gallery.py`
- `utils/shape_gallery.py`

Read-only supporting context before editing:

- `AGENTS.md`
- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/orchestration-prompt.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-1-payload-contract.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-2-renderer-contract.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-3-renderer-tests.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-4-backend-boundary.md`
- This task brief and the three in-scope paths.

At handoff, update only the required orchestration records:

- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-4-1-shape-gallery-union.md`

Do not change any other path unless a focused test demonstrates a merged
public-contract defect. Record that failure and the smallest affected path
before making a narrow repair; retain the regression test with the repair.

## Required union

1. Keep the public shape-payload builder/API expected by `main`, including its
   circle and optional-thickness behavior and its caller-facing contract.
2. Keep the target branch's labeled developer-inspection/gallery behavior.
   Labels are part of the developer-facing output contract; do not replace
   them with unlabeled output or silently drop a labeled case.
3. Combine each branch's distinct public shape and gallery assertions. Collapse
   only genuine duplicate coverage, and do not weaken an assertion merely to
   make a merged test file compile.
4. Keep the gallery utility and its tests aligned: public builder output,
   supported shapes, optional thickness, and labels must describe the same
   contract.

## Constraints

1. Resolve the three paths as a coverage and behavior union, never with a
   blanket ours/theirs selection. Do not delete a public API, labeled gallery
   behavior, or distinct assertion without recording why it is truly obsolete
   under the merged contract.
2. Preserve the completed Task 3 contract: circles retain their geometry and
   required radius; omitted thickness remains absent/defaulted according to the
   established path; explicit valid circle and rectangle thickness remains
   supported. Do not reintroduce group-scale stroke semantics or alter renderer
   behavior in this task.
3. Keep public-test coverage at public payload/gallery seams. Do not couple it
   to private renderer state or use implementation details solely to make a
   test pass.
4. Do not introduce a `fix219` boundary violation. Generic follow/runtime code
   must not acquire compositor-specific presentation imports or raw
   backend/helper-enum dispatch.
5. Do not resolve `version.py`; do not change configuration, rendering,
   payload-inspector, release, API-documentation, refactoring-document, or
   unrelated test paths. Leave Tasks 4.2 and 4.3 untouched.
6. Do not run `git merge`, `git merge --continue`, `git commit`, `git amend`,
   `git push`, `git fetch`, `git pull`, `git rebase`, `git reset`, `git
   restore`, `git checkout`, `git switch`, `git stash`, `git clean`, or `git
   merge --abort`. Stage only the three resolved paths and any narrowly
   justified demonstrated repair with explicit paths.
7. Do not launch a live overlay, send live payloads, access external services,
   or make a release decision.

## Test type and validation

This is deterministic public payload and gallery behavior, so focused unit
tests are required. No EDMC lifecycle harness is required for Task 4.1; the
mixed unit/harness gate remains Task 5. Run the smallest focused command after
resolving the union:

```bash
source .venv/bin/activate
python -m pytest tests/test_edmcoverlay_shapes.py tests/test_shape_gallery.py
```

If the known missing-`pytest` environment persists, attempt that command once
only. Then run syntax/compile and scoped whitespace checks for all changed
in-scope paths, record the exact failure and fallback outcomes, and defer the
focused pytest rerun to Task 5 after development dependencies are restored.
Do not weaken, delete, or skip coverage to conceal an environment failure.

## Acceptance criteria

1. Given the active merge's versions of the three in-scope paths, when Task
   4.1 completes, then the resulting public tests and gallery are an
   intentional union with no conflict markers and no blanket-side resolution.
2. Given consumers of the gallery's public shape-payload builder, when they
   build supported rectangle and circle examples with omitted or explicit valid
   thickness, then the public output remains compatible with the Task 3
   optional-thickness and circle contract.
3. Given a developer inspecting the gallery, when each supported example is
   rendered or listed, then the target branch's developer-facing labels remain
   present and the labeled cases stay covered by `tests/test_shape_gallery.py`.
4. Given the resolved public shape tests, when the shape contract is reviewed,
   then each branch's distinct public assertion is retained or a genuine
   duplicate is consolidated without weakening circle, radius, or optional
   thickness coverage.
5. Given Task 4.1 completion, when its focused validation is run, then the
   two public test modules pass; if `pytest` is still unavailable, the single
   exact environment failure plus compile and scoped-whitespace fallback are
   recorded for Task 5.
6. Given the active merge after Task 4.1, when scope is inspected, then
   `version.py` remains reserved for Task 4.3, no configuration or unrelated
   payload-inspector/documentation path was changed, and the phase/stage table,
   dashboard row, and self-contained handoff identify Task 4.2 as the exact
   next task.
