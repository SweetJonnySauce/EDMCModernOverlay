# Contract Tests and Migration Coverage

## Existing coverage worth preserving

The repository already has strong raw material:

- selector, probe, status, override, bundle, and consumer unit tests;
- architecture-boundary tests preventing direct GNOME dispatch from `follow_surface.py`;
- extensive GNOME helper health, target, presentation, raster-frame, transition, and source tests;
- native X11/XWayland bundle and tracker tests;
- plugin harness tests for backend selection/status/override round trips and plugin lifecycle hooks;
- collector and extension-manifest tests.

Several tests intentionally anchor transitional behavior that must later be replaced: combined presentation/input adapters, nominal out-of-scope Wayland bundles, separate `gnome_shell_raster` identity/override, plugin/launcher GNOME cleanup, and enum-driven GNOME consumers.

## Reusable backend contract suite

Create a parameterized suite driven by a backend test factory. Every implemented backend supplies runtime construction plus fake/injected dependencies. Required contracts:

- immutable identity and one start/stop lifetime;
- idempotent bounded stop, including partial-start failure;
- operational probe evidence and truthful selection;
- discovery target appearance/loss and safe recovery;
- presentation apply/hide/unavailable behavior;
- input click-through/focus behavior independent of presentation identity;
- support/evidence/health separation and schema serialization;
- normalized failure and sanitized diagnostics;
- owner loss and resource cleanup;
- no unsupported fallback claims.

A paper/example backend should implement these contracts with deterministic in-memory components. It proves extension points without pretending to implement KDE/KWin.

## GNOME-specific suite

Layer private tests on top of generic contracts:

- construction prerequisite and protocol mismatch;
- helper lease acquire/renew/release/conflict/expiry;
- transient helper loss and live recovery;
- managed-PyQt windowed versus Shell-raster borderless presenter selection;
- Phase 19 transition state and atomic fullscreen monitor handoff;
- startup recovery, client crash expiry, and extension disable cleanup;
- no presenter means hidden overlay, never unsupported PyQt fullscreen fallback.

Phase 19 invariants must remain explicit assertions: never dual visible presenters, no title-bar/monitor-relative intermediate, black surface, focus trap, unexpected identity, or premature stable-renderer commitment.

## Native X11 and XWayland

Native X11 contract tests should inject ICCCM/EWMH capability evidence and verify that environment support certification remains separate. Add a Mutter policy test only if manual validation discovers behavior generic capabilities cannot express. XWayland receives the generic suite plus selection/degraded-status tests; its manual scope remains the agreed basic smoke test.

## Harness boundary

Any `load.py` or hook-flow change requires harness coverage. The ownership transport adds harness cases for:

- server/launch-record/watchdog order;
- authenticated client ownership and heartbeats;
- plugin stop allowing cleanup before watchdog escalation;
- EDMC crash/restart producing a new identity;
- backend status schema round trips and stale-version failure;
- removal of all GNOME-specific plugin cleanup.

Pure lease, timing, status, selection, and contract logic stays in fast unit tests.

## Staged replacement

| Stage | Test posture |
|---|---|
| Lift | Add new contracts beside current tests; old path remains oracle |
| Route | Run old/new parity tests with injected identical inputs |
| Own | Add liveness/lease/crash tests before moving cleanup ownership |
| Validate | Run automated suite, performance comparison, and manual GNOME matrix |
| Remove | Delete transitional identities/toggles/tests and strengthen forbidden-import scans |

Tests should compare observable results and state transitions, not internal class identity, so future backends can use different internal composition.
