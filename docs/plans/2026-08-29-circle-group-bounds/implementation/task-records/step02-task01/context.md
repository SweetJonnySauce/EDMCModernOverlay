# Step 2 / Task 1 context

## Scope

Add the minimal circle-specific `accumulate_group_bounds()` branch and one
transformed-circle unit test. No renderer, API, grouping-helper, or unrelated
worktree changes are in scope.

## Contract and dependency map

`LegacyItem(kind="circle")` flows through
`payload_transform.accumulate_group_bounds()` to `GroupBounds`, which
`FillGroupingHelper.prepare()` consumes. The renderer defines a circle as the
square enclosing its centre and radius. Bounds must transform all four square
corners through the existing local helper before aggregation.

## Test choice

This is deterministic, pure geometry under the existing PyQt-dependent test
module. It requires a unit test, not a lifecycle harness.
