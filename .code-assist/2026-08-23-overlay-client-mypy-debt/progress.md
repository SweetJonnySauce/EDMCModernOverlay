# Overlay Client Mypy-Debt Remediation Progress

## Phase tracking

| Phase | Status |
| --- | --- |
| 1. Baseline and scope lock | Completed |
| 2. Shared-state contract | Completed |
| 3. Pure data and renderer corrections | In progress |
| 4. Enforcement and regression validation | Pending review |

## Checklist

### Phase 1 — Baseline and scope lock

- [x] 1.1 Capture the direct and import-closure mypy failures.
- [x] 1.2 Identify the current mypy configuration gap: `overlay_client` is excluded from the default target.
- [x] 1.3 Classify errors and record invariants for the X11 repair and fix219 worktree.

### Phase 2 — Shared-state contract

- [x] 2.1 Freeze the directory-wide RED mypy baseline and classify the composite `OverlayWindow` state contract family.
- [x] 2.2 Introduce a type-only authoritative declaration strategy without changing Qt initialization or MRO.
- [x] 2.3 Make the mixin/`OverlayWindow` error family green and run focused Qt/follow tests.

### Phase 3 — Pure data and renderer corrections

- [ ] 3.1 Correct geometry, anchor, payload, and legacy data/container annotations; all Stage 3.1 source changes are rolled back pending runtime verification, while the TTL coercion contract remains deferred.
- [ ] 3.2 Correct renderer protocols, command unions, and debug collection typing.
- [ ] 3.3 Resolve integration/launcher annotations and prove affected behavior with focused tests.

### Phase 4 — Enforcement and regression validation

- [ ] 4.1 Make the directory-wide overlay-client mypy command pass.
- [ ] 4.2 Add `overlay_client` to the enforced mypy target and make the default typecheck pass.
- [ ] 4.3 Run focused tests, `make check`, patch hygiene, scoped diff review, and compliance review.

## Execution result to date

Production annotations and task documentation have changed in the completed scoped stages. No
test code, configuration, commit, or push has occurred. The remaining directory-wide cleanup and
final CI-enforcement expansion are pending their planned stages.

## Stage 2.1 — Directory-wide baseline inventory (2026-08-23)

- Completed in the isolated artifact directory
  `.code-assist/2026-08-23-overlay-client-mypy-debt/stage-2.1-baseline-inventory/`.
- Ran exactly once: `source overlay_client/.venv/bin/activate && python -m mypy overlay_client`.
  Expected RED result: exit 1, `Found 203 errors in 27 files (checked 171 source files)`.
- The raw output and exit status are retained in that stage's `logs/`; `inventory.md` maps every
  error into the approved families: shared-state 81, pure-data 34, renderer 43, integration 45.
  No new family appeared. The 88-error increase from the former 115-error import-closure result
  comes from directory-wide test/integration surfaces, not from a configuration or scope change.
- No source, test, configuration, fix219/X11, top-level dashboard, staging, commit, or external
  action occurred in the isolated context. The next stage is the annotation-only shared-state
  contract; no harness test is required because `load.py` is out of scope.

## Stage 2.2 — Annotation-only shared-state contract (2026-08-23)

- Completed in the isolated artifact directory
  `.code-assist/2026-08-23-overlay-client-mypy-debt/stage-2.2-shared-state-contract/`.
- Added `OverlayWindowState` as a `TYPE_CHECKING`-only `Protocol` for setup-owned fields, then
  used local `cast` seams in consumers. State ownership and initialization remain in
  `SetupSurfaceMixin`; no runtime base, Qt MRO, constructor, timer, paint, focus, follow, or
  backend-boundary movement occurred.
- Narrow mypy RED/GREEN command: 53 to 5 errors (48 removed). The five residual shared-state
  errors are documented without suppression for Stage 2.3 review.
- Offscreen regression: `QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest
  overlay_client/tests/test_setup_surface.py overlay_client/tests/test_repaint_debounce.py
  overlay_client/tests/test_follow_surface_mixin.py -q` — 55 passed. No test file changed;
  annotation-only type evidence and existing regressions were selected, and no harness applies.

## Stage 2.3 — Mixin declarations and inheritance (2026-08-23)

- Completed with the isolated implementation artifact directory
  `.code-assist/2026-08-23-overlay-client-mypy-debt/stage-2.3-mixin-declarations/` and its
  fresh `remediation-1/` continuation.
- Removed all 19 inherited `OverlayWindow` declaration conflicts and the five Stage 2.2 residuals
  using precise declarations and local types. Qt MRO/base order, setup ownership, initialization,
  timers, painting, focus/cursor behavior, follow, and the generic fix219 boundary were unchanged.
- The bounded remediation replaced an unchecked preparation-rect cast with the existing
  `BackendPresentationSurfacePreparation` contract and gave the device-ratio log a distinct exact
  local. Focused mypy now reports only 10 renderer-family diagnostics reserved for Stage 3.2.
- The offscreen setup/repaint/follow command passed in both Stage 2.3 contexts (55 passed each);
  `git diff --check` passed. No test, harness, configuration, or `load.py` change was needed.

## Stage 3.1 — Pure-data type corrections (2026-08-23)

- The initial isolated context and fresh remediation artifact are retained at
  `.code-assist/2026-08-23-overlay-client-mypy-debt/stage-3.1-pure-data-types/remediation-1/`.
- The user reported that the runtime symptom under investigation returned after the fresh
  remediation. The user then directed a complete Stage 3.1 rollback. All Stage 3.1 source
  changes—including native-origin annotations in `follow_geometry.py`, the trace-detail type in
  `anchor_helpers.py`, and mapping/vector-point annotations in `legacy_processor.py`—are removed.
  This records the rollback without claiming the annotations caused the symptom.
- Post-rollback normal mypy of the six scoped modules again reports the original 20 errors in all
  six files; the focused pure-unit slice passed (`90 passed`), the offscreen
  setup/repaint/follow slice passed (`55 passed`), and `git diff --check` passed.
- Hold Stage 3.1 and do not start Stage 3.2 pending user runtime verification. The TTL diagnostic
  remains deferred: `PayloadModel.ingest` accepts `dict[str, object]` and its direct `int()`
  coercion lacks a source-proven closed static contract. Do not suppress or change it without
  user-approved, test-first runtime-contract work.
