# Payload inspector circle preview — context

## Requirement

Render a logged `shape: "circle"` payload in the payload inspector preview.

## Existing structure and conventions

- `utils/payload_inspector.py` renders selected payloads on a Tk `Canvas` using
  the 1280×960 legacy coordinate system.
- `_render_payload()` already renders vectors, rectangles, and messages. It
  normalises colors and converts coordinates through the preview scale.
- Circle payloads are emitted with `x`/`y` as centre coordinates and a positive
  `radius`; `w` and `h` are omitted.
- The repository uses `pytest`; this is deterministic local rendering logic, so
  it needs a unit test rather than an EDMC harness test.

## Integration map

`Overlay.send_shape(circle)` → payload log → `PayloadParser` → selected
payload → `PayloadInspectorApp._draw_preview()` → `_render_payload()` → Tk
canvas. The missing circle dispatch is the only gap in that sequence.

## Existing documentation

- `README.md` describes the plugin and its Python-based cross-platform scope.
- `docs/testing.md` describes pytest-based automated testing. No `CODEASSIST.md`
  is present.
