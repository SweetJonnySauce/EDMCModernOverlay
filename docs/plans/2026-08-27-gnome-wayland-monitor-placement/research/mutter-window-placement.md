# Mutter window placement research

## Primary-source findings

Mutter's current `Meta.Window` API documents that:

- [`get_monitor()`](https://gnome.pages.gitlab.gnome.org/mutter/meta/class.Window.html)
  returns the monitor index on which a window resides.
- [`move_to_monitor()`](https://gnome.pages.gitlab.gnome.org/mutter/meta/class.Window.html)
  moves a window to the supplied monitor index while preserving the relative
  position of its top-left corner.
- [`move_resize_frame()`](https://gnome.pages.gitlab.gnome.org/mutter/meta/class.Window.html)
  resizes a window so its outer frame fits the supplied rectangle.
- `Meta.Display` exposes monitor geometry and monitor-enter/leave signals,
  confirming that monitor identity and desktop geometry are distinct concepts.
  See [Meta.Display](https://gnome.pages.gitlab.gnome.org/mutter/meta/class.Display.html).

This means a move to the target monitor followed by resize is semantically
valid: the move changes monitor assignment; the resize then establishes the
target frame rectangle.

## Application to the observed failure

The overlay began on the monitor whose origin is `x=3440`. The helper asked for
an `x=0` full-monitor rectangle but later reported `x=3440`. That result is
consistent with monitor assignment taking precedence over the coordinate-only
resize request. It is also consistent with the current implementation never
calling `move_to_monitor()` during ordinary placement.

## Important constraints

1. Treat the Elite `Meta.Window.get_monitor()` result as authoritative. Do not
   derive a target monitor by guessing from display order, primary status, or
   Qt screen order.
2. Use `move_to_monitor()` only when the overlay's own `get_monitor()` differs
   from that target index. Avoid unnecessary moves and focus/stacking churn.
3. Re-read the overlay frame and monitor after the operation. A successful API
   call is not sufficient evidence that the compositor applied the requested
   rectangle.
4. Preserve the existing mismatch/degrade gate. It is correctly preventing a
   visibly wrong overlay from being treated as healthy.
5. Validate on the real GNOME session. The sandbox cannot reach the session
   bus, so it cannot execute a safe helper probe or verify timing/visibility.

## Decision

Use a guarded `move_to_monitor(targetMonitor)` then
`move_resize_frame(requestedRect)` sequence in the normal native GNOME Wayland
placement path, only after focused tests establish the exact ordering and
observability contract. Do not use the existing strategy-probe mechanism as a
production switch: it is diagnostic and includes intentionally risky
fullscreen variants.
