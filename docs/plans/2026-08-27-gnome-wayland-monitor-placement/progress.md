# Progress

| Phase | Goal | Status |
|---|---|---|
| 1 | Research and remediation design | Completed |
| 2 | Implementation and automated validation | Completed — elevated local project gates passed |
| 3 | Manual Wayland validation and merge closure | Completed for the Shell-raster replacement route; old monitor-transfer delivery was superseded |
| 4 | Native GNOME fullscreen focus-visibility regression | Closed as an unsafe direct-authorization approach — safety rollback is user-verified; the original checkbox requirement is a new-design follow-up. |
| 5 | Native GNOME Shell-raster content suppression | Completed — focused remap warm-up is corrected (275 focused tests; 1,697 project tests) and the user verified the complete live focus/monitor matrix. |

## Phase 1 stages

| Stage | Description | Status |
|---|---|---|
| 1.1 | Capture the live native-Wayland placement failure | Completed |
| 1.2 | Verify backend separation and merge scope | Completed |
| 1.3 | Research Mutter monitor-move semantics | Completed |
| 1.4 | Define the guarded remediation and validation strategy | Completed: detailed design drafted with GNOME-only move-then-resize, fail-closed readback, automated checks, and a live-session matrix. |
| 1.5 | Create the test-driven implementation plan | Completed: three incremental implementation steps cover the helper correction, contract/boundary validation, and live GNOME delivery. |
| 1.6 | Create the fresh-context execution orchestrator | Completed: orchestration prompt and status dashboard require a separate code-task-generator context per plan step and a separate code-assist context per generated task. |

## Phase 4 stages

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Document the preference-bypass diagnosis and test-first correction | Completed |
| 4.2 | Make unchecked `keep_overlay_visible` suppress unfocused native GNOME Shell-raster content | Superseded for safety — direct `allow_unfocused_target` control triggered actor suspension and black-screen regression; rollback restored fullscreen actor continuity. |
| 4.3 | Run automated gates and the live focus/placement acceptance matrix | Completed for rollback safety — project gates/focused tests passed and the user confirmed the black-screen regression is gone. Checkbox behavior is deferred. |

## Phase 5 stages

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Mark the direct authorization plan invalid and record the live regression lessons | Completed |
| 5.2 | Define the capability-gated renderer-content suppression design, implementation plan, and execution orchestration | Completed — ready for user-directed autonomous execution |
| 5.3 | Implement safe native GNOME Shell-raster content suppression | Completed for automated behavior — helper-supported retained Shell-raster content now remains eligible for neutral suppression despite no generic Qt attachment. |
| 5.4 | Run automated and live GNOME focus-transition acceptance | Completed — all automated gates passed and the user verified checkbox-off suppression after debounce, stable focus return, repeated cycles, and two-monitor placement. |
| 5.5 | Reconcile and restore the managed-surface policy hypothesis | Completed — live evidence showed that route was inactive; its existing behavior was restored. |
| 5.6 | Add retained Shell-raster availability to the neutral runtime result boundary | Completed — GNOME bundle declares it only for applied, matching, helper-supported raster content; generic Qt remains unmapped; focused suite: 274 passed; project gates: 1,696 passed. |
| 5.7 | Correct retained-actor visibility for generic remap warm-up policy | Completed — neutral retained-actor availability now supplies the policy visibility signal when generic Qt is intentionally unmapped; focused suite: 275 passed; project gates: 1,697 passed. |
