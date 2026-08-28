# Step 3.2 Progress

- [x] Setup and instruction/design review
- [x] Reconcile Step 3.1 handoff and preserve its changes
- [x] RED tests written and observed failing
- [x] GREEN implementation completed
- [x] Refactor review completed
- [x] Focused validation, Ruff, and diff check recorded
- [x] Handoff and plan/status updates completed

## Decision log

- Use the existing GNOME helper resolver in the native runner; generic code
  remains neutral.
- Represent unsupported stable-visible fallback in raster diagnostics rather
  than `degrade_reasons`, because a valid helper presentation must remain a
  reusable success and must not be converted into a lifecycle failure.
- Omit capability diagnostics for the normal default `visible` intent when a
  helper lacks the optional capability, preserving exact legacy raster request
  semantics. A suppressed intent retains its gated fallback diagnostic.

## TDD evidence

- RED: the supported-wire assertion failed because the raster request carried
  no `content_visibility` field.
- GREEN: the GNOME runtime now forwards neutral intent and resolves the
  helper-owned field only after health validation.
- Regression correction: initial fallback metadata altered legacy frame
  equality. Metadata is now emitted only for an actual suppressed-to-visible
  fallback, preserving the pre-existing visible route unchanged.

