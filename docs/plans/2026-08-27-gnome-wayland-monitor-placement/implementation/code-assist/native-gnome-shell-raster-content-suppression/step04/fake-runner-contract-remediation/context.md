# Step 4 Fake-Runner Contract Remediation: Context

## Scope

Repair only the test-local GNOME presentation runner in
`test_backend_presentation_cycle_wraps_gnome_helper_result_when_helper_available`.
The Step 3 neutral runtime request now always supplies
`content_visibility`; this fake runner predated that request field.

## Requirements and invariants

- Accept and record the neutral `BackendPresentationContentVisibility` value.
- Assert the default cycle sends `VISIBLE`.
- Do not change production code or the helper protocol.
- Preserve the fix219 boundary: this test imports only the neutral policy type.
- Do not run project-wide gates, live GNOME actions, or Git mutations.

## Dependency map

`run_backend_presentation_cycle` → native GNOME runtime → injected fake runner.
The runner is a test double for the bundle-owned presentation-cycle callable;
it must accept the same keyword contract as the real runner.

## Test selection

This is deterministic test-double wiring. The exact consumer test is the RED
and GREEN proof; the consumer and architecture-boundary suites are the scoped
regression checks. No harness test is needed because neither `load.py` nor
lifecycle wiring changes.
