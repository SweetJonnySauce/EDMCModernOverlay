`send_raw` is the lowest-level helper for emitting legacy payloads. It lives in the `EDMCOverlay.edmcoverlay.Overlay` compatibility layer and normalizes a raw dict into a `LegacyOverlay` message, shape, clear, or raw payload. Coordinates use the legacy 1280x960 virtual canvas; the overlay client scales them to the current window size.

This document covers the payload shape, defaults, and common usage patterns for `send_raw`.

## API signature

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_raw({
    "id": "my-raw-id",
    "text": "Hello CMDR",
    "color": "#80d0ff",
    "x": 40,
    "y": 40,
    "ttl": 6,
})
```

`send_raw` requires a dict and raises `TypeError` if you pass anything else.

## Normalization order

`send_raw` inspects the payload in this order:

1. If `command` is present, handle it and return (`exit` clears all; `noop` does nothing).
2. If `text` is non-empty, emit a **message** payload (ignores `shape`/`vector`).
3. If `shape` is present, emit a **shape** payload.
4. If `ttl <= 0` and `id` is present, emit a **legacy_clear** payload.
5. If the payload is `id`-only, emit a **legacy_clear** payload.
6. If `text == ""` and `id` is present, emit a **message** payload with empty text (clear-by-id).
7. Otherwise emit a **raw** payload that is stored for future handling.

## Field reference (top-level)

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Recommended. Stable identifier used for updates, grouping, and clears. Prefix matching is case-insensitive. |
| `text` | string | Optional. Non-empty makes this a message. Empty string clears a message by `id`. |
| `color` | string | Optional. Named color or `#RRGGBB`/`#AARRGGBB`. Defaults to `white` for messages/shapes. |
| `size` | enum | Optional. Message size preset: `small`, `normal`, `large`, or `huge` (case-insensitive). Defaults to `normal`. **Note:** top-level `size` applies to messages only. |
| `x` / `y` | integer | Optional. `rect` uses a top-left corner; `circle` uses a centre, both in the 1280x960 legacy canvas. |
| `ttl` | integer | Optional. Seconds before expiry. `0` (or any value <= 0) makes the payload persistent. Default is `4`. |
| `shape` | string | Optional. Shape name (e.g., `rect`, `circle`, `vect`). |
| `fill` | string | Optional. Fill color for `rect` or `circle`; empty or `"none"` is transparent. |
| `w` / `h` | integer | Optional. Width/height for `shape="rect"`. |
| `radius` | integer | Required, strictly positive radius for `shape="circle"`. |
| `thickness` | integer | Required, strictly positive border width for `shape="circle"`; optional, strictly positive border width for `shape="rect"`. An explicit value uses legacy-canvas units and scales with the shape. Omitting it for `rect` preserves the existing client-controlled default. |
| `vector` | array | Optional. Vector points for `shape="vect"`. |
| `plugin` | string | Optional. Source plugin label for attribution/grouping. |
| `command` | string | Optional. `exit` clears all; `noop` does nothing; other values are ignored. |

### Vector point fields (`shape="vect"`)

| Field | Type | Notes |
|-------|------|-------|
| `x` / `y` | integer | Required. Point coordinate in legacy canvas. |
| `color` | string | Optional. Marker/text color for this point. |
| `marker` | string | Optional. `circle` or `cross`. |
| `text` | string | Optional. Marker label text. |
| `size` | enum | Optional. Marker label size preset: `small`, `normal`, `large`, `huge`. Applies only when `text` is present. |

Vector payloads must contain at least two points, or a single point that has `marker` or `text`. Otherwise the payload is dropped.

> ⚠️ **Caution:** `size` for marker text is not backwards compatible with legacy overlays such as EDMCOverlay. Make sure the CMDR is using EDMCModernOverlay before sending payloads with this keyword argument.

## Coordinate system

Legacy payloads always target a 1280x960 virtual canvas. Modern Overlay remaps those coordinates to the active window, so you only need to compute legacy positions once.

- `x=0, y=0` is the top-left of the legacy canvas.
- `x=640` is the horizontal midpoint.
- `x=1280, y=960` is the bottom-right.

If you need a payload to follow a group anchor or justification, pair your IDs with `define_plugin_group` and anchor that prefix (see [`define_plugin_group-API`](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/define_plugin_group-API)).

## Examples

### Example 1: Message (same as `send_message`)

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_raw({
    "id": "myplugin-status",
    "text": "Docking granted",
    "color": "#80d0ff",
    "x": 40,
    "y": 40,
    "ttl": 4,
    "size": "normal",
})
```

### Example 2: Rectangle

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_raw({
    "id": "myplugin-rect",
    "shape": "rect",
    "color": "#ff9c6b",
    "fill": "#1a1a1acc",
    "x": 50,
    "y": 50,
    "w": 300,
    "h": 80,
    "thickness": 2,
    "ttl": 6,
})
```

### Example 3: Circle

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_raw({
    "id": "legacy-circle-1",
    "shape": "circle",
    "color": "#80d0ff",
    "fill": "#1a1a1acc",
    "x": 100,
    "y": 200,
    "radius": 50,
    "thickness": 2,
    "ttl": 7,
    "plugin": "CirclePlugin",
})
```

Raw/TCP normalization retains supported shape thickness fields for the client.
It does not make the geometry decision: the client warns and drops a missing,
non-numeric, zero, or negative circle `radius`/`thickness`, or an explicitly
supplied invalid rectangle `thickness`, before that payload can replace a
visible same-ID shape. An omitted rectangle thickness keeps the existing client
default.

### Example 4: Vector with marker label size

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_raw({
    "id": "myplugin-vector",
    "shape": "vect",
    "ttl": 10,
    "vector": [
        {"x": 100, "y": 100},
        {"x": 200, "y": 160, "marker": "circle", "text": "Target", "size": "small"},
    ],
})
```

### Example 5: Clear by ID

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_raw({
    "id": "myplugin-status",
    "text": "",
})
```

Clears are resolved by `id`; other fields are ignored when `text` is empty.

## Runtime behavior

- Messages and shapes with the same `id` replace the existing entry and refresh the TTL.
- Empty `text` removes the message immediately.
- A `shape="circle"` uses centre `x`/`y`, positive `radius` and `thickness`, the requested `color` border, and an optional transparent `fill`. It is a shape primitive, not a `marker: "circle"` vector point.
- Explicit `thickness` for `circle` or `rect` is a logical legacy-canvas width;
  the renderer scales, rounds, and clamps it to at least one physical pixel.
  Omitted rectangle thickness keeps the current client-controlled width.
- Vector payloads with insufficient points are dropped (unless a single point has `marker` or `text`).
- Size presets are derived from the overlay font settings; adjust the "Font Step" and base font size in preferences to tune `small`/`large`/`huge`.
- Plugin ownership is inferred from `id` prefixes (case-insensitive). If your payloads do not include a `plugin` field, add prefixes via `define_plugin_group` so the overlay can attribute payloads correctly.

## Debugging

- `overlay-payloads.log` mirrors incoming legacy payloads when payload logging is enabled.
- Run `python3 utils/payload_inspector.py` to tail that log and inspect resolved plugin/group labels and live IDs.
