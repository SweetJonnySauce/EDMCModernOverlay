# Stage 2.3 Scope Review — Mixin Declarations and Inheritance

## Review decision

**Approved for one implementation task.** The parent plan explicitly approves
the one-task breakdown. It is limited to declaration compatibility across the
existing `OverlayWindow` mixins and the five residual diagnostics retained by
Stage 2.2.

## Evidence and boundary

The Stage 2.1 log identifies 19 incompatible inherited definitions at
`overlay_client.py:190`: setup-owned fields conflict with declarations or
inference in follow, control, interaction, and render mixins. Stage 2.2's
identical focused GREEN command retained exactly five errors:

- `_cursor_saved` is read through uncast interaction/follow branches.
- `preparation.rect` is read from an `object`-typed preparation value.
- A local begins as `tuple[()]` before receiving a tracker tuple.
- A reused `snapshot` local has incompatible tracker/device-ratio tuple shapes.

All are shared-state/mixin typing work already inventoried. The change may not
alter `OverlayWindow`'s MRO, setup ownership, constructors, timers, painting,
focus/click-through, backend selection, attachment, or follow behavior.

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 2. Shared-state contract | 2.3 | Generate and scope-review one declaration-reconciliation task | Completed |

Phase status: **Completed — planning only.**

## Test selection review

This is expected to be annotation-only, so a focused mypy RED/GREEN comparison
is the primary proof. The required existing offscreen setup, repaint-debounce,
and follow-surface tests guard the affected Qt/follow contracts. No harness
test applies because `load.py` and EDMC lifecycle wiring are excluded. No test
update is planned unless a precise fixture annotation is necessary; any runtime
contract uncertainty requires a test-first implementation or coordinator stop.

## Explicit exclusions and stop conditions

- Do not modify source/test/configuration/top-level documentation in planning;
  the implementation task must not change the Qt MRO, initialization, or
  behavior merely to satisfy mypy.
- Do not add broad `Any`, `ignore_errors`, unexplained ignores, dependencies,
  compositor/helper imports, or raw backend/helper presentation dispatch.
- Preserve the independent fix219 clear-first transparent-surface repair and
  generic backend boundary.
- Stop for coordinator review if an inherited conflict cannot be reconciled
  through a precise type-only seam, any residual needs behavioral/lifecycle
  movement, or a focused/directory-wide command reveals a new error family.
