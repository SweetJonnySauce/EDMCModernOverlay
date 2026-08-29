# Circle Shape Support: Planning Summary

## Status

Planning is complete. Implementation has not started.

## Artifacts

- `rough-idea.md`: initial request.
- `idea-honing.md`: agreed requirements.
- `research/payload-and-rendering.md`: repository and Qt research, data flow, risks, and references.
- `design/detailed-design.md`: standalone technical design.
- `implementation/plan.md`: test-driven, staged implementation plan and checklist.

## Approved design

The feature adds `shape="circle"` to the legacy `send_shape` helper. Circles use a stable ID, centre coordinates, positive radius and stroke thickness, border colour, fill colour, and existing TTL semantics. Client-side processing validates all sources, rejects invalid geometry with a warning before store mutation, derives a square bounding box through existing legacy transforms, and renders it via PyQt `QPainter.drawEllipse`.

Existing rectangles and vectors remain behaviorally unchanged.

## Implementation sequence

1. Extend the public payload contract with regression coverage for rectangles.
2. Normalize, validate, deduplicate, and store circles.
3. Add transform-aware PyQt paint commands.
4. Prove EDMC raw/TCP wiring and update documentation.
5. Run focused, harness, full, lint, type-check, and GUI-enabled validation.

## Next step

Begin implementation from Step 1 in the implementation plan. Before each code change, update the relevant stage status and run the step’s focused tests before advancing.
