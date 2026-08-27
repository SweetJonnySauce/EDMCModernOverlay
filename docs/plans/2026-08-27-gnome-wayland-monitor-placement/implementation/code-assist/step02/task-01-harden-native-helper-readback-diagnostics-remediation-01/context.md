# Remediation Context

## Purpose

This fresh, auto-mode remediation context corrects an evidence-only gap from
the initial Step 2 code-assist attempt: the required validation commands had
been reported but their complete output was not retained in the task artifact
directory. No production or test behavior is to change unless the fresh
evidence exposes a verified discrepancy.

## Reconciled state

- The approved task, detailed design, required research, orchestration prompt,
  implementation plan, execution dashboard, previous code-assist artifacts,
  current diff, and Step 1 handoff were reviewed before work.
- The current scoped product diff is limited to the three approved Step 2 test
  suites. The GNOME helper already provides optional schema-1 diagnostics;
  protocol/version/capabilities and backend-owned interfaces remain unchanged.
- `overlay_client/follow_surface.py`, X11/XWayland compatibility, renderer
  selection, and payload processing are outside the diff and remain outside
  this remediation scope.
- The initial permitted staging attempt already failed because Git metadata is
  read-only. This remediation must not retry `git add` or `git commit`.

## Test type and validation

The approved changes are deterministic helper source-contract and Python unit
coverage; no `load.py`, lifecycle hook, or EDMC runtime wiring is touched, so a
harness test is not applicable. This context records complete logs for the
exact focused Step 2 pytest command, root `make check`, the overlay-client venv
alternate, and `git diff --check`.

## Constraints

Diagnostics are observational only. Matching helper-reported applied geometry
remains the readiness authority; retry, wrong-monitor classification,
persistent-mismatch backoff, and degradation/suppression must remain intact.
