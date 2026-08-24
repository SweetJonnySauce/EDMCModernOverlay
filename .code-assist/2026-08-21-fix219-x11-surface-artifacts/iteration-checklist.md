# Iteration Checklist: Native-X11 Transparent Surface Artifact Repair

## Outcome

Current status: **the narrow surface-clear repair is implemented and focused Qt/Ruff validation
passes. Full automated validation is blocked by pre-existing mypy failures. Native-X11 manual
validation has not started and remains user-gated.**

The implementation does not change backend selection, X11 window flags, follow behavior, EDMC
hooks, configuration, or compositor/helper behavior. It introduces one backend-neutral paint
invariant: every `OverlayWindow` frame begins with an explicitly transparent surface.

## Phase tracking

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Reconcile the approved plan, execution status, diff, and validation evidence | Completed |
| 5.2 | Audit the transparent-surface repair and the Qt unit-test seam | Completed |
| 5.3 | Assess automated validation, manual gates, and remaining blockers | Completed |
| 5.4 | Record scope-specific EDMC compliance and the readiness decision | Completed |

Phase 5 status: **Completed**

## Requirements and diagnosis

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| R1 | Does the repair address stale native-window pixels rather than payload de-duplication? | Yes | The normal `paintEvent` now clears the client-owned translucent surface before drawing current content; no payload model logic changed. |
| R2 | Does it explain duplicate tiles containing old scene pixels? | Yes | A transparent ARGB backing surface can retain prior composited pixels. Clearing it prevents prior-frame content from surviving into the next overlay frame. |
| R3 | Is the scope limited to the lowest-risk first hypothesis? | Yes | The patch does not alter `WA_NoSystemBackground`, `X11BypassWindowManagerHint`, stacking, focus, click-through, or follow geometry. |
| R4 | Is a fallback path defined if the clear does not resolve the artifact? | Yes | The plan requires a separate reversible X11-bypass experiment only after native-X11 evidence proves the clear insufficient. |

## Implementation and boundary review

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| I1 | Does normal painting clear before active drawing? | Yes | `OverlayWindow._clear_transparent_surface` runs before the normal/suppressed branch in `overlay_client/overlay_client.py`. |
| I2 | Does the clear restore source-over composition before content drawing? | Yes | The helper switches from `CompositionMode_Clear` back to `CompositionMode_SourceOver`; normal painting then enables antialiasing and calls `_paint_overlay`. |
| I3 | Is suppressed-content behavior preserved? | Yes | The suppressed branch still clears, skips `_paint_overlay`, ends the painter, increments its existing metric once, calls `super().paintEvent`, and returns. |
| I4 | Is the repair backend-neutral? | Yes | The helper has no backend, compositor, helper, or raw-enum dependency. No backend bundle/follow-surface boundary changed. |
| I5 | Were follow, click-through, window flags, settings, and EDMC hooks left unchanged? | Yes | The task diff is limited to `overlay_client/overlay_client.py`, `overlay_client/tests/test_setup_surface.py`, and task documentation. |
| I6 | Is the test seam deterministic and scoped? | Yes | A recording replacement for the module-local `QPainter` asserts operation order without relying on fragile compositor pixels. |

## Validation evidence

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| V1 | Was RED evidence captured before implementation? | Yes | Offscreen PyQt test run: 3 expected failures and 3 passes; normal paints lacked clear-first behavior and the suppressed path did not restore source-over. |
| V2 | Did the added/updated Qt tests pass after implementation? | Yes | `QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest overlay_client/tests/test_setup_surface.py -q`: 6 passed in 0.44s. |
| V3 | Did focused rendering/follow regression tests pass? | Yes | `QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py -q`: 55 passed in 1.23s. |
| V4 | Did scoped lint pass? | Yes | `python -m ruff check overlay_client/overlay_client.py overlay_client/tests/test_setup_surface.py`: passed. |
| V5 | Did scoped mypy pass? | No | `python -m mypy overlay_client/overlay_client.py` reports 115 pre-existing errors across 14 imported client modules. A `--follow-imports=skip` diagnosis still reports five unrelated pre-existing attribute errors; none reference the new helper. Separate type-debt authority or an explicit validated waiver is required. |
| V6 | Did `make check` pass? | No | Correctly not run after the prescribed mypy gate blocked, per the execution stop protocol. |
| V7 | Did patch hygiene pass? | No | Correctly not run after the prescribed mypy gate blocked. Run `git diff --check` only when the validation gate has a resolved disposition. |

## Manual native-X11 gate

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| M1 | Was any live EDMC/Elite/X11 action performed? | No | Correctly excluded from the automated iteration. |
| M2 | Is bounded move/focus/follow validation complete? | No | Requires explicit user approval and an affected native-X11 session. |
| M3 | Is representative long-session validation complete? | No | Requires separate user-performed evidence after M2 passes. |
| M4 | Is changing `X11BypassWindowManagerHint` authorized? | No | Correctly deferred unless the transparent-clear repair fails native-X11 validation. |

## Scope-specific EDMC compliance

| Category | Yes/No | Evidence and action |
| --- | --- | --- |
| Stay aligned with EDMC core | Yes | Plugin layout, entrypoints, version gates, and EDMC runtime behavior are untouched. |
| Supported APIs and helpers | Yes | No EDMC imports, requests, config, or monitor behavior changed. |
| Logging and versioning | Yes | No logger, `print`, traceback, or version-gate behavior changed. |
| Responsive and Tk-safe runtime | Yes | The change is a synchronous Qt paint-event operation on the GUI thread; no EDMC Tk hook or worker ownership changed. |
| Preferences and UI hooks | Yes | Preferences/configuration/UI-hook code is untouched. |
| Dependency and debug HTTP handling | Yes | No dependency, package, HTTP, or debug-sender behavior changed. |

## Readiness decision

- Repair implementation and focused behavior tests: **Yes — complete.**
- Full automated validation: **No — blocked pending an explicit disposition for existing mypy
  failures.**
- Native-X11 manual validation: **No — not authorized or started.**
- Broaden the repair to window flags/remapping: **No — not justified yet.**
- Commit or push: **No — not authorized.**

The next action is to decide how to handle the existing type-check blocker. After a valid
pass/waiver disposition, run the deferred project and patch-hygiene gates. Only then request
explicit approval for bounded native-X11 validation. If that validation fails, open a new,
separate reversible experiment for the X11 bypass-window-manager flag.
