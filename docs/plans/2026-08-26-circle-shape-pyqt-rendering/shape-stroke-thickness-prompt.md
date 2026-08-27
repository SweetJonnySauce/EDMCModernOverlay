# Prompt: Generalize Explicit Shape Stroke Thickness

Implement a backward-compatible shape-stroke thickness capability for EDMC Modern Overlay. Apply it to the existing `circle` and `rect` legacy shapes, and create a small, clear extension seam so future stroked shapes can opt in without duplicating payload validation or PyQt pen behavior.

## Scope

- Circle already has a required caller-supplied `thickness`; reconcile it so its documented legacy-canvas semantics match rendering.
- Add an optional, keyword-only caller-supplied `thickness` for `rect`.
- Establish a reusable internal stroke-width policy for future shapes. Do not add a new visual primitive in this change.
- Preserve all existing message, rectangle, circle, vector, EDMC hook, socket, grouping, and preference behavior except where this prompt explicitly changes it.

## Governing requirements

Read `AGENTS.md`, the circle detailed design, the completed circle implementation plan, and the existing circle/rectangle code and tests before changing anything. Write a short, staged follow-up plan with tests before editing code. Use numbered phase/stage tables and update them as work progresses.

## Public API contract

1. Existing positional rectangle calls remain byte-for-byte behavior-compatible when `thickness` is omitted. Their payload shape must stay unchanged and their existing client `legacy_rect` configured width remains authoritative.
2. A rectangle may opt in with a keyword-only argument:

   ```python
   overlay.send_shape(
       "myplugin-box",
       "rect",
       color="#80d0ff",
       fill="none",
       x=100,
       y=100,
       w=200,
       h=80,
       thickness=2,
       ttl=5,
   )
   ```

3. Circle retains its existing keyword-only `thickness` requirement.
4. For both supported shapes, an explicitly supplied `thickness` is a strictly positive legacy-canvas unit. It must be carried through compatibility-helper, raw, and TCP payload paths.
5. Omitted rectangle thickness means “use the existing rectangle default”; do not serialize a synthetic `thickness` field in that case.
6. Explicit missing, non-numeric, zero, or negative thickness must log a useful warning and drop the payload before it replaces a visible same-ID shape. Circle radius validation remains unchanged.
7. Do not claim that a future shape supports `thickness` until its normalizer, renderer, tests, and docs implement it.

## Rendering contract

1. Explicit thickness must be scaled with the same `group_ctx.scale` used to convert a shape’s logical bounds into its pixel bounds. A logical thickness of `2` therefore becomes a 4-pixel pen at scale `2.0`, rounded and clamped to at least one pixel.
2. An omitted rectangle thickness must retain its exact existing pen-width path. Do not begin scaling the legacy rectangle default as a side effect of this change.
3. Encapsulate the policy in a small reusable helper or data-only descriptor. The API should distinguish:
   - an explicit logical stroke width to scale;
   - a shape-specific existing pixel/default stroke width to preserve; and
   - no pen for absent/invalid border color.
4. Apply global payload opacity after width resolution and do not mutate stored/original pens.
5. Retain the current circle square-bounds transform and `QPainter.drawEllipse` call. Rectangle continues to use `QPainter.drawRect`.

## Future-shape extension seam

Create the smallest maintainable seam that lets a future renderer declare whether it supports optional explicit stroke thickness and what default it uses. Keep it internal; do not introduce a speculative public generic-shape schema, registry, or new dependency.

The seam must let a future shape follow this sequence without copying circle/rectangle validation logic:

1. Declare explicit-stroke support and the default-width behavior.
2. Preserve an optional raw payload value through normalization.
3. Validate explicit thickness centrally before store mutation.
4. Resolve a final pen width at the common transformed-shape rendering boundary.

## Testing requirements

Choose test types before editing.

- **Unit tests:** helper payload contract, raw normalization, centralized validation/no-mutation behavior, width resolution at scales `0.5`, `1.0`, and `2.0`, opacity, and existing rectangle/circle regressions.
- **Harness tests:** because raw/TCP ingress is modified, extend the existing fake EDMC harness to prove a valid explicit rectangle thickness survives publication and invalid geometry is not accepted downstream. Do not use a live EDMC process, socket, OAuth flow, or external service.
- Prove a positional rectangle omitting thickness still emits no `thickness` field and uses the unchanged legacy default width.
- Prove explicit rectangle and circle thickness are separately scaled and rounded/clamped correctly.
- Prove no-pen/transparent-fill behavior is unchanged.
- Run focused tests first, then GUI-enabled paint/render tests, then `python scripts/check_edmc_python.py` and `make check`.

## Documentation requirements

Update public shape and raw-payload documentation so it clearly distinguishes:

- default rectangle thickness (existing client-controlled behavior);
- explicitly supplied logical thickness (scaled with the shape);
- required circle thickness;
- optional rectangle thickness; and
- which shapes currently support the field.

Do not describe thickness as a legacy-canvas unit unless its implementation scales it as specified above.

## Completion and reporting

Update the new follow-up plan as each stage completes. Record changed test files, exact commands, pass/fail/skip outcomes, manual checks remaining, and any backward-compatibility caveats. Do not change versions, package a release, commit, or push unless separately requested.
