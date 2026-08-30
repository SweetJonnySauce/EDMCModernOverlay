# Step 2 context

## Scope

Implement the approved circle-only stroke-width policy in the deterministic
bounded-shape command builder. This is a unit-test-covered rendering seam; it
does not involve EDMC lifecycle or `load.py` wiring.

## Touch points and invariants

- `overlay_client/render_surface.py`: add a separate caller-supplied pixel
  policy and select it ahead of the existing logical policy.
- Existing Step 1 tests: circles use unscaled Qt logical pixels; rectangles
  remain scale-aware logical widths.
- Unchanged: circle geometry, transforms, grouping, validation, vectors,
  configuration, and public APIs.

## Validation

Run the focused thickness filter, the full render-surface mixin module, and
`git diff --check` after the narrow implementation.
