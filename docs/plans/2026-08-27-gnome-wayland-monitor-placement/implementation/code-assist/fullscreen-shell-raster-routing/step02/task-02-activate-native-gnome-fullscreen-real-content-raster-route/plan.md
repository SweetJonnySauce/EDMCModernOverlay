# Plan: Activate native GNOME fullscreen real-content raster route

## Test strategy

| Scenario | Input / expected outcome |
| --- | --- |
| Native bundle profile | `gnome_shell_wayland` runtime reports active fullscreen raster and fallback suppression. |
| Eligible selected native fullscreen | Healthy helper + borderless full-monitor target + provider result → cropped `gnome_shell_raster_frame`; `should_show_overlay=False`. |
| Windowed/ineligible target | Existing helper-cycle inputs → no raster request and established managed-PyQt behavior only for genuinely windowed targets. |
| Failed/no-visible provider | Existing helper-cycle provider failure inputs + suppression flag → clear/degrade and no fullscreen PyQt fallback. |
| Boundary | Existing architecture test confirms generic consumer neutrality and absence of GNOME imports in X11/xcompat. |

The pre-existing native selected-fullscreen test and profile test are the RED tests: both currently assert/observe inactive native flags. The focused helper tests already isolate provider, visibility, and eligibility contracts independent of selection identity.

## Implementation

1. Change only `_NATIVE_GNOME_PRESENTATION_PROFILE` in `gnome_shell_wayland.py` to enable the two existing flags.
2. Keep legacy profile, callback transport, helper runner, diagnostics, and protocol untouched.
3. Run the exact task suite and boundary suite, review for static proof-frame use and raw GNOME dispatch, then record results.

## Risks and mitigation

Fullscreen failure must not fall back to a misplaced PyQt surface. The existing helper runner owns that behavior; this task only forwards its already-tested suppression flag. No live action is authorized, so automated contracts cannot prove GNOME session placement.
