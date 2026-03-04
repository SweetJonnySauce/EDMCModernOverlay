`define_plugin_group` is EDMCModernOverlay's public helper for registering plugin grouping defaults. Call it from your plugin startup path to define ownership prefixes and group behavior (anchoring, offsets, justification, marker labels, controller box mode, and optional backgrounds).

This document focuses on the API contract and usage patterns.

## API signature

```python
from overlay_plugin.overlay_api import define_plugin_group, PluginGroupingError

updated = define_plugin_group(
    plugin_name="MyPlugin",
    plugin_matching_prefixes=["myplugin-"],
    plugin_group_name="alerts",
    plugin_group_prefixes=["myplugin-alert-"],
    plugin_group_anchor="ne",
    plugin_group_offset_x=0,
    plugin_group_offset_y=0,
    payload_justification="left",
    marker_label_position="below",
    controller_preview_box_mode="last",
    plugin_group_background_color="#1A1A1ACC",
    plugin_group_border_color="#000000",
    plugin_group_border_width=2,
)
```

## Return value and exceptions

- Returns `True` when `overlay_groupings.json` changed.
- Returns `False` when input was valid but no persisted change was needed.
- Raises `PluginGroupingError` when validation fails or when Modern Overlay is unavailable.

## Argument reference

| Argument | Type | Required | Notes | Legacy alias |
|---|---|---|---|---|
| `plugin_name` | `str` | Yes | Plugin bucket name (for example `BGS-Tally`). | `plugin_group` |
| `plugin_matching_prefixes` | `Sequence[str]` | No | Top-level plugin ownership prefixes. Lowercased and deduplicated. | `matching_prefixes` |
| `plugin_group_name` | `str` | No* | Group label used in controller UI. Required when passing any group-scoped settings. | `id_prefix_group` |
| `plugin_group_prefixes` | `Sequence[str | {"value": str, "matchMode": "startswith"|"exact"}]` | No | Prefix match rules for the group. Lowercased, deduplicated, and unique within the plugin. | `id_prefixes` |
| `plugin_group_anchor` | `str` | No | One of: `nw`, `ne`, `sw`, `se`, `center`, `top`, `bottom`, `left`, `right`. | `id_prefix_group_anchor` |
| `plugin_group_offset_x` | `int \| float` | No | Horizontal group offset in legacy 1280x960 canvas units. | `id_prefix_offset_x` |
| `plugin_group_offset_y` | `int \| float` | No | Vertical group offset in legacy 1280x960 canvas units. | `id_prefix_offset_y` |
| `payload_justification` | `str` | No | One of: `left`, `center`, `right`. | N/A |
| `marker_label_position` | `str` | No | One of: `below`, `above`, `centered`. | N/A |
| `controller_preview_box_mode` | `str` | No | One of: `last`, `max`. | N/A |
| `plugin_group_background_color` | `str` | No | Named color or hex `#RRGGBB` / `#AARRGGBB`. | `background_color` |
| `plugin_group_border_color` | `str` | No | Named color or hex `#RRGGBB` / `#AARRGGBB`. | `background_border_color` |
| `plugin_group_border_width` | `int \| float` | No | Border width in pixels, normalized to integer `0..10`. | `background_border_width` |

`*` You may call with only `plugin_matching_prefixes` and no group settings.

## Legacy alias compatibility

Legacy argument names are still accepted for compatibility.

- Canonical + legacy with matching values: accepted.
- Canonical + legacy with conflicting values: `PluginGroupingError`.
- Legacy alias warning policy: once per process, per legacy argument, per calling plugin.
- Warning messages include the plugin name when available.

## Examples

### Example 1: Register top-level plugin ownership prefixes

```python
from overlay_plugin.overlay_api import define_plugin_group, PluginGroupingError

try:
    define_plugin_group(
        plugin_name="MyPlugin",
        plugin_matching_prefixes=["myplugin-"],
    )
except PluginGroupingError as exc:
    print(f"Could not register grouping: {exc}")
```

### Example 2: Register a group with exact matching and anchor settings

```python
from overlay_plugin.overlay_api import define_plugin_group, PluginGroupingError

try:
    define_plugin_group(
        plugin_name="BGS-Tally",
        plugin_group_name="Tick",
        plugin_group_prefixes=[
            {"value": "bgstally-frame-tick", "matchMode": "exact"},
            "bgstally-msg-tick-",
        ],
        plugin_group_anchor="top",
        plugin_group_offset_x=0,
        plugin_group_offset_y=10,
        payload_justification="center",
        controller_preview_box_mode="max",
    )
except PluginGroupingError as exc:
    print(f"Could not register grouping: {exc}")
```

### Example 3: Legacy aliases still work

```python
from overlay_plugin.overlay_api import define_plugin_group

define_plugin_group(
    plugin_group="LegacyPlugin",
    matching_prefixes=["legacy-"],
    id_prefix_group="status",
    id_prefixes=["legacy-status-"],
)
```

## Runtime behavior

- `plugin_matching_prefixes` and `plugin_group_prefixes` (legacy `id_prefixes`) are lowercased and deduplicated.
- `plugin_group_prefixes` are unique within a plugin; assigning a prefix to one `plugin_group_name` removes it from other groups in that same plugin.
- When `plugin_group_prefixes` are supplied, missing top-level ownership prefixes are appended automatically to `plugin_matching_prefixes` (add-only behavior).
- Data is persisted to `overlay_groupings.json` and picked up by the runtime reload path.

## Debugging

- Check `EDMarketConnector-debug.log` for `PluginGroupingError` validation failures.
- Check `EDMarketConnector-debug.log` for legacy alias compatibility warnings (with plugin name).
- Use `python3 utils/payload_inspector.py` to confirm payload IDs resolve to expected plugin/group labels.

## Related docs

- [[Getting-Started]]
- [[Developer-FAQs]]
- [[send_message-API]], [[send_shape-API]], [[send_raw-API]]

## Canonical API vs persisted schema

The API now uses canonical argument names, but the persisted grouping structure has **not** changed. `define_plugin_group` still writes the same keys/shape used by `overlay_groupings.json`. Here's how the API names map to the schema names: 

| Canonical API argument | Persisted key/path in `overlay_groupings.json` |
|---|---|
| `plugin_name` | top-level key: `<plugin_name>` |
| `plugin_matching_prefixes` | `<plugin_name>.matchingPrefixes` |
| `plugin_group_name` | `<plugin_name>.idPrefixGroups.<plugin_group_name>` |
| `plugin_group_prefixes` | `<plugin_name>.idPrefixGroups.<plugin_group_name>.idPrefixes` |
| `plugin_group_anchor` | `<plugin_name>.idPrefixGroups.<plugin_group_name>.idPrefixGroupAnchor` |
| `plugin_group_offset_x` | `<plugin_name>.idPrefixGroups.<plugin_group_name>.offsetX` |
| `plugin_group_offset_y` | `<plugin_name>.idPrefixGroups.<plugin_group_name>.offsetY` |
| `payload_justification` | `<plugin_name>.idPrefixGroups.<plugin_group_name>.payloadJustification` |
| `marker_label_position` | `<plugin_name>.idPrefixGroups.<plugin_group_name>.markerLabelPosition` |
| `controller_preview_box_mode` | `<plugin_name>.idPrefixGroups.<plugin_group_name>.controllerPreviewBoxMode` |
| `plugin_group_background_color` | `<plugin_name>.idPrefixGroups.<plugin_group_name>.backgroundColor` |
| `plugin_group_border_color` | `<plugin_name>.idPrefixGroups.<plugin_group_name>.backgroundBorderColor` |
| `plugin_group_border_width` | `<plugin_name>.idPrefixGroups.<plugin_group_name>.backgroundBorderWidth` |
