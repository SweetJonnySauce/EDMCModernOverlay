## Goal: Register Modern Overlay actions with EDMC-Hotkeys

Follow persona details in `AGENTS.md`.
Document implementation results in the Implementation Results section.
After each stage is complete, change stage status to Completed.
When all stages in a phase are complete, change phase status to Completed.
If something is not clear, ask clarifying questions.

## Requirements (Reviewed)
- EDMCModernOverlay will register actions with `EDMC-Hotkeys`.
- Register two actions:
- `overlay on`: if current opacity is `0`, restore previous visible opacity; if current opacity is already `>0`, no-op.
- `overlay off`: if current opacity is `>0`, set opacity to `0`; if current opacity is already `0`, no-op.
- Reuse the existing in-game chat-command behavior and logic; do not duplicate toggle/opacity rules in a separate path.
- Keep action callbacks safe for UI/main-thread expectations (`thread_policy="main"`).
- Use retry with exponential backoff and a max-attempt cap when EDMC-Hotkeys import fails.
- Retry policy: 5 retries, each with a longer wait than the previous attempt (exponential backoff).
- Retry applies to EDMC-Hotkeys import failures and `register_action == false` responses.
- Retry does not apply to registration exceptions or action-build/API-shape failures.
- Action labels shown to users should be human-readable: `Overlay On` and `Overlay Off`.

## Current Reuse Surface
- Existing chat command path already routes to runtime methods:
- `set_payload_opacity_preference(value: int)` in `load.py`
- `toggle_payload_opacity_preference()` in `load.py`
- Toggle storage/restore behavior already lives in:
- `toggle_payload_opacity(preferences)` in `overlay_plugin/toggle_helpers.py`
- Journal command wiring already delegates to the above runtime methods in:
- `build_command_helper(...)` in `overlay_plugin/journal_commands.py`

## Design Approach
- Add hotkeys registration to plugin runtime lifecycle (start/stop), not module-global hook code.
- Use dynamic imports (`importlib`) for EDMC-Hotkeys APIs so Modern Overlay remains optional-compatible when the hotkeys plugin is not installed.
- Keep hotkey callbacks thin: they should delegate to existing runtime opacity/toggle methods.
- Add a small runtime helper for explicit on/off semantics so callbacks and any future callers share one behavior.

## Open Questions
- Resolved: `overlay on` is a no-op when current opacity is already `>0`.
- Resolved: `overlay off` is a no-op when current opacity is already `0`.
- Resolved: add exponential-backoff retry when importing EDMC-Hotkeys fails.
- Resolved: retry path includes import failures plus `register_action == false`.
- Resolved: action labels are `Overlay On` and `Overlay Off`.
- Resolved: retry will perform 5 attempts with progressively longer waits (exponential backoff).
- Remaining: none.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Define behavior contract and hotkeys lifecycle integration points | Completed |
| 2 | Implement hotkeys registration + callback wiring via existing runtime logic | Completed |
| 2A | Phase 2 addendum: extract hotkeys implementation into `overlay_plugin/hotkeys.py` with lightweight `load.py` tie-ins | Completed |
| 3 | Add tests for registration, fallback, and callback behavior (moduleized `hotkeys.py`) | Completed |
| 4 | Verify test runs and document implementation outcomes | Completed |
| 5 | Expand retry scope to include `register_action == false` registration retries | Completed |

## Phase Details

### Phase 1: Behavior contract + integration seams
- Confirm explicit on/off behavior and fallback expectations when EDMC-Hotkeys is unavailable.
- Lock in where registration/unregistration occurs in runtime lifecycle (`start`/`stop`).
- Keep behavior unchanged for existing journal/chat command flows.
- Risks: retry cadence too aggressive (log spam/startup overhead) or too weak (misses late plugin availability).
- Mitigations: settle behavior before implementation and encode as tests.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Resolve `overlay on/off` no-op semantics at current-state boundaries | Completed |
| 1.2 | Finalize registration lifecycle contract (retry on import failure; stop-time cleanup) | Completed |
| 1.3 | Finalize retry parameter values for exponential backoff + max attempts | Completed |

#### Stage 1.1 Detailed Plan (#1): `overlay on/off` no-op semantics
- Objective: implement deterministic hotkey behavior that matches the agreed boundary rules without changing existing chat-command behavior.
- Primary touchpoints:
- `load.py`: hotkey callback methods and small internal helpers for explicit on/off actions.
- `overlay_plugin/toggle_helpers.py`: existing last-on restore/off logic (reuse as-is, no new toggle math).
- `load.py` existing methods: `toggle_payload_opacity_preference()` and `set_payload_opacity_preference()` (reuse entry points; avoid duplicate persistence/config logic).
- Behavior contract:
- `overlay on` when current opacity is `0`: restore previous visible opacity through existing toggle path.
- `overlay on` when current opacity is `>0`: no-op (no state write, no config push).
- `overlay off` when current opacity is `>0`: switch to `0` through existing toggle path so last-on value is preserved.
- `overlay off` when current opacity is `0`: no-op (no state write, no config push).
- Implementation steps:
- Add a tiny internal helper to read current opacity from preferences under `_prefs_lock`.
- Add `_hotkey_overlay_on(...)` callback:
- if current opacity is `0`, call `toggle_payload_opacity_preference()`;
- else return without mutation.
- Add `_hotkey_overlay_off(...)` callback:
- if current opacity is `>0`, call `toggle_payload_opacity_preference()`;
- else return without mutation.
- Keep callbacks main-thread safe and exception-guarded with runtime logging.
- Invariants to preserve:
- No duplicate opacity/toggle math outside existing helper path.
- No behavior change to journal/chat command handling.
- Last-on restore remains driven by existing preferences fields and helper coercion.
- Observability:
- Add concise debug logs for hotkey action, branch taken (`applied` vs `no-op`), and resulting opacity when applied.
- Planned verification (implemented in Phase 3):
- Unit test: `overlay on` from `0` restores previous visible opacity.
- Unit test: `overlay on` from `>0` is no-op.
- Unit test: `overlay off` from `>0` sets opacity to `0`.
- Unit test: `overlay off` from `0` is no-op.
- Risk: unintended config rebroadcasts on no-op paths.
- Mitigation: guard branch before invoking toggle helper and assert no-op behavior in tests.

#### Stage 1.2 Decision Record: runtime lifecycle contract
- Registration entry point: `_PluginRuntime.start()` in `load.py`, after runtime services are started.
- Chosen insertion point: after `register_publisher(self._publish_external)` and before `_log("Plugin started")`.
- Rationale: broadcaster/publisher services are already online, so retries can run without blocking startup path correctness.
- Unregistration entry point: `_PluginRuntime.stop()` in `load.py`, immediately after `_running` is flipped to `False`.
- Stop-time behavior:
- cancel any pending retry timers/handles before other shutdown work.
- best-effort unregister hotkey actions if API provides unregister support.
- if unregister is unavailable or fails, log and continue shutdown (no hard failure).
- Invariants:
- startup remains successful even when EDMC-Hotkeys is absent.
- no duplicate registrations when `start()` is called while already running.
- retries stop once registration succeeds or plugin begins stopping.

#### Stage 1.3 Decision Record: retry/backoff contract
- Retry scope: import failures from `importlib.import_module("EDMC-Hotkeys.load")` only.
- Max retries: 5.
- Backoff schedule (seconds): `0.5`, `1.0`, `2.0`, `4.0`, `8.0`.
- Timer model: schedule one retry at a time; do not queue all timers upfront.
- Success behavior:
- first successful import stops future retries.
- action registration occurs immediately after successful import.
- Failure behavior:
- if all 5 retries fail, stop retrying and keep plugin running without hotkeys integration.
- emit one summary warning at exhaustion.
- Logging expectations:
- warning log for each failed import attempt with attempt index.
- info log on successful import/registration.
- final warning when retries are exhausted.

### Phase 2: Runtime hotkeys registration + callbacks
- Status note: this phase was implemented directly in `load.py`, but is now superseded by Phase 2A addendum to reduce monolith growth.
- Add runtime hotkeys registration helpers in `load.py`:
- `_register_hotkeys_actions()` to import EDMC-Hotkeys API and register two actions.
- `_unregister_hotkeys_actions()` (if supported by EDMC-Hotkeys API) for clean stop.
- `_hotkey_overlay_on(...)` / `_hotkey_overlay_off(...)` callbacks that delegate to runtime opacity helpers.
- Action IDs and labels (proposed):
- `Overlay On` / `Overlay On`
- `Overlay Off` / `Overlay Off`
- Callback behavior will reuse existing methods:
- `overlay off`: use existing toggle/opacity persistence logic to move to `0` while preserving restore value; no-op when already `0`.
- `overlay on`: restore previous visible value when currently `0`; no-op when already `>0`.
- Registration call site:
- invoke in runtime startup after plugin runtime is initialized and ready.
- exponential-backoff retry hook for import failures only, bounded by max attempts.
- Risks: hard import of optional dependency breaks plugin startup.
- Mitigations: import inside helper; log warning and no-op if unavailable.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add dynamic EDMC-Hotkeys import + action registration helper(s) | Completed |
| 2.2 | Add `overlay on/off` callback methods that reuse existing opacity/toggle logic | Completed |
| 2.3 | Wire register/unregister into runtime start/stop lifecycle | Completed |

#### Stage 2.1 Detailed Plan: dynamic import + action registration helpers
- Objective: add a resilient hotkeys registration surface that never blocks plugin startup.
- Primary touchpoints:
- `load.py` imports: add safe optional import for `Action` from `edmc_hotkeys.registry` with fallback handling.
- `_PluginRuntime` fields: add state for hotkeys API/module handle, registered action ids, retry attempt counter, retry timer handle, and retry-active flag.
- New runtime helpers in `load.py`:
- `_import_hotkeys_api() -> Optional[Any]`: imports `EDMC-Hotkeys.load`; returns module or `None`.
- `_build_hotkeys_actions() -> list[Any]`: creates two action objects (`Overlay On`, `Overlay Off`) with `thread_policy="main"`.
- `_register_hotkeys_actions() -> bool`: imports API, builds actions, registers each action, stores registration state on success.
- `_schedule_hotkeys_retry(attempt: int) -> None`: schedules one retry timer using the Phase 1 backoff schedule.
- `_clear_hotkeys_retry_state() -> None`: cancels timer and resets retry tracking.
- Registration algorithm:
- attempt immediate `_register_hotkeys_actions()` once at start.
- on import failure, call `_schedule_hotkeys_retry(1)`.
- each retry invokes the same register helper.
- stop retrying when register succeeds or after 5 failed retry attempts.
- do not retry on non-import registration failures (`register_action` false/exception).
- Data contract for actions:
- label: `Overlay On` and `Overlay Off`.
- callback: bound runtime methods for on/off behavior.
- `enabled=True`, `thread_policy="main"`, `plugin=PLUGIN_NAME`.
- ID strategy:
- keep deterministic ids (internal), but user-facing labels remain human-readable as required.
- Risks:
- timer leaks across stop/start cycles.
- duplicate action registration after partial success.
- Mitigations:
- one-timer-at-a-time model with explicit cancel path.
- idempotent state checks before re-registering already-registered actions.

#### Stage 2.2 Detailed Plan: hotkey callbacks reusing existing opacity/toggle logic
- Objective: implement on/off callbacks without introducing new opacity business logic.
- Primary touchpoints in `load.py`:
- `_current_payload_opacity()` helper (under `_prefs_lock`) returning int 0..100.
- `_hotkey_overlay_on(*, payload=None, source="hotkey", hotkey=None)` callback.
- `_hotkey_overlay_off(*, payload=None, source="hotkey", hotkey=None)` callback.
- Callback flow:
- `overlay on`: read current opacity; if `0` call `toggle_payload_opacity_preference()`, else no-op.
- `overlay off`: read current opacity; if `>0` call `toggle_payload_opacity_preference()`, else no-op.
- logging includes source/hotkey/payload and branch (`applied`/`no-op`) at debug level.
- error handling:
- callback wraps internal calls and logs exceptions; no exception escapes to EDMC-Hotkeys caller.
- no-op path:
- must not call save or `_send_overlay_config`.
- Invariants:
- all persistence/config-broadcast side effects continue to flow through existing runtime methods.
- chat command behavior remains unchanged and untouched.
- Risks:
- accidental use of `set_payload_opacity_preference(0/100)` could break restore semantics.
- Mitigations:
- enforce use of `toggle_payload_opacity_preference()` for state-changing on/off transitions.

#### Stage 2.3 Detailed Plan: lifecycle wiring in start/stop
- Objective: integrate registration/retry lifecycle with existing runtime start/stop semantics.
- `start()` wiring plan:
- after `register_publisher(self._publish_external)`, call `_register_hotkeys_actions()`.
- if import fails, `_register_hotkeys_actions()` schedules retry #1 and returns false; startup continues.
- if success, clear retry state and log success.
- `stop()` wiring plan:
- immediately after `_running` is set false, call `_clear_hotkeys_retry_state()`.
- call `_unregister_hotkeys_actions()` best-effort:
- if hotkeys API provides unregister by action id, invoke it for registered ids.
- if unregister API absent/unexpected, log debug/warn and continue shutdown.
- clear in-memory hotkeys registration state regardless of unregister outcome.
- retry callback guard:
- each retry callback checks `_running`; if false, exits without further scheduling.
- each retry callback checks whether actions already registered; if yes, exits.
- idempotence requirements:
- repeated `start()` while running must not register again.
- stop/start cycle should produce exactly one active registration set.
- Risks:
- race between stop and an in-flight retry timer callback.
- Mitigations:
- cancel timer in stop and guard retry callback with `_running` + state checks.

### Phase 2 Addendum: Extract hotkeys to `overlay_plugin/hotkeys.py`
- Goal: move hotkeys functionality out of `load.py` into a dedicated module while preserving all Phase 1/2 behavior.
- Architecture decision:
- all hotkeys code will live in `overlay_plugin/hotkeys.py`.
- `load.py` will keep only thin lifecycle hooks and existing opacity/toggle APIs.
- Behavioral invariants (must not change):
- same action labels: `Overlay On`, `Overlay Off`.
- same no-op semantics for `overlay on/off`.
- same retry contract: import-failure-only, 5 retries, increasing delays (`0.5`, `1.0`, `2.0`, `4.0`, `8.0`).
- same best-effort unregister on stop.

| Stage | Description | Status |
| --- | --- | --- |
| 2A.1 | Create `overlay_plugin/hotkeys.py` manager skeleton (constants, state, lifecycle API) | Completed |
| 2A.2 | Move import/register/unregister/retry logic from `load.py` into manager module | Completed |
| 2A.3 | Move `overlay on/off` callbacks and no-op semantics into manager module | Completed |
| 2A.4 | Reduce `load.py` to lightweight tie-ins (`__init__`, `start`, `stop`) and remove monolith hotkeys internals | Completed |
| 2A.5 | Update/add tests for moduleized hotkeys behavior and runtime integration | Completed |

#### Phase 2A Detailed Execution Plan
- Execution order: implement stages `2A.1` -> `2A.2` -> `2A.3` -> `2A.4` -> `2A.5`; do not skip ahead.
- Migration rule: keep runtime behavior identical at each step; if behavior drifts, stop and document before proceeding.
- Scope boundary: this addendum only restructures code location/ownership; no feature expansion beyond existing Phase 2 behavior.

#### Stage 2A.1 Detailed Plan: manager skeleton in `hotkeys.py`
- Files to touch:
- `overlay_plugin/hotkeys.py` (new).
- `load.py` (temporary import/instantiation only; no behavior switch yet).
- Create `HotkeysManager` class with:
- constructor accepting host/runtime and logger.
- `start()` and `stop()` public lifecycle methods.
- private state: lock, timer handle, api handle, registered action IDs, retry bookkeeping.
- Define module constants in `hotkeys.py`:
- `HOTKEYS_IMPORT_MODULE`, `HOTKEYS_REGISTRY_MODULE`.
- action IDs and retry delay schedule.
- Define host contract in code comments/type hints:
- host running-state access,
- host opacity accessor,
- host toggle method.
- Acceptance criteria:
- module imports cleanly in both package and top-level plugin load contexts.
- manager object can be instantiated from runtime without side effects.
- no registration behavior moved yet (skeleton only).
- Risks:
- import path mismatch between package/non-package mode.
- Mitigation:
- mirror existing dual import strategy and keep manager module free of EDMC-only side effects.

#### Stage 2A.2 Detailed Plan: extract registration/retry/unregister logic
- Files to touch:
- `overlay_plugin/hotkeys.py`, `load.py`.
- Move from runtime into manager:
- import hotkeys api,
- build/register actions,
- retry scheduling/callback/cancel,
- unregister best effort.
- Keep these invariants while moving:
- one retry timer at a time.
- retry only on import failure.
- max 5 retries with increasing delays (`0.5`, `1.0`, `2.0`, `4.0`, `8.0`).
- rollback partial action registrations when later action registration fails.
- logging parity:
- preserve warning/info semantics from existing behavior.
- Acceptance criteria:
- manager `start()` performs immediate registration attempt.
- import failure path schedules retry and does not block plugin startup.
- manager `stop()` cancels timer and attempts unregister.
- Risks:
- duplicate registration if manager start called twice.
- Mitigation:
- explicit idempotence guards on registered-id state.

#### Stage 2A.3 Detailed Plan: extract callbacks/no-op behavior
- Files to touch:
- `overlay_plugin/hotkeys.py`, `load.py`.
- Move hotkey callbacks and opacity guard behavior from runtime into manager:
- `overlay_on_callback` and `overlay_off_callback`.
- `current opacity` helper.
- Preserve exact semantics:
- `overlay on`: apply only when opacity is `0`; otherwise no-op.
- `overlay off`: apply only when opacity is `>0`; otherwise no-op.
- Keep existing business path:
- callback must call host `toggle_payload_opacity_preference()` for state changes.
- no-op path must not trigger save/config broadcast.
- Acceptance criteria:
- callbacks are bound into action objects created by manager.
- callback logs include branch (`applied`/`no-op`) and source metadata.
- runtime chat command behavior remains unchanged.
- Risks:
- accidental direct set to `0/100` bypassing restore logic.
- Mitigation:
- disallow use of `set_payload_opacity_preference()` inside manager callbacks.

#### Stage 2A.4 Detailed Plan: lightweight `load.py` tie-ins
- Files to touch:
- `load.py` (primary), `overlay_plugin/hotkeys.py` (final API shape).
- Runtime changes in `load.py`:
- instantiate `HotkeysManager` in `_PluginRuntime.__init__`.
- call `self._hotkeys.start()` in `start()` after publisher registration.
- call `self._hotkeys.stop()` in `stop()` immediately after `_running=False`.
- Delete old Phase 2 hotkeys internals from `load.py`:
- hotkeys constants,
- hotkeys state fields,
- registration/retry helpers,
- on/off callback helpers moved to manager.
- Keep existing generic runtime methods used by manager:
- `toggle_payload_opacity_preference()`.
- helper accessor for current opacity (or expose via host callable).
- Acceptance criteria:
- `load.py` has only lightweight hotkeys tie-ins and no hotkeys workflow logic.
- plugin start/stop remains idempotent and non-blocking.
- Risks:
- hidden call sites to removed methods.
- Mitigation:
- run `rg` for removed method names and clean all references.

#### Stage 2A.5 Detailed Plan: tests and verification
- Files to touch:
- `tests/test_hotkeys.py` (new).
- existing lifecycle/runtime tests as needed (`tests/test_lifecycle_tracking.py`, `tests/test_plugin_hooks.py`).
- Add tests for manager module:
- registers both actions on success.
- retries on import failure with expected retry count/backoff progression.
- stops retrying after max attempts.
- does not retry on non-import registration failure.
- cancels timer and attempts unregister on stop.
- callback no-op/apply behavior for on/off opacity boundaries.
- Add runtime integration tests:
- runtime calls manager `start()`/`stop()` exactly once per lifecycle transition.
- no monolith hotkeys state required in runtime after extraction.
- Validation commands to run when available:
- `python -m pytest tests/test_hotkeys.py tests/test_lifecycle_tracking.py tests/test_plugin_hooks.py`.
- `python -m pytest tests/test_journal_commands.py tests/test_toggle_helpers.py` (regression guard).
- Acceptance criteria:
- all hotkeys tests pass.
- no regressions in existing journal/toggle tests.
- If pytest unavailable:
- run `py -3 -m py_compile load.py overlay_plugin/hotkeys.py` and record limitation.

### Phase 3: Automated tests (moduleized architecture)
- Add focused tests for `overlay_plugin/hotkeys.py` without requiring EDMC-Hotkeys installed.
- Use import monkeypatching and fake hotkeys API objects to validate manager behavior deterministically.
- Validate behavior:
- registration succeeds when API is present and both actions are registered with expected labels/IDs/thread policy.
- import-failure retry schedule/exhaustion follows agreed backoff policy.
- registration failure path does not schedule retries.
- callback behavior (`overlay on/off`) preserves no-op boundaries and toggle-path reuse.
- runtime lifecycle tie-ins remain lightweight (`start()`/`stop()` call manager exactly once per transition).
- Risks: brittle tests tied to internal method names.
- Mitigations: assert externally visible behavior/state transitions over incidental logging text.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add manager registration/retry success/failure tests with mocked hotkeys modules | Completed |
| 3.2 | Add callback behavior tests for `overlay on/off` semantics in `hotkeys.py` | Completed |
| 3.3 | Add lifecycle tie-in test to assert lightweight runtime integration (`start`/`stop`) | Completed |

#### Phase 3 Detailed Execution Plan
- Objective: verify hotkeys behavior through module-level tests with deterministic mocks and minimal runtime coupling.
- Test architecture:
- primary module tests live in `tests/test_hotkeys.py`.
- lifecycle integration assertions live in `tests/test_lifecycle_tracking.py`.
- no tests require EDMC-Hotkeys to be installed; all external dependencies are mocked.

#### Stage 3.1 Detailed Plan: registration and retry behavior
- Files:
- `tests/test_hotkeys.py`.
- Test fixtures/stubs:
- fake host state exposing running flag, current opacity, and toggle function.
- fake hotkeys API with configurable `register_action` outcomes and `unregister_action` capture.
- fake `Action` class for registry module.
- fake `threading.Timer` to capture delay schedule and trigger retries deterministically.
- Planned assertions:
- success path registers exactly two actions with labels `Overlay On` and `Overlay Off`.
- action metadata includes deterministic IDs and `thread_policy="main"`.
- import failure schedules retries with delays `0.5`, `1.0`, `2.0`, `4.0`, `8.0`.
- retry scheduling stops after max attempts.
- non-import registration failures do not schedule retries.
- stop path cancels pending retry timer.
- Risks:
- retry tests can become flaky if real timers run.
- Mitigation:
- fully monkeypatch timer class and drive callback invocation manually.

#### Stage 3.2 Detailed Plan: callback no-op/apply semantics
- Files:
- `tests/test_hotkeys.py`.
- Behavior matrix to validate:
- `overlay on`, opacity `>0` => no-op (toggle not called).
- `overlay on`, opacity `==0` => apply (toggle called once).
- `overlay off`, opacity `==0` => no-op (toggle not called).
- `overlay off`, opacity `>0` => apply (toggle called once).
- Additional guard:
- callbacks route state changes via toggle path only; no direct set-to-100/set-to-0 branch.
- Risks:
- false positives if host stub auto-mutates unexpectedly.
- Mitigation:
- keep host stub state transitions explicit and assert both call count and resulting opacity.

#### Stage 3.3 Detailed Plan: runtime tie-ins remain lightweight
- Files:
- `tests/test_lifecycle_tracking.py`.
- Test approach:
- monkeypatch `load.HotkeysManager` with a dummy manager that counts `start()` and `stop()` calls.
- instantiate runtime with existing lifecycle stubs and run `start()`/`stop()`.
- Planned assertions:
- runtime constructs manager once.
- runtime invokes `manager.start()` once per start.
- runtime invokes `manager.stop()` once per stop.
- runtime lifecycle still drains tracked resources as before.
- Risks:
- coupling with other lifecycle monkeypatches could hide regression.
- Mitigation:
- keep tie-in assertion test isolated and additive to existing lifecycle tests.

#### Phase 3 Acceptance Criteria
- `tests/test_hotkeys.py` covers registration, retry, callback semantics, and stop behavior.
- lifecycle tie-in test confirms `load.py` remains thin for hotkeys integration.
- tests remain deterministic and dependency-free (no EDMC-Hotkeys installation required).
- any environment constraint (e.g., missing pytest) is recorded in Phase 3/4 results.

### Phase 4: Verification and docs
- Run targeted tests first, then broader suite as needed:
- `python -m pytest tests/test_hotkeys.py tests/test_lifecycle_tracking.py tests/test_plugin_hooks.py`
- `python -m pytest tests/test_journal_commands.py tests/test_toggle_helpers.py` (regression guard)
- If pytest unavailable: run `py -3 -m py_compile load.py overlay_plugin/hotkeys.py tests/test_hotkeys.py tests/test_lifecycle_tracking.py`
- Capture results and any skips in Implementation Results.
- Risks: silent regressions in existing command behavior.
- Mitigations: include existing command/toggle test files in targeted run.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Run targeted pytest selections for hotkeys + existing toggle/command paths | Completed (Passed via Windows-only pytest wrapper) |
| 4.2 | Record outcomes, deviations, and follow-ups in Implementation Results | Completed |

#### Phase 4 Detailed Execution Plan
- Objective: finalize verification evidence for the moduleized hotkeys architecture and close the planning cycle with explicit pass/blocker reporting.
- Verification principle: run highest-signal targeted suites first, then regression guards, then fallback compile checks if pytest is unavailable.
- Evidence rule: each executed command must be captured in `Phase 4 Results` with pass/fail/block reason.

#### Stage 4.1 Detailed Plan: verification command matrix
- Files/areas validated:
- `overlay_plugin/hotkeys.py` behavior and integration.
- `load.py` lightweight tie-ins.
- hotkeys/lifecycle tests and existing command/toggle regressions.
- Execution order:
- 1) `python -m pytest tests/test_hotkeys.py tests/test_lifecycle_tracking.py tests/test_plugin_hooks.py`
- 2) `python -m pytest tests/test_journal_commands.py tests/test_toggle_helpers.py`
- 3) If pytest is unavailable:
- `py -3 -m py_compile load.py overlay_plugin/hotkeys.py tests/test_hotkeys.py tests/test_lifecycle_tracking.py tests/test_journal_commands.py tests/test_toggle_helpers.py`
- Planned assertions from command runs:
- no import/runtime failures in moduleized hotkeys path.
- no regressions in existing chat command and toggle helper behavior.
- lifecycle tests continue to pass with hotkeys manager tie-ins.
- Risks:
- pytest/tooling unavailable in environment.
- Mitigation:
- record explicit blocker output and run compile checks as minimum verification baseline.

#### Stage 4.2 Detailed Plan: documentation closure and risk callout
- Update `Implementation Results -> Phase 4 Results` with:
- commands attempted in order,
- command outcomes (`passed`, `failed`, or `blocked`),
- specific blocker text when blocked,
- residual risk statement tied to unexecuted pytest suites.
- Update phase/stage status rules:
- keep `4.1` as `Planned` or move to `Completed` only when pytest/verification goals are met or accepted as blocked by environment.
- keep `4.2` as `Completed` only after results section reflects the latest verification attempt set.
- Final doc consistency pass:
- ensure Phase Overview status aligns with Stage 4.x statuses and results narrative.

#### Phase 4 Acceptance Criteria
- verification commands for hotkeys and regression scope are explicitly attempted and recorded.
- blocker conditions (if any) are concrete and reproducible (command + error).
- `Phase 4 Results` provides enough evidence for handoff/review without re-reading terminal output.

### Phase 5: Registration retry scope expansion
- Context: runtime logs showed import eventually succeeded, but registration was rejected while EDMC-Hotkeys had not fully started yet.
- Goal: keep current import retry behavior and add bounded retry for `register_action == false` so startup ordering races self-heal.
- Updated retry contract:
- retry remains capped at 5 attempts with delays `0.5`, `1.0`, `2.0`, `4.0`, `8.0`.
- retry applies to import failures and `register_action == false` only.
- retry does not apply to registration exceptions or action build/API-shape failures.
- partial registration rollback is removed; failures are logged and retried only on `register_action == false`.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Update `HotkeysManager` retry logic to schedule backoff on `register_action == false` | Completed |
| 5.2 | Update/add tests for registration-failure retry behavior | Completed |
| 5.3 | Run targeted verification and document outcomes | Completed |

#### Phase 5 Detailed Plan
- Stage 5.1 implementation:
- add a single helper to schedule/retry with consistent attempt accounting and logging.
- call that helper from import failure path and `register_action == false` path.
- preserve idempotence and one-timer-at-a-time behavior.
- Stage 5.2 tests:
- replace existing no-retry-on-registration-failure assertion with retry-on-registration-failure assertions.
- verify retry timer is scheduled with expected delay and that a subsequent attempt can succeed.
- verify registration exceptions do not schedule retry.
- Stage 5.3 verification:
- run `overlay_client\.venv\Scripts\python scripts\run_pytest_safe_windows.py tests/test_hotkeys.py -p no:cacheprovider`.
- run `overlay_client\.venv\Scripts\python scripts\run_pytest_safe_windows.py tests/test_lifecycle_tracking.py tests/test_plugin_hooks.py -p no:cacheprovider` as regression check.

## Implementation Results

### Phase 1 Results
- Completed planning decisions:
- `overlay on/off` no-op behavior is explicitly defined.
- Retry policy is import-failure-only with explicit exponential schedule: `0.5`, `1.0`, `2.0`, `4.0`, `8.0` seconds (5 retries).
- Action labels are `Overlay On` and `Overlay Off`.
- Runtime lifecycle contract is fixed:
- register in `_PluginRuntime.start()` after publisher registration.
- cancel retry/unregister in `_PluginRuntime.stop()` as best effort with no shutdown hard-failures.

### Phase 2 Results
- Implemented in `load.py`:
- Added hotkeys constants for import modules, retry delays, and action IDs.
- Added runtime hotkeys state (`_hotkeys_api`, `_hotkeys_retry_timer`, `_hotkeys_registered_action_ids`) guarded by `_hotkeys_lock`.
- Added dynamic import + registration helpers:
- `_import_hotkeys_api`, `_build_hotkeys_actions`, `_register_hotkeys_actions`, `_schedule_hotkeys_retry`, `_hotkeys_retry_callback`, `_clear_hotkeys_retry_state`, `_unregister_hotkeys_actions`.
- Implemented `overlay on/off` callbacks and opacity guard helper:
- `_current_payload_opacity`, `_hotkey_overlay_on`, `_hotkey_overlay_off`.
- Reused existing toggle pathway (`toggle_payload_opacity_preference`) for state-changing transitions; no-op paths skip mutation/config push.
- Wired lifecycle integration:
- `start()` now attempts hotkeys registration after `register_publisher(...)`.
- `stop()` now cancels retry timer and unregisters actions best-effort before continuing shutdown.
- Retry behavior implemented per Phase 1 decisions:
- import-failure-only retries with schedule `0.5`, `1.0`, `2.0`, `4.0`, `8.0` seconds.
- registration failures (non-import) do not schedule retry.
- Validation run:
- `py -3 -m py_compile load.py` passed.
- Could not run pytest in this environment (`py -3 -m pytest ...` failed: `No module named pytest`; `.venv` not present).
- Superseded by Phase 2A addendum to modularize hotkeys into `overlay_plugin/hotkeys.py`.

### Phase 2 Addendum Results
- Implemented `overlay_plugin/hotkeys.py` with a dedicated `HotkeysManager` that now owns:
- EDMC-Hotkeys import/register/unregister workflow.
- import-failure-only retry scheduling with delays `0.5`, `1.0`, `2.0`, `4.0`, `8.0`.
- `Overlay On` / `Overlay Off` callbacks with no-op boundary semantics.
- best-effort rollback of partially registered actions when registration fails mid-sequence.
- Refactored `load.py` to lightweight tie-ins:
- runtime instantiates `HotkeysManager` in `__init__`.
- `start()` calls `self._hotkeys.start()` after publisher registration.
- `stop()` calls `self._hotkeys.stop()` before broader shutdown steps.
- Removed monolith hotkeys internals from `load.py`:
- hotkeys constants, state fields, retry helpers, action registration helpers, and callback handlers.
- Kept existing runtime opacity/toggle method pathways unchanged for behavior parity.
- Added tests for moduleized behavior:
- new `tests/test_hotkeys.py` covering registration success, retry scheduling/exhaustion, no-retry-on-registration-failure, stop-time cancel/unregister, and callback no-op/apply semantics.
- updated `tests/test_lifecycle_tracking.py` with `test_hotkeys_manager_start_stop_are_lightweight_tie_ins` to validate runtime integration.
- Validation run:
- `py -3 -m py_compile load.py overlay_plugin/hotkeys.py tests/test_hotkeys.py tests/test_lifecycle_tracking.py` passed.
- `py -3 -m pytest tests/test_hotkeys.py tests/test_lifecycle_tracking.py` could not run in this environment (`No module named pytest`).

### Phase 3 Results
- Added `tests/test_hotkeys.py` with moduleized manager coverage:
- registration success path and expected action metadata.
- import-failure retry scheduling/exhaustion behavior.
- no retry on non-import registration failure.
- stop-time retry cancel + unregister behavior.
- `overlay on/off` callback no-op/apply boundary semantics.
- Updated `tests/test_lifecycle_tracking.py` with a runtime tie-in test:
- `test_hotkeys_manager_start_stop_are_lightweight_tie_ins`.
- Validation run for Phase 3 test scope:
- `py -3 -m py_compile tests/test_hotkeys.py tests/test_lifecycle_tracking.py tests/test_journal_commands.py tests/test_toggle_helpers.py` passed.
- `py -3 -m pytest tests/test_hotkeys.py tests/test_lifecycle_tracking.py tests/test_journal_commands.py tests/test_toggle_helpers.py` blocked in this environment (`No module named pytest`).

### Phase 4 Results
- Verification commands attempted in planned order:
- Initial attempts:
- `py -3 -m pytest tests/test_hotkeys.py tests/test_lifecycle_tracking.py tests/test_plugin_hooks.py` -> blocked (`No module named pytest`).
- `py -3 -m pytest tests/test_journal_commands.py tests/test_toggle_helpers.py` -> blocked (`No module named pytest`).
- Fallback compile verification:
- `py -3 -m py_compile load.py overlay_plugin/hotkeys.py tests/test_hotkeys.py tests/test_lifecycle_tracking.py tests/test_journal_commands.py tests/test_toggle_helpers.py` -> passed.
- Retry attempt (Windows venv under `overlay_client/.venv`):
- `overlay_client\.venv\Scripts\python -m pytest ...` -> blocked (`No module named pytest`).
- `overlay_client\.venv\Scripts\python -m pip install -r requirements\dev.txt` -> blocked by `pydbus>=0.6.0` resolution failure (pulled from `overlay_client/requirements/wayland.txt`).
- `overlay_client\.venv\Scripts\python -m pip install pytest` -> blocked (no matching distribution in current package index/network context).
- After pytest became available in `overlay_client/.venv`:
- `overlay_client\.venv\Scripts\python -m pytest tests/test_hotkeys.py tests/test_lifecycle_tracking.py tests/test_plugin_hooks.py` -> partial pass:
- `tests/test_hotkeys.py`: 5 passed.
- `tests/test_lifecycle_tracking.py` and `tests/test_plugin_hooks.py`: setup errors from `PermissionError: [WinError 5] Access is denied` on `pytest-of-jonow` and `.pytest_cache` temp/cache directories.
- command summary: `5 passed, 5 errors`.
- `overlay_client\.venv\Scripts\python -m pytest tests/test_journal_commands.py tests/test_toggle_helpers.py` -> passed (`24 passed`) with a non-fatal pytest cache warning (`WinError 5` on cache path).
- Windows-only workaround codified for Python 3.13+ temp-permission behavior:
- added `scripts/run_pytest_safe_windows.py` (Windows-only launcher) to set a safe `PYTEST_DEBUG_TEMPROOT` and patch `Path.mkdir(mode=0o700)` handling during test runs.
- `overlay_client\.venv\Scripts\python scripts\run_pytest_safe_windows.py tests/test_hotkeys.py tests/test_lifecycle_tracking.py tests/test_plugin_hooks.py -p no:cacheprovider` -> passed (`10 passed`).
- `overlay_client\.venv\Scripts\python scripts\run_pytest_safe_windows.py tests/test_journal_commands.py tests/test_toggle_helpers.py -p no:cacheprovider` -> passed (`24 passed`).
- Residual risk:
- targeted suites now pass under the Windows-only wrapper; local testing on Windows Python 3.13+ depends on this workaround until upstream temp-permission behavior is resolved.

### Phase 5 Results
- Implemented retry-scope expansion in `overlay_plugin/hotkeys.py`:
- import failures continue to retry with backoff `0.5`, `1.0`, `2.0`, `4.0`, `8.0`.
- `register_action == false` now retries with the same backoff/cap.
- registration exceptions now fail fast (logged) and do not retry.
- removed partial-registration rollback behavior on registration failure.
- Updated tests in `tests/test_hotkeys.py`:
- replaced no-retry expectation with `register_action == false` retry expectation.
- added explicit assertion that registration exceptions do not retry.
- Verification runs:
- `overlay_client\.venv\Scripts\python scripts\run_pytest_safe_windows.py tests/test_hotkeys.py -p no:cacheprovider` -> passed (`6 passed`).
- `overlay_client\.venv\Scripts\python scripts\run_pytest_safe_windows.py tests/test_lifecycle_tracking.py tests/test_plugin_hooks.py -p no:cacheprovider` -> passed (`5 passed`).
