## Goal: Add profile-based per-ship/per-context overlay placements

Follow persona details in `AGENTS.md`.
Document implementation results in the `Implementation Results` section.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear, capture it under `Open Questions`.

## Source Inputs
- Issue: [#159 Per ship placement configs](https://github.com/SweetJonnySauce/EDMCModernOverlay/issues/159)
- Owner scoping comment (In Scope/Out of Scope draft): [comment](https://github.com/SweetJonnySauce/EDMCModernOverlay/issues/159#issuecomment-4033609263)
- Follow-up owner UX direction (settings-tab create/list + copy profile deferred): [comment](https://github.com/SweetJonnySauce/EDMCModernOverlay/issues/159#issuecomment-4042312667)

## Requirements (Initial)
- Support placement profiles for plugin groups ("overlays"); placement data can vary by profile.
- Rule evaluation inputs for profile activation must be sourced from EDMC `dashboard_entry` status payloads (Flags/Flags2/GuiFocus-derived values), not journal-only context inference.
- Keep a reserved `Default` profile that always exists, cannot be renamed, and cannot be deleted.
- New profile creation must start from `Default` placements (inherit baseline placements).
- A profile can be assigned to multiple conditions (0..N rules), including multiple ship-specific matches.
- Profile activation rules must support context set: `InMainShip`, `InSRV`, `InFighter`, `OnFoot`, `InWing`, `InTaxi`, `InMulticrew`.
- If rule is `InMainShip`, UI must allow selecting the ship scope used by that rule.
- Plugin must maintain its own CMDR fleet cache sourced from journal `StoredShips` entries.
- Fleet cache must persist across sessions and remain available when no fresh `StoredShips` event has arrived yet.
- `InMainShip` rules must key on stable `ShipID` values from the cached fleet list.
- Fleet cache refresh/update logic must process `StoredShips` snapshots and shipyard/name-change delta events.
- `StoredShips` payloads must be treated as incomplete for active-ship coverage; implementation must not assume the currently occupied ship is present in `ShipsHere`/`ShipsRemote`.
- During `StoredShips` cache refresh, plugin must preserve/add the currently occupied ship using latest journal `state`/entry `ShipID` + ship metadata when available.
- `InMainShip ShipID` rule picker must include the currently occupied ship whenever a valid current `ShipID` is known, including after docking/landing transitions (for example carrier landing) where `StoredShips` omits the active ship.
- `InMainShip ShipID` rule picker must not render ID-only placeholder rows; only ships with known ship names are shown in selectable rows.
- `InMainShip ShipID` rule picker row labels must use only ship identity fields: render as `{ship_name} ({ship_ident})` when ident is present, otherwise `{ship_name}` (never include ship type or numeric ShipID in the row text).
- Users must be able to set the current profile from Overlay Controller, chat commands, and hotkeys.
- Chat commands and hotkeys must support profile navigation actions for `next` and `prev` profile selection (in addition to direct profile selection), and traversal order must match the profile table order in settings.
- On profile switch, plugin must materialize the selected profile overrides into the root plugin/group keys in `overlay_groupings.user.json` (active-root view) for legacy compatibility.
- Each profile must persist a full placement configuration set (including unmodified values inherited from `Default`), not only sparse changed fields.
- Profile management (create/list/rename/delete/rule assignment) must live in a dedicated tab on the EDMCModernOverlay preferences pane.
- Rule labels in the preferences pane must be human-readable with spaces between words (e.g., `In Main Ship`, `In SRV`, `In Fighter`, `On Foot`, `In Wing`, `In Taxi`, `In Multicrew`).
- Profile table in preferences must emulate the look/interaction pattern of BGS-Tally's Discord webhooks table (reference implementation in `../BGS-Tally/bgstally/ui.py`, `sheet_webhooks` setup).
- Profile rule assignment in that table must be checkbox-driven; each rule is represented by a checkbox column (use abbreviations where needed for column width, while keeping full human-readable meaning in labels/tooltips/help text).
- Profile table right-click menu must support row insert, row move up/down, row delete, `Set Active`, `Copy`, and `Paste` actions.
- Profile name editing in the preferences table must be inline (cell edit), with the same validation rules as any other rename path.
- `Paste` naming must be deterministic: first duplicate uses ` (Copy)` suffix, then ` (Copy 2)`, ` (Copy 3)`, etc. as needed.
- Context-menu action icons may be reused from sibling plugin assets under `../BGS-Tally/assets` (for example: `icon_col_edit.png`, `icon_col_delete.png`, `icon_green_tick_16x16.png`), with a graceful fallback to text-only menu entries if icon loading fails.
- Profile names are case-insensitive and may include spaces and symbols.
- When multiple profiles match simultaneously, winner precedence is:
- any matching non-`Default` profile beats `Default`
- if multiple non-`Default` profiles match, the lowest profile sequence number (settings table order) wins
- Manual profile selection must always remain user-selectable from controller/preferences/chat/hotkeys.
- Profiles with no rules are manual-only and must never auto-activate.
- Rule triggers only change the active profile; they must not disable or block manual profile selection controls.
- Auto-rule-driven profile switches must only occur when match state changes and the resolved winner changes (no repeated re-activation on identical successive status snapshots).
- When an auto-rule changes the active profile, use the standard overlay message scheme and show `Active Profile: {name}` briefly on screen.
- Overlay Controller profile UX is switch-only; it must not expose profile CRUD operations.
- Overlay Controller must render profile selection as its own dedicated selector widget.
- Profile selector widget must be positioned above the IdPrefix selector widget in the controller sidebar stack.
- Profile selector widget label text must be `Profile`, rendered above the profile dropdown field.
- IdPrefix selector widget label text must be `Overlay`, rendered above the overlay dropdown field.
- Profile selector widget interaction rules must match IdPrefix selector widget rules (same readonly dropdown semantics, left/right arrow-button stepping, keyboard/focus behavior, selection-wrapping behavior, and empty/disabled-state handling model).
- Controller `Reset Defaults` action must be profile-aware and scoped to the currently selected overlay group across all profiles:
- when active profile is non-`Default`, reset the selected overlay group's placement overrides in that active profile to `Default` profile values
- when active profile is `Default`, reset the selected overlay group's settings in all profiles back to original shipped plugin settings
- Reset button label must be profile-aware:
- when active profile is `Default`, button text is `Reset Overlay (All Profiles)`
- when active profile is non-`Default`, button text is `Reset Profile to Default`
- Placement edits in non-`Default` profiles apply to the current profile only.
- When editing `Default`, changed plugin-group settings must propagate to all other profiles that do not currently hold a divergent override for that same setting.
- `Default` propagation must be evaluated at per-setting granularity (plugin -> group -> field). A profile keeps its own value only when that specific field differs from the pre-edit `Default` value.
- Deleting a non-default profile deletes that profile's assignments/rules and all profile-scoped placements for that profile.
- Existing installs without profile metadata must continue to work via `Default` profile behavior.
- If no ship cache entries are available yet, `InMainShip` ship-selection UI must show a clear `no ships yet` state.
- `overlay_groupings.user.json` must persist profile-aware placement data.
- `overlay_group_cache.json` must persist/cache profile-aware resolved placement values.

### Dashboard Status Contract (Implementation Detail)
- Implement the EDMC plugin hook `dashboard_entry(cmdr, is_beta, entry)` in `load.py` and use it as the canonical source for rule-context flags.
- Decode `entry["Flags"]`, `entry["Flags2"]`, and `entry["GuiFocus"]` into a normalized status snapshot used by the profile rule engine.
- Rule-token to status mapping must be explicit and stable:
- `InMainShip` -> `Flags.InMainShip`
- `InSRV` -> `Flags.InSRV`
- `InFighter` -> `Flags.InFighter`
- `OnFoot` -> `Flags2.OnFoot`
- `InWing` -> `Flags.InWing`
- `InTaxi` -> `Flags2.InTaxi`
- `InMulticrew` -> `Flags2.InMulticrew`
- Profile auto-rule evaluation must run when dashboard status updates are received; it must not depend on journal event-name inference for these contexts.
- Auto-rule evaluation runs on dashboard updates, but profile-switch side effects (state change + message) fire only when rule-match state/winner transitions.
- Journal/state ingestion remains responsible for ship identity (`ShipID`) and fleet-cache maintenance; dashboard status drives context flags.
- Keep/refresh a last-known decoded dashboard snapshot for rule checks during the session.
- If no dashboard status has been received yet in the current session, do not synthesize context from journal events for the above rules; preserve manual/default fallback behavior.
- Add targeted tests for dashboard status decoding and rule evaluation that cover all supported rule tokens.

### Preferences Table UX Contract (BGS-Tally Emulation)
- Reference visual/behavior baseline:
- `../BGS-Tally/bgstally/ui.py` lines around the `sheet_webhooks` table configuration (`Sheet`, checkbox columns, right-click bindings, modified callback).
- Use a table widget approach that preserves the same interaction model as BGS-Tally's webhook sheet:
- row index gutter visible for right-click row operations
- editable cells where appropriate
- checkbox columns for boolean rule toggles
- keyboard navigation and standard edit bindings
- right-click popup menu bindings enabled
- inline cell editing for profile-name rename operations
- Required right-click commands for profile rows:
- `Insert Row Above/Below`
- `Delete Row`
- `Set Active`
- `Copy`
- `Paste`
- `Set Active` updates current/manual active profile state through the same shared profile service path as other switch controls.
- `Copy` stores full selected profile data in table clipboard state (profile name, rules/checkbox assignments, and full profile placement configuration snapshot).
- `Paste` creates a new profile row from copied data, cloning all copied profile content, and resolves profile-name collisions with deterministic unique naming: first duplicate uses ` (Copy)`, then ` (Copy 2)`, ` (Copy 3)`, etc.

### Overlay Controller Selector Layout Contract
- Controller top selector area must contain two stacked selector widgets, in this exact order:
- `Profile` selector widget (top)
- `Overlay` selector widget (below)
- Each selector widget must render a text label above its dropdown input, matching exact copy:
- `Profile`
- `Overlay`
- Both selectors must remain switch-only controls (no create/rename/delete/rule-edit actions in controller).
- Profile selector behavior must mirror Overlay selector behavior for interaction ergonomics:
- readonly combobox/dropdown behavior
- matching left/right triangle step controls
- matching key handling in focus mode (`Left`/`Right` step, existing dropdown open/close/confirm patterns)
- matching focus request/exit integration with controller focus manager
- matching fallback handling when option lists are empty or stale
- Selection-change plumbing for both selectors must use the same shared profile/group state service path already used by chat/hotkeys/preferences, avoiding controller-specific state forks.

### Fleet Cache Completeness Contract
- `StoredShips` is authoritative for parked/known fleet membership but not guaranteed to include the active ship currently flown by the CMDR.
- Fleet-cache refresh on `StoredShips` must merge active-ship data from current journal context (`state` first, `entry` fallback) using `ShipID` as the key.
- If active `ShipID` is already present, refresh must enrich/retain metadata instead of dropping/replacing with blank fields.
- If active `ShipID` is missing from `StoredShips`, refresh must inject/preserve that ship record so profile-rule ship pickers remain complete.
- Add regression coverage for scenario: `StoredShips` snapshot excludes active ship; expected cache/result still includes active `ShipID` and label metadata.
- Picker rendering rule: entries that do not have a known ship name are excluded from the UI list to avoid ambiguous rule targeting.

### Default Propagation Contract
- `Default` is the baseline profile and acts as inheritance source for non-divergent profile settings.
- On `Default` edit, propagation evaluation must compare each changed setting against the previous `Default` value:
- if target profile value is missing, adopt new `Default` value
- if target profile value equals previous `Default` value, adopt new `Default` value
- if target profile value differs from previous `Default` value, preserve target profile value (profile is explicitly divergent for that setting)
- Propagation scope is limited to the specific changed fields; unrelated fields in target profiles must not be rewritten.
- This propagation rule applies only when `Default` is edited; edits in non-`Default` profiles do not back-propagate to `Default` or siblings.

### Active Root Materialization Contract
- Persisted profile entries remain stored per profile under `_overlay_profile_overrides` as full configuration snapshots (including inherited/unmodified `Default` values).
- The currently active profile must be materialized to root plugin/group keys in `overlay_groupings.user.json`.
- Profile switch operations must rewrite the active-root view to match the selected profile without mutating other profiles' stored snapshots.
- This contract ensures legacy/root-only readers observe the same placement data as the selected active profile.

### Reset Contract
- Controller `Reset Defaults` behavior is conditional on active profile and is scoped to the currently selected overlay group.
- Active profile is non-`Default`: reset operation reverts the selected overlay group's settings in the active profile to `Default` profile values.
- Active profile is non-`Default`: reset operation also reverts selected overlay-group visibility (`Overlay Visible`) to the `Default` profile setting for that overlay group.
- Active profile is `Default`: reset operation reverts the selected overlay group's settings in all profiles to shipped/original plugin settings.
- Controller reset button label mirrors active-profile reset mode:
- `Default` active -> `Reset Overlay (All Profiles)`
- non-`Default` active -> `Reset Profile to Default`
- `Default`-profile reset must clear profile-specific divergent overrides for the selected overlay group so every profile resolves to shipped defaults for that overlay group after reset completes.
- Reset operations must trigger the same runtime reload/invalidation path as normal controller edits so overlays update immediately.

## Out Of Scope (This Change)
- Large standalone Profile Controller window redesign.

## Current Touch Points
- Code:
- `overlay_plugin/preferences.py` (new dedicated preferences tab for profile management UI and wiring)
- `overlay_plugin/journal_commands.py` (chat command grammar for current-profile changes)
- `overlay_plugin/hotkeys.py` (hotkey actions for profile switching)
- `overlay_plugin/plugin_group_state.py` (state surface for current profile + rule mappings)
- `load.py` (`dashboard_entry` status ingestion for rule-evaluation context flags + journal ingestion for `StoredShips`/shipyard updates into plugin-managed cache)
- `overlay_plugin/<status decode helper>` (new/updated pure helper for `Flags`/`Flags2` context decoding to keep `load.py` thin and testable)
- `overlay_plugin/preferences.py` (BGS-Tally-like profile table widget + checkbox columns + right-click menu actions)
- `overlay_plugin/groupings_loader.py` (loading/merging profile-aware placements)
- `overlay_controller/services/group_state.py` (controller state persistence and cache writes)
- `overlay_controller/overlay_controller.py` (controller UI profile switch entrypoints + apply edits)
- `overlay_controller/controller/layout.py` (separate stacked `Profile` and `Overlay` selector widget placement and labels in sidebar)
- `overlay_controller/widgets/idprefix.py` (Overlay selector behavior baseline and label placement)
- `overlay_controller/widgets/<profile selector widget>` (new/updated dedicated profile selector widget with parity behavior)
- `overlay_controller/controller/edit_controller.py` (edit routing to active profile)
- Tests:
- `overlay_plugin/tests/*` (new profile-state, command, and loader behavior coverage)
- `overlay_controller/tests/test_group_state_service.py`
- `overlay_controller/tests/test_controller_groupings_loader.py`
- `overlay_controller/tests/test_focus_manager.py` (if controller profile-switch UI adds bindings)
- Docs/notes:
- `docs/plans/feature-per-ship-placement.md`
- `RELEASE_NOTES.md`

## Assumptions
- Ship/context signals are obtainable from current EDMC `dashboard_entry` status payloads (plus journal-derived ship identifiers) without adding new external services.
- EDMC dashboard payloads expose `Flags` and `Flags2` values compatible with the rule-token mapping above across supported EDMC versions.
- Profile-aware schema changes can be made backward-compatible through migration/defaulting to `Default`.
- Controller + plugin can share profile state through existing cache/settings sync patterns.
- Reusing visual cues/icon assets from sibling plugin `../BGS-Tally` is permitted for this local EDMC plugin installation context.

## Risks
- Risk: Schema evolution for user config/cache causes migration regressions.
- Mitigation: Add explicit migration/default logic and golden-file tests for old/new schema.
- Risk: Ambiguous rule matching (multiple profiles matching same context/ship).
- Mitigation: Define deterministic precedence and add exhaustive precedence tests.
- Risk: Fleet cache drift/staleness when `StoredShips` has not fired recently.
- Mitigation: Persist last-known fleet cache, update on shipyard/name-change events, and surface cache age in debug logs.
- Risk: `StoredShips` snapshot omits currently occupied ship, causing `InMainShip ShipID` picker/rules to miss the active vessel.
- Mitigation: Merge/preserve active ship from journal `state`/entry during `StoredShips` refresh and guard with targeted regression tests.
- Risk: `Default` edit propagation may overwrite intentional per-profile custom values.
- Mitigation: Propagate only for fields that are missing or equal to pre-edit `Default`; preserve fields that differ, with targeted diff/merge tests.
- Risk: `Default`-profile reset (selected-overlay-group scope across all profiles) could unintentionally erase per-profile customization for that overlay group.
- Mitigation: Add explicit reset-behavior tests and clear UI messaging that reset scope is the selected overlay group across profiles.
- Risk: UX confusion between "current profile", "assigned rules", and "Default" fallback.
- Mitigation: Lock terms/labels early and add inline helper copy in settings/controller.
- Risk: Command/hotkey/controller paths diverge in behavior.
- Mitigation: Route all profile-change paths through one shared service API.
- Risk: Missing or delayed `dashboard_entry` updates leave context flags unavailable at startup.
- Mitigation: Gate auto-rule context matching on decoded dashboard availability and retain manual/default fallback until dashboard status is present.

## Open Questions
- None currently.

## Decisions (Locked)
- `Default` profile is reserved and always present.
- `Default` profile cannot be renamed or deleted.
- New profiles inherit placements from `Default` at creation.
- Each profile stores a full config snapshot (including unmodified `Default`-inherited values), not sparse diffs only.
- Placement edits in non-`Default` profiles apply only to the current profile.
- `Default` edits propagate to other profiles only for non-divergent fields (missing or equal to pre-edit `Default`), and never overwrite divergent per-profile values.
- Switching active profile materializes that profile's overrides at root in `overlay_groupings.user.json` for legacy compatibility.
- `Reset Defaults` is scoped to the currently selected overlay group.
- `Reset Defaults` from a non-`Default` profile reverts the selected overlay group's settings in the active profile to `Default` profile values.
- `Reset Defaults` from `Default` resets the selected overlay group's settings in all profiles to shipped/original plugin settings.
- Reset button text is locked to active-profile mode: `Reset Overlay (All Profiles)` (`Default`) vs `Reset Profile to Default` (non-`Default`).
- `InMainShip` assignment uses cached `ShipID` values as the canonical key.
- Plugin maintains its own persisted fleet cache from `StoredShips` + shipyard/name-change updates.
- `StoredShips` processing must preserve/include active ship data from journal `state`/entry when active ship is missing from snapshot.
- Active `ShipID` inclusion in fleet cache is a hard requirement for `InMainShip` picker/rule authoring correctness.
- `InMainShip` picker suppresses ID-only/type-only rows; only ships with known ship names appear in selectable UI rows.
- `InMainShip` picker display text is identity-only: `{ship_name} ({ship_ident})` when ident exists, else `{ship_name}`; no ship type/ShipID text in picker rows.
- Rule evaluation for profile activation is sourced from EDMC `dashboard_entry` status payloads.
- Rule set includes `InMainShip`, `InSRV`, `InFighter`, `OnFoot`, `InWing`, `InTaxi`, `InMulticrew`.
- Preferences-pane rule labels use human-readable spaced wording for all rule options.
- Rule-token mapping to dashboard flags is explicit (`Flags.*` / `Flags2.*`) and must be unit-tested.
- Auto-rule evaluation for these context rules runs on dashboard status updates; journal path remains ship-id/fleet-cache only.
- Preferences profile table emulates BGS-Tally webhook table look/interaction model, including checkbox columns and right-click row operations.
- Preferences profile table right-click menu includes `Insert`, `Delete`, `Set Active`, `Copy`, and `Paste`.
- Preferences profile table supports inline rename editing in the name cell.
- `Paste` collision naming is deterministic: ` (Copy)`, then ` (Copy 2)`, ` (Copy 3)`, etc.
- `Copy`/`Paste` clones the full profile payload (rules and full placement snapshot), not name/rules only.
- Profile management UX is a dedicated tab in EDMCModernOverlay preferences; current-profile switching is exposed in controller/chat/hotkeys.
- Chat and hotkey profile switching includes `next` and `prev` selection actions, ordered by the profile table order in settings.
- Overlay Controller profile UX is switch-only (no profile CRUD operations).
- Overlay Controller uses two separate stacked selector widgets: `Profile` above `Overlay`.
- Controller selector labels are explicit and rendered above dropdowns with exact text `Profile` and `Overlay`.
- Profile selector interaction contract is parity-matched to Overlay selector interaction rules.
- Profile-name uniqueness/lookup is case-insensitive; spaces/symbols are valid in display and persisted values.
- Multi-match precedence is:
- any matching non-`Default` profile beats `Default`
- if multiple non-`Default` profiles match, the lowest profile sequence number (settings table order) wins.
- Manual profile selection is always available to users from every control surface.
- Auto-rule matches may change the active profile, but never block or disable manual profile selection.
- Auto-rule-triggered profile changes occur only on match-state/winner transitions and use the standard overlay message scheme with exact text `Active Profile: {name}`.
- Profiles with no rules are manual-only and never participate in auto-rule matching.
- Deleting a non-default profile removes that profile's assignments/rules and profile-scoped placements.
- `InMainShip` ship picker shows `no ships yet` when fleet cache has no entries.
- Overlay visibility (`plugin_group_states`, controller `Overlay Visible`) is profile-scoped and follows the active profile across controller/chat/hotkey/settings profile switches.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Finalize locked contracts into implementation-ready acceptance matrix | Completed |
| 2 | Data model + persistence + migration implementation (including fleet cache) | Completed |
| 3 | Control surfaces integration (dedicated preferences tab + controller switch-only + chat/hotkeys) | Completed |
| 4 | Rule evaluation/runtime behavior (non-`Default` precedence + sequence-order tie-break + manual-selection fallback semantics) + end-to-end validation | Completed |
| 5 | Docs, release notes, rollout safeguards, and follow-up backlog | Completed |

## Execution Run (2026-03-22)

| Phase | Execution Plan (This Run) | Status |
| --- | --- | --- |
| 1 | Reconcile this branch against locked requirements and document execution matrix + verification commands for each phase. | Completed |
| 2 | Restore/implement profile persistence, migration, active-root materialization, and fleet cache completeness behaviors. | Completed |
| 3 | Restore/implement preferences/controller/chat/hotkey profile control surfaces with locked UX semantics. | Completed |
| 4 | Restore/implement runtime rule evaluation, transition-only auto-switching, and active-profile overlay messaging. | Completed |
| 5 | Run consolidated tests, update implementation results, and close documentation/release deltas. | Completed |

### Execution Details (This Run)
- Phase 1 detailed execution:
- Audit current branch for profile feature coverage against locked requirements.
- Reuse existing implementation from `per-ship-placement` branch where possible to minimize behavioral risk.
- Record exact test commands for each downstream phase before code changes.
- Phase 2 detailed execution:
- Reintroduce profile state model/persistence (`_overlay_profile_state`, `_overlay_profile_overrides`) and migration/default handling.
- Reintroduce active-root materialization on profile switch.
- Reintroduce fleet cache updates and active-ship merge on `StoredShips`.
- Validate with profile-state and group-state tests.
- Phase 3 detailed execution:
- Reintroduce preferences profile tab/table workflows (CRUD/rules/ship picker/copy-paste).
- Reintroduce controller profile selector integration and profile-aware reset behavior.
- Reintroduce chat/hotkey profile commands and traversal controls.
- Validate with preferences/controller/command/hotkey tests.
- Phase 4 detailed execution:
- Reintroduce/align runtime profile rule evaluation and deterministic precedence.
- Align transition behavior to locked contract (transition-only auto-switching and manual selection always available).
- Emit locked active-profile overlay message format on auto-rule-triggered switches.
- Validate with runtime/profile transition tests.
- Phase 5 detailed execution:
- Run consolidated targeted test pass across touched profile/controller/plugin modules.
- Update `Implementation Results` with this run's phase-by-phase outcomes and test evidence.

## Phase Details

### Phase 1: Contracts And UX Decisions
- Translate already-locked decisions into explicit acceptance criteria and implementation contracts.
- Risks: implicit assumptions slipping back into implementation.
- Mitigations: bind each decision to concrete acceptance/tests before coding.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Convert locked behavior into profile activation/state-transition matrix | Completed |
| 1.2 | Finalize persisted schema contract for profiles + fleet cache | Completed |
| 1.3 | Finalize UX contract (preferences CRUD tab + controller switch-only with separate `Profile`/`Overlay` selector widgets) | Completed |

#### Stage 1.1 Detailed Plan
- Objective:
- Create a single source of truth for activation behavior, fallback to `Default`, edit-target semantics, and manual-selection fallback behavior.
- Primary touch points:
- `docs/plans/feature-per-ship-placement.md`
- Steps:
- Document context/rule match matrix including unmatched/fallback paths.
- Define expected behavior for manual switches vs auto-rule selection, including no-rule profile manual-only handling.
- Acceptance criteria:
- All core behavior paths are explicit and testable.
- No unresolved ambiguity for basic activation/edit scenarios.
- Verification to run:
- `n/a (design stage)`

#### Stage 1.2 Detailed Plan
- Objective:
- Define profile-aware schema for `overlay_groupings.user.json` and `overlay_group_cache.json`, including persisted fleet cache data.
- Steps:
- Propose additive schema with backward-compatible defaulting.
- Define migration/default rules from legacy unprofiled data to `Default`.
- Define persisted fields needed for controller switch-only and manual-selection state continuity.
- Acceptance criteria:
- Schema doc includes read/write examples for legacy and new payloads.
- Migration path preserves existing placements.
- Verification to run:
- `n/a (design stage)`

#### Stage 1.3 Detailed Plan
- Objective:
- Finalize operator UX for preferences CRUD, controller switch-only, and command/hotkey switching.
- Steps:
- Define dedicated preferences-tab create/list/rename/delete flows and validation rules for profile names.
- Define controller/chat/hotkey switching semantics and messaging.
- Lock controller selector layout contract to two distinct stacked widgets (`Profile` above `Overlay`) with labels above dropdowns and no CRUD affordances.
- Acceptance criteria:
- Clear UI/command contract exists for all required control surfaces.
- Out-of-scope workflows explicitly deferred.
- Verification to run:
- `n/a (design stage)`

#### Phase 1 Execution Order
- Implement in strict order: `1.1` -> `1.2` -> `1.3`.

#### Phase 1 Exit Criteria
- Requirements and schema contracts are locked.
- Remaining ambiguity is captured only under `Open Questions` with bounded impact.

### Phase 2: Persistence And Migration
- Implement profile-aware data model and persistence plumbing.
- Risks: breaking existing user config/cache compatibility.
- Mitigations: additive schema + migration + compatibility tests.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Implement profile schema read/write in plugin/controller state services | Completed |
| 2.2 | Add migration/default handling from legacy to `Default` profile | Completed |
| 2.3 | Add persisted fleet cache model fed by `StoredShips` + deltas | Completed |

#### Stage 2.1 Detailed Plan
- Objective:
- Add profile-aware in-memory model and persisted shape for placements.
- Primary touch points:
- `overlay_plugin/plugin_group_state.py`
- `overlay_plugin/groupings_loader.py`
- `overlay_controller/services/group_state.py`
- Steps:
- Add profile identifiers and rule collections to state payloads.
- Route read/write operations through profile-aware model.
- Add `Default`-edit propagation merge path that updates only non-divergent fields in other profiles.
- Add reset-state paths for both reset modes scoped to selected overlay group (non-`Default` -> selected overlay group in active profile reverts to `Default`; `Default` -> selected overlay group resets to shipped defaults across all profiles).
- Add active-profile materialization path so profile switches rewrite root plugin/group keys to selected profile values.
- Ensure per-profile persistence writes full snapshots (including unmodified inherited values), not sparse-only diffs.
- Acceptance criteria:
- State API can load/save placements by profile.
- Legacy callers still function with `Default` profile fallback.
- Editing `Default` updates non-divergent fields in other profiles while preserving divergent overrides.
- Reset semantics are deterministic for both modes and preserve expected profile state after reload.
- Switching profiles updates the root materialized view to selected profile values while retaining per-profile snapshots.
- Persisted profile payloads remain full snapshots after edits/switches and keep unchanged inherited values.
- Verification to run:
- `python -m pytest overlay_controller/tests/test_group_state_service.py -k "profile or default"`
- `python -m pytest tests/test_profile_state.py -k "default and propagate"`
- `python -m pytest tests/test_profile_state.py -k "reset and default"`
- `python -m pytest tests/test_profile_state.py -k "materializes_root_overrides"`
- `python -m pytest tests/test_profile_state.py -k "profile and snapshot"`

#### Stage 2.2 Detailed Plan
- Objective:
- Ensure legacy data is preserved and mapped to `Default` profile seamlessly.
- Steps:
- Implement migration/default logic in loader/state entrypoints.
- Add golden tests for legacy payloads and upgraded payloads.
- Acceptance criteria:
- Existing user files produce equivalent runtime placements post-upgrade.
- No data loss in migration path.
- Verification to run:
- `python -m pytest overlay_controller/tests/test_controller_groupings_loader.py -k "legacy or default"`

#### Stage 2.3 Detailed Plan
- Objective:
- Add persisted fleet cache and integrate with profile/rule lookup inputs.
- Steps:
- Define fleet cache schema keyed by `ShipID` with display metadata.
- Ingest/update cache from `StoredShips`, `Shipyard*`, and `SetUserShipName` journal events.
- Explicitly merge/preserve active ship from journal `state`/entry when handling `StoredShips` snapshots that omit occupied ship.
- Persist and reload cache with backward-compatible defaults.
- Acceptance criteria:
- Fleet list remains available after restart without waiting for a new `StoredShips` event.
- `InMainShip` rule picker and matcher consume `ShipID` entries from this cache.
- `InMainShip ShipID` picker still includes active ship after `StoredShips` refresh even when snapshot omits that active ship.
- `InMainShip ShipID` picker excludes entries without known ship names, showing `no ships yet` when every cached ship lacks a known ship name.
- `InMainShip ShipID` picker rows display identity-only labels (`{ship_name} ({ship_ident})` or `{ship_name}`), with no ship type/ShipID text.
- Verification to run:
- `python -m pytest overlay_controller/tests/test_group_state_service.py -k "cache or ship"`
- `python -m pytest tests/test_profile_state.py -k "storedships and current ship"`
- `python -m pytest tests/test_preferences_panel_controller_tab.py -k "profile_ship_list"`

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.

#### Phase 2 Exit Criteria
- Persistence layer supports profile-aware placements with backward compatibility.
- Migration and cache behavior are covered by automated tests.

### Phase 3: Control Surface Integration
- Wire profile workflows into dedicated preferences tab, controller switch-only UX, and chat/hotkeys.
- Risks: behavior mismatch across input surfaces.
- Mitigations: shared service entrypoints and common validation.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Dedicated preferences-tab profile management UI (create/list/rename/delete/rules) | Completed |
| 3.2 | Controller current-profile switch UX integration | Completed |
| 3.3 | Chat and hotkey profile switch commands/actions | Completed |

#### Stage 3.1 Detailed Plan
- Objective:
- Provide a dedicated preferences-tab profile management interface and rule assignments.
- Steps:
- Add a dedicated tab to the EDMCModernOverlay preferences pane for profile management.
- Add BGS-Tally-style profile table UI (webhook-table visual pattern) with rule checkbox columns and right-click row commands.
- Add profile list/create/rename/delete controls, inline table rename editing, rule assignment controls, `Set Active`/`Copy`/`Paste` context-menu actions, and validation messaging.
- Persist changes through shared profile service APIs.
- Acceptance criteria:
- CMDR can create and manage profiles/rules from the dedicated preferences tab.
- New profile creation inherits `Default` placements.
- Table interactions (insert/delete/set active/copy/paste, inline rename, checkbox toggles) behave consistently with the BGS-Tally reference UX.
- `Paste` name collision handling follows deterministic ` (Copy)` / ` (Copy N)` suffixing.
- `Copy`/`Paste` clones full profile content (rules + full placement snapshot), not partial row metadata only.
- Verification to run:
- `python -m pytest overlay_plugin/tests -k "profile and preferences or context menu or table"`
- `python -m pytest tests/test_preferences_panel_controller_tab.py -k "profile and copy or paste or inline"`

#### Stage 3.2 Detailed Plan
- Objective:
- Allow switching current profile in Overlay Controller via a dedicated `Profile` selector widget, while preserving switch-only (no CRUD) behavior.
- Steps:
- Implement two distinct selector widgets in the controller sidebar top area: `Profile` (top) and `Overlay` (below), each with a label above its dropdown.
- Ensure `Profile` selector widget follows the same interaction rules as `Overlay` selector widget (readonly behavior, left/right arrows, keyboard/focus handling, wrap behavior, empty-state handling).
- Sync both selectors with shared state/service APIs.
- Explicitly prevent create/rename/delete/rule-assignment operations in controller UI.
- Implement controller reset wiring that dispatches reset behavior according to active profile reset contract.
- Implement dynamic reset-button labeling tied to active profile (`Reset Overlay (All Profiles)` vs `Reset Profile to Default`).
- Scope controller reset behavior to the currently selected overlay group across profiles.
- Ensure placement edits apply only to active profile.
- Acceptance criteria:
- Controller reflects current profile and updates edit target accordingly.
- Controller exposes profile switch only; profile CRUD appears only in preferences tab.
- Controller renders separate labeled `Profile` and `Overlay` selector widgets in required order (`Profile` above `Overlay`).
- `Profile` selector interaction behavior is parity-matched with `Overlay` selector behavior.
- Controller reset behavior matches contract for non-`Default` and `Default` active-profile cases.
- Controller reset scope is limited to the currently selected overlay group.
- Controller reset button text updates immediately when active profile changes and matches locked label copy exactly.
- Profile switch updates preview/placement behavior deterministically.
- Verification to run:
- `python -m pytest overlay_controller/tests -k "profile and controller"`

#### Stage 3.3 Detailed Plan
- Objective:
- Add command/hotkey pathways for profile switching.
- Steps:
- Extend chat command parser and hotkey actions for profile select plus `next`/`prev` profile traversal.
- Route through shared service to keep behavior identical to UI paths.
- Acceptance criteria:
- Chat and hotkeys can switch profiles with consistent validation/errors.
- Chat and hotkeys support deterministic `next`/`prev` profile cycling behavior using the same ordering as the settings profile table.
- State updates are reflected in controller and runtime behavior.
- Verification to run:
- `python -m pytest overlay_plugin/tests -k "profile and command or hotkey"`
- `python -m pytest tests/test_hotkeys.py tests/test_journal_commands.py -k "profile and next or prev"`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3`.

#### Phase 3 Exit Criteria
- Required control surfaces support profile switching/management.
- All control surfaces use shared semantics and validation.

### Phase 4: Runtime Rule Evaluation And Validation
- Implement activation engine and verify end-to-end profile selection behavior.
- Risks: precedence bugs and hard-to-debug transitions.
- Mitigations: explicit precedence algorithm + transition-focused tests + debug logging.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Implement rule evaluation engine for context + ship-id matching | Completed |
| 4.2 | Implement profile switch transition handling and cache coherence | Completed |
| 4.3 | Add end-to-end tests for activation/edit behavior matrix | Completed |

#### Stage 4.1 Detailed Plan
- Objective:
- Evaluate current game state against rules and resolve active profile deterministically.
- Steps:
- Implement `dashboard_entry` ingestion and decode `Flags`/`Flags2` status fields into rule-context tokens.
- Implement matcher for `InMainShip`, `InSRV`, `InFighter`, `OnFoot`, `InWing`, `InTaxi`, `InMulticrew` plus `ShipID`-scoped `InMainShip` subrules.
- Define and enforce deterministic winner precedence (non-`Default` beats `Default`; among matching non-`Default` profiles, first in persisted profile order wins).
- Exclude profiles with zero rules from auto-rule matching.
- Ensure auto-rule transition handling only switches profile when match-state/winner changes; unchanged repeated snapshots are no-op for switching/message emission.
- Acceptance criteria:
- Rule matching produces single deterministic profile result for all states.
- Unmatched states fall back according to locked contract.
- Repeated identical dashboard snapshots do not re-trigger profile switch side effects or duplicate auto-switch messages.
- Verification to run:
- `python -m pytest overlay_plugin/tests -k "dashboard or rule and profile"`
- `python -m pytest tests/test_plugin_group_state.py -k "profile and transition"`

#### Stage 4.2 Detailed Plan
- Objective:
- Ensure profile transitions are consistent across runtime, cache, and controller.
- Steps:
- Trigger refresh paths on auto/manual profile changes.
- Implement manual-selection fallback semantics: users can always manually select a profile; auto-rule matches may still switch to matching profiles.
- Emit the standard overlay message `Active Profile: {name}` whenever an auto-rule changes the active profile.
- Validate no stale placement leakage across profiles.
- Acceptance criteria:
- Switching profile updates rendered placements immediately and correctly.
- Cache state remains coherent after repeated transitions.
- Manual-selection and auto-rule behavior matches locked requirements, including transition-only auto-switching and always-available manual selection.
- Auto-rule transitions emit the standard overlay message with exact text format `Active Profile: {name}`.
- Verification to run:
- `python -m pytest overlay_controller/tests -k "profile and cache and transition"`
- `python -m pytest tests/test_lifecycle_tracking.py tests/test_runtime_plugin_group_publish.py -k "profile and active message"`

#### Stage 4.3 Detailed Plan
- Objective:
- Prove behavior against requirements with end-to-end coverage.
- Steps:
- Build matrix tests for create->assign->activate->edit flows.
- Include edge cases: no rules, overlapping rules, unknown ship identifiers, missing profile.
- Acceptance criteria:
- Core requirements have explicit test traceability.
- Regressions from existing default-only behavior are prevented.
- Verification to run:
- `python -m pytest overlay_plugin/tests overlay_controller/tests -k "profile"`

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- Runtime activation behavior matches locked requirements.
- End-to-end test matrix covers expected and boundary scenarios.

### Phase 5: Docs, Release, And Follow-Up
- Document behavior and ship with clear compatibility notes and deferred items.
- Risks: user confusion during migration/adoption.
- Mitigations: clear release notes, terminology consistency, explicit follow-up backlog.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Update user/admin docs for profile behavior and controls | Completed |
| 5.2 | Add release notes + migration notes | Completed |
| 5.3 | Capture deferred follow-ups and rollout checks | Completed |

#### Stage 5.1 Detailed Plan
- Objective:
- Document profile concepts, rules, and control surfaces.
- Steps:
- Update docs with examples for `Default`, custom profiles, and rule assignment.
- Document command/hotkey/controller/settings workflows.
- Acceptance criteria:
- Docs explain setup and troubleshooting for profile activation.
- Terminology is consistent across surfaces.
- Verification to run:
- `n/a (docs review)`

#### Stage 5.2 Detailed Plan
- Objective:
- Communicate migration and compatibility impacts clearly.
- Steps:
- Add release note entries for schema/profile feature and fallback behavior.
- Include known limitations and explicit out-of-scope items.
- Acceptance criteria:
- Release notes accurately describe behavior and migration expectations.
- Verification to run:
- `n/a (docs review)`

#### Stage 5.3 Detailed Plan
- Objective:
- Finalize rollout safeguards and future backlog.
- Steps:
- Capture deferred items in roadmap/issues.
- Define post-release checks for activation correctness and user feedback.
- Acceptance criteria:
- Follow-up backlog is explicit and linked.
- Rollout checks are documented.
- Verification to run:
- `n/a (planning/docs stage)`

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
- Documentation/release artifacts are complete and coherent.
- Deferred scope and rollout follow-ups are explicitly tracked.

## Test Plan (Per Iteration)
- Env setup (once per machine):
- `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- Headless quick pass:
- `source .venv/bin/activate && python -m pytest`
- Targeted tests:
- `source .venv/bin/activate && python -m pytest <path/to/tests> -k "<pattern>"`
- Milestone checks:
- `make check`
- `make test`
- Compliance baseline check (release/compliance work):
- `python scripts/check_edmc_python.py`

## Implementation Results
- Plan created on 2026-03-21.
- Phase 1 completed on 2026-03-21.
- Phase 2 completed on 2026-03-21.
- Phase 3 completed on 2026-03-21.
- Phase 4 completed on 2026-03-21.
- Phase 5 completed on 2026-03-21.
- Requirements clarification update on 2026-03-22: Overlay Controller selector contract now requires separate stacked `Profile` and `Overlay` widgets with labels above each dropdown; this supersedes earlier "single composite top-frame selector" wording.
- Requirements clarification update on 2026-03-22: Fleet-cache contract now explicitly requires preserving/merging active ship on `StoredShips` refresh so `InMainShip ShipID` rules include the currently occupied ship even when omitted from snapshot payloads.
- Requirements clarification update on 2026-03-22: `InMainShip ShipID` picker now explicitly excludes entries without known ship names; only ships with known ship names are shown in the selectable list.
- Requirements clarification update on 2026-03-22: `Default` edit behavior now requires per-setting propagation to other profiles unless that profile has a divergent override for the same setting.
- Requirements clarification update on 2026-03-22: reset behavior is profile-aware and scoped to the currently selected overlay group (`non-Default` reset -> selected overlay group in active profile reverts to `Default`; `Default` reset -> selected overlay group resets to shipped defaults across all profiles).
- Requirements clarification update on 2026-03-22: reset button copy is profile-aware (`Reset Overlay (All Profiles)` when `Default` is active, `Reset Profile to Default` for custom profiles).
- Requirements clarification update on 2026-03-22: profile switching now explicitly requires active-root materialization (selected profile is copied to root plugin/group keys for legacy readers).
- Requirements clarification update on 2026-03-22: per-profile persistence now explicitly requires full snapshots (including unmodified inherited `Default` values), not sparse-only diffs.
- Requirements clarification update on 2026-03-22: preferences profile-table context menu now explicitly includes `Copy` and `Paste` with deterministic unique-name handling (` (Copy)`, ` (Copy 2)`, ...), and profile-name editing is inline in the table.
- Requirements clarification update on 2026-03-22: `InMainShip` picker label format now explicitly uses only `ship_name`/`ship_ident` (`{ship_name} ({ship_ident})` or `{ship_name}`), excluding ship type and ShipID text.
- Requirements clarification update on 2026-03-22: auto-rule activation may switch profiles but never blocks manual profile selection; auto-rule-triggered switches only fire on match-state/winner changes and show `Active Profile: {name}` via the standard overlay message scheme.
- Requirements clarification update on 2026-03-22: chat commands and hotkeys must include `next` and `prev` profile-switch actions ordered the same as the settings profile table.
- Requirements clarification update on 2026-03-22: preferences profile-table `Copy`/`Paste` clones full profile data (rules + full placement snapshot), not partial row metadata.
- Execution update on 2026-03-22:
- Restored profile feature implementation from `per-ship-placement` branch into this branch and reconciled with locked requirements.
- Implemented dashboard-driven rule contexts for `InMainShip`, `InSRV`, `InFighter`, `OnFoot`, `InWing`, `InTaxi`, and `InMulticrew`, with transition-only auto-switch behavior and `Active Profile: {name}` overlay messaging for auto-rule transitions.
- Implemented profile next/prev traversal support in both chat commands (`!overlay next|prev`, `!overlay profile next|prev`) and EDMCHotkeys actions.
- Implemented profile-aware controller edit/reset semantics through profile store integration:
- Default edits propagate per-field to non-divergent values in other profiles.
- Non-default edits apply to active profile only.
- Reset from non-default reverts selected overlay group to `Default` values.
- Reset from `Default` resets selected overlay group across all profiles to shipped/original values for controller-editable placement fields.
- Implemented controller reset-button copy contract:
- `Reset Overlay (All Profiles)` when active profile is `Default`.
- `Reset Profile to Default` when active profile is non-`Default`.
- Implemented controller selector layout contract with separate stacked widgets:
- `Profile` selector above `Overlay` selector.
- Labels rendered above each dropdown.
- Profile selector interaction parity with overlay selector (readonly, step arrows, keyboard/focus behavior).
- Implemented preferences profile-table workflow updates:
- Table-based profile list with rule checkbox columns (`MS`, `SRV`, `FTR`, `Foot`, `Wing`, `Taxi`, `MC`).
- Inline profile rename on double-click name cell.
- Right-click menu actions: insert above/below, delete row, set active, copy, paste.
- Insert above/below now preserves table/profile traversal order by reordering persisted profile list.
- Paste uses deterministic naming (` (Copy)`, ` (Copy 2)`, ...).
- Paste clones full profile payload by adding `profile_clone` runtime/CLI path (`source_profile` + `new_profile`).
- Added `profile_reorder` runtime/CLI path used by preferences table insert-above/insert-below flows.
- Added/updated tests for profile propagation/reset semantics and updated controller state-service expectations.

### Tests Run (2026-03-22 Execution Update)
- `python3 -m pytest tests/test_profile_state.py tests/test_hotkeys.py tests/test_journal_commands.py tests/test_lifecycle_tracking.py -q`
- `python3 -m pytest overlay_controller/tests/test_group_state_service.py tests/test_profile_state.py tests/test_hotkeys.py tests/test_journal_commands.py -q`
- `python3 -m pytest tests/test_profile_state.py tests/test_hotkeys.py tests/test_journal_commands.py tests/test_preferences_panel_controller_tab.py tests/test_launch_entrypoint_parity.py tests/test_lifecycle_tracking.py overlay_controller/tests/test_group_state_service.py overlay_controller/tests/test_idprefix_refresh.py overlay_controller/tests/test_focus_manager.py -q`
- `python3 -m pytest overlay_controller/tests tests/test_plugin_group_state.py tests/test_plugin_group_controls.py tests/test_runtime_plugin_group_publish.py tests/test_plugin_hooks.py tests/test_lifecycle_tracking.py tests/test_hotkeys.py tests/test_journal_commands.py tests/test_profile_state.py tests/test_preferences_panel_controller_tab.py tests/test_launch_entrypoint_parity.py -q`
- Result: passed (`129 passed`, `21 skipped`)

### Phase 1 Execution Summary
- Stage 1.1:
- Created and locked the activation/state-transition matrix.
- Locked fallback semantics: auto-match winner takes precedence with transition-only switching; when no auto match exists, runtime falls back to manual-selected profile (or `Default` if unset), and manual selection remains available at all times.
- Locked no-rule profile behavior as manual-only.
- Stage 1.2:
- Finalized additive persisted schema contract in `overlay_groupings.user.json`:
- `_overlay_profile_state` for profile metadata, rules, current/manual selection, and fleet cache.
- `_overlay_profile_overrides` for per-profile placement override snapshots.
- Locked migration strategy: preserve existing root overrides as `Default`, keep legacy-compatible root keys as active-profile materialized view.
- Stage 1.3:
- Finalized UX contract:
- Preferences: dedicated profile-management tab handles CRUD/rules.
- Controller: switch-only profile control uses separate stacked `Profile` and `Overlay` selector widgets (labels above dropdowns), no CRUD operations.
- Chat/hotkeys/controller all route through shared profile service APIs.

### Tests Run For Phase 1
- `n/a`
- Result: completed (design/contract stage)

### Phase 2 Execution Summary
- Stage 2.1:
- Implemented profile-aware persistence service in `overlay_plugin/profile_state.py`.
- Added plugin/runtime profile APIs and CLI endpoints (`profile_status`, `profile_set`, `profile_create`, `profile_rename`, `profile_delete`, `profile_set_rules`).
- Stage 2.2:
- Implemented migration/default behavior by materializing active profile overrides at root while persisting full profile map in `_overlay_profile_overrides`.
- Preserved metadata keys during controller/state writes so profile metadata survives diff writes.
- Stage 2.3:
- Implemented persisted fleet cache updates from `StoredShips` snapshots plus ship delta events (including rename/nameplate updates).
- Fleet cache is now exposed through profile status for rules UI and `InMainShip` ship matching.

### Tests Run For Phase 2
- `overlay_client/.venv/bin/python -m pytest tests/test_profile_state.py overlay_controller/tests/test_group_state_service.py overlay_controller/tests/test_controller_groupings_loader.py -q`
- Result: passed

### Phase 3 Execution Summary
- Stage 3.1:
- Added dedicated `Profiles` preferences tab with profile create/rename/delete, current-profile switching, and rule editing UI.
- Added ship list presentation (`no ships yet` fallback) for `InMainShip` rule assignment.
- Stage 3.2:
- Added controller switch-only selector flow backed by plugin bridge `profile_status`/`profile_set`; selector layout contract is now separate stacked `Profile` and `Overlay` widgets with labels above each dropdown.
- Wired profile polling and active-profile sync into controller status polling loop.
- Stage 3.3:
- Extended chat command helper with `profile`/`profiles` commands.
- Added EDMCHotkeys action for profile switching payloads.

### Tests Run For Phase 3
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py tests/test_preferences_panel_controller_tab.py tests/test_launch_entrypoint_parity.py -q`
- Result: passed

### Phase 4 Execution Summary
- Stage 4.1:
- Implemented runtime rule engine (`InMainShip`, `InSRV`, `InFighter`, `OnFoot`) with `ShipID` filtering.
- Implemented deterministic precedence: matching non-`Default` profiles beat `Default`; matching non-`Default` conflicts resolve by persisted profile order.
- Stage 4.2:
- Implemented manual-selection fallback semantics: no auto-match falls back to manual-selected profile.
- Added runtime transition signaling (`OverlayProfileChanged` + `OverlayOverrideReload`) and config rebroadcast on profile changes.
- Stage 4.3:
- Added targeted tests for profile store behavior, command/hotkey paths, and metadata-preserving write flows.
- Validated controller/plugin test slices plus overlay-controller suite.

### Tests Run For Phase 4
- `overlay_client/.venv/bin/python -m pytest tests/test_plugin_hooks.py tests/test_lifecycle_tracking.py tests/test_runtime_plugin_group_publish.py tests/test_plugin_group_controls.py tests/test_plugin_group_state.py tests/test_preferences_panel_controller_tab.py tests/test_hotkeys.py tests/test_journal_commands.py tests/test_launch_entrypoint_parity.py -q`
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests -q`
- Result: passed

### Phase 5 Execution Summary
- Stage 5.1:
- Updated implementation plan execution summaries and per-phase test evidence in this document.
- Stage 5.2:
- Added release-note entry for profile-based per-ship/context placement support.
- Stage 5.3:
- Documented rollout validation for profile-scoped visibility and profile-copy behavior captured in automated tests.

### Tests Run For Phase 5
- `overlay_client/.venv/bin/python -m pytest tests/test_profile_state.py tests/test_hotkeys.py tests/test_journal_commands.py tests/test_preferences_panel_controller_tab.py overlay_controller/tests/test_controller_groupings_loader.py overlay_controller/tests/test_group_state_service.py tests/test_launch_entrypoint_parity.py -q`
- Result: passed
