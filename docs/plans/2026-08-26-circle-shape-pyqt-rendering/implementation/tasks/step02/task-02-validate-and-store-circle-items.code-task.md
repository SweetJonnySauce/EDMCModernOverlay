# Task: Validate and Store Circle Legacy Items

## Description
Add the centralized client-side circle path in `process_legacy_payload`: normalize valid circle geometry into a first-class stored item, reject invalid radius or thickness before same-ID store mutation, and make circle visual/transform changes visible to deduplication tracing. Keep rectangles, vectors, unknown shapes, and TTL semantics behavior-compatible.

## Background
The standalone client is the authoritative destination for all legacy payload sources. Task 01 preserves raw circle fields, while the compatibility helper from Step 1 already emits the canonical circle form. The current processor recognizes `rect` and `vect`, but stores other shape tokens as future-support payloads. Circles must become a `LegacyItem(kind="circle")` before rendering is added in Step 3. Invalid geometry must not replace a previously visible same-ID circle, so validation must happen before `store.set`. The existing store's expiry semantics and trace-based `_hashable_payload_snapshot` must remain consistent with legacy shapes.

## Reference Documentation
**Required:**
- Design: docs/plans/2026-08-26-circle-shape-pyqt-rendering/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/research/payload-and-rendering.md (centralized validation and dedupe expectations)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/plan.md (Step 2 Stage 2.2 and validation commands)
- overlay_client/legacy_processor.py (current rectangle/vector processor and snapshot conventions)
- overlay_client/legacy_store.py (stored-item and expiry contract)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. **Test type selected before edits: unit.** This task changes deterministic client normalization/storage with an injected `LegacyItemStore` and trace callback; it does not touch `load.py`, EDMC lifecycle hooks, sockets, or PyQt drawing. No harness test is required here; Step 4 owns lifecycle coverage.
2. Add a `shape == "circle"` branch in `process_legacy_payload` before the unknown-shape fallback. Coerce `x`, `y`, `radius`, and `thickness` consistently to integer legacy-canvas units, then accept only strictly positive radius and thickness.
3. For missing, non-numeric, zero, or negative radius/thickness, log an actionable warning that includes the payload ID, field, and invalid value; return `False`; and perform no store mutation. An invalid update must leave an existing same-ID circle intact.
4. For valid circles, store `LegacyItem(kind="circle")` with border `color`, transparent-default `fill`, centre `x`/`y`, `radius`, `thickness`, `__mo_ttl__`, copied optional `__mo_transform__`, `__mo_updated__`, expiry, and extracted plugin attribution. Reuse established TTL/expiry behavior exactly; do not reinterpret non-positive TTL handling.
5. Extend `_hashable_payload_snapshot` for `shape: "circle"` so the shape token, centre, radius, thickness, colour, fill, and transform metadata are all represented. Preserve rectangle and vector snapshot values unchanged.
6. Add focused unit coverage in `tests/test_legacy_processor.py` (or its established adjacent unit-test location) for valid circle storage, default/transparent fill, plugin and transform propagation, replacement by stable ID, and the existing TTL/purge contract.
7. Add parameterized invalid-radius and invalid-thickness unit cases. Each must capture the warning and assert `False`/no repaint plus no mutation of a previously stored same-ID circle.
8. Add trace-callback snapshot assertions proving a change to each circle visual/geometry/transform field yields a changed circle snapshot, while rectangle/vector regression tests continue to pass unchanged.
9. Run the Step 2 plan commands after focused tests pass:
   - `overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py -q`
   - `overlay_client/.venv/bin/python -m pytest -k 'legacy_processor or legacy_tcp' -q`

## Dependencies
- Task 01 preserves raw `radius` and `thickness`; this task must also accept direct canonical client payloads so the processor remains source-agnostic.
- `overlay_client/legacy_processor.py`: owns validation, storage, warning, and snapshot behavior.
- `overlay_client/legacy_store.py`: existing storage/expiry API; do not alter it unless review proves that impossible.
- Step 3 will consume the stored `circle` item for rendering and is out of scope.

## Implementation Approach
1. Inspect the rectangle and vector branches, `_hashable_payload_snapshot`, store expiry rules, and existing processor tests. Add failing unit tests for valid circle storage/replacement/TTL, invalid same-ID replacement, transparent fill, and changed trace snapshots.
2. Introduce a small private coercion seam only if it removes duplication without changing existing rectangle/vector coercion behavior. Implement the circle branch before the unknown-shape fallback and validate both geometry fields before building data or calling `store.set`.
3. Mirror the rectangle branch's transform-copy, timestamp, plugin, trace, and TTL patterns where applicable; keep warnings explicit and avoid broad exception handling.
4. Run the focused processor tests, then both Step 2 plan commands in order. Record exact command text and outcomes in this task's progress record; do not update the approved plan or execution dashboard from this task context.

## Acceptance Criteria

1. **Valid circle becomes a first-class stored item**
   - Given a canonical valid circle payload with centre coordinates, positive radius/thickness, colour, fill, TTL, plugin, and transform metadata
   - When `process_legacy_payload` receives it
   - Then it returns `True` and the store contains a `kind == "circle"` item with the normalized geometry, visual fields, TTL/expiry, copied transform, timestamp, and plugin attribution.

2. **Default fill and replacement preserve the existing contract**
   - Given a valid circle without a fill and a later valid same-ID circle with changed geometry or visual fields
   - When both are processed
   - Then the first item has the established transparent fill default, the later item replaces it, and the current TTL/expiry behavior is refreshed exactly as for existing legacy items.

3. **Invalid geometry is warned and cannot erase a visible circle**
   - Given a store containing a valid circle for an ID and parameterized incoming circles with missing, non-numeric, zero, or negative radius or thickness for that ID
   - When each invalid payload is processed
   - Then processing returns `False`, the captured warning names the ID, offending field, and value, and the stored valid circle remains unchanged.

4. **Circle dedupe snapshots cover every rendering-relevant field**
   - Given trace-enabled processing of otherwise identical valid circles
   - When centre, radius, thickness, border colour, fill, or transform metadata changes one at a time
   - Then the emitted circle dedupe snapshot changes for each variation, while existing rectangle and vector snapshot behavior remains unchanged.

5. **Existing non-circle behavior remains stable**
   - Given the existing rectangle, vector, unknown-shape, clear, and TTL processor tests
   - When the completed unit suite is run
   - Then their behavior continues to pass without changes to their public payload contracts.

6. **Focused unit evidence**
   - Given the completed processor and tests
   - When focused tests and both Step 2 plan commands are run
   - Then the commands pass and their exact results are recorded for the main-thread Step 2 review.

## Metadata
- **Complexity**: Medium
- **Labels**: circle-shape, legacy-processor, validation, legacy-store, deduplication, unit-tests, step-2
- **Required Skills**: Python data validation, deterministic state-transition testing, pytest parameterization, logging assertions
