# Step 3.1 Progress: Neutral Content-Intent Transport

## Checklist

- [x] Setup and context documented.
- [x] Requirements, boundary constraints, and test type selected.
- [x] RED tests written and failure verified.
- [x] GREEN implementation complete.
- [x] Refactor and focused validation complete.
- [x] Handoff complete.

## TDD log

### RED

Command:

```bash
source overlay_client/.venv/bin/activate && python -m pytest \
  overlay_client/tests/test_backend_consumers.py \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_backend_architecture_boundary.py -q
```

Result: expected 5 failures. `run_backend_presentation_cycle` rejected the
missing `content_visibility` keyword, while follow-surface spies received no
such request field.

### GREEN

Added a typed neutral request field, generic consumer forwarding, and retained
follow-surface state. The state starts and resets at `visible`; it updates only
from the existing policy decision. A changed shown-content intent sets the
existing one-shot refresh flag unless the managed-surface snapshot already owns
the remap refresh. The same focused command passed: `82 passed`.

### Refactor and validation

The retained intent helper is intentionally small and accepts only the neutral
enum. It does not inspect helper availability, compositor identity, target
focus, or preference state. Managed-windowed snapshots do not receive an extra
refresh request because their existing remap flow already owns that one-shot
refresh.

Focused validation:

```bash
source overlay_client/.venv/bin/activate && python -m pytest \
  overlay_client/tests/test_backend_presentation_policy.py \
  overlay_client/tests/test_backend_consumers.py \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_backend_architecture_boundary.py \
  overlay_client/tests/test_setup_surface.py -q -rs
```

Result: `99 passed, 6 skipped`. The six skips are the suite's normal
PyQt-dependent skips because `PYQT_TESTS` was not set. `ruff check` over all
touched Python files and `git diff --check` both passed.

The GUI-enabled rerun initially aborted when Qt attempted to use the active
display. The headless GUI-enabled command succeeded:

```bash
source overlay_client/.venv/bin/activate && QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest \
  overlay_client/tests/test_backend_presentation_policy.py \
  overlay_client/tests/test_backend_consumers.py \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_backend_architecture_boundary.py \
  overlay_client/tests/test_setup_surface.py -q
```

Result: `105 passed`.

## Commit status

No staging, commit, push, GNOME Shell reload, or live D-Bus action is allowed
for this task.
