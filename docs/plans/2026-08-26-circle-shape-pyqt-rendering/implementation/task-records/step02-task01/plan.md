# Step 02 Task 01 Plan

## Test strategy

Test type selected before edits: **unit**. The normalizer is pure mapping logic; no lifecycle, hook, socket, or rendering contract is touched.

| Scenario | Input | Expected output |
| --- | --- | --- |
| Canonical circle | Raw `circle` with canonical geometry and metadata | Shape event retains ID, colours, centre, radius, thickness, TTL, and plugin. |
| Legacy-cased circle | Raw `Shape` with `Radius`/`Thickness` | Same geometry values survive unchanged. |
| Invalid circle geometry | Zero/non-numeric raw geometry | Values survive unchanged for Task 02 validation. |
| Rectangle regression | Established raw rectangle | Existing normalized rectangle fields and metadata remain unchanged. |
| Vector regression | Valid and rejected raw vectors | Existing vector preservation and insufficient-point rejection remain unchanged. |

## Implementation checklist

- [x] Reconcile restart state and select unit testing.
- [x] Inspect normalizer, helper aliases, Step 2 design, and existing unit-test patterns.
- [x] RED: add focused raw-normalization tests and run them to show circle geometry is absent.
- [x] GREEN: add the smallest circle-only raw-field retention branch.
- [x] REFACTOR: review the narrow change against rectangle/vector contracts.
- [x] Run the focused test and both mandated Step 2 commands.
- [x] Record results and deferred commit.

## Implementation approach

Keep the generic normalized shape payload intact. For a normalized `circle` shape only, copy raw `radius` and `thickness` through using the established key aliases; do not coerce or inspect their values. Add tests to the established `edmcoverlay` shape test module so the direct helper and raw normalizer contracts remain colocated.

## Risks and mitigations

- Premature validation could hide invalid input from the authoritative client validator. Tests explicitly expect malformed values to survive.
- A broad payload rewrite could change rectangle/vector behavior. The production edit is conditional on the existing lowercase shape token, with direct regression assertions.
