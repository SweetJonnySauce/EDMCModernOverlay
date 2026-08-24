# X11 Surface Artifact Repair Context

## Goal

Eliminate the long-running X11 artifact in which old, duplicated overlay tiles, including stale
Elite scene pixels, appear after window movement. The repair must preserve transparent rendering,
click-through, following, payload behavior, and the `fix219` backend boundary.

## User-observed behavior

- The issue occurs in a native X11 session after several hours of play.
- The top of the game acquires repeated rectangular tiles containing old overlay content and
  background pixels.
- The tiled background moves differently from the current game scene while Elite is moved.
- Leaving and returning to the game clears the issue temporarily; restarting EDMC clears it for a
  longer period.

This is evidence of stale transparent-window surface contents or X11 compositing damage, not
merely duplicate messages in the overlay payload store. The client does not paint Elite scene
pixels itself.

## Relevant implementation paths

| Area | Path | Current behavior |
| --- | --- | --- |
| Overlay widget paint entry | `overlay_client/overlay_client.py` | The normal `paintEvent` draws active content without an explicit transparent clear. The backend-suppressed branch clears first. |
| Surface setup | `overlay_client/setup_surface.py` | Enables `WA_TranslucentBackground`, `WA_NoSystemBackground`, and `X11BypassWindowManagerHint` on Linux. |
| Content renderer | `overlay_client/setup_surface.py`, `overlay_client/render_surface.py` | Draws active legacy payloads, optional backgrounds/grid/debug views, but does not establish a clear baseline itself. |
| X11 backend bundle | `overlay_client/backend/bundles/native_x11.py` | Uses the shared XCB integration and `wmctrl` tracker. |
| Follow/move flow | `overlay_client/follow_surface.py` | Tracks Elite and moves/resizes the separate overlay window. |
| Existing Qt paint tests | `overlay_client/tests/test_setup_surface.py` | Verifies dispatch to `_paint_overlay` and suppressed-mode skip only; it does not verify clearing or stale-content removal. |

`git blame` shows the transparent/no-system-background/X11-bypass combination arrived together in
commit `044247b` (2025-12-01). The explicit clear exists only in the backend-suppressed path,
added in `bc04f96d` (2026-05-12).

## Constraints and invariants

- This is a client/UI rendering change: use Qt unit tests plus manual native-X11 validation. No
  `load.py` hook changes are planned, so a new EDMC harness test is not required.
- Do not solve the issue by disabling transparent overlays, click-through, follow mode, or native
  X11 support.
- Keep compositor-specific behavior behind `overlay_client/backend`; do not add GNOME/helper
  dependencies to generic X11 render paths.
- Clear only the overlay's own ARGB surface. Never attempt to capture, redraw, or cache Elite
  content.
- Preserve the intentionally dirty `fix219` worktree; do not reset, stage, commit, or modify
  unrelated files.

## Candidate repair approaches

| Option | Assessment |
| --- | --- |
| A. Clear the transparent paint surface before every normal draw | Recommended first repair. It matches the existing suppressed-content safety path, has a small surface area, and directly prevents stale pixels from surviving a paint. |
| B. Remove `WA_NoSystemBackground` or enable Qt auto-fill | Do not use as the first repair. It changes Qt's background behavior globally and risks opaque flashes or platform-specific regressions. |
| C. Remove `X11BypassWindowManagerHint` | Diagnostic fallback only. It may avoid the artifact but could change stacking, focus, and click-through behavior. It needs a separately justified experiment if A fails. |
| D. Force hide/show or remap after every move | Reject as a primary fix. It masks surface corruption and risks flicker, focus changes, and additional window-manager churn. |

## Dependency map

```text
payload/follow update
  -> QWidget paint event for transparent X11 overlay
  -> explicit ARGB clear (new invariant)
  -> active payload/grid/debug draw
  -> X11 compositor presents only current overlay pixels
```

## Open questions

1. Does clearing the whole widget rect in `paintEvent` clear the complete native damaged surface
   under Qt/XCB, or should the implementation clear the exact paint region? The initial repair
   should prioritize correctness; profiling determines whether region scoping is safe later.
2. Can a native X11 session reproduce the failure with a bounded move/focus cycle, or does it
   require long gameplay? The acceptance procedure must record whichever is true.
3. If a full clear does not fix it, is `X11BypassWindowManagerHint` the contributing lifecycle
   trigger? Do not change that flag without a separate, reversible experiment.
