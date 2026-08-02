# Task 04 Context: Quiet Measurement State

## Summary

Task 04 executes authoritative Stage 1.6 / working Stage 3.10. It is an operational configuration
and evidence step: no runtime code, production routing, capture, manifest, or threshold artifact
may change.

## Requirements

- Back up the user-local GNOME helper developer configuration before editing it.
- Disable helper diagnostics while preserving `enabled`, `mode`, and unrelated fields.
- Restore client diagnostics to quiet normal-use values:
  - `overlay_settings.json`: `dev_mode=false`;
  - `dev_settings.json`: `log_repaint_debounce=false`, with visual outlines and tracing disabled;
  - capture-only environment flags absent from the running client.
- Reload the helper because it reads the developer configuration during extension enable.
- Prove a bounded stable observation has no `target_query_started` or per-repaint journal stream.
- Preserve bounded counters, state changes, normalized failures, and privacy boundaries.
- Preserve the 12 reduced-v2 captures and two superseded full-v1 captures exactly.
- Do not resume capture or create a post-optimization evidence identity.

## Existing Documentation

- The detailed design requires high-frequency diagnostics to remain dev-gated and aggregated and
  explicitly disables per-cycle query/repaint events for quiet measurement.
- The Step 03 plan maps this work to Stage 3.10 and makes it a prerequisite for the cache change.
- The performance README freezes the diagnostics-enabled reduced-v2 procedure as history.
- No `CODEASSIST.md` exists. Repository `AGENTS.md` instructions therefore supplement the task and
  design documents.

## Current State Before Mutation

- `overlay_settings.json`: `dev_mode=true`.
- `dev_settings.json`: repaint-debounce logging enabled; tracing and visual outlines disabled;
  repaint debounce itself remains enabled.
- Helper developer configuration: enabled full-helper mode with diagnostics enabled.
- Historical evidence inventory: 12 reduced-v2 captures and two superseded full-v1 captures.
- The helper configuration backup name is fixed and non-overwriting for recoverability.

## Implementation Paths

- Repository settings: `overlay_settings.json`, `dev_settings.json`.
- User-local helper settings: the GNOME helper developer configuration under the user's standard
  Modern Overlay configuration directory.
- Execution records: this directory plus the chronological Step 03 progress record and the
  performance evidence README.

## Dependency Map

```text
EDMC preference / overlay_settings.json ─┐
dev_settings.json ───────────────────────┼─> overlay client quiet state
helper developer configuration ──reload─┘
                                         └─> bounded journal observation
historical capture inventory ───────────────> immutability verification
```

## Test-Type Decision

No unit or harness test is selected because Task 04 changes no logic, `load.py`, EDMC hook,
lifecycle wiring, or Tk behavior. Acceptance uses configuration validation, helper health/state,
a bounded live journal observation, evidence hashes, and patch hygiene. Runtime behavior changes
begin in Task 05 and require focused RED/GREEN unit tests there.

## Uncertainties and Safety

- The EDMC-managed `dev_mode` preference must not silently overwrite the quiet shadow value.
- Helper disable/enable is the supported reload mechanism and must leave the helper enabled and
  healthy.
- If a live client cannot be observed in a stable state, configuration can be prepared but the
  quiet-observation gate remains incomplete.
