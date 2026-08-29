# Task: Add Circle Compatibility Payload Contract

## Description
Extend the legacy `EDMCOverlay.edmcoverlay.Overlay.send_shape` compatibility helper with a circle-specific form while retaining the existing positional rectangle API exactly. The helper must emit the canonical circle wire payload for the client work in Step 2, without adding normalization, validation, storage, or rendering behavior.

## Background
`Overlay.send_shape` currently always emits rectangle geometry (`w` and `h`) after coercing positional arguments. Circle callers need a stable-ID form whose `x` and `y` values are the logical circle centre and whose geometry is represented only by `radius` and `thickness`. The compatibility layer is intentionally not the authoritative geometry validator: it must preserve supplied circle fields for the client-side validation path introduced in Step 2. Existing publisher dispatch and rate-limited unavailable warnings are established behavior and must remain unchanged.

## Reference Documentation
**Required:**
- Design: docs/plans/2026-08-26-circle-shape-pyqt-rendering/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/research/payload-and-rendering.md (existing compatibility contract and canonical circle payload)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/plan.md (Step 1 requirements and required validation commands)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. **Test type selected before edits: unit.** This task changes a deterministic compatibility helper and its injected publisher boundary; it does not touch `load.py`, EDMC lifecycle hooks, sockets, or client rendering, so no harness test is required.
2. Keep `shapeid` and `shape` as the first two `send_shape` arguments and preserve every existing positional rectangle invocation, coercion, and payload field unchanged.
3. Support `shape == "circle"` with named `color`, `fill`, `x`, `y`, `radius`, `thickness`, and `ttl` inputs. Emit `type: "shape"`, `shape: "circle"`, the supplied stable `id`, centre `x`/`y`, `radius`, `thickness`, `color`, `fill`, and `ttl`; do not emit `w` or `h` for circle payloads.
4. Preserve the existing `_emit_payload` path, including its `event: "LegacyOverlay"` envelope, publisher behavior, and unavailable-warning behavior. Do not add client normalization, invalid-geometry handling, storage, or PyQt rendering in this task.
5. Add focused unit coverage around `Overlay.send_shape` using the repository's existing monkeypatch/test-double approach for `send_overlay_message`. Cover the exact circle event payload, stable ID and passed TTL, and an existing positional rectangle call whose event payload remains byte-for-byte field-equivalent to the prior contract.
6. Run the Step 1 focused commands exactly as recorded in the approved plan after the task-specific tests pass:
   - `overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py -q`
   - `overlay_client/.venv/bin/python -m pytest tests -k 'send_shape or legacy' -q`

## Dependencies
- `EDMCOverlay/edmcoverlay.py`: existing `Overlay.send_shape` and `_emit_payload` compatibility/publisher behavior.
- The repository pytest configuration and a test-double/monkeypatch seam for intercepting `send_overlay_message` without invoking a real overlay service.
- Step 2 consumes the emitted circle contract; this task must not depend on Step 2 client support being implemented.

## Implementation Approach
1. Before editing, inspect the current `Overlay.send_shape` signature and existing test conventions, then add a failing unit test that captures the emitted `LegacyOverlay` event for a keyword-based circle call and asserts its exact dictionary fields, including absence of `w` and `h`.
2. Add failing regression coverage for a positional rectangle call and for circle ID/TTL pass-through; ensure all tests use a local publisher double and make no network or EDMC-runtime call.
3. Refactor only the helper signature and payload construction needed to branch between the unchanged rectangle form and the new named circle form. Route both forms through the existing `_emit_payload` method unchanged.
4. Run the task-specific tests, then the two plan-mandated focused commands in order. Record the exact commands and outcomes in the task progress record required by the implementation workflow; do not update plan or dashboard status from this task context.

## Acceptance Criteria

1. **Canonical circle event payload**
   - Given an `Overlay` whose publisher is replaced with a test double
   - When `send_shape("myplugin-radius", "circle", color="#80d0ff", fill="#1a1a1acc", x=100, y=100, radius=50, thickness=2, ttl=5)` is called
   - Then the double receives exactly one `LegacyOverlay` event with `type`, `shape`, `id`, `color`, `fill`, `x`, `y`, `radius`, `thickness`, and `ttl` equal to the supplied values, and it contains no `w` or `h` keys.

2. **Stable replacement identity and TTL pass-through**
   - Given two circle calls with a stable shape ID and caller-supplied TTL values
   - When their events are captured by the test publisher
   - Then each event retains the supplied ID and its corresponding TTL without the compatibility helper substituting either value.

3. **Positional rectangle compatibility**
   - Given an existing positional rectangle invocation of `send_shape`
   - When it is emitted through the same publisher seam
   - Then its `LegacyOverlay` payload retains the legacy rectangle `x`, `y`, `w`, `h`, colour, fill, ID, shape, and TTL fields with their current coercion and no circle-only fields.

4. **Existing publisher behavior remains the delivery path**
   - Given either supported shape form and an available test publisher
   - When `send_shape` is called
   - Then publication still occurs through `_emit_payload` with the `LegacyOverlay` envelope, without introducing a new network or rendering path.

5. **Focused unit evidence**
   - Given the completed helper and focused tests
   - When the task-specific pytest selection and both Step 1 plan commands are run
   - Then they pass, with their exact command text and results recorded for the main-thread step review.

## Metadata
- **Complexity**: Medium
- **Labels**: circle-shape, compatibility-api, legacy-payload, unit-tests, step-1
- **Required Skills**: Python API evolution, backward-compatible signature design, pytest monkeypatching, payload-contract testing
