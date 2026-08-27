# Task: Add Circle Transform and Render Dispatch

## Description
Wire stored `circle` items into `RenderSurfaceMixin` by deriving the logical square from centre/radius, passing that square through the established rectangle/group/viewport transform flow, and constructing `_CirclePaintCommand` instances. The result must participate in existing group bounds, anchors, cycle targeting, fill mapping, and tracing without changing rectangle or vector contracts.

## Background
Task 01 supplies the direct Qt paint command but deliberately does not know about legacy logical coordinates or group transforms. `RenderSurfaceMixin._build_rect_command` already centralizes the exact group context, transform metadata, fill mapping, anchor selection, bounds reporting, and cycle-anchor rules needed for legacy shapes. A circle must derive `left = x - radius`, `top = y - radius`, `width = height = 2 * radius` and reuse that machinery, yielding a mapped ellipse when a viewport mapping is non-uniform by design. The render loop currently dispatches message, rect, and vector kinds only.

## Reference Documentation
**Required:**
- Design: docs/plans/2026-08-26-circle-shape-pyqt-rendering/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/research/payload-and-rendering.md (derived-square transform decision and regression risks)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/plan.md (Step 3 Stage 3.2, demo, and validation commands)
- overlay_client/render_surface.py (`_build_rect_command`, `_compute_rect_transform`, and `_build_legacy_commands_for_pass`)
- overlay_client/tests/test_render_surface_mixin.py (surface, grouping, anchoring, and command assertions)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step03/task-01-add-opacity-aware-circle-paint-command.code-task.md (required command API)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. **Test type selected before edits: unit.** This task uses deterministic render-surface fixtures, a mapper, and command doubles; it does not change `load.py`, EDMC hooks, TCP ingestion, or lifecycle state. No harness test is required; Step 4 owns runtime-wiring coverage.
2. Import and use `_CirclePaintCommand` in `overlay_client/render_surface.py`. Add a dedicated circle builder and a `legacy_item.kind == "circle"` dispatch branch without changing message, rectangle, vector, or unknown-kind branches.
3. Derive the logical bounding square from stored centre/radius: `left = x - radius`, `top = y - radius`, `width = height = 2 * radius`. Route it through the same group context and `_compute_rect_transform` path used by rectangles; do not fork Fill, placement, anchoring, justification, viewport, transform-metadata, or overlay-hint math.
4. Build the circle pen from the stored requested `thickness`, with the existing no-pen behavior for missing, `none`, or invalid border colour. Build fill with the existing transparent/no-brush behavior for empty, `none`, or invalid fill. Do not alter rectangle's `legacy_rect` line-width policy or global render hints.
5. Report transformed square bounds, overlay bounds, base/reference overlay bounds, debug vertices, effective anchor, and mapped-square centre as the circle command's `bounds`, `cycle_anchor`, and group/cycle metadata. Match rectangle rounding and scale behavior.
6. Add unit/integration coverage in `overlay_client/tests/test_render_surface_mixin.py` for dispatch to `_CirclePaintCommand`, expected mapped bounding square, requested pen width, filled/transparent handling, group bounds, anchored/offset placement, and cycle anchor. Keep task-owned changes out of `overlay_client/paint_commands.py` and `overlay_client/tests/test_paint_commands.py`.
7. Include regression assertions or execute existing tests proving rectangle and vector command generation is unchanged. Do not add an alternate circle geometry transform to preserve visual circularity under non-uniform scaling; the transformed bounds are the intended behavior.
8. Run the required GUI-enabled Step 3 commands exactly:
   - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_paint_commands.py overlay_client/tests/test_render_surface_mixin.py -q`
   - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest -k 'paint_commands or render_surface' -q`
   Attempt the documented local dev-overlay demo only when the existing environment can run it safely; capture a local screenshot only if it contains no credentials, personal data, or sensitive overlay content. If the demo cannot run, record the concrete prerequisite/reason and do not fabricate a screenshot.

## Dependencies
- Task 01 provides `_CirclePaintCommand`; do not revise its paint behavior in this task.
- Step 2 provides validated first-class circle legacy items.
- `overlay_client/render_surface.py` owns rectangle-transform reuse, group metadata, and dispatch.
- `overlay_client/tests/test_render_surface_mixin.py` supplies the PyQt-enabled mapper and render-surface test conventions.

## Implementation Approach
1. Inspect rectangle builder/dispatch and existing render-surface group/anchor tests. Add failing tests that construct a stored circle and assert the derived logical square's mapped command bounds, style, group bounds, anchor translation, and cycle centre.
2. Extract only a small private common helper if it can preserve the existing rectangle transform code byte-for-byte in behavior; otherwise lift the rectangle builder flow into a dedicated circle builder. Keep all rectangle/vector paths untouched.
3. Add the single circle dispatch branch and verify first/second-pass group collection, transformed bounds, and cycle anchor use the mapped square centre.
4. Run the focused GUI tests followed by the exact Step 3 plan commands. Attempt the safe local screenshot condition and record either its local path plus sensitive-content scan result or why the documented demo is unavailable in `docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step03-task02/progress.md`; do not update the approved plan or execution dashboard from this task context.

## Acceptance Criteria

1. **Stored circle dispatches to a circle paint command**
   - Given a valid `LegacyItem(kind="circle")` in the payload store
   - When the render surface builds legacy commands
   - Then it produces `_CirclePaintCommand` rather than dropping the item, and existing message/rectangle/vector dispatch remains unchanged.

2. **Centre/radius becomes the transformed square bounding rectangle**
   - Given a circle centred at `(x, y)` with radius `r` and a deterministic mapper
   - When the command is built
   - Then it uses the transformed result of `(x - r, y - r, 2r, 2r)` as its ellipse bounds, preserving non-uniform mapped dimensions where the current viewport mapper produces them.

3. **Style and bounds reuse rectangle/group behavior**
   - Given circles with requested thickness, valid fill, transparent fill, transforms, group placement, and anchor configuration
   - When commands are collected for render passes
   - Then pen/no-pen and brush/no-brush behavior matches the documented contract, transformed square bounds contribute to group and overlay bounds, and anchor/offset placement matches the existing rectangle transform rules.

4. **Cycle targeting uses the mapped square centre**
   - Given a transformed circle command with group or payload offsets
   - When its cycle metadata is inspected or it paints
   - Then its cycle anchor is the mapped bounding square centre and receives the same final offsets as the rendered ellipse.

5. **Rectangle and vector regressions remain intact**
   - Given the existing rectangle and vector render-surface tests
   - When the Step 3 GUI test selections run
   - Then they pass without altered rectangle/vector output or changed global render hints.

6. **GUI validation and safe-demo evidence**
   - Given a GUI-capable environment
   - When the exact required commands below and the documented demo attempt are run
   - Then both commands pass, and either a locally captured, credential-scanned screenshot is recorded or a specific environment limitation is recorded without claiming visual confirmation.

## Metadata
- **Complexity**: High
- **Labels**: circle-shape, pyqt6, render-surface, transforms, grouping, cycle-anchor, unit-tests, step-3
- **Required Skills**: Python rendering pipelines, PyQt6 QPainter integration, coordinate transforms, deterministic integration-style unit tests, pytest
