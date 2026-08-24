# Stage 3.1 Remediation 1 Plan

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 3. Pure data and renderer corrections | 3.1-R1.1 | Capture normal six-module mypy RED evidence | Completed — 9 errors in 4 files: eight owned annotations plus TTL. |
| 3. Pure data and renderer corrections | 3.1-R1.2 | Apply the eight exact annotation corrections | Completed — common declaration seam, existing `PrefixEntry` contract, and exact point shapes. |
| 3. Pure data and renderer corrections | 3.1-R1.3 | Run normal mypy GREEN, pure-unit regressions, Ruff, and diff hygiene | Completed — one retained TTL error; 90 tests and Ruff passed. |
| 3. Pure data and renderer corrections | 3.1-R1.4 | Record handoff and leave TTL diagnostic unchanged | Completed |

## Validation plan

Run exactly one RED and one GREEN normal-import-following check against:

```bash
source overlay_client/.venv/bin/activate && python -m mypy \
  overlay_client/follow_geometry.py \
  overlay_client/anchor_helpers.py \
  overlay_client/legacy_processor.py \
  overlay_client/plugin_overrides.py \
  overlay_client/payload_model.py \
  overlay_client/transform_helpers.py
```

Then run the established five-file pure unit slice, scoped Ruff for the three edited modules,
and `git diff --check`. This is annotation-only work: no test is added unless runtime behavior
changes, which is not expected or authorized.

## Results

The normal GREEN check reports only `payload_model.py:98`; all eight owned diagnostics are
removed. The five-file pure unit slice passed 90 tests, scoped Ruff passed, and the final
worktree hygiene check passed. No test was added because no runtime behavior changed.
