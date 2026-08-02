# Task 05 Progress: Stable Target Query Pressure

## Execution checklist

- [x] Stage 1.1: read the task, design, pressure research, Step 03 plan/progress, and iteration checklist.
- [x] Stage 1.2: inspect the current cache, transition guard, force-refresh, invalidation, stale-raster, and post-remap paths.
- [x] Stage 1.3: select focused unit tests; confirm no harness touchpoint.
- [x] Stage 1.4: record touchpoints, unchanged behavior, risks, and commands before code edits.
- [x] Stage 2.1: add all Task 05 behavior tests before runtime edits.
- [x] Stage 2.2: run focused tests and capture expected RED evidence.
- [x] Stage 3.1: implement the smallest backend-owned correction.
- [x] Stage 3.2: run focused GREEN and refactor checks.
- [x] Stage 4.1: run the query/follow regression slice, compile check, and `git diff --check`.
- [x] Stage 4.2: synchronize authoritative and working progress records.
- [x] Stage 4.3: record commit status; do not commit before approved Stage 3.16.

## Setup and exploration

- Auto-mode parameters were inferred from the explicit user instruction and loaded handoff.
- Documentation directory creation succeeded.
- No `CODEASSIST.md` was found.
- The dirty tree matches the handoff and contains broader Step 03 work that must be preserved.
- Unit tests are the selected test type. Harness tests are not required because no plugin/Tk/lifecycle wiring is touched.

## Design decision

The existing backend runtime state and injected clock already implement the intended bounded
cache seam. The observed regression is caused by one policy condition that disables the target
skip whenever the transition guard is active. Task 05 will correct that interaction and fill
signature gaps without changing the generic boundary or transition state machine.

## TDD cycles

### RED 1

- Command: `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py -q`
- Result: 9 failed, 102 passed.
- Expected failures: two guarded stable-query cases showed the transition guard still forced a
  target query; the mapped-suppressed raster case showed the target throttle hid a lease refresh;
  and six new signature inputs (frame rect, buffer rect, monitor index, output, scale, workspace)
  were incorrectly treated as unchanged.
- Log: `logs/red-focused.log`

### GREEN 1

- Removed the transition guard as an unconditional blocker of the existing mapped-suppressed
  target-query cache; no new throttle or generic interface was added.
- Kept pending fullscreen handoff, managed-commit, surface-preparation, confirmed exposure
  recovery, and stale Shell-raster lease work outside the cached path.
- Invalidated the deadline on held transitions and pre-guard Shell-raster clear failure.
- Expanded the backend presentation signature with frame/buffer geometry, monitor index/output/
  scale, and workspace so refreshed target changes cannot reuse an obsolete presentation.
- Focused GREEN passed on the first implementation attempt: 111 passed.

## Validation

- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py -q`: 111 passed (`logs/green-focused-attempt-1.log`).
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_consumers.py -q`: 35 passed (`logs/green-backend-consumers.log`).
- `overlay_client/.venv/bin/python -m ruff check overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`: passed (`logs/ruff.log`).
- `overlay_client/.venv/bin/python -m compileall -q overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`: passed with no output (`logs/compileall.log`).
- `git diff --check`: passed.
- Full `make check` / `make test`: deferred by the approved Step 03 plan to the integrated
  query-plus-repaint milestone after Task 06.

## Commit status

No commit will be created for Task 05. The approved Step 03 plan reserves the reviewed increment
commit for Stage 3.16, and pushing remains unauthorized.
