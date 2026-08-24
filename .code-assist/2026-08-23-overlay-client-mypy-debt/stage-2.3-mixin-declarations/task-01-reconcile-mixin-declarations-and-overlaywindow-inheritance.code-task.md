# Task: Reconcile Mixin Declarations and `OverlayWindow` Inheritance

## Description

Resolve the remaining shared-state typing family by reconciling incompatible
mixin declarations seen at `OverlayWindow`, without changing its Qt base order,
initialization, or runtime behavior. Finish the five remaining narrow
diagnostics only where precise annotations make their existing contracts clear.

## Background

Stage 2.2 reduced its four-file shared-state measurement from 53 to five
errors using the type-only `OverlayWindowState` protocol. The frozen
directory-wide inventory also records 19 `OverlayWindow` multiple-inheritance
conflicts involving setup-owned fields redeclared or inferred by follow,
control, interaction, and render mixins. The existing MRO is fixed:
`SetupSurfaceMixin, InteractionSurfaceMixin, QWidget, RenderSurfaceMixin,
FollowSurfaceMixin, ControlSurfaceMixin`.

## Reference Documentation

**Required:**
- Design: `.code-assist/2026-08-23-overlay-client-mypy-debt/plan.md`
- Context and orchestration: `.code-assist/2026-08-23-overlay-client-mypy-debt/context.md`; `.code-assist/2026-08-23-overlay-client-mypy-debt/orchestration-prompt.md`
- Prior evidence and handoff: `.code-assist/2026-08-23-overlay-client-mypy-debt/stage-2.1-baseline-inventory/`; `.code-assist/2026-08-23-overlay-client-mypy-debt/stage-2.2-shared-state-contract/`
- X11 boundary record: `.code-assist/2026-08-21-fix219-x11-surface-artifacts/`

**Note:** Read the complete governing artifacts, dashboard, Stage 2.2 handoff,
stage-local task, relevant source, and scoped dirty diff before implementation.
The approved parent plan authorizes this one-task breakdown.

## Technical Requirements

1. Resolve only the 19 inherited field-definition conflicts and the five Stage
   2.2 residuals: `_cursor_saved` reads, backend preparation `rect`
   indexability, empty-tuple inference, and device-ratio snapshot reuse.
2. Use exact annotations and type-only declaration seams; retain every state
   owner, assignment, default, method body, constructor, `super()` chain, and
   the current Qt MRO. Do not add runtime bases or storage.
3. Do not use broad `Any`, blanket/undocumented ignores, `ignore_errors`,
   compositor-specific imports, or raw backend/helper-enum presentation
   dispatch. Keep the fix219 transparent clear and backend boundary intact.
4. Treat a residual whose real contract cannot be expressed precisely as a
   stop condition: preserve the diagnostic and return evidence for coordinator
   review instead of changing behavior or widening types.
5. Before edits, capture one focused RED command:
   `source overlay_client/.venv/bin/activate && python -m mypy --follow-imports=skip overlay_client/overlay_client.py overlay_client/interaction_surface.py overlay_client/follow_surface.py overlay_client/control_surface.py overlay_client/render_surface.py`.
   After edits rerun that identical command once as GREEN and record the delta;
   do not run the directory-wide milestone in this stage.
6. Run the required offscreen regression slice:
   `source overlay_client/.venv/bin/activate && QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py -q`.
   Add or update a test only if an existing behavior contract needs a precise
   annotation seam; no `load.py` harness applies.
7. Maintain stage-local `context.md`, `plan.md`, `progress.md`, command logs,
   and an exactly six-field handoff before ending the isolated context.

## Dependencies

- Stage 2.1's 203-error frozen inventory and raw mypy log.
- Stage 2.2's `OverlayWindowState` contract, five-error GREEN log, and passing
  55-test offscreen regression record.
- The intentionally dirty, independent fix219/X11 repair.

## Implementation Approach

1. Compare each inherited-field conflict with its setup-owned annotation and
   replace conflicting mixin-side declarations/inferences with compatible,
   type-only declarations or local precisely typed values.
2. Address each of the five residuals independently, keeping only changes
   whose runtime value contract is directly established by existing code/tests.
3. Prove focused RED/GREEN, run the offscreen setup/repaint/follow regressions,
   inspect the scoped diff for MRO/lifecycle and backend-boundary preservation,
   then hand off any unresolved diagnostics unchanged.

## Acceptance Criteria

1. **Inheritance contract is compatible**
   - Given the unchanged `OverlayWindow` base list and setup-owned state
   - When the focused inheritance/state mypy target runs after the change
   - Then it has no remaining inherited-field conflict or five-residual error
     that was safely in scope, without suppressions or runtime contract changes.

2. **Qt lifecycle remains unchanged**
   - Given the mixin declarations are reconciled
   - When the offscreen setup, repaint-debounce, and follow-surface tests run
   - Then they pass while the existing clear-first paint, timers, follow,
     cursor, focus, and click-through behavior remains unchanged.

3. **Boundary and scope discipline**
   - Given the scoped diff and Stage 2.2 handoff
   - When the implementation is reviewed
   - Then no MRO/base-order/initializer movement, compositor-specific generic
     import or dispatch, broad `Any`, or blanket ignore is present; any
     unresolvable residual is documented for coordinator review.

## Metadata

- **Complexity**: Medium
- **Labels**: mypy, typing, overlay-client, shared-state, mixins, stage-2.3
- **Required Skills**: Python typing and mypy diagnosis, PyQt MRO awareness, offscreen regression testing
