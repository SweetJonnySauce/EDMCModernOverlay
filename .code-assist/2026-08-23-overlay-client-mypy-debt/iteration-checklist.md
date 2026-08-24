# Iteration Checklist — Overlay Client Mypy Debt

**Iteration:** 2026-08-23 coordinator review  
**Scope:** type-cleanup goal only; no production implementation in this iteration.

## Result

**Hold at Stage 3.1 pending runtime verification.** Its complete source change set was
user-directed rolled back after a runtime symptom report. The full directory target remains
intentionally red, including the deferred TTL contract.

## Phase and stage status

| Phase | Stage | Status | Evidence / next action |
| --- | --- | --- | --- |
| 1. Baseline | 2.1 | Completed | Frozen `python -m mypy overlay_client` baseline: 203 errors in 27 files. |
| 2. Shared state | 2.2 | Completed | Annotation-only `OverlayWindowState` contract; targeted errors improved 53 → 5; 55 offscreen tests passed. |
| 2. Shared state | 2.3 | Completed | Residual shared-state declarations resolved in a fresh remediation context; 55 offscreen tests passed. |
| 3. Pure data | 3.1 | Open — fully rolled back | Runtime symptom was reported after the fresh remediation; all Stage 3.1 source edits were removed without asserting causality. Normal scoped mypy is again 20 errors. |
| 3. Renderer | 3.2 | Pending | Do not begin until the user verifies the rollback at runtime. |
| 3. Integration | 3.3 | Pending | Must explicitly own the remaining `control_surface.py:1101` directory-target diagnostic or amend the plan. |
| 4. Enforcement | 4.1–4.3 | Pending | Client directory target is 113 errors in 21 files; do not add it to default mypy yet. |

## Independent validation

| Check | Result | Interpretation |
| --- | --- | --- |
| `python -m mypy --follow-imports=skip` on Stage 3.1's six source files | **Fail:** 5 errors in 2 files | Four `follow_geometry.py` assignment errors and the TTL ingress diagnostic remain. |
| Normal `python -m mypy` on those same six source files | **Fail:** 20 errors in 6 files | This is the restored pre-Stage-3.1 state after the complete user-directed rollback. |
| `python -m pytest` prescribed Stage 3.1 pure-unit slice | **Pass:** 90 passed | Existing behavior is retained for geometry, anchors, transforms, payload dedupe, and override grouping. |
| Ruff on Stage 3.1 source files | **Pass** | No lint issue in the bounded source edits. |
| `python -m mypy overlay_client` | **Fail:** 113 errors in 21 files | Improved from the frozen 203 errors in 27 files, but far from the directory-wide acceptance criterion. |
| `git diff --check` | **Pass** | No whitespace error in the current dirty worktree. |

## Boundary and process review

| Check | Result | Notes |
| --- | --- | --- |
| Isolated Code Assist contexts and six-field handoffs | Pass through Stage 3.1 | Stage records exist for 2.1, 2.2, 2.3 (+ one remediation), and 3.1. |
| Type-only shared-state approach | Pass | `OverlayWindowState` is a `Protocol`; consumers use `TYPE_CHECKING` imports and string casts. Qt MRO/init order was not moved. |
| X11 clear-first repair | Not revalidated in this iteration | It is out of Stage 3.1's source scope; prior focused Qt evidence remains recorded. Re-run its offscreen tests after any relevant client-surface change. |
| fix219 compositor boundary | No issue observed | The reviewed type-contract and pure-data paths add no compositor/backend imports or raw enum dispatch. |
| Blanket suppression / broad `Any` | No new use observed in reviewed stages | Existing narrow ignores remain elsewhere; no new suppression should be introduced. |
| Top-level execution dashboard accuracy | Corrected | It previously said a new family required review and implied all remediation needed user direction. Neither follows the evidence. |

## Next action

Verify the rollback in the affected runtime. Do not open Stage 3.2 or repeat the Stage 3.1
remediation until the user confirms whether the symptom is gone. Preserve the unresolved
`payload_model.py:98` TTL diagnostic; it needs a user-approved runtime input-contract decision
and test-first evidence before it may change.
