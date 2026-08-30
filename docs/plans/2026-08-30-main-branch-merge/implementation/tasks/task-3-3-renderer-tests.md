# Task 3.3: Integrate Renderer Test Coverage

## Scope

Resolve `overlay_client/tests/test_render_surface_mixin.py` as an intentional
coverage union for the renderer contract integrated in Tasks 3.1 and 3.2.
Retain relevant coverage from both sides of the merge without duplicating or
weakening it. The resulting focused test coverage must anchor circle geometry,
optional thickness, opacity, explicit rectangle miter joins, cycle anchors,
and transformed circle bounds where those behaviors are exercised by the
renderer test module.

This task is limited to renderer-test coverage. The public shape-test and
gallery union belongs to Task 4.1; do not edit its paths. Do not resolve
`version.py`.

## Exact file boundary

Primary merge-resolution and test file:

- `overlay_client/tests/test_render_surface_mixin.py`

Read-only supporting modules and focused tests, to understand the established
contract before changing the primary test file:

- `overlay_client/render_surface.py`
- `overlay_client/paint_commands.py`
- `overlay_client/payload_transform.py`
- `overlay_client/tests/test_paint_commands.py`
- `overlay_client/tests/test_payload_bounds.py`

At handoff, update only the required orchestration records:

- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-3-renderer-tests.md`

Do not edit implementation, gallery, public-shape test, documentation,
configuration, or version paths. An implementation edit is permitted only to
correct a demonstrated merged-contract defect: first record the failing
expectation and smallest affected path, make the narrow repair, and preserve
the same focused regression test. Otherwise, no implementation path is in
scope.

## Required reading

- `AGENTS.md`
- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/orchestration-prompt.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-1-payload-contract.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-2-renderer-contract.md`
- This task brief.
- The primary test module, supporting renderer modules, and the directly
  relevant focused tests before editing.

## Constraints

1. Resolve the test module as a coverage union, not a blanket ours/theirs
   selection. Keep each test only when it proves a distinct merged-contract
   behavior; consolidate overlap without losing either branch's assertion.
2. Keep the test seam at the renderer/paint-command boundary. The tests must
   not bypass the public command-building path with private implementation
   state merely to make a test pass.
3. Preserve the Task 3.2 contract: circle centre/radius geometry and opacity;
   explicit-versus-omitted shape thickness; miter joins for explicitly thick
   rectangles; unchanged cycle anchors; and transformed circle bounds. Where a
   behavior is already proved by the adjacent focused module, avoid a
   redundant duplicate here and identify that coverage in the handoff.
4. Do not introduce a `fix219` backend-boundary violation. Generic
   follow/runtime code must not acquire compositor-specific presentation
   imports or raw backend/helper-enum dispatch because of this task.
5. Stage only the resolved test module and any narrowly justified demonstrated
   defect repair with explicit paths. Do not use blanket `--ours`/`--theirs`.
6. Leave `version.py` unresolved for Task 4.3. Do not run `git merge`, `git
   merge --continue`, `git commit`, `git amend`, `git push`, `git fetch`, `git
   pull`, `git rebase`, `git reset`, `git restore`, `git checkout`, `git
   switch`, `git stash`, `git clean`, or `git merge --abort`.
7. Do not launch a live overlay, send live payloads, or access external
   services.

## Test type and validation

This is deterministic renderer behavior, so focused unit tests are required;
no EDMC lifecycle harness is required for this subtask. Run the smallest
focused command after resolving the test module:

```bash
source .venv/bin/activate
PYQT_TESTS=1 python -m pytest overlay_client/tests/test_render_surface_mixin.py
```

If the known missing-`pytest` environment persists, attempt that command once
only. Then run syntax/compile and scoped whitespace checks for the changed test
file, record the exact failure and fallback outcomes, and defer pytest to the
required validation milestone. Do not weaken, delete, or skip coverage merely
to conceal an environment failure.

## Acceptance criteria

1. Given the active merge's two versions of
   `test_render_surface_mixin.py`, when Task 3.3 resolves the file, then the
   resulting module intentionally retains both branches' distinct renderer
   coverage and contains no conflict markers.
2. Given circle payloads with omitted and explicit valid thickness, when the
   renderer builds and paints their commands, then tests demonstrate the
   correct circle geometry, opacity, and stroke policy without changing the
   existing default-stroke behavior.
3. Given an explicitly thick rectangle and cyclic/transformed bounded shapes,
   when renderer commands are generated, then the focused coverage preserves
   miter joins and cycle anchors and confirms the circle-bounds convention, or
   records the adjacent focused test that provides that proof.
4. Given the resolved renderer-test module, when its scoped diff is reviewed,
   then it introduces no production dependency or raw backend/helper-enum
   dispatch; the dedicated boundary test remains Task 3.4. If the environment
   prevents the focused test run, the exact failure and completed fallback
   checks are recorded for Task 5 validation.
5. Given Task 3.3 completion, when the merge state is inspected, then only the
   scoped renderer-test module has been resolved or updated by this task,
   `version.py` remains unresolved for Task 4.3, and the phase/stage table,
   dashboard row, and self-contained handoff identify Task 3.4 as the exact
   next task.
