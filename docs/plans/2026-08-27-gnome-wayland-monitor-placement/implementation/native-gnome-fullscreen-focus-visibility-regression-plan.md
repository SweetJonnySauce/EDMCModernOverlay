# Native GNOME Fullscreen Raster Focus-Visibility Regression: Implementation Plan

**Status:** In progress — Step 1 committed; Step 2 remains pending automated
project gates and user-gated live validation.

## Checklist

- [x] Step 1: Make the unchecked preference suppress unfocused native-GNOME fullscreen raster content.
- [ ] Step 2: Validate preference behavior and preserve native-GNOME presenter safety.

## Phase Status

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Restore the focus-visibility contract in the native GNOME bundle | Completed |
| 2 | Automated and live acceptance | Planned |

### Phase 1: Restore the focus-visibility contract in the native GNOME bundle

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Remove the fullscreen geometry exception that authorizes an unfocused Shell-raster target | Completed |
| 1.2 | Prove checked and unchecked preference behavior through the helper request/result contract | Completed — focused runtime, extension-source, and frame suites passed (152 tests). |

### Phase 2: Automated and live acceptance

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Run focused unit/source-contract coverage and the project gates | Planned |
| 2.2 | Verify focus-loss and focus-return behavior in a live GNOME Wayland session | Planned |

## Scope and diagnosis

The native `gnome_shell_wayland` fullscreen Shell-raster route currently computes
`allow_unfocused_target` as either the `keep_overlay_visible` preference **or**
a full-monitor fullscreen geometry match. The latter path makes the helper keep
rendering an unfocused Elite target even when the preference is unchecked.

This plan corrects only that authorization decision. It does not alter monitor
placement, Shell-raster eligibility, geometry, presenter ownership, click-through,
or the X11/xcompat backends.

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
