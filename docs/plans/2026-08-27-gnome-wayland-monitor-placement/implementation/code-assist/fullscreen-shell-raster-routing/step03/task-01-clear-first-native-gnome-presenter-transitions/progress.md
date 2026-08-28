# Progress: Clear First Native GNOME Presenter Transitions

- [x] Setup: created isolated artifact directory and logs directory.
- [x] Explore: read governing instructions, approved task/design/plan/research,
  Step 2 handoff, source/tests, worktree status, and recent commits.
- [x] Plan: selected unit tests only; no `load.py` or lifecycle wiring is in scope.
- [x] RED: deterministic callback-order contract failed as expected with
  `prepare -> managed_attach -> clear`.
- [x] GREEN: clear acknowledgement now gates the guarded managed path and the
  contract proves `clear -> prepare -> managed_attach`.
- [x] REFACTOR and validation: focused suite passed and `git diff --check`
  passed. Scoped Ruff was skipped because the system `python` executable is
  absent; the repository venv test command is the available Python runtime.
- [x] Commit and handoff: `cfbf6f6 fix(gnome): clear raster before managed transition`.

## TDD evidence

- RED command: `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest
  overlay_client/tests/test_gnome_helper_presentation_runtime.py -k
  guarded_persistent_fullscreen_loss_clears_before_managed_preparation_and_attach -q`
  — expected failure: recorded `prepare, managed_attach, clear`.
- GREEN targeted command: same test plus
  `selected_shell_raster_windowed_transition_blocks_pyqt_when_clear_fails` —
  passed after the acknowledgement gate moved earlier.
- Final focused Step 3 command — `140 passed in 0.64s`.

## Review

The source diff retains the existing public clear payload and converts all
guarded `HIDE_ALL` exits with a cached raster actor into the same clear/reset
path as token replacement. No generic runtime, X11/xcompat, helper schema,
target discovery, timer, coordinate, or fallback behavior changed.

## Setup notes

`CODEASSIST.md` was not discovered. Pre-existing dirty planning artifacts are
user-owned and will not be staged. Baseline `git diff --check` passed.
