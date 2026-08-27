# Task 01 Context: Circle Compatibility Payload Contract

## Mode and scope

`code-assist` is running in auto mode for generated Step 1 Task 01 only. The task changes the deterministic `Overlay.send_shape` compatibility helper and its injected publisher boundary. It does not change raw normalization, client storage, rendering, EDMC hooks, or network behavior.

## Existing documentation

- `AGENTS.md` requires an explicit test-type choice, small behavior-scoped changes, and recorded validation.
- The approved idea, research, detailed design, and implementation plan require a stable-ID `circle` payload with centre `x`/`y`, `radius`, `thickness`, `color`, `fill`, and `ttl`, while preserving positional rectangle calls.
- No `CODEASSIST.md` was found. The repository has `README.md` and harness documentation, neither adding a constraint relevant to this pure helper change.

## Implementation paths and dependencies

| Area | Path | Role |
| --- | --- | --- |
| Compatibility helper | `EDMCOverlay/edmcoverlay.py` | `Overlay.send_shape` builds a payload then delegates to `_emit_payload`. |
| Publisher seam | `EDMCOverlay/edmcoverlay.py` | `_emit_payload` adds the `LegacyOverlay` envelope and calls the module-level `send_overlay_message`. |
| New focused unit test | `tests/test_edmcoverlay_shapes.py` | Monkeypatches the local publisher to capture payloads without sockets or EDMC runtime activity. |

## Requirements and acceptance mapping

- Select **unit** testing: the helper is deterministic and the publisher is injectable; no `load.py` or lifecycle code is touched.
- Retain the existing nine-argument positional rectangle call and its field coercion exactly.
- Permit a keyword circle form, emitting only circle geometry (`radius`, `thickness`) and no rectangle `w`/`h` fields.
- Keep `_emit_payload` as the only publishing path so the envelope and availability behavior remain unchanged.
- Prove the exact circle event, stable ID/TTL pass-through, and positional rectangle regression with a local test double.

## Dependency map

`Overlay.send_shape` -> `_emit_payload` -> `send_overlay_message` (monkeypatched test double). Step 2 will consume the emitted wire fields; this task deliberately does not depend on Step 2.

## Uncertainties

None material. The existing method has required positional rectangle geometry, so optional defaults are necessary only to make the documented keyword circle form callable; positional rectangle values retain their original conversions.
