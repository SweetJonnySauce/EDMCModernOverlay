# Cross-Platform Overlay Architecture Research

Research date: 2026-04-02

## Goal

Document external platform constraints and architectural patterns that matter for a true cross-platform overlay spanning Windows, X11, Wayland desktop environments, and compositor-specific integrations. This is a research note, not an implementation plan.

## Scope

- Summarize what the platform owners and protocol docs make possible.
- Distinguish true overlay paths from degraded fallback paths.
- Translate those findings into architecture guidance for EDMCModernOverlay.
- Record sources so later refactor planning can cite concrete platform constraints instead of tribal knowledge.

## Executive Summary

- There is no single Linux overlay backend. X11 and Wayland must be treated as different platforms, and Wayland itself must be split by capability and sometimes by compositor family.
- Qt can remain a rendering shell where useful, but it should not be the architecture boundary for platform behavior. Platform behavior needs explicit backends.
- On Wayland, a generic client can only provide a true overlay where the compositor exposes the required protocols. In other environments, a compositor-native helper or extension is required.
- GNOME and KDE should be treated as first-class compositor integrations, not as generic Wayland sessions with a few extra conditionals.
- Unsupported or sandboxed environments need a clearly defined fallback mode. Portals are a valid degraded path for capture and input brokering, but they are not a substitute for a compositor-backed always-on-top overlay.

## What "True Overlay" Means

For this project, an environment qualifies as `true_overlay` only if it passes every item in the checklist below for its declared supported play mode.

### True Overlay Checklist

| Check | Requirement |
| --- | --- |
| `visibility` | The overlay remains visible above the target app in the declared supported play mode. |
| `tracking_basic` | The overlay tracks the target window position and size correctly during normal moves, resizes, and focus changes. |
| `tracking_display_matrix` | The overlay tracks correctly across multiple monitor layouts, mixed resolutions, mixed DPI/scaling configurations, negative monitor origins, primary-monitor changes, and monitor offset changes. |
| `tracking_mode_changes` | The overlay remains correctly placed through supported borderless/fullscreen-windowed transitions and normal session changes relevant to that backend. |
| `input_policy` | Click-through, focus, drag, and other interaction rules behave as designed for that backend. |
| `presentation` | No major stacking, placement, or focus artifacts occur in the supported scenario. |
| `stability` | Behavior is repeatable across restart, reconnect, and normal environment changes without requiring ad hoc manual recovery. |
| `supportability` | Backend selection, capability state, and failure reasons are visible in logs and support diagnostics. |
| `no_undefined_hacks` | The result does not depend on undocumented global hacks that are known to vary unpredictably by compositor or window manager. |

### Checklist interpretation

- Failing any checklist item means the environment is not `true_overlay`.
- An environment that mostly works but fails one or more checklist items should be classified as `degraded_overlay`.
- An environment with no acceptable backend path should be classified as `unsupported`.

### Tracking-specific notes

The `tracking_display_matrix` requirement is intentionally strict. It exists because overlay failures often appear only in real desktop layouts rather than in single-monitor happy-path testing. At minimum, tracking validation should consider:

- single-monitor and multi-monitor layouts
- different monitor resolutions
- mixed DPI/scaling setups
- monitors positioned left/right/above/below each other
- negative coordinate spaces
- primary monitor changes
- compositor-specific coordinate normalization differences
- X11, XWayland, and native Wayland coordinate mismatches where applicable

If any of those guarantees cannot be met, the environment should be treated as a degraded or unsupported mode rather than silently claiming parity.

## Platform Findings

### 1. Wayland requires a compositor-first architecture

Wayland is a protocol family, not a single window server with a unified overlay story. The official Wayland site explicitly frames the user experience and window management model as compositor-defined rather than centrally owned in the way X11/Xorg historically was.

Implication for EDMCModernOverlay:

- "Linux" cannot be one runtime backend.
- Backend selection on Wayland must be capability-based and sometimes compositor-specific.
- Any architecture that assumes one shared follow/stacking/input model across all Wayland desktops will continue to accumulate special cases.

### 2. Generic Wayland overlays only work where layer-shell is available

The `wlr-layer-shell` protocol is the clearest generic path for an overlay surface that belongs to a desktop layer and can be anchored with explicit behavior. That makes it the strongest generic Wayland presentation path where supported.

Implication for EDMCModernOverlay:

- A generic Wayland client backend should be built around layer-shell capability detection, not around assumptions that a normal toplevel window can behave like an overlay everywhere.
- If layer-shell is absent, the client should not pretend it has the same guarantees.

### 3. Foreign-window tracking on Wayland is limited and sometimes privileged

The `ext-foreign-toplevel-list` protocol exposes foreign toplevel handles, but the protocol docs also allow compositor-side restriction, including cases where only a special client launched by the compositor can use it.

Implication for EDMCModernOverlay:

- Generic Wayland window tracking is not a safe universal assumption.
- A true follow-mode design on Wayland needs a separate discovery/tracking contract and a fallback path.
- Some compositors will require native helpers, shell extensions, or scripts for reliable target discovery and geometry updates.

### 4. GNOME should be treated as an extension-backed integration

GNOME Shell extensions run inside the shell environment and have access to GNOME Shell and Mutter APIs around windows, displays, and workspaces. That is materially different from what an ordinary external Wayland client can do.

Implication for EDMCModernOverlay:

- GNOME support should be designed as a dedicated backend with an extension-side helper and a narrow IPC contract to the shared overlay core.
- Trying to preserve GNOME support through generic client heuristics will likely keep producing fragile fixes.

### 5. KDE should be treated as a KWin-native integration

KWin scripting exposes workspace, window, geometry, PID, active state, stacking, and output information. That makes it a viable native integration surface for discovery and follow behavior.

Implication for EDMCModernOverlay:

- KDE Wayland support should have a KWin-specific backend or helper path.
- KWin behavior should not be encoded as special cases spread across launch environment building, tracker selection, and window flag logic.

### 6. X11 remains a separate but workable overlay platform

X11 still provides overlay-relevant primitives such as Shape extension support for non-rectangular windows and input regions. EWMH stacking hints exist, but they are hints, not absolute guarantees, and behavior depends on the window manager.

Implication for EDMCModernOverlay:

- X11 deserves its own backend rather than being treated as "legacy Linux."
- The X11 backend can support a real overlay model, but it still needs explicit handling for WM-dependent stacking behavior and graceful degradation.

### 7. Windows should use a native composition-oriented backend

Microsoft's composition guidance emphasizes the Visual layer and the composition stack for high-performance retained rendering. Qt window flags such as transparent-for-input are useful hints, but they are not a sufficient architecture boundary for robust Windows overlay behavior.

Implication for EDMCModernOverlay:

- Windows support should be defined as a native desktop backend with explicit presentation and input policy handling.
- The architecture should not assume that a single Qt window-flag strategy is the source of truth across all platforms.

### 8. Portals are a fallback mechanism, not a true overlay mechanism

XDG portals provide a supported path for screencast and remote-desktop style mediation in sandboxed or otherwise restricted environments. That is valuable for degraded behavior, but it does not create a compositor-level always-on-top overlay by itself.

Implication for EDMCModernOverlay:

- Portal support should be treated as a fallback mode with explicitly reduced guarantees.
- The fallback mode should be honest about what it can and cannot do.

### 9. X11 sessions are declining, but XWayland remains a live compatibility path

Major desktop environments are continuing to move away from full X11 desktop sessions. GNOME 49 disabled the dedicated X11 session by default and explicitly said apps depending on X11 remain supported through XWayland. GNOME's follow-up post clarified that the change targets the X11/Xorg session rather than XWayland itself. KDE announced that Plasma 6.8 will be Wayland-exclusive, while also saying X11 applications will continue to work through XWayland and that the Plasma X11 session will be supported into early 2027.

At the same time, the Wayland documentation still describes XWayland as crucial for Wayland adoption, and Qt 6.11 continues to document both `qwayland` and `qxcb` as supported platform plugins for Linux.

Implication for EDMCModernOverlay:

- The current Wayland -> XWayland -> Qt `qxcb` path is still a valid compatibility backend.
- It should be preserved during the refactor instead of being treated as dead code.
- It should not be treated as the strategic end-state for Wayland support.
- Planning should model it as a compatibility backend with weaker guarantees than native Wayland/compositor integrations, not as the universal Linux backend.

## Recommended Architecture

### Shared Overlay Core

Keep a single shared core that is platform-agnostic:

- payload model
- scene or render model
- layout and anchor engine
- geometry normalization rules
- state caches, profile data, and presentation policy
- transport between EDMC plugin, controller, and renderer

This layer should not know whether it is running on Windows, X11, GNOME Shell, KWin, or a fallback path.

### Backend Contracts

Define platform behavior through explicit contracts instead of scattering conditionals across launch, tracking, and rendering code:

- `PlatformProbe`
  - Detect session type, compositor family, protocol availability, sandbox state, and helper availability.
- `TargetDiscoveryBackend`
  - Discover target windows or surfaces and emit geometry/state updates.
- `PresentationBackend`
  - Own the actual overlay surface or native shell integration.
- `InputPolicyBackend`
  - Apply click-through, focus, and interaction policy appropriate to the platform.
- `CapturePolicyBackend`
  - Decide how capture exclusion or related behavior is handled where supported.
- `HelperIpcBackend`
  - Bridge to compositor-native helpers such as GNOME extensions or KWin scripts.

Each contract should be testable in isolation, with capability reporting that explains why a backend is supported, degraded, or unavailable.

### Concrete Backend Families

The research supports these backend families:

| Backend family | Primary environments | Notes |
| --- | --- | --- |
| `windows_desktop` | Windows desktop sessions | Native composition-oriented presentation backend. |
| `x11_desktop` | X11 sessions on Linux and similar environments | Uses X11 primitives directly, with WM-aware stacking behavior. |
| `xwayland_compat` | Wayland sessions intentionally using XWayland with Qt `qxcb` | Compatibility backend for existing X11-based behavior inside Wayland sessions. |
| `wayland_layer_shell_generic` | Wayland compositors exposing layer-shell with enough generic support | Best generic Wayland option where protocols exist. |
| `gnome_shell` | GNOME Shell / Mutter sessions | Requires extension-backed integration for reliable control. |
| `kwin` | KDE Plasma / KWin sessions | Best served by KWin script or effect integration. |
| `portal_fallback` | Restricted, sandboxed, or unsupported environments | Degraded mode, not parity mode. |

### Capability Probe Before Backend Selection

Backend selection should be based on explicit probes instead of a long chain of desktop-name checks:

1. Determine host family: Windows, X11, or Wayland.
2. On Wayland, detect protocol capability:
   - layer-shell
   - foreign-toplevel access
   - helper availability
   - sandbox restrictions
3. Detect compositor-native helper availability:
   - GNOME extension present and reachable
   - KWin script or effect present and reachable
4. Select the highest-capability backend.
5. If no true overlay path exists, surface degraded capability explicitly.

This keeps policy in one place and prevents launch-time environment code, runtime tracker code, and window-flag code from making separate platform decisions.

## Support Tiers

The cleanest support model is tiered:

### Tier 1: Native or protocol-backed true overlay

- Windows native backend
- X11 backend
- Wayland layer-shell backend on compositors where the necessary protocols are present and behave correctly

### Tier 2: Compositor-native integrations

- GNOME extension backend
- KWin backend

These are still first-class solutions, but they require helper deployment and version coordination.

### Tier 3: Degraded fallback

- Portal-backed or otherwise restricted mode

This tier should be explicit about reduced guarantees. It should not be used to hide the absence of a true overlay path.

### Transitional Compatibility Backend

- XWayland plus Qt `qxcb`

This path deserves explicit support in planning because it matches the current implementation reality on some Wayland systems. However, it should be treated as a compatibility track during migration, not as the destination architecture for Wayland.

## Repo-Specific Linux Planning Set

The current Linux installer and runtime do not describe exactly the same environment set. For planning purposes, the repo should treat the following Linux environments as explicit entries instead of relying only on the current installer compositor list.

### What the repo recognizes today

- The installer manifest currently defines compositor profiles for `kwin-wayland`, `gnome-shell`, and a combined `wlroots` bucket covering `sway`, `wayfire`, and `hyprland`.
- The runtime already distinguishes more cases than the installer profile list:
  - native X11
  - XWayland compatibility mode
  - Hyprland as a distinct tracker path
  - COSMIC as detected but not implemented

### Recommended Linux environment matrix for planning

| Environment | Current repo status | Planning status | Why it needs to be explicit |
| --- | --- | --- | --- |
| `native_x11` | Runtime path exists and is used as the X11 tracker fallback. | Include as explicit support target. | It is already a real backend path and should not be hidden behind generic Linux wording. |
| `xwayland_compat` | Runtime path exists via `force_xwayland` and Qt `qxcb`. | Include as explicit transitional compatibility backend. | This is part of the current Wayland story and must be preserved during migration. |
| `kwin_wayland` | Installer profile exists; runtime has KWin-specific tracking and click-through behavior. | Include as explicit support target. | The repo already treats KWin differently enough to justify a named backend. |
| `gnome_shell_wayland` | Installer profile exists; runtime logs that full follow/click-through needs the GNOME extension. | Include as explicit helper-backed environment. Do not assume Tier 1 without the extension path. | GNOME support is not equivalent to generic Wayland support in the current code. |
| `sway_wayfire_wlroots` | Installer profile exists; runtime has wlroots/layer-shell handling and sway-style tracking. | Include as explicit support target. | This is the strongest current generic Wayland-style path in the repo. |
| `hyprland` | Installer currently folds it into `wlroots`, but runtime has a dedicated tracker path. | Split out as its own planning entry. | The implementation already treats it as meaningfully different. |
| `cosmic` | Runtime detects it, but no backend is implemented. | Add to backlog/investigation list. | Detection means it is already part of the platform model whether or not support exists yet. |
| `gamescope` | No explicit detection or backend in the current repo. | Add to investigation list if SteamOS/Bazzite are important targets. | The installer already targets SteamOS/Bazzite distro families, so this environment is likely relevant even though it is not yet modeled. |
| `flatpak` | Repo already tracks Flatpak context. | Keep as an execution-context flag, not a backend. | Flatpak affects capabilities and packaging, but it is not itself a compositor/backend family. |

### Planning takeaway

For Linux planning, the minimum explicit set should be:

- `native_x11`
- `xwayland_compat`
- `kwin_wayland`
- `gnome_shell_wayland`
- `sway_wayfire_wlroots`
- `hyprland`

And the immediate backlog/investigation set should be:

- `cosmic`
- `gamescope`

The plan should also keep `flatpak` as a capability/context axis rather than turning it into another backend family.

## Classification And Downgrade Policy

The refactor plan may classify environments as:

- `true_overlay`
- `degraded_overlay`
- `unsupported`

However, classification is not allowed to become a silent downgrade mechanism for environments that already work in the current shipped plugin.

### Required rules

- Every non-`true_overlay` classification must include a concrete reason.
- Reasons should be technical and observable, not vague. Examples:
  - `missing_protocol`
  - `missing_helper`
  - `compositor_restriction`
  - `xwayland_compat_only`
  - `tracking_unavailable`
  - `click_through_unavailable`
  - `stacking_not_guaranteed`
  - `sandbox_restriction`
  - `not_implemented`
- For any environment already working in the current repo, moving it to `degraded_overlay` or `unsupported` requires explicit owner review and approval.
- No silent downgrades are allowed for the sake of architectural cleanliness alone.

### Required evidence for any proposed downgrade

If a future plan proposes downgrading an environment that already works today, it must document all of the following before that decision is valid:

- current shipped behavior
- proposed new classification
- exactly what guarantee is being removed or weakened
- the concrete reason for the downgrade
- whether the limitation is:
  - a real compositor/platform restriction
  - a missing helper/backend that has not been built yet
  - a temporary migration tradeoff
- whether owner review is required

### Planning takeaway

This means existing environments such as `gnome_shell_wayland` cannot be downgraded automatically just because the architecture would be simpler if they were treated as helper-only or degraded. If the refactor plan proposes a worse classification than current practical behavior, that change must be surfaced for review instead of being assumed.

## Migration Decision: Separate Linux Backend Tracks

For the refactor, Linux should not collapse into a single backend. The migration target should keep separate backend tracks for:

- `native_x11`
- `xwayland_compat`
- `native_wayland_*`

### Meaning of each track

- `native_x11`
  - X11 session backend using X11-native behavior and assumptions.
- `xwayland_compat`
  - X11-based compatibility backend running inside a Wayland session through XWayland and Qt `qxcb`.
- `native_wayland_*`
  - A family of native Wayland backends rather than one generic Linux path.

### Native Wayland backend family

The expected native Wayland family should include at least:

- `wayland_layer_shell_generic`
- `kwin_wayland`
- `gnome_shell_wayland`

Additional compositor-specific backends may be added later as needed.

### Planning takeaway

- `xwayland_compat` should remain a named backend during migration.
- It may share implementation with `native_x11`, but it should not share classification.
- Native Wayland should be modeled as multiple backends or backend bundles, not as one catch-all path.
- Any later decision to remove or demote `xwayland_compat` should happen only after replacement native Wayland backends are real, tested, and reviewed.

## Backend Selection Policy: Native First, Fallback Available

When a native Wayland backend exists for a supported compositor, it should be the default selected backend for that environment.

However, `xwayland_compat` must remain available as an explicit fallback during migration and stabilization.

### Rules

- Prefer the native Wayland backend by default when it is implemented and considered supported for that compositor.
- Keep `xwayland_compat` available as a selectable fallback for troubleshooting, regression recovery, and edge-case environments.
- Do not silently remove or hide `xwayland_compat` while native replacements are still being validated in real user environments.
- Selection logic must report which backend was chosen and why.
- Manual override must remain available so support and users can force `xwayland_compat` when needed.
- If a native Wayland backend fails capability checks or is explicitly classified below the required support bar for the current environment, the selector may fall back to `xwayland_compat` with a logged reason.

### Planning takeaway

The migration target is not "replace XWayland immediately." The migration target is "make native Wayland the preferred path where it is truly ready, while preserving XWayland as an operational fallback until it is no longer needed."

## First Refactor Milestone Policy: Extraction Without Behavior Changes

The first refactor milestone should be architectural only. Its job is to introduce the new seams and backend structure without intentionally changing runtime behavior.

### Rules

- Phase 1 should make no behavior changes unless a change is strictly required to complete the extraction safely.
- Existing backend selection behavior should be preserved as closely as possible during the first milestone.
- Architectural cleanup is not by itself a valid reason to change backend choice, support classification, or runtime behavior.
- If a behavior change is required to complete an extraction, that change must be surfaced for review rather than folded in silently.
- Any required behavior change must be documented with:
  - what behavior changes
  - why the extraction cannot proceed safely without it
  - what risk it reduces
  - what tests or evidence will validate it

### Planning takeaway

The first milestone should focus on introducing `PlatformProbe`, backend contracts, and explicit backend tracks while keeping the current practical behavior intact. Backend selection improvements and policy changes belong in later milestones unless an extraction is blocked without them.

## Architecture Decision: Separate Contracts With Backend Bundles

The refactor should use separate contracts for major platform concerns, with per-environment backend bundles composed from those parts.

### Required contracts

- `PlatformProbe`
- `TargetDiscoveryBackend`
- `PresentationBackend`
- `InputPolicyBackend`
- `HelperIpcBackend`

### Composition model

Each supported environment should be represented as a backend bundle assembled from concrete implementations of the contracts above rather than from a single large environment object that owns every concern.

### Why this is the chosen direction

- It prevents recreating the current spaghetti architecture in a new location.
- Discovery, presentation, input policy, and helper IPC evolve at different rates and need different tests.
- Some environments may share one contract implementation without sharing the entire backend.
- It creates clearer test seams and better migration boundaries.

### Planning takeaway

- Use separate contracts as the stable architecture boundary.
- Use backend bundles as the environment-specific assembly layer.
- Avoid introducing one giant backend class per environment that mixes selection, discovery, presentation, and helper logic together.

## Authority Policy: Client Final, Plugin Advisory

The overlay client is the final authority for local platform, compositor, and capability detection.

The plugin may detect and pass launch-time hints, preferences, and user overrides, but those inputs are advisory rather than authoritative.

### Rules

- The plugin may provide:
  - session/compositor hints
  - user preferences
  - forced backend overrides
  - launch context metadata
- The client must perform the final local capability probe in its own runtime environment.
- Backend selection must be finalized in the client, not split across plugin and client.
- The client must publish its final probe result, selected backend, and downgrade/fallback reasons in a form visible to the plugin, controller, and support diagnostics.
- If plugin hints and client probe results differ, the client result wins, and the mismatch should be logged.

### Main tradeoff

This centralizes platform truth in the correct runtime process, but it requires an explicit reporting path back out of the client.

In other words:

- upside: one source of truth, fewer split-brain decisions, cleaner backend selection
- cost: the client must report final detection and selection results back to the rest of the system

### Planning takeaway

The plugin should remain the control plane for launch, configuration, and orchestration. The client should own final environment detection and backend selection.

That is the crisp tradeoff:

- either tolerate duplicate or inconsistent platform decisions
- or accept that the client must become the authority and report its decision outward

## Selection Authority Policy: One Selector, No Secondary Selection

Backend selection must happen in one place only.

A single selector is responsible for:

- evaluating the final capability probe
- applying overrides and fallback rules
- choosing the backend bundle
- recording the reason for the selection

All other layers must consume the selected backend decision rather than performing their own platform or backend selection.

### Rules

- Only the selector may choose or change the active backend.
- Tracking, presentation, input policy, helper IPC, and launch/runtime wiring must use the selected backend bundle rather than inferring their own backend from environment variables, compositor names, or ad hoc conditions.
- Plugin-side launch context may provide hints and overrides, but it must not finalize backend choice independently of the selector.
- If a fallback is used, the selector must record:
  - selected backend
  - fallback source backend
  - reason for fallback
- Secondary selection logic in other layers is not allowed.

### Main purpose

This prevents platform policy from being spread across:

- plugin launch environment construction
- runtime platform integration
- target tracking selection
- follow/window behavior

### Planning takeaway

The architecture should have one backend selector and many backend consumers. If a code path needs to know "what platform or backend am I on?", it should ask for the selector's result, not re-decide it locally.

## Helper-Backed Integration Policy: Selective, With User Approval

The product may ship compositor-native helper-backed integrations where they are the only credible path to the required overlay guarantees.

These helper-backed integrations may include separate modules or components such as:

- GNOME Shell extensions
- KWin scripts or effects
- compositor-specific helper services or scripts

### Rules

- Helper-backed integrations are allowed selectively, not by default for every environment.
- A helper-backed integration should be introduced only when a generic external-client path cannot credibly meet the required support bar.
- Helper-backed integrations are part of the product architecture even when they are installed into a compositor-specific extension or script system.
- Installation or enablement of a helper-backed integration must require user approval.
- The product must not silently install, enable, or upgrade compositor-native helpers behind the user's back.
- If a helper is available but not installed or enabled, the selector should classify the environment accordingly and report the missing-helper reason.

### User approval requirement

If a backend depends on a compositor-native helper, the user must be told:

- what helper will be installed or enabled
- why it is needed
- what capability it unlocks
- what environment it applies to

The user must then be able to approve or decline that installation or enablement.

### Planning takeaway

The architecture may rely on compositor-native helpers where needed, but helper deployment must remain explicit and user-approved rather than automatic.

## Helper Friction Policy: Moderate, Review Case By Case

Moderate installation and update friction is acceptable for compositor-native helpers when that friction is necessary to unlock required overlay capability.

However, acceptable friction is situational and must be reviewed in the context of the specific helper, environment, and user impact.

### Rules

- Helper-backed integrations may require moderate friction when there is a clear capability benefit.
- Acceptable friction may include:
  - separate installation steps
  - explicit enablement inside the compositor environment
  - extra runtime dependencies
  - version checks and mismatch handling
  - explicit user-approved updates
- Friction must be reviewed case by case rather than assumed acceptable in the abstract.
- Existing friction already present in the product, such as DBus-related requirements for some environments, should be treated as part of the baseline operational reality rather than as a reason to avoid all helper-backed designs.
- Helper lifecycle operations must remain explicit, understandable, and reversible.
- If helper friction becomes too high for a given environment, that environment's support strategy should be reviewed rather than hidden.

### Review criteria

When evaluating whether a helper's friction is acceptable, review at least:

- what capability it unlocks
- which environment it applies to
- what the install or enablement path requires
- what ongoing update burden it adds
- what failure modes the user may encounter
- whether the behavior degrades cleanly if the helper is missing or disabled

### Planning takeaway

The project is willing to accept moderate helper friction where justified, but helper deployment is not automatically acceptable just because it is technically possible. Each helper-backed integration should be reviewed in terms of concrete user and support cost.

## Generic Wayland Policy: Capability-Gated, Not Best-Effort

The generic native Wayland backend must be capability-gated.

It is not a catch-all backend for every Wayland compositor. It should only be selected when the compositor exposes the capabilities required for the declared support level.

### Rules

- `wayland_layer_shell_generic` is only valid for compositors that meet the required generic capability bar.
- If the required generic Wayland capabilities are not present, the selector must not pretend the generic backend is equivalent.
- In those environments, the selector must instead choose one of:
  - a compositor-specific backend
  - `xwayland_compat`
  - `degraded_overlay`
  - `unsupported`
- Generic Wayland support must be defined by explicit capability checks, not by broad "Wayland session detected" logic.
- Best-effort native Wayland attempts that blur support boundaries are not the target architecture.

### Compatibility clarification

This policy does not require removing compatibility that exists today.

What it means is:

- stop treating broad best-effort behavior as if it were one generic native Wayland backend
- preserve existing practical compatibility through explicit backends or fallbacks
- do not remove or downgrade currently working behavior without review

In other words, capability-gating the generic Wayland backend is not the same as dropping the current fallback paths. Existing compatibility may continue through:

- `xwayland_compat`
- compositor-specific backends
- reviewed degraded paths where appropriate

### Main purpose

This prevents the project from using "generic Wayland" as a vague compatibility bucket for environments that actually require compositor-specific handling or fallback behavior.

### Planning takeaway

The generic Wayland backend should mean "protocol-backed generic support where the capability bar is met," not "try something native on every Wayland compositor and hope it works." Adopting this policy should not silently reduce current compatibility; it should reclassify and preserve current behavior through explicit backend and fallback decisions.

## Capability Visibility Policy: Quiet by Default, Inspectable On Demand

Backend capability and selection state must be visible to users and support tooling.

The visibility model should be layered so normal operation stays quiet, while degraded or fallback states are clear and actionable.

### Visibility layers

#### 1. Always-visible status

The controller and/or plugin preferences UI should expose a compact status summary showing at least:

- selected backend
- support classification
- concise reason when not `true_overlay`

Example fields:

- `Backend: KWin Wayland`
- `Mode: true_overlay`
- `Mode: degraded_overlay`
- `Reason: missing_helper`

#### 2. Conditional user-facing warnings

The product should surface a user-facing warning only when the state is actionable or materially different from the ideal path.

Warnings should be shown for cases such as:

- `degraded_overlay`
- `unsupported`
- fallback to `xwayland_compat`
- missing required helper
- active manual override

Warnings should be informative rather than noisy, and should not repeat unnecessarily during normal use.

#### 3. Full diagnostics view

A support/details surface should expose the full backend and capability state, including:

- detected session type
- detected compositor
- selected backend
- support classification
- fallback source and reason
- missing protocol/helper reasons
- manual override state
- helper installed/enabled state where applicable
- key capability probe results

### Logging and support output

The same capability state should be reflected in logs and support diagnostics so support workflows do not depend on reproducing UI state manually.

### Noise policy

- `true_overlay`: quiet status only
- `degraded_overlay`: visible warning plus details
- `unsupported`: visible error state plus details
- `manual override`: visible note that backend selection was forced

### Planning takeaway

Capability and backend selection must not be hidden internal state. They should be quiet during healthy operation, obvious when degraded, and fully inspectable when troubleshooting.

## Manual Override Policy: Allowed for Troubleshooting, Visible By Design

Users and support should be able to force backend selection manually for troubleshooting and regression isolation.

Manual override is an escape hatch, not the default operating mode.

### Rules

- A manual backend override must be available.
- The override must be explicit and easy to clear.
- The current override state must be visible in status and diagnostics.
- A forced backend does not change the truth of capability classification; it only changes the selected path.
- If a forced backend is invalid for the current environment, the system must report that clearly rather than failing silently.
- Manual override should be used for troubleshooting, regression recovery, comparison testing, and support workflows.
- Manual override must not become a hidden substitute for proper automatic backend selection.

### User-facing behavior

The UI or configuration surface should expose at least:

- `Auto`
- valid backend choices relevant to the current platform family
- clear indication when a backend is being forced

### Planning takeaway

Automatic selection remains the normal path, but the architecture must preserve a visible, user-clearable manual override for debugging and support.

## Support Language Policy: Stable Family Labels Plus Specific Backend Instances

Support and diagnostic language should explicitly distinguish the major backend families instead of collapsing them into broad labels such as "Wayland" or "Linux."

### Stable support vocabulary

The stable support-family labels should include at least:

- `native_x11`
- `xwayland_compat`
- `native_wayland`
- `compositor_helper`
- `portal_fallback`

### Instance naming

Support-family labels should be paired with a specific backend instance where possible.

Examples:

- `native_wayland / kwin_wayland`
- `native_wayland / wayland_layer_shell_generic`
- `compositor_helper / gnome_shell_wayland`
- `xwayland_compat / xwayland_compat`

### Rules

- Support output, diagnostics, and developer discussions should use the stable support-family label plus the specific backend instance when available.
- User-facing UI may use friendlier display names, but support diagnostics should retain the precise labels.
- The project should avoid using broad terms such as "Wayland support" when a more precise backend family or instance is known.

### Planning takeaway

The architecture should expose both:

- a stable backend family label for support vocabulary
- a specific backend instance name for precise diagnostics

This keeps support language consistent without losing technical specificity.

## Testing Policy: Backend Contracts And Capability Matrix Are Required

The refactor must add backend contract tests and a capability-matrix test harness.

These are not optional cleanup items. They are required to keep backend selection, capability classification, and fallback behavior from drifting back into ad hoc platform logic.

### Required test layers

#### 1. Capability-matrix tests

Tests must cover selector behavior across synthetic environment combinations, including:

- platform family
- session type
- compositor identity
- helper availability
- protocol availability
- manual override state
- expected backend selection
- expected classification
- expected fallback reason

#### 2. Backend contract tests

Tests must verify that backend bundles and their component contracts behave as expected, including:

- `PlatformProbe`
- `TargetDiscoveryBackend`
- `PresentationBackend`
- `InputPolicyBackend`
- `HelperIpcBackend`

#### 3. Existing project test layers

This refactor should continue using:

- unit tests for pure logic
- harness tests for plugin/runtime wiring
- targeted integration-style tests where runtime behavior must be proven

### Harness ownership and immutability

The repo already vendors part of its harness infrastructure from the BGS-Tally test harness snapshot. That distinction must remain explicit in planning.

Immutable vendored upstream harness snapshot:

- `tests/harness.py`
- `tests/edmc/**`

Local project-owned integration layer and fixtures:

- `tests/harness_bootstrap.py`
- `tests/harness_fixtures.py`
- `tests/overlay_adapter.py`
- `tests/config/**`
- project-owned harness test files under `tests/test_harness_*.py`

Rules for this refactor:

- Do not edit immutable vendored harness files as part of normal refactor work.
- If the vendored snapshot truly needs to change, refresh it intentionally from upstream rather than patching it ad hoc.
- Project-specific test scaffolding, adapters, fixtures, and harness-facing tests should be built in the local integration layer around the vendored snapshot.
- New backend contract and capability-matrix coverage should be added in project-owned test surfaces, not by mutating the vendored harness core.

### Scope and rollout

- The test scaffolding should be introduced in stages rather than as one giant framework effort.
- Early milestones should prioritize:
  - selector tests
  - capability classification tests
  - fallback-policy tests
- Additional backend contract coverage should be added as backend extraction lands.
- Test framework work must support the architecture effort, not become a separate refactor project.

### Planning takeaway

This architecture only works if backend selection and capability classification are testable at the contract level. Backend contract tests and capability-matrix coverage are therefore mandatory parts of the refactor, not follow-up nice-to-haves. The existing vendored harness snapshot should be treated as immutable core infrastructure, with new project-specific testing built around it rather than inside it.

## Current Manual Verification Coverage

Support claims and rollout order should reflect the environments that are actually available for manual verification.

### First-party verification currently available

- `windows_desktop`
- `gnome_x11`
- `gnome_wayland`

### User-assisted verification currently available

- `fedora / kde_wayland`

This environment is not currently first-party verified by the maintainer, but there are users available to help validate behavior on that stack.

### Planning takeaway

- First-party support confidence should be strongest on the environments available for direct manual verification.
- Environments validated primarily through user feedback should still be planned for, but rollout and support claims should account for the weaker direct test loop.
- If future support commitments expand, this section should be updated so planning and release decisions stay aligned with actual verification coverage.

## Prioritization Policy: Short-Term Stabilization First, Long-Term Cleanup Still Required

When short-term stabilization and long-term architectural cleanup are in tension, the refactor should prioritize short-term stabilization first.

However, long-term architectural cleanup remains a required outcome of the overall effort, not an optional aspiration.

### Rules

- Phase ordering should favor behavior stability and compatibility preservation during migration.
- The refactor must not take architecturally cleaner paths that create unnecessary short-term regressions in currently working environments.
- Existing compatibility and support behavior should be preserved unless a reviewed change is required.
- Short-term stabilization is a sequencing rule, not permission to stop at partial cleanup.
- The plan must still drive toward the target architecture:
  - explicit backend contracts
  - single backend selector
  - capability-based classification
  - separated backend tracks
  - reduced cross-layer platform logic
- If a short-term stabilization choice creates temporary architectural debt, that debt should be documented and scheduled for follow-up removal.

### Planning takeaway

The migration should proceed in a way that keeps the shipped product stable, but each phase must still move the codebase measurably toward the long-term backend architecture. Stability comes first in the sequence; cleanup remains mandatory in the destination.

## Documentation Preservation Policy: Archive, Do Not Delete

When documents are superseded during this refactor, they should be archived rather than deleted.

### Rules

- Old or superseded planning and architecture documents should be moved into `docs/archive/`.
- Superseded documents should not be deleted unless there is a separate explicit decision to remove them.
- Archived documents should remain available for historical context, comparison, and rollback of planning decisions.
- New documents should link forward where appropriate, and archived documents may be annotated as superseded.

### Planning takeaway

The refactor should preserve document history. Replace active documents where needed, but move the old versions into `docs/archive/` instead of removing them.

## Controller Boundary Policy: Keep the Tk Controller As Is

The separate Tk controller remains part of the product architecture and is not a refactor target for this backend-architecture effort.

### Rules

- The Tk controller should remain in place as-is during this refactor.
- The refactor must not redesign, replace, or substantially restructure the controller as part of the backend architecture work.
- The controller should be treated as a stable control-plane boundary.
- The controller may consume new backend and capability status produced by the client, but it should not become a decision-making authority for backend selection.
- Controller changes should be limited to the minimum needed to display or pass through new backend/capability information.
- If controller changes beyond that minimum appear necessary, they should be surfaced explicitly rather than folded into this refactor.

### Planning takeaway

The backend-architecture effort should focus on plugin, client, and backend seams. The Tk controller stays in place and is not part of the primary refactor scope.

## Helper Communication Policy: Direct to Client, With a Narrow Trusted Boundary

Compositor-native helpers should communicate directly with the overlay client for runtime backend behavior.

The plugin remains the control plane for launch, approval, configuration, and diagnostics, but it should not sit in the middle of runtime helper communication.

### Rules

- Runtime helper communication should be `helper -> client` direct.
- The plugin may participate in installation, approval, configuration, and status reporting, but it should not act as the transport hub for compositor-specific runtime events.
- The client must own the local communication boundary used by helpers.
- That boundary must be treated as a narrow trusted surface and secured accordingly.

### Security requirements

- Communication must be local-only.
- Prefer local transports such as:
  - Unix domain sockets in the user session runtime directory
  - session-scoped DBus where appropriate
- Avoid broader transports such as localhost TCP unless there is a strong reason and equivalent local-only controls are enforced.
- The client must validate helper identity or session ownership before accepting runtime messages.
- The protocol must be narrow and schema-validated.
- The allowed operation set must be minimal and specific to runtime backend behavior.
- The client must reject malformed, oversized, unexpected, or version-incompatible messages.
- The communication layer should include version negotiation or protocol-version checks.
- Failure to authenticate or validate helper communication must fail closed.
- Helper status, version mismatch, and communication failure should be visible in diagnostics.

### Risk model

The main security concern is not just the transport itself. The bigger concern is that compositor-native helpers may run inside more trusted desktop or compositor contexts.

Because of that:

- helpers should remain minimal
- helpers should expose the smallest possible runtime surface
- helpers should avoid becoming general-purpose command channels

### Planning takeaway

Direct helper-to-client communication is the preferred runtime architecture, but only if it is implemented as a deliberately small, validated, local trusted boundary rather than as an open local command channel.

## Implications For The Current EDMCModernOverlay Codebase

### 1. Stop spreading platform policy across multiple layers

Current behavior is split across:

- plugin-side environment construction
- client-side platform integration
- tracker backend selection
- follow-surface and window-flag behavior

That should collapse into one authoritative capability probe plus explicit backend instances.

### 2. Keep the plugin as control plane, not platform policy owner

The EDMC plugin should remain responsible for EDMC lifecycle, settings, orchestration, and process launch. It should not be the long-term owner of compositor-specific follow and presentation policy.

Recommended split:

- plugin provides launch context and user preferences
- client performs local capability probe
- selected backend reports capabilities and reasons
- plugin and controller consume those results for UX and support diagnostics

### 3. Treat Qt as an implementation detail where appropriate

Qt can still host rendering and local windowing for backends where it fits, but the architecture should not assume that Qt-level window flags are the stable abstraction for every OS and compositor.

### 4. Model true overlay vs fallback as an explicit product distinction

The architecture should expose at least these modes:

- `true_overlay`
- `degraded_overlay`
- `unsupported`

That is more honest and easier to debug than accumulating hidden compatibility branches.

### 5. Build tests around contracts, not helper fragments

The future test matrix should focus on backend contracts:

- unit tests for probe logic, capability ranking, and policy decisions
- unit tests for pure geometry normalization and layout behavior
- harness tests for plugin wiring and launch context
- backend contract tests for target discovery, presentation, and input semantics

This is a better fit than only testing small helper functions while the cross-platform behavior remains implicit.

### 6. Keep XWayland compatibility explicit in the migration plan

The refactor plan should preserve the current XWayland-backed path as a named backend while native Wayland and compositor-specific backends are introduced. Removing it too early would create avoidable regressions on systems where it is still the only viable path.

Recommended planning stance:

- keep `xwayland_compat` working during early backend extraction
- classify it separately from native X11 and native Wayland backends
- document its weaker guarantees in support output and troubleshooting
- only demote or remove it after replacement backends are real, tested, and shipped

## Recommended Decision Record For Planning

Before implementation work begins, the refactor plan should answer these questions explicitly:

1. Is the client the final authority on local compositor capability, with the plugin only passing hints?
2. Which backend families are officially supported in the near term?
3. Will GNOME and KWin be treated as helper-backed integrations from the start, or staged in after a generic Wayland split?
4. What are the minimum guarantees required before calling a backend `true_overlay`?
5. What telemetry or debug reporting is required so support can see probe results, backend selection, and degraded reasons?

## Source Matrix

All observations below were checked on 2026-04-02.

| Source | Why it matters | Architectural takeaway |
| --- | --- | --- |
| [Wayland official site](https://wayland.freedesktop.org/) | Establishes that Wayland is compositor-defined rather than one shared window server model. | Wayland must be treated as a compositor-first platform family. |
| [wlr-layer-shell protocol](https://wayland.app/protocols/wlr-layer-shell-unstable-v1) | Documents a desktop-layer overlay surface model. | Generic Wayland overlay support should be built around capability detection for layer-shell. |
| [ext-foreign-toplevel-list protocol](https://wayland.app/protocols/ext-foreign-toplevel-list-v1) | Documents foreign toplevel discovery and notes compositor restriction possibilities. | Generic Wayland follow-mode cannot assume universal access. |
| [GNOME Shell extension architecture](https://gjs.guide/extensions/overview/architecture.html) | Shows that extensions run inside GNOME Shell with access to shell and Mutter APIs. | GNOME should use an extension-backed backend. |
| [KWin scripting API](https://develop.kde.org/docs/plasma/kwin/api/) | Exposes window/workspace/output information for KWin-native behavior. | KDE should use a KWin-native backend or helper path. |
| [X11 Shape library docs](https://www.x.org/releases/X11R7.7/doc/libXext/shapelib.html) | Documents shape and input-shape capabilities. | X11 can support real overlay primitives directly. |
| [X Shape protocol docs](https://www.x.org/releases/X11R7.7/doc/xextproto/shape.html) | Protocol-level details for shaped windows and bounding/input regions. | Reinforces that X11 overlay/input behavior should be implemented natively in its own backend. |
| [EWMH window state spec](https://specifications.freedesktop.org/wm-spec/latest/ar01s05.html) | Describes stacking states such as above/below as WM hints. | X11 stacking behavior is workable but not absolute. |
| [Windows Visual layer documentation](https://learn.microsoft.com/en-us/windows/apps/develop/composition/visual-layer) | Composition guidance for high-performance Windows presentation. | Windows should have a native composition-oriented presentation backend. |
| [Qt window flag documentation](https://doc.qt.io/archives/qt-6.9/qt.html) | Documents transparent-for-input and related flags as window-system hints. | Qt flags are useful tools, but not a complete cross-platform architecture. |
| [XDG ScreenCast portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html) | Provides mediated capture for restricted environments. | Portals support fallback behavior, not a true compositor overlay. |
| [XDG RemoteDesktop portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html) | Provides mediated input/device brokering in supported cases. | Portal-assisted interaction is a fallback capability. |
| [XDG window identifier notes](https://flatpak.github.io/xdg-desktop-portal/docs/window-identifiers.html) | Documents platform-specific window identifier handling for portals. | Reinforces that portal integration is environment-dependent and separate from native overlay control. |
| [GNOME 49 developer notes](https://release.gnome.org/49/developers/) | Documents that the dedicated X11 session is disabled by default while X11 apps remain supported through XWayland. | Full X11 sessions are fading, but XWayland remains part of the compatibility story. |
| [GNOME X11 session removal update](https://blogs.gnome.org/alatiera/2025/06/08/the-x11-session-removal/) | Clarifies that the GNOME change targets the X11/Xorg session rather than XWayland. | Planning should not confuse X11 session removal with XWayland removal. |
| [KDE Wayland future announcement](https://blogs.kde.org/2025/11/26/going-all-in-on-a-wayland-future/) | States that Plasma is moving to a Wayland-exclusive session while retaining XWayland for X11 app support. | Reinforces XWayland as a compatibility layer, not the long-term desktop session target. |
| [Wayland X11 application support](https://wayland.freedesktop.org/docs/book/Xwayland.html) | Describes XWayland as crucial for Wayland adoption and notes it will not fully match a native X server. | XWayland is important to keep, but it should be modeled as a compatibility backend with known limits. |
| [Qt for Linux requirements](https://doc.qt.io/qt-6/linux-requirements.html) | Shows that Qt still documents X11/XCB requirements on Linux. | Qt's `qxcb` path remains supported and should not be treated as already removed upstream. |

## Bottom Line

The strongest long-term architecture is not a single universal overlay window. It is a shared overlay core with multiple presentation and discovery backends, plus compositor-native integrations where Wayland requires them. That plan should explicitly retain XWayland plus Qt `qxcb` as a compatibility backend during migration, while avoiding the mistake of treating that compatibility path as the final architecture for Wayland support. Any plan that continues to treat platform behavior as a collection of distributed conditionals will keep recreating the same class of bugs.
