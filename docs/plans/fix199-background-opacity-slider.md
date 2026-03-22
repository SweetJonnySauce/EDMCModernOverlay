## Goal: Add a background-opacity slider to `BackgroundWidget` that synchronizes alpha for background and border colors

Follow persona details in `AGENTS.md`.
Document implementation results in the `Implementation Results` section.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear, capture it under `Open Questions`.

## Requirements (Initial)
- Add an opacity slider in the background widget row, positioned to the right of the `Border (px)` spin box.
- Slider range and direction are fixed: `0%` on the left and `100%` on the right.
- `0%` means fully transparent (`alpha=0x00`), and `100%` means fully visible (`alpha=0xFF`).
- Changing the slider updates the alpha channel for both `backgroundColor` and `backgroundBorderColor` on slider release/commit.
- Show the current slider percentage on or near the slider.
- If `backgroundColor` is `None`, slider changes are allowed but do not change `backgroundColor`.
- If `backgroundBorderColor` is `None`, slider changes are allowed but do not change `backgroundBorderColor`.
- Once a color is set for either field, current slider value is automatically applied to that field's alpha.
- If the user manually edits alpha in either color entry, the slider updates to match that alpha.
- If border alpha differs from background alpha, slider feedback/authority comes from `backgroundColor`.
- If border alpha differs from background alpha and the user moves the slider, both alphas become the slider value.
- If one color entry is invalid while the other is valid, slider updates still apply to the valid color.
- `Left`/`Right` arrow navigation can move focus onto the slider from adjacent fields.
- When slider is the active field, `Left`/`Right` arrows adjust slider value (do not move focus away).
- While slider is active, focus exits slider only on `Space`, `Return`/`KP_Enter`, or `Up`/`Down` arrows.
- Slider step size is `1%` per keyboard increment/decrement.
- While slider is active, keyboard `Left`/`Right` value changes commit on slider exit (not per keypress).
- After slider exit without leaving slider focus, `Left`/`Right` revert to normal horizontal navigation and can move focus off slider.
- On slider exit via `Space`/`Enter`, focus stays on slider (exit mode changes, not focus target).
- During mouse drag, the percentage display updates live; color alpha commit still occurs on release/commit.

## Out Of Scope (This Change)
- Any redesign of unrelated controller widgets or sidebar navigation behavior.
- Any change to non-background opacity systems (for example global payload opacity preferences).
- Any change to border-width behavior beyond layout space needed for the new slider.

## Current Touch Points
- Code:
- `overlay_controller/widgets/background.py` (slider UI, alpha sync, keyboard/focus behavior)
- `overlay_controller/overlay_controller.py` (background change callback compatibility)
- `overlay_plugin/overlay_api.py` (retained color token compatibility)
- Tests:
- `overlay_controller/tests/test_background_widget.py`
- `overlay_controller/tests/test_focus_manager.py`
- `overlay_controller/tests/test_app_context.py`
- Docs/notes:
- `docs/plans/fix199-background-opacity-slider.md`

## Assumptions
- Alpha-bearing color tokens use `#AARRGGBB` format in controller entries.
- When a color token has no explicit alpha (`#RRGGBB`), effective alpha for slider feedback defaults to `100%` until user sets slider or explicit alpha.
- If both colors are `None`, slider displays `100%` initially.
- Percent-to-alpha mapping uses rounding semantics (`50% -> 0x80`).
- Slider retains its last percent value even when both colors are `None`; that remembered value is applied when a color is later set.

## Risks
- Bidirectional synchronization (entry edit <-> slider move) can create callback loops.
- Mitigation: guard programmatic updates and only commit on explicit release/exit.
- Invalid text in one field could block updates to the valid sibling.
- Mitigation: keep invalid text/highlight untouched and update only valid sibling value on slider commit.
- Added control could regress focus behavior.
- Mitigation: keep explicit active-field keyboard mode and cover with tests.

## Open Questions
- None currently.

## Decisions (Locked)
- Slider is the canonical UI control for opacity percentage in `BackgroundWidget`.
- Background alpha is the source of truth for slider feedback whenever background and border alpha differ.
- Slider edits unify both alphas to a single value when both colors are present.
- `None` colors remain `None` when moving slider; slider does not auto-create missing colors.
- Named colors are converted to explicit `#AARRGGBB` when slider alpha is applied.
- Slider writes are commit-based (mouse release/commit), not continuous drag updates.
- Color picker selections immediately get current slider alpha applied.
- If background has no explicit alpha and border does, slider feedback still uses background (`100%`) per precedence rule.
- Alpha-bearing outputs are normalized uppercase `#AARRGGBB`.
- If one color field is invalid and the other valid, slider still updates the valid one.
- Background widget remains a multi-control widget and slider keyboard handling follows an explicit active-field rule.
- While slider is active, horizontal arrows are value-adjustment keys; `Space`/`Enter`/`Up`/`Down` are explicit exit keys.
- `Up` exits to previous field and `Down` exits to next field.
- Slider keyboard increments/decrements use `1%` steps.
- Slider keyboard edits commit on exit keys rather than per arrow press.
- Slider keeps remembered percentage state even when both colors are `None`.
- After an exit event while still focused on slider, `Left`/`Right` return to navigation semantics.
- `Space`/`Enter` exits slider-adjust mode while keeping focus on slider.
- Mouse drag updates displayed percent continuously, with color writes committed on release.
- If one color field is invalid, its text/highlight is preserved while valid sibling still updates.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Contract lock: alpha precedence, commit rules, and keyboard interaction model | Completed |
| 2 | Widget implementation: slider UI, percent display, and commit-on-release behavior | Completed |
| 3 | Integration wiring: controller persistence, normalization, and focus-cycle parity | Completed |
| 4 | Validation: targeted tests for sync, keyboard mode, and regression safety | Completed |
| 5 | Documentation closeout and follow-up tracking | Completed |

## Phase Details

### Phase 1: Scope and Contracts
- Lock exact behavior for slider placement, alpha semantics, and precedence rules.
- Risks: ambiguous handling for missing alpha or named colors.
- Mitigations: define canonical alpha-derivation and write acceptance checks before code edits.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Confirm touch points and current alpha behavior in widget/controller callbacks | Completed |
| 1.2 | Lock slider/color synchronization contract (precedence, `None`, conversion, commit timing) | Completed |
| 1.3 | Lock multi-control keyboard contract and no-regression checklist | Completed |

#### Phase 1 Execution Plan (2026-03-21)
- Inventory all alpha-related paths in widget/controller write flow.
- Freeze slider precedence/commit/`None`/invalid-field contract.
- Freeze keyboard mode semantics for slider active vs exited states.

#### Phase 1 Results
- Requirement contract finalized and locked in this document.
- Open questions reduced to `None`.
- Keyboard behavior for slider entry/adjust/exit fully specified before implementation.

### Phase 2: Widget UI and Behavior Implementation
- Add slider UI and implement alpha synchronization in `BackgroundWidget`.
- Risks: layout crowding and callback recursion.
- Mitigations: guard programmatic updates and keep UI changes scoped to the existing border row.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add slider UI to border row with live percentage display | Completed |
| 2.2 | Implement commit-on-release alpha application with `None`/invalid-field handling | Completed |
| 2.3 | Implement bidirectional alpha sync (entry/picker -> slider and mismatch resolution) | Completed |

#### Phase 2 Execution Plan (2026-03-21)
- Add slider + percent label to `Border (px)` row in `BackgroundWidget`.
- Add slider state (`remembered`, `pending commit`, `active adjust mode`) and helper functions.
- Implement slider commit-on-release and keyboard-adjust/exit behavior.
- Implement alpha application helpers to enforce uppercase `#AARRGGBB` output and named-color conversion.

#### Phase 2 Results
- Added `tk.Scale` slider and live `%` label.
- Implemented slider active/exit keyboard mode:
- `Left/Right` adjust while active; `Space/Enter/Up/Down` exit adjust mode.
- Post-exit `Left/Right` restores navigation semantics.
- Implemented commit behavior:
- mouse drag updates label live;
- color alpha writes commit on release/exit.
- Implemented color application rules:
- slider applies alpha to both valid colors on commit,
- `None` fields remain `None`,
- invalid sibling text/highlight preserved while valid sibling updates.

### Phase 3: Controller Wiring and Integration
- Ensure background widget + controller integration preserves persisted values and live preview behavior.
- Risks: unintended write storms or stale UI state after group switch.
- Mitigations: reuse existing change callback path and add change-delta guards where needed.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Wire `set_values`/group selection to slider state, including remembered value behavior | Completed |
| 3.2 | Verify persistence path normalizes/stores `#AARRGGBB` values after slider edits | Completed |
| 3.3 | Ensure sidebar focus-cycle and slider active/exit keyboard modes are regression-safe | Completed |

#### Phase 3 Execution Plan (2026-03-21)
- Integrate slider state with `set_values` loading path.
- Preserve existing callback signature while applying slider-driven alpha normalization.
- Ensure focus manager target exposure includes slider control.

#### Phase 3 Results
- `set_values` now syncs slider feedback state with loaded background/border values.
- Change callback payloads remain `color, border_color, border_width` and continue routing through `_handle_background_changed`.
- Slider added to binding targets and integrated into widget traversal without changing controller callback API.

### Phase 4: Tests and Validation
- Add focused tests for slider behavior and run targeted suites.
- Risks: Tk/headless environment may skip widget tests.
- Mitigations: record skips clearly and include manual UI verification steps.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Add/update widget tests for full slider contract (sync, precedence, keyboard) | Completed |
| 4.2 | Run targeted background/focus/controller integration tests | Completed |
| 4.3 | Run milestone checks and capture outcomes with skips/failures documented | Completed |

#### Phase 4 Execution Plan (2026-03-21)
- Update/extend `test_background_widget.py` for picker alpha + slider mode behaviors.
- Run focused background/focus tests.
- Run milestone `make check`.

#### Phase 4 Results
- Updated `test_background_widget.py` with new cases for:
- picker applying current slider alpha,
- manual background alpha syncing slider,
- invalid-sibling slider commit behavior,
- slider exit-mode keyboard behavior.
- Commands executed:
- `overlay_client/.venv/bin/python -m ruff check overlay_controller/widgets/background.py overlay_controller/tests/test_background_widget.py`
- `overlay_client/.venv/bin/python -m mypy overlay_controller/widgets/background.py`
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_background_widget.py overlay_controller/tests/test_focus_manager.py`
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests -k "background_widget or focus_manager or app_context"`
- `make check`
- Results:
- focused widget tests skipped in this headless environment (`Tk root unavailable`);
- non-widget targeted tests passed;
- full project milestone checks passed.

### Phase 5: Docs, Results, and Follow-up
- Finalize documentation and capture residual risks.
- Risks: behavior details drift from implementation reality.
- Mitigations: keep results tied to exact files/commands and update stage/phase statuses consistently.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Record implementation results and test evidence | Completed |
| 5.2 | Capture residual risks and deferred UX/cleanup follow-ups | Completed |
| 5.3 | Final phase/stage bookkeeping and closeout consistency check | Completed |

#### Phase 5 Execution Plan (2026-03-21)
- Update all phase/stage statuses.
- Record implementation outputs and test evidence.
- Capture remaining risks/skips.

#### Phase 5 Results
- All phase/stage statuses set to `Completed`.
- Implementation and validation evidence captured below.
- Residual risk recorded for headless-only widget skips.

## Test Plan (Per Iteration)
- Env setup (once per machine):
- `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- Headless quick pass:
- `source .venv/bin/activate && python -m pytest`
- Targeted tests:
- `source .venv/bin/activate && python -m pytest overlay_controller/tests/test_background_widget.py -k "opacity or alpha or slider"`
- `source .venv/bin/activate && python -m pytest overlay_controller/tests -k "background_widget or focus_manager or app_context"`
- Milestone checks:
- `make check`
- `make test`
- Compliance baseline check (release/compliance work):
- `python scripts/check_edmc_python.py`

## Implementation Results
- Plan created on 2026-03-21 and implemented in this run.
- Completed phases: `1`, `2`, `3`, `4`, `5`.
- Touched files:
- `overlay_controller/widgets/background.py`
- `overlay_controller/tests/test_background_widget.py`
- `docs/plans/fix199-background-opacity-slider.md`
- Behavioral outcome:
- Added opacity slider to the right of `Border (px)` with live `%` label.
- Slider semantics implemented:
- `0%` transparent / `100%` visible,
- mouse drag updates label live, commit on release,
- keyboard adjust mode on slider (`Left/Right`), explicit exits (`Space/Enter/Up/Down`),
- post-exit `Left/Right` restores navigation behavior.
- Alpha synchronization implemented:
- slider applies alpha to both valid colors on commit,
- `None` fields remain unchanged,
- remembered slider percent retained when both colors are `None`,
- picker-selected colors immediately inherit current slider alpha,
- outputs normalized to uppercase `#AARRGGBB`,
- named colors converted to `#AARRGGBB` when alpha is applied,
- invalid field text/highlight preserved while valid sibling can still update.
- Verification summary:
- `overlay_client/.venv/bin/python -m ruff check overlay_controller/widgets/background.py overlay_controller/tests/test_background_widget.py` -> passed.
- `overlay_client/.venv/bin/python -m mypy overlay_controller/widgets/background.py` -> passed.
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_background_widget.py overlay_controller/tests/test_focus_manager.py` -> `1 passed`, `7 skipped` (headless Tk guards).
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests -k "background_widget or focus_manager or app_context"` -> `2 passed`, `7 skipped`, `51 deselected`.
- `make check` -> passed (`ruff`, `mypy`, full pytest `547 passed`, `32 skipped`).
- Follow-up:
- Run a live GUI/manual controller pass in a non-headless session to validate slider drag feel, focus transitions, and visual alignment.
