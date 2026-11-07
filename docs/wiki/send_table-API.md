# send_table API

`Overlay.send_table()` renders a table using the overlay's actual proportional font metrics.

Unlike padding text with spaces, column alignment is based on measured pixel widths, so columns remain aligned when the configured font is proportional.

```python
overlay.send_table(
    "ArchTrack_table",
    [
        ["Material", "Required", "Provided", "Needed"],
        ["Ceramic Composites", 500, 125, 375],
        ["Titanium", 250, 200, 50],
    ],
    x=100,
    y=200,
    ttl=60,
    size="large",
    columns=[
        {"align": "left"},
        {"align": "right"},
        {"align": "right"},
        {"align": "right"},
    ],
    row_colors=["yellow", "white"],
)
```

Arguments:

- `tableid`: unique payload ID.
- `rows`: sequence of rows. Cell values are converted to strings.
- `x`, `y`: table origin in the legacy overlay coordinate system.
- `ttl`: payload lifetime in seconds.
- `size`: existing overlay text size preset.
- `columns`: optional column definitions. Each definition may contain `width` (overlay units) and `align` (`left`, `center`, or `right`). Omit `width` for automatic measured sizing.
- `padding`: cell padding in overlay units.
- `header`: whether the first row is treated as the header.
- `header_bold`: render the header using a bold font.
- `header_color`: header text color.
- `header_background`: optional header background color.
- `row_colors`: text colors for data rows, excluding the header.
- `row_backgrounds`: optional background colors for data rows, excluding the header.
- `background`: optional background color for the complete table.

Automatic column widths are calculated from the actual `QFontMetrics` used by the renderer. Explicit column widths override automatic measurement.
