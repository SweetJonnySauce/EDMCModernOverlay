# Implementation plan: unify explicit shape thickness as pixels

## Scope

An explicitly supplied `thickness` for either `rect` or `circle` is a logical
Qt-pixel width, rounded and clamped to at least one pixel without viewport or
group scaling. A rectangle that omits `thickness` continues to use the
configured `legacy_rect` width.

## Phase status

| Phase | Stage | Status |
| --- | --- | --- |
| 1 | 1.1 Add the red rectangle pixel-width contract | Completed |
| 2 | 2.1 Route explicit rectangles through the shared pixel policy | Completed |
| 3 | 3.1 Validate rendering, ingestion, documentation, and repository checks | Completed |

## Stages

### 1.1 Contract test

Replace the scale-aware explicit-rectangle matrix with an unscaled matrix:
`thickness=2` must resolve to a 2-pixel pen at group scales 0.5, 1.0, and 2.0.
Retain the MiterJoin assertion and omitted-rectangle default test. This is a
pure unit test in `overlay_client/tests/test_render_surface_mixin.py`; run the
focused thickness filter and expect red before implementation.

### 2.1 Shared policy wiring

Change only `_build_rect_command()` to pass explicit thickness through the
existing `explicit_pixel_width` policy. Preserve the default-pixel fallback
when thickness is absent, all geometry, and both shapes' existing pen/brush
behavior. Remove the obsolete logical-width policy only if no remaining
consumer or test needs it; otherwise do not expand the refactor.

### 3.1 Validation and documentation

Update the wiki-source and rendering documentation so both shapes have the
same explicit pixel-width rule. Run the focused renderer module, legacy
processor/API tests, `make check`, and `git diff --check`. No commit is part
of this plan.
