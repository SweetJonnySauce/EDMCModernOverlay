# Requirements clarification

## Established context

- The change belongs on branch `fix/circle-group-bounds`.
- `payload_transform.accumulate_group_bounds()` needs circle-aware bounds.
- The renderer's existing circle geometry is the behavioral reference: centre
  coordinates plus radius form a square bounding box.
- A deterministic unit test is required because the affected helper is pure
  apart from injected font dependencies.

## Decision

Proceed directly to the detailed design and implementation plan. Scope is
limited to correcting circle bounds in the Fill-mode grouping path and proving
the behavior with unit tests; it does not change the public `send_shape` API or
the circle paint implementation.
