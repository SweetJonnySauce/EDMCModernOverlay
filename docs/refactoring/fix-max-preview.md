## Goal: Fix controller "max" preview to use cached max bounds

## Problem Summary
- Issue #101 reports that `controllerPreviewBoxMode: "max"` does not render the max-preview box in 0.7.6 beta.
- The overlay cache contains `max_transformed` data for the group, but the controller preview path never reads it.
- Controller preview builds snapshots from `_get_cache_record`, which only returns `base` and `transformed`.
- Preview rendering uses `snapshot.transform_bounds` or `snapshot.base_bounds`, so `max_transformed` is effectively ignored.

## Root Cause (Current Behavior)
- `_get_cache_record` in `overlay_controller/overlay_controller.py` and `overlay_controller/services/group_state.py` only extracts `base` and `transformed` from `overlay_group_cache.json`.
- The preview renderer (`overlay_controller/preview/renderer.py`) relies on `snapshot.transform_bounds` and `snapshot.base_bounds` only.
- As a result, `max_transformed` never influences the controller preview even when configured.

## Proposed Fix Plan
## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Define snapshot selection rules + touch points | Completed |
| 2 | Implement snapshot-layer selection for max preview | Completed |
| 3 | Verify behavior + document tests | In Progress |

## Phase Details

### Phase 1: Define snapshot selection rules + touch points
- Goal: settle the minimal snapshot-layer logic for max preview selection and identify code paths to change.
- Touch points:
  - `overlay_controller/services/group_state.py` snapshot construction
  - `overlay_controller/controller/preview_controller.py` fallback snapshot construction
  - `overlay_controller/overlay_controller.py` legacy snapshot fallback
- Invariants: keep renderer logic unchanged; keep "last" behavior unchanged.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Define snapshot selection precedence for `max` and `last` modes | Completed |
| 1.2 | Confirm minimal touch points to update snapshot construction | Completed |

### Phase 2: Implement snapshot-layer selection for max preview
- Goal: ensure snapshot `transform_bounds` reflect max preview when configured.
- Plan:
  - Parse `controllerPreviewBoxMode` (camel/snake) from group config.
  - Extract `max_transformed` and `last_visible_transformed` from cache entries.
  - When mode is `max`, set `transform_bounds` from `max_transformed` when valid; otherwise fall back to last/transformed/base.
  - Keep renderer unchanged and keep "last" mode behavior unchanged.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add cache extraction + bounds selection in GroupStateService snapshot | Completed |
| 2.2 | Mirror the selection logic in preview_controller fallback snapshot | Completed |
| 2.3 | Update legacy snapshot fallback in overlay_controller | Completed |

### Phase 3: Verify + test
- Goal: confirm max preview renders and document checks.
- Tests (planned):
  - Unit test for snapshot selection precedence (max → last → transformed → base).
  - Manual controller preview check with known `max_transformed` cache entry.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add/record unit tests for snapshot selection | Completed |
| 3.2 | Manual controller preview verification | Planned |

## Results
- Snapshot selection now reads `max_transformed` (and `last_visible_transformed` fallback) when `controllerPreviewBoxMode` is `max`.
- Selection logic is applied in GroupStateService snapshots and both controller fallback paths.
- Renderer remains unchanged; it consumes the selected `transform_bounds`.
- Unit tests added and run for max preview snapshot selection (`python3 -m pytest overlay_controller/tests/test_group_state_service.py`).
- Snapshot nonce tests now pass after renaming the raw cache accessor (`python3 -m pytest overlay_controller/tests/test_snapshot_nonce.py`).

## Open Questions / Decisions
- Decision: keep it simple by selecting preview bounds in the snapshot layer and hand the renderer a single set of bounds to draw.
- Decision: do not persist a preview-mode hint in the snapshot.
