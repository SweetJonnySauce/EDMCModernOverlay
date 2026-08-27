# Research plan

| Phase | Goal | Status |
|---|---|---|
| 1 | Establish runtime symptom and local code ownership | Completed |
| 2 | Verify Mutter monitor-move semantics from primary documentation | Completed |
| 3 | Define a testable, low-risk native-Wayland correction | Completed |
| 4 | Validate the design and prepare an implementation plan | Completed: implementation plan drafted; awaiting implementation approval |

## Phase 3 stages

| Stage | Description | Status |
|---|---|---|
| 3.1 | Specify the guarded monitor-transfer decision and invariants | Completed in the detailed design. |
| 3.2 | Identify unit, helper-contract, and live validation evidence | Completed in the detailed design. |
| 3.3 | Evaluate non-production alternatives and rollback behavior | Completed: retain the fail-closed gate and existing helper feature-mode escape hatch; do not promote diagnostic probes. |

## Questions still requiring a live validation environment

- Does the actual helper's `move_to_monitor(target)` produce the target
  `get_monitor()` immediately, or only by the next presentation cycle?
- Does the move followed by resize retain click-through, stacking, and
  non-focus-stealing behavior in this GNOME/Mutter version?
- Does the reverse handoff remain correct when Elite moves from the primary to
  the secondary display?
