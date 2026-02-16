`send_message` is the helper for placing text on the Overlay. It is part of the `EDMCOverlay.edmcoverlay.Overlay` compatibility layer and emits a `LegacyOverlay` message payload. Coordinates use the legacy 1280x960 virtual canvas; the overlay client scales them to the current window size.

This document covers the payload shape, defaults, and common usage patterns for `send_message`.

## API signature

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_message(
    msgid,   # stable string id for updates and grouping
    text,    # message text ("" clears the message)
    color,   # color string (named or #RRGGBB/#AARRGGBB)
    x,       # left edge in 1280x960
    y,       # top edge in 1280x960
    ttl=4,   # seconds; 0 means persistent
    size="normal",
)
```

`send_message` wraps and publishes this legacy payload:

```json
{
  "event": "LegacyOverlay",
  "type": "message",
  "id": "my-message-id",
  "text": "Hello CMDR",
  "color": "#80d0ff",
  "x": 640,
  "y": 40,
  "ttl": 6,
  "size": "large"
}
```

## Field reference

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Required. Stable identifier used for updates, grouping, and clears. Prefix matching is case-insensitive. |
| `text` | string | Required. An empty string removes the existing message with the same `id`. `\n` creates multi-line output. |
| `color` | string | Required. Named color or `#RRGGBB`/`#AARRGGBB`. |
| `x` / `y` | integer | Required. Top-left corner of the text block in the 1280x960 legacy canvas. |
| `ttl` | integer | Optional. Seconds before expiry. `0` (or any value <= 0) makes the message persistent. |
| `size` | enum | Optional. `small`, `normal`, `large`, or `huge` (case-insensitive). Unknown values render as `normal`. |

## Coordinate system

Legacy payloads always target a 1280x960 virtual canvas. Modern Overlay remaps those coordinates to the active window, so you only need to compute legacy positions once.

- `x=0, y=0` is the top-left of the legacy canvas.
- `x=640` is the horizontal midpoint.
- `x=1280, y=960` is the bottom-right.

If you need a message to follow a group anchor or justification, pair your IDs with `define_plugin_group` and anchor that prefix (see [`define_plugin_group-API`](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/define_plugin_group-API)).

## Examples

### Example 1: Simple status message

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_message(
    "myplugin-status",
    "Docking granted",
    "#80d0ff",
    40,
    40,
    ttl=4,
    size="normal",
)
```

### Example 2: Persistent banner

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_message(
    "myplugin-banner",
    "Frame Shift Drive charging",
    "#ffd27f",
    100,
    20,
    ttl=0,       # persistent until cleared
    size="large",
)
```

### Example 3: Clear an existing message

```python
from EDMCOverlay import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_message(
    "myplugin-banner",
    "",
    "#ffffff",
    0,
    0,
)
```

Clears are resolved by `id`; position and color are ignored when `text` is empty.

## Runtime behavior

- Messages with the same `id` replace the existing entry and refresh the TTL.
- Empty `text` removes the message immediately.
- Size presets are derived from the overlay font settings; adjust the "Font Step" and base font size in preferences to tune small/large/huge.
- Plugin ownership is inferred from `id` prefixes (case-insensitive). If your plugin does not populate a `plugin` field, add prefixes via `define_plugin_group` so the overlay can attribute payloads correctly.

## Debugging

- `overlay-payloads.log` mirrors incoming legacy payloads when payload logging is enabled.
- Run `python3 utils/payload_inspector.py` to tail that log and inspect resolved plugin/group labels and live IDs.

