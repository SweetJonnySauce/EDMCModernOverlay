# Step 03 Task 01 Context

## Mode and scope

`code-assist` is running in auto mode for Step 3 Task 01 only. It adds the direct Qt `_CirclePaintCommand` and focused GUI-backed unit coverage. Transform construction, render-surface dispatch, lifecycle wiring, the approved plan, and the execution dashboard remain out of scope.

## Restart reconciliation

- Read the governing artifacts in orchestration order, the dashboard, Step 3 task artifacts, prior task records, and available validation/log locations.
- Step 2 is complete; the dashboard identifies this paint-command task as the first incomplete Step 3 implementation action. Stale dashboard entries were observed but are task-external and left unchanged.
- `git status --short` contains earlier Step 1/2 source/test changes and untracked plan artifacts. This task preserves them. `git diff --check` passed before task edits.
- No Step 3 Task 01 record or validation log existed. Instruction discovery found `README.md` and test READMEs but no `CODEASSIST.md`.

## Test selection

Test type selected before edits: **unit**. The command accepts precomputed bounds and is proven through recording painter/window doubles. It does not touch `load.py`, EDMC hooks, sockets, or runtime lifecycle; no harness test belongs to this task.

## Requirements and implementation paths

| Area | Path | Contract |
| --- | --- | --- |
| Direct paint command | `overlay_client/paint_commands.py` | Add a `_RectPaintCommand` sibling that only invokes bounding-rectangle `drawEllipse`, preserves opacity-copy behavior, traces `circle`, and registers an offset anchor. |
| Focused GUI units | `overlay_client/tests/test_paint_commands.py` | Assert exact ellipse arguments, style/no-brush handling, safe opacity copies, trace, and anchor contracts. |
| Deferred integration | `overlay_client/render_surface.py` | Task 02 constructs and dispatches the command; this task must not edit it. |

## Dependency map

Validated stored circle -> Task 02 mapped bounds/style builder -> `_CirclePaintCommand.paint` -> recording painter / `QPainter.drawEllipse`. The command itself has no geometry-validation or transform responsibility.

## Existing behavior to preserve

- Rectangle command opacity, offset, trace, and cycle-anchor behavior.
- Vector centre/radius ellipse marker behavior.
- Original `QPen`/`QBrush` identity and alpha when global payload opacity requires temporary active copies.

## Uncertainties

None material. The rectangle command provides a direct behavior-preserving sibling pattern.
