# Progress: Restore inactive native-GNOME runtime profile

- [x] Setup: created isolated documentation directory and `logs/`; discovered instructions and found no `CODEASSIST.md`.
- [x] Explore: audited design, plan, research, task, current source/tests, Git status/diff/log, and routing dashboard.
- [x] RED: changed the native injected-runner/profile expectations; required focused suite failed as expected: 2 failed, 41 passed. The failures showed both native flags were still active.
- [x] GREEN: set only `_NATIVE_GNOME_PRESENTATION_PROFILE.fullscreen_shell_raster_active` and `.suppress_managed_pyqt_fallback_on_shell_raster_failure` to `False`; required focused suite passed: 43 passed in 0.18s.
- [x] REFACTOR: no further reshaping. The profile-only two-line production change preserves the existing bundle-owned adapter and legacy profile.
- [x] Validation: scoped Ruff passed; `git diff --check` passed; source diff has no protocol, target-discovery, extension, X11, or xcompat changes; a scoped secret-pattern scan found no matches.
- [x] Commit: exact-six-field handoff written; scoped conventional local commit created after validation (hash reported by the invoking context).

## Acceptance evidence

- Native GNOME remains helper-owned and raster-capable, while its profile and injected runner now receive `False` for both activation/suppression fields.
- Legacy raster's profile and injected-runner test retain `True` for both fields; its unavailable-helper fail-closed test remains in the focused suite.
- Architecture tests passed: generic consumer runtime dispatch carries no raw GNOME/helper/raster policy, and native X11/XWayland have neither GNOME runtime nor GNOME presentation imports.
- Unit-only test selection remains valid: no `load.py`, EDMC hook, public helper protocol/schema, target discovery, or live action was touched.

## Initial decisions

- Auto mode selected by the parent orchestration request; no further approval is needed.
- Unit-only coverage is appropriate because no lifecycle or `load.py` touch is permitted.
- Existing non-task dirty paths are preserved and will not be staged.
