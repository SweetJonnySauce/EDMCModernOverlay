# Step 4 Fake-Runner Contract Remediation: Plan

## Acceptance criteria

- [x] Reproduce the fake runner's unexpected-keyword failure.
- [x] Extend only that fake runner to accept and capture `content_visibility`.
- [x] Assert the default request carries neutral `VISIBLE` intent.
- [x] Run the exact test, scoped consumer/boundary tests, Ruff, and diff check.
- [x] Record the sandbox loopback limitation without rerunning project gates.

## TDD scenarios

| Scenario | Input | Expected result |
| --- | --- | --- |
| Stale runner (RED) | Native GNOME cycle calls fake runner | `TypeError` for missing `content_visibility` keyword. |
| Updated runner (GREEN) | Default native GNOME cycle | Fake runner records `BackendPresentationContentVisibility.VISIBLE`; existing result assertions remain true. |
| Boundary regression | Consumer and architecture tests | Generic code remains backend-neutral and suite passes. |

## Implementation

1. Add a keyword-only, typed `content_visibility` parameter with a visible
   default to the single fake runner.
2. Append the received intent to the existing call record and assert it.
3. Re-run scoped validation. No production implementation is involved.
