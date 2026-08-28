# Remediation 01 Progress

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Reconcile the live regression, prior change, and scoped rollback boundary | Completed |
| 1.2 | RED proof that direct preference authorization breaks fullscreen continuity | Completed — focused test failed as expected with `allow_unfocused_target=False` |
| 1.3 | Restore the prior fullscreen/full-monitor authorization and regression coverage | Completed |
| 1.4 | Run focused validation, secret scan, handoff, and scoped commit | Completed — committed locally after recorded validation |

## RED / GREEN / REFACTOR evidence

- **RED:** the focused continuity test failed under the direct
  `keep_overlay_visible` forwarding path because its request used
  `allow_unfocused_target=False`.
- **GREEN:** restoring the fullscreen/full-monitor authorization made that test
  pass.
- **REFACTOR:** the test name now documents actor continuity rather than
  implying a user-preference contract that this safety rollback deliberately
  does not provide.

## Validation

- `source overlay_client/.venv/bin/activate && PYQT_TESTS=1 python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_shell_raster_frame.py -q` — 152 passed.
- `git diff --check` — passed.
- Changed-text secret scan — no credentials or private material found; the
  literal phrase “non-secret” is documentation only.
