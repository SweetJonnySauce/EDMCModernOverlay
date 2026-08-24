# Stage 2.2 Progress — Shared Overlay-State Contract

## Phase tracking

| Phase | Status |
| --- | --- |
| 2. Shared-state contract | Completed |

## Checklist

- [x] 2.2.1 Read governing records, Stage 2.1 evidence, generated task/scope review,
  execution status, and the dirty scoped fix219 diff.
- [x] 2.2.2 Create stage-local context, plan, progress, and logs before production edits.
- [x] 2.2.3 Run the one prescribed narrow mypy RED command and save its output.
- [x] 2.2.4 Add only the centralized annotation-only contract and consuming seams.
- [x] 2.2.5 Run the same narrow mypy command once for GREEN and record the delta.
- [x] 2.2.6 Run the prescribed offscreen setup/repaint/follow regression slice once.
- [x] 2.2.7 Review the scoped diff and leave the exact six-field handoff.

## Decisions

- Test type was selected before coding: static mypy RED/GREEN plus existing
  offscreen regressions. No test update is planned because the change is
  annotation-only; no harness test applies because `load.py` is not touched.
- Existing dirty fix219 and pressure-AB work is user work. This stage may alter
  only its own records and source needed for the centralized type contract.

## TDD record

- RED command ran once: `source overlay_client/.venv/bin/activate && python -m
  mypy --follow-imports=skip overlay_client/overlay_client.py
  overlay_client/interaction_surface.py overlay_client/follow_surface.py
  overlay_client/control_surface.py`.
- Result: expected failure, exit `1`; `Found 53 errors in 4 files (checked 4
  source files)`. The saved output is
  `logs/mypy-shared-state-red.raw.log` and its status is
  `logs/mypy-shared-state-red.exit-status`.
- The 53 diagnostics are all within the frozen shared-state family: 30 control,
  16 follow, 3 interaction, and 4 direct `OverlayWindow` state reads. No
  out-of-family diagnostic was revealed, so the annotation-only implementation
  may proceed.
- GREEN command ran once with the identical four-file target and exited `1` with
  5 errors, saved in `logs/mypy-shared-state-green.raw.log` with status in
  `logs/mypy-shared-state-green.exit-status`. The targeted delta is **48 fewer
  errors**. The contract removes all control-surface and direct-`OverlayWindow`
  errors plus the covered interaction/follow reads.
- The five residuals are deferred: two `_cursor_saved` reads in unmodified
  interaction/follow methods, the non-contract `preparation.rect` indexability
  diagnostic, the follow-owned empty-tuple inference diagnostic, and one
  remaining device-ratio-log assignment. No residual was suppressed; no
  runtime/MRO/lifecycle change was needed.
- Offscreen regression command ran once: `source overlay_client/.venv/bin/activate
  && QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest
  overlay_client/tests/test_setup_surface.py
  overlay_client/tests/test_repaint_debounce.py
  overlay_client/tests/test_follow_surface_mixin.py -q`.
  Result: passed, `55 passed in 0.99s`; raw output and exit status are in
  `logs/pytest-offscreen-shared-state-contract.*`.
- No test file was added or modified: the source changes are annotation-only,
  and the existing offscreen tests provide the selected regression proof. The
  scoped review found no changed `SetupSurfaceMixin` assignment, Qt base list,
  constructor, timer, paint operation, backend import, compositor/helper
  import, or raw backend/helper-enum presentation dispatch. The pre-existing
  fix219 clear-first diff in `overlay_client.py` and its test remains separate.
