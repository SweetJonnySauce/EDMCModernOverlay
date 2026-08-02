# Task 07 Progress

> **Readiness correction (2026-08-02):** A read-only deep assessment found implementation and
> evidence-pipeline blockers in addition to the recorded host-preflight blocker. Live A/B work
> must not begin until remediation Stages 7.R1-7.R6 in
> [`assessment-addendum.md`](assessment-addendum.md) pass and are reviewed. The July 21 test and
> host-preflight sections below remain historical evidence rather than current run authorization.

## Implementation checklist

- [x] Stage 7.1: verify task/design authority, dirty worktree, capture hold, and host preconditions.
- [x] Stage 7.2: write unit and harness tests before production edits.
- [x] Stage 7.3: implement strict on-demand work snapshots and bounded request wiring.
- [x] Stage 7.4: implement the controlled capture CLI and deterministic report inputs.
- [x] Stage 7.5: pass focused, integrated, harness, and project validation.
- [ ] Stage 7.6: establish and verify the fixed quiet host workload.
- [ ] Stage 7.7: complete all four cells with three accepted 60-second samples each.
- [ ] Stage 7.8: review evidence, derive report-only bounds, and synchronize authoritative state.

## Setup notes

- Mode: `auto`.
- Task source:
  `.agents/tasks/2026-07-17-fix219-architecture-convergence/step03/task-07-run-controlled-helper-pressure-ab.code-task.md`.
- Documentation directory:
  `.code-assist/2026-07-17-fix219-architecture-convergence/step03/task07-controlled-helper-pressure-ab/`.
- Branch/HEAD at start: `backend-refactor-implementation`, `3d23328`.
- The Step 03 worktree is intentionally dirty. No existing change may be reset, discarded, or
  bulk-staged.
- `CODEASSIST.md` is absent; creating one is a future repository-maintenance option, not Task 07
  scope.
- No commit or push is authorized. Stage 3.16 remains the approved commit point.

## Authority and design decisions

- The approved detailed design, research amendment, authoritative plan, iteration checklist,
  Step 03 records, and performance README were reviewed before implementation.
- Capture diagnostics remain off. The historical 12/42 reduced-v2 and two superseded v1
  captures remain immutable.
- Pressure bounds belong only in the reviewed A/B report; migration `thresholds.json` remains
  absent.
- The smallest viable measurement seam is an on-demand fixed-schema cumulative snapshot over
  the existing plugin/client connection. It avoids prohibited per-cycle logging and reuses the
  current bounded request/response pattern.
- Because `load.py` orchestration is involved, the selected test policy is unit plus harness.

## Host preflight observation

- GNOME Shell 46 is present.
- Firefox is running and must be stopped for acceptance.
- Elite gameplay, EDMC, and the overlay client were not active at the initial check.
- Current unrelated host activity is too high for a quiet acceptance sample.
- No A/B cell has started. These observations contain no PID, command line, title, handle, or
  personal path in committed evidence.

## TDD cycles

### Cycle 1: strict quiet snapshot and A/B evidence contracts

- Status: **Completed**.
- RED target: fixed-schema snapshots, cumulative deltas, complete-cell/repetition enforcement,
  deterministic aggregation, privacy rejection, and plugin/client lifecycle request behavior.
- The initial collection RED failed because the strict module did not yet exist. After the pure
  schema landed, 11 pure tests passed and three expected harness failures proved the missing
  plugin/client request path.
- GREEN passed 16 snapshot/schema/harness tests.

### Cycle 2: helper aggregates and controlled cell runner

- Status: **Completed**.
- Added helper source coverage before exposing saturating `target_queries` and
  `presentation_calls` plus current bounded actor counts in `GetHealth`. Diagnostics remain off
  and no per-call log was added.
- Added the fixed 300-second warm-up / three 60-second sample cell runner. It records no PID,
  command line, title, handle, raw helper payload, or journal text in output; existing output is
  never overwritten.
- Focused Task 07 GREEN passed 66 tests. The integrated query/repaint/helper slice passed 217.

## Validation evidence

- `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_pressure_snapshot_window.py overlay_client/tests/test_backend_pressure_ab_runner.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_pressure_ab_snapshot.py -q`: **66 passed**.
- Integrated focused query/repaint/helper/harness command: **217 passed**.
- `source overlay_client/.venv/bin/activate && make check`: **1,402 passed, 21 skipped**;
  repository Ruff and mypy passed. One intermediate run found a new annotation mismatch; it was
  corrected before this final green result.
- `source overlay_client/.venv/bin/activate && make test`: **1,402 passed, 21 skipped**.
- Targeted Ruff, compileall, runner `--help`, and `git diff --check`: **passed**. Ruff was not
  applied to JavaScript; helper source behavior is covered by its dedicated source tests.
- The 21 skips are the expected headless Tk widget skips already documented for Step 03.

## Live gate

Status: **Blocked before first cell by host preconditions**. Firefox remains active, Elite
gameplay/EDMC/the client are absent, and Shell/background load is not quiet. No helper reload,
warm-up, or sample was started. Stage 7.6 remains pending rather than weakening the gate.

## Commit status

No commit or push. Task 07 and Stage 3.13 remain incomplete.

## Deep-assessment addendum — 2026-08-02

- Current disposition: **implementation-blocked and host-preflight-blocked**.
- Stop-ship findings: the real socket snapshot path blocks its own response transport; runner
  output is incompatible with the existing completion/summary functions; and GPU-available
  sampling is unreachable.
- Additional gaps cover exact cell-state proof, fallback/helper route proof, restart/saturation
  handling, aligned measurement windows, provenance/order, immediate safety stopping, warning
  scoping, strict privacy validation, report rendering, and missing orchestration coverage.
- No live cell, host action, runtime edit, test run, capture, report, acceptance bound,
  `thresholds.json`, commit, or push occurred during the assessment.
- The self-contained findings and required continuation are recorded in
  [`assessment-addendum.md`](assessment-addendum.md). Resume at Stage 7.R1 with a real socket-level
  RED harness test; do not begin Stage 7.6 until Stages 7.R1-7.R6 pass review.
