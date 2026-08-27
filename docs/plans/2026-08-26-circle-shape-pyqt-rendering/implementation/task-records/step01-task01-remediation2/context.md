# Step 01 Task 01 Remediation 2 Context

## Mode and scope

`code-assist` is running in auto mode for the final permitted fresh-context remediation of Step 1 Task 01. The sole scope is the collection failure in the plan-required `tests/test_legacy_processor.py` command. Production circle code, the approved plan, and the execution dashboard are out of scope.

## Restart reconciliation

- Governing artifacts were reread in the required order.
- The task artifact and prior Task 01 record show that circle helper behavior and its focused unit tests are already green.
- `git status --short` shows the prior helper and test changes plus untracked plan artifacts; `git diff --check` is clean.
- No validation-log files exist. The prior record captures the required-command collection failure.

## Failure analysis and correction boundary

`tests/test_legacy_processor.py` prepends `overlay_client/` to `sys.path` then imports `legacy_processor` as a top-level module. `legacy_processor` uses absolute `overlay_client.*` imports; Python consequently resolves the sibling `overlay_client/overlay_client.py` file instead of the `overlay_client` package. The repository root conftest already supplies the project root and related tests import `overlay_client.legacy_store` as a package.

The minimal correction is test-only: remove the conflicting path injection, import the processor/store through `overlay_client.*`, and qualify three monkeypatch target strings. This preserves the test's production module coverage and changes no runtime behavior.

## Test selection

Test type: **unit**. This is a pure test import-path correction; no lifecycle, `load.py`, socket, or EDMC runtime wiring is touched. No new test scenario is needed because the existing focused test is the failing coverage under repair.
