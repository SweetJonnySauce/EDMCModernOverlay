# Step 2 / Task 1 plan

- [x] Inspect approved design, renderer geometry, rectangle convention, and Step 1 red baseline.
- [x] Add transformed-circle contract test and record its red result.
- [x] Add the narrow circle bounds branch using transformed extent corners.
- [x] Run the focused PyQt-enabled bounds module green and `git diff --check`.

## Test scenarios

- Untransformed centre `(100, 200)`, radius `25` spans `(75, 175)` to `(125, 225)`.
- With scale `(2, 0.5)` and offset `(10, -20)`, the same circle spans `(160,
  67.5)` to `(260, 92.5)` after transforming all extent corners.
