## Goal: Finish backend-architecture cleanup by removing remaining runtime platform-policy leakage outside `overlay_client/backend`

This follow-up plan tracks the cleanup work left after `docs/refactoring/fix219_backend_architecture_refactor_plan.md` completed the selector cutover, visibility plumbing, and helper-boundary foundation.
The purpose of this plan is narrower than the original refactor plan: preserve current behavior while moving the remaining runtime platform/compositor specifics behind explicit backend-owned boundaries and documenting which non-backend boundaries are intentionally retained.
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
- Track progress with per-phase tables of stages (stage #, description, status). Mark each stage as completed when done; when all stages in a phase are complete, flip the phase status to `Completed`. Number stages as `<phase>.<stage>` (for example, `1.1`, `1.2`) to keep ordering clear.
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
| Backend-owned presentation/input extraction | KWin/GNOME/wlroots/Hyprland/X11 behavior remains behavior-equivalent while ownership moves behind backend bundles | Unit | Runtime policy moves should be proven through bundle-facing adapters without EDMC lifecycle noise | `overlay_client/tests/test_backend_bundles_x11.py`, `overlay_client/tests/test_backend_bundles_wayland.py`, `overlay_client/tests/test_backend_consumers.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_consumers.py -q` |
| Tracker ownership cleanup | Tracker selection stays status-driven; fallback remains unchanged; compositor-specific tracker behavior remains intact | Mixed (Unit + Harness) | Tracker classes are runtime-heavy, but status/config handoff must still be proven through project-owned wiring | `overlay_client/tests/test_window_tracking_bundle_routing.py`, `overlay_client/tests/test_backend_consumers.py`, `tests/test_harness_backend_selection_wiring.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_backend_consumers.py tests/test_harness_backend_selection_wiring.py -q` |
| `force_xwayland` retirement and explicit XWayland fallback | `Auto` must not silently launch XWayland, while `xwayland_compat` remains available only as an explicit manual fallback/override path | Mixed (Unit + Harness) | This changes launch-time Qt platform wiring, payload/config transport, and persisted preference semantics while preserving the existing XWayland compatibility backend | `overlay_client/tests/test_backend_selector.py`, `overlay_client/tests/test_platform_context.py`, `overlay_client/tests/test_client_config.py`, `tests/test_overlay_config_payload.py`, `tests/test_preferences_persistence.py`, `tests/test_harness_backend_override_roundtrip.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_platform_context.py overlay_client/tests/test_client_config.py tests/test_overlay_config_payload.py tests/test_preferences_persistence.py tests/test_harness_backend_override_roundtrip.py -q` |
| Override-choice metadata centralization | Preferences/controller stop reconstructing backend choices from compositor branches and instead consume backend metadata | Mixed (Unit + Harness) | Choice derivation can be pure, but prefs/controller round-trip is integration-sensitive | `overlay_client/tests/test_backend_status.py`, `tests/test_preferences_panel_controller_tab.py`, `tests/test_harness_backend_override_roundtrip.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_override_roundtrip.py -q` |
| Client-runtime status surfacing and debug visibility | Preferences should show client-authoritative backend status when available, keep `plugin_hint` as labeled fallback, omit backend status from the controller title bar, and surface backend choice in debug/test-overlay visuals | Mixed (Unit + Harness) | Status transport/formatting is integration-sensitive across plugin, client, prefs, controller, and debug-overlay rendering | `overlay_client/tests/test_backend_status.py`, `tests/test_preferences_panel_controller_tab.py`, `tests/test_harness_backend_status_roundtrip.py`, `overlay_controller/tests/test_backend_status_title.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_status_roundtrip.py overlay_controller/tests/test_backend_status_title.py -q` |
| Residual boundary audit and shrink-wrap | Remaining OS-specific checks outside backend are either removed or explicitly documented as generic/windowing boundaries rather than backend policy | Unit | This is mostly refactor-proofing and should be locked with narrow tests around retained generic behavior | `overlay_client/tests/test_follow_surface_mixin.py`, `overlay_client/tests/test_platform_controller_backend_status.py`, `overlay_client/tests/test_control_surface_platform_context.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_control_surface_platform_context.py -q` |

## Test Acceptance Gates (Required)
- [ ] Unit tests added/updated for extracted pure logic.
- [ ] Harness tests added/updated for lifecycle/wiring surfaces.
- [ ] Commands executed and outcomes recorded.
- [ ] Skips/failures documented with reason and follow-up action.

## Scope
- In scope:
- move remaining runtime presentation/input policy ownership for X11/XWayland/native Wayland out of shared legacy modules and into backend-owned modules or backend-private implementations
- move compositor-specific tracker implementations behind backend-owned discovery surfaces instead of leaving them as general-purpose runtime modules
- express the remaining cleanup in terms of the research-contract model (`PresentationBackend`, `InputPolicyBackend`, `TargetDiscoveryBackend`, `HelperIpcBackend`) rather than treating file moves alone as success
- stop preferences/control-plane code from reconstructing backend policy from raw OS/session/compositor data when backend metadata can be consumed directly
- retire the separate `force_xwayland` setting and keep `xwayland_compat` only as an explicit manual fallback/override (restart required) instead of a silent `Auto` fallback
- expose client-authoritative backend status to plugin preferences through the existing plugin/client socket path while retaining `plugin_hint` as a clearly labeled fallback
- remove backend status from the Overlay Controller title bar for now
- surface backend choice in the test logo and debug overlay metrics in the lower-left debug/test-overlay area
- document and preserve the non-backend boundaries that are still intentional, such as plugin launch/orchestration and installer/deployment logic
- Out of scope:
- redesigning or replacing the Tk controller
- changing backend selection authority away from the client
- removing `plugin_hint` as an advisory launch-time surface
- expanding or validating Linux `standalone_mode` behavior as part of `fix219`; preserve current Windows standalone behavior and defer Linux standalone work to a separate post-`fix219` feature track
- removing installer compositor profiles or Flatpak launch handling from `scripts/install_linux.sh`
- silently downgrading any currently working environment
- editing immutable vendored harness files (`tests/harness.py`, `tests/edmc/**`) as part of normal refactor work

## Current Audit Findings
- Remaining runtime platform-policy leakage exists in `overlay_client/platform_integration.py`, where native Wayland compositor-specific presentation/input behavior still lives outside `overlay_client/backend`.
- Remaining runtime platform-policy leakage exists in `overlay_client/window_tracking.py`, where X11/KWin/Hyprland/wlroots tracker implementations still live outside `overlay_client/backend`.
- Preferences UI still reconstructs backend override choices from raw `operating_system` / `session_type` / `compositor` data instead of consuming backend-owned metadata.
- The separate `force_xwayland` setting still exists as a launch-time/persistence knob instead of expressing XWayland use as an explicit backend fallback or override.
- Preferences backend status currently reflects plugin-side shadow status instead of client-authoritative runtime status.
- Overlay controller title-bar status is currently used as a backend visibility surface, but that surface should be removed for now.
- Debug/test-overlay surfaces do not yet expose the chosen backend as part of the lower-left diagnostic/test-logo metrics area.
- Plugin launch/orchestration logic in `load.py` still contains OS/compositor detection, but that is currently an intentional boundary because the plugin owns process launch, advisory context, and Flatpak/env shaping.
- Installer compositor logic in `scripts/install_linux.sh` / `scripts/install_matrix.json` remains an intentional deployment boundary rather than a runtime backend-architecture defect.

## Settings Impact Classification
- Backend-critical settings/surfaces:
  - `manual_backend_override`: explicit backend/fallback choice surface; this is the intended long-term user-facing backend control.
  - `force_xwayland`: currently still backend-critical because it changes launch-time Qt platform selection; tracked for retirement in Stage `3.2`.
  - `QT_QPA_PLATFORM` and related env override paths: not normal user settings, but still backend-critical because they can override startup transport/backend shape and must be documented or constrained explicitly.
- Visibility-only settings:
  - `show_debug_overlay`: relevant because backend choice/status will be surfaced in the debug/test-overlay diagnostics.
  - `debug_overlay_corner`: only affects where the debug/test-overlay diagnostics render.
  - `title_bar_enabled` / `title_bar_height`: relevant only because backend status is being removed from the controller title bar while title-bar compensation remains a separate runtime/UI feature.
- Not part of backend-architecture cleanup unless a later stage explicitly broadens scope:
  - `force_render`: visibility/focus behavior only, not backend choice.
  - `standalone_mode`: runtime mode/UI behavior, not backend selection. Preserve the current Windows behavior during `fix219`; defer Linux standalone behavior/support and validation until after this cleanup plan, and treat that later work as a separate runtime/presentation feature with backend/compositor-specific support expectations rather than as backend-selection cleanup.
  - `physical_clamp_enabled` / `physical_clamp_overrides`: shared geometry-normalization escape hatches, not backend ownership or backend choice. Preserve current opt-in behavior during `fix219`; require backend/tracker cleanup to keep feeding the shared normalizer correctly; defer any deeper coordinate-space redesign to a separate post-`fix219` geometry/follow refactor.
  - opacity, font bounds/steps, gridlines, payload cycling, payload logging, connection-status display, controller launch command, and other presentation/debug preferences.

## Current Gaps And Planned Closure

| Gap | Current State | Why It Is Still A Gap | Planned Closure |
| --- | --- | --- | --- |
| Preferences backend status is not client-authoritative | Plugin `backend_status` CLI still returns plugin shadow status, so prefs currently surface `source=plugin_hint` rather than `source=client_runtime` | User-visible backend truth is still advisory instead of authoritative, and stale/unavailable-client behavior is not explicitly modeled yet | Stage `3.1`: expose client-runtime backend status through the existing plugin/client socket path, keep `plugin_hint` only as labeled fallback, and define unavailable/stale-client behavior |
| `force_xwayland` still exists as a separate setting instead of an explicit backend fallback | Launch-time Qt platform choice still depends on a dedicated `force_xwayland` preference/env path, even though `xwayland_compat` already exists as a named backend | This duplicates backend intent with a separate transport knob and makes XWayland use look like a mode flag rather than an explicit backend/fallback choice | Stage `3.2`: retire the user-facing `force_xwayland` setting, migrate existing persisted values to explicit `xwayland_compat` override semantics where needed, and derive startup Qt platform from backend/override intent instead of a separate boolean |
| Overlay Controller title bar still shows backend status | Controller polls backend status and formats it into the window title | This is no longer the desired visibility surface and creates redundant/noisy status presentation | Stage `3.4`: remove backend-title formatting and leave the controller on its base title |
| Debug/test-overlay diagnostics do not show backend choice | The lower-left debug/test-overlay panel renders monitor, geometry, scaling, and settings data, but not backend identity | There is no client-side visual diagnostic surface showing the chosen backend once the controller title-bar surface is removed | Stage `3.4`: add backend choice to the lower-left debug/test-overlay metrics/test-logo area |
| Preferences still derive override choices from raw probe fields | `_backend_override_choices_for_status(...)` still branches on `operating_system`, `session_type`, and `compositor` | Backend policy is still reconstructed in UI code instead of consumed from backend-owned metadata | Stage `3.3`: centralize backend-owned override-choice metadata and have prefs consume it directly |
| Native Wayland presentation/input policy still lives outside backend | `overlay_client/platform_integration.py` still owns compositor-specific Wayland click-through/presentation behavior | Runtime compositor policy is still split across a shared legacy module instead of bundle-owned code | Stages `1.2` and `1.3`: move native Wayland presentation/input ownership into backend-owned modules and reduce `platform_integration.py` to a generic shim |
| Tracker ownership still lives outside backend | `overlay_client/window_tracking.py` still contains X11/KWin/Hyprland/wlroots tracker implementations | Backend-specific target-discovery behavior is still physically and logically outside the backend ownership boundary | Stages `2.2` and `2.3`: move tracker ownership behind backend-owned discovery modules and reduce `window_tracking.py` to a generic entrypoint |
| Residual OS-specific guards outside backend have not been fully audited | Generic runtime modules still contain some `sys.platform` / Wayland checks whose role has not been fully reclassified | Without a final audit, backend policy can remain hidden inside generic runtime code even after the major ownership moves are done | Stage `3.5`: classify remaining guards as either legitimate generic windowing logic or leaked backend policy, then remove or redirect the leaked cases |
| Boundary/archive cleanup is not fully consolidated yet | Some notes still rely on readers finding the follow-up plan rather than seeing boundary-retention and completion limits stated everywhere they matter | Future readers may still overread the completed refactor plan unless retained boundaries and deferrals are explicitly archived or annotated | Stage `3.6`: update/refine the refactor docs so retained boundaries, intentional exceptions, and follow-up ownership limits are explicit wherever completion is summarized |
| Real-environment validation remains incomplete for deferred/non-closure paths | Additional wlroots, Hyprland, COSMIC, gamescope, and helper-backed Wayland runs may still lack testers even after the minimum `fix219` closure matrix is validated | These paths can remain deferred, but signoff must not imply validated support for them without recorded environment evidence | Stage `4.1`: validate the minimum closure matrix, record any extra runs that are available, and explicitly defer/remove implied support claims for any still-unvalidated paths before signoff |
| Post-refactor EDMC compliance pass is not yet recorded | The docs do not currently record a final compliance review for plugin API usage, logging, threading, and prefs/config handling after the refactor | Release readiness is incomplete until compliance review evidence is explicit | Stage `4.2`: run and record the EDMC compliance pass, then capture any required follow-up fixes or explicit exceptions |

## Cross-Phase Decision Gates
- `DG-1`: Resolve the backend-ownership vs physical file-move policy before Stage `1.2` or Stage `2.2` begins.
- Decision: for `fix219`, backend ownership is contract/factory ownership first, not physical file location first.
- Constraint: this only counts when backend ownership is discoverable from backend-facing APIs, import surfaces, and tests.
- Discoverability requirements:
  - a maintainer can find the owning backend entrypoint from the bundle/factory layer without hunting through unrelated runtime modules
  - non-backend modules do not instantiate backend-specific implementations directly
  - any legacy implementation file that remains outside `overlay_client/backend` is reachable only through backend-owned facades/factories
  - tests prove routing/ownership from backend bundle/contract to the retained implementation
  - if a backend-private implementation file remains outside `overlay_client/backend`, its temporary ownership is documented clearly enough that maintainers will not mistake it for generic runtime code
- Physical file moves remain preferred when they are the smallest reversible way to make ownership unambiguous or to stop continued policy leakage.
- Record the decision and any retained ambiguous file locations in the `Execution Log` before any stage that would otherwise move or retain legacy implementation files ambiguously.

## Current Touch Points
- Code:
- `overlay_client/backend/bundles/*.py` (target ownership location for runtime presentation/input/discovery behavior)
- `overlay_client/backend/consumers.py` (bundle resolution and bundle-facing consumer helpers)
- `overlay_client/platform_integration.py` (current shared integration logic still holding native Wayland compositor branches)
- `overlay_client/window_tracking.py` (current shared tracker implementations and Linux fallback entrypoint)
- `overlay_client/follow_surface.py` (generic follow/runtime logic that still contains some Linux-specific checks)
- `overlay_client/interaction_controller.py` (generic click-through/runtime logic that still contains some Linux/Wayland checks)
- `overlay_client/overlay_client.py` (legacy `_is_wayland()` helper currently tied to Qt platform name)
- `overlay_client/debug_cycle_overlay.py` (debug metrics/test-logo rendering surface)
- `overlay_client/render_surface.py` (debug overlay paint hookup)
- `overlay_client/client_config.py` (bootstrap settings still carrying `force_xwayland`)
- `overlay_plugin/preferences.py` (backend override choice derivation and backend status consumption)
- `overlay_plugin/overlay_config_payload.py` (overlay config payload fields still carrying `force_xwayland`)
- `overlay_client/platform_context.py` (client-authoritative selector entrypoint; retain as authoritative boundary while shrinking external policy leakage)
- `load.py` (retain as plugin launch/orchestration boundary; update only if follow-up stages need richer backend metadata transport)
- `overlay_controller/overlay_controller.py` (currently uses backend status in the controller window title)
- `scripts/install_linux.sh` and `scripts/install_matrix.json` (retain as deployment boundary; may be referenced in documentation/decision notes only)
- Tests:
- `overlay_client/tests/test_backend_bundles_x11.py`
- `overlay_client/tests/test_backend_bundles_wayland.py`
- `overlay_client/tests/test_backend_consumers.py`
- `overlay_client/tests/test_window_tracking_bundle_routing.py`
- `overlay_client/tests/test_follow_surface_mixin.py`
- `overlay_client/tests/test_platform_controller_backend_status.py`
- `overlay_client/tests/test_control_surface_platform_context.py`
- `tests/test_preferences_panel_controller_tab.py`
- `tests/test_harness_backend_selection_wiring.py`
- `tests/test_harness_backend_override_roundtrip.py`
- `tests/test_harness_backend_status_roundtrip.py`
- `overlay_controller/tests/test_backend_status_title.py`
- Docs/notes:
- `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- `docs/refactoring/fix219_cross_platform_overlay_architecture_research.md`
- `docs/refactoring/_template.md`

## Open Questions
- None currently. `DG-1` resolves the backend-ownership vs physical file-move policy for this follow-up.

## Decisions (Locked)
- The original backend-architecture plan remains the authority for selector, classification, fallback, helper, and visibility policy.
- The client remains the final authority for backend selection; this follow-up must not reintroduce plugin-side authority.
- `load.py` launch-time OS/compositor detection, `plugin_hint`, Flatpak launch handling, and advisory `platform_context` remain intentional control-plane boundaries unless a later decision supersedes them explicitly.
- Installer compositor detection, package selection, helper guidance, and approval recording remain intentional deployment boundaries and are not runtime backend leakage by themselves.
- Runtime presentation, input-policy, and target-discovery behavior should be backend-owned; shared runtime modules may remain only as thin generic shims after cleanup.
- This follow-up explicitly inherits the research contract model: `PlatformProbe` remains the client-authoritative probe boundary, Phase `1` must converge on backend-owned `PresentationBackend` and `InputPolicyBackend` ownership, and Phase `2` must converge on backend-owned `TargetDiscoveryBackend` ownership even if some implementation files move later in smaller reversible steps.
- Helper-backed compositor paths remain part of the intended architecture through explicit helper-boundary / `HelperIpcBackend` ownership; for `fix219`, this plan preserves those helper boundaries, helper-backed classification, missing-helper behavior, approval boundaries, and client-owned runtime helper communication expectations without expanding scope into new helper-side implementation work unless a current path breaks and forces it.
- Preferences/controller surfaces should consume backend-owned metadata where possible instead of reproducing compositor-selection policy locally.
- The separate `force_xwayland` setting should be retired as a user-facing control; `xwayland_compat` should remain available only as an explicit backend fallback/override (restart required), and `Auto` must not silently launch `QT_QPA_PLATFORM=xcb`.
- Explicit manual backend override authority is retained as the user-facing override surface over `Auto` within startup-transport constraints; this follow-up must not remove, silently weaken, or bypass that override path.
- Backend override selection is made in plugin preferences. When a selected override changes Qt startup transport, the preference change is saved immediately but surfaced in the preferences status area as pending until restart. Preferences must show that the current runtime backend remains unchanged until the overlay client is explicitly restarted, and must not imply that the backend switch has already applied live. The existing `Restart Overlay Client` action should remain the explicit apply path for restart-required backend changes.
- Plugin preferences should prefer client-authoritative backend status (`source=client_runtime`) via the existing plugin/client socket path when available; `plugin_hint` should remain only as a fallback and must be labeled advisory.
- The plugin/client backend-status contract should use request/response over the existing local socket path, treat fresh `client_runtime` as authoritative, fall back to labeled advisory `plugin_hint` when runtime status is unavailable or stale, and never allow `plugin_hint` to override runtime truth.
- Backend override-choice metadata must be backend-owned. `overlay_client/backend/contracts.py` may define the stable metadata type, but the concrete override-option data and availability rules must live in backend registry metadata rather than in `status.py` or preferences-specific OS/compositor mapping code. `status.py` may format or expose that metadata for diagnostics/UI, but it must not become the source of backend override policy. Preferences must consume the backend-owned metadata rather than reconstructing valid choices locally.
- Backend status should not appear in the Overlay Controller title bar for now.
- Backend choice should be visible in debug/test-overlay diagnostics, specifically in the lower-left debug/test-logo metrics area.
- `standalone_mode` remains a runtime/presentation feature rather than a backend-selection control for the purposes of `fix219`; keep the current Windows behavior unchanged in this plan and defer Linux standalone behavior/support to a separate post-`fix219` track.
- `physical_clamp_enabled` / `physical_clamp_overrides` remain shared, opt-in geometry-normalization escape hatches for `fix219`; preserve the current behavior while backend/tracker ownership moves, and do not absorb clamp policy into backend selection or per-backend policy.
- Capability classification and support-tier policy from the architecture research remain authoritative for this plan; Phase `4` must record final claimed environment classifications (`true_overlay`, `degraded_overlay`, `unsupported`) and concrete reasons rather than only pass/fail validation notes.
- Final environment classification must be based on recorded environment evidence plus selector/status coverage; `true_overlay` requires demonstrated full claimed behavior with no material unresolved limitation, `degraded_overlay` requires demonstrated partial behavior with an explicit weakened guarantee and concrete reason, `unsupported` requires recorded evidence that the required support bar is not met or not implemented, and unvalidated environments must remain deferred rather than being silently classified.
- The minimum real-environment closure matrix for `fix219` is Windows baseline, `native_x11`, explicit `xwayland_compat`, and one recorded KWin Wayland run. wlroots/Hyprland/COSMIC/gamescope and helper-backed Wayland paths may remain deferred if testers are unavailable, but they must not remain implied support claims at signoff without recorded validation.
- Windows is not broadened as an implementation target in this follow-up, but no stage may introduce Linux-specific shortcuts that would block the eventual cross-platform contract model described in the architecture research.
- Deeper Windows backend-contract cleanup remains part of the overall architecture direction and is deferred to a dedicated post-`fix219` plan; signoff for this follow-up must not imply that Windows contract-model work is complete.
- For `fix219`, Phase `1` may land on a bundle-owned combined presentation/input adapter rather than forcing separate public `PresentationBackend` and `InputPolicyBackend` objects per bundle immediately, provided that ownership is explicit and the design does not block a later split in a subsequent architecture redesign phase.
- Generic OS/windowing guards may remain outside backend only when they are mechanical compatibility or API-availability checks that do not select a backend, encode compositor/backend policy, instantiate backend-specific implementations, or recreate fallback/support/override logic. Any branch outside backend that maps raw platform/session/compositor state to tracking, presentation, input, fallback, or override behavior remains backend-policy leakage and must be removed or pushed behind backend-owned contracts.

## Architecture Alignment Requirements
- `PlatformProbe`
  - Remains the client-authoritative probe boundary. No follow-up stage may reintroduce split-brain platform selection between plugin and client.
- `PresentationBackend` + `InputPolicyBackend`
  - Phase `1` is complete only when presentation/input ownership is backend-owned in contract terms, not merely when files move.
  - For `fix219`, a bundle-owned combined adapter is acceptable as the landing shape, but later architecture work may still split presentation and input policy into cleaner public contracts when reuse and lifecycle boundaries justify it.
- `TargetDiscoveryBackend`
  - Phase `2` is complete only when tracker/discovery ownership is backend-owned in contract terms, not merely when tracker classes move.
  - For `fix219`, keep the runtime discovery contract minimal (tracked geometry/state plus any identity token actually needed for reacquire/stability), but preserve a separate structured diagnostics surface rich enough for multi-monitor / mixed-DPI / fractional-scaling troubleshooting.
- `HelperIpcBackend`
  - Helper-backed paths must stay explicit, user-approved, and architecture-visible. Deferred helper work must remain documented as such rather than collapsing back into hidden compositor branches.
  - For `fix219`, preserving the helper boundary is sufficient; new helper-side implementation work is deferred unless required to keep an already-claimed path functioning.
- Capability classification and visibility
  - Phase `3` and Phase `4` must preserve the architecture policy that backend/status surfaces report chosen backend, source of truth, and any degraded/fallback reason in a way support can inspect.
  - Multi-monitor / DPR troubleshooting must remain supported after the cleanup through logs, debug-overlay fields, or collected diagnostics; richer debug metadata must not be forced into the core runtime `TargetDiscoveryBackend` contract just to preserve supportability.
- Non-backend boundaries
  - `standalone_mode`, `physical_clamp_*`, plugin launch/orchestration, Flatpak/env shaping, and installer/deployment logic remain outside backend-selection cleanup unless a later plan explicitly broadens scope.

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
| 1 | Move remaining presentation/input ownership into backend-owned runtime modules | Not Started |
| 2 | Move tracker ownership into backend-owned discovery modules and trim shared runtime tracking code | Not Started |
| 3 | Remove UI/control-surface backend-policy leakage, fix status surfaces, and document the retained non-backend boundaries | Not Started |
| 4 | Run remaining environment validation, EDMC compliance review, and final release/signoff closure | Not Started |

## Phase Details

### Phase 1: Backend-Owned Presentation And Input Cleanup (`PresentationBackend` + `InputPolicyBackend`)
- Move shared X11/XWayland/native Wayland runtime presentation/input behavior behind backend-owned presentation/input-policy surfaces.
- Preserve current behavior, current fallback paths, and current user-visible capability reporting while changing ownership only.
- `fix219` may land Phase `1` with a bundle-owned combined presentation/input adapter where that keeps the migration smaller and behavior-scoped; a later architecture redesign phase may still split those responsibilities into cleaner public contracts if the codebase proves that split is warranted.
- Risks: subtle click-through regressions; Qt/Wayland behavior changing when integration classes move; accidental backend-family conflation between `native_x11`, `xwayland_compat`, and native Wayland instances.
- Mitigations: keep X11/XWayland shared implementation only where backend identity stays explicit; add bundle-facing tests before trimming old shims; keep Windows path untouched unless a stage explicitly says otherwise.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add bundle-facing tests that lock current presentation/input behavior across X11/XWayland/native Wayland bundle identities | Not Started |
| 1.2 | Lift shared X11/XWayland integration creation and native Wayland compositor-specific integration behavior into backend-owned modules or backend-private implementation files | Not Started |
| 1.3 | Reduce `overlay_client/platform_integration.py` to a generic bundle-consumer shim with no compositor-specific native Wayland policy branches | Not Started |

#### Stage 1.1 Detailed Plan
- Objective:
- Anchor existing runtime presentation/input behavior before moving ownership.
- Primary touch points:
- `overlay_client/tests/test_backend_bundles_x11.py`
- `overlay_client/tests/test_backend_bundles_wayland.py`
- `overlay_client/tests/test_backend_consumers.py`
- Steps:
- Add or expand tests that prove explicit bundle identity still maps to the current integration behavior for `native_x11`, `xwayland_compat`, `kwin_wayland`, `gnome_shell_wayland`, `sway_wayfire_wlroots`, and `hyprland`.
- Lock current click-through and presentation-policy outcomes without broadening support claims.
- Keep this stage test-first; do not move runtime implementation ownership yet.
- Acceptance criteria:
- Bundle-facing tests fail if a bundle starts using the wrong presentation/input behavior.
- Existing runtime behavior remains unchanged in this stage.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_consumers.py -q`

#### Stage 1.2 Detailed Plan
- Objective:
- Move runtime presentation/input ownership behind backend-owned modules while preserving current shipped behavior.
- Primary touch points:
- `overlay_client/backend/bundles/native_x11.py`
- `overlay_client/backend/bundles/xwayland_compat.py`
- `overlay_client/backend/bundles/_wayland_common.py`
- `overlay_client/backend/bundles/wayland_layer_shell_generic.py`
- `overlay_client/backend/bundles/kwin_wayland.py`
- `overlay_client/backend/bundles/gnome_shell_wayland.py`
- `overlay_client/backend/bundles/hyprland.py`
- `overlay_client/backend/bundles/sway_wayfire_wlroots.py`
- `overlay_client/platform_integration.py`
- Steps:
- Lift the current XCB/X11 integration implementation behind backend-owned factories so `native_x11` and `xwayland_compat` remain explicitly distinct even if implementation internals are shared.
- Lift the current native Wayland integration behavior, including compositor-specific click-through/presentation handling, behind backend-owned `PresentationBackend` / `InputPolicyBackend` surfaces instead of the shared `_WaylandIntegration` class.
- Keep any generic Qt-only helpers in a neutral/shared utility if truly backend-agnostic, but move compositor/backend policy ownership out of `platform_integration.py`.
- Acceptance criteria:
- Backend-owned modules now own runtime presentation/input behavior for Linux bundle identities in explicit contract terms, not only by file placement.
- Current user-visible behavior remains unchanged.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_consumers.py -q`

#### Stage 1.3 Detailed Plan
- Objective:
- Leave `overlay_client/platform_integration.py` as a generic consumer facade rather than a second home for compositor policy.
- Primary touch points:
- `overlay_client/platform_integration.py`
- `overlay_client/backend/consumers.py`
- `overlay_client/tests/test_platform_controller_backend_status.py`
- Steps:
- Remove compositor-branching native Wayland policy from `PlatformController` integration creation.
- Keep generic responsibilities only: consume backend status, rebuild integrations when bundle identity changes, expose generic policy queries like `uses_transient_parent()`, and delegate presentation/input ownership to backend-owned contract implementations.
- Preserve Windows-specific platform integration here unless a later phase chooses to unify that ownership too.
- Acceptance criteria:
- No native Wayland compositor branch remains in `platform_integration.py`.
- `PlatformController` consumes backend-owned presentation/input-policy surfaces only.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_backend_consumers.py -q`

#### Phase 1 Execution Order
- Implement in strict order: `1.1` -> `1.2` -> `1.3`.

#### Phase 1 Exit Criteria
- Linux presentation/input behavior is backend-owned in `PresentationBackend` / `InputPolicyBackend` terms.
- `overlay_client/platform_integration.py` no longer contains compositor-specific native Wayland policy.

### Phase 2: Backend-Owned Discovery And Tracker Cleanup (`TargetDiscoveryBackend`)
- Move tracker implementations and related runtime discovery behavior behind backend-owned target-discovery surfaces.
- Preserve current follow-mode behavior, tracker fallback rules, and current native-wayland-first/X11 fallback policy.
- Keep the runtime discovery contract minimal while retaining a separate structured diagnostics path for issue-`#215`-style multi-monitor / fractional-scaling troubleshooting.
- Risks: follow mode regressions on wlroots/Hyprland/KWin; subtle fallback breakage when no tracker is available; accidental coupling between tracker ownership cleanup and selector policy.
- Mitigations: keep fallback policy status-driven through `BackendSelectionStatus`; preserve current shipped tracker factories first, then trim shared entrypoints only after coverage passes.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add or expand tests that lock current tracker ownership and fallback behavior by bundle/status rather than by raw compositor branches | Not Started |
| 2.2 | Lift X11/KWin/Hyprland/wlroots tracker implementations behind backend-owned discovery modules or backend-private implementation files | Not Started |
| 2.3 | Reduce `overlay_client/window_tracking.py` to a generic status-driven tracker entrypoint with no compositor-specific tracker ownership | Not Started |

#### Stage 2.1 Detailed Plan
- Objective:
- Lock the current tracker/fallback contract before moving implementation ownership.
- Primary touch points:
- `overlay_client/tests/test_window_tracking_bundle_routing.py`
- `overlay_client/tests/test_backend_consumers.py`
- `tests/test_harness_backend_selection_wiring.py`
- Steps:
- Expand bundle-routing tests so they prove tracker resolution and fallback work off backend status/bundle identity rather than raw compositor branching.
- Add or preserve test coverage for the structured diagnostics/debug path needed to troubleshoot multi-monitor, per-monitor DPR, fractional scaling, and normalization issues without inflating the runtime `TargetDiscoveryBackend` contract.
- Keep harness coverage around config/platform-context plumbing that feeds runtime status into tracker setup.
- Acceptance criteria:
- Tracker fallback expectations are explicit in project-owned tests before tracker ownership moves.
- Support diagnostics remain sufficient to troubleshoot issue-`#215`-style placement/scaling problems after tracker ownership moves.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_backend_consumers.py tests/test_harness_backend_selection_wiring.py -q`

#### Stage 2.2 Detailed Plan
- Objective:
- Move tracker implementations behind backend-owned discovery ownership while preserving the current shipped tracker set.
- Primary touch points:
- `overlay_client/backend/bundles/native_x11.py`
- `overlay_client/backend/bundles/xwayland_compat.py`
- `overlay_client/backend/bundles/_wayland_common.py`
- `overlay_client/backend/bundles/kwin_wayland.py`
- `overlay_client/backend/bundles/hyprland.py`
- `overlay_client/backend/bundles/sway_wayfire_wlroots.py`
- `overlay_client/window_tracking.py`
- Steps:
- Lift `wmctrl`, `swaymsg`, `hyprctl`, and KWin DBus tracker ownership into backend-owned `TargetDiscoveryBackend` modules or backend-private implementation files.
- Preserve current “no tracker available” behavior for intentionally unavailable paths such as helper-required GNOME and generic unknown Wayland.
- Keep richer troubleshooting data separate from the minimal runtime discovery contract: tracker backends may emit or expose diagnostics for support collection, but they should not turn backend discovery into a second probe/status/classification surface.
- Keep Windows tracker behavior intact unless a later cleanup stage explicitly broadens the scope.
- Acceptance criteria:
- Linux tracker implementation ownership is backend-owned in explicit `TargetDiscoveryBackend` terms.
- `window_tracking.py` no longer owns compositor-specific tracker classes for Linux backends.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_backend_consumers.py -q`

#### Stage 2.3 Detailed Plan
- Objective:
- Reduce the public tracker entrypoint to a generic status-driven consumer shim.
- Primary touch points:
- `overlay_client/window_tracking.py`
- `overlay_client/backend/consumers.py`
- `overlay_client/tests/test_window_tracking_bundle_routing.py`
- Steps:
- Keep `create_elite_window_tracker(...)` as a generic runtime entrypoint if still useful, but make it consume backend status and backend-owned `TargetDiscoveryBackend` factories only.
- Remove raw compositor/session branching from Linux tracker ownership paths.
- Leave only generic platform top-level branching where necessary (for example, Windows vs Linux vs unsupported OS).
- Preserve or centralize the structured diagnostics path used to troubleshoot mixed-monitor / fractional-scaling issues so supportability is not lost when raw tracker ownership moves behind backend boundaries.
- Acceptance criteria:
- Linux tracking behavior is selected by backend status/bundle only, with target discovery owned by backend-specific contract implementations.
- `window_tracking.py` is no longer a second home for Linux compositor policy.
- Multi-monitor / DPR troubleshooting remains possible through structured diagnostics even though the core runtime discovery contract stays minimal.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py -q`

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.

#### Phase 2 Exit Criteria
- Linux tracker ownership is backend-owned in `TargetDiscoveryBackend` terms.
- Shared tracking entrypoints consume backend-owned discovery modules rather than owning compositor-specific trackers directly.

### Phase 3: UI Metadata, Launch Fallback Cleanup, Status Surface Corrections, And Boundary Clarification
- Remove remaining UI/control-surface backend-policy leakage and document the boundaries that are intentionally left outside backend.
- Keep launch/orchestration and installer behavior intact; this phase is about clarifying ownership, not expanding scope.
- Risks: overreaching into plugin/install redesign; accidental behavior change in override options or status visibility; conflating plugin-hint status with client-runtime truth; breaking XWayland fallback startup while retiring `force_xwayland`; removing generic OS guards that are still appropriate.
- Mitigations: narrow the phase to metadata/choice derivation, launch fallback cleanup, status transport, controlled visibility-surface changes, generic guard audit, and documentation updates; keep selector/runtime authority unchanged and preserve `xwayland_compat` as an explicit fallback.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Expose client-authoritative backend status to plugin preferences via the existing plugin/client socket path, with `plugin_hint` retained as labeled fallback | Not Started |
| 3.2 | Retire the separate `force_xwayland` setting in favor of explicit manual `xwayland_compat` fallback/override semantics (restart required) | Not Started |
| 3.3 | Centralize backend-owned override-choice metadata so prefs stop deriving backend choices from raw compositor branches | Not Started |
| 3.4 | Remove backend status from the Overlay Controller title bar and add backend choice to the lower-left debug/test-overlay metrics area | Not Started |
| 3.5 | Audit and shrink-wrap residual OS-specific checks in generic runtime modules, removing only the ones that encode backend policy | Not Started |
| 3.6 | Document the retained intentional boundaries (`load.py`, installer/deployment logic, `plugin_hint`) and archive/supersede any notes that imply broader cleanup is still complete | Not Started |

#### Stage 3.1 Detailed Plan
- Objective:
- Expose client-authoritative backend status to plugin preferences without introducing a second backend authority.
- Primary touch points:
- `overlay_client/data_client.py`
- `overlay_client/overlay_client.py`
- `load.py`
- `overlay_plugin/preferences.py`
- `overlay_client/backend/status.py`
- `overlay_client/tests/test_backend_status.py`
- `tests/test_preferences_panel_controller_tab.py`
- `tests/test_harness_backend_status_roundtrip.py`
- Steps:
- Add or extend the existing plugin/client socket path so the plugin can request client-authoritative backend status (`source=client_runtime`) rather than only plugin shadow status.
- Use a request/response status contract over that existing local socket path rather than introducing pushed status updates for this phase.
- Keep the current plugin shadow status (`source=plugin_hint`) as fallback when client-runtime status is unavailable, and label that fallback explicitly as advisory.
- Define freshness and fallback behavior explicitly so stale or unreachable client-runtime status does not continue to present as current truth; when `client_runtime` and `plugin_hint` disagree, `client_runtime` remains authoritative and any `plugin_hint` mismatch is surfaced only as a secondary advisory note.
- Keep this stage out of the controller title bar; the goal here is accurate preferences visibility, not more title-bar status.
- Preserve current selector authority and do not introduce a second selection path.
- Acceptance criteria:
- Preferences can show client-authoritative backend status when the client is reachable.
- `plugin_hint` remains available only as fallback and is clearly labeled advisory.
- Stale or unavailable `client_runtime` status falls back cleanly to advisory `plugin_hint`, and a `plugin_hint` mismatch never overrides fresh runtime truth.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_status_roundtrip.py -q`

#### Stage 3.2 Detailed Plan
- Objective:
- Retire `force_xwayland` as a separate user-facing/persisted setting and keep XWayland usage only as an explicit backend fallback or override.
- Primary touch points:
- `load.py`
- `overlay_client/backend/selector.py`
- `overlay_client/platform_context.py`
- `overlay_client/client_config.py`
- `overlay_plugin/preferences.py`
- `overlay_plugin/overlay_config_payload.py`
- `overlay_client/tests/test_backend_selector.py`
- `overlay_client/tests/test_platform_context.py`
- `overlay_client/tests/test_client_config.py`
- `tests/test_overlay_config_payload.py`
- `tests/test_preferences_persistence.py`
- `tests/test_harness_backend_override_roundtrip.py`
- Steps:
- Remove the user-facing `force_xwayland` setting from prefs/config/bootstrap payloads and stop emitting `EDMC_OVERLAY_FORCE_XWAYLAND` as part of normal backend control flow.
- Migrate persisted `force_xwayland=true` state to explicit `manual_backend_override="xwayland_compat"` semantics where needed so existing users keep the same fallback intent.
- Treat XWayland startup transport as what it really is: an explicit startup transport override to the `xwayland_compat` backend. Under `Auto`, do not silently launch `QT_QPA_PLATFORM=xcb`; only an explicit manual backend override to `xwayland_compat` may drive `QT_QPA_PLATFORM=xcb` on Wayland.
- Make the user-facing surface explicit that `xwayland_compat` is restart-required, because Qt platform transport cannot be switched in-process after launch.
- Backend override selection is made in plugin preferences. When a selected override changes Qt startup transport, the preference change is saved immediately but surfaced in the preferences status area as pending until restart. Preferences must show that the current runtime backend remains unchanged until the overlay client is explicitly restarted, and must not imply that the backend switch has already applied live. The existing `Restart Overlay Client` action should remain the explicit apply path for restart-required backend changes.
- Preserve `xwayland_compat` as a named explicit fallback backend and do not silently remove the compatibility path.
- Acceptance criteria:
- No user-facing or persisted `force_xwayland` setting remains in the normal backend-control path.
- Explicit `xwayland_compat` fallback/override still works end to end, including launch-time Qt platform selection and restart-required UX.
- `Auto` no longer behaves like a hidden XWayland-force toggle and never silently launches `QT_QPA_PLATFORM=xcb`.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_platform_context.py overlay_client/tests/test_client_config.py tests/test_overlay_config_payload.py tests/test_preferences_persistence.py tests/test_harness_backend_override_roundtrip.py -q`

#### Stage 3.3 Detailed Plan
- Objective:
- Move override-choice policy out of preferences-specific OS/compositor branching.
- Primary touch points:
- `overlay_client/backend/status.py`
- `overlay_client/backend/contracts.py`
- `overlay_plugin/preferences.py`
- `overlay_client/tests/test_backend_status.py`
- `tests/test_preferences_panel_controller_tab.py`
- Steps:
- Add backend-owned override-choice metadata so valid override choices come from backend registry metadata rather than preferences-specific OS/compositor mapping logic. `overlay_client/backend/contracts.py` may define the metadata shape, but `status.py` must not become the owner of backend override policy.
- Update preferences to consume that metadata instead of rebuilding the choice list from `operating_system`, `session_type`, and `compositor`.
- Keep UI behavior and override persistence unchanged.
- Acceptance criteria:
- Preferences no longer encode compositor mapping tables for backend override choices.
- Override-choice availability rules live in backend-owned metadata rather than `status.py` or preferences-local policy code.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_override_roundtrip.py -q`

#### Stage 3.4 Detailed Plan
- Objective:
- Correct the remaining backend-status visibility surfaces.
- Primary touch points:
- `overlay_controller/overlay_controller.py`
- `overlay_client/backend/status.py`
- `overlay_client/debug_cycle_overlay.py`
- `overlay_client/render_surface.py`
- `overlay_client/tests/test_backend_status.py`
- `overlay_controller/tests/test_backend_status_title.py`
- Steps:
- Remove backend-status formatting from the Overlay Controller title bar and leave the controller title at its base title for now.
- Add backend choice to the lower-left debug/test-overlay metrics area so backend visibility remains available in the client-side visual diagnostics surface.
- Keep the debug/test-overlay addition scoped to existing diagnostic/test-logo surfaces rather than expanding controller UI.
- Acceptance criteria:
- Overlay Controller title bar no longer shows backend status.
- The debug/test-overlay lower-left metrics area includes backend choice information.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py overlay_controller/tests/test_backend_status_title.py -q`

#### Stage 3.5 Detailed Plan
- Objective:
- Separate legitimate generic windowing guards from leaked backend policy in runtime modules outside backend.
- Primary touch points:
- `overlay_client/follow_surface.py`
- `overlay_client/interaction_controller.py`
- `overlay_client/overlay_client.py`
- `overlay_client/control_surface.py`
- `overlay_client/tests/test_follow_surface_mixin.py`
- `overlay_client/tests/test_control_surface_platform_context.py`
- Steps:
- Audit remaining `sys.platform` / Wayland checks and classify each one as either generic UI/windowing behavior or leaked backend policy.
- Treat as acceptable only the mechanical compatibility or API-availability guards that do not select a backend, instantiate backend-specific implementations, or recreate fallback/support/override logic from raw platform/session/compositor inputs.
- Remove or redirect any checks that still choose backend behavior outside the backend layer.
- Retain only the generic guards that do not encode backend-family/compositor policy.
- Acceptance criteria:
- Residual generic checks are minimal and explicitly justifiable.
- No remaining runtime module outside backend decides Linux compositor/backend policy locally.
- Any retained non-backend guard can be explained as a generic compatibility/windowing check rather than backend-policy leakage.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_control_surface_platform_context.py overlay_client/tests/test_platform_controller_backend_status.py -q`

#### Stage 3.6 Detailed Plan
- Objective:
- Make the intentional non-backend boundaries explicit so future audits do not treat them as accidental leakage.
- Primary touch points:
- `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md`
- `docs/refactoring/fix219_cross_platform_overlay_architecture_research.md`
- `load.py`
- `scripts/install_linux.sh`
- `scripts/install_matrix.json`
- Steps:
- Update docs to state explicitly that plugin launch/orchestration, `plugin_hint`, Flatpak/env shaping, and installer compositor profiles are retained boundaries.
- Record any remaining cleanup deferrals clearly if a stage finishes with intentional exceptions.
- Keep the `standalone_mode` boundary explicit: Windows standalone behavior is preserved as-is during `fix219`, while Linux standalone behavior/support remains deferred to a separate post-`fix219` feature/validation plan.
- Keep the physical-clamp boundary explicit: it remains a shared geometry/follow escape hatch during `fix219`, and any deeper coordinate-space redesign or override-identity cleanup is deferred to a separate post-`fix219` geometry/follow plan.
- Keep the Windows boundary explicit: Windows behavior is preserved and regression-validated during `fix219`, while deeper Windows backend-contract cleanup remains a named post-`fix219` architecture track rather than an unplanned omission.
- Archive or annotate any refactor notes that incorrectly imply all platform-specific runtime ownership is already inside backend.
- Acceptance criteria:
- The follow-up architecture boundary is documented precisely.
- Future cleanup work has an unambiguous distinction between runtime leakage and intentional plugin/install boundaries.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py overlay_client/tests/test_platform_context.py -q`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3` -> `3.4` -> `3.5` -> `3.6`.

#### Phase 3 Exit Criteria
- Preferences show client-authoritative backend status when available and treat `plugin_hint` as advisory fallback only.
- `force_xwayland` is retired as a separate user-facing setting, with `xwayland_compat` retained only as an explicit fallback/override path.
- Overlay Controller title bar is no longer used as a backend-status surface.
- Debug/test-overlay diagnostics surface backend choice in the lower-left metrics area.
- Preferences consume backend-owned metadata instead of reconstructing backend policy.
- Remaining non-backend boundaries are explicit, documented, and intentionally retained.

### Phase 4: Validation, Compliance, And Signoff
- Close the remaining release-readiness gaps after the ownership/status cleanup lands.
- Keep this phase evidence-driven: record exact environments checked, exact compliance findings, and any explicit limitations retained at signoff time.
- Risks: declaring completion based only on tests and refactor shape while remaining compositor/helper paths or EDMC compliance edges are still unverified.
- Mitigations: require recorded environment results, recorded compliance findings, and an explicit closeout of the release signoff checklist before calling the cleanup complete.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Run the remaining compositor/helper validation matrix and record exact environment results and retained limitations | Not Started |
| 4.2 | Run and record the EDMC compliance review after the refactor cleanup is complete | Not Started |
| 4.3 | Close the release signoff checklist and record any final deferrals or explicit limitations | Not Started |

#### Stage 4.1 Detailed Plan
- Objective:
- Replace the current “known validation gap” state with recorded environment evidence for the remaining claimed paths.
- Primary touch points:
- `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md`
- `RELEASE_NOTES.md`
- Steps:
- Re-run or confirm the minimum closure matrix environments required for `fix219`: Windows baseline, `native_x11`, explicit `xwayland_compat`, and one recorded KWin Wayland run.
- As part of that closure matrix, explicitly validate that manual backend override authority still works end to end and remains the effective user-facing override over `Auto`, including the restart-required `xwayland_compat` path.
- If additional wlroots/Hyprland/COSMIC/gamescope or helper-backed Wayland testers are available, record those runs too; otherwise mark those environments deferred and remove any implied signoff claim that they were fully validated in this plan.
- Record each checked environment as pass, fail, unsupported, or deferred, with the exact limitation or follow-up needed.
- Record or confirm the final claimed support classification for each checked environment (`true_overlay`, `degraded_overlay`, `unsupported`) and the concrete reason when the result is not `true_overlay`.
- Apply the classification evidence rule explicitly: no environment receives a final support classification from code inspection alone; `true_overlay` requires demonstrated full claimed behavior with no material unresolved limitation, `degraded_overlay` requires demonstrated partial behavior with an explicit weakened guarantee and concrete reason, `unsupported` requires recorded evidence that the required support bar is not met or not implemented, and any environment lacking sufficient recorded evidence remains deferred.
- Do not silently broaden support claims if validation reveals a weaker support story than planned.
- Acceptance criteria:
- The minimum closure matrix has recorded evidence rather than an unspecified validation gap.
- Claimed support classifications and reasons are explicit for the environments covered by signoff.
- Any environment still lacking sufficient evidence remains explicitly deferred rather than silently promoted to a claimed support tier.
- Any retained limitation is explicit in docs/release notes.
- Verification to run:
- Record exact commands, environments, and outcomes in the `Execution Log`; include any supporting automated tests run alongside the manual checks.

#### Stage 4.2 Detailed Plan
- Objective:
- Record a post-refactor EDMC compliance review instead of relying on assumptions from earlier implementation stages.
- Primary touch points:
- `scripts/check_edmc_python.py`
- `docs/compliance/edmc_python_version.txt`
- `load.py`
- `overlay_plugin/preferences.py`
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md`
- Steps:
- Run the required EDMC baseline/compliance checks, including Python baseline enforcement and a targeted review of plugin API usage, logging, threading/Tk safety, and prefs/config handling against the AGENTS/PLUGINS guidance.
- Record any non-compliance findings as either fixed, accepted with rationale, or deferred with explicit follow-up.
- Keep this review limited to actual compliance obligations rather than reopening settled architecture decisions that are already documented as intentional boundaries.
- Acceptance criteria:
- A recorded compliance pass exists for the refactored state.
- Any non-compliance exception or follow-up is documented explicitly.
- Verification to run:
- `python scripts/check_edmc_python.py`
- Record any additional targeted test/lint commands run as part of the compliance review.

#### Stage 4.3 Detailed Plan
- Objective:
- Make final completion conditional on the recorded evidence rather than on implementation confidence alone.
- Primary touch points:
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md`
- `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- `RELEASE_NOTES.md`
- Steps:
- Walk the `Release Signoff Checklist` and mark each item with recorded evidence or an explicit documented exception.
- If any item remains open, carry it forward as a named deferral rather than implying completion.
- Summarize final retained limitations and ownership boundaries in the `Execution Log`.
- Revisit and refresh the `Architecture Progress Snapshot` at the top of `docs/refactoring/fix219_backend_architecture_refactor_plan.md` so the main architecture plan reflects the post-cleanup state rather than stopping at the initial cutover milestone.
- Acceptance criteria:
- The release signoff checklist is either fully closed or has explicit named deferrals.
- The top-level architecture progress snapshot has been updated to reflect final follow-up status.
- The final docs do not overstate completion.
- Verification to run:
- No single fixed command; this stage is complete only when the checklist and execution log contain the required evidence and any retained deferrals.

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- Remaining claimed compositor/helper paths have recorded validation outcomes.
- A post-refactor EDMC compliance review is recorded.
- The release signoff checklist is closed or has explicit named deferrals with rationale.

## Release Signoff Checklist
Use this checklist before declaring the backend-architecture cleanup complete.

### Architecture Boundaries
- [ ] Are all runtime OS/DE/compositor backend decisions owned by `overlay_client/backend` or explicitly documented as intentional non-backend boundaries?
- [ ] Are `overlay_client/platform_integration.py` and `overlay_client/window_tracking.py` reduced to generic shims rather than second homes for compositor/backend policy?
- [ ] Do preferences/controller surfaces consume backend metadata rather than rebuilding backend policy from raw OS/session/compositor values?

### Authority And Status
- [ ] When the client is reachable, do preferences show `source=client_runtime` rather than `plugin_hint`?
- [ ] When the client is unavailable, do preferences fall back cleanly to `plugin_hint` and label it advisory?
- [ ] Is there only one effective backend authority, with no plugin-side path that can silently override client runtime selection?
- [ ] Has the separate `force_xwayland` setting been retired, with `xwayland_compat` remaining available only as an explicit backend fallback/override?

### Visibility Surfaces
- [ ] Is backend status removed from the Overlay Controller title bar?
- [ ] Does the lower-left debug/test-overlay metrics area show the chosen backend?
- [ ] Can support tell from the UI/logs both the chosen backend and whether it came from `client_runtime` or `plugin_hint`?

### Behavior Preservation
- [ ] Has no currently working environment been silently downgraded?
- [ ] Does `xwayland_compat` remain a named, explicit fallback path?
- [ ] Do manual backend overrides still work end to end?

### Lifecycle And Failure Modes
- [ ] Is startup behavior defined before the client has published runtime status?
- [ ] Is stale/disconnected-client behavior defined for open preferences/controller surfaces?
- [ ] Is plugin-hint vs client-runtime disagreement surfaced predictably?

### Tests And Validation
- [ ] Do unit tests cover backend-owned policy and formatting?
- [ ] Do harness tests cover `load.py` / prefs / controller status wiring?
- [ ] Have real-environment checks been done for the supported X11/Wayland compositor paths being claimed?
- [ ] Has the minimum closure matrix been validated: Windows baseline, `native_x11`, explicit `xwayland_compat`, and one recorded KWin Wayland run?
- [ ] Has explicit manual backend override authority been validated as still working end to end over `Auto`, including the restart-required `xwayland_compat` path?
- [ ] Do logs/debug diagnostics still expose enough information to troubleshoot mixed-monitor / DPR / fractional-scaling issues after tracker ownership moves?
- [ ] Does every claimed environment classification have recorded environment evidence rather than code-inspection-only reasoning?
- [ ] Does every non-`true_overlay` classification record the exact weakened guarantee and concrete reason?
- [ ] Are any still-unvalidated environments marked deferred rather than silently classified?

### Docs And Release Readiness
- [ ] Do the `fix219_` docs match shipped behavior rather than intended future behavior?
- [ ] Are intentional non-backend boundaries documented so future audits do not reopen them as defects?
- [ ] Are claimed environment classifications (`true_overlay`, `degraded_overlay`, `unsupported`) and any non-ideal reasons explicit at signoff time?
- [ ] Has an EDMC compliance pass been done for plugin API usage, logging, threading, and prefs/config handling after the refactor?

## Execution Log
- Plan created on 2026-04-03.
- Record one execution summary subsection per completed phase.
- Record exact test commands and outcomes for each completed phase.

### Phase 1 Execution Summary
- Not started.

### Tests Run For Phase 1
- None yet.

### Phase 2 Execution Summary
- Not started.

### Tests Run For Phase 2
- None yet.

### Phase 3 Execution Summary
- Not started.

### Tests Run For Phase 3
- None yet.

### Phase 4 Execution Summary
- Not started.

### Tests Run For Phase 4
- None yet.
