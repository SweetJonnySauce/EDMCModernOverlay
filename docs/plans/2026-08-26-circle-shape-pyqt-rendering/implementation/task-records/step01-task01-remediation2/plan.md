# Step 01 Task 01 Remediation 2 Plan

## Acceptance target

The exact approved Step 1 command must collect and run the existing legacy processor unit tests through the real `overlay_client` package, without production code changes.

## Checklist

- [x] Reconcile prior task evidence and reproduce the collection failure once.
- [x] Establish that package-qualified imports are the repository convention.
- [x] Apply the minimum test-only import-path correction.
- [x] Run the repaired exact plan command.
- [x] Run the Step 1 combined command after the repaired command passed.
- [x] Review the scoped diff and record outcomes.

## Risks and mitigation

Removing the test-local path insertion could alter which module is tested. Package-qualified imports explicitly select the same production `overlay_client.legacy_processor` module used by the client and are already the project convention; the focused command verifies that coverage remains executable.
