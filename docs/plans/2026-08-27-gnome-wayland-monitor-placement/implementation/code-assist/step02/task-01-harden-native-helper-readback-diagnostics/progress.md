# Progress

## Setup

- [x] Reconciled the approved task, Step 1 evidence, plan/dashboard, working
  tree, helper source, and existing deterministic tests.
- [x] Selected deterministic source-contract/unit tests; no lifecycle harness
  is warranted because `load.py` and EDMC hooks are untouched.

## TDD record

- [x] RED: Added source-contract, presentation-state, and runtime coverage.
  The new contract passed immediately because Step 1 already retained the
  required helper diagnostics; this task therefore makes no production change.
- [x] GREEN: The existing implementation satisfied the new contract without a
  helper-side correction.
- [x] REFACTOR: Kept the tests compact and reused the established helper
  diagnostics shape; no cleanup change was necessary.
- [x] Validation: Focused command passed 156 tests and `git diff --check`
  passed. Root `make check` is limited by a missing root-interpreter Ruff;
  the venv alternate passed Ruff and mypy but its full pytest leg had five
  unrelated loopback-socket harness setup errors after 1,641 passed and 21
  skipped.

## Evidence correction

- [x] The initial attempt correctly reported its validation outcomes but did
  not retain complete command output under its artifact directory. Fresh
  remediation context `task-01-harden-native-helper-readback-diagnostics-remediation-01`
  now owns the required logs; this does not change the implementation or its
  blocked-local-commit state.

## Decisions

- Reuse the established `include_presentation_diagnostics` request flag and
  `presentation_diagnostics` result field; do not introduce a new schema,
  selector, or production branch.
- Treat helper diagnostics as evidence only. The existing applied-rectangle
  validation remains the readiness authority.
- The scoped product diff contains only the three established test suites; the
  helper source, protocol/schema, generic follow surface, backend interfaces,
  X11/XWayland, renderer, and payload processing remain unchanged.
