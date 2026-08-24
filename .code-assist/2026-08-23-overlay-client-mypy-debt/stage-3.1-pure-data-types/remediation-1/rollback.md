# User-Directed Rollback — Stage 3.1 Remediation 1

## Reason

The user reported that the runtime issue under investigation reappeared after this remediation.
This record does not assert that the annotation-only changes caused the symptom.

## Reverted source edits

- Removed the shared clamp-origin `float` declarations from `follow_geometry.py`.
- Restored the prior `Tuple[str, ...]` annotation in `plugin_overrides.py`.
- Restored the prior `tuple(pt)` point materialization in `transform_helpers.py`.

The user subsequently directed a complete Stage 3.1 rollback, which also removed the earlier
Stage 3.1 native-origin annotation in `_convert_native_rect_to_qt_standard`, the trace-detail
type in `anchor_helpers.py`, and the mapping/vector-point annotations in `legacy_processor.py`.
The X11 clear-first repair, TTL behavior, tests, configuration, lifecycle, backend boundary,
commits, and external state were not changed.

## Post-rollback evidence

- Normal six-module mypy: expected failure, 20 errors in 6 files (the complete reverted Stage
  3.1 diagnostic set plus the intentionally deferred TTL diagnostic).
- Pure-data regression slice: 90 passed.
- Offscreen setup/repaint/follow regression slice: 55 passed.
- `git diff --check`: passed.

## Next action

Await user runtime verification before opening another remediation or starting Stage 3.2.
