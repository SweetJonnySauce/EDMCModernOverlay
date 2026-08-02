# Research Plan

## Status

Completed on 2026-07-19 and reopened for a focused Step 3 amendment on 2026-07-21.
Requirements clarification was explicitly declared complete before the original pass; Question
35 records the user-approved pressure-reduction and clean-baseline amendment. The amendment
changes planning documents only and does not authorize or modify implementation code.

## Scope

Research the current repository implementation and planning records to establish an evidence-based design foundation for completing `fix219` architecture convergence around the active GNOME/Wayland backend.

GNOME/Wayland is the implementation scope for this project. Future backends—including KDE/KWin and other Wayland compositors—are explicitly out of implementation scope. However, generic contracts, runtime composition, capability models, and lifecycle boundaries must remain backend-extensible and must not embed GNOME-specific assumptions.

The project-level success criterion is that GNOME on Wayland and GNOME on X11 are supported backends, and that the resulting architecture provides stable seams for implementing additional backends later without another generic-runtime redesign. Preliminary research must distinguish native X11 from XWayland compatibility behavior so the supported GNOME/X11 scope can be specified precisely during requirements clarification.

## Topics

1. Map current probe, selector, status, bundle, consumer, and lifecycle flows.
2. Trace GNOME target discovery, DBus/helper IPC, presentation, raster, transition, and cleanup ownership.
3. Compare the implementation against the original `fix219` research and refactor plans.
4. Identify transitional contracts, status/runtime identity mismatches, special dispatch, and generic boundary leaks.
5. Inventory relevant unit, architecture, harness, and GNOME Phase 19 tests.
6. Record existing behavior invariants and safe contract-first extraction seams.
7. Separate architecture-convergence work from Phase 5 validation, compliance, and signoff.
8. Assess whether proposed generic seams can later support KDE/KWin without designing or implementing that backend now.
9. Establish the current behavior and ownership differences among GNOME native Wayland, GNOME native X11, and XWayland compatibility paths.

### Focused design-dependency pass

| Stage | Description | Status |
|---|---|---|
| R.1 | Map the composition root, construction sequence, and plugin/controller/client/backend ownership graph | Completed |
| R.2 | Define EDMC-to-client ownership-channel and liveness constraints | Completed |
| R.3 | Research GNOME helper owner-token, lease, conflict, expiry, and recovery mechanics | Completed |
| R.4 | Derive backend behavioral contracts and a versioned control-plane schema | Completed |
| R.5 | Map reusable contract tests, migration tests, and Phase 19 invariant coverage | Completed |
| R.6 | Define the pre-migration performance baseline and regression comparison method | Completed |
| R.7 | Define support/evidence workflow, diagnostic extensions, and current EDMC compliance findings | Completed |
| R.8 | Record stable helper-query/repaint pressure, safety constraints, A/B method, and clean-baseline evidence rules | Completed |

## Initial Sources

- Current repository source and tests
- Relevant Git history
- `/tmp/handoff-20260717-135402.md` as an index whose claims must be independently verified
- `/tmp/handoff-20260721-062740.md` as the Step 3 incident, evidence, and requirements amendment
- `docs/refactoring/fix219_cross_platform_overlay_architecture_research.md`
- `docs/refactoring/fix219_backend_architecture_refactor_plan.md`
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md`
- `docs/refactoring/gnome_wayland_presentation_attachment.md`

## Deliverables

- Separate research notes organized by architecture, GNOME runtime ownership, test coverage/invariants, and scope/risks
- Mermaid diagrams for architecture, component ownership, and runtime data flow
- A concise set of findings that can drive requirements clarification and detailed design

Focused notes:

- `composition-root-and-ownership.md`
- `owner-liveness-transport.md`
- `gnome-helper-lease-protocol.md`
- `backend-contracts-and-control-plane.md`
- `contract-tests-and-migration.md`
- `performance-baseline.md`
- `validation-evidence-and-compliance.md`
- `gnome-helper-pressure-and-repaint.md`

## Authoritative external sources

- [EDMC `PLUGINS.md`](https://github.com/EDCD/EDMarketConnector/blob/main/PLUGINS.md)
- [EDMC `docs/Releasing.md`](https://github.com/EDCD/EDMarketConnector/blob/main/docs/Releasing.md)
- [GNOME Shell extension anatomy and lifecycle](https://gjs.guide/extensions/overview/anatomy.html)
- [GIO D-Bus name ownership](https://docs.gtk.org/gio/func.bus_own_name.html)
- [Python monotonic clock](https://docs.python.org/3/library/time.html#time.monotonic)
- [Python asyncio streams](https://docs.python.org/3/library/asyncio-stream.html)
