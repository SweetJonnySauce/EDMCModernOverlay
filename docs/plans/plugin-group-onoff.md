## Goal: Implement true plugin-group on/off controls (not opacity emulation) across runtime, controls, and docs.

Follow persona details in `AGENTS.md`.
Document implementation results in the `Implementation Results` section.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear, capture it under `Open Questions`.

## Requirements (Initial)
- Implement true enabled/disabled behavior for plugin groups; this is not opacity-based emulation.
- Scope this as a CMDR/user setting and runtime control; do not add this to `define_plugin_group` in this change.
- Granularity is plugin group; each plugin group can be turned on/off independently.
- Drop disabled plugin-group payloads as early as possible to minimize processing/render overhead.
- Use plugin runtime as the authoritative visibility gate for plugin-group on/off; client remains a defensive fallback.
- Achieve authoritative runtime gating via shared resolver extraction so plugin runtime and client reuse one payload-to-group resolution path.
- Roll out authoritative runtime gating safely with staged parity validation before full cutover.
- Refactor existing overlay-level on/off behavior paths that currently use payload opacity `0` to use true on/off behavior.
- Preserve all existing opacity semantics aside from on/off behavior changes.
- Extend EDMCHotkeys actions:
- `Overlay On` and `Overlay Off` should support optional payload JSON with plugin groups; no payload means whole overlay.
- Add `Toggle Overlay` action with the same payload semantics.
- Extend chat commands:
- Add explicit `on` and `off` arguments (with optional plugin-group targeting).
- Preserve/extend toggle behavior.
- Coerce ordering/phrasing so these forms are equivalent for `on`/`off`/`toggle`:
- `!ovr on "BGS-Tally Objectives"`
- `!ovr "BGS-Tally Objectives" on`
- `!ovr turn "BGS-Tally Objectives" on`
- `!ovr turn on "BGS-Tally Objectives"`
- Note: `"BGS-Tally Objectives"` is an example plugin-group name in these command examples.
- Add overlay controller UI checkbox for plugin-group on/off control.
- In Overlay Controller UI, place the plugin-group on/off checkbox immediately above the `Reset` button.
- Add equivalent on/off control in `utils/plugin_group_manager.py`.
- Provide an easy way to inspect current on/off states for plugin groups (chat command list is a candidate).
- Design for future rule-layer gating defined via `define_plugin_group` without implementing rules now.
- Use a hybrid disabled-group behavior: drop disabled groups from continuous ingest/render processing, while retaining minimal last-known metadata snapshots for controller/group targeting UX.
- Hybrid retained metadata while off is limited to last-known `bounds` and timestamps.
- Hybrid timestamp fields are `last_payload_seen_at` and `last_bounds_updated_at`.
- Canonical group identity for CMDR controls is `plugin_group_name` (same label shown in Overlay Controller dropdown).
- Targeted `on` must work even when all groups are currently off.
- Unset per-group state defaults to `on`.
- Whole-overlay on/off actions (no payload) should apply explicit state updates across currently defined plugin groups from resolved runtime config.
- No separate persisted global overlay enabled flag; global on/off is implemented as bulk per-group state updates.
- Stale removed/renamed group entries in `overlay_groupings.user.json` are not targets for whole-overlay no-payload on/off and are not auto-pruned in this change.
- Persist CMDR on/off state in `overlay_groupings.user.json`.
- Hotkey payload format should use `{"plugin_group": "..."}` with optional multi-group list support via `plugin_groups`; if both are provided, union + dedupe targets before applying.
- Unknown plugin-group names should be ignored with one warning per unknown group in EDMC logs.
- Group-state list command should output to overlay text; when EDMC log level is DEBUG, also emit to EDMC logs.
- Use `status` as the one-word chat command argument for listing plugin-group on/off states.
- `status` output should be alphabetically sorted by `plugin_group_name`, one group per line, formatted as `<plugin_group_name>: On|Off` (example: `BGS-Tally Colonisation: On`).
- Chat command arguments should be simplified to one-word action tokens.
- Supported chat-command action tokens: `on`, `off`, `toggle` (with `toggle` also honoring the configurable pref argument; default `t`).
- Off groups remain visible/editable in Overlay Controller and `plugin_group_manager`.
- Ignore legacy opacity-based logical-off state during migration; initialize true on/off from defaults and document this in release notes.

## Non-Functional Requirements
- Avoid adding substantive new logic to existing monolith modules (especially `load.py`).
- Prefer extracting new behavior into focused modules/services with explicit interfaces.
- Keep monolith changes to minimal orchestration/wiring only (imports, delegation, hook calls).
- Preserve behavior parity while refactoring; no silent regressions.
- Use staged rollout controls (parity checks and temporary fallback path) for resolver extraction and runtime authoritative gating.

## Out Of Scope (This Change)
- Implementing rule evaluation or rule-driven automatic on/off.
- Changing plugin-author APIs (`define_plugin_group`) for CMDR on/off control in this iteration.

## Current Touch Points
- Code:
- `load.py` (runtime payload ingest/broadcast, CLI command handling, preference rebroadcast, hotkey wiring)
- `overlay_client/render_surface.py` (ingest + paint path; likely early-drop gate location)
- `overlay_client/payload_model.py` (payload storage; potential early-drop seam)
- `overlay_client/grouping_helper.py` and `overlay_client/group_coordinator.py` (group identity mapping)
- `overlay_plugin/journal_commands.py` (chat command parsing/coercion and dispatch)
- `overlay_plugin/hotkeys.py` (EDMCHotkeys action registration/callback handling)
- `overlay_plugin/preferences.py` (settings persistence, UI wiring)
- `overlay_controller/overlay_controller.py` and `overlay_controller/controller/*` (controller checkbox and persistence flow)
- `utils/plugin_group_manager.py` (group manager UI/CLI controls)
- `overlay_plugin/overlay_config_payload.py` (config contract if enabled-state payload is propagated)
- Tests:
- `tests/test_journal_commands.py`
- `tests/test_hotkeys.py`
- `tests/test_preferences_persistence.py`
- `tests/test_controller_services.py`
- `overlay_client/tests/test_data_client.py`
- `overlay_client/tests/test_grouping_helper.py`
- `overlay_client/tests/test_interaction_controller.py`
- `overlay_controller/tests/test_group_state_service.py`
- Docs/notes:
- `docs/wiki/Chat-Command.md`
- `docs/wiki/Overlay-Controller.md`
- `docs/wiki/APIs.md`
- `docs/wiki/Usage.md`
- `docs/wiki/Developer-FAQs.md`

## Assumptions
- Plugin-group identity used for placement (`plugin` + group label/prefix) is stable enough to key enabled-state.
- Existing payload opacity controls remain available for visual transparency and are not redefined as logical on/off.
- Disabled plugin groups should still be editable in controller/group manager even when not rendered.

## Risks
- Risk: Ambiguous plugin-group identifiers across payload sources (label vs prefix vs plugin+group tuple) cause mismatched toggles.
- Mitigation: Define and lock a canonical key format early, with normalization and compatibility aliases.
- Risk: Early-drop point chosen too late keeps most processing cost, or too early breaks cache/controller previews.
- Mitigation: instrument pipeline stage counters and validate behavior with targeted tests.

## Open Questions
- None currently.

## Decisions (Locked)
- Logical on/off is separate from opacity and must not be implemented by forcing opacity to zero.
- On/off control is CMDR-facing at plugin-group granularity.
- Future rule-layer gating must be designed for (state composition model) but not implemented now.
- Canonical identifier is `plugin_group_name` (Overlay Controller dropdown label).
- Targeted `on` works even when all groups are currently off.
- Persistence location is `overlay_groupings.user.json`.
- Unknown groups are ignored with one warning per unknown group in EDMC logs.
- Group-state list outputs to overlay text and to EDMC logs when log level is DEBUG.
- One-word list argument is `status`.
- `status` output format is alphabetical by `plugin_group_name`, one line per group as `<plugin_group_name>: On|Off`.
- Chat-command action tokens are `on`, `off`, and `toggle`; toggle also supports the configurable pref token (default `t`).
- Off groups remain visible/editable in Overlay Controller and `plugin_group_manager`.
- Hotkey payload supports `plugin_group` plus optional `plugin_groups` list for multi-group targeting.
- If both `plugin_group` and `plugin_groups` are provided, targets are unioned and deduplicated.
- Authoritative gate is plugin runtime; client-side filter remains as defensive fallback.
- Authoritative runtime gating will be implemented using shared resolver extraction (single payload-to-group resolution path used by plugin runtime and client).
- Authoritative runtime gating must be introduced with a safe staged rollout (parity validation before full cutover).
- Disabled groups use hybrid handling: no continuous ingest/render processing while off, but minimal last-known metadata is retained for controller/group targeting usability.
- Hybrid retained metadata is limited to last-known bounds and timestamps (`last_payload_seen_at`, `last_bounds_updated_at`).
- State composition rule: per-group override wins when present; unset per-group state defaults to `on`.
- Whole-overlay on/off (no payload) applies explicit updates to currently defined groups from resolved runtime config only.
- No separate persisted global overlay enabled flag; whole-overlay on/off is bulk per-group updates.
- Stale removed/renamed groups present only in persisted user state are ignored for whole-overlay no-payload on/off and are not auto-pruned in this change.
- Migration rule: ignore legacy opacity-based logical off values and start true on/off from defaults.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Requirements + contracts + state model | Completed |
| 2 | Runtime early-drop + state plumbing | Pending |
| 3 | Commands/hotkeys/controller/group-manager UX | Pending |
| 4 | Refactor legacy opacity-on/off paths + docs | Pending |
| 5 | Validation/perf checks + rollout notes | Pending |

## Phase Details

### Phase 1: Requirements + Contracts + State Model
- Lock requirements, identifiers, state composition, persistence location, and command grammar before code changes.
- Risks: unresolved ambiguity in identifier and bulk-vs-targeted command sequencing semantics.
- Mitigations: lock decisions with examples and acceptance tests first.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Define canonical plugin-group key and command payload schema | Completed |
| 1.2 | Define enabled-state model (per-group + bulk global command semantics) and persistence | Completed |
| 1.3 | Define safe rollout plan for authoritative runtime gating | Completed |

#### Stage 1.1 Detailed Plan
- Objective:
- Lock a canonical identifier and accepted input coercions for chat/hotkey/control flows.
- Primary touch points:
- `overlay_plugin/journal_commands.py`
- `overlay_plugin/hotkeys.py`
- `load.py`
- Steps:
- Define accepted payload schema for actions (single/multi-group).
- Define chat parsing normalization for order-insensitive phrases.
- Capture examples and error handling strategy for unknown groups, including one EDMC log warning per unknown group.
- Acceptance criteria:
- Canonical key format and coercion rules documented with examples.
- Payload schema for hotkeys/actions and chat is unambiguous.
- Verification to run:
- `source .venv/bin/activate && python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py -k "command or toggle or payload"`

#### Stage 1.2 Detailed Plan
- Objective:
- Define per-group state semantics, bulk global command behavior, and persistence model.
- Steps:
- Document command sequencing semantics for: bulk off + targeted on, bulk on + targeted off, and unset group state (defaults on).
- Document whole-overlay behavior: no-payload on/off applies explicit updates only to currently defined groups from resolved runtime config.
- Document that there is no separate persisted global enabled flag (global on/off is bulk per-group updates).
- Document stale-entry behavior: stale removed/renamed groups in persisted user state are ignored and not auto-pruned in this change.
- Document migration behavior: ignore opacity-based legacy logical-off state and initialize from defaults.
- Define how future rule-layer gating composes with CMDR state.
- Acceptance criteria:
- State machine table documented and approved.
- Persistence file format and migration behavior documented.
- Verification to run:
- `source .venv/bin/activate && python -m pytest tests/test_preferences_persistence.py -k "opacity or toggle or persistence"`

#### Stage 1.3 Detailed Plan
- Objective:
- Define the safe implementation rollout for locked architecture: plugin runtime authoritative gate with shared resolver extraction and client fallback.
- Steps:
- Define resolver extraction boundaries and shared interface contract.
- Define parity validation strategy between runtime and client resolution results.
- Define staged activation/cutover approach with rollback path.
- Define counters/logging used to verify reduced processing overhead.
- Acceptance criteria:
- Safe staged rollout plan approved, including parity checks and rollback.
- Measurable pre/post criteria documented.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests -k "data_client or render_surface or payload_model"`

#### Phase 1 Execution Order
- Implement in strict order: `1.1` -> `1.2` -> `1.3`.

#### Phase 1 Exit Criteria
- Canonical contracts are locked and open questions resolved or explicitly deferred.
- Safe rollout plan for runtime authoritative gating and persistence model are approved.

### Phase 2: Runtime Early-Drop + State Plumbing
- Implement state plumbing and early-drop behavior while preserving existing rendering/opacity semantics.
- Risks: regressions in cycle/controller/debug behavior when groups are off.
- Mitigations: gate with explicit tests and logging.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add per-group enabled-state storage and propagation (no global persisted flag) | Pending |
| 2.2 | Implement early-drop gate with hybrid metadata retention | Pending |
| 2.3 | Add state inspection/list command backend support (`status` formatter) | Pending |

#### Stage 2.1 Detailed Plan
- Objective:
- Add data structures and message contracts for per-group enabled state plus bulk global command semantics.
- Primary touch points:
- `load.py`
- `overlay_plugin/overlay_config_payload.py`
- `overlay_client/developer_helpers.py`
- Steps:
- Introduce state container and serialization contract.
- Wire runtime updates to client/controller pathways.
- Add persistence read/write path.
- Ensure there is no separate persisted global enabled flag.
- Acceptance criteria:
- State persists and propagates without affecting unrelated config.
- Persistence stores per-group state only; global no-payload commands operate as bulk updates.
- Verification to run:
- `source .venv/bin/activate && python -m pytest tests/test_runtime_services.py tests/test_controller_services.py`

#### Stage 2.2 Detailed Plan
- Objective:
- Drop disabled-group payloads before expensive transforms/render command generation.
- Steps:
- Implement gate at approved stage.
- Retain hybrid metadata only (`bounds`, `last_payload_seen_at`, `last_bounds_updated_at`) for disabled groups.
- Preserve overlays for enabled groups and all opacity behavior.
- Add debug counters/log lines for dropped payloads.
- Acceptance criteria:
- Disabled groups no longer incur full render path cost.
- Disabled groups keep only the locked hybrid metadata and do not continue full ingest/transform while off.
- Enabled groups behave unchanged.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests -k "render_surface or grouping_helper or payload_bounds"`

#### Stage 2.3 Detailed Plan
- Objective:
- Provide backend support for listing current group on/off state.
- Steps:
- Add query method and output formatter.
- Integrate with chat command dispatcher (final command grammar implemented in Phase 3).
- Format `status` output alphabetically by `plugin_group_name`, one line per group as `<plugin_group_name>: On|Off`.
- Acceptance criteria:
- State listing is available from runtime with stable, alphabetical one-line-per-group format.
- Verification to run:
- `source .venv/bin/activate && python -m pytest tests/test_journal_commands.py -k "plugins or state or list"`

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.

#### Phase 2 Exit Criteria
- True on/off behavior exists in runtime with early-drop and persistence.
- State inspection backend works for command/UI consumers.

### Phase 3: Commands, Hotkeys, Controller, Group Manager
- Implement user controls across chat, hotkeys actions, overlay controller, and plugin_group_manager.
- Risks: UX inconsistency between channels and unclear error feedback.
- Mitigations: single normalization helper and shared validation.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Extend chat commands for on/off/toggle/status with phrase coercion | Pending |
| 3.2 | Extend hotkeys actions (On/Off payload-aware + new Toggle action) | Pending |
| 3.3 | Add plugin-group on/off checkbox in controller and `plugin_group_manager` | Pending |

#### Stage 3.1 Detailed Plan
- Objective:
- Support flexible chat phrasing/order, optional plugin-group targeting, and `status` output.
- Steps:
- Implement argument normalizer/parser for `on/off/toggle` forms.
- Include equivalent parsing for `!ovr on "<group>"`, `!ovr "<group>" on`, `!ovr turn "<group>" on`, and `!ovr turn on "<group>"`.
- Implement `status` chat argument output using backend formatter.
- Emit one EDMC log warning per unknown group targeted by chat command.
- Wire to runtime state updates and list command output.
- Acceptance criteria:
- Equivalent chat forms resolve identically.
- Global and targeted updates both work.
- `status` output matches locked alphabetical one-line format.
- Unknown groups are ignored and generate one EDMC warning per group.
- Verification to run:
- `source .venv/bin/activate && python -m pytest tests/test_journal_commands.py`

#### Stage 3.2 Detailed Plan
- Objective:
- Update EDMCHotkeys actions to support global and targeted on/off/toggle.
- Steps:
- Add `Toggle Overlay` action registration and callback.
- Extend `Overlay On`/`Overlay Off` payload handling for one or many groups.
- If both `plugin_group` and `plugin_groups` are supplied, union + dedupe targets before state updates.
- Emit one EDMC log warning per unknown group in hotkey payload targets.
- Acceptance criteria:
- Actions work with and without payload.
- Backward compatibility maintained for existing on/off use.
- Unknown groups are ignored and warned per group without failing action execution.
- Verification to run:
- `source .venv/bin/activate && python -m pytest tests/test_hotkeys.py tests/test_toggle_helpers.py`

#### Stage 3.3 Detailed Plan
- Objective:
- Add on/off controls to overlay controller and `utils/plugin_group_manager.py`.
- Steps:
- Add checkbox control and persistence wiring in controller.
- Place the controller checkbox immediately above the `Reset` button.
- Add corresponding control in plugin_group_manager tool.
- Ensure both surfaces reflect current state and handle missing groups safely.
- Acceptance criteria:
- CMDR can toggle group on/off in both tools with immediate effect.
- Controller placement matches requirement: checkbox appears immediately above `Reset`.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_controller/tests tests/test_plugin_group_manager_api.py`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3`.

#### Phase 3 Exit Criteria
- All requested control surfaces can manage global and plugin-group on/off.
- Command/hotkey/controller behavior is consistent.

### Phase 4: Refactor Legacy Overlay On/Off Paths + Documentation
- Migrate old opacity-based toggles for logical on/off and document full action usage.
- Risks: accidental opacity regressions.
- Mitigations: preserve opacity tests and add explicit non-regression checks.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Refactor existing logical on/off paths away from opacity emulation | Pending |
| 4.2 | Add new wiki page for actions (all actions, not only on/off) | Pending |
| 4.3 | Update existing wiki pages and in-repo docs for new behavior | Pending |

#### Stage 4.1 Detailed Plan
- Objective:
- Replace current global toggle semantics that rely on `global_payload_opacity=0` for logical off behavior.
- Steps:
- Identify all old on/off call sites (chat, hotkeys, helpers).
- Route logical on/off through new state model while leaving opacity controls intact.
- Acceptance criteria:
- Logical on/off no longer depends on opacity side effects.
- Opacity slider and per-payload alpha behavior remain unchanged.
- Verification to run:
- `source .venv/bin/activate && python -m pytest tests/test_toggle_helpers.py tests/test_preferences_persistence.py overlay_client/tests/test_opacity_utils.py`

#### Stage 4.2 Detailed Plan
- Objective:
- Create `docs/wiki` action usage page that documents all supported actions.
- Steps:
- Add new markdown with hotkey payload format, chat examples, and behavior matrix.
- Include global vs targeted examples, `status` output example, and unknown-group warning behavior.
- Acceptance criteria:
- New doc exists and covers all actions end-to-end.
- Verification to run:
- `source .venv/bin/activate && python -m pytest -k "docs" || true`

#### Stage 4.3 Detailed Plan
- Objective:
- Update existing related docs to align terminology and commands.
- Steps:
- Update `Chat-Command`, `Overlay-Controller`, and `Usage` docs.
- Ensure references to opacity-based off semantics are corrected.
- Acceptance criteria:
- No contradictory docs remain.
- Verification to run:
- `source .venv/bin/activate && python -m pytest -k "journal_commands or hotkeys"`

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- Legacy logical on/off emulation paths are removed/refactored.
- Documentation is complete and consistent.

### Phase 5: Validation, Performance, and Rollout Guidance
- Final validation pass with regression, targeted performance checks, and release guidance.
- Risks: hidden regressions across platform-specific behavior.
- Mitigations: targeted + broad tests and manual checklist.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Add/expand automated tests for new state model and command coercion | Pending |
| 5.2 | Validate processing overhead improvements and no-op behavior | Pending |
| 5.3 | Final compatibility review + release notes updates | Pending |

#### Stage 5.1 Detailed Plan
- Objective:
- Ensure reliable coverage for parsing, state composition, and UI wiring.
- Steps:
- Add unit tests for chat coercion permutations.
- Add tests for bulk-vs-targeted command sequencing and persistence.
- Add tests for `status` formatting (alphabetical, one line per group, `On|Off` casing).
- Add tests for unknown-group warning behavior (one EDMC warning per unknown group).
- Add tests that stale removed/renamed persisted entries are ignored and not auto-pruned.
- Add tests confirming there is no separate persisted global flag.
- Acceptance criteria:
- New behavior covered with deterministic tests.
- Verification to run:
- `source .venv/bin/activate && python -m pytest tests overlay_client/tests overlay_controller/tests`

#### Stage 5.2 Detailed Plan
- Objective:
- Prove disabled groups are dropped before heavy processing.
- Steps:
- Add counters/assertions in tests around dropped payload flow.
- Run targeted perf-style tests or timing assertions where stable.
- Acceptance criteria:
- Measurable evidence that disabled groups avoid full render processing.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests -k "render_surface or data_client or performance"`

#### Stage 5.3 Detailed Plan
- Objective:
- Complete release-readiness checks and compatibility notes.
- Steps:
- Add/update release notes entries for plugin-group true on/off behavior and action/chat syntax changes.
- Explicitly note migration behavior: legacy opacity-based logical-off state is ignored and true on/off initializes from defaults.
- Update migration notes.
- Capture any deferred follow-ups for rule-layer integration.
- Acceptance criteria:
- Release notes and compatibility guidance are ready.
- Verification to run:
- `make check`

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
- Feature is validated, documented, and ready for release.
- Follow-up items are explicitly captured.

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
- Plan created on 2026-03-06.
- Phase 1 completed (requirements/contracts/state model locked; planning only, no code changes).
- Phase 2 not started.
- Phase 3 not started.
- Phase 4 not started.
- Phase 5 not started.

### Phase 1 Execution Summary
- Stage 1.1:
- Completed: canonical key/payload schema and command examples locked.
- Stage 1.2:
- Completed: per-group state model, bulk global semantics, persistence, and migration behavior locked.
- Stage 1.3:
- Completed: runtime-authoritative gating with shared resolver extraction and safe rollout expectations locked.

### Tests Run For Phase 1
- None (planning/documentation phase only; no code/tests executed).

### Phase 2 Execution Summary
- Stage 2.1:
- <result>
- Stage 2.2:
- <result>
- Stage 2.3:
- <result>

### Tests Run For Phase 2
- `<command>`
- Result: <passed/failed/skipped + brief notes>

### Phase 3 Execution Summary
- Stage 3.1:
- <result>
- Stage 3.2:
- <result>
- Stage 3.3:
- <result>

### Tests Run For Phase 3
- `<command>`
- Result: <passed/failed/skipped + brief notes>

### Phase 4 Execution Summary
- Stage 4.1:
- <result>
- Stage 4.2:
- <result>
- Stage 4.3:
- <result>

### Tests Run For Phase 4
- `<command>`
- Result: <passed/failed/skipped + brief notes>

### Phase 5 Execution Summary
- Stage 5.1:
- <result>
- Stage 5.2:
- <result>
- Stage 5.3:
- <result>

### Tests Run For Phase 5
- `<command>`
- Result: <passed/failed/skipped + brief notes>
