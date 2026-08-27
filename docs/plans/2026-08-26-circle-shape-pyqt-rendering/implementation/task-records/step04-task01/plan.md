# Step 04 Task 01 Plan

## Test strategy

Test type selected before edits: **mixed**. The runtime call depends on EDMC lifecycle shims and fake external publication, requiring the `harness` marker. The same-ID no-mutation replay is pure deterministic client processing and requires a unit test.

| Scenario | Input | Expected output |
| --- | --- | --- |
| Raw/TCP valid circle publication | Raw circle with stable ID, shape, colours/fill, centre, positive radius/thickness/TTL, and plugin | Runtime returns `True`; captured `LegacyOverlay` preserves every canonical field and adds only established raw/timestamp metadata. |
| Raw-normalised invalid replay | Valid stored circle followed by same-ID raw circle normalised with missing, non-numeric, zero, or negative radius/thickness | Processor returns `False`, logs ID and bad geometry, emits no trace/repaint, and retains the original store item. |
| Regression gate | Existing harness, processor, and paint-command tests | Both exact Step 4 commands pass without a real listener or external connection. |

## Implementation checklist

- [x] Reconcile restart state and select mixed harness/unit testing.
- [x] Inspect the harness fixture, runtime publication seam, normaliser, and processor-store patterns.
- [ ] RED: add focused valid-publication and raw-normalised invalid-replay tests; run the exact Step 4 commands and capture failures.
- [ ] GREEN: no production change is authorized; verify existing implementation satisfies the new tests.
- [ ] REFACTOR: review tests for local naming and authority-boundary clarity.
- [ ] Run both exact Step 4 commands in order and record results.
- [ ] Record deferred commit and hand off for independent review.

## Risks and mitigation

- The runtime could silently become a geometry authority: the harness input is valid and the unit replay explicitly normalises invalid raw fields before client rejection.
- An invalid same-ID update could erase a drawable item: every invalid replay asserts object identity of the pre-existing stored circle.
- A test could use live infrastructure: the established harness overrides `_publish_external`; the unit test uses only in-memory state.
