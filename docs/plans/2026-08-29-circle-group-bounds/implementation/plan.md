# Implementation plan: circle group bounds

## Checklist

- [ ] Step 1: Prove normal circle bounds.
- [ ] Step 2: Implement transformed circle bounds and preserve all shapes.
- [ ] Step 3: Validate the integrated Fill-mode grouping behavior.

## Steps

### Step 1: Prove normal circle bounds

**Objective:** Add a deterministic unit test that defines the circle-to-bounds
contract before changing production code.

**Implementation guidance:** In `overlay_client/tests/test_payload_bounds.py`,
construct a `LegacyItem(kind="circle")` with centre coordinates and radius,
then call `accumulate_group_bounds()` using stable injected dependencies.
Assert that the bounds equal the circle’s enclosing square, not its centre
point.

**Test requirements:** The new test must fail against the current generic
fallback and use no PyQt event loop or EDMC harness lifecycle.

**Integration:** Establishes the shared geometry contract consumed by
`FillGroupingHelper.prepare()`.

**Demo:** The test demonstrates that a circle at `(100, 200)` with radius `25`
contributes `(75, 175)` through `(125, 225)` to its group.

### Step 2: Implement transformed circle bounds and preserve all shapes

**Objective:** Add the circle branch to `accumulate_group_bounds()` and prove
that transform metadata is applied consistently with rectangles.

**Implementation guidance:** Derive four logical corners from centre/radius,
transform each through the existing local transform function, and update the
enclosing rectangle. Keep the rectangle/vector/message branches unchanged.

**Test requirements:** Add a transformed-circle test whose expected bounds
would differ if only the centre were transformed. Run
`overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_payload_bounds.py`.

**Integration:** The existing Fill grouping helper will consume the corrected
bounds without new API or renderer wiring.

**Demo:** A transformed circle yields a stable, radius-aware group transform
while its rendered footprint remains unchanged.

### Step 3: Validate the integrated Fill-mode grouping behavior

**Objective:** Validate the regression fix across the grouping and rendering
surfaces without changing public payload behavior.

**Implementation guidance:** Review the changed helper for equivalence with
the renderer’s `x-radius`, `y-radius`, and diameter model. Do not alter
BioScan, `send_shape`, or circle paint commands.

**Test requirements:** Run the focused bounds module, the relevant group
transform/render-surface tests, and `make check`.

**Integration:** Confirms that existing Fill-mode `GroupTransform` construction
receives complete circle geometry and that all repository checks remain green.

**Demo:** Repeated BioScan circle refreshes no longer reposition its group.
