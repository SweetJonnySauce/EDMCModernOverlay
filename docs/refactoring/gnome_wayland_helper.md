## Goal: Build GNOME Wayland helper-backed true overlay support without expanding `fix219`

This plan is separate from the `fix219_*` backend cleanup docs.
`fix219` established the backend architecture, helper boundary concepts, and support-classification vocabulary.
This plan owns the GNOME Wayland helper work itself: requirements, truthful status behavior, helper installation/enablement, helper IPC, and real-environment validation for attaching the overlay to the Elite Dangerous window on GNOME Wayland.

Current issue:
- GNOME Wayland without the helper currently reports `classification=true_overlay` while also reporting `fallback_reason=missing_helper` and `gnome_shell_extension:required:inactive:unapproved:none`.
- That is internally inconsistent for user-facing "Mode: True overlay" wording.
- This plan must correct the status truthfulness before claiming GNOME Wayland true-overlay support.

## Refactorer Persona
- Bias toward carving out modules aggressively while guarding behavior: no feature changes, no silent regressions.
- Prefer pure/push-down seams, explicit interfaces, and fast feedback loops (tests + dev-mode toggles) before deleting code from the monolith.
- Treat risky edges (I/O, timers, sockets, UI focus, GNOME Shell extension lifecycle) as contract-driven: write down invariants, probe with tests, and keep escape hatches to revert quickly.
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

## Requirements Draft

### Support Classification Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-SC-1 | GNOME Wayland without an installed/enabled helper must report `degraded_overlay`, not `true_overlay`. | The status may still show selected backend `native_wayland / gnome_shell_wayland`, but mode must be truthful. |
| R-SC-2 | GNOME Wayland without helper must preserve `fallback_reason=missing_helper` and identify `gnome_shell_extension` as required/unavailable. | Current helper diagnostics are useful and should remain visible. |
| R-SC-3 | GNOME Wayland with helper installed, enabled, approved, version-compatible, and reachable may report `true_overlay`. | True-overlay classification requires real helper availability plus validation evidence. |
| R-SC-4 | Preferences, debug overlay, logs, and diagnostic collector output must use the same backend classification and helper state. | Avoid one UI saying true while another says missing helper. |
| R-SC-5 | `plugin_hint` remains advisory; fresh `client_runtime` status remains authoritative. | Inherits `fix219` authority policy. |

### Helper Installation And Enablement Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-IN-1 | The plugin installer must run the GNOME Shell helper install flow when GNOME Wayland is detected and the user approves it. | User approval required. No silent install/enable. |
| R-IN-2 | The helper must also be installable after initial plugin install when the user switches from X11 to Wayland or changes desktop environment. | Q7 decision: first implementation handles this by surfacing a settings warning and instructing the user to rerun the installer while using GNOME Wayland, so the installer detects GNOME Wayland and runs the helper install flow; in-settings install/uninstall buttons are deferred. |
| R-IN-3 | A user must be able to see whether the helper is missing, installed but disabled, enabled but incompatible, or active. | Preferences/status surface should avoid vague "not working" states. |
| R-IN-4 | Helper install/enable operations must be explicit, understandable, and reversible. | GNOME extension enablement may require Shell restart/logout depending on GNOME version/session. |
| R-IN-5 | The installer must not claim the helper is installed merely because approval guidance was recorded. | `helper_approval.json` is approval metadata only, not runtime availability. |
| R-IN-6 | Manual installation from a packaged extension directory must be documented and testable. | Needed for distro/session variance and development builds. |
| R-IN-7 | Any required host tools or session services for the helper must be shown to the user before install/enable and in troubleshooting diagnostics. | If the chosen transport requires `gjs`, `gdbus`, `busctl`, `dbus-monitor`, a session bus, `gnome-extensions`, or similar host capabilities, the user must see clear prerequisite/pass/fail status. |
| R-IN-8 | Missing helper prerequisites must produce an actionable degraded/remediation state, not a silent install/runtime failure. | Example: "GNOME Shell DBus session not available" or "gjs missing; install GNOME JavaScript bindings." |
| R-IN-9 | The installer/preferences remediation path must detect when GNOME user extensions are globally disabled. | `org.gnome.shell disable-user-extensions=true` prevents a listed/enabled extension from becoming active; this must be surfaced distinctly from helper missing, disabled, or incompatible. |

### Extension Packaging Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-PK-1 | The extension must have a fixed UUID and install directory name. | Required for `gnome-extensions enable <uuid>`, upgrades, and support diagnostics. |
| R-PK-2 | The extension package must include valid GNOME metadata (`metadata.json`) with `uuid`, `name`, `description`, `shell-version`, and extension `version`. | Add manifest tests before runtime wiring depends on the package. |
| R-PK-3 | Release artifacts must define whether they ship source directory, zipped extension, checksums, or all of those. | The installer and manual install docs must consume the same artifact shape. |
| R-PK-4 | The plan must define user-install and system-install paths explicitly. | Default should prefer the user extension path unless a later installer decision justifies system-wide install. |
| R-PK-5 | The helper protocol version and extension version compatibility matrix must be documented. | Overlay client should reject incompatible helpers clearly. |
| R-PK-6 | The extension package must avoid bundling unrelated overlay client/runtime files. | Keep helper artifact small and auditable. |

### Install/Enable Lifecycle Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-LC-1 | The plan must define exact install, enable, disable, uninstall, and update commands. | Include both installer-driven and manual command paths. |
| R-LC-2 | The flow must handle `gnome-extensions` being missing, unusable, or unable to talk to the active Shell session. | This should become a visible remediation state, not a silent failure. |
| R-LC-3 | The flow must state when logout, Shell restart, or session restart is required. | GNOME Wayland often cannot restart Shell in-place like X11. |
| R-LC-4 | The plugin must detect "GNOME Wayland active, helper missing" after a user switches from X11 to Wayland or changes desktop environment. | Settings/status must warn and direct the user to rerun the installer while currently logged into GNOME Wayland. |
| R-LC-5 | Flatpak EDMC must be treated as a host-install problem for the GNOME Shell extension. | The extension belongs to the host Shell, not inside the EDMC Flatpak sandbox. |
| R-LC-6 | Install state must distinguish approval, copied/installed files, Shell-enabled state, protocol-compatible reachability, and active health. | Avoid collapsing all helper states into one boolean. |
| R-LC-7 | Manual extension copy must account for GNOME Shell discovery latency and session restart requirements. | On GNOME Wayland, a newly copied user extension may not appear in `gnome-extensions info/enable` until logout/login or another supported rescan/install path. |
| R-LC-8 | Extension active-state checks must include global user-extension enablement. | A UUID can be present in `enabled-extensions` while still inactive if user extensions are globally disabled. |

### Helper Runtime Contract Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-RT-1 | The helper must run as a GNOME Shell extension and expose a narrow, versioned helper boundary to the overlay client. | Existing `HelperIpcBackend` / `helper_ipc.py` concepts are the starting point. |
| R-RT-2 | The helper boundary must be local-only and fail closed on protocol/version/session-token mismatch. | No broad remote command surface. |
| R-RT-3 | The helper must publish enough target-window state for the overlay client to attach to the Elite Dangerous window. | At minimum: target identity, geometry, monitor/output context, focus/fullscreen/visibility state, and timestamps. |
| R-RT-4 | The helper must expose state transitions needed to maintain attachment across moves, resizes, monitor changes, focus changes, fullscreen/borderless transitions, and Shell restarts. | These are true-overlay requirements, not nice-to-have telemetry. |
| R-RT-5 | The helper must report degraded/unavailable reasons explicitly. | Examples: game not found, extension disabled, incompatible GNOME Shell version, missing permission/API, helper protocol mismatch. |
| R-RT-6 | The overlay client must treat helper data as authoritative for GNOME Wayland target discovery only when the helper is active and version-compatible. | Otherwise fallback remains degraded. |

### Runtime Detection Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-RD-1 | Runtime status must distinguish helper not installed, installed but disabled, enabled but unreachable, reachable but protocol-incompatible, and active/healthy. | These states drive user remediation and support triage. |
| R-RD-2 | The helper must send or expose a heartbeat/health signal with timeout and staleness rules. | Stale helper state must degrade predictably. |
| R-RD-3 | Logs must contain a stable line proving helper active state, helper version, protocol version, and selected backend classification. | Needed for diagnostics and validation evidence. |
| R-RD-4 | Helper detection must run in the overlay client runtime context and publish status back through the existing backend-status path. | Preserve client-authoritative status from `fix219`. |
| R-RD-5 | A disabled or incompatible helper must not allow `true_overlay` classification. | Helper presence alone is insufficient. |

### IPC And Transport Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-IPC-1 | The plan must choose a primary helper transport: session DBus, Unix socket under `$XDG_RUNTIME_DIR`, or a staged fallback between the two. | This is the next highest-priority design question after helper role. |
| R-IPC-2 | The plan must define which side owns the listener/service and which side initiates connections. | GNOME Shell extension lifecycle and overlay client lifecycle differ. |
| R-IPC-3 | The handshake must include protocol version, helper version, helper kind, session token or equivalent freshness guard, and advertised capabilities. | Reuse/extend `helper_ipc.py` where possible. |
| R-IPC-4 | Invalid token/version/helper kind/event type must fail closed. | No permissive fallback parsing. |
| R-IPC-5 | Reconnect behavior after overlay client restart, EDMC restart, GNOME Shell restart, and helper extension reload must be explicit. | Required for real-world support. |
| R-IPC-6 | IPC payloads must stay narrow: no arbitrary command execution or broad shell-control surface. | Security and supportability requirement. |
| R-IPC-7 | The chosen transport's runtime prerequisites must be detected and reported as helper requirements. | Session DBus implies a user bus and DBus-capable GNOME/GJS environment; Unix sockets imply a writable `$XDG_RUNTIME_DIR` and socket lifecycle support. |

### Target Window Contract Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-TW-1 | The helper must define how it identifies Elite Dangerous under Wine/Proton. | Candidate inputs: title, app/window class, PID tree, command line, process metadata, or a weighted combination. |
| R-TW-2 | Target-window updates must include a stable target token, title/app metadata when available, geometry, monitor/output identity, visibility/focus/fullscreen state, and timestamp/sequence number. | Keep metadata minimal but sufficient for support. |
| R-TW-3 | The coordinate space of helper geometry must be defined explicitly. | For example: GNOME Shell logical coordinates, physical pixels, per-output logical coordinates, or another named space. |
| R-TW-4 | The overlay client must define the conversion from helper coordinate space into Qt overlay geometry. | Fractional scaling and mixed-DPI behavior must not be heuristic-only. |
| R-TW-5 | The helper must report target not found, target ambiguous, and target stale separately. | Avoid attaching to the wrong window silently. |
| R-TW-6 | Target reacquire behavior must be deterministic when Elite exits, relaunches, changes display mode, or changes title. | Needed for game/session transitions. |
| R-TW-7 | Process metadata matching must avoid broad substring searches. | Issue #82 showed `pgrep -f` can match unrelated browser/file/terminal command lines. If process metadata is used, anchor it to window-provided PID/app metadata and exact known executable/app identifiers. |

### Overlay Behavior Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-OV-1 | With the helper active, the overlay must stay aligned to the Elite Dangerous window in GNOME Wayland for the supported play modes: windowed and borderless fullscreen. | Exclusive fullscreen is not a supported play mode for this overlay. |
| R-OV-2 | The overlay must maintain current payload rendering behavior, profile/group behavior, controller placement behavior, and existing legacy overlay compatibility. | Helper work should change platform attachment, not payload semantics. |
| R-OV-3 | Click-through/focus behavior must remain predictable while the overlay is attached. | Any GNOME-specific limitation must be surfaced as degraded/unsupported, not hidden. |
| R-OV-4 | Mixed-monitor, negative-origin, fractional-scaling, and monitor-DPI cases must have recorded validation or explicit deferral. | Inherits strict `fix219` tracking-display-matrix requirement. |
| R-OV-5 | Existing Windows, native X11, KWin, wlroots/Hyprland, and explicit `xwayland_compat` behavior must not regress. | GNOME helper work must stay isolated behind backend/helper seams. |
| R-OV-6 | Normal overlay mode must not show window manager chrome, title bars, task-switcher app framing, or other standalone-app presentation. | If GNOME Wayland can only show a decorated standalone window, the result is degraded/experimental, not true overlay. |
| R-OV-7 | "Run as standalone" must be an explicit opt-in setting, not an implicit side effect of GNOME Wayland fallback or helper activation. | Standalone mode may remain useful for development/diagnostics, but it must be surfaced and gated separately from true-overlay support. |
| R-OV-8 | Exclusive fullscreen must be documented as unsupported for GNOME Wayland overlay use. | Users who want the overlay must run Elite Dangerous in windowed or borderless fullscreen mode. Do not spend helper design or validation scope on exclusive fullscreen. |
| R-OV-9 | The overlay must remain stacked above the game while click-through sends input to the game. | Clicking through must not demote the overlay behind the game in windowed or borderless fullscreen mode. |

### Visibility Terminology Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-VN-1 | Rename `force_render` to `keep_overlay_visible` before helper implementation depends on it. | IQ3 decision: this happens immediately after status truthfulness, before helper behavior depends on visibility terminology. |
| R-VN-2 | The rename must preserve behavior: the setting keeps the overlay visible when Elite Dangerous is not foreground; it does not force payload rendering. | This distinction matters for GNOME helper validation and support triage. |
| R-VN-3 | The migration must be backward compatible with existing EDMC config keys, `overlay_settings.json`, controller CLI payloads, and tests. | Existing installs may still store or send `force_render`; accept legacy input during a migration window. |
| R-VN-4 | Controller runtime override terminology must be renamed consistently away from "force render." | It is a temporary visibility override while the controller is active, not a renderer override. |
| R-VN-5 | User-facing docs, logs, preferences labels, and troubleshooting guidance must distinguish payload rendering, overlay visibility, and compositor presentation/focus behavior. | Prevent future data-gathering mistakes like treating `force_render` as a render-path diagnostic. |

### Overlay Attachment Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-OA-1 | The plan must define what "attach" means for GNOME Wayland. | Candidate models: PyQt overlay follows helper geometry, Shell extension manages Shell actor/presentation, or a staged hybrid. |
| R-OA-2 | The first implementation must preserve the existing PyQt renderer unless helper presentation/attachment validation proves that Shell-owned rendering is required. | Avoid rewriting rendering before target discovery and Shell-mediated presentation are proven. |
| R-OA-3 | Behavior must be defined for minimized target, hidden target, target on another workspace, focus loss, monitor move, game exit, and resolution/display-mode changes. | Each state should either attach, hide, degrade, or unsupported with reason. |
| R-OA-4 | Overlay attachment must handle helper stale/disconnected state by degrading visibly and avoiding stale geometry drift. | Do not keep blindly following old coordinates forever. |
| R-OA-5 | The helper-backed path must keep existing manual backend override escape hatches available. | Users/support must still be able to force `xwayland_compat`. |

### Security And Privacy Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-SP-1 | The helper must not expose arbitrary command execution or broad GNOME Shell control commands. | Helper is a telemetry/control bridge for overlay attachment only. |
| R-SP-2 | The helper should emit only the window geometry/state needed for overlay attachment and support diagnostics. | Avoid unnecessary process/window metadata in logs and IPC. |
| R-SP-3 | User-facing install/enable copy must explain what the extension observes and why. | Required for informed consent. |
| R-SP-4 | Logs must redact or avoid sensitive command-line/process metadata unless explicitly needed for debug mode. | Keep support logs safe by default. |
| R-SP-5 | Helper IPC must stay local to the user session. | No network listener or cross-user channel. |

### Validation Matrix Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-VM-1 | First support claim must name the GNOME Shell version range validated. | Q9 target floor is GNOME Shell 46; support target is GNOME Shell 46 and newer, with exact validated versions recorded in release evidence. |
| R-VM-2 | Minimum first-party validation should include at least one Ubuntu GNOME Wayland or Fedora GNOME Wayland run. | Exact first distro target remains open until Q9 is fully resolved. |
| R-VM-3 | Validation must include install/enable, active helper detection, target attach/follow, restart/reconnect, and disable/uninstall recovery. | This is broader than just "extension enabled". |
| R-VM-4 | At least one fractional-scaling or multi-monitor scenario must be validated before claiming full true-overlay behavior, or explicitly deferred with a reduced claim. | Aligns with `fix219` true-overlay checklist. |
| R-VM-5 | Flatpak EDMC on GNOME Wayland must be validated or explicitly deferred. | Host extension plus sandboxed EDMC is a likely support path. |
| R-VM-6 | Every non-`true_overlay` result must record the exact weakened guarantee and reason. | Same classification discipline as `fix219`. |

### Documentation And Support Requirements

| ID | Requirement | Notes |
| --- | --- | --- |
| R-DO-1 | Installation docs must distinguish approval, installed, enabled, and active helper states. | This prevents the current "approval means installed" confusion. |
| R-DO-2 | Troubleshooting docs must include commands/log lines for checking helper state. | Include `gnome-extensions`, extension directory, and overlay backend status examples. |
| R-DO-3 | Release notes must avoid claiming GNOME Wayland true-overlay support until helper validation is recorded. | If helper is partial, call it degraded/experimental. |
| R-DO-4 | User documentation must list helper prerequisites for the selected transport and explain how to verify them. | These are user-facing requirements, not hidden developer assumptions. |

## Test Type Selection (Required Before Refactoring)
- Use **unit tests** for selector classification, status formatting, helper package metadata parsing, helper IPC validation, and helper-message normalization.
- Use **harness tests** when changes touch `load.py`, preferences status polling, plugin/client status transport, installer-triggered runtime state, or EDMC lifecycle behavior.
- Use **shell/script tests** for Linux installer extension packaging/install/approval behavior.
- Use **manual real-environment validation** for GNOME Shell extension attach/follow/click-through behavior because GNOME Shell/Mutter behavior cannot be fully proven in headless unit tests.
- For mixed changes, require unit tests for pure logic and harness/manual validation for runtime wiring and real compositor behavior.

## Testing Strategy Matrix (Required)

| Refactor Slice | Existing Behavior/Invariants To Preserve | Test Type (Unit/Harness/Manual) | Why This Level | Test File(s) | Command |
| --- | --- | --- | --- | --- | --- |
| GNOME helper-missing classification | Missing GNOME helper remains visible; mode no longer says true overlay | Unit + Harness | Selector/status is pure, preferences consumes status via runtime paths | `overlay_client/tests/test_backend_selector.py`, `overlay_client/tests/test_backend_status.py`, `tests/test_harness_backend_status_roundtrip.py`, `tests/test_preferences_panel_controller_tab.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py tests/test_harness_backend_status_roundtrip.py tests/test_preferences_panel_controller_tab.py -q` |
| Helper package and manifest | No silent install; extension metadata is valid and versioned | Unit + shell/script | Packaging and installer behavior are deterministic but shell-specific | `tests/test_install_linux.py`, new extension manifest tests | `source .venv/bin/activate && python -m pytest tests/test_install_linux.py -q` |
| Helper IPC boundary | Local-only, versioned, fail-closed validation remains intact | Unit | Pure helper-boundary validation should stay headless | `overlay_client/tests/test_helper_ipc_boundary.py`, new GNOME helper IPC tests | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py -q` |
| Helper discovery and runtime state | Client status distinguishes missing/disabled/incompatible/active helper states | Mixed | Discovery can be unit-tested with fake probes; plugin/preferences status needs harness coverage | `overlay_client/tests/test_platform_probe.py`, `overlay_client/tests/test_backend_status.py`, `tests/test_harness_backend_status_roundtrip.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_platform_probe.py overlay_client/tests/test_backend_status.py tests/test_harness_backend_status_roundtrip.py -q` |
| Target-window attach/follow contract | Existing payload rendering unchanged while target geometry source changes on GNOME Wayland | Unit + Manual | Fake helper messages can prove client behavior; real GNOME validates compositor behavior | new `overlay_client/tests/test_gnome_helper_tracking.py`, manual GNOME Wayland matrix | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_tracking.py -q` |
| Visibility terminology rename | Behavior unchanged while `force_render` is renamed to visibility terminology with legacy compatibility | Unit + Harness | Config, controller CLI, preferences, and client visibility behavior cross process boundaries | `overlay_client/tests/test_window_controller.py`, `overlay_client/tests/test_client_config.py`, `overlay_controller/tests/test_plugin_bridge.py`, `tests/test_overlay_config_payload.py`, `tests/test_preferences_persistence.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_window_controller.py overlay_client/tests/test_client_config.py overlay_controller/tests/test_plugin_bridge.py tests/test_overlay_config_payload.py tests/test_preferences_persistence.py -q` |
| Installer and post-install enable flow | Helper can be installed during plugin install and after DE/session switch | Shell/script + Harness | Installer paths are shell-owned; runtime remediation appears in prefs/status | `tests/test_install_linux.py`, `tests/test_preferences_panel_controller_tab.py` | `source .venv/bin/activate && python -m pytest tests/test_install_linux.py tests/test_preferences_panel_controller_tab.py -q` |
| Cross-platform regression | Non-GNOME backends keep current status/override/fallback behavior | Unit + Harness | Selector/status and runtime wiring are shared surfaces | existing backend selector/status/consumer/harness tests | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_consumers.py tests/test_harness_backend_selection_wiring.py -q` |

## Test Acceptance Gates (Required)
- [ ] Unit tests added/updated for extracted pure logic.
- [ ] Harness tests added/updated for lifecycle/wiring surfaces.
- [ ] Installer/script tests added/updated for helper install/approval paths.
- [ ] Manual GNOME Wayland validation evidence recorded before any `true_overlay` claim.
- [ ] Commands executed and outcomes recorded.
- [ ] Skips/failures documented with reason and follow-up action.

## Scope
- In scope:
- Correct GNOME Wayland helper-missing classification and UI/status wording.
- Define and implement a GNOME Shell extension helper package.
- Define helper install, enable, reinstall, update, and removal paths.
- Add a post-install/remediation path when the user switches from X11 to GNOME Wayland after initial plugin installation.
- Rename misleading `force_render` terminology to a visibility-focused setting/override name with backward-compatible migration.
- Separate normal overlay presentation from any standalone-app mode, with standalone behavior gated by an explicit user/developer setting.
- Connect the helper to the existing backend/helper IPC model.
- Use helper data to attach/follow the Elite Dangerous window on GNOME Wayland.
- Validate GNOME Wayland true-overlay requirements in real environments before claiming support.
- Out of scope:
- Reopening the completed `fix219` backend architecture cleanup.
- Replacing the Tk Overlay Controller.
- Building KWin/wlroots/Hyprland helpers in this plan.
- Redesigning payload rendering, plugin groups, profiles, or legacy overlay payload semantics.
- Silently installing/enabling GNOME Shell extensions without user approval.
- Claiming Linux standalone/VR support as part of this GNOME helper plan.
- Supporting Elite Dangerous exclusive fullscreen mode. Overlay use requires windowed or borderless fullscreen mode.

## Current Touch Points
- Code:
- `overlay_client/backend/selector.py` (GNOME helper-missing classification and fallback semantics)
- `overlay_client/backend/status.py` (status summary/warning wording and helper-state reporting)
- `overlay_client/backend/contracts.py` (helper/backend contract extensions if needed)
- `overlay_client/backend/helper_ipc.py` (helper message validation and boundary shape)
- `overlay_client/backend/bundles/gnome_shell_wayland.py` (GNOME bundle helper ownership)
- `overlay_client/backend/bundles/_linux_window_integration.py` (current GNOME Wayland presentation/click-through fallback behavior)
- `overlay_client/backend/bundles/_linux_trackers.py` (current fallback tracker behavior; should not own GNOME helper tracking once implemented)
- `overlay_client/platform_context.py` and `overlay_client/control_surface.py` (client runtime status/probe ingestion and visibility-setting naming)
- `overlay_client/setup_surface.py`, `overlay_client/window_controller.py`, and `overlay_client/window_tracking.py` (runtime tracker creation, attachment, and visibility decisions)
- `overlay_client/client_config.py` and `overlay_client/developer_helpers.py` (settings/config payload compatibility for renamed visibility setting and explicit standalone-mode gating)
- `overlay_plugin/preferences.py` (helper status, install/remediation UI, backend warning text, and visibility-setting label/key migration)
- `overlay_plugin/overlay_config_payload.py`, `load.py`, and `overlay_controller/services/plugin_bridge.py` (plugin/controller visibility override protocol and legacy `force_render` compatibility)
- `scripts/install_linux.sh` and `scripts/install_matrix.json` (installer-time helper guidance/install/approval)
- New extension package path, proposed: `gnome_shell_extension/` or `helpers/gnome_shell_extension/`
- Tests:
- `overlay_client/tests/test_backend_selector.py`
- `overlay_client/tests/test_backend_status.py`
- `overlay_client/tests/test_helper_ipc_boundary.py`
- `overlay_client/tests/test_platform_probe.py`
- `overlay_client/tests/test_window_tracking_bundle_routing.py`
- `tests/test_harness_backend_status_roundtrip.py`
- `tests/test_preferences_panel_controller_tab.py`
- `tests/test_install_linux.py`
- New helper-specific tests for extension manifest/package and fake helper tracking messages
- Docs/notes:
- `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md`
- `docs/refactoring/fix219_cross_platform_overlay_architecture_research.md`
- `docs/wiki/Installation.md`
- `docs/wiki/Installation-FAQs.md`
- `docs/wiki/Troubleshooting.md`
- `RELEASE_NOTES.md`

## Question Priority And Resolution Log

Tackle these one at a time, in priority order. Do not implement code for a lower-priority question when a higher-priority answer still changes the required architecture.

| Priority | Question | Status | Current Answer / Decision Candidate | Why This Comes Here |
| --- | --- | --- | --- | --- |
| Q1 | What is the helper's actual role: geometry-only target discovery, Shell-owned presentation/input, or staged hybrid? | Completed | Geometry-only is ruled out. The GNOME helper must be a Shell-side presentation/attachment helper that owns or mediates focus/visibility state, placement, stacking, and chrome/titlebar-free presentation for windowed and borderless fullscreen modes. The first prototype should still try to keep PyQt as the renderer, but must prove Shell-mediated presentation before claiming true-overlay support. | This determines the extension API, IPC shape, install claims, and validation bar. |
| Q2 | What transport should the extension use: session DBus, Unix socket under `$XDG_RUNTIME_DIR`, or staged fallback? | Completed | Use session DBus as the primary helper transport. Keep Unix socket under `$XDG_RUNTIME_DIR` as an unimplemented fallback only if DBus later fails during prototype lifecycle/security review. | Transport determines helper lifecycle, security model, reconnect behavior, and implementation complexity. |
| Q3 | Which process owns the listener/service and connection lifecycle? | Completed | The GNOME Shell extension owns the session-DBus service name and exported helper object lifecycle. The overlay client connects as a validating consumer/controller, registers one active runtime session, subscribes to typed signals, sends narrow requests, and degrades when the service is absent or stale. | Depends on transport and GNOME Shell extension lifecycle. |
| Q4 | How do we identify the Elite Dangerous target window under Wine/Proton? | Completed | Require the Shell-visible title match for the actual game client (`Elite - Dangerous`, observed as `Elite - Dangerous (CLIENT)`) and use launcher-specific app/class metadata, normal toplevel type, visible/non-minimized workspace state, nonzero geometry, monitor, and helper target token as supporting fields. Steam app class `steam_app_359320` is common for Steam installs but must not be required globally because Elite can be launched through other launchers such as Epic. Treat PID/process ancestry as advisory only. | Attachment correctness depends on target identity before geometry can be trusted. |
| Q5 | What coordinate-space contract does helper geometry use, and how does the client convert it to Qt geometry? | Completed | Helper geometry uses GNOME Shell global logical coordinates and must report `frameRect`, `bufferRect`, monitor/output identity, visibility/workspace state, and an explicit `contentRect`/decoration-inset contract for game viewport alignment. Use `contentRect` for overlay content alignment; use Shell coordinates as authoritative for Shell-mediated presentation. Qt geometry is secondary and must not be treated as proof of visible placement on GNOME Wayland. | Mixed DPI/fractional scaling correctness depends on this. |
| Q6 | How do install, enable, update, disable, and uninstall work? | Completed | Default to user-local install under `~/.local/share/gnome-shell/extensions/edmc-modern-overlay-helper@edmcmodernoverlay.github.io/`. Release artifact is source-directory-only at `helpers/gnome_shell_extension/`; install copies that directory directly. Updates disable, clean-replace from packaged source, enable, require logout/login, then verify active/version/protocol. No backup is kept. Remediation state model uses platform-neutral `not_required` for sessions where this helper does not apply. | Needed before shipping helper artifacts or remediation UI. |
| Q7 | How do users remediate after switching from X11 to GNOME Wayland post-install? | Completed | The installer is the helper-install path: when run under GNOME Wayland, it detects GNOME Wayland and installs/enables the helper with user approval using the Q6 flow. If the user originally installed under X11 and later switches to GNOME Wayland, settings/status warns that the required helper is unavailable and tells the user to rerun the installer while logged into GNOME Wayland, then log out/in and verify helper health. | This is a deliberate scope tradeoff: installer-driven remediation is accepted even though richer in-app remediation may come later. |
| Q8 | What helper states must preferences/logs/debug diagnostics show? | Completed | Helper/backend state must be rendered from one authoritative status object across preferences/settings, user-facing backend status, overlay client logs, EDMC/plugin status bridge logs, `utils/collect_overlay_debug_*` scripts, and the live "Show debug overlay metrics" overlay. Use stable helper field names and compact preferences/debug-overlay text. Collect overlay-client status when available plus direct Linux host facts. | Required to avoid confusing approval/install/active states. |
| Q9 | What GNOME Shell versions and distros are supported first? | Completed | Target GNOME Shell 46 and newer. First validation target is Ubuntu GNOME Wayland, starting with GNOME Shell 46. `metadata.json` should list explicit shell versions `46`, `47`, `48`, `49`, and `50`, with newer entries added after porting-guide review and smoke validation. Release wording must distinguish the 46+ target from exact validated environments. | Sets `metadata.json`, validation matrix, and release claims. |
| Q10 | What is the first release validation matrix? | Completed | Minimum first release gate covers Ubuntu GNOME Wayland/GNOME Shell 46, install lifecycle, backend/status truthfulness, windowed and borderless overlay behavior, failure/recovery states, and privacy/security checks. Any failed/deferred item blocks a GNOME Wayland `true_overlay` claim unless release wording explicitly downgrades it. | Depends on version/distro support and the helper's role. |
| Q11 | What exact security/privacy copy and log-redaction rules are required? | Completed | Helper privacy copy must explain that the local GNOME Shell extension observes limited window metadata for overlay attachment only. It must not capture screen contents, keyboard/mouse input, game data, or network traffic. Logs/diagnostics avoid process command lines, screenshots, environment variables, and broad Shell/process dumps by default. | Important, but depends on final metadata emitted by the helper. |

### Closed Question: Q1 Helper Role

#### Decision
Geometry-only target discovery is not enough for GNOME Wayland true-overlay support.

The GNOME Shell helper must own or mediate:
- target focus/visibility state
- overlay placement
- overlay stacking above the game after click-through/focus changes
- chrome/titlebar-free presentation
- supported mode behavior for windowed and borderless fullscreen

The first helper prototype should still try to keep the existing PyQt renderer and payload pipeline. Rendering should move into the extension only if Shell-mediated placement/presentation cannot host or control the PyQt overlay surface well enough to satisfy the overlay requirements.

#### Problem
GNOME Wayland blocks the normal external-client assumptions used by the current PyQt overlay path. The helper could solve different layers of the problem:
- target discovery and geometry only
- presentation/stacking/input policy inside GNOME Shell
- both, through a staged hybrid

#### Final Direction
Use a staged Shell-mediated attachment model:
- Phase 2/early Phase 4: the GNOME Shell extension owns helper health, version/capability reporting, explicit unavailable/degraded reasons, and the transport boundary.
- The helper must provide authoritative target state and participate in overlay presentation/attachment, not just report target geometry.
- The PyQt overlay remains the renderer for the first prototype and continues to own payload rendering, grouping, profiles, controller placement, and legacy payload compatibility.
- If validation proves that a PyQt surface cannot be reliably placed, stacked, or presented without chrome by Shell-side mediation, add a later stage to move the specific failing presentation/render-hosting responsibility into the extension.

#### Rationale
- The evidence rules out a geometry-only helper, but it does not yet prove that payload rendering must move out of PyQt.
- Keeping the PyQt renderer for the first prototype preserves existing payload semantics and reduces regression risk across non-GNOME backends.
- Shell-mediated presentation is the narrowest next step that directly targets the observed failures: focus/visibility loops, ignored/stale placement, titlebar/chrome, and stacking after click-through.
- Moving rendering or visual hosting into the extension remains an explicit escalation only if Shell mediation cannot make the PyQt surface satisfy the true-overlay requirements.

#### Evidence Collected
- Environment observed on 2026-05-09: GNOME Shell 46.0, `XDG_SESSION_TYPE=wayland`, `XDG_CURRENT_DESKTOP=ubuntu:GNOME`, `DESKTOP_SESSION=ubuntu-wayland`.
- Helper state observed in logs: `gnome_shell_extension:required:inactive:unapproved:none`; no installed/active helper was found.
- Backend status observed in logs: `family=native_wayland instance=gnome_shell_wayland classification=true_overlay fallback_from=compositor_helper/gnome_shell_wayland fallback_reason=missing_helper`. This confirms the current status inconsistency that Phase 1 must fix.
- Payload rendering itself works in the current PyQt client path: BGS-Tally payloads rendered and continued receiving deduped payload updates during testing.
- When the mock Elite window was found, the overlay resized/attached to the mock target geometry (`1280x960`) and then repeatedly toggled visibility. The client log showed a loop of `Overlay visibility set to visible` followed about 0.5 seconds later by `Overlay visibility set to hidden`.
- The current tracking timer interval is 500 ms, matching the visible/hidden cadence. The current visibility decision is `force_render or (state.is_visible and state.is_foreground)`, so losing foreground after showing/raising the overlay is a plausible cause of the flashing loop.
- When the user enabled the preference labeled "Keep overlay visible when Elite Dangerous is not the foreground window", the overlay stopped flashing. This strongly suggests the loop is caused by foreground/visibility state changes after the overlay is shown, not by payload rendering failure.
- With the keep-visible preference enabled, clicks pass through the overlay to the mock target, but the overlay does not stay attached when the mock target window is moved. This indicates the current PyQt/input path can preserve click-through in this scenario, while target geometry updates remain unreliable on GNOME Wayland without a helper.
- Follow logging during actual game target movement showed the tracker reporting changing target positions, the client calculating matching overlay geometry, `setGeometry` being applied, and Qt `moveEvent` reporting the same position. The user observed that the overlay does not merely lag during movement; it never catches up after the target stops, and the visible overlay position never changes when the actual game window is moved. This points to compositor-visible placement divergence rather than simple polling cadence or a mock-window artifact.
- A second actual-game movement log at 2026-05-09 14:22 UTC confirmed the same pattern across multiple target positions, including `(164,282)`, `(301,345)`, `(335,261)`, `(217,191)`, and `(303,253)`: tracker geometry, calculated overlay geometry, `setGeometry`, and Qt `moveEvent` all matched. This strengthens the conclusion that the client believes the overlay moved even though the visible overlay does not.
- The user could not click-drag the overlay window, which is expected while click-through is active, but could move the visible overlay with desktop keyboard window-move commands. Those keyboard moves produced no overlay client log messages and no `wmctrl` geometry changes. This shows the compositor-visible overlay position can change independently of both Qt-reported geometry and X11 tooling, which is direct evidence that GNOME Wayland placement cannot be validated or controlled from the current client path alone.
- When the actual game was moved to the middle of the screen in windowed mode and EDMC was restarted, the overlay started in the upper-left corner of the screen instead of over the game window. This rules out a dynamic-reposition-only failure: initial client-side placement is also not reliable on GNOME Wayland.
- In borderless fullscreen with "Keep overlay visible when Elite Dangerous is not the foreground window" enabled, the overlay appeared correctly positioned, but it showed a title bar and behaved like a standalone application. Correct placement in this mode is useful evidence, but titlebar/standalone presentation violates the true-overlay requirements and must be treated separately from successful attachment.
- A standalone/titlebar source check showed `force_render=true`, `standalone_mode=false`, and `manual_backend_override=""`. Logs also showed `Applying drag state: drag_enabled=False transparent=True move_mode=False window=False flags=none`. This means the borderless-fullscreen titlebar/standalone presentation is not caused by the explicit standalone setting or manual backend override; it is a GNOME Wayland presentation/windowing behavior that the helper plan must address.
- In borderless fullscreen with "Keep overlay visible when Elite Dangerous is not the foreground window" disabled, the overlay flashes. The log shows repeated `Overlay visibility set to visible` / `hidden` transitions at about 0.5 second cadence with full-screen geometry (`3440x1440`, scale `2.69`). This means borderless fullscreen still suffers from the foreground/visibility loop; the previous correct-looking placement was only stable because the keep-visible setting masked that loop.
- After restarting EDMC with the game in borderless fullscreen, the overlay placed correctly except for the title bar: the visible overlay was shifted downward by the title bar height. This confirms borderless startup attachment can be correct, but window chrome makes the final presentation fail true-overlay alignment.
- In windowed mode, resizing the game window caused the overlay to resize without restarting EDMC. This separates size tracking from position tracking: dynamic size updates can be visible, while dynamic position updates still fail.
- In both windowed and borderless modes, clicking through the overlay to the game sends input through but moves the overlay behind the game. This confirms click-through alone is insufficient; true-overlay behavior also requires Shell-level stacking/presentation that keeps the overlay above the target after focus changes.
- In exclusive fullscreen, the overlay did not show, and alt-tabbing to the overlay minimized the game. This is acceptable because exclusive fullscreen is explicitly out of scope: users must use windowed or borderless fullscreen mode when they want overlay support.
- `force_render` is a misleading internal name. In current behavior and user-facing UI it means "Keep overlay visible when Elite Dangerous is not the foreground window", not "force payload rendering". It also triggers Linux/Wayland interaction side effects such as clearing transient parent state and reapplying click-through, so it is not a clean rendering-only diagnostic toggle.
- Evidence supports keeping payload rendering in PyQt for the first helper prototype, but Shell-mediated attachment/presentation is required. The helper must provide authoritative focus/visibility state and participate in placement, stacking, and chrome-free presentation; rendering or visual hosting should move into the extension only if that prototype cannot satisfy the requirements.

#### Prototype Evidence Needed After Q1
- Prove whether Shell-side mediation can keep the PyQt-rendered surface correctly placed, stacked, chrome-free, and visible without the keep-visible workaround.
- If PyQt still fails, record the exact failed requirement: stacking, click-through, focus, chrome/titlebar suppression, coordinate conversion, target tracking, or render hosting.
- Do not continue testing or designing for exclusive fullscreen. The validation matrix should include only windowed and borderless fullscreen play modes for GNOME Wayland overlay support.

### Closed Question: Q2 Helper Transport

#### Decision
Use **session DBus** as the primary IPC transport between the GNOME Shell extension and the overlay client.

Unix sockets under `$XDG_RUNTIME_DIR` remain a reserved fallback, but Q2 does not require a Unix-socket prototype now. The fallback should only be revisited if DBus fails during helper lifecycle, reconnect, or security review.

#### Problem
The GNOME Shell extension and overlay client need a local, versioned, fail-closed communication boundary. Existing `overlay_client/backend/helper_ipc.py` already models both `session_dbus` and `unix_socket`, but Q2 must choose which transport to prototype first.

#### Constraints From Q1
- The helper must support more than telemetry: focus/visibility, placement, stacking, and presentation state will need timely events.
- Runtime communication should be direct between helper and overlay client; `load.py` remains the EDMC control plane, not the helper transport hub.
- The transport must survive normal EDMC/client restarts and fail visibly when the Shell extension is disabled/reloaded.
- The transport must remain local-only, narrow, versioned, and session-scoped.
- Any host tools or session services required by the chosen transport are user-facing prerequisites and must appear in installer, preferences, diagnostics, and troubleshooting docs.

#### Decision Rationale
Session DBus passed both the standalone GJS smoke test and the GNOME Shell extension-context smoke test. It is also a normal GNOME/GJS integration surface, avoids managing socket files from inside GNOME Shell, and gives us service names/object paths/interfaces that map cleanly onto the existing `HelperEndpointConfig`.

Unix socket remains viable if DBus ownership, signal delivery, or extension lifecycle behavior becomes too awkward, but it should not be chosen only because Python-side code is easy. No Unix-socket test is required before moving to Q3.

#### Q2 Tests To Run

| Test | Goal | Command / Action | Pass Signal | Failure Signal |
| --- | --- | --- | --- | --- |
| T-Q2-1 Session bus/tooling probe | Confirm the session has usable DBus tools and GJS. | `command -v gjs gdbus busctl dbus-monitor` and `gjs --version` | Tools are present enough to build/probe DBus from GJS and Python. | Missing `gjs` or DBus tools means installation/docs must account for prerequisites. |
| T-Q2-2 GNOME Shell DBus visibility | Confirm this session exposes GNOME Shell on the user bus. | `busctl --user --no-pager list | grep -E "org.gnome.Shell|org.freedesktop.DBus"` | Shell/session bus names are visible. | No Shell/session bus visibility means DBus may be harder to use for runtime diagnostics. |
| T-Q2-3 GJS DBus owner smoke test | Prove a GJS process can own a session bus name and exchange a minimal message with a client. | Temporary script under `/tmp`, not repo code. | GJS can own a name, expose a method or signal, and Python/`gdbus` can call/read it. | DBus API friction or failure pushes Unix socket higher. |
| T-Q2-4 Extension-context DBus smoke test | Prove the same DBus pattern works from a minimal GNOME Shell extension, not just standalone `gjs`. | Prototype extension only after T-Q2-3 passes. | Extension can publish hello/heartbeat state and client can observe it. | Standalone GJS success but extension failure means transport decision stays open. |
| T-Q2-5 Unix socket fallback smoke test | Prove GJS can create/connect a Unix socket under `$XDG_RUNTIME_DIR` if DBus is rejected. | Temporary script under `/tmp` or prototype extension. | Socket path is session-local, cleaned up, and Python can exchange framed JSON. | Lifecycle/cleanup or GJS socket friction makes DBus preferable. |

#### Q2 Follow-Up For Q3
- Decide whether the Shell extension or overlay client owns the DBus service name and exported object lifecycle.
- Record exact service name pattern, object path/interface names, event shape, heartbeat expectations, and reconnect behavior to prototype.
- Record which prerequisite checks are mandatory for users and which are developer-only diagnostics.

#### Evidence Collected
- T-Q2-1 passed on 2026-05-09: `gjs`, `gdbus`, `busctl`, and `dbus-monitor` are present; `gjs --version` reports `gjs 1.80.2`; `XDG_RUNTIME_DIR=/run/user/1000`; `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus`.
- T-Q2-2 passed on 2026-05-09: `busctl --user --no-pager list` shows `org.freedesktop.DBus`, `org.gnome.Shell`, `org.gnome.Shell.Introspect`, `org.gnome.Shell.Extensions`, and related GNOME Shell services on the user bus.
- T-Q2-3 passed on 2026-05-09: a standalone `/tmp` GJS process owned `org.edmc.ModernOverlay.Test`, exported `/org/edmc/ModernOverlay/Test`, returned `('pong:hello',)` from `Ping("hello")`, and emitted repeated `Heartbeat ('alive',)` signals observed by `gdbus monitor`.
- T-Q2-4 initial setup evidence on 2026-05-09: after manually creating `~/.local/share/gnome-shell/extensions/edmc-modern-overlay-dbus-smoke@local.test`, `gnome-extensions info` reported "doesn't exist" and `gnome-extensions enable` reported "does not exist". This indicates the current GNOME Wayland session did not discover the manually copied extension immediately, so the test requires logout/login or a different supported install/rescan path before extension-context DBus can be evaluated.
- T-Q2-4 enablement evidence after logout/login on 2026-05-09: GNOME Shell discovered the extension and reported `State: INITIALIZED`, but `Enabled: No`; repeated `gnome-extensions enable edmc-modern-overlay-dbus-smoke@local.test` calls did not make it appear in `gnome-extensions list --enabled`. Diagnostics showed `org.gnome.shell disable-user-extensions=true`, while `enabled-extensions` already contained the smoke-test UUID. This explains the blocker: user extensions are globally disabled, so helper remediation must detect and report this state separately from per-extension enablement.
- T-Q2-4 passed on 2026-05-09 after setting `org.gnome.shell disable-user-extensions=false`: `gnome-extensions info` reported `Enabled: Yes` and `State: ACTIVE`; the extension-context DBus service returned `('extension-pong:hello',)` from `Ping("hello")`. This proves a GNOME Shell extension can publish and answer a session-DBus helper endpoint in this environment.

### Closed Question: Q3 Listener And Lifecycle Ownership

#### Decision
The GNOME Shell extension owns the session-DBus service name and exported helper object lifecycle.

The overlay client connects as a validating consumer/controller. It registers one active runtime session, subscribes to typed helper signals, sends narrow requests, and degrades when the service is absent, stale, disabled, incompatible, or globally blocked.

#### Ownership Model
- Extension owns the DBus service name.
- Extension owns the exported object path and interface lifecycle.
- Extension publishes helper hello/status/heartbeat while active.
- Extension can remain active when no overlay client is running; expensive target tracking may stay idle until a client registers.
- Overlay client owns connection attempts, reconnect backoff, protocol validation, session-token validation, stale-helper timeout, and backend classification.
- `load.py` remains the EDMC control plane for launch/config/diagnostics and does not proxy runtime helper traffic.

#### Client Registration Rules
- Support one active registered overlay client per user session.
- The overlay client generates a fresh session token per runtime start and sends it during `RegisterClient`.
- The extension echoes the active session token in helper events/signals that are intended for the registered client.
- If a new valid client registers, the extension replaces the prior active client session; stale tokens are ignored by the client and should be considered disconnected by the extension.

#### Lifecycle Rules
- If EDMC or the overlay client restarts, the extension keeps running; the new client registers with a new token.
- If the extension reloads or GNOME Shell restarts, the DBus name disappears/reappears; the client marks helper state stale/unreachable, reconnects, and re-registers.
- If user extensions are globally disabled, the helper service is absent even if the extension is installed and listed in `enabled-extensions`; diagnostics must report this distinct state.
- If the helper version, protocol version, helper kind, or session token does not match, communication fails closed.

#### Method And Signal Shape Constraints
- Do not expose arbitrary command execution or broad Shell-control methods.
- Methods should stay narrow: register/unregister client, get status/capabilities, and any explicitly needed presentation request.
- Signals should be typed and allowlisted: heartbeat/status, target state, presentation state, degraded/unavailable reason, and later narrowly scoped events.
- All future methods/signals must preserve the local-only, versioned, fail-closed boundary chosen in Q2.

### Closed Question: Q4 Target Window Identity

#### Decision
The GNOME helper identifies the Elite Dangerous game window using a weighted target identity contract:

Mandatory first-release discriminator:
- Shell-visible normalized title must match the actual game client title pattern, observed as `Elite - Dangerous (CLIENT)`.

Supporting fields:
- launcher-specific `wmClass` / `wmClassInstance` / app name match known Elite launcher metadata when available. For Steam installs this was observed as `steam_app_359320`, but this is not mandatory because Epic and other launcher paths may expose different identifiers.
- window type is normal/toplevel (`Meta.WindowType.NORMAL`, observed as `0`).
- frame/buffer geometry is nonzero.
- window is showing on the current workspace or in another explicitly supported target state.
- window is not minimized.
- monitor and frame/buffer rects are included in the target state.
- helper emits a stable target token for the selected `Meta.Window`; observed temporary `appId` values such as `window:21` are not treated as durable across restarts.

Advisory fields:
- PID/process metadata may be reported for diagnostics, but it is not mandatory for first-release matching and must not use broad substring searches.

Rejected states:
- launcher-only state is not a valid target; in the observed Steam install the launcher shares `steam_app_359320` but has title `elite launcher`.
- ambiguous multiple client matches must report `target_ambiguous`.
- mock/test windows require an explicit development/test flag.

#### Problem
The helper must identify the actual Elite Dangerous game window under Wine/Proton without attaching to the wrong window, stale window, launcher, EDMC, controller, or a mock/test window unless a development test explicitly asks for a mock target.

The current client trackers use a title-based baseline:
- default title hint: `elite - dangerous`
- shared matcher: `matches_window_title()`
- fallback regex: `elite\s*-\s*dangerous`
- current Linux trackers choose the focused match first, otherwise the largest matching window

That baseline has worked for current X11-derived tracking, but GNOME helper-backed support should not depend on title alone until we know what Shell exposes for real Wine/Proton windows.

#### Decision Rationale
Use a weighted identity contract rather than a single-field match.

Required initial match:
- normalized title matches `Elite - Dangerous` or accepted localized/variant title discovered during validation

Strong supporting signals, when available:
- GNOME Shell app id / window class / WM class matches known Elite/Wine/Proton identifiers for the detected launcher path
- process id or process metadata points to Wine/Proton/Steam/Epic launch ancestry for Elite Dangerous
- window is a normal/toplevel game window with nonzero geometry
- window is visible/on current workspace or in a supported target state
- window size/display mode is plausible for the configured game display mode

Tie-breakers:
- prefer currently focused matching game window
- otherwise prefer the largest visible matching game window
- keep a stable helper target token for the selected `Meta.Window` and only reacquire when that token becomes invalid/stale

Rejection rules:
- never attach to EDMC, the Overlay Controller, the overlay client, extension diagnostics, or other plugin windows
- never attach to the Elite launcher when the actual game client is absent; report target not found or launcher-only state instead
- do not silently attach when multiple plausible Elite windows are ambiguous; report `target_ambiguous`
- do not treat mock/test windows as production targets unless a development/test flag explicitly enables mock matching

#### Q4 Tests To Run

| Test | Goal | Command / Action | Pass Signal | Failure Signal |
| --- | --- | --- | --- | --- |
| T-Q4-1 Xwayland metadata inventory | Capture title/class/PID-style metadata currently visible for the real game. | `wmctrl -lGx`, then `xprop` on the game window id if available. | We know title, WM class, geometry, and any X11-exposed process metadata for the actual game. | Only title is useful, or metadata differs unexpectedly across modes. |
| T-Q4-2 Process ancestry inventory | Determine whether a visible window id can be connected to Wine/Proton/Steam process metadata. | Use `xprop _NET_WM_PID` if present, then inspect `ps` for that PID and parent chain. | Process metadata can strengthen identity. | PID is absent/wrong/unhelpful, so helper must not depend on it. |
| T-Q4-3 Mode stability check | Compare metadata across windowed and borderless fullscreen. | Run T-Q4-1/T-Q4-2 in both supported modes. | Identity fields are stable enough for one matcher. | Fields change by mode, requiring mode-specific matching or lower confidence. |
| T-Q4-4 Restart stability check | Compare metadata across game restart and EDMC restart. | Re-run inventory after restarting the game and/or EDMC. | Stable fields remain stable; volatile fields are marked as per-window tokens only. | Key matching fields change too much for reliable support. |
| T-Q4-5 Shell extension metadata probe | Determine what the GNOME Shell extension can see directly from `Meta.Window`. | Use a temporary extension/prototype after Q4. | Shell exposes enough title/class/pid/app/window-state data to implement matcher in the helper. | Shell exposes less than X11 tools; Q4 matcher must be adjusted. |

#### Q4 Follow-Up
- Add fake-helper tests for `target_found`, `target_not_found`, `target_ambiguous`, `launcher_only`, and `target_stale`.
- Validate whether title variants/localization exist in supported Elite Dangerous configurations before broadening the mandatory title pattern.
- Keep process/PID diagnostics safe and avoid broad process scans per issue #82.

#### Evidence Collected
- GitHub issue #82 (`pgrep is finding too much`) documents a real false-positive failure from broad process substring matching: `pgrep -f "EDMarketConnector"` matched unrelated Firefox/browser command lines containing an EDMarketConnector GitHub URL. This is directly relevant to Q4: helper target identity must not rely on loose process substring matching.
- T-Q4-1 windowed metadata inventory on 2026-05-09 found both launcher and client windows using the same Steam app class. `wmctrl -lGx` showed `elite launcher` as `steam_app_359320.steam_app_359320` and the actual game as `Elite - Dangerous (CLIENT)` with the same `steam_app_359320.steam_app_359320` class. Therefore WM class/app id is a useful supporting signal for Steam app identity, but it does not distinguish launcher vs game client by itself and must not be required for non-Steam launchers.
- `xprop` on the actual Steam-launched game window `0x05800003` reported `WM_NAME="Elite - Dangerous (CLIENT)"`, `WM_CLASS="steam_app_359320", "steam_app_359320"`, `_NET_WM_NAME="Elite - Dangerous (CLIENT)"`, `_NET_WM_PID=126153`, and `_NET_WM_WINDOW_TYPE_NORMAL`. This supports making title match mandatory for first-release target selection, with launcher-specific app/class metadata and normal toplevel type as supporting evidence.
- T-Q4-3 borderless metadata check on 2026-05-09 matched the windowed identity fields. In borderless fullscreen, `wmctrl` reported the actual game as `0x05800003 0 0 0 3440 1440 steam_app_359320.steam_app_359320 ... Elite - Dangerous (CLIENT)`, while `xprop` still reported `WM_NAME="Elite - Dangerous (CLIENT)"`, `WM_CLASS="steam_app_359320", "steam_app_359320"`, `_NET_WM_NAME="Elite - Dangerous (CLIENT)"`, `_NET_WM_PID=126153`, and `_NET_WM_WINDOW_TYPE_NORMAL`. This supports one identity matcher across windowed and borderless modes; geometry/display state changes, identity fields do not.
- Follow-up process inspection for `_NET_WM_PID=126153` could not find the process by the time it was checked, so PID/process ancestry remains unproven and should be treated as advisory until captured live.
- T-Q4-5 Shell extension metadata probe passed on 2026-05-09. A temporary GNOME Shell extension reported the actual Steam-launched game client with `title="Elite - Dangerous (CLIENT)"`, `wmClass="steam_app_359320"`, `wmClassInstance="steam_app_359320"`, `appName="steam_app_359320"`, `pid=9135`, `windowType=0`, full-screen `frameRect`/`bufferRect` at `0,0 3440x1440`, `monitor=0`, `showingOnWorkspace=true`, and `minimized=false`. It also reported the launcher separately as `title="elite launcher"` with the same Steam class and 1280x720 geometry. This confirms the Shell helper can see the fields needed for the Q4 identity contract and must use title to distinguish game client from launcher. The Steam class evidence is launcher-specific and should be broadened with Epic/non-Steam validation later.

### Closed Question: Q5 Coordinate-Space Contract

#### Problem
The helper must report geometry in a coordinate space that the overlay can use without mixing GNOME Shell, Xwayland, and Qt interpretations of `x`, `y`, `width`, and `height`.

This matters because earlier GNOME Wayland testing showed Qt `setGeometry` and `moveEvent` can report positions that do not match visible compositor placement. Therefore Qt geometry is not authoritative for Shell-visible placement.

#### Decision
The helper reports GNOME Shell global logical coordinates as the authoritative coordinate space for GNOME Wayland, but it must distinguish window actor geometry from game-content alignment geometry.

Each target update should include:
- `frameRect`
- `bufferRect`
- `contentRect` or `targetContentRect`
- decoration/content inset metadata when available
- monitor index/output identity
- workspace/showing/minimized/focus/fullscreen state
- timestamp/sequence number
- later: output scale and logical/physical size metadata if Shell exposes it cleanly

Report `frameRect` and `bufferRect` from Shell for diagnostics and presentation context, but use the named content/client rect for overlay alignment. Windowed testing shows Shell `frameRect` includes titlebar/decorated-window area while the current Xwayland tracker reports the game client/content area.

In borderless fullscreen on the tested setup, `frameRect`, `bufferRect`, and `contentRect` collapse to the same monitor-sized rectangle. In windowed mode, `contentRect` is `frameRect` minus decoration/content insets when those insets can be read or derived. If the helper cannot derive content bounds from Shell alone, windowed mode must remain degraded until presentation/placement can align overlay content to the actual game viewport.

If PyQt remains the renderer, the client treats Shell helper geometry as Shell logical coordinates and converts only through a documented GNOME-specific adapter. It must not treat Qt `moveEvent` as proof that the compositor-visible overlay moved.

#### Q5 Tests To Run

| Test | Goal | Command / Action | Pass Signal | Failure Signal |
| --- | --- | --- | --- | --- |
| T-Q5-1 Borderless Shell geometry | Confirm Shell frame/buffer rects in borderless fullscreen. | WindowProbe `DumpWindows("elite")` in borderless fullscreen. | `frameRect` and `bufferRect` match the full monitor rect. | Frame/buffer diverge unexpectedly or monitor is wrong. |
| T-Q5-2 Client geometry comparison | Compare current client/Xwayland tracker geometry with Shell geometry. | `grep -E "Tracker state|Raw tracker|Calculated overlay geometry|Applying geometry|Overlay moveEvent|Recorded WM authoritative rect" overlay_client.log | tail -80` | Client and Shell agree where expected, or divergence is documented. | No comparable logs or unexplained coordinate mismatch. |
| T-Q5-3 Windowed Shell geometry | Capture Shell frame/buffer rects after moving the game in windowed mode. | WindowProbe `DumpWindows("elite")` in windowed mode. | Rects match the visible game location/size in Shell logical space. | Rects differ from visible placement or omit needed frame/buffer distinction. |
| T-Q5-4 Windowed resize geometry | Capture Shell rects before/after resizing the game. | WindowProbe before/after resize plus client logs. | Size changes are reflected consistently; primary alignment rect is clear. | Size updates require special handling or diverge by rect type. |
| T-Q5-5 Monitor/scale inventory | Capture monitor layout and scale context for interpreting Shell coordinates. | `xrandr --listmonitors` plus Shell monitor/output data when available. | Contract can name logical/global coordinates and scale behavior. | Scale metadata is missing or inconsistent, requiring explicit deferral. |

#### Evidence Collected
- T-Q5-1 partial evidence on 2026-05-09: in borderless fullscreen, the WindowProbe extension reported the Elite client `frameRect` and `bufferRect` both at `x=0`, `y=0`, `width=3440`, `height=1440`, `monitor=0`, with `showingOnWorkspace=true` and `minimized=false`. This supports using Shell global logical coordinates and shows no frame/buffer distinction in borderless fullscreen on this setup.
- T-Q5-2 attempted on 2026-05-09 using `tail -120 overlay_client.log | grep ...`, but no matching geometry lines were present in the last 120 log lines. This comparison remains incomplete; use whole-file `grep ... | tail -80` or trigger a fresh overlay follow update before comparing client and Shell coordinates.
- T-Q5-3 windowed Shell geometry on 2026-05-09: WindowProbe reported the Elite client on `monitor=0` with `frameRect=(1568,262,1440,997)` and `bufferRect=(1554,250,1468,1026)`, while the launcher remained at `frameRect=(1080,360,1280,720)` and `bufferRect=(1080,360,1280,720)`. This confirms Shell coordinates are global logical desktop coordinates, and that `frameRect` and `bufferRect` can diverge in windowed mode.
- T-Q5-5 monitor inventory on 2026-05-09: `xrandr --listmonitors` reported two side-by-side 3440x1440 monitors: primary `DP-2` at `+0+0` and `HDMI-1` at `+3440+0`. The Shell window probe's `monitor=0` maps to the primary `DP-2` monitor in this test.
- T-Q5-2 client geometry log comparison on 2026-05-09: whole-file log grep showed current tracker/calculated geometry uses the same global desktop coordinate convention as the monitor layout (`DP-2` at `0,0`, `HDMI-1` at `3440,0`). The logs also show dynamic windowed sizes such as `1440x1080`, `1280x960`, and `1920x1080` being detected/applied. However, borderless/fullscreen entries repeatedly recorded WM authoritative rects moving the overlay between `DP-2` and `HDMI-1` independently of intended target geometry, confirming again that Qt `moveEvent`/WM intervention is not authoritative for Shell-visible placement. This log slice was not synchronized with the WindowProbe windowed sample, so it did not resolve whether `frameRect` or `bufferRect` is the correct content-alignment rectangle.
- T-Q5 synchronized client comparison was blocked on 2026-05-09 because `overlay_client.log` was stale. The file had not been modified since the morning, no files under `/home/jon/edmc-logs` had been updated in the last 30 minutes, and no matching overlay/EDMC process was visible from a local `ps` check. Restart EDMC/overlay and verify the log updates before rerunning the synchronized comparison.
- T-Q5 synchronized comparison evidence on 2026-05-09: with fresh overlay logs, the Shell probe reported windowed Elite `frameRect=(1080,216,1280,997)` and `bufferRect=(1066,204,1308,1026)`. The fresh client log at startup reported tracker/calculated geometry `target=(1080,253,1280,960)`. This lines up with Shell `frameRect` for X/width, but Y is 37 px lower and height is 37 px smaller, consistent with the current tracker reporting game client/content area while Shell `frameRect` includes the titlebar/decorated frame. Later client updates showed target rects changing to `(1723,220,1280,960)` and `(1000,253,1440,960)` as the window was moved/resized, confirming live client updates but also showing the need for an explicitly named content-alignment rect rather than choosing `frameRect` or `bufferRect` blindly.
- T-Q5 decoration-inset evidence on 2026-05-09: `xprop` on the same window reported `_NET_FRAME_EXTENTS(CARDINAL) = 0, 0, 37, 0` and no `_GTK_FRAME_EXTENTS`. `xwininfo` reported absolute upper-left `(1000,253)`, relative upper-left `(14,49)`, and size `1440x960`. This confirms the fresh client tracker target `(1000,253,1440,960)` is the game client/content rect, while the Shell `frameRect` top edge is 37 px above it. Therefore Q5 must name and carry `contentRect`/decoration insets explicitly; raw `frameRect` would shift a normal windowed overlay down from the game viewport.

#### Q5 Follow-Up
- Prototype whether the GNOME Shell extension can read or derive `_NET_FRAME_EXTENTS`-equivalent decoration insets for Xwayland/Wine windows directly. If it cannot, the helper must report `content_rect_unavailable` and keep windowed mode degraded rather than guessing.
- Add fake-helper tests for borderless `frameRect == bufferRect == contentRect`, windowed top-inset derivation, multi-monitor global coordinates, and stale/invalid geometry.
- Define how monitor/output scale metadata is represented before claiming mixed-DPI or fractional-scaling support.

### Closed Question: Q6 Install/Enable Lifecycle

#### Problem
The helper can only support GNOME Wayland true-overlay behavior if users can install, enable, update, disable, and remove the GNOME Shell extension predictably.

Q6 must define the exact lifecycle model before implementation. It must avoid treating "files copied", "extension enabled", "extension active", and "helper DBus reachable/protocol-compatible" as the same state.

#### Decisions So Far
- Fixed helper UUID: `edmc-modern-overlay-helper@edmcmodernoverlay.github.io`.
- Repo package path: `helpers/gnome_shell_extension/`.
- Default installation is user-local, not system-wide: `~/.local/share/gnome-shell/extensions/edmc-modern-overlay-helper@edmcmodernoverlay.github.io/`.
- Install method: directly copy the source directory into the user-local GNOME Shell extension path, then use `gnome-extensions info`, `gnome-extensions enable`, `gnome-extensions disable`, and helper DBus health checks for lifecycle state.
- Install/enable sequence: detect GNOME Wayland, check prerequisites, then with explicit user approval copy files, verify discovery, check global user-extension setting, enable extension, require logout/login, then verify `ACTIVE` and DBus health.
- User approval rule: any action that installs, updates, removes, enables, disables, or changes GNOME/plugin configuration for the helper requires explicit user approval before the action runs.
- Logout/login rule: after helper install, update, uninstall, enable/disable, or global user-extension configuration changes, the user must log out and log back in before the helper is treated as final-active or final-removed. Final `ACTIVE` and DBus health verification happens after the user returns to a fresh session.
- Update behavior: with user approval, disable the extension, remove/replace the installed helper directory with a fresh copy from `helpers/gnome_shell_extension/`, enable the extension, require logout/login, then verify `State: ACTIVE`, DBus health, helper version, and protocol compatibility. Do not keep a backup/rollback copy; users can revert by reinstalling an older plugin version.
- Release artifact shape: source directory only. Do not require or ship a zip as the primary helper artifact.
- The helper artifact should be a small source directory rather than an opaque binary or only a zip. This keeps the helper easy to inspect and easier to debug.
- Installer-driven and manual installation should consume the same source-directory artifact shape.
- Any system-wide install path is out of the default flow and should be treated as advanced/manual unless a later packaging decision proves it is needed.

#### Decision Candidate
Install the packaged source directory from `helpers/gnome_shell_extension/` into the current user's GNOME Shell extension directory using the fixed helper UUID.

Lifecycle commands should use direct file copy for install/update and GNOME's own tooling for Shell lifecycle state:
- install/copy: copy `helpers/gnome_shell_extension/` to `~/.local/share/gnome-shell/extensions/edmc-modern-overlay-helper@edmcmodernoverlay.github.io/`
- enable: `gnome-extensions enable edmc-modern-overlay-helper@edmcmodernoverlay.github.io`
- status: `gnome-extensions info edmc-modern-overlay-helper@edmcmodernoverlay.github.io` plus DBus helper health check
- disable: `gnome-extensions disable edmc-modern-overlay-helper@edmcmodernoverlay.github.io`
- uninstall: disable first, then remove only `~/.local/share/gnome-shell/extensions/edmc-modern-overlay-helper@edmcmodernoverlay.github.io/`

Install/enable order:
1. Detect GNOME Wayland.
2. Check helper prerequisites.
3. Ask for explicit user approval.
4. Copy helper files into the user-local extension path.
5. Verify GNOME Shell discovers the extension with `gnome-extensions info`.
6. Check `org.gnome.shell disable-user-extensions`.
7. Enable the extension with `gnome-extensions enable`.
8. Instruct the user to log out and log back in.
9. After login, verify `gnome-extensions info` reports `State: ACTIVE`.
10. Verify helper DBus health and protocol compatibility.

Active/healthy status must require all of:
- files installed at the expected path
- GNOME Shell can discover the extension
- user extensions are not globally disabled
- the extension is enabled and active
- the helper DBus service is reachable
- protocol/helper version is compatible

#### Q6 Workflow Summary

These workflows are the current Q6 source of truth if conversation context is lost.

Common rules:
- Every install, update, uninstall, enable/disable, or helper-related config change requires explicit user approval before it runs.
- The helper is installed only for the current user.
- The helper source in this repo is `helpers/gnome_shell_extension/`.
- The installed GNOME Shell extension path is `~/.local/share/gnome-shell/extensions/edmc-modern-overlay-helper@edmcmodernoverlay.github.io/`.
- The release/helper artifact is source-directory-only; no zip is required for install/runtime behavior.
- After install, update, uninstall, enable/disable, or global user-extension config changes, the user must log out and log back in before final state is trusted.
- Final `true_overlay` eligibility requires post-login `State: ACTIVE`, reachable helper DBus service, compatible helper version, and compatible protocol version.

Install/enable workflow:
1. Detect GNOME Wayland.
2. Check helper prerequisites.
3. Ask for explicit user approval.
4. Copy `helpers/gnome_shell_extension/` to `~/.local/share/gnome-shell/extensions/edmc-modern-overlay-helper@edmcmodernoverlay.github.io/`.
5. Verify GNOME Shell can discover the extension with `gnome-extensions info edmc-modern-overlay-helper@edmcmodernoverlay.github.io`.
6. Check `org.gnome.shell disable-user-extensions`.
7. Enable with `gnome-extensions enable edmc-modern-overlay-helper@edmcmodernoverlay.github.io`.
8. Instruct the user to log out and log back in.
9. After login, verify `State: ACTIVE`.
10. Verify helper DBus health, helper version, and protocol compatibility.

Update workflow:
1. Detect installed helper version and packaged helper version.
2. If update is needed, ask for explicit user approval.
3. Disable with `gnome-extensions disable edmc-modern-overlay-helper@edmcmodernoverlay.github.io`.
4. Remove/replace the installed helper directory with a fresh copy from `helpers/gnome_shell_extension/`.
5. Enable with `gnome-extensions enable edmc-modern-overlay-helper@edmcmodernoverlay.github.io`.
6. Instruct the user to log out and log back in.
7. After login, verify `State: ACTIVE`, DBus health, helper version, and protocol compatibility.
8. Do not keep a backup/rollback copy; recovery is reinstalling an older plugin version.

Disable workflow:
1. Ask for explicit user approval.
2. Disable with `gnome-extensions disable edmc-modern-overlay-helper@edmcmodernoverlay.github.io`.
3. Instruct the user to log out and log back in.
4. After login, verify the extension is not active and helper DBus is not reachable as a healthy helper.

Uninstall workflow:
1. Ask for explicit user approval.
2. Disable with `gnome-extensions disable edmc-modern-overlay-helper@edmcmodernoverlay.github.io`.
3. Remove only `~/.local/share/gnome-shell/extensions/edmc-modern-overlay-helper@edmcmodernoverlay.github.io/`.
4. Instruct the user to log out and log back in.
5. After login, verify the extension is not installed/active and helper DBus is not reachable as a healthy helper.

#### Q6 Remediation State Model

Remediation states describe helper applicability/health, not the full Linux platform classifier. The platform classifier should stay separate so future Linux variants can add their own helpers without overloading GNOME-specific negative states.

Current state names:
- `not_required`: this GNOME Wayland helper is not required for the current platform/session.
- `prerequisites_missing`: helper is required, but required host tools or session services are missing.
- `not_installed`: helper is required, but the user-local extension directory is missing.
- `installed_not_discovered`: helper files exist, but GNOME Shell does not discover the extension.
- `globally_disabled`: GNOME user extensions are globally disabled.
- `disabled`: extension is discovered but not enabled.
- `restart_required`: a lifecycle/config action has been performed and logout/login is required before final verification.
- `inactive_or_error`: extension is enabled but not `ACTIVE` after logout/login, or GNOME reports an extension error state.
- `dbus_unreachable`: extension is active, but the helper DBus service is not reachable.
- `protocol_incompatible`: helper DBus is reachable, but helper version/protocol is incompatible with the client.
- `healthy`: extension is active, helper DBus is reachable, and helper version/protocol is compatible.

#### Q6 Remediation Messages

These state IDs should remain stable for logs/tests. User-facing copy can be refined, but it must preserve the action and distinction.

| State | User-facing meaning | User action |
| --- | --- | --- |
| `not_required` | The GNOME Wayland helper is not required for this session. | No action. |
| `prerequisites_missing` | Required GNOME helper tools or session services are missing. | Install/enable the listed prerequisites, then retry helper setup. |
| `not_installed` | The GNOME Wayland helper is not installed for this user. | Approve the helper install workflow. |
| `installed_not_discovered` | Helper files exist, but GNOME Shell does not discover the extension. | Log out and back in, then retry verification; reinstall if it still is not discovered. |
| `globally_disabled` | GNOME user extensions are globally disabled. | Approve enabling user extensions or change it manually, then log out and back in. |
| `disabled` | The helper extension is discovered but disabled. | Approve the helper enable workflow, then log out and back in. |
| `restart_required` | A helper lifecycle/config change was made and needs a fresh session. | Log out and back in, then reopen/recheck EDMC. |
| `inactive_or_error` | GNOME reports the helper extension is enabled but not active, or it reports an error. | Review the `gnome-extensions info` state/error, then reinstall or report diagnostics if it persists after logout/login. |
| `dbus_unreachable` | The extension appears active, but the overlay client cannot reach the helper DBus service. | Log out and back in, then verify again; reinstall or report diagnostics if it persists. |
| `protocol_incompatible` | The helper is reachable, but its version/protocol does not match this plugin version. | Approve the helper update workflow or reinstall a matching plugin/helper version. |
| `healthy` | The helper is active, reachable, and protocol-compatible. | No action. GNOME Wayland true-overlay eligibility may proceed. |

#### Q6 Tests To Run

| Test | Goal | Command / Action | Pass Signal | Failure Signal |
| --- | --- | --- | --- | --- |
| T-Q6-1 Extension path probe | Confirm user-local extension path and fixed UUID are discoverable. | Copy a temporary extension source directory to `~/.local/share/gnome-shell/extensions/<uuid>/`, log out/in, then run `gnome-extensions info <uuid>`. | GNOME reports the extension path and initialized state after login. | Extension is not discovered after login. |
| T-Q6-2 Enable/active probe | Confirm enablement transitions to active when global user extensions are allowed. | With user approval, set prerequisites/config as needed, run `gnome-extensions enable <uuid>`, log out/in, then run `gnome-extensions info <uuid>`. | `Enabled: Yes` and `State: ACTIVE` after login. | Enabled list changes but state remains inactive/error after login. |
| T-Q6-3 Global disable blocker | Confirm global disablement is detected distinctly. | Set `org.gnome.shell disable-user-extensions true` with extension in enabled list. | Status reports globally blocked, not missing or incompatible. | UI/logs collapse it into generic disabled/missing. |
| T-Q6-4 Disable/uninstall probe | Confirm cleanup affects only the helper. | `gnome-extensions disable <uuid>`, remove helper directory, verify other extensions unchanged. | Helper gone/inactive; unrelated extensions remain. | Cleanup removes wrong files or leaves stale active helper. |
| T-Q6-5 Update probe | Confirm clean-replacing the source directory yields expected version/protocol state. | Install v1, disable, replace installed directory with v2 source directory, enable, log out/in, then verify active/version/protocol. | Helper reports new version and compatible protocol after login. | Old code stays active, replacement fails unclearly, or protocol state lies. |

### Closed Question: Q7 Post-Install GNOME Wayland Remediation

#### Decision
For the first helper implementation, the **installer is the helper-install path**.

When the installer runs while the user is logged into GNOME Wayland, it must detect GNOME Wayland and run the Q6 helper install/enable workflow with explicit user approval.

Post-install remediation after a user originally installed under X11 and later switches to GNOME Wayland is **settings warning plus installer rerun**, not in-settings install/uninstall.

When settings/status detects GNOME Wayland and the helper is required but unavailable or unhealthy:
- show a persistent helper warning in settings/status
- show the current helper remediation state from the Q6 state model
- tell the user to rerun the plugin installer while logged into GNOME Wayland, so the installer detects GNOME Wayland and installs/enables the helper with approval
- after installer completion, tell the user to log out and log back in
- after login, verify helper `State: ACTIVE`, DBus health, helper version, and protocol compatibility

#### Rationale
This deliberately chooses the simplest first-pass remediation path even though richer in-app remediation was considered. It keeps GNOME Shell extension file/config mutation inside the installer workflow instead of adding settings-panel install/uninstall buttons now. The settings surface remains responsible for detection, warning, state display, and directing the user to the installer.

#### Deferred
- In-settings **Install Helper**, **Enable Helper**, **Update Helper**, and **Uninstall Helper** buttons.
- Guided setup wizard.
- Startup pop-up prompting install after a session switch.

#### Q7 Acceptance
- Installer run under GNOME Wayland must offer/run the helper install flow with explicit user approval.
- GNOME Wayland with missing/unhealthy helper must not be silent.
- Settings/status must not claim `true_overlay` while helper is unavailable.
- The warning must be actionable: rerun installer while using GNOME Wayland so the installer detects GNOME Wayland and installs/enables the helper, then log out/in.
- The installer must still use the Q6 lifecycle, approval, logout/login, and health-verification rules.

### Closed Question: Q8 Helper State Surfaces

#### Problem
Q6 defines helper lifecycle/remediation states, but Q8 must define where those states appear. The current GNOME Wayland status problem came from one surface claiming `true_overlay` while another surface reported `missing_helper`, so this plan needs one authoritative helper/backend status object rendered consistently everywhere.

#### Decision
Use a single client-authoritative helper/backend status object and render it into every user/support surface. Preferences, logs, debug scripts, and debug overlay metrics must not compute conflicting helper state independently.

#### Required Surfaces
- Preferences/settings panel backend status and warning text.
- User-facing backend mode summary.
- Overlay client logs, including one stable grep-friendly helper status line.
- EDMC/plugin status bridge logs where backend/helper state is relayed.
- `utils/collect_overlay_debug_linux.sh`.
- `utils/collect_overlay_debug_windows.ps1` where applicable, with non-Linux output saying GNOME helper is `not_required`.
- Any future `utils/collect_overlay_debug_*` or similarly named helper/debug collection scripts.
- The live **Show debug overlay metrics** overlay.

#### Required Fields
- platform/session classifier, for example `linux_gnome_wayland`
- backend family and instance
- support classification, for example `true_overlay` or `degraded_overlay`
- helper required flag
- helper kind, for example `gnome_shell_extension`
- helper remediation state from Q6
- extension UUID
- installed helper path
- GNOME extension discovered/enabled/active state when available
- global user-extension disabled state
- DBus reachable state
- helper version
- helper protocol version
- client expected protocol version
- logout/login required flag
- last health-check timestamp or freshness indicator
- last failure reason

#### Surface-Specific Rules
- If helper is required but state is not `healthy`, no user-facing surface may report `true_overlay`.
- Preferences/settings should show the full remediation state and the Q7 installer-rerun instruction when applicable.
- Logs should include a compact stable line suitable for support triage, for example: `GNOME helper status: required=true state=not_installed uuid=... path=... enabled=false active=false dbus=false protocol=none expected=1 classification=degraded_overlay`.
- `utils/collect_overlay_debug_linux.sh` must collect the helper status line plus host/session facts needed to understand it, such as GNOME session type, desktop, GNOME Shell version if available, `gnome-extensions info`, global user-extension setting, installed path existence, and DBus reachability.
- The Windows debug collector should not try to inspect GNOME Shell, but should make clear that the GNOME helper is `not_required` on Windows.
- The live debug overlay metrics must include a compact helper/backend summary when debug metrics are enabled, so a user can see GNOME helper required/healthy/degraded state without digging through logs.
- Diagnostic output should avoid broad process command-line dumps by default. Any expanded process/window metadata belongs behind explicit debug intent and Q11 privacy rules.

#### Compact Display Text

Preferences/settings:
- `GNOME Wayland helper: <state>`
- `Action: <Q6/Q7 remediation text>`

Live debug overlay metrics:
- `Backend: <backend_instance> <classification>`
- `Helper: required <helper_state>` when helper is required
- `Helper: not_required` when helper is not required

Keep live overlay text compact; detailed diagnostics belong in settings/logs/collector output.

#### Stable Field Names

Use these field names in the status object, logs, and collector output:
- `platform`
- `backend_family`
- `backend_instance`
- `classification`
- `helper_required`
- `helper_kind`
- `helper_state`
- `helper_uuid`
- `helper_path`
- `extension_discovered`
- `extension_enabled`
- `extension_active`
- `user_extensions_disabled`
- `dbus_reachable`
- `helper_version`
- `helper_protocol`
- `expected_protocol`
- `logout_required`
- `last_health_check`
- `failure_reason`

#### Collector Source Of Truth

Debug collector scripts should collect both:
- the overlay-client authoritative status/log line when available
- direct host facts on Linux, including session/desktop environment, GNOME Shell version when available, `gnome-extensions info`, `gsettings get org.gnome.shell disable-user-extensions`, installed path existence, and DBus bus visibility

The overlay-client status is primary when available because it is the runtime classification authority. Direct host facts are still required because the overlay client may be stopped, stale, or failing before it can publish status.

### Closed Question: Q9 GNOME Shell Version And Distro Support

#### Problem
The extension package, release notes, and validation matrix need a clear first support target. GNOME Shell extension APIs can drift between Shell versions, so the helper cannot claim broad GNOME Wayland support without naming the version floor and validation evidence.

#### Decisions So Far
- Minimum supported GNOME Shell version target: `46`.
- Support target: GNOME Shell `46` and newer.
- Initial observed validation baseline from this investigation: GNOME Shell `46` on GNOME Wayland.
- First distro/session validation target: Ubuntu GNOME Wayland.
- Initial release metadata shell-version entries: `["46", "47", "48", "49", "50"]`.
- Newer GNOME Shell versions are added after reviewing the GNOME porting guide and doing at least smoke validation.

#### Decision
Implement and package the helper for GNOME Shell 46+.

The extension metadata should include explicit entries for GNOME Shell `46`, `47`, `48`, `49`, and `50`. Because GNOME extension metadata does not represent open-ended support well, newer GNOME Shell versions should be added explicitly after reviewing the porting guide and doing at least smoke validation.

First-party validation starts with Ubuntu GNOME Wayland because it is the current real test environment and already has evidence in this plan. Fedora GNOME Wayland and other distros remain follow-up validation targets.

Release/support wording must separate target from validation:

> The GNOME Wayland helper targets GNOME Shell 46 and newer. Initial validation is on Ubuntu GNOME Wayland with GNOME Shell 46. Additional GNOME Shell versions and distributions are supported as validated.

#### GNOME 46-50 Compatibility Notes

Initial research does not show a single large GNOME Shell 46-to-50 extension break comparable to the GNOME 45 ESM migration. Because this plan targets GNOME Shell 46+, the helper starts after the ESM transition and should use modern extension module structure from the beginning.

Known compatibility risks to design around:
- GNOME Shell 46 renamed extension lifecycle/state terminology toward `ACTIVE`/`INACTIVE`; status handling should use active-state terminology.
- GNOME Shell 47/48 changed or removed several Clutter/GJS types. This should not affect a minimal DBus/window-state helper unless rendering or drawing is moved into the extension.
- GNOME Shell 48 moved/renamed some `Meta` compositor APIs, including compositor/window actor access patterns. Shell-mediated presentation/stacking code must feature-test APIs instead of assuming one version's private API shape.
- GNOME Shell 49 removed `Meta.Rectangle`; helper geometry should use plain DBus-safe objects or version-safe rectangle helpers such as `Mtk.Rectangle` where needed.
- GNOME Shell 49/50 porting guides report no relevant `metadata.json` or `extension.js` structure changes, but release metadata still needs explicit supported shell-version entries.

Design guidance:
- Keep the extension minimal: DBus service, target/window state, health/version reporting, and the narrow presentation hooks required by Q1.
- Prefer plain JSON-like DBus payloads for rectangles/state instead of exporting Shell/Mutter object types.
- Feature-test Shell/Mutter APIs used for target enumeration, actor/presentation, stacking, and geometry.
- Treat unsupported/missing APIs as helper degraded states, not crashes.
- Avoid moving rendering into the extension unless the PyQt renderer cannot satisfy Q1 validation.

### Closed Question: Q10 First Release Validation Matrix

#### Decision
The first GNOME Wayland helper release claim requires the validation matrix below. Any failed or deferred item blocks a GNOME Wayland `true_overlay` claim unless release wording explicitly downgrades the feature and names the missing guarantee.

#### Environment Gate
- Ubuntu GNOME Wayland.
- GNOME Shell 46 initial validation.
- Multi-monitor validation included.
- Supported game display modes: windowed and borderless fullscreen only.
- Exclusive fullscreen remains out of scope and unsupported.

#### Install/Lifecycle Gate
- Installer detects GNOME Wayland.
- User approval is required before helper install/config changes.
- Helper files copy to the user-local extension path.
- Extension is discovered and enabled.
- Logout/login is completed after lifecycle/config changes.
- `gnome-extensions info` reports `State: ACTIVE`.
- Helper DBus health passes.
- Helper version and protocol are compatible with the client.
- Update flow passes: disable, clean replace, enable, logout/login, verify active/version/protocol.
- Disable/uninstall flow passes and affects only the helper UUID directory.
- Q7 rerun-installer remediation passes after a simulated X11-to-GNOME-Wayland post-install switch.

#### Backend/Status Gate
- Missing helper reports `degraded_overlay`, not `true_overlay`.
- Healthy helper can report `true_overlay` only after active DBus/protocol validation.
- Preferences/settings, user-facing status, logs, debug collector scripts, and live debug overlay metrics agree on helper state.
- Visibility terminology is clear: the `force_render` rename work must not confuse payload rendering with keep-visible behavior.

#### Windowed Overlay Behavior Gate
- Elite Dangerous target is identified correctly.
- Launcher-only state does not attach.
- Overlay aligns to the game content/client rect.
- Overlay follows target moves.
- Overlay follows target resizes.
- Overlay is chrome/titlebar-free.
- Click-through works.
- Overlay remains stacked above the game after click-through.

#### Borderless Fullscreen Overlay Behavior Gate
- Elite Dangerous target is identified correctly.
- Overlay aligns to the monitor/game viewport.
- Overlay is chrome/titlebar-free.
- Overlay does not flash due foreground/visibility loops.
- Click-through works.
- Overlay remains stacked above the game after click-through.

#### Failure/Recovery Gate
- Helper disabled reports `disabled` or equivalent degraded helper state with actionable remediation.
- Global user extensions disabled reports `globally_disabled`.
- DBus unreachable reports `dbus_unreachable`.
- Protocol mismatch reports `protocol_incompatible`.
- Game not found does not attach to another window.
- Launcher-only state does not attach.
- Ambiguous target state does not attach and reports ambiguity.

#### Privacy/Security Gate
- Helper exposes no arbitrary command execution.
- Helper API stays narrow and local to the user session.
- Debug output avoids broad process command-line dumps by default.
- Helper emits only window/state metadata needed for attachment and support diagnostics.

### Closed Question: Q11 Security, Privacy, And Redaction

#### Decision
The GNOME Wayland helper is a local GNOME Shell extension used only for overlay attachment. It exposes limited window state to the local overlay client and does not capture screen contents or input.

#### User-Facing Copy
Use this wording as the basis for installer, docs, and release notes:

> EDMC Modern Overlay installs a GNOME Shell extension helper on GNOME Wayland. The helper runs inside your local GNOME Shell session and lets the overlay find and attach to the Elite Dangerous window. It observes limited window metadata such as window title, class/app id, geometry, monitor, focus/visibility state, and helper health. It does not capture screen contents, keyboard input, mouse input, game data, or network traffic.

Short release-note wording:

> The GNOME Wayland helper is a local GNOME Shell extension used only for overlay attachment. It exposes limited window state to the local overlay client and does not capture screen contents or input.

#### Allowed Helper Data
- target window title
- app/window class or app id
- GNOME/Mutter window token/id, preferably non-persistent
- PID only if Shell exposes it and it is needed for diagnostics
- geometry: `frameRect`, `bufferRect`, `contentRect`, decoration insets
- monitor/output id
- focus, visibility, minimized, workspace, and fullscreen state
- helper version, protocol, and health
- timestamps and sequence numbers

#### Default Logs/Diagnostics Must Avoid
- process command lines
- full process trees
- environment variables
- screen contents or screenshots
- keyboard or mouse event streams
- arbitrary GNOME Shell object dumps
- unrelated window titles
- broad process substring search results

#### Debug-Only Escalation
Deeper diagnostics must be explicit and labeled as debug data. Even in debug mode, avoid broad command-line dumps unless the user deliberately enables that collection for a specific support task.

#### Security Boundary
- DBus service is session-local.
- No network listener.
- No arbitrary command execution.
- No broad GNOME Shell control API.
- Protocol version, helper version, helper kind, and session token/freshness are validated.
- Mismatches fail closed.
- Methods/signals stay limited to health, helper lifecycle state, target state, and the narrow presentation/attachment actions required by Q1.

## Open Questions
- Q1 is closed with Shell-mediated attachment as the helper role.
- Q2 is closed with session DBus as the primary helper transport.
- Q3 is closed with extension-owned DBus service/object lifecycle and client registration/reconnect rules.
- Q4 is closed with a weighted Shell-visible Elite Dangerous target identity contract.
- Q5 is closed with Shell global logical coordinates plus an explicit content-rect/decorations contract.
- Q6 is closed with user-local direct-copy source-directory install, fixed helper UUID, repo package path, source-directory-only artifact, install/enable order, user-approval rule, logout/login rule, no-backup clean-replace update flow, and helper remediation state/message model.
- Q7 is closed with settings warning plus installer-rerun remediation after switching to GNOME Wayland post-install.
- Q8 is closed with one client-authoritative status object rendered across preferences/settings, logs, debug collectors, and live debug overlay metrics.
- Q9 is closed with GNOME Shell 46+ target, Ubuntu GNOME Wayland first validation target, explicit `metadata.json` entries for 46-50, and release wording that separates target from exact validation.
- Q10 is closed with the first release validation matrix and true-overlay claim gate.
- Q11 is closed with privacy copy, allowed helper data, default redaction rules, debug-only escalation, and local fail-closed security boundary.
- Requirements questions Q1-Q11 are complete.

## Follow-Up Implementation Questions

These questions are not requirements blockers, but they should be answered one at a time before implementation starts. They define sequencing, staging, and merge policy.

| Priority | Question | Status | Recommendation / Default | Why This Comes Here |
| --- | --- | --- | --- | --- |
| IQ1 | What is the first implementation slice? | Completed | Start with status truthfulness: GNOME Wayland with missing/unhealthy helper reports `degraded_overlay`, not `true_overlay`. | This fixes the current user-facing inconsistency before adding helper complexity. |
| IQ2 | What is the helper MVP boundary? | Completed | Stage the extension: manifest/package first, DBus health/version second, target discovery third, and presentation/stacking fourth. | Avoid building a large Shell extension before proving each boundary. |
| IQ3 | When do we rename `force_render`? | Completed | Rename `force_render` to `keep_overlay_visible` before helper behavior depends on it, ideally immediately after status truthfulness. Preserve backward-compatible migration from existing `force_render` config/settings/controller payloads. | Current naming continues to confuse rendering, visibility, and compositor presentation. |
| IQ4 | What should the installer do about globally disabled GNOME user extensions? | Completed | Detect `org.gnome.shell disable-user-extensions=true`, but do not change it automatically. With explicit user permission, show the remediation command/instructions and let the user run it themselves, then require logout/login and recheck. | Keeps host GNOME configuration mutation user-owned while still making remediation actionable. |
| IQ5 | How are helper version and protocol version managed? | Completed | `helper_version` tracks the plugin version exactly. `helper_protocol` is a separate integer contract version starting at `1`; client `expected_protocol` starts at `1`; mismatch reports `protocol_incompatible`. Tests/checklist must force an explicit protocol-bump decision when helper contract payloads or semantics change. | Update/compatibility checks require stable semantics. |
| IQ6 | What is the merge policy for incomplete helper code? | Completed | Incomplete helper code may merge incrementally only behind degraded-by-default production behavior and/or `gnome_helper_experimental=false` by default. The flag lives in overlay settings, is diagnostics-visible, and never permits `true_overlay` without Q10 validation. | Prevent accidental unsupported `true_overlay` claims. |
| IQ7 | Do we need an explicit cleanup note for temporary research extensions? | Completed | Add cleanup instructions for local research helpers such as `edmc-modern-overlay-window-probe@local.test` and `edmc-modern-overlay-dbus-smoke@local.test`; validation preflight must confirm only the real helper UUID is present/enabled. | Avoid stale test extensions affecting future validation. |

Recommended implementation order after these are answered:
1. Status truthfulness.
2. `force_render` visibility rename.
3. Helper package skeleton and manifest tests.
4. DBus health/version MVP.
5. Installer lifecycle.
6. Diagnostics, collectors, and debug overlay metrics.
7. Target discovery.
8. Presentation/stacking behavior.
9. Release validation and docs closeout.

### Temporary Research Extension Cleanup

Before implementation or validation, remove temporary GNOME Shell extensions created during research so they cannot affect helper discovery, DBus names, logs, or validation results.

Known research UUIDs:
- `edmc-modern-overlay-window-probe@local.test`
- `edmc-modern-overlay-dbus-smoke@local.test`

Cleanup commands:

```bash
for UUID in \
  edmc-modern-overlay-window-probe@local.test \
  edmc-modern-overlay-dbus-smoke@local.test
do
  gnome-extensions disable "$UUID" 2>/dev/null || true
  rm -rf "$HOME/.local/share/gnome-shell/extensions/$UUID"
  gnome-extensions info "$UUID" 2>/dev/null || true
done
```

Validation preflight:
- No research helper UUID is installed or enabled.
- Only the real helper UUID, `edmc-modern-overlay-helper@edmcmodernoverlay.github.io`, may be present for production helper validation.
- If global user extensions were changed during research, restore the intended test state before validation and record it.

## Decisions (Locked)
- This work is not part of the current `fix219_*` scope; it is a new GNOME-helper plan.
- GNOME Wayland without an active helper must not be called `true_overlay` in user-facing status.
- The helper must be explicit and user-approved; no silent GNOME Shell extension install or enable.
- `helper_approval.json` records consent/guidance only; it is not proof that the helper is installed or active.
- The overlay client remains the final authority for runtime backend status.
- `load.py` remains the EDMC control plane and should not become the helper runtime transport hub.
- The helper must preserve current payload rendering and grouping behavior; it only changes GNOME Wayland attachment/platform behavior.
- `xwayland_compat` remains an explicit fallback/override and must not be removed by this plan.
- Exclusive fullscreen is unsupported for this GNOME Wayland overlay plan. Supported play modes are windowed and borderless fullscreen.
- Q1 decision: GNOME Wayland true-overlay support requires Shell-mediated attachment/presentation. A geometry-only helper is not sufficient.
- Q2 decision: the GNOME helper uses session DBus as the primary IPC transport; Unix socket remains a reserved fallback only if DBus fails later.
- Q3 decision: the GNOME Shell extension owns the DBus service/object lifecycle; the overlay client registers one active session, validates helper messages, reconnects on service loss, and degrades on stale/unreachable helper state.
- Q4 decision: target matching requires the Shell-visible Elite Dangerous client title, with launcher-specific app/class metadata such as Steam's `steam_app_359320`, normal toplevel state, visible/non-minimized workspace state, nonzero geometry, monitor, and helper target token as supporting fields; launcher-only and ambiguous states must not attach.
- Q5 decision: helper geometry uses GNOME Shell global logical coordinates and must report `frameRect`, `bufferRect`, monitor/output identity, visibility/workspace state, and an explicit `contentRect`/decoration-inset contract; overlay alignment uses the content/client rect, while Shell geometry remains authoritative for GNOME Wayland presentation.
- Q6 partial decision: fixed helper UUID is `edmc-modern-overlay-helper@edmcmodernoverlay.github.io`; repo package path is `helpers/gnome_shell_extension/`; release artifact is source-directory-only; default helper installation is direct source-directory copy to `~/.local/share/gnome-shell/extensions/edmc-modern-overlay-helper@edmcmodernoverlay.github.io/`; use `gnome-extensions info/enable/disable` plus helper DBus health for lifecycle checks; any install/config-changing action requires explicit user approval; install/enable order is detect GNOME Wayland, check prerequisites, ask for approval, copy files, verify discovery, check global user-extension setting, enable, require logout/login, then verify `ACTIVE` and DBus health; update flow is disable, clean-replace from packaged source, enable, require logout/login, then verify active/version/protocol, with no backup kept.
- Q6 remediation state decision: helper remediation states are separate from platform/session classification and use platform-neutral `not_required` when this GNOME helper does not apply.
- Q6 decision: helper remediation states and messages are locked for `not_required`, `prerequisites_missing`, `not_installed`, `installed_not_discovered`, `globally_disabled`, `disabled`, `restart_required`, `inactive_or_error`, `dbus_unreachable`, `protocol_incompatible`, and `healthy`.
- Q7 decision: the installer is the helper-install path; when run under GNOME Wayland it must detect GNOME Wayland and run the helper install/enable flow with user approval. After a post-install switch from X11 to GNOME Wayland, settings/status warns when the required helper is unavailable and directs the user to rerun the installer while using GNOME Wayland; in-settings helper install/uninstall actions are deferred.
- Q8 decision: helper/backend state must be rendered from one authoritative status object across preferences/settings, user-facing status, logs, EDMC/plugin status bridge, `utils/collect_overlay_debug_*` scripts, and the live "Show debug overlay metrics" overlay; use stable field names, compact preferences/debug-overlay text, overlay-client status as primary collector source, and direct Linux host facts as fallback/support context.
- Q9 decision: target GNOME Shell 46 and newer; first validation target is Ubuntu GNOME Wayland; initial extension metadata lists shell versions `46`, `47`, `48`, `49`, and `50`; newer versions are added after porting-guide review and smoke validation; release wording separates the 46+ target from exact validated environments.
- Q10 decision: first release validation must pass environment, install/lifecycle, backend/status, windowed overlay, borderless fullscreen overlay, failure/recovery, and privacy/security gates; failed or deferred items block GNOME Wayland `true_overlay` release claims unless explicitly downgraded in release wording.
- Q11 decision: helper privacy/security copy states the local GNOME Shell extension observes limited window metadata for overlay attachment only; it does not capture screen contents, keyboard/mouse input, game data, or network traffic; default logs/diagnostics avoid process command lines, screenshots, environment variables, unrelated window titles, and broad Shell/process dumps; helper IPC remains local, narrow, versioned, and fail-closed.
- IQ1 decision: first implementation slice is status truthfulness; GNOME Wayland with missing/unhealthy helper must report `degraded_overlay`, not `true_overlay`, before helper package or installer complexity is added.
- IQ2 decision: helper MVP is staged as manifest/package, then DBus health/version, then target discovery, then presentation/stacking.
- IQ3 decision: rename `force_render` to `keep_overlay_visible` before helper behavior depends on it, with backward-compatible migration for existing config, settings, controller payloads, logs, docs, and tests.
- IQ4 decision: if GNOME user extensions are globally disabled, installer/settings detect the state but do not run `gsettings set org.gnome.shell disable-user-extensions false`; after explicit user permission, show the command/instructions for the user to run manually, then require logout/login and recheck helper state.
- IQ5 decision: `helper_version` tracks the plugin version exactly; `helper_protocol` is a separate integer contract version starting at `1`; client `expected_protocol` starts at `1`; protocol mismatch reports `protocol_incompatible`; tests and review checklist must force an explicit protocol-bump decision when helper contract payloads or semantics change.
- IQ6 decision: incomplete helper code may merge incrementally only behind degraded-by-default production behavior and/or `gnome_helper_experimental=false` by default; the flag is stored in overlay settings, included in diagnostics, and never permits `true_overlay` without Q10 validation.
- IQ7 decision: cleanup instructions are required for temporary research extensions; validation preflight must confirm research UUIDs are absent and only the real helper UUID may be present/enabled for production helper validation.

## Per-Iteration Test Plan
- **Env setup (once per machine):** `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements/dev.txt`
- **Headless quick pass (default for each step):** `source .venv/bin/activate && python -m pytest`
- **Targeted tests:** `source .venv/bin/activate && python -m pytest <path/to/tests> -k "<pattern>"`
- **Installer/script tests:** `source .venv/bin/activate && python -m pytest tests/test_install_linux.py -q`
- **Milestone checks:** `make check` and `make test`
- **Compliance baseline check (release/compliance work):** `python scripts/check_edmc_python.py`
- **Full suite with GUI deps (as applicable):** `source .venv/bin/activate && PYQT_TESTS=1 python -m pytest overlay_client/tests -q`
- **Manual GNOME validation:** record GNOME Shell version, distro, session type, monitor layout, scaling, EDMC install mode, helper version, exact install/enable commands, overlay logs, and pass/fail observations.
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

The implementation plan is intentionally broader than five phases. Each phase has a narrow behavioral goal, test gate, and rollback/degraded path. This keeps GNOME Shell integration incremental while preventing accidental `true_overlay` claims before Q10 validation passes.

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Status truthfulness and degraded fallback for missing/unhealthy helper | Completed |
| 2 | Visibility terminology rename from `force_render` to `keep_overlay_visible` | Completed |
| 3 | GNOME Shell extension package skeleton, metadata, and protocol constants | Completed |
| 4 | Session-DBus helper health/version MVP and client handshake/status object | Not Started |
| 5 | Installer lifecycle and post-install GNOME Wayland remediation | Not Started |
| 6 | Helper state surfaces, diagnostics, collectors, and debug overlay metrics | Not Started |
| 7 | Helper-backed target discovery and coordinate contract | Not Started |
| 8 | Shell-mediated presentation, attachment, stacking, and click-through behavior | Not Started |
| 9 | Release validation, docs, privacy/security closeout, and support claim gate | Not Started |

## Phase Coverage Against Requirements

| Requirement Area | Primary Phase(s) | Coverage Notes |
| --- | --- | --- |
| Support classification requirements | 1, 4, 6, 9 | Phase 1 fixes degraded-vs-true truthfulness; Phase 4 adds health/protocol authority; Phase 6 renders the same state everywhere; Phase 9 gates release claims. |
| Helper installation and enablement requirements | 5, 6, 9 | Phase 5 owns installer lifecycle, user approval, logout/login, and Q7 rerun-installer remediation; Phase 6 exposes state; Phase 9 validates. |
| Extension packaging requirements | 3, 5, 9 | Phase 3 creates metadata/package/protocol constants; Phase 5 installs source-directory artifact; Phase 9 validates metadata/release claims. |
| Install/enable lifecycle requirements | 5, 6, 9 | Phase 5 implements install/update/disable/uninstall and global user-extension manual remediation; Phase 6 reports lifecycle state; Phase 9 validates flows. |
| Helper runtime contract requirements | 3, 4, 7, 8 | Phase 3 defines constants; Phase 4 proves DBus health/fail-closed behavior; Phase 7 adds target state; Phase 8 adds presentation/attachment actions. |
| Runtime detection requirements | 1, 4, 5, 6 | Phase 1 fixes classification; Phase 4 detects active helper health/protocol; Phase 5 detects installed/enabled states; Phase 6 exposes diagnostics. |
| IPC and transport requirements | 3, 4, 7, 8 | Phase 3 defines protocol; Phase 4 implements DBus health; Phase 7/8 add typed target/presentation messages. |
| Target window contract requirements | 7, 8, 9 | Phase 7 owns identity, geometry, content rects, and stale/ambiguous states; Phase 8 consumes them for attachment; Phase 9 validates real behavior. |
| Overlay behavior requirements | 2, 7, 8, 9 | Phase 2 removes visibility terminology confusion; Phase 7 provides target state; Phase 8 delivers chrome-free/stacking/click-through behavior; Phase 9 validates. |
| Visibility terminology requirements | 2, 6, 9 | Phase 2 renames/migrates; Phase 6 surfaces clear terminology; Phase 9 validates no release confusion. |
| Overlay attachment requirements | 7, 8, 9 | Phase 7 discovers target and geometry; Phase 8 mediates presentation/attachment; Phase 9 validates supported modes. |
| Security and privacy requirements | 3, 4, 6, 9 | Phase 3/4 keep helper narrow/versioned/local; Phase 6 limits diagnostics; Phase 9 closes Q11 privacy/security gate. |
| Validation matrix requirements | 9 | Phase 9 is the Q10 gate and records exact tested environment, pass/fail/deferred outcomes, and release wording. |
| Documentation and support requirements | 5, 6, 9 | Phase 5 owns install/remediation docs; Phase 6 owns diagnostics/debug output; Phase 9 updates wiki/troubleshooting/release notes. |

## Phase Details

### Phase 1: Status Truthfulness And Degraded Fallback
- Implements IQ1.
- Corrects the current inconsistency where GNOME Wayland without a healthy helper can show `Mode: True overlay`.
- Keeps selected backend identity and helper diagnostics visible while changing support classification to `degraded_overlay` when helper state is not `healthy`.
- Preserves `xwayland_compat` as a degraded compatibility fallback/override, not a true-overlay claim.
- Risks: existing tests may encode the current optimistic classification; wording changes can surprise users.
- Mitigations: update selector/status tests first, keep fallback reason/helper state visible, and keep user-facing warnings actionable.

#### Phase 1 Implementation Notes
- Touch points to inspect before coding: backend selector/status rules, backend status contracts/formatting, status consumers in preferences/log/debug-overlay surfaces, and existing selector/status/consumer tests.
- Expected unchanged behavior: non-GNOME backend selection, selected backend identity (`native_wayland` / `gnome_shell_wayland`), helper diagnostic fields, `fallback_reason=missing_helper`, manual override handling, and `xwayland_compat` availability as degraded compatibility.
- Out of scope for this phase: GNOME Shell extension files, installer lifecycle, DBus helper implementation, target discovery, presentation/attachment work, and the `force_render` rename.
- Test type choice: unit tests for selector/status classification and pure formatting logic; harness tests only if `load.py`, EDMC preferences wiring, or plugin/client status bridge wiring is touched.
- Tests to run after coding: targeted backend selector/status/consumer tests, plus any touched preferences/status bridge harness tests.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Update backend selector/status rules so GNOME Wayland with missing/unhealthy helper reports `degraded_overlay` | Completed |
| 1.2 | Preserve helper diagnostics: helper kind, required/unavailable state, `fallback_reason=missing_helper`, and selected backend identity | Completed |
| 1.3 | Update preferences/status/log/debug-overlay wording tests so no surface says `true_overlay` while helper is unhealthy | Completed |
| 1.4 | Add regression tests for manual override and `xwayland_compat` degraded fallback behavior | Completed |

#### Phase 1 Execution Notes
- Selector now classifies GNOME Wayland without the required GNOME Shell extension as `degraded_overlay` while preserving `selected_backend=native_wayland / gnome_shell_wayland`, `fallback_from=compositor_helper / gnome_shell_wayland`, and `fallback_reason=missing_helper`.
- Status/report formatting defensively downgrades stale or plugin-provided GNOME Wayland payloads when `fallback_reason=missing_helper` or the required `gnome_shell_extension` helper is unavailable.
- `xwayland_compat` remains degraded compatibility. Existing explicit override behavior is preserved: when a manual override changes from a native Wayland auto backend to `xwayland_compat`, fallback reason is `manual_override`; when the manual override already matches the selected XWayland path, no extra fallback reason is added.
- Added/updated coverage for selector/status, backend consumers, platform context, control-surface log text, debug overlay backend text, plugin config payload, and preferences backend warning text.

#### Phase 1 Tests Run
- `python3 -m py_compile overlay_client/backend/selector.py overlay_client/backend/status.py` -> passed.
- `python3 -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py tests/test_overlay_config_payload.py -q` -> passed, `28 passed`.
- `python3 -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_platform_probe.py overlay_client/tests/test_platform_context.py overlay_client/tests/test_control_surface_platform_context.py overlay_client/tests/test_debug_overlay_view.py tests/test_overlay_config_payload.py tests/test_preferences_panel_controller_tab.py -q` -> passed, `89 passed`.
- `python3 -m pytest tests/test_preferences_panel_controller_tab.py -q` -> passed, `17 passed`.
- `python3 -m pytest tests/test_harness_backend_selection_wiring.py tests/test_harness_backend_status_roundtrip.py tests/test_harness_backend_override_roundtrip.py -q -rs` -> skipped locally, `6 skipped`; missing dev dependency `semantic_version`.
- `git diff --check` -> passed.
- `make check` -> passed; ruff and mypy passed, full pytest reported `843 passed, 21 skipped`.

#### Phase 1 Exit Criteria
- GNOME Wayland without healthy helper never reports user-facing `Mode: True overlay`.
- Missing/unhealthy helper state remains visible in preferences, logs, debug overlay, and diagnostics.
- `xwayland_compat` remains available as degraded compatibility, not true overlay.
- Unit/harness tests cover selector/status and status consumers touched by this phase.

### Phase 2: Visibility Terminology Rename
- Implements IQ3 and R-VN requirements.
- Renames misleading `force_render` terminology to `keep_overlay_visible` before helper behavior depends on it.
- Keeps behavior unchanged: this is a visibility/focus override, not a payload rendering control.
- Risks: config/controller/client compatibility regressions across process boundaries.
- Mitigations: accept legacy `force_render` during migration, write config/payload tests, and keep logs explicit about visibility semantics.

#### Phase 2 Implementation Notes
- Touch points to inspect before coding: EDMC preferences/config persistence, `overlay_settings.json` shadow/bootstrap settings, plugin-to-client `OverlayConfig` payloads, controller CLI override payloads, overlay client initial/config application, visibility/follow-window code, logs, docs, and all tests that mention `force_render`.
- Expected unchanged behavior: the setting still means "keep overlay visible when Elite Dangerous is not the foreground window"; effective visibility remains preference OR controller runtime override; controller open/close still temporarily enables/disables the runtime override; legacy `force_render` settings and payloads remain accepted.
- Migration/precedence rule: when both `keep_overlay_visible` and legacy `force_render` are present, `keep_overlay_visible` wins. If `keep_overlay_visible` is absent, fall back to `force_render`. New writes and new payloads use `keep_overlay_visible`.
- Out of scope for this phase: GNOME Shell extension files, installer lifecycle, DBus helper health, target discovery, presentation/attachment behavior, and any status/classification changes beyond terminology updates.
- Test type choice: unit tests for pure config/payload/migration parsing; harness tests for `load.py`, preferences persistence, and plugin/controller bridge wiring touched by the rename.
- Tests to run after coding: targeted client config, overlay config payload, plugin bridge, preferences persistence, lifecycle/visibility tests, affected harness backend/controller tests, then `make check`.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add `keep_overlay_visible` config/settings support with fallback read from legacy `force_render` | Completed |
| 2.2 | Update preferences labels, overlay settings JSON handling, controller bridge payloads, and runtime override naming | Completed |
| 2.3 | Update logs/docs/tests to distinguish payload rendering, overlay visibility, and compositor presentation | Completed |
| 2.4 | Add migration/compatibility tests for old `force_render` inputs and new `keep_overlay_visible` outputs | Completed |

#### Phase 2 Execution Notes
- EDMC preferences now persist `edmc_modern_overlay.keep_overlay_visible` and write `keep_overlay_visible` to `overlay_settings.json`; legacy `force_render` config/shadow values are accepted on read.
- OverlayConfig and controller CLI payloads now emit `keep_overlay_visible`; legacy `force_render_override` and `force_render` CLI payloads remain accepted for migration.
- Overlay client/bootstrap/config application, follow-window visibility logic, controller bridge naming, logs, FAQ, and compliance docs now use keep-overlay-visible terminology.
- Compatibility aliases remain in code for existing tests/extensions that directly call old Python names, but new writes and new payloads use `keep_overlay_visible`.

#### Phase 2 Tests Run
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_client_config.py tests/test_preferences_persistence.py tests/test_overlay_config_payload.py overlay_controller/tests/test_plugin_bridge.py overlay_controller/tests/test_app_context.py tests/test_harness_cli_ingestion.py tests/test_lifecycle_tracking.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_exception_scoping.py overlay_client/tests/test_follow_helpers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_window_controller.py tests/test_overlay_controller_platform.py -q` -> initially failed, `68 passed, 3 skipped, 2 failed`; harness fixture still inherited the repo-local preference value, then was pinned to `keep_overlay_visible = false` for override semantics.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_client_config.py tests/test_preferences_persistence.py tests/test_overlay_config_payload.py overlay_controller/tests/test_plugin_bridge.py overlay_controller/tests/test_app_context.py tests/test_harness_cli_ingestion.py tests/test_lifecycle_tracking.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_exception_scoping.py overlay_client/tests/test_follow_helpers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_window_controller.py tests/test_overlay_controller_platform.py -q` -> passed, `70 passed, 3 skipped`.
- `overlay_client/.venv/bin/python -m pytest tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_override_roundtrip.py tests/test_harness_backend_status_roundtrip.py tests/test_overlay_controller_platform.py overlay_client/tests/test_developer_helpers.py overlay_client/tests/test_client_config_defaults.py -q` -> collection failed; `overlay_client/tests/test_developer_helpers.py` does not exist.
- `overlay_client/.venv/bin/python -m pytest tests/test_preferences_panel_controller_tab.py tests/test_harness_backend_override_roundtrip.py tests/test_harness_backend_status_roundtrip.py tests/test_overlay_controller_platform.py overlay_client/tests/test_client_config_defaults.py -q` -> passed, `34 passed`.
- `overlay_client/.venv/bin/python -m ruff check .` -> passed.
- `make check` -> passed; ruff and mypy passed, full pytest reported `854 passed, 21 skipped`.

#### Phase 2 Exit Criteria
- New installs/settings use `keep_overlay_visible` terminology.
- Existing `force_render` config/settings/controller payloads remain accepted during migration.
- Tests prove behavior is unchanged and terminology is no longer render-focused.

### Phase 3: Extension Package Skeleton And Protocol Constants
- Implements the first IQ2 helper MVP stage.
- Adds the inspectable source-directory helper package at `helpers/gnome_shell_extension/` without depending on it for production true-overlay claims.
- Establishes metadata, UUID, shell-version entries, helper version, helper protocol, and manifest tests.
- Risks: invalid GNOME metadata, version drift, accidental bundling of unrelated files.
- Mitigations: manifest tests, explicit package allowlist, and protocol constants checked on both helper/client sides.

#### Phase 3 Implementation Notes
- Touch points to inspect before coding: existing helper IPC boundary (`overlay_client/backend/helper_ipc.py`), backend helper kind constants, plugin version source (`version.py`), release/manifest tests, and installer tests that already mention the GNOME helper kind.
- Expected unchanged behavior: GNOME Wayland without a healthy helper remains `degraded_overlay`; the extension package is not installed, enabled, probed, or used for target discovery/presentation in this phase; no `true_overlay` claim changes; `keep_overlay_visible` behavior remains unchanged.
- Package layout: source-directory artifact at `helpers/gnome_shell_extension/` with `metadata.json`, `extension.js`, and a small local JS constants module. The directory name at install time is the fixed UUID `edmc-modern-overlay-helper@edmcmodernoverlay.github.io`.
- Version/protocol ownership: Python backend helper IPC constants are the client source of truth for expected helper kind/protocol/version. The JS helper constants intentionally mirror them; manifest tests fail if UUID, helper kind, protocol, helper version, or shell-version support drifts.
- Shell-version support: `metadata.json` lists explicit GNOME Shell versions `46`, `47`, `48`, `49`, and `50`; newer versions require porting-guide review and smoke validation before metadata is extended.
- Test type choice: unit/manifest tests only for metadata validity, package allowlist, UUID, shell-version range, protocol constants, and helper-version sync. No harness tests are required because this phase does not touch `load.py`, plugin lifecycle hooks, installer lifecycle, runtime helper health, target discovery, or presentation.
- Tests to run after coding: targeted helper package/protocol manifest tests, existing helper IPC boundary tests, then `make check`.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Create `helpers/gnome_shell_extension/` with `metadata.json`, fixed UUID, shell versions `46`-`50`, and source-directory artifact shape | Completed |
| 3.2 | Add helper constants: `HELPER_KIND`, `HELPER_PROTOCOL=1`, and `helper_version` tracking the plugin version | Completed |
| 3.3 | Add client expected protocol/kind constants in the backend/helper contract layer | Completed |
| 3.4 | Add manifest/package tests for UUID, shell versions, helper version source, package contents, and metadata validity | Completed |
| 3.5 | Add protocol-bump checklist/test fixture scaffolding for future helper contract changes | Completed |

#### Phase 3 Execution Notes
- Added source-directory GNOME Shell extension skeleton at `helpers/gnome_shell_extension/` with `metadata.json`, `constants.js`, and `extension.js`.
- Metadata uses fixed UUID `edmc-modern-overlay-helper@edmcmodernoverlay.github.io`, explicit shell versions `46` through `50`, and extension artifact version `1`.
- Added backend helper contract constants for UUID, supported Shell versions, helper kind, helper protocol, and helper version. `HELPER_VERSION` tracks `version.__version__`; `HELPER_PROTOCOL_VERSION` remains as a compatibility alias for the existing helper IPC boundary.
- Extension JS constants intentionally mirror the Python helper contract constants and are checked by tests. The extension currently only stores identity on enable/disable; it does not expose DBus, target discovery, presentation, attachment, click-through, installer lifecycle, or any active runtime dependency.
- Added protocol-bump fixture scaffolding at `tests/fixtures/gnome_shell_helper_contract_v1.json` so future DBus, signal, target geometry, presentation, or validation contract changes require an explicit protocol review.

#### Phase 3 Tests Run
- `overlay_client/.venv/bin/python -m pytest tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_helper_ipc_boundary.py -q` -> passed, `14 passed`.
- `make check` -> passed; ruff and mypy passed, full pytest reported `860 passed, 21 skipped`.
- `git diff --check` -> passed.

#### Phase 3 Exit Criteria
- Extension source directory exists and is inspectable.
- Metadata and package contents are test-covered.
- Helper/client protocol constants are centralized and mismatch behavior is testable.
- No user-visible `true_overlay` behavior depends on the skeleton.

### Phase 4: DBus Health/Version MVP And Status Object
- Implements the second IQ2 helper MVP stage.
- Adds the minimal GNOME Shell extension runtime that owns the session-DBus service and exposes helper health/version/protocol/capabilities.
- Adds client handshake, fail-closed validation, reconnect/stale handling, and the Q8 authoritative status object.
- Risks: DBus lifecycle mismatch, Shell extension load errors, stale helper state, false healthy status.
- Mitigations: narrow DBus interface, protocol/kind validation, timeout/staleness tests, and degraded fallback on every failure.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Implement extension-owned session-DBus service/object with hello/health/version/protocol/capabilities only | Not Started |
| 4.2 | Implement client DBus probe/handshake with helper kind, helper version, helper protocol, and freshness validation | Not Started |
| 4.3 | Add helper remediation states for DBus unreachable, protocol incompatible, inactive/error, and healthy | Not Started |
| 4.4 | Add unit/fake-helper tests for accepted protocol, rejected old/new protocols, stale health, and missing service | Not Started |
| 4.5 | Keep helper MVP behind degraded-by-default behavior and `gnome_helper_experimental=false` as required by IQ6 | Not Started |

#### Phase 4 Exit Criteria
- Live helper can prove it is active/reachable without target discovery.
- Client status reports `healthy` only when DBus, helper kind, version, and protocol validate.
- Protocol mismatch and DBus failure degrade visibly and fail closed.
- Incomplete helper code cannot enable `true_overlay` without Q10 validation.

### Phase 5: Installer Lifecycle And Post-Install Remediation
- Implements Q6, Q7, and IQ4 installer authority decisions.
- Installer detects GNOME Wayland and runs the Q6 helper install/enable flow with explicit user approval.
- Post-install X11-to-GNOME-Wayland remediation is settings/status warning plus rerun-installer instruction, not in-settings install/uninstall buttons.
- Risks: silently changing host configuration, stale Shell discovery, confusing approval/install/active state, unsafe cleanup.
- Mitigations: direct user-local copy, explicit approval before mutations, user-owned global-extension remediation, logout/login requirement, and source-directory-only artifact.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Extend installer to detect GNOME Wayland, prerequisites, installed path, extension discovery, and helper state | Not Started |
| 5.2 | Add user-approved install flow: copy source directory, verify discovery, enable extension, require logout/login, then verify health after login | Not Started |
| 5.3 | Add update flow: disable, clean replace, enable, require logout/login, verify active/version/protocol; no backup kept | Not Started |
| 5.4 | Add disable/uninstall flow that removes only the real helper UUID directory and requires logout/login before final verification | Not Started |
| 5.5 | Add global user-extension disabled remediation that shows instructions but does not run `gsettings set ... false` automatically | Not Started |
| 5.6 | Add Q7 settings/status warning instructing rerun installer when user switches to GNOME Wayland after installing under X11 | Not Started |
| 5.7 | Add installer/script tests for install, update, uninstall, global-disabled, and rerun-installer remediation paths | Not Started |

#### Phase 5 Exit Criteria
- Installer is the only first-pass helper install path and follows Q6 lifecycle rules.
- Helper install/update/uninstall requires explicit user approval and logout/login before final verification.
- Settings/status remediation after X11-to-Wayland switch tells the user to rerun installer under GNOME Wayland.
- Tests prove approval/install/enabled/active/healthy states are distinct.

### Phase 6: Diagnostics, Collectors, And Debug Overlay Metrics
- Implements Q8 across all required surfaces.
- Renders one client-authoritative helper/backend status object into preferences, logs, EDMC/plugin bridge output, `utils/collect_overlay_debug_*`, and live debug overlay metrics.
- Risks: status drift between UI/logs/collectors; debug output leaking too much host data; support output missing host facts when client is down.
- Mitigations: stable field names, compact display text, collector host facts, and Q11 redaction rules.

| Stage | Description | Status |
| --- | --- | --- |
| 6.1 | Define and wire the authoritative helper/backend status object with Q8 stable field names | Not Started |
| 6.2 | Update preferences/settings and user-facing backend summary with compact helper state/action text | Not Started |
| 6.3 | Add stable grep-friendly overlay client and EDMC/plugin bridge log lines | Not Started |
| 6.4 | Update `utils/collect_overlay_debug_linux.sh` to collect status line plus GNOME/session/extension/DBus host facts | Not Started |
| 6.5 | Update `utils/collect_overlay_debug_windows.ps1` to report GNOME helper `not_required` without probing GNOME | Not Started |
| 6.6 | Add live debug overlay metrics lines for backend/classification/helper state and experimental flag | Not Started |
| 6.7 | Add tests or scripted checks for required status fields and redaction-sensitive defaults | Not Started |

#### Phase 6 Exit Criteria
- Preferences, logs, collectors, and debug metrics agree on helper state.
- Debug collectors remain useful if overlay client is stopped or stale.
- No collector/debug surface reports `true_overlay` when helper is unhealthy.
- Default diagnostics avoid broad process/window dumps per Q11.

### Phase 7: Helper-Backed Target Discovery And Coordinate Contract
- Implements the third IQ2 helper MVP stage plus Q4/Q5 contracts.
- Uses the helper as the GNOME Wayland target-discovery source only when active/version-compatible.
- Emits Shell global logical geometry with explicit `frameRect`, `bufferRect`, `contentRect`, and decoration inset semantics.
- Risks: attaching to launcher or wrong window, geometry/content-rect mismatch, stale target tokens, launcher diversity beyond Steam.
- Mitigations: weighted target identity, no broad process substring scans, target ambiguity states, fake-helper fixtures, and live GNOME probes.

| Stage | Description | Status |
| --- | --- | --- |
| 7.1 | Implement helper target enumeration using Shell-visible title/class/app/window state with launcher-only and ambiguity rejection | Not Started |
| 7.2 | Emit target state with stable target token, title/app metadata, focus/visibility/workspace/minimized/fullscreen, timestamp, and sequence | Not Started |
| 7.3 | Emit geometry contract: Shell global logical `frameRect`, `bufferRect`, `contentRect`, decoration insets, monitor/output identity, and scale metadata when available | Not Started |
| 7.4 | Add client adapter for helper target/geometry state without treating Qt `moveEvent` as proof of compositor-visible placement | Not Started |
| 7.5 | Add fake-helper tests for found/not_found/launcher_only/ambiguous/stale target and borderless/windowed geometry cases | Not Started |
| 7.6 | Record degraded behavior when helper cannot derive content rect or required geometry metadata | Not Started |

#### Phase 7 Exit Criteria
- Helper can identify the real Elite Dangerous client and reject launcher-only/ambiguous states.
- Client consumes helper target/geometry state through a typed adapter and degrades on stale/missing/invalid state.
- Content/client rect alignment is explicit and test-covered for windowed and borderless fixtures.

### Phase 8: Shell-Mediated Presentation And Attachment
- Implements the fourth IQ2 helper MVP stage and the core Q1 behavior.
- Keeps the PyQt renderer first, while Shell-side mediation provides enough presentation/attachment control for true-overlay requirements.
- Escalates rendering into the extension only if validation proves PyQt cannot satisfy chrome-free, stacking, click-through, and visibility requirements.
- Risks: GNOME/Mutter private API drift, click-through/focus loops, titlebar/chrome, stacking demotion, Shell restarts, multi-monitor positioning.
- Mitigations: feature-test Shell APIs, degrade on unsupported APIs, keep rendering out of extension unless forced, and validate windowed/borderless behavior separately.

| Stage | Description | Status |
| --- | --- | --- |
| 8.1 | Prototype Shell-mediated placement/presentation hooks while preserving PyQt payload rendering | Not Started |
| 8.2 | Ensure normal overlay mode is chrome/titlebar-free and standalone mode remains explicitly setting-gated | Not Started |
| 8.3 | Maintain overlay stacking above the game after click-through/focus changes in windowed and borderless modes | Not Started |
| 8.4 | Eliminate foreground/visibility flashing without relying on `keep_overlay_visible` as a workaround | Not Started |
| 8.5 | Handle target minimize, workspace change, monitor move, game exit/relaunch, helper reload, and stale/disconnected helper states | Not Started |
| 8.6 | Add tests for presentation state machines where possible and manual validation notes where GNOME behavior cannot be headless-tested | Not Started |

#### Phase 8 Exit Criteria
- Windowed and borderless presentation requirements pass in fake-helper and real GNOME validation where applicable.
- Overlay remains chrome-free, click-through-capable, and stacked above the game after focus changes.
- Unsupported Shell API or presentation failure degrades visibly and never claims `true_overlay`.
- Rendering remains in PyQt unless a recorded validation failure requires moving specific responsibility into the extension.

### Phase 9: Release Validation, Documentation, And Support Claim Gate
- Implements Q9, Q10, Q11 closeout and validates all earlier phases together.
- Proves helper-active behavior on Ubuntu GNOME Wayland/GNOME Shell 46 first, with exact environment details recorded.
- Updates user docs, troubleshooting, release notes, and privacy/security copy based on evidence.
- Risks: overclaiming GNOME version/distro support, missing multi-monitor/fractional-scaling edge cases, stale test extensions affecting results.
- Mitigations: Q10 validation matrix, IQ7 cleanup preflight, explicit deferrals, and release wording that separates target from validated environments.

| Stage | Description | Status |
| --- | --- | --- |
| 9.1 | Run IQ7 cleanup preflight and record GNOME Shell version, distro/session, monitor layout, scaling, EDMC install mode, helper version, and protocol | Not Started |
| 9.2 | Run Q10 install/lifecycle validation: install, update, disable, uninstall, rerun-installer remediation, logout/login, health/protocol verification | Not Started |
| 9.3 | Run Q10 backend/status validation across preferences, logs, collectors, and debug overlay metrics | Not Started |
| 9.4 | Run Q10 windowed overlay validation: identity, content alignment, move, resize, chrome-free, click-through, stacking | Not Started |
| 9.5 | Run Q10 borderless fullscreen validation: identity, viewport alignment, chrome-free, no flashing, click-through, stacking | Not Started |
| 9.6 | Run Q10 failure/recovery validation for disabled/global-disabled/DBus/protocol/game-not-found/launcher-only/ambiguous states | Not Started |
| 9.7 | Run Q10 privacy/security review and EDMC compliance review for installer/preferences/helper surfaces | Not Started |
| 9.8 | Update docs/wiki/troubleshooting/release notes with support wording, privacy copy, install/remediation instructions, and any deferrals | Not Started |

#### Phase 9 Exit Criteria
- Q10 validation matrix has recorded pass/fail/deferred outcomes.
- GNOME Wayland `true_overlay` claim is allowed only if every required gate passes.
- Any failed/deferred item is reflected in degraded/experimental release wording with exact missing guarantees.
- Docs and diagnostics match shipped behavior.

## Execution Log
- Plan created on 2026-05-09.
- This initial entry is documentation-only. No runtime code, installer code, extension code, or tests were changed.
- Added Q1 evidence from GNOME Wayland testing on 2026-05-09: helper missing/inactive state, current `true_overlay` inconsistency, payload rendering success, overlay visible/hidden flashing loop, and corrected `force_render` semantics.
- Added `force_render` rename requirements on 2026-05-09 so future work treats it as an overlay visibility setting/override, not a payload rendering control.
- Added Q1 keep-visible test result on 2026-05-09: enabling "Keep overlay visible when Elite Dangerous is not the foreground window" stops the flashing loop, pointing the next investigation at foreground/focus state and show/raise side effects.
- Added Q1 movement test result on 2026-05-09: clicks pass through with keep-visible enabled, but the overlay does not remain attached when the mock target moves, making helper-provided geometry/follow state the next priority.
- Added Q1 follow-log result on 2026-05-09: current tracker detects mock target movement and Qt reports matching overlay moves, leaving follow cadence, compositor-visible position, and coordinate conversion as the remaining movement questions.
- Refined Q1 follow-log result on 2026-05-09: the overlay never catches up after target movement stops, ruling out simple polling lag and pointing at visible placement divergence or coordinate-space mismatch.
- Corrected Q1 movement evidence on 2026-05-09: the observed non-moving overlay was against the actual game window, not the mock target, strengthening the presentation/placement concern.
- Added Q1 compositor-move evidence on 2026-05-09: desktop keyboard window-move commands can move the visible overlay without Qt move logs or `wmctrl` geometry changes, showing app-side and X11-reported geometry are not authoritative on GNOME Wayland.
- Added Q1 restart-placement evidence on 2026-05-09: with the actual game centered in windowed mode, restarting EDMC placed the overlay at the upper-left screen corner instead of on the game, ruling out a dynamic-reposition-only failure.
- Added Q1 borderless-fullscreen evidence on 2026-05-09: overlay placement looks correct with keep-visible enabled, but the title bar and standalone-app behavior violate true-overlay presentation requirements.
- Added overlay-behavior requirements on 2026-05-09: normal overlay mode must be chrome/titlebar-free, and standalone-app behavior must be gated by an explicit setting.
- Added exclusive-fullscreen scope decision on 2026-05-09: exclusive fullscreen is unsupported and will not drive helper requirements; users must run windowed or borderless fullscreen mode for overlay support.
- Added standalone/titlebar source evidence on 2026-05-09: config has `standalone_mode=false` and no manual backend override, but GNOME Wayland still presents titlebar/standalone behavior in borderless fullscreen, so this is not an explicit standalone-mode configuration issue.
- Added borderless-fullscreen focus evidence on 2026-05-09: with keep-visible disabled, the overlay flashes on a roughly 0.5 second visible/hidden cadence at full-screen geometry, so borderless fullscreen still needs helper-authoritative focus/visibility state.
- Added borderless-fullscreen restart evidence on 2026-05-09: initial overlay placement is correct after EDMC restart, but titlebar chrome shifts the visible overlay content downward, making chrome suppression an alignment requirement.
- Added windowed resize and stacking evidence on 2026-05-09: dynamic resize updates are visible without EDMC restart, but clicking through demotes the overlay behind the game in both windowed and borderless modes, so stacking/presentation is a helper requirement.
- Closed Q1 on 2026-05-09: the helper must provide Shell-mediated attachment/presentation, including focus/visibility, placement, stacking, and chrome-free presentation; geometry-only is insufficient. PyQt remains the first renderer candidate until a helper prototype proves otherwise.
- Opened Q2 on 2026-05-09 with transport tests: evaluate session DBus first and keep Unix socket under `$XDG_RUNTIME_DIR` as the fallback candidate.
- Recorded Q2 transport probe evidence on 2026-05-09: GJS/DBus tooling is present, the session bus uses `/run/user/1000/bus`, and GNOME Shell services are visible on the user bus.
- Added user-facing prerequisite requirements on 2026-05-09: chosen helper transport requirements must be surfaced in installer, preferences, diagnostics, troubleshooting, and degraded/remediation states.
- Recorded Q2 standalone DBus smoke evidence on 2026-05-09: standalone GJS can own a session bus name, answer a method call, and emit heartbeat signals.
- Recorded T-Q2-4 discovery evidence on 2026-05-09: GNOME Shell did not immediately discover a manually copied user extension, so manual install/remediation must account for logout/login or another supported rescan/install path.
- Recorded T-Q2-4 enablement blocker on 2026-05-09: after logout/login the smoke extension is discovered but remains `Enabled: No` / `State: INITIALIZED` after enable attempts, so extension enablement diagnostics are required before DBus-in-extension can be evaluated.
- Explained T-Q2-4 enablement blocker on 2026-05-09: `disable-user-extensions=true` globally disables GNOME user extensions even when the extension UUID is present in `enabled-extensions`; added requirements to detect and remediate this state.
- Recorded T-Q2-4 pass on 2026-05-09: after globally enabling user extensions, the smoke extension became active and answered a session-DBus `Ping` call, making session DBus the leading primary transport candidate.
- Closed Q2 on 2026-05-09: session DBus is the primary helper IPC transport; Unix socket remains a reserved fallback only if DBus later fails during lifecycle, reconnect, or security review.
- Cleaned up the temporary DBus smoke-test extension on 2026-05-09 and restored `org.gnome.shell disable-user-extensions=true`, matching the pre-test global user-extension setting.
- Closed Q3 on 2026-05-09: the GNOME Shell extension owns the session-DBus service/object lifecycle; the overlay client registers one active session, validates events, reconnects after helper loss/reload, and degrades when helper state is absent or stale.
- Opened Q4 on 2026-05-09: existing trackers use title matching as the compatibility baseline, but helper-backed GNOME support needs a weighted target identity contract using real Wine/Proton metadata collected from windowed and borderless modes.
- Added Q4 metadata evidence on 2026-05-09: GitHub issue #82 rules out loose process substring matching, real Steam/Proton window metadata shows launcher and game share `steam_app_359320` class while title distinguishes the actual `Elite - Dangerous (CLIENT)` game window, and windowed/borderless modes keep the same identity fields.
- Closed Q4 on 2026-05-09: Shell extension metadata confirms the helper can see title, Steam class, PID, normal window type, geometry, monitor, workspace visibility, minimized state, and focus; target identity requires the Elite Dangerous client title with Steam class and normal visible window state as supporting evidence, while launcher-only and ambiguous states must not attach.
- Corrected Q4 on 2026-05-09: Steam app class `steam_app_359320` is launcher-specific supporting evidence, not a universal requirement, because Elite can also be launched through Epic or other launch paths.
- Opened Q5 on 2026-05-09: candidate coordinate contract uses GNOME Shell global logical coordinates with both `frameRect` and `bufferRect`; borderless fullscreen Shell evidence shows both rects at `0,0 3440x1440`, while client-log comparison remains incomplete because no recent geometry lines were present in the last 120 log lines.
- Added Q5 windowed/monitor evidence on 2026-05-09: Shell reports global logical coordinates across two 3440x1440 monitors, with Elite windowed `frameRect` and `bufferRect` diverging, so Q5 must explicitly choose the content-alignment rectangle.
- Recorded Q5 synchronized-log blocker on 2026-05-09: overlay client logs were stale and no matching overlay/EDMC process was visible, so fresh EDMC/overlay runtime logs are needed before comparing Shell and client geometry for the same moment.
- Added Q5 synchronized comparison evidence on 2026-05-09: Shell windowed `frameRect` and client tracker geometry share X/width, but the client target is 37 px lower and 37 px shorter, indicating the current tracker is closer to game content/client area while Shell `frameRect` includes titlebar/decorated frame; Q5 now requires a named content rect or decoration inset contract.
- Closed Q5 on 2026-05-09: `_NET_FRAME_EXTENTS=0,0,37,0` plus `xwininfo` confirmed the current tracker target is the game client/content rect, while Shell `frameRect` includes the 37 px titlebar; helper geometry must use Shell global logical coordinates and carry explicit `contentRect`/decoration-inset metadata for overlay alignment.
- Opened Q6 on 2026-05-09 and recorded initial lifecycle decisions: default helper installation is user-local under `~/.local/share/gnome-shell/extensions/<helper-uuid>/`, and the helper should ship/install as a small source directory for user inspection.
- Recorded Q6 helper UUID decision on 2026-05-09: the fixed GNOME Shell extension UUID is `edmc-modern-overlay-helper@edmcmodernoverlay.github.io`, making the default user-local install path `~/.local/share/gnome-shell/extensions/edmc-modern-overlay-helper@edmcmodernoverlay.github.io/`.
- Recorded Q6 package path decision on 2026-05-09: the source-directory helper package lives at `helpers/gnome_shell_extension/` and installs to the fixed user-local GNOME Shell extension directory.
- Recorded Q6 install-method decision on 2026-05-09: install/update copies the source directory directly into the user-local GNOME Shell extension path; `gnome-extensions info/enable/disable` and helper DBus health checks provide lifecycle verification.
- Recorded Q6 install/enable sequence on 2026-05-09: detect GNOME Wayland, check prerequisites, ask for user approval, copy files, verify discovery, check global user-extension setting, enable extension, require logout/login, then verify `ACTIVE` and DBus health/protocol compatibility.
- Recorded Q6 release artifact decision on 2026-05-09: ship the GNOME helper as source-directory-only under `helpers/gnome_shell_extension/`; do not require a zip artifact for install/runtime behavior.
- Recorded Q6 approval/restart decision on 2026-05-09: every helper install/config-changing action requires explicit user approval, and the supported lifecycle requires logout/login before final `ACTIVE`/DBus-health or final-removed verification.
- Recorded Q6 update decision on 2026-05-09: with user approval, update by disabling the helper, clean-replacing the installed source directory from `helpers/gnome_shell_extension/`, enabling the helper, requiring logout/login, then verifying active/version/protocol; no backup/rollback copy is kept.
- Consolidated Q6 workflow summary on 2026-05-09 so install/enable, update, disable, and uninstall workflows remain recoverable if conversation context is lost.
- Closed Q6 on 2026-05-09: accepted platform-neutral remediation state model and user-facing action table for `not_required`, prerequisite, install/discovery, global-disable, disabled, restart-required, inactive/error, DBus, protocol, and healthy states.
- Closed Q7 on 2026-05-09: the installer is the helper-install path when run under GNOME Wayland; post-install X11-to-GNOME-Wayland remediation is a settings/status warning that tells the user to rerun the installer while logged into GNOME Wayland so the installer detects GNOME Wayland and installs/enables the helper with approval. In-settings install/uninstall buttons are deferred.
- Opened Q8 on 2026-05-09: helper/backend state must appear consistently in preferences/settings, logs, EDMC/plugin status bridge output, `utils/collect_overlay_debug_*` scripts, and the live "Show debug overlay metrics" overlay.
- Closed Q8 on 2026-05-09: accepted compact display text, stable helper/backend status field names, and collector-source rules that prefer overlay-client authoritative status while also collecting direct Linux host facts.
- Opened Q9 on 2026-05-09: support target is GNOME Shell 46 and newer, with GNOME Shell 46 as the initial observed baseline; exact first distro/session validation target remains open.
- Added Q9 GNOME 46-50 compatibility notes on 2026-05-09: no large post-46 extension structure break is expected, but implementation must feature-test Shell/Mutter APIs, avoid `Meta.Rectangle`, use plain DBus-safe geometry payloads, and keep rendering out of the extension unless Q1 validation forces it.
- Closed Q9 on 2026-05-09: first validation target is Ubuntu GNOME Wayland; initial `metadata.json` shell versions are `46`, `47`, `48`, `49`, and `50`; newer versions require porting-guide review plus smoke validation; release wording separates GNOME Shell 46+ target from exact validated environments.
- Closed Q10 on 2026-05-09: first release validation matrix covers Ubuntu GNOME Wayland/GNOME Shell 46, install lifecycle, backend/status truthfulness, windowed and borderless overlay behavior, failure/recovery states, and privacy/security checks; failed/deferred items block `true_overlay` claims unless explicitly downgraded in release wording.
- Closed Q11 on 2026-05-09: accepted helper privacy/security copy, allowed metadata set, default log/diagnostic redaction rules, debug-only escalation rule, and local fail-closed DBus security boundary. Q1-Q11 requirements questions are complete.
- Added follow-up implementation questions on 2026-05-09: first implementation slice, helper MVP boundary, `force_render` rename timing, installer authority for global user-extension config, helper/protocol versioning, incomplete-helper merge policy, and temporary research-extension cleanup.
- Closed IQ1 on 2026-05-09: first implementation slice is status truthfulness, so GNOME Wayland missing/unhealthy helper reports `degraded_overlay` instead of `true_overlay` before extension/installer work begins.
- Closed IQ2 on 2026-05-09: helper MVP is staged as manifest/package, DBus health/version, target discovery, and presentation/stacking.
- Closed IQ3 on 2026-05-09: `force_render` will be renamed to `keep_overlay_visible` before helper behavior depends on it, with backward-compatible migration for existing config/settings/controller payloads and related docs/logs/tests.
- Closed IQ4 on 2026-05-09: globally disabled GNOME user extensions are detected, but the installer does not change the setting itself; with explicit user permission, it shows remediation instructions for the user to run manually, then requires logout/login and recheck.
- Closed IQ5 on 2026-05-10: helper version tracks the plugin version exactly; helper protocol is a separate integer contract version starting at `1`; client expected protocol starts at `1`; protocol mismatch reports `protocol_incompatible`; tests/checklist enforce explicit protocol-bump decisions for contract changes.
- Closed IQ6 on 2026-05-10: incomplete helper code may merge incrementally only behind degraded-by-default production behavior and/or `gnome_helper_experimental=false` by default; the flag is stored in overlay settings, appears in diagnostics, and never permits `true_overlay` without Q10 validation.
- Closed IQ7 on 2026-05-10: added cleanup instructions for temporary research extensions and validation preflight requiring research UUIDs to be absent before production helper validation.
- Reworked implementation phases on 2026-05-10: expanded from five broad phases to nine requirement-covered phases spanning status truthfulness, visibility rename, extension packaging, DBus health, installer lifecycle, diagnostics, target discovery, presentation/attachment, and release validation. Added a phase coverage matrix against all requirement groups.
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

### Phase 5 Execution Summary
- Not started.

### Tests Run For Phase 5
- None yet.

### Phase 6 Execution Summary
- Not started.

### Tests Run For Phase 6
- None yet.

### Phase 7 Execution Summary
- Not started.

### Tests Run For Phase 7
- None yet.

### Phase 8 Execution Summary
- Not started.

### Tests Run For Phase 8
- None yet.

### Phase 9 Execution Summary
- Not started.

### Tests Run For Phase 9
- None yet.
