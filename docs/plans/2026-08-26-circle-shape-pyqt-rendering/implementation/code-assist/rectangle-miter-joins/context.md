# Explicit Rectangle Miter Joins: Context

## Goal

Render rectangles that explicitly opt into `thickness` with square corners,
while leaving the established no-`thickness` rectangle rendering unchanged.

## Requirements and Acceptance Criteria

- A rectangle whose payload contains a positive `thickness` uses Qt's
  `MiterJoin` after its stroke width is resolved.
- An otherwise identical rectangle without `thickness` retains Qt's default
  `BevelJoin`, preserving the legacy rendering contract.
- Circle rendering and all payload/validation behavior remain unchanged.
- The join configuration is made on the per-command pen, never on shared pen
  state.

## Existing Patterns and Dependency Map

`LegacyItem.data` → `RenderSurfaceMixin._build_rect_command()` →
`_build_bounded_shape_command()` → `_RectPaintCommand.paint()` → Qt
`QPainter.drawRect()`.

- `render_surface.py` creates the rectangle pen and resolves an explicit
  legacy-canvas-unit thickness to physical pixels. That helper already copies
  a pen before changing explicit stroke width, providing the right ownership
  boundary for a join-style change.
- `paint_commands.py` only installs the command pen and draws the rectangle;
  it should not need shape-policy logic.
- `overlay_client/tests/test_render_surface_mixin.py` constructs rectangle
  commands directly and already asserts explicit scaling and omitted-thickness
  behavior.

## Documentation and Constraints

- The project is a Python/PyQt overlay; `README.md` confirms its EDMC plugin
  and overlay-client roles.
- No `CODEASSIST.md` or `CONTRIBUTING.md` exists. `AGENTS.md` requires small,
  behavior-scoped changes, a pre-code plan, and unit tests for pure renderer
  logic.
- Qt documents `BevelJoin` as the default and `MiterJoin` as the sharp-corner
  alternative. This is an internal rendering correction; no public API
  documentation changes are needed.

## Decision

Apply `MiterJoin` only when the rectangle has explicit thickness. Applying it
to every rectangle would silently change omitted-thickness legacy output,
which the existing shape-thickness contract expressly preserves.
