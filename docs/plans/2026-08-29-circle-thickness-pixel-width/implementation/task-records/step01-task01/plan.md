# Step 1 test plan

- Rectangle `thickness=2`: at scales 0.5, 1.0, and 2.0, assert pen widths 1,
  2, and 4 with `MiterJoin`.
- Circle `thickness=1`: at scales 0.5, 1.0, and 2.0, assert pen width 1 with
  `BevelJoin`.
- Circle `thickness=3` at scale 2.0: assert pen width 3, proving the contract
  is unscaled for non-unit values as well.

The focused thickness test is expected to fail for the circle cases until the
separate Step 2 renderer change supplies the explicit pixel-width policy.
