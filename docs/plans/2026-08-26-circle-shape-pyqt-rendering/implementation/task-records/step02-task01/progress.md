# Step 02 Task 01 Progress

## Setup

- [x] Restart protocol completed: governing artifacts, dashboard, task artifacts/records, status/diff checks, and available validation logs reconciled.
- [x] Writable task-record and `logs/` directories created under `implementation/task-records/step02-task01`.
- [x] Instruction discovery completed; no `CODEASSIST.md` exists.
- [x] Test type selected before edits: unit.

## Phase tracking

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 2 | 2.1 | Preserve circle fields through raw payload normalization | Completed |
| 2 | 2.2 | Validate and store circles as first-class legacy items | Pending (Task 02) |

Phase 2 status: **In progress**; this task completes only Stage 2.1 and does not update the approved plan or execution dashboard.

## TDD cycles

### RED

- [x] Add focused canonical, legacy-cased, malformed-circle, rectangle, and vector normalization tests.
- [x] Run the focused test and record the expected failure: `overlay_client/.venv/bin/python -m pytest tests/test_edmcoverlay_shapes.py -q` -> `3 failed, 4 passed in 0.07s`; each failure is the expected missing `radius` key, while the rectangle/vector regression passed.

### GREEN

- [x] Retain raw circle `radius` and `thickness` using established aliases only.
- [x] Re-run focused tests and record the result: `overlay_client/.venv/bin/python -m pytest tests/test_edmcoverlay_shapes.py -q` -> `8 passed in 0.05s`.
- [x] Run source/test style check: `overlay_client/.venv/bin/python -m ruff check EDMCOverlay/edmcoverlay.py tests/test_edmcoverlay_shapes.py` -> `All checks passed!`.

### REFACTOR and validation

- [x] Review scope and regression contracts: the only task-owned production branch applies to `shape_lower == "circle"`; rectangle and vector logic remain structurally unchanged, and focused tests assert their behavior.
- [x] Run `overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py -q` -> `8 passed in 0.04s`.
- [x] Run `overlay_client/.venv/bin/python -m pytest -k 'legacy_processor or legacy_tcp' -q` -> `11 passed, 6 skipped, 710 deselected in 0.66s`.
- [x] Run supplemental skip-reason evidence: `overlay_client/.venv/bin/python -m pytest -k 'legacy_processor or legacy_tcp' -q -rs` -> `11 passed, 6 skipped, 710 deselected in 0.53s`; the six skips are PyQt-dependent tests skipped because `PYQT_TESTS` is not set. GUI tests are out of scope for this pure normalizer task.
- [x] Run `git diff --check` -> passed. Scoped review confirmed no task-owned edit to client processor/storage, `load.py`, rendering, approved plan, or execution dashboard. The visible `Overlay.send_shape` and `tests/test_legacy_processor.py` modifications predate this task and were left untouched.

## Validation result

Canonical and title-cased raw circle geometry now reaches the centralized client validator unchanged, including missing, non-numeric, zero, and negative values. Existing rectangle and vector normalization contracts remain covered by the focused unit test.

## Commit status

Deferred. This task must neither commit nor push while the approved multi-step plan remains unfinished.
