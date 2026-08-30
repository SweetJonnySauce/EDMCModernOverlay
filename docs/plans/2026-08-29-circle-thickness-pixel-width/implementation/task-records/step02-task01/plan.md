# Step 2 plan

| Phase | Stage | Status |
| --- | --- | --- |
| 2 | 2.1 Add explicit pixel policy field and resolver branch | Completed |
| 2 | 2.2 Wire circles without changing rectangle construction | Completed |
| 2 | 2.3 Run focused/module validation and diff check | Completed |

The resolver uses the separate explicit pixel field before the pre-existing
logical field. It rounds and clamps the pixel value without applying group
scale; malformed direct/internal values leave the copied pen unchanged rather
than raising. Rectangles continue through their unchanged logical branch.
