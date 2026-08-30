# Optional Circle Thickness: Context

## Requirements

- `circle` accepts an omitted `thickness` through both `send_shape` and raw
  shape intake.
- An omitted circle thickness uses the same client-controlled default as an
  omitted rectangle: `legacy_rect`.
- Explicit circle and rectangle thickness remain positive, logical Qt-pixel
  widths that are not viewport/group scaled.
- The shape gallery contains a `thickness=1` and omitted-thickness example for
  each shape.
- Invalid explicit circle thickness remains rejected before a same-ID item is
  replaced.

## Dependency map

`EDMCOverlay.edmcoverlay.Overlay.send_shape` and raw payloads feed
`overlay_client.legacy_processor.process_legacy_payload`, which creates a
`LegacyItem`. `RenderSurfaceMixin._build_circle_command` and
`_build_rect_command` resolve stored or omitted widths into Qt pens.
`utils.shape_gallery` publishes representative payloads through the same
legacy-overlay CLI path.

## Existing patterns

- Rectangles already omit `thickness` from stored data and resolve it through
  `_line_width("legacy_rect")` at render time.
- Both shapes use `_StrokeWidthSpec`, so the circle can reuse that same
  fallback without changing geometry or explicit pixel-width behavior.
- Processor tests prove validation and non-mutation; render-surface tests use
  a pure Qt command seam; gallery tests examine generated payloads without a
  socket.
