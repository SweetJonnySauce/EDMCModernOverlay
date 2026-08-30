# Task 3.2: Integrate the Renderer and Geometry Contract

## Scope

Resolve `overlay_client/render_surface.py` in the active merge. Semantically
review the auto-merged `overlay_client/paint_commands.py` and
`overlay_client/payload_transform.py`; a clean Git auto-merge is not evidence
that their combined behavior matches the resolved payload contract.

Retain the target branch's renderer/backend ownership and deliberately retain
`main`'s circle and optional shape-thickness behavior. The three modules must
agree on circle geometry, opacity, cycle anchors, miter joins for explicitly
thick rectangles, optional circle stroke width, and transformed group bounds.
This is a renderer/geometry-contract task only: do not resolve `version.py` or
alter tests, gallery, documentation, configuration, public payload processing,
or unrelated merge paths.

## Required reading

- `AGENTS.md`
- plan, orchestration prompt, and execution dashboard for this merge
- Task 2 and Task 3.1 handoffs
- This brief, the three scoped modules, and only the directly relevant
  renderer/bounds tests before editing.

## Constraints

1. Resolve `render_surface.py` as an intentional merge: preserve the target
   renderer/backend structure while retaining `main`'s circle drawing path and
   its explicit-versus-omitted thickness policy. Do not use a blanket
   ours/theirs selection.
2. Preserve circle rendering geometry and opacity end-to-end. A circle's
   centre/radius, colour/alpha handling, and stroke policy must correspond to
   the normalized payload and generated paint command; an omitted thickness
   must remain semantically distinct from an explicit valid thickness.
3. Preserve rectangle rendering behavior: an explicitly supplied rectangle
   thickness continues to use miter joins, while existing default-stroke
   behavior is not changed. Preserve existing cycle-anchor behavior exactly;
   do not reinterpret or relocate anchors as part of this task.
4. Review `paint_commands.py` semantically for command construction that
   carries the above circle geometry, opacity, optional stroke, rectangle
   miter-join, and cycle-anchor semantics. Review `payload_transform.py`
   semantically so transformed group bounds include the correct circle extent
   and continue to agree with renderer coordinates. Make an edit there only
   when needed to preserve that contract.
5. Retain the `fix219` boundary. Generic follow/runtime code must not gain a
   compositor-specific presentation import or raw backend/helper-enum
   dispatch.
6. Leave `version.py` unmerged. Do not touch configuration, gallery,
   documentation, public payload-processing modules, or unrelated paths. No
   commit, amend, push, fetch, reset, abort, live overlay, or external-service
   access.

## Expected unchanged behavior

- The target branch remains the owner of renderer/backend structure.
- Existing non-circle rendering, default stroke behavior, and coordinate
  conventions do not change merely because `main` added circle support.
- The active merge remains uncommitted; resolving the known `version.py`
  conflict belongs exclusively to Task 4.3.

## Test type and validation

This is deterministic rendering/geometry logic, so unit tests are required;
no EDMC lifecycle harness is needed for this subtask. Run the smallest focused
renderer/bounds tests available, normally:

```bash
source .venv/bin/activate
PYQT_TESTS=1 python -m pytest \
  overlay_client/tests/test_paint_commands.py \
  overlay_client/tests/test_payload_bounds.py \
  overlay_client/tests/test_render_surface_mixin.py
```

The focused review must cover, either in the existing tests or only by additions
that are strictly necessary in these three paths: circle command geometry and
opacity; omitted and explicit circle thickness; explicit rectangle miter
joins; preserved cycle anchors; and transformed circle/group bounds. Test-file
union work remains Task 3.3.

If the known missing `pytest` environment persists, attempt the command once,
then run syntax/compile and scoped whitespace checks, record the exact failure,
and defer pytest to the required validation milestone. Do not weaken coverage
or edit tests merely to make an environment failure disappear.

## Acceptance criteria

1. Given a circle with opacity and either omitted or explicit valid thickness,
   when it becomes a paint command and is rendered, then its centre/radius,
   alpha, and stroke policy agree with the payload contract.
2. Given an explicitly thick rectangle, when it is converted and painted, then
   its miter-join behavior remains intact and existing default-stroke behavior
   remains unchanged when thickness is omitted.
3. Given cyclic and transformed grouped shapes, when commands and bounds are
   built, then cycle anchors remain unchanged and transformed bounds include
   the correct circle extent in the same coordinate convention as rendering.
4. Given the active merge, when Task 3.2 completes, then only
   `render_surface.py` has been resolved and the two auto-merged geometry
   modules have been semantically reviewed (and edited only if required);
   `version.py` remains unmerged.
