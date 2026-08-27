# Step 3 Task 02 Context

## Existing documentation

- `AGENTS.md`: preserve behavior-scoped changes, choose unit tests for this deterministic render-surface work, and record exact validation evidence.
- Circle detailed design and implementation plan: derive `left=x-radius`, `top=y-radius`, and a `2*radius` square, then reuse legacy rectangle transforms. Non-uniform mapping may intentionally yield an ellipse.
- Task artifact: this task owns only render-surface transform reuse, circle dispatch, render-surface tests, and a safe demo attempt. It must not alter the paint command supplied by Task 01, the processor, approved plan, or dashboard.

## Requirements and dependency map

Test type: **unit**. The deterministic render-surface fixtures inject mapping/group behavior; no EDMC lifecycle, `load.py`, TCP, or runtime wiring changes are in scope.

`LegacyItem(kind="circle")` → `RenderSurfaceMixin._build_legacy_commands_for_pass` → circle builder → existing rectangle group/transform path → `_CirclePaintCommand` (Task 01) → `QPainter.drawEllipse`.

Touch points:

- `overlay_client/render_surface.py`: import the existing circle command, build circle command metadata/style from the derived square, and add one dispatch branch.
- `overlay_client/tests/test_render_surface_mixin.py`: failing-then-passing integration-style unit coverage for dispatch, bounds, pen/brush behavior, groups, offsets, and cycle anchoring.

Unchanged contracts: message, rectangle, vector, unknown-kind dispatch, rectangle line-width policy, paint-command implementation, render hints, and processor behavior.
