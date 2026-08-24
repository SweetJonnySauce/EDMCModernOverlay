# Stage 3.1 Progress — Pure Data Type Corrections

## Checklist

- [x] 3.1.1 Read governing artifacts, Stage 2 evidence, scope review, prior
  handoff, dashboard, fix219 records, and the dirty worktree.
- [x] 3.1.1 Create stage-local context, plan, progress, and validation location
  before production edits.
- [x] 3.1.2 Run the prescribed focused mypy RED command exactly once.
- [x] 3.1.3 Correct only source-proven annotations in the six scoped modules.
- [x] 3.1.4 Run the identical focused mypy command exactly once for GREEN.
- [x] 3.1.4 Run the prescribed focused pure-unit slice exactly once.
- [x] 3.1.5 Review the scoped diff and write the exact six-field handoff.

## Test decision

Chosen before coding: static mypy RED/GREEN plus the existing focused pure-unit
slice. No test update is appropriate unless an observable runtime behavior
change becomes necessary, which is outside this annotation-only scope and
requires coordinator review. No harness applies because `load.py` is untouched.

## TDD record

- RED ran once: `source overlay_client/.venv/bin/activate && python -m mypy
  --follow-imports=skip overlay_client/follow_geometry.py
  overlay_client/anchor_helpers.py overlay_client/legacy_processor.py
  overlay_client/plugin_overrides.py overlay_client/payload_model.py
  overlay_client/transform_helpers.py`.
- Result: expected failure, exit `1`; `Found 16 errors in 4 files (checked 6
  source files)`. The errors are the frozen anchor (4), legacy (5), geometry
  (6), and TTL (1) sites. The task's frozen plugin-override and transform
  diagnostics are already absent in the current worktree; this is an
  improvement within the approved pure-data family, not a new error family.
- The full raw output is retained in `logs/mypy-pure-data-red.raw.log`; exit
  status is `logs/mypy-pure-data-red.exit-status`.
- Source inspection proved the geometry's native-origin locals become float
  intermediates before the existing integer rounding, the anchor trace details
  contain floats and strings, and legacy transform/vector containers are
  mappings or string/integer point dictionaries. Only annotations were changed.
- TTL is not changed: all reachable runtime inputs arrive through a
  `dict[str, object]` payload boundary, and source/call sites do not establish a
  closed representation for every pre-existing direct `int()`-accepted value
  (including protocol-based values). A guard, narrowing, or broad cast would
  change or hide that contract, so the diagnostic must remain for coordinator
  review.
- GREEN ran once with the identical six-module target and exited `1`; it
  improved from 16 to 5 errors. The anchor and legacy errors, plus the first
  two standard-geometry errors, are absent. The remaining error at
  `payload_model.py:98` is the documented TTL stop. The four remaining clamp
  geometry errors are source-proven annotation work, but mypy binds the local
  type from the earlier integer-valued branches before reaching the later
  branch-local annotations. Correcting that declaration requires a fresh
  context because this task's sole GREEN measurement has been consumed.
- The full raw output is retained in `logs/mypy-pure-data-green.raw.log`; exit
  status is `logs/mypy-pure-data-green.exit-status`. The required pure-unit
  regression still runs once as behavior evidence; no unchanged failing mypy
  command will be rerun here.
- Unit regression ran once: `source overlay_client/.venv/bin/activate &&
  python -m pytest overlay_client/tests/test_follow_geometry.py
  overlay_client/tests/test_anchor_helpers.py
  overlay_client/tests/test_transform_helpers.py
  overlay_client/tests/test_payload_dedupe.py
  overlay_client/tests/test_override_grouping.py -q`.
  Result: exit `0`, `90 passed in 0.32s`; raw output and status are in
  `logs/pytest-pure-data.*`. Existing tests were selected because all applied
  changes are annotations; no harness applies and no test was added.
- `git diff --check` passed. The bounded production diff contains only type
  declarations in `follow_geometry.py`, `anchor_helpers.py`, and
  `legacy_processor.py`; it adds no backend/compositor import, raw enum
  dispatch, Qt/lifecycle/follow behavior, config, `load.py`, or fix219
  transparent-clear change. `plugin_overrides.py`, `transform_helpers.py`, and
  `payload_model.py` needed no safe source edit in this context.
