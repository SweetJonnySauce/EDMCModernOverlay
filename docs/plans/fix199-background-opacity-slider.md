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
- `overlay_controller/widgets/background.py` (add slider UI, alpha parsing/formatting sync, keyboard/focus behavior updates)
- `overlay_controller/overlay_controller.py` (`set_values`/change propagation interactions with background widget values)
- `overlay_plugin/overlay_api.py` (confirm/retain accepted color token format `#RRGGBB` / `#AARRGGBB`)
- `overlay_controller/controller/layout.py` (only if geometry/padding needs adjustment after slider insertion)
- Tests:
- `overlay_controller/tests/test_background_widget.py` (new slider behavior and alpha synchronization coverage)
- `overlay_controller/tests/test_app_context.py` (sanity-only if wiring shifts require context updates)
- Docs/notes:
- `docs/plans/fix199-background-opacity-slider.md`

## Assumptions
- Alpha-bearing color tokens use `#AARRGGBB` format in controller entries.
- When a color token has no explicit alpha (`#RRGGBB`), effective alpha for slider feedback defaults to `100%` until user sets slider or explicit alpha.
- If both colors are `None`, slider displays `100%` initially.
- Percent-to-alpha mapping uses rounding semantics (`50% -> 0x80`).
- Slider retains its last percent value even when both colors are `None`; that remembered value is applied when a color is later set.
- Existing background widget focus and key-navigation contracts remain intact unless explicitly updated in this plan.

## Risks
- Bidirectional synchronization (entry edit <-> slider move) can create callback loops.
- Mitigation: add explicit guard flags around programmatic updates and emit changes only on effective value deltas.
- Ambiguity around named colors and non-alpha tokens can cause inconsistent slider feedback.
- Mitigation: define a single normalization rule for effective alpha and apply it consistently in `set_values`, entry validation, and slider handlers.
- Adding one more control can regress keyboard traversal/focus behavior.
- Mitigation: extend `get_binding_targets`, `focus_next_field`, `focus_previous_field`, and `handle_key` in lockstep with tests.

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
- Background widget remains a multi-control widget and slider keyboard handling follows an explicit modal-like active-field rule.
- While slider is active, horizontal arrows are value-adjustment keys; `Space`/`Enter`/`Up`/`Down` are the explicit exit keys.
- `Up` exits to previous field and `Down` exits to next field, following normal multi-control navigation.
- Slider keyboard increments/decrements use `1%` steps.
- Slider keyboard edits commit on exit keys (`Space`/`Enter`/`Up`/`Down`) rather than per arrow press.
- Slider keeps a remembered percentage state even when both colors are `None`; later color assignment applies that value.
- After an exit event while still focused on slider, `Left`/`Right` return to navigation semantics and can move focus off slider.
- `Space`/`Enter` exits slider-adjust mode while keeping focus on slider.
- Mouse-drag updates the displayed percent continuously, with color writes committed on release.
- If one color field is invalid, its text/highlight state is preserved while the valid sibling field is still updated.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Contract lock: alpha precedence, commit rules, and keyboard interaction model | Pending |
| 2 | Widget implementation: slider UI, percent display, and commit-on-release behavior | Pending |
| 3 | Integration wiring: controller persistence, normalization, and focus-cycle parity | Pending |
| 4 | Validation: targeted tests for sync, keyboard mode, and regression safety | Pending |
| 5 | Documentation closeout and follow-up tracking | Pending |

## Phase Details

### Phase 1: Scope and Contracts
- Lock exact behavior for slider placement, alpha semantics, and precedence rules.
- Risks: ambiguous handling for missing alpha or named colors.
- Mitigations: define canonical alpha-derivation and write acceptance checks before code edits.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Confirm touch points and current alpha behavior in background widget/controller callbacks | Pending |
| 1.2 | Lock slider/color synchronization contract (precedence, `None`, conversion, commit timing) | Pending |
| 1.3 | Lock multi-control keyboard contract and no-regression checklist | Pending |

#### Stage 1.1 Detailed Plan
- Objective:
- Build a complete inventory of background-widget paths that parse, normalize, and emit color values.
- Primary touch points:
- `overlay_controller/widgets/background.py`
- `overlay_controller/overlay_controller.py`
- `overlay_plugin/overlay_api.py`
- Steps:
- Trace `set_values`, `_emit_change`, `_parse_color_value`, `_normalise_color_text`, and picker flows.
- Trace `_handle_background_changed` write path and normalization.
- Acceptance criteria:
- All alpha-affecting and emit paths are listed and mapped to slider integration points.
- Verification to run:
- `rg -n "set_values|_emit_change|_parse_color_value|_normalise_color_text|_handle_background_changed|backgroundColor|backgroundBorderColor" overlay_controller overlay_plugin`

#### Stage 1.2 Detailed Plan
- Objective:
- Lock synchronization contract for slider and color fields.
- Steps:
- Specify how slider value is derived from color entries (including `None`, named colors, `#RRGGBB`, `#AARRGGBB`).
- Specify precedence and conflict resolution when border alpha differs from background alpha.
- Acceptance criteria:
- All requirement bullets map to explicit rules without unresolved conflicts.
- Verification to run:
- Manual requirements review against this document.

#### Stage 1.3 Detailed Plan
- Objective:
- Define no-regression expectations before implementation.
- Steps:
- Lock keyboard traversal order with the new slider included.
- Lock slider active-field keyboard behavior:
- `Left`/`Right` can enter slider focus from adjacent fields.
- While slider is active, `Left`/`Right` adjust value and do not move focus.
- `Space`/`Return`/`KP_Enter`/`Up`/`Down` exit slider and continue widget navigation.
- Slider keyboard step size is `1%`, with commit on exit.
- `Up` maps to previous field and `Down` maps to next field.
- Post-exit horizontal keys regain focus-navigation behavior.
- Lock existing color-picker and border spinbox behavior as unchanged unless explicitly required.
- Acceptance criteria:
- Focus/keyboard and existing color-validation behavior are explicitly covered by planned tests.
- Verification to run:
- `python3 -m pytest overlay_controller/tests -k "background_widget or focus_manager"`

#### Phase 1 Execution Order
- Implement in strict order: `1.1` -> `1.2` -> `1.3`.

#### Phase 1 Exit Criteria
- Synchronization and precedence rules are explicit and testable.
- No-regression checklist is defined for focus/navigation and value normalization.

### Phase 2: Widget UI and Behavior Implementation
- Add slider UI and implement alpha synchronization in `BackgroundWidget`.
- Risks: layout crowding and callback recursion.
- Mitigations: guard programmatic updates and keep UI changes scoped to the existing border row.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add slider UI to border row with live percentage display | Pending |
| 2.2 | Implement commit-on-release alpha application with `None`/invalid-field handling | Pending |
| 2.3 | Implement bidirectional alpha sync (entry/picker -> slider and mismatch resolution) | Pending |

#### Stage 2.1 Detailed Plan
- Objective:
- Add slider control on the `Border (px)` row, right of the spinbox.
- Primary touch points:
- `overlay_controller/widgets/background.py`
- Steps:
- Add slider variable, percentage display, and placement in border row.
- Include slider in enabled/disabled state handling and focus target bindings.
- Acceptance criteria:
- Slider renders in required location and exposes `0%` left / `100%` right.
- Verification to run:
- Manual controller visual check in display session.

#### Stage 2.2 Detailed Plan
- Objective:
- Apply slider value to color alpha channels with `None`-safe behavior.
- Steps:
- Implement helper(s) to set alpha for supported color tokens.
- On slider commit, update both colors when present and leave `None` fields unchanged.
- If one field is invalid and the other valid, apply slider update to the valid field.
- Keep a remembered slider percentage when both fields are `None`, and apply it once a color becomes available.
- Acceptance criteria:
- Slider updates both alphas when colors exist and is no-op for missing colors.
- Verification to run:
- `python3 -m pytest overlay_controller/tests/test_background_widget.py -k "opacity or alpha or slider"`

#### Stage 2.3 Detailed Plan
- Objective:
- Keep slider value synchronized with manual color alpha edits and picker updates.
- Steps:
- Update slider from edited color alpha; use background alpha as precedence when mismatch exists.
- Ensure slider change resolves mismatches by setting both alphas to the slider value.
- Apply current slider alpha immediately when a picker returns a new color token.
- Preserve invalid entry text/highlight state while still syncing the valid sibling field.
- Acceptance criteria:
- Manual/picker alpha changes update slider; mismatch and invalid-sibling rules match locked requirements.
- Verification to run:
- `python3 -m pytest overlay_controller/tests/test_background_widget.py -k "manual or mismatch or precedence"`

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.

#### Phase 2 Exit Criteria
- Slider behavior matches all requirement bullets.
- Existing border/background field editing behavior is preserved apart from planned alpha synchronization.

### Phase 3: Controller Wiring and Integration
- Ensure background widget + controller integration preserves persisted values and live preview behavior.
- Risks: unintended write storms or stale UI state after group switch.
- Mitigations: reuse existing change callback path and add change-delta guards where needed.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Wire `set_values`/group selection to slider state, including remembered value behavior | Pending |
| 3.2 | Verify persistence path normalizes/stores `#AARRGGBB` values after slider edits | Pending |
| 3.3 | Ensure sidebar focus-cycle and slider active/exit keyboard modes are regression-safe | Pending |

#### Stage 3.1 Detailed Plan
- Objective:
- Keep group-selection loads aligned with slider state.
- Steps:
- Ensure loaded background/border values determine slider feedback according to precedence rules.
- Validate `None` cases do not force unintended color mutations.
- Acceptance criteria:
- Switching groups presents correct slider value and does not alter stored colors until user edits.
- Verification to run:
- `python3 -m pytest overlay_controller/tests -k "background_widget or app_context"`

#### Stage 3.2 Detailed Plan
- Objective:
- Preserve background change callback semantics.
- Steps:
- Confirm change callback payloads remain compatible with `_normalise_background_color` and border-width normalization.
- Confirm live preview refresh behavior remains unchanged.
- Acceptance criteria:
- Controller receives valid color tokens after slider changes and persists without new errors.
- Verification to run:
- `python3 -m pytest overlay_controller/tests -k "background_widget"`

#### Stage 3.3 Detailed Plan
- Objective:
- Preserve widget accessibility behavior with the extra control.
- Steps:
- Update navigation order and binding-target exposure for slider inclusion.
- Implement explicit slider key-mode behavior for `Left`/`Right` adjust and `Space`/`Enter`/`Up`/`Down` exit.
- Ensure `Up` exits to previous field and `Down` exits to next field.
- Ensure post-exit `Left`/`Right` semantics revert to navigation while slider remains focusable.
- Ensure `Space`/`Enter` exits slider-adjust mode without moving focus off slider.
- Validate enter/exit focus mode behavior remains coherent in sidebar.
- Acceptance criteria:
- Background widget remains keyboard-operable with predictable field traversal.
- Verification to run:
- `python3 -m pytest overlay_controller/tests/test_focus_manager.py`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3`.

#### Phase 3 Exit Criteria
- Controller wiring remains stable with slider-enabled background updates.
- Focus and interaction semantics remain accessible and predictable.

### Phase 4: Tests and Validation
- Add focused tests for slider behavior and run targeted suites.
- Risks: Tk/headless environment may skip widget tests.
- Mitigations: record skips clearly and include manual UI verification steps.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Add/update widget tests for full slider contract (sync, precedence, keyboard) | Pending |
| 4.2 | Run targeted background/focus/controller integration tests | Pending |
| 4.3 | Run milestone checks and capture outcomes with skips/failures documented | Pending |

#### Stage 4.1 Detailed Plan
- Objective:
- Codify slider contract in tests.
- Steps:
- Add tests for slider placement semantics, range mapping, `None` no-op behavior, manual alpha feedback, mismatch precedence, and mismatch resolution on slider move.
- Add tests for slider keyboard behavior:
- `Left`/`Right` can enter slider field from neighbors.
- `Left`/`Right` on slider adjusts value without leaving slider field.
- `Space`/`Enter`/`Up`/`Down` exits slider field.
- `Left`/`Right` slider adjustment uses `1%` steps.
- Slider keyboard adjustments commit on exit only.
- `Up` exits to previous field and `Down` exits to next field.
- After exit, `Left`/`Right` from slider can navigate away.
- `Space`/`Enter` exits slider-adjust mode while keeping slider focus.
- Mouse drag updates percentage label live while committing alpha on release.
- Slider remembers percentage when both colors are `None` and applies that value when a color is later set.
- Picker-selected colors inherit current slider alpha immediately.
- Invalid field text/highlight remains unchanged while valid sibling updates.
- Acceptance criteria:
- Test coverage explicitly maps to each locked requirement bullet.
- Verification to run:
- `python3 -m pytest overlay_controller/tests/test_background_widget.py`

#### Stage 4.2 Detailed Plan
- Objective:
- Validate integration with focus/controller paths.
- Steps:
- Run focused tests for background widget + focus manager + related controller wiring.
- Acceptance criteria:
- Targeted tests pass or skips are documented with reasons.
- Verification to run:
- `python3 -m pytest overlay_controller/tests -k "background_widget or focus_manager or app_context"`

#### Stage 4.3 Detailed Plan
- Objective:
- Execute milestone-level project checks.
- Steps:
- Run lint/typecheck/pytest project checks.
- Acceptance criteria:
- Failures are either fixed or documented in `Implementation Results`.
- Verification to run:
- `make check`

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- Slider behavior is covered by tests and validated end-to-end.
- No unexplained regressions remain.

### Phase 5: Docs, Results, and Follow-up
- Finalize documentation and capture residual risks.
- Risks: behavior details drift from implementation reality.
- Mitigations: keep results tied to exact files/commands and update stage/phase statuses consistently.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Record implementation results and test evidence | Pending |
| 5.2 | Capture residual risks and deferred UX/cleanup follow-ups | Pending |
| 5.3 | Final phase/stage bookkeeping and closeout consistency check | Pending |

#### Stage 5.1 Detailed Plan
- Objective:
- Populate `Implementation Results` with touched files, behavior changes, and test outcomes.
- Steps:
- List exact files changed and test command outputs.
- Acceptance criteria:
- Results are auditable and complete.
- Verification to run:
- N/A (documentation update)

#### Stage 5.2 Detailed Plan
- Objective:
- Capture post-merge follow-up work if needed.
- Steps:
- Document optional improvements (for example slider label polish or named-color UX decisions).
- Acceptance criteria:
- Follow-up items are explicit and scoped.
- Verification to run:
- N/A

#### Stage 5.3 Detailed Plan
- Objective:
- Ensure phase/stage status tables accurately reflect completion.
- Steps:
- Mark completed stages/phases and verify consistency with results text.
- Acceptance criteria:
- Plan status and implementation evidence are aligned.
- Verification to run:
- N/A

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
- Plan is fully documented and ready for reference/closeout.
- Residual risks and follow-up items are recorded.

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
- Plan created on 2026-03-21.
- Phase 1 not started.
- Phase 2 not started.
- Phase 3 not started.
- Phase 4 not started.
- Phase 5 not started.

### Phase 1 Execution Summary
- Stage 1.1:
- Not started.
- Stage 1.2:
- Not started.
- Stage 1.3:
- Not started.

### Tests Run For Phase 1
- Not started.

### Phase 2 Execution Summary
- Stage 2.1:
- Not started.
- Stage 2.2:
- Not started.
- Stage 2.3:
- Not started.

### Tests Run For Phase 2
- Not started.

### Phase 3 Execution Summary
- Stage 3.1:
- Not started.
- Stage 3.2:
- Not started.
- Stage 3.3:
- Not started.

### Tests Run For Phase 3
- Not started.

### Phase 4 Execution Summary
- Stage 4.1:
- Not started.
- Stage 4.2:
- Not started.
- Stage 4.3:
- Not started.

### Tests Run For Phase 4
- Not started.

### Phase 5 Execution Summary
- Stage 5.1:
- Not started.
- Stage 5.2:
- Not started.
- Stage 5.3:
- Not started.

### Tests Run For Phase 5
- Not started.
