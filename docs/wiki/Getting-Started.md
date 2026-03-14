Short quickstart for EDMC plugin authors who want to draw overlays using EDMCModernOverlay

Overlays consist of text or simple graphical objects called payloads. Payloads are drawn on a canonical 1280 x 960 window. EDMCModernOverlay handles all the scaling for different monitor and window sizes.

# Send your first text payload
EDMCModernOverlay keeps the legacy `edmcoverlay` interface so existing plugins keep working. 

```python
import edmcoverlay

overlay = edmcoverlay.Overlay()
overlay.send_message(
    msgid="myplugin-hello",
    text="Hello, overlay!",
    color="white",
    x=20,
    y=20,
    ttl=5,
    size="normal",
)
```

| Parameter | Type | Description |
| --- | --- | --- |
| `msgid` | str | Unique payload ID (used to update/replace the same item). |
| `text` | str | Message text to render. |
| `color` | str | Text color name or hex string. |
| `x` | int | X position in the canonical 1280×960 window. |
| `y` | int | Y position in the canonical 1280×960 window. |
| `ttl` | int | Seconds before auto-clear; default is `4`. |
| `size` | str | Font preset name: `small`, `normal`, `large`, or `huge` (case-insensitive); default is `normal`. |


# Clear a message
Send a clear for the same `msgid` when the overlay should remove it.

```python
overlay.send_raw({"id": "myplugin-hello"})
```
Or send a empty text string or ttl=0 (expire now)
```python
overlay.send_message(
    msgid="myplugin-hello",
    text="",
    color="white",
    x=0,
    y=0,
    ttl=0,
    size="normal",
)
```
# Send a rectangle shape
```python
overlay.send_shape(
    shapeid="myplugin-box",
    shape="rect",
    color="white",
    fill="#4000ff00",  # or "none" for no fill
    x=100,
    y=100,
    w=200,
    h=80,
    ttl=5,
)
```
# Send a vector image
```python
overlay.send_raw({
    "id": "myplugin-arrow",
    "shape": "vect",
    "color": "#00ffff",
    "ttl": 5,
    "vector": [
        {"x": 100, "y": 100, "color": "#00ffff", "marker": "circle", "text": "Start"},
        {"x": 200, "y": 140, "color": "#00ffff"},
    ],
})
```
In send_raw for shape="vect", the top‑level color becomes the vector’s base_color. It’s used for all line segments and as the fallback for markers/text. Per‑point vector[i]["color"] only affects that point’s marker and label text. It does not change the line segment colors.
Colors are parsed by Qt (QColor): named colors or hex (#RRGGBB / #AARRGGBB). Invalid strings fall back to white.

# Add marker images to your payloads

Vector Markers (Circle + Cross)
Modern Overlay only renders two marker types on vector points: circle and cross (case-insensitive). Any other value is ignored (no marker drawn). Markers are set per-point on shape: "vect" payloads.
```python

overlay.send_raw(
    {
        "id": "marker-demo",
        "shape": "vect",
        "color": "#80d0ff",
        "ttl": 10,
        "vector": [
            {"x": 100, "y": 100, "marker": "circle", "color": "#80d0ff", "text": "Alpha"},
            {"x": 200, "y": 160, "marker": "cross", "color": "#ffcc00", "text": "Bravo"},
        ],
    }
)

```
X/Y is the center point of the marker. The "circle" marker produces a filled dot as seen on EDR Navroute and the "cross" marker produces an X as seen on Bioscan Radar. By default, all marker labels are to the right and below the marker. With EDMCModernOverlay, you can adjust the vertical placement of the label to be above or in-line with the marker by setting the `marker_label_position` property for the plugin group in `define_plugin_group` (described below)



# Define a Plugin Group
>⚠️ `define_plugin_group` is not compatible with other overlays (EDMCOverlay, edmcoverlay2, etc). If you implement this, make sure to wrap it in a try/catch block and handle the error.

See the [FAQ](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Developer-FAQs#what-is-a-plugin-group-and-why-do-i-want-to-define-it) and [API](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/define_plugin_group-API) wiki for more information.

```python

from overlay_plugin.overlay_api import define_plugin_group, PluginGroupingError

try:
    define_plugin_group(
        plugin_name="MyPlugin",
        plugin_matching_prefixes=["myplugin-"],
        plugin_group_name="alerts",
        plugin_group_prefixes=["myplugin-alert-"],
        plugin_group_anchor="ne",
        marker_label_position="below",
        controller_preview_box_mode="last",
        plugin_group_background_color="#1A1A1ACC",
        plugin_group_border_color="#FF0000",
        plugin_group_border_width=2,
    )
except PluginGroupingError as exc:
    # Modern Overlay is offline, a legacy overlay is being used, or the payload was invalid
    print(f"Could not register grouping: {exc}")
```
