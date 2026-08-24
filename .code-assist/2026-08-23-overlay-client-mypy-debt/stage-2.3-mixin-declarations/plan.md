# Stage 2.3 Plan — Mixin Declaration Reconciliation

## Test plan

| ID | Type | Command/input | Expected result |
| --- | --- | --- | --- |
| S2.3-R | Static RED | Prescribed focused five-file mypy target before edits | Records the 19 inheritance conflicts and five in-scope residuals once. |
| S2.3-G | Static GREEN | Identical focused mypy target after declaration-only edits | No owned conflict/residual remains, without suppression. |
| S2.3-Q | Offscreen regression | Existing setup/repaint/follow three-file slice | Existing Qt paint, timer, cursor, and follow contracts pass unchanged. |

No tests are added because no runtime behavior is changed. Risk remaining after
static and regression proof is limited to incomplete static inventory; a new
family is a stop-and-review condition.

## Implementation plan

1. Save one focused RED result and map each diagnostic to an existing
   setup-owned contract, mixin declaration, or locally inferred value.
2. Apply only exact annotations/declaration reconciliation, retaining the
   current Qt MRO, constructors, assignment owners, and backend boundary.
3. Save one identical GREEN result; stop if an owned error requires behavioral
   movement or an imprecise type.
4. Run the prescribed offscreen regression slice, review the scoped diff, and
   leave the exact six-field handoff.

## Stage tracking

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 2. Shared-state contract | 2.3.1 | Read evidence and create stage-local records | Completed |
| 2. Shared-state contract | 2.3.2 | Capture focused static RED inventory | In progress |
| 2. Shared-state contract | 2.3.3 | Reconcile exact declarations/residual local types | Partially completed — 19 inheritance conflicts and 3/5 residuals removed; fresh remediation required for 2 residuals. |
| 2. Shared-state contract | 2.3.4 | Capture focused GREEN and offscreen regression proof | Completed — 12 focused errors remain: 11 deferred renderer errors and 2 Stage 2.3 residuals. |
| 2. Shared-state contract | 2.3.5 | Scoped review and exact six-field handoff | Completed — incomplete handoff for fresh remediation. |

Phase status: **In progress — one fresh remediation context is required.**
