# Task 5.1: Targeted Mixed Validation

## Scope

Run the one prescribed mixed unit-and-harness pytest suite for the active,
uncommitted merge of local `main` into `backend-refactor-implementation`.
This task establishes test evidence only. It does not repair code, tests,
dependencies, merge contents, configuration, or release metadata.

The target-side `__version__ = "1.0.0"` selected in Task 4.3 remains a
**pre-release integration assumption** only. This task must not make a
release decision, tag, package upload, shipped-version claim, commit, or push.

## Read-only context

Read these records before running the suite, in order:

1. `AGENTS.md`
2. `docs/plans/2026-08-30-main-branch-merge/implementation/orchestration-prompt.md`
3. `docs/plans/2026-08-30-main-branch-merge/plan.md`
4. `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
5. `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-4-3-version.md`
6. This task brief

Reconcile the active merge state with read-only Git inspection before testing.
If a new unmerged path, a moved source/target tip, or an unexpected
out-of-scope change makes the recorded state unreliable, do not run the test
command; record the evidence and hand off the smallest bounded remediation or
the user decision required.

## Exact file boundary

Do not edit, stage, unstage, restore, or otherwise change production source,
test files, the merge index, `version.py`, `overlay_groupings.json`, or
`overlay_settings.json`.

After the one test attempt, the only permitted edits are these task records:

- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-5-1-targeted-validation.md`

Keep the merge uncommitted. Do not run `git merge`, `git merge --continue`,
`git commit`, `git amend`, `git tag`, `git push`, `git fetch`, `git pull`,
`git rebase`, `git reset`, `git restore`, `git checkout`, `git switch`,
`git stash`, `git clean`, or `git merge --abort`. Do not access external
services or start a live overlay/send live payloads.

## Test-type selection

**Selected test type: mixed unit and harness validation.** The merged shape
path includes deterministic payload normalization, rendering, bounds, gallery,
and backend-boundary behavior, which need unit coverage, plus the EDMC-facing
legacy TCP ingestion path, which needs harness coverage. This task is
validation-only: add or update no test files. The remaining risk after a
blocked or failing command is explicitly carried to Task 5.2 and the final
user review.

## Plan and stages

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 5 | 5.1.1 | Reconcile the active merge and Task 4.3 version-assumption boundary using read-only evidence. | Pending |
| 5 | 5.1.2 | Run the exact mixed unit-and-harness pytest suite once with Qt tests enabled. | Pending |
| 5 | 5.1.3 | Record the complete result and create the Task 5.1 handoff. | Pending |

Phase 5 remains **In progress** after this task. Task 5.2 owns the
compatibility and project gates; Task 5.3 owns final merge-integrity review.

## Technical requirements

1. Confirm the active merge still has no unresolved paths before invoking
   pytest. Treat Task 4.3's resolved `version.py` and its `1.0.0`
   pre-release-assumption wording as settled input, not as a validation target
   to change.
2. Run this exact suite once from the repository root, using the root
   development environment and no dependency override:

   ```bash
   source .venv/bin/activate
   PYQT_TESTS=1 python -m pytest \
     tests/test_edmcoverlay_shapes.py \
     tests/test_legacy_processor.py \
     tests/test_harness_legacy_tcp_ingestion.py \
     tests/test_shape_gallery.py \
     overlay_client/tests/test_paint_commands.py \
     overlay_client/tests/test_payload_bounds.py \
     overlay_client/tests/test_render_surface_mixin.py \
     overlay_client/tests/test_backend_architecture_boundary.py
   ```

3. Do not install dependencies, alter the virtual environment, set an
   override such as `ALLOW_EDMC_PYTHON_MISMATCH`, or substitute a different
   interpreter, test selection, environment flag, or static inspection.
4. If collection is blocked by the already documented
   `No module named pytest` condition, do not retry the unchanged command.
   Capture its exit status and complete output exactly; record that the
   prescribed test evidence is unavailable rather than claiming success.
5. If pytest reaches collection or execution and fails, do not repair code or
   rerun the same command. Record failing node IDs, output, and the smallest
   bounded remediation needed. If it passes, record the exact collection/pass
   count and elapsed time.
6. Update the plan stage table and dashboard after the attempt. A command that
   ran but was environment-blocked may be marked completed as an *execution
   record*, but it must state that validation remains blocked; do not mark
   Phase 5 complete or represent it as a passing test result.

## Acceptance criteria

1. **Mixed test coverage is attempted exactly once**
   - Given the recorded active merge and the Task 4.3 handoff are still
     consistent with read-only Git state
   - When Task 5.1 invokes the prescribed command with `PYQT_TESTS=1`
   - Then it runs the listed unit and harness test paths exactly once without
     a changed interpreter, dependency installation, or altered test scope.

2. **Known environment block is reported accurately**
   - Given the root `.venv` still lacks `pytest`
   - When pytest cannot collect the prescribed suite
   - Then the task records the complete command, exit status, and missing
     dependency output once, makes no retry, and does not claim the tests
     passed.

3. **Merge content remains untouched**
   - Given Task 5.1 is validation-only
   - When the command completes or is blocked
   - Then no source, test, configuration, version, merge-index, commit, or
     remote state is changed by this task.

4. **Orchestration evidence is complete**
   - Given the one test attempt has an outcome
   - When Task 5.1 updates its permitted records
   - Then Stage 5.1 and its sub-stages state the exact result, Phase 5 remains
     in progress, the Task 4.3 `1.0.0` assumption remains explicitly
     pre-release only, and Task 5.2 is the exact next task.

## Handoff requirements

Create
`docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-5-1-targeted-validation.md`
with:

- fresh-context identifier and completed/blocked status;
- preflight merge-state evidence, including whether unmerged paths were empty;
- the selected mixed unit/harness rationale and confirmation that no test file
  changed;
- the exact pytest command, environment flag, exit status, and complete
  output or summarized passed/failed count with retained command log;
- confirmation that no dependency override, installation, retry, source/test
  edit, configuration change, merge continuation, commit, or remote operation
  occurred;
- the continuing `1.0.0` pre-release-integration-assumption boundary;
- residual combined-product, test-environment, backend-boundary,
  compatibility, project-gate, and release risks; and
- the exact next task: **Task 5.2 — run backend-boundary tests and project
  gates**.

Task 5.2 is not release approval or permission to commit.
