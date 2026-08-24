# Task: Centralize the Annotation-Only OverlayWindow State Contract

## Description

Create one authoritative, annotation-only contract for `OverlayWindow` state that is initialized
by `SetupSurfaceMixin` and consumed by the interaction, follow, and control surfaces. Use it to
reduce the targeted shared-state mypy diagnostics without changing widget ownership or behavior.

## Background

Stage 2.1 froze 203 directory-wide mypy errors; 81 are in the shared-state family. The primary
source symptoms are indeterminate attributes in `interaction_surface.py`, `follow_surface.py`,
and `control_surface.py`, plus later `OverlayWindow` multiple-inheritance conflicts. This task
establishes the central contract only. Stage 2.3 owns reconciliation of conflicting mixin
declarations and must remain a separate follow-up.

## Reference Documentation

**Required:**
- Design: `.code-assist/2026-08-23-overlay-client-mypy-debt/plan.md`
- Context: `.code-assist/2026-08-23-overlay-client-mypy-debt/context.md`
- Orchestration: `.code-assist/2026-08-23-overlay-client-mypy-debt/orchestration-prompt.md`
- Prior handoff and inventory: `.code-assist/2026-08-23-overlay-client-mypy-debt/stage-2.1-baseline-inventory/`
- X11 boundary record: `.code-assist/2026-08-21-fix219-x11-surface-artifacts/`

**Note:** Read every governing artifact, the current execution status, this task, the Stage 2.1
handoff, and the scoped dirty diff before implementation. The approved parent plan and
orchestration prompt approve this single-task breakdown.

## Technical Requirements

1. Add a single central contract module or equivalent type-only declaration that describes only
   shared `OverlayWindow` attributes already initialized by `SetupSurfaceMixin`; retain every
   existing assignment, default, owner, and initialization location.
2. Consume the contract through annotation-only typing seams in the interaction, follow, and
   control surfaces. Do not add it as a runtime base class or alter `OverlayWindow`'s Qt MRO.
3. Do not move or change `__init__`, `_setup_overlay`, `super()` calls, timers, painting,
   focus/click-through, backend selection, attachment, input policy, or follow behavior.
4. Do not import compositor/X11/helper/presentation implementations into the contract or generic
   surfaces, and do not dispatch presentation from backend/helper enums. Preserve the fix219
   clear-first paint implementation and backend-owned boundary.
5. Do not add broad `Any`, blanket mypy ignores, `ignore_errors`, or unexplained narrow ignores.
   Stop for coordinator review if a safe annotation-only contract cannot express an attribute.
6. Before edits, record one narrow RED diagnostic using:
   `source overlay_client/.venv/bin/activate && python -m mypy --follow-imports=skip overlay_client/overlay_client.py overlay_client/interaction_surface.py overlay_client/follow_surface.py overlay_client/control_surface.py`.
   After the contract change, rerun that exact command once as GREEN measurement and report the
   targeted error delta; do not claim Stage 2.3's inheritance-conflict family is green.
7. After GREEN, run the existing offscreen regression slice:
   `source overlay_client/.venv/bin/activate && QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py -q`.
   No new runtime test is required for a proven annotation-only change; update a test annotation
   only if a fixture must mirror the contract, with no assertion or runtime behavior change.
8. The implementation context must update its stage-local `context.md`, `plan.md`, and
   `progress.md` before production edits, retain command output in this directory, and leave the
   exact six-field handoff required by the orchestration prompt.

## Dependencies

- Stage 2.1's preserved RED inventory and raw mypy output.
- Existing `overlay_client/.venv` with mypy and the offscreen PyQt test dependencies.
- The intentionally dirty, independent fix219/X11 surface-clear repair.

## Implementation Approach

1. Map only the already-owned state consumed across the three surfaces, then introduce a pure
   protocol/type declaration with no constructor or runtime side effect.
2. Apply the narrow annotations at consuming seams, preserving all lifecycle and backend
   boundaries; defer inheritance-conflict reshaping to Stage 2.3.
3. Compare the one targeted RED/GREEN result, run the selected existing regressions, inspect the
   scoped diff, and document any remaining shared-state diagnostics for Stage 2.3.

## Acceptance Criteria

1. **Central contract without lifecycle movement**
   - Given state remains initialized in `SetupSurfaceMixin`
   - When the shared contract is introduced and consumed
   - Then it has no runtime base-class, constructor, timer, Qt, or backend side effect and every
     state assignment and initialization order remains unchanged.

2. **Bounded mypy improvement**
   - Given the saved Stage 2.1 inventory and one narrow RED measurement
   - When the annotation-only contract is applied
   - Then the same narrow GREEN command reports a documented improvement in targeted
     indeterminate shared-state diagnostics without suppressing or hiding remaining errors.

3. **Existing UI contracts preserved**
   - Given the contract is annotation-only
   - When the offscreen setup/repaint/follow slice runs
   - Then it passes, including the clear-first transparent-surface and follow/repaint behavior.

4. **Stage and boundary discipline**
   - Given Stage 2.2 completes
   - When the coordinator reviews the scoped diff and handoff
   - Then no MRO/inheritance reconciliation, runtime behavior move, X11/compositor leakage, or
     broad typing escape hatch is present, and remaining conflict work is explicitly deferred to
     Stage 2.3.

## Metadata

- **Complexity**: Medium
- **Labels**: mypy, typing, overlay-client, shared-state, stage-2.2
- **Required Skills**: Python typing protocols, mypy diagnosis, PyQt regression awareness
