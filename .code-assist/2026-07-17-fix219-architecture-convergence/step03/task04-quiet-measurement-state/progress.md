# Task 04 Progress: Quiet Measurement State

## Implementation Checklist

- [x] Stage 4.1: establish context, inventory, and test selection.
- [x] Stage 4.2: back up and quiet client/helper diagnostic configuration.
- [x] Stage 4.3: reload helper and verify effective quiet state.
- [x] Stage 4.4: run bounded stable journal observation.
- [x] Stage 4.5: verify evidence immutability and synchronize records.

## Setup Notes

- Mode: auto.
- Task source: `.agents/tasks/2026-07-17-fix219-architecture-convergence/step03/task-04-establish-quiet-measurement-state.code-task.md`.
- Design authority: existing fix219 detailed design and synchronized Step 03 plan.
- No repository `CODEASSIST.md` was found.
- No runtime code or tests are selected for this operational configuration task.

## Pre-Mutation Evidence

- The client shadow setting had development mode enabled.
- Repaint-debounce event logging was enabled; visual outlines and tracing were already disabled;
  repaint debounce itself was enabled and must remain enabled.
- The helper developer configuration selected enabled full-helper behavior with diagnostics on.
- The active historical tree contained 12 reduced-v2 and two superseded full-v1 JSON captures.
- A fixed non-overwriting backup target was available before the helper edit.

## Validation Evidence

- Client shadow: development mode false; payload/debug overlay disabled.
- Developer settings: tracing, outlines, markers, and repaint-debounce logging false; repaint
  debounce true.
- Helper configuration: a non-overwriting pre-Stage-3.10 backup exists; only the diagnostics
  field changed, leaving enabled full-helper mode intact.
- Reloaded helper health: healthy, version 1.0.0, protocol 3, diagnostics disabled.
- Bounded live probe: 20 target calls over 10 seconds, zero call failures, zero filtered
  `target_query_started`, repaint-request, or repaint-detail journal events.
- Historical evidence: all 12 reduced-v2 and two superseded full-v1 SHA-256 checks passed.
- Premature evidence guard: no post-optimization identity or `thresholds.json` exists.
- Patch hygiene: `git diff --check` passed.
- Tests: not run. No behavior, runtime code, EDMC hook, lifecycle, or Tk wiring changed; this task
  selected operational configuration/evidence validation only.

## Scope Review

- No runtime or test file changed.
- No capture, manifest, summary, threshold, or production-routing artifact changed.
- The original capture hold remains active.
- Stage 3.10 is complete; Stage 3.11 has not started.

## Commands Run

Configuration and preservation checks:

```bash
python3 -m json.tool overlay_settings.json
python3 -m json.tool dev_settings.json
jq -e '.dev_mode == false and .show_debug_overlay == false and .log_payloads == false' overlay_settings.json
jq -e '.log_repaint_debounce == false and .overlay_outline == false and .group_bounds_outline == false and .payload_vertex_markers == false and .repaint_debounce_enabled == true and .tracing.enabled == false' dev_settings.json
jq -e '.diagnostics == false and .enabled == true and .mode == "full_helper"' "${XDG_CONFIG_HOME:-$HOME/.config}/EDMCModernOverlay/gnome_helper_dev_mode.json"
sha256sum -c /tmp/fix219-task04-historical.sha256
git diff --check
```

Helper lifecycle and health:

```bash
gnome-extensions disable edmc-modern-overlay-helper@edmcmodernoverlay.github.io
gnome-extensions enable edmc-modern-overlay-helper@edmcmodernoverlay.github.io
gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.GetHealth
```

The bounded probe invoked that same D-Bus destination's `GetTargetState '{}'` method 20 times at
0.5-second intervals, then filtered the user journal between the recorded start/end timestamps
for `target_query_started`, `Repaint request:`, and repaint detail markers.

## Execution Notes

- The first helper reload attempt was rejected by the filesystem/session sandbox with dconf
  write warnings. It did not apply the reload. The approved host-session retry passed.
- The first bounded probe attempted inside the restricted session failed all 20 calls with session
  access denied and was discarded. The approved host-session rerun completed 20/20 calls and is
  the acceptance result recorded above.

## Commit Status

No commit. The Step 03 working plan reserves the reviewed increment commit for Stage 3.16, and
this task never pushes.
