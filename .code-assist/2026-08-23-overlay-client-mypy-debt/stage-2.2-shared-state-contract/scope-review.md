# Stage 2.2 Scope Review — Shared State Contract

## Review decision

**Approved for one implementation task.** The parent plan and orchestration prompt provide the
required task approval. The task is limited to a central annotation-only contract for state
already owned by `SetupSurfaceMixin` and read by interaction, follow, and control surfaces.

## Evidence and boundary

Stage 2.1 records 81 shared-state diagnostics: 3 interaction, 16 follow, 30 control, 19
`OverlayWindow` inheritance-conflict, and 13 test-adjacent errors. The direct source errors show
that consuming mixins cannot determine types for setup-owned state such as follow geometry,
cursor, title-bar, repaint, and platform-context fields. The current `OverlayWindow` MRO is:
`SetupSurfaceMixin, InteractionSurfaceMixin, QWidget, RenderSurfaceMixin, FollowSurfaceMixin,
ControlSurfaceMixin`; changing it is expressly out of scope.

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 2. Shared-state contract | 2.2 | Generate and review the one annotation-only contract task | Completed |

Phase status: **Completed — planning only.**

## Explicit exclusions

- No Qt MRO, constructor, `super()` chain, initialization order, timers, painting, focus,
  click-through, backend selection, or follow behavior movement.
- No attempt to resolve `OverlayWindow`'s multiple-inheritance declaration conflicts; that is
  Stage 2.3.
- No broad `Any`, `ignore_errors`, unexplained ignores, dependency changes, or config edits.
- No import or dispatch leakage of X11/compositor/helper presentation into generic surfaces.
- No changes to the independent fix219 clear-first surface repair or its test behavior.

## Test selection review

This is annotation-only work, so targeted mypy RED/GREEN is the primary proof. The existing
offscreen setup/repaint/follow tests are required as regression coverage because the contract
touches state consumed by those paths. No harness test applies: `load.py` and EDMC lifecycle
wiring are untouched. No test addition is required unless a test fixture annotation must mirror
the contract without behavioral change.

## Implementation stop conditions

Stop for coordinator review if the contract requires runtime inheritance, initializer movement,
or an X11/backend-specific type import; if the narrow result reveals a diagnostic outside the
frozen shared-state family; or if a typing change appears to require a behavior change. Preserve
the existing 203-error raw inventory and report, rather than suppress, any residual errors.
