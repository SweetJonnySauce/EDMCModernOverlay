# Plan: Restore inactive native-GNOME runtime profile

## Test strategy

| Scenario | Input | Expected result |
| --- | --- | --- |
| Native GNOME healthy helper | Native-GNOME status plus injected runner | Profile is helper-owned/raster-capable; runner receives `shell_raster_runtime_enabled=False` and `suppress_pyqt_fallback_on_shell_raster_failure=False`. |
| Legacy raster healthy helper | Legacy-raster status plus injected runner | Runner receives both raster-related flags as `True`. |
| Legacy raster unavailable helper | Legacy-raster status with unavailable GNOME helper | Existing fail-closed generic result is retained; runner is not invoked. |
| Architecture/X11 isolation | Focused architecture and bundle tests | Generic consumer contains no raw GNOME/helper/raster presenter policy; X11/xcompat have no GNOME runtime/imports. |

## Implementation plan

- [x] Update native-profile test expectations first and run the required focused tests to demonstrate RED.
- [x] Set only the two normal native-GNOME runtime profile flags inactive.
- [x] Run the required focused suite to GREEN.
- [x] Review/refactor for the smallest profile-only change; run scoped lint and final diff checks.
- [x] Record evidence, update the routing plan/dashboard accurately, write the required handoff, and commit only this task's paths.

## Risks and mitigation

The activation commit currently predates this remediation. The repair avoids reversing the runtime seam or touching transitions/protocols, so legacy raster remains the active compatibility route and native activation remains reserved for Step 2.
