# Stage 2.2 Context — Shared Overlay-State Contract

## Scope and invariant

This isolated implementation adds one centralized, annotation-only contract for
`OverlayWindow` attributes that are already initialized by `SetupSurfaceMixin`
and consumed by interaction, follow, and control surfaces. It must not move an
assignment, change a default or owner, alter the Qt MRO or `super()` chain, or
touch timers, painting, focus, click-through, following, backend selection, or
the independent fix219 clear-first repair.

## Evidence and dependencies

- Stage 2.1 froze 203 directory-wide mypy errors; 81 belong to shared state.
  The direct consuming-surface counts are interaction 3, follow 16, and control
  30; 19 `OverlayWindow` inheritance-conflict diagnostics remain owned by Stage
  2.3.
- The required narrow measurement targets `overlay_client.py`,
  `interaction_surface.py`, `follow_surface.py`, and `control_surface.py` using
  `--follow-imports=skip`. The comparison is the only RED/GREEN type proof for
  this annotation-only task.
- Existing offscreen setup/repaint/follow tests are the selected regression
  proof. No test is added unless fixture annotations require it; `load.py` is
  untouched, so no harness test applies.
- `overlay_client/overlay_client.py` and `overlay_client/tests/test_setup_surface.py`
  contain the independently dirty, backend-neutral fix219 transparent-clear
  repair. They must retain their current behavior and generic surfaces must not
  import compositor/helper/presentation implementations.

## Intended implementation seam

Create a pure type declaration module containing only attributes already set by
`SetupSurfaceMixin`. Consume it at type-checking seams in the three named
surfaces, with no runtime base class or constructor. Do not resolve duplicated
mixin declarations or `OverlayWindow` inheritance conflicts here; record those
for Stage 2.3.

## Existing documentation

`AGENTS.md` requires staged, behavior-scoped refactors, explicit test choices,
and exact test evidence. The top-level mypy-debt plan and the Stage 2.2 task
limit this work to the central contract. The fix219 records require preserving
the clear-first paint invariant and backend boundary. `CODEASSIST.md` is absent.

## Uncertainty and stop condition

If the narrow diagnostic contains a non-shared-state family, or expressing a
field requires runtime/MRO/lifecycle movement, a broad `Any`, an ignore, or a
compositor-specific type import, stop and leave the evidence for coordinator
review.

## Implemented seam

`overlay_client/overlay_state.py` defines `OverlayWindowState` as a `Protocol`
whose fields are all initialized by `SetupSurfaceMixin`. The consuming methods
use `typing.cast` with a string forward reference and import the contract only
under `TYPE_CHECKING`; the protocol is never a runtime base and is not imported
at runtime. The narrow mypy result improved by 48 errors. Five residual
diagnostics remain unsuppressed for the next reviewed shared-state stage.
