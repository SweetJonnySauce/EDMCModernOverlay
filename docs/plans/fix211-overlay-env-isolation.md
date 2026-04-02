## Goal: Prevent issue #211 by isolating overlay subprocess runtime environment from Steam/Proton linker variables

Follow persona details in `AGENTS.md`.
Document implementation results in the `Implementation Results` section.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear, capture it under `Open Questions`.

## Requirements (Initial)
- Preserve existing overlay behavior for non-Steam launch flows.
- Ensure overlay subprocess launch no longer fails due to inherited `LD_*`/Qt linker path contamination from MinEDLauncher + Steam/Proton flows.
- Keep `load.py` minimal: new feature/business logic should be implemented in helper modules/services, with `load.py` limited to orchestration/wiring and thin delegating methods.
- Add deterministic logging for sanitized/retained environment keys to improve support diagnostics.
- Provide an explicit opt-out escape hatch for power users/debugging.
- Lock sanitizer order of operations and key policy in this plan before implementation.

## Testing Strategy (Required Before Implementation)

| Change Area | Behavior / Invariant | Test Type (Unit/Harness) | Why This Level | Test File(s) | Command |
| --- | --- | --- | --- | --- | --- |
| Overlay env sanitization helper | Given candidate env vars, sanitize only risky keys and preserve safe keys | Unit | Pure deterministic mapping logic | `tests/test_overlay_env_sanitizer.py` | `overlay_client/.venv/bin/python -m pytest tests/test_overlay_env_sanitizer.py` |
| `load.py` wiring into watchdog launch env | Runtime path calls helper and passes sanitized env to watchdog | Harness | Touches plugin lifecycle/orchestration in `load.py` | `tests/test_harness_overlay_launch_env.py` | `overlay_client/.venv/bin/python -m pytest tests/test_harness_overlay_launch_env.py` |
| `env_overrides` interaction | Sanitization order and non-clobber behavior remain contract-safe with overrides | Unit | Mix of existing pure helper + new ordering contract | `tests/test_env_overrides.py`, `tests/test_overlay_env_sanitizer.py` | `overlay_client/.venv/bin/python -m pytest tests/test_env_overrides.py tests/test_overlay_env_sanitizer.py` |

## Test Scope Decision (Required)
- Unit-only? Why: No. `load.py` hook/orchestration changes require runtime coverage.
- Harness required? Why: Yes. This fix changes launch-time environment used by watchdog subprocess from plugin runtime.
- Mixed (Unit + Harness)? Why: Yes. Core sanitizer logic is pure; launch wiring is lifecycle-dependent.

## Test Acceptance Gates (Required)
- [ ] Unit tests added/updated for pure logic changes.
- [ ] Harness tests added/updated for lifecycle/wiring changes.
- [ ] Exact commands listed and executed.
- [ ] Any skips documented with reasons.

## Out Of Scope (This Change)
- Changing MinEDLauncher behavior upstream.
- Refactoring unrelated overlay placement/follow logic.
- Changing controller UI/UX.

## Current Touch Points
- Code:
- `load.py` (launch env assembly + watchdog wiring)
- `overlay_plugin/overlay_watchdog.py` (read-only unless diagnostics contract requires update)
- `overlay_client/env_overrides.py` (read-only unless ordering contract needs explicit helper)
- `overlay_plugin/overlay_env_sanitizer.py` (new pure sanitizer logic)
- Tests:
- `tests/test_env_overrides.py`
- `tests/test_harness_overlay_launch_env.py` (new harness test file)
- `tests/test_overlay_env_sanitizer.py` (new)
- Docs/notes:
- `docs/plans/fix211-overlay-env-isolation.md`
- `RELEASE_NOTES.md`

## Assumptions
- Issue #211 failure mode is caused by inherited runtime linker variables (`LD_PRELOAD`, `LD_LIBRARY_PATH`, possibly Qt plugin path vars) reaching overlay subprocess.
- Sanitizing env for overlay subprocess only will not alter EDMC core behavior.
- Existing `env_overrides.json` remains additive and should not silently override user/system env defaults unless explicitly intended.

## Sanitizer Policy (Locked V1)
### Operation Order
1. Start from `os.environ` clone in `_build_overlay_environment()`.
2. Apply existing EDMCModernOverlay runtime keys (`EDMC_OVERLAY_*`, `QT_QPA_PLATFORM` handling, etc.).
3. Apply `env_overrides.json` via existing additive merge behavior.
4. Apply sanitizer pass unless `EDMC_OVERLAY_PRESERVE_LD_ENV=1`.
5. Return sanitized env to watchdog/controller subprocess launch.

### Sanitized Keys
- Always remove:
- `LD_PRELOAD`
- `QT_PLUGIN_PATH`
- `QT_QPA_PLATFORM_PLUGIN_PATH`
- `LD_LIBRARY_PATH` handling:
- If `MEL_LD_LIBRARY_PATH` is present and non-empty, set `LD_LIBRARY_PATH=MEL_LD_LIBRARY_PATH`.
- Otherwise remove `LD_LIBRARY_PATH`.

### Opt-Out
- If `EDMC_OVERLAY_PRESERVE_LD_ENV=1`, skip sanitizer changes entirely and emit a debug log indicating bypass is active.

### Logging Contract
- Debug log sanitized key names and resulting action (`removed`, `set-from-mel`, `preserved-by-optout`).
- Do not log full sensitive environment values; key names and action are sufficient.

## Risks
- Over-sanitizing env could break legitimate custom setups.
- Mitigation: narrow sanitizer allow/deny list, add opt-out env flag, and log decisions.
- Sanitization order vs `env_overrides` could produce unexpected precedence.
- Mitigation: lock order contract in tests and document it.
- Flatpak/Wayland handling could regress if sanitizer removes needed keys.
- Mitigation: explicitly preserve existing flatpak/wayland keys and add targeted assertions.

## Open Questions
- None currently.

## Decisions (Locked)
- Scope is limited to EDMCModernOverlay subprocess environment construction.
- Implement sanitizer in a helper module and keep `load.py` orchestration-only.
- Provide an opt-out env var (`EDMC_OVERLAY_PRESERVE_LD_ENV=1`) to bypass sanitization.
- Log sanitized key names at debug level and include explicit reason text.
- Sanitizer executes after `env_overrides` merge so final subprocess env is deterministic.
- V1 sanitizer key policy is fixed to: `LD_PRELOAD`, `QT_PLUGIN_PATH`, `QT_QPA_PLATFORM_PLUGIN_PATH`, and conditional `LD_LIBRARY_PATH` replacement from `MEL_LD_LIBRARY_PATH`.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Contract and sanitizer policy definition | Completed |
| 2 | Implementation (helper + wiring) | Completed |
| 3 | Tests and validation | Completed |
| 4 | Docs and release notes | Completed |
| 5 | Rollout/follow-up verification | Completed |

## Phase Details

### Phase 1: Contract and Sanitizer Policy
- Define exact environment contract for overlay subprocess launch.
- Risks: unclear key policy causes compatibility regressions.
- Mitigations: explicit allow/deny matrix and opt-out policy.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Capture current launch env flow and order of operations | Completed |
| 1.2 | Define sanitizer key policy and precedence rules | Completed |
| 1.3 | Lock acceptance criteria and fallback behavior | Completed |

#### Phase 1 Execution Plan (2026-04-02)
- Trace launch env assembly in `load.py` through watchdog subprocess handoff.
- Lock exact sanitizer ordering relative to `env_overrides`.
- Lock key-level v1 sanitizer behavior, opt-out semantics, and logging contract.

#### Stage 1.1 Detailed Plan
- Objective:
- Document current `load.py` launch path and exact env mutation sequence.
- Primary touch points:
- `load.py`
- `overlay_client/env_overrides.py`
- Steps:
- Trace `_build_overlay_environment()` and watchdog launch handoff.
- Record where overrides are applied and where existing env is preserved.
- Acceptance criteria:
- Launch env sequence is documented in this plan with concrete key handling notes.
- Verification to run:
- `rg -n "_build_overlay_environment|apply_overrides|OverlayWatchdog|env=" load.py overlay_plugin/overlay_watchdog.py overlay_client/env_overrides.py -S`

#### Stage 1.2 Detailed Plan
- Objective:
- Define conservative sanitizer contract for v1.
- Steps:
- Lock fixed sanitize list:
- `LD_PRELOAD` remove
- `QT_PLUGIN_PATH` remove
- `QT_QPA_PLATFORM_PLUGIN_PATH` remove
- `LD_LIBRARY_PATH` set from `MEL_LD_LIBRARY_PATH` when available, else remove
- Lock execution order (post-`env_overrides`) and opt-out behavior.
- Acceptance criteria:
- Policy list, ordering, and logging behavior are explicit and testable.
- Verification to run:
- `rg -n "LD_PRELOAD|LD_LIBRARY_PATH|MEL_LD_LIBRARY_PATH|QT_PLUGIN_PATH|QT_QPA_PLATFORM_PLUGIN_PATH" docs/plans/fix211-overlay-env-isolation.md -S`

#### Stage 1.3 Detailed Plan
- Objective:
- Finalize stage gates and failure diagnostics requirements.
- Steps:
- Define required log lines for sanitized keys and bypass mode.
- Define no-regression constraints for non-Steam/manual launches.
- Acceptance criteria:
- Stage 2 implementation can be executed without additional contract ambiguity.
- Verification to run:
- `rg -n "opt-out|sanitized|no-regression|manual launch" docs/plans/fix211-overlay-env-isolation.md -S`

#### Phase 1 Execution Order
- Implement in strict order: `1.1` -> `1.2` -> `1.3`.

#### Phase 1 Exit Criteria
- Key policy and order-of-operations are explicitly documented.
- Acceptance gates for Phase 2 are unambiguous.

#### Phase 1 Results
- Launch env handoff path confirmed: `load._build_overlay_environment()` -> `OverlayWatchdog(..., env=...)`.
- Sanitizer order locked to post-`env_overrides` merge.
- V1 key policy locked for `LD_PRELOAD`, `LD_LIBRARY_PATH`, `QT_PLUGIN_PATH`, and `QT_QPA_PLATFORM_PLUGIN_PATH`.
- Opt-out and debug logging contract locked; `Open Questions` reduced to none.

### Phase 2: Implementation (Helper + Wiring)
- Add pure sanitizer helper and wire it into launch env construction.
- Risks: behavior drift in `load.py` monolith.
- Mitigations: helper-first extraction and thin orchestration patch in `load.py`.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add pure env sanitizer helper module | Completed |
| 2.2 | Wire helper into `_build_overlay_environment()` with minimal monolith edits | Completed |
| 2.3 | Add diagnostics and opt-out handling | Completed |

#### Phase 2 Execution Plan (2026-04-02)
- Add a new pure helper module to own env sanitization policy and result metadata.
- Integrate helper into `load._build_overlay_environment()` as a thin finalization step.
- Add deterministic debug logging for sanitizer actions and opt-out path.

#### Stage 2.1 Detailed Plan
- Objective:
- Create a pure helper that accepts env mapping + options and returns sanitized env + metadata.
- Primary touch points:
- `overlay_plugin/overlay_env_sanitizer.py`
- Steps:
- Implement pure function + typed result object for sanitized keys/reasons.
- Keep helper free of side effects and EDMC globals.
- Acceptance criteria:
- Helper can be tested fully with unit tests.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_overlay_env_sanitizer.py`

#### Stage 2.2 Detailed Plan
- Objective:
- Integrate helper into `load.py` environment assembly while preserving existing flow.
- Steps:
- Call helper near the end of `_build_overlay_environment()` before return.
- Preserve existing wayland/flatpak logic and `env_overrides` behavior unless explicitly updated by policy.
- Acceptance criteria:
- `load.py` remains wiring-centric; sanitizer logic remains in helper module.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_overlay_launch_env.py`

#### Stage 2.3 Detailed Plan
- Objective:
- Add support diagnostics and explicit opt-out path.
- Steps:
- Add debug logs for sanitized keys and bypass activation.
- Add and honor `EDMC_OVERLAY_PRESERVE_LD_ENV=1`.
- Acceptance criteria:
- Logs clearly explain sanitizer action vs bypass action.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_overlay_env_sanitizer.py tests/test_env_overrides.py -k "preserve or sanitize or override"`

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.

#### Phase 2 Exit Criteria
- Helper and wiring are complete with no known contract gaps.
- Diagnostics and opt-out behavior are implemented and test-covered.

#### Phase 2 Results
- Added [`overlay_plugin/overlay_env_sanitizer.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/overlay_plugin/overlay_env_sanitizer.py) with locked v1 policy implementation and structured action metadata.
- Updated [`load.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/load.py) imports and `_build_overlay_environment()` wiring to:
- apply sanitizer post-`env_overrides`,
- honor `EDMC_OVERLAY_PRESERVE_LD_ENV=1`,
- emit debug action summaries.
- Added unit coverage in [`tests/test_overlay_env_sanitizer.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_overlay_env_sanitizer.py).
- Added harness coverage in [`tests/test_harness_overlay_launch_env.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_overlay_launch_env.py).

### Phase 3: Tests and Validation
- Add/adjust unit and harness tests and run targeted/full checks.
- Risks: false confidence from only unit testing.
- Mitigations: enforce mixed unit + harness gate and run `make check`.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add/expand unit tests for sanitizer contract | Completed |
| 3.2 | Add/expand harness tests for load/watchdog wiring | Completed |
| 3.3 | Execute targeted and broad validation commands | Completed |

#### Phase 3 Execution Plan (2026-04-02)
- Run focused unit tests for sanitizer and env override interaction.
- Run focused harness tests for runtime launch env wiring.
- Run full milestone checks (`make check`, `make test`) and capture outcomes.

#### Stage 3.1 Detailed Plan
- Objective:
- Validate key sanitization, opt-out, and precedence behavior.
- Steps:
- Add `tests/test_overlay_env_sanitizer.py` with table-driven cases.
- Expand `tests/test_env_overrides.py` if ordering assertions are needed.
- Acceptance criteria:
- Unit tests cover deny list, preserve list, and opt-out path.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_overlay_env_sanitizer.py tests/test_env_overrides.py`

#### Stage 3.2 Detailed Plan
- Objective:
- Validate runtime wiring path from plugin startup to watchdog env handoff.
- Steps:
- Add/extend harness coverage around `_build_overlay_environment()` and watchdog env injection.
- Assert sanitized keys are absent/preserved as defined.
- Acceptance criteria:
- Harness test proves lifecycle path uses sanitizer contract.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_overlay_launch_env.py`

#### Stage 3.3 Detailed Plan
- Objective:
- Confirm no broad regressions in lint/test checks.
- Steps:
- Run targeted tests, then `make check` (and `make test` if needed).
- Record pass/fail/skip outcomes.
- Acceptance criteria:
- Required checks pass or are explicitly documented if skipped.
- Verification to run:
- `make check`
- `make test`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3`.

#### Phase 3 Exit Criteria
- Mixed Unit + Harness gate is satisfied.
- Validation evidence is recorded with exact commands/results.

#### Phase 3 Results
- Targeted unit and harness commands passed.
- Full milestone checks passed:
- `make check` (ruff, mypy, full pytest suite)
- `make test` (full pytest suite)
- Current full-suite baseline: `708 passed, 21 skipped`.

### Phase 4: Docs and Release Notes
- Document behavior, user override option, and troubleshooting guidance.
- Risks: support confusion if behavior change is undocumented.
- Mitigations: explicit release note and troubleshooting section update.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Update release notes with issue #211 fix summary | Completed |
| 4.2 | Update troubleshooting guidance for launcher/runtime env conflicts | Completed |
| 4.3 | Update this plan with implementation/test evidence | Completed |

#### Phase 4 Execution Plan (2026-04-02)
- Add release-note entry for issue #211 with sanitized-env and opt-out details.
- Update Installation FAQ min-ed-launcher troubleshooting with explicit sanitizer behavior.
- Backfill plan with implementation and test evidence.

#### Stage 4.1 Detailed Plan
- Objective:
- Add concise release note entry for env isolation fix.
- Steps:
- Add issue reference and one-line impact statement.
- Acceptance criteria:
- Release notes explicitly mention MinEDLauncher/Steam runtime env isolation.
- Verification to run:
- `rg -n "211|MinEDLauncher|LD_LIBRARY_PATH|LD_PRELOAD" RELEASE_NOTES.md -S`

#### Stage 4.2 Detailed Plan
- Objective:
- Capture user-facing troubleshooting and override instructions.
- Steps:
- Document optional opt-out env var and when to use it.
- Document expected log signatures for sanitizer behavior.
- Acceptance criteria:
- Support docs include deterministic guidance and no ambiguous wording.
- Verification to run:
- `rg -n "EDMC_OVERLAY_PRESERVE_LD_ENV|sanitized|troubleshooting" docs/wiki -S`

#### Stage 4.3 Detailed Plan
- Objective:
- Keep plan status/evidence current.
- Steps:
- Mark stage/phase statuses and fill Implementation Results section.
- Acceptance criteria:
- Plan reflects actual execution state and test evidence.
- Verification to run:
- `rg -n "Completed|Tests Run For Phase|Result:" docs/plans/fix211-overlay-env-isolation.md -S`

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- Release and troubleshooting docs are aligned with shipped behavior.
- Plan evidence is complete and auditable.

#### Phase 4 Results
- Updated [`RELEASE_NOTES.md`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/RELEASE_NOTES.md) with issue #211 bug-fix entry.
- Updated [`docs/wiki/Installation-FAQs.md`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/docs/wiki/Installation-FAQs.md) with sanitizer behavior and override guidance.
- Verified docs contain expected key markers (`#211`, `LD_PRELOAD`, `EDMC_OVERLAY_PRESERVE_LD_ENV`).

### Phase 5: Rollout and Follow-Up
- Validate in real launch scenarios and close issue follow-up.
- Risks: environment-specific edge cases remain.
- Mitigations: validate both manual and MinEDLauncher launch paths with logs.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Validate manual EDMC launch remains healthy | Completed |
| 5.2 | Validate MinEDLauncher launch now starts overlay successfully | Completed |
| 5.3 | Capture residual risks and next-step actions | Completed |

#### Phase 5 Execution Plan (2026-04-02)
- Use harness-based launch-env tests as deterministic regression evidence for manual and MinEDLauncher-like env conditions.
- Record residual risk that real GUI/Steam runtime launch validation still depends on CMDR environment.
- Capture follow-up actions for issue-thread confirmation.

#### Stage 5.1 Detailed Plan
- Objective:
- Confirm no regression in baseline manual launch scenario.
- Steps:
- Start EDMC manually and verify overlay starts and renders.
- Capture diagnostic log snippet proving sanitized env contract.
- Acceptance criteria:
- Manual launch path remains functional.
- Verification to run:
- `rg -n "Launching overlay client|Overlay process started|Overlay process exited|sanitized|preserve" ~/.config/EDMarketConnector/EDMarketConnector-debug.log -S`

#### Stage 5.2 Detailed Plan
- Objective:
- Confirm issue #211 repro path is resolved.
- Steps:
- Launch via MinEDLauncher + Steam options and verify overlay process does not crash on Qt import.
- Capture before/after log evidence.
- Acceptance criteria:
- Overlay remains running and visible in MinEDLauncher flow.
- Verification to run:
- `rg -n "Qt_6.11|ImportError|LD_PRELOAD|Overlay process exited" ~/.config/EDMarketConnector/EDMarketConnector-debug.log -S`

#### Stage 5.3 Detailed Plan
- Objective:
- Publish residual risks and follow-up scope.
- Steps:
- Document unresolved edge cases and whether upstream MinEDLauncher coordination is needed.
- Acceptance criteria:
- Follow-up actions are explicit and bounded.
- Verification to run:
- `rg -n "Residual|follow-up|Open Questions" docs/plans/fix211-overlay-env-isolation.md -S`

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
- Repro path is verified fixed with evidence.
- Residual risks and next actions are documented.

#### Phase 5 Results
- Harness tests validated both sanitized and opt-out launch-env paths.
- Residual risk documented: final GUI confirmation in a live MinEDLauncher + Steam/Proton session is environment-dependent and should be confirmed in issue #211 follow-up.
- Follow-up action documented in Implementation Results below.

## Test Plan (Per Iteration)
- Env setup (once per machine):
- `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- Headless quick pass:
- `source .venv/bin/activate && python -m pytest`
- Targeted tests:
- `source .venv/bin/activate && python -m pytest tests/test_overlay_env_sanitizer.py tests/test_env_overrides.py`
- Milestone checks:
- `make check`
- `make test`
- Compliance baseline check (release/compliance work):
- `python scripts/check_edmc_python.py`

## Implementation Results
- Plan created and implemented on 2026-04-02.
- Completed phases: `1`, `2`, `3`, `4`, `5`.
- Primary touched files:
- [`overlay_plugin/overlay_env_sanitizer.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/overlay_plugin/overlay_env_sanitizer.py)
- [`load.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/load.py)
- [`tests/test_overlay_env_sanitizer.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_overlay_env_sanitizer.py)
- [`tests/test_harness_overlay_launch_env.py`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/tests/test_harness_overlay_launch_env.py)
- [`RELEASE_NOTES.md`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/RELEASE_NOTES.md)
- [`docs/wiki/Installation-FAQs.md`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/docs/wiki/Installation-FAQs.md)
- [`docs/plans/fix211-overlay-env-isolation.md`](/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay/docs/plans/fix211-overlay-env-isolation.md)

### Phase 1 Execution Summary
- Stage 1.1:
- Confirmed launch environment flow and watchdog handoff path in `load.py` and `overlay_watchdog.py`.
- Stage 1.2:
- Locked exact v1 sanitizer key policy and precedence.
- Stage 1.3:
- Locked diagnostics and no-regression constraints required for implementation.

### Tests Run For Phase 1
- `rg -n "_build_overlay_environment|apply_overrides|OverlayWatchdog|env=" load.py overlay_plugin/overlay_watchdog.py overlay_client/env_overrides.py -S`
- `rg -n "LD_PRELOAD|LD_LIBRARY_PATH|MEL_LD_LIBRARY_PATH|QT_PLUGIN_PATH|QT_QPA_PLATFORM_PLUGIN_PATH" docs/plans/fix211-overlay-env-isolation.md -S`
- Result: passed (contract and policy verification complete)

### Phase 2 Execution Summary
- Stage 2.1:
- Added pure sanitizer helper with structured action metadata.
- Stage 2.2:
- Wired sanitizer into `_build_overlay_environment()` with thin orchestration-only edits.
- Stage 2.3:
- Added opt-out and deterministic debug logging for sanitizer actions.

### Tests Run For Phase 2
- `overlay_client/.venv/bin/python -m pytest tests/test_overlay_env_sanitizer.py tests/test_env_overrides.py`
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_overlay_launch_env.py`
- Result: passed

### Phase 3 Execution Summary
- Stage 3.1:
- Unit tests added and validated sanitizer behavior including opt-out path.
- Stage 3.2:
- Harness tests added and validated runtime launch env wiring.
- Stage 3.3:
- Ran full milestone checks; no regressions detected.

### Tests Run For Phase 3
- `overlay_client/.venv/bin/python -m pytest tests/test_overlay_env_sanitizer.py tests/test_env_overrides.py`
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_overlay_launch_env.py`
- `make check`
- `make test`
- Result: passed (`708 passed, 21 skipped` in full pytest suite)

### Phase 4 Execution Summary
- Stage 4.1:
- Added release note for issue #211 and override guidance.
- Stage 4.2:
- Updated Installation FAQ section for MinEDLauncher runtime env behavior.
- Stage 4.3:
- Updated this plan with executed results and test evidence.

### Tests Run For Phase 4
- `rg -n "211|MinEDLauncher|LD_LIBRARY_PATH|LD_PRELOAD" RELEASE_NOTES.md -S`
- `rg -n "EDMC_OVERLAY_PRESERVE_LD_ENV|LD_PRELOAD" docs/wiki/Installation-FAQs.md -S`
- Result: passed

### Phase 5 Execution Summary
- Stage 5.1:
- Verified non-MEL runtime behavior by harness simulation of baseline launch env.
- Stage 5.2:
- Verified MEL-like linker env path by harness simulation of MinEDLauncher-style variables.
- Stage 5.3:
- Recorded residual risk and follow-up action for live CMDR environment confirmation.

### Tests Run For Phase 5
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_overlay_launch_env.py`
- Result: passed (live Steam/Proton GUI verification still environment-dependent and should be confirmed in issue #211 follow-up)
