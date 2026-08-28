# Progress: Activate native GNOME fullscreen real-content raster route

- [x] Setup: isolated documentation directory and logs created; instructions, task, design, research, plan, dashboard, source, tests, Git state, and historical evidence audited.
- [x] Explore: selected unit tests; no lifecycle/harness scope.
- [x] RED: profile expectation plus existing selected-native real-content test failed exactly because the native profile forwarded inactive flags (2 failed).
- [x] GREEN: enabled only the normal native profile flags; exact focused suite including architecture coverage passed (165 passed).
- [x] REFACTOR: no simplification was warranted; the two existing profile flags remain the smallest bundle-owned seam.
- [x] Validation: exact task suite and boundary coverage passed; scoped Ruff and `git diff --check` passed; scope/secret review found no static proof-frame production selection, protocol edits, raw generic dispatch, X11/xcompat changes, or credentials (the scan's token-name matches are existing test fixtures).
- [ ] Commit: stage only this task's scoped source/tests/artifacts and commit locally.

## Auto-mode decision log

Auto mode is in effect under standing user approval. Existing historical commits and dashboards are evidence only; current source is being independently validated. No `CODEASSIST.md` exists, so no project-specific code-assist addendum applies.

## TDD evidence

- RED: `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_consumers.py::test_native_gnome_bundle_owns_an_active_fail_closed_fullscreen_shell_raster_profile overlay_client/tests/test_gnome_helper_presentation_runtime.py::test_native_gnome_runtime_routes_eligible_fullscreen_to_real_content_raster -q` → 2 failed. The profile remained false and the existing native real-content request was not presented.
- GREEN: `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_shell_raster_frame.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_architecture_boundary.py -q` → 165 passed.
- REFACTOR: retained the profile-only activation; existing helper-cycle tests cover windowed/partial/ambiguous exclusion and provider/no-visible-content fail-closed clear/degrade behavior through the forwarded neutral flags.

## Test rationale and limitations

Unit tests only: no `load.py`, EDMC hook, or lifecycle state changed. A GNOME Shell/DBus/EDMC live action is intentionally not run; the later user-gated manual matrix remains required for session placement proof.

## Commit

- [x] Local implementation commit `33ec919b2ee6e337e026dd1b062938837e435c29` (`feat(gnome): activate native fullscreen raster route`); no push was performed. Only this task's implementation, tests, routing plan/dashboard, and isolated code-assist documentation were staged.
