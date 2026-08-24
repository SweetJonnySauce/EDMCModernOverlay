# Stage 2.1 Context — Directory-Wide Mypy Baseline

## Scope

This isolated implementation context freezes the RED baseline for exactly
`overlay_client` and classifies its reported errors. It may write only this stage's
documentation and raw validation evidence. Production code, tests, configuration,
top-level task records, and the independent fix219/X11 repair are out of scope.

## Requirements and invariants

- Run `source overlay_client/.venv/bin/activate && python -m mypy overlay_client`
  once, preserve its combined raw output and exit status, and do not rerun it.
- Assign every reported error to one approved family: shared-state, pure-data,
  renderer, or integration. A genuinely new family stops the broader plan.
- This is annotation-only baseline evidence; mypy is the selected RED proof. No
  unit or harness test is applicable because no behavior changes.
- Preserve the dirty fix219 worktree. In particular, the backend-neutral
  transparent-surface clear and its tests remain unchanged, and generic client
  paths must not gain compositor-specific imports or raw backend/helper enum
  presentation dispatch.

## Project and configuration

`pyproject.toml` targets Python 3.10 and currently excludes `overlay_client`
from `[tool.mypy].files`; the directory-wide command is therefore intentionally
explicit. The current `Makefile` typecheck target invokes default mypy only.
The client virtual environment supplies the checker. No dependency installation
is authorized.

## Prior evidence and dependency map

The approved plan predicts four error families. The initial shared-state family
centers on `OverlayWindow`'s mixins, whose state is initialized by
`SetupSurfaceMixin` and consumed by interaction, follow, control, and render
surfaces. Pure-data covers geometry, anchor, legacy/payload, and override value
shapes. Renderer covers vector/debug/render protocol and command unions.
Integration covers launcher-facing annotations.

The preceding fix219 records show a separate clear-first Qt paint repair in
`overlay_client/overlay_client.py` and `overlay_client/tests/test_setup_surface.py`.
That repair is not evidence for this typing baseline and must not be changed.

## Uncertainty

The frozen output, rather than earlier import-closure counts, is authoritative.
If it reports a family outside the approved taxonomy, record file/error evidence
and stop rather than expanding this stage.

## Frozen result

The sole required command exited `1` and reported 203 errors in 27 files. This
directory-wide result includes 88 more errors than the earlier 115-error
import-closure baseline, primarily in already-existing tests and
integration-adjacent interfaces. The complete line-level mapping is in
`inventory.md`; each diagnostic fits an approved family, so no new-family stop
was triggered.
