# Remediation 01 Plan

1. RED: change the selected full-monitor fullscreen test to require the
   pre-`8ef91cd` continuity request and prove that the direct-preference path
   fails it.
2. GREEN: restore the backend-owned fullscreen geometry authorization helper
   and use it with the explicit preference when building the Shell-raster
   request.
3. REFACTOR: retain a clear continuity-focused test name, review the narrow
   source/test diff, and verify no generic runtime or protocol surface changes.
4. Run the required focused GNOME unit/source-contract suite and
   `git diff --check`.
