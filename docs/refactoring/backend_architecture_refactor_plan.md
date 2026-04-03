## Goal: Refactor EDMCModernOverlay into an explicit backend architecture without breaking current behavior

This plan turns the locked decisions from `docs/refactoring/cross_platform_overlay_architecture_research.md` into a staged refactor sequence.
Document implementation results in the `Execution Log` section.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear, capture it under `Open Questions`.

## Refactorer Persona
- Bias toward carving out modules aggressively while guarding behavior: no feature changes, no silent regressions.
- Prefer pure/push-down seams, explicit interfaces, and fast feedback loops (tests + dev-mode toggles) before deleting code from the monolith.
- Treat risky edges (I/O, timers, sockets, UI focus) as contract-driven: write down invariants, probe with tests, and keep escape hatches to revert quickly.
- Default to "lift then prove" refactors: move code intact behind an API, add coverage, then trim/reshape once behavior is anchored.
- Resolve the "be aggressive" vs. "keep changes small" tension by staging extractions: lift intact, add tests, then slim in follow-ups so each step stays behavior-scoped and reversible.
- Track progress with per-phase tables of stages (stage #, description, status). Mark each stage as completed when done; when all stages in a phase are complete, flip the phase status to `Completed`. Number stages as `<phase>.<stage>` (e.g., `1.1`, `1.2`) to keep ordering clear.
- Personal rule: if asked to "Implement...", expand/document the plan and stages (including tests to run) before touching code.
- Personal rule: keep notes ordered by phase, then by stage within that phase.

## Dev Best Practices
- Keep changes small and behavior-scoped; prefer feature flags/dev-mode toggles for risky tweaks.
- Plan before coding: note touch points, expected unchanged behavior, and tests you will run.
- Avoid UI work off the main thread; keep new helpers pure/data-only where possible.
- When touching preferences/config code, use EDMC `config.get_int/str/bool/list` helpers and `number_from_string` for locale-aware numeric parsing; avoid raw `config.get/set`.
- Record tests run (or skipped with reasons) when landing changes; default to headless tests for pure helpers.
- Prefer fast/no-op paths in release builds; keep debug logging/dev overlays gated behind dev mode.

## Test Type Selection (Required Before Refactoring)
- Decide and document test type before code edits for each touched behavior.
- Use **unit tests** for pure/data-only seams and deterministic helpers.
- Use **harness tests** when refactors touch `load.py`, hook wiring, startup/shutdown lifecycle, EDMC callback flow, or runtime state integration.
- For refactors that split pure logic from wiring, require both test types (unit for lifted logic, harness for integration contract).

## Testing Strategy Matrix (Required)

| Refactor Slice | Existing Behavior/Invariants To Preserve | Test Type (Unit/Harness) | Why This Level | Test File(s) | Command |
| --- | --- | --- | --- | --- | --- |
| Backend contracts and status schema | Existing behavior remains unchanged while new types/contracts are introduced | Unit | Pure types and policy logic should be proven without EDMC lifecycle noise | `overlay_client/tests/test_backend_contracts.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py -q` |
| Platform probe and selector matrix | Current environment selection/fallback behavior is mirrored before cutover | Unit | Selector correctness must be locked across synthetic environment combinations | `overlay_client/tests/test_platform_probe.py`, `overlay_client/tests/test_backend_selector.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_platform_probe.py overlay_client/tests/test_backend_selector.py -q` |
| Client authority and selector wiring | Plugin hints remain advisory and client final selection is published correctly | Harness | Touches `load.py`, startup wiring, runtime state handoff | `tests/test_harness_backend_selection_wiring.py` | `source .venv/bin/activate && python -m pytest tests/test_harness_backend_selection_wiring.py -q` |
| Backend consumer cutover | Tracking/presentation/input consumers stop re-selecting locally and consume the chosen bundle only | Mixed (Unit + Harness) | Pure consumer adapters need unit coverage; `load.py`/runtime wiring needs harness coverage | `overlay_client/tests/test_backend_consumers.py`, `tests/test_harness_backend_consumer_contract.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py tests/test_harness_backend_consumer_contract.py -q` |
| Capability visibility and manual override | Status, warnings, override state, and diagnostics remain truthful and visible | Mixed (Unit + Harness) | Status formatting is pure; prefs/controller/runtime round-trip is integration-sensitive | `overlay_client/tests/test_backend_status.py`, `tests/test_harness_backend_override_roundtrip.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py tests/test_harness_backend_override_roundtrip.py -q` |
| Helper boundary and approval flows | Helper comms stay local-only and helper install/enable remains explicit and user-approved | Mixed (Unit + Harness) | Local protocol validation is pure; approval/reporting paths may cross plugin/runtime surfaces | `overlay_client/tests/test_helper_ipc_boundary.py`, `tests/test_install_linux.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py tests/test_install_linux.py -q` |

## Test Acceptance Gates (Required)
- [ ] Unit tests added/updated for extracted pure logic.
- [ ] Harness tests added/updated for lifecycle/wiring surfaces.
- [ ] Commands executed and outcomes recorded.
- [ ] Skips/failures documented with reason and follow-up action.

## Scope
- In scope:
- extract platform/backend decisions into explicit contracts and backend bundles
- preserve current behavior while moving to a client-authoritative, selector-driven backend architecture
- add capability visibility, manual override, and diagnostics required by the locked decisions
- add backend contract tests and capability-matrix coverage around project-owned test surfaces
- Out of scope:
- redesigning or replacing the Tk controller
- silently downgrading currently working environments
- silently removing `xwayland_compat`
- silently installing or enabling compositor-native helpers
- editing immutable vendored harness files (`tests/harness.py`, `tests/edmc/**`) as part of normal refactor work

## Current Touch Points
- Code:
- `load.py` (plugin lifecycle, launch context hints, env construction, prefs, watchdog)
- `overlay_client/platform_context.py` (current platform context seeding)
- `overlay_client/client_config.py` (initial settings and config ingestion)
- `overlay_client/platform_integration.py` (runtime platform/controller behavior)
- `overlay_client/window_tracking.py` (tracker selection and compositor-specific follow logic)
- `overlay_client/setup_surface.py` (window setup and platform-controller initialization)
- `overlay_client/follow_surface.py` (follow-mode behavior and transient parent handling)
- `overlay_client/control_surface.py` (runtime config ingestion and platform-context updates)
- `overlay_controller/services/plugin_bridge.py` (minimal controller-side status/override pass-through only)
- `overlay_controller/overlay_controller.py` (minimal status display/override UI only)
- `overlay_plugin/preferences.py` (manual override and status surfacing)
- `scripts/install_linux.sh` and `scripts/install_matrix.json` (helper approval/install flows if helper-backed phases are reached)
- `utils/collect_overlay_debug_linux.sh` (diagnostic visibility)
- Tests:
- `overlay_client/tests/test_platform_context.py`
- `tests/test_harness_plugin_hooks_contract.py`
- `tests/HARNESS_README.md`
- `tests/config/README.md`
- Docs/notes:
- `docs/refactoring/cross_platform_overlay_architecture_research.md`
- `docs/archive/refactoring/client_refactor.md`
- `docs/archive/refactoring/load_refactory.md`
- `docs/archive/refactoring/compositor_aware_install.md`
- `docs/archive/README.md`

## Open Questions
- None currently. Environment-specific helper packaging details beyond the generic approval/security policy should be captured in follow-up helper plans when Phase 5 is reached.

## Decisions (Locked)
- Linux backend tracks remain explicit: `native_x11`, `xwayland_compat`, and `native_wayland_*`.
- Native Wayland is preferred where truly ready, but `xwayland_compat` remains an explicit fallback.
- The client is the final authority for runtime platform/compositor capability detection; the plugin is advisory.
- Backend selection happens in one place only; no secondary backend selection logic is allowed elsewhere.
- Generic Wayland is capability-gated, not best-effort.
- Helper-backed integrations are allowed selectively, require user approval, and helper install/update friction is reviewed case by case.
- The Tk controller remains in place as-is and is not a refactor target.
- Manual backend override remains available as a visible troubleshooting escape hatch.
- Capability state must be visible to users/support and fully inspectable in diagnostics.
- No currently working environment may be downgraded without explicit owner review.
- Short-term stabilization comes first in sequencing, but long-term backend cleanup remains mandatory.

## Architecture Diagram

```mermaid
flowchart LR
    subgraph EDMC["EDMC Host Process (Tk main loop)"]
        Core["EDMC Core"]
        Plugin["EDMCModernOverlay Plugin (load.py)\nControl plane: launch/config/prefs/CLI"]
        Prefs["Plugin Preferences UI"]
        Ctrl["Overlay Controller (Tk)"]
        EDMCLog["EDMC debug log"]
    end

    subgraph ClientProc["Overlay Client Process (Qt)"]
        Ingest["Config + platform_context ingest"]
        Probe["PlatformProbe (runtime evidence)"]
        Selector["Single BackendSelector\n(client authoritative)"]
        Status["BackendSelectionStatus + report\n(source=client_runtime)"]
        Bundles["Backend bundles/consumers\n(native_x11, xwayland_compat, native_wayland_*)"]
        ClientLog["overlay_client.log"]
    end

    subgraph Runtime["Local Runtime Channels"]
        Socket["Plugin↔Client socket channel\n(port.json + JSON messages)"]
        Helper["Optional compositor helpers\n(local IPC boundary)"]
        Diag["Diagnostics collector scripts"]
    end

    Core --> Plugin
    Plugin -->|overlay_config + platform_context + shadow_backend_status| Socket
    Socket --> Ingest
    Ingest --> Probe --> Selector --> Status --> Bundles
    Helper -->|helper->client only (no plugin in transport path)| Bundles

    Plugin -->|backend_status CLI (currently returns plugin_hint)| Prefs
    Plugin -->|backend_status CLI (currently returns plugin_hint)| Ctrl

    Status -->|client-runtime status lines| ClientLog
    ClientLog --> Diag
    Plugin -->|plugin shadow status lines| EDMCLog

    Plugin -. advisory only .->|shadow_backend_status (source=plugin_hint)| Selector
```

## Per-Iteration Test Plan
- **Env setup (once per machine):** `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements/dev.txt`
- **Headless quick pass (default for each step):** `source .venv/bin/activate && python -m pytest`
- **Targeted tests:** `source .venv/bin/activate && python -m pytest <path/to/tests> -k "<pattern>"`
- **Milestone checks:** `make check` and `make test`
- **Compliance baseline check (release/compliance work):** `python scripts/check_edmc_python.py`
- **Full suite with GUI deps (as applicable):** ensure GUI/runtime deps are installed, then run `source .venv/bin/activate && PYQT_TESTS=1 python -m pytest overlay_client/tests -q`
- **After wiring changes:** rerun headless tests plus the full GUI-enabled suite once per milestone to catch integration regressions.

## Guiding Traits for Readable, Maintainable Code
- Clarity first: simple, direct logic; avoid clever tricks; prefer small functions with clear names.
- Consistent style: stable formatting, naming conventions, and file structure; follow project style guides/linters.
- Intent made explicit: meaningful names; brief comments only where intent is not obvious; docstrings for public APIs.
- Single responsibility: each module/class/function does one thing; separate concerns; minimize side effects.
- Predictable control flow: limited branching depth; early returns for guard clauses; avoid deeply nested code.
- Good boundaries: clear interfaces; avoid leaking implementation details; use types or assertions to define expectations.
- DRY but pragmatic: share common logic without over-abstracting; duplicate only when it improves clarity.
- Small surfaces: limit global state; keep public APIs minimal; prefer immutability where practical.
- Testability: code structured so it is easy to unit/integration test; deterministic behavior; clear seams for injecting dependencies.
- Error handling: explicit failure paths; helpful messages; avoid silent catches; clean resource management.
- Observability: surface guarded fallbacks/edge conditions with trace/log hooks so silent behavior changes do not hide regressions.
- Documentation: concise README/usage notes; explain non-obvious decisions; update docs alongside code.
- Tooling: automated formatting/linting/tests in CI; commit hooks for quick checks; steady dependency management.
- Performance awareness: efficient enough without premature micro-optimizations; measure before tuning.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Introduce backend contracts, status schema, and a shadow selector without changing behavior | Completed |
| 2 | Extract current runtime behavior into explicit backend bundles while preserving behavior | Completed |
| 3 | Cut over to a client-authoritative selector and remove secondary backend selection | Completed |
| 4 | Surface capability state, manual override, and diagnostics with minimal controller changes | Completed |
| 5 | Add helper-boundary foundations, helper-aware approval flows, and final cleanup/archive work | Completed |

## Phase Details

### Phase 1: Backend Contracts And Shadow Selector Foundation
- Introduce the shared backend model, status schema, and selector logic as pure infrastructure.
- Keep runtime behavior unchanged: the selector runs in shadow mode and reports what it would choose without driving consumers yet.
- Risks: shadow logic drifting from current behavior; over-designing the contracts before extraction starts.
- Mitigations: keep contracts minimal, mirror current behavior first, and lock it with capability-matrix tests.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add backend contracts, status schema, and shared enums/data models | Completed |
| 1.2 | Implement `PlatformProbe` and `BackendSelector` in shadow mode, mirroring current behavior | Completed |
| 1.3 | Add capability-matrix and harness wiring tests around the shadow selector | Completed |

#### Stage 1.1 Detailed Plan
- Objective:
- Introduce the stable contract layer for probe results, backend bundles, support-family labels, capability classification, and fallback reasons.
- Primary touch points:
- `overlay_client/backend/__init__.py` (new)
- `overlay_client/backend/contracts.py` (new)
- `overlay_client/backend/status.py` (new)
- `overlay_client/tests/test_backend_contracts.py` (new)
- Steps:
- Create a new pure `overlay_client.backend` package that is importable without pulling in PyQt or current runtime selector code.
- Define dataclasses/enums/protocols for `PlatformProbe`, selector results, backend family/instance labels, capability classification, downgrade reasons, helper capability state, and bundle component contracts.
- Keep the initial contracts minimal and aligned with the decisions already locked in the research note.
- Do not wire the new types into `platform_context.py`, `platform_integration.py`, or any runtime consumer in this stage.
- Acceptance criteria:
- New contract modules are pure/data-oriented and introduce no runtime behavior change by themselves.
- The package can be imported in headless unit tests without requiring PyQt or EDMC runtime setup.
- Support-family and backend-instance naming are explicit and stable.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py -q`

#### Stage 1.2 Detailed Plan
- Objective:
- Build `PlatformProbe` and `BackendSelector` as pure logic that reproduces today's effective behavior, but do not make them authoritative yet.
- Primary touch points:
- `overlay_client/backend/contracts.py`
- `overlay_client/backend/probe.py` (new)
- `overlay_client/backend/selector.py` (new)
- `overlay_client/tests/test_platform_probe.py` (new)
- `overlay_client/tests/test_backend_selector.py` (new)
- Steps:
- Encode the current environment-detection rules from `platform_context.py`, `platform_integration.py`, and `window_tracking.py` into pure probe/selector helpers.
- Keep the selector conservative for already-working environments: mirror today's effective backend path without introducing stricter degraded or unsupported classifications that would require owner review.
- Defer runtime shadow-status plumbing in Qt-facing code to Stage `1.3`, where the plan already requires harness coverage for wiring.
- Acceptance criteria:
- Shadow selector produces expected backend family/instance, classification, and fallback reason for the currently supported matrix.
- Existing backend behavior remains unchanged because no runtime consumer is driven by the selector yet.
- The new probe and selector modules are importable and testable without PyQt runtime setup.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_platform_probe.py overlay_client/tests/test_backend_selector.py -q`

#### Stage 1.3 Detailed Plan
- Objective:
- Lock the selector and shadow-wiring behavior with unit and harness tests, while respecting vendored harness immutability.
- Primary touch points:
- `overlay_client/backend/contracts.py`
- `overlay_client/backend/status.py`
- `load.py`
- `overlay_client/tests/test_backend_contracts.py`
- `overlay_client/tests/test_platform_probe.py`
- `overlay_client/tests/test_backend_selector.py`
- `tests/test_overlay_config_payload.py`
- `tests/test_harness_backend_selection_wiring.py` (new)
- Steps:
- Expand the unit matrix to cover the agreed synthetic environments explicitly: Windows, GNOME X11, GNOME Wayland, Fedora KDE Wayland, and fallback scenarios.
- Add pure serialization helpers for probe and shadow selector status so runtime wiring can publish advisory shadow metadata without coupling to UI or sockets.
- Add a harness test that proves `load.py` can publish the shadow selector result through the existing overlay config payload path without taking authority away from the current runtime paths.
- Acceptance criteria:
- Capability-matrix coverage exists in project-owned tests only; vendored harness core remains untouched.
- At least one harness test covers the new runtime shadow-status plumbing on the existing config payload path.
- Runtime consumers still ignore the shadow selector metadata in this stage; it is advisory only.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_platform_probe.py overlay_client/tests/test_backend_selector.py tests/test_overlay_config_payload.py tests/test_harness_backend_selection_wiring.py -q`

#### Phase 1 Execution Order
- Implement in strict order: `1.1` -> `1.2` -> `1.3`.

#### Phase 1 Exit Criteria
- Contracts, status schema, and shadow selector exist and are test-covered.
- No runtime consumer has changed backend behavior yet.

### Phase 2: Backend Bundle Extraction Around Current Behavior
- Extract the existing runtime behavior into explicit backend bundles and consumer adapters.
- Keep current behavior and fallback paths intact, especially `native_x11` and `xwayland_compat`.
- Risks: hidden behavior drift during extraction; accidental recombination of X11/XWayland/Wayland behavior into new monoliths.
- Mitigations: extract one backend family at a time, allow shared implementation only where classification remains explicit, and add unit coverage per bundle.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Extract `native_x11` and `xwayland_compat` bundle surfaces from current X11/XCB behavior | Completed |
| 2.2 | Extract native Wayland family bundles for wlroots/Hyprland/KWin/GNOME paths while preserving behavior | Completed |
| 2.3 | Route platform integration, tracking, and follow consumers through backend adapters without changing selection | Completed |

#### Stage 2.1 Detailed Plan
- Objective:
- Separate current X11/XCB logic into explicit `native_x11` and `xwayland_compat` bundles, even if they share implementation internals.
- Primary touch points:
- `overlay_client/platform_integration.py`
- `overlay_client/window_tracking.py`
- `overlay_client/backend/consumers.py` (new)
- `overlay_client/backend/bundles/__init__.py` (new)
- `overlay_client/backend/bundles/native_x11.py` (new)
- `overlay_client/backend/bundles/xwayland_compat.py` (new)
- `overlay_client/tests/test_backend_bundles_x11.py` (new)
- `overlay_client/tests/test_backend_consumers.py` (new)
- Steps:
- Expose the current X11/XCB integration and wmctrl tracker through thin public factory helpers instead of making runtime code import private classes directly.
- Lift current X11/XCB presentation/tracking/input behavior into explicit bundle-oriented modules that preserve separate `native_x11` and `xwayland_compat` identities while reusing the same shipped implementation path underneath.
- Add generic consumer helpers for creating integrations and trackers from a backend bundle, but do not route runtime consumers through them yet.
- Preserve the distinction between true X11 sessions and XWayland compatibility even if helper functions are reused.
- Acceptance criteria:
- X11 and XWayland remain separately reported families/instances.
- Existing behavior remains unchanged because setup/runtime consumers still use the old selection path in this stage.
- `overlay_client.backend` top-level purity from Phase 1 remains intact; Qt-dependent bundle code lives under the bundle/consumer submodules only.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_consumers.py -q`

#### Stage 2.2 Detailed Plan
- Objective:
- Lift existing native Wayland runtime logic into explicit bundle modules for the currently recognized compositor families.
- Primary touch points:
- `overlay_client/platform_integration.py`
- `overlay_client/window_tracking.py`
- `overlay_client/backend/consumers.py`
- `overlay_client/backend/bundles/_wayland_common.py` (new)
- `overlay_client/backend/bundles/wayland_layer_shell_generic.py` (new)
- `overlay_client/backend/bundles/kwin_wayland.py` (new)
- `overlay_client/backend/bundles/gnome_shell_wayland.py` (new)
- `overlay_client/backend/bundles/hyprland.py` (new)
- `overlay_client/backend/bundles/sway_wayfire_wlroots.py` (new)
- `overlay_client/tests/test_backend_bundles_wayland.py` (new)
- `overlay_client/tests/test_backend_consumers.py`
- Steps:
- Expose the current shipped Wayland integration and compositor-specific trackers through thin public factory helpers instead of making bundle code import private classes directly.
- Extract current compositor-specific behavior into explicit bundle/adaptor modules without broadening support claims.
- Allow bundle discovery helpers to return `None` for compositor paths that intentionally have no shipped tracker yet, such as GNOME helper-required and generic unknown Wayland.
- Preserve today's missing-helper and fallback behavior for GNOME/KWin/unknown Wayland cases.
- Acceptance criteria:
- Native Wayland bundle modules exist for the currently recognized family set.
- Generic Wayland remains capability-gated in the selector model, but current compatibility is preserved by explicit bundle/fallback mapping.
- Runtime setup/follow consumers still use the old selection path in this stage; no follow-surface cutover happens yet.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_consumers.py -q`

#### Stage 2.3 Detailed Plan
- Objective:
- Make runtime consumers call backend adapters instead of re-deriving platform behavior locally.
- Primary touch points:
- `overlay_client/backend/consumers.py`
- `overlay_client/platform_integration.py`
- `overlay_client/window_tracking.py`
- `overlay_client/follow_surface.py`
- `overlay_client/setup_surface.py`
- `overlay_client/tests/test_backend_consumers.py`
- `overlay_client/tests/test_window_tracking_bundle_routing.py` (new)
- `overlay_client/tests/test_follow_surface_mixin.py`
- Steps:
- Add legacy runtime bundle-resolution helpers in the consumer layer so Linux runtime code can resolve explicit bundle identities without making the Phase `3` selector authoritative early.
- Route `PlatformController` integration creation, platform labeling, and transient-parent/Wayland policy queries through bundle helpers instead of repeating local session/compositor branching.
- Route Linux tracker creation through bundle discovery helpers while preserving the current XWayland/X11 fallback behavior for missing native Wayland trackers.
- Update follow/input call sites to ask the platform controller for policy decisions instead of re-deriving Wayland behavior locally.
- Acceptance criteria:
- Linux-side runtime consumers operate from explicit bundle adapters or bundle-derived policy helpers instead of open-coded compositor branches.
- No selector cutover has happened yet; behavior remains current and Windows stays on its existing direct path.
- No EDMC/plugin lifecycle wiring changes are required in this stage; targeted unit coverage is sufficient.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_follow_surface_mixin.py -q`

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.

#### Phase 2 Exit Criteria
- Current runtime behavior is represented by explicit bundle modules and adapters.
- Major consumers are bundle-ready even though the selector is still not authoritative.

### Phase 3: Client-Authoritative Selector Cutover
- Make the client the final authority for platform capability and backend selection.
- Remove distributed backend selection logic from runtime consumers and preserve native-first/fallback-available behavior.
- Risks: split-brain selection during cutover; accidental downgrade of currently working environments; missing override paths.
- Mitigations: staged cutover, explicit mismatch logging, no-silent-downgrade checks, and harness coverage on runtime wiring.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Move final capability probe/backend selection authority into the client; keep plugin hints advisory | Completed |
| 3.2 | Remove secondary backend selection from runtime consumers so they use selector results only | Completed |
| 3.3 | Preserve native-first fallback policy, no-silent-downgrade safeguards, and explicit fallback reasons | Completed |

#### Stage 3.1 Detailed Plan
- Objective:
- Shift final platform/capability authority to the client while preserving plugin launch/orchestration responsibilities.
- Primary touch points:
- `overlay_client/platform_context.py`
- `overlay_client/setup_surface.py`
- `overlay_client/control_surface.py`
- `overlay_client/tests/test_platform_context.py`
- `overlay_client/tests/test_control_surface_platform_context.py` (new)
- `tests/test_harness_backend_selection_wiring.py`
- Steps:
- Keep the plugin-side `shadow_backend_status` payload as an advisory hint only; do not make `load.py` authoritative for the client runtime decision.
- Add client-side helpers that derive the final backend-selection result from local runtime evidence first (`QGuiApplication.platformName()`, local environment), using plugin-provided platform context only as fallback hints or explicit user overrides.
- Initialize and retain client-owned final backend-selection state on startup, then recompute it when platform-context payloads arrive.
- Log plugin/client mismatches explicitly, but do not change runtime consumer behavior in this stage.
- Acceptance criteria:
- The client is authoritative for final backend selection.
- Plugin/client mismatches are logged rather than silently resolved in two places.
- No new client-to-plugin protocol is introduced in this stage; the client retains and publishes its final status through runtime state and logs only.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_platform_context.py overlay_client/tests/test_control_surface_platform_context.py tests/test_harness_backend_selection_wiring.py tests/test_harness_plugin_hooks_contract.py -q`

#### Stage 3.2 Detailed Plan
- Objective:
- Ensure tracking, presentation, and input-policy runtime consumers consume the client-selected backend bundle instead of re-resolving Linux backends from raw session/compositor context.
- Primary touch points:
- `overlay_client/backend/consumers.py`
- `overlay_client/platform_integration.py`
- `overlay_client/window_tracking.py`
- `overlay_client/follow_surface.py`
- `overlay_client/setup_surface.py`
- `overlay_client/control_surface.py`
- `overlay_client/launcher.py`
- `overlay_client/overlay_client.py`
- `overlay_client/tests/test_backend_consumers.py`
- `overlay_client/tests/test_platform_controller_backend_status.py` (new)
- `overlay_client/tests/test_window_tracking_bundle_routing.py`
- `overlay_client/tests/test_control_surface_platform_context.py`
- Steps:
- Add bundle-resolution helpers that map the client-owned `BackendSelectionStatus` to explicit Linux bundles and tracker fallback bundles without re-reading compositor/session environment in each consumer.
- Thread the selected backend status into `PlatformController` and tracker creation at runtime startup so the active client path uses the selector result rather than `resolve_legacy_linux_bundle(...)`.
- Keep fallback behavior anchored to the selected status so current native-Wayland-first, XWayland-available tracker behavior is preserved without reintroducing secondary selection logic.
- Keep plugin `shadow_backend_status` advisory-only and avoid `load.py` or controller changes in this stage.
- Acceptance criteria:
- The active client runtime path uses the client-owned selector result for platform integration and tracker creation.
- Runtime consumers no longer perform open-coded Linux backend selection from raw context/env once the client-owned status is available.
- No plugin/runtime lifecycle wiring changes are introduced in this stage; targeted client-side unit coverage is sufficient.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_control_surface_platform_context.py -q`

#### Stage 3.3 Detailed Plan
- Objective:
- Carry forward the agreed selection/classification safeguards during the cutover by turning implicit fallback and downgrade-protection policy into explicit selector/status data.
- Primary touch points:
- `overlay_client/backend/selector.py`
- `overlay_client/backend/status.py`
- `overlay_client/tests/test_backend_selector.py`
- `overlay_client/tests/test_backend_status.py` (new)
- Steps:
- Encode explicit fallback metadata for current selector outcomes instead of leaving fallback policy hidden in selector notes.
- Preserve `xwayland_compat` as a named fallback path by reporting what native backend it fell back from and why.
- Add explicit review/downgrade-guard metadata for cases where conservative classification is intentionally preserving current shipped behavior.
- Keep this stage pure: no prefs/controller/load.py changes, and no new manual-override UI plumbing yet.
- Acceptance criteria:
- Fallback reasons are explicit and testable.
- Downgrade-sensitive environments are marked for review rather than being silently reclassified.
- Current behavior and classification remain unchanged unless an existing test already required otherwise.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_platform_context.py -q`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3`.

#### Phase 3 Exit Criteria
- The client is the final authority and exactly one selector is active.
- Runtime consumers no longer re-decide the backend locally.

### Phase 4: Capability Visibility, Manual Override, And Minimal Control-Plane Plumbing
- Surface backend/capability state to users and support without redesigning the controller.
- Add the manual override escape hatch and keep support language precise.
- Risks: over-scoping controller work; hiding capability truth behind forced backends; noisy UX.
- Mitigations: keep the controller minimal, separate truth from override state, and follow the quiet-by-default visibility model.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Implement capability status reporting, support-family labels, and diagnostics/log surfaces | Completed |
| 4.2 | Add always-visible status and conditional warnings with minimal plugin/controller changes | Completed |
| 4.3 | Add visible manual override and end-to-end diagnostics/override round-trip coverage | Completed |

#### Stage 4.1 Detailed Plan
- Objective:
- Build the status/reporting layer that makes backend family, backend instance, classification, fallback reason, and helper state visible.
- Primary touch points:
- `overlay_client/backend/status.py`
- `overlay_client/setup_surface.py`
- `overlay_client/control_surface.py`
- `utils/collect_overlay_debug_linux.sh`
- `load.py`
- `overlay_client/tests/test_backend_status.py`
- `tests/test_overlay_config_payload.py`
- `tests/test_harness_backend_selection_wiring.py`
- Steps:
- Add pure status-report formatting helpers and derived report payload fields using the stable support-family labels plus specific backend instances.
- Push the same formatted truth into plugin-side shadow status payloads and client/plugin log lines without changing backend selection behavior.
- Extend the Linux debug collector to extract and print the latest backend-selection summary from overlay client logs so support does not need to read raw log lines.
- Acceptance criteria:
- Capability state is no longer hidden internal data.
- Support diagnostics can display family/instance/classification/fallback clearly.
- No selector or runtime behavior changes are introduced in this stage; only status/reporting surfaces change.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py tests/test_overlay_config_payload.py tests/test_harness_backend_selection_wiring.py -q`

#### Stage 4.2 Detailed Plan
- Objective:
- Add quiet-by-default UI visibility with minimal controller/prefs changes, without mislabeling plugin-side shadow status as client-final truth.
- Primary touch points:
- `overlay_client/backend/status.py`
- `load.py`
- `overlay_controller/services/plugin_bridge.py`
- `overlay_controller/overlay_controller.py`
- `overlay_plugin/preferences.py`
- `overlay_client/tests/test_backend_status.py`
- `overlay_controller/tests/test_plugin_bridge.py`
- `overlay_controller/tests/test_backend_status_title.py` (new)
- `tests/test_preferences_panel_controller_tab.py`
- `tests/test_harness_backend_status_roundtrip.py` (new)
- Steps:
- Extend the pure status helpers with user-facing summary and warning formatting that can explicitly label the current source as `plugin_hint` when only advisory shadow status is available.
- Add a minimal plugin runtime status endpoint plus controller bridge pass-through so prefs and controller can request backend status without re-running selection logic themselves.
- Surface compact status plus conditional warning text in the EDMC preferences panel, and keep the controller change minimal by updating only an always-visible status/title surface instead of restructuring Tk layouts.
- Keep the Tk controller structure intact; limit changes to status display and pass-through wiring.
- Acceptance criteria:
- The controller remains a stable boundary.
- Users can see backend family/classification without requiring debug logs.
- UI surfaces do not misrepresent plugin shadow status as client-authoritative runtime truth.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py overlay_controller/tests/test_plugin_bridge.py overlay_controller/tests/test_backend_status_title.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_status_roundtrip.py -q`

#### Stage 4.3 Detailed Plan
- Objective:
- Add the manual backend override escape hatch while keeping capability truth intact.
- Primary touch points:
- `overlay_client/backend/selector.py`
- `overlay_client/backend/status.py`
- `overlay_client/platform_context.py`
- `overlay_client/control_surface.py`
- `overlay_plugin/preferences.py`
- `overlay_client/client_config.py`
- `load.py`
- `overlay_client/tests/test_backend_selector.py`
- `overlay_client/tests/test_backend_status.py`
- `overlay_client/tests/test_platform_context.py`
- `overlay_client/tests/test_client_config.py` (new)
- `tests/test_preferences_panel_controller_tab.py`
- `tests/test_preferences_persistence.py`
- `tests/test_overlay_config_payload.py`
- `tests/test_harness_backend_override_roundtrip.py` (new)
- Steps:
- Add an explicit `Auto` plus relevant forced-backend choices in the preferences UI, with persistence through the existing EDMC-config plus `overlay_settings.json` shadow path.
- Carry the requested override through the existing bootstrap and live config surfaces (`overlay_settings.json` and `platform_context`) instead of introducing a second transport.
- Apply the override only in the selector path so backend choice still happens in one place, and keep the default `Auto` path behavior-equivalent to the current shipped behavior.
- Surface active override and invalid-override state in backend status/reporting so status, diagnostics, and warnings stay truthful.
- Acceptance criteria:
- Forced backends are visible in status/diagnostics.
- Invalid forced backends fail clearly instead of silently.
- `Auto` remains the default and preserves current behavior.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_platform_context.py overlay_client/tests/test_client_config.py tests/test_preferences_panel_controller_tab.py tests/test_preferences_persistence.py tests/test_overlay_config_payload.py tests/test_harness_backend_override_roundtrip.py -q`

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- Capability visibility and override behavior match the locked policies.
- Minimal controller changes are complete without expanding controller scope.

### Phase 5: Helper Boundary Foundation, Approval Flows, And Final Cleanup
- Add the minimal helper-facing foundation required by the architecture and finish cleanup/documentation work.
- Keep helper deployment explicit and user-approved; do not silently ship or enable helpers.
- Risks: overreaching into helper implementation details too early; creating an insecure local command channel; leaving old platform logic half-removed.
- Mitigations: limit this phase to helper-boundary foundation, missing-helper classification, approval plumbing, and final cleanup with strong tests.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Introduce `HelperIpcBackend` and a secured local-only helper boundary on the client side | Completed |
| 5.2 | Add helper-aware classification plus user-approved install/enable plumbing for helper-backed paths | Completed |
| 5.3 | Remove leftover distributed platform logic, archive superseded docs, and finalize verification hardening | Completed |

#### Stage 5.1 Detailed Plan
- Objective:
- Create the client-owned helper boundary and protocol constraints without turning the plugin into a runtime transport hub.
- Primary touch points:
- `overlay_client/backend/__init__.py`
- `overlay_client/backend/helper_ipc.py` (new)
- `overlay_client/backend/contracts.py`
- `overlay_client/tests/test_backend_contracts.py`
- `overlay_client/tests/test_helper_ipc_boundary.py` (new)
- Steps:
- Tighten the existing placeholder `HelperIpcBackend` contract just enough to carry helper identity metadata, without introducing live transport wiring in this stage.
- Define pure local-only helper boundary models covering endpoint shape, protocol version checks, schema validation, and fail-closed message parsing.
- Keep the helper surface minimal and helper-to-client only; defer actual socket/DBus startup and bundle hookup to later stages.
- Acceptance criteria:
- The helper boundary is narrow, local-only, and schema-validated.
- The plugin is not in the middle of runtime helper communication.
- No live runtime transport or helper installation behavior changes are introduced in this stage.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_helper_ipc_boundary.py -q`

#### Stage 5.2 Detailed Plan
- Objective:
- Make helper-backed paths first-class in selection/classification and prepare explicit approval/install flows without silently installing helpers.
- Primary touch points:
- `overlay_client/backend/selector.py`
- `overlay_client/backend/status.py`
- `overlay_client/backend/contracts.py`
- `scripts/install_linux.sh`
- `scripts/install_matrix.json`
- `overlay_client/tests/test_backend_selector.py`
- `tests/test_install_linux.py`
- `overlay_client/tests/test_backend_status.py`
- Steps:
- Add helper-aware selector/status metadata for GNOME and KWin without changing the default runtime path when helpers are absent; preserve conservative existing classifications for shipped environments.
- Populate explicit helper-state details so required missing helpers are visible in diagnostics, while optional helper paths do not create misleading warnings.
- Extend the compositor install matrix with helper metadata and add explicit installer approval recording/guidance for helper-backed environments, keeping helper installation or enablement optional and visible.
- Acceptance criteria:
- Missing helper state degrades cleanly and visibly.
- Helper install/enable remains explicit and user-approved.
- No live helper deployment is introduced in this stage; approval/guidance plumbing only.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py tests/test_install_linux.py -q`

#### Stage 5.3 Detailed Plan
- Objective:
- Remove leftover distributed platform logic, archive superseded docs, and finish the verification matrix for the new architecture.
- Primary touch points:
- `overlay_client/backend/consumers.py`
- `overlay_client/platform_integration.py`
- `overlay_client/window_tracking.py`
- `overlay_client/tests/test_backend_consumers.py`
- `overlay_client/tests/test_platform_controller_backend_status.py`
- `overlay_client/tests/test_window_tracking_bundle_routing.py`
- `docs/refactoring/backend_architecture_refactor_plan.md`
- `docs/archive/refactoring/client_refactor.md`
- `docs/archive/refactoring/load_refactory.md`
- `docs/archive/refactoring/compositor_aware_install.md`
- `docs/archive/refactoring/refactor-plan.md`
- `docs/archive/`
- Steps:
- Replace the remaining Linux no-status fallback branches in runtime consumers with a single compatibility helper that derives backend status through the pure probe/selector path, so runtime modules stop re-encoding platform selection locally.
- Keep auxiliary fallback behavior intact where removing it would change behavior, but make the fallback consume the same selector path instead of raw ad hoc branching.
- Archive superseded planning/refactor docs instead of deleting them.
- Run the full planned test matrix and record the remaining environment-specific validation gaps.
- Acceptance criteria:
- Secondary platform-selection branching is gone from runtime consumers; any remaining compatibility fallback goes through the shared selector path.
- Document history is preserved under `docs/archive/`.
- Final verification status is explicit for first-party and user-assisted environments.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_window_tracking_bundle_routing.py -q`
- `source .venv/bin/activate && python -m pytest -m harness -q`
- `source .venv/bin/activate && python -m pytest overlay_client/tests -q`
- `source .venv/bin/activate && PYQT_TESTS=1 python -m pytest overlay_client/tests -q`
- `make check`
- `make test`

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
- The architecture has a client-owned helper boundary, explicit helper-aware classification, and no leftover distributed backend-selection logic.
- Documentation and diagnostics reflect the new backend architecture and preserved compatibility model.

## Execution Log
- Plan created on 2026-04-02.
- Record one execution summary subsection per completed phase.
- Record exact test commands and outcomes for each completed phase.

### Phase 1 Execution Summary
- Stage `1.1` completed on 2026-04-02.
- Added a new pure `overlay_client.backend` package with immutable contract and status models:
  - `overlay_client/backend/__init__.py`
  - `overlay_client/backend/contracts.py`
  - `overlay_client/backend/status.py`
- Added `overlay_client/tests/test_backend_contracts.py` to lock the initial contract surface with headless unit coverage.
- Refined Stage `1.1` to keep runtime code untouched in this step; `platform_context.py`, `platform_integration.py`, and consumer wiring were intentionally left unchanged.
- Corrected the repo-local env setup path in this plan from `requirements-dev.txt` to `requirements/dev.txt`.
- Stage `1.2` completed on 2026-04-02.
- Added pure shadow-selector infrastructure without touching runtime consumers:
  - `overlay_client/backend/probe.py`
  - `overlay_client/backend/selector.py`
  - `overlay_client/tests/test_platform_probe.py`
  - `overlay_client/tests/test_backend_selector.py`
- Extended `PlatformProbeResult` to include `qt_platform_name`, because current client behavior already branches on the Qt platform plugin.
- Kept the selector conservative for already-working environments in shadow mode; stricter degraded classifications and runtime shadow-status plumbing remain deferred to Stage `1.3`.
- Stage `1.3` completed on 2026-04-02.
- Added pure payload serialization for backend descriptors, probe snapshots, helper state, and shadow selection status so runtime wiring can publish advisory selector metadata without driving consumers.
- Added advisory shadow selector plumbing in `load.py` by embedding `shadow_backend_status` inside the existing `platform_context` overlay-config payload.
- Added project-owned harness coverage in `tests/test_harness_backend_selection_wiring.py` proving the runtime publishes the shadow selector snapshot through the existing config payload path.
- Phase `1` completed with no runtime consumer cutover and no backend behavior change.

### Tests Run For Phase 1
- `python3 -m venv .venv`
- `.venv/bin/python -m pip install -r requirements/dev.txt`
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py -q`
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_platform_probe.py overlay_client/tests/test_backend_selector.py -q`
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_platform_probe.py overlay_client/tests/test_backend_selector.py tests/test_overlay_config_payload.py tests/test_harness_backend_selection_wiring.py -q`
- Result: pass (`21 passed`)

### Phase 2 Execution Summary
- Stage `2.1` completed on 2026-04-02.
- Added thin public factory helpers around the current shipped XCB/X11 integration and wmctrl tracker in:
  - `overlay_client/platform_integration.py`
  - `overlay_client/window_tracking.py`
- Added explicit X11-derived bundle modules without wiring runtime consumers to them yet:
  - `overlay_client/backend/bundles/__init__.py`
  - `overlay_client/backend/bundles/native_x11.py`
  - `overlay_client/backend/bundles/xwayland_compat.py`
- Added generic bundle consumer helpers in `overlay_client/backend/consumers.py`.
- Kept `native_x11` and `xwayland_compat` as separate bundle identities while intentionally reusing the same shipped XCB/wmctrl implementation underneath.
- Left `setup_surface.py` and active runtime selection untouched in this stage, so behavior remains on the old path until Stage `2.3`.
- Stage `2.2` completed on 2026-04-02.
- Restored `_WmctrlTracker._active_window_id()` as a class method and exposed public Wayland tracker factories in `overlay_client/window_tracking.py` so bundle code no longer relies on private tracker classes directly.
- Added explicit native Wayland bundle modules while preserving the current shipped implementation path underneath:
  - `overlay_client/backend/bundles/_wayland_common.py`
  - `overlay_client/backend/bundles/wayland_layer_shell_generic.py`
  - `overlay_client/backend/bundles/kwin_wayland.py`
  - `overlay_client/backend/bundles/gnome_shell_wayland.py`
  - `overlay_client/backend/bundles/hyprland.py`
  - `overlay_client/backend/bundles/sway_wayfire_wlroots.py`
- Widened `overlay_client/backend/consumers.py` so bundle discovery can truthfully return `None` for current helper-required or generic Wayland paths that still have no shipped tracker.
- Added Stage `2.2` unit coverage in:
  - `overlay_client/tests/test_backend_bundles_wayland.py`
  - `overlay_client/tests/test_backend_consumers.py`
- Kept runtime setup, follow-mode consumer wiring, and active backend selection on the old path in this stage; no runtime cutover happened.
- Stage `2.3` completed on 2026-04-02.
- Added legacy Linux bundle-resolution and bundle-policy helpers in `overlay_client/backend/consumers.py` so runtime consumers can resolve explicit backend identities without making the Phase `3` selector authoritative early.
- Routed `PlatformController` through bundle adapters and bundle-derived policy helpers in `overlay_client/platform_integration.py` for:
  - integration creation
  - platform labeling
  - native-Wayland detection
  - transient-parent policy
- Routed Linux tracker creation through the same legacy bundle resolver in `overlay_client/window_tracking.py`, preserving the current native-Wayland-first then XWayland/X11 fallback behavior.
- Updated follow/input call sites to use platform-controller policy instead of local Wayland checks:
  - `overlay_client/follow_surface.py`
  - `overlay_client/setup_surface.py`
- Added Stage `2.3` unit coverage in:
  - `overlay_client/tests/test_backend_consumers.py`
  - `overlay_client/tests/test_window_tracking_bundle_routing.py`
  - `overlay_client/tests/test_follow_surface_mixin.py`
- Phase `2` completed with bundle-backed consumer seams in place and no selector cutover yet.

### Tests Run For Phase 2
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_consumers.py -q`
- Result: pass (`8 passed`)
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_consumers.py -q`
- Result: pass (`17 passed`)
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_follow_surface_mixin.py -q`
- Result: pass (`19 passed`)

### Phase 3 Execution Summary
- Stage `3.1` completed on 2026-04-02.
- Kept `load.py` unchanged in this stage: plugin-side `shadow_backend_status` remains an advisory hint published through `OverlayConfig`, not the authoritative client decision.
- Added client-side backend-status helpers in `overlay_client/platform_context.py` so the client can derive a final non-shadow selector result from local runtime evidence first, using plugin platform context only as fallback hints or explicit overrides.
- Initialized client-owned final backend-selection state in `overlay_client/setup_surface.py` during startup.
- Updated `overlay_client/control_surface.py` so incoming platform-context payloads:
  - retain the plugin shadow status as a hint
  - recompute the client-owned final backend-selection result
  - log plugin/client mismatches explicitly
  - avoid introducing a new client-to-plugin protocol in this stage
- Added Stage `3.1` test coverage in:
  - `overlay_client/tests/test_platform_context.py`
  - `overlay_client/tests/test_control_surface_platform_context.py`
- Preserved current runtime behavior in this stage: the client now owns final backend-selection state, but runtime consumers still follow the pre-cutover execution path until Stage `3.2`.
- Stage `3.2` completed on 2026-04-02.
- Added selector-result-to-bundle helpers in `overlay_client/backend/consumers.py` so Linux runtime code can consume the client-owned backend selection without re-reading raw session/compositor context in each consumer.
- Updated `overlay_client/platform_integration.py` so `PlatformController` can be seeded with the client-owned backend status and rebuild its bundle-backed integration when the selected backend changes.
- Updated startup/runtime wiring so active runtime consumers use the selected backend status rather than legacy Linux bundle resolution:
  - `overlay_client/setup_surface.py`
  - `overlay_client/launcher.py`
  - `overlay_client/overlay_client.py`
  - `overlay_client/window_tracking.py`
  - `overlay_client/control_surface.py`
- Preserved current tracker fallback behavior by anchoring fallback bundle selection to the selected client status rather than to open-coded environment branching.
- Added Stage `3.2` unit coverage in:
  - `overlay_client/tests/test_backend_consumers.py`
  - `overlay_client/tests/test_platform_controller_backend_status.py`
  - `overlay_client/tests/test_window_tracking_bundle_routing.py`
  - `overlay_client/tests/test_control_surface_platform_context.py`
- Kept `load.py`, plugin lifecycle wiring, and controller surfaces unchanged in this stage; the cutover stayed client-only.
- Stage `3.3` completed on 2026-04-03.
- Tightened `overlay_client/backend/selector.py` so explicit fallback metadata is now part of the selector result instead of being implied only through selector notes.
- Preserved native-first, fallback-available policy in explicit selector output by:
  - reporting `xwayland_compat` as a named fallback from the compositor-specific native Wayland backend
  - reporting GNOME helper-missing fallback metadata without downgrading current shipped behavior
  - retaining conservative classification for downgrade-sensitive `xwayland_compat` paths while marking the preserved classification as review-required
- Extended `overlay_client/backend/status.py` so selection status payloads can surface review-guard metadata alongside fallback metadata.
- Added Stage `3.3` unit coverage in:
  - `overlay_client/tests/test_backend_selector.py`
  - `overlay_client/tests/test_backend_status.py`
  - `overlay_client/tests/test_platform_context.py`
  - `overlay_client/tests/test_backend_contracts.py`
- Kept this stage pure: no `load.py`, preferences, controller, or runtime-consumer wiring changes were required.
- Phase `3` completed with client-authoritative selection, runtime consumer cutover, explicit fallback metadata, and no secondary backend selection logic left in the active client path.

### Tests Run For Phase 3
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_platform_context.py overlay_client/tests/test_control_surface_platform_context.py tests/test_harness_backend_selection_wiring.py tests/test_harness_plugin_hooks_contract.py -q`
- Result: pass (`9 passed`)
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_control_surface_platform_context.py -q`
- Result: pass (`24 passed`)
- `make check`
- Result: pass (`ruff`, `mypy`, `PYQT_TESTS=1 python -m pytest`; `759 passed, 21 skipped`)
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_platform_context.py -q`
- Result: pass (`16 passed`)
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py -q`
- Result: pass (`5 passed`)
- `make check`
- Result: pass (`ruff`, `mypy`, `PYQT_TESTS=1 python -m pytest`; `762 passed, 21 skipped`)

### Phase 4 Execution Summary
- Stage `4.1` completed on 2026-04-03.
- Added derived backend status reporting helpers in `overlay_client/backend/status.py` so selection payloads now carry:
  - flattened family/instance/classification/fallback report fields
  - a compact parseable summary line for logs and support tooling
- Updated client-side backend-status logs in:
  - `overlay_client/setup_surface.py`
  - `overlay_client/control_surface.py`
  so the overlay client emits the same stable family/instance/classification/fallback truth in a collector-friendly format.
- Updated `load.py` so plugin-side shadow selector status is logged in the same compact format at launch/config publish time, while preserving the existing advisory shadow payload behavior.
- Extended `tests/test_overlay_config_payload.py` and `tests/test_harness_backend_selection_wiring.py` to prove shadow backend status payloads now include the derived report block.
- Extended `utils/collect_overlay_debug_linux.sh` so the Linux support collector extracts the latest backend-selection summary and mismatch state from overlay client logs and prints a dedicated backend section.
- Kept this stage reporting-only: no selector, runtime behavior, or manual-override behavior changed.
- Stage `4.2` completed on 2026-04-03.
- Extended the pure status helpers in `overlay_client/backend/status.py` with:
  - user-facing summary formatting
  - conditional warning formatting
  - window-title formatting
  - explicit `source` labeling so `shadow_mode=True` is surfaced as `plugin_hint` instead of being misrepresented as client-final truth
- Added a minimal plugin runtime backend-status endpoint in `load.py` and routed it through the existing CLI surface so UI consumers can request backend visibility without re-running selection logic.
- Added controller bridge support in `overlay_controller/services/plugin_bridge.py` for backend-status requests.
- Kept the controller structure intact by updating only the always-visible window title in `overlay_controller/overlay_controller.py`; no controller layout restructuring or secondary selector logic was introduced.
- Added quiet-by-default backend visibility to the EDMC preferences panel in `overlay_plugin/preferences.py`:
  - always-visible backend summary
  - conditional warning line for degraded/fallback/helper-missing/review-required states
  - reuse of the existing background poll loop instead of introducing a second Tk timer
- Added Stage `4.2` coverage in:
  - `overlay_client/tests/test_backend_status.py`
  - `overlay_controller/tests/test_plugin_bridge.py`
  - `overlay_controller/tests/test_backend_status_title.py`
  - `tests/test_preferences_panel_controller_tab.py`
  - `tests/test_harness_backend_status_roundtrip.py`
- Kept this stage visibility-only: no backend selection behavior, fallback behavior, or manual-override behavior changed.
- Stage `4.3` completed on 2026-04-03.
- Added manual override support to the pure selector and status layers in:
  - `overlay_client/backend/selector.py`
  - `overlay_client/backend/status.py`
  so the selected backend can be forced explicitly, invalid overrides are surfaced clearly, and capability truth remains separate from override state.
- Completed the override transport on existing config paths without introducing a second selection channel:
  - `overlay_client/client_config.py` now reads `manual_backend_override` from `overlay_settings.json`
  - `overlay_client/platform_context.py` and `overlay_client/control_surface.py` now carry the override through client bootstrap and runtime platform-context updates
  - `load.py` now persists the preference, publishes it in `platform_context`, and applies it to the plugin-side shadow selector status
- Added a visible manual override control to the EDMC preferences panel in `overlay_plugin/preferences.py`:
  - explicit `Auto` option
  - platform-relevant backend choices
  - persistence through EDMC config plus `overlay_settings.json`
  - status text for both active and cleared overrides
- Kept override behavior bounded to the selector path only:
  - `Auto` still preserves the shipped behavior
  - invalid override tokens no longer silently disappear
  - status/diagnostics now report both active overrides and invalid override errors
- Added Stage `4.3` coverage in:
  - `overlay_client/tests/test_backend_selector.py`
  - `overlay_client/tests/test_backend_status.py`
  - `overlay_client/tests/test_platform_context.py`
  - `overlay_client/tests/test_client_config.py`
  - `tests/test_preferences_panel_controller_tab.py`
  - `tests/test_preferences_persistence.py`
  - `tests/test_overlay_config_payload.py`
  - `tests/test_harness_backend_override_roundtrip.py`
- Phase `4` is now complete: capability visibility, quiet warnings, and visible override plumbing are all in place without expanding controller scope or introducing a second backend selector.

### Tests Run For Phase 4
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py overlay_client/tests/test_control_surface_platform_context.py tests/test_overlay_config_payload.py tests/test_harness_backend_selection_wiring.py -q`
- Result: pass (`9 passed`)
- `make check`
- Result: pass (`ruff`, `mypy`, `PYQT_TESTS=1 python -m pytest`; `763 passed, 21 skipped`)
- `bash -n utils/collect_overlay_debug_linux.sh`
- Result: pass
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py overlay_controller/tests/test_plugin_bridge.py overlay_controller/tests/test_backend_status_title.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_status_roundtrip.py -q`
- Result: pass (`27 passed`)
- `make check`
- Result: pass (`ruff`, `mypy`, `PYQT_TESTS=1 python -m pytest`; `771 passed, 21 skipped`)
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_platform_context.py overlay_client/tests/test_client_config.py tests/test_preferences_panel_controller_tab.py tests/test_preferences_persistence.py tests/test_overlay_config_payload.py tests/test_harness_backend_override_roundtrip.py -q`
- Result: pass (`50 passed`)
- `make check`
- Result: pass (`ruff`, `mypy`, `PYQT_TESTS=1 python -m pytest`; `785 passed, 21 skipped`)

### Phase 5 Execution Summary
- Stage `5.1` completed on 2026-04-03.
- Tightened the existing placeholder `HelperIpcBackend` contract in `overlay_client/backend/contracts.py` so helper-backed components now expose explicit helper identity metadata in addition to backend identity.
- Added a new pure helper-boundary module in `overlay_client/backend/helper_ipc.py` with:
  - local-only transport families (`unix_socket`, `session_dbus`)
  - validated endpoint configuration models
  - client-owned helper boundary configuration
  - fail-closed helper message parsing with protocol-version, session-token, helper-kind, and allowed-event checks
- Re-exported the new helper-boundary types and validators from `overlay_client/backend/__init__.py` so later stages can consume the boundary through the existing backend package.
- Added Stage `5.1` contract and boundary coverage in:
  - `overlay_client/tests/test_backend_contracts.py`
  - `overlay_client/tests/test_helper_ipc_boundary.py`
- Kept this stage pure and non-invasive:
  - no live socket or DBus transport was started
  - no helper installation flow changed
  - no plugin/runtime transport hub was introduced
- Stage `5.2` completed on 2026-04-03.
- Made helper-aware selector/status behavior more explicit without changing the default shipped runtime path when helpers are absent:
  - `overlay_client/backend/selector.py` now treats GNOME helper state as required and KWin helper state as an explicit optional helper-backed path when a helper is actually present in the probe.
  - `overlay_client/backend/status.py` now distinguishes required missing helpers from optional missing helpers so diagnostics can carry helper truth without creating misleading warnings for optional future helper paths.
  - `overlay_client/backend/contracts.py` now serializes helper requirement state through `HelperCapabilityState`.
- Extended the Linux compositor install matrix in `scripts/install_matrix.json` with helper metadata for:
  - `gnome-shell`
  - `kwin-wayland`
- Added explicit helper approval/guidance plumbing in `scripts/install_linux.sh`:
  - helper metadata now flows out of `matrix_helper compositor-match`
  - installer records an explicit helper approval decision in `overlay_client/helper_approval.json`
  - helper install/enable remains manual and visible; no helper is installed automatically
- Added Stage `5.2` coverage in:
  - `overlay_client/tests/test_backend_selector.py`
  - `overlay_client/tests/test_backend_status.py`
  - `tests/test_install_linux.py`
- Kept this stage conservative:
  - GNOME still uses the existing conservative shipped classification path
  - KWin helper support is first-class only when a helper is explicitly present in the probe
  - no live helper deployment was introduced
- Stage `5.3` completed on 2026-04-03.
- Removed the last duplicated Linux runtime selection branches from active consumers by centralizing no-status fallback derivation in `overlay_client/backend/consumers.py`:
  - `derive_linux_backend_status(...)` now builds a Linux fallback status through the shared pure probe/selector path
  - `ensure_linux_backend_status(...)` lets runtime consumers keep compatibility fallback behavior without re-encoding raw session/compositor branching locally
- Updated active runtime consumers to use the shared compatibility helper instead of local ad hoc selection:
  - `overlay_client/platform_integration.py`
  - `overlay_client/window_tracking.py`
- Updated Stage `5.3` coverage in:
  - `overlay_client/tests/test_backend_consumers.py`
  - `overlay_client/tests/test_platform_controller_backend_status.py`
  - `overlay_client/tests/test_window_tracking_bundle_routing.py`
- Archived superseded refactor/architecture planning docs under `docs/archive/refactoring/` instead of deleting them:
  - `client_refactor.md`
  - `load_refactory.md`
  - `compositor_aware_install.md`
  - `refactor-plan.md`
- Updated active refactoring notes that still referenced the archived client plan:
  - `docs/refactoring/pref_refactor.md`
  - `docs/refactoring/overlay_client_performance.md`
- Final verification status for the backend architecture is now explicit:
  - automated verification matrix passed
  - first-party manual validation coverage remains `windows_desktop`, `gnome_x11`, and `gnome_wayland`
  - user-assisted validation coverage remains `fedora / kde_wayland`
  - remaining gap: no first-party manual validation yet for wlroots/Hyprland/COSMIC/gamescope paths or actual installed helper-backed GNOME/KWin flows
- Phase `5` is now complete: the helper boundary exists, helper-aware approval/classification is in place, distributed runtime backend selection logic has been collapsed behind the shared selector path, and superseded planning history has been archived rather than deleted.

### Tests Run For Phase 5
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_helper_ipc_boundary.py -q`
- Result: pass (`13 passed`)
- `make check`
- Result: pass (`ruff`, `mypy`, `PYQT_TESTS=1 python -m pytest`; `793 passed, 21 skipped`)
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py tests/test_install_linux.py -q`
- Result: pass (`32 passed`)
- `make check`
- Result: pass (`ruff`, `mypy`, `PYQT_TESTS=1 python -m pytest`; `797 passed, 21 skipped`)
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_window_tracking_bundle_routing.py -q`
- Result: pass (`23 passed`)
- `source .venv/bin/activate && python -m pytest -m harness -q`
- Result: pass (`28 passed, 6 skipped, 768 deselected`)
- `source .venv/bin/activate && python -m pytest overlay_client/tests -q`
- Result: pass (`301 passed, 18 skipped`)
- `source .venv/bin/activate && PYQT_TESTS=1 python -m pytest overlay_client/tests -q`
- Result: pass (`336 passed`)
- `make check`
- Result: pass (`ruff`, `mypy`, `PYQT_TESTS=1 python -m pytest`; `798 passed, 21 skipped`)
- `make test`
- Result: pass (`798 passed, 21 skipped`)

## Outstanding follow-up items
- Don't put the backend info on the Overlay controller title bar. Let's leave it off for now. 
- Backend choice shown in preferences is from the plugin suggestion, not the client determination. I want to expose client-authoritative backend status (source=client_runtime) to plugin preferences via the existing plugin↔client socket path, with current plugin shadow status (source=plugin_hint) retained as fallback and explicitly labeled advisory.
- Add backend choice to the test logo and debug overlay metrics
