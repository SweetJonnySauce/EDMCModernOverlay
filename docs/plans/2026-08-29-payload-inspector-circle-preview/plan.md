# Payload inspector circle preview — plan

## Acceptance criteria

1. Selecting a circle payload draws an oval in the inspector preview.
2. The oval is centred at the payload `x`/`y`, and its radius is scaled from
   the legacy 1280×960 coordinate system.
3. Existing colour and transparent-fill handling is reused.
4. Vectors, rectangles, and messages retain their existing rendering behavior.

## Test strategy

| Scenario | Input | Expected result | Test type |
| --- | --- | --- | --- |
| Circle geometry | circle at `(100, 200)`, radius `50`, scale `0.25`, offset `(20, 30)` | canvas receives an oval from `(32.5, 67.5)` to `(57.5, 92.5)` with the normalised styles | Unit |
| Existing payload types | existing branches | unchanged; covered by existing behavior and scoped implementation | Regression through focused test/code review |

## Implementation stages

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add a focused unit test for circle canvas geometry and style | Completed |
| 1.2 | Add circle dispatch using `create_oval` | Completed |
| 1.3 | Run focused pytest and lint/type checks for touched files | Completed |
