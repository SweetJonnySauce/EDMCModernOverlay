# Step 1 Task Context: Guarded Normal-Path Monitor Transfer

## Scope and test type

This task changes only the ordinary native GNOME Shell helper presentation path
in `helpers/gnome_shell_extension/extension.js` and its deterministic Python
source-contract tests in
`overlay_client/tests/test_gnome_shell_helper_extension_source.py`.

Test type: source-contract/unit-style tests. The behavior is deterministic at
the JavaScript source boundary and does not touch `load.py`, EDMC hooks, or
lifecycle wiring, so a harness test is neither needed nor appropriate.

## Existing documentation

- `AGENTS.md`: preserve the fix219 boundary, keep the change behavior-scoped,
  and record focused test evidence. The EDMC plugin-runtime constraints do not
  introduce a new plugin API, network operation, or Tk/UI action here.
- Root `README.md`: this repository is the cross-platform EDMC Modern Overlay;
  the helper is a platform-specific presentation component.
- The approved plan, detailed design, and runtime/Mutter research require a
  trusted target monitor to be transferred before frame resize only when both
  monitor indexes are valid and unequal. Readback remains authoritative.
- No `CODEASSIST.md` exists. The code-assist SOP applies its normal
  documentation, TDD, validation, and local-commit requirements.

## Existing implementation and dependency map

`ApplyPresentation` resolves a trusted target and overlay, then calls
`_applyOverlayPresentation(window, requestedRect, rectTolerance, options)`.
The options already include `targetPayload`; its `monitor` came from the
target `Meta.Window.get_monitor()` call. `_normaliseMonitorIndex()` already
returns a non-negative integral index or `null`.

The normal branch currently reads the overlay frame and monitor, skips resize
when the frame matches, otherwise calls `move_resize_frame`, then always reads
the post-operation frame and monitor. It retains mismatch degradation and
stacking handling. Diagnostic strategy probes use separate code and remain
outside ordinary presentation.

Required change shape:

1. Normalise target and overlay monitor indexes with the existing helper.
2. On a valid mismatch, call `move_to_monitor(targetMonitor)` before the
   existing resize/no-op decision.
3. Keep the no-op only for a matching frame on a valid, matching monitor.
4. Record an unavailable/throwing transfer condition, continue to the resize
   fallback, and leave post-operation readback/mismatch validation unchanged.

No protocol, Python presentation-state/runtime, backend bundle, X11,
XWayland, rendering, payload, or generic-follow changes are allowed.

## Constraints and uncertainty

Automated testing cannot prove Mutter settles the monitor transfer in a live
GNOME session. The later manual-only plan step owns that evidence. This task
must not run extension tooling, interact with the session bus, or add sleeps,
coordinate guesses, fullscreen behavior, or cross-backend fallbacks.
