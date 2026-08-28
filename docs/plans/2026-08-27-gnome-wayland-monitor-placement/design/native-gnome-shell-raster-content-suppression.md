# Native GNOME Shell-Raster Content Suppression Design

**Status:** Proposed — implementation requires approval and live GNOME Wayland validation.

## Goal

Honor the unchecked foreground-visibility preference for the native GNOME
fullscreen Shell-raster route without repeating the black-screen regression.
The compositor actor must remain valid throughout ordinary focus loss and
focus return; only the rendered overlay content may become suppressed.

## Requirements

- An eligible fullscreen target retains its Shell-raster actor across an
  ordinary focus transition.
- With the preference unchecked, content becomes suppressed after the existing
  focus policy/debounce decides the target is unfocused; with it checked,
  content remains visible.
- Focus loss must not cause `target_not_focused`, actor clear/hide/detach,
  actor destruction, or a managed-PyQt fallback.
- Hard lifecycle loss retains the current clear behavior.
- An older or unsupported helper fails closed to stable visible content rather
  than actor-risk suppression.
- X11, xcompat, windowed presentation, geometry/placement, stacking, and
  click-through behavior remain unchanged.

## Architecture

```mermaid
sequenceDiagram
    participant Policy as Generic visibility policy
    participant Bundle as Native GNOME backend bundle
    participant Helper as GNOME Shell helper
    participant Actor as Existing Shell-raster actor

    Policy->>Bundle: neutral content intent: visible | suppressed
    Bundle->>Helper: request with continuity=true and optional content intent
    Helper->>Actor: retain parent, identity, placement, input policy
    Helper->>Actor: apply content visibility only
    Note over Actor: No clear, hide, detach, or recreate on ordinary focus loss
    Policy->>Bundle: visible on focus return
    Bundle->>Helper: restore content visibility
```

Generic policy owns only a neutral `visible`/`suppressed` intent. The native
GNOME presentation bundle owns all decisions about whether the helper supports
that intent and how it is represented in the helper request. Generic
follow/runtime code must not inspect a GNOME helper enum or presentation type.

## Contract

| Field | Owner | Meaning |
| --- | --- | --- |
| `allow_unfocused_target` | Native GNOME bundle | Actor-continuity authorization; remains true for an eligible fullscreen route during ordinary focus loss. |
| `content_visibility` | Native GNOME bundle/helper | Optional neutral value: `visible` or `suppressed`; controls raster content only. |
| capability/version | Helper | Explicitly states whether content suppression is implemented safely. |
| result status | Helper | Reports applied, suppressed, unsupported, or degraded without treating focus loss as target loss. |

The helper should accept `content_visibility` only behind an explicit protocol
capability/version gate. Before modifying actor state, it validates the current
actor/session identity. For both frame and region actors, the operation must
preserve parentage, session token, monitor placement, stacking, timeout state,
and non-reactivity. The initial implementation may use a reversible actor
content/opacity state change only if live testing confirms no flash or black
frame; if it does not, use a transparent-content replacement while retaining
the same actor identity. The exact mechanism is subordinate to those
invariants.

## Failure behavior

- Unsupported capability, malformed response, or helper rejection: retain the
  last known-safe visible actor state and report a degraded result.
- Suppression application error: restore or retain visible content; do not
  invoke the focus-risk clear path.
- Invalid actor/session identity or ordinary hard lifecycle loss: use existing
  lifecycle handling, not a PyQt fallback for a valid native route.
- Focus return: request `visible`; it must restore content on the already
  attached actor without re-placement or remapping.

## Test strategy

Unit tests prove neutral intent resolution, request serialization, capability
fallback, and backend-boundary ownership. Extension/runtime tests prove both
single-frame and region actors preserve identity and input/placement state
through `visible -> suppressed -> visible`. Transition tests prove ordinary
focus loss does not classify the target as lost or trigger a presenter swap.

Live GNOME acceptance is mandatory: repeatedly move focus away from and back
to fullscreen Elite with the preference both unchecked and checked, including
the two-monitor placement case. The unchecked path must hide overlay content
without black screens or flashes; focus return must restore it without actor
recreation. The checked path must remain visibly continuous.

## Rejected alternatives

- Directly mapping the preference to `allow_unfocused_target`: rejected after
  the live black-screen regression.
- Hiding/clearing/destroying the actor on focus loss: rejected because actor
  continuity is required for safe fullscreen focus return.
- Leaving the actor permanently visible: safe but does not meet the requested
  unchecked-preference behavior.
- Implementing suppression only in managed PyQt: insufficient because the
  affected fullscreen route is rendered by GNOME Shell raster actors.

