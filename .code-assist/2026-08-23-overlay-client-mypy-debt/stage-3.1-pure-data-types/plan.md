# Stage 3.1 Plan — Pure Data Type Corrections

## Test plan

| ID | Type | Input | Expected result |
| --- | --- | --- | --- |
| 3.1-R | Static RED | Prescribed six-module focused mypy target before edits | Records only frozen pure-data diagnostics, including the TTL boundary. |
| 3.1-G | Static GREEN | Identical target after source-proven annotations | Removes proven diagnostics without suppression; unresolved TTL is retained if its coercion contract is not statically proven. |
| 3.1-U | Unit regression | Prescribed five-file pure-unit slice | Existing geometry, anchor, transform, dedupe/TTL, and override behavior passes unchanged. |

No new test is planned because no runtime change is authorized. If a helper
behavior change becomes necessary, this context must stop for coordinator
review before adding a unit RED/GREEN cycle.

## Implementation plan

1. Capture the one required focused mypy RED result and compare each owned
   line with its source assignments and existing unit-test contract.
2. Apply only exact local/container annotations proven by source. Independently
   trace payload TTL producers and consumers; retain its error if direct
   `int()` coercion cannot be represented precisely without changing behavior.
3. Run the identical focused command once for the GREEN delta, followed once
   by the required pure-unit regression slice.
4. Inspect the bounded diff for behavior/boundary preservation and leave the
   required six-field handoff.

## Stage tracking

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 3. Pure data and renderer corrections | 3.1.1 | Reconcile evidence and create stage-local records | Completed |
| 3. Pure data and renderer corrections | 3.1.2 | Capture one focused static RED result | Completed — 16 diagnostics in 4 files; no out-of-family error appeared. |
| 3. Pure data and renderer corrections | 3.1.3 | Apply source-proven pure-data annotations | Partially completed — 11 errors removed; four clamp-branch geometry annotations require a fresh context because this context's GREEN measurement is consumed. |
| 3. Pure data and renderer corrections | 3.1.4 | Capture GREEN and run pure-unit regression | Completed — focused result improved 16 to 5; 90 selected unit tests passed. |
| 3. Pure data and renderer corrections | 3.1.5 | Review bounded diff and leave handoff | Completed — `git diff --check` passed; bounded diff remains annotation-only and backend-neutral. |

Phase 3 status: **In progress — Stage 3.1 is incomplete and requires coordinator review plus a fresh remediation context.**
