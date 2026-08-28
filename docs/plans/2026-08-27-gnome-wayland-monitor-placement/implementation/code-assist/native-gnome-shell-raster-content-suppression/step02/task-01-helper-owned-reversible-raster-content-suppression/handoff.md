# Handoff: Helper-Owned Reversible Raster Content Suppression

## Status

Completed. No commit, staging, live D-Bus call, extension reload, or preference
wiring was performed.

## Files changed

`helpers/gnome_shell_extension/constants.js`,
`helpers/gnome_shell_extension/extension.js`, and
`overlay_client/tests/test_gnome_shell_helper_extension_source.py`, plus this
task's context, plan, progress, and validation log.

## Validation commands/results

RED: focused source tests failed as expected (`2 failed`) before the helper
implementation. Final: Ruff passed; focused extension-source, presentation
state, and helper presentation runtime tests passed (`162 passed`); `git diff
--check` passed. The local GJS lacks a `--check` option, so no standalone JS
syntax check was available.

## Decisions

The helper advertises `shell_raster_content_visibility` only when its raster
code and actors are enabled. A valid request mutates the retained actor records
with `set_opacity(0|255)` and preserves non-reactivity. The content-only method
contains no clear, suspend, hide, detach, destroy, or show calls. Malformed or
mutation-failing requests return a degraded, stable-visible result without
actor lifecycle handling.

## Risks

Automated coverage is source/contract based; it cannot prove Mutter/Clutter's
live focus-return behavior. The new helper capability is untested in a live
GNOME session and must remain unwired to the preference until Step 3 and the
user-approved Step 4 manual matrix.

## Next exact action

Main orchestration context should independently inspect this helper-only diff
and focused evidence, update the Step 2 dashboard/stages if accepted, then
continue only with the next separately generated Step 2 task or remediation.
