# Plan: Neutral Content-Visibility Intent

## Test strategy

| Scenario | Input | Expected output |
| --- | --- | --- |
| Focused target | Valid focused snapshot, preference unchecked | `visible`; existing mapped-visible behavior unchanged. |
| Keep-visible target | Valid unfocused snapshot, preference checked | `visible`; existing mapped-visible behavior unchanged. |
| Debounced focus loss | Valid unfocused snapshot after thresholds | `suppressed`; existing mapped-suppressed behavior unchanged. |
| Prepared surface | Prepared unfocused mapping path | `suppressed`; existing mapping/warmup behavior unchanged. |
| Hard loss | Unavailable, minimized, or off-workspace snapshot | `suppressed`; existing hidden behavior unchanged. |
| Boundary | Generic policy source | No GNOME helper import, enum, or protocol dispatch. |

## Implementation plan

- [x] Add RED assertions for the neutral intent and generic boundary.
- [x] Run the focused RED tests and record the expected missing-symbol failure.
- [x] Add the smallest typed, two-value policy representation derived from
  `content_visible`.
- [x] Run the focused GREEN tests.
- [x] Review for simplification and run the task validation command.

## Outcome

The implementation is a read-only derived property rather than a second
policy field. Existing callers retain their boolean contract, while later
backend-owned consumers can use the typed intent. No helper request, actor
behavior, `allow_unfocused_target`, or follow-surface code changed.

## Risks and mitigation

The principal risk is duplicating policy logic and drifting from existing
debounce behavior. A derived property avoids a second decision path. This task
does not send any helper request or change actor state.
