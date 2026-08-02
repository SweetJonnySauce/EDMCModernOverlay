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
- [x] Step 2: Add behavioral runtime contracts and the reusable paper-backend contract suite
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
| 1.2 | 2 | Behavioral contracts and paper-backend suite | Completed |
| 1.3 | 3 | Performance evidence schema, capture adapter, reduced oracle, and tooling | Completed |
| 1.4 | 3 | Cold-start/remap correction and capture-rotation robustness | Completed |
| 1.5 | 3 | Pre-optimization reduced-v2 matrix retained as historical evidence | Paused at 12/42 |
| 1.6 | 3 | Quiet diagnostic configuration and normal-use state | Completed |
| 1.7 | 3 | Backend-owned stable-target query pressure reduction | Completed |
| 1.8 | 3 | Proven unchanged-repaint suppression | Completed |
| 1.9 | 3 | Controlled helper-disabled/helper-enabled A/B and reviewed pressure bounds | In progress; automated gate passed, live preflight blocked |
| 1.10 | 3 | Manual behavior regression and quiet-soak validation | Not started |
| 1.11 | 3 | Clean post-optimization 42-capture baseline and migration-regression thresholds | Not started |

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

Run commands from the repository root. Use the repository environment at `.venv`.

- Targeted unit/harness tests: `.venv/bin/python -m pytest <test paths> -q`
- Headless suite: `.venv/bin/python -m pytest`
- GUI-enabled suite: `PYQT_TESTS=1 .venv/bin/python -m pytest`
- Harness suite: `.venv/bin/python -m pytest -m harness -q`
- Lint/typecheck/full test gate: `make check`
- Project test target: `make test`
- EDMC baseline check: `.venv/bin/python scripts/check_edmc_python.py`
- Patch hygiene: `git diff --check`

On Windows Python 3.13+, use `.venv\Scripts\python scripts\run_pytest_safe_windows.py <pytest args>` only if the documented `tmp_path` `WinError 5` occurs.

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
  - `.venv/bin/python -m pytest overlay_client/tests/test_backend_status.py overlay_client/tests/test_backend_control_plane.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_runtime_contracts.py -q`
  - `git diff --check`

**Integration**

The paper runtime serializes through Step 1's envelope and establishes the test factory later supplied by GNOME, native X11, and XWayland.

**Demo**

Run one deterministic paper runtime from construction through target appearance, present, input change, owner loss, repeated stop, and final serialized status without importing any compositor module.

**Completion evidence — 2026-07-19**

- Added immutable normalized target, frame, geometry/coordinate-space, presentation,
  interaction, helper-health, presentation-state, input-state, and lifecycle records plus
  runtime-checkable runtime/discovery/presentation/input/helper protocols.
- Kept presentation and input behavior independently revisioned and gave their snapshot methods
  distinct names so separate objects and one combined Python implementation both satisfy the
  contracts without identity coupling.
- Added directly constructible unavailable and unimplemented runtimes with stable inert
  services, exact selected identity, independent support/evidence/health, fail-closed
  presentation, one-start/terminal-stop behavior, deadline-aware reverse cleanup, bounded
  normalized failures, and schema-v1 status.
- Added a test-only deterministic paper backend, injected clock/failure/target/owner controls,
  resource ledger, backend test-factory protocol, and reusable observable contract assertions.
  No production selector, bundle, launcher, consumer, or registration imports the paper backend;
  production routing remains unchanged.
- Added `overlay_client/tests/test_backend_runtime_contracts.py` and
  `overlay_client/tests/backend_runtime_testkit.py`; retained all assertions in
  `overlay_client/tests/test_backend_contracts.py` unchanged.
- Targeted unit/contract gate: 36 passed. Named paper lifecycle demo: 1 passed. Headless suite:
  1,197 passed, 41 skipped. `make check`: ruff and mypy passed, then GUI-enabled pytest passed
  with 1,234 passed and 21 skipped. `make test`: 1,234 passed and 21 skipped.
- Focused mypy passed for the three new implementation/test-support modules. The EDMC Python
  compatibility-floor check passed under the documented development override and repeated the
  existing 64-bit-versus-preferred-32-bit warning. `git diff --check` passed.
- The skipped tests retain their existing environment/runtime gates. No harness or manual
  compositor test was required because Step 2 changes no EDMC hook or production behavior.
- Rollback remains additive: remove the behavioral/failure-runtime modules, exports, test-only
  paper suite, focused tests, and this evidence; the shipped runtime route is unchanged.

## Step 3: Capture the repeatable pre-migration performance baseline

**Objective**

Create the scenario manifest and summary tooling, reduce proven unnecessary stable helper-query
and unchanged repaint pressure in the shipped architecture, then capture a coherent clean
current-behavior baseline before production routing changes begin.

**Implementation guidance**

- Reuse existing client raster, helper, transition, repaint, and CPU diagnostics.
- Add a versioned scenario manifest for stable windowed/fullscreen, both transition directions, both monitor handoffs, Alt-Tab, and Overview at 100% and 125%.
- Add a small pure summary tool for median, p95, maximum, counts, helper/raster work, and idle CPU.
- Store raw sanitized captures and summaries under the release validation evidence tree; never store secrets or personal paths.
- Disable capture diagnostics before pressure measurement and ordinary use. Quiet runs retain
  only allowlisted bounded counters, state changes, and normalized failures.
- Test and correct the existing GNOME stable-target suppression rather than add an overlapping
  throttle. Use backend-owned explicit state and an injected monotonic clock; the active
  transition guard cannot by itself force target enumeration every 500 ms cycle.
- Preserve immediate invalidation/recovery for explicit presentation refresh, failed/unavailable
  responses, target loss/recovery, presenter or mode transitions, stale raster state, and
  relevant focus, monitor, geometry, workspace, minimize, fullscreen, and exposure changes.
- Preserve the cold-start deferred-remap one-shot refresh: it bypasses matching-success and
  mismatch suppression exactly once, then returns to steady no-op behavior.
- Audit existing visual-snapshot deduplication before changing repaint behavior. Suppress only
  work proven to leave rendered output unchanged, and keep repaint requests, Qt update/paint,
  and Shell raster build/reuse as separate measured contracts.
- Run the four-cell helper-disabled/helper-enabled A/B after implementation and before restarting
  the matrix. Stop immediately on visible Shell instability; Firefox failure reproduction is not
  part of acceptance.
- Preserve the 12 accepted reduced-v2 captures and the two superseded long-form captures under
  their original identities. They are historical pre-optimization evidence and cannot be mixed
  into the clean baseline or threshold population.
- After A/B and manual regression gates pass, create a new post-optimization evidence identity
  and restart the representative 14-scenario by three-repetition matrix at 0/42.
- Derive pressure-reduction acceptance bounds from the quiet A/B and record them in its report;
  they do not populate `thresholds.json`.
- Determine migration-regression investigation thresholds from the complete coherent baseline
  variance and record them in `thresholds.json` before Step 5.

**Test requirements**

- Unit tests for manifest validation, sample aggregation, clock-domain separation, redaction, and threshold comparison.
- Unit tests for stable matching cycles, monotonic deadline expiry, transition-guard interaction,
  forced refresh, errors/recovery, target and presentation invalidation inputs, stale raster
  state, and the post-remap exactly-once refresh contract.
- Unit tests for visual fingerprints and unchanged repaint suppression, including TTL-only and
  metadata-only refresh plus every supported content/style/geometry/group/override/expiry/
  animation/scale/mode/monitor/visibility recovery trigger.
- No harness test is selected while this remains in pure/runtime services. If `load.py`, EDMC
  hooks, plugin lifecycle, or Tk wiring is touched, add and run a harness test before landing.
- Controlled GNOME A/B at stable windowed monitor A/100%: A1 client stopped/helper disabled, A2
  client running/helper disabled, B1 client stopped/helper enabled with diagnostics off, and B2
  both running with diagnostics off. Use five-minute warm-up and three 60-second samples per cell
  with interleaved order where practical.
- Manual baseline capture on GNOME Shell 46/Ubuntu 24.04.4 using fixed fixture, geometry, warm-up, duration, and repetitions.
- Run:
  - `.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_payload_dedupe.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py -q`
  - `.venv/bin/python -m pytest overlay_client/tests/test_backend_performance_capture.py overlay_client/tests/test_backend_performance_summary.py tests/test_debug_collectors.py -q`
  - `make check`
  - `make test`
  - `git diff --check`
- This step cannot be marked complete without the manual baseline; if the target environment is unavailable, Steps 1–2 may stand but production routing must not proceed.

**Integration**

The clean post-optimization manifest and migration-regression thresholds become the comparison
gate for Steps 8, 16, 17, and 24. The pressure-reduced shipped architecture is the oracle. The
12 incident-era captures remain diagnostic history and do not define candidate thresholds.

**Demo**

Demonstrate materially reduced stable helper-query/repaint request rates with no startup,
unfocused attachment, focus, transition, placement, Alt-Tab, Overview, click-through, or privacy
regression, then generate a sanitized comparison-ready baseline for all 42 repetitions using the
shipped architecture.

**Execution sequence**

1. Stage 1.6 restores a quiet normal-use configuration and proves per-query diagnostic journal
   events are absent before measurement.
2. Stage 1.7 adds RED unit tests for the transition-guard/stable-cache interaction, implements
   the smallest backend-owned correction, and proves every invalidation/recovery contract.
3. Stage 1.8 uses bounded per-reason evidence to locate unchanged repaint requests, adds RED unit
   tests at the smallest pure seam, and suppresses no-op scheduling without weakening fallbacks.
4. Stage 1.9 runs the controlled four-cell A/B and derives reviewed pressure-reduction acceptance
   bounds from repeated quiet measurements rather than intuition or one favorable sample. These
   bounds stay in the A/B report and do not become `thresholds.json`.
5. Stage 1.10 repeats two terminal-focused clean starts, one game-focused start, both mode
   transitions, both-monitor placement, Alt-Tab, Overview, and one quiet soak.
6. Stage 1.11 creates a new manifest/evidence identity, restarts at 0/42, completes manual Phase
   19 review, analyzes variance, freezes reviewed migration-regression thresholds, and only then
   completes Step 3.

**Progress evidence — 2026-07-20 (automated tooling complete; manual gate pending)**

- Added a strict standard-JSON schema-v1 manifest/capture/summary/threshold boundary, separate
  client/helper clock-domain enforcement, privacy rejection, deterministic nearest-rank p95,
  normalized helper/raster/repaint/frame/CPU aggregation, invariant-first blocking, and fixed
  dual-threshold comparison in `overlay_client/backend/performance_evidence.py`.
- Added a thin validate/summarize/compare CLI, a committed 36-scenario GNOME 46 manifest for
  uniform 100%/125% left-of-primary dual-monitor layouts, and an exact manual capture,
  invariant-review, evidence-layout, and threshold-freeze workflow. The manifest distinguishes
  Mutter/Qt's normalized global geometry from its validated primary-relative negative
  projection so evidence records real compositor values without losing the design's negative
  coverage.
- The legacy broad capture scripts were rejected for committed evidence because they include
  command lines and unsanitized logs. Added a diagnostics-gated allowlist-only event at the
  existing generic presentation-cycle seam, a pure capture adapter, and an interactive runner
  that enforces the fixed warm-up/idle/observation intervals and manual checklist before strict
  revalidation and write. Unit tests prove private target/title/path fields cannot enter the
  event or normalized artifact.
- Added `overlay_client/tests/test_backend_performance_summary.py`; the focused unit/collector
  gate passes with 85 tests. Headless pytest passes with 1,280 passed and 41 skipped.
  `make check` and `make test`, using the repository's intact `overlay_client/.venv` because the
  documented root `.venv` is absent, pass with 1,316 passed and 21 skipped; whole-repository
  Ruff and configured mypy also pass.
- No production selector, launcher, presentation decision, helper default, `load.py`, Tk hook,
  content payload, or settings behavior changed. The new follow-surface timing/log call is a
  no-op unless the explicit capture diagnostic flag is enabled; capture adaptation remains pure
  and additive.
- The manual baseline is not captured. The host matches Ubuntu 24.04.4/GNOME Shell 46 and has
  two matching 3440x1440 displays. A host-session recheck on 2026-07-20 confirmed EDMC, Elite,
  and the overlay client running; helper version `1.0.0`/protocol `3` healthy on D-Bus with its
  full target/presentation feature gate; and live rectangle-matched
  `target_found`/`presentation_applied` cycles. The 100% topology is now verified with the
  secondary monitor physically left of the primary; observed coordinates are `(0, 0)` and
  `(3440, 0)`, with a validated primary-relative projection of `(-3440, 0)` and `(0, 0)`.
  The client is capture-configured and emitted real allowlisted events, but the first 100%
  managed-windowed repetition was aborted before artifact write. Fixture messages and repaint
  requests reached the client while Qt paint counts remained zero; backend diagnostics
  incorrectly reported the surface mapped/content-visible, and the user saw no overlay content.
  A borderless-fullscreen round trip restored the windowed overlay and changed paint counts from
  zero to 6-12 per interval, isolating a cold-start managed-windowed remap/exposure defect rather
  than payload loss. The matrix is blocked at 0/180 accepted repetitions. Corrected cold-start
  managed-windowed presentation,
  the later 125% reconfiguration, five repetitions of every scenario, manual Phase 19 review,
  sanitized summaries, and variance-derived frozen thresholds remain required.
- Step 03, checklist item 3, and Phase stage 1.3 therefore remain incomplete/in progress.
  Step 05 production routing remains gated. No placeholder threshold artifact was created.
- A local test-first correction now treats `QWindow.isExposed()` as mapping proof for surfaces
  covered by the normalized `prepared_surface_requires_mapping` contract and allows one
  controlled post-policy remap per managed-surface generation. Repeated terminal-focused host
  starts proved that a same-stack hide/show is nondeterministic, so the controlled remap now
  hides and primes synchronously, then shows and reapplies platform/click-through state on the
  next Qt event-loop turn. The diagnostics event adds only widget-visible, window-exposed,
  target-focused, mapping-required, geometry-agreement, and bounded paint-count fields; no
  compositor-specific type or enum entered generic follow code. The final Step 03 focused gate
  passes with 126 tests. Host diagnostics then proved that focus corrected attachment without any
  target/requested-rectangle change: the focus transition caused one helper presentation call
  after unfocused cycles had reused a pre-remap cached success. A one-shot generic presentation-
  refresh request now crosses the consumer boundary after deferred map completion, while the
  GNOME runtime privately bypasses its cache for that cycle. Backend boundary/consumer/runtime/
  follow tests pass with 139 tests, and `make check`/`make test` each pass with 1,336 passed/21
  skipped; whole-repository Ruff and configured mypy also pass. Two clean terminal-focused starts
  then passed without focusing Elite, followed by repeated successful live transitions in both
  windowed-to-borderless/fullscreen and borderless/fullscreen-to-windowed directions. Three
  reviewed return-to-windowed sequences completed with visible/exposed, geometry-matched Qt
  surfaces and no warning/error or failure marker. One possible brief missing-overlay observation
  was not reproducible and remains a watch item rather than a recorded invariant failure. The
  manual pre-capture gate is complete and the matrix is ready to restart at repetition 1, but it
  remains 0/180 and this step is not complete.
- The first observation exposed and then test-first corrected an offset-only capture-runner bug
  when `overlay_client.log` rotates. The runner now follows a stable inode/offset cursor through
  numeric rotations and rejects incomplete history. Capture tests pass 15/15, the Step 03 focused
  gate passes 130 tests, and `make check`/`make test` each pass with 1,340 passed/21 skipped. The
  full repetition was rerun twice and independently validated with zero manual failures and an
  empty prohibited-field scan. Those captures are preserved with the superseded full v1 oracle.
- The user approved a reduced v2 oracle: 14 representative scenarios, three repetitions, and
  10-second warm-up/15-second idle/30-second observation timing. It retains both scales,
  presenters, mode directions, monitors, bidirectional fullscreen handoff, Alt-Tab, and Overview
  while removing redundant cross-products. The active matrix restarts at 0/42; Step 03 remains
  incomplete until all reduced captures, summaries, manual review, and thresholds pass.

**Progress amendment — 2026-07-21 (matrix paused for pressure reduction)**

- The reduced-v2 matrix reached 12/42 accepted captures: three repetitions each for 100% stable
  windowed monitor A, stable borderless-fullscreen monitor A, windowed-to-fullscreen monitor A,
  and fullscreen-to-windowed monitor A. All 12 documents independently validated, all eight
  manual invariant fields were false, and prohibited-field scans were empty.
- During later desktop instability, the helper journal showed 3,601 target-query-start events in
  30 minutes—exactly two per second—while the client was stable. Reduced captures also showed
  approximately 816–841 repaint requests per 30 seconds even though managed paint and Shell
  raster-build counts were much lower. The overlay/helper is not established as the Firefox/
  Mutter failure's cause, but it is a plausible load amplifier and unnecessary stable work must
  be reduced before more baseline capture.
- Code review identified that the existing 1.5-second suppressed-target poll is bypassed while
  the transition guard is enabled, which is the leading explanation for querying at the generic
  500 ms follow cadence. Existing payload visual snapshots already deduplicate supported content,
  so repaint work requires source attribution before selecting a suppression seam.
- Stage 1.5 is therefore paused at 12/42. Those captures and the two superseded full-oracle
  captures remain immutable historical evidence. No threshold artifact exists, and none may be
  created from this partial or mixed population.
- Stages 1.6–1.10 now gate a new coherent baseline. After they pass, Stage 1.11 creates a new
  evidence identity and starts at 0/42; continuing with monitor B under the old identity is not
  permitted.

**Progress amendment — 2026-07-21 (Stage 1.6 quiet state complete)**

- The client shadow and developer settings now disable development mode, repaint-detail logging,
  tracing, payload logging, visual outlines, and the debug overlay while retaining repaint
  debounce. No persisted EDMC development-mode override was present.
- The user-local helper developer configuration was backed up before editing. Only diagnostics
  changed from enabled to disabled; enabled full-helper mode and all unrelated fields were
  preserved. After the supported helper reload, health remained healthy at helper version 1.0.0
  and protocol 3 with diagnostics reported disabled.
- A bounded 10-second host-session probe issued 20 real target-state calls with zero failures and
  produced zero filtered per-query or repaint-detail journal events. No target response or private
  diagnostic field was retained.
- SHA-256 verification passed for all 12 reduced-v2 and both superseded full-v1 captures. No
  capture, manifest identity, summary, migration threshold, runtime code, or production route
  changed. Stage 1.7 is next and remains not started.

**Progress amendment — 2026-07-21 (Stage 1.7 stable-target pressure complete)**

- Added focused unit coverage before runtime edits for guarded stable cycles, monotonic deadline
  expiry/rearming, explicit one-shot refresh, target loss/recovery, stale raster refresh, and the
  complete target/presentation signature inputs named by the design.
- RED produced 9 expected failures with 102 passes. The existing transition guard defeated the
  target-query cache, the target throttle hid a required Shell-raster lease refresh, and frame/
  buffer/monitor/output/scale/workspace changes were treated as unchanged.
- Corrected the existing backend-owned cache rather than adding another throttle: guarded stable
  mapped-suppressed cycles now reuse matching state inside the 1.5-second injected-monotonic
  deadline. Pending transitions, forced refresh, failures, surface preparation/recovery, stale
  raster work, and exposure-key changes bypass or invalidate it.
- Expanded the private presentation signature with the missing geometry, monitor, scale, output,
  and workspace facts. Generic follow/consumer interfaces and compositor boundaries are unchanged.
- Focused query/follow tests passed with 111 tests; backend-consumer tests passed with 35 tests;
  targeted ruff, compileall, and `git diff --check` passed. Full project gates remain scheduled
  after the integrated query-plus-repaint milestone. Stage 1.8 is next and remains not started.

**Progress amendment — 2026-07-21 (Stage 1.8 unchanged-repaint suppression complete)**

- Attributed the historical request, Qt paint, Shell-frame preparation, raster encode/reuse, and
  helper-presentation layers separately. For example, 841 requests corresponded to 49 managed
  paints in one stable capture, while a Shell-raster capture recorded 60 frame preparations but
  only one raster build and 59 payload reuses. Request volume was not treated as material-work
  volume.
- Extended the existing supported message/rect/vector visual fingerprint rather than adding a
  competing dedupe system. TTL and incidental metadata refresh expiry/lifecycle state without
  dirtying pixels; plugin/group/override changes and animation bypass preserve repaint; unknown
  or malformed visual state takes the safe repaint fallback.
- Added fixed-cardinality saturating counters for ingest outcomes, repaint request/scheduling
  paths, Qt update/paint work, and Shell-frame preparation outcomes. Detailed traces remain
  gated and no per-cycle release log was added.
- Added a deterministic render identity and reused only successful Shell-frame preparation
  results with complete matching content, renderer settings, target geometry, monitor/output,
  scale, workspace, visibility/mode, request, and diagnostic state. Incomplete state or failure
  is never cached; backend-owned lease refresh and helper presentation remain authoritative.
- Focused RED recorded 11 expected failures and 59 passes. Focused GREEN passed 70 tests; the
  integrated query/repaint/follow slice passed 151; the backend-consumer boundary passed 35;
  targeted Ruff and compileall passed. The milestone `make check` and `make test` gates each
  passed with 1,379 tests and 21 existing environment/runtime skips; repository Ruff and mypy
  passed through `make check`.
- No `load.py`, EDMC hook/lifecycle, Tk wiring, compositor-private generic dispatch, capture,
  evidence identity, threshold, Task 07 A/B, or production route changed. No harness test was
  required. Stage 1.9 is next and remains not started; the capture hold remains active.

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
  - `.venv/bin/python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_registry.py overlay_client/tests/test_backend_architecture_boundary.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_application_composition_root.py overlay_client/tests/test_platform_context.py -q`
  - `PYQT_TESTS=1 .venv/bin/python -m pytest overlay_client/tests/test_application_composition_root.py overlay_client/tests/test_launcher_group_filter.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_runtime_contracts.py -q`
  - `PYQT_TESTS=1 .venv/bin/python -m pytest overlay_client/tests/test_follow_surface_mixin.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_interaction_surface.py overlay_client/tests/test_backend_runtime_contracts.py -q`
  - `PYQT_TESTS=1 .venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_surface.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_presentation_transition.py -q`
  - `PYQT_TESTS=1 .venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_launcher_shell_raster_shutdown.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_application_composition_root.py overlay_client/tests/test_backend_architecture_boundary.py -q`
  - `PYQT_TESTS=1 .venv/bin/python -m pytest overlay_client/tests/test_application_composition_root.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_owner_transport.py tests/test_controller_launcher.py tests/test_harness_backend_selection_wiring.py -q`
  - `.venv/bin/python -m pytest -m harness -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_owner_transport.py overlay_client/tests/test_data_client.py tests/test_lifecycle_tracking.py tests/test_harness_plugin_hooks_contract.py -q`
  - `.venv/bin/python -m pytest -m harness -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_platform_controller_backend_status.py tests/test_harness_backend_status_roundtrip.py tests/test_harness_prefs_roundtrip.py tests/test_preferences_panel_controller_tab.py -q`
  - `.venv/bin/python -m pytest -m harness -q`
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
  - `.venv/bin/python -m pytest tests/test_harness_plugin_hooks_contract.py tests/test_harness_integration.py overlay_client/tests/test_backend_architecture_boundary.py -q`
  - `.venv/bin/python -m pytest -m harness -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_dbus_health.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_gnome_helper_presentation_runtime.py tests/test_gnome_shell_extension_manifest.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_lease.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_backend_status_roundtrip.py -q`
  - `.venv/bin/python -m pytest -m harness -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_owner_transport.py overlay_client/tests/test_gnome_helper_lease.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_application_composition_root.py -q`
  - `PYQT_TESTS=1 .venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_override_options.py overlay_client/tests/test_backend_status.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_presentation_transition.py -q`
  - `PYQT_TESTS=1 .venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_selector.py overlay_client/tests/test_window_tracking_bundle_routing.py overlay_client/tests/test_native_x11_probes.py -q`
  - `PYQT_TESTS=1 .venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_follow_surface_mixin.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_backend_bundles_wayland.py overlay_client/tests/test_backend_bundles_x11.py overlay_client/tests/test_backend_selector.py overlay_client/tests/test_backend_override_options.py overlay_client/tests/test_backend_registry.py overlay_client/tests/test_backend_architecture_boundary.py -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_backend_control_plane.py overlay_client/tests/test_platform_controller_backend_status.py tests/test_status_table_model.py tests/test_status_table_payloads.py tests/test_harness_backend_status_roundtrip.py tests/test_harness_backend_override_roundtrip.py tests/test_harness_prefs_roundtrip.py -q`
  - `.venv/bin/python -m pytest -m harness -q`
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
  - `.venv/bin/python -m pytest tests/test_debug_collectors.py tests/test_backend_support_matrix.py overlay_client/tests/test_backend_control_plane.py -q`
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
  - `.venv/bin/python scripts/check_edmc_python.py`
  - `.venv/bin/python -m pytest tests/test_harness_plugin_hooks_contract.py tests/test_harness_prefs_roundtrip.py tests/test_logging_and_version_helper.py tests/test_preferences_persistence.py tests/test_debug_collectors.py -q`
  - `.venv/bin/python -m pytest -m harness -q`
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
  - `.venv/bin/python -m pytest overlay_client/tests/test_backend_runtime_contracts.py overlay_client/tests/test_backend_architecture_boundary.py tests/test_backend_implementation_guide.py -q`
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
  - `.venv/bin/python -m pytest`
  - `PYQT_TESTS=1 .venv/bin/python -m pytest`
  - `.venv/bin/python -m pytest -m harness -q`
  - `make check`
  - `make test`
  - `.venv/bin/python scripts/check_edmc_python.py`
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
