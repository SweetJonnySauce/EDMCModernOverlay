# Task: Add Guarded Normal-Path Monitor Transfer

## Description
Correct the native GNOME Shell helper's ordinary overlay-presentation path so an
overlay on a different monitor transfers to the trusted Elite target monitor
before the existing frame-resize operation. Preserve the existing fail-closed
readback validation and all non-GNOME backend boundaries.

## Background
The helper currently resizes the overlay frame without changing its compositor
monitor assignment. Runtime evidence shows that can leave the overlay exactly
one monitor width from the requested global rectangle. The helper already has
the target payload and overlay `Meta.Window`; this task adds a guarded,
normal-path `move_to_monitor` decision before the established resize fallback.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/existing-code-and-runtime-evidence.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/mutter-window-placement.md`

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Limit production changes to the normal attach/presentation flow in `helpers/gnome_shell_extension/extension.js` and focused source-contract coverage in `overlay_client/tests/test_gnome_shell_helper_extension_source.py`.
2. Read the overlay's current monitor and normalise the trusted target monitor from the existing target payload. Invoke `window.move_to_monitor(targetMonitor)` only when both indexes are valid non-negative integers and they differ.
3. Invoke the guarded monitor transfer before the existing `move_resize_frame` fallback. A matching frame is a no-op only when the overlay is also already on the target monitor.
4. If monitor transfer is unavailable or throws, record an internal helper diagnostic/degrade condition and continue through the existing resize and applied-rectangle readback gate. Do not treat a normally returned transfer or resize call as placement success.
5. Preserve post-operation frame and monitor reads, existing tolerance/mismatch behavior, stacking, click-through, focus safety, public helper protocol/schema, and diagnostic strategy-probe-only behavior.
6. Do not modify native X11, XWayland compatibility, renderer selection, payload processing, backend selection, or generic follow/runtime surfaces.

## Dependencies
- The existing trusted target payload must continue to provide the target monitor in the normal attach path.
- Existing helper diagnostics and applied-rectangle readback validation remain the observability and fail-closed mechanisms.
- Mutter `Meta.Window.get_monitor()`, `move_to_monitor()`, and `move_resize_frame()` behavior documented in the linked research.

## Implementation Approach
1. Extend the established Python source-contract tests first to state the guarded transfer, no-op, fallback, ordering, and post-operation readback contracts.
2. In the helper's non-strategy-probe branch, derive valid overlay and target monitor indexes; perform and label a monitor transfer only for a valid mismatch, then retain the existing resize fallback decision.
3. Ensure unavailable or failed transfer is visible through the existing internal result/diagnostic path while resize and post-operation readback continue to determine healthy versus degraded placement.
4. Run the focused test and diff checks, then inspect the scoped diff for excluded backend or protocol changes.

## Acceptance Criteria

1. **Valid monitor mismatch transfers before resize**
   - Given valid unequal target and overlay monitor indexes in the normal presentation path
   - When the helper applies overlay presentation
   - Then source-contract coverage proves `move_to_monitor(targetMonitor)` is selected before `move_resize_frame` and the normal resize operation remains available afterward

2. **Co-located overlay avoids unnecessary monitor movement**
   - Given valid equal target and overlay monitor indexes with a matching frame
   - When the helper applies overlay presentation
   - Then it records the matching-frame no-op without calling `move_to_monitor`

3. **Invalid monitor state preserves the proven fallback**
   - Given a missing, invalid, or negative target or overlay monitor index
   - When the helper applies overlay presentation
   - Then it skips monitor transfer and retains the existing resize/readback path without reporting false placement success

4. **Transfer failures remain observable and fail closed**
   - Given an unavailable or throwing `move_to_monitor` operation for a valid mismatch
   - When the helper applies overlay presentation
   - Then it records the transfer condition, attempts the established resize fallback, and preserves applied-rectangle mismatch degradation rather than accepting the method call as success

5. **Post-operation state and boundaries remain intact**
   - Given a completed normal-path presentation attempt
   - When source-contract tests inspect the helper implementation
   - Then post-operation frame and monitor reads remain present, strategy probes remain diagnostic-only, and no code outside the GNOME helper plus its focused test changes

6. **Focused validation passes**
   - Given the completed helper and test change
   - When running `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py -q` and `git diff --check`
   - Then the focused source-contract suite passes and the diff has no whitespace errors

## Metadata
- **Complexity**: Medium
- **Labels**: GNOME Wayland, Native Helper, Monitor Placement, Source Contract, Regression
- **Required Skills**: GNOME Shell JavaScript, Mutter Meta.Window API, Python pytest, Source-contract testing
