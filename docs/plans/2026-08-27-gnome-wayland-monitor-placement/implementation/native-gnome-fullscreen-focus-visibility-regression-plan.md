# Native GNOME Fullscreen Raster Focus-Visibility Regression: Implementation Plan

**Status:** Safety rollback implemented — the direct unchecked-preference
authorization was unsafe and has been restored to the prior fullscreen
actor-continuity behavior. The checkbox behavior remains unresolved; do not
treat this historical plan as authority for another direct authorization change.

## Checklist

- [x] Step 1: Attempt the unchecked-preference actor suppression and record its live black-screen regression.
- [x] Safety rollback: Restore the prior fullscreen Shell-raster actor-continuity authorization.
- [ ] Follow-up design: Define safe renderer-level content suppression that preserves actor continuity.
- [ ] Live rollback check: Verify the black screen is gone without claiming unchecked-preference hiding.

## Phase Status

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Restore the focus-visibility contract in the native GNOME bundle | Superseded — direct preference-to-actor authorization is unsafe; safety rollback is complete |
| 2 | Automated and live acceptance | Blocked — rollback needs user verification, then a new content-suppression design |

### Phase 1: Restore the focus-visibility contract in the native GNOME bundle

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Remove the fullscreen geometry exception that authorizes an unfocused Shell-raster target | Superseded — removal activated unsafe actor suspension; rollback restored the exception as an actor-continuity guard |
| 1.2 | Prove checked and unchecked preference behavior through the helper request/result contract | Failed live acceptance — unit coverage modeled the helper response but not compositor focus-return safety |

### Phase 2: Automated and live acceptance

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Run focused unit/source-contract coverage and the project gates | Completed — focused suite: 152 passed; elevated `make check` and `make test`: Ruff/mypy clean and 1,675 tests passed each. The ordinary sandbox run was blocked only by five loopback-socket fixture setups. |
| 2.2 | Verify focus-loss and focus-return behavior in a live GNOME Wayland session | Failed — user observed a black screen on click/focus return after the Step 1 change |

## Scope and diagnosis

Before Step 1, the native `gnome_shell_wayland` fullscreen Shell-raster route
computed `allow_unfocused_target` as either the `keep_overlay_visible`
preference **or** a full-monitor fullscreen geometry match. That latter path
made the helper keep rendering an unfocused Elite target even when the
preference was unchecked. Step 1 removed the geometry exception; this plan now
records the remaining validation work.

This plan corrects only that authorization decision. It does not alter monitor
placement, Shell-raster eligibility, geometry, presenter ownership, click-through,
or the X11/xcompat backends.

## Live regression addendum (2026-08-28)

The Step 1 implementation proved that sending `allow_unfocused_target=False`
causes the helper to classify an unfocused fullscreen target as
`target_not_focused`. The extension then calls
`_clearShellRasterFrame('target_not_focused')`, whose transient path suspends
(hides) the compositor-owned raster actors. In the affected live fullscreen
session, clicking/focusing away from and back to Elite produces a black screen.

This establishes that `allow_unfocused_target` is not merely a user-content
visibility preference. It is also a fullscreen Shell-actor continuity/safety
control. The preceding fullscreen geometry exception was an over-broad way to
preserve that continuity, but replacing it with the preference directly is not
safe either.

Do not apply further direct authorization changes. The next remediation must
first restore the previously stable actor-continuity behavior, then separately
design and validate a renderer-level content-suppression mechanism that does
not hide/detach the Shell raster actor during a normal focus transition. That
mechanism needs new helper/actor contract coverage and live validation before
it replaces the stable fallback.

## Safety rollback addendum (2026-08-28)

The approved emergency rollback restored the pre-`8ef91cd` native fullscreen
full-monitor authorization: an eligible active fullscreen Shell-raster target
may retain `allow_unfocused_target=True` while focus is transiently elsewhere.
This preserves the compositor-owned actor across focus return and is covered by
a focused unit regression test. It deliberately leaves the checkbox ineffective
for that eligible fullscreen route. A future change must use a renderer-level
content-suppression contract that does not clear, hide, or detach the actor;
it requires a new approved design and live GNOME validation.

## Step 1: Make the unchecked preference suppress unfocused native-GNOME fullscreen raster content

**Objective:** Ensure `keep_overlay_visible` is the only reason a native GNOME
Shell-raster frame may be presented while Elite is unfocused.

**Implementation guidance:**

- In `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`,
  remove the fullscreen/full-monitor geometry exception from the calculation
  that supplies `ShellRasterFrameRequest.allow_unfocused_target`.
- Pass `keep_overlay_visible` directly as that authorization flag for every
  Shell-raster request. Do not change the native-GNOME runtime profile,
  fullscreen eligibility, or frame-provider selection.
- Remove the now-unused
  `_shell_raster_runtime_allows_unfocused_fullscreen_target` helper and its
  geometry-only tests. Its purpose conflicts with the user-visible preference.
- Retain the existing helper behavior for an unfocused target with
  `allow_unfocused_target=False`: it suspends/hides the Shell actor with
  `target_not_focused`. This keeps the compositor-owned actor from remaining
  visible; changing only the generic PyQt content policy is insufficient.
- Keep this policy backend-owned. Do not introduce raw GNOME/raster enum
  dispatch or compositor imports into generic follow/runtime code.

**Test requirements:**

- Replace the current selected-fullscreen test that expects
  `allow_unfocused_target=True` with an unfocused, full-monitor native-GNOME
  case where `keep_overlay_visible=False`; assert the outgoing frame flag is
  `False`, the helper's `target_not_focused` response is classified as a
  focus-risk suspension, and `should_show_overlay` is false.
- Add or strengthen the inverse case: an otherwise identical unfocused target
  with `keep_overlay_visible=True` sends `allow_unfocused_target=True` and can
  present the raster frame.
- Retain focused fullscreen, windowed managed-PyQt, overview, target-loss, and
  presenter-transition regression coverage. They must remain behaviorally
  unchanged.
- Run:

  ```bash
  source overlay_client/.venv/bin/activate
  PYQT_TESTS=1 python -m pytest \
    overlay_client/tests/test_gnome_helper_presentation_runtime.py \
    overlay_client/tests/test_gnome_shell_helper_extension_source.py \
    overlay_client/tests/test_shell_raster_frame.py -q
  ```

**Integration:** The existing GNOME helper protocol already understands the
flag and hides a non-authorized unfocused actor. This step restores the
preference-to-protocol connection without changing the protocol or extension
implementation.

**Demo:** With a full-monitor fullscreen Elite target whose helper state says
`hasFocus:false`, the outgoing raster request has
`allow_unfocused_target:false` when the preference is unchecked. The extension
suspends the actor; checking the preference permits it again.

## Step 2: Validate preference behavior and preserve native-GNOME presenter safety

**Objective:** Prove the corrected policy works in the affected live session
and does not regress placement, focus safety, or other backends.

**Implementation guidance:**

- Run the focused automated suite before deploying/reloading the extension.
- In the live GNOME Wayland session, test a normal focus transition rather
  than querying helper state from the terminal alone: focus Elite, move focus
  to another application, wait for the follow poll/debounce cycle, then return
  focus to Elite.
- Capture presentation diagnostics for the unfocused interval. Require
  `target.hasFocus:false`, `allow_unfocused_target:false`, and a
  `target_not_focused`/suspended raster result when the preference is
  unchecked. When checked, require `allow_unfocused_target:true` and normal
  raster presentation.
- Re-run the two-monitor fullscreen placement smoke case after the focus
  cases. The actor must still be on Elite's monitor and remain non-reactive;
  this change must not revive managed-PyQt monitor movement.

**Test requirements:**

```bash
source overlay_client/.venv/bin/activate
make check
make test
```

If GUI/live dependencies or the session prevent a command from running,
record the exact command, environmental reason, and remaining risk instead of
claiming acceptance.

Manual matrix:

| Preference | Elite focus | Required result |
| --- | --- | --- |
| Unchecked | Focused | Shell raster presents normally on Elite's monitor |
| Unchecked | Lost | Shell actor is suspended/hidden after the normal refresh cycle; no stale content remains visible |
| Unchecked | Regained | Shell raster resumes on Elite's monitor without focus theft |
| Checked | Lost | Shell raster remains visible by explicit user choice |
| Either | Fullscreen target moves monitor | Placement remains with Elite; no duplicate PyQt surface appears |

**Integration:** This validates the existing native GNOME route only. X11 and
xcompat have no runtime behavior change; their backend-boundary coverage must
remain green.

**Demo:** The affected user can toggle the checkbox and observe exactly the
documented difference while Elite is unfocused, without changing fullscreen
monitor placement.

## Completion criteria

- The unchecked preference produces `allow_unfocused_target:false` for an
  unfocused fullscreen native-GNOME Shell-raster target.
- The checked preference remains the explicit opt-in that produces `true`.
- The helper suspends/clears the raster actor on ordinary focus loss rather
  than relying on generic PyQt-label suppression.
- Focused fullscreen placement, windowed managed PyQt, target-loss, and
  presenter-transition tests remain green.
- Focused tests, `make check`, `make test`, and the live matrix have recorded
  results.
