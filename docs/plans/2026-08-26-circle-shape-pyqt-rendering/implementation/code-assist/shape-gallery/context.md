# Shape Gallery Utility: Context

## Goal

Add `utils/shape_gallery.py`, a manual visual-inspection sender for a running
EDMC Modern Overlay. It publishes a fixed gallery of circles and rectangles
through the existing local CLI socket, rather than creating a second renderer.

## Existing Patterns

- `utils/send_overlay_from_log.py` resolves the repository root, reads
  `port.json`, sends JSON CLI messages to the localhost broadcaster, and waits
  for acknowledgements.
- `overlay_client/launcher.py` uses `port.json` by default; a command-line
  override is supported.
- The public shape contract accepts circle radius/thickness and optional
  rectangle thickness. `fill="none"` produces an unfilled shape.

## Design

- Generate payloads in a pure `build_gallery_payloads(ttl)` helper so unit tests
  can verify visual-coverage data without opening a socket or Qt window.
- Publish each payload as a `legacy_overlay` CLI command with stable,
  `shape-gallery-`-prefixed IDs.
- Include circles and rectangles that vary thickness, color, dimensions,
  position, and filled/unfilled state.
- Default to a finite 60-second TTL to avoid leaving inspection content behind;
  allow `--ttl 0` for persistent inspection.

## Test-Type Decision

| Behavior | Test type | Reason |
| --- | --- | --- |
| Gallery coverage and payload contract | Unit | Pure deterministic payload construction. |
| Socket publication | Manual | Requires a running local overlay and is the purpose of this developer tool. |
