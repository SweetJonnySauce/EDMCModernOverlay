# Task 05 Context: Stable Target Query Pressure

## Parameters

- Mode: `auto`
- Repository root: `EDMCModernOverlay`
- Task: `.agents/tasks/2026-07-17-fix219-architecture-convergence/step03/task-05-reduce-stable-target-query-pressure.code-task.md`
- Design authority: `docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md`
- Working stage: authoritative 1.7 / Step 03 stage 3.11

## Requirements and unchanged contracts

- Keep stable target-query policy inside the GNOME backend implementation.
- Reuse the existing bounded 1.5-second monotonic deadline; do not add a generic throttle.
- A matching successful mapped-suppressed snapshot may skip target enumeration inside the deadline even when the Phase 19 transition guard is enabled.
- Deadline expiry, explicit refresh, cache failure, target/presentation change, stale raster work, and transition/recovery state must continue to bypass or invalidate suppression.
- Preserve the post-remap backend-neutral refresh as a one-shot bypass.
- Preserve Phase 19 ownership, focus, placement, click-through, privacy, and fail-closed behavior.
- Keep diagnostics dev-gated and avoid per-cycle release logging.

## Existing documentation

- The detailed design assigns cache ownership and all compositor decisions to the backend and forbids generic GNOME enum dispatch.
- The pressure research identifies the transition-guard condition as the leading cause of two synchronous `GetTargetState` calls per second.
- The Step 03 plan requires focused RED/GREEN unit evidence now; full `make check` and `make test` remain reserved for the integrated query-plus-repaint milestone.
- The post-Task-04 iteration checklist reports quiet configuration complete and Task 05 ready.
- No `CODEASSIST.md` exists; repository AGENTS instructions and the approved PDD artifacts apply.

## Implementation paths and dependency map

```text
follow_surface (generic refresh intent)
  -> backend.consumers (backend-neutral cycle call)
    -> _gnome_shell_helper_presentation (backend-owned cache/query/transition policy)
      -> helper target probe and presentation probe
```

Primary runtime touchpoint:
`overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`

Primary tests:
`overlay_client/tests/test_gnome_helper_presentation_runtime.py`

Regression-only companion:
`overlay_client/tests/test_follow_surface_mixin.py`

## Existing pattern and defect

`GnomeHelperPresentationRuntimeState` already owns the cached target, request, presentation,
matching signature, last-success time, and next suppressed-target deadline. The clock is already
injected. A successful matching mapped-suppressed result arms the deadline, and explicit refresh
already bypasses both target and presentation suppression. The defect is the additional
`not transition_guard_enabled` eligibility condition, which defeats the existing cache in the
normal Shell-raster-capable runtime.

## Risks and uncertainty

- Suppression must not run while transition evidence is pending or after a failed/non-matching result.
- Target-derived invalidations are observed at the bounded target-query deadline; explicit and caller-visible refresh/exposure inputs bypass sooner.
- Workspace and complete monitor/geometry identity need explicit signature coverage so a refreshed query cannot be mistaken for an unchanged presentation.
- The repository contains prior uncommitted Step 03 work; Task 05 edits must remain isolated and uncommitted.
