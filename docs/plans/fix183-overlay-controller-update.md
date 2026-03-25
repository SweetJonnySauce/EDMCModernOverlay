## Goal: Remove overlay-controller hint text and hint-update plumbing, and move bottom controls into a dedicated widget

Follow persona details in `AGENTS.md`.
Document implementation results in the `Implementation Results` section.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear, capture it under `Open Questions`.

## Requirements (Initial)
- Remove the bottom contextual hint text from the Overlay Controller UI (both primary and secondary lines).
- Remove runtime hint update behavior so focus/navigation no longer computes or pushes contextual tip text.
- Add a dedicated bottom-controls widget that owns `Enabled` checkbox and `Reset` button.
- Keep the bottom control row functional: `Enabled` and `Reset` remain visible and interactive after moving into the new widget.
- Ensure the new widget participates in the normal sidebar widget focus cycle.
- Ensure the new widget follows the same navigation pattern as existing multi-control widgets (focus enter/exit handling, keyboard navigation paths, and binding-target exposure used by the focus manager).
- Preserve existing focus, selection, and placement behavior after hint removal.

## Out Of Scope (This Change)
- Any redesign of the Overlay Controller layout beyond removing hint text.
- Any behavior change to what `Enabled` and `Reset` do; this change only relocates ownership/rendering into a new widget.
- Changes to plugin-group logic, cache behavior, or CLI bridge protocol.

## Current Touch Points
- Code:
- `overlay_controller/controller/layout.py` (bottom-row composition now mounted via `GroupControlsWidget`)
- `overlay_controller/widgets/group_controls.py` (new widget owning `Enabled`/`Reset`)
- `overlay_controller/controller/focus_manager.py` (hint-update removal plus controls-widget focus/binding registration)
- `overlay_controller/overlay_controller.py` (layout wiring, controls enable-state handling, and call-site cleanup)
- `overlay_controller/controller/preview_controller.py` (call-site cleanup after hint removal)
- `overlay_controller/widgets/__init__.py` (widget export updates)
- `overlay_controller/input_bindings.py` and `overlay_controller/keybindings.json` (new controls-widget binding actions)
- Tests:
- `overlay_controller/tests/test_app_context.py` (sanity around setup context; verify no coupling to removed hints)
- `overlay_controller/tests/test_controller_groupings_loader.py` (controller-side behavior sanity)
- `overlay_controller/tests/test_focus_manager.py` (updated expectations for controls-widget binding registration)
- `overlay_controller/tests/test_group_controls_widget.py` (new widget focus/navigation behavior tests)
- Docs/notes:
- `docs/plans/fix183-overlay-controller-update.md`

## Assumptions
- The "hints" in scope are the contextual strings rendered by `SidebarTipHelper` in the bottom sidebar section.
- The new controls widget can be mounted in the current bottom-row area without changing controller semantics.

## Risks
- Removing hint hooks could accidentally break focus refresh paths if callers assume side effects.
- Mitigation: keep `refresh_widget_focus` and highlight logic intact; only remove hint-specific branches/calls.
- Moving controls into a new widget could break keyboard accessibility or focus transitions.
- Mitigation: mirror existing widget focus contract (`set_focus_request_callback`, `on_focus_enter/exit`, `handle_key`, and binding-target behavior where applicable) and validate with focused tests.
- Removing the tip widget / relocating controls may shift bottom-row geometry.
- Mitigation: preserve existing alignment routine and validate layout manually and with tests.

## Open Questions
- None currently.

## Decisions (Locked)
- Hint removal is behavioral, not cosmetic: no fallback default hint text should remain visible.
- `Enabled` and `Reset` controls remain in the bottom row after hint removal, but are owned/rendered by a dedicated widget.
- The new bottom-controls widget is part of the normal sidebar widget focus cycle.
- Keyboard behavior for `Enabled`/`Reset` matches existing multi-control widget navigation patterns.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Scope, contracts, and UI behavior definition | Completed |
| 2 | UI/layout changes and controls-widget extraction | Completed |
| 3 | Focus-manager, call-site, and accessibility wiring cleanup | Completed |
| 4 | Tests and validation | Completed |
| 5 | Docs/results and follow-up | Completed |
| 6 | Follow-up geometry fix: compact group-controls row height | Completed |
| 7 | Follow-up geometry fix: enforce minimum window height for controls visibility | Completed |

## Phase Details

### Phase 1: Scope and Contracts
- Lock exact hint-removal contract and no-regression targets.
- Risks: ambiguous definition of "hints" or unclear widget accessibility contract.
- Mitigations: explicitly map hint sources/update paths and lock widget accessibility contract before edits.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Identify all hint rendering/update touch points | Completed |
| 1.2 | Define new bottom-controls widget contract and alignment constraints | Completed |
| 1.3 | Define validation checklist for focus/navigation and accessibility parity | Completed |

#### Stage 1.1 Detailed Plan
- Objective:
- Create a complete inventory of hint-related code paths.
- Primary touch points:
- `overlay_controller/widgets/tips.py`
- `overlay_controller/controller/focus_manager.py`
- `overlay_controller/overlay_controller.py`
- `overlay_controller/controller/preview_controller.py`
- Steps:
- Trace all calls to `_update_contextual_tip` / `update_contextual_tip`.
- Trace where `tip_helper` is instantiated and rendered.
- Acceptance criteria:
- Every hint-rendering and hint-update path is listed in this plan.
- Verification to run:
- `rg -n "tip_helper|update_contextual_tip|_update_contextual_tip" overlay_controller`

#### Stage 1.2 Detailed Plan
- Objective:
- Lock expected bottom-row behavior with controls moved into a dedicated widget.
- Steps:
- Define the new widget API/ownership for `Enabled` and `Reset`.
- Define where this widget sits in the normal sidebar focus-cycle order.
- Keep `Enabled` and `Reset` controls in the current bottom section after extraction.
- Preserve existing alignment routine (`_align_group_controls_to_pick_button`).
- Acceptance criteria:
- Bottom controls remain visible and functional without hint text, are rendered by the new widget, and have an explicit focus-cycle position.
- Verification to run:
- Manual UI smoke check in Overlay Controller.

#### Stage 1.3 Detailed Plan
- Objective:
- Define no-regression baseline for focus/navigation/accessibility behavior.
- Steps:
- Keep highlight refresh and widget focus transitions untouched except hint calls.
- Require the new controls widget to follow existing widget accessibility rules (focus enter/exit behavior, keyboard handling paths, and focus-manager-visible binding targets where applicable).
- Require the new controls widget to participate in the normal sidebar widget focus cycle.
- Require keyboard behavior to mirror existing multi-control widget navigation patterns.
- Lock expected intra-widget key flow (`Enabled` <-> `Reset`) to match existing multi-control widget conventions.
- Record specific interactions to verify.
- Acceptance criteria:
- Sidebar/placement focus behavior remains unchanged, and controls remain reachable/operable via expected keyboard focus flows.
- Verification to run:
- `python -m pytest overlay_controller/tests -k "focus or controller or widget"`

#### Phase 1 Execution Order
- Implement in strict order: `1.1` -> `1.2` -> `1.3`.

#### Phase 1 Exit Criteria
- Hint contract is explicit and testable.
- Retained controls widget contract and no-regression behaviors are clearly defined.

#### Phase 1 Execution Plan (2026-03-21)
- Inventory all hint render/update call paths with static search.
- Inventory existing widget accessibility/focus contracts used by multi-control widgets.
- Lock the new controls-widget behavioral contract:
- in normal sidebar focus cycle,
- follows existing multi-control keyboard navigation patterns,
- preserves existing bottom-row alignment behavior.

#### Phase 1 Results
- Completed hint-path inventory across `layout.py`, `focus_manager.py`, `overlay_controller.py`, `preview_controller.py`, and widget exports.
- Completed focus-contract inventory across `absolute.py` and `background.py` (binding targets + next/prev field navigation) plus `set_focus_request_callback`/`on_focus_enter`/`on_focus_exit` patterns.
- Requirements and decisions are now explicit for:
- sidebar focus-cycle participation,
- multi-control intra-widget navigation parity,
- preserving existing control behavior while removing hints.

### Phase 2: UI/Layout and Controls Widget Extraction
- Remove hint rendering from the bottom row and extract `Enabled`/`Reset` into a dedicated widget.
- Risks: layout collapse, spacing regressions, or incorrect ownership wiring.
- Mitigations: preserve existing container geometry/alignment logic and move callbacks intact into the new widget seam.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Create dedicated bottom-controls widget for `Enabled`/`Reset` | Completed |
| 2.2 | Remove tip helper widget and integrate new controls widget in layout | Completed |
| 2.3 | Confirm bottom-row alignment and accessibility behavior | Completed |

#### Stage 2.1 Detailed Plan
- Objective:
- Introduce a dedicated widget that owns the `Enabled` checkbox and `Reset` button.
- Primary touch points:
- `overlay_controller/widgets/group_controls.py` (new)
- `overlay_controller/controller/layout.py`
- Steps:
- Implement widget construction and control ownership with current callbacks/state wiring preserved.
- Expose focus/accessibility hooks consistent with other widgets.
- Implement the same keyboard navigation contract used by existing multi-control widgets.
- Acceptance criteria:
- New widget renders `Enabled`/`Reset`, preserves current behavior, and is ready for sidebar focus-cycle participation.
- Verification to run:
- `python -m pytest overlay_controller/tests -k "controller or focus or widget"`

#### Stage 2.2 Detailed Plan
- Objective:
- Remove hint UI rendering and mount the new controls widget in the bottom row.
- Steps:
- Delete `SidebarTipHelper` usage and associated imports from layout wiring.
- Remove widget module if fully unused after extraction.
- Ensure layout return payload remains consistent for downstream focus wiring.
- Ensure layout/focus metadata places the new controls widget in the normal sidebar focus cycle.
- Acceptance criteria:
- No active code path depends on `SidebarTipHelper`, bottom controls are provided by the new widget, and no legacy standalone control wiring remains.
- Verification to run:
- `rg -n "SidebarTipHelper|tips.py" overlay_controller`

#### Stage 2.3 Detailed Plan
- Objective:
- Validate control geometry and accessibility behavior after extraction/removal.
- Steps:
- Verify `Enabled` and `Reset` placement logic still operates as expected.
- Verify focus entry/exit and keyboard navigation behavior for the new widget matches project widget norms.
- Validate sidebar traversal reaches the controls widget in normal sequence and intra-widget navigation matches existing multi-control widgets.
- Acceptance criteria:
- Controls remain right-aligned, interactive, and keyboard reachable in the bottom row.
- Verification to run:
- Manual Overlay Controller launch and interaction.

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.

#### Phase 2 Exit Criteria
- Hint text no longer appears in UI.
- Bottom-row controls are owned by the new widget and still behave/access correctly.

#### Phase 2 Execution Plan (2026-03-21)
- Add new widget module `overlay_controller/widgets/group_controls.py` that owns `Enabled` and `Reset`.
- Implement widget focus/accessibility contract to mirror existing multi-control widgets:
- `set_focus_request_callback`, `on_focus_enter`, `on_focus_exit`, `handle_key`,
- `get_binding_targets`, `focus_next_field`, `focus_previous_field`.
- Update `overlay_controller/controller/layout.py`:
- remove `SidebarTipHelper` usage,
- replace bottom-row manual checkbox/button creation with `GroupControlsWidget`,
- include the bottom controls section in normal sidebar selectable cycle.
- Update `overlay_controller/widgets/__init__.py` exports for new widget and remove tip-helper export.

#### Phase 2 Results
- Added `GroupControlsWidget` with owned `Enabled` and `Reset` controls, focus callbacks, and multi-control navigation methods.
- Updated layout builder to mount `GroupControlsWidget` in the bottom section and include it in selectable sidebar focus widgets.
- Removed `SidebarTipHelper` usage from layout and deleted `overlay_controller/widgets/tips.py`.
- Updated widget exports to include `GroupControlsWidget` and drop tip-helper exports.

### Phase 3: Focus/Call-Site and Accessibility Wiring Cleanup
- Remove hint update logic from focus and controller flows and ensure focus manager wiring for the new widget is correct.
- Risks: accidental disruption to focus refresh or keyboard traversal.
- Mitigations: only strip hint calls, preserve highlight/focus transitions, and wire the new widget through existing focus contracts.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Remove `update_contextual_tip` logic from FocusManager and align widget registration | Completed |
| 3.2 | Remove controller wrapper and direct tip update call sites | Completed |
| 3.3 | Verify no residual hint hooks and validate focus wiring completeness | Completed |

#### Stage 3.1 Detailed Plan
- Objective:
- Eliminate hint text computation/helper writes in focus manager and keep accessibility wiring coherent.
- Primary touch points:
- `overlay_controller/controller/focus_manager.py`
- Steps:
- Remove `update_contextual_tip` implementation and invocation from refresh path.
- Keep `update_sidebar_highlight` / `update_placement_focus_highlight` intact.
- Register/bind the new controls widget in the same manner expected for comparable widgets (as needed by current focus-manager contracts).
- Ensure focus-manager traversal includes the new widget in normal sidebar cycle order.
- Acceptance criteria:
- Focus refresh still executes without attempting hint updates, and controls widget focus behavior remains accessible.
- Verification to run:
- `python -m pytest overlay_controller/tests/test_focus_manager.py`

#### Stage 3.2 Detailed Plan
- Objective:
- Remove wrapper/call sites that only exist for hints.
- Steps:
- Remove `_update_contextual_tip` wrapper and any remaining direct calls.
- Update preview/controller code that currently triggers tip refresh explicitly.
- Acceptance criteria:
- No runtime calls attempt to update contextual hints.
- Verification to run:
- `rg -n "_update_contextual_tip|update_contextual_tip" overlay_controller`

#### Stage 3.3 Detailed Plan
- Objective:
- Validate end-to-end cleanup completeness and focus wiring coverage.
- Steps:
- Perform static search for hint-related identifiers and dead imports.
- Confirm no missing focus callback/binding target links for the new controls widget.
- Confirm no gaps in sidebar focus-cycle registration/order after controls extraction.
- Acceptance criteria:
- Only intentional references to "tip"/"hint" remain (non-contextual, unrelated usages), and the new controls widget is fully integrated in focus traversal paths with expected multi-control key navigation behavior.
- Verification to run:
- `rg -n "tip_helper|SidebarTipHelper|contextual tip|Handy tips" overlay_controller`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3`.

#### Phase 3 Exit Criteria
- Hint update plumbing is removed.
- Focus, selection, and keyboard accessibility flows still function.

#### Phase 3 Execution Plan (2026-03-21)
- Remove contextual-tip refresh methods and invocations from focus manager/controller/preview controller.
- Extend focus manager binding registration to include the new controls widget.
- Add controls-widget action bindings in defaults/config so next/prev field navigation matches existing multi-control widgets.
- Verify no residual hint identifiers remain under `overlay_controller/`.

#### Phase 3 Results
- Removed `update_contextual_tip` from `FocusManager` and removed tip refresh from `refresh_widget_focus`.
- Removed `_update_contextual_tip` wrapper/callers from `overlay_controller.py` and `preview_controller.py`.
- Added `group_controls_focus_next` / `group_controls_focus_prev` actions in `FocusManager`, `input_bindings.py`, and `keybindings.json`.
- Verified no remaining hint plumbing references in `overlay_controller/` via static search.

### Phase 4: Tests and Validation
- Add/update tests and run targeted controller checks.
- Risks: missing UI-level regressions in headless tests.
- Mitigations: combine targeted tests with manual controller smoke check, including controls widget accessibility flow.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Update/add tests impacted by hint removal and controls-widget extraction | Completed |
| 4.2 | Run targeted controller test suite | Completed |
| 4.3 | Run full project check as milestone validation | Completed |

#### Stage 4.1 Detailed Plan
- Objective:
- Ensure tests reflect hint-free controller behavior and accessible controls widget integration.
- Steps:
- Update focus manager/controller tests that depended on hint helper behavior.
- Add assertion coverage for absence of hint wiring if needed.
- Add/update assertions that `Enabled`/`Reset` controls remain reachable and operable through expected focus/keyboard flows.
- Add/update assertions that the controls widget participates in normal sidebar focus traversal order.
- Add/update assertions that intra-widget navigation matches existing multi-control widget behavior.
- Acceptance criteria:
- Tests assert intended behavior post-removal and post-extraction.
- Verification to run:
- `python -m pytest overlay_controller/tests -k "focus or controller or widget"`

#### Stage 4.2 Detailed Plan
- Objective:
- Validate controller package behavior.
- Steps:
- Run full `overlay_controller/tests` suite.
- Acceptance criteria:
- Controller tests pass without regressions.
- Verification to run:
- `python -m pytest overlay_controller/tests`

#### Stage 4.3 Detailed Plan
- Objective:
- Confirm broader plugin/client/controller integrity.
- Steps:
- Run repo check targets.
- Acceptance criteria:
- Lint/typecheck/tests complete successfully or failures are documented.
- Verification to run:
- `make check`

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- Relevant tests pass.
- No unexpected regressions introduced by hint removal and controls-widget extraction.

#### Phase 4 Execution Plan (2026-03-21)
- Update focus-manager test coverage to assert controls-widget binding registration.
- Add dedicated controls-widget tests for focus targets, keyboard navigation, activation, and disabled-state behavior.
- Run focused controller/widget pytest filters, then full controller tests, then `make check`.

#### Phase 4 Results
- Updated `overlay_controller/tests/test_focus_manager.py` to validate controls-widget next/prev binding actions.
- Added `overlay_controller/tests/test_group_controls_widget.py`.
- Test execution results:
- `python3 -m pytest overlay_controller/tests -k "focus or controller or widget"` -> 46 passed, 11 skipped.
- `python3 -m pytest overlay_controller/tests/test_focus_manager.py` -> 1 passed.
- `python3 -m pytest overlay_controller/tests` -> 46 passed, 11 skipped.
- `make check` -> ruff pass, mypy pass, full pytest pass (547 passed, 29 skipped).

### Phase 5: Docs, Results, and Follow-up
- Record implementation outcomes and cleanup notes.
- Risks: undocumented behavior change for users/devs.
- Mitigations: summarize final behavior in plan results.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Record implementation results and test evidence | Completed |
| 5.2 | Capture residual risks and follow-up items | Completed |
| 5.3 | Final review and phase completion updates | Completed |

#### Stage 5.1 Detailed Plan
- Objective:
- Populate the `Implementation Results` section with concrete outcomes.
- Steps:
- List touched files, behavior changes, and test commands/results.
- Acceptance criteria:
- Results section is complete and auditable.
- Verification to run:
- N/A (documentation update)

#### Stage 5.2 Detailed Plan
- Objective:
- Capture any deferred work.
- Steps:
- Document optional layout simplifications or cleanup left out of scope.
- Acceptance criteria:
- Follow-up list is explicit and scoped.
- Verification to run:
- N/A

#### Stage 5.3 Detailed Plan
- Objective:
- Finalize plan status bookkeeping.
- Steps:
- Mark completed stages/phases accordingly.
- Acceptance criteria:
- Stage/phase tables accurately reflect completion state.
- Verification to run:
- N/A

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
- Implementation outcomes are documented.
- Plan is ready for closeout/reference.

#### Phase 5 Execution Plan (2026-03-21)
- Update plan status tables for all completed phases/stages.
- Record exact touched files, behavior changes, and executed tests.
- Capture residual risks and any deferred manual verification.

#### Phase 5 Results
- Phase/stage statuses updated to `Completed` across the plan.
- Implementation and test evidence documented in this file.
- Residual risk: manual visual smoke-check of bottom-row geometry/focus highlight in live controller UI is still recommended because this environment is headless.

### Phase 6: Follow-up Geometry Fix (Compact Controls Row Height)
- Reduce the group-controls frame height to content so the selected frame does not consume extra vertical space.
- Risks: changing row expansion may alter sidebar stretching behavior.
- Mitigations: move stretch responsibility to a dedicated spacer row and keep focus-cycle/order unchanged.

| Stage | Description | Status |
| --- | --- | --- |
| 6.1 | Define compact-height contract and touch points | Completed |
| 6.2 | Update layout row expansion to avoid stretching controls widget | Completed |
| 6.3 | Run targeted regression tests and record results | Completed |

#### Stage 6.1 Detailed Plan
- Objective:
- Lock behavior for the follow-up UI fix.
- Steps:
- Keep `GroupControlsWidget` content and behavior unchanged.
- Remove forced expansion from the bottom controls row so frame height follows child controls.
- Preserve sidebar focus order and binding targets.
- Acceptance criteria:
- Bottom controls frame wraps the controls row height instead of expanding to fill remaining sidebar space.
- Verification to run:
- Manual controller visual check in display session.

#### Stage 6.2 Detailed Plan
- Objective:
- Apply layout changes that prevent oversized controls frame.
- Primary touch points:
- `overlay_controller/controller/layout.py`
- Steps:
- Remove fixed-height/non-propagating settings for the group-controls row.
- Stop assigning the grow-weight to the controls row.
- Add a trailing spacer grid row with grow-weight to absorb free vertical space.
- Acceptance criteria:
- Controls row remains compact while sidebar still expands to fill available height.
- Verification to run:
- `python3 -m pytest overlay_controller/tests/test_group_controls_widget.py`
- `python3 -m pytest overlay_controller/tests/test_focus_manager.py`

#### Stage 6.3 Detailed Plan
- Objective:
- Validate no behavior regression from geometry update.
- Steps:
- Run focused tests for controls widget and focus wiring.
- Document results under `Implementation Results`.
- Acceptance criteria:
- Targeted tests pass.
- Verification to run:
- `python3 -m pytest overlay_controller/tests -k "group_controls or focus_manager"`

#### Phase 6 Execution Order
- Implement in strict order: `6.1` -> `6.2` -> `6.3`.

#### Phase 6 Exit Criteria
- Group-controls frame height is content-sized.
- Focus/navigation behaviors remain unchanged.

#### Phase 6 Execution Plan (2026-03-21)
- Patch layout so the controls row no longer expands.
- Keep behavior scoped to geometry only.
- Run focused tests for controls and focus-manager wiring.

#### Phase 6 Results
- Updated `overlay_controller/controller/layout.py` so the group-controls row no longer forces fixed height or expansion.
- Removed grow-weight from selectable rows and added a trailing spacer row to absorb extra sidebar height.
- Focus wiring and controls widget behavior remain unchanged; only geometry behavior changed.
- Focused test execution results:
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_group_controls_widget.py` -> `4 skipped` (headless Tk guard in this environment).
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_focus_manager.py` -> `1 passed`.
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests -k "group_controls or focus_manager"` -> `1 passed`, `4 skipped`, `52 deselected`.

### Phase 7: Follow-up Geometry Fix (Minimum Height Enforcement)
- Prevent shrinking the controller window vertically to a size that clips/hides the bottom controls.
- Risks: over-constraining height could feel rigid on smaller displays.
- Mitigations: derive min-height from current required layout height with `base_min_height` as floor.

| Stage | Description | Status |
| --- | --- | --- |
| 7.1 | Define min-height contract and touch points | Completed |
| 7.2 | Implement dynamic minimum-height resolution in placement-state logic | Completed |
| 7.3 | Run targeted regression tests and record results | Completed |

#### Stage 7.1 Detailed Plan
- Objective:
- Lock the behavior contract for vertical sizing.
- Steps:
- Keep existing width-toggle behavior unchanged.
- Ensure min-height follows required UI height so the bottom controls remain visible.
- Keep `base_min_height` as fallback floor.
- Acceptance criteria:
- User cannot resize window height below the height needed to show sidebar controls.
- Verification to run:
- Manual controller resize check in display session.

#### Stage 7.2 Detailed Plan
- Objective:
- Apply scoped min-height enforcement without changing control behavior.
- Primary touch points:
- `overlay_controller/overlay_controller.py`
- Steps:
- Add helper to resolve effective min-height from `winfo_reqheight()` with `base_min_height` floor.
- Use resolved min-height in `_apply_placement_state` when setting `minsize` and target height.
- Acceptance criteria:
- Both open/collapsed placement states enforce effective min-height.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_focus_manager.py`
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_app_context.py`

#### Stage 7.3 Detailed Plan
- Objective:
- Validate no regressions from min-height change.
- Steps:
- Run focused tests that cover controller context/focus wiring.
- Document results in `Implementation Results`.
- Acceptance criteria:
- Targeted tests pass.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests -k "focus_manager or app_context"`

#### Phase 7 Execution Order
- Implement in strict order: `7.1` -> `7.2` -> `7.3`.

#### Phase 7 Exit Criteria
- Vertical resize floor preserves visibility of bottom controls.
- Focus/navigation behavior remains unchanged.

#### Phase 7 Execution Plan (2026-03-21)
- Add a dynamic min-height resolver to `OverlayConfigApp`.
- Apply the resolved min-height in `_apply_placement_state` for open and collapsed modes.
- Run targeted non-GUI-heavy tests and record results.

#### Phase 7 Results
- Added `_resolve_min_window_height()` in `overlay_controller/overlay_controller.py` to derive effective min-height from `winfo_reqheight()` with `base_min_height` as floor.
- Updated `_apply_placement_state()` to apply the effective min-height to both open/collapsed `minsize(...)` calls and current-height clamping.
- Focused test execution results:
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_focus_manager.py overlay_controller/tests/test_app_context.py` -> `2 passed`.
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests -k "focus_manager or app_context"` -> `2 passed`, `55 deselected`.

## Tests To Run (Per Iteration)
- `python3 -m pytest overlay_controller/tests -k "focus or controller or widget"`
- `python3 -m pytest overlay_controller/tests/test_focus_manager.py`
- `python3 -m pytest overlay_controller/tests`
- `make check`

## Implementation Results
- Completed phases: `1`, `2`, `3`, `4`, `5`, `6`, `7`.
- Touched files:
- `overlay_controller/widgets/group_controls.py` (new)
- `overlay_controller/controller/layout.py`
- `overlay_controller/controller/focus_manager.py`
- `overlay_controller/overlay_controller.py`
- `overlay_controller/controller/preview_controller.py`
- `overlay_controller/widgets/__init__.py`
- `overlay_controller/input_bindings.py`
- `overlay_controller/keybindings.json`
- `overlay_controller/tests/test_focus_manager.py`
- `overlay_controller/tests/test_group_controls_widget.py` (new)
- `overlay_controller/widgets/tips.py` (deleted)
- `docs/plans/fix183-overlay-controller-update.md`
- Behavioral outcome:
- Bottom hint text and hint-update plumbing removed from overlay-controller runtime.
- `Enabled` checkbox and `Reset` button now live in a dedicated `GroupControlsWidget`.
- New controls widget is part of normal sidebar focus cycle and follows multi-control navigation patterns.
- Group-controls frame now sizes to control content height; excess sidebar height is assigned to a non-selectable spacer row.
- Controller minimum height now follows required layout height, preventing vertical resize that would hide bottom controls.
- Verification summary:
- `python3 -m pytest overlay_controller/tests -k "focus or controller or widget"` passed (`46 passed`, `11 skipped`).
- `python3 -m pytest overlay_controller/tests/test_focus_manager.py` passed (`1 passed`).
- `python3 -m pytest overlay_controller/tests` passed (`46 passed`, `11 skipped`).
- `make check` passed (`ruff`, `mypy`, full pytest with `547 passed`, `29 skipped`).
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_group_controls_widget.py` passed with headless skips (`4 skipped`).
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_focus_manager.py` passed (`1 passed`).
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests -k "group_controls or focus_manager"` passed (`1 passed`, `4 skipped`, `52 deselected`).
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_focus_manager.py overlay_controller/tests/test_app_context.py` passed (`2 passed`).
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests -k "focus_manager or app_context"` passed (`2 passed`, `55 deselected`).
- Follow-up:
- Run a live manual controller UI smoke check to validate visual alignment/highlight behavior in a real display session.
