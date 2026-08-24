# Stage 3.1 Remediation 1 Context — Source-Proven Annotation Corrections

## Scope

This fresh Code Assist context owns exactly eight source-proven annotations left by the prior
Stage 3.1 context:

- four common-origin `float` declarations in `overlay_client/follow_geometry.py`;
- two local `tuple[PrefixEntry, ...]` declarations in `overlay_client/plugin_overrides.py`; and
- two `tuple[float, float]` point declarations in `overlay_client/transform_helpers.py`.

`overlay_client/payload_model.py` and its direct `int()` TTL coercion are explicitly excluded.
The current TTL diagnostic must remain unresolved, without a cast, guard, ignore, or input-
contract change. No Qt lifecycle/MRO, rendering, backend, fix219/X11, config, test, `load.py`,
or CI change is authorized.

## Evidence and invariants

The normal six-module mypy check reports nine diagnostics: the eight source-proven annotation
diagnostics in scope plus `payload_model.py:98`. Earlier placement of the four clamp-native
origin declarations inside later branches did not establish the mutable local's type at its
common earlier assignment seam. Moving only those declarations to that seam preserves all
assignments, arithmetic, rounding, and returned integer geometry.

The `PrefixEntry` tuple and transformed-point tuple values are already produced by existing
helpers and consumed through the stated shapes. These are annotation-only corrections; runtime
behavior must remain unchanged. Existing focused pure-unit tests are the selected regression
evidence. No new test is needed unless a behavior change is discovered, in which case this
context must stop.

## Prior records read

- Root `AGENTS.md`; no `CODEASSIST.md` exists.
- All top-level mypy-debt artifacts, including `iteration-checklist.md` and
  `orchestration-prompt.md`.
- The prior Stage 3.1 context, plan, progress, scope review, and handoff.
- The fix219 X11 records, including the clear-first paint invariant and its pending manual gate.

