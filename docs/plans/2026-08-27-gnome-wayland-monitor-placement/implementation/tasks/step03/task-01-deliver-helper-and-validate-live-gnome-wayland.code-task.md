# Task: Deliver Helper and Validate Live GNOME Wayland Handoff

## Description
Deploy the already-validated GNOME Shell helper change to the user's active
GNOME Wayland session and collect decisive live evidence that the overlay
follows Elite Dangerous across monitors without losing the existing safety,
input, focus, stacking, resize, or readback guarantees.

## Background
Steps 1 and 2 corrected the helper's normal path and proved its deterministic
readback and backend-boundary contracts. Real Mutter/session timing and the
user-visible interaction contract cannot be proven in this sandbox. This task
is therefore a functional manual-delivery gate, not a request for a new
implementation or a test-only task. A visually correct overlay is insufficient:
the helper-reported applied rectangle must also match the request within the
existing tolerance.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/existing-code-and-runtime-evidence.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/mutter-window-placement.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/orchestration-prompt.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Depend on Step 1 commit `fa94da3c76a4136fe7f034e45fa2fbc9a7c0d9cd` and
   Step 2 commit `fe35ac29ce96e1a17360fc1d298b1b657d730443`; do not alter their
   GNOME-helper, diagnostics, protocol/schema, or backend-boundary behavior.
2. Treat extension deployment, session-bus health/status, live application
   interaction, and every acceptance observation as manual-only. Before any
   such action, explain the exact command, target, and side effect, then get a
   separate explicit user approval after this task has been generated.
3. The approved deployment commands are:

   ```bash
   ./scripts/dev_gnome_helper.sh update
   ./scripts/dev_gnome_helper.sh status
   ```

   `update` clean-replaces the helper UUID directory, normally
   `/home/jon/.local/share/gnome-shell/extensions/edmc-modern-overlay-helper@edmcmodernoverlay.github.io`,
   with `helpers/gnome_shell_extension` and requests extension enablement.
   The script may resolve a different user-local base through its documented
   Snap or environment override logic and may require logout/login before the
   helper is active. `status` reads extension state and invokes the helper's
   session-bus health check. Neither command may be run by the agent.
4. Record only non-secret evidence: session type, GNOME Shell version, helper
   state, target and overlay monitor indexes, transfer action label, requested
   and applied rectangles, degrade reasons, bounded-retry result, and the
   observed interaction result. Do not record session-bus addresses,
   credentials, or unrelated user data.
5. Preserve scope: do not modify native X11, XWayland compatibility, renderer
   selection, payload processing, generic follow/runtime surfaces, backend
   selection/bundles, helper protocol/schema/versioning, diagnostics schema,
   GNOME settings, or strategy-probe/fullscreen behavior.
6. Do not compensate for a failed live result with sleeps, coordinate guesses,
   fullscreen workarounds, or cross-backend fallbacks. Record a live-only
   defect with its evidence and stop for user direction.
7. Re-run the deterministic regression command before recording a passing live
   result. Run `make check` again only if resolving a live finding changes code;
   otherwise retain and clearly report Step 2's documented environment limit.

## Dependencies
- Step 1's guarded monitor-transfer implementation and focused source-contract
  evidence in commit `fa94da3c76a4136fe7f034e45fa2fbc9a7c0d9cd`.
- Step 2's diagnostics/readback/boundary evidence in commit
  `fe35ac29ce96e1a17360fc1d298b1b657d730443`.
- A user-controlled active GNOME Wayland session with the helper, EDMC, Elite
  Dangerous, and the overlay available for manual observation.
- A separate explicit user approval for every live/session mutation or probe;
  generated-task approval alone grants no authority for those actions.

## Implementation Approach
1. Reconcile the two prerequisite commits and rerun the focused deterministic
   regression command without touching live-session resources.
2. Explain the `update` and `status` side effects and the target helper UUID
   directory, then wait for separate explicit user approval. The user, not the
   agent, performs the commands in the active GNOME Wayland session and shares
   only relevant non-secret status/diagnostic output.
3. After the helper is active, have the user exercise and document each live
   acceptance case. Fail closed when readback does not match, even if visual
   placement appears correct.
4. Record evidence, outcomes, known limitations, and the exact manual next
   action in the isolated code-assist artifacts and status dashboard. On a
   complete pass, inspect the scoped documentation diff and create the required
   conventional local evidence/documentation commit; on a defect, stop before
   changing code or committing a workaround.

## Acceptance Criteria

1. **Manual deployment remains separately authorized**
   - Given this generated task and a user-controlled GNOME Wayland session
   - When helper deployment or status is needed
   - Then the agent first explains the two exact commands, their user-local
     target directory, overwrite/enablement/session-bus side effects, and
     waits for a separate explicit user approval; it does not execute a live
     action itself

2. **Primary-target handoff has matching readback**
   - Given Elite is on the primary monitor and the overlay begins on the
     secondary monitor
   - When the user applies presentation through the active helper
   - Then the recorded target/pre/post monitor indexes show transfer to the
     primary monitor, the action label identifies the guarded transfer, and
     requested and applied rectangles match within the existing tolerance

3. **Secondary-target reverse handoff has matching readback**
   - Given Elite is on the secondary monitor and the overlay begins on the
     primary monitor
   - When the user applies presentation through the active helper
   - Then the recorded target/pre/post monitor indexes show transfer to the
     secondary monitor, the action label identifies the guarded transfer, and
     requested and applied rectangles match within the existing tolerance

4. **Repeated moves remain stable and co-location is a no-op**
   - Given Elite is moved repeatedly between monitors and a separate
     presentation begins with Elite and overlay already co-located
   - When the user observes the presentation cycles and diagnostics
   - Then no accumulated offset occurs, a retry occurs only under the existing
     bounded readback policy, and the co-located case records no unnecessary
     transfer action

5. **Interaction guarantees remain intact**
   - Given a matching-readback presentation across both handoff directions
   - When the user tests click-through, focus, stacking, and Elite resize
   - Then the overlay remains click-through, does not steal focus, stays above
     Elite, and follows resize without chrome or interaction regressions

6. **Failure remains fail-closed and no workaround is introduced**
   - Given any live case has mismatched helper readback, persistent
     wrong-monitor placement, unavailable transfer, or another live-only
     defect
   - When the evidence is reviewed
   - Then the result is recorded as failed/degraded, no sleep/coordinate/
     fullscreen/cross-backend workaround is added, and work stops for user
     direction before a code change

7. **Deterministic regression and evidence closure are complete**
   - Given all live matrix cases pass with matching readback
   - When the following command is run and the manual evidence is recorded
   - Then the regression suite passes, the status dashboard and handoff include
     all required non-secret evidence, and a conventional local evidence/
     documentation commit SHA is recorded without pushing

   ```bash
   PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
     overlay_client/tests/test_gnome_shell_helper_extension_source.py \
     overlay_client/tests/test_gnome_shell_helper_presentation_state.py \
     overlay_client/tests/test_gnome_helper_presentation_runtime.py \
     overlay_client/tests/test_backend_architecture_boundary.py -q
   ```

## Metadata
- **Complexity**: Medium
- **Labels**: GNOME Wayland, Manual Delivery, Live Validation, Monitor Placement, Regression
- **Required Skills**: GNOME Shell extension operations, Mutter Meta.Window diagnostics, manual Wayland testing, Python pytest, evidence review
- **Test Type**: Manual live GNOME Wayland integration/acceptance validation; rerun deterministic source-contract and unit regression coverage. No harness test is required because this task does not modify `load.py`, EDMC lifecycle/hooks, or runtime wiring.
