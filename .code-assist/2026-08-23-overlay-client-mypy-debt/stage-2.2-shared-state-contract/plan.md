# Stage 2.2 Plan — Annotation-Only Shared-State Contract

## Test selection

| ID | Type | Input | Expected result |
| --- | --- | --- | --- |
| S2.2-R | Static RED | Unchanged four-file narrow mypy target | Existing shared-state diagnostics are saved once. |
| S2.2-G | Static GREEN | Same target after type-only contract | Targeted indeterminate shared-state diagnostics improve without suppression; Stage 2.3 conflicts may remain. |
| S2.2-Q | Offscreen regression | Setup, repaint-debounce, follow-surface tests | Existing Qt paint and follow behavior passes unchanged. |

No unit or harness test is added: no runtime behavior, pure helper, `load.py`,
or lifecycle wiring changes. Residual risk is limited to static contract
accuracy and is bounded by mypy plus the existing offscreen regression slice.

## Implementation plan

1. Record one prescribed narrow mypy RED result and inspect only its
   shared-state diagnostics and the setup-owned assignments they reference.
2. Add one type-only state declaration, then apply narrow consumer annotation
   seams without changing inheritance, constructors, assignments, or behavior.
3. Run the same narrow command once for the GREEN delta; stop if it exposes an
   out-of-family error or requires scope expansion.
4. Run the prescribed offscreen regression slice once, review the scoped diff,
   and leave the required six-field handoff.

## Stage tracking

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 2. Shared-state contract | 2.2.1 | Reconcile scope and create stage-local records | Completed |
| 2. Shared-state contract | 2.2.2 | Capture prescribed narrow RED evidence | Completed — 53 shared-state errors |
| 2. Shared-state contract | 2.2.3 | Add contract and annotation-only consuming seams | Completed |
| 2. Shared-state contract | 2.2.4 | Compare GREEN evidence and run offscreen regression | Completed — 48-error mypy improvement; 55 tests passed |
| 2. Shared-state contract | 2.2.5 | Review scope and hand off | Completed |

Phase status: **Completed.**
