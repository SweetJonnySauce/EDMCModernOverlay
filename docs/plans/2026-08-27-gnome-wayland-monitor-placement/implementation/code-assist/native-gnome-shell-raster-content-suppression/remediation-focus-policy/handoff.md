# Focused retained-actor remap-warm-up remediation handoff

Status; Completed — the live log’s `target_focused_remap_warmup` loop was reproduced in a unit test and removed without changing helper behavior.

Files changed; `overlay_client/follow_surface.py`; `overlay_client/tests/test_follow_surface_mixin.py`; the native GNOME content-suppression plan, execution-status dashboard, iteration checklist, progress table, and this remediation artifact.

Validation commands/results; RED: `source overlay_client/.venv/bin/activate && PYQT_TESTS=1 python -m pytest overlay_client/tests/test_follow_surface_mixin.py::test_refresh_follow_geometry_treats_retained_actor_as_mapped_when_target_is_focused -q` → failed because content became `SUPPRESSED`; GREEN targeted retained-content set → 4 passed; eight-file focused suite with `PYQT_TESTS=1` → 275 passed; external `make PYTHON="$VIRTUAL_ENV/bin/python" check` → Ruff clean, mypy clean, 1,697 passed; external `make PYTHON="$VIRTUAL_ENV/bin/python" test` → 1,697 passed; `git diff --check` → passed.

Decisions; The generic follow code consumes only the neutral `retained_content_visibility_available` fact and `should_show_overlay`.  When that fact represents the Shell-raster actor and generic Qt is intentionally unmapped, the actor is the policy’s current visible surface.  This prevents generic Qt remap warm-up while preserving `visible -> suppressed -> visible` content intent, actor continuity, and all backend boundaries.

Risks; Automated tests cannot prove Mutter live focus timing.  Manual acceptance must still verify checkbox-off focus loss suppresses content after debounce and focus return remains continuously visible.  No helper reload/update is required because this is Python client code only.

Next exact action; Restart EDMC once, then run the live native-GNOME focus matrix with the preference unchecked: verify focused content is continuously visible, unfocused content suppresses after debounce without black screen, and returning focus restores without a flash.  Do not commit unless explicitly approved.
