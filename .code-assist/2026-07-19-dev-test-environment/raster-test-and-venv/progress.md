# Raster Test and Developer Environment Progress

## Checklist

- [x] Stage 1.1: verified state and inspected test/build/dependency boundaries.
- [x] Stage 1.2: documented tests, touchpoints, invariants, and commits.
- [x] Stage 1.3: captured raster and tooling-contract RED evidence.
- [x] Stage 1.4: isolated, validated, and committed the raster bridge test.
- [x] Stage 2.1: standardized root-venv tooling and active documentation.
- [x] Stage 2.2: ran focused and complete project gates.
- [x] Stage 2.3: prepared tooling and workflow evidence for the final commit.

## Setup Notes

- Mode: auto.
- Branch start: `backend-refactor-implementation` at `ce25a95` (2 ahead, 0 behind).
- Initial worktree: only nine pre-existing untracked task files under `.agents/tasks/`.
- Workflow documentation: `.code-assist/2026-07-19-dev-test-environment/raster-test-and-venv/`.
- Root `.venv` currently contains the exact versions pinned by `requirements/dev.txt`.
- `overlay_client/.venv` is a client runtime with PyQt/runtime packages but no pytest, ruff,
  or mypy; it must remain outside the developer dependency path.

## TDD Cycles

### Cycle 1: Raster bridge isolation

- Existing named test failed before modification while creating
  `/run/user/1000/EDMCModernOverlay/shell-raster` (`logs/red-raster.log`).
- The failure occurs before helper transport and confirms accidental filesystem work.
- Replaced the production raster builder only in that bridge test with an eligible injected
  result containing the existing request fixture.
- The named test passes (1 passed), and the combined helper-runtime/raster suite passes
  (93 passed).

### Cycle 2: Developer-environment contract

- Added `tests/test_dev_environment_contract.py` before configuration changes.
- After correcting the test to follow `requirements/dev.txt` include files, dependency-source
  coverage passes while Makefile and active-documentation assertions remain RED
  (`logs/red-dev-environment-final.log`).
- Updated the Makefile to prefer root `.venv/bin/python`, retaining `python3` only as the
  fallback; the installed client runtime is never selected for developer commands.
- Corrected active setup and validation documentation to use `requirements/dev.txt` and the
  root environment on Unix and Windows.
- The developer-environment contract passes (3 passed).

## Validation Evidence

- `.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py::test_shell_raster_bridge_sends_static_frame_when_eligible -q`
  - Passed: 1.
- `.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_shell_raster_frame.py -q`
  - Passed: 93.
- `.venv/bin/python -m pytest tests/test_dev_environment_contract.py -q`
  - Passed: 3.
- `.venv/bin/python -m ruff check tests/test_dev_environment_contract.py`
  - Passed.
- `make -n lint`
  - Passed; resolved command starts with `.venv/bin/python`.
- `.venv/bin/python -m pip check`
  - Passed: no broken requirements.
- `make check`
  - Passed: ruff, mypy (92 source files), and GUI-enabled pytest (1,206 passed,
    21 skipped).
- `make test`
  - Passed: GUI-enabled pytest (1,206 passed, 21 skipped).
- `git diff --check`
  - Passed.

The 21 skips are existing GUI cases gated by their own runtime conditions; neither full run
was deselected or skipped because the GNOME helper is absent.

## Commit Status

- `9dfaa1c test(gnome): isolate raster bridge forwarding`
- Tooling/docs changes are prepared for `build(dev): standardize root test environment`.
