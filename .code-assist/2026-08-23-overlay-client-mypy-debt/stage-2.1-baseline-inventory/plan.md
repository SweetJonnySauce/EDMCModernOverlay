# Stage 2.1 Plan — Freeze and Classify the RED Baseline

## Test selection

| Proof | Type | Input | Expected result |
| --- | --- | --- | --- |
| B1 | Mypy RED baseline | Unchanged `overlay_client` directory | One saved raw checker result, nonzero or zero exit status recorded exactly. |
| B2 | Inventory review | Every B1 diagnostic | Exactly one approved family per reported error, or an explicit new-family stop. |

No unit or harness tests are added: this stage makes no runtime, helper, or
`load.py` change. The residual risk is limited to correctly classifying static
diagnostics; raw output remains available for coordinator review.

## Implementation checklist

- [x] Reconcile governing records, worktree state, prior handoff, dashboard, and
  stage-local artifacts.
- [x] Create stage-local context, plan, progress, and log directory before the
  validation command.
- [x] Run the single required directory-wide mypy command and preserve raw output
  plus its exit status.
- [x] Map all diagnostics to the approved taxonomy and check for a new family.
- [x] Record the outcome and leave the exact six-field handoff for review.

## Risks and controls

- Existing dirty work is preserved through stage-local documentation-only edits.
- The baseline command is not retried, even if it fails, because that failure is
  the required RED evidence.
- No source/configuration change can reduce the baseline in this stage.

## Result

The command exited `1` with 203 errors in 27 files. `inventory.md` maps each
error record to an approved family; no fifth family was found. The 88-error
increase over the earlier import-closure count is a directory-wide test and
integration inventory expansion, not an implementation change or suppression.
