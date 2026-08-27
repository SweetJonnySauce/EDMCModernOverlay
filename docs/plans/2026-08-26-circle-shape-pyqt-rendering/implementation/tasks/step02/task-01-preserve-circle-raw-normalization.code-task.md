# Task: Preserve Circle Fields Through Raw Legacy Normalization

## Description
Extend the pure raw legacy-payload normalizer so raw `shape="circle"` messages retain `radius` and `thickness` while preserving every established rectangle and vector normalization contract. This task prepares canonical raw/TCP payloads for the centralized client validation introduced by the next task; it must not validate geometry, mutate runtime wiring, or render circles.

## Background
Step 1 introduced the canonical compatibility-helper circle payload. Raw senders and the legacy TCP boundary both call `EDMCOverlay.edmcoverlay.normalise_legacy_payload`, which currently copies rectangle coordinates and dimensions but discards circle-specific geometry. The detailed design makes the client processor—not this normalizer—the authoritative validator, so malformed circle geometry must still be forwarded unchanged for the centralized validation/no-mutation behavior in Task 02. The existing normalizer supports case-insensitive legacy field aliases, ID, colour, fill, coordinates, TTL, vector handling, and optional plugin attribution; those contracts must remain intact.

## Reference Documentation
**Required:**
- Design: docs/plans/2026-08-26-circle-shape-pyqt-rendering/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/research/payload-and-rendering.md (raw normalization seam and canonical wire payload)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/plan.md (Step 2 Stage 2.1 and validation commands)
- EDMCOverlay/edmcoverlay.py (existing `normalise_legacy_payload` implementation)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. **Test type selected before edits: unit.** The normalizer is deterministic and accepts mappings without EDMC lifecycle, socket, or `load.py` hook wiring; no harness test belongs in this Step 2 task. Step 4 owns raw/TCP lifecycle harness coverage.
2. In `normalise_legacy_payload`, when the supplied shape token denotes `circle`, retain `radius` and `thickness` from the raw payload in the normalized shape event. Support the same legacy key-alias convention used by the existing fields where applicable.
3. Preserve raw circle geometry as input data for the centralized processor. Do not coerce, clamp, reject, warn about, or otherwise validate `radius` or `thickness` in this normalizer.
4. Do not add synthetic `w`/`h` semantics for circles beyond the normalizer's existing generic shape output, and do not alter legacy rectangle or `vect` normalization, vector-point rejection, ID-only clear behavior, TTL normalization, colour/fill defaults, or plugin attribution.
5. Add focused unit tests for a raw circle containing canonical and legacy-cased keys. Assert `type`, `shape`, ID, colours, centre coordinates, `radius`, `thickness`, TTL, and plugin attribution survive normalization. Include malformed/non-positive circle geometry to prove this layer preserves it for Task 02 rather than dropping it.
6. Retain or add direct rectangle and vector regression assertions in the same normalization test scope, proving their existing normalized fields and vector behavior are unchanged.
7. Run the Step 2 plan commands after focused tests pass:
   - `overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py -q`
   - `overlay_client/.venv/bin/python -m pytest -k 'legacy_processor or legacy_tcp' -q`

## Dependencies
- Step 1's canonical `Overlay.send_shape(..., "circle", ...)` payload contract is already implemented and remains unchanged.
- `EDMCOverlay/edmcoverlay.py`: owns pure raw normalization and must be the only production source file changed by this task.
- Task 02 consumes this normalized circle payload to validate and store it; do not implement that branch here.

## Implementation Approach
1. Inspect `normalise_legacy_payload`, its coercion helpers, and tests that already exercise `Overlay` raw payload handling. Add focused failing unit cases for canonical and legacy-cased circle fields, including an invalid geometry pass-through case.
2. Make the smallest circle-only payload-construction change that preserves `radius` and `thickness` without changing the existing `rect` or `vect` branches.
3. Add or retain narrow rectangle/vector normalization regressions in the same test file; do not create a harness test or edit `load.py`.
4. Run the focused normalization tests, then both Step 2 plan commands in order. Record exact command text and outcomes in this task's progress record; do not update the approved plan or execution dashboard from this task context.

## Acceptance Criteria

1. **Canonical raw circle fields survive normalization**
   - Given a raw legacy mapping with `shape: "circle"`, an ID, colour, fill, centre `x`/`y`, `radius`, `thickness`, TTL, and plugin metadata
   - When `normalise_legacy_payload` is called
   - Then it returns a `type: "shape"` circle payload retaining those fields and values for downstream processing.

2. **Legacy aliases and invalid geometry reach the client validator**
   - Given raw circle messages using supported legacy-cased geometry keys and messages whose radius or thickness is missing, non-numeric, or non-positive
   - When they are normalized
   - Then the corresponding geometry values are preserved in the normalized output without a normalizer-side rejection, clamping, or warning.

3. **Existing shape normalization is unchanged**
   - Given established raw rectangle and vector payloads
   - When they are normalized after the circle change
   - Then their existing fields, vector validation behavior, TTL, and plugin attribution remain unchanged and no circle-only fields appear in their contract.

4. **No lifecycle or rendering scope expansion**
   - Given the completed raw-normalization change
   - When the scoped diff is reviewed
   - Then it changes only the normalizer and its unit tests, with no `load.py`, socket/harness, client storage, or PyQt rendering changes.

5. **Focused unit evidence**
   - Given the completed normalizer and unit tests
   - When focused tests and both Step 2 plan commands are run
   - Then the commands pass and their exact results are recorded for the main-thread Step 2 review.

## Metadata
- **Complexity**: Low
- **Labels**: circle-shape, raw-normalization, legacy-payload, unit-tests, step-2
- **Required Skills**: Python mapping normalization, backward-compatible payload contracts, pytest parameterization
