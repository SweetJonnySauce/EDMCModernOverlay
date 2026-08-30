# Step 1 context

## Scope

Test-only TDD task for the approved circle stroke-width policy. Runtime source
must remain unchanged.

## Dependency map

`LegacyItem` shape data flows through `_build_rect_command()` or
`_build_circle_command()` to `_build_bounded_shape_command()`, which sets the
Qt pen width using the injected group scale. The tests use `_StubGroupContext`
to make the scale deterministic.

## Existing pattern

The pre-existing shared test parameterized both shapes. It is replaced with
separate unit-test contracts so that rectangles retain their scale-aware
behavior while circles describe the approved unscaled-pixel behavior.
