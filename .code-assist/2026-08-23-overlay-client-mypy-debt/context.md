# Overlay Client Mypy-Debt Remediation Context

## Goal

Remove the current type-check failures reachable from `overlay_client/overlay_client.py`, then add
the overlay client to the repository's enforced mypy target only after it is green. The work must
be behavior-preserving and must not disturb the separate native-X11 surface repair.

## Baseline

- `python -m mypy overlay_client/overlay_client.py` currently reports **115 errors in 14 files**.
- `python -m mypy --follow-imports=skip overlay_client/overlay_client.py` reports five direct
  attribute-inference errors in `overlay_client/overlay_client.py` at lines 536, 558, 656, 669,
  and 679.
- The default `[tool.mypy].files` list in `pyproject.toml` does not include `overlay_client`.
  Consequently, the repository's default `make typecheck` / `make check` does not enforce this
  client surface today.

## Error families

| Family | Representative paths | Underlying issue |
| --- | --- | --- |
| Shared UI state / mixins | `setup_surface.py`, `interaction_surface.py`, `follow_surface.py`, `control_surface.py`, `render_surface.py`, `overlay_client.py` | Attributes initialized in one mixin are read or reassigned in another without one authoritative declaration; `OverlayWindow` reports incompatible base definitions. |
| Pure geometry/data shapes | `follow_geometry.py`, `anchor_helpers.py`, `transform_helpers.py`, `legacy_processor.py`, `plugin_overrides.py`, `payload_model.py` | Inferred container/value types are narrower than actual valid values. |
| Render protocol/command typing | `vector_renderer.py`, `debug_cycle_overlay.py`, `render_surface.py` | Incomplete protocol bodies, `object`-typed inputs passed to collections, and mismatched command/measurement unions. |
| Integration/launcher annotations | `launcher.py` | Values imported from composite UI modules lack a stable type at use sites. |

## Relevant architecture

```text
OverlayWindow
  = SetupSurfaceMixin + InteractionSurfaceMixin + QWidget
    + RenderSurfaceMixin + FollowSurfaceMixin + ControlSurfaceMixin

SetupSurfaceMixin initializes most shared state
  -> the other mixins consume/update it
  -> mypy sees independent bases with incompatible or indeterminate attributes
```

The preferred repair is a type-only, centralized shared-state contract plus narrowly corrected
value/container annotations. It must not move Qt initialization, alter mixin method-resolution
order, add runtime data storage, or change drawing/follow behavior.

## Governing constraints

- Read `AGENTS.md`, `pyproject.toml`, and the existing X11 task records before implementation.
- Keep the current intentionally dirty fix219 worktree intact. Do not reset, bulk-stage, commit,
  or modify unrelated files.
- Preserve the fix219 backend boundary: generic runtime surfaces must remain compositor-neutral.
- This is a Python typing/refactor task. Add unit tests only when correcting a runtime helper's
  observable behavior; pure annotation-only changes are proven by mypy plus existing focused
  tests. No `load.py` change is planned, so harness tests are not required.
- `CODEASSIST.md` is absent. Creating one is outside this task.

## Existing documentation

- `README.md`: project purpose and supported platforms.
- `AGENTS.md`: test, EDMC compliance, backend-boundary, and dirty-worktree rules.
- `pyproject.toml` / `Makefile`: Python 3.10 mypy configuration and default checks.
- `.code-assist/2026-08-21-fix219-x11-surface-artifacts/`: the separate narrow X11 repair and
  its validation history. Its changed files must not be absorbed by this type-cleanup task.

## Open decisions

1. Should the final scope make `python -m mypy overlay_client` green, or only the import closure
   of `overlay_client/overlay_client.py`? This plan recommends the directory-wide target so CI
   enforcement is meaningful.
2. After the client is green, should `overlay_client` be added to `[tool.mypy].files` immediately?
   This plan recommends yes, in the final enforcement stage, but keeps it separate from cleanup
   so a temporary configuration change cannot hide work.
3. If a typing correction exposes a real runtime ambiguity, stop and request direction rather
   than widening types to `Any` or adding a blanket `ignore_errors` override.
