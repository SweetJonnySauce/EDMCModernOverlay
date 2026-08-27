`send_shape` is the legacy helper for drawing rectangles and circles on the Overlay. It is part of the `EDMCOverlay.edmcoverlay.Overlay` compatibility layer and emits a `LegacyOverlay` shape payload. Coordinates use the legacy 1280x960 virtual canvas; the overlay client scales them to the current window size.

This document covers the payload shape, defaults, and common usage patterns for `send_shape`.

## API signature

The positional rectangle signature remains supported:

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_shape(
    shapeid,  # stable string id for updates and grouping
    shape,    # shape name (use "rect")
    color,    # border color (named or #RRGGBB/#AARRGGBB)
    fill,     # fill color (named or #RRGGBB/#AARRGGBB)
    x,        # left edge in 1280x960
    y,        # top edge in 1280x960
    w,        # width in 1280x960
    h,        # height in 1280x960
    ttl,      # seconds; 0 means persistent
)
```

To request an explicit rectangle border width, use keyword arguments and add
`thickness`. Omitting it leaves the legacy rectangle payload unchanged and lets
the client keep its configured `legacy_rect` border width:

```python
overlay.send_shape(
    "myplugin-box",
    "rect",
    color="#80d0ff",
    fill="none",
    x=100,
    y=100,
    w=200,
    h=80,
    thickness=2,
    ttl=5,
)
```

For a circle, keep the stable ID and shape token positional, then use named
arguments for the colour and geometry. A circle has a centre (`x`, `y`), not a
top-left corner, and does not send `w` or `h`:

```python
overlay.send_shape(
    "myplugin-radius",
    "circle",
    color="#80d0ff",
    fill="#1a1a1acc",
    x=100,
    y=100,
    radius=50,
    thickness=2,
    ttl=5,
)
```

The circle form wraps and publishes this legacy payload:

```json
{
  "event": "LegacyOverlay",
  "type": "shape",
  "shape": "circle",
  "id": "myplugin-radius",
  "color": "#80d0ff",
  "fill": "#1a1a1acc",
  "x": 100,
  "y": 100,
  "radius": 50,
  "thickness": 2,
  "ttl": 5
}
```

## Field reference

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Required. Stable identifier used for updates, grouping, and clears. Prefix matching is case-insensitive. |
| `shape` | string | Required. Use `rect` or `circle`. |
| `color` | string | Required. Border color. Named color or `#RRGGBB`/`#AARRGGBB`. |
| `fill` | string | Required. Fill color. Named color or `#RRGGBB`/`#AARRGGBB`. Empty or `"none"` renders transparent. |
| `x` / `y` | integer | Required. Rectangle: top-left corner. Circle: centre, both in the 1280x960 legacy canvas. |
| `w` / `h` | integer | Required for `rect` only. Width/height in the 1280x960 legacy canvas. Do not send these for `circle`. |
| `radius` | integer | Required and strictly positive for `circle`; the circle radius in legacy-canvas units. |
| `thickness` | integer | Required and strictly positive for `circle`; optional and strictly positive for `rect`. When supplied, it is a legacy-canvas border width that scales with the shape. When omitted for `rect`, no field is sent and the existing client-controlled rectangle width is preserved. |
| `ttl` | integer | Required. Seconds before expiry. `0` (or any value <= 0) makes the shape persistent. |

If you need vector shapes (`shape="vect"`), use `send_raw` and include a `vector` list. `send_shape` does not accept vector points.

## Coordinate system

Legacy payloads always target a 1280x960 virtual canvas. Modern Overlay remaps those coordinates to the active window, so you only need to compute legacy positions once.

- `x=0, y=0` is the top-left of the legacy canvas.
- `x=640` is the horizontal midpoint.
- `x=1280, y=960` is the bottom-right.

If you need a shape to follow a group anchor or justification, pair your IDs with `define_plugin_group` and anchor that prefix (see [`define_plugin_group-API`](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/define_plugin_group-API)).

## Examples

### Example 1: Simple rectangle

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_shape(
    "myplugin-rect",
    "rect",
    "#80d0ff",
    "#00000000",  # transparent fill
    40,
    40,
    200,
    60,
    4,
)
```

### Example 2: Filled banner block

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_shape(
    "myplugin-banner-bg",
    "rect",
    "#ffd27f",
    "#1a1a1acc",
    20,
    20,
    400,
    90,
    0,  # persistent until cleared
)
```

### Example 3: Circle with transparent fill

```python
overlay.send_shape(
    "myplugin-radius",
    "circle",
    color="#80d0ff",
    fill="none",
    x=100,
    y=100,
    radius=50,
    thickness=2,
    ttl=5,
)
```

## Runtime behavior

- Shapes with the same `id` replace the existing entry and refresh the TTL.
- Clear a shape by its stable `id` using the existing raw clear-by-ID behavior.
- `fill` is transparent when empty or `"none"`; `color` requests the circle or rectangle border colour.
- Explicit thickness is resolved after the viewport/group transform: it is scaled,
  rounded, and clamped to at least one physical pixel. This applies to both
  supported shapes.
- Circle `radius` and `thickness`, and an explicitly supplied rectangle
  `thickness`, must be numeric and strictly positive. Invalid geometry is warned
  about and dropped by the client before it can replace a visible same-ID shape.
- `rect` and `circle` are supported by `send_shape`; use `send_raw` for vectors.
- Plugin ownership is inferred from `id` prefixes (case-insensitive). If your payloads do not include a `plugin` field, add prefixes via `define_plugin_group` so the overlay can attribute payloads correctly.

## Debugging

- `overlay-payloads.log` mirrors incoming legacy payloads when payload logging is enabled.
- Run `python3 utils/payload_inspector.py` to tail that log and inspect resolved plugin/group labels and live IDs.
