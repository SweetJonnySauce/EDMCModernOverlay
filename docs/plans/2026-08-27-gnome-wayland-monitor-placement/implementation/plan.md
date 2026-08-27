# GNOME Wayland Monitor Placement: Implementation Plan

## Checklist

- [ ] Step 1: Add guarded monitor transfer to normal GNOME presentation.
- [ ] Step 2: Prove the native-helper readback and backend boundary contracts.
- [ ] Step 3: Deploy the helper update and validate live GNOME Wayland handoff.

## Phase Status

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Helper normal-path correction | Pending |
| 2 | Contract validation and observability | Pending |
| 3 | Live GNOME Wayland delivery | Pending |

### Phase 1: Helper normal-path correction

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add source-contract coverage for monitor mismatch, match, invalid state, and failure fallback | Pending |
| 1.2 | Implement conditional `move_to_monitor` before the existing frame-resize operation | Pending |
| 1.3 | Run focused helper tests and inspect the staged helper-only scope | Pending |

### Phase 2: Contract validation and observability

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Preserve and prove applied-rectangle mismatch/retry/backoff behavior | Pending |
| 2.2 | Make the normal-path transfer decision diagnosable without changing the helper protocol | Pending |
| 2.3 | Verify the architecture boundary and run the required automated gates | Pending |

### Phase 3: Live GNOME Wayland delivery

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Install/reload the changed helper in the target GNOME session | Pending |
| 3.2 | Validate primary-to-secondary and secondary-to-primary handoff, input, stacking, and resize behavior | Pending |
| 3.3 | Record evidence, resolve remaining live-only issues, and prepare the reviewed change for commit | Pending |

## Step 1: Add guarded monitor transfer to normal GNOME presentation

**Objective:** Correct the native GNOME Shell normal presentation path so a
PyQt overlay transfers to Elite's Shell-reported monitor before the existing
frame-resize operation.

**Implementation guidance:**

- Work only in the GNOME Shell helper's ordinary attach/presentation flow.
  Do not modify renderer selection, payload processing, generic follow code,
  native X11, or XWayland compatibility.
- Add/extend the established helper source-contract tests first so they encode
  the normal-path ordering and guard conditions.
- Read the overlay's current monitor and normalise the target window monitor.
  Invoke `move_to_monitor(targetMonitor)` only when both are valid
  non-negative indexes and they differ.
- Keep `move_resize_frame` as the next operation. A matching frame is a no-op
  only when the overlay is also already on the target monitor.
- If monitor transfer is unavailable or throws, record that condition and
  retain the existing resize fallback. Never report placement as successful
  solely because either method returned normally.
- Do not use the diagnostic strategy-probe/fullscreen paths for normal
  behavior. Do not add a public preference, protocol field, or backend
  selector branch.

**Test requirements:**

- Update `overlay_client/tests/test_gnome_shell_helper_extension_source.py`
  with tests covering the guarded move, ordering before resize, matching-monitor
  no-op, invalid-monitor fallback, and post-operation reads.
- Run:

  ```bash
  PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
    overlay_client/tests/test_gnome_shell_helper_extension_source.py -q
  ```

- Run `git diff --check` and inspect the diff to confirm the production change
  is confined to the GNOME helper plus its focused tests.

**Integration:** This wires the design's monitor-ownership correction into the
already active `gnome_shell_wayland` helper presentation path. It does not
change how other backend bundles are selected or called.

**Demo:** With a controlled helper/window double or source-contract evidence,
the normal presentation path chooses `move_to_monitor` followed by
`move_resize_frame` for a monitor mismatch and performs no monitor move for an
already co-located overlay.

## Step 2: Prove the native-helper readback and backend boundary contracts

**Objective:** Ensure the new helper action remains observable and cannot turn
a wrong-monitor readback into a false healthy overlay.

**Implementation guidance:**

- Keep the existing presentation payload schema intact. Reuse optional helper
  diagnostics to expose the normal-path decision, pre/post monitor indexes, and
  the existing requested/applied rectangles when diagnostics are requested.
- Preserve the Python client's existing tolerance, bounded retry, and
  persistent-mismatch backoff. Do not weaken
  `wrong_monitor_applied_rect`, `applied_rect_mismatch`, or persistent mismatch
  handling.
- Add/adjust deterministic tests only where the helper action labels or
  diagnostics contract changes. Retain the existing simulated wrong-monitor
  case as the regression guard.
- Run the architecture-boundary test so generic follow/runtime code is proven
  not to gain direct GNOME-helper imports or enum dispatch.

**Test requirements:**

```bash
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
  overlay_client/tests/test_gnome_shell_helper_extension_source.py \
  overlay_client/tests/test_gnome_shell_helper_presentation_state.py \
  overlay_client/tests/test_gnome_helper_presentation_runtime.py \
  overlay_client/tests/test_backend_architecture_boundary.py -q
make check
```

If the environment cannot run `make check`, record the missing dependency or
environment constraint and run the focused pytest command; do not claim the
full gate passed. No `load.py` or EDMC hook flow is in scope, so no new plugin
lifecycle harness test is required unless the implementation expands into that
wiring.

**Integration:** The helper remains compositor-owned and the native client
continues to decide readiness from the existing validated applied rectangle.
X11 and XWayland-compatibility remain separate backend consumers with no code
change.

**Demo:** A simulated one-cycle lag succeeds only after a matching readback;
a persistent one-monitor-right readback still retries, backs off, and suppresses
the overlay. Architecture tests confirm the GNOME behavior did not leak into
generic follow code.

## Step 3: Deploy the helper update and validate live GNOME Wayland handoff

**Objective:** Prove the shipped native GNOME Wayland behavior in the actual
session and capture evidence sufficient to decide whether the change is ready
to commit.

**Implementation guidance:**

- Use the repository's helper development/install workflow to install or
  reload the changed GNOME Shell extension in the active session. Keep this
  work within the helper's existing lifecycle tooling; do not change helper
  protocol/versioning unless a real compatibility requirement appears.
- Enable only the existing presentation diagnostics needed to capture the
  action label, target monitor, overlay pre/post monitor, requested rectangle,
  applied rectangle, and degrade reasons.
- Test both handoff directions. Start with the overlay on the opposite monitor
  from Elite, then move Elite back and forth repeatedly. Test an already
  co-located case to confirm that no extra monitor transfer occurs.
- Verify click-through, no focus theft, chrome-free appearance, stacking above
  Elite, and resize follow. Treat an apparent visual success with mismatched
  helper readback as a failure.
- If `move_to_monitor` settles only on a subsequent presentation cycle, accept
  it only when the existing bounded retry reports a matching applied rectangle.
  Persistent mismatch remains a blocker; do not add sleeps, coordinate guesses,
  fullscreen workarounds, or cross-backend fallbacks.

**Test requirements:**

```bash
./scripts/dev_gnome_helper.sh status
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
  overlay_client/tests/test_gnome_shell_helper_extension_source.py \
  overlay_client/tests/test_gnome_shell_helper_presentation_state.py \
  overlay_client/tests/test_gnome_helper_presentation_runtime.py \
  overlay_client/tests/test_backend_architecture_boundary.py -q
```

Record the exact helper reload/install command used, session type, GNOME Shell
version, target and overlay monitor indexes, requested/applied rectangles,
action labels, and pass/fail result for every matrix case. Run `make check`
again after any code change made while resolving live findings.

**Integration:** This is the deployment-level proof of the helper change from
Steps 1–2. It exercises only the native GNOME Wayland backend; a successful
result does not imply X11 or XWayland behavior changed.

**Demo:** Elite on either monitor receives a visible, click-through overlay on
the same monitor with matching helper readback. Repeated transfers remain
aligned and do not steal focus. The logs show the guarded transfer only when
the monitor indexes differ.

## Completion Criteria

The implementation is ready for a reviewed commit only when all of the
following are true:

- Focused helper, presentation-state/runtime, and architecture-boundary tests
  pass.
- `make check` passes, or any environmental inability to run it is explicitly
  documented and approved.
- The change is limited to the GNOME helper, its tests, and relevant
  documentation; no X11, XWayland-compatibility, renderer, payload, or generic
  follow-surface behavior changes are present.
- The live GNOME Wayland matrix passes in both monitor directions, including
  click-through, focus, stacking, and resize behavior.
- Helper readback matches the requested rectangle within the existing
  tolerance. Persistent mismatch remains degraded/suppressed.
- Test commands, manual evidence, known limitations, and any skip are recorded
  in the progress document before commit.
