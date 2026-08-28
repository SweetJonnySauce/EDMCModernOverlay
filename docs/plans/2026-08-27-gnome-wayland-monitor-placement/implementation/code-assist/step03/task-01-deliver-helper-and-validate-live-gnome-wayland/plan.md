# Step 3 Delivery and Acceptance Plan

## Preconditions

- [x] Reconcile prerequisite commits, task scope, existing evidence, worktree, and helper development script.
- [x] Choose test type: manual live GNOME Wayland integration/acceptance plus deterministic regression; no harness.
- [x] Run the deterministic pre-gate regression and retain its log.
- [x] Prepare exact delivery commands and their side effects without invoking them.
- [x] Close the manual monitor-transfer gate as superseded; the user accepted the fullscreen Shell-raster live matrix instead.

## Acceptance scenarios

| Scenario | Input/setup | Expected observable output | Evidence required |
| --- | --- | --- | --- |
| Primary handoff | Elite primary; overlay initially secondary | Target/pre/post indexes end on primary; guarded transfer label; applied rect matches request | Non-secret helper diagnostics and observation |
| Secondary handoff | Elite secondary; overlay initially primary | Target/pre/post indexes end on secondary; guarded transfer label; applied rect matches request | Non-secret helper diagnostics and observation |
| Repeated handoff | Move Elite across monitors repeatedly | No accumulated offset; retry only under existing bounded policy | Diagnostics and observation |
| Co-location | Elite and overlay already share a monitor | No unnecessary transfer action; matching readback | Diagnostics |
| Interaction | Matching-readback cases above | Click-through, no focus theft, above Elite, follows resize, no chrome regression | User observation |
| Failure gate | Any mismatch/unavailable/error result | Recorded degraded/failed result; no workaround or code edit | Diagnostics and stop-for-direction record |

## Execution sequence

1. After separate approval, the user runs `./scripts/dev_gnome_helper.sh update`, which clean-replaces the UUID directory and requests enablement.
2. The user runs `./scripts/dev_gnome_helper.sh status`, which reports extension state and performs a session-bus health call when possible. If inactive/not discovered, logout/login may be necessary; do not infer activation without status evidence.
3. The user supplies only non-secret output and exercises the six scenarios above in the active GNOME Wayland session.
4. Record the result. On every matching-readback pass, inspect the scoped documentation diff and prepare the required local evidence commit. On any live failure, record evidence and stop; do not add sleeps, coordinate guesses, fullscreen workarounds, or cross-backend fallback.

## Regression command

```bash
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
  overlay_client/tests/test_gnome_shell_helper_extension_source.py \
  overlay_client/tests/test_gnome_shell_helper_presentation_state.py \
  overlay_client/tests/test_gnome_helper_presentation_runtime.py \
  overlay_client/tests/test_backend_architecture_boundary.py -q
```

Result: pass, 156 tests in 0.37s. `make check` is not rerun unless a live
finding changes code; Step 2's root-Ruff and loopback-socket environment limits
remain documented.
