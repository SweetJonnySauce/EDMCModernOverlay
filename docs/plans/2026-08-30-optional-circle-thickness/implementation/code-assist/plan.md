# Optional Circle Thickness: Plan

## Test strategy

| Scenario | Input | Expected result |
| --- | --- | --- |
| Compatibility helper | `send_shape(..., shape="circle", radius=...)` | Emits no `thickness` field. |
| Raw/client intake | Valid raw circle with omitted thickness | Normalizes, stores, and renders as a circle without an explicit thickness field. |
| Validation regression | `None`, non-numeric, zero, or negative explicit circle thickness | Drops the update and preserves the existing item. |
| Renderer fallback | Omitted circle thickness at scaled viewport | Uses unscaled `legacy_rect` default width. |
| Gallery | Both shapes, explicit `1` and omitted field | Four stable, inspectable payloads. |

## Implementation stages

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add failing helper, processor, renderer, and gallery unit tests. | Completed |
| 1.2 | Make circle thickness optional and use the common default at render time. | Completed |
| 1.3 | Update generated wiki and rendering-pipeline documentation. | Completed |
| 1.4 | Run focused tests, GUI rendering tests, and `make check`. | Completed |

## Phase 2: Gallery labels

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add a failing gallery test for one stable label message per shape. | Completed |
| 2.2 | Generate descriptive, same-TTL labels above each shape. | Completed |
| 2.3 | Run gallery tests and the project gate. | Completed |

## Design decision

The omitted-width default is intentionally `legacy_rect`, rather than a new
circle-specific configuration key. It provides identical omitted-thickness
rules for the two bounded shapes while preserving the explicit-width pixel
contract and avoiding a preference migration.
