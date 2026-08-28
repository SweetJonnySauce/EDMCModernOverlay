# Plan

## Acceptance coverage

| Scenario | Expected result |
| --- | --- |
| Native GNOME bundle | Profile owns helper presentation, supports future fullscreen raster, but sends both existing runner flags as `False`. |
| Legacy raster bundle | Profile enables raster and fallback suppression; unavailable helper produces the existing fail-closed result. |
| Native X11 / XWayland | `presentation_runtime` is `None`; a presentation-cycle call is a no-op. |
| Generic boundary | `consumers.py` has no raw GNOME helper/raster runtime predicates or direct helper-presentation implementation import. |

## Implementation sequence

- [x] Explore the selected bundle and consumer seams.
- [x] RED: add profile/runtime and source-boundary tests, then run the focused suite.
- [x] GREEN: add the narrow contract, GNOME-owned implementation, and neutral consumer invocation.
- [x] REFACTOR: remove superseded generic GNOME helpers and review X11/xcompat imports.
- [x] Validate the required focused suite and `git diff --check`.
- [x] Scan scoped changes/logs for secrets; update routing plan/dashboard; hand off and commit.

## Risks and mitigations

The runtime request keeps existing injected-runner and surface/frame callbacks,
so the runner is lifted rather than reshaped. The native GNOME profile remains
inactive to prevent premature raster activation. The legacy unavailable-helper
marker stays fail-closed.
