## Goal: Expand harness coverage for runtime wiring and EDMC hook integration surfaces

Follow persona details in `AGENTS.md`.
Document implementation results in the `Implementation Results` section.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear, capture it under `Open Questions`.

## Requirements (Initial)
- Add harness-backed tests for high-risk `load.py` integration paths currently covered only by unit/stub tests.
- Preserve existing behavior; this is a test-coverage expansion only (no feature changes).
- Keep tests deterministic/headless and isolated (no GUI window dependency for harness tests).
- Keep `load.py` minimal: new feature/business logic should be implemented in helper modules/services, with `load.py` limited to orchestration/wiring and thin delegating methods.

## Testing Strategy (Required Before Implementation)

| Change Area | Behavior / Invariant | Test Type (Unit/Harness) | Why This Level | Test File(s) | Command |
| --- | --- | --- | --- | --- | --- |
| Journal hook flow | `journal_entry -> handle_journal -> state update/publish` works for broadcast/non-broadcast and gating | Harness | Hook wiring + runtime state + publish path integration | `tests/test_harness_journal_flow.py` | `overlay_client/.venv/bin/python -m pytest tests/test_harness_journal_flow.py -q` |
| Hook forwarding contracts | `plugin_start3/plugin_stop/journal_entry/dashboard_entry` forward/no-op correctly | Harness | Global runtime singleton wiring and EDMC entrypoint behavior | `tests/test_harness_plugin_hooks_contract.py` | `overlay_client/.venv/bin/python -m pytest tests/test_harness_plugin_hooks_contract.py -q` |
| Prefs save/runtime callback wiring | `plugin_prefs` callback wiring and `prefs_changed` runtime refresh path | Harness | Cross-object callback wiring is integration-sensitive | `tests/test_harness_prefs_roundtrip.py` | `overlay_client/.venv/bin/python -m pytest tests/test_harness_prefs_roundtrip.py -q` |
| CLI ingestion integration | High-value `cli` commands route through runtime and produce expected effects | Harness | `_handle_cli_payload` touches many orchestration branches | `tests/test_harness_cli_ingestion.py` | `overlay_client/.venv/bin/python -m pytest tests/test_harness_cli_ingestion.py -q` |
| Legacy TCP ingress | `_handle_legacy_tcp_payload` normalises and publishes correctly | Harness | Ingress normalisation + publish semantics are contract-driven | `tests/test_harness_legacy_tcp_ingestion.py` | `overlay_client/.venv/bin/python -m pytest tests/test_harness_legacy_tcp_ingestion.py -q` |
| Optional helper extractions | Any new pure helper introduced for readability remains behavior-equivalent | Unit | Fast proof for local deterministic logic | `tests/test_*.py` (new as needed) | `overlay_client/.venv/bin/python -m pytest tests/<file> -q` |

## Test Scope Decision (Required)
- Unit-only? Why: No; target gaps are runtime/hook wiring contracts.
- Harness required? Why: Yes; touched behaviors depend on EDMC entrypoints, singleton plugin runtime, and callback forwarding.
- Mixed (Unit + Harness)? Why: Yes, only if small pure helpers are extracted while adding harness tests.

## Test Acceptance Gates (Required)
- [x] Unit tests added/updated for pure logic changes (N/A: no pure-logic production refactor was introduced).
- [x] Harness tests added/updated for lifecycle/wiring changes.
- [x] Exact commands listed and executed.
- [x] Any skips documented with reasons.

## Out Of Scope (This Change)
- Overlay rendering/UI visual validation (handled by manual tools and resolution scripts).
- Functional changes to command semantics, profile rules, or payload formats.

## Current Touch Points
- Code:
- [`load.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/load.py) (entrypoint/hook/runtime integration surfaces under test)
- [`tests/harness_bootstrap.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/harness_bootstrap.py) (shared fixture path as needed)
- Tests:
- [`tests/test_harness_integration.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_integration.py)
- [`tests/test_harness_chat_commands.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_chat_commands.py)
- [`tests/test_harness_dashboard_profiles.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_dashboard_profiles.py)
- [`tests/test_harness_profile_lifecycle.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_profile_lifecycle.py)
- Docs/notes:
- [`AGENTS.md`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/AGENTS.md)

## Assumptions
- `overlay_client/.venv` remains the canonical environment for local harness runs.
- Harness tests should remain safe in CI/headless environments (no visible Tk dependency).

## Risks
- Harness tests can become flaky if they rely on timing or mutable global runtime state.
- Mitigation: keep lightweight runtime stubs, reset globals in fixture teardown, avoid arbitrary sleeps.
- Coverage overlap can duplicate existing unit tests without increasing confidence.
- Mitigation: target only wiring contracts currently uncovered by existing harness suites.

## Open Questions
- Resolved 2026-03-25: CLI ingestion harness tests invoke `_handle_cli_payload` directly for deterministic contract coverage at the runtime boundary; socket-level ingestion remains a future integration candidate.
- Resolved 2026-03-25: Shared helper fixture module was added as [`tests/harness_fixtures.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/harness_fixtures.py) and adopted across new harness suites.

## Decisions (Locked)
- Prioritize harness tests for `load.py` entrypoint/wiring surfaces.
- Keep behavioral scope strictly to tests/docs; no runtime feature changes.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Define harness coverage contracts and reusable fixtures | Completed |
| 2 | Add journal/hook forwarding harness tests | Completed |
| 3 | Add prefs/CLI/legacy-ingress harness tests | Completed |
| 4 | Validation and stabilization | Completed |
| 5 | Documentation/reporting follow-up | Completed |

## Phase Details

### Phase 1: Coverage Contract And Fixture Setup
- Define precise harness invariants and shared fixture strategy for new suites.
- Risks: overbroad scope and duplicate tests.
- Mitigations: tie each new test to an uncovered integration contract.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Inventory uncovered harness contracts by `load.py` entrypoint | Completed |
| 1.2 | Define shared harness fixture helpers for new suites | Completed |
| 1.3 | Draft test-file map and command matrix | Completed |

#### Stage 1.1 Detailed Plan
- Objective:
- Produce a concrete list of uncovered runtime/hook integration behaviors.
- Primary touch points:
- [`load.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/load.py)
- Steps:
- Map `load.py` entrypoints to existing harness tests.
- Mark uncovered contracts and assign target test files.
- Acceptance criteria:
- Gap list exists with one target test owner per contract.
- Verification to run:
- `rg -n "pytest\\.mark\\.harness" tests -S`

#### Stage 1.2 Detailed Plan
- Objective:
- Consolidate fixture helpers for startup/stop + payload capture to avoid duplication.
- Steps:
- Add or refine shared fixture helpers under `tests/` as needed.
- Validate teardown resets runtime globals and mutable state.
- Acceptance criteria:
- New harness files can reuse shared fixture setup with no copy/paste boilerplate.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_integration.py -q`

#### Stage 1.3 Detailed Plan
- Objective:
- Freeze execution order and command matrix for implementation phases.
- Steps:
- Add command list per stage.
- Confirm command list is runnable in local venv.
- Acceptance criteria:
- Plan contains explicit commands for each staged addition.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest -m harness -q`

#### Phase 1 Execution Order
- Implement in strict order: `1.1` -> `1.2` -> `1.3`.

#### Phase 1 Exit Criteria
- Contracts, fixtures, and command matrix are locked.
- No unresolved blocker remains for writing new harness tests.

### Phase 2: Journal And Hook Forwarding Harness Coverage
- Add harness tests for journal state transitions and entrypoint forwarding/no-op guarantees.
- Risks: brittle assumptions about internal state fields.
- Mitigations: assert externally observable outcomes and stable runtime flags.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add harness tests for `journal_entry`/`handle_journal` state and publish path | Completed |
| 2.2 | Add harness tests for hook forwarding/no-op contracts | Completed |
| 2.3 | Harden with event-sequence fixtures and non-broadcast assertions | Completed |

#### Stage 2.1 Detailed Plan
- Objective:
- Verify runtime state and publish behavior across key journal events.
- Primary touch points:
- [`tests/config/journal_events.json`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/config/journal_events.json)
- `<new> tests/test_harness_journal_flow.py`
- Steps:
- Replay targeted events through harness.
- Assert state (`system/station/docked`) and publish counts/payloads.
- Acceptance criteria:
- Broadcast events publish payloads; non-broadcast events do not.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_journal_flow.py -q`

#### Stage 2.2 Detailed Plan
- Objective:
- Verify plugin hook functions forward only when runtime exists and no-op otherwise.
- Steps:
- Add tests for `plugin_start3`, `plugin_stop`, `journal_entry`, `dashboard_entry`.
- Assert idempotent stop and no exceptions on absent runtime.
- Acceptance criteria:
- Hook contract remains stable and explicit.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_plugin_hooks_contract.py -q`

#### Stage 2.3 Detailed Plan
- Objective:
- Prevent regressions in command-helper invocation and game/live-galaxy gating.
- Steps:
- Add event sequences covering gate-disabled and gate-enabled cases.
- Assert expected suppression vs forwarding.
- Acceptance criteria:
- Gate behavior is covered by harness assertions.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_journal_flow.py -q`

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.

#### Phase 2 Exit Criteria
- Journal and hook forwarding contracts are harness-covered.
- Existing harness suites remain green.

### Phase 3: Prefs, CLI, And Legacy Ingress Harness Coverage
- Expand harness coverage across callback wiring, CLI command ingestion, and legacy TCP normalization path.
- Risks: wide CLI command surface increases maintenance load.
- Mitigations: target high-value commands only and keep assertions contract-level.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add harness tests for `plugin_prefs`/`prefs_changed` runtime wiring | Completed |
| 3.2 | Add harness tests for high-value `_handle_cli_payload` command families | Completed |
| 3.3 | Add harness tests for `_handle_legacy_tcp_payload` normalization+publish | Completed |

#### Stage 3.1 Detailed Plan
- Objective:
- Verify prefs panel callbacks and save hook propagate runtime updates.
- Steps:
- Build prefs panel in harness context.
- Simulate save flow and assert runtime callbacks fired.
- Acceptance criteria:
- Callback wiring and update propagation are harness-proven.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_prefs_roundtrip.py -q`

#### Stage 3.2 Detailed Plan
- Objective:
- Cover representative CLI commands across profile/group/control payload routes.
- Steps:
- Add harness ingestion tests for: `plugin_group_status`, `profile_*`, `legacy_overlay`, `controller_active_group`.
- Assert response payload shape and side effects.
- Acceptance criteria:
- Critical CLI integration contracts are covered.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_cli_ingestion.py -q`

#### Stage 3.3 Detailed Plan
- Objective:
- Validate legacy TCP ingress normalization and publish behavior.
- Steps:
- Feed raw legacy payloads into `_handle_legacy_tcp_payload`.
- Assert normalization failures drop safely; valid payloads publish correctly.
- Acceptance criteria:
- Legacy ingress path has explicit harness contract tests.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_legacy_tcp_ingestion.py -q`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3`.

#### Phase 3 Exit Criteria
- Prefs/CLI/legacy ingress harness gaps are closed.
- No new flaky tests introduced.

### Phase 4: Validation And Stabilization
- Run targeted and aggregate harness suites; eliminate flakiness and redundant assertions.
- Risks: hidden ordering dependencies between harness suites.
- Mitigations: independent fixtures, explicit teardown, focused assertions.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Run targeted suites for each new harness file | Completed |
| 4.2 | Run aggregate harness marker suite and touched unit suites | Completed |
| 4.3 | De-flake/trim assertions and finalize stable command list | Completed |

#### Stage 4.1 Detailed Plan
- Objective:
- Confirm each new suite passes independently.
- Steps:
- Run each new harness file directly.
- Record failures/skips and patch quickly.
- Acceptance criteria:
- Each new harness file passes standalone.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_*.py -q`

#### Stage 4.2 Detailed Plan
- Objective:
- Confirm total harness suite compatibility.
- Steps:
- Run `-m harness`.
- Run adjacent touched unit tests if helpers were extracted.
- Acceptance criteria:
- Full harness marker set passes.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest -m harness -q`

#### Stage 4.3 Detailed Plan
- Objective:
- Stabilize test runtime and remove redundant checks.
- Steps:
- Remove duplicate assertions and noisy brittle internals.
- Keep contract-level assertions only.
- Acceptance criteria:
- Stable pass rate across repeated runs.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest -m harness -q`

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- Harness suite is stable and deterministic.
- Validation commands and outcomes are captured.

### Phase 5: Documentation And Follow-Up
- Document new harness scope and note next potential gaps.
- Risks: drift between docs and actual coverage.
- Mitigations: tie docs to concrete file paths and commands.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Update test docs with new harness files/commands | Completed |
| 5.2 | Record residual risk list and next candidates | Completed |
| 5.3 | Final implementation summary and evidence table | Completed |

#### Stage 5.1 Detailed Plan
- Objective:
- Keep docs aligned with new harness coverage.
- Steps:
- Update `docs/testing.md` harness section with new files and commands.
- Acceptance criteria:
- Reader can run all harness suites from docs.
- Verification to run:
- `rg -n "harness" docs/testing.md -S`

#### Stage 5.2 Detailed Plan
- Objective:
- Preserve forward-looking gap list after this plan.
- Steps:
- Add short residual list (if any) in Implementation Results.
- Acceptance criteria:
- Remaining known gaps are explicit and scoped.
- Verification to run:
- `rg -n "Residual|gap|follow-up" docs/plans/harness-coverage-expansion.md -S`

#### Stage 5.3 Detailed Plan
- Objective:
- Produce final completion record with commands/results.
- Steps:
- Fill Execution Summary + Tests Run sections for each phase.
- Acceptance criteria:
- Final report contains exact commands and outcomes.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest -m harness -q`

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
- Docs and execution evidence are complete.
- Plan is ready for closure.

## Test Plan (Per Iteration)
- Env setup (once per machine):
- `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- Headless quick pass:
- `source .venv/bin/activate && python -m pytest`
- Targeted tests:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_*.py -q`
- Milestone checks:
- `make check`
- `make test`
- Compliance baseline check (release/compliance work):
- `python scripts/check_edmc_python.py`

## Implementation Results
- Plan implemented on 2026-03-25.
- New shared harness fixture module added:
  - [`tests/harness_fixtures.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/harness_fixtures.py)
- New harness suites added:
  - [`tests/test_harness_journal_flow.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_journal_flow.py)
  - [`tests/test_harness_plugin_hooks_contract.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_plugin_hooks_contract.py)
  - [`tests/test_harness_prefs_roundtrip.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_prefs_roundtrip.py)
  - [`tests/test_harness_cli_ingestion.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_cli_ingestion.py)
  - [`tests/test_harness_legacy_tcp_ingestion.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_legacy_tcp_ingestion.py)

### Phase 1 Execution Summary
- Stage 1.1:
  - Mapped uncovered `load.py` integration contracts against existing harness suites and assigned target files for each contract family.
- Stage 1.2:
  - Implemented shared fixture/runtime helper module in [`tests/harness_fixtures.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/harness_fixtures.py).
- Stage 1.3:
  - Locked per-suite command matrix in this plan and used it for execution.

### Tests Run For Phase 1
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_integration.py -q`
- `overlay_client/.venv/bin/python -m pytest -m harness -q`

### Phase 2 Execution Summary
- Stage 2.1:
  - Added journal flow harness coverage for broadcast/non-broadcast behavior, state updates, and publish calls in [`tests/test_harness_journal_flow.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_journal_flow.py).
- Stage 2.2:
  - Added hook forwarding/no-op contract checks for `journal_entry`, `dashboard_entry`, and `plugin_stop` in [`tests/test_harness_plugin_hooks_contract.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_plugin_hooks_contract.py).
- Stage 2.3:
  - Added explicit gating assertions for `_game_running` and `_is_live_galaxy` suppression paths in journal harness tests.

### Tests Run For Phase 2
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_journal_flow.py -q`
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_plugin_hooks_contract.py -q`

### Phase 3 Execution Summary
- Stage 3.1:
  - Added prefs callback/save propagation harness coverage in [`tests/test_harness_prefs_roundtrip.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_prefs_roundtrip.py).
- Stage 3.2:
  - Added CLI ingestion harness tests for `profile_*`, `legacy_overlay`, `plugin_group_status`, and `controller_active_group` in [`tests/test_harness_cli_ingestion.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_cli_ingestion.py).
- Stage 3.3:
  - Added legacy TCP normalization/publish harness tests in [`tests/test_harness_legacy_tcp_ingestion.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_legacy_tcp_ingestion.py).

### Tests Run For Phase 3
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_prefs_roundtrip.py -q`
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_cli_ingestion.py -q`
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_legacy_tcp_ingestion.py -q`

### Phase 4 Execution Summary
- Stage 4.1:
  - Ran all new harness files together; no failures.
- Stage 4.2:
  - Ran aggregate harness marker suite; no regressions.
- Stage 4.3:
  - Kept assertions at contract level and reused deterministic runtime stubs; no timing-based sleeps introduced.

### Tests Run For Phase 4
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_journal_flow.py tests/test_harness_plugin_hooks_contract.py tests/test_harness_prefs_roundtrip.py tests/test_harness_cli_ingestion.py tests/test_harness_legacy_tcp_ingestion.py -q`
  - Result: `14 passed in 0.77s`
- `overlay_client/.venv/bin/python -m pytest -m harness -q`
  - Result: `24 passed, 6 skipped, 669 deselected in 1.51s`

### Phase 5 Execution Summary
- Stage 5.1:
  - Updated [`docs/testing.md`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/docs/testing.md) with all new harness suites/commands.
- Stage 5.2:
  - Residual risk list recorded below.
- Stage 5.3:
  - Finalized this execution summary with exact commands and observed outcomes.

### Tests Run For Phase 5
- `rg -n "Harness (journal flow|plugin hook contracts|prefs round-trip|CLI ingestion|legacy TCP ingestion)" docs/testing.md -S`
- `overlay_client/.venv/bin/python -m pytest -m harness -q`

### Residual Risks / Follow-Up Candidates
- Socket-level CLI ingress coverage is still limited; current tests target runtime handler boundary directly.
- Full EDMC GUI-thread interaction is outside this harness scope and remains covered by existing integration/manual validation flows.
