# Task 3.4: Verify the Backend Architecture Boundary

## Scope

Perform the single focused architecture-boundary validation after the Task 3.1
payload integration, Task 3.2 renderer/geometry integration, and Task 3.3
renderer-test coverage review. This task establishes whether the integrated
merge still preserves the `fix219` boundary; it is not a further merge
resolution or implementation task.

The required test is:

```bash
source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_architecture_boundary.py
```

Run it once. Do not make a production, test, merge-index, version, or
configuration change in response to its result. A failing boundary assertion
is evidence for a bounded remediation context, not authority to repair it in
this validation context.

## Exact file boundary

Read-only validation target:

- `overlay_client/tests/test_backend_architecture_boundary.py`

Read-only supporting material, only as needed to understand or document the
test's result:

- `AGENTS.md`
- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/orchestration-prompt.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-1-payload-contract.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-2-renderer-contract.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-3-renderer-tests.md`

At completion, update only the orchestration records required by the governing
prompt:

- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-3-4-backend-boundary.md`

No source or test file is in scope for modification. Do not modify `version.py`
or any configuration, gallery, public-shape-test, documentation, or unrelated
merge path.

## Required context and invariants

Read the governing documents and all three predecessor handoffs before running
the test. Their established integration result is the baseline under test:

1. Generic follow/runtime code must not import compositor-specific presentation
   helpers or dispatch compositor-specific behavior through raw backend/helper
   enums; backend-owned bundles and consumers remain the boundary.
2. The target branch remains owner of the backend/renderer architecture while
   the merged payload and renderer retain `main`'s circle and optional
   shape-thickness contract.
3. `version.py` deliberately remains for Task 4.3. Its unresolved state is not
   a reason to alter this boundary task or to claim repository-wide merge
   completion.
4. The active merge must remain uncommitted. Do not start, continue, abort, or
   otherwise manipulate it.

## Constraints

1. Treat this as a focused deterministic unit-test task. No EDMC lifecycle
   harness is required here; the mixed unit/harness validation remains Task
   5.1.
2. Execute the exact focused command once. If it passes, record its complete
   result and do not substitute a broader test suite for it.
3. If it fails because an architecture-boundary assertion fails, record the
   exact command, exit status, concise failure identity, and affected boundary
   rule. Do not weaken the test, edit implementation, or begin remediation;
   hand off the failure as a new bounded decision/remediation task.
4. If `pytest` is still unavailable, record the single exact environment
   failure and do not rerun the unchanged command. Perform only read-only
   supporting inspection of the boundary test and the directly implicated
   boundary surface; clearly label that inspection as non-test evidence that
   does not replace the required pytest result. Do not use compilation or a
   static inspection to claim the architecture test passed.
5. Do not run merge-mutating or history-mutating Git commands, create a
   commit, or access external services. Do not launch a live overlay or send a
   live payload.
6. Before marking Stage 3.4 completed, record the exact command and outcome in
   the plan, dashboard, and handoff. Mark Phase 3 `Completed` only if all four
   of its stages are completed; otherwise preserve the accurate phase status.

## Acceptance criteria

1. Given the completed Task 3.1–3.3 integration, when the exact focused
   boundary command runs, then its pass/fail/environment-blocked outcome is
   recorded verbatim enough to reproduce, including the exit status.
2. Given a passing focused test, when Task 3.4 closes, then the records state
   that the `fix219` architecture boundary test passed after the payload and
   renderer integration, while distinguishing this result from the separate
   Task 5 project gates.
3. Given an assertion failure, when the result is handed off, then no source,
   test, or merge-resolution change has been made and the exact next action is
   a fresh, bounded remediation/decision task rather than an in-context fix.
4. Given the known missing-`pytest` environment failure persists, when the
   task closes, then the records identify it as the sole validation blocker,
   retain the result of any read-only supporting inspection as non-test
   evidence only, and leave the required pytest rerun for Task 5 after
   development dependencies are restored.
5. Given Task 3.4 is complete, when the phase and dashboard are updated, then
   Phase 3 is `Completed`, Task 4.1 is named as the exact next task, and
   `version.py` remains reserved for Task 4.3.

## Required handoff content

Create `implementation/handoffs/task-3-4-backend-boundary.md` with: status;
the validation/test type; files changed (expected: orchestration records only);
the exact command and outcome; any read-only supporting inspection and its
limited evidentiary value; the backend-boundary decision; remaining risks; and
the exact next task. If the focused test passes, the exact next task is Task
4.1, `tests/test_edmcoverlay_shapes.py`, `tests/test_shape_gallery.py`, and
`utils/shape_gallery.py` shape-test/gallery union. If it is blocked or fails,
identify the required bounded remediation or environment-restoration action
instead of advancing the merge blindly.
