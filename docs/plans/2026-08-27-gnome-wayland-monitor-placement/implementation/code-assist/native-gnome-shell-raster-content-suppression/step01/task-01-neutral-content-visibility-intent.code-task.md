# Task: Add Neutral Content-Visibility Intent

## Description

Make the existing backend-neutral presentation visibility decision expose an
explicit `visible` or `suppressed` content intent. The intent must faithfully
represent the already-debounced policy outcome without changing current
runtime behavior or importing GNOME-specific implementation/protocol details
into generic follow or presentation-policy code.

## Background

The generic policy already distinguishes mapped-visible from
mapped-suppressed behavior through `content_visible` and `content_suppressed`.
The native GNOME fullscreen Shell-raster route needs a neutral intent it can
consume later, while the current release behavior must remain unchanged in
this step. The previous direct mapping from the unchecked preference to
`allow_unfocused_target=false` caused a live black-screen regression and was
rolled back.

## Reference Documentation

**Required:**

- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/native-gnome-shell-raster-content-suppression.md`

**Additional References (if relevant to this task):**

- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/native-gnome-shell-raster-content-suppression-lessons.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-shell-raster-content-suppression-plan.md` (Step 1)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-fullscreen-focus-visibility-regression-plan.md` (invalid historical evidence)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. Use the existing backend-neutral presentation-policy seam under
   `overlay_client/backend/`; do not import GNOME helper code, GNOME protocol
   types, or compositor-specific enums into generic policy or follow/runtime
   code.
2. Define one explicit, typed, neutral representation of content visibility
   with exactly the values `visible` and `suppressed`, or an equivalently
   constrained existing project convention.
3. Make every visibility-policy outcome deterministically expose the neutral
   intent while preserving all existing `show`, `surface_action`,
   `content_visible`, debounce, warmup, and hard-lifecycle semantics.
4. Do not consume the new intent in a live GNOME helper request, alter
   `allow_unfocused_target`, or change helper actor behavior in this task.
5. Preserve the `fix219` boundary: generic code may express the neutral
   intent only; backend bundles own renderer/protocol mapping.
6. Add unit tests for focused, debounced-unfocused, keep-visible,
   prepared-surface, and hard-loss policy outcomes, plus architecture-boundary
   assertions as needed to prove the neutral layer contains no GNOME dispatch.

## Dependencies

- Existing generic policy in `overlay_client/backend/presentation_policy.py`.
- Existing policy coverage in `overlay_client/tests/test_backend_presentation_policy.py`.
- Existing architecture boundary coverage in
  `overlay_client/tests/test_backend_architecture_boundary.py`.
- Task 02 consumes this neutral intent at the native GNOME helper boundary,
  but Task 01 must remain independently valid and behavior-neutral.

## Implementation Approach

1. Inspect the policy decision model and its callers to select the smallest
   pure, typed intent seam; prefer deriving it from the existing
   `content_visible` contract rather than duplicating debounce logic.
2. Write focused RED tests establishing the neutral intent for all decision
   classes, including suppression after the existing debounce and visible
   fallback outcomes.
3. Implement the minimal pure model/API change, keeping compatibility for
   existing callers and making no compositor-specific imports.
4. Refactor only for clarity after tests are green. Record exact test evidence
   in the task handoff and do not stage or commit changes.

## Acceptance Criteria

1. **Focused target resolves visible intent**
   - Given a valid focused target and an unchecked preference
   - When the existing visibility policy resolves its decision
   - Then the decision exposes `visible` intent and preserves the current
     mapped-visible behavior.

2. **Debounced focus loss resolves suppressed intent**
   - Given a valid unfocused target that has crossed the existing sample and
     time debounce thresholds with the preference unchecked
   - When the policy resolves its decision
   - Then the decision exposes `suppressed` intent while preserving the
     existing mapped-suppressed action and debounce state.

3. **Keep-visible and hard-loss behavior remain explicit**
   - Given the preference is checked or a target has a genuine hard lifecycle
     loss such as unavailable, minimized, or off-workspace
   - When the policy resolves its decision
   - Then checked valid targets expose `visible`, hard-loss paths retain their
     current hidden semantics, and no ordinary-focus actor lifecycle action is
     implied by the neutral intent.

4. **Backend boundary remains intact**
   - Given generic policy and follow/runtime source
   - When architecture-boundary tests inspect their imports and dispatch
   - Then they contain no GNOME helper implementation import, raw GNOME helper
     enum, or compositor-specific protocol dispatch.

5. **Unit test evidence**
   - Given the completed pure policy change
   - When the focused policy and architecture-boundary tests run through
     `overlay_client/.venv`
   - Then all selected tests pass, and the handoff records the exact command
     and result.

## Metadata

- **Complexity**: Medium
- **Labels**: native-wayland, gnome, presentation-policy, fix219-boundary, unit-tests
- **Required Skills**: Python dataclasses and enums, backend policy design, pytest, architecture-boundary testing
