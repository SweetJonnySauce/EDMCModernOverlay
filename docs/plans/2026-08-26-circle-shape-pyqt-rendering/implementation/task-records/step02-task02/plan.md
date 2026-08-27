# Step 02 Task 02 Plan

## Test strategy

Test type selected before edits: **unit**. The test seam is `process_legacy_payload(store, payload, trace_fn)` and the in-memory `LegacyItemStore`; no runtime wiring is involved.

| Scenario | Input | Expected output |
| --- | --- | --- |
| Valid circle storage | Positive numeric-string/integer centre, radius, thickness, visual fields, TTL, plugin, transform | `True`; `kind="circle"`; normalized integer geometry; copied transform; stored attribution and expiry. |
| Transparent default/replacement | Omitted fill then same-ID valid update | First fill is `#00000000`; later item replaces data and refreshes expiry. |
| TTL contract | Positive then zero/negative TTL circle at fixed monotonic time | Existing positive/next-purge expiry behavior is preserved. |
| Invalid geometry | Missing, non-numeric, zero, and negative radius or thickness after a valid same-ID circle | `False`, no trace/repaint/store replacement; warning names ID, field, and value. |
| Dedupe snapshot | Otherwise-equal trace-enabled circles varying one visual/geometry/transform field | Each variation emits a distinct circle snapshot; existing rect/vector snapshot forms stay unchanged. |

## Implementation checklist

- [x] Reconcile restart state and select unit testing.
- [x] Inspect processor/store/snapshot conventions and Task 01 input contract.
- [x] RED: add all focused circle processor tests and capture expected failure.
- [x] GREEN: add the smallest validation/storage/snapshot circle branch.
- [x] REFACTOR: retain direct local conventions and review rect/vector compatibility.
- [x] Run focused processor tests and both mandated Step 2 commands.
- [x] Record exact results and deferred commit.

## Implementation approach

Add a small positive-integer coercion helper so radius and thickness share one explicit failure path. The circle branch will validate both values before tracing or calling `store.set`, then mirror rectangle metadata handling. Its snapshot will include the shape token, border/fill, centre, radius, thickness, and transform. Existing shapes remain structurally unchanged.

## Risks and mitigations

- Invalid same-ID input could erase visible output: tests seed an existing circle and assert no mutation before/after every invalid update.
- Snapshot omission could hide a rendering change: parameterized trace tests vary every rendering-relevant circle field.
- TTL semantics could drift: tests fix monotonic time and exercise existing expiry/purge behavior.
