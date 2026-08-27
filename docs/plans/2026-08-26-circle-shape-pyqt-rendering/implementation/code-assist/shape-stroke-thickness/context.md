# Shape Stroke Thickness: Context

## Scope

Extend explicit, logical stroke thickness from the existing `circle` shape to
`rect`, without changing rectangles that omit the field. Keep the implementation
internal and small enough for future stroked shapes to opt in.

## Existing Documentation

- `AGENTS.md` requires a behavior-scoped plan, unit and harness coverage for
  mixed transport/rendering work, staged progress tracking, and recorded test
  evidence.
- `shape-stroke-thickness-prompt.md` defines the approved compatibility and
  rendering contracts.
- The prior circle design and implementation plan establish the legacy-canvas
  coordinate model and the client processor as the authority for validation.

## Integration Map

```text
Overlay.send_shape (EDMCOverlay/edmcoverlay.py)
  -> raw legacy payload normalizer (same module)
  -> process_legacy_payload (overlay_client/legacy_processor.py)
  -> LegacyItem.data
  -> RenderSurfaceMixin bounded-shape builder (overlay_client/render_surface.py)
  -> rectangle/circle paint commands (overlay_client/paint_commands.py)
  -> QPainter
```

## Existing Patterns and Invariants

- `rect` currently creates its pen with `_line_width("legacy_rect")`; that is
  the unchanged path for omitted thickness.
- `circle` currently validates a required positive integer thickness in
  `legacy_processor` but sets its pen width before the shared transform. This
  causes the documented logical-unit meaning not to scale with the shape.
- `RenderSurfaceMixin._build_bounded_shape_command` already receives the group
  scale that transforms logical bounds to physical pixels, making it the correct
  common width-resolution boundary.
- `process_legacy_payload` returns before `store.set` on invalid circle geometry;
  rectangle must have the same no-mutation property only when an explicit
  thickness is supplied and invalid.
- Existing tests use pure processor and render-surface tests plus the fake EDMC
  harness for raw/TCP publication. No live socket or EDMC runtime is needed.

## Design Decision

Use a compact stroke specification at the bounded-shape boundary. It represents
either an explicit logical width to scale, an existing physical/default width to
preserve, or no pen. Shape-specific builders declare the spec; the shared
builder resolves it using `group_ctx.scale` and copies the pen before changing
its width. This is an internal opt-in seam, not a generic public registry.

## Test-Type Decision

| Behavior | Test type | Reason |
| --- | --- | --- |
| Helper payload compatibility and raw normalization | Unit | Deterministic data transformation. |
| Central validation and no-store-mutation behavior | Unit | Processor dependencies are injected. |
| Scaled width, opacity, and pen isolation | GUI-enabled unit | Requires Qt paint objects but not lifecycle wiring. |
| Raw/TCP publication of rectangle thickness | Harness | Exercises the fake EDMC transport/hook boundary. |

## Risks

- Scaling the omitted rectangle default would silently change established visuals;
  keep that code path separate.
- Mutating a cached pen could leak widths across payloads; always work on a copy
  during final command construction.
- Any change to raw normalization must preserve unrelated shape payloads.
