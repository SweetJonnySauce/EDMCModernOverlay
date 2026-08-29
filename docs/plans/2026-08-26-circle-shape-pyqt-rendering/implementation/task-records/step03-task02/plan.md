# Step 3 Task 02 Plan

## Phase status

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 3 | 3.2.1 | Write deterministic render-surface circle tests (RED) | Completed |
| 3 | 3.2.2 | Add circle transform builder and dispatch (GREEN) | Completed |
| 3 | 3.2.3 | Review/refactor and run required GUI validations | Completed |
| 3 | 3.2.4 | Attempt documented safe local demo | Completed (blocked safely) |

## Test strategy

1. A stored circle dispatches to `_CirclePaintCommand` and uses the mapped result of its derived square, including intentionally non-uniform dimensions.
2. Requested thickness produces that pen width; invalid/missing/`none` border gives `NoPen`; valid fill gives a brush and empty/`none`/invalid fill gives `NoBrush`.
3. The transformed square supplies command/group/overlay bounds, mapped-square-centre cycle anchor, and the existing group anchor/offset placement.
4. Existing rectangle and vector tests in the required selections remain green.

## Implementation approach

Lift the rectangle builder flow into a small shared private shape helper only if the rectangle result remains behaviorally identical; otherwise retain it and add a sibling circle builder. The circle builder derives its logical square before entering that shared transform flow. Add only the `circle` dispatch branch.

Validation order: focused RED test, focused GREEN test, exact GUI-enabled Step 3 commands, then a safe documented demo attempt. No commit, network activity, screenshot fabrication, plan update, or dashboard update is authorized.

## Refactor review

The shared bounded-shape helper now owns the pre-existing rectangle transform, bounds, anchor, debug-vertex, and trace-metadata path. Rectangle-specific style construction and `legacy_rect` line width remain unchanged; the circle supplies its derived square plus requested thickness. This avoids a parallel Fill/group/viewport implementation.

## EDMC compliance review for this task

| Check | Yes/No | Result |
| --- | --- | --- |
| Runtime/plugin API, config, logging, or versioning changed | No | Render-only client code changed; no EDMC hook or plugin API change was introduced. |
| Long-running work or Tk manipulation added | No | This deterministic PyQt command construction adds neither threads nor Tk access. |
| Supported dependencies/imports preserved | Yes | Uses existing PyQt6 and internal overlay-client imports only. |
| `load.py` harness coverage required | No | `load.py` and lifecycle wiring are untouched; deterministic unit tests are the selected test type. |
