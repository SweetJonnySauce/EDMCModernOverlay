# X11 Surface Artifact Repair Progress

## Phase tracking

| Phase | Status |
| --- | --- |
| 1. Investigation and plan | Completed |
| 2. Test-first surface-clear repair | Completed |
| 3. Native X11 validation | Pending review |
| 4. Regression validation and handoff | Blocked by pre-existing mypy failures |
| 5. Iteration checklist | Completed |

## Checklist

### Phase 1 — Investigation and plan

- [x] 1.1 Record the user-observed X11 symptom and recovery behavior.
- [x] 1.2 Inspect transparent surface setup, normal/suppressed paint paths, X11 bundle, follow flow, and existing tests.
- [x] 1.3 Compare the current paths with source history and identify the missing normal-path clear.
- [x] 1.4 Document alternatives, invariants, risks, and a test strategy.

### Phase 2 — Test-first surface-clear repair

- [x] 2.1 Add failing Qt tests for a clear-before-draw invariant in normal and suppressed paint paths.
- [x] 2.2 Extract one narrowly scoped transparent-surface-clear helper and call it from both paths.
- [x] 2.3 Verify correct painter composition state, draw order, and paint metrics without changing payload behavior.

### Phase 3 — Native X11 validation

- [ ] 3.1 Run a bounded manual X11 move/focus/follow test with the overlay active.
- [ ] 3.2 Run an extended real-game validation appropriate to the observed long-running failure.
- [ ] 3.3 If artifacts persist, stop and conduct a separate reversible `X11BypassWindowManagerHint` experiment.

### Phase 4 — Regression validation and handoff

- [ ] 4.1 Run targeted Qt/repaint/backend tests. (Partially complete; blocked by prescribed mypy.)
- [ ] 4.2 Run project checks proportionate to the final touchpoints. (Not run per stop protocol.)
- [ ] 4.3 Record X11 results, remaining uncertainty, and rollback guidance; do not commit without separate authorization.

### Phase 5 — Iteration checklist

- [x] 5.1 Reconcile plan, execution-status, implementation diff, and validation evidence.
- [x] 5.2 Audit scope, backend boundary, tests, deferred gates, and manual authorization.
- [x] 5.3 Record the readiness decision in `iteration-checklist.md`.

## Planning result

No production code, tests, settings, helper configuration, captures, commits, or pushes were
changed. The recommended first repair is an explicit transparent-surface clear at the start of
every normal paint, shared with the existing suppressed-content clearing behavior.

## Stage 2.1 — RED tests (2026-08-21)

- Added `pyqt_required` painter-operation unit tests in `overlay_client/tests/test_setup_surface.py`.
  They exercise direct normal, suppressed, and repeated normal `paintEvent` calls through a small
  recording painter seam; no harness test is needed because no `load.py` or lifecycle wiring is
  touched.
- First attempted command: `source overlay_client/.venv/bin/activate && PYQT_TESTS=1 python -m
  pytest overlay_client/tests/test_setup_surface.py -q`. It aborted during Qt application setup
  because no platform plugin was selected.
- Remediation and RED command: `source overlay_client/.venv/bin/activate &&
  QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest
  overlay_client/tests/test_setup_surface.py -q`.
- Outcome: expected RED — 3 failed, 3 passed. The failures show the normal path begins without a
  clear and the current suppressed path does not restore source-over. The next stage is the
  narrow shared helper; no external or live-X11 action occurred.

## Stage 2.2 — GREEN repair (2026-08-21)

- Added the private, backend-neutral `OverlayWindow._clear_transparent_surface` helper. It clears
  `self.rect()` using transparent clear composition and restores source-over before either branch
  proceeds. Both normal and backend-suppressed paint paths share it.
- Preserved antialiasing before normal overlay drawing, suppressed-content early return,
  `super().paintEvent`, and paint-count accounting.
- GREEN command: `source overlay_client/.venv/bin/activate && QT_QPA_PLATFORM=offscreen
  PYQT_TESTS=1 python -m pytest overlay_client/tests/test_setup_surface.py -q`.
- Outcome: 6 passed in 0.44s.

## Stage 4.1 — Automated validation (2026-08-21, blocked)

- Passed: `source overlay_client/.venv/bin/activate && QT_QPA_PLATFORM=offscreen PYQT_TESTS=1
  python -m pytest overlay_client/tests/test_setup_surface.py
  overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py
  -q` — 55 passed in 1.23s.
- Passed: `source overlay_client/.venv/bin/activate && python -m ruff check
  overlay_client/overlay_client.py overlay_client/tests/test_setup_surface.py` — all checks passed.
- Blocked: `source overlay_client/.venv/bin/activate && python -m mypy
  overlay_client/overlay_client.py` — 115 errors in 14 existing imported client modules. The
  errors include existing `OverlayWindow` multiple-inheritance conflicts and unrelated type issues.
- One meaningful diagnosis: `source overlay_client/.venv/bin/activate && python -m mypy
  --follow-imports=skip overlay_client/overlay_client.py` — five existing attribute-typing errors
  at lines 536, 558, 656, 669, and 679; none refer to `_clear_transparent_surface`.
- Stop protocol applied: no type-cleanup work was authorized, and no further validation command
  (`make check` or `git diff --check`) was run. Do not request native-X11 validation until the
  automated gate has a passing/waived disposition.

## Stage 2.3 — Scoped review (2026-08-21)

- Reviewed the production/test diff directly. The only production behavior is a private helper
  that establishes transparent clear then source-over before the existing branch split.
- Confirmed the normal branch still enables antialiasing, calls `_paint_overlay`, finalizes the
  painter, increments paint metrics, and calls `super().paintEvent`. The suppressed branch still
  clears once, skips `_paint_overlay`, increments paint metrics once, calls `super()`, and returns.
- Confirmed no backend, GNOME, Wayland, helper, raw-enum, X11-flag, settings, or `load.py`
  touchpoint was added. The generic paint path remains backend-neutral.
