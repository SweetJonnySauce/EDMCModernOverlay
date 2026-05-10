## Goal: Ship a real GNOME Shell extension helper path for `gnome_shell_wayland`

This plan is separate from the `fix219_*` backend-cleanup plans.
`fix219` preserved the helper-backed GNOME architecture and status model, but it did not add a real GNOME helper implementation.
The purpose of this plan is to define what would be required to ship the GNOME helper as a concrete product surface: what kind of code it is, where it lives, how it is installed/enabled/disabled/uninstalled, how the overlay client talks to it, and how the support/validation story should work.
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
- Use **unit tests** for pure selector/probe/IPC/packaging helpers and payload validation.
- Use **harness tests** when plugin prefs, client startup, socket status, or override/lifecycle wiring changes.
- Use **manual GNOME-session validation** for extension install/enable/disable/uninstall flows and live Mutter/GNOME Shell behavior, because that part cannot be proven headlessly in the current repo.

## Testing Strategy Matrix (Required)

| Refactor Slice | Existing Behavior/Invariants To Preserve | Test Type | Why This Level | Test File(s) | Command |
| --- | --- | --- | --- | --- | --- |
| Helper IPC contract and message validation | Session token, protocol version, allowed-event validation, and endpoint safety remain fail-closed | Unit | This is pure validation logic and should be proven without GNOME Shell | `overlay_client/tests/test_helper_ipc_boundary.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py -q` |
| GNOME selector/probe/status integration | `gnome_shell_wayland` keeps explicit identity, reports missing-helper or `incompatible_helper` state honestly, and switches to helper-backed family only when the extension is present and reachable | Unit | The selector/probe/status model is pure and should be stable before live integration | `overlay_client/tests/test_backend_selector.py`, `overlay_client/tests/test_backend_status.py`, `overlay_client/tests/test_platform_probe.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_platform_probe.py -q` |
| Client/runtime wiring for helper-backed GNOME path | Bundle resolution, backend status round-trip, prefs notices, and fallback when the helper is absent remain correct | Mixed (Unit + Harness) | Runtime surfaces cross backend, client config, and plugin prefs/status wiring | `overlay_client/tests/test_backend_consumers.py`, `tests/test_harness_backend_status_roundtrip.py`, `tests/test_preferences_panel_controller_tab.py` | `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py tests/test_harness_backend_status_roundtrip.py tests/test_preferences_panel_controller_tab.py -q` |
| Installer metadata and explicit approval flow | GNOME helper stays manual/approved-only, and install guidance does not imply silent auto-enable | Mixed (Unit + Harness) | Installer metadata is testable, but the approval story also touches runtime-facing docs/status | `tests/test_install_linux.py` | `source .venv/bin/activate && python -m pytest tests/test_install_linux.py -q` |
| Live GNOME extension operations | Install, enable, disable, upgrade, and uninstall produce the expected overlay fallback/status behavior in a real GNOME session | Manual GNOME-session validation | GNOME Shell extension behavior cannot be relied on from headless tests alone | Manual checklist in this plan | Record exact session, GNOME Shell version, and observed status output in the `Execution Log` |

## Test Acceptance Gates (Required)
- [ ] Unit tests added/updated for pure selector/probe/IPC logic.
- [ ] Harness tests added/updated for prefs/client wiring surfaces.
- [ ] Manual GNOME-session install/enable/disable/uninstall validation recorded.
- [ ] Commands executed and outcomes recorded.
- [ ] Skips/failures documented with reason and follow-up action.

## Scope
- In scope:
- define the GNOME helper as a real GNOME Shell extension rather than a generic client-side Wayland workaround
- choose the extension repo layout, UUID strategy, packaging shape, and local install target
- define explicit install, enable, disable, upgrade, and uninstall behavior
- implement client-owned helper IPC runtime wiring for GNOME over session D-Bus
- add real helper availability and reachability probing for GNOME
- add a GNOME-specific discovery/runtime path that can consume helper events for follow/tracking plus full click-through and stacking behavior
- keep the fallback path explicit when the helper is missing, disabled, incompatible, or unreachable
- document user approval and support expectations for the helper-backed path
- Out of scope:
- broadening `fix219` itself beyond preserving the helper-backed architecture slot
- silently installing, enabling, updating, or removing GNOME Shell extensions on behalf of the user
- claiming GNOME helper support parity before live GNOME-session validation is recorded
- shipping distro-specific system packages in this first helper plan

## Operational Model
- Code type:
  - The helper is a GNOME Shell extension written in GJS JavaScript, with `metadata.json` plus `extension.js` as the minimum extension payload.
  - Optional extension-side files may include `prefs.js`, `stylesheet.css`, and `schemas/*.gschema.xml`.
- Default install target:
  - Per-user install to `~/.local/share/gnome-shell/extensions/<uuid>/`.
  - System-wide install to `/usr/share/gnome-shell/extensions/<uuid>/` is allowed later, but is not the default target for the first shipped path.
- Enablement model:
  - Manual user action only. The product may guide or warn, but it must not silently install or auto-enable the GNOME extension.
- Runtime usage:
  - The extension exposes a narrow helper service over session D-Bus.
  - The overlay client probes whether the helper is present and reachable, performs a version/token handshake, then consumes the minimum event/control surface needed for the first milestone: active-window and geometry changes plus the helper-backed behaviors required for full click-through and stacking support on GNOME.
  - The first shipped helper scope is Elite Dangerous window targeting only; it is not a generic desktop/window helper.
- Disable/uninstall model:
  - Disabling the extension must immediately return the overlay to the missing-helper/fallback state on the next status refresh or restart.
  - Uninstalling a per-user extension means disabling it first, then removing the installed extension directory.
  - Uninstalling a system-wide extension is a package-manager operation and is not handled by plugin runtime code.

## Current Touch Points
- Existing code:
- `overlay_client/backend/bundles/gnome_shell_wayland.py` (currently a stub bundle with no tracker/helper implementation)
- `overlay_client/backend/helper_ipc.py` (helper boundary contract and validation)
- `overlay_client/backend/selector.py` (helper-aware GNOME backend selection)
- `overlay_client/backend/probe.py` (platform probe model; currently lacks GNOME-specific helper discovery)
- `overlay_client/backend/status.py` (user-facing helper status/fallback reporting)
- `scripts/install_matrix.json` (manual-helper metadata for GNOME)
- Existing tests:
- `overlay_client/tests/test_helper_ipc_boundary.py`
- `overlay_client/tests/test_backend_selector.py`
- `overlay_client/tests/test_backend_status.py`
- `overlay_client/tests/test_platform_probe.py`
- `tests/test_install_linux.py`
- Planned new code surfaces:
- `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/metadata.json`
- `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/extension.js`
- `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/README.md`
- `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/schemas/*.gschema.xml` (if extension settings or persistent approvals are needed)
- `overlay_client/backend/gnome_helper_runtime.py` (client-side D-Bus connection, handshake, and event consumption)
- `overlay_client/backend/bundles/gnome_shell_wayland.py` (upgrade from stub bundle to helper-backed bundle)
- `overlay_client/backend/probe_gnome.py` or equivalent helper-discovery seam (exact file name to be decided when implementation begins)
- Possible support scripts/docs:
- `scripts/install_gnome_shell_extension.sh` or equivalent packaging helper
- helper install/uninstall instructions in repo docs or wiki

## Open Questions
- None currently.

## Decisions (Locked)
- The GNOME helper is a separate GNOME Shell extension, not Python code inside the EDMC plugin.
- The first supported install target is per-user: `~/.local/share/gnome-shell/extensions/<uuid>/`.
- The first supported GNOME Shell range for v1 is `46`, `47`, `48`, and `49`; widen support only after recorded validation.
- The extension must remain explicitly user-installed and user-enabled; no silent install/enable/update path is allowed.
- The first supported operator workflow is manual copy/install plus manual enable; a repo-managed install helper script is deferred.
- The client/helper transport for GNOME uses session D-Bus, consistent with the existing helper-boundary tests.
- The client must fail closed when helper protocol version, session token, or event type is invalid.
- The first milestone is not tracking-only; it targets full GNOME helper-backed click-through and stacking behavior as well.
- The first milestone targets Elite Dangerous window detection only; generic tracked-window support is deferred.
- No extension-side settings UI (`prefs.js`) is planned for v1 unless implementation proves a real need.
- Documentation should include both CLI (`gnome-extensions ...`) and GNOME Extensions app GUI paths for enable/disable operations.
- Helper availability should be detected live when the D-Bus service appears/disappears cleanly; if GNOME-session reality makes that unreliable, restart-required fallback is acceptable for v1.
- A helper that is installed but unreachable, protocol-incompatible, or otherwise fails handshake should surface an explicit `incompatible_helper` reason rather than collapsing into `missing_helper`.
- `gnome_shell_wayland` must not be classified as `true_overlay` until real GNOME-session validation evidence is recorded, even if the helper is present and the handshake succeeds in principle.
- The current helper-backed GNOME path does not count as `true_overlay` evidence in its declared supported play mode unless live validation proves the overlay remains above the active game while the game itself keeps focus.
- Current live blocker evidence comes from borderless/windowed-sized testing, not confirmed exclusive fullscreen. Support policy must therefore treat the remaining issue as an active-game stacking/presentation problem in a supported play mode, not as a fullscreen-only limitation.
- Fullscreen is not a hard requirement for any backend. Windowed and borderless/windowed support are acceptable supported outcomes when compositor or platform limits prevent a stable fullscreen overlay path.
- If GNOME cannot keep the current external Qt overlay above the active game in the declared supported mode, the project will pursue a deeper helper-owned presentation model rather than stopping at a narrowed-support fallback.
- Prototype work is allowed in Phase `5.2` if that is the fastest way to answer the presentation-control question, but any prototype chosen for the product must be followed by hardening and a full implementation stage before it counts as shipped behavior.
- Proposed extension UUID: `edmc-modern-overlay@edmc.local`.
- If later GNOME extension publication/review requires a stronger namespace claim, revisit the UUID before external distribution; for local/per-user deployment this UUID is acceptable.
- Removing or disabling the extension must cleanly return the product to the existing missing-helper/fallback behavior rather than leaving a half-active GNOME backend.

## Per-Iteration Test Plan
- **Env setup (once per machine):** `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- **Headless quick pass (default for each step):** `source .venv/bin/activate && python -m pytest`
- **Targeted helper-boundary tests:** `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_platform_probe.py -q`
- **Installer approval tests:** `source .venv/bin/activate && python -m pytest tests/test_install_linux.py -q`
- **Wiring checks:** `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py tests/test_harness_backend_status_roundtrip.py tests/test_preferences_panel_controller_tab.py -q`
- **Milestone checks:** `make check` and `make test`
- **Manual GNOME-session checks:** record GNOME Shell version, distro/session details, helper install path, enable/disable method, and resulting backend status/fallback output after each milestone

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Lock the product/operations contract for the GNOME extension helper | Completed |
| 2 | Add the extension payload and helper-side D-Bus service | Completed |
| 3 | Add client-side GNOME helper discovery, handshake, runtime consumption, and foreground-stability fixes | Completed |
| 4 | Integrate install/enable/disable/uninstall support surfaces and status reporting | Completed |
| 5 | Add a GNOME-controlled presentation/active-game stacking path, or explicitly narrow support if GNOME cannot provide one | In Progress |
| 6 | Record live GNOME validation, compatibility limits, and release-readiness evidence | In Progress |

## Phase Details

### Phase 1: Requirements And Product Contract
- Define the shipping model before implementation starts.
- Choose the UUID, repo layout, minimum supported GNOME Shell range, and first supported install target.
- Lock the support policy for enable, disable, uninstall, and fallback.
- Risks: building code before the operational model is explicit will create churn in packaging, docs, and support output.
- Mitigations: treat install/uninstall and approval behavior as first-class requirements, not post-implementation cleanup.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Confirm the proposed extension UUID, repo layout, and minimum file set (`metadata.json`, `extension.js`, optional prefs/schema files) | Completed |
| 1.2 | Define the first supported per-user manual copy/enable, disable, uninstall, and upgrade rules | Completed |
| 1.3 | Define helper approval/status language, including explicit `incompatible_helper` handling and the bar for `true_overlay` signoff | Completed |

#### Stage 1.1 Detailed Plan
- Objective:
  - Lock the exact helper UUID and repo layout before creating any extension payload files.
  - Keep runtime behavior unchanged; this stage is requirements-only and must not add live helper wiring.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
- Planned repository layout to confirm in this stage:
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/metadata.json`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/extension.js`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/README.md`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/schemas/` only if later stages prove a settings/schema need
- Minimum file-set decisions to confirm in this stage:
  - required in the first payload: `metadata.json`, `extension.js`, `README.md`
  - deferred unless needed: `prefs.js`, `stylesheet.css`, `schemas/*.gschema.xml`
- Planned tests for this stage:
  - None. This stage is doc-only and does not change runtime or testable code paths.
- Unchanged behavior contract:
  - no selector/status/runtime behavior changes
  - no installer behavior changes
  - no helper files created yet

#### Stage 1.3 Detailed Plan
- Objective:
  - Lock the future helper approval and backend-status vocabulary before any runtime helper wiring lands.
  - Keep runtime and installer behavior unchanged; this stage defines wording and evidence thresholds only.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - reference-only code surfaces whose later implementation must follow this wording:
    - `overlay_client/backend/contracts.py`
    - `overlay_client/backend/status.py`
    - `overlay_client/backend/selector.py`
    - `tests/test_install_linux.py`
    - `overlay_client/tests/test_backend_status.py`
    - `overlay_client/tests/test_backend_selector.py`
- Locked status-language rules for later stages:
  - `missing_helper` means the GNOME extension is absent, disabled, not user-approved for use, or otherwise not available as a helper-backed path
  - `incompatible_helper` means a GNOME helper is present but unusable because handshake, protocol version, UUID/identity, D-Bus reachability, or message validation failed
  - helper approval wording should distinguish:
    - helper approved for use
    - helper not approved yet
    - helper missing/disabled
    - helper present but incompatible
  - `true_overlay` for GNOME must require recorded real-session evidence on the supported GNOME Shell versions that the helper-backed path delivers the claimed click-through, stacking, and target-tracking behavior
  - helper presence or clean handshake alone is insufficient to claim `true_overlay`
- Planned tests for this stage:
  - None. This stage is doc-only and does not change runtime or testable code paths.
- Unchanged behavior contract:
  - no selector/status/runtime behavior changes
  - no installer behavior changes
  - no helper files created yet

#### Stage 1.2 Detailed Plan
- Objective:
  - Lock the supported per-user GNOME helper operating workflow before creating any extension payload files.
  - Keep runtime and installer behavior unchanged; this stage defines workflow rules only.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
- Supported v1 per-user install workflow:
  - destination path: `~/.local/share/gnome-shell/extensions/edmc-modern-overlay@edmc.local/`
  - create the destination directory if needed
  - manually copy the extension payload into that directory
  - first supported enable methods:
    - CLI: `gnome-extensions enable edmc-modern-overlay@edmc.local`
    - GUI: enable the extension in the GNOME Extensions app
- Supported v1 disable workflow:
  - first supported disable methods:
    - CLI: `gnome-extensions disable edmc-modern-overlay@edmc.local`
    - GUI: disable the extension in the GNOME Extensions app
- Supported v1 uninstall workflow:
  - disable the extension first
  - remove `~/.local/share/gnome-shell/extensions/edmc-modern-overlay@edmc.local/`
  - `gnome-extensions uninstall edmc-modern-overlay@edmc.local` is allowed as a convenience when GNOME recognizes the installed extension, but the product-supported uninstall rule for the manual-copy path remains disable-then-remove-directory
- Supported v1 upgrade workflow:
  - disable the extension
  - replace the contents of `~/.local/share/gnome-shell/extensions/edmc-modern-overlay@edmc.local/`
  - re-enable the extension through CLI or GUI
  - if the helper does not reconnect cleanly, restart the Overlay Client; if GNOME Shell itself still presents stale extension code, log out/in before treating the upgrade as successful
- Explicitly unsupported in v1:
  - system-wide install to `/usr/share/gnome-shell/extensions/...`
  - repo-managed install/uninstall scripts
  - silent install, enable, disable, upgrade, or removal
- Planned tests for this stage:
  - None. This stage is doc-only and does not change runtime or testable code paths.
- Unchanged behavior contract:
  - no selector/status/runtime behavior changes
  - no installer behavior changes
  - no helper files created yet

### Phase 2: Extension Payload And Helper Service
- Add the actual GNOME Shell extension payload under a dedicated helper directory.
- Expose a minimal D-Bus service from the extension side for active-window and geometry state.
- Keep the extension-side contract small enough to evolve safely.
- Risks: GNOME Shell API/version churn, leaking too much policy into the extension, or building a protocol that is too broad to secure easily.
- Mitigations: keep the initial protocol event set minimal; require versioned hello + session token handshake.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add extension skeleton files and extension-side README/developer notes | Completed |
| 2.2 | Implement the extension-side D-Bus service and handshake (`hello`, protocol version, session token) | Completed |
| 2.3 | Emit the minimum event set needed for the first tracking milestone, likely active-window and geometry updates | Completed |

#### Stage 2.1 Detailed Plan
- Objective:
  - Add the first GNOME helper payload files to the repo without wiring them into the overlay runtime yet.
  - Keep shipped behavior unchanged by making the extension skeleton inert and no-op.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/metadata.json`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/extension.js`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/README.md`
- Planned file contents for this stage:
  - `metadata.json`
    - UUID `edmc-modern-overlay@edmc.local`
    - name/description/url
    - `shell-version` entries for `46`, `47`, `48`, and `49`
    - no `prefs.js`, stylesheet, schema, or helper protocol claims yet
  - `extension.js`
    - GNOME 46-49 ESModule entrypoint
    - no-op `enable()` / `disable()` implementation with no helper service yet
  - `README.md`
    - purpose of the helper
    - current stage limits
    - pointer to the plan doc and manual install target
- Planned tests for this stage:
  - `python3 -m json.tool helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/metadata.json >/dev/null`
- Unchanged behavior contract:
  - no selector/status/runtime behavior changes
  - no installer behavior changes
  - no helper D-Bus service yet
  - no helper discovery/probe changes yet

#### Stage 2.2 Detailed Plan
- Objective:
  - Implement the helper-side D-Bus service and handshake for the GNOME extension payload.
  - Keep the service surface narrow and aligned with the existing Python helper-boundary contract before any client-side consumption lands.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/extension.js`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/service.js` (new helper-local service module; preferred to keep the entrypoint thin)
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/README.md`
  - reference-only alignment source: `overlay_client/backend/helper_ipc.py`
- Planned implementation shape for this stage:
  - extension enable path exports a session D-Bus service
  - helper service advertises protocol version and helper identity
  - helper service requires a session token before event exchange
  - no client-side connection or discovery logic yet
- Planned tests for this stage:
  - `python3 -m json.tool helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/metadata.json >/dev/null`
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py -q`
- Expected behavior change:
  - yes. Once the extension is manually installed and enabled, it would begin exposing a real helper-side D-Bus surface.
  - Because this is a new behavior rather than a pure extraction, stop for user confirmation before implementing the stage.

#### Stage 2.3 Detailed Plan
- Objective:
  - Extend the helper-side D-Bus service so it can emit the first live event stream for GNOME helper-backed tracking.
  - Keep the event surface minimal and scoped to the first milestone: active-window and geometry updates for Elite Dangerous targeting.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/service.js`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/README.md`
  - `overlay_client/tests/test_helper_ipc_boundary.py`
  - reference-only alignment source: `overlay_client/backend/helper_ipc.py`
- Planned implementation shape for this stage:
  - extend the D-Bus interface with an `Event(message_json)` signal whose JSON payload mirrors the existing Python helper-boundary event schema (`type`, `helper_kind`, `protocol_version`, `session_token`, `event`, `payload`)
  - use GNOME Shell display/window hooks only inside the extension:
    - `global.display` focus changes to refresh the active target window
    - tracked-window `position-changed`, `size-changed`, and lifecycle loss hooks to refresh geometry or clear state
  - emit `active_window_changed` only after a successful `Hello(session_token)` handshake establishes a session token
  - emit `window_geometry_changed` only after a successful `Hello(session_token)` handshake establishes a session token
  - treat Elite Dangerous targeting as title-driven for now, matching the existing client-side title-hint behavior rather than introducing a new GNOME-only identity rule
  - constrain payload content to the minimum fields later client-side code will need for Elite Dangerous targeting and geometry tracking:
    - `identifier`
    - `title`
    - `wm_class`
    - `is_foreground`
    - `is_visible`
    - `x`, `y`, `width`, `height` for geometry events
  - do not add client-side consumption yet
- Planned tests for this stage:
  - `python3 -m json.tool helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/metadata.json >/dev/null`
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py -q`
- Expected behavior change:
  - yes. Once the extension is manually installed and enabled, it would begin emitting live helper event traffic after a successful handshake.
  - Because this is a new behavior rather than a pure extraction, stop for user confirmation before implementing the stage.

### Phase 3: Client-Side GNOME Helper Integration
- Teach the client to discover whether the GNOME extension is installed, enabled, and reachable.
- Upgrade the GNOME backend bundle from a stub path into a real helper-backed runtime path.
- Preserve explicit fallback when the helper is unavailable or invalid.
- Risks: false-positive helper detection, stale helper sessions, or status that overstates support.
- Mitigations: require reachability, protocol-version match, and token match before the backend is treated as helper-backed.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add GNOME helper availability/reachability probing to the platform/backend probe layer | Completed |
| 3.2 | Add a client-side GNOME helper runtime module for D-Bus connection, validation, and event consumption | Completed |
| 3.3 | Replace the stub GNOME bundle with a helper-backed discovery/runtime path and preserve explicit missing-helper fallback behavior | Completed |
| 3.4 | Stabilize helper-backed GNOME tracking so focus loss does not incorrectly clear an existing Elite window match | Completed |
| 3.5 | Prevent the helper-backed GNOME overlay from raising/activating itself and oscillating visibility | Completed |
| 3.6 | Preserve hidden-state during click-through reapplication so helper-backed GNOME does not forcibly re-show the overlay every follow tick | Completed |
| 3.7 | Tighten helper-side foreground detection for the tracked GNOME window so follow visibility does not rely on brittle focus-window identity alone | Completed |
| 3.8 | Stabilize helper-backed GNOME foreground semantics and add the observability needed to distinguish true backgrounding from ambiguous focus loss | Completed |

#### Stage 3.1 Detailed Plan
- Objective:
  - Add a real GNOME helper probe path so backend selection no longer depends on test-only `available_helpers` injection for GNOME helper presence.
  - Keep the change scoped to probe/selection/status surfaces only; do not consume helper events or replace the GNOME bundle in this stage.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `overlay_client/backend/contracts.py`
  - `overlay_client/backend/probe.py`
  - `overlay_client/backend/probe_gnome.py` (new runtime helper-probe seam so D-Bus reachability checks stay out of the pure probe normalizer)
  - `overlay_client/backend/selector.py`
  - `overlay_client/backend/status.py`
  - `overlay_client/platform_context.py`
  - `overlay_client/backend/consumers.py`
  - `load.py` only if the plugin-side shadow status must continue to emit a structurally compatible probe payload
  - unit tests:
    - `overlay_client/tests/test_platform_probe.py`
    - `overlay_client/tests/test_backend_selector.py`
    - `overlay_client/tests/test_backend_status.py`
    - `overlay_client/tests/test_backend_contracts.py`
- Planned implementation shape for this stage:
  - extend the pure probe model so GNOME helper availability can distinguish at least:
    - helper absent/unseen
    - helper present and reachable enough to count as available
    - helper present but incompatible/unusable
  - keep the probe model pure by normalizing explicit probe inputs first, then let runtime callers supply GNOME helper evidence into `collect_platform_probe(...)`
  - teach selector/status surfaces to use the new GNOME helper probe evidence so fallback/helper-state reporting can distinguish `missing_helper` from `incompatible_helper`
  - do not add helper event consumption, tracker replacement, or bundle runtime wiring yet
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_platform_probe.py overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_backend_contracts.py -q`
- Expected behavior change:
  - yes. Once runtime callers start supplying real GNOME helper probe evidence, GNOME Wayland backend family, fallback reason, and helper-state reporting can change from the current conservative “helper missing unless explicitly injected” model to runtime-detected helper availability or incompatibility.
  - Because this changes live backend status behavior rather than performing a pure extraction, stop for user confirmation before implementing the stage.

#### Stage 3.2 Detailed Plan
- Objective:
  - Add the client-side GNOME helper runtime module that connects to the helper over session D-Bus, validates the helper boundary, performs the handshake, and prepares typed event consumption.
  - Keep the scope below full backend cutover: this stage should build the runtime seam and tests without yet replacing the stub GNOME bundle.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `overlay_client/backend/gnome_helper_runtime.py` (new client-side runtime seam)
  - `overlay_client/backend/helper_ipc.py`
  - `overlay_client/backend/contracts.py`
  - `overlay_client/backend/consumers.py`
  - `overlay_client/backend/__init__.py`
  - `overlay_client/tests/test_helper_ipc_boundary.py`
  - `overlay_client/tests/test_backend_contracts.py`
  - `overlay_client/tests/test_backend_consumers.py`
  - `overlay_client/tests/test_gnome_helper_runtime.py` (new)
- Planned implementation shape for this stage:
  - create a client-owned runtime object that:
    - targets `org.edmc.EDMCModernOverlay` at `/org/edmc/EDMCModernOverlay`
    - builds and validates a `session_dbus` helper boundary
    - performs `Hello(session_token)` and validates helper kind and protocol version
    - subscribes to the helper `Event(message_json)` signal
    - parses incoming JSON through the existing helper-boundary validation path
  - keep the runtime seam data-oriented so bundle/runtime consumers can use it in Stage `3.3` without reimplementing handshake or event parsing
  - do not replace the GNOME bundle or enable follow-mode consumption yet
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_gnome_helper_runtime.py -q`
- Expected behavior change:
  - yes. Once the runtime module starts performing a real D-Bus handshake and listening for helper events, the overlay client gains a live GNOME helper communication path even before the GNOME bundle is cut over to use it.
  - Because this is a new runtime behavior rather than a pure extraction, stop for user confirmation before implementing the stage.

#### Stage 3.3 Detailed Plan
- Objective:
  - Replace the stub GNOME bundle with a helper-backed bundle path that uses the Stage `3.2` runtime seam for GNOME helper communication and preserves explicit fallback when the helper is missing or incompatible.
  - Keep the cutover focused on GNOME runtime wiring; do not broaden install/docs work into this stage.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `overlay_client/backend/bundles/gnome_shell_wayland.py`
  - `overlay_client/backend/bundles/_wayland_common.py` only if the existing bundle helper factory needs a narrow extension point
  - `overlay_client/backend/contracts.py`
  - `overlay_client/backend/consumers.py`
  - `overlay_client/backend/gnome_helper_runtime.py`
  - `overlay_client/window_tracking.py`
  - `overlay_client/tests/test_backend_consumers.py`
  - `overlay_client/tests/test_backend_contracts.py`
  - `overlay_client/tests/test_window_tracking_bundle_routing.py`
  - `overlay_client/tests/test_gnome_helper_runtime.py`
- Planned implementation shape for this stage:
  - attach a real GNOME helper IPC backend to the GNOME bundle
  - replace the current `create_unavailable_tracker` path with a GNOME helper-backed tracker/runtime path that consumes validated helper events
  - preserve explicit missing-helper and incompatible-helper fallback behavior by keeping selection/probe authority outside the bundle
  - reuse the Stage `3.2` runtime seam rather than reimplementing D-Bus handshake or event parsing inside the bundle
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_gnome_helper_runtime.py -q`
- Expected behavior change:
  - yes. This stage changes live GNOME target-discovery/runtime behavior by replacing the current no-tracker stub path with helper-backed runtime consumption.
  - Because this is the GNOME bundle cutover rather than a pure extraction, stop for user confirmation before implementing the stage.

#### Stage 3.4 Detailed Plan
- Objective:
  - Fix the helper-backed GNOME tracking regression where the overlay flashes briefly on alt-tab or focus transitions, then hides because the helper reports `matched: false` even though the Elite window still exists.
  - Keep the scope narrow: stabilize target retention and foreground reporting for the helper-backed GNOME path without broadening helper install, selector policy, or non-GNOME behavior.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/service.js`
  - `overlay_client/backend/gnome_helper_runtime.py`
  - `overlay_client/tests/test_gnome_helper_runtime.py`
  - `overlay_client/tests/test_helper_ipc_boundary.py` only if the event payload contract needs a narrow clarification
- Planned implementation shape for this stage:
  - change GNOME helper target resolution so it does not depend solely on the currently focused window
  - prefer the focused window when it matches Elite, but otherwise retain the currently tracked Elite window while it still exists and still matches
  - if no focused match exists, scan GNOME-managed windows for a surviving Elite match before emitting `matched: false`
  - report `is_foreground` truthfully from focus state instead of hardcoding `true` for every matched helper event
  - keep `matched: false` reserved for the real disappearance/unmanage case rather than ordinary focus loss
  - keep the client visibility rule unchanged; the bug is in helper/runtime state semantics rather than the visibility policy itself
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_helper_ipc_boundary.py -q`
- Expected behavior change:
  - yes. This stage changes live helper-backed GNOME target-retention behavior so an existing Elite window remains tracked across focus transitions instead of being cleared immediately.
  - This behavior change is the intended bug fix for the current GNOME helper flash-and-hide regression.

#### Stage 3.5 Detailed Plan
- Objective:
  - Fix the remaining helper-backed GNOME flash/hide loop after Stage `3.4` by preventing the overlay from explicitly raising/activating itself on the compositor-helper GNOME path.
  - Keep the fix narrowly scoped to helper-backed GNOME raise/show policy; do not weaken X11/XWayland behavior or generic Wayland visibility semantics.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `overlay_client/platform_integration.py`
  - `overlay_client/setup_surface.py`
  - `overlay_client/follow_surface.py`
  - `overlay_client/tests/test_platform_controller_backend_status.py`
  - `overlay_client/tests/test_follow_surface_mixin.py`
- Planned implementation shape for this stage:
  - add an explicit platform policy seam for whether the overlay window should call `raise_()` on show/drag-state refresh
  - return `False` only for the helper-backed GNOME compositor path, where compositor-managed stacking exists and explicit raising appears to steal focus from the tracked game window
  - keep `show()`/visibility behavior intact while suppressing explicit `raise_()` calls in the helper-backed GNOME path
  - route all follow-surface/show/drag-state raise sites through the same policy helper so the GNOME path cannot oscillate by mixing raised and non-raised flows
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_follow_surface_mixin.py -q`
- Expected behavior change:
  - yes. This stage changes the helper-backed GNOME overlay window policy so the overlay no longer explicitly raises itself when shown or when click-through/drag state is reapplied.
  - This behavior change is the intended fix for the current helper-backed GNOME activation loop.

#### Stage 3.6 Detailed Plan
- Objective:
  - Fix the remaining helper-backed GNOME flash/hide loop after Stage `3.5` by making click-through reapplication preserve the current overlay visibility state instead of forcibly calling `show()` on a hidden overlay.
  - Keep the scope narrow: interaction/click-through state should continue to prepare the window and apply transparency flags, but it must not override follow-mode visibility decisions.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `overlay_client/interaction_controller.py`
  - `overlay_client/setup_surface.py`
  - `overlay_client/tests/test_interaction_controller.py`
  - `overlay_client/tests/test_exception_scoping.py`
- Planned implementation shape for this stage:
  - add a visibility-state seam to `InteractionController` so click-through updates can tell whether the overlay is already visible
  - preserve the existing visible-path behavior when the overlay is already shown
  - stop calling `ensure_visible()` and `raise_()` when the overlay is currently hidden, so periodic drag-state/click-through refreshes cannot re-show it behind follow-mode’s back
  - keep the rest of the click-through/platform wiring unchanged
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_exception_scoping.py -q`
- Expected behavior change:
  - yes. This stage changes the interaction-controller visibility policy so click-through reapplication preserves the current hidden state instead of forcibly showing the overlay.
  - This behavior change is the intended fix for the remaining helper-backed GNOME flash/hide loop visible in the current live logs.

#### Stage 3.7 Detailed Plan
- Objective:
  - Fix the remaining helper-backed GNOME false-background state where the Elite window stays tracked but the helper reports `is_foreground=False`, causing follow mode to hide the overlay even while the game is active.
  - Keep the change helper-side and focused on foreground detection only; do not broaden the selector, visibility policy, or payload contract.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/service.js`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/README.md` only if the helper version marker or foreground semantics note needs a narrow refresh
- Planned implementation shape for this stage:
  - prefer GNOME/Mutter window-native focus APIs such as `has_focus()` when available on the tracked `MetaWindow`
  - fall back to the existing `display.get_focus_window()` / `focus_window` identity comparison only when direct focus APIs are unavailable
  - keep the helper event payload shape unchanged so the client/runtime contract does not need to change again
  - bump the helper version marker so live-session verification can confirm the new helper code is loaded
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_helper_ipc_boundary.py -q`
  - manual GNOME-session validation remains required because the changed logic lives in the GNOME Shell extension and the repo does not currently have helper-side automated tests for Mutter focus behavior
- Expected behavior change:
  - yes. This stage changes helper-side `is_foreground` detection for the tracked GNOME window so active gameplay is less likely to be misreported as background.
  - This behavior change is the intended fix for the current post-Stage `3.6` log pattern where the game remains tracked but helper events still report `foreground=False`.

#### Stage 3.8 Detailed Plan
- Objective:
  - Fix the remaining helper-backed GNOME visibility oscillation seen in live `stage3.7` validation, where the overlay is shown correctly and then hidden on the next 500 ms follow tick because the tracked Elite window remains matched and visible but the helper still reports `is_foreground=False`.
  - Keep the scope narrow and evidence-driven: improve foreground-state observability first, then make helper-backed GNOME treat ambiguous focus loss differently from a proven background transition.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/service.js`
  - `overlay_client/follow_controller.py`
  - `overlay_client/tests/test_gnome_helper_runtime.py`
  - `overlay_client/tests/test_follow_controller.py` (new)
- Planned implementation shape for this stage:
  - expand follow-controller observability so tracker-state logging includes foreground/visible transitions even when identifier and geometry stay the same
  - keep the helper payload contract unchanged; continue emitting boolean `is_foreground` and `is_visible`
  - refine helper-side foreground evaluation in `service.js` so it distinguishes:
    - tracked Elite window definitely focused
    - another window definitely focused
    - ambiguous/unknown focus state where GNOME does not positively identify a focused non-Elite window and the tracked Elite window is still matched and visible
  - stop treating that ambiguous state as an immediate background transition; instead retain the prior foreground result briefly while the tracked Elite window remains matched, visible, and unchanged
  - implement the hold/debounce on the helper side only, so the Python runtime and window-visibility policy continue to consume a simple boolean foreground signal
  - keep `matched`, geometry, install flow, selector policy, runtime contract shape, and non-GNOME behavior unchanged
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_follow_controller.py -q`
  - manual GNOME-session validation remains required because the changed logic depends on live Mutter/GNOME focus behavior and the repo has no direct helper-side GJS test harness
- Expected behavior change:
  - yes. This stage changes helper-backed GNOME foreground semantics so the overlay is not hidden immediately on an ambiguous focus-loss report while the tracked Elite window is still clearly present and visible.
  - This behavior change is the intended fix for the current `stage3.7` live log pattern where the overlay is shown full-screen and then hidden roughly 0.5 seconds later by follow-mode policy.
  - Because this stage changes live helper-backed GNOME focus/visibility semantics rather than performing a pure extraction, confirm the behavior change before implementation.

### Phase 4: Install/Enable/Disable/Uninstall Integration
- Make the helper operationally usable by documenting or scripting the install flow without violating the explicit-approval rule.
- Ensure disabling or uninstalling the extension returns the overlay to a truthful fallback state.
- Risks: support confusion around where the extension lives, how to remove it, or what state the client is in after helper removal.
- Mitigations: make install target, enablement, disablement, and uninstall steps visible in docs and status messages.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Add helper install guidance for the first supported per-user manual copy/enable workflow | Completed |
| 4.2 | Add disable/uninstall guidance and ensure status surfaces describe missing, disabled, and `incompatible_helper` states accurately | Completed |
| 4.3 | Add or update installer/prefs/support docs so GNOME helper operations are user-comprehensible and reversible | Completed |
| 4.4 | Add the GNOME host `python3-gi` prerequisite path, explicit permission gate, and truthful missing-prerequisite status reporting | Completed |

#### Stage 4.1 Detailed Plan
- Objective:
  - Add the minimal supported install guidance for the per-user GNOME helper path without turning the helper README into a long walkthrough.
  - Keep the change doc-only and operationally narrow: install target, copy step, and enable methods only.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/README.md`
- Planned documentation shape for this stage:
  - update the helper README status so it no longer claims there is no client/runtime wiring
  - add the first supported per-user install target:
    - `~/.local/share/gnome-shell/extensions/edmc-modern-overlay@edmc.local/`
  - add the minimal supported install/enable flow:
    - copy this extension directory into the target path
    - enable via `gnome-extensions enable edmc-modern-overlay@edmc.local`
    - or enable in the GNOME Extensions app
  - keep uninstall/disable/upgrade details out of this stage
- Planned tests for this stage:
  - None. This stage is doc-only and does not change runtime or testable code paths.
- Unchanged behavior contract:
  - no selector/probe/runtime changes
  - no installer-script changes
  - no status-surface changes

#### Stage 4.2 Detailed Plan
- Objective:
  - Add the minimal supported disable/uninstall guidance for the per-user GNOME helper path and verify that the existing status/UI wording already distinguishes missing/disabled helper states from `incompatible_helper`.
  - Keep the stage narrow and mostly doc-focused; do not broaden it into installer scripting or additional runtime behavior unless an actual wording gap is discovered.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/README.md`
  - reference-only validation surfaces:
    - `overlay_client/backend/status.py`
    - `overlay_client/tests/test_backend_status.py`
- Planned documentation shape for this stage:
  - add the minimal supported disable flow:
    - `gnome-extensions disable edmc-modern-overlay@edmc.local`
    - or disable in the GNOME Extensions app
  - add the minimal supported uninstall flow:
    - disable the extension first
    - remove `~/.local/share/gnome-shell/extensions/edmc-modern-overlay@edmc.local/`
  - add one concise note that disable/uninstall should return the overlay to the existing missing-helper fallback path, while protocol or D-Bus mismatch remains an `incompatible_helper` case
  - keep upgrade and broader support/troubleshooting notes out of this stage
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py -q`
- Unchanged behavior contract:
  - no selector/probe/runtime changes
  - no installer-script changes
  - no new status-surface behavior changes expected; existing status wording should remain authoritative

#### Stage 4.3 Detailed Plan
- Objective:
  - Align the support-facing docs with the now-implemented GNOME helper path without duplicating the full helper README or turning the support docs into long walkthroughs.
  - Keep the stage doc-only: the helper README remains the authoritative install/enable/disable/uninstall reference, while FAQ/troubleshooting only explain the helper requirement, status vocabulary, and reversible operator path at a high level.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `docs/FAQ.md`
  - `docs/troubleshooting.md`
  - reference-only validation surfaces:
    - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/README.md`
    - `overlay_client/backend/status.py`
    - `tests/test_install_linux.py`
- Planned documentation shape for this stage:
  - update the Wayland support FAQ so GNOME no longer reads as XWayland-only or future-only:
    - state that GNOME Wayland now has a helper-backed path
    - keep the install guidance minimal by pointing to the helper README for the exact per-user copy/enable/disable/uninstall steps
    - note that the Linux installer records helper approval but does not install or enable the extension automatically
  - add one concise troubleshooting note that maps the current status vocabulary to operator action:
    - `missing_helper` means the extension is absent or disabled
    - `incompatible_helper` means the extension is present but the D-Bus/helper contract failed
    - disable or uninstall should return to the missing-helper fallback path
  - avoid broadening root installation docs, adding scripts, or duplicating the helper README workflow verbatim
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py tests/test_install_linux.py -q`
- Unchanged behavior contract:
  - no selector/probe/runtime changes
  - no installer-script or installer-matrix changes
  - no new prefs/status behavior changes; this stage only aligns support documentation with the existing implementation

#### Phase 4 Addendum: Host `python3-gi` Dependency And Permission Gate
- Purpose:
  - Capture and implement the GNOME-helper packaging fix for the missing host `python3-gi` dependency on Debian/Ubuntu GNOME Wayland.
  - Keep the scope narrow: explicit permission-gated host package install, forced venv rebuild after approval, and truthful missing-prerequisite status reporting.
- Problem statement:
  - The GNOME Shell extension can be installed, enabled, and live on D-Bus while the overlay client still reports `missing_helper`.
  - On Linux, the current overlay client virtualenv installs `pydbus` but does not reliably expose the host `gi` module that `pydbus` depends on.
  - On Ubuntu/Debian, that means the live helper-backed GNOME path may require the host package `python3-gi` plus a Linux virtualenv strategy that can see distro-provided Python modules.
- Implemented touch points for this stage:
  - `scripts/install_linux.sh`
  - `tests/test_install_linux.py`
  - `docs/wiki/Installation-FAQs.md`
  - `overlay_client/backend/probe_gnome.py`
  - `overlay_client/backend/status.py`
  - `overlay_client/tests/test_probe_gnome.py`
  - `overlay_client/tests/test_platform_probe.py`
  - `overlay_client/tests/test_backend_status.py`
- Locked approval rule for any future installer change:
  - Installing `python3-gi` or any equivalent host package is a host-system change and must require explicit user permission.
  - The Linux installer must ask the user before installing that package; it must never install host GNOME/PyGObject packages silently.
  - GNOME helper approval and host package approval are separate decisions. Recording approval for GNOME helper guidance does not authorize host package installation.
  - Any future non-interactive path must remain explicit and user-driven. Do not infer permission for host package installation from compositor auto-detection alone.
  - More broadly, host package installation on the normal Linux installer path must be permission-gated. As part of this addendum, audit the existing generic dependency-install flow and fix it if any host-package path can proceed without an explicit user approval step.
- Reviewed scope decisions:
  - keep the implementation minimal: only apply this host-package path when the installer detects GNOME Wayland
  - only offer the host-package install after the user has already approved the GNOME helper path
  - first implementation pass is Debian/Ubuntu only; do not widen the distro package matrix yet
  - prompting each time is acceptable; do not persist separate host-package approval state in this first pass
  - existing installs should force a virtualenv rebuild once the user approves the host-package path, because the current isolated `overlay_client/.venv` cannot see the distro-provided `gi` module
  - if the user declines the host package install, keep the user-facing outcome consistent with `missing_helper` so long as the status wording makes it clear the required host prerequisite was not installed
  - bundle the probe/runtime honesty fix into the same later implementation stage so GNOME helper import/runtime failures do not silently collapse into ambiguous status
  - use one combined installer approval prompt for the host package plus required venv rebuild:
    - `GNOME Wayland helper support needs the host package 'python3-gi' and a rebuild of overlay_client/.venv. Continue?`
  - while implementing this addendum, also verify that the normal Linux dependency-install prompt is always explicit before any host package install; if not, tighten that flow in the same stage
- Implemented technical direction:
  - keep the generic Linux dependency bucket unchanged so `python3-gi` is not silently pulled in by the normal Wayland package path
  - after GNOME-helper approval, on Debian/Ubuntu GNOME Wayland only, prompt explicitly before installing `python3-gi` and rebuilding `overlay_client/.venv`
  - rebuild `overlay_client/.venv` with `--system-site-packages` so the overlay client can see distro-provided `gi` modules when this path is approved
  - tighten GNOME helper probing/status so missing `gi` reports a deliberate host-prerequisite-missing detail instead of collapsing into an ambiguous missing-helper path
- Deferred release-note reminder:
  - when preparing the `1.0.0` release notes, add a callout explaining that GNOME-helper users on Debian/Ubuntu may be prompted to install `python3-gi` and rebuild `overlay_client/.venv`
  - do not update `RELEASE_NOTES.md` yet; keep this reminder in the plan until release-note work begins
- Tests for this implementation:
  - `source .venv/bin/activate && python -m pytest tests/test_install_linux.py overlay_client/tests/test_probe_gnome.py overlay_client/tests/test_platform_probe.py overlay_client/tests/test_backend_status.py -q`
- Implementation status:
  - implemented in Stage `4.4`
  - Debian/Ubuntu GNOME Wayland only
  - no automatic GNOME Shell extension install or enable path was added
  - `RELEASE_NOTES.md` is still intentionally deferred; keep the `1.0.0` reminder in this plan until release-note work begins

#### Stage 4.4 Detailed Plan
- Objective:
  - Implement the minimal Debian/Ubuntu-only GNOME helper prerequisite path without violating the approved permission chain.
  - Keep the stage tightly scoped: do not broaden the distro matrix, do not add persistent host-package approval state, and do not change non-GNOME Linux behavior.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `scripts/install_linux.sh`
  - `tests/test_install_linux.py`
  - `docs/wiki/Installation-FAQs.md`
  - `overlay_client/backend/probe_gnome.py`
  - `overlay_client/backend/status.py`
  - `overlay_client/tests/test_probe_gnome.py` (new)
  - `overlay_client/tests/test_platform_probe.py`
  - `overlay_client/tests/test_backend_status.py`
  - optional metadata touch point, only if it proves cleaner than shell-local constants:
    - `scripts/install_matrix.json`
- Actual-code constraint discovered during planning:
  - the current installer order runs `ensure_system_packages` and `create_venv_and_install` before `handle_compositor_helper_guidance`
  - because of that, `python3-gi` cannot simply be added to the normal Wayland package list without violating the approved flow
  - the GNOME helper host-package prompt must instead live in a helper-specific post-approval path after `handle_compositor_helper_guidance` (or the installer flow must be reordered so helper approval happens before any GNOME helper host-package install prompt)
- Planned implementation shape for this stage:
  - keep `ensure_system_packages` responsible for the existing core/Qt/general Wayland packages only
  - after GNOME helper approval is granted, and only on detected GNOME Wayland + Debian/Ubuntu, ask:
    - `GNOME Wayland helper support needs the host package 'python3-gi' and a rebuild of overlay_client/.venv. Continue?`
  - audit the generic Linux dependency-install path and ensure host packages on the normal installer path also require an explicit approval prompt before installation
  - if the user declines:
    - make no host package or venv changes
    - keep the user-facing helper outcome in the `missing_helper` path, with status wording that explains the required host prerequisite was not installed
  - if the user accepts:
    - install `python3-gi`
    - force a rebuild of `overlay_client/.venv`
    - rebuild the venv so it can see distro-provided `gi` modules when needed
  - in the same stage, tighten GNOME helper probe/status reporting so import/environment failures no longer collapse silently into the happy path
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest tests/test_install_linux.py overlay_client/tests/test_probe_gnome.py overlay_client/tests/test_platform_probe.py overlay_client/tests/test_backend_status.py -q`
- Behavior change required for this stage:
  - yes. This stage changes Linux installer flow, can install a new host package on Debian/Ubuntu GNOME Wayland after explicit approval, forces a rebuild of `overlay_client/.venv` after that approval, and changes GNOME helper status reporting.
  - do not proceed with implementation without explicit confirmation that these behavior changes are acceptable for Stage `4.4`.
- Unchanged behavior contract:
  - no changes for Windows
  - no changes for non-GNOME Linux sessions
  - no changes for non-Debian/Ubuntu distros in this first pass
  - no automatic GNOME Shell extension install or enable path
  - no persistence of separate host-package approval state in this first pass

### Phase 5: GNOME Presentation And Active-Game Stacking Control
- Close the remaining gap between helper-backed GNOME tracking and a reliable overlay in the declared supported GNOME play mode.
- Determine whether GNOME Shell can manage the existing external Qt overlay window above the active game, or whether the product must narrow support to a weaker classification even for borderless/windowed.
- Architectural requirement:
  - fullscreen is not a release gate for GNOME or any other backend
  - a stable borderless/windowed path is an acceptable supported outcome
  - fullscreen support should be treated as an additional capability only when live validation proves it
- Risks: the current GNOME helper boundary may be fundamentally tracking-only, and Mutter/GNOME Shell may not provide a safe/stable way to keep an external Wayland Qt window above a focused active game window even in borderless/windowed-sized play.
- Mitigations: separate capability investigation from support claims, keep the current tracking path intact while probing presentation control, and fail honest if GNOME cannot provide the required presentation guarantees.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Record the current active-game stacking blocker and lock the honesty gate for GNOME supported-mode support | Completed |
| 5.2 | Prove or disprove a GNOME-controlled presentation mechanism for the external overlay window | Completed |
| 5.3 | Implement the chosen GNOME presentation/control seam and wire it into the helper-backed runtime | Completed |
| 5.4 | Suppress GNOME shell chrome while the helper-backed overlay is actively promoted in the supported play mode | In Progress |
| 5.5 | Revalidate borderless/windowed behavior and any optional fullscreen behavior, then finalize support classification and release-readiness language | Not Started |

#### Stage 5.1 Detailed Plan
- Objective:
  - Capture the live blocker explicitly in the plan so GNOME supported-mode support is not conflated with the now-working helper tracking/runtime path.
  - Lock the honesty bar before any more runtime edits: GNOME helper presence, handshake success, and geometry tracking are not enough if the overlay still renders behind the active game in the play mode we actually intend to support.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - reference-only evidence surfaces:
    - `overlay_client/window_controller.py`
    - `overlay_client/follow_surface.py`
    - `overlay_client/backend/bundles/_linux_window_integration.py`
    - `overlay_client/backend/helper_ipc.py`
    - live log evidence from `overlay_client.log`
- Planned documentation shape for this stage:
  - record that the current helper-backed GNOME path is a tracking/runtime success but an active-game presentation failure in borderless/windowed-sized testing
  - lock that GNOME cannot be called `true_overlay` for its declared supported mode until the overlay is proven visible above the active game while the game retains focus
  - note that the current `follow_surface.py` fullscreen-sized warning is only a heuristic and must not be treated as proof that the failing play mode was exclusive fullscreen
  - note the immediate fallback if Phase `5` fails: narrow support/classification honestly rather than pretending the supported borderless/windowed mode is working
- Planned tests for this stage:
  - None. This stage is plan/evidence-only and should not change code paths.
- Unchanged behavior contract:
  - no runtime changes
  - no helper protocol changes
  - no selector/status changes yet

#### Stage 5.2 Detailed Plan
- Objective:
  - Determine whether GNOME Shell can reliably control presentation/stacking for the current external Qt overlay window, rather than only tracking the game window.
  - Keep this stage prototype-scoped: prove or disprove that the existing external Qt overlay can be identified and promoted by the helper before committing to a deeper helper-owned presentation model in Stage `5.3`.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - investigation/prototype targets for the approved behavior change:
    - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/service.js`
    - `overlay_client/launcher.py` as the current source of the fixed overlay window title used by the prototype (`EDMC Modern Overlay`)
    - `overlay_client/backend/helper_ipc.py`
    - `overlay_client/backend/gnome_helper_runtime.py`
    - `overlay_client/tests/test_helper_ipc_boundary.py`
    - `overlay_client/tests/test_gnome_helper_runtime.py`
    - `overlay_client/tests/test_backend_consumers.py`
  - live-session validation targets outside the repo:
    - GNOME Shell / Mutter window state exposed to the extension
    - the external Qt overlay window as seen by GNOME Shell
- Current-code constraint discovered during planning:
  - the current GNOME helper boundary is tracking-only: `service.js` exposes `Hello(...)` plus `Event(message_json)`, and `helper_ipc.py` only allows `active_window_changed` / `window_geometry_changed`
  - the current GNOME runtime seam consumes validated tracking events but has no notion of overlay-window registration, presentation ownership, or GNOME-side control commands
  - the current GNOME presentation path still runs through the generic external-window Wayland integration in `_linux_window_integration.py`, which means a meaningful Stage `5.2` prototype cannot answer the question without introducing a real helper/runtime behavior change
- Planned investigation shape for this stage:
  - identify the overlay window using the fixed title currently set by the Qt launcher (`EDMC Modern Overlay`) rather than adding a new client registration seam in this stage
  - teach the GNOME helper to track both the Elite window and the external overlay window as distinct `MetaWindow` objects
  - prototype GNOME-side presentation control by applying the narrowest safe Mutter window-management calls to the overlay window only while the tracked game window is foreground/visible
  - do not migrate the external overlay window across monitors or workspaces in this stage; GNOME 46 live evidence showed that `move_to_monitor()` on the external overlay `MetaWindow` can abort GNOME Shell
  - emit a dedicated helper event describing whether the helper found the overlay window and whether compositor-side promotion was attempted/applied, so the prototype outcome is observable from the existing client/runtime seam
  - if this prototype cannot keep the overlay above the active game without stealing focus or becoming unstable, treat that as negative evidence for the current external-window model and pivot Stage `5.3` toward a deeper helper-owned presentation model
  - do not change the shipped support claim in this stage; this is still capability-proving work, not final hardening
- Planned tests/evidence for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_backend_consumers.py -q`
  - manual GNOME-session validation only
  - record exact GNOME Shell version, whether the overlay window is visible to the extension as a distinct window, whether the helper reports presentation promotion as applied, and whether that prototype affects active-game stacking in borderless/windowed-sized play
- Expected outcome gate:
  - if GNOME can control the existing external Qt window through helper-side window promotion, proceed to Stage `5.3` by hardening that control seam
  - if GNOME cannot, pivot Stage `5.3` toward a helper-owned presentation model rather than stopping at a support-policy downgrade

#### Stage 5.3 Detailed Plan
- Objective:
  - Harden the viable GNOME helper-controlled seam chosen in Stage `5.2` so the helper owns both stacking and click-through for the promoted external overlay window.
  - Keep the change explicit and backend-owned; do not silently broaden the helper contract beyond what the current click-through/input failure proves is necessary.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/service.js`
  - `overlay_client/backend/helper_ipc.py`
  - `overlay_client/backend/gnome_helper_runtime.py`
  - `overlay_client/backend/gnome_helper_control.py`
  - `overlay_client/backend/bundles/_linux_window_integration.py`
  - `overlay_client/tests/test_helper_ipc_boundary.py`
  - `overlay_client/tests/test_gnome_helper_runtime.py`
  - `overlay_client/tests/test_gnome_helper_control.py`
  - `overlay_client/tests/test_linux_window_integration.py`
- Planned implementation shape for this stage:
  - extend the helper boundary with an explicit client-to-helper control call for overlay input passthrough rather than trying to infer drag/interactivity state from tracking events
  - keep overlay discovery title-based in this stage; do not add a separate overlay registration handshake unless the control call proves insufficient
  - teach the GNOME helper to apply compositor-side input suppression to the overlay actor/window when click-through is requested, while preserving the current Stage `5.2.1` non-migrating stacking path
  - add a small Python-side helper control client and wire GNOME Wayland integration to call it when click-through toggles, while keeping the existing Qt/native click-through path as the fallback if helper control is unavailable
  - emit richer `presentation_state_changed` diagnostics so live validation can distinguish stacking success from input-suppression success
  - keep non-GNOME backends unchanged
  - keep the current tracking and geometry behavior intact
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_gnome_helper_control.py overlay_client/tests/test_linux_window_integration.py -q`
  - manual GNOME-session validation remains required because the actual success criterion is active-game stacking behavior under GNOME Shell in the declared supported play mode
- Behavior change required for this stage:
  - yes. This stage changes the helper/client contract and GNOME presentation behavior.
  - explicit confirmation to proceed was recorded after Stage `5.2` identified the GNOME-controlled external-window path as viable.

#### Stage 5.4 Detailed Plan
- Objective:
  - Close the newly isolated GNOME shell-chrome gap after stacking and click-through already proved out: hide the GNOME top panel and Ubuntu Dock only while the helper-backed overlay is actively promoted above the tracked Elite window in the supported play mode.
  - Keep this helper-owned and reversible; restore shell chrome immediately on focus loss, helper disable, or overlay loss.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/extension.js`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/service.js`
  - `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/README.md`
  - `overlay_client/backend/gnome_helper_runtime.py`
  - `overlay_client/tests/test_gnome_helper_runtime.py`
- Current-code constraint discovered during planning:
  - helper-backed GNOME `stage5.3` now proves `overlay_above=True` and `overlay_input_passthrough_applied=True`, but the Ubuntu Dock and GNOME top bar still remain visible above the active game in supported borderless/windowed testing
  - the remaining gap is therefore shell-owned chrome, not overlay window stacking or input passthrough
  - live `stage5.4` validation shows the helper code is running, but the current shell-chrome manager is still too weak:
    - `presentation_state_changed` reports `stage5.4`, so the helper reload path is not the blocker
    - `panel_hidden` / `dock_hidden` currently count "any hidden actor" as success, which can be a false positive when one hidden corner or dummy dock actor exists while the visible top bar or dock still remains on screen
    - `_hideShellChrome()` stops reapplying once `_shellChromeHidden` is set, so GNOME Shell or Ubuntu Dock can make the chrome visible again without the helper pushing it back down
  - this chrome is not controlled by Qt window flags, so the next fix must stay helper-side and make shell-chrome suppression idempotent while the promoted overlay remains active
  - live `stage5.4.1` follow-up validation narrowed the remaining Ubuntu Dock problem further:
    - the dock visibly "tries to close" and then bounces back about every half second
    - helper diagnostics now show the real mismatch instead of a false positive: `panel_hidden=True` can hold while `dock_hidden=False`
    - that means the helper is no longer failing to act; it is now fighting Ubuntu Dock's own `DockedDash` autohide/intellihide loop
- Planned implementation shape for this stage:
  - import GNOME Shell `Main` in the helper and add a narrow shell-chrome manager
  - hide `Main.layoutManager.panelBox` and related panel actors only while the helper-backed overlay is actively promoted for the tracked Elite window
  - detect Ubuntu Dock actors by name (`dashtodockContainer`) and prefer the dock actor's own `_hide()` / `_show()` seam when available, falling back to generic actor visibility only if that seam is absent
  - when the dock actor is a real Ubuntu Dock `DockedDash`, suppress its own show loop while the overlay is promoted by temporarily overriding the per-dock hover/autohide/intellihide state and driving `_animateOut(0, 0)` or equivalent internal hide logic instead of repeatedly fighting `_show()`
  - restore the dock actor's prior hover/autohide/intellihide state on blur, helper disable, or overlay loss, then hand control back to its normal `_updateVisibilityMode()` path
  - keep shell-chrome suppression idempotent: while promotion remains active, reapply panel/dock suppression instead of treating the first hide as final
  - preserve and restore previous visibility state rather than assuming the shell chrome should always come back visible
  - make `panel_hidden` / `dock_hidden` diagnostics truthful by requiring all targeted actors to be hidden before claiming success
  - keep the live diagnostics rich enough that the next GNOME-session test can distinguish "helper attempted suppression" from "all targeted shell chrome really disappeared"
  - keep non-GNOME backends unchanged and keep the current stacking/input seam intact
- Planned tests for this stage:
  - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_runtime.py -q`
  - manual GNOME-session validation is required because the shell-chrome actors live inside GNOME Shell and are not covered by the current headless test harness
- Behavior change required for this stage:
  - yes. This stage changes live GNOME shell actor visibility while the helper-backed presentation path is active.

#### Stage 5.5 Detailed Plan
- Objective:
  - Revalidate the GNOME helper path against the real user-facing promise and finalize the honest support policy.
  - End with either proof-backed support for borderless/windowed play or an explicit narrowed support statement.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - likely truthfulness/support surfaces if policy changes are required:
    - `overlay_client/backend/status.py`
    - `overlay_client/backend/selector.py`
    - `docs/FAQ.md`
    - `docs/troubleshooting.md`
    - `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- Planned validation matrix for this stage:
  - Elite Dangerous active and focused in borderless/windowed
  - Elite Dangerous active and focused in windowed if needed to separate borderless-specific vs generic active-window behavior
  - Elite Dangerous active and focused in fullscreen only as an optional extra-capability check, not as the primary support gate
  - helper enabled vs disabled fallback
  - supported GNOME Shell versions still in scope (`46`-`49`) as far as available evidence allows
- Planned tests/evidence for this stage:
  - manual GNOME-session validation is required
  - if code/state truthfulness changes are needed:
    - `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py overlay_client/tests/test_backend_selector.py -q`
- Exit criteria for this stage:
  - either record proof that the helper-backed path keeps the overlay above the active game in the declared supported play mode and restore the `true_overlay` signoff bar for GNOME
  - or explicitly narrow support/classification so GNOME support is not overstated, with borderless/windowed documented honestly if it remains limited or unsupported

### Phase 6: Live Validation And Support Policy
- Prove the helper works in a real GNOME session and document what is and is not supported.
- Record compatibility evidence for install, enable, runtime behavior, disable, uninstall, and fallback.
- Risks: shipping a helper path that only works in one narrow local setup while docs imply broader support.
- Mitigations: record exact GNOME Shell version, distro, install target, and observed backend status during validation.
- Current blocker:
  - Live `stage3.8` validation shows the helper-backed path can install, handshake, track the Elite window, and show the overlay window, but it does not yet keep that overlay above the active game in borderless/windowed-sized testing on GNOME Wayland.
  - Until Phase `5` either lands a real GNOME-managed presentation path or narrows the support claim honestly, Phase `6` can record current evidence but cannot treat GNOME borderless/windowed support as signed off for `true_overlay`.

| Stage | Description | Status |
| --- | --- | --- |
| 6.1 | Validate per-user install and enable flow in a real GNOME Wayland session | Completed |
| 6.2 | Validate runtime handshake, event flow, disable behavior, and uninstall fallback in a real GNOME Wayland session | Not Started |
| 6.3 | Record supported GNOME-version range, known limitations, and release-readiness evidence | Not Started |

#### Stage 6.1 Detailed Plan
- Objective:
  - Validate the first supported per-user GNOME helper install and enable workflow in a real GNOME Wayland session and record the exact environment evidence.
  - This stage is validation-only; it should not modify repo runtime code or broaden the supported workflow beyond the locked per-user manual-copy/manual-enable path.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - live-session validation targets outside the repo:
    - source payload: `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/`
    - install target: `~/.local/share/gnome-shell/extensions/edmc-modern-overlay@edmc.local/`
    - GNOME Shell CLI: `gnome-shell`, `gnome-extensions`
- Planned validation evidence for this stage:
  - record GNOME Shell version and session details (`XDG_SESSION_TYPE`, `XDG_CURRENT_DESKTOP`)
  - copy the helper payload into the per-user extension target
  - enable the extension through the supported CLI path or GNOME Extensions app
  - confirm GNOME reports the extension as installed and enabled
  - record whether the helper service appears to activate cleanly after enable
- Planned commands/evidence collection for this stage:
  - `gnome-shell --version`
  - `printf '%s\n' \"$XDG_SESSION_TYPE\" \"$XDG_CURRENT_DESKTOP\"`
  - `gnome-extensions info edmc-modern-overlay@edmc.local`
  - `gnome-extensions list --enabled`
- Behavior change required for this stage:
  - yes. This stage writes the extension payload into `~/.local/share/gnome-shell/extensions/` and enables it in the live GNOME session.
  - do not proceed with the live install/enable actions without explicit user approval for those environment changes.
- Unchanged behavior contract:
  - no repo code changes
  - no installer-script changes
  - no status-model or selector changes; this stage only records live install/enable evidence

#### Stage 6.2 Detailed Plan
- Objective:
  - Validate the live helper contract after enable: handshake shape, helper identity, and the first observable runtime event/fallback behavior in a real GNOME Wayland session.
  - Confirm that disabling the extension returns the product to the missing-helper fallback path, and keep uninstall validation scoped so it remains reversible and clearly recorded.
- Exact touch points for this stage:
  - `docs/refactoring/gnome_shell_extension_helper_plan.md`
  - live-session validation targets outside the repo:
    - `gnome-extensions`
    - `gdbus`
    - `dbus-monitor` or `gdbus monitor` if needed for signal evidence
  - reference-only runtime/status surfaces:
    - `overlay_client/backend/gnome_helper_runtime.py`
    - `overlay_client/backend/helper_ipc.py`
    - `overlay_client/backend/status.py`
- Planned validation evidence for this stage:
  - call `Hello(session_token)` against `org.edmc.EDMCModernOverlay.Helper` and record helper kind, protocol version, and helper version
  - observe at least one live helper signal or other direct runtime evidence that the helper is emitting the expected event surface after enable
  - disable the extension and confirm the helper service disappears and the product returns to the expected missing-helper fallback path on the next status refresh/restart
  - if uninstall is exercised in this stage, keep it per-user only and record the exact reinstall path used to restore the environment afterward
- Planned commands/evidence collection for this stage:
  - `gdbus call --session --dest org.edmc.EDMCModernOverlay --object-path /org/edmc/EDMCModernOverlay --method org.edmc.EDMCModernOverlay.Helper.Hello <session-token>`
  - `gdbus monitor --session --dest org.edmc.EDMCModernOverlay --object-path /org/edmc/EDMCModernOverlay`
  - `gnome-extensions disable edmc-modern-overlay@edmc.local`
  - `gnome-extensions info edmc-modern-overlay@edmc.local`
- Behavior change required for this stage:
  - yes. This stage disables the live GNOME extension and may temporarily uninstall/reinstall it if uninstall fallback is exercised.
  - do not proceed with disable or uninstall validation without explicit user approval for those live-session changes.
- Unchanged behavior contract:
  - no repo code changes
  - no installer-script changes
  - no selector/status-model edits; this stage only records live runtime and fallback evidence

## Execution Log
- Plan created on 2026-04-04.

### Phase 1 Execution Summary
- Stage `1.1` completed on 2026-04-04.
- Refined the stage before any code work so it reflects the actual repo state: there is no existing helper directory today, so Phase `2` will introduce the first helper payload under `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/`.
- Locked the minimum v1 file set as `metadata.json`, `extension.js`, and a helper-side `README.md`, while explicitly deferring `prefs.js`, `stylesheet.css`, and `schemas/*.gschema.xml` unless later stages prove a real need.
- Recorded this as a requirements-only stage with no runtime, selector, installer, or status-surface behavior changes.
- Stage `1.2` completed on 2026-04-04.
- Refined the stage before any helper payload work so the supported operator workflow is explicit: v1 uses per-user manual copy into `~/.local/share/gnome-shell/extensions/edmc-modern-overlay@edmc.local/`, supports both `gnome-extensions ...` CLI and GNOME Extensions app GUI enable/disable flows, treats disable-then-remove-directory as the supported uninstall rule for the manual-copy path, and keeps system-wide or script-managed install flows out of scope for the first milestone.
- Recorded a conservative upgrade rule for v1: disable, replace the directory contents, re-enable, then restart the Overlay Client if the helper does not reconnect live.
- Stage `1.3` completed on 2026-04-04.
- Refined the stage before any runtime helper wiring so the future status surface has a locked vocabulary: `missing_helper` covers absent/disabled/unapproved helper states, `incompatible_helper` covers present-but-unusable helper states such as protocol or D-Bus failures, and GNOME must not claim `true_overlay` until real-session evidence demonstrates the full helper-backed click-through, stacking, and tracking guarantees.
- Phase `1` is now complete: the UUID/layout, per-user operator workflow, and approval/status language are locked before any helper payload or runtime code is added.

### Tests Run For Phase 1
- Stage `1.1`: no tests run; doc-only stage with no code-path changes.
- Stage `1.2`: no tests run; doc-only stage with no code-path changes.
- Stage `1.3`: no tests run; doc-only stage with no code-path changes.

### Phase 2 Execution Summary
- Stage `2.1` completed on 2026-04-04.
- Added the first GNOME helper payload files under `helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/`: `metadata.json`, a no-op ESModule `extension.js`, and a helper-side `README.md`.
- Kept the stage inert on purpose: no D-Bus helper service, no client/runtime wiring, no selector/probe changes, and no installer changes landed here.
- Stage `2.2` completed on 2026-04-04.
- Replaced the no-op extension entrypoint with a helper-service bootstrap and added `service.js`, which now owns `org.edmc.EDMCModernOverlay` on the session bus, exports `/org/edmc/EDMCModernOverlay`, and implements a narrow `Hello(session_token)` handshake on `org.edmc.EDMCModernOverlay.Helper`.
- Kept the scope intentionally narrow: this stage does not add client-side discovery, backend selection changes, or any emitted helper event stream yet.
- Stage `2.3` completed on 2026-04-04.
- Refined the stage before editing so the plan now pins the exact helper-event surface: `Event(message_json)` on `org.edmc.EDMCModernOverlay.Helper`, JSON payloads aligned to the existing Python helper-boundary schema, GNOME-side focus tracking via display focus changes, and tracked-window geometry/lifecycle refreshes for the currently matched Elite Dangerous window.
- Updated `service.js` to emit `active_window_changed` and `window_geometry_changed` only after a successful `Hello(session_token)` handshake establishes a session token, while keeping client-side discovery/consumption out of scope for this phase.
- Updated the helper README and boundary unit test to document and pin the new event envelope without yet changing backend selection, probe status, or install flows.
- Phase `2` is now complete: the helper payload exists, owns its D-Bus name, performs the session-token handshake, and emits the first live GNOME-side event stream.

### Tests Run For Phase 2
- Stage `2.1`: `python3 -m json.tool helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/metadata.json >/dev/null` -> passed.
- Stage `2.2`: `python3 -m json.tool helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/metadata.json >/dev/null` -> passed.
- Stage `2.2`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py -q` -> passed (`8` passed).
- Stage `2.3`: `python3 -m json.tool helpers/gnome_shell_extension/edmc-modern-overlay@edmc.local/metadata.json >/dev/null` -> passed.
- Stage `2.3`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py -q` -> passed (`9` passed).

### Phase 3 Execution Summary
- Phase `3` was reopened on 2026-04-07 after live `stage3.7` validation showed a remaining helper-backed GNOME false-background/visibility-oscillation bug: the tracked Elite window stayed matched and visible, but the client still hid the overlay on the next follow tick because helper events reported `is_foreground=False`.
- Stage `3.1` completed on 2026-04-04.
- Refined the stage before editing so the new runtime GNOME helper evidence stays separate from the pure probe normalizer: a new `probe_gnome.py` runtime seam performs the lightweight session-D-Bus reachability check, while `collect_platform_probe(...)` now only normalizes explicit helper probe states into the stable probe payload.
- Extended the pure backend contracts to carry per-helper runtime evidence (`available`, `missing`, `incompatible`) without breaking the existing `available_helpers` compatibility surface, and updated selector/status reporting so GNOME can now distinguish `missing_helper` from `incompatible_helper`.
- Wired the runtime GNOME helper probe into the client/backend status callers without adding handshake or event consumption yet, keeping bundle/runtime cutover out of scope for this stage.
- Stage `3.2` completed on 2026-04-04.
- Refined the stage before editing so the new runtime seam stayed separate from bundle cutover: `gnome_helper_runtime.py` now owns the client-side session-D-Bus boundary, `Hello(session_token)` handshake, `Event(message_json)` subscription, and typed event queue, while bundles still remain unchanged until Stage `3.3`.
- Extended the helper IPC contract with a reusable GNOME helper boundary builder and stable GNOME helper endpoint constants, added a bundle-consumer helper for helper IPC runtimes, and exported the new runtime/backend types through the backend package surface.
- Added dedicated GNOME helper runtime tests for handshake validation, event parsing, fail-closed invalid-event handling, and helper-backend runtime creation without yet wiring the GNOME bundle to consume the runtime.
- Stage `3.3` completed on 2026-04-04.
- Refined the stage before editing so GNOME helper availability stayed under selector/status control rather than being hidden inside the bundle: `resolve_linux_bundle_from_status(...)` now chooses the helper-enabled GNOME bundle only for `compositor_helper / gnome_shell_wayland`, while native GNOME selections still use the trackerless fallback-preserving bundle.
- Replaced the helper-enabled GNOME bundle path with a real helper-backed tracker/runtime path: the GNOME bundle now attaches `GnomeShellHelperIpcBackend`, creates a `GnomeShellHelperTracker`, and consumes validated helper events to produce `WindowState` updates, while helper-disabled GNOME bundle paths remain intentionally trackerless.
- Added bundle/tracker tests that pin the two GNOME bundle modes explicitly: helper-enabled GNOME preserves the helper tracker with no XWayland fallback, and native/fallback GNOME keeps the existing XWayland tracker fallback behavior when the helper is not selected.
- Stage `3.4` completed on 2026-04-06.
- Refined the stage before editing so the fix stayed in the helper semantics rather than the visibility policy: helper-backed GNOME tracking now retains the last matched Elite window across focus transitions, reports `is_foreground` from real focus state, and only emits `matched: false` when no Elite match survives.
- Updated the GNOME Shell extension helper to prefer the focused Elite window, otherwise keep the currently tracked Elite window while it still exists, and only then fall back to scanning GNOME-managed windows for another surviving Elite match.
- Confirmed the Python runtime did not need extra behavioral changes for this fix because the existing same-identifier `active_window_changed` path already preserves geometry/state correctly once the helper stops emitting false disappearance events.
- Stage `3.5` completed on 2026-04-06.
- Refined the stage before editing so the fix stayed focused on the remaining helper-backed GNOME activation loop: the overlay now routes follow-surface and interaction-driven `raise_()` calls through an explicit platform policy seam instead of always raising itself when shown, repositioned, or refreshed.
- Added `PlatformController.should_raise_overlay_window()` and disabled explicit raising only for the helper-backed `compositor_helper / gnome_shell_wayland` path, keeping X11, XWayland, and non-helper Wayland behavior unchanged.
- Updated the setup/follow-surface wiring so visibility refresh, drag-state application, and geometry application all use the same raise policy, then added direct tests that prove helper-backed GNOME suppresses `raise_()` while other backends still allow it.
- Stage `3.6` completed on 2026-04-06.
- Refined the stage before editing so the fix stayed on the remaining forced-show path: `InteractionController` now preserves the current hidden/visible state while reapplying click-through flags instead of always calling `show()` on a hidden overlay.
- Added an explicit visibility-state seam to the interaction controller, wired the live window through it from setup, and kept the existing visible-path behavior intact so currently shown overlays still preserve their interactive/window-flag state.
- Added a regression test that proves hidden overlays no longer get forcibly re-shown during click-through reapplication, plus the required constructor/signature updates for the existing exception-scope coverage.
- Stage `3.7` completed on 2026-04-06.
- Refined the stage before editing so the next fix stayed helper-side: the game window was still being tracked, but live GNOME logs showed `foreground=False`, so the helper now prefers `MetaWindow`-native focus APIs such as `has_focus()` and `appears_focused` before falling back to display focus-window identity checks.
- Kept the helper event payload contract unchanged and bumped the helper version marker to `stage3.7` so live-session verification can prove GNOME has reloaded the new extension code.
- Existing Python-side GNOME helper runtime/boundary tests stayed green, while helper-side focus behavior still requires live GNOME-session validation because the repo has no direct automated Mutter/GJS test harness.
- Stage `3.8` completed on 2026-04-07.
- Refined the stage before editing so the fix stayed split cleanly between helper semantics and client observability: helper-backed GNOME now keeps a narrow foreground hold for the tracked Elite window across transient or ambiguous focus-loss reports, while the follow-controller now logs foreground/visible transitions even when identifier and geometry stay unchanged.
- Updated the GNOME Shell helper to retain the last known foreground result for a short debounce window before demoting the tracked Elite window to background, and bumped the helper version marker to `stage3.8` so live-session validation can prove GNOME has reloaded the new extension code.
- Added a pure follow-controller regression test surface that proves tracker-state logging now reacts to foreground-only changes while still suppressing duplicate logs for identical state.
- Phase `3` is now complete again: GNOME helper discovery, handshake/event intake, helper-backed runtime wiring, and the current foreground-stability fixes all exist behind the existing selector/status authority.

### Tests Run For Phase 3
- Stage `3.1`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_platform_probe.py overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_backend_contracts.py -q` -> passed (`36` passed).
- Stage `3.2`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_gnome_helper_runtime.py -q` -> passed (`46` passed).
- Stage `3.3`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_gnome_helper_runtime.py -q` -> passed (`49` passed).
- Stage `3.4`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_helper_ipc_boundary.py -q` -> passed (`17` passed).
- Stage `3.5`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_follow_surface_mixin.py -q` -> passed (`11` passed).
- Stage `3.6`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_exception_scoping.py -q` -> passed (`11` passed).
- Stage `3.7`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_helper_ipc_boundary.py -q` -> passed (`17` passed).
- Stage `3.8`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_follow_controller.py -q` -> passed (`10` passed).

### Phase 4 Execution Summary
- Stage `4.1` completed on 2026-04-04.
- Refined the stage before editing so the install guidance stayed minimal, per the current product direction: only the supported per-user target path, the copy step, and the two supported enable methods were added.
- Updated the helper README to reflect the actual repo state after Phase `3`: the helper now has client/runtime wiring, but it still awaits live GNOME-session validation and final support signoff.
- Stage `4.2` completed on 2026-04-04.
- Refined the stage before editing so it remained narrow: only the minimal supported disable/uninstall flow was added to the helper README, plus one concise fallback note tying disable/uninstall to `missing_helper` and protocol/runtime failures to `incompatible_helper`.
- Verified the existing backend-status/UI wording rather than adding new runtime behavior, because the current status layer already distinguishes missing-helper and incompatible-helper cases correctly.
- Stage `4.3` completed on 2026-04-04.
- Refined the stage before editing so it stayed doc-only: the helper README remains the authoritative operator workflow, while support-facing docs now explain the GNOME helper path at a high level without duplicating the full install/uninstall instructions.
- Updated the Wayland FAQ to remove the stale GNOME XWayland-only wording, point GNOME users at the helper README for the exact per-user workflow, and note that the Linux installer records helper approval but does not install or enable the extension automatically.
- Updated troubleshooting guidance with the current GNOME helper status vocabulary so `missing_helper`, `incompatible_helper`, and the disable/uninstall fallback path are user-comprehensible and reversible.
- Stage `4.4` completed on 2026-04-05.
- Refined the stage before editing so the new host-prerequisite path stayed post-approval and GNOME-specific: the generic Linux dependency bucket remains unchanged, while Debian/Ubuntu GNOME Wayland installs `python3-gi` only after GNOME helper approval and an explicit combined permission prompt.
- Updated the Linux installer to keep the existing generic host-package approval path intact, then add a GNOME-helper-specific follow-up path that can install `python3-gi` and rebuild `overlay_client/.venv` with `--system-site-packages` when the user approves it.
- Added Debian/Ubuntu GNOME-only probe/status honesty for this packaging gap: missing `gi` now records `host_prerequisite_missing:python3-gi`, and the backend warning tells the user to install the host package and rebuild `overlay_client/.venv` for GNOME helper support.
- Updated the installation FAQ so it no longer implies that `pydbus` alone is sufficient for Debian/Ubuntu GNOME helper support.
- Phase `4` is now complete: install/support docs are aligned, the GNOME helper host prerequisite is permission-gated, and missing-prerequisite status reporting is now explicit instead of ambiguous.

### Tests Run For Phase 4
- Stage `4.1`: no tests run; doc-only stage with no code-path changes.
- Stage `4.2`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py -q` -> passed (`8` passed).
- Stage `4.3`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_status.py tests/test_install_linux.py -q` -> passed (`20` passed).
- Stage `4.4`: `source .venv/bin/activate && python -m pytest tests/test_install_linux.py overlay_client/tests/test_probe_gnome.py overlay_client/tests/test_platform_probe.py overlay_client/tests/test_backend_status.py -q` -> passed (`30` passed).

### Phase 5 Execution Summary
- Stage `5.1` completed on 2026-04-07.
- Refined the stage before editing so the evidence surfaces match the actual code and logs: `window_controller.py` remains the pure visibility gate, `follow_surface.py` contains the current fullscreen-sized warning heuristic, `_linux_window_integration.py` shows that GNOME still uses the generic external-window Wayland presentation path, and `helper_ipc.py` confirms the current helper boundary is tracking-oriented rather than a presentation-control contract.
- Recorded the current live blocker explicitly: helper-backed GNOME is now a tracking/runtime success but an active-game stacking failure in borderless/windowed-sized testing, so GNOME must not be treated as `true_overlay` for its declared supported mode yet.
- Locked the interpretation rule that the current `follow_surface.py` fullscreen-sized warning is only a heuristic and must not be treated as proof that the failing play mode was exclusive fullscreen.
- Phase `5` is now in progress: the blocker is documented honestly and the next work moves to proving or disproving a GNOME-controlled presentation path instead of debating whether the current issue was “just fullscreen.”
- Stage `5.2` completed on 2026-04-07.
- Refined the stage before editing so the prototype stayed narrow: instead of introducing a new client-owned overlay-registration seam immediately, the helper now uses the fixed overlay title already set by the Qt launcher (`EDMC Modern Overlay`) to identify the external overlay window as a distinct GNOME `MetaWindow`.
- Extended the GNOME helper event boundary with a dedicated `presentation_state_changed` event and added a helper/runtime log surface so prototype evidence now shows whether the helper found the overlay window and attempted compositor-side promotion.
- Landed a helper-side prototype that tracks the external overlay window separately from the Elite window and applies GNOME-side window promotion only while the tracked game window is foreground/visible.
- Kept the tracker geometry/focus contract unchanged for non-presentation events: the new presentation event is observable in logs but does not drive tracker state yet, because Stage `5.2` is capability proof rather than the hardened shipping seam.
- Recorded live GNOME 46 crash evidence from the first prototype attempt: the helper found the overlay window and attempted promotion successfully enough to report `overlay_found=True` and `promotion_applied=True`, but `move_to_monitor()` on the external overlay `MetaWindow` triggered a Mutter abort. The Stage `5.2` prototype is therefore narrowed to non-migrating promotion only before any further live testing.
- Patched the Stage `5.2` prototype to remove workspace/monitor migration and keep only the non-migrating promotion path, then bumped the helper version marker to `stage5.2.1` so the next live test can verify the safer helper code is actually loaded.
- Manual GNOME-session validation is still required before choosing whether this prototype becomes the Stage `5.3` hardening path or negative evidence for a deeper helper-owned presentation model.
- Stage `5.3` completed on 2026-04-06.
- Refined the stage before editing so the fix stayed explicit and reversible: helper-owned GNOME click-through now uses a dedicated client-to-helper control call instead of trying to infer drag/interactivity state from tracking events.
- Extended the helper with `SetOverlayInputPassthrough(enabled) -> applied`, taught the GNOME helper to apply compositor-side actor reactivity changes to the promoted external overlay window, and enriched `presentation_state_changed` diagnostics with passthrough-requested/applied state.
- Added a small Python-side GNOME helper control client and wired the GNOME Wayland integration path to call it for both click-through enable and disable transitions, while keeping the current Qt/native click-through behavior as the fallback if helper control is unavailable.
- Follow-up hardening on 2026-04-06 narrowed the remaining shell-chrome issue: helper-backed GNOME now explicitly opts into `Qt.Tool` classification on Wayland so the promoted overlay is no longer presented as a normal application window on that backend, while other Wayland backends keep the previous `Tool=False` behavior.
- Kept non-GNOME backends unchanged and left tracker/geometry semantics intact; Stage `5.3` hardens the GNOME presentation/input seam chosen in Stage `5.2` without broadening helper tracking responsibilities.
- Stage `5.4` is in progress on 2026-04-06.
- Refined the stage before editing so the new fix stayed helper-owned and reversible: the remaining visible Ubuntu Dock/top-bar issue is shell chrome, not overlay stacking or input passthrough, so the helper now manages GNOME shell actor visibility only while the promoted overlay is active.
- Updated the helper to import GNOME Shell `Main`, hide the top panel/panel corners plus Ubuntu Dock actors (`dashtodockContainer`) while the helper-backed overlay is actively promoted, and restore the prior visibility state on blur, helper loss, or disable.
- Enriched `presentation_state_changed` diagnostics and the Python runtime log surface with `shell_chrome_hidden`, `panel_hidden`, and `dock_hidden` so the next live test can prove whether the helper is controlling shell chrome successfully.
- Follow-up hardening on 2026-04-06 corrected the live `stage5.4` failure mode instead of treating the first hide attempt as final:
  - helper version bumped to `stage5.4.1`
  - shell-chrome suppression is now re-applied while the promoted overlay remains active, because GNOME Shell and Ubuntu Dock can make the chrome visible again without a new window-geometry event
  - Ubuntu Dock actors still use the `dashtodockContainer` seam, but now prefer the dock actor's own `_hide()` / `_show()` methods when available before falling back to generic actor visibility
  - `panel_hidden` / `dock_hidden` diagnostics now require all targeted actors to be hidden before reporting success, fixing the earlier false-positive "any hidden actor" behavior
- Manual GNOME-session validation is still required before Stage `5.4` can be marked complete, because the shell-chrome actor behavior is not covered by the current headless test harness.

### Tests Run For Phase 5
- Stage `5.1`: no tests run; doc/evidence-only stage with no code-path changes.
- Stage `5.2`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_backend_consumers.py -q` -> passed (`46` passed).
- Stage `5.2` safety patch rerun: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_backend_consumers.py -q` -> passed (`46` passed).
- Stage `5.3`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_helper_ipc_boundary.py overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_gnome_helper_control.py overlay_client/tests/test_linux_window_integration.py -q` -> passed (`24` passed).
- Stage `5.3`: `source .venv/bin/activate && python -m ruff check overlay_client/backend/helper_ipc.py overlay_client/backend/gnome_helper_control.py overlay_client/backend/gnome_helper_runtime.py overlay_client/backend/bundles/_linux_window_integration.py overlay_client/tests/test_helper_ipc_boundary.py overlay_client/tests/test_gnome_helper_runtime.py overlay_client/tests/test_gnome_helper_control.py overlay_client/tests/test_linux_window_integration.py` -> passed.
- Stage `5.3` follow-up: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_exception_scoping.py overlay_client/tests/test_platform_controller_backend_status.py -q` -> passed (`18` passed).
- Stage `5.3` follow-up: `source .venv/bin/activate && python -m ruff check overlay_client/interaction_controller.py overlay_client/platform_integration.py overlay_client/setup_surface.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_exception_scoping.py overlay_client/tests/test_platform_controller_backend_status.py` -> passed.
- Stage `5.4`: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_runtime.py -q` -> passed (`10` passed).
- Stage `5.4`: `source .venv/bin/activate && python -m ruff check overlay_client/backend/gnome_helper_runtime.py overlay_client/tests/test_gnome_helper_runtime.py` -> passed.
- Stage `5.4` follow-up: `source .venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_runtime.py -q` -> passed (`10` passed).

### Phase 6 Execution Summary
- Stage `6.1` completed on 2026-04-04.
- Recorded live GNOME-session install/enable evidence on GNOME Shell `46.0` with `XDG_SESSION_TYPE=wayland` and `XDG_CURRENT_DESKTOP=ubuntu:GNOME`.
- Confirmed the helper is installed at `/home/jon/.local/share/gnome-shell/extensions/edmc-modern-overlay@edmc.local/`, visible to `gnome-extensions`, and enabled successfully in the live session.
- Confirmed the helper D-Bus service is live after enable: `org.edmc.EDMCModernOverlay` exports `/org/edmc/EDMCModernOverlay` with `org.edmc.EDMCModernOverlay.Helper`, `HelperKind='gnome_shell_extension'`, `ProtocolVersion=1`, and `HelperVersion='stage2.3'`.

### Tests Run For Phase 6
- Stage `6.1`: `gnome-shell --version` -> `GNOME Shell 46.0`.
- Stage `6.1`: `printf '%s\n' "$XDG_SESSION_TYPE" "$XDG_CURRENT_DESKTOP"` -> `wayland`, `ubuntu:GNOME`.
- Stage `6.1`: `gnome-extensions info edmc-modern-overlay@edmc.local` -> before enable: `Enabled: No`, `State: INITIALIZED`.
- Stage `6.1`: `gnome-extensions enable edmc-modern-overlay@edmc.local` -> succeeded with no error output in the live user shell.
- Stage `6.1`: `gnome-extensions info edmc-modern-overlay@edmc.local` -> after enable: `Enabled: Yes`, `State: ACTIVE`.
- Stage `6.1`: `gdbus introspect --session --dest org.edmc.EDMCModernOverlay --object-path /org/edmc/EDMCModernOverlay` -> succeeded; helper interface and properties present.
