# Implementation Plan: fix219 Architecture Convergence

Plan review status: **Approved for PDD completion on 2026-07-19**

Implementation status: **In progress**

## Authority and Scope

This plan implements the approved `design/detailed-design.md`. It does not authorize implementation by itself. Each step is a behavior-scoped, reversible increment and must be explicitly selected for implementation.

The plan follows a lift-then-prove sequence:

1. Anchor contracts, evidence, and a pre-migration baseline.
2. Establish one composition root without changing behavior.
3. Move lifecycle ownership behind authenticated, bounded channels.
4. Add GNOME helper leases as one coordinated client/extension protocol bump.
5. Converge identity, capability selection, status, and diagnostics.
6. Pass acceptance gates and remove the temporary second architecture.

No step implements KDE/KWin or another out-of-scope compositor. Windows, content/rendering payloads, layout/group behavior, capture policy, portal fallback, and geometry/follow redesign remain behaviorally unchanged unless a step explicitly names a compatibility lift required by the composition root.

## Implementation Checklist

- [x] Step 1: Add converged backend models and a shadow control-plane envelope
- [ ] Step 2: Add behavioral runtime contracts and the reusable paper-backend contract suite
- [ ] Step 3: Capture the repeatable pre-migration performance baseline
- [ ] Step 4: Add the backend registry and prove selection/construction identity in shadow mode
- [ ] Step 5: Install the launcher-owned application composition root
- [ ] Step 6: Route discovery and tracking through the owned runtime
- [ ] Step 7: Route non-GNOME presentation and input through separate runtime contracts
- [ ] Step 8: Lift existing GNOME presentation intact behind `GnomeWaylandRuntime`
- [ ] Step 9: Move overlay-client GNOME startup and shutdown cleanup into runtime ownership
- [ ] Step 10: Add the atomic authenticated owner launch record and handshake
- [ ] Step 11: Enforce owner heartbeat, terminal EOF, and graceful watchdog shutdown
- [ ] Step 12: Replace synchronous Tk status requests with pushed, cached backend status
- [ ] Step 13: Remove GNOME-specific lifecycle behavior from `load.py`
- [ ] Step 14: Land GNOME helper protocol 4 ownership leases as one coordinated increment
- [ ] Step 15: Add independent helper expiry and non-preemptive restart/conflict handling
- [ ] Step 16: Couple EDMC ownership health to backend lease renewal and recovery
- [ ] Step 17: Converge GNOME Wayland to one production identity and fail-closed selection
- [ ] Step 18: Add operational native-X11 probes and environment-scoped support policy
- [ ] Step 19: Make XWayland explicit and other Wayland environments unimplemented
- [ ] Step 20: Migrate every backend control-plane consumer to schema version 1
- [ ] Step 21: Publish support evidence and extend the privacy-safe diagnostic collector
- [ ] Step 22: Automate and satisfy the EDMC compliance gate
- [ ] Step 23: Publish the future-backend implementation guide
- [ ] Step 24: Pass convergence acceptance and remove the old GNOME architecture

Checklist items correspond one-to-one with the numbered steps below. A box is checked only after implementation, required automated tests, the named demo, and step-specific evidence are complete.

## Phase Tracking

### Phase 1: Contract and Evidence Anchors

Phase status: **In progress**

| Stage | Step | Description | Status |
| --- | --- | --- | --- |
| 1.1 | 1 | Converged pure models and shadow status envelope | Completed |
| 1.2 | 2 | Behavioral contracts and paper-backend suite | Not started |
| 1.3 | 3 | Repeatable pre-migration performance baseline | Not started |

### Phase 2: One Composition Root

Phase status: **Not started**

| Stage | Step | Description | Status |
| --- | --- | --- | --- |
| 2.1 | 4 | Registry and shadow selection/construction parity | Not started |
| 2.2 | 5 | Launcher-owned root and runtime lifetime | Not started |
| 2.3 | 6 | Runtime-owned discovery/tracking route | Not started |
| 2.4 | 7 | Separate presentation/input routes for non-GNOME backends | Not started |
| 2.5 | 8 | Existing GNOME behavior behind its runtime | Not started |
| 2.6 | 9 | Client-side GNOME lifecycle ownership | Not started |

### Phase 3: EDMC-to-Client Ownership

Phase status: **Not started**

| Stage | Step | Description | Status |
| --- | --- | --- | --- |
| 3.1 | 10 | Atomic launch record and authenticated owner role | Not started |
| 3.2 | 11 | Heartbeat, terminal EOF, and watchdog cleanup | Not started |
| 3.3 | 12 | Pushed/cached Tk-safe status | Not started |
| 3.4 | 13 | Backend-neutral `load.py` lifecycle | Not started |

### Phase 4: GNOME External Ownership

Phase status: **Not started**

| Stage | Step | Description | Status |
| --- | --- | --- | --- |
| 4.1 | 14 | Coordinated protocol 4 lease authority | Not started |
| 4.2 | 15 | Independent expiry and ownership conflict behavior | Not started |
| 4.3 | 16 | Hierarchical owner/lease liveness and recovery | Not started |

### Phase 5: Selection, Status, and Evidence

Phase status: **Not started**

| Stage | Step | Description | Status |
| --- | --- | --- | --- |
| 5.1 | 17 | One GNOME identity and construction prerequisites | Not started |
| 5.2 | 18 | Native-X11 operational evidence and support scope | Not started |
| 5.3 | 19 | XWayland compatibility and unimplemented placeholders | Not started |
| 5.4 | 20 | End-to-end backend schema migration | Not started |
| 5.5 | 21 | Public evidence workflow and safe diagnostics | Not started |

### Phase 6: Compliance and Convergence Closure

Phase status: **Not started**

| Stage | Step | Description | Status |
| --- | --- | --- | --- |
| 6.1 | 22 | Automated EDMC compliance and remediations | Not started |
| 6.2 | 23 | Future-backend implementation guide | Not started |
| 6.3 | 24 | Acceptance, migration-route removal, and final evidence | Not started |

When every stage in a phase is complete, update its phase status to **Completed**. Keep evidence notes ordered by phase and stage.

## Global Implementation Rules

- Write tests before or with each behavior change.
- Use unit tests for pure models, state machines, probes, selection, serialization, timing, and injected dependencies.
- Use harness tests for every `load.py`, plugin hook, startup/shutdown, server/watchdog, settings, or Tk status-path change.
- Use both unit and harness tests for mixed changes.
- Run Qt widget/surface operations only on the Qt main thread and Tk operations only on the Tk main thread.
- Keep the current GNOME route behind one developer-only process-start rollback toggle until Step 24.
- Do not rewrite Phase 19 while moving it. Preserve the 1.5-second injectable grace period and all atomic handoff/focus/visibility invariants.
- Do not remove a transitional test until replacement parity coverage is already passing.
- Never log or collect owner or lease tokens, raw owner IDs, target handles, arbitrary window titles, command lines, or personal paths.
- Record files changed, exact commands, pass/fail/skip counts, manual evidence, and rollback state for every completed step.
- Stop a step if its required test type cannot run; document the blocker rather than substituting an unrelated test.

## Standard Validation Commands

Run commands from the repository root. Use the repository environment at `overlay_client/.venv`.

- Targeted unit/harness tests: `overlay_client/.venv/bin/python -m pytest <test paths> -q`
- Headless suite: `overlay_client/.venv/bin/python -m pytest`
- GUI-enabled suite: `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest`
- Harness suite: `overlay_client/.venv/bin/python -m pytest -m harness -q`
- Lint/typecheck/full test gate: `make check`
- Project test target: `make test`
- EDMC baseline check: `overlay_client/.venv/bin/python scripts/check_edmc_python.py`
- Patch hygiene: `git diff --check`

On Windows Python 3.13+, use `overlay_client\.venv\Scripts\python scripts\run_pytest_safe_windows.py <pytest args>` only if the documented `tmp_path` `WinError 5` occurs.

## Step 1: Add converged backend models and a shadow control-plane envelope

**Objective**

Introduce immutable backend identity, operational probe, support policy, evidence level, runtime health, operation result, failure, lifecycle, and schema-version-1 envelope models without changing production selection or presentation.

**Implementation guidance**

- Add the approved normalized enums/dataclasses beside the transitional types in `overlay_client/backend/`.
- Keep backend-private evidence in allowlisted sanitized mappings.
- Add deterministic JSON serialization/deserialization with explicit unknown-version rejection and bounded failure history.
- Produce a developer-only shadow snapshot from current `BackendSelectionStatus`; it is diagnostic comparison output, not a new production control path.
- Preserve the existing status payload and all content/settings payloads.

**Test requirements**

- Unit tests for enum values, immutable records, revision behavior, round trips, unknown versions, bounded histories, and redaction.
- Extend `test_backend_status.py` while adding a focused control-plane model test rather than replacing transitional assertions.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_status.py overlay_client/tests/test_backend_control_plane.py -q`
  - `git diff --check`

**Integration**

The shadow adapter consumes current status and provides a comparison artifact for Steps 4 and 20. No generic consumer reads the new envelope for behavior yet.

**Demo**

Given representative GNOME, native-X11, XWayland, and unimplemented inputs, serialize schema-version-1 snapshots showing independent support, evidence, and health dimensions while the shipped runtime path remains unchanged.

**Completion evidence — 2026-07-19**

- Added immutable normalized models, strict deterministic schema-v1 codec, bounded/privacy-safe
  diagnostic boundaries, and a developer-gated shadow adapter beside transitional types.
- Preserved production selector, bundle, presentation, content/settings payloads, and
  `BackendSelectionStatus.to_payload()`; no generic consumer reads the envelope for behavior.
- Added/updated `overlay_client/tests/test_backend_control_plane.py` and
  `overlay_client/tests/test_backend_status.py` with representative GNOME, native-X11,
  XWayland, unimplemented, revision, round-trip, malformed, bounds, and redaction coverage.
- Targeted unit gate: 45 passed using the repository root `.venv`; the requested
  `overlay_client/.venv` could not run because that environment has no pytest installation.
- Headless suite excluding one pre-existing environment-defective raster test: 1165 passed,
  41 skipped, 1 deselected. Offscreen GUI-enabled suite with the same deselection: 1202 passed,
  21 skipped, 1 deselected.
- The deselected test constructs a `QFont` without a `QGuiApplication`; it aborts when its
  `/run/user/1000` cache is writable and otherwise fails on the sandbox's read-only runtime
  directory. The touched pure modules do not participate in that test.
- Whole-repository ruff and mypy, touched-file format check, and `git diff --check` passed.
- Rollback remains additive: remove the new models/codec/adapter, exports, and focused tests;
  the shipped runtime route is unchanged.

## Step 2: Add behavioral runtime contracts and the reusable paper-backend contract suite

**Objective**

Define backend runtime, discovery, presentation, input, and helper-lifecycle behavior contracts and prove them with a deterministic in-memory paper backend.

**Implementation guidance**

- Add the approved process-lifetime interfaces and normalized intent/result types.
- Permit one object to implement multiple interfaces without requiring object identity.
- Add an unavailable runtime implementation for construction failures and an unimplemented runtime for placeholders.
- Put the paper backend under test support; do not register it in production.
- Build a parameterized contract suite that production backends can adopt incrementally.

**Test requirements**

- Unit/contract tests for immutable identity, one start, partial-start cleanup, idempotent stop, stable component instances, discovery appearance/loss, presentation/hide results, independent input state, status revisions, owner-loss cleanup, and sanitized diagnostics.
- Keep current `test_backend_contracts.py` assertions until their production replacements exist.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_runtime_contracts.py -q`
  - `git diff --check`

**Integration**

The paper runtime serializes through Step 1's envelope and establishes the test factory later supplied by GNOME, native X11, and XWayland.

**Demo**

Run one deterministic paper runtime from construction through target appearance, present, input change, owner loss, repeated stop, and final serialized status without importing any compositor module.

## Step 3: Capture the repeatable pre-migration performance baseline

**Objective**

Create the scenario manifest and summary tooling, then capture the required current-behavior baseline before production routing changes begin.

**Implementation guidance**

- Reuse existing client raster, helper, transition, repaint, and CPU diagnostics.
- Add a versioned scenario manifest for stable windowed/fullscreen, both transition directions, both monitor handoffs, Alt-Tab, and Overview at 100% and 125%.
- Add a small pure summary tool for median, p95, maximum, counts, helper/raster work, and idle CPU.
- Store raw sanitized captures and summaries under the release validation evidence tree; never store secrets or personal paths.
- Determine investigation thresholds from repeated baseline variance and record them before Step 5.

**Test requirements**

- Unit tests for manifest validation, sample aggregation, clock-domain separation, redaction, and threshold comparison.
- Manual baseline capture on GNOME Shell 46/Ubuntu 24.04.4 using fixed fixture, geometry, warm-up, duration, and repetitions.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_performance_summary.py tests/test_debug_collectors.py -q`
  - `git diff --check`
- This step cannot be marked complete without the manual baseline; if the target environment is unavailable, Steps 1–2 may stand but production routing must not proceed.

**Integration**

The manifest and thresholds become the comparison gate for Steps 8, 16, 17, and 24. Existing release behavior is the oracle.

**Demo**

Generate a sanitized baseline summary and comparison-ready artifact for every required scenario using the shipped architecture.

## Step 4: Add the backend registry and prove selection/construction identity in shadow mode

**Objective**

Associate stable backend identities with factories in one registry and prove that selection, construction, runtime identity, and shadow status cannot disagree.

**Implementation guidance**

- Add one composition registry as the permitted generic-to-concrete import boundary.
- Adapt current bundle builders to factory registrations without routing production consumers through them yet.
- Produce a shadow `RuntimeConstructionResult` beside the shipped selection/bundle path.
- Return unavailable/unimplemented runtime objects rather than `None` for known failed/placeholder selections.
- Extend architecture scans so behavior cannot leak into the registry.

**Test requirements**

- Unit tests for registration uniqueness, exact identity equality, unknown identity, failed construction, placeholder construction, and parity with current selection.
- Architecture tests for allowed registry imports and forbidden behavior dispatch.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_registry.py overlay_client/tests/test_backend_architecture_boundary.py -q`
  - `git diff --check`

**Integration**

The registry consumes Steps 1–2 and remains shadow-only until the launcher root in Step 5 owns its construction result.

**Demo**

For every existing selector fixture, print/assert the shipped selection and shadow runtime identity side by side, with exact matches or an explicit normalized construction failure.

## Step 5: Install the launcher-owned application composition root

**Objective**

Make `overlay_client.launcher.main()` construct and stop exactly one selected runtime while retaining existing presentation behavior behind the developer rollback route.

**Implementation guidance**

- Add `ApplicationCompositionRoot` after `QApplication` and initial settings are available and before the overlay is shown.
- Move probe, selection, registry construction, runtime start, surface attachment, status publication, and final stop ordering under the root.
- Inject factories, clocks, scheduling, and logging for tests.
- Keep `OverlayWindow` as a consumer and keep the existing data/content client behavior unchanged.
- Add a process-start developer toggle for the old versus new root; never mix roots or switch at runtime.

**Test requirements**

- Unit tests for construction order, exactly one runtime, hidden unavailable startup, idempotent stop, partial-start cleanup, and identity invariants.
- GUI-enabled launcher tests for surface attachment/show gating and Qt main-thread behavior.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_application_composition_root.py overlay_client/tests/test_platform_context.py -q`
  - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_application_composition_root.py overlay_client/tests/test_launcher_group_filter.py -q`
  - `git diff --check`

**Integration**

The root consumes the registry/runtime from Steps 2 and 4. Existing consumer functions remain adapters, so the user-visible overlay stays unchanged.

**Demo**

Launch with the new-root toggle, observe one matching runtime/status lifetime, then quit normally and show one bounded runtime stop with no content/layout regression.

## Step 6: Route discovery and tracking through the owned runtime

**Objective**

Replace separate tracker construction with the root-owned discovery service while preserving target appearance/loss, fallback, and geometry behavior.

**Implementation guidance**

- Lift current X11/XWayland/Windows tracker factories behind discovery adapters.
- Preserve GNOME's current helper-driven/no-generic-tracker behavior through its adapter.
- Inject one discovery instance into follow/window code; do not reconstruct bundles on target or monitor changes.
- Marshal discovery callbacks onto the Qt main thread.
- Keep existing title hints, monitor providers, fallback rules, and diagnostics intact.

**Test requirements**

- Unit/contract tests for one discovery lifetime, appearance/loss, fallback selection, recovery, and stop.
- Extend current tracker routing and follow-surface tests; add GUI tests only where callback/UI wiring requires them.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_runtime_contracts.py -q`
  - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_surface_mixin.py -q`
  - `git diff --check`

**Integration**

The Step 5 root now owns and injects discovery. Presentation still uses the existing consumer path, limiting this increment to tracking ownership.

**Demo**

Run the new root, show the Elite target appearing, moving monitors, and disappearing through one discovery object, then switch to the rollback root and confirm observable parity.

## Step 7: Route non-GNOME presentation and input through separate runtime contracts

**Objective**

Lift existing X11, XWayland, Windows, and transitional generic presentation/input integrations behind separate behavior interfaces without redesigning their platform behavior.

**Implementation guidance**

- Adapt current integration creation, click-through, focus acceptance, visibility, and teardown.
- Give generic consumers only the contract they use.
- Preserve separate native-X11 and XWayland identities even where adapters share XCB code.
- Keep out-of-scope Wayland implementations transitional until Step 19 rather than improving them here.
- Retain the old combined-adapter assertions only as parity tests until replacements pass.

**Test requirements**

- Unit/contract tests for present/hide, click-through/focus, independent revisions, teardown, and identity separation.
- GUI tests for Qt flags/surface behavior; existing X11/XWayland bundle tests remain regression anchors.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_interaction_surface.py overlay_client/tests/test_backend_runtime_contracts.py -q`
  - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_surface.py -q`
  - `git diff --check`

**Integration**

The new root now reaches non-GNOME discovery, presentation, and input entirely through runtime-owned adapters. GNOME remains on its old consumer dispatch until Step 8.

**Demo**

Show unchanged native-X11/XWayland positioning and input transparency while tests prove presentation and input can be backed by different objects.

## Step 8: Lift existing GNOME presentation intact behind `GnomeWaylandRuntime`

**Objective**

Route the complete current GNOME helper/raster/managed-PyQt behavior through a GNOME-owned runtime adapter without rewriting Phase 19.

**Implementation guidance**

- Delegate to the existing GNOME helper presentation functions, request validators, raster builder, transition state, timings, and diagnostics.
- Keep protocol 3 and current payloads unchanged in this step.
- Expose normalized discovery, presentation, input, helper-health, and status results at the runtime boundary.
- Select the new adapter with the developer architecture toggle; preserve the old `backend.consumers` route as the oracle.
- Split large modules only if a state owner must be isolated for this adapter; do not split by line count.

**Test requirements**

- Old/new parity tests with identical injected inputs and clocks.
- Reuse all GNOME helper, raster, presentation state, transition, focus, negative-coordinate, and monitor-handoff tests.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_presentation_transition.py -q`
  - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py -q`
  - `git diff --check`

**Integration**

GNOME now participates in the Step 5 root and Step 2 contracts, but protocol and external lifecycle ownership remain unchanged. The rollback route stays available.

**Demo**

With the new GNOME route enabled, demonstrate stable windowed and borderless modes plus both fullscreen monitor handoffs with the same normalized results and no dual-visible presenter.

## Step 9: Move overlay-client GNOME startup and shutdown cleanup into runtime ownership

**Objective**

Make the selected GNOME runtime own client-side startup recovery and shutdown cleanup, removing private GNOME cleanup imports from the generic launcher.

**Implementation guidance**

- Lift launcher startup/shutdown clear behavior behind runtime `start()`/`stop()`.
- Preserve environment/dev gating, current protocol-3 semantics, idempotence, and bounded subprocess behavior.
- Ensure non-GNOME runtimes perform no GNOME cleanup.
- Replace launcher cleanup tests with runtime lifecycle assertions only after parity passes.
- Leave the temporary plugin-side `load.py` cleanup until owner shutdown is reliable in Steps 10–13.

**Test requirements**

- Unit tests for GNOME startup recovery, normal stop, repeated stop, partial start, and non-GNOME no-op behavior.
- GUI launcher tests for root stop ordering and no private imports.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_launcher_shell_raster_shutdown.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_application_composition_root.py overlay_client/tests/test_backend_architecture_boundary.py -q`
  - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_application_composition_root.py -q`
  - `git diff --check`

**Integration**

Step 8's GNOME adapter now owns its client-local lifecycle. The plugin fallback cleanup remains deliberately temporary until the authenticated owner path can guarantee client shutdown.

**Demo**

Start and stop the client through the new root and show exactly one GNOME cleanup owned by the runtime, with the launcher containing no private presentation import.

## Step 10: Add the atomic authenticated owner launch record and handshake

**Objective**

Promote the watchdog-launched loopback client connection to one authenticated owner role while preserving existing content/settings/controller transport.

**Implementation guidance**

- Atomically write owner-transport schema version 1 with port, fresh secret token, opaque owner ID, expected role/version, and timing policy.
- Pass only the record path to the client; never put the token on the command line or in logs.
- Add bounded `owner_hello`/accept/reject frames and bind exactly one connection to the owner role.
- Separate any retained CLI/controller role so it cannot renew ownership or receive secrets.
- Restrict record permissions where supported and delete only the stopping instance's record.

**Test requirements**

- Unit tests for atomic records, schema validation, permissions, token/role acceptance, rejection, multiple clients, bounded frames, and redaction.
- Transport tests for owner/content coexistence.
- Harness tests are mandatory because `load.py`, server, launch, and watchdog wiring change.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_owner_transport.py tests/test_controller_launcher.py tests/test_harness_backend_selection_wiring.py -q`
  - `overlay_client/.venv/bin/python -m pytest -m harness -q`
  - `git diff --check`

**Integration**

The existing broadcaster still carries existing payloads. The Step 5 root receives an authenticated `OwnerSession`, but disconnect behavior remains transitional until Step 11.

**Demo**

Launch one valid client successfully, reject a second/invalid owner without exposing secrets, and continue sending an unchanged overlay content payload.

## Step 11: Enforce owner heartbeat, terminal EOF, and graceful watchdog shutdown

**Objective**

Make the owner stream authoritative: clean EOF/shutdown stops the client immediately, missed heartbeats bound half-open loss, and the watchdog escalates only after a graceful cleanup interval.

**Implementation guidance**

- Send 2-second owner heartbeats and use an injected monotonic approximately 6-second loss deadline.
- Treat clean EOF and explicit shutdown as terminal; an owned client never reconnects.
- Stop new updates, hide, stop the runtime, acknowledge when possible, quit Qt, and exit exactly once.
- Let the plugin coordinator await `client_stopped` off the Tk callback path, then close and escalate terminate/kill only on timeout.
- Keep release timing configurable from the authenticated record; add a visible developer-only debugger override.

**Test requirements**

- Unit/transport tests for deadlines, clean EOF, explicit shutdown, half-open/no-heartbeat, late heartbeat, duplicate stop, malformed frames, backpressure, and reconnect prohibition.
- Harness tests for normal plugin stop, abrupt server loss, EDMC restart/new identity, cleanup grace, and watchdog escalation.
- Manual suspend/resume and debugger-pause probes; record results without silently retuning defaults.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_owner_transport.py overlay_client/tests/test_data_client.py tests/test_lifecycle_tracking.py tests/test_harness_plugin_hooks_contract.py -q`
  - `overlay_client/.venv/bin/python -m pytest -m harness -q`
  - `git diff --check`

**Integration**

Owner loss now drives the Step 5 root's idempotent stop and Step 9 runtime cleanup. A restarted EDMC always launches a new client.

**Demo**

Show immediate cleanup on orderly plugin stop, bounded client exit after simulated missed heartbeats, and watchdog escalation only when a fake client refuses to stop.

## Step 12: Replace synchronous Tk status requests with pushed, cached backend status

**Objective**

Make preferences/status reads immediate and Tk-safe by caching client-pushed immutable snapshots instead of waiting on a network `threading.Event`.

**Implementation guidance**

- Push status revisions from the client over the authenticated channel when relevant fields change.
- Store the latest valid snapshot, receipt time, schema state, and connection state in `_PluginRuntime`.
- Make `get_backend_status()` return the cache immediately and queue refresh requests asynchronously.
- Display stale/disconnected/incompatible state clearly; never pretend a cached healthy snapshot is current.
- Synchronize worker writes and Tk reads without performing Tk operations from workers.

**Test requirements**

- Unit tests for monotonic revisions, stale age, disconnect state, incompatible payloads, and immutable cache reads.
- Harness tests for status push, preferences open with a silent client, fresh-client cache replacement after EDMC restart, and shutdown safety.
- Add a timing assertion that the Tk-facing read does not wait on network/helper activity.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_platform_controller_backend_status.py tests/test_harness_backend_status_roundtrip.py tests/test_harness_prefs_roundtrip.py tests/test_preferences_panel_controller_tab.py -q`
  - `overlay_client/.venv/bin/python -m pytest -m harness -q`
  - `git diff --check`

**Integration**

This keeps the transitional status payload initially but establishes the push/cache path consumed by schema version 1 in Step 20.

**Demo**

Open preferences while the fake client deliberately withholds responses; the panel renders cached/stale status immediately and updates when a later push arrives.

## Step 13: Remove GNOME-specific lifecycle behavior from `load.py`

**Objective**

Complete backend-neutral plugin lifecycle ownership by deleting plugin-side GNOME startup/stop cleanup and relying on the authenticated client/runtime shutdown contract.

**Implementation guidance**

- Remove private GNOME imports, environment checks, and D-Bus cleanup calls from `load.py`.
- Preserve only backend-neutral server/watchdog/data/settings orchestration.
- Ensure startup recovery remains in the Step 9 GNOME runtime and abnormal cleanup remains temporarily covered by current helper behavior until protocol 4.
- Keep plugin stop bounded and worker-owned; do not touch Tk from shutdown workers.
- Strengthen the architecture boundary to prohibit future compositor-private plugin imports.

**Test requirements**

- Harness tests are mandatory for plugin start, normal stop, client refusal, repeated stop, and EDMC restart.
- Architecture/source tests assert no private GNOME lifecycle import or behavior in `load.py`.
- Run:
  - `overlay_client/.venv/bin/python -m pytest tests/test_harness_plugin_hooks_contract.py tests/test_harness_integration.py overlay_client/tests/test_backend_architecture_boundary.py -q`
  - `overlay_client/.venv/bin/python -m pytest -m harness -q`
  - `git diff --check`

**Integration**

Steps 9 and 11 now provide primary cleanup authority. This step removes the last plugin-side compositor behavior before adding independent external expiry.

**Demo**

Start and stop through the EDMC harness, show client/runtime cleanup and process exit, and mechanically prove that `load.py` contains no GNOME presentation import or dispatch.

## Step 14: Land GNOME helper protocol 4 ownership leases as one coordinated increment

**Objective**

Update the client and GNOME extension together so every presentation mutation requires one non-preemptive owner lease.

**Implementation guidance**

- Add protocol-4 acquire, renew, release, sanitized ownership query, and token-authorized apply semantics.
- Generate a helper lease token independently from the EDMC owner token.
- Make acquire/release idempotent for the active owner and reject invalid tokens.
- Clamp requested lease duration to extension policy and return only the effective non-secret duration.
- Remove `REPLACE` service-name behavior unless current validation proves it necessary.
- Update extension metadata/source, installer/update behavior, protocol fixture, client validation, and restart/session instructions together.
- Do not maintain dual protocol operation; protocol 3 mismatch fails closed after this increment.

**Test requirements**

- Pure injected-clock tests for lease state and secret-safe results.
- Client tests prove every mutating presentation request carries active authority.
- Extension source/manifest/protocol-fixture tests cover Shell 46–50 and protocol 4.
- Isolated D-Bus/GJS tests where supported; otherwise document environment skip and require the manual helper smoke before completion.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_dbus_health.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_gnome_helper_presentation_runtime.py tests/test_gnome_shell_extension_manifest.py -q`
  - `git diff --check`

**Integration**

The Step 8 GNOME runtime owns the lease manager. Existing Phase 19 presentation payload semantics remain unchanged except for required lease authorization.

**Demo**

Acquire one lease, apply windowed/fullscreen presentation, renew, release, and show that a missing or incorrect token cannot mutate Shell state.

## Step 15: Add independent helper expiry and non-preemptive restart/conflict handling

**Objective**

Ensure external GNOME state clears without client cleanup and overlapping clients cannot preempt a healthy owner.

**Implementation guidance**

- Run extension-owned GLib expiry against monotonic time with the initial approximately 10-second deadline.
- Clear actors, raster state, attachment, suppression, renderer ownership, cached identity, and transition state through one idempotent operation.
- Return sanitized `ownership_conflict` for another token without owner metadata.
- Let a fresh client publish a visible wait/conflict state and retry with bounded jitter until normal release or expiry.
- Clear all hosted state on extension disable or D-Bus name loss.

**Test requirements**

- Pure/isolated tests for expiry without requests, repeated clear, competing tokens, same-token retries, release-versus-expiry races, clock behavior, and secret redaction.
- Harness/integration test for EDMC restart launching a fresh client while the old lease remains.
- Manual extension disable/re-enable and Shell restart checks.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_lease.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_backend_status_roundtrip.py -q`
  - `overlay_client/.venv/bin/python -m pytest -m harness -q`
  - `git diff --check`

**Integration**

Protocol 4 from Step 14 now supplies the independent orphan-cleanup layer required after Step 13 removes plugin cleanup.

**Demo**

Crash the fake client without release and show complete helper-state expiry; launch a second client before expiry, observe conflict without preemption, then acquire after expiry.

## Step 16: Couple EDMC ownership health to backend lease renewal and recovery

**Objective**

Complete hierarchical lifecycle behavior so helper renewals occur only while EDMC ownership is healthy and transient post-start helper loss recovers without runtime reconstruction.

**Implementation guidance**

- Drive the initial 2-second helper renewal only from a healthy owner session and active runtime.
- On owner loss, atomically stop renewals, hide, stop runtime components, release the lease, and exit.
- Map transient post-acquisition D-Bus/helper loss to degraded/hidden state and bounded live recovery.
- Keep construction-time missing/incompatible helper restart-required; do not reselect or reconstruct.
- Add one startup legacy-state recovery before protocol-4 acquisition.
- Correlate safe owner/client/backend/helper lifecycle events without sharing tokens or clock origins.

**Test requirements**

- Unit/integration tests for owner-loss ordering, renew scheduling, late renew response, transient helper failure/recovery, startup legacy clear, lease loss, duplicate stop, and client crash.
- GUI tests prove modes without a valid presenter stay hidden.
- Manual suspend/resume, lock/unlock, Overview, and debugger-pause observations finalize or retain initial timing.
- Compare Step 3 performance measures and investigate unexpected call-rate/latency changes.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_owner_transport.py overlay_client/tests/test_gnome_helper_lease.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_application_composition_root.py -q`
  - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py -q`
  - `git diff --check`

**Integration**

EDMC owner health from Step 11, runtime lifecycle from Step 9, and helper leases from Steps 14–15 now form one bounded ownership chain.

**Demo**

Show EDMC loss stopping renewals and cleaning immediately, client crash clearing externally by expiry, and a transient helper transport failure hiding then recovering the same runtime.

## Step 17: Converge GNOME Wayland to one production identity and fail-closed selection

**Objective**

Remove Shell raster as a backend identity and make one `gnome_shell_wayland` runtime own managed-PyQt windowed and Shell-raster fullscreen presenters.

**Implementation guidance**

- Make compatible helper availability a construction-time prerequisite.
- Return unavailable/incompatible GNOME runtime status with restart-required instead of selecting an unrelated fallback.
- Move active presenter/transition reporting to diagnostic state, never generic dispatch.
- Remove the production `gnome_shell_raster` override and filter presenter forcing into developer-only controls.
- Keep the developer old/new architecture toggle until Step 24; it selects routes, not backend identities.
- Preserve supported windowed managed-PyQt operation and forbid automatic managed-PyQt borderless-fullscreen fallback.

**Test requirements**

- Selector/override/status/runtime tests for one identity, helper prerequisite, restart requirement, presenter diagnostics, and invalid stale override reset.
- Phase 19 tests for every presenter transition and monitor handoff.
- GUI/manual matrix slice at 100% and 125% for both stable modes and both transition directions.
- Compare Step 3 latency/work/invariant metrics.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_override_options.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_presentation_transition.py -q`
  - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py -q`
  - `git diff --check`

**Integration**

The one GNOME runtime from Step 8 and lease ownership from Step 16 become the only production GNOME identity. The old route remains solely for architectural rollback.

**Demo**

Start in windowed mode, enter borderless fullscreen, hand off monitors both ways, return windowed, and show one immutable backend identity with changing opaque presenter diagnostics.

## Step 18: Add operational native-X11 probes and environment-scoped support policy

**Objective**

Select and classify `native_x11` from required ICCCM/EWMH behavior while certifying support separately for validated GNOME/Mutter environments.

**Implementation guidance**

- Probe the X11 capabilities required for tracking, geometry, presentation/stacking, click-through, focus, and mode behavior.
- Record sanitized window-manager identity/version as evidence, not primary selection.
- Add the narrow `WindowManagerPolicy` seam with generic default behavior.
- Add a Mutter-specific policy only if the GNOME 46 native-X11 matrix proves a difference generic capability handling cannot represent.
- Map capable unvalidated window managers to `unvalidated_operational`; never inherit GNOME support.

**Test requirements**

- Unit/contract tests with injected X11 capability sets, missing requirements, support-record lookup, and generic policy behavior.
- Existing X11 tracker/presentation tests remain regression anchors.
- Run the full GNOME/Mutter native-X11 matrix at 100%/125%, two monitors/negative coordinates, transitions, Alt-Tab, and Overview.
- Add Mutter policy tests only if such code is introduced.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_selector.py overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_native_x11_probes.py -q`
  - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_follow_surface_mixin.py -q`
  - `git diff --check`

**Integration**

Native X11 uses the Step 7 runtime contracts and Step 1 status axes. No GNOME helper behavior enters X11 generic code.

**Demo**

Show the same `native_x11` runtime as supported under the validated GNOME/Mutter key, unvalidated-operational under another capable WM fixture, and unavailable when a required capability is missing.

## Step 19: Make XWayland explicit and other Wayland environments unimplemented

**Objective**

Stop nominal native-Wayland identities from constructing a shared runtime or claiming true-overlay support while preserving XWayland as an explicit degraded compatibility choice.

**Implementation guidance**

- Keep `xwayland_compat` separate from native X11 even when reusing XCB/tracker internals.
- Register stable unimplemented descriptors for KWin, wlroots, Hyprland, generic Wayland, COSMIC, and gamescope.
- Return detected environment/probe evidence and `unimplemented` support without constructing transitional `_WaylandIntegration`.
- Filter the user override list to valid supportable choices, primarily XWayland; keep internal identities developer-only.
- Unknown/stale overrides reset safely and report restart implications.

**Test requirements**

- Selector, registry, bundle, override, architecture, and status tests for each placeholder and XWayland identity.
- Replace transitional tests that expect shared Wayland integrations only after new placeholder tests pass.
- Basic manual GNOME Wayland XWayland smoke for startup, tracking/presentation baseline, degraded status, and clean shutdown.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_override_options.py overlay_client/tests/test_backend_registry.py overlay_client/tests/test_backend_architecture_boundary.py -q`
  - `git diff --check`

**Integration**

The Step 4 registry now truthfully represents every detected Linux environment without adding future compositor behavior or changing generic consumers.

**Demo**

Probe GNOME/XWayland and show a degraded operational runtime; probe each out-of-scope Wayland fixture and show a distinct unimplemented descriptor with no shared presenter construction.

## Step 20: Migrate every backend control-plane consumer to schema version 1

**Objective**

Switch the client, plugin, controller, preferences/status UI, settings, collector interface, and tests together to the approved backend envelope and settings schema.

**Implementation guidance**

- Replace transitional family/instance/classification/helper/fallback payloads with the schema-version-1 envelope.
- Use separate settings schema version 1 for automatic selection and environment-filtered compatibility override.
- Update status tables to show support policy, evidence level, health, restart requirement, ownership, active presenter, and normalized failures without collapsing dimensions.
- Reject unknown versions clearly; reset stale backend settings safely.
- Preserve all overlay content, group/layout, third-party integration, rendering command, and non-backend preference payloads.
- Remove the Step 1 shadow adapter after every consumer has migrated.

**Test requirements**

- Unit tests for every producer/consumer round trip, unknown versions, stale settings, status table rendering, revision/cache behavior, and compatibility payload invariants.
- Harness tests for selection/status/override/preferences wiring; both unit and harness are required.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_control_plane.py overlay_client/tests/test_platform_controller_backend_status.py tests/test_status_table_model.py tests/test_status_table_payloads.py tests/test_harness_backend_status_roundtrip.py tests/test_harness_backend_override_roundtrip.py tests/test_harness_prefs_roundtrip.py -q`
  - `overlay_client/.venv/bin/python -m pytest -m harness -q`
  - `git diff --check`

**Integration**

Steps 12 and 17–19 provide the live cache and truthful selections serialized through the Step 1 models. All backend control-plane participants move in one coordinated schema increment.

**Demo**

Open preferences/status for healthy GNOME, missing-helper GNOME, validated native X11, unvalidated X11, XWayland, and unimplemented Wayland fixtures and show distinct, correct axes and restart guidance.

## Step 21: Publish support evidence and extend the privacy-safe diagnostic collector

**Objective**

Create the public support/evidence workflow and generate a reviewable redacted backend report suitable for community success and failure evidence.

**Implementation guidance**

- Add machine-readable JSON policy/evidence matrix, generated Markdown terminology/matrix, structured report template, privacy guide, and release validation record layout.
- Seed GNOME 46, Shell 47–50, native X11, XWayland, and unimplemented environment records truthfully.
- Extend the Linux collector to consume schema version 1 and output only allowlisted probes, support/evidence, health, ownership summary, lifecycle events, presenter/transition state, bounded failures, and optional performance summary.
- Make user review explicit before sharing.
- Add a reviewed workflow for turning community reports into evidence changes and release notes; reports never mutate support policy automatically.

**Test requirements**

- Unit/source tests for matrix schema, generated Markdown consistency, evidence record references, report-template fields, collector parsing, bounded histories, and privacy redaction.
- Negative fixtures include tokens, raw IDs, personal paths, titles, command lines, and broad environment fields and assert none survive.
- Run:
  - `overlay_client/.venv/bin/python -m pytest tests/test_debug_collectors.py tests/test_backend_support_matrix.py overlay_client/tests/test_backend_control_plane.py -q`
  - `git diff --check`

**Integration**

The collector and public artifacts consume the Step 20 envelope and Step 3 performance format. No new runtime dispatch or support inference is introduced.

**Demo**

Generate a local report for each support/health combination, review it as a user, and validate that it references the public evidence record while containing no secret or personal diagnostic material.

## Step 22: Automate and satisfy the EDMC compliance gate

**Objective**

Remediate all known EDMC compliance failures and produce a reproducible yes/no release report backed by automated checks and harness evidence.

**Implementation guidance**

- Re-check upstream `docs/Releasing.md`, update `docs/compliance/edmc_python_version.txt` and its checker from the stale 3.10.3 baseline, and validate supported plugin-runtime syntax/dependencies.
- Add dated evidence of EDMC release/discussion review before release.
- Mechanically audit supported imports, logger naming/exception handling, `config.appversion` gates, typed namespaced config, locale parsing, `timeout_session`, debug routing, dependency packaging, and operational `print`.
- Confirm Steps 12–13 removed synchronous status waits and plugin-side GNOME cleanup.
- Remediate any `No`; do not waive it silently. Keep controller/client Python >=3.10 separate from the EDMC plugin runtime baseline.

**Test requirements**

- Unit/source checks for compliance rules plus mandatory harness coverage for plugin lifecycle/preferences.
- Run:
  - `overlay_client/.venv/bin/python scripts/check_edmc_python.py`
  - `overlay_client/.venv/bin/python -m pytest tests/test_harness_plugin_hooks_contract.py tests/test_harness_prefs_roundtrip.py tests/test_logging_and_version_helper.py tests/test_preferences_persistence.py tests/test_debug_collectors.py -q`
  - `overlay_client/.venv/bin/python -m pytest -m harness -q`
  - `make check`
  - `git diff --check`

**Integration**

This gate audits the actual converged plugin/control plane rather than the discarded historical Phase 5 structure. Failures feed back into the owning earlier step and its tests.

**Demo**

Generate the release compliance table with an explicit evidence link and `Yes` or justified not-applicable result for every required item, with no unresolved `No`.

## Step 23: Publish the future-backend implementation guide

**Objective**

Document and prove the process a future backend must follow without implementing KDE/KWin or another compositor.

**Implementation guidance**

- Document registration, operational probes, runtime composition, discovery/presentation/input behavior, lifecycle/orphan cleanup, support/evidence/health, safe failures, diagnostics, tests, manual evidence, and completion rules.
- Use the Step 2 paper backend as the minimal example and link to the reusable contract test factory.
- Include a checklist that forbids compositor-private changes to generic consumers and nominal identity-only support.
- Explain optional helper lifecycle and capture vocabulary without inventing a capture behavior contract.
- Verify all example names/paths against the converged source.

**Test requirements**

- Run the paper backend contract suite and architecture scans.
- Add a documentation/source consistency test for referenced public interfaces and test-factory entry points.
- Run:
  - `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_runtime_contracts.py overlay_client/tests/test_backend_architecture_boundary.py tests/test_backend_implementation_guide.py -q`
  - `git diff --check`

**Integration**

The guide documents the production contracts completed in Steps 17–20 and the evidence workflow from Step 21; it does not create an unused production backend.

**Demo**

Follow the guide to register a second in-memory test backend and pass the reusable suite without editing launcher, follow, lifecycle, status, or UI consumers.

## Step 24: Pass convergence acceptance and remove the old GNOME architecture

**Objective**

Prove the converged runtime against all automated, performance, manual, support, and compliance gates, then delete the temporary GNOME consumer-dispatch architecture and its rollback toggle.

**Implementation guidance**

- Before deletion, require old/new observable parity, all Phase 19 tests, GNOME 46 native-Wayland full matrix, lifecycle/lease/crash/restart evidence, accepted performance comparison, privacy/schema tests, and explicit rollback removal approval.
- Delete GNOME enum/helper dispatch from `backend.consumers`, direct private imports, obsolete `gnome_shell_raster` production identity/override, architecture toggle, transitional adapters, and superseded tests.
- Keep only explicitly approved diagnostic/performance or narrowly scoped behavioral toggles; none may select a second architecture.
- Complete the GNOME/Mutter native-X11 matrix, XWayland smoke, Shell 47–50 evidence levels, support artifacts, compliance report, and future-backend guide.
- Update phase/checklist status and record exact final evidence. Do not claim deferred mixed-scale/vertical/primary-monitor/exclusive-fullscreen support.

**Test requirements**

- Strengthened architecture tests prove no private compositor dispatch in generic launcher/follow/lifecycle/status/control-plane code.
- Run all targeted suites named in prior steps, then:
  - `overlay_client/.venv/bin/python -m pytest`
  - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest`
  - `overlay_client/.venv/bin/python -m pytest -m harness -q`
  - `make check`
  - `make test`
  - `overlay_client/.venv/bin/python scripts/check_edmc_python.py`
  - `git diff --check`
- Run and archive the full manual support/performance matrix. Record any platform-dependent skip with reason; required acceptance cases cannot be skipped.

**Integration**

This step removes the last second architecture only after every replacement from Steps 1–23 is active and proven. The resulting production root owns one runtime and all generic consumers are backend-neutral.

**Demo**

Launch the production client with no architecture toggle, demonstrate supported GNOME Wayland and GNOME/Mutter native X11 behavior, show truthful XWayland/unimplemented status, exercise bounded owner/helper cleanup, and pass forbidden-import scans plus the final evidence gates.

## Completion Criteria

The plan is complete when all 24 checklist items and phase stages are marked complete and Step 24 evidence proves:

- one launcher composition root owns one matching runtime;
- generic consumers and plugin lifecycle contain no compositor-private behavior dispatch;
- GNOME Wayland and GNOME/Mutter native X11 satisfy their support contracts;
- XWayland and out-of-scope environments report truthfully;
- support, evidence, health, ownership, and diagnostics remain independent;
- owner loss and helper loss clear resources within validated bounds;
- Phase 19 and performance invariants pass;
- EDMC compliance contains no unresolved `No`;
- the old architecture is removed; and
- the future-backend guide and reusable suite are usable.

After the user approves this implementation plan, the PDD workflow may create `summary.md`. Approval of the plan still does not authorize implementation code changes unless the user separately asks to begin implementation.
