# Step 1 / Task 1 plan

- [x] Inspect the approved design, bounds helper, and existing unit-test style.
- [x] Add one untransformed circle-bounds regression test.
- [x] Run the focused PyQt-enabled module and capture the expected red result.
- [x] Record the red-baseline cause and hand off Step 2.

## Test scenario

Given `LegacyItem(kind="circle")` with `x=100`, `y=200`, and `radius=25`,
after `accumulate_group_bounds()` the bounds must have minimum `(75, 175)` and
maximum `(125, 225)`. The current generic fallback is expected to produce the
centre `(100, 200)` instead.
