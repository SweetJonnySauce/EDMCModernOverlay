# Step 3.2 Plan

## Test strategy

- Supported helper + `suppressed`: frame wire field is `suppressed` and
  fullscreen continuity stays true.
- Supported helper + `visible`: frame wire field is `visible`; a subsequent
  request is not cache-skipped.
- Capability-missing helper: no wire field, continuity remains true, and
  diagnostics record stable-visible fallback without a presenter change.
- Bundle runtime forwards the neutral request only to the GNOME runner.
- Existing architecture tests prove generic code has no GNOME protocol imports.

## Implementation

1. Add the neutral runtime argument at the GNOME bundle boundary.
2. Resolve the helper-owned value after health succeeds, immediately before
   raster request construction.
3. Attach the optional value and fallback metadata only to Shell-raster frame
   requests. Keep actor continuity calculation unchanged.
4. Run focused RED, GREEN, then refactor/validation checks.

