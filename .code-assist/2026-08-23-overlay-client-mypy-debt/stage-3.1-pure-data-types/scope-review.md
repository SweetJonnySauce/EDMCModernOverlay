# Stage 3.1 Scope Review — Pure Data Types

## Review decision

**Approved for one implementation task.** The approved parent plan is the
approval for this concise one-task breakdown. The task is limited to the
frozen Stage 2.1 pure-data diagnostics in `follow_geometry.py`,
`anchor_helpers.py`, `legacy_processor.py`, `payload_model.py`,
`plugin_overrides.py`, and `transform_helpers.py`.

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 3. Pure data and renderer corrections | 3.1 | Generate and scope-review the pure-data type task | Completed |

Phase 3 status: **In progress — Stage 3.1 implementation pending.**

## Frozen diagnostic and contract inventory

| Module | Frozen lines | Exact established value contract | Planned type-only treatment |
| --- | --- | --- | --- |
| `follow_geometry.py` | 74, 76, 185, 187, 202, 204 | Native geometry originates as integer pixels, but origin arithmetic with a floating device ratio creates an intermediate float; the returned `Geometry` remains rounded integers. | Explicitly type only the mutable native-origin locals as `float`; retain every calculation and final rounding/clamping. |
| `anchor_helpers.py` | 65, 66, 85, 86 | Trace detail dictionaries deliberately include numeric measurements plus `suffix` and `justification` strings. | Widen only the trace callback/detail mapping to its actual `float | str` value union. |
| `legacy_processor.py` | 240, 310, 312, 315, 318 | A copied transform is a mapping, and normalized vector points always contain integer `x`/`y` with optional string `color`, `marker`, `text`, and `size`. | Add precise mapping/heterogeneous-point container annotations without changing normalization, filtering, or stored payloads. |
| `plugin_overrides.py` | 514, 523 | `_clean_group_prefixes` returns `tuple[PrefixEntry, ...]`; `_GroupSpec.prefixes` already records that contract. | Declare the local with the existing `PrefixEntry` tuple type. |
| `transform_helpers.py` | 203, 242 | `remap_rect_points` and inverse scaling are consumed as two-coordinate floating points; the return contract is `list[tuple[float, float]]`. | Preserve the existing point transformations and give the comprehensions an exact two-float tuple shape. |
| `payload_model.py` | 98 | The current ingest contract passes the payload's TTL directly to `int()` and clamps the result to zero or greater. The static `dict[str, object]` surface does not itself prove which `int()`-accepted runtime values may occur. | Do not add a guessed runtime guard or a broad escape hatch. First prove a precise static representation that preserves the current accepted coercions; otherwise stop with evidence for coordinator review. |

No compositor-specific helper/presentation import, backend enum dispatch,
shared-state change, Qt lifecycle change, or fix219 transparent-surface change
belongs in this task.

## Test selection review

The geometry, anchor, transform, legacy point, override-prefix, and payload
diagnostics are expected to be annotation-only. Their existing runtime behavior
is already exercised by pure unit tests, so focused mypy RED/GREEN plus the
following unit slice is required:

```bash
source overlay_client/.venv/bin/activate && python -m pytest \
  overlay_client/tests/test_follow_geometry.py \
  overlay_client/tests/test_anchor_helpers.py \
  overlay_client/tests/test_transform_helpers.py \
  overlay_client/tests/test_payload_dedupe.py \
  overlay_client/tests/test_override_grouping.py -q
```

No `load.py` or runtime lifecycle wiring is in scope, therefore no harness test
applies. A new focused unit test must be written before any runtime helper
branch/coercion changes. In particular, the `payload_model.py` TTL diagnostic
may not be resolved by changing which values are accepted without first adding
a test for the proposed accepted/rejected value contract and obtaining
coordinator review.

## Explicit exclusions and stop conditions

- Do not change runtime geometry, rounding, scale clamp, payload normalization,
  TTL expiry, dedupe, override matching, transform order, data ownership, or
  serialized output merely to satisfy mypy.
- Do not add broad `Any`, `ignore_errors`, blanket or unexplained ignores, new
  dependencies, configuration changes, or test-only type suppression.
- Preserve the independent clear-first fix219 X11 repair and the generic
  backend boundary; pure helpers must not import compositor-specific code.
- Stop for coordinator review if `payload_model.py` cannot express the existing
  `int()` coercion contract narrowly and behavior-preservingly, if any planned
  annotation changes an observable result, or if the focused/directory-wide
  diagnostic reveals a family outside the frozen inventory.
