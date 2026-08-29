# Task 01 Plan: Circle Compatibility Payload Contract

## Test strategy

Test type selected before edits: **unit**. The task is a pure compatibility-helper and injected-publisher change; it does not exercise EDMC startup, hooks, sockets, or rendering, so a harness test is not applicable.

| Scenario | Input | Expected output |
| --- | --- | --- |
| Circle wire contract | Stable ID, `circle`, named colour/fill/centre/radius/thickness/TTL | One `LegacyOverlay` event with exact supplied circle fields and no `w`/`h`. |
| Circle ID and TTL | Two circle calls with the same ID and different TTL values | Captured events retain that ID and their individual TTL values. |
| Positional rectangle regression | Existing nine-argument rectangle call | Existing envelope and rectangle payload, including integer geometry, with no circle-only fields. |

The new tests must fail before the helper supports keyword circle geometry. They use a module-level publisher monkeypatch and never make real network or EDMC runtime calls.

## Implementation checklist

- [x] Explore `send_shape`, its `_emit_payload` boundary, and repository test patterns.
- [x] Choose unit testing before edits.
- [ ] RED: add focused contract tests and record expected failure.
- [ ] GREEN: add the smallest signature/payload branch while preserving rectangle behavior.
- [ ] REFACTOR: verify naming and local conventions; keep the helper direct.
- [ ] Validate task-specific tests and the two Step 1 commands.
- [ ] Record a deferred commit because the approved plan remains unfinished.

## Implementation approach

Keep the first two parameters unchanged. Make only the rectangle-specific positional parameters optional so a circle can omit `w` and `h`; branch on `shape == "circle"`. Both branches call the unchanged `_emit_payload` method. The rectangle branch retains its pre-existing dictionary order and `int` conversions.

## Risks and mitigations

- Signature compatibility: preserve the original positional parameter order and rectangle body.
- Delivery behavior: reuse `_emit_payload` unchanged and assert its envelope through the publisher double.
- Scope creep: do not validate geometry or add normalization/rendering; those are later approved steps.
