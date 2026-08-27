# Context

## Approved scope

Step 2 locks the Step 1 guarded normal GNOME Shell monitor transfer to the
existing optional presentation-diagnostics and applied-rectangle readiness
contracts. This is deterministic source-contract and Python unit work only;
no `load.py` or EDMC lifecycle wiring is in scope, so no harness test is
required.

## Existing implementation

- `helpers/gnome_shell_extension/extension.js` already emits optional
  `presentation_diagnostics` with schema `1`, the normal action label, target
  monitor, pre/post overlay monitor, and pre/post frame state.
- The helper result keeps requested and applied rectangles at its existing
  top-level result surface. The Python client keeps diagnostics observational
  and makes readiness depend on validated applied-rectangle readback.
- The runtime suite already simulates a one-cycle mismatch retry and persistent
  wrong-monitor backoff. The generic boundary suite protects
  `overlay_client/follow_surface.py`.

## Constraints

- Do not alter helper protocol/version/capabilities, request/result schema, or
  diagnostic schema version.
- Do not change generic follow/runtime code, backend bundles/interfaces, X11,
  XWayland, rendering, payload processing, or live GNOME state.
- Preserve tolerance, bounded retry, wrong-monitor classification, persistent
  mismatch backoff, and degraded/suppressed behavior.

## Existing documentation

Read `AGENTS.md`; the code-assist SOP; the approved orchestration prompt,
plan, execution dashboard, task, detailed design, required research, and Step
1 handoff. No `CODEASSIST.md` exists. The repository README and harness README
were discovered but are not needed for this helper-only, non-harness task.

## Test strategy

Add source-contract coverage for the optional normal diagnostic record and its
stable evidence. Add presentation-state coverage proving diagnostics cannot
override a mismatched readback. Add runtime coverage proving a diagnostic
normal transfer action still becomes ready only after the matching retry.
