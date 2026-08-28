# Focus-Policy Remediation Progress

- [x] Reconciled the failed live acceptance and identified the policy bypass.
- [x] Recorded scope, invariants, dependency map, stages, and tests before code.
- [x] RED: capture the live client result and reproduce the missing neutral retained-content fact (`TypeError`: snapshot did not yet accept the field).
- [x] GREEN: add the GNOME-owned declaration and neutral runtime/consumer/policy transport.
- [x] REFACTOR: restored the unrelated managed-PyQt focus-unreliability branch and added a no-Qt-remap guard for retained content; no generic GNOME protocol dispatch was introduced.
- [x] Validate project gates and update the authoritative trackers (focused: 274 passed; external `make check` and `make test`: 1,696 passed each; Ruff/mypy clean).
- [x] RED → GREEN: reproduce the focused retained-actor remap warm-up, then treat the neutral retained actor as visible before the policy decision (targeted regression set: 4 passed).
- [x] Rerun focused and project gates for the focused remap-warm-up remediation (focused: 275 passed; external `make check` and `make test`: 1,697 passed each; Ruff/mypy clean; `git diff --check` passed).
- [x] Live acceptance: user verified the complete native-GNOME focus/monitor matrix after restarting EDMC; no helper reload/update was needed.
- [ ] Commit (requires explicit user approval; not authorized).

## Validation notes

- The same project targets outside the restricted sandbox passed all 1,696
  tests. `git diff --check` passed.
- The focused remap-warm-up remediation then passed the eight-file focused
  suite (275 passed) and, outside the socket-restricted sandbox, `make check`
  and `make test` each passed all 1,697 tests with Ruff and mypy clean.
- `python scripts/check_edmc_python.py` correctly reports the local Python
  3.12.3 64-bit environment is not the documented EDMC 3.13.9+ 32-bit runtime;
  this pure overlay-client policy change does not alter plugin-runtime code.
