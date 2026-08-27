# Plan

## Test type

Deterministic Python unit and source-contract tests. No harness test: the
change does not touch `load.py`, plugin startup, or EDMC hooks.

## RED → GREEN → REFACTOR

- [x] RED: add source-contract assertions for the normal optional diagnostic
  evidence and default omission; add state/runtime tests proving diagnostics
  are observational while readback controls readiness.
- [x] GREEN: make the smallest production correction only if RED exposes a
  missing contract.
- [x] REFACTOR: review changed code and tests for local style and scope.
- [x] Validate focused pytest, `make check`, and `git diff --check`.
- [x] Record scope review, results, and commit state in the handoff.

## Acceptance mapping

| Requirement | Evidence |
| --- | --- |
| Optional normal diagnostics retain action, target/pre/post monitor, requested/applied evidence | Helper source-contract test plus diagnostic payload assertions |
| No schema expansion | Scoped diff review and source contract against the existing conditional payload |
| Readback is authoritative | Presentation-state mismatch test and runtime transient-lag test |
| Persistent wrong-monitor behavior survives | Existing runtime wrong-monitor/backoff regression test rerun unchanged |
| Backend ownership survives | Existing architecture-boundary test rerun unchanged |
