# Step 03 Task 01 Plan

## Test strategy

Test type selected before edits: **unit**. The recording painter makes the Qt draw operation deterministic without render-surface or lifecycle setup.

| Scenario | Input | Expected output |
| --- | --- | --- |
| Offset ellipse bounds | `(x, y, width, height)` plus offsets | Exactly one `drawEllipse(x + offset_x, y + offset_y, width, height)`; no `drawRect`. |
| Requested stroke and fill | Coloured width-`n` `QPen`, coloured `QBrush` | Painter receives the requested width, colour, and fill. |
| Transparent fill | `QBrush(NoBrush)` | Painter retains `NoBrush`. |
| Global opacity | Non-empty pen/brush, 50% payload opacity | Painter receives alpha-adjusted copies; originals retain their original alpha. |
| Empty style preservation | `NoPen` and `NoBrush`, reduced opacity | Painter receives those empty styles unchanged. |
| Cycle and trace | Cycle anchor, offsets, trace callback | Window stores offset anchor; callback receives `trace:complete`, `kind="circle"`. |

## Implementation checklist

- [x] Reconcile restart state and select unit testing.
- [x] Inspect design, rectangle command, recording-painter tests, and Task 02 boundary.
- [x] RED: add circle command tests and run the focused GUI command to demonstrate the missing symbol/behavior.
- [x] GREEN: add the minimal rectangle-sibling circle command.
- [x] REFACTOR: review focused changes for local conventions and rectangle/vector isolation.
- [x] Run the three mandated Step 3 GUI commands in order.
- [x] Record exact evidence, validation logs, and deferred commit.

## Implementation approach

Lift the rectangle command's opacity-copy, painter setup, offset rounding, trace, and cycle-anchor flow intact. Change only the primitive to the four-integer bounding-rectangle `drawEllipse` overload and the completion trace kind. Keep command creation and renderer dispatch for Task 02.

## Risks and mitigations

- Mutating the stored pen/brush at reduced opacity would cause later paints to compound alpha. Tests assert command-original alpha remains unchanged.
- Accidentally using vector marker overload or a rectangle would bypass the transform contract. Tests assert the exact four-integer ellipse call and absence of a rectangle call.
- GUI dependency unavailability could prevent validation. Required commands will be run exactly and their direct output recorded without a substitute.
