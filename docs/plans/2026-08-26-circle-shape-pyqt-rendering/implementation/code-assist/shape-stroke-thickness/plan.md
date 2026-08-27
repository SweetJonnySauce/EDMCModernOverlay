# Shape Stroke Thickness: Implementation Plan

## Acceptance Criteria

1. `rect` accepts an optional keyword-only `thickness`, while omitted calls emit
   the exact legacy rectangle payload and keep the existing client default.
2. Explicit circle and rectangle thicknesses are positive logical integers,
   validate before store mutation, and survive helper/raw/TCP paths.
3. Explicit widths resolve as `max(1, round(logical_width * group_scale))`.
4. The internal render seam distinguishes explicit logical width, preserved
   default pixel width, and no pen; it does not change other primitive APIs.
5. Public documentation describes supported shapes and both default/explicit
   behaviors accurately.

## Test Scenarios

| Input | Expected result |
| --- | --- |
| Positional rect without thickness | Exact existing payload, no `thickness` key. |
| Keyword rect with `thickness=2` | Payload and raw/TCP publication retain `thickness: 2`. |
| Circle/rect explicit width 2 at scales 0.5, 1, 2 | Resolved pen widths 1, 2, 4. |
| Explicit 1 at scale 0.5 | Resolved pen width clamps to 1. |
| Explicit zero/non-numeric/negative value | Warning, no store replacement. |
| Omitted rect | Existing `legacy_rect` width is used without scaling. |
| No border/transparent fill | No pen/brush behavior remains unchanged. |
| Opacity and multiple commands | Original pen remains unchanged; opacity is applied after width resolution. |

## Phase Status

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Explore and plan | Completed |
| 2 | Test-first coverage | Completed |
| 3 | Implementation | Completed |
| 4 | Documentation and validation | Completed |

### Phase 1: Explore and plan

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Read instructions and approved design | Completed |
| 1.2 | Map helper, ingress, processor, renderer, and tests | Completed |
| 1.3 | Select unit and harness test coverage | Completed |

### Phase 2: Test-first coverage

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add compatibility, normalization, and validation tests | Completed |
| 2.2 | Add scaled-width, fill, opacity, and isolation tests | Completed |
| 2.3 | Add raw/TCP rectangle harness coverage and verify RED | Completed |

### Phase 3: Implementation

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Carry optional rectangle thickness through helper and normalizer | Completed |
| 3.2 | Centralize supported-shape thickness validation before storage | Completed |
| 3.3 | Add internal bounded-shape stroke resolution seam | Completed |
| 3.4 | Reconcile circle scaling and preserve omitted rectangle default | Completed |

### Phase 4: Documentation and validation

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Update public API and rendering documentation | Completed |
| 4.2 | Run focused, GUI, baseline, and project validation | Completed |
| 4.3 | Review scoped diff and record remaining manual checks | Completed |

## Tests to Run

1. Focused helper/processor/harness tests after test creation (expected RED).
2. The same focused tests after implementation (expected GREEN).
3. GUI-enabled paint/render tests with `PYQT_TESTS=1`.
4. `overlay_client/.venv/bin/python scripts/check_edmc_python.py`.
5. `make check`.
