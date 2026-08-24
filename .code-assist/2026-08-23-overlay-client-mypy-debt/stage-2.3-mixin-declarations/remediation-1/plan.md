# Stage 2.3 Remediation 1 Plan

## Test plan

| ID | Type | Command | Expected result |
| --- | --- | --- | --- |
| R1 | Static RED | Prescribed five-file focused mypy command before source edits | The 11 deferred renderer errors and two owned follow-surface diagnostics are recorded once. |
| R2 | Static GREEN | Identical command after exact type/local-name changes | Only the 11 deferred renderer diagnostics remain. |
| R3 | Regression | Prescribed offscreen setup/repaint/follow slice | Existing behavior passes unchanged. |

No tests will be added: both changes are type-local, and the runtime contract
will be read directly from its enforced producer/consumer structure.

## Implementation stages

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 2. Shared-state contract | 2.3.6 | Record remediation context and focused RED evidence | Completed — 11 deferred renderer diagnostics plus the two owned follow-surface diagnostics. |
| 2. Shared-state contract | 2.3.7 | State the enforced rect-member shape and separate the typed snapshot local | Completed — used the existing backend-owned preparation callback type and a distinct typed device-ratio local. |
| 2. Shared-state contract | 2.3.8 | Record focused GREEN, run offscreen slice, and review diff | Completed — focused result retains only 10 deferred renderer diagnostics; offscreen slice passed and diff check is clean. |
| 2. Shared-state contract | 2.3.9 | Leave exact six-field handoff | Completed |

Phase status: **Completed — remediation attempt 1 of 2 removed every owned Stage 2.3 diagnostic.**
