# Stage 2.3 Progress — Mixin Declaration Reconciliation

## Checklist

- [x] 2.3.1 Read governing records, prior stage evidence, task/scope review,
  dashboard, and intentionally dirty scoped worktree.
- [x] 2.3.2 Create context, plan, progress, and logs before production edits.
- [x] 2.3.3 Run the prescribed focused mypy RED command once and save output.
- [ ] 2.3.4 Make only exact declaration/local-type edits for every owned diagnostic
  (19 conflicts and 3/5 residuals completed; remediation needed for 2/5).
- [x] 2.3.5 Run the identical focused mypy command once for GREEN.
- [x] 2.3.6 Run the prescribed offscreen setup/repaint/follow regression slice.
- [x] 2.3.7 Review the scoped diff and leave the exact six-field handoff.

## Decisions

- Test type was selected before coding: static mypy RED/GREEN plus existing
  offscreen regressions. No test or harness update is planned because this is
  annotation-only and `load.py` is outside scope.
- Production edits, if supported by RED evidence, remain limited to exact type
  declarations/local annotations. No MRO, owner, initializer, timer, paint,
  focus/cursor, follow, backend, or X11 boundary changes are permitted.

## TDD record

- RED ran once: `source overlay_client/.venv/bin/activate && python -m mypy
  --follow-imports=skip overlay_client/overlay_client.py
  overlay_client/interaction_surface.py overlay_client/follow_surface.py
  overlay_client/control_surface.py overlay_client/render_surface.py`.
  It exited `1` with `Found 16 errors in 3 files (checked 5 source files)`;
  raw output and exit status are in `logs/mypy-mixin-declarations-red.*`.
- Five errors are this stage's owned residuals: two cursor-state reads, generic
  preparation `rect` indexing, empty-tuple inference for the preparation key,
  and device-ratio snapshot reuse. The same target contains 11 existing
  renderer-family diagnostics in `render_surface.py`; Stage 2.1 inventories
  that family for Stage 3.2, so it is neither changed nor suppressed here.
- The implementation uses type-only class declarations matching setup-owned
  types, direct state-protocol casts for the two cursor branches, and a
  `Sequence[object]` cast for the already-guarded generic preparation value.
  Runtime ownership, MRO, initialization, backend behavior, and the fix219
  boundary remain unchanged.
- GREEN ran once with the identical five-file target and exited `1` with
  `Found 12 errors in 2 files (checked 5 source files)`; raw output and exit
  status are in `logs/mypy-mixin-declarations-green.*`. It removes all 19
  `OverlayWindow` inheritance conflicts and three owned residuals (both cursor
  reads and the empty-tuple preparation-key inference). The 11 renderer errors
  remain unchanged. Two owned diagnostics remain: `int()` receives an
  `object`-typed preparation-rect member, and a second local `snapshot` reuse
  is inferred as incompatible with its prior tracker tuple. The first requires
  a source-contract decision rather than another unchecked cast; the second is
  a safe local renaming candidate but must be handled in a fresh remediation
  context because this task's one permitted GREEN measurement is complete.
- The offscreen regression ran once: `source overlay_client/.venv/bin/activate
  && QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest
  overlay_client/tests/test_setup_surface.py
  overlay_client/tests/test_repaint_debounce.py
  overlay_client/tests/test_follow_surface_mixin.py -q`. It passed: `55 passed
  in 0.96s`; raw output and exit status are in
  `logs/pytest-offscreen-mixin-declarations.*`.
- Scoped review: `git diff --check` passed. Direct review confirms the
  `OverlayWindow` base list and `__init__`, setup assignment order, timer/paint
  paths, and generic backend imports/dispatch were not changed by this stage.
  The dirty diff also includes the prior Stage 2.2 state-contract edits and
  independent fix219 work; neither is claimed as new Stage 2.3 behavior.
