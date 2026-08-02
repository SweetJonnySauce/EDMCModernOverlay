# Task 04 Plan: Quiet Measurement State

## Stage Tracking

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Establish context, inventory, and test selection | Completed |
| 4.2 | Back up and quiet client/helper diagnostic configuration | Completed |
| 4.3 | Reload helper and verify effective quiet state | Completed |
| 4.4 | Run bounded stable journal observation | Completed |
| 4.5 | Verify evidence immutability and synchronize records | Completed |

Phase 4 status: **Completed**

## Expected Unchanged Behavior

- Full helper functionality and current backend selection remain enabled.
- Repaint debounce remains enabled.
- Visual output, focus, click-through, cold-start remap, one-shot refresh, recovery, and Phase 19
  behavior are not changed.
- Existing historical captures, manifests, and evidence identities are untouched.

## Validation Scenarios

1. **Configuration preservation**
   - Input: current repository settings and helper JSON.
   - Output: only diagnostic gates change; all unrelated fields compare equal.
2. **Recoverable helper edit**
   - Input: existing helper JSON and absent fixed backup.
   - Output: a mode/ownership-preserving backup exists before the quiet file is installed.
3. **Effective helper state**
   - Input: helper reload after `diagnostics=false`.
   - Output: helper remains enabled and healthy in full-helper mode with diagnostics disabled.
4. **Quiet stable observation**
   - Input: bounded journal interval during stable normal use.
   - Output: zero high-frequency `target_query_started` and per-repaint diagnostic events.
5. **Historical evidence preservation**
   - Input: pre/post hashes for 12 reduced-v2 and two superseded captures.
   - Output: counts and hashes remain identical; no new identity or threshold file exists.

## Execution Plan

1. Validate JSON and record only allowlisted configuration facts.
2. Create a non-overwriting user-local helper backup.
3. Apply the smallest quiet-state edits with unrelated fields preserved.
4. Reload the GNOME extension and verify effective feature-gate/health state.
5. Restart or otherwise verify the client has consumed quiet settings if a live client exists.
6. Observe a bounded stable interval and count only named diagnostic event types.
7. Recheck evidence hashes and repository scope, then update status records.

## Validation Commands

- Parse and compare the three JSON configurations with allowlisted fields only.
- Query GNOME extension enabled state and helper health after reload.
- Use a bounded `journalctl --user` interval filtered only for named high-frequency events.
- Recalculate SHA-256 hashes for historical JSON captures.
- Run `git diff --check` and a scoped `git status` review.

## Commit Decision

The authoritative Step 03 plan defers the reviewed Step 03 commit to Stage 3.16. Task 04 therefore
records its completed increment but does not commit or push independently.
