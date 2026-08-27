# Step 04 Task 02 Plan

## Documentation review strategy

No test code is added: the acceptance evidence is a manual field-by-field
comparison against `tests/test_edmcoverlay_shapes.py` and Task 01's accepted
raw/TCP lifecycle proof, followed by the exact Step 4 commands reused unchanged.

| Scenario | Source | Expected documentation result |
| --- | --- | --- |
| Helper circle example | Exact Step 1 payload test | Stable ID, `circle`, color, fill, centre `x`/`y`, positive radius/thickness, and TTL; no `w`/`h`. |
| Raw circle example | Task 01 harness | Canonical fields are retained through runtime publication; client validation remains authoritative. |
| Existing primitives | Existing wiki and Step 1 rectangle test | Positional rectangle semantics and vector marker semantics remain explicit. |
| PyQt rendering | Step 3 paint/render tests and detailed design | Derived square uses existing mapping and bounded `drawEllipse`; pen/fill/opacity and non-uniform ellipse behavior are accurate. |

## Implementation checklist

- [x] Reconcile restart state, select documentation-only evidence, and create the writable task record.
- [x] Identify stale rectangle-only and support-list claims.
- [x] Update API references and Getting Started with exact tested circle examples.
- [x] Update Concepts and FAQs discovery statements without expanding compatibility promises.
- [x] Update the rendering pipeline without inventing circle trace stages.
- [x] Compare every new public payload field/semantic claim to the tests and accepted Task 01 evidence.
- [x] Reuse the unchanged exact Step 4 command results; perform stale-claim and diff checks.
- [x] Record residual risk and hand off for independent review.

## Risks and mitigation

- A documentation example can drift from the wire contract. Mitigate through
  exact field-by-field comparison with the tested fixture.
- The word “circle” can be mistaken for a vector point marker. Mitigate through
  an explicit distinction in Getting Started and raw-payload documentation.
- Runtime normalization can be incorrectly described as validation. Mitigate by
  stating that it preserves fields and the client drops invalid geometry before
  drawable same-ID replacement.
