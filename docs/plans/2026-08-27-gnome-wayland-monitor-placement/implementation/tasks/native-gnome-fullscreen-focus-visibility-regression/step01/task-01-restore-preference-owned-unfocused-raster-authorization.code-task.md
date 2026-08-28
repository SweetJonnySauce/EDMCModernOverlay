# Task: Restore Preference-Owned Unfocused Shell-Raster Authorization

## Description
Restore the advertised `keep_overlay_visible` contract for the native
`gnome_shell_wayland` fullscreen Shell-raster route. An unfocused target may
receive `allow_unfocused_target=True` only when the user has explicitly enabled
that preference. Remove the obsolete full-monitor fullscreen geometry exception
that currently bypasses the unchecked preference, while preserving the helper's
existing focus-risk suspension path.

## Background
The native GNOME bundle owns the compositor-specific presentation cycle behind
the fix219 backend boundary. It currently derives the outgoing raster-frame
authorization from `keep_overlay_visible` **or** a fullscreen/full-monitor
geometry helper. The second condition keeps the GNOME Shell actor visible after
Elite loses focus despite the preference being unchecked. The helper protocol
already treats an unfocused target with `allow_unfocused_target=False` as
`target_not_focused`, clears/suspends the actor, suppresses managed-PyQt
fallback, and returns a focus-risk result. This task must restore that existing
protocol behavior; it must not redesign it.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-fullscreen-focus-visibility-regression-plan.md` (authoritative Step 1 scope and acceptance)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/fullscreen-shell-raster-routing.md` (required routing design; read it even though this task narrows its focus behavior)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-plan.md` (existing presenter, transition, and fix219 constraints)
- `AGENTS.md` (backend boundary and required test-type policy)

**Note:** You MUST read the detailed design document and the routing design
before beginning implementation. The existing native GNOME Shell-raster route,
not generic follow/runtime code, owns this policy.

## Technical Requirements
1. In `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`, make `keep_overlay_visible` the sole authorization forwarded as `ShellRasterFrameRequest.allow_unfocused_target` for every Shell-raster request.
2. Remove `_shell_raster_runtime_allows_unfocused_fullscreen_target` and all now-dead call-site/geometry-only coverage; do not replace it with another fullscreen, monitor, rectangle, target-state, or focus-reliability bypass.
3. Preserve the existing helper request/result protocol for the unchecked, unfocused native-GNOME fullscreen case: outgoing `allow_unfocused_target=False`, `target_not_focused` classifies as focus-risk suspension, managed-PyQt fallback remains suppressed, and `should_show_overlay` is false.
4. Preserve the explicit opt-in: with an otherwise identical unfocused target and `keep_overlay_visible=True`, forward `allow_unfocused_target=True` and retain normal raster presentation.
5. Do not change fullscreen eligibility, geometry, raster frame-provider selection, presenter ownership, transition ordering, overview handling, target-loss behavior, diagnostics/helper schema, click-through, monitor placement, or native X11/xcompat behavior.
6. Preserve fix219: do not add compositor imports, raw backend/helper enum dispatch, or GNOME/raster policy to generic follow/runtime/consumer code. Keep the correction inside the backend-owned GNOME bundle.
7. Explicitly select unit tests. This is deterministic bundle-owned request policy with injected helper inputs; it does not modify `load.py`, EDMC startup/shutdown, hooks, or lifecycle wiring, so a harness test is not required.

## Dependencies
- The active selected-native GNOME Shell-raster runtime and its existing `_shell_raster_bridge_request` request transport.
- The helper's established `target_not_focused` focus-risk suppression result and fail-closed managed-PyQt behavior.
- Existing focused coverage in `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, `overlay_client/tests/test_gnome_shell_helper_extension_source.py`, and `overlay_client/tests/test_shell_raster_frame.py`.

## Implementation Approach
1. Start RED by replacing the obsolete selected-fullscreen focus-unreliability expectation with the unchecked preference contract: use a full-monitor fullscreen unfocused target, assert the frame request flag is false, and return/verify the existing `target_not_focused` focus-risk suspension result.
2. Retain or strengthen the inverse explicit-preference test so the same unfocused target with `keep_overlay_visible=True` sends the flag as true and can present.
3. Make the smallest GREEN source change: pass `keep_overlay_visible` directly to the Shell-raster bridge and delete the obsolete fullscreen geometry authorization helper.
4. REFACTOR only test names/fixtures needed to make user-preference authorization clear. Review the scoped diff for removal of the stale exception, unchanged focused/windowed/overview/target-loss/transition coverage, and no fix219 boundary leakage.

## Acceptance Criteria

1. **Unchecked Preference Suspends an Unfocused Fullscreen Raster Actor**
   - Given a healthy selected native-GNOME fullscreen/full-monitor target whose helper state has `hasFocus=False` and `keep_overlay_visible=False`
   - When the backend-owned Shell-raster presentation cycle builds and sends its frame request
   - Then the outgoing `allow_unfocused_target` is false, the helper `target_not_focused` response is classified as focus-risk suspension, managed-PyQt remains suppressed, and `should_show_overlay` is false

2. **Checked Preference Is the Explicit Unfocused Override**
   - Given the otherwise identical healthy selected native-GNOME unfocused fullscreen/full-monitor target and `keep_overlay_visible=True`
   - When the Shell-raster presentation cycle sends its frame request
   - Then `allow_unfocused_target` is true and the existing successful raster presentation result remains available without changing helper protocol semantics

3. **Obsolete Fullscreen Geometry Authorization Is Removed**
   - Given the native GNOME helper-presentation source and its focused runtime coverage
   - When the focus authorization implementation is inspected and its unit tests run
   - Then `_shell_raster_runtime_allows_unfocused_fullscreen_target` and its selected-fullscreen exception coverage are absent, and no fullscreen/full-monitor geometry condition can set `allow_unfocused_target` true while the preference is false

4. **Existing Presenter and Backend Contracts Remain Unchanged**
   - Given focused fullscreen, windowed managed-PyQt, overview, target-loss, and presenter-transition cases plus native X11/xcompat boundary coverage
   - When the scoped regression tests execute after the change
   - Then their existing behavior remains unchanged, the helper extension source contract remains green, and generic follow/runtime/consumer code gains no compositor-specific imports or raw backend/helper enum dispatch

5. **Unit-Test Evidence Is Recorded**
   - Given this pure backend-bundle policy correction and its updated unit tests
   - When running `source overlay_client/.venv/bin/activate && PYQT_TESTS=1 python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_shell_raster_frame.py -q` followed by `git diff --check`
   - Then both commands pass, the changed tests and exact results are recorded, and no lifecycle harness is required because `load.py` and EDMC lifecycle wiring are untouched

## Metadata
- **Complexity**: Low
- **Labels**: GNOME Wayland, Shell Raster, Focus Visibility, Regression, fix219, Unit Tests
- **Required Skills**: Python backend policy, GNOME helper presentation, pytest, source-contract testing
