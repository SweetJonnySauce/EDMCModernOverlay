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

## Current Audit Snapshot
- Phase `1` is complete: Linux presentation/input ownership now routes through backend-owned modules rather than living in shared runtime integration code.
- Phase `2` is complete: Linux tracker ownership now routes through backend-owned discovery modules rather than living in the public runtime tracker entrypoint.
- Phase `3` is complete: preferences use client-authoritative backend status when available, `force_xwayland` has been retired in favor of explicit `xwayland_compat` override semantics, override-choice metadata is backend-owned, backend status has been removed from the controller title bar, debug/test-overlay diagnostics show backend choice, residual generic runtime guards have been audited, and the retained intentional boundaries are documented explicitly.
- Phase `4` is complete: the public backend surface now declares required discovery/presentation behavior directly, capability truth for generic runtime consumers now lives in `BackendCapabilities`, the still-intentional combined Linux presentation/input adapter shape is documented explicitly, and the helper boundary remains narrow and transport-specific.
- Phase `4A` is complete: shipped status surfaces now report Wayland `xwayland_compat` as `degraded_overlay`, the transitional review-guarded `true_overlay` classification has been removed, and explicit manual-override/runtime behavior remains unchanged.
- `load.py` launch/orchestration, advisory `plugin_hint`, and Flatpak/env shaping remain intentional plugin control-plane boundaries rather than backend-ownership defects.
- Installer compositor profiles in `scripts/install_linux.sh` / `scripts/install_matrix.json` remain intentional deployment guidance boundaries rather than runtime backend-selection defects.
- The remaining open work in this plan is Phase `5`: real-environment validation, EDMC compliance review, and final signoff.

## Settings Impact Classification
- Backend-critical settings/surfaces:
  - `manual_backend_override`: explicit backend/fallback choice surface; this is the intended long-term user-facing backend control, including the explicit `xwayland_compat` override path.
  - `QT_QPA_PLATFORM` and related env override paths: not normal user settings, but still backend-critical because they can override startup transport/backend shape and must be documented or constrained explicitly.
  - Historical note: the old `force_xwayland` setting has been retired from the normal backend-control path; only legacy persisted values are migrated forward for compatibility.
- Visibility-only settings:
  - `show_debug_overlay`: relevant because backend choice/status will be surfaced in the debug/test-overlay diagnostics.
  - `debug_overlay_corner`: only affects where the debug/test-overlay diagnostics render.
  - `title_bar_enabled` / `title_bar_height`: relevant only because backend status is being removed from the controller title bar while title-bar compensation remains a separate runtime/UI feature.
- Not part of backend-architecture cleanup unless a later stage explicitly broadens scope:
  - `force_render`: visibility/focus behavior only, not backend choice.
  - `standalone_mode`: runtime mode/UI behavior, not backend selection. Preserve the current Windows behavior during `fix219`; defer Linux standalone behavior/support and validation until after this cleanup plan, and treat that later work as a separate runtime/presentation feature with backend/compositor-specific support expectations rather than as backend-selection cleanup.
  - `physical_clamp_enabled` / `physical_clamp_overrides`: shared geometry-normalization escape hatches, not backend ownership or backend choice. Preserve current opt-in behavior during `fix219`; require backend/tracker cleanup to keep feeding the shared normalizer correctly; defer any deeper coordinate-space redesign to a separate post-`fix219` geometry/follow refactor.
  - opacity, font bounds/steps, gridlines, payload cycling, payload logging, connection-status display, controller launch command, and other presentation/debug preferences.

## Current Remaining Gaps And Planned Closure

| Gap | Current State | Why It Is Still A Gap | Planned Closure |
| --- | --- | --- | --- |
| Real-environment validation remains incomplete for deferred/non-closure paths | Additional wlroots, Hyprland, COSMIC, gamescope, and helper-backed Wayland runs may still lack testers even after the minimum `fix219` closure matrix is validated | These paths can remain deferred, but signoff must not imply validated support for them without recorded environment evidence | Stage `5.1`: validate the minimum closure matrix, record any extra runs that are available, and explicitly defer/remove implied support claims for any still-unvalidated paths before signoff |
| Post-refactor EDMC compliance pass is not yet recorded | The docs do not currently record a final compliance review for plugin API usage, logging, threading, and prefs/config handling after the refactor | Release readiness is incomplete until compliance review evidence is explicit | Stage `5.2`: run and record the EDMC compliance pass, then capture any required follow-up fixes or explicit exceptions |
| Final release signoff and top-level progress closeout are not yet recorded | The release checklist, final architecture snapshot refresh, and release-note/signoff summary still depend on Phase `5` evidence | The plan should not be read as fully complete until the recorded validation/compliance evidence is reflected in the final signoff docs | Stage `5.3`: close the release signoff checklist, refresh the top-level architecture progress snapshot, and record any remaining named deferrals |

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
- `overlay_client/backend/contracts.py` (public backend protocol and metadata surface)
- `overlay_client/backend/status.py` (status/report metadata that still reflects identity-oriented assumptions)
- `overlay_client/backend/helper_ipc.py` (existing helper boundary that may need a richer public contract shape)
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
- `overlay_client/tests/test_backend_contracts.py`
- `overlay_client/tests/test_helper_ipc_boundary.py`
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
- Capability classification and support-tier policy from the architecture research remain authoritative for this plan; Phase `5` must record final claimed environment classifications (`true_overlay`, `degraded_overlay`, `unsupported`) and concrete reasons rather than only pass/fail validation notes.
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
- Contract tightening
  - Phase `4` of this plan strengthens the backend contracts so they define required behavior, not only identity.
  - That phase removes `getattr(...)`-style capability discovery from bundle consumers by promoting required methods onto the public protocols used by:
    - `TargetDiscoveryBackend`
    - `PresentationBackend`
  - `InputPolicyBackend` intentionally remains minimal during `fix219` because no generic runtime consumer currently requires a separate input-policy method.
  - `HelperIpcBackend` intentionally remains narrow during `fix219`; transport/message validation continues to live in `overlay_client/backend/helper_ipc.py` unless later runtime work requires more on the generic contract surface.
  - The same phase also moves semantic bundle behavior out of enum/family inference and into explicit backend-declared capabilities, specifically:
    - tracker availability
    - transient-parent requirements
    - native-Wayland vs X11-style windowing expectation
    - tracker fallback transport expectations
  - The current `fix219` landing shape keeps the Linux bundle-owned combined `presentation` / `input_policy` adapter explicit and test-locked; a later plan may still split that public shape if reuse/lifecycle boundaries justify it.
  - Validation and signoff happen only after that tightening work lands so the release-readiness evidence reflects the stronger contract surface rather than the looser transitional one.
- Capability classification and visibility
  - Phase `3`, Phase `4`, and Phase `5` must preserve the architecture policy that backend/status surfaces report chosen backend, source of truth, and any degraded/fallback reason in a way support can inspect.
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
| 1 | Move remaining presentation/input ownership into backend-owned runtime modules | Completed |
| 2 | Move tracker ownership into backend-owned discovery modules and trim shared runtime tracking code | Completed |
| 3 | Remove UI/control-surface backend-policy leakage, fix status surfaces, and document the retained non-backend boundaries | Completed |
| 4 | Tighten backend contracts so the public backend surface is behavior-oriented rather than primarily identity-oriented | Completed |
| 4A | Flip Wayland `xwayland_compat` reporting from transitional `true_overlay` to explicit `degraded_overlay` without changing runtime backend behavior | Completed |
| 5 | Run remaining environment validation, EDMC compliance review, and final release/signoff closure | Not Started |

## Phase Details

### Phase 1: Backend-Owned Presentation And Input Cleanup (`PresentationBackend` + `InputPolicyBackend`)
- Move shared X11/XWayland/native Wayland runtime presentation/input behavior behind backend-owned presentation/input-policy surfaces.
- Preserve current behavior, current fallback paths, and current user-visible capability reporting while changing ownership only.
- `fix219` may land Phase `1` with a bundle-owned combined presentation/input adapter where that keeps the migration smaller and behavior-scoped; a later architecture redesign phase may still split those responsibilities into cleaner public contracts if the codebase proves that split is warranted.
- Risks: subtle click-through regressions; Qt/Wayland behavior changing when integration classes move; accidental backend-family conflation between `native_x11`, `xwayland_compat`, and native Wayland instances.
- Mitigations: keep X11/XWayland shared implementation only where backend identity stays explicit; add bundle-facing tests before trimming old shims; keep Windows path untouched unless a stage explicitly says otherwise.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add bundle-facing tests that lock current presentation/input behavior across X11/XWayland/native Wayland bundle identities | Completed |
| 1.2 | Lift shared X11/XWayland integration creation and native Wayland compositor-specific integration behavior into backend-owned modules or backend-private implementation files | Completed |
| 1.3 | Reduce `overlay_client/platform_integration.py` to a generic bundle-consumer shim with no compositor-specific native Wayland policy branches | Completed |

#### Stage 1.1 Detailed Plan
- Objective:
- Anchor existing runtime presentation/input behavior before moving ownership.
- Primary touch points:
- `overlay_client/tests/test_backend_bundles_x11.py`
- `overlay_client/tests/test_backend_bundles_wayland.py`
- `overlay_client/tests/test_backend_consumers.py`
- `overlay_client/backend/bundles/native_x11.py`
- `overlay_client/backend/bundles/xwayland_compat.py`
- `overlay_client/backend/bundles/_wayland_common.py`
- `overlay_client/backend/bundles/gnome_shell_wayland.py`
- `overlay_client/backend/bundles/kwin_wayland.py`
- `overlay_client/backend/bundles/hyprland.py`
- `overlay_client/backend/bundles/sway_wayfire_wlroots.py`
- `overlay_client/backend/bundles/wayland_layer_shell_generic.py`
- `overlay_client/backend/consumers.py`
- Steps:
- Add or expand tests that prove explicit bundle identity still maps to the current integration behavior for `native_x11`, `xwayland_compat`, `kwin_wayland`, `gnome_shell_wayland`, `sway_wayfire_wlroots`, and `hyprland`.
- Lock the current combined presentation/input backend shape per bundle, the shared XCB-vs-Wayland integration factory routing, and the current `uses_transient_parent()` / platform-label policy outcomes without broadening support claims.
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
- `overlay_client/window_integration.py`
- `overlay_client/backend/bundles/_linux_window_integration.py`
- `overlay_client/backend/bundles/native_x11.py`
- `overlay_client/backend/bundles/xwayland_compat.py`
- `overlay_client/backend/bundles/_wayland_common.py`
- `overlay_client/backend/bundles/wayland_layer_shell_generic.py`
- `overlay_client/backend/bundles/kwin_wayland.py`
- `overlay_client/backend/bundles/gnome_shell_wayland.py`
- `overlay_client/backend/bundles/hyprland.py`
- `overlay_client/backend/bundles/sway_wayfire_wlroots.py`
- `overlay_client/platform_integration.py`
- `overlay_client/tests/test_platform_controller_backend_status.py`
- Steps:
- Lift the current XCB/X11 integration implementation behind backend-owned factories so `native_x11` and `xwayland_compat` remain explicitly distinct even if implementation internals are shared.
- Lift the current native Wayland integration behavior, including compositor-specific click-through/presentation handling, behind backend-owned `PresentationBackend` / `InputPolicyBackend` surfaces instead of the shared `_WaylandIntegration` class.
- Keep any generic Qt-only helpers in a neutral/shared utility if truly backend-agnostic, but move Linux compositor/backend policy ownership and the shipped XCB/Wayland integration classes out of `platform_integration.py`.
- Acceptance criteria:
- Backend-owned modules now own runtime presentation/input behavior for Linux bundle identities in explicit contract terms, not only by file placement.
- Current user-visible behavior remains unchanged.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_platform_controller_backend_status.py -q`

#### Stage 1.3 Detailed Plan
- Objective:
- Leave `overlay_client/platform_integration.py` as a generic consumer facade rather than a second home for compositor policy or Linux integration implementation ownership.
- Primary touch points:
- `overlay_client/platform_integration.py`
- `overlay_client/tests/test_platform_controller_backend_status.py`
- `overlay_client/tests/test_backend_consumers.py`
- Steps:
- Remove any stale Linux integration imports or helper residue that still makes `platform_integration.py` look like an implementation owner after Stage `1.2`.
- Keep generic responsibilities only: consume backend status, rebuild integrations when bundle identity changes, expose generic policy queries like `uses_transient_parent()`, and delegate presentation/input ownership to backend-owned contract implementations.
- Preserve Windows-specific platform integration here unless a later phase chooses to unify that ownership too.
- Acceptance criteria:
- No native Wayland compositor branch remains in `platform_integration.py`.
- `PlatformController` consumes backend-owned presentation/input-policy surfaces only, and `platform_integration.py` no longer exposes or imports the shipped Linux XCB/Wayland integration factories.
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
| 2.1 | Add or expand tests that lock current tracker ownership and fallback behavior by bundle/status rather than by raw compositor branches | Completed |
| 2.2 | Lift X11/KWin/Hyprland/wlroots tracker implementations behind backend-owned discovery modules or backend-private implementation files | Completed |
| 2.3 | Reduce `overlay_client/window_tracking.py` to a generic status-driven tracker entrypoint with no compositor-specific tracker ownership | Completed |

#### Stage 2.1 Detailed Plan
- Objective:
- Lock the current tracker/fallback contract before moving implementation ownership.
- Primary touch points:
- `overlay_client/tests/test_window_tracking_bundle_routing.py`
- `overlay_client/tests/test_backend_consumers.py`
- `tests/test_harness_backend_selection_wiring.py`
- Steps:
- Expand bundle-routing tests so they prove tracker resolution and fallback work off backend status/bundle identity rather than raw compositor branching, including the current X11 fallback rule when an X11 session is paired with a non-`native_x11` selected bundle.
- Lock the current `create_elite_window_tracker(...)` pass-through contract for `title_hint` and `monitor_provider`, including fallback attempts, so later tracker ownership moves cannot silently drop the monitor-offset/troubleshooting hook.
- Keep the existing harness coverage around overlay-config shadow backend-status publication as the upstream status-wiring guard that later tracker stages still depend on; do not broaden this stage into new harness plumbing unless the actual tracker entrypoint wiring changes.
- Acceptance criteria:
- Tracker fallback expectations are explicit in project-owned tests before tracker ownership moves.
- The current monitor-provider / monitor-offset troubleshooting hook remains explicit in unit tests before tracker ownership moves.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_backend_consumers.py tests/test_harness_backend_selection_wiring.py -q`

#### Stage 2.2 Detailed Plan
- Objective:
- Move tracker implementations behind backend-owned discovery ownership while preserving the current shipped tracker set.
- Primary touch points:
- `overlay_client/window_tracking_support.py`
- `overlay_client/backend/bundles/_linux_trackers.py`
- `overlay_client/backend/bundles/native_x11.py`
- `overlay_client/backend/bundles/xwayland_compat.py`
- `overlay_client/backend/bundles/_wayland_common.py`
- `overlay_client/backend/bundles/kwin_wayland.py`
- `overlay_client/backend/bundles/hyprland.py`
- `overlay_client/backend/bundles/sway_wayfire_wlroots.py`
- `overlay_client/window_tracking.py`
- `overlay_client/tests/test_backend_bundles_x11.py`
- `overlay_client/tests/test_backend_bundles_wayland.py`
- Steps:
- Lift `wmctrl`, `swaymsg`, `hyprctl`, and KWin DBus tracker ownership into backend-owned `TargetDiscoveryBackend` modules or backend-private implementation files, while leaving the public tracker entrypoint and Windows tracker in `window_tracking.py`.
- Move only truly shared tracker data/helpers (`WindowState`, monitor-provider types, monitor augmentation helpers) into a neutral support module so backend-owned Linux tracker modules do not need to reach back into the public runtime entrypoint for shared primitives.
- Preserve current “no tracker available” behavior for intentionally unavailable paths such as helper-required GNOME and generic unknown Wayland.
- Keep richer troubleshooting data separate from the minimal runtime discovery contract: tracker backends may emit or expose diagnostics for support collection, but they should not turn backend discovery into a second probe/status/classification surface.
- Keep Windows tracker behavior intact unless a later cleanup stage explicitly broadens the scope.
- Acceptance criteria:
- Linux tracker implementation ownership is backend-owned in explicit `TargetDiscoveryBackend` terms.
- `window_tracking.py` no longer owns compositor-specific tracker classes for Linux backends.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_backend_consumers.py -q`

#### Stage 2.3 Detailed Plan
- Objective:
- Reduce the public tracker entrypoint to a generic status-driven consumer shim.
- Primary touch points:
- `overlay_client/window_tracking.py`
- `overlay_client/tests/test_window_tracking_bundle_routing.py`
- `overlay_client/tests/test_backend_consumers.py`
- `overlay_client/tests/test_follow_surface_mixin.py`
- Steps:
- Keep `create_elite_window_tracker(...)` as the generic runtime entrypoint, but leave Linux tracking selection limited to deriving/consuming backend status and backend-owned `TargetDiscoveryBackend` factories only.
- Remove any stale Linux tracker implementation residue or unused imports from `window_tracking.py` now that Stage `2.2` has moved the Linux tracker classes behind backend-owned modules.
- Leave only generic platform top-level branching where necessary (for example, Windows vs Linux vs unsupported OS), and keep the current status-driven Wayland fallback log path intact.
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
| 3.1 | Expose client-authoritative backend status to plugin preferences via the existing plugin/client socket path, with `plugin_hint` retained as labeled fallback | Completed |
| 3.2 | Retire the separate `force_xwayland` setting in favor of explicit manual `xwayland_compat` fallback/override semantics (restart required) | Completed |
| 3.3 | Centralize backend-owned override-choice metadata so prefs stop deriving backend choices from raw compositor branches | Completed |
| 3.4 | Remove backend status from the Overlay Controller title bar and add backend choice to the lower-left debug/test-overlay metrics area | Completed |
| 3.5 | Audit and shrink-wrap residual OS-specific checks in generic runtime modules, removing only the ones that encode backend policy | Completed |
| 3.6 | Document the retained intentional boundaries (`load.py`, installer/deployment logic, `plugin_hint`) and archive/supersede any notes that imply broader cleanup is still complete | Completed |

#### Stage 3.1 Detailed Plan
- Objective:
- Expose client-authoritative backend status to plugin preferences without introducing a second backend authority.
- Primary touch points:
- `overlay_client/launcher.py`
- `load.py`
- `overlay_plugin/preferences.py`
- `overlay_client/tests/test_backend_status.py`
- `tests/test_preferences_panel_controller_tab.py`
- `tests/test_harness_backend_status_roundtrip.py`
- Steps:
- Add or extend the existing plugin/client socket path so the plugin can request client-authoritative backend status (`source=client_runtime`) rather than only plugin shadow status, using a plugin->client request event and a client->plugin CLI response over the already-open local connection.
- Use a request/response status contract over that existing local socket path rather than introducing pushed status updates for this phase.
- Keep the request path lightweight for the Tk preferences poll by caching recent client-runtime responses in the plugin runtime and only performing synchronous request attempts when the cached runtime status is stale enough to need refresh.
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
- `overlay_client/backend/contracts.py`
- `overlay_client/backend/probe.py`
- `overlay_client/backend/consumers.py`
- `overlay_client/backend/selector.py`
- `overlay_client/platform_context.py`
- `overlay_client/platform_integration.py`
- `overlay_client/client_config.py`
- `overlay_client/control_surface.py`
- `overlay_client/developer_helpers.py`
- `overlay_client/window_tracking.py`
- `overlay_client/launcher.py`
- `overlay_client/setup_surface.py`
- `overlay_plugin/preferences.py`
- `overlay_plugin/overlay_config_payload.py`
- `overlay_client/tests/test_backend_selector.py`
- `overlay_client/tests/test_platform_context.py`
- `overlay_client/tests/test_client_config.py`
- `overlay_client/tests/test_platform_controller_backend_status.py`
- `tests/test_overlay_config_payload.py`
- `tests/test_preferences_persistence.py`
- `tests/test_preferences_panel_controller_tab.py`
- `tests/test_harness_backend_override_roundtrip.py`
- `tests/test_harness_backend_selection_wiring.py`
- `tests/test_lifecycle_tracking.py`
- Steps:
- Remove the user-facing `force_xwayland` setting from prefs/config/bootstrap payloads and stop emitting `EDMC_OVERLAY_FORCE_XWAYLAND` as part of normal backend control flow.
- Migrate persisted `force_xwayland=true` state to explicit `manual_backend_override="xwayland_compat"` semantics where needed so existing users keep the same fallback intent.
- Treat XWayland startup transport as what it really is: an explicit startup transport override to the `xwayland_compat` backend. Under `Auto`, do not silently launch `QT_QPA_PLATFORM=xcb`; only an explicit manual backend override to `xwayland_compat` may drive `QT_QPA_PLATFORM=xcb` on Wayland.
- Keep the running client truthful while that transport change is pending: when switching into `xwayland_compat` from a live Wayland runtime, save the override immediately but do not push a live overlay-config context update that would make the current runtime claim XWayland before restart.
- Make the user-facing surface explicit that `xwayland_compat` is restart-required, because Qt platform transport cannot be switched in-process after launch.
- Backend override selection is made in plugin preferences. When a selected override changes Qt startup transport, the preference change is saved immediately but surfaced in the preferences status area as pending until restart. Preferences must show that the current runtime backend remains unchanged until the overlay client is explicitly restarted, and must not imply that the backend switch has already applied live. The existing `Restart Overlay Client` action should remain the explicit apply path for restart-required backend changes.
- Preserve `xwayland_compat` as a named explicit fallback backend and do not silently remove the compatibility path.
- Acceptance criteria:
- No user-facing or persisted `force_xwayland` setting remains in the normal backend-control path.
- Explicit `xwayland_compat` fallback/override still works end to end, including launch-time Qt platform selection and restart-required UX.
- `Auto` no longer behaves like a hidden XWayland-force toggle and never silently launches `QT_QPA_PLATFORM=xcb`.
- Changing to explicit `xwayland_compat` while a native Wayland client is already running leaves the current runtime/backend status unchanged until restart instead of falsely claiming XWayland immediately.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_platform_context.py overlay_client/tests/test_client_config.py overlay_client/tests/test_platform_controller_backend_status.py tests/test_overlay_config_payload.py tests/test_preferences_persistence.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_override_roundtrip.py tests/test_harness_backend_selection_wiring.py tests/test_lifecycle_tracking.py -q`

#### Stage 3.3 Detailed Plan
- Objective:
- Move override-choice policy out of preferences-specific OS/compositor branching.
- Primary touch points:
- `overlay_client/backend/contracts.py`
- `overlay_client/backend/override_options.py`
- `overlay_client/backend/__init__.py`
- `load.py`
- `overlay_plugin/preferences.py`
- `overlay_client/tests/test_backend_override_options.py`
- `tests/test_preferences_panel_controller_tab.py`
- `tests/test_harness_backend_override_roundtrip.py`
- Steps:
- Add backend-owned override-choice metadata so valid override choices and restart-required rules come from backend registry metadata rather than preferences-specific OS/compositor mapping logic. `overlay_client/backend/contracts.py` may define the metadata shape, but the concrete option data and availability rules should live in a backend-owned metadata module rather than in `status.py` or preferences.
- Update preferences and the plugin runtime to consume that backend-owned metadata instead of rebuilding the choice list or restart-required rule from raw `operating_system`, `session_type`, and `compositor` branches.
- Keep UI behavior and override persistence unchanged.
- Acceptance criteria:
- Preferences no longer encode compositor mapping tables for backend override choices.
- Override-choice availability rules and restart-required metadata live in backend-owned metadata rather than `status.py`, `load.py`, or preferences-local policy code.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_override_options.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_override_roundtrip.py -q`

#### Stage 3.4 Detailed Plan
- Objective:
- Correct the remaining backend-status visibility surfaces.
- Primary touch points:
- `overlay_controller/overlay_controller.py`
- `overlay_client/debug_cycle_overlay.py`
- `overlay_client/render_surface.py`
- `overlay_client/tests/test_debug_overlay_view.py`
- `overlay_controller/tests/test_backend_status_title.py`
- Steps:
- Remove backend-status formatting from the Overlay Controller title bar and leave the controller title at its base title for now; `overlay_controller/overlay_controller.py` should stop consuming backend-title formatting helpers rather than reshaping backend status payloads.
- Add backend choice to the existing client-side debug diagnostics panel rendered by `DebugOverlayView`, using the current client backend-status snapshot already maintained on the overlay window rather than inventing a second diagnostics source.
- Keep the debug/test-overlay addition scoped to the existing diagnostics panel content and placement logic rather than expanding controller UI or adding a new metrics widget/surface.
- Acceptance criteria:
- Overlay Controller title bar no longer shows backend status.
- The debug/test-overlay diagnostics panel includes backend choice information from the current client runtime status.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_debug_overlay_view.py overlay_controller/tests/test_backend_status_title.py -q`

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
- `overlay_client/tests/test_interaction_controller.py`
- Steps:
- Audit remaining `sys.platform` / Wayland checks and classify each one as either generic UI/windowing behavior or leaked backend policy.
- Treat as acceptable only the mechanical compatibility or API-availability guards that do not select a backend, instantiate backend-specific implementations, or recreate fallback/support/override logic from raw platform/session/compositor inputs.
- Remove or redirect only the stale checks that no longer serve even that generic compatibility role; in the current code, this primarily means trimming dead residual helpers rather than reworking the retained force-render, transient-parent, standalone-mode, or runtime-status guards that already delegate to backend-owned status/controller APIs.
- Retain only the generic guards that do not encode backend-family/compositor policy.
- Acceptance criteria:
- Residual generic checks are minimal and explicitly justifiable.
- No remaining runtime module outside backend decides Linux compositor/backend policy locally.
- Any retained non-backend guard can be explained as a generic compatibility/windowing check rather than backend-policy leakage.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_control_surface_platform_context.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py -q`

#### Stage 3.6 Detailed Plan
- Objective:
- Make the intentional non-backend boundaries explicit so future audits do not treat them as accidental leakage.
- Primary touch points:
- `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md`
- `docs/refactoring/fix219_cross_platform_overlay_architecture_research.md`
- `docs/archive/refactoring/load_refactory.md`
- `docs/archive/refactoring/compositor_aware_install.md`
- `docs/archive/refactoring/client_refactor.md`
- `docs/archive/refactoring/refactor-plan.md`
- `load.py` (reference/comment-only if needed)
- `scripts/install_linux.sh` (reference/comment-only if needed)
- `scripts/install_matrix.json` (reference-only)
- Steps:
- Update docs to state explicitly that plugin launch/orchestration, `plugin_hint`, Flatpak/env shaping, and installer compositor profiles are retained boundaries.
- Refresh the top-level narrative in this follow-up plan so the current audit/gap snapshot reflects the post-Phase-`3.5` state rather than repeating already-closed Phase `1`-`3.5` gaps as if they were still active.
- Update the original refactor plan and architecture research doc anywhere completion is summarized so retained control-plane and deployment boundaries are explicit at the same level as the completed backend-cutover story.
- Annotate the archived refactor notes that still read like live planning documents so they are clearly historical and do not supersede the active `fix219_` boundary decisions.
- Keep this stage documentation-first: `load.py` and `scripts/install_linux.sh` may receive boundary comments/annotations if helpful, but this stage should not change launch or installer behavior, and `scripts/install_matrix.json` should only be referenced/documented unless a later plan explicitly broadens scope.
- Record any remaining cleanup deferrals clearly if a stage finishes with intentional exceptions.
- Keep the `standalone_mode` boundary explicit: Windows standalone behavior is preserved as-is during `fix219`, while Linux standalone behavior/support remains deferred to a separate post-`fix219` feature/validation plan.
- Keep the physical-clamp boundary explicit: it remains a shared geometry/follow escape hatch during `fix219`, and any deeper coordinate-space redesign or override-identity cleanup is deferred to a separate post-`fix219` geometry/follow plan.
- Keep the Windows boundary explicit: Windows behavior is preserved and regression-validated during `fix219`, while deeper Windows backend-contract cleanup remains a named post-`fix219` architecture track rather than an unplanned omission.
- Archive or annotate any refactor notes that incorrectly imply all platform-specific runtime ownership is already inside backend.
- Acceptance criteria:
- The follow-up architecture boundary is documented precisely.
- The follow-up plan no longer presents already-completed Phase `1`-`3.5` cleanup items as current unresolved gaps.
- Archived refactor notes are visibly historical and point readers back to the active `fix219_` boundary documents.
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

### Phase 4: Backend Contract Tightening
- Tighten the public backend contract surface before release-readiness signoff.
- The goal is to make the backend layer behavior-oriented rather than primarily identity-oriented, so generic consumers stop depending on undeclared methods and enum/family inference.
- Risks: overreaching into a second architecture project, or changing runtime behavior while trying to improve the contract shape.
- Mitigations: keep this phase contract-first and behavior-preserving, use targeted unit tests around the public protocol surface, and avoid re-opening already-completed ownership work unless the looser contract shape genuinely forces it.

#### Phase 4 Preflight Notes
- `4.1` scope guard:
  - promote only the methods that generic consumers already require today
  - do not use `4.1` to redesign the public contract shape under the label of "tightening"
- `4.2` capability-shape guard:
  - define only the smallest explicit capability metadata set needed to replace current enum/family inference
  - expected first candidates are:
    - tracker availability
    - transient-parent requirement
    - click-through/windowing expectation
    - compatibility/fallback transport expectation
- `HelperIpcBackend` guard:
  - enrich the public helper contract only if generic runtime consumers truly need more than helper identity
  - otherwise keep the helper boundary narrow in `fix219` and defer richer helper-runtime semantics to a later plan
- Implementation rule:
  - if a Phase `4` change would merge, split, or redefine the intended public backend contracts rather than merely tightening them, stop and record it as a new architecture decision instead of folding it into this plan silently

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Strengthen the public backend protocols so required runtime behavior is declared rather than discovered through `getattr(...)` | Completed |
| 4.2 | Move semantic bundle capabilities out of enum/family inference and into explicit backend-declared metadata/capabilities | Completed |
| 4.3 | Lock the tightened contract shape with focused protocol-level tests and refresh the active docs to reflect the stronger public contract | Completed |

#### Stage 4.1 Detailed Plan
- Objective:
- Make the public backend protocols accurately describe the behavior that runtime consumers require.
- Primary touch points:
- `overlay_client/backend/contracts.py`
- `overlay_client/backend/consumers.py`
- `overlay_client/backend/bundles/native_x11.py`
- `overlay_client/backend/bundles/xwayland_compat.py`
- `overlay_client/backend/bundles/_wayland_common.py`
- `overlay_client/tests/test_backend_contracts.py`
- `overlay_client/tests/test_backend_consumers.py`
- Steps:
- Promote required runtime methods onto the public protocols instead of relying on `getattr(...)` checks in bundle consumers, specifically for:
  - `TargetDiscoveryBackend`
  - `PresentationBackend`
  - `InputPolicyBackend` only where a generic consumer already requires a concrete method today
- Keep `HelperIpcBackend` narrow in this stage unless the actual generic runtime consumer seam proves it needs more than identity metadata.
- Keep the first tightening pass behavior-preserving: bundle implementations may stay combined where that is the current shipped shape, but the public protocol surface must stop pretending the already-required discovery/presentation methods are optional.
- Update the consumer helpers so they depend on the declared contract rather than probing for undeclared methods at runtime.
- Acceptance criteria:
- Bundle consumers no longer use `getattr(...)` to discover required backend behavior.
- Runtime Linux bundle implementations conform to the declared public protocols used by current generic consumers.
- No intentional runtime behavior change is introduced in this stage.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_consumers.py -q`

#### Stage 4.2 Detailed Plan
- Objective:
- Move semantic bundle behavior out of enum/family inference and into explicit backend-declared capabilities.
- Primary touch points:
- `overlay_client/backend/contracts.py`
- `overlay_client/backend/consumers.py`
- `overlay_client/backend/bundles/native_x11.py`
- `overlay_client/backend/bundles/xwayland_compat.py`
- `overlay_client/backend/bundles/_wayland_common.py`
- `overlay_client/tests/test_backend_contracts.py`
- `overlay_client/tests/test_backend_consumers.py`
- `overlay_client/tests/test_backend_bundles_x11.py`
- `overlay_client/tests/test_backend_bundles_wayland.py`
- `overlay_client/tests/test_platform_controller_backend_status.py`
- Steps:
- Replace helper logic in bundle consumers that infers backend behavior from family/instance labels with explicit bundle-declared capability metadata, specifically for:
  - tracker availability
  - transient-parent requirements
  - native-Wayland vs X11-style windowing expectation
  - tracker fallback transport expectation by session type
- Keep this stage minimal and behavior-preserving: do not add unused capability metadata merely because it might be useful later, and do not move support-family/status-report formatting out of the existing status model.
- Keep human-readable labels intact by sourcing the current platform-label helper from backend-declared metadata rather than from family/instance branching.
- Acceptance criteria:
- Generic consumers query explicit backend capabilities rather than inferring behavior from enums or helper-specific family checks.
- Bundle-facing tests fail if a bundle exposes the wrong capability behavior.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_platform_controller_backend_status.py -q`

#### Stage 4.3 Detailed Plan
- Objective:
- Lock the tightened contract shape and document it clearly before moving into release-readiness evidence work.
- Primary touch points:
- `overlay_client/backend/contracts.py`
- `overlay_client/tests/test_backend_contracts.py`
- `overlay_client/tests/test_helper_ipc_boundary.py`
- `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md`
- Steps:
- Add focused contract-level tests that prove the tightened public shape directly rather than only testing bundle identity and selector output, specifically for:
  - explicit `BackendCapabilities` behavior
  - the still-intentional combined `presentation` / `input_policy` adapter shape during `fix219`
  - the intentionally narrow split between generic `HelperIpcBackend` identity metadata and transport/message validation in `helper_ipc.py`
- Document the current landing shape explicitly:
  - capability truth now lives in `BackendCapabilities`
  - Linux bundles intentionally keep a combined presentation/input runtime adapter during `fix219`
  - helper transport validation remains owned by `helper_ipc.py`, while `HelperIpcBackend` stays narrow unless later runtime work requires more
- Refresh the active `fix219_` docs so the strengthened contract surface is reflected before the final validation/signoff phase begins, including rolling the plan snapshots forward from Phase `4` as next work to Phase `5` as next work when this stage completes.
- Acceptance criteria:
- The tightened contract is covered by focused protocol-level tests.
- The active docs describe the strengthened contract shape accurately.
- Phase `4` no longer appears as an open remaining gap once this stage is complete.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_helper_ipc_boundary.py -q`

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- Public backend protocols describe the required runtime behavior directly.
- Generic consumers no longer depend on undeclared backend methods or enum/family inference for capability truth.
- The active `fix219_` docs reflect the tightened contract shape before signoff work begins.

### Phase 4A: XWayland Compatibility Honesty Cutover
- Land a narrow truthfulness update before release-readiness signoff so the shipped status model stops overstating the Wayland `xwayland_compat` compatibility path.
- Scope guard: this phase changes selector/status truthfulness only. It must not remove `xwayland_compat`, redesign startup transport, or change the actual runtime backend behavior of the compatibility path.
- Risks: surprising users/support with a new degraded label, or accidentally broadening the work into a transport/backend redesign rather than a status-policy correction.
- Mitigations: keep fallback metadata and manual-override behavior intact, keep the schema stable, cover the cutover with focused unit/harness tests, and update the active docs before Phase `5` validation treats the new output as release-ready evidence.

#### Phase 4A Preflight Notes
- `4A.1` policy guard:
  - keep backend selection and runtime behavior unchanged; only the reported support classification changes
  - preserve `fallback_from` and `fallback_reason=xwayland_compat_only` so support can still see why the compatibility backend was chosen
- `4A.2` surface guard:
  - keep `review_required` in the payload/report schema for compatibility, but stop using it for the Wayland `xwayland_compat` case once the classification is honest
  - update UI/debug wording only as needed to reflect the honest `degraded_overlay` result
- `4A.3` validation guard:
  - re-prove explicit manual override and restart-required behavior end to end
  - if a real Wayland validation environment is not available, record that the behavior change is test-backed and defer manual confirmation explicitly rather than inventing signoff evidence

| Stage | Description | Status |
| --- | --- | --- |
| 4A.1 | Flip the shipped selector/status policy so Wayland `xwayland_compat` reports `degraded_overlay` instead of transitional `true_overlay` | Completed |
| 4A.2 | Update selector/status/preferences/debug coverage so all user-visible surfaces reflect the honest degraded classification consistently | Completed |
| 4A.3 | Re-validate explicit `xwayland_compat` override behavior, then refresh active docs/release notes so Phase `5` signoff uses the honest shipped classification | Completed |

#### Stage 4A.1 Detailed Plan
- Objective:
- Make the shipped selector/status result for Wayland `xwayland_compat` truthful without changing which backend launches or how it runs.
- Primary touch points:
- `overlay_client/backend/selector.py`
- `overlay_client/backend/status.py`
- `overlay_client/tests/test_backend_selector.py`
- `overlay_client/tests/test_backend_status.py`
- Steps:
- Remove the conservative selector rewrite that currently upgrades strict `degraded_overlay` to shipped `true_overlay` for Wayland `xwayland_compat`.
- Keep `fallback_from` and `fallback_reason=xwayland_compat_only` intact so the compatibility downgrade remains explicit in diagnostics.
- Stop using `review_required=no_silent_downgrade:xwayland_compat` for this path once the reported classification matches the strict classification.
- Keep the payload/report schema stable: `review_required` and `review_reasons` may remain present but should be false/empty for this case.
- Acceptance criteria:
- Wayland sessions running Qt `xcb` still select `xwayland_compat`.
- The selected backend remains unchanged, but the reported classification becomes `degraded_overlay`.
- No startup transport, manual override, or bundle/runtime behavior changes are introduced in this stage.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py -q`

#### Stage 4A.2 Detailed Plan
- Objective:
- Keep every user-visible/backend-visible status surface aligned once the honest degraded classification ships.
- Primary touch points:
- `overlay_client/tests/test_backend_selector.py`
- `overlay_client/tests/test_backend_status.py`
- `tests/test_preferences_panel_controller_tab.py`
- `tests/test_harness_backend_status_roundtrip.py`
- `tests/test_harness_backend_override_roundtrip.py`
- `overlay_client/tests/test_debug_overlay_view.py`
- Steps:
- Update selector and status expectations that currently lock the transitional `true_overlay + review_required` combination for Wayland `xwayland_compat`.
- Update preferences/debug/status-surface coverage so summaries and warnings describe `xwayland_compat` as a degraded compatibility path instead of a true-overlay path.
- Reconfirm that explicit manual override to `xwayland_compat` remains restart-required and continues to report as a manual compatibility selection rather than as an invalid or implicit fallback.
- Acceptance criteria:
- Unit and harness coverage agree on the new `degraded_overlay` result for Wayland `xwayland_compat`.
- Preferences/debug/status surfaces remain internally consistent and continue to expose fallback/manual-override metadata correctly.
- Verification to run:
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_status_roundtrip.py tests/test_harness_backend_override_roundtrip.py overlay_client/tests/test_debug_overlay_view.py -q`

#### Stage 4A.3 Detailed Plan
- Objective:
- Make the honesty cutover part of the active `fix219` narrative before Phase `5` validation/signoff consumes the new output as evidence.
- Primary touch points:
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md`
- `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- `RELEASE_NOTES.md`
- `/home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log`
- Steps:
- If a real Wayland environment is available, confirm that explicit `xwayland_compat` override still launches the overlay with `QT_QPA_PLATFORM=xcb` and that runtime status now reports `degraded_overlay`.
- If a real Wayland environment is not available, record that limitation explicitly and carry the manual confirmation into Phase `5.1` rather than implying it was already re-validated.
- Refresh the active docs/release notes so they describe the shipped `xwayland_compat` status as an explicit degraded compatibility path rather than a conservative temporary `true_overlay` classification.
- Acceptance criteria:
- The active docs no longer describe the transitional `true_overlay` reporting as current behavior.
- Any manual-validation gap remains explicit rather than implied complete.
- Verification to run:
- Record exact commands, environments, and outcomes in the `Execution Log`; include any targeted automated tests run alongside the manual checks.

#### Phase 4A Execution Order
- Implement in strict order: `4A.1` -> `4A.2` -> `4A.3`.

#### Phase 4A Exit Criteria
- Wayland `xwayland_compat` reports as `degraded_overlay` in shipped status surfaces.
- `xwayland_compat` remains available as an explicit manual compatibility override with unchanged runtime behavior.
- The active `fix219_` docs reflect the honest compatibility classification before Phase `5` validation/signoff begins.

### Phase 5: Validation, Compliance, And Signoff
- Close the remaining release-readiness gaps after the ownership/status cleanup and contract-tightening work land.
- Keep this phase evidence-driven: record exact environments checked, exact compliance findings, and any explicit limitations retained at signoff time.
- Risks: declaring completion based only on tests and refactor shape while remaining compositor/helper paths or EDMC compliance edges are still unverified.
- Mitigations: require recorded environment results, recorded compliance findings, and an explicit closeout of the release signoff checklist before calling the cleanup complete.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Run the remaining compositor/helper validation matrix and record exact environment results and retained limitations | Not Started |
| 5.2 | Run and record the EDMC compliance review after the refactor cleanup is complete | Not Started |
| 5.3 | Close the release signoff checklist and record any final deferrals or explicit limitations | Not Started |

#### Stage 5.1 Detailed Plan
- Objective:
- Replace the current “known validation gap” state with recorded environment evidence for the remaining claimed paths.
- Primary touch points:
- `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md`
- `RELEASE_NOTES.md`
- `/home/jon/edmc-logs/EDMarketConnector-debug.log`
- `/home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log`
- Steps:
- Collect any already-recorded real-environment evidence from the current EDMC/plugin/client logs first so the stage does not ignore existing runs.
- Re-run or confirm the minimum closure matrix environments required for `fix219`: Windows baseline, `native_x11`, explicit `xwayland_compat`, and one recorded KWin Wayland run.
- As part of that closure matrix, explicitly validate that manual backend override authority still works end to end and remains the effective user-facing override over `Auto`, including the restart-required `xwayland_compat` path.
- If additional wlroots/Hyprland/COSMIC/gamescope or helper-backed Wayland testers are available, record those runs too; otherwise mark those environments deferred and remove any implied signoff claim that they were fully validated in this plan.
- Record each checked environment as pass, fail, unsupported, or deferred, with the exact limitation or follow-up needed.
- Record or confirm the final claimed support classification for each checked environment (`true_overlay`, `degraded_overlay`, `unsupported`) and the concrete reason when the result is not `true_overlay`.
- Apply the classification evidence rule explicitly: no environment receives a final support classification from code inspection alone; `true_overlay` requires demonstrated full claimed behavior with no material unresolved limitation, `degraded_overlay` requires demonstrated partial behavior with an explicit weakened guarantee and concrete reason, `unsupported` requires recorded evidence that the required support bar is not met or not implemented, and any environment lacking sufficient recorded evidence remains deferred.
- If the minimum closure matrix cannot be satisfied from the available real runs and logs, stop the stage and record the missing evidence explicitly rather than promoting inferred results into signoff claims.
- Do not silently broaden support claims if validation reveals a weaker support story than planned.
- Acceptance criteria:
- The minimum closure matrix has recorded evidence rather than an unspecified validation gap.
- Claimed support classifications and reasons are explicit for the environments covered by signoff.
- Any environment still lacking sufficient evidence remains explicitly deferred rather than silently promoted to a claimed support tier.
- Any retained limitation is explicit in docs/release notes.
- Verification to run:
- Record exact commands, environments, and outcomes in the `Execution Log`; include any supporting automated tests run alongside the manual checks.

#### Stage 5.2 Detailed Plan
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

#### Stage 5.3 Detailed Plan
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

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
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
- Stage `1.1` completed on 2026-04-03.
- Refined Stage `1.1` in this plan before code changes so the touch points match the current bundle/consumer layout, including the X11/XWayland bundle modules, native Wayland bundle modules, and `overlay_client/backend/consumers.py`.
- Added test-only coverage to lock the current combined presentation/input backend shape per bundle, shared XCB-vs-Wayland integration routing, and current `uses_transient_parent()` / platform-label policy outcomes across explicit bundle identities.
- Runtime behavior was unchanged in this stage.
- Stage `1.2` completed on 2026-04-03.
- Refined Stage `1.2` in this plan before code changes so the exact extraction scope matched the current code: move the generic shared integration base into `overlay_client/window_integration.py`, move the shipped Linux XCB/Wayland integration implementations into `overlay_client/backend/bundles/_linux_window_integration.py`, and re-point the backend bundle modules at those backend-owned factories.
- Preserved the current shipped behavior by keeping Windows integration ownership in `platform_integration.py`, keeping the Linux bundle-facing factory names unchanged, and changing only implementation ownership for Linux runtime presentation/input behavior.
- Stage `1.3` completed on 2026-04-03.
- Refined Stage `1.3` in this plan before code changes so the remaining work matched the actual code state: `PlatformController` was already delegating through backend consumers, so the stage only needed to remove stale Linux integration imports/residue from `platform_integration.py` and leave it as a generic bundle-consumer facade.
- Runtime behavior remained unchanged in both Stage `1.2` and Stage `1.3`.

### Tests Run For Phase 1
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_consumers.py -q` -> failed before setup because `.venv/bin/activate` did not exist.
- `python3 -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_consumers.py -q` -> failed during collection because `PyQt6` was not installed in the system Python.
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_consumers.py -q` -> passed (`34` passed).
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_platform_controller_backend_status.py -q` -> passed (`37` passed).
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_backend_consumers.py -q` -> passed (`22` passed).

### Phase 2 Execution Summary
- Stage `2.1` completed on 2026-04-03.
- Refined Stage `2.1` in this plan before code changes so the test scope matched the actual tracker contract edges in the code: status-driven bundle selection, the current X11-vs-Wayland fallback rules, and pass-through of `title_hint` / `monitor_provider` through both primary and fallback tracker creation attempts.
- Added unit coverage that locks the X11 fallback bundle rule and the current `create_elite_window_tracker(...)` pass-through contract without moving any runtime tracker implementation code yet.
- Kept the existing harness shadow-backend-status publication test as the upstream status-wiring guard for later tracker stages; runtime behavior was unchanged in this stage.
- Stage `2.2` completed on 2026-04-03.
- Refined Stage `2.2` in this plan before code changes so the extraction matched the actual code seams: move the Linux tracker implementations into `overlay_client/backend/bundles/_linux_trackers.py`, move shared tracker primitives into `overlay_client/window_tracking_support.py`, and leave the public entrypoint plus Windows tracker in `overlay_client/window_tracking.py`.
- Preserved current shipped tracker behavior by moving the Linux tracker implementations intact behind backend-owned discovery modules, keeping factory names and tracker class names unchanged, and re-pointing the bundle modules at the backend-owned factories.
- Stage `2.3` completed on 2026-04-03.
- Refined Stage `2.3` in this plan before code changes so the remaining work matched the post-extraction code state: `window_tracking.py` was already status-driven, so the stage only needed to remove stale Linux-tracker residue and leave the file as a generic runtime entrypoint plus the Windows tracker.
- Runtime behavior remained unchanged in both Stage `2.2` and Stage `2.3`.

### Tests Run For Phase 2
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_backend_consumers.py tests/test_harness_backend_selection_wiring.py -q` -> passed (`28` passed).
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_backend_consumers.py -q` -> passed (`42` passed).
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py -q` -> passed (`31` passed).

### Phase 3 Execution Summary
- Stage `3.1` completed on 2026-04-03.
- Refined Stage `3.1` in this plan before code changes so the actual transport seam matched the codebase: request/response wiring lives in `load.py` and `overlay_client/launcher.py`, not in `overlay_client/data_client.py`.
- Added a lightweight plugin->client request event plus client->plugin CLI reply path over the existing local socket connection, backed by a short-lived plugin cache so preferences can use fresh `client_runtime` status without turning every poll into a blocking request.
- Preserved existing fallback behavior by keeping `plugin_hint` as the advisory fallback when no fresh client-runtime status is available; selector authority did not change.
- Stage `3.2` completed on 2026-04-03.
- Refined Stage `3.2` in this plan before code changes so the actual behavior-change surface matched the codebase: retire `force_xwayland` from the normal preferences/bootstrap/runtime path, remove it from the backend probe/selector contracts, split requested-vs-runtime-applied backend override handling inside `load.py`, and update preferences so `xwayland_compat` is surfaced as restart-required without making the running client claim XWayland before restart.
- Implemented the approved behavior change by migrating legacy persisted `force_xwayland=true` state to explicit `manual_backend_override="xwayland_compat"`, deriving XWayland startup only from explicit manual override plus launch-time `QT_QPA_PLATFORM=xcb`, and removing the old `EDMC_OVERLAY_FORCE_XWAYLAND`/`force_xwayland` normal-control plumbing from runtime payloads, platform context, and selector inputs.
- Kept the running client truthful by separating requested manual override from runtime-applied manual override inside the plugin runtime: live `platform_context` payloads now keep the current runtime backend stable until restart, while plugin shadow status can still reflect the pending requested fallback/override as advisory information.
- Stage `3.3` completed on 2026-04-03.
- Refined Stage `3.3` in this plan before code changes so the metadata-owner cleanup matched the actual code seams: define the override-option metadata shape in `overlay_client/backend/contracts.py`, move the concrete option table and restart-required rules into `overlay_client/backend/override_options.py`, re-export them through `overlay_client/backend/__init__.py`, and repoint both prefs and `load.py` at the backend-owned helpers.
- Moved backend override-choice availability and restart-required metadata out of preferences-specific raw probe branching and into backend-owned metadata while keeping the UI option list, persistence flow, and restart-required behavior unchanged.
- Added focused unit coverage for backend-owned override-option availability and restart-required semantics, then re-ran the existing preferences and harness roundtrip coverage to prove the wiring stayed intact.
- Stage `3.4` completed on 2026-04-03.
- Refined Stage `3.4` in this plan before code changes so the user-visible status-surface cleanup matched the actual code seams: stop `overlay_controller/overlay_controller.py` from consuming backend-title formatting helpers, and thread the existing client backend-status snapshot into `DebugOverlayView` via `overlay_client/render_surface.py` instead of inventing a new diagnostics surface.
- Removed backend status from the Overlay Controller window title while keeping backend visibility available in the existing client-side debug diagnostics panel, which now includes the chosen backend, source, and mode from the current client runtime status.
- Added direct view-level coverage for the debug overlay backend block and updated the controller title tests to lock the restored base-title behavior.
- Stage `3.5` completed on 2026-04-03.
- Refined Stage `3.5` in this plan before code changes so the audit matched the actual code state: the remaining live branches in `follow_surface.py`, `interaction_controller.py`, and `control_surface.py` are generic compatibility/windowing guards or calls into backend-owned status/controller APIs, while the only stale residue left in scope was an unused `_is_wayland()` helper in `overlay_client/overlay_client.py`.
- Removed that dead residual helper and left the retained generic guards intact, recording the stage as an audited shrink-wrap rather than a broader runtime rewrite.
- Verified the retained force-render, transient-parent, runtime-status, and interaction-controller paths still behave as expected through the existing unit coverage.
- Stage `3.6` completed on 2026-04-03.
- Refined Stage `3.6` in this plan before code changes so the actual work matched the remaining documentation debt: refresh the current-state snapshot in this follow-up plan, make retained control-plane/deployment boundaries explicit in the top-level `fix219_` docs, and annotate the archived refactor notes that still read like live planning documents.
- Updated the active `fix219_` docs to state consistently that `load.py`, advisory `plugin_hint`, Flatpak/env shaping, and installer compositor profiles are intentional retained boundaries, while the remaining open work now starts with Phase `4` backend-contract tightening followed by Phase `5` validation/compliance/signoff.
- Added historical markers to the archived `load_refactory.md`, `compositor_aware_install.md`, `client_refactor.md`, and `refactor-plan.md` notes so they no longer read as active backend-boundary authority.

### Tests Run For Phase 3
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_status_roundtrip.py -q` -> failed on the first attempt because a new preferences assertion accidentally captured current Stage `3.3` override-choice behavior instead of only Stage `3.1` status-source behavior.
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_status_roundtrip.py -q` -> passed (`23` passed).
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_platform_context.py overlay_client/tests/test_client_config.py overlay_client/tests/test_platform_controller_backend_status.py tests/test_overlay_config_payload.py tests/test_preferences_persistence.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_override_roundtrip.py tests/test_harness_backend_selection_wiring.py tests/test_lifecycle_tracking.py -q` -> passed (`56` passed).
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_override_options.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_override_roundtrip.py -q` -> passed (`21` passed).
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_debug_overlay_view.py overlay_controller/tests/test_backend_status_title.py -q` -> passed (`3` passed).
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_control_surface_platform_context.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py -q` -> passed (`13` passed).
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py overlay_client/tests/test_platform_context.py -q` -> passed (`13` passed).
- `source .venv/bin/activate && make check` -> passed (`ruff` clean, `mypy` clean, full suite `815` passed / `21` skipped).

### Phase 4 Execution Summary
- Stage `4.1` completed on 2026-04-03.
- Refined Stage `4.1` in this plan before code changes so the scope matched the actual consumer seam in the code: tighten the public discovery and presentation protocols, leave `InputPolicyBackend` unchanged because no generic consumer currently requires an input-policy method, and keep `HelperIpcBackend` narrow because no generic runtime consumer currently needs more than helper identity metadata.
- Declared the already-required `create_tracker(...)` and `create_integration(...)` methods on the public protocols in `overlay_client/backend/contracts.py`, then removed the `getattr(...)`-based runtime probing from `overlay_client/backend/consumers.py`.
- Kept bundle behavior unchanged by leaving the current combined Linux bundle implementations intact and tightening only the public contract surface they already satisfy.
- Expanded protocol coverage in `overlay_client/tests/test_backend_contracts.py` so both protocol fixtures and shipped Linux bundles are checked against the tightened runtime-checkable contract.
- Stage `4.2` completed on 2026-04-03.
- Refined Stage `4.2` in this plan before code changes so the scope matched the actual remaining inference seam: add explicit bundle capability metadata for platform label, native-Wayland vs X11-style windowing, transient-parent requirement, tracker availability, and tracker fallback by session type; do not broaden the stage into unused click-through metadata or status-surface redesign.
- Added explicit backend-declared capability metadata to `BackendBundle` in `overlay_client/backend/contracts.py`, threaded it through the Linux bundle builders in `native_x11.py`, `xwayland_compat.py`, and `_wayland_common.py`, and switched the generic consumer helpers in `overlay_client/backend/consumers.py` to read those declared capabilities instead of inferring behavior from backend family/instance labels.
- Preserved current behavior by keeping the human-readable platform labels unchanged, keeping the existing tracker-fallback outcomes unchanged, and leaving runtime bundle implementations intact while only changing where capability truth lives.
- Expanded bundle/consumer/contract coverage so tests now assert the explicit capability metadata on shipped bundles and prove the generic helper functions can follow capability metadata instead of descriptor-family inference.
- Stage `4.3` completed on 2026-04-03.
- Refined Stage `4.3` in this plan before code changes so the closure matched the actual remaining work: add focused contract tests for `BackendCapabilities`, explicitly lock the still-intentional combined Linux `presentation` / `input_policy` adapter shape during `fix219`, keep the helper-boundary split clear between narrow `HelperIpcBackend` identity and `helper_ipc.py` transport validation, and roll the active `fix219_` docs forward so Phase `5` is the next open work rather than Phase `4`.
- Expanded `overlay_client/tests/test_backend_contracts.py` with focused contract-shape coverage for explicit capability fallback mapping, full Linux bundle protocol conformance across the shipped bundle matrix, and the intentional combined presentation/input adapter shape.
- Expanded `overlay_client/tests/test_helper_ipc_boundary.py` so helper-boundary validation continues to lock the transport-specific surface separately from the generic helper identity contract.
- Refreshed the active `fix219_` docs so they now describe the landed contract shape explicitly:
  - `BackendCapabilities` is the generic runtime capability truth source
  - Linux bundles intentionally keep a combined presentation/input adapter during `fix219`
  - helper transport validation remains in `overlay_client/backend/helper_ipc.py`, while `HelperIpcBackend` stays narrow
  - Phase `5` is now the next active work
- Phase `4` is now complete: the public backend surface is behavior-oriented, generic consumers no longer rely on undeclared methods or family/instance inference for capability truth, and the active `fix219_` docs describe the tightened contract shape accurately.

### Tests Run For Phase 4
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_consumers.py -q` -> passed (`26` passed).
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_platform_controller_backend_status.py -q` -> passed (`46` passed).
- `source .venv/bin/activate && python -m ruff check overlay_client/backend/contracts.py overlay_client/backend/consumers.py overlay_client/backend/bundles/native_x11.py overlay_client/backend/bundles/xwayland_compat.py overlay_client/backend/bundles/_wayland_common.py overlay_client/backend/__init__.py overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_platform_controller_backend_status.py` -> passed.
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_helper_ipc_boundary.py -q` -> passed (`16` passed).
- `source .venv/bin/activate && python -m ruff check overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_helper_ipc_boundary.py` -> passed.

### Phase 4A Execution Summary
- Stage `4A.1` completed on 2026-04-04.
- Removed the transitional selector rewrite in `overlay_client/backend/selector.py` so Wayland `xwayland_compat` now reports its strict classification directly as `degraded_overlay` instead of shipping a softened `true_overlay` result with a review guard.
- Preserved runtime behavior and backend choice: Wayland + Qt `xcb` still selects `xwayland_compat`, fallback metadata remains explicit, and the payload/report schema still includes `review_required` fields even though this path no longer uses them.
- Stage `4A.2` completed on 2026-04-04.
- Updated unit and harness coverage to lock the honest degraded classification across selector, status formatting, preferences-facing status snapshots, plugin shadow status payloads, and explicit manual-override round-trips.
- Preserved the existing explicit manual `xwayland_compat` override semantics, including restart-required transport behavior, while making the user-visible status surfaces reflect the weaker compatibility guarantee truthfully.
- Stage `4A.3` completed on 2026-04-04.
- Refreshed the active `fix219_` docs and release notes so they no longer describe the conservative transitional `true_overlay` classification as current behavior for Wayland `xwayland_compat`.
- No real Wayland manual rerun was performed as part of this implementation step; explicit runtime confirmation of the unchanged `QT_QPA_PLATFORM=xcb` override path remains part of Phase `5.1` validation evidence rather than being implied complete here.
- Phase `4A` is now complete: shipped status/reporting is honest about the XWayland compatibility path, while backend selection and runtime behavior remain unchanged.

### Tests Run For Phase 4A
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_status_roundtrip.py tests/test_harness_backend_override_roundtrip.py overlay_client/tests/test_debug_overlay_view.py -q` -> passed (`42` passed).
- `source .venv/bin/activate && python -m pytest overlay_client/tests/test_platform_context.py tests/test_overlay_config_payload.py -q` -> passed (`10` passed).
- `source .venv/bin/activate && python -m ruff check overlay_client/backend/selector.py overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_platform_context.py tests/test_overlay_config_payload.py tests/test_harness_backend_override_roundtrip.py` -> passed.

### Phase 5 Execution Summary
- Not started.

### Tests Run For Phase 5
- None yet.
