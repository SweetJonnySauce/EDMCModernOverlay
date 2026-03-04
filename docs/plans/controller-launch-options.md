## Goal: Add more ways to launch the Overlay Controller

Follow persona details in `AGENTS.md`.
Document implementation results in the Implementation Results section.
After each stage is complete, change stage status to Completed.
When all stages in a phase are complete, change phase status to Completed.
If something is not clear, ask clarifying questions.

## Requirements (Initial)
- Keep existing in-game chat launch behavior unchanged:
- `!ovr` and existing launch aliases continue to launch the Overlay Controller exactly as they do today.
- Add a dedicated `Controller` tab in preferences.
- Tab order: place `Controller` immediately after the `Overlay` tab.
- Move these existing controls to the new `Controller` tab:
- `Chat command to launch controller`
- `Chat command argument to toggle overlay`
- Add a `Launch Controller` button to the new `Controller` tab.
- Button layout: own row (not inline with the text fields).
- Button order: first control shown on the `Controller` tab.
- Add a hotkey action to launch the Overlay Controller via EDMCHotkeys integration.
- Hotkey action label: `Launch Overlay Controller`.
- Reuse the same runtime launch infrastructure across chat, settings button, and hotkey paths.
- Addendum A: settings-button and hotkey launches must skip the 3-second countdown and launch immediately.
- Chat launch behavior remains unchanged unless explicitly revised in a later addendum.
- Preserve thread-safety and responsiveness:
- launch still occurs via worker thread (`overlay_plugin/controller_services.py` path).
- no Tk/UI work moves off the main thread.
- Add tests before behavior-changing rewires, especially at settings-callback and hotkey-callback seams.

## Out Of Scope (This Change)
- Adding launch arguments/options to chat commands.
- Adding launch profiles/default launch modes in preferences.
- Arbitrary CLI argument passthrough to the controller process.

## Current Touch Points
- Command parsing:
- `overlay_plugin/journal_commands.py`
- Runtime launch entry and process wiring:
- `load.py` (`launch_overlay_controller`, `_overlay_controller_launch_sequence`, `_spawn_overlay_controller_process`, `_controller_countdown`)
- Thread/process orchestration:
- `overlay_plugin/controller_services.py`
- Hotkeys integration:
- `overlay_plugin/hotkeys.py`
- Preferences/config persistence and UI hooks:
- `overlay_plugin/preferences.py`
- Settings tab construction and ordering:
- `overlay_plugin/preferences.py` (`tabs` creation and per-tab row layout)
- Existing tests:
- `tests/test_journal_commands.py`
- `tests/test_controller_services.py`
- `tests/test_launch_command_pref.py`
- `tests/test_hotkeys.py`
- `tests/test_preferences_persistence.py`

## Open Questions
- None currently.

## Decisions (Locked)
- EDMCHotkeys launch action label will be `Launch Overlay Controller`.
- Duplicate-launch handling for button/hotkey paths will stay log-only (no new user-facing status message added by this change).

## Addendum A (2026-03-04)
- New requirement: for settings button and hotkey launch paths, do not wait through the 3..2..1 countdown.
- Expected behavior: launch starts immediately for settings/hotkey entrypoints.
- Existing chat launch behavior remains unchanged for now.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Lock scope + launch invariants | Completed |
| 2 | Add Controller tab layout + settings launch button wiring | Completed |
| 3 | Add EDMCHotkeys launch action wiring | Completed |
| 4 | Tests, compliance checks, and rollout notes | Completed |
| 5 | Addendum A: immediate launch for settings button + hotkey | Completed |

## Phase Details

### Phase 1: Lock scope + launch invariants
- Freeze unchanged behavior guarantees for existing chat-launch commands.
- Define settings-button and hotkey-launch behavior as thin wrappers around runtime launch entrypoint.
- Confirm expected user-facing behavior for duplicate launch attempts and failure paths.
- Risks: accidental expansion into launch-option scope.
- Mitigations: keep option parsing/profile work explicitly out of scope in this milestone.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Audit current launch behavior and document invariants | Completed |
| 1.2 | Confirm settings-button and hotkey-launch contracts (plain launch only) | Completed |
| 1.3 | Define error handling/user feedback policy for duplicate launch/failure | Completed |

Phase 1 Outcomes:
- Existing chat-launch behavior remains unchanged and continues to route through `launch_overlay_controller`.
- Settings button and hotkey action are both plain launch wrappers over the same runtime launch entrypoint.
- Duplicate-launch handling remains log-only for this change (no new user-facing status message path introduced).

#### Stage 1.1 Detailed Plan: audit current launch behavior and invariants
- Objective: establish a concrete baseline of current launch flow before UI/hotkey entrypoint changes.
- Primary touch points:
- `overlay_plugin/journal_commands.py` (chat command dispatch into launch callback)
- `load.py` (`launch_overlay_controller`, runtime callback wiring)
- `overlay_plugin/controller_services.py` (launch thread/process guard behavior)
- Steps:
- Confirm chat path calls only the existing runtime launch entrypoint.
- Confirm runtime launch path enforces duplicate-launch guards (already launching / already running).
- Confirm launch sequence remains worker-thread based and process spawn path unchanged.
- Record invariants to preserve in later phases:
- `!ovr` behavior unchanged.
- Duplicate launch attempts are blocked by runtime guard.
- Launch path remains centralized and shared.
- Acceptance criteria:
- A baseline list of invariants is documented in this plan and referenced by later test stages.
- No new launch entrypoint bypasses are introduced in the plan scope.
- Verification to run (read-only checks):
- `python -m pytest -k "journal_commands or controller_services or launch_command_pref"`

#### Stage 1.2 Detailed Plan: define settings-button and hotkey-launch contracts
- Objective: lock functional contracts for new entrypoints so Phase 2/3 implementation is deterministic.
- Settings contract:
- Add a `Controller` tab immediately after `Overlay`.
- `Launch Controller` appears first and on its own row.
- `Chat command to launch controller` and `Chat command argument to toggle overlay` move to this tab.
- Settings launch callback delegates directly to `launch_overlay_controller`.
- Hotkey contract:
- Add one launch action labeled `Launch Overlay Controller`.
- Hotkey callback delegates directly to `launch_overlay_controller`.
- Thread policy/cardinality remain explicit in hotkeys metadata (`main`, `single`).
- Acceptance criteria:
- All placement/order/label contracts are explicit in Requirements + Phase 2/3 stages.
- No contract remains ambiguous in Open Questions.
- Verification to run (post-implementation in later phases):
- `python -m pytest -k "hotkeys or preferences"`

#### Stage 1.3 Detailed Plan: lock duplicate-launch behavior and feedback policy
- Objective: set one consistent behavior for repeated launch requests across all entrypoints.
- Policy decisions:
- Keep duplicate-launch handling log-only for settings/hotkey paths in this change.
- Do not add new user-facing duplicate-launch status message path.
- Rely on existing runtime launch guard exceptions/messages and current on-screen controller-active behavior.
- Scope boundary:
- No launch options/profiles/argument parsing added.
- No CLI passthrough behavior introduced.
- Acceptance criteria:
- Decisions section reflects final policy and remains in sync with Phase 2/3 stage wording.
- Phase 2 stage text explicitly notes no new duplicate-launch UI message.
- Verification to run (post-implementation in later phases):
- `python -m pytest -k "controller_services or hotkeys or preferences"`

### Phase 2: Add Controller tab layout + settings launch button wiring
- Add a dedicated `Controller` tab to preferences immediately after `Overlay`.
- Move controller-launch-related controls from current location to the new `Controller` tab.
- Add a dedicated launch button in the `Controller` tab that invokes the existing runtime launch path.
- Placement contract: render `Launch Controller` on its own row.
- Ordering contract: `Launch Controller` is the first option/control on the `Controller` tab.
- Keep UI interactions main-thread safe; callback must delegate quickly and avoid blocking.
- Preserve current behavior of existing controls and status messaging.
- Risks: accidental duplicate launches from repeated clicks.
- Mitigations: rely on existing runtime launch guards and clear user-facing errors/messages; add layout checks for tab ordering and control placement.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add `Controller` tab after `Overlay`; place `Launch Controller` first, then moved launch/toggle command controls | Completed |
| 2.2 | Add `Launch Controller` button on its own row and wire callback to `launch_overlay_controller` (no new duplicate-launch UI message) | Completed |
| 2.3 | Add/adjust tests for tab ordering, first-control ordering, control placement, callback wiring, and no-regression behavior | Completed |

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.
- Do not refactor unrelated Overlay/Experimental tab controls during this phase.
- Keep behavior-scoped changes only: tab layout move + launch button wiring; no launch semantics changes.

#### Stage 2.1 Detailed Plan: create Controller tab and relocate command controls
- Objective: move controller-launch-related settings into a dedicated `Controller` tab without changing command persistence behavior.
- Primary touch points:
- `overlay_plugin/preferences.py` notebook/tab setup (`tabs.add(...)` sequence).
- Existing launch/toggle command rows currently built in overlay tab section.
- Steps:
- Add `controller_tab = nb.Frame(tabs)` and insert it immediately after `overlay_tab` in `tabs.add(...)`.
- Create a dedicated section/frame in `controller_tab` for controller controls.
- Move these rows from Overlay tab layout into Controller tab layout:
- `Chat command to launch controller`
- `Chat command argument to toggle overlay`
- Preserve existing Tk vars and handlers unchanged:
- `self._var_launch_command`, `self._on_launch_command_event`
- `self._var_toggle_argument`, `self._on_toggle_argument_event`
- Keep existing spacing/style patterns (`ROW_PAD`, frame styles) consistent with current preferences UI.
- Acceptance criteria:
- Tab order is `Overlay`, `Controller`, `Experimental`.
- Launch/toggle command controls appear only on `Controller` tab.
- No behavior change in launch/toggle command editing or persistence callbacks.
- Verification to run after stage:
- `python3 -m pytest tests/test_launch_command_pref.py`

#### Stage 2.2 Detailed Plan: add Launch Controller button and runtime callback wiring
- Objective: add a first-row `Launch Controller` action in `Controller` tab that reuses existing runtime launch path.
- Primary touch points:
- `overlay_plugin/preferences.py` (`PreferencesPanel.__init__`, new button row + click handler).
- `load.py` `plugin_prefs(...)` callback wiring into `PreferencesPanel`.
- Runtime launch entrypoint already in use: `load._PluginRuntime.launch_overlay_controller`.
- Steps:
- Extend `PreferencesPanel` constructor with optional launch callback input (parallel to existing callback pattern).
- Add `Launch Controller` button as the first control row in `Controller` tab.
- Implement `_on_launch_controller(...)` handler that delegates to the injected callback.
- Keep duplicate-launch policy aligned with Phase 1 decision:
- no new user-facing duplicate-launch message path introduced by this button.
- Wire callback in `load.py::plugin_prefs` by passing `_plugin.launch_overlay_controller` when available.
- Acceptance criteria:
- `Launch Controller` is the first control on `Controller` tab and on its own row.
- Button path calls existing runtime launch entrypoint only (no duplicate launch logic in UI layer).
- Existing prefs panel construction remains backward-compatible when callback is unavailable.
- Verification to run after stage:
- `python3 -m pytest tests/test_controller_services.py tests/test_launch_command_pref.py`

#### Stage 2.3 Detailed Plan: add/adjust UI layout and callback tests
- Objective: lock tab/row placement and callback wiring with focused tests to prevent regression.
- Primary touch points:
- New or updated tests under `tests/` for preferences panel layout/callback behavior.
- Existing no-regression tests: `tests/test_launch_command_pref.py`.
- Proposed test coverage:
- Tab order includes `Controller` immediately after `Overlay`.
- `Launch Controller` control is present on `Controller` tab and appears before moved command rows.
- Launch/toggle command rows are present on `Controller` tab and absent from Overlay tab.
- Launch button callback delegates to runtime launch callback.
- Duplicate-launch policy remains log-only (no new UI message assertions for duplicate path).
- Implementation strategy for testability:
- Prefer direct panel instantiation with lightweight stubs/mocks for callbacks and notebook introspection.
- If widget-tree assertions are too brittle, add narrow helper seams in `PreferencesPanel` for deterministic inspection.
- Acceptance criteria:
- New/updated tests pass and guard tab ordering + control placement + callback delegation.
- Existing launch-command helper tests remain green.
- Verification to run after stage:
- `python3 -m pytest tests/test_launch_command_pref.py tests/test_controller_services.py tests/test_hotkeys.py`
- `python3 -m pytest -k "preferences"`

Phase 2 Outcomes:
- Added a dedicated `Controller` tab in `PreferencesPanel` and inserted it immediately after `Overlay`.
- Moved `Chat command to launch controller` and `Chat command argument to toggle overlay` controls from Overlay tab to Controller tab.
- Added `Launch Controller` button as the first control on the Controller tab and kept it on its own row.
- Added optional `launch_controller_callback` wiring from `load.py::plugin_prefs` into `PreferencesPanel`.
- Added `_on_launch_controller` UI handler that delegates to runtime callback and keeps duplicate-launch feedback log-only.
- Added test coverage for tab/control-order contracts and launch callback delegation.

### Phase 3: Add EDMCHotkeys launch action wiring
- Register a new EDMCHotkeys action to launch the Overlay Controller.
- Label contract: use `Launch Overlay Controller`.
- Reuse the existing launch method; do not duplicate process/thread logic in hotkey layer.
- Keep action callback thread policy aligned with EDMC/Tk expectations.
- Risks: duplicate registration or launch race with existing actions.
- Mitigations: manager lifecycle checks + registration tests + existing runtime launch lock.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Define/register hotkey action metadata (`Launch Overlay Controller`, id, thread policy, cardinality) | Completed |
| 3.2 | Wire launch hotkey callback to runtime launch entrypoint | Completed |
| 3.3 | Add/adjust hotkeys tests for registration and callback behavior | Completed |

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3`.
- Keep current `Overlay On` and `Overlay Off` actions unchanged while adding launch action.
- Avoid changing retry/backoff policy except where needed to include the additional action registration.

#### Stage 3.1 Detailed Plan: define launch hotkey action metadata and registration shape
- Objective: add a deterministic third EDMCHotkeys action definition for controller launch.
- Primary touch points:
- `overlay_plugin/hotkeys.py` action id constants and `_build_hotkeys_actions()`.
- `tests/test_hotkeys.py` metadata assertions.
- Steps:
- Add a dedicated action id constant for launch action (stable namespaced id under `edmcmodernoverlay.hotkeys.*`).
- Extend action list construction to include launch action metadata:
- label: `Launch Overlay Controller`
- plugin: existing plugin name
- callback: launch callback method (added in Stage 3.2)
- thread policy: `main`
- cardinality: `single`
- enabled: `True`
- Keep existing on/off action metadata unchanged.
- Keep registration deterministic (fixed action list ordering) so tests can assert expected outputs.
- Acceptance criteria:
- Hotkeys action builder returns three actions: On, Off, Launch (or explicitly documented deterministic order).
- Launch action label/id/thread policy/cardinality exactly match contract.
- Verification to run after stage:
- `python3 -m pytest tests/test_hotkeys.py -k "registers_overlay_actions"`

#### Stage 3.2 Detailed Plan: wire launch action callback to runtime launch entrypoint
- Objective: route hotkey launch action through existing runtime launch path without duplicating logic.
- Primary touch points:
- `overlay_plugin/hotkeys.py` manager constructor + callback methods.
- `load.py` HotkeysManager initialization wiring.
- Steps:
- Extend `HotkeysManager` constructor to accept an injected `launch_controller` callable.
- Add `_launch_controller_callback(...)` handler in manager:
- invoke injected runtime callback directly.
- catch/log exceptions defensively at debug/warn level.
- do not emit new user-facing duplicate-launch message (log-only policy preserved).
- Update runtime wiring in `load.py` to pass `_PluginRuntime.launch_overlay_controller`.
- Preserve existing hotkeys start/stop lifecycle and retry behavior.
- Acceptance criteria:
- Launch hotkey path invokes the same runtime entrypoint used by chat/settings button.
- No process/thread logic duplicated in hotkeys module.
- Existing on/off behavior remains unchanged.
- Verification to run after stage:
- `python3 -m pytest tests/test_hotkeys.py tests/test_controller_services.py`

#### Stage 3.3 Detailed Plan: add/adjust hotkeys tests for launch action behavior
- Objective: lock launch-action registration and callback behavior with regression-safe test coverage.
- Primary touch points:
- `tests/test_hotkeys.py`
- Proposed test coverage:
- Registration includes launch action with label `Launch Overlay Controller`.
- Registration metadata for launch action uses `thread_policy="main"` and `cardinality="single"`.
- Launch hotkey callback delegates to injected launch callable exactly once.
- Launch callback exception is handled/logged without raising to caller.
- Existing retry behavior still works when registration import/register paths fail with three-action set.
- Existing on/off callback tests remain green.
- Acceptance criteria:
- Updated hotkeys tests pass and cover launch-action metadata + callback delegation.
- No regression in current on/off registration and retry assertions.
- Verification to run after stage:
- `python3 -m pytest tests/test_hotkeys.py tests/test_launch_command_pref.py tests/test_controller_services.py`

Phase 3 Outcomes:
- Added launch hotkey action id `edmcmodernoverlay.hotkeys.launch_controller`.
- Added launch hotkey action label `Launch Overlay Controller` with `thread_policy="main"` and `cardinality="single"`.
- Extended `HotkeysManager` constructor to accept `launch_controller` callback and wired runtime `launch_overlay_controller` from `load.py`.
- Added `_launch_controller_callback` in `HotkeysManager` that delegates to runtime launch path and handles errors via logging.
- Preserved existing Overlay On/Off hotkey behavior and retry/backoff semantics while expanding registration to three actions.
- Expanded hotkeys tests to cover launch metadata, callback delegation, and three-action registration state.

### Phase 4: Tests, compliance checks, and rollout notes
- Expand automated tests around settings launch callback, hotkey launch action, controller launch services, and unchanged chat-launch behavior.
- Run project checks and document what was run vs. deferred.
- Perform EDMC plugin compliance review against launch-related touch points.
- Risks: gaps in integration coverage across launch entrypoints.
- Mitigations: targeted entrypoint parity tests + smoke checks for current `!ovr` behavior.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Add/extend runtime/controller service tests for launch entrypoint parity | Completed |
| 4.2 | Add/extend prefs/hotkeys tests for launch button + hotkey action | Completed |
| 4.3 | Run checks (`python -m pytest`, targeted `-k`, `make check`, `make test`) and capture outcomes | Completed |
| 4.4 | Complete EDMC compliance yes/no checklist for touched launch code | Completed |

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3` -> `4.4`.
- Keep this phase verification-focused: no new feature scope unless a failing test requires a behavior-preserving fix.
- If a regression fix is needed, keep it minimal and record it under Implementation Results with test evidence.

#### Stage 4.1 Detailed Plan: runtime/controller parity coverage
- Objective: prove all launch entrypoints (chat, settings button, hotkey) converge on the same runtime launch method and guard behavior.
- Primary touch points:
- `tests/test_launch_command_pref.py`
- `tests/test_controller_services.py`
- `tests/test_hotkeys.py`
- `tests/test_preferences_panel_controller_tab.py`
- Coverage goals:
- Chat command path still triggers `launch_overlay_controller`.
- Settings button callback triggers `launch_overlay_controller`.
- Hotkey launch callback triggers `launch_overlay_controller`.
- Duplicate-launch guard behavior still enforced by runtime/controller services.
- Acceptance criteria:
- Tests explicitly assert parity/delegation to the same launch entrypoint for all three paths.
- No new direct subprocess/process-control logic appears in UI/hotkeys layers.
- Verification to run after stage:
- `python3 -m pytest tests/test_launch_command_pref.py tests/test_controller_services.py tests/test_hotkeys.py tests/test_preferences_panel_controller_tab.py`

#### Stage 4.2 Detailed Plan: prefs/hotkeys regression expansion
- Objective: harden UI/hotkeys regression coverage for tab layout and hotkey metadata/callback behavior.
- Primary touch points:
- `tests/test_preferences_panel_controller_tab.py`
- `tests/test_hotkeys.py`
- `tests/test_preferences_persistence.py`
- Coverage goals:
- Controller tab order and first-control ordering remain locked.
- Launch/toggle command controls remain on Controller tab.
- Launch hotkey action metadata remains:
- label: `Launch Overlay Controller`
- thread policy/cardinality: `main` / `single`
- id: `edmcmodernoverlay.hotkeys.launch_controller`
- Launch hotkey callback handles callback exceptions without crashing.
- Preferences persistence remains unchanged for touched fields/config keys.
- Acceptance criteria:
- New/updated tests pass and protect Phase 2/3 contracts.
- No regression in on/off hotkeys behavior tests.
- Verification to run after stage:
- `python3 -m pytest tests/test_preferences_panel_controller_tab.py tests/test_hotkeys.py tests/test_preferences_persistence.py`

#### Stage 4.3 Detailed Plan: run checks and capture outcomes
- Objective: execute agreed test/check commands and document exact results, including blocked/deferred runs with reasons.
- Command plan:
- Targeted headless pass:
- `python3 -m pytest tests/test_hotkeys.py tests/test_launch_command_pref.py tests/test_controller_services.py tests/test_preferences_panel_controller_tab.py tests/test_preferences_persistence.py`
- Additional targeted pass (if needed for confidence):
- `python3 -m pytest tests/test_journal_commands.py`
- Project checks:
- `make check`
- `make test`
- Environment caveat handling:
- If broad pytest collection fails due unrelated PyQt overlay-client import issues, record as environment limitation and keep targeted verification as release evidence for plugin-side changes.
- Acceptance criteria:
- Every executed command is recorded with pass/fail outcome.
- Any skipped/blocked command includes explicit reason and impact assessment.
- Verification artifact format:
- Add a `Tests Run For Phase 4` subsection under Implementation Results with command/result bullets.

#### Stage 4.4 Detailed Plan: EDMC compliance yes/no review for touched code
- Objective: complete a focused compliance review for launch-related changes and document evidence.
- Review scope (touched files):
- `load.py`
- `overlay_plugin/preferences.py`
- `overlay_plugin/hotkeys.py`
- `tests/test_hotkeys.py`
- `tests/test_preferences_panel_controller_tab.py`
- Checklist format (must be filled with `Yes`/`No`):
- EDMC plugin entrypoint/layout requirements unchanged (`plugin_start3`, plugin directory conventions).
- Logging uses plugin logger patterns (no `print`, exceptions logged with context).
- Optional integrations are guarded (EDMCHotkeys optional import/retry behavior preserved).
- Tk safety preserved (UI handlers remain on main thread; no off-thread widget manipulation added).
- Runtime launch remains worker-thread/process path (no UI thread blocking launch mechanics introduced).
- Preferences/config handling remains EDMC-compatible (`config` helpers, namespaced keys; no raw new config anti-patterns).
- Hotkey metadata uses explicit `thread_policy="main"` and `cardinality="single"`.
- Acceptance criteria:
- Compliance section completed with `Yes`/`No`, evidence, and remediation notes for any `No`.
- Any `No` item gets a follow-up action entry before phase sign-off.

Phase 4 Outcomes:
- Added launch-entrypoint parity test coverage in `tests/test_launch_entrypoint_parity.py` to validate chat, settings button, and hotkey launch paths delegate to the same runtime callable.
- Re-ran targeted launch/hotkeys/preferences suites plus journal command coverage.
- Ran `make check` and `make test` successfully in the project test environment.
- Completed EDMC compliance checklist for launch-related touched files with documented evidence and one environment caveat (EDMC baseline Python mismatch in local dev interpreter).

### Phase 5: Addendum A - immediate launch for settings button + hotkey
- Add source-aware launch behavior so settings/hotkey paths skip countdown while chat retains existing countdown behavior.
- Preserve existing runtime launch guard semantics (already launching/running) and log-only duplicate feedback policy.
- Keep launch mechanics on worker thread path; no Tk/UI work off main thread.
- Risks: entrypoint behavior drift (chat accidentally skips countdown, or settings/hotkey still countdown).
- Mitigations: explicit source enum/flag, targeted tests for all entrypoints, and parity assertions for shared launch infrastructure.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Introduce source-aware launch mode contract (`chat` = countdown, `settings/hotkey` = immediate) | Completed |
| 5.2 | Wire settings/hotkey launch callbacks to immediate mode and keep chat path unchanged | Completed |
| 5.3 | Add/extend tests for countdown policy by entrypoint + run targeted verification | Completed |

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.
- Keep behavior changes narrowly scoped to countdown policy by entrypoint.
- Do not alter launch guard semantics, process spawn logic, or config persistence behavior in this phase.

#### Phase 5 Design Record
- Shared launch infrastructure remains centralized:
- `load._PluginRuntime.launch_overlay_controller(...)` remains single runtime entrypoint.
- `overlay_plugin/controller_services.launch_controller(...)` remains guard/thread boundary.
- Countdown policy becomes explicit and source-aware:
- chat caller requests countdown-enabled launch.
- settings button and hotkey callers request countdown-disabled launch.
- Logging/UX policy remains unchanged:
- duplicate-launch handling stays log-only for settings/hotkey.
- no new user-facing duplicate-launch status messages introduced.

#### Stage 5.1 Detailed Plan: source-aware launch mode contract
- Objective: define an explicit runtime contract for countdown behavior by launch source.
- Primary touch points:
- `load.py` (`launch_overlay_controller` API and call sites).
- `overlay_plugin/controller_services.py` (`controller_launch_sequence` countdown invocation).
- `overlay_plugin/journal_commands.py` (chat launch caller).
- `overlay_plugin/preferences.py` (settings button caller).
- `overlay_plugin/hotkeys.py` (hotkey launch caller).
- Contract:
- `chat` source -> retain current countdown behavior.
- `settings` and `hotkey` sources -> skip countdown and launch immediately.
- API proposal (implementation-level):
- add a runtime-level launch mode/source argument (for example `launch_overlay_controller(source=...)` or `launch_overlay_controller(skip_countdown=...)`).
- thread the value into `controller_launch_sequence(...)` so countdown call is conditional.
- default mode remains countdown-enabled to preserve existing chat behavior.
- keep public behavior backward-compatible for existing call sites that do not pass the new argument.
- Acceptance criteria:
- Countdown behavior is controlled by explicit source/mode, not inferred indirectly.
- Existing launch guard behavior remains centralized and unchanged.
- Verification to run after stage:
- `python3 -m pytest tests/test_controller_services.py tests/test_launch_command_pref.py`

#### Stage 5.2 Detailed Plan: wire immediate launch for settings/hotkey
- Objective: route settings button and hotkey launch calls through immediate mode without changing chat command path.
- Steps:
- Extend runtime/hotkey/settings callback wiring to pass source-aware launch mode.
- Ensure chat command helper continues to call chat-mode launch (countdown preserved).
- Ensure settings button and hotkey callbacks call immediate-mode launch.
- Keep duplicate-launch feedback log-only for settings/hotkey as already locked.
- Wiring map:
- `overlay_plugin/journal_commands.py` launch callback path -> countdown-enabled mode.
- `overlay_plugin/preferences.py` `_on_launch_controller` path -> immediate mode.
- `overlay_plugin/hotkeys.py` `_launch_controller_callback` path -> immediate mode.
- `load.py` runtime wiring updates for settings/hotkey callback adapters as needed.
- `overlay_plugin/controller_services.py` conditionally invoke countdown based on mode.
- Acceptance criteria:
- Settings/hotkey launch no longer waits 3 seconds.
- Chat launch still performs countdown.
- No direct subprocess launch code added in UI/hotkeys layers.
- Verification to run after stage:
- `python3 -m pytest tests/test_hotkeys.py tests/test_preferences_panel_controller_tab.py tests/test_journal_commands.py`

#### Stage 5.3 Detailed Plan: tests and verification for entrypoint-specific countdown behavior
- Objective: lock countdown policy with explicit regression coverage.
- Coverage goals:
- Chat launch path triggers countdown hook.
- Settings button launch path skips countdown hook.
- Hotkey launch path skips countdown hook.
- Shared launch guards still block duplicate launches consistently.
- Suggested test additions/updates:
- add/extend controller-service tests to assert countdown invocation toggles by mode.
- add/extend parity test to assert delegation still converges on shared runtime launch callable while honoring source mode.
- add/extend settings/hotkey tests to ensure immediate mode is requested by those callers.
- keep existing chat command tests green as regression anchor for unchanged chat behavior.
- Verification commands:
- `python3 -m pytest tests/test_controller_services.py tests/test_hotkeys.py tests/test_preferences_panel_controller_tab.py tests/test_journal_commands.py tests/test_launch_entrypoint_parity.py`
- `make test` (or scoped fallback if environment constraints require).
- Acceptance criteria:
- All new/updated tests pass and prove entrypoint-specific countdown behavior.
- Results are recorded under Implementation Results before phase sign-off.

## Test Plan (Per Iteration)
- Env setup (once per machine):
- `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- Headless quick pass after each stage:
- `source .venv/bin/activate && python -m pytest -k "controller_services or hotkeys or launch_command_pref or preferences"`
- Milestone checks:
- `source .venv/bin/activate && python -m pytest`
- `make check`
- `make test`
- GUI-enabled suite once wiring lands (as applicable):
- set required env flag(s), then run full suite with GUI deps installed.

## Implementation Results
- Phase 1 implemented on 2026-03-04.
- Phase 2 implemented on 2026-03-04.
- Phase 3 implemented on 2026-03-04.
- Phase 4 implemented on 2026-03-04.
- Phase 5 implemented on 2026-03-04.

### Phase 1 Execution Summary
- Stage 1.1 completed:
- Verified chat launch still routes through runtime callback path (`journal_commands` -> `launch_overlay_controller` -> `controller_services.launch_controller`).
- Verified duplicate-launch guards remain in the centralized runtime launch service (`launch already in progress` / `already running` checks).
- Verified launch continues to execute on worker thread path (`OverlayControllerLaunch` thread), preserving Tk main-thread safety for UI.
- Stage 1.2 completed:
- Locked UI contract in this plan: new `Controller` tab after `Overlay`, `Launch Controller` first control on its own row, launch/toggle chat command controls moved to the tab.
- Locked hotkey contract in this plan: one launch action labeled `Launch Overlay Controller`, callback delegates to `launch_overlay_controller`.
- Stage 1.3 completed:
- Locked duplicate-launch behavior to log-only for settings/hotkey entrypoints in this change.
- Confirmed scope guard remains explicit: no launch options/profiles/CLI passthrough in this milestone.

### Tests Run For Phase 1
- Attempted broad selectors (blocked during collection by unrelated `overlay_client` PyQt import errors in this environment):
- `python3 -m pytest -k "journal_commands or controller_services or launch_command_pref"`
- `python3 -m pytest -k "hotkeys or preferences"`
- Targeted verification (passed):
- `python3 -m pytest tests/test_journal_commands.py tests/test_controller_services.py tests/test_launch_command_pref.py tests/test_hotkeys.py`
- Result: 32 passed, 0 failed.

### Phase 2 Execution Summary
- Stage 2.1 completed:
- Added `Controller` tab layout in preferences and ordered tabs as `Overlay`, `Controller`, `Experimental`.
- Moved launch/toggle chat command rows onto the `Controller` tab.
- Stage 2.2 completed:
- Added `Launch Controller` button as first row on `Controller` tab.
- Added `PreferencesPanel` launch callback injection and `load.plugin_prefs` wiring to `_plugin.launch_overlay_controller`.
- Kept duplicate-launch feedback log-only by handling callback exceptions via debug logging only (no new UI status message path).
- Stage 2.3 completed:
- Added `tests/test_preferences_panel_controller_tab.py` covering tab/control-order contract helpers and launch callback delegation.
- Added plugin prefs wiring assertion for `launch_controller_callback`.
- Re-ran launch/hotkeys regression tests.

### Tests Run For Phase 2
- Targeted Phase 2 suite (passed):
- `python3 -m pytest tests/test_preferences_panel_controller_tab.py tests/test_launch_command_pref.py tests/test_controller_services.py tests/test_hotkeys.py`
- Result: 16 passed, 0 failed.
- Additional persistence regression check (passed):
- `python3 -m pytest tests/test_preferences_persistence.py`
- Result: 3 passed, 0 failed.

### Phase 3 Execution Summary
- Stage 3.1 completed:
- Added launch action constants and metadata in `overlay_plugin/hotkeys.py`:
- id: `edmcmodernoverlay.hotkeys.launch_controller`
- label: `Launch Overlay Controller`
- thread policy/cardinality: `main` / `single`
- Stage 3.2 completed:
- Added launch callback injection to `HotkeysManager` and wired `load._PluginRuntime.launch_overlay_controller` into manager initialization.
- Added `_launch_controller_callback` handler that delegates launch and logs failures defensively.
- Stage 3.3 completed:
- Extended `tests/test_hotkeys.py` to assert launch-action registration metadata and launch callback behavior.
- Updated existing hotkeys registration-state tests for the three-action registration set.

### Tests Run For Phase 3
- Targeted Phase 3 + regression suite (passed):
- `python3 -m pytest tests/test_hotkeys.py tests/test_launch_command_pref.py tests/test_controller_services.py tests/test_preferences_panel_controller_tab.py tests/test_preferences_persistence.py`
- Result: 21 passed, 0 failed.

### Phase 4 Execution Summary
- Stage 4.1 completed:
- Added `tests/test_launch_entrypoint_parity.py` to assert chat, settings button, and hotkey launch entrypoints all delegate to the same runtime launch callable.
- Confirmed runtime/controller guard behavior coverage remains in existing controller service tests.
- Stage 4.2 completed:
- Expanded regression coverage via parity + existing preferences/hotkeys tests (tab ordering, first-control ordering, hotkey launch metadata/callback behavior).
- Stage 4.3 completed:
- Executed targeted pytest passes, additional journal command pass, and full project checks (`make check`, `make test`).
- Stage 4.4 completed:
- Completed compliance yes/no checklist below for touched launch files and recorded the EDMC baseline Python caveat.

### Tests Run For Phase 4
- Targeted launch parity + regression suite (passed):
- `python3 -m pytest tests/test_hotkeys.py tests/test_launch_command_pref.py tests/test_controller_services.py tests/test_preferences_panel_controller_tab.py tests/test_preferences_persistence.py tests/test_launch_entrypoint_parity.py`
- Result: 22 passed, 0 failed.
- Additional chat-launch regression pass (passed):
- `python3 -m pytest tests/test_journal_commands.py`
- Result: 21 passed, 0 failed.
- Project checks (passed):
- `make check`
- Result: `ruff` passed, `mypy` passed, full pytest passed (482 passed, 25 skipped).
- `make test`
- Result: full pytest passed (482 passed, 25 skipped).
- Baseline compliance script:
- `python3 scripts/check_edmc_python.py`
- Result: failed in local dev interpreter (expected EDMC baseline Python 3.10.3 32-bit; found Python 3.12.3 64-bit).
- `ALLOW_EDMC_PYTHON_MISMATCH=1 python3 scripts/check_edmc_python.py`
- Result: warning-only pass (override for non-release/dev work).

### Phase 4 Compliance Checklist (Yes/No)
- EDMC plugin entrypoint/layout requirements unchanged (`plugin_start3`, plugin directory conventions): Yes.
- Evidence: no changes to plugin entrypoint wiring semantics; plugin remains single-directory plugin with existing `plugin_start3` flow.
- Logging uses plugin logger patterns (no `print`, exceptions logged with context): Yes.
- Evidence: launch button/hotkey callbacks use logger-backed debug/warning handling; no `print` introduced.
- Optional integrations are guarded (EDMCHotkeys optional import/retry behavior preserved): Yes.
- Evidence: `HotkeysManager` import/retry flow unchanged except added launch action registration.
- Tk safety preserved (UI handlers remain on main thread; no off-thread widget manipulation added): Yes.
- Evidence: new UI handler `_on_launch_controller` delegates callback only; no thread spawning or widget access from worker threads added.
- Runtime launch remains worker-thread/process path (no UI thread blocking launch mechanics introduced): Yes.
- Evidence: launch delegation still targets `launch_overlay_controller` -> `controller_services.launch_controller` thread path.
- Preferences/config handling remains EDMC-compatible (`config` helpers, namespaced keys; no raw new config anti-patterns): Yes.
- Evidence: Phase 4 introduced no new preference persistence keys or raw config writes.
- Hotkey metadata uses explicit `thread_policy="main"` and `cardinality="single"`: Yes.
- Evidence: launch action metadata matches existing hotkey metadata contract in `overlay_plugin/hotkeys.py`.

### Phase 5 Execution Summary
- Stage 5.1 completed:
- Added explicit source-aware launch mode support in runtime/services:
- `load._PluginRuntime.launch_overlay_controller(..., source=...)`
- `overlay_plugin/controller_services.launch_controller(..., source=...)`
- `overlay_plugin/controller_services.controller_launch_sequence(..., source=...)`
- Countdown policy now applies by source:
- `chat` keeps countdown.
- `settings` and `hotkey` skip countdown and launch immediately.
- Stage 5.2 completed:
- Updated settings launch wiring in `plugin_prefs` so `Launch Controller` button requests `source="settings"` (immediate launch).
- Updated hotkey wiring in `_PluginRuntime` so EDMCHotkeys launch action requests `source="hotkey"` (immediate launch).
- Kept chat launch wiring unchanged (`journal_commands` still invokes runtime launch entrypoint default mode).
- Stage 5.3 completed:
- Expanded launch tests for source-aware countdown behavior and entrypoint mode routing.
- Preserved duplicate-launch guard behavior and shared launch infrastructure.

### Tests Run For Phase 5
- Targeted Phase 5 verification (passed):
- `python3 -m pytest tests/test_controller_services.py tests/test_hotkeys.py tests/test_preferences_panel_controller_tab.py tests/test_journal_commands.py tests/test_launch_entrypoint_parity.py tests/test_launch_command_pref.py`
- Result: 42 passed, 0 failed.
- Project test target (passed):
- `make test`
- Result: 484 passed, 25 skipped.
- Project check target (passed):
- `make check`
- Result: `ruff` passed, `mypy` passed, full pytest passed (484 passed, 25 skipped).
