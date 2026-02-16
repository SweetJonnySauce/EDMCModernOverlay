`send_shape` is the legacy helper for drawing rectangles on the Overlay. It is part of the `EDMCOverlay.edmcoverlay.Overlay` compatibility layer and emits a `LegacyOverlay` shape payload. Coordinates use the legacy 1280x960 virtual canvas; the overlay client scales them to the current window size.

This document covers the payload shape, defaults, and common usage patterns for `send_shape`.

## API signature

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

`send_shape` wraps and publishes this legacy payload:

```json
{
  "event": "LegacyOverlay",
  "type": "shape",
  "shape": "rect",
  "id": "my-rect-id",
  "color": "#80d0ff",
  "fill": "#1a1a1acc",
  "x": 40,
  "y": 40,
  "w": 200,
  "h": 60,
  "ttl": 6
}
```

## Field reference

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Required. Stable identifier used for updates, grouping, and clears. Prefix matching is case-insensitive. |
| `shape` | string | Required. Use `rect`. Other shapes are ignored or dropped. |
| `color` | string | Required. Border color. Named color or `#RRGGBB`/`#AARRGGBB`. |
| `fill` | string | Required. Fill color. Named color or `#RRGGBB`/`#AARRGGBB`. Empty/falsey values render transparent. |
| `x` / `y` | integer | Required. Top-left corner of the rectangle in the 1280x960 legacy canvas. |
| `w` / `h` | integer | Required. Width/height in the 1280x960 legacy canvas. |
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

## Runtime behavior

- Shapes with the same `id` replace the existing entry and refresh the TTL.
- `fill` defaults to transparent when empty or falsey.
- Only `rect` is supported by `send_shape`; use `send_raw` for vectors.
- Plugin ownership is inferred from `id` prefixes (case-insensitive). If your payloads do not include a `plugin` field, add prefixes via `define_plugin_group` so the overlay can attribute payloads correctly.

## Debugging

- `overlay-payloads.log` mirrors incoming legacy payloads when payload logging is enabled.
- Run `python3 utils/payload_inspector.py` to tail that log and inspect resolved plugin/group labels and live IDs.
