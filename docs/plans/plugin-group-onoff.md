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
| 2 | Runtime early-drop + state plumbing | Completed |
| 3 | Commands/hotkeys/controller/group-manager UX | Completed |
| 4 | Refactor legacy opacity-on/off paths + docs | Completed |
| 5 | Validation/perf checks + rollout notes | Completed |
| 6 | Immediate clear on group off | Completed |

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
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py -k "command or toggle or payload"`

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
- `overlay_client/.venv/bin/python -m pytest tests/test_preferences_persistence.py -k "opacity or toggle or persistence"`

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
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "data_client or render_surface or payload_model"`

#### Phase 1 Detailed Execution Plan

| Stage | Goal | Detailed work items | Outputs to document | Validation for completion |
| --- | --- | --- | --- | --- |
| 1.1 | Lock command/target contracts | Build command grammar matrix for `on/off/toggle/status` across supported phrase orders; define single + multi-target payload schema with `plugin_group` and `plugin_groups`; define unknown-group handling and EDMC warning behavior | Grammar matrix, payload schema examples, warning behavior examples in this plan | Contracts are unambiguous and cover all approved examples, including `!ovr turn on "BGS-Tally Objectives"` |
| 1.2 | Lock state/persistence model | Define per-group state model (`unset => on`), bulk no-payload semantics, stale-entry behavior, and migration behavior; define persistence shape in `overlay_groupings.user.json`; define hybrid metadata fields (`bounds`, `last_payload_seen_at`, `last_bounds_updated_at`) | State model table, persistence schema notes, migration notes in this plan | No remaining ambiguity around bulk vs targeted sequencing, stale entries, or migration |
| 1.3 | Lock safe rollout strategy | Define shared resolver extraction interface and boundaries; define runtime-authoritative + client-fallback behavior; define parity checks and rollback path; define counters/observability for early-drop impact | Resolver interface contract notes, rollout stages, parity/rollback checklist | Rollout strategy is specific enough to implement without adding new design decisions during coding |

#### Phase 1 Artifact Checklist
- Command grammar coverage includes `on`, `off`, `toggle`, and `status`.
- Chat phrase coercion examples are explicitly documented and equivalent.
- Hotkey payload schema includes single target, multi-target, and union+dedupe behavior.
- Unknown-group behavior specifies one EDMC warning per unknown group.
- State semantics document `unset => on`.
- Global no-payload behavior is documented as bulk per-group updates with no separate global persisted flag.
- Stale removed/renamed entries are ignored and not auto-pruned.
- Hybrid metadata retention fields are explicitly named.
- Migration behavior explicitly ignores legacy opacity-based logical-off state.
- Safe rollout notes include parity checks and fallback/rollback path.

#### Stage 1.1 Contract Artifacts

| Input example | Normalized command | Target resolution | Notes |
| --- | --- | --- | --- |
| `!ovr on "BGS-Tally Objectives"` | `action=on` | `["BGS-Tally Objectives"]` | Example group name only. |
| `!ovr "BGS-Tally Objectives" on` | `action=on` | `["BGS-Tally Objectives"]` | Equivalent to row above. |
| `!ovr turn "BGS-Tally Objectives" on` | `action=on` | `["BGS-Tally Objectives"]` | Equivalent to row above. |
| `!ovr turn on "BGS-Tally Objectives"` | `action=on` | `["BGS-Tally Objectives"]` | Equivalent to row above. |
| `!ovr off "BGS-Tally Objectives"` | `action=off` | `["BGS-Tally Objectives"]` | Same coercion rules as `on`. |
| `!ovr toggle "BGS-Tally Objectives"` | `action=toggle` | `["BGS-Tally Objectives"]` | Also honor configurable toggle token (default `t`). |
| `!ovr on` | `action=on` | all currently defined groups | Bulk update; no separate global persisted flag. |
| `!ovr off` | `action=off` | all currently defined groups | Bulk update; no separate global persisted flag. |
| `!ovr status` | `action=status` | query only | Output alphabetical by `plugin_group_name`, one line per group: `<plugin_group_name>: On|Off`. |

Hotkey payload schema (contract):

```json
{
  "plugin_group": "BGS-Tally Objectives",
  "plugin_groups": ["BGS-Tally Colonisation", "BGS-Tally Objectives"]
}
```

- `plugin_group` is optional single-target.
- `plugin_groups` is optional multi-target list.
- If both are present, runtime unions and deduplicates targets.
- Unknown target names are ignored and emit one EDMC warning per unknown group.

#### Stage 1.2 Contract Artifacts

State/command sequencing table:

| Scenario | Result |
| --- | --- |
| Per-group state unset | Effective state is `On` (default). |
| Bulk `off` then targeted `on` for one group | That group `On`; other defined groups remain `Off`. |
| Bulk `on` then targeted `off` for one group | That group `Off`; other defined groups remain `On`. |
| Bulk `on/off` with no payload | Applies explicit per-group updates across currently defined groups only. |
| Removed/renamed stale groups in persisted user file | Ignored for bulk updates and command targeting; no auto-prune in this change. |

Persistence schema snapshot (`overlay_groupings.user.json`):

```json
{
  "plugin_groups": {
    "BGS-Tally Objectives": {
      "enabled": false,
      "last_payload_seen_at": "2026-03-06T18:45:12Z",
      "last_bounds_updated_at": "2026-03-06T18:45:10Z"
    }
  }
}
```

- No separate persisted global enabled flag.
- Hybrid retained metadata fields while disabled: `bounds`, `last_payload_seen_at`, `last_bounds_updated_at`.
- Migration behavior: ignore legacy opacity-based logical-off state and initialize true on/off from defaults.

#### Stage 1.3 Contract Artifacts

Safe rollout stages:

| Rollout stage | Runtime behavior | Client behavior | Safeguards |
| --- | --- | --- | --- |
| R0 Baseline | Existing behavior | Existing behavior | Capture baseline counters/log references. |
| R1 Shared resolver introduced | Runtime resolves group identity via shared resolver and logs parity-only metrics | Existing client resolver remains active | No gating change; parity mismatch logging only. |
| R2 Runtime authoritative gate on | Runtime drops disabled groups early using shared resolver | Client fallback filter remains enabled defensively | Monitor parity mismatch counters and dropped-payload counters. |
| R3 Stabilize | Runtime authoritative remains primary | Client fallback retained until confidence threshold met | Keep rollback switch and mismatch alerting during burn-in. |

Parity/counter contract:

- `resolver_parity_match_count`
- `resolver_parity_mismatch_count`
- `disabled_payload_drop_count`
- `disabled_payload_hybrid_metadata_update_count`

Rollback contract:

- If parity mismatch rate exceeds accepted threshold during R2/R3, revert to fallback mode and investigate resolver divergence.
- If disabled payload processing cost is not materially reduced, pause cutover and re-evaluate gate location.
- Rollback preserves user-visible behavior: enabled groups render unchanged; disabled groups remain non-rendered.

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
| 2.1 | Add per-group enabled-state storage and propagation (no global persisted flag) | Completed |
| 2.2 | Implement early-drop gate with hybrid metadata retention | Completed |
| 2.3 | Add state inspection/list command backend support (`status` formatter) | Completed |

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
- `overlay_client/.venv/bin/python -m pytest tests/test_runtime_services.py tests/test_controller_services.py`

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
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "render_surface or grouping_helper or payload_bounds"`

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
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py -k "plugins or state or list"`

#### Phase 2 Detailed Execution Plan

| Stage | Goal | Detailed work items | Outputs to document | Validation for completion |
| --- | --- | --- | --- | --- |
| 2.1 | Implement per-group state plumbing end-to-end | Add runtime state store for per-group enabled flags; wire persistence read/write in `overlay_groupings.user.json`; propagate state updates to client/controller channels; enforce no-global-flag model | State store contract, propagation path notes, persistence mapping notes | Runtime can read/write per-group state, propagate updates, and execute bulk no-payload actions as per-group updates |
| 2.2 | Implement runtime early-drop with hybrid metadata | Insert runtime authoritative gate before expensive render-command generation; drop disabled-group payloads; retain only `bounds`, `last_payload_seen_at`, `last_bounds_updated_at`; keep client fallback filter active | Gate placement notes, metadata-retention notes, counters/log keys and interpretation | Disabled groups avoid full processing path while retaining required metadata; enabled groups remain behavior-equivalent |
| 2.3 | Implement backend status listing service | Add runtime query for effective state per currently defined group; implement alphabetical formatter `<plugin_group_name>: On|Off`; expose backend API for chat/controller consumers | Formatter contract, sample output block, consumer integration notes | `status` backend output is deterministic, alphabetical, and reusable by chat/UI without duplicate formatting logic |

#### Phase 2 Artifact Checklist
- Per-group state persistence shape is documented and implemented without a separate global enabled flag.
- Bulk no-payload `on/off` path is implemented as explicit per-group updates to currently defined groups only.
- Stale removed/renamed persisted entries are ignored and not auto-pruned.
- Runtime early-drop location is documented and demonstrably before expensive render command generation.
- Hybrid retained metadata is limited to `bounds`, `last_payload_seen_at`, `last_bounds_updated_at`.
- Runtime/client parity and drop counters are present and documented.
- `status` formatter contract is implemented and shared (no duplicate ad-hoc formatters).
- `status` output sorts by `plugin_group_name` and emits one line per group as `<plugin_group_name>: On|Off`.

#### Stage 2.1 Contract Artifacts

Per-group state persistence contract (illustrative):

```json
{
  "plugin_groups": {
    "BGS-Tally Objectives": {
      "enabled": true
    },
    "BGS-Tally Colonisation": {
      "enabled": false
    }
  }
}
```

- `enabled` is persisted per group.
- Missing group entry is interpreted as unset/default `On`.
- Whole-overlay no-payload commands operate by writing explicit per-group values for currently defined groups.

#### Stage 2.2 Contract Artifacts

Early-drop flow contract:

1. Resolve payload -> canonical `plugin_group_name` using shared resolver.
2. Read effective enabled state for that group.
3. If enabled: continue normal pipeline unchanged.
4. If disabled: skip heavy transform/render-command generation; update only hybrid metadata (`bounds`, timestamps).
5. Emit debug counters/log lines for dropped payload events and metadata updates.

Required counters/log keys:

- `disabled_payload_drop_count`
- `disabled_payload_hybrid_metadata_update_count`
- `resolver_parity_match_count`
- `resolver_parity_mismatch_count`

#### Stage 2.3 Contract Artifacts

`status` formatter contract:

- Input: mapping of currently defined `plugin_group_name` -> effective boolean enabled state.
- Sort order: ascending alphabetical by `plugin_group_name`.
- Output line format: `<plugin_group_name>: On|Off`.

Example output:

```text
BGS-Tally Colonisation: On
BGS-Tally Objectives: Off
```

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
| 3.1 | Extend chat commands for on/off/toggle/status with phrase coercion | Completed |
| 3.2 | Extend hotkeys actions (On/Off payload-aware + new Toggle action) | Completed |
| 3.3 | Add plugin-group on/off checkbox in controller and `plugin_group_manager` | Completed |

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
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py`

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
- `overlay_client/.venv/bin/python -m pytest tests/test_hotkeys.py tests/test_toggle_helpers.py`

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
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests tests/test_plugin_group_manager_api.py`

#### Phase 3 Detailed Execution Plan

| Stage | Goal | Detailed work items | Outputs to document | Validation for completion |
| --- | --- | --- | --- | --- |
| 3.1 | Implement chat command controls | Extend parser for `on/off/toggle/status`; apply order-insensitive coercion; support optional group target; route commands to Phase 2 backend state/status services; emit one EDMC warning per unknown group | Command grammar notes, coercion mapping, warning examples, status output examples | Chat commands produce deterministic state changes and deterministic `status` output with unknown-group behavior matching requirements |
| 3.2 | Implement hotkeys control surface | Add `Toggle Overlay` action; extend `Overlay On`/`Overlay Off` payload handling for `plugin_group` and `plugin_groups`; union+dedupe targets; ignore unknown groups with per-group EDMC warnings | Hotkey payload contract examples, action behavior matrix (no payload vs targeted payload), warning behavior notes | All three actions operate globally and targeted, and maintain backward compatibility for existing action paths |
| 3.3 | Implement controller and manager UX controls | Add plugin-group enabled checkbox in Overlay Controller and `plugin_group_manager`; wire immediate persistence and runtime update; preserve visibility/editability for off groups; place controller checkbox immediately above `Reset` | UI placement note, wiring summary, persistence/update flow notes | UI controls are consistent with chat/hotkey behavior and reflect current state without stale interactions |

#### Phase 3 Implementation Kickoff (Execution Checklist)

| Stage | Ordered implementation tasks | Stage test commands |
| --- | --- | --- |
| 3.1 | 1) Add shared plugin-group action service helpers (target parsing, unknown warnings, set/toggle execution). 2) Add runtime delegate methods and CLI handlers for plugin-group set/toggle/status. 3) Update chat command parsing for `on/off/toggle/status` + phrase coercion and optional target. | `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_plugin_group_state.py -k "on or off or toggle or status or plugin_group"` |
| 3.2 | 1) Extend hotkeys manager with payload-targeted on/off + new toggle action. 2) Support `plugin_group` + `plugin_groups` union/dedupe. 3) Preserve no-payload bulk behavior and per-group unknown warnings in EDMC logs. | `overlay_client/.venv/bin/python -m pytest tests/test_hotkeys.py tests/test_journal_commands.py -k "hotkey or toggle or plugin_group"` |
| 3.3 | 1) Add controller checkbox immediately above `Reset`, with runtime-backed state read/write. 2) Add matching checkbox behavior in `utils/plugin_group_manager.py`. 3) Ensure off groups remain visible/editable and status refresh remains stable. | `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_plugin_bridge.py overlay_controller/tests/test_idprefix_refresh.py tests/test_overlay_controller_platform.py` |

#### Phase 3 Artifact Checklist
- Chat command grammar includes `on`, `off`, `toggle`, and `status`.
- Chat coercion supports equivalent forms:
- `!ovr on "<group>"`
- `!ovr "<group>" on`
- `!ovr turn "<group>" on`
- `!ovr turn on "<group>"`
- `status` output format remains alphabetical `<plugin_group_name>: On|Off` one per line.
- Unknown group handling is per-group EDMC warning for chat and hotkeys.
- Hotkey payload handling supports `plugin_group` + optional `plugin_groups` with union+dedupe.
- No-payload action behavior remains bulk update across currently defined groups.
- Overlay Controller checkbox placement is immediately above `Reset`.
- Off groups remain visible/editable in both controller and `plugin_group_manager`.
- All control surfaces (chat, hotkeys, controller, manager) call shared backend state operations.

#### Stage 3.1 Contract Artifacts

Chat command behavior matrix:

| Input | Effective action | Target set |
| --- | --- | --- |
| `!ovr on` | enable | all currently defined groups |
| `!ovr off` | disable | all currently defined groups |
| `!ovr toggle` / `!ovr t` | flip | all currently defined groups |
| `!ovr on "BGS-Tally Objectives"` | enable | `["BGS-Tally Objectives"]` |
| `!ovr "BGS-Tally Objectives" on` | enable | `["BGS-Tally Objectives"]` |
| `!ovr turn "BGS-Tally Objectives" on` | enable | `["BGS-Tally Objectives"]` |
| `!ovr turn on "BGS-Tally Objectives"` | enable | `["BGS-Tally Objectives"]` |
| `!ovr status` | list state | query only |

Unknown-group behavior contract:

- Ignore unknown targets.
- Emit one EDMC warning log entry per unknown group.
- Do not fail entire command if at least one target is valid.

#### Stage 3.2 Contract Artifacts

Hotkey action payload contract:

```json
{
  "plugin_group": "BGS-Tally Objectives",
  "plugin_groups": ["BGS-Tally Colonisation", "BGS-Tally Objectives"]
}
```

- `Overlay On` with no payload: enable all currently defined groups.
- `Overlay Off` with no payload: disable all currently defined groups.
- `Toggle Overlay` with no payload: invert all currently defined groups.
- Targeted payloads use union+dedupe across `plugin_group` + `plugin_groups`.
- Unknown payload targets are ignored with one EDMC warning per unknown group.

#### Stage 3.3 Contract Artifacts

Controller and manager UX contract:

- Overlay Controller:
- Add per-group enabled checkbox control.
- Place checkbox immediately above `Reset` button.
- Toggle updates persisted user state and runtime immediately.
- `plugin_group_manager`:
- Add equivalent per-group enabled checkbox/control path.
- Reuse same persistence and runtime update behavior.
- Off groups remain listed and editable in both tools.

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
| 4.1 | Refactor existing logical on/off paths away from opacity emulation | Completed |
| 4.2 | Add new wiki page for actions (all actions, not only on/off) | Completed |
| 4.3 | Update existing wiki pages and in-repo docs for new behavior | Completed |

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
- `overlay_client/.venv/bin/python -m pytest tests/test_toggle_helpers.py tests/test_preferences_persistence.py overlay_client/tests/test_opacity_utils.py`

#### Stage 4.2 Detailed Plan
- Objective:
- Create `docs/wiki` action usage page that documents all supported actions.
- Steps:
- Add new markdown with hotkey payload format, chat examples, and behavior matrix.
- Include global vs targeted examples, `status` output example, and unknown-group warning behavior.
- Acceptance criteria:
- New doc exists and covers all actions end-to-end.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest -k "docs" || true`

#### Stage 4.3 Detailed Plan
- Objective:
- Update existing related docs to align terminology and commands.
- Steps:
- Update `Chat-Command`, `Overlay-Controller`, and `Usage` docs.
- Ensure references to opacity-based off semantics are corrected.
- Acceptance criteria:
- No contradictory docs remain.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest -k "journal_commands or hotkeys"`

#### Phase 4 Detailed Execution Plan

| Stage | Goal | Detailed work items | Outputs to document | Validation for completion |
| --- | --- | --- | --- | --- |
| 4.1 | Remove legacy logical on/off via opacity pathways | Inventory all logical on/off callsites still routed through `global_payload_opacity` toggling; reroute chat/hotkey/controller logical on/off to true plugin-group state operations; preserve opacity sliders and numeric opacity commands as visual-only controls; add focused regression tests for opacity behavior and logical on/off separation | Legacy-path inventory list, reroute summary, opacity-vs-on/off behavior matrix | No logical on/off path depends on opacity mutation; opacity still works exactly as a visual transparency control |
| 4.2 | Publish a complete actions usage doc | Add a new `docs/wiki` markdown page for action usage; document all actions (not only on/off), payload schema (`plugin_group` + optional `plugin_groups`), group target union+dedupe, no-payload bulk behavior, unknown-group warning behavior, and `status` output format; include concrete chat and hotkey examples | New wiki page outline + example command/action blocks | New wiki page is complete, accurate, and consistent with implemented behavior |
| 4.3 | Align existing docs with final semantics | Update `Chat-Command`, `Overlay-Controller`, `Usage`, and related index/sidebar references to remove opacity-off phrasing for logical on/off; cross-link to the new actions page; ensure migration notes explicitly call out “legacy opacity-based logical-off is ignored” | Doc delta summary by file + migration note references | No conflicting language remains across wiki/docs for on/off vs opacity semantics |

#### Phase 4 Artifact Checklist
- Complete list of legacy logical on/off codepaths previously using opacity toggling.
- Confirmed routing map showing each logical on/off entrypoint now uses true plugin-group on/off.
- Explicit non-regression statement: opacity numeric controls remain visual-only and unchanged.
- New actions wiki page covering all supported actions and payload examples.
- Action behavior matrix includes: no-payload (bulk), single group, multi-group, unknown group handling.
- Chat command examples include `on`, `off`, `toggle`, `status`, and `turn ...` coercion forms.
- Hotkey examples include `Overlay On`, `Overlay Off`, and `Toggle Overlay` with optional payload.
- Existing docs updated to remove contradictory opacity-off language.
- Migration note added and cross-linked in docs/release notes section for legacy behavior.

#### Phase 4 Implementation Checklist (Execution Order)

| Item | Stage | Task | Primary touch points | Verification |
| --- | --- | --- | --- | --- |
| 4.1.1 | 4.1 | Inventory legacy logical on/off paths that still rely on opacity mutation; capture before/after routing map | `overlay_plugin/journal_commands.py`, `overlay_plugin/hotkeys.py`, `load.py`, docs notes in this plan | `rg -n "toggle_payload_opacity|global_payload_opacity|set_payload_opacity_preference|toggle"` |
| 4.1.2 | 4.1 | Remove remaining logical on/off opacity mutations from chat/hotkey/controller pathways; keep numeric opacity command behavior unchanged | `overlay_plugin/journal_commands.py`, `overlay_plugin/hotkeys.py`, `load.py`, `overlay_plugin/toggle_helpers.py` (read-only unless required) | `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py tests/test_toggle_helpers.py` |
| 4.1.3 | 4.1 | Add/adjust regression tests proving logical on/off does not write opacity while numeric opacity still works | `tests/test_journal_commands.py`, `tests/test_hotkeys.py`, `tests/test_preferences_persistence.py`, `tests/test_toggle_helpers.py` | `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py tests/test_preferences_persistence.py tests/test_toggle_helpers.py` |
| 4.1.4 | 4.1 | Confirm no residual logical on/off opacity coupling in runtime handlers and document findings in Phase 4 summary | `load.py`, `docs/plans/plugin-group-onoff.md` | `overlay_client/.venv/bin/python -m ruff check load.py overlay_plugin/journal_commands.py overlay_plugin/hotkeys.py tests/test_journal_commands.py tests/test_hotkeys.py` |
| 4.2.1 | 4.2 | Create new actions doc covering all actions (chat + hotkeys), payload schema, unknown-group handling, and status output format | `docs/wiki/Overlay-Actions.md` (new) | manual doc review against locked requirements |
| 4.2.2 | 4.2 | Add explicit examples for bulk/global and targeted behaviors, including `turn` coercion and toggle token note | `docs/wiki/Overlay-Actions.md` | manual doc review + requirement checklist in this plan |
| 4.2.3 | 4.2 | Add canonical behavior matrix for actions/commands (global vs targeted vs mixed payloads) | `docs/wiki/Overlay-Actions.md` | checklist validation against Phase 1/3 decisions |
| 4.2.4 | 4.2 | Document migration behavior: legacy opacity-based logical-off ignored; defaults used for true on/off | `docs/wiki/Overlay-Actions.md`, release notes target file | manual review |
| 4.3.1 | 4.3 | Update `Chat-Command.md` to align one-word tokens/coercion and remove contradictory opacity-off semantics | `docs/wiki/Chat-Command.md` | manual cross-page consistency review |
| 4.3.2 | 4.3 | Update `Overlay-Controller.md` and `Usage.md` with per-group checkbox behavior, status command expectations, and true on/off semantics | `docs/wiki/Overlay-Controller.md`, `docs/wiki/Usage.md` | manual cross-page consistency review |
| 4.3.3 | 4.3 | Add sidebar/navigation links to new actions doc and verify discoverability | `docs/wiki/_Sidebar.md`, optionally `docs/wiki/Home.md` | manual navigation check |
| 4.3.4 | 4.3 | Update release notes with migration note and summarize doc changes in plan results | release notes file + `docs/plans/plugin-group-onoff.md` | `overlay_client/.venv/bin/python -m pytest -k "journal_commands or hotkeys"` |

#### Stage 4.1 Module-Level Checklist

1. Detect and remove any logical on/off codepath that calls opacity toggles or writes `global_payload_opacity` as part of visibility switching.
2. Preserve numeric opacity command parsing and preference setters for transparency-only behavior.
3. Verify chat actions (`on/off/toggle/status`) do not mutate opacity state.
4. Verify hotkey actions (`Overlay On`, `Overlay Off`, `Toggle Overlay`) do not mutate opacity state.
5. Keep controller/group-manager behavior bound to plugin-group enabled state only.
6. Add/adjust tests to enforce the separation contract (logical visibility vs visual opacity).

#### Stage 4.1 Exit Checklist

- `on/off/toggle` logical paths do not call opacity helpers.
- Numeric opacity commands still call opacity setters and continue to work.
- Test coverage exists for both logical state change and opacity change behaviors.
- Ruff/pytest pass on touched files.

#### Stage 4.1 Contract Artifacts

Behavior contract after refactor:

| Command/action intent | Expected runtime behavior | Opacity side effects |
| --- | --- | --- |
| Logical `on` | Enable targeted groups (or all defined groups if no target) | None |
| Logical `off` | Disable targeted groups (or all defined groups if no target) | None |
| Logical `toggle` | Invert targeted groups (or all defined groups if no target) | None |
| Numeric opacity command (e.g. `!ovr 40`) | Update visual transparency only | Yes (intended visual effect only) |

Acceptance assertions:
- No logical on/off/toggle path writes `global_payload_opacity` as part of logical visibility changes.
- Numeric opacity commands and preferences continue to update rendered alpha as before.

##### Item 4.1.1 Inventory Results (Completed 2026-03-06)

Legacy opacity mutation paths retained (visual transparency only):

| Path | Current purpose |
| --- | --- |
| `load.py:set_payload_opacity_preference` | Explicit numeric opacity preference updates. |
| `load.py:toggle_payload_opacity_preference` + `overlay_plugin/toggle_helpers.py` | Explicit opacity toggle behavior for transparency workflows. |
| `overlay_plugin/journal_commands.py:_set_opacity` | Numeric chat opacity command handling only. |

Logical on/off/toggle authoritative paths (true plugin-group state):

| Surface | Runtime route |
| --- | --- |
| Chat `on/off/toggle/status` | `overlay_plugin/journal_commands.py` -> `load.py:_set_plugin_groups_enabled` / `_toggle_plugin_groups_enabled` |
| Hotkeys `Overlay On/Off/Toggle Overlay` | `overlay_plugin/hotkeys.py` -> injected `set_group_state` / `toggle_group_state` callbacks |
| Controller/group manager checkbox | plugin CLI `plugin_group_set` / `plugin_group_toggle` handled in `load.py` |

Before/after routing map for logical visibility:

| Flow | Before (legacy behavior) | After (current behavior) |
| --- | --- | --- |
| Chat toggle/on/off intent | Opacity-based logical emulation (`global_payload_opacity` mutation) | True plugin-group state mutation (`plugin_group_set`/`plugin_group_toggle`) |
| Hotkey On/Off intent | Opacity-based toggle semantics | True plugin-group state set semantics |
| Hotkey Toggle intent | Not available as true state action | Dedicated `Toggle Overlay` action using true plugin-group state |

##### Item 4.1.2 Implementation Results (Completed 2026-03-06)

- Verified there are no remaining chat/hotkey/controller logical on/off pathways that call opacity mutation methods.
- Confirmed opacity mutation paths are now explicitly scoped to visual transparency behavior only.
- Added explicit method-level runtime notes in `load.py`:
  - `set_payload_opacity_preference`: visual-only transparency.
  - `toggle_payload_opacity_preference`: visual-only transparency.
- No logical state routing changes were required in this item because chat/hotkey/controller were already on true plugin-group on/off paths.

##### Item 4.1.3 Implementation Results (Completed 2026-03-06)

- Added regression coverage that explicitly enforces separation:
  - logical chat commands (`on/off/toggle`) do not call opacity mutation paths.
  - numeric chat opacity commands continue to call opacity mutation paths.
- Expanded preference persistence regression coverage for `global_payload_opacity` save/reload behavior to ensure visual opacity behavior remains stable and independently persisted.
- Hotkey tests continue validating true plugin-group state routing (`Overlay On/Off/Toggle`) with no opacity coupling.

##### Item 4.1.4 Verification Results (Completed 2026-03-06)

- Final residual-coupling scan confirms:
  - logical state routes: `load.py:_set_plugin_groups_enabled`, `load.py:_toggle_plugin_groups_enabled`, CLI `plugin_group_set`, CLI `plugin_group_toggle`;
  - opacity routes remain isolated to visual transparency methods: `set_payload_opacity_preference`, `toggle_payload_opacity_preference`, and `toggle_payload_opacity`.
- No runtime handler in chat/hotkey/controller logical on/off flow writes `global_payload_opacity`.
- Stage `4.1` exit checklist conditions are satisfied.

#### Stage 4.2 Contract Artifacts

Planned new doc: `docs/wiki/Overlay-Actions.md`

Required sections:
- Action overview and scope (logical on/off vs opacity).
- Hotkey action reference:
  - `Overlay On`
  - `Overlay Off`
  - `Toggle Overlay`
  - payload targeting (`plugin_group`, `plugin_groups`)
- Chat command reference:
  - `on`, `off`, `toggle`, `status`
  - coercion examples with `turn`
- Status output format:
  - alphabetical
  - one line per group
  - `<plugin_group_name>: On|Off`
- Unknown group behavior:
  - ignored with one EDMC warning per unknown group.

##### Stage 4.2 Itemized Checklist

1. `4.2.1` Build page skeleton for `Overlay-Actions.md`:
- Purpose/scope.
- Section anchors for chat commands, hotkeys, payload schema, status output, unknown-group behavior.

2. `4.2.2` Add normative examples:
- Chat:
  - `!ovr on "BGS-Tally Objectives"`
  - `!ovr "BGS-Tally Objectives" on`
  - `!ovr turn "BGS-Tally Objectives" on`
  - `!ovr turn on "BGS-Tally Objectives"`
  - `!ovr off`, `!ovr toggle`, `!ovr status`
- Hotkeys:
  - `Overlay On` / `Overlay Off` / `Toggle Overlay`
  - payload with `plugin_group` and `plugin_groups`

3. `4.2.3` Add canonical behavior matrix:
- no payload => bulk all currently defined groups.
- `plugin_group` only => single target.
- `plugin_groups` only => multi-target list.
- both => union + dedupe.
- unknown groups => ignored, one EDMC warning per group.

4. `4.2.4` Add migration section:
- Legacy opacity-based logical-off is ignored.
- True on/off initializes from defaults (`unset => on`).
- Explicitly separate opacity (visual) from on/off (logical visibility).

##### Stage 4.2 Exit Checklist

- New `Overlay-Actions.md` exists and covers all actions.
- Examples match implemented parser/action behavior exactly.
- Matrix aligns with locked Phase 1/3 decisions.
- Migration note is explicit and unambiguous.

##### Item 4.2.1 Implementation Results (Completed 2026-03-06)

- Created new wiki page: `docs/wiki/Overlay-Actions.md`.
- Added required skeleton/anchors:
  - Scope (logical on/off vs visual opacity),
  - Chat actions,
  - Hotkey actions,
  - Payload targeting schema (`plugin_group`, `plugin_groups`),
  - Status output format,
  - Unknown-group handling.
- Included action inventory coverage for both chat and hotkeys as the baseline for items `4.2.2`-`4.2.4`.

##### Item 4.2.2 Implementation Results (Completed 2026-03-06)

- Expanded `docs/wiki/Overlay-Actions.md` with explicit normative examples for:
  - bulk/global `on`, `off`, `toggle`,
  - targeted `on`, `off`, `toggle`,
  - `status`.
- Added chat coercion examples for `turn` ordering variants (for `on`, `off`, and `toggle`).
- Added toggle token note for chat (configurable argument; default `t`).
- Added hotkey examples for no-payload bulk behavior and targeted payload behavior.

##### Item 4.2.3 Implementation Results (Completed 2026-03-06)

- Added canonical behavior matrix to `docs/wiki/Overlay-Actions.md` covering:
  - no payload bulk behavior,
  - `plugin_group` only behavior,
  - `plugin_groups` only behavior,
  - mixed `plugin_group` + `plugin_groups` union/dedupe behavior,
  - unknown-group handling (ignored + one EDMC warning per group),
  - `status` query behavior/format.

##### Item 4.2.4 Implementation Results (Completed 2026-03-06)

- Added migration notes to `docs/wiki/Overlay-Actions.md`:
  - legacy opacity-based logical-off state is ignored,
  - true on/off initializes from defaults (`unset => On`),
  - opacity remains visual transparency only.
- Release-notes linkage remains queued for Stage `4.3.4` (per execution order).

#### Stage 4.3 Contract Artifacts

Doc synchronization checklist by file:
- `docs/wiki/Chat-Command.md`: remove/replace opacity-based logical-off references.
- `docs/wiki/Overlay-Controller.md`: describe per-group enabled checkbox behavior.
- `docs/wiki/Usage.md`: update quick-start action examples to true on/off semantics.
- `docs/wiki/_Sidebar.md`: link to `Overlay-Actions.md`.
- Release/migration notes: explicitly state legacy opacity-based logical-off migration behavior.

##### Stage 4.3 Itemized Checklist

1. `4.3.1` `Chat-Command.md`:
- reflect one-word action tokens: `on`, `off`, `toggle`, `status`;
- include coercion notes for `turn ... on/off/toggle`;
- remove any implication that logical off is implemented by opacity.

2. `4.3.2` `Overlay-Controller.md` + `Usage.md`:
- document per-group enabled checkbox behavior;
- placement note: checkbox immediately above `Reset` in controller;
- clarify off groups remain visible/editable.

3. `4.3.3` Navigation/docs discoverability:
- add `Overlay-Actions.md` link in sidebar (and home/index if used);
- verify no orphaned docs.

4. `4.3.4` Release-note/doc summary closure:
- add migration note to release notes;
- update this plan’s Phase 4 results with files touched + key wording changes.

##### Stage 4.3 Exit Checklist

- No contradictory wording remains across Chat/Controller/Usage/Actions pages.
- Navigation includes the new actions page.
- Release notes include migration behavior statement.
- Plan has a concise doc-delta summary for Phase 4.

##### Item 4.3.1 Implementation Results (Completed 2026-03-06)

- Updated `docs/wiki/Chat-Command.md` to align with one-word action tokens:
  - `on`, `off`, `toggle`, `status`.
- Added coercion guidance and examples for `turn` variants.
- Clarified toggle token behavior (default `t`, configurable).
- Removed legacy wording that implied logical off was opacity-based.
- Kept opacity command documentation, explicitly scoped to visual transparency only.

##### Item 4.3.2 Implementation Results (Completed 2026-03-06)

- Updated `docs/wiki/Overlay-Controller.md`:
  - documented per-group `Enabled` checkbox behavior,
  - documented checkbox placement (immediately above `Reset`),
  - clarified off groups remain visible/editable,
  - added `!ovr status` reference for state inspection.
- Updated `docs/wiki/Usage.md`:
  - added true on/off workflow examples (global + targeted),
  - added status output expectations,
  - added controller checkbox behavior notes,
  - clarified opacity is transparency-only (not logical off),
  - linked to `Overlay-Actions` for full action reference.

##### Item 4.3.3 Implementation Results (Completed 2026-03-06)

- Updated wiki navigation surfaces for discoverability:
  - `docs/wiki/_Sidebar.md`: added `Overlay Actions` under `Usage`.
  - `docs/wiki/Home.md`: added direct link to `Overlay Actions` in the usage section.
- Verified `Overlay-Actions` is no longer orphaned from primary wiki navigation paths.

##### Item 4.3.4 Implementation Results (Completed 2026-03-06)

- Updated `RELEASE_NOTES.md` with an `Unreleased` section covering:
  - true plugin-group on/off feature summary,
  - migration note (legacy opacity-based logical-off ignored),
  - default behavior note (`unset => On`),
  - opacity semantics (visual-only, not logical off).
- Added Phase 4 doc-delta summary references in this plan so maintainers can review changed wiki/release-note surfaces quickly.

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
| 5.1 | Add/expand automated tests for new state model and command coercion | Completed |
| 5.2 | Validate processing overhead improvements and no-op behavior | Completed |
| 5.3 | Final compatibility review + release notes updates | Completed |

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
- `overlay_client/.venv/bin/python -m pytest tests overlay_client/tests overlay_controller/tests`

#### Stage 5.2 Detailed Plan
- Objective:
- Prove disabled groups are dropped before heavy processing.
- Steps:
- Add counters/assertions in tests around dropped payload flow.
- Run targeted perf-style tests or timing assertions where stable.
- Acceptance criteria:
- Measurable evidence that disabled groups avoid full render processing.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "render_surface or data_client or performance"`

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

#### Phase 5 Detailed Execution Plan

| Stage | Goal | Detailed work items | Outputs to document | Validation for completion |
| --- | --- | --- | --- | --- |
| 5.1 | Expand automated regression coverage for finalized behavior | Add deterministic tests for command coercion, bulk vs targeted sequencing, unknown-group warning behavior, status formatting, stale entry handling, and no-global-flag persistence semantics; include controller/manager integration assertions where feasible | Test-gap list, new/updated test files, traceability map from requirements -> tests | All locked requirements have explicit automated coverage or documented rationale for exclusion |
| 5.2 | Validate early-drop overhead reduction and no-op guarantees | Use runtime counters and targeted tests to verify disabled groups skip heavy processing while preserving required hybrid metadata; verify enabled-group parity; avoid unstable wall-clock assertions | Counter baseline vs post-change summary, no-op behavior notes, perf-risk caveats | Counter evidence confirms early-drop path is active and behavior-equivalent for enabled groups |
| 5.3 | Final release/readiness and compatibility closeout | Finalize release notes/migration guidance, run compatibility/compliance checklist, capture deferred follow-ups (rule-layer integration), and complete final quality gates | Release-ready checklist, compliance matrix, deferred follow-up list | Release artifacts and checks are complete with no unresolved blocking items |

#### Phase 5 Artifact Checklist
- Requirements-to-tests traceability exists for every Phase 1-4 locked behavior.
- Tests explicitly cover:
  - chat coercion variants (`on/off/toggle/status` + `turn` ordering),
  - hotkey payload union+dedupe behavior,
  - unknown-group warning behavior (one warning per group),
  - status line formatting/sort order,
  - stale removed/renamed persisted entries ignored/no auto-prune,
  - no separate persisted global enabled flag.
- Runtime counter evidence captured for disabled payload early-drop behavior.
- Enabled-group behavior parity evidence captured (no regressions vs intended behavior).
- Release notes include migration posture and finalized user-facing behavior summary.
- Deferred rule-layer items are captured explicitly (out-of-scope follow-ups).

#### Item 5.1.1 Requirements-to-Tests Matrix (Completed 2026-03-06)

| Locked requirement | Primary automated coverage |
| --- | --- |
| Chat coercion equivalence (`on/off/toggle/status` + `turn` ordering) | `tests/test_journal_commands.py::test_overlay_group_action_phrase_coercion`, `tests/test_journal_commands.py::test_overlay_group_action_phrase_coercion_for_off_and_toggle`, `tests/test_journal_commands.py::test_overlay_status_command_outputs_sorted_lines` |
| Toggle token behavior (default `t` + configurable token) | `tests/test_journal_commands.py::test_overlay_toggle_argument`, `tests/test_journal_commands.py::test_overlay_toggle_argument_case_insensitive`, `tests/test_journal_commands.py::test_overlay_toggle_argument_multi_character` |
| Hotkey payload `plugin_group` + `plugin_groups` union/dedupe | `tests/test_hotkeys.py::test_hotkeys_callbacks_apply_global_and_targeted_actions`, `tests/test_hotkeys.py::test_hotkeys_target_payload_unions_plugin_group_and_plugin_groups`, `tests/test_plugin_group_controls.py::test_resolve_payload_group_targets_unions_and_dedupes` |
| Unknown groups ignored with one warning per group (EDMC logs) | `tests/test_plugin_group_controls.py::test_plugin_group_control_service_warns_once_per_unknown_group` |
| `status` format alphabetical, one line per group, `On|Off` | `tests/test_plugin_group_state.py::test_state_manager_persists_enabled_state_and_ignores_stale_entries`, `tests/test_journal_commands.py::test_overlay_status_command_outputs_sorted_lines` |
| `unset => on`, stale entries ignored/no auto-prune, no separate global flag | `tests/test_plugin_group_state.py::test_state_manager_persists_enabled_state_and_ignores_stale_entries`, `tests/test_plugin_group_state.py::test_state_manager_bulk_set_updates_only_known_groups_and_keeps_stale_entries` |
| Runtime early-drop + hybrid metadata + counters | `tests/test_runtime_plugin_group_publish.py::test_publish_payload_drops_disabled_group_before_broadcast`, `tests/test_plugin_group_state.py::test_state_manager_drops_disabled_payload_and_tracks_hybrid_metadata`, `tests/test_plugin_group_state.py::test_state_manager_enabled_payload_tracks_parity_without_drop_or_disabled_metadata_counter`, `overlay_client/tests/test_launcher_group_filter.py::test_payload_handler_drops_legacy_overlay_when_filter_blocks` |

Coverage gap decision:
- No additional gaps remain for locked Phase 1-4 requirements.

#### Phase 5 Implementation Checklist (Execution Order)

| Item | Stage | Task | Primary touch points | Verification |
| --- | --- | --- | --- | --- |
| 5.1.1 | 5.1 | Build final requirements-to-tests matrix and identify any remaining coverage gaps | `docs/plans/plugin-group-onoff.md`, `tests/*`, `overlay_controller/tests/*`, `overlay_client/tests/*` | manual matrix review in plan |
| 5.1.2 | 5.1 | Add/adjust chat/hotkey coercion and targeting tests (including unknown-group warnings and status formatting) | `tests/test_journal_commands.py`, `tests/test_hotkeys.py`, `tests/test_plugin_group_controls.py` | `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py tests/test_plugin_group_controls.py` |
| 5.1.3 | 5.1 | Add/adjust persistence/state-model tests (`unset => on`, stale entries ignored, no global flag) | `tests/test_plugin_group_state.py`, `tests/test_preferences_persistence.py` | `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_state.py tests/test_preferences_persistence.py` |
| 5.1.4 | 5.1 | Add/adjust controller/group-manager integration tests where deterministic | `overlay_controller/tests/test_plugin_bridge.py`, related controller tests | `overlay_client/.venv/bin/python -m pytest overlay_controller/tests -k \"plugin_bridge or status or group\"` |
| 5.1.5 | 5.1 | Run consolidated stage-coverage pass and record results | combined touched test suites | `overlay_client/.venv/bin/python -m pytest tests overlay_controller/tests overlay_client/tests -k \"journal_commands or hotkeys or plugin_group or status\"` |
| 5.2.1 | 5.2 | Define/confirm counter assertions for early-drop behavior (`drop`, `metadata`, parity counters) | `overlay_plugin/plugin_group_state.py`, runtime publish tests | `overlay_client/.venv/bin/python -m pytest tests/test_runtime_plugin_group_publish.py tests/test_plugin_group_state.py` |
| 5.2.2 | 5.2 | Add/adjust targeted tests proving disabled groups avoid heavy processing path while metadata is retained | runtime/client filter tests | `overlay_client/.venv/bin/python -m pytest tests/test_runtime_plugin_group_publish.py overlay_client/tests/test_launcher_group_filter.py -k \"drop or disabled or metadata\"` |
| 5.2.3 | 5.2 | Run focused client pipeline tests for behavior parity (`enabled` unaffected) | client/render tests | `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k \"render_surface or grouping_helper or payload_bounds\"` |
| 5.2.4 | 5.2 | Document counter/perf findings and residual risks (avoid unstable wall-clock claims) | `docs/plans/plugin-group-onoff.md` | manual review against acceptance criteria |
| 5.3.1 | 5.3 | Finalize release-note wording for feature + migration behavior | `RELEASE_NOTES.md` | manual review |
| 5.3.2 | 5.3 | Run EDMC compatibility/compliance checklist and capture yes/no outcomes with remediations if needed | plugin code + `AGENTS.md` compliance rules | documented matrix in plan (or linked compliance note) |
| 5.3.3 | 5.3 | Capture deferred follow-ups for rule-layer integration and operational rollout notes | `docs/plans/plugin-group-onoff.md` | manual review |
| 5.3.4 | 5.3 | Execute final quality gates and summarize | repo-wide checks | `make check` (and `make test` if needed) |

#### Stage 5.1 Itemized Checklist

1. Build explicit test traceability from locked requirements to concrete test functions.
2. Close remaining gaps in chat/hotkey/state/persistence coverage.
3. Ensure unknown-group warning and status formatting are asserted, not just observed.
4. Ensure stale-entry and no-global-flag semantics are asserted.
5. Record any intentionally untested paths with rationale.

#### Stage 5.1 Exit Checklist

- Locked behavior is covered by deterministic tests.
- Coverage gaps are either closed or explicitly deferred with rationale.
- Stage test suite passes on the selected environment.

#### Stage 5.2 Itemized Checklist

1. Assert counter behavior for disabled payload drops and metadata updates.
2. Assert enabled-path behavior parity remains unchanged.
3. Avoid flaky time-based benchmarks; prefer counter/path assertions.
4. Document measured evidence and residual performance risk.

#### Stage 5.2 Exit Checklist

- Early-drop behavior is proven with counter/path assertions.
- Enabled-group behavior parity is validated.
- Findings and caveats are documented in this plan.

#### Stage 5.3 Itemized Checklist

1. Finalize release notes for feature behavior and migration semantics.
2. Produce compatibility/compliance review results (yes/no + remediation notes).
3. Capture deferred post-release follow-ups (rule-layer integration scope).
4. Run final quality gates and publish summary in plan.

#### Stage 5.3 Exit Checklist

- Release artifacts are complete and consistent.
- Compatibility/compliance review is documented with clear outcomes.
- Final checks pass or blockers are explicitly recorded.

#### Stage 5.1 Contract Artifacts

Required assertion set:
- Chat coercion equivalence for `on/off/toggle`.
- Toggle token behavior (`t` default + configurable token).
- Bulk vs targeted state transitions.
- `status` alphabetical `<plugin_group_name>: On|Off` formatting.
- Unknown-group handling: ignored + one warning per unknown group.
- Persistence semantics: `unset => on`, stale entries ignored, no global flag.

#### Stage 5.2 Contract Artifacts

Counter evidence contract:
- `disabled_payload_drop_count` increases when disabled-group payloads arrive.
- `disabled_payload_hybrid_metadata_update_count` increases only for disabled-group metadata touches.
- `resolver_parity_match_count` / `resolver_parity_mismatch_count` remain within expected bounds (mismatch ideally zero in current path).
- Enabled payloads continue through normal publish/render flow.

#### Stage 5.3 Contract Artifacts

Release-readiness outputs:
- Final release-note section for this feature set.
- Compatibility/compliance checklist outcomes (yes/no + action if no).
- Deferred follow-up list for future rule-layer behavior implementation.
- Final verification command outputs recorded in plan.

##### Item 5.1.2 Implementation Results (Completed 2026-03-06)

- Added/updated deterministic tests for:
  - chat coercion equivalence for `off`/`toggle` phrase permutations (`turn ...` variants),
  - strict `status` line formatting and ordering,
  - hotkey target union/dedupe when both `plugin_group` and `plugin_groups` are supplied,
  - unknown-group warning logging semantics (one warning per unknown group).

##### Item 5.1.3 Implementation Results (Completed 2026-03-06)

- Added/updated persistence/state model assertions for:
  - stale persisted entries remaining unpruned,
  - stale entries ignored for whole-overlay/bulk updates,
  - absence of any separate persisted global enabled flag,
  - parity counters for enabled and disabled payload resolution paths.

##### Item 5.1.4 Implementation Results (Completed 2026-03-06)

- Ran deterministic controller/group-manager integration coverage pass:
  - plugin bridge CLI request/set behavior,
  - group state service/status polling surfaces,
  - controller grouping loaders and mode profile interactions selected by `-k "plugin_bridge or status or group"`.

##### Item 5.1.5 Implementation Results (Completed 2026-03-06)

- Consolidated coverage pass across plugin tests, controller tests, and client tests with group/status-focused selector completed successfully.
- Stage `5.1` exit criteria satisfied.

##### Item 5.2.1-5.2.4 Implementation Results (Completed 2026-03-06)

- Verified early-drop counter contract with explicit assertions:
  - disabled payload path increments `disabled_payload_drop_count`,
  - disabled metadata path increments `disabled_payload_hybrid_metadata_update_count`,
  - enabled payload path keeps disabled counters at `0`,
  - parity counters remain stable with `resolver_parity_mismatch_count == 0` in covered paths.
- Verified disabled groups are dropped before publish/broadcast and client fallback blocks disabled payloads.
- Verified enabled payload paths still reach render/publish flows (no-op parity maintained).
- Performance note: validation uses path/counter assertions only; no unstable wall-clock benchmarks were added.
- Residual risk: exact wall-clock savings remain environment-dependent and are not asserted in CI; runtime counters are the authoritative signal.

##### Item 5.3.1 Implementation Results (Completed 2026-03-06)

- Finalized `RELEASE_NOTES.md` `Unreleased` wording to explicitly include:
  - chat action syntax (`on/off/toggle/status` with `turn` coercion),
  - hotkey payload targeting (`plugin_group` + `plugin_groups`, union+dedupe),
  - migration semantics (`unset => On`, legacy opacity logical-off ignored, opacity visual-only).

##### Item 5.3.2 Compliance Review (Completed 2026-03-06)

| Compliance item (AGENTS.md) | Outcome | Notes |
| --- | --- | --- |
| Stay aligned with EDMC core (`load.py` entrypoint, `plugin_start3`, plugin directory layout) | Yes | `load.py` entrypoint remains in plugin root with `plugin_start3`; plugin remains self-contained in own directory. |
| Supported EDMC API/helpers only, plus EDMC-aware state/persistence handling | Yes | Existing plugin architecture continues to use EDMC integration modules/helpers; no new unsupported EDMC API usage introduced in Phase 5. |
| Logging/versioning patterns (`logger.*`, no `print`, folder/logger naming) | Yes | Phase 5 changes added no `print`; warnings/debug remain on plugin loggers. |
| Runtime responsiveness/Tk safety for long-running work | Yes | Phase 5 introduced only tests/docs/release-note updates; no new Tk-thread or long-running runtime work paths. |
| Prefs/UI hooks pattern (`plugin_prefs`/`prefs_changed`, namespaced config keys, Tk thread safety) | Yes | No new prefs hook behavior introduced in Phase 5; existing Phase 3 wiring retained. |
| Dependency packaging/debug HTTP guidance | Yes | No new runtime dependencies or HTTP behavior introduced in Phase 5. |
| Python baseline check (`scripts/check_edmc_python.py`) | No (local env baseline mismatch), Mitigated | Local machine is Python 3.12 64-bit; baseline script fails without override. Validation run with `ALLOW_EDMC_PYTHON_MISMATCH=1` per non-release/dev guidance. |
| Monitor EDMC releases/discussions before shipping | No (process item) | Ongoing operational process; not automatable in this code change. Must be performed by release owner before shipment. |

##### Item 5.3.3 Deferred Follow-Ups (Captured 2026-03-06)

- Rule-layer composition follow-up (out of scope for this change):
  - keep runtime plugin-group controls as CMDR override layer,
  - add future rule-evaluation layer that gates display state before client render,
  - ensure composition model remains `effective_on = rule_on AND cmdr_on` (with `unset => on` at CMDR layer).
- Operational rollout follow-up:
  - track `plugin_group_status` counters in debug sessions during early adoption to confirm disabled-drop activity in real-world payload mixes.

##### Item 5.3.4 Final Quality Gates (Completed 2026-03-06)

- `make check` completed successfully (`ruff`, `mypy`, full `pytest`).
- Full suite result at gate: `519 passed, 25 skipped`.

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
- Feature is validated, documented, and ready for release.
- Follow-up items are explicitly captured.

## Test Plan (Per Iteration)
- Env setup (once per machine):
- `python3 -m venv overlay_client/.venv && overlay_client/.venv/bin/python -m pip install -U pip pytest ruff mypy`
- Headless quick pass:
- `overlay_client/.venv/bin/python -m pytest`
- Targeted tests:
- `overlay_client/.venv/bin/python -m pytest <path/to/tests> -k "<pattern>"`
- Milestone checks:
- `make check`
- `make test`
- Compliance baseline check (release/compliance work):
- `python scripts/check_edmc_python.py`

## Implementation Results
- Plan created on 2026-03-06.
- Phase 1 completed (requirements/contracts/state model locked; documentation artifacts added, no runtime code changes).
- Phase 2 completed (runtime state plumbing, early-drop gate, status backend, and client fallback filter implemented).
- Phase 3 completed (chat command controls, hotkey action controls, and controller/manager checkbox UX wired to true plugin-group on/off).
- Phase 4 completed (logical on/off refactor + action/wiki/release-note documentation updates complete).
- Phase 5 completed (validation coverage, counter/perf verification, compliance/release readiness documented).
- Phase 6 completed (runtime clear-event emission, client immediate targeted cache eviction, docs/release updates, and validation evidence recorded).

### Phase 1 Execution Summary
- Stage 1.1:
- Completed: canonical key/payload schema and chat coercion rules locked.
- Documented command normalization matrix for `on/off/toggle/status`, including equivalent `turn` phrasing.
- Documented hotkey payload schema (`plugin_group` + `plugin_groups`) with union+dedupe semantics.
- Documented unknown-group handling as one EDMC warning per unknown group.
- Stage 1.2:
- Completed: per-group state model, bulk global semantics, persistence, and migration behavior locked.
- Documented sequencing table for bulk-vs-targeted behavior and unset default-on semantics.
- Documented persisted-state snapshot and confirmed no separate global enabled flag.
- Documented stale-entry behavior (ignored, no auto-prune) and hybrid metadata scope.
- Stage 1.3:
- Completed: runtime-authoritative gating with shared resolver extraction and safe rollout expectations locked.
- Documented staged rollout (`R0`-`R3`), parity counters, and rollback triggers.
- Documented client fallback posture during rollout and cutover safety constraints.

### Tests Run For Phase 1
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py -k "command or toggle or payload"`
- Result: passed (`21 passed, 8 deselected`).
- `overlay_client/.venv/bin/python -m pytest tests/test_preferences_persistence.py -k "opacity or toggle or persistence"`
- Result: passed (`3 passed`).
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "data_client or render_surface or payload_model"`
- Result: passed (`16 passed, 6 skipped, 208 deselected`).

### Phase 2 Execution Summary
- Stage 2.1:
- Completed: added `PluginGroupStateManager` with per-group enabled-state persistence in `overlay_groupings.user.json` (`_plugin_group_state` metadata).
- Completed: enforced no separate persisted global flag by modeling no-payload global behavior as per-group bulk state representation.
- Completed: propagated state to client via `OverlayConfig` (`plugin_group_states`, `plugin_group_state_default_on`).
- Stage 2.2:
- Completed: added runtime authoritative early-drop gate in `_publish_payload` for disabled `LegacyOverlay` groups.
- Completed: retained hybrid metadata (`bounds`, `last_payload_seen_at`, `last_bounds_updated_at`) and counters (`disabled_payload_drop_count`, parity/drop metadata counters).
- Completed: added client defensive fallback filter using the same shared resolver path.
- Stage 2.3:
- Completed: implemented backend status formatter/query (`plugin_group_status` CLI command and manager formatter).
- Completed: status output now supports deterministic alphabetical `<plugin_group_name>: On|Off` lines for downstream chat/UI integration in Phase 3.

### Tests Run For Phase 2
- `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_resolver.py tests/test_plugin_group_state.py tests/test_runtime_plugin_group_publish.py tests/test_overlay_config_payload.py overlay_client/tests/test_launcher_group_filter.py`
- Result: passed (`11 passed`).
- `overlay_client/.venv/bin/python -m pytest tests/test_runtime_services.py tests/test_controller_services.py`
- Result: passed (`10 passed`).
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "render_surface or grouping_helper or payload_bounds"`
- Result: passed (`11 passed, 6 skipped, 216 deselected`).
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py -k "plugins or state or list"`
- Result: skipped/no matches (`0 selected, 21 deselected`).

### Phase 3 Execution Summary
- Stage 3.1:
- Completed: added shared plugin-group control service (`overlay_plugin/plugin_group_controls.py`) for target parsing (`plugin_group` + `plugin_groups`), unknown-group warning emission, and on/off/toggle orchestration.
- Completed: extended runtime with group-state delegates and new CLI commands (`plugin_group_set`, `plugin_group_toggle`, existing `plugin_group_status` integration).
- Completed: chat command parser now supports `on`, `off`, `toggle` (plus configurable toggle token), and `status` with phrase coercion:
- `!ovr on "BGS-Tally Objectives"`
- `!ovr "BGS-Tally Objectives" on`
- `!ovr turn "BGS-Tally Objectives" on`
- `!ovr turn on "BGS-Tally Objectives"`
- Completed: `status` renders alphabetical `<plugin_group_name>: On|Off` lines to overlay text and logs status lines at DEBUG.
- Stage 3.2:
- Completed: EDMCHotkeys integration now uses true plugin-group on/off/toggle paths instead of opacity toggling.
- Completed: added `Toggle Overlay` action (`edmcmodernoverlay.hotkeys.toggle`).
- Completed: `Overlay On` / `Overlay Off` / `Toggle Overlay` now parse payload targets via `plugin_group` and optional `plugin_groups` with union+dedupe behavior.
- Completed: unknown plugin-group targets are ignored and warned once per group through EDMC logs via shared control service.
- Stage 3.3:
- Completed: Overlay Controller now includes a per-group `Enabled` checkbox in the sidebar context panel.
- Completed: controller checkbox placement is immediately above `Reset` in the same context block.
- Completed: controller checkbox reads/writes runtime group state through plugin CLI (`plugin_group_status` / `plugin_group_set`) and refreshes live state during polling.
- Completed: `utils/plugin_group_manager.py` now includes a per-group enabled checkbox with runtime-backed set/status synchronization.
- Completed: off groups remain selectable and editable in both surfaces (visibility/editability unchanged).

### Tests Run For Phase 3
- `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_state.py tests/test_plugin_group_controls.py tests/test_journal_commands.py tests/test_hotkeys.py tests/test_launch_entrypoint_parity.py overlay_controller/tests/test_plugin_bridge.py`
- Result: passed (`44 passed`).
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests/test_idprefix_refresh.py overlay_controller/tests/test_status_poll_mode_profile.py tests/test_overlay_controller_platform.py`
- Result: passed (`14 passed`).
- `overlay_client/.venv/bin/python -m ruff check overlay_plugin/plugin_group_controls.py overlay_plugin/plugin_group_state.py overlay_plugin/journal_commands.py overlay_plugin/hotkeys.py load.py overlay_controller/controller/layout.py overlay_controller/overlay_controller.py overlay_controller/services/plugin_bridge.py utils/plugin_group_manager.py tests/test_plugin_group_controls.py tests/test_plugin_group_state.py tests/test_journal_commands.py tests/test_hotkeys.py tests/test_launch_entrypoint_parity.py overlay_controller/tests/test_plugin_bridge.py`
- Result: passed (`All checks passed`).

### Phase 4 Execution Summary
- Stage 4.1:
- Completed.
- Item `4.1.1` completed: inventory/routing map captured under `Stage 4.1 Contract Artifacts` with legacy opacity paths vs authoritative true on/off routes.
- Item `4.1.2` completed: confirmed no residual logical on/off opacity routing in chat/hotkey/controller pathways; opacity methods explicitly documented as visual-only.
- Item `4.1.3` completed: regression tests added/expanded to enforce logical on/off vs opacity separation and verify continued numeric opacity behavior.
- Item `4.1.4` completed: final runtime handler scan + lint/test validation confirms no residual logical on/off opacity coupling.
- Stage 4.2:
- Completed.
- Item `4.2.1` completed: created `docs/wiki/Overlay-Actions.md` skeleton with required section anchors for action usage documentation.
- Item `4.2.2` completed: added explicit normative chat/hotkey examples, `turn` coercion examples, and toggle token note.
- Item `4.2.3` completed: added canonical behavior matrix for global/targeted/mixed payload action semantics and unknown-group handling.
- Item `4.2.4` completed: added migration notes (legacy opacity logical-off ignored, `unset => On`, opacity remains visual-only).
- Stage 4.3:
- Completed.
- Item `4.3.1` completed: updated `Chat-Command.md` for one-word tokens/coercion and removed contradictory opacity-based logical-off wording.
- Item `4.3.2` completed: updated `Overlay-Controller.md` and `Usage.md` for per-group enabled checkbox behavior, status expectations, and true on/off semantics.
- Item `4.3.3` completed: added `Overlay Actions` links to sidebar/home navigation for discoverability.
- Item `4.3.4` completed: updated release notes with migration behavior and added Phase 4 doc-delta summary references in this plan.

### Tests Run For Phase 4
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py tests/test_toggle_helpers.py`
- Result: passed (`35 passed`).
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py tests/test_preferences_persistence.py tests/test_toggle_helpers.py`
- Result: passed (`39 passed`).
- `overlay_client/.venv/bin/python -m ruff check load.py overlay_plugin/journal_commands.py overlay_plugin/hotkeys.py tests/test_journal_commands.py tests/test_hotkeys.py`
- Result: passed (`All checks passed`).
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py`
- Result: passed (`33 passed`).
- `overlay_client/.venv/bin/python -m pytest -k "journal_commands or hotkeys"`
- Result: passed (`34 passed, 6 skipped, 499 deselected`).

### Phase 5 Execution Summary
- Stage 5.1:
- Completed.
- Added requirement-to-test traceability matrix in this plan.
- Added deterministic tests for:
  - `off`/`toggle` chat coercion forms and strict `status` output ordering,
  - hotkey payload union/dedupe when both `plugin_group` and `plugin_groups` are provided,
  - unknown-group warning behavior (one warning per unknown group),
  - stale-entry/no-global-flag persistence semantics,
  - parity counter assertions on enabled/disabled payload paths.
- Stage 5.2:
- Completed.
- Validated runtime early-drop behavior and client fallback behavior using counter/path assertions.
- Confirmed disabled-group payloads skip broadcast/render paths while retaining hybrid metadata.
- Confirmed enabled-path behavior remains intact in focused client pipeline coverage.
- Stage 5.3:
- Completed.
- Finalized release-note wording for feature behavior and migration semantics.
- Completed compatibility/compliance yes/no review with explicit notes/remediations for non-code process/baseline items.
- Captured deferred follow-ups for future rule-layer composition and rollout monitoring.
- Executed final quality gates (`make check`) successfully.

### Tests Run For Phase 5
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py tests/test_plugin_group_controls.py`
- Result: passed (`38 passed`).
- `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_state.py tests/test_preferences_persistence.py`
- Result: passed (`8 passed`).
- `overlay_client/.venv/bin/python -m pytest overlay_controller/tests -k "plugin_bridge or status or group"`
- Result: passed (`24 passed, 27 deselected`).
- `overlay_client/.venv/bin/python -m pytest tests overlay_controller/tests overlay_client/tests -k "journal_commands or hotkeys or plugin_group or status"`
- Result: passed (`93 passed, 6 skipped, 445 deselected`).
- `overlay_client/.venv/bin/python -m pytest tests/test_runtime_plugin_group_publish.py tests/test_plugin_group_state.py`
- Result: passed (`7 passed`).
- `overlay_client/.venv/bin/python -m pytest tests/test_runtime_plugin_group_publish.py overlay_client/tests/test_launcher_group_filter.py -k "drop or disabled or metadata"`
- Result: passed (`2 passed, 3 deselected`).
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "render_surface or grouping_helper or payload_bounds"`
- Result: passed (`11 passed, 6 skipped, 216 deselected`).
- `python3 scripts/check_edmc_python.py`
- Result: failed in local dev env (expected baseline mismatch: Python 3.10.3 32-bit required; local was 3.12.3 64-bit).
- `ALLOW_EDMC_PYTHON_MISMATCH=1 python3 scripts/check_edmc_python.py`
- Result: passed with warning override (expected for non-release/dev environment).
- `make check`
- Result: passed (`ruff`/`mypy` clean; full test suite `519 passed, 25 skipped`).

## Phase 6: Immediate Clear On Group Off

### Objective
- Eliminate visible delay when groups are turned `off` by clearing already-rendered payloads immediately, while preserving existing on/off, opacity, cache, and controller behavior contracts.

### Problem Statement
- Current behavior drops new payloads when a group is turned off, but existing rendered items remain visible until TTL expiry.
- This creates a visible delay after `off`, especially for payloads with longer TTL values.

### Requirement Addendum
- When a plugin group is turned `off`, existing on-screen payloads for that group must clear immediately.
- This clear behavior applies to targeted and bulk `off` actions from chat, hotkeys, controller, and manager flows.
- Opacity behavior remains unchanged.

| Stage | Description | Status |
| --- | --- | --- |
| 6.1 | Runtime clear-event contract and emission | Completed |
| 6.2 | Client targeted cache eviction and immediate repaint | Completed |
| 6.3 | End-to-end action semantics (targeted + global/idempotent off) | Completed |
| 6.4 | Validation, docs sync, and rollout notes | Completed |

### Phase 6 Execution Summary
- Stage 6.1:
- Completed.
- Extended runtime control service to emit `OverlayPluginGroupClear` events on `off` actions with resolved clear targets.
- Added runtime publisher wiring for clear-control payload broadcast.
- Stage 6.2:
- Completed.
- Added client launcher handling for `OverlayPluginGroupClear`.
- Added targeted client store eviction (`clear_plugin_groups`) with immediate repaint.
- Implemented resolver-based cached-item group matching for safe targeted removal.
- Stage 6.3:
- Completed.
- Enforced global/idempotent `off` clear semantics via resolved full currently-defined group set.
- Preserved unknown-group behavior (`ignore + warning`, no clear for unknown-only targeted requests).
- Stage 6.4:
- Completed.
- Updated action docs and release notes with immediate-clear behavior.
- Added/updated regression tests and recorded Phase 6 verification evidence.

#### Stage 6.1 Detailed Plan
- Objective:
- Emit a deterministic clear-control payload whenever `off` semantics require immediate cache eviction.
- Primary touch points:
- `overlay_plugin/plugin_group_controls.py`
- `load.py`
- Steps:
- Extend control service wiring to accept a `publish_group_clear` callback.
- Resolve clear-targets using canonical `plugin_group_name` values.
- Emit `OverlayPluginGroupClear` when action is `off` and resolved clear-targets are non-empty.
- Keep `on` and `toggle` behavior unchanged.
- Acceptance criteria:
- `off` emits clear-control payload with correct target set.
- `on` never emits clear-control payload.
- No change to existing enabled-state persistence semantics.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_controls.py tests/test_plugin_group_state.py -k "off or clear or plugin_group"`

#### Stage 6.2 Detailed Plan
- Objective:
- Evict matching payloads from live client store immediately on clear-control event.
- Primary touch points:
- `overlay_client/launcher.py`
- `overlay_client/control_surface.py` and/or `overlay_client/render_surface.py`
- Steps:
- Add handler branch for `event == "OverlayPluginGroupClear"` in launcher.
- Add `clear_plugin_groups(group_names)` to remove matching store items by resolved plugin-group mapping.
- Trigger immediate repaint after eviction.
- Ensure non-target group items remain untouched.
- Acceptance criteria:
- Matching target payloads disappear immediately (no TTL wait).
- Non-target payloads remain.
- No controller cache reset side effects.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_launcher_group_filter.py overlay_client/tests/test_render_surface_mixin.py -k "clear or group"`

#### Stage 6.3 Detailed Plan
- Objective:
- Ensure targeted and global `off` semantics are consistent across all control surfaces.
- Primary touch points:
- `overlay_plugin/journal_commands.py`
- `overlay_plugin/hotkeys.py`
- `overlay_controller/services/plugin_bridge.py`
- `utils/plugin_group_manager.py`
- Steps:
- Confirm all existing `off` paths route through shared control service clear emission.
- Enforce bulk/global `off` clear target resolution as full currently-defined group set.
- Enforce idempotent behavior: repeated global `off` still emits clear event.
- Preserve unknown-group handling (ignore + warning) and avoid clear emission for unknown-only targeted requests.
- Acceptance criteria:
- Chat, hotkeys, controller, and manager `off` commands have identical clear semantics.
- Global `off` clears all currently defined groups even when state already off.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py tests/test_plugin_group_controls.py -k "off or clear or plugin_group"`

#### Stage 6.4 Detailed Plan
- Objective:
- Lock release readiness for Phase 6 and ensure docs remain consistent.
- Primary touch points:
- `docs/plans/plugin-group-onoff.md`
- `docs/wiki/Overlay-Actions.md`
- `RELEASE_NOTES.md`
- Steps:
- Add/refresh tests documenting immediate-clear behavior.
- Update wiki/release notes with immediate-clear expectations for `off`.
- Record rollout caveats and verification evidence in plan results.
- Acceptance criteria:
- Docs match implemented behavior.
- Full quality gates pass.
- Verification to run:
- `make check`

#### Phase 6 Detailed Execution Plan

| Stage | Goal | Detailed work items | Outputs to document | Validation for completion |
| --- | --- | --- | --- | --- |
| 6.1 | Emit runtime clear events for `off` | Add clear publisher callback and clear-target resolution; emit `OverlayPluginGroupClear` for off-only paths with non-empty target sets | Runtime clear contract, payload schema, emission conditions | Runtime emits correct clear payloads without altering existing on/off persistence behavior |
| 6.2 | Remove target group payloads immediately in client | Add clear-event branch in launcher; implement targeted store eviction and immediate repaint | Client eviction flow notes, affected store/repaint paths | Target payloads disappear immediately, non-target payloads persist |
| 6.3 | Ensure consistent semantics across entry points | Validate chat/hotkey/controller/manager `off` flows share same clear behavior; enforce global/idempotent semantics | Entry-point parity matrix and idempotency notes | All `off` entry points behave consistently for targeted/global operations |
| 6.4 | Finalize docs and readiness | Update action docs/release notes and run full quality gates | Doc delta summary + test evidence | Release artifacts reflect immediate-clear behavior and checks pass |

#### Phase 6 Artifact Checklist
- Clear event payload contract documented and implemented.
- Runtime clear emission happens for `off` only.
- Global `off` clear targets include all currently defined groups.
- Repeated global `off` still emits clear for cleanup.
- Unknown-only targeted `off` emits warnings but no clear event.
- Client targeted eviction is immediate and repaint is immediate.
- Non-target payloads remain visible.
- Controller placement/cache files remain unchanged.
- Opacity and TTL semantics remain unchanged.

#### Phase 6 Implementation Checklist (Execution Order)

| Item | Stage | Task | Primary touch points | Verification |
| --- | --- | --- | --- | --- |
| 6.1.1 | 6.1 | Add `publish_group_clear` callback contract to control service and runtime wiring | `overlay_plugin/plugin_group_controls.py`, `load.py` | `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_controls.py -k "clear or off"` |
| 6.1.2 | 6.1 | Implement clear-target resolution rules (targeted vs global/idempotent) | `overlay_plugin/plugin_group_controls.py` | `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_controls.py tests/test_plugin_group_state.py -k "global or off or unknown"` |
| 6.1.3 | 6.1 | Emit `OverlayPluginGroupClear` payload from runtime broadcaster path | `load.py` | `overlay_client/.venv/bin/python -m pytest tests/test_runtime_plugin_group_publish.py -k "clear or plugin_group"` |
| 6.2.1 | 6.2 | Add launcher handler for `OverlayPluginGroupClear` | `overlay_client/launcher.py` | `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_launcher_group_filter.py -k "clear"` |
| 6.2.2 | 6.2 | Add client `clear_plugin_groups(group_names)` store-eviction + repaint path | `overlay_client/control_surface.py`, `overlay_client/render_surface.py` | `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py -k "clear or repaint"` |
| 6.2.3 | 6.2 | Ensure resolver-based group matching for cached items during eviction | client clear helper + resolver seams | `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "group_filter or clear"` |
| 6.3.1 | 6.3 | Validate chat/hotkey/controller/manager parity for targeted/global `off` clear semantics | `tests/test_journal_commands.py`, `tests/test_hotkeys.py`, controller bridge tests | `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py overlay_controller/tests/test_plugin_bridge.py -k "off or clear or plugin_group"` |
| 6.3.2 | 6.3 | Add idempotent global `off` regression assertions | plugin control tests | `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_controls.py -k "idempotent or global"` |
| 6.4.1 | 6.4 | Update docs for immediate clear expectations | `docs/wiki/Overlay-Actions.md`, `docs/plans/plugin-group-onoff.md` | manual review |
| 6.4.2 | 6.4 | Update release notes for phase 6 behavior | `RELEASE_NOTES.md` | manual review |
| 6.4.3 | 6.4 | Run final quality gates | repo-wide | `make check` |

#### Phase 6 Safe Boundaries (Locked)
- Scope of clear:
- only remove matching items from the in-memory legacy payload store used for current rendering.
- do not issue broad `clear_all` behavior for non-target groups.
- Controller cache safety:
- do not call `reset_group_cache()` as part of off-clear flow.
- do not call `GroupPlacementCache.reset()` or otherwise wipe `overlay_group_cache.json`.
- keep controller placement snapshots/anchors intact.
- Persistence safety:
- do not write any new cache-clearing state into `overlay_groupings.user.json`.
- keep plugin-group enabled persistence semantics unchanged (only existing on/off state writes).
- Behavior safety:
- do not change TTL semantics for normal payload processing.
- keep runtime early-drop and client fallback filters unchanged for incoming payloads.
- keep opacity controls isolated from logical on/off and clear behavior.
- Threading/UI safety:
- perform client-side store mutation and repaint on the existing payload-handling/UI path only (no background-thread UI mutation).

#### Stage 6 Contract Artifacts

`OverlayPluginGroupClear` payload contract:

```json
{
  "event": "OverlayPluginGroupClear",
  "plugin_groups": ["BGS-Tally Objectives", "BGS-Tally Colonisation"],
  "source": "chat_off"
}
```

- `plugin_groups` contains canonical `plugin_group_name` values.
- For targeted `off`, targets are resolved targeted groups only.
- For global/bulk `off`, targets are all currently defined groups.
- Clear emission is independent of state-delta for global/idempotent off.

#### Phase 6 Exit Criteria
- Turning a group `off` removes existing on-screen payloads for that group immediately.
- Global `off` clears all currently defined groups immediately, including repeated/idempotent invocations.
- Controller cache and persisted placement state remain intact.
- Docs and release notes reflect final behavior.

### Tests Run For Phase 6
- `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_controls.py tests/test_runtime_plugin_group_publish.py overlay_client/tests/test_launcher_group_filter.py overlay_client/tests/test_plugin_group_clear.py overlay_client/tests/test_control_surface_group_clear.py`
- Result: passed (`16 passed`).
- `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_controls.py tests/test_plugin_group_state.py -k "global or off or unknown"`
- Result: passed (`3 passed, 7 deselected`).
- `overlay_client/.venv/bin/python -m pytest tests/test_runtime_plugin_group_publish.py -k "clear or plugin_group"`
- Result: passed (`3 passed`).
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_hotkeys.py tests/test_plugin_group_controls.py overlay_controller/tests/test_plugin_bridge.py -k "off or clear or plugin_group"`
- Result: passed (`9 passed, 37 deselected`).
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_launcher_group_filter.py overlay_client/tests/test_render_surface_mixin.py overlay_client/tests/test_control_surface_group_clear.py overlay_client/tests/test_plugin_group_clear.py -k "clear or group"`
- Result: passed (`10 passed, 9 deselected`).
- `make check`
- Result: passed (`ruff`/`mypy` clean; full suite `527 passed, 25 skipped`).

### Non-Goals
- No rule-layer behavior changes.
- No changes to TTL semantics for normal payload lifecycle.
- No change to opacity controls.

## Addendum: `!ovr status` Enriched Group Status

### Requirement
- Update `!ovr status` output to include three state dimensions per plugin group:
- `plugin_group_name: Enabled|Not Enabled|Unknown|Ignored, Seen|Not Seen, On|Off`
- Continue listing one plugin group per line in alphabetical order.
- Continue hiding internal `EDMCModernOverlay` command/status groups from `!ovr status`.

### Data Sources and Resolution
- `plugin_group_name`:
- from canonical plugin-group names resolved by plugin runtime group resolver (current status source of truth).
- `Enabled|Not Enabled|Unknown|Ignored`:
- from plugin install/enable scan data used by `!ovr plugins`, mapped from plugin group -> owning plugin.
- `Seen|Not Seen`:
- from runtime in-memory plugin-group metadata (for example `last_payload_seen_at`).
- `On|Off`:
- from plugin-group runtime state manager (`_plugin_group_state.enabled`), defaulting to `On` when unset.

### Implementation Notes
- Keep grouping/schema separation intact:
- do not move `_plugin_group_state` fields into plugin definition schema.
- Add a shared status composer in plugin runtime so chat path and any future controller/API status path can reuse the same line rendering logic.
- Keep unknown plugin-group behavior unchanged (`ignore + warning` in EDMC logs) for control actions; status rendering should be best-effort and non-fatal.

### Decisions Locked
- plugin status mapping:
- preserve `Unknown` and `Ignored` as explicit first-slot states (do not collapse into `Not Enabled`).
- `Seen|Not Seen` mapping:
- `Seen` uses runtime in-memory metadata evidence for that plugin group (for example `last_payload_seen_at`).
- Missing owner mapping:
- render as `Unknown` in the first status slot (for example `Group X: Unknown, Seen, On`).
- Scan freshness:
- use cached plugin scan results (do not run a full scan on every `!ovr status` invocation).

### Detailed Execution Plan

| Stage | Description | Status |
| --- | --- | --- |
| 7.1 | Add a shared enriched-status composer for plugin groups | Completed |
| 7.2 | Add plugin scan cache service used by `!ovr plugins` and `!ovr status` | Completed |
| 7.3 | Wire `!ovr status` to enriched lines and preserve hide-filter behavior | Completed |
| 7.4 | Add regression tests for mapping, seen-state, sort order, and fallback states | Completed |
| 7.5 | Update docs and release notes for enriched status output | Completed |

#### Stage 7.1 Plan
- Objective:
- create a runtime helper that returns enriched status lines in final user format:
- `plugin_group_name: Enabled|Not Enabled|Unknown|Ignored, Seen|Not Seen, On|Off`
- Primary touch points:
- `overlay_plugin` new module (for example `group_status_enrichment.py`)
- `load.py` runtime method surface (minimal wiring only)
- Design details:
- source `plugin_group_name` and `On|Off` from existing plugin-group control/state manager.
- source `Seen|Not Seen` from runtime in-memory metadata snapshot.
- source owner mapping from resolver indexes and fallback `Unknown` when owner is missing.
- keep line ordering alphabetical by `plugin_group_name` (case-insensitive).
- Acceptance criteria:
- helper emits one line per visible plugin group in required title-case token format.
- owner-missing groups render `Unknown`.
- no opacity or on/off behavior changes.
- Verification:
- `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_state.py -k "status"`

#### Stage 7.2 Plan
- Objective:
- implement plugin enablement scan caching so `!ovr status` does not trigger full rescans each time.
- Primary touch points:
- `overlay_plugin/plugin_scan_services.py`
- `overlay_plugin` new cache module (for example `plugin_scan_cache.py`)
- Design details:
- cache stores `{plugin_name -> status}` using same status tokens as plugin scan flow.
- `!ovr plugins` refreshes cache after a full scan.
- `!ovr status` reads cache and maps owner plugin status to `Enabled|Not Enabled|Unknown|Ignored`.
- if cache is empty at startup, perform one lazy initial scan, then serve cached values.
- Acceptance criteria:
- repeated `!ovr status` calls do not rescan when cache is populated and fresh.
- cache values match plugin scan status mapping.
- Verification:
- `overlay_client/.venv/bin/python -m pytest tests/test_plugin_scan_services.py -k "cache or status"`

#### Stage 7.3 Plan
- Objective:
- route chat command status rendering to enriched lines while preserving current visibility filtering.
- Primary touch points:
- `overlay_plugin/journal_commands.py`
- `load.py`
- Design details:
- expose `get_enriched_plugin_group_status_lines()` on runtime and wire command helper to use it.
- keep existing hide-filter for internal `EDMCModernOverlay` groups.
- keep existing overlay-first / chat-fallback delivery behavior.
- Acceptance criteria:
- `!ovr status` outputs enriched lines with three state slots.
- hidden internal groups stay hidden.
- no behavior regressions for `on/off/toggle` command handling.
- Verification:
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py -k "status"`

#### Stage 7.4 Plan
- Objective:
- anchor behavior with targeted tests for all mapping/fallback rules.
- Primary touch points:
- `tests/test_journal_commands.py`
- `tests/test_plugin_group_state.py`
- new tests for enrichment/cache modules.
- Required assertions:
- title-case output tokens.
- alphabetical ordering.
- `Seen` derives from runtime metadata presence.
- `Unknown`/`Ignored` states preserved.
- owner-missing group renders `Unknown`.
- hidden `EDMCModernOverlay` status groups excluded.
- Verification:
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_plugin_group_state.py tests/test_plugin_scan_services.py -k "status or seen or unknown or ignored"`

#### Stage 7.5 Plan
- Objective:
- finalize docs and release communication for enriched `!ovr status`.
- Primary touch points:
- `docs/wiki/Chat-Command.md`
- `docs/wiki/Usage.md`
- `RELEASE_NOTES.md`
- `docs/plans/plugin-group-onoff.md`
- Acceptance criteria:
- docs include final status format and semantics for each slot.
- release notes call out enriched status and cache-backed plugin state behavior.
- Verification:
- manual doc review + `make check`

### Implementation Checklist (Ordered)

| Item | Stage | Task | Primary touch points | Validation |
| --- | --- | --- | --- | --- |
| 7.1.1 | 7.1 | Add enriched status DTO/composer module | `overlay_plugin/group_status_enrichment.py` | `overlay_client/.venv/bin/python -m pytest tests/test_plugin_group_state.py -k "status"` |
| 7.1.2 | 7.1 | Add resolver owner-map extraction with `Unknown` fallback | enrichment module + resolver seam | targeted unit tests |
| 7.2.1 | 7.2 | Add plugin scan cache structure + read/write API | `overlay_plugin/plugin_scan_cache.py` | cache unit tests |
| 7.2.2 | 7.2 | Refresh cache during `!ovr plugins` scan path | `overlay_plugin/plugin_scan_services.py` | scan service tests |
| 7.2.3 | 7.2 | Consume cached scan states in enriched status path | enrichment + runtime wiring | status tests |
| 7.3.1 | 7.3 | Wire runtime status callback to enriched composer | `load.py` | command helper tests |
| 7.3.2 | 7.3 | Keep internal-group hide filter in chat status output | `overlay_plugin/journal_commands.py` | status filter tests |
| 7.4.1 | 7.4 | Add end-to-end `!ovr status` output assertions | `tests/test_journal_commands.py` | pytest targeted |
| 7.4.2 | 7.4 | Add seen/unknown/ignored mapping regression tests | new/updated test modules | pytest targeted |
| 7.5.1 | 7.5 | Update chat command docs and release notes | docs + `RELEASE_NOTES.md` | manual review |
| 7.5.2 | 7.5 | Run full quality gates | repo-wide | `make check` |

### Safe Boundaries
- Do not change plugin-group on/off state persistence semantics.
- Do not move `_plugin_group_state` into grouping definition schema.
- Do not change payload rendering, TTL, or clear-on-off behavior.
- Do not expose hidden internal `EDMCModernOverlay` status groups in chat output.
- Avoid adding new logic to existing monolith modules unless only minimal wiring is required.

### Exit Criteria
- `!ovr status` consistently renders:
- `plugin_group_name: Enabled|Not Enabled|Unknown|Ignored, Seen|Not Seen, On|Off`
- output is alphabetical, title-case, and hides internal groups.
- plugin enablement state is cache-backed rather than full-scan-per-status-invocation.
- docs and release notes are updated and tests pass.

### Addendum Execution Summary
- Stage 7.1:
- Completed.
- Added `overlay_plugin/group_status_enrichment.py` with a shared status composer and title-case token normalization for `Enabled|Not Enabled|Unknown|Ignored`.
- Added plugin-group owner mapping support in resolver/state manager (`group_owner_map`) with `Unknown` fallback when ownership is ambiguous/missing.
- Stage 7.2:
- Completed.
- Added `overlay_plugin/plugin_scan_cache.py` and cache-aware status access in `overlay_plugin/plugin_scan_services.py`.
- `!ovr plugins` now refreshes cache as part of normal scan flow.
- `!ovr status` reads cached scan state and performs lazy scan only when cache is empty.
- Stage 7.3:
- Completed.
- Updated runtime `get_plugin_group_status_lines` to compose enriched lines using cached plugin scan state, runtime metadata (`Seen`), and group on/off state.
- Kept existing `journal_commands` filter so internal `EDMCModernOverlay` groups remain hidden from chat status output.
- Stage 7.4:
- Completed.
- Added new regression tests:
- `tests/test_group_status_enrichment.py`
- `tests/test_plugin_scan_services.py`
- `tests/test_group_status_runtime.py`
- Extended resolver coverage in `tests/test_plugin_group_resolver.py` for owner-map ambiguity handling.
- Stage 7.5:
- Completed.
- Updated docs/wiki status format descriptions:
- `docs/wiki/Chat-Command.md`
- `docs/wiki/Usage.md`
- `docs/wiki/Overlay-Actions.md`
- Added release note entry in `RELEASE_NOTES.md`.

### Tests Run For Addendum
- `overlay_client/.venv/bin/python -m ruff check overlay_plugin/plugin_scan_cache.py overlay_plugin/plugin_scan_services.py overlay_plugin/group_status_enrichment.py overlay_plugin/plugin_group_resolver.py overlay_plugin/plugin_group_state.py load.py tests/test_group_status_enrichment.py tests/test_plugin_scan_services.py tests/test_group_status_runtime.py tests/test_plugin_group_resolver.py`
- Result: passed.
- `overlay_client/.venv/bin/python -m pytest tests/test_group_status_enrichment.py tests/test_plugin_scan_services.py tests/test_group_status_runtime.py tests/test_plugin_group_resolver.py tests/test_journal_commands.py`
- Result: passed (`35 passed`).
- `overlay_client/.venv/bin/python -m pytest tests/test_launch_command_pref.py tests/test_launch_entrypoint_parity.py tests/test_plugin_group_state.py tests/test_hotkeys.py`
- Result: passed (`17 passed`).

## Phase 8: `!ovr status` True Table Overlay

### Objective
- Replace line-per-message status rendering with a true table overlay layout for `!ovr status`.
- Keep status data semantics unchanged from Phase 7 (`Enabled|Not Enabled|Unknown|Ignored`, `Seen|Not Seen`, `On|Off`).

### Non-Functional Requirement (Locked)
- Do not add new feature logic to monolith modules (`load.py`, `overlay_plugin/journal_commands.py`).
- Only minimal wiring changes are allowed in monolith modules.
- New table behavior must live in focused helper modules under `overlay_plugin/`.

### Output Contract
- The overlay renders a structured table with:
- Header row: `Plugin Group | Plugin | Seen | State`
- Data rows:
- `Plugin Group` = canonical `plugin_group_name`
- `Plugin` = `Enabled|Not Enabled|Unknown|Ignored`
- `Seen` = `Seen|Not Seen`
- `State` = `On|Off`
- Rows are alphabetically ordered by `plugin_group_name`.
- Internal `EDMCModernOverlay` groups remain hidden.

### Decisions Locked
- Row capacity:
- use a fixed max row count; when rows exceed the cap, render a final overflow row with `+N more`.
- Long cell content:
- truncate with ellipsis (no wrapping).
- Visual styling:
- keep current command-group styling (`black` background, `blue` border, white text).
- Border strategy:
- minimal borders only (outer border + row separators; no full cell grid).
- Empty-state behavior:
- keep current plan behavior (existing non-table fallback path for no groups configured).

| Stage | Description | Status |
| --- | --- | --- |
| 8.1 | Define table model and deterministic column/layout rules | Completed |
| 8.2 | Build table payload renderer (header, cells, borders) in new modules | Completed |
| 8.3 | Wire `!ovr status` overlay path to table renderer with minimal monolith edits | Completed |
| 8.4 | Add regression tests for layout/payload contract and visibility behavior | Completed |
| 8.5 | Update docs/release notes and record execution evidence | Completed |

#### Stage 8.1 Plan
- Objective:
- establish a stable, testable table model and layout spec before rendering.
- Primary touch points:
- new `overlay_plugin/status_table_model.py`
- new `overlay_plugin/status_table_layout.py`
- Design details:
- define typed row model from enriched status data.
- define fixed row height, header height, column widths, left/top origin, padding.
- enforce fixed max rows with deterministic overflow row (`+N more`).
- define ellipsis truncation policy for long text cells (no wrapping).
- Acceptance criteria:
- table model and layout math are pure and unit-testable.
- no runtime behavior changes yet.
- Verification:
- `overlay_client/.venv/bin/python -m pytest tests/test_status_table_layout.py`

#### Stage 8.2 Plan
- Objective:
- render a true table using overlay payload primitives.
- Primary touch points:
- new `overlay_plugin/status_table_payloads.py`
- existing `overlay_plugin/command_overlay_groups.py` (renderer hook only)
- Design details:
- emit header cell text payloads.
- emit row cell text payloads at column X offsets.
- emit minimal borders using `LegacyOverlay` shapes (outer border + row separators).
- keep per-render payload IDs prefixed with existing group status prefix for grouping compatibility.
- Acceptance criteria:
- renderer returns deterministic payload set for a given table model.
- table remains readable with variable row counts.
- Verification:
- `overlay_client/.venv/bin/python -m pytest tests/test_status_table_payloads.py`

#### Stage 8.3 Plan
- Objective:
- plug table renderer into current status overlay send flow with minimal monolith wiring.
- Primary touch points:
- `overlay_plugin/command_overlay_groups.py` (public render function swap)
- minimal call-site compatibility wiring in `load.py` only if required by signature.
- Design details:
- preserve current `send_group_status_overlay(...)` call contract.
- map enriched lines into table rows via new model layer.
- preserve existing hidden-group filtering from chat path.
- Acceptance criteria:
- `!ovr status` renders as table without changing command semantics.
- no regressions for `on/off/toggle` handling.
- Verification:
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py -k "status"`

#### Stage 8.4 Plan
- Objective:
- lock table behavior with regression tests.
- Primary touch points:
- new `tests/test_status_table_layout.py`
- new `tests/test_status_table_payloads.py`
- updates to `tests/test_command_overlay_groups.py` as needed.
- Required assertions:
- header row always present.
- row ordering alphabetical.
- fixed max-row cap enforced with overflow row when needed.
- long text is truncated with ellipsis.
- payload IDs stable prefix contract.
- minimal border payloads (outer + row separators) emitted as expected.
- empty-state rendering remains graceful.
- internal status groups remain hidden.
- Verification:
- `overlay_client/.venv/bin/python -m pytest tests/test_status_table_layout.py tests/test_status_table_payloads.py tests/test_command_overlay_groups.py tests/test_journal_commands.py -k "status or table"`

#### Stage 8.5 Plan
- Objective:
- finalize release readiness and documentation for table rendering.
- Primary touch points:
- `docs/wiki/Overlay-Actions.md`
- `docs/wiki/Chat-Command.md`
- `docs/wiki/Usage.md`
- `RELEASE_NOTES.md`
- `docs/plans/plugin-group-onoff.md`
- Acceptance criteria:
- docs describe true table output format and behavior.
- release notes call out table rendering change for `!ovr status`.
- Verification:
- `make check`

### Implementation Checklist (Ordered)

| Item | Stage | Task | Primary touch points | Validation |
| --- | --- | --- | --- | --- |
| 8.1.1 | 8.1 | Add status table row model and parsing helpers | `overlay_plugin/status_table_model.py` | model unit tests |
| 8.1.2 | 8.1 | Add deterministic table layout math | `overlay_plugin/status_table_layout.py` | layout unit tests |
| 8.2.1 | 8.2 | Add table payload builder for text cells | `overlay_plugin/status_table_payloads.py` | payload unit tests |
| 8.2.2 | 8.2 | Add border/separator shape payload generation | `overlay_plugin/status_table_payloads.py` | payload unit tests |
| 8.2.3 | 8.2 | Integrate renderer entrypoint in command overlay group helper | `overlay_plugin/command_overlay_groups.py` | renderer tests |
| 8.3.1 | 8.3 | Keep status overlay call contract stable, swap renderer | minimal wiring in `load.py` if needed | journal command tests |
| 8.4.1 | 8.4 | Add regression tests for table contract and hidden groups | `tests/test_status_table_*`, `tests/test_journal_commands.py` | pytest targeted |
| 8.4.2 | 8.4 | Validate fallback/empty table behavior | status table tests | pytest targeted |
| 8.5.1 | 8.5 | Update wiki docs with true table behavior | docs/wiki files | manual review |
| 8.5.2 | 8.5 | Update release notes + plan execution notes | `RELEASE_NOTES.md`, this plan doc | manual review + `make check` |

### Safe Boundaries
- Do not modify plugin-group on/off semantics, persistence, or clear behavior.
- Do not modify scan-cache semantics introduced in Phase 7.
- Do not remove existing internal-group hide filter behavior.
- Keep all new rendering logic in new helper modules; monolith edits must be minimal wiring only.
- Preserve existing payload ID prefixing/grouping behavior for status payloads.

### Exit Criteria
- `!ovr status` renders a true table (header + columns + rows) in overlay.
- Table rows reflect existing Phase 7 status semantics without data regressions.
- Internal `EDMCModernOverlay` status groups remain hidden.
- Docs/release notes updated and quality gates pass.

### Phase 8 Execution Summary
- Stage 8.1:
- Completed.
- Added pure table model/layout modules:
- `overlay_plugin/status_table_model.py`
- `overlay_plugin/status_table_layout.py`
- Implemented deterministic parsing, alphabetical ordering, row capping, overflow row (`+N more`), and ellipsis truncation helpers.
- Stage 8.2:
- Completed.
- Added `overlay_plugin/status_table_payloads.py` to emit:
- header text payloads,
- row cell text payloads,
- minimal border shapes (outer border + row separators).
- Preserved existing status payload ID prefix contract.
- Stage 8.3:
- Completed.
- Swapped `render_group_status_payloads` in `overlay_plugin/command_overlay_groups.py` to use the new table payload renderer.
- Kept monolith changes minimal (no new table logic in `load.py` or `journal_commands.py`).
- Stage 8.4:
- Completed.
- Added new regression tests:
- `tests/test_status_table_layout.py`
- `tests/test_status_table_model.py`
- `tests/test_status_table_payloads.py`
- Updated `tests/test_command_overlay_groups.py` for true-table payload contract.
- Re-ran key status/chat/hotkey coverage to confirm no behavior regressions.
- Stage 8.5:
- Completed.
- Updated docs and release notes for table rendering:
- `docs/wiki/Chat-Command.md`
- `docs/wiki/Usage.md`
- `docs/wiki/Overlay-Actions.md`
- `RELEASE_NOTES.md`

### Tests Run For Phase 8
- `overlay_client/.venv/bin/python -m ruff check overlay_plugin/status_table_layout.py overlay_plugin/status_table_model.py overlay_plugin/status_table_payloads.py overlay_plugin/command_overlay_groups.py tests/test_status_table_layout.py tests/test_status_table_model.py tests/test_status_table_payloads.py tests/test_command_overlay_groups.py`
- Result: passed.
- `overlay_client/.venv/bin/python -m pytest tests/test_status_table_layout.py tests/test_status_table_model.py tests/test_status_table_payloads.py tests/test_command_overlay_groups.py`
- Result: passed (`11 passed`).
- `overlay_client/.venv/bin/python -m pytest tests/test_journal_commands.py tests/test_group_status_runtime.py tests/test_group_status_enrichment.py tests/test_plugin_scan_services.py tests/test_plugin_group_resolver.py tests/test_hotkeys.py`
- Result: passed (`44 passed`).
