# Requirements Clarification: fix219 Architecture Convergence

## Question 1: Meaning of GNOME support

What exact environment scope must pass before this project can declare GNOME supported?

Possible dimensions include GNOME Shell versions, Linux distributions, native Wayland versus native X11 sessions, XWayland compatibility, multi-monitor layouts, fractional scaling, and Elite display modes.

### Answer

GNOME support targets GNOME Shell 46 and newer. The extension metadata explicitly supports GNOME Shell 46, 47, 48, 49, and 50; newer versions may be added after reviewing the relevant GNOME porting guide and completing smoke validation. Release claims must distinguish the 46+ target policy from the exact versions validated for a release.

The initial required distribution is Ubuntu 24.04.4 LTS. Both native Wayland and native X11 sessions are in the primary support scope. XWayland compatibility should remain supported as a distinct compatibility path, but it is not a priority and is not part of the primary GNOME acceptance gate.

Supported Elite display modes are borderless fullscreen and windowed. The acceptance matrix must include multiple monitors and screen scaling. Exclusive fullscreen is not included.

Repository source for the existing version decision: `docs/refactoring/gnome_wayland_helper.md`, Q9 and “Closed Question: Q9 GNOME Shell Version And Distro Support.”

## Question 2: Relationship to fix219 closure

Should this project include both architectural convergence and the unfinished `fix219` Phase 5 validation/compliance/signoff work, or should Phase 5 closure remain a separate project that this design only references?

### Answer

The unfinished `fix219` follow-up Phase 5 is superseded and is not part of this project. Do not use its existing validation/compliance/signoff stages as the acceptance structure for the convergence work.

This project focuses on architectural convergence. The PDD design and implementation plan must include a new validation phase built around the converged runtime architecture, the defined GNOME support matrix, behavior-preservation requirements, EDMC lifecycle constraints, and truthful support claims.

The historical Phase 5 record may remain available as context, but completion of this project must not depend on closing or preserving that phase structure.

## Question 3: GNOME X11 backend identity

Should GNOME on native X11 remain an environment validated through the shared `native_x11` backend, with GNOME-specific X11 behavior added only if testing proves it necessary, or should the converged architecture introduce a dedicated GNOME/X11 backend identity from the outset?

### Answer

GNOME on native X11 remains the `native_x11` backend. The converged X11 architecture must combine protocol-level capability probing with a narrow optional window-manager policy strategy. It must introduce a Mutter-specific X11 policy only if validation demonstrates a behavioral difference that cannot be handled through generic ICCCM/EWMH capability logic.

GNOME/Mutter on Ubuntu 24.04.4 LTS is an environment-specific support and validation target. Reusing the generic X11 implementation does not imply that every X11 desktop environment is supported.

Native X11 and XWayland compatibility remain separate backend identities even when they reuse XCB presentation and X11 tracking mechanisms.

Decision evidence: `research/x11-backend-identity.md`.

## Question 4: Runtime switching policy

After the composition root constructs a backend runtime, must the application support switching to a different backend while the overlay client remains running, or may backend/session/manual-override changes require an overlay-client restart?

### Answer

Yes. A change to the selected backend identity requires restarting the overlay client. This includes session/platform changes and manual override changes that select a different runtime.

The active backend must handle transient state changes live without reconstructing the backend: helper health loss/recovery, target appearance or loss, windowed/borderless transitions, monitor changes, scaling changes, presentation degradation/recovery, and GNOME renderer ownership changes.

The composition root therefore owns one production backend runtime for the lifetime of the overlay-client process, while tests may construct replacement roots independently.

## Question 5: GNOME helper failure behavior

If the GNOME helper becomes unavailable or incompatible during a native Wayland session, should the overlay remain hidden and report the backend as unavailable/degraded until the helper recovers, or should it automatically expose a managed PyQt fallback even when that fallback cannot meet the supported overlay contract?

### Answer

The overlay must remain hidden when the GNOME helper is unavailable, unhealthy, or incompatible and no presenter can satisfy the active mode's supported contract. The runtime must publish a clear degraded/unavailable status and reason, then recover automatically when helper health and compatibility return.

Windowed mode may continue to use its supported managed-PyQt presenter when that presenter remains valid. Borderless fullscreen must not expose an automatic managed-PyQt fallback. Building such a fallback is outside this project's scope unless a separate feasibility effort first proves it can satisfy the full support contract.

## Question 6: Startup with a missing GNOME helper

When a native GNOME Wayland session starts without a usable helper, should the selector still construct the GNOME backend runtime in a degraded/unavailable state so it can detect and recover if the helper appears, or should backend startup fail and require an overlay-client restart after the helper is installed or enabled?

### Answer

A usable, protocol-compatible GNOME helper is a construction-time prerequisite for the supported GNOME native-Wayland runtime. If the helper is missing, disabled, or incompatible when the overlay client starts, the backend reports unavailable and installing/enabling/upgrading the helper requires an overlay-client restart.

This does not prohibit live recovery from a transient helper transport or health failure after a compatible helper was present during runtime construction. Such recovery remains internal to the already-selected GNOME backend.

## Question 7: GNOME lifecycle ownership

Should the overlay client be the sole owner of GNOME helper presentation startup recovery and cleanup, with the EDMC plugin limited to launching/stopping the client and never calling GNOME-specific DBus cleanup directly?

### Answer

Yes. The overlay client, through its selected GNOME backend runtime, is the sole owner of GNOME presentation startup recovery, runtime state, and cleanup.

The EDMC plugin remains responsible for backend-neutral overlay-client process orchestration and data/settings transport. `load.py` must not import private GNOME presentation code or issue GNOME-specific DBus cleanup calls.

The GNOME backend cleanup contract must be idempotent and bounded. Startup recovery must handle presentation state left behind when a previous client did not shut down normally.

## Question 8: Hierarchical runtime ownership and orphan cleanup

Must every runtime layer automatically terminate or release its state within a bounded time when its owner disappears—including the overlay client shutting down when EDMC dies, and external helper presentation state clearing when the overlay client dies?

### Answer

Yes. Runtime ownership is hierarchical:

1. EDMC owns the overlay-client lifetime.
2. The overlay client owns the selected backend runtime.
3. The backend runtime owns all client-local and externally hosted presentation resources it creates.

Normal EDMC shutdown must ask the overlay client to stop cleanly. If EDMC crashes, exits unexpectedly, or stops renewing ownership, the overlay client must detect that loss and exit within a bounded time. Before exiting, it must stop its backend runtime and immediately release client-local and external resources.

If the overlay client crashes or cannot complete cleanup, externally hosted helper/compositor state must expire independently within a bounded time. For GNOME this includes Shell actors, raster content, presentation attachment, surface suppression, and renderer ownership.

Cleanup at every layer must be idempotent. Startup recovery is a defensive final layer for incomplete cleanup, not the primary orphan-cleanup mechanism. Diagnostics must distinguish EDMC-owner loss, client shutdown, backend cleanup, and helper ownership expiration.

The detailed design must research the existing EDMC/controller/client transport before choosing the liveness mechanism. It may use an ownership token, heartbeat, pipe/socket lifetime, or an equivalent reliable signal; it must not assume that checking only the original parent PID is sufficient.

## Question 9: Multiple overlay clients

If a second overlay client attempts to acquire GNOME presentation ownership while another healthy client owns it, should the helper reject the second client and report an ownership conflict, or should the newer client automatically take ownership from the existing client?

### Answer

The helper must reject a second overlay client while a healthy client owns presentation. It must preserve the existing owner's state and return an explicit ownership-conflict result that the rejected client publishes in diagnostics/status.

Ownership may transfer only after the current owner releases it normally or its lease/liveness expires. A newer client must not silently preempt a healthy owner.

Owner identity and conflict diagnostics must avoid exposing sensitive process or user data while remaining sufficient for troubleshooting.

## Question 10: Support, validation evidence, and live availability

Should the architecture represent support policy, validation-evidence level, and active runtime health/availability as separate dimensions—for example, “GNOME Wayland is supported, community-confirmed, but its helper is currently unavailable”—instead of collapsing them into one classification?

### Answer

Yes. Support policy, validation-evidence level, and current runtime availability/health are separate dimensions.

Support policy describes whether the project intentionally maintains the backend/environment/mode combination and accepts responsibility for investigating defects. Evidence level describes how strongly the configuration has been demonstrated to work. Health describes whether the selected runtime and its required capabilities are operational now.

For example, a supported GNOME Wayland environment may have `full_matrix`, `maintainer_smoke`, `community_confirmed`, `mixed_reports`, `reported_failure`, or `not_yet_reported` evidence while independently reporting `helper_unavailable`, `protocol_incompatible`, `ownership_conflict`, or another runtime state. A transient failure must not rewrite support policy, and a healthy runtime must not imply support where the project has intentionally declared none.

User-facing status and diagnostics must expose these dimensions without collapsing them into one classification.

## Question 11: Capability implementation scope

Should this project implement operational capability probes only for the in-scope GNOME Wayland and native X11 runtimes, while defining backend-neutral capability contracts that future KDE/KWin and other backends can implement later, or should it also build probes for those out-of-scope backends now?

### Answer

This project implements operational capability probes only for the in-scope GNOME native-Wayland and native-X11 runtimes. It defines backend-neutral probe evidence and capability contracts that other backends can implement later, but it does not build speculative KDE/KWin or other out-of-scope probes.

Every future backend implementation is required to add its own operational capability probes, tests, diagnostics, and environment validation before it can claim support. Selecting by compositor name, desktop name, or nominal bundle identity alone is insufficient.

The generic contract must allow future probes to provide backend-specific evidence without adding compositor-specific fields or decisions to generic runtime consumers.

## Question 12: Capture policy contract

The original architecture research proposed a `CapturePolicyBackend` for behavior such as capture exclusion. Should this convergence project add a backend-neutral optional capture-policy contract now, even if GNOME Wayland and native X11 initially report that no special capture policy is supported, or defer the contract until a backend actually needs it?

### Answer

Add extensible capability vocabulary that can represent capture-related support later, but do not introduce a behavioral `CapturePolicyBackend` interface in this project.

The first backend with a concrete capture-policy requirement must define the behavioral contract from real use cases, platform evidence, and tests. Until then, capture behavior must not be folded into presentation, input, or helper contracts as an undocumented side responsibility.

Adding capture policy later must be possible as an extension of backend composition without redesigning the composition root or generic consumers.

## Question 13: Presentation and input contracts

Should presentation and input policy become separate behavioral contracts even when one backend object can implement both, or should the architecture retain the current combined presentation/input adapter as the public contract?

### Answer

Presentation and input policy are separate behavioral contracts. Generic consumers must depend only on the contract relevant to their operation.

A backend may use one concrete object to implement both contracts when the platform implementation is genuinely coupled, but bundle composition must not require that identity and tests must not lock all backends into a combined adapter.

The input contract must own operations such as click-through, focus acceptance, and interaction-state changes rather than exposing backend identity only. The presentation contract must own presentation preparation, update, visibility/attachment results, renderer transitions where applicable, and teardown rather than only creating a window integration.

## Question 14: Helper protocol boundary

Should generic runtime contracts expose only backend-neutral helper lifecycle and health behavior, while GNOME-specific DBus methods, request/response models, renderer names, and transition details remain private to the GNOME backend?

### Answer

Yes. Generic runtime contracts expose backend-neutral helper behavior such as availability, compatibility, health, ownership acquisition/release, lifecycle, and sanitized diagnostics.

GNOME-specific DBus destinations/methods, helper payload models, renderer names, Shell-raster fields, target tokens, transition actions, and protocol validation remain private to the GNOME backend implementation.

Generic presentation/discovery results may carry normalized state and opaque diagnostics, but generic consumers must not dispatch on GNOME-specific values. Future helper-backed backends implement the generic behavior through their own private protocols.

## Question 15: Large-module decomposition scope

After GNOME behavior is lifted behind backend-owned contracts, should this project also split the large GNOME modules by responsibility where needed for maintainability, or stop once ownership and generic boundaries converge and leave broader file decomposition for a later project?

### Answer

Lift the existing GNOME implementation substantially intact behind the new backend-owned behavioral contracts, redirect generic consumers through those contracts, and prove behavioral parity before reshaping internals.

After ownership convergence, split large GNOME modules only where a responsibility boundary is required for clear state ownership, lifecycle management, isolated testing, or maintainability. File length alone is not a reason to expand scope.

Decomposition must be staged, behavior-scoped, and reversible. Phase 19 transition behavior and existing helper protocol compatibility remain anchored by tests and manual validation throughout.

## Question 16: Migration rollback path

Should the old GNOME consumer-dispatch route remain temporarily available behind a developer-only rollback toggle until the new backend-owned runtime passes the validation matrix, then be removed rather than maintained as a permanent second architecture?

### Answer

Yes. During migration, the current GNOME consumer-dispatch path remains temporarily available behind a developer-only rollback toggle while the backend-owned runtime is proven.

The rollback path must preserve existing behavior and diagnostics sufficiently to support comparison and emergency reversal. It is removed after automated parity tests and the required GNOME validation matrix pass. It must not remain as a permanent production alternative or force both architectures to evolve indefinitely.

Removal of the old path, its toggle, its direct private imports, and superseded tests is an explicit completion gate in the implementation plan.

## Question 17: Scaling acceptance matrix

What minimum scaling configurations must the new validation phase require for GNOME Wayland and native X11—for example 100%, common fractional scales such as 125%/150%, 200%, and mixed per-monitor scaling?

### Answer

The required initial validation matrix includes uniform 100% scaling and uniform 125% scaling for the in-scope GNOME Wayland and native-X11 environments.

Mixed per-monitor scaling is explicitly deferred. It is not part of this project's initial support claim or acceptance gate and must be recorded as a known validation gap rather than implied supported behavior.

## Question 18: Multi-monitor layout matrix

What minimum physical monitor layouts and handoffs must pass—for example, a two-monitor horizontal layout with the secondary monitor on either side/negative coordinates, primary-monitor changes, and vertical layouts?

### Answer

Require a two-monitor horizontal layout, fullscreen/windowed handoffs in both directions, and at least one arrangement where a monitor occupies negative desktop coordinates.

Vertical monitor layouts and changing the primary monitor are deferred. They are not part of the initial support claim and must be documented as validation gaps.

## Question 19: Mode-transition acceptance

Should validation require stable windowed and borderless-fullscreen operation plus transitions in both directions on each monitor, fullscreen monitor handoffs in both directions, and Alt-Tab/GNOME Overview checks before and after transitions?

### Answer

Yes. Validation requires stable windowed and borderless-fullscreen operation, transitions from each mode to the other on each monitor, fullscreen monitor handoffs in both directions, and Alt-Tab/GNOME Overview checks before and after transitions.

Acceptance must preserve Phase 19 invariants: no simultaneously visible Shell-raster and managed-PyQt presenters, no title-bar or monitor-relative intermediate, no black surface, no focus trap, no unexpected task-list/Overview identity, and correct bounded commitment to the stable renderer.

## Question 20: EDMC compliance in the new validation phase

Should the new PDD validation phase include formal EDMC plugin compliance as a release gate—covering supported APIs, Python baseline, logger/version handling, Tk-main-thread responsiveness, lifecycle hooks, preferences/config access, and dependency/HTTP practices—even though the old `fix219` Phase 5 has been discarded?

### Answer

Yes. The replacement validation phase includes a formal EDMC compliance gate covering the current upstream Python baseline, supported plugin APIs/helpers, logger naming and exception handling, version gating, Tk-main-thread responsiveness, startup/shutdown hooks, preferences/config access, dependencies, and HTTP/debug-routing practices.

Every compliance item must receive an explicit yes/no result with evidence. Failures must be remediated or explicitly block the support/release gate; they cannot be hidden by discarding the old Phase 5 record.

Changes to `load.py` or EDMC hook flow require harness coverage, and synchronous backend-specific I/O must not remain on the Tk hook path.

## Question 21: GNOME helper protocol compatibility

Must the converged client remain compatible with the currently installed GNOME helper protocol throughout migration, or may lifecycle ownership/lease changes introduce a coordinated protocol version bump that requires updating the extension and restarting the overlay client/session?

### Answer

The architecture lift should initially preserve current helper behavior so ownership changes are isolated from composition rewiring. After backend-owned runtime parity is proven, the lifecycle-ownership stage may update the client and GNOME extension together and introduce one explicit helper protocol version bump.

Because no intermediate build will ship before broader Linux backend coverage exists, this project does not need to implement or maintain dual old/new helper protocol compatibility. The version bump, extension update, client update, manifest/schema tests, installation/update behavior, and required restart/session instructions land as one coordinated increment before removal of the old dispatch path and final validation.

An incompatible helper must fail closed with explicit status. Silent protocol fallback is not allowed.

## Question 22: Existing configuration compatibility

Should existing user settings, backend override values, environment toggles, and status/config payload fields remain backward compatible through convergence unless a field is explicitly documented as developer-only and removed with a migration note?

### Answer

Backward compatibility is not required for backend-related settings or control-plane payloads. The convergence work may redesign and version backend override values, family/instance fields, capability evidence, support/health state, helper ownership, fallback state, restart requirements, and backend diagnostics.

The EDMC plugin, controller, overlay client, preferences/status UI, diagnostic collectors, and tests must be updated together. Stale or unknown backend schema versions must fail safely with clear diagnostics; backend settings may be reset rather than migrated.

This permission applies only to the backend control plane. Overlay content/message payloads, rendering commands, third-party overlay integrations, layout/group payloads, and non-backend user preferences must remain compatible and behaviorally unchanged.

## Question 23: GNOME backend identity versus presenter mode

Should `gnome_shell_wayland` and `gnome_shell_raster` converge into one GNOME Wayland backend runtime that selects managed PyQt for supported windowed presentation and Shell raster for supported borderless fullscreen presentation, instead of exposing Shell raster as a separate backend identity/manual override?

### Answer

Yes. Converge `gnome_shell_wayland` and `gnome_shell_raster` into one GNOME Wayland backend identity and runtime.

The GNOME runtime owns presenter selection: managed PyQt for supported windowed presentation and Shell raster for supported borderless fullscreen presentation. Phase 19 renderer handoff remains an internal backend state transition, not a backend-selection change.

Remove Shell raster as a separate production backend identity and manual override. Preserve any temporary renderer-forcing control only as a developer validation/rollback mechanism, then remove or clearly retain it as developer-only after its test purpose is complete.

Support and health status identify the GNOME Wayland backend while separately reporting the active presenter and transition state in diagnostics.

## Question 24: Manual backend override exposure

In the converged product, should manual backend overrides remain a user-facing preference for troubleshooting, or become developer-only controls while normal users receive automatic capability-based selection plus a restart-required status when selection inputs change?

### Answer

Automatic capability-based backend selection is the normal user path.

Retain a user-facing manual override only for valid, supportable compatibility choices, primarily XWayland where available and meaningful. Overrides must be filtered by the probed environment, report their degraded/support implications, and require an overlay-client restart when changed.

Internal backend identities, GNOME presenter selection, renderer forcing, and migration rollback controls are developer-only. Invalid or stale override values fail safely with clear status rather than silently selecting an unrelated backend.

## Question 25: Future-backend implementation guide

Should this project deliver a documented backend implementation checklist and reusable contract-test suite that every future backend—such as KDE/KWin—must satisfy for probing, composition, lifecycle, support/health reporting, and validation before it can be added?

### Answer

Yes. Required project deliverables include a documented backend implementation checklist and reusable contract-test suite.

Every future backend must provide and prove: operational capability probes, composition registration, discovery/presentation/input behavior as applicable, lifecycle and orphan cleanup, support-versus-health reporting, safe failure behavior, diagnostics, automated contract tests, environment-specific validation evidence, and documented support boundaries.

The guide must include a minimal paper/example backend that demonstrates extension points without embedding GNOME behavior or implementing an out-of-scope compositor. KDE/KWin implementation remains outside this project.

## Question 26: Existing out-of-scope Wayland bundles

During convergence, should the current nominal KWin, wlroots, Hyprland, generic layer-shell, COSMIC, and gamescope entries remain as explicitly unimplemented/unvalidated detected environments until dedicated backend projects implement their probes and behavior, rather than continuing to claim support through the shared transitional Wayland integration?

### Answer

Yes. KWin, wlroots/Sway/Wayfire, Hyprland, generic layer-shell, COSMIC, and gamescope remain detectable environment identities for diagnostics and future backend registration, but are explicitly unimplemented/unvalidated in this project.

They must not construct a shared transitional Wayland runtime and claim `true_overlay` merely from compositor identity. Their status must clearly report that a dedicated backend has not yet satisfied the required probes, contracts, and validation gate.

Future backend projects may replace each placeholder through the documented registration and contract process without changing generic runtime consumers.

## Question 27: Unvalidated native-X11 environments

Because this project validates `native_x11` only under GNOME/Mutter on Ubuntu 24.04.4 LTS, should other detected X11 window managers remain operational where the generic runtime works but report an unvalidated support state rather than inheriting the GNOME support claim?

### Answer

Yes. The generic `native_x11` runtime may remain operational on other X11 window managers when required capabilities are present, but those environments report an explicit unvalidated support state and do not inherit the GNOME/Mutter support claim.

Support certification is keyed to validated environment evidence, not merely backend implementation identity. Future X11 environment validation may promote an environment without requiring a new backend unless distinct behavior requires a narrow window-manager policy.

## Question 28: XWayland acceptance level

Should XWayland remain an explicitly degraded compatibility backend with automated contract coverage and a basic GNOME/Wayland smoke test, but stay outside the full windowed/borderless/multi-monitor/scaling acceptance matrix required for native GNOME backends?

### Answer

Yes. XWayland remains a distinct, explicitly degraded compatibility backend.

It requires automated contract/selection/status tests and a basic GNOME Wayland smoke test proving startup, tracking/presentation baseline, clear degraded reporting, and clean shutdown. It is outside the full native-GNOME windowed/borderless, transition, multi-monitor, and scaling acceptance matrix.

XWayland compatibility must not be presented as equivalent to native GNOME Wayland or native X11 support.

## Question 29: Validation depth for GNOME Shell 47–50

Should GNOME Shell 46 on Ubuntu 24.04.4 receive the full acceptance matrix while GNOME Shell 47, 48, 49, and 50 each require at least a live smoke test plus automated helper manifest/protocol coverage before being described as validated, with untested listed versions remaining target-compatible but unvalidated?

### Answer

GNOME Shell 46, 47, 48, 49, and 50 are supported by project policy. GNOME Shell 46 on Ubuntu 24.04.4 receives the complete maintainer acceptance matrix. Evidence for GNOME Shell 47–50 may come from maintainer smoke tests or structured community reports; those versions do not need the full matrix before the project accepts and supports them.

Track validation evidence separately using at least these levels:

- `full_matrix`
- `maintainer_smoke`
- `community_confirmed`
- `mixed_reports`
- `reported_failure`
- `not_yet_reported`
- `not_applicable`

Community feedback is accepted as evidence for both success and failure. A useful report records GNOME Shell version, distribution/version, session type, play mode, monitor layout, scale factor, plugin/client/helper versions, observed startup/tracking/input/transition/shutdown behavior, and relevant sanitized diagnostics or logs.

A reproducible failure changes evidence/known-issue state; it does not automatically remove the configuration from support policy. Unsupported means intentionally outside project scope, not merely insufficiently tested.

Launch requirements include a public support/evidence matrix, a community-facing explanation of these terms, a structured success/failure report template, instructions for collecting safe diagnostics, and a maintained workflow for incorporating reports into the evidence matrix and release notes.

## Question 30: Orphan cleanup timing

What maximum delay is acceptable between EDMC ownership loss and overlay-client shutdown, and between overlay-client loss and externally hosted presentation cleanup?

### Answer

Use the persistent EDMC/plugin-to-client TCP connection as the primary ownership signal. Confirmed orderly connection closure begins overlay-client shutdown immediately.

Add an ownership heartbeat with an initial 2-second cadence. After three missed heartbeats, the client treats EDMC ownership as lost and begins shutdown, giving an initial maximum detection bound of approximately 6 seconds.

The client renews externally hosted backend presentation ownership on an initial 2-second cadence. External ownership expires and presentation state clears after approximately 10 seconds without renewal.

These are initial requirements subject to focused lifecycle tests against suspend/resume, EDMC restart, debugger pauses, temporary event-loop stalls, half-open connections, and clock behavior. Final tuning may change the exact values while preserving prompt cleanup and reasonable false-positive resistance.

## Question 31: EDMC restart and client adoption

If EDMC restarts while an old overlay client is still within its owner-loss grace period, should the new EDMC instance adopt that client, or should the old client always exit and the new EDMC launch a fresh client with a new ownership identity?

### Answer

A restarted EDMC instance must launch a fresh overlay client with a new ownership identity. It must not adopt a client created by the previous EDMC instance.

The old client must complete its bounded owner-loss shutdown. The helper must reject overlapping ownership while the old lease is healthy and allow the new client to acquire ownership only after orderly release or confirmed expiration. Startup must expose a clear temporary ownership-wait/conflict state rather than preempting the old owner.

## Question 32: Performance regression gate

Should convergence include a performance acceptance gate that captures a pre-migration baseline and rejects material regressions in presentation-cycle latency, helper call frequency, raster generation/transfer, CPU usage, and visible transition smoothness?

### Answer

Yes. Capture a representative pre-migration performance baseline for stable windowed mode, stable borderless fullscreen, windowed/fullscreen transitions, and fullscreen monitor handoffs.

After each relevant migration stage, compare presentation-cycle latency, helper call/query frequency, raster generation/encoding/transfer work, idle CPU behavior, transition timing, and compositor-visible smoothness. Existing diagnostics should be reused or extended rather than creating a broad unrelated benchmark system.

The gate uses realistic tolerances and repeated observations. Ordinary measurement noise does not fail the project, but material regressions require investigation and resolution or an explicit documented acceptance decision.

## Question 33: Community diagnostic collection

Should the existing Linux diagnostic collector be extended to produce a privacy-conscious backend report containing support policy/evidence, probe results, selected runtime, helper compatibility/ownership, lifecycle events, active presenter, and recent failure reasons for community validation reports?

### Answer

Yes. Extend the existing Linux diagnostic collector with a privacy-conscious backend report suitable for structured community success/failure evidence.

The report includes support policy and evidence level, normalized probe/capability results, selected runtime identity, helper protocol compatibility and ownership state, EDMC/client/backend lifecycle events, active presenter/transition state, and recent normalized failure reasons.

It must preserve the collector's existing privacy posture: avoid screenshots, broad process/window dumps, command lines, unrelated window titles, sensitive environment dumps, ownership secrets/tokens, and unnecessary personal paths. Reports must remain reviewable by the user before sharing.

## Question 34: Architectural completion gate

Should architectural convergence be considered complete only when one composition root owns the selected runtime, generic consumers/lifecycle contain no private compositor dispatch, GNOME and native X11 satisfy their contracts, old migration routes are removed, truthful status/evidence reporting is live, validation/compliance gates pass, and the future-backend guide/tests are complete?

### Answer

Yes. Architectural convergence is complete only when:

- One composition root constructs and owns the selected runtime for the overlay-client lifetime.
- Generic consumers, launcher code, and EDMC lifecycle code contain no private compositor implementation imports or compositor-specific behavior dispatch.
- GNOME Wayland and native X11 satisfy their defined behavioral contracts and support boundaries.
- GNOME Wayland uses one backend identity with backend-owned presenter selection.
- Support policy, validation evidence, runtime health, ownership, and diagnostics are represented truthfully.
- Hierarchical lifecycle/orphan cleanup, performance, automated tests, the manual support matrix, and formal EDMC compliance gates pass.
- The future-backend implementation guide and reusable contract-test suite are complete.

Temporary migration routes are removed per migrated backend after that backend passes its convergence validation; removal does not wait for all desired future backends. Specifically, the old GNOME consumer-dispatch path, direct generic imports, obsolete `gnome_shell_raster` production identity/override, and old-versus-new architecture toggle must be removed after GNOME acceptance.

Intentional diagnostic, performance-tracing, or narrowly scoped behavioral rollback toggles may remain only after an explicit retention decision. They must not preserve a second architecture or become requirements for future backends.

## Question 35: Step 3 pressure reduction and baseline restart

After the reduced pre-migration matrix exposed sustained stable-state GNOME helper queries,
high repaint-request counts, and a desktop-instability incident in which the helper was a
possible load amplifier but not a proven root cause, should Step 3 pause capture, reduce
unnecessary steady-state work, run a controlled helper-disabled/helper-enabled A/B, and then
restart a clean baseline rather than mix pre- and post-optimization samples?

### Answer

Yes. Amend the existing fix219 PDD and Step 3 rather than create a separate project.

Before resuming performance capture:

- disable capture diagnostics and establish a quiet normal-use configuration;
- add test-first, backend-owned stable-target query caching or rate limiting with an injected
  monotonic clock and explicit invalidation/recovery rules;
- diagnose repaint-request sources and suppress only work proven to leave rendered output
  unchanged, while preserving TTL/metadata refresh and all required repaint triggers;
- keep generic follow/runtime code free of compositor-specific imports and raw helper/backend
  enum dispatch;
- run a controlled four-cell A/B that separates the cost of an enabled idle extension from the
  incremental cost of the client's helper loop; and
- repeat the manual startup, focus, transition, placement, Alt-Tab, Overview, and quiet-soak
  contracts before restarting the matrix.

The 12 accepted reduced-v2 captures remain immutable historical pre-optimization/incident-era
evidence. They cannot contribute to post-optimization thresholds or be relabeled as part of the
new baseline. After the pressure-reduction and A/B gates pass, create a new manifest/evidence
identity and restart the coherent 42-capture matrix at 0/42. Numeric thresholds remain unset
until that repeated baseline is complete and reviewed.
