# Native-X11 Surface Artifact Execution Status

## Scope and safety state

- Authorized scope: the narrow backend-neutral overlay-surface clear, Qt unit tests, task
  documentation, and non-destructive automated validation.
- Preserved state: the pre-existing fix219 worktree is intentionally dirty. Its files are user
  work and are not modified, staged, reset, committed, or included in this task.
- Manual boundary: no live EDMC/Elite/client launch, focus or window-manager change, X11 session
  inspection, process/window data collection, or native-X11 validation has occurred.
- Test selection: this UI-local paint behavior uses `pyqt_required` unit tests. No `load.py` or
  lifecycle touchpoint is planned, so no harness test is required.

## Phase tracking

| Phase | Status |
| --- | --- |
| 1. Planning and state reconciliation | Completed |
| 2. Test-first surface-clear repair | Completed |
| 3. Native-X11 manual validation | Pending user approval |
| 4. Automated validation and handoff | Blocked by pre-existing mypy failures |

## Stage checklist

### Phase 1 — Planning and state reconciliation

- [x] 1.1 Read the governing artifacts, approved plan, context, and progress records.
- [x] 1.2 Inspect the intentionally dirty worktree and targeted task paths; no prior task code
  change or validation evidence was present.
- [x] 1.3 Reconcile the task records and resume at Stage 2.1.

### Phase 2 — Test-first surface-clear repair

- [x] 2.1 Add and record expected-failing `pyqt_required` painter-operation unit tests.
- [x] 2.2 Add the shared private backend-neutral transparent-surface clear helper and make tests green.
- [x] 2.3 Review the scoped production/test diff for paint semantics and fix219-boundary safety.

### Phase 3 — Native-X11 manual validation

- [ ] 3.1 Obtain explicit user approval before requesting or performing the bounded X11 test.
- [ ] 3.2 Record only user-provided sanitized native-X11 results, if supplied.

### Phase 4 — Automated validation and handoff

- [ ] 4.1 Run the prescribed focused Qt/repaint/follow tests. (Partial: Qt/repaint/follow and Ruff passed; mypy blocked.)
- [ ] 4.2 Run the prescribed Ruff, mypy, `make check`, and patch-hygiene gates. (`make check` and patch hygiene not run per stop protocol.)
- [ ] 4.3 Update task records with evidence, risks, rollback, and the outstanding manual gate.

## Initial evidence — 2026-08-21

- `git status --short` showed pre-existing dirty fix219 work outside this task. The task directory
  itself was untracked and contained only planning artifacts; `execution-status.md` is the first
  execution record.
- Targeted `git diff` for `overlay_client/overlay_client.py`,
  `overlay_client/tests/test_setup_surface.py`, and this task directory was empty because no task
  production/test changes had been made.
- The current normal `OverlayWindow.paintEvent` draws `_paint_overlay` without a transparent
  clear. The backend-suppressed path clears with `CompositionMode_Clear`, increments the existing
  paint metric, invokes `super().paintEvent`, and returns.

## Validation evidence

| Stage | Command | Outcome |
| --- | --- | --- |
| 1.1 | Read-only governing-artifact and targeted worktree review | Completed; Stage 2.1 is the first incomplete stage. |
| 2.1 | `QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest overlay_client/tests/test_setup_surface.py -q` | Expected RED: 3 failed, 3 passed. The initial no-platform attempt aborted before collection; offscreen was the one meaningful remediation. |
| 2.2 | `QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest overlay_client/tests/test_setup_surface.py -q` | GREEN: 6 passed in 0.44s. |
| 2.3 | Scoped `git diff` and backend-term scan | Completed: only the transparent clear helper, Qt unit seam, and task records changed; no fix219 boundary violation. |
| 4.1 | `QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py -q` | Passed: 55 passed in 1.23s. |
| 4.1 | `python -m ruff check overlay_client/overlay_client.py overlay_client/tests/test_setup_surface.py` | Passed: all checks passed. |
| 4.1 | `python -m mypy overlay_client/overlay_client.py` | Blocked: 115 errors in 14 existing imported modules. One `--follow-imports=skip` diagnosis found five existing errors in this file, none at the new helper. Stop protocol prevents further validation. |
