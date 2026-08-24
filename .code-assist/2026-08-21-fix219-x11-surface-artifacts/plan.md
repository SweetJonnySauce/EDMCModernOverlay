# Plan: Fix Native-X11 Transparent Surface Artifacts

## Scope and acceptance criteria

Repair only the overlay client's transparent X11 paint lifecycle.

The repair is acceptable when:

1. Every normal overlay paint begins from transparent pixels; previous overlay pixels cannot
   survive merely because a payload expires, moves, or is removed.
2. The backend-suppressed branch continues to clear content and does not regress its current
   behavior.
3. Current overlay content, optional background/grid/debug rendering, input transparency,
   follow mode, and X11 stacking remain functional.
4. A native X11 manual test shows no tiled stale content after focus changes and a bounded
   move/follow stress cycle. A longer game session is used when practical because that is the
   reported failure mode.
5. No Wayland/GNOME helper-specific behavior leaks into the generic paint path.

## Test strategy

### Automated tests — Qt unit tests

Add to `overlay_client/tests/test_setup_surface.py` (or a tightly focused adjacent test file).
The implementation will expose a minimal test seam for recording painter operations; tests must
fail before the repair because the normal path currently does not clear.

| ID | Input / setup | Expected result |
| --- | --- | --- |
| U1 | Normal `paintEvent` with active overlay rendering | A transparent clear occurs before `_paint_overlay`; painter then uses ordinary source-over drawing. |
| U2 | Backend-suppressed `paintEvent` | One transparent clear occurs; `_paint_overlay` is not called; paint-count behavior remains unchanged. |
| U3 | Two successive normal paints where the second has less content | The second paint starts with a clear, so no prior region is available for reuse. This is tested at the operation/order seam, not by brittle pixel snapshots. |
| U4 | Paint event with antialiasing enabled | Clearing does not leave the painter in `CompositionMode_Clear`; active text/vector/background drawing follows with the normal composition mode. |
| U5 | Existing paint dispatch tests | Existing normal and suppressed behavior still passes unchanged apart from the new clear invariant. |

The tests are `pyqt_required` because they exercise the widget event path. A harness test is not
needed: no EDMC hook, plugin lifecycle, socket, or `load.py` behavior changes.

### Manual native-X11 validation

CI's offscreen Qt platform cannot validate XCB compositor damage. Run manually on the affected
native-X11 environment:

1. Start EDMC, the overlay client, and Elite in the known working windowed configuration.
2. Confirm overlay visibility, click-through, and following before the stress sequence.
3. Move/focus Elite repeatedly for a bounded interval while visible payloads update and expire.
4. Confirm no stale/duplicated tiles or copied scene background appears; verify focus and input
   still behave normally.
5. Keep the overlay active through a representative longer gameplay session if feasible. Record
   only pass/fail and sanitized duration/configuration facts, never window IDs, titles, PIDs, or
   raw environment dumps.

If an artifact appears, stop the test and preserve the current client log as a local diagnostic
only; do not collect sensitive window/process data in project artifacts.

## Implementation stages

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add RED tests for normal clear-before-draw ordering and preserved suppressed behavior | Completed (RED recorded) |
| 2.2 | Add one private paint helper that clears the widget ARGB surface, restores source-over mode, and is used by both paint branches | Completed (GREEN recorded) |
| 2.3 | Run focused Qt tests and inspect for rendering/follow regressions | Completed (scoped review recorded) |
| 3.1 | Perform bounded native-X11 move/focus/follow validation | Pending review |
| 3.2 | Perform representative extended X11 gameplay validation | Pending review |
| 4.1 | Run targeted and project validation; document outcome and rollback | Blocked by pre-existing mypy failures |

## Design decision

Use option A: clear the overlay widget's transparent surface at the beginning of *every* paint,
then draw the current frame. The clear must be shared by the normal and suppressed branches so
their semantics cannot drift.

The helper should be private to `OverlayWindow` and should not know whether the selected backend
is X11, Wayland, GNOME, or helper-backed. It only establishes the Qt rendering invariant needed
by a translucent `QWidget`: before current-frame drawing, the surface contains no prior-frame
pixels.

Initially clear the complete widget paint surface rather than trying to calculate stale regions.
This favors correctness and reversibility. If profiling later shows a material cost, a separate
follow-up may safely consider region-aware clearing after native-X11 evidence proves equivalent
behavior.

## Test implementation detail

`test_setup_surface.py` uses a small recording replacement for the module-local `QPainter` in
the direct `OverlayWindow.paintEvent` unit tests. It records composition, transparent fill,
antialiasing, overlay dispatch, and painter finalization without relying on screen pixels. The
RED cases assert the normal and repeated-normal ordering, the suppressed no-overlay path, and
unchanged `paint_count` increments. This remains a `pyqt_required` unit seam; no lifecycle or
`load.py` behavior is in scope, so no harness test is required.

### RED evidence

`QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest
overlay_client/tests/test_setup_surface.py -q` produced the expected three failures before the
repair: the normal path began with antialiasing instead of transparent clear, the suppressed
path did not restore source-over, and both repeated normal paints lacked the clear prefix. Three
unrelated existing tests passed. The first attempt without `QT_QPA_PLATFORM=offscreen` aborted
during Qt application startup; the repository-standard offscreen setting was the one permitted
environment remediation and exposed the intended RED failures.

### GREEN evidence

The private `OverlayWindow._clear_transparent_surface` helper is backend-neutral. It clears the
overlay widget rect with transparent pixels in clear composition mode, restores source-over, and
is called before the suppressed/normal branch. `QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m
pytest overlay_client/tests/test_setup_surface.py -q` passed all 6 tests after the change.

### Automated-validation stop

The prescribed Qt/repaint/follow test command passed 55 tests and the prescribed scoped Ruff
command passed. The prescribed `python -m mypy overlay_client/overlay_client.py` command failed
with 115 existing errors across 14 imported client modules. One scoped diagnosis using
`--follow-imports=skip` still found five existing attribute-typing errors in `overlay_client.py`
outside this repair; it found no error at the new surface-clear helper. Per the orchestration stop
protocol, no further remediation or validation command (including `make check` or `git diff
--check`) may run in this execution. The native-X11 manual gate remains unrequested because
automated validation did not complete.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Full clears increase paint cost at high resolution | Keep the repair minimal; measure on native X11 before optimizing. The client already coalesces ordinary repaint requests. |
| Qt/XCB clips a full-rect clear to a partial invalidation region | Validate with real X11 movement; if it fails, investigate an explicit full-surface invalidation/remap in a separate iteration. |
| The root trigger is also `X11BypassWindowManagerHint` | Do not change it in the first patch. If artifacts persist after a correct clear, conduct an isolated, reversible flag experiment with stacking/focus/click-through tests. |
| Child widgets retain stale pixels independently | Check the `message_label` during native validation. If implicated, add a child-specific clear/update plan rather than broadening the first patch. |
| Change conflicts with the active fix219 worktree | Limit the patch to paint helper/tests unless evidence requires more; preserve all unrelated changes. |

## Validation commands

Run after implementation, using the established project environment:

```bash
source overlay_client/.venv/bin/activate && python -m pytest \
  overlay_client/tests/test_setup_surface.py \
  overlay_client/tests/test_repaint_debounce.py \
  overlay_client/tests/test_follow_surface_mixin.py -q

source overlay_client/.venv/bin/activate && python -m ruff check \
  overlay_client/overlay_client.py \
  overlay_client/tests/test_setup_surface.py

source overlay_client/.venv/bin/activate && python -m mypy overlay_client/overlay_client.py

source overlay_client/.venv/bin/activate && make check
git diff --check
```

`make check` requires the GUI-capable environment used by this repository. Native-X11 manual
validation remains mandatory even when the automated checks pass.

## Rollback

The first implementation should be limited to the shared paint-clear helper and its tests. If it
causes a visible regression, reverting that narrow change restores the current rendering behavior
without altering the backend selector, X11 tracker, helper integrations, preferences, or stored
settings.
