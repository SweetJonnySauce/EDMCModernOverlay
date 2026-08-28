# Plan

## Acceptance coverage

| Scenario | Expected result |
| --- | --- |
| Eligible native GNOME fullscreen | Selected native bundle enables the existing bridge and submits a cropped real-content raster request. |
| Windowed native GNOME | No raster frame; managed PyQt remains the safe presenter. |
| Ineligible fullscreen | No raster frame; a clear/degraded request suppresses PyQt fallback. |
| Provider/no-visible-content failure | Clear/degrade result and no visible PyQt fullscreen surface. |
| Compatibility boundary | Legacy raster remains active; X11/xcompat remain outside the runtime. |

## Implementation sequence

- [x] Explore the Step 1 seam, helper-cycle eligibility, existing focused tests, and routing artifacts.
- [x] RED: add native-GNOME policy and selected-cycle tests; run the required focused suite.
- [x] GREEN: activate only the native bundle profile.
- [x] REFACTOR: profile change is already the smallest clear expression; generic consumers remain untouched and neutral.
- [x] Validate required focused suite and `git diff --check`; scoped Ruff passed.
- [x] Review scoped diff and logs for secrets; update plan/dashboard, write handoff, and make a scoped local commit.

## Risks and mitigations

The existing helper-cycle bridge already distinguishes windowed targets from
fullscreen failures. Activating both native profile flags together is the
smallest change that preserves that distinction. Tests use injected callbacks,
never live GNOME/DBus actions, and retain legacy/X11/xcompat boundaries.
