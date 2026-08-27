# Step 1 Task Plan: Guarded Normal-Path Monitor Transfer

## Checklist

- [x] Reconcile approved task, plan, design, research, status, Git state, and logs.
- [x] Select deterministic source-contract/unit-style tests; no harness test.
- [ ] RED: add source-contract expectations and run the focused test.
- [ ] GREEN: add the guarded normal-path transfer with fallback diagnostics.
- [ ] REFACTOR: review names, control flow, and unchanged helper boundaries.
- [ ] Validate focused pytest and `git diff --check`.
- [ ] Update task/status evidence and make the local conventional commit.

## Test scenarios

| Scenario | Source input/condition | Expected source contract |
| --- | --- | --- |
| Valid mismatch | Normalised target and pre-operation overlay monitor are non-negative and unequal | `move_to_monitor(targetMonitor)` occurs before the resize fallback; action records transfer-then-resize. |
| Co-located matching frame | Valid equal monitor indexes and frame matches tolerance | No transfer; matching-frame action remains the no-op. |
| Invalid monitor | Either normalisation returns `null` | No transfer; existing resize/readback branch remains reachable. |
| Unavailable transfer | Valid mismatch but method is not callable | Diagnostic/degrade condition is recorded and resize fallback remains reachable. |
| Throwing transfer | Valid mismatch and transfer throws | Error condition is recorded, resize fallback remains reachable, and readback mismatch remains the health gate. |
| Readback and probes | A normal presentation attempt | Post frame and monitor reads remain; strategy probe branch is unchanged and opt-in. |

## Implementation plan

Reuse `_normaliseMonitorIndex()` rather than introducing a new parser. Keep the
normal decision local to `_applyOverlayPresentation`: compute target/current
monitor values, attempt transfer only for a valid mismatch, then retain the
existing resize fallback chain. A transfer failure is scoped to that operation
so it cannot bypass resize or the later frame-readback gate. No operation return
value alone changes healthy status.

## Validation plan

Run the required focused command first, followed by `git diff --check` and a
scoped diff review. `make check` belongs to the next plan step's stated
broader gate and is not required by this approved helper-only task.
