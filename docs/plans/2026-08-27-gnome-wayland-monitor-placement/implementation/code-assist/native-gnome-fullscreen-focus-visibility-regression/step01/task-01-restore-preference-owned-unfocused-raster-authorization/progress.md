# Progress

## Setup

- [x] Created the isolated code-assist documentation directory and `logs/`.
- [x] Read repository instructions, the approved regression plan/task,
  progress dashboard, detailed/routing design references, and repository
  documentation discovered by the workflow.
- [x] Selected unit tests: the change is deterministic bundle policy and does
  not touch `load.py` or EDMC lifecycle wiring.

## TDD

- [x] RED recorded: `PYQT_TESTS=1 python -m pytest
  overlay_client/tests/test_gnome_helper_presentation_runtime.py -q` produced
  the expected one failing test. The old fullscreen exception forwarded
  `allow_unfocused_target=True`, so the injected assertion failed and the
  cycle correctly surfaced a helper-unhealthy wrapper around that assertion.
- [x] GREEN recorded: the presentation cycle now forwards
  `keep_overlay_visible` directly and the obsolete fullscreen geometry helper
  is deleted. The approved focused suite passed, 152 tests.
- [x] REFACTOR recorded: renamed the two selected-runtime tests to express
  disabled suspension versus enabled opt-in, and kept their targets/frame
  geometry otherwise identical. An initially misplaced static-frame mock
  caused a PyQt abort; it was restored to its existing parameterized test and
  removed from the provider-backed selected-runtime case. The focused suite
  then passed, 152 tests.

## Validation and commit

- [x] Focused regression suite: `source overlay_client/.venv/bin/activate &&
  PYQT_TESTS=1 python -m pytest
  overlay_client/tests/test_gnome_helper_presentation_runtime.py
  overlay_client/tests/test_gnome_shell_helper_extension_source.py
  overlay_client/tests/test_shell_raster_frame.py -q` — 152 passed.
- [x] `git diff --check`
- [x] Scoped diff and secret scan: reviewed the source/test diff and scanned
  changed task documentation/logs for credential-like content. The only
  matches were the documentation phrases `non-secret evidence` and `secret
  scan`; no secrets are present.
- [x] Handoff written: `/home/jon/handoffs/handoff-20260827-205145.md`.
- [x] Scoped conventional commit: `fix(gnome): honor unfocused overlay
  preference`; the final commit identifier is recorded in the external task
  handoff to avoid a second documentation-only commit.

## Decisions

- Keep the correction inside the native GNOME presentation bundle to preserve
  the fix219 backend boundary.
- Treat the existing helper `target_not_focused` response as the required
  fail-closed focus-risk behavior; do not change helper protocol semantics.
