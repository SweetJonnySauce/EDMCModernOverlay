# Task: Add an Opacity-Aware Circle Paint Command

## Description
Add a dedicated `_CirclePaintCommand` beside `_RectPaintCommand`. It must paint an already-transformed bounding rectangle exclusively with `QPainter.drawEllipse`, apply the established payload-opacity copy behavior to its pen and brush, and retain the command-level cycle-anchor and trace contracts. This task intentionally does not build transforms or add render-surface dispatch.

## Background
Step 2 stores validated `LegacyItem(kind="circle")` values with centre/radius geometry, border colour, fill, and requested stroke thickness. Existing rectangle commands own the renderer's command-level Qt behavior: they apply offsets at paint time, copy non-empty `QPen`/`QBrush` values before changing their alpha for global payload opacity, register cycle anchors, and emit a completion trace. Circles need that same isolated paint behavior but must use the bounding-rectangle `QPainter.drawEllipse(x, y, width, height)` overload. A later task will derive and transform those bounds in `RenderSurfaceMixin`.

## Reference Documentation
**Required:**
- Design: docs/plans/2026-08-26-circle-shape-pyqt-rendering/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/research/payload-and-rendering.md (Qt ellipse overload and opacity contract)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/plan.md (Step 3 Stage 3.1 and required GUI validation)
- overlay_client/paint_commands.py (`_RectPaintCommand` as the behavior-preserving sibling)
- overlay_client/tests/test_paint_commands.py (recording-painter test pattern)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. **Test type selected before edits: unit.** The command accepts already-computed values and uses the recording painter/window doubles; it does not touch `load.py`, EDMC lifecycle hooks, sockets, or runtime ingestion. No harness test is required.
2. Add `_CirclePaintCommand` to `overlay_client/paint_commands.py` as a sibling of `_RectPaintCommand`, retaining the established command metadata fields and accepting `pen`, `brush`, `x`, `y`, `width`, `height`, optional `cycle_anchor`, and optional `trace_fn`.
3. In `paint`, apply `offset_x`/`offset_y` only to the draw origin and cycle anchor, set the active pen and brush, and call only `painter.drawEllipse(draw_x, draw_y, width, height)` for this primitive. Do not use the vector marker's centre/radius overload.
4. Mirror rectangle opacity semantics exactly: when global payload opacity is below 100, copy a non-`NoPen` pen and a non-`NoBrush` brush before alpha adjustment; do not mutate the command's original pen or brush. Preserve `NoPen` and `NoBrush` unchanged.
5. Preserve the existing trace and cycle contracts: emit `trace:complete` with `kind: "circle"` when tracing is enabled and register the offset cycle anchor for the item ID.
6. Extend the existing recording painter and imports in `overlay_client/tests/test_paint_commands.py` only as needed for precise circle command assertions. Do not modify render-surface builders, render dispatch, rectangle behavior, vector behavior, or global painter render hints.
7. Add direct unit coverage for transformed offsets and exact `drawEllipse` arguments, requested pen width/stroke colour, filled versus transparent (`none`/`NoBrush`) behavior, opacity-adjusted pen and brush alpha without original-object mutation, cycle-anchor registration, and `kind: "circle"` completion tracing.
8. Run the focused GUI-enabled test command and then the required Step 3 GUI regression commands:
   - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_paint_commands.py -q`
   - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_paint_commands.py overlay_client/tests/test_render_surface_mixin.py -q`
   - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest -k 'paint_commands or render_surface' -q`
   If GUI prerequisites are unavailable, capture the exact skip/failure evidence rather than silently substituting a headless result.

## Dependencies
- Step 2's stored circle items provide validated geometry and visual fields; this task does not reinterpret or validate them.
- `overlay_client/paint_commands.py` owns direct Qt paint-command behavior.
- Task 02 will import this command and supply transformed bounds, group metadata, and render dispatch.
- The existing PyQt6 test environment and recording-painter doubles must remain compatible with rectangle/vector tests.

## Implementation Approach
1. Inspect `_RectPaintCommand.paint` and its recording-painter tests. Add failing direct tests for the circle ellipse call, pen/brush setup, transparent brush, opacity-copy behavior, trace callback, and cycle anchor.
2. Lift the rectangle command's safe pen/brush/opacity, offset, trace, and cycle-anchor flow intact into `_CirclePaintCommand`, changing only the draw primitive and trace kind.
3. Run the focused GUI test and the two Step 3 plan commands in order. Record exact commands and outcomes in `docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step03-task01/progress.md`; do not update the approved plan or execution dashboard from this task context.

## Acceptance Criteria

1. **Ellipse command paints mapped bounds with offsets**
   - Given a circle command with precomputed `(x, y, width, height)` and non-zero paint offsets
   - When `paint` is called with the recording painter
   - Then the painter receives exactly `drawEllipse(x + offset_x, y + offset_y, width, height)` and no rectangle draw is used for that circle.

2. **Circle styling follows the requested stroke and fill contract**
   - Given commands with a requested-width coloured pen, a valid fill brush, and a transparent/no-fill brush
   - When each command paints
   - Then the recording painter receives the requested pen width and colour, receives the fill brush when present, and retains `NoBrush` for transparent fill.

3. **Global opacity is safe and behavior-compatible**
   - Given a circle command with non-empty pen/brush and a window reporting payload opacity below 100 percent
   - When it paints
   - Then the painter receives alpha-adjusted copies of both colours and the command's original pen and brush remain unchanged; `NoPen` and `NoBrush` remain untouched.

4. **Cycle and trace behavior is retained**
   - Given a circle command with a cycle anchor and trace callback
   - When it paints with offsets
   - Then the window registers the offset anchor for the circle item and the callback receives `trace:complete` with `kind` equal to `circle`.

5. **Focused GUI unit evidence**
   - Given PyQt dependencies are enabled
   - When the focused task test and the Step 3 plan commands are run
   - Then they pass with existing rectangle and vector paint tests still green, or exact unavailable-environment evidence is recorded for the main-thread review.

## Metadata
- **Complexity**: Medium
- **Labels**: circle-shape, pyqt6, paint-command, opacity, unit-tests, step-3
- **Required Skills**: Python dataclasses, PyQt6 QPainter/QPen/QBrush, deterministic recording-painter testing, pytest
