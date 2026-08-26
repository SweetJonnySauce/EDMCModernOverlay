# fix219 Repository Recheck — Iteration Checklist

Reviewed: 2026-08-24  
Commit: `7ac45ee` (`refactor(fix219): converge backend pressure controls and harden overlays`)

This is a post-commit verification pass.  It introduces no runtime-code changes.

## Status

| Phase | Stage | Check | Status | Evidence / next action |
| --- | --- | --- | --- | --- |
| 1 — Repository state | 1.1 | Confirm commit and worktree state | Completed | `git status --short` was empty; `git diff --check` passed. |
| 1 — Repository state | 1.2 | Confirm automatic backend selection is configured | Completed | `overlay_settings.json` has an empty `manual_backend_override`; startup can select the detected X11 backend. |
| 2 — Automated validation | 2.1 | Lint with the available project environment | Completed | `overlay_client/.venv`: `python -m ruff check .` passed. |
| 2 — Automated validation | 2.2 | Run focused fix219 unit and harness coverage | Completed | 255 passed with `QT_QPA_PLATFORM=offscreen PYQT_TESTS=1`. |
| 2 — Automated validation | 2.3 | Validate EDMC runtime-version guard | Completed with development override | Guard ran successfully with `ALLOW_EDMC_PYTHON_MISMATCH=1`; the local client venv is Python 3.12.3 64-bit, not the EDMC release baseline (3.13.9+ 32-bit). |
| 2 — Automated validation | 2.4 | Run the repository's canonical `make check` | Blocked — environment | The root `.venv` is absent and system Python lacks `ruff`; build the documented root dev environment, then rerun `make check`. |
| 2 — Automated validation | 2.5 | Linux install smoke script | Completed | `bash tests/test_install_linux.sh` passed. It refreshed the existing local installation and reported `overlay_groupings.json` as changed; no repository files changed. |
| 2 — Automated validation | 2.6 | Establish current client type-check baseline | Completed — failing baseline | `python -m mypy overlay_client` reports 124 errors in 23 files. This is expected open debt after the Stage 3.1 annotation rollback; it is not a clean type gate. |
| 3 — X11 runtime acceptance | 3.1 | Restart EDMC/game with no backend override and verify selected backend | Pending — manual | Confirm logs/status report the normal X11/Qt path, not `gnome_shell_raster`. |
| 3 — X11 runtime acceptance | 3.2 | Exercise long-session move/focus/repaint behavior | Pending — manual | The reported duplication is only reproducible in a live compositor session. Test startup, focus out/in, movement, repeated layout updates, then a multi-hour play session. Capture backend status and logs if artifacts recur. |

## Findings

1. The repository is clean at the reviewed commit, and the focused coverage for the backend-pressure and transparent-surface paths passes.
2. The persisted manual override that previously forced the GNOME Shell raster backend is now empty. This restores automatic runtime selection, but it needs live X11 confirmation because tests cannot reproduce the compositor artifact.
3. Root-level `make check` has not run locally because its documented development environment has not been created. Do not treat this as a source failure.
4. The type-check baseline is now **124 errors / 23 files**, superseding the earlier 113 / 21 inventory. The difference follows the intentional rollback of Stage 3.1 geometry/tuple annotations. Keep the TTL coercion diagnostic unchanged unless an input-contract decision is explicitly approved.

## Exact commands and outcomes

```text
git status --short && git diff --check && git rev-parse --short HEAD && git log -1 --oneline
# PASS — clean worktree; 7ac45ee

source overlay_client/.venv/bin/activate && python -m ruff check .
# PASS — All checks passed

source overlay_client/.venv/bin/activate && ALLOW_EDMC_PYTHON_MISMATCH=1 python scripts/check_edmc_python.py
# PASS with expected local-runtime warning

source overlay_client/.venv/bin/activate && QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest \
  overlay_client/tests/test_setup_surface.py \
  overlay_client/tests/test_repaint_debounce.py \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_backend_pressure_ab_runner.py \
  overlay_client/tests/test_pressure_ab.py \
  tests/test_harness_backend_status_roundtrip.py \
  tests/test_harness_plugin_hooks_contract.py \
  tests/test_harness_pressure_ab_snapshot.py \
  tests/test_check_edmc_python.py -q
# PASS — 255 passed in 2.15s (run outside the sandbox because five harness tests require local sockets)

source overlay_client/.venv/bin/activate && python -m mypy overlay_client
# OPEN BASELINE — 124 errors in 23 files

make check
# NOT RUN — root .venv missing; system Python lacks ruff

bash tests/test_install_linux.sh
# PASS — updated existing local install; no repo changes
```

## Next iteration entry criteria

- Build the root development environment from `requirements/dev.txt`, then run `make check`.
- Run the two manual X11 acceptance stages with `manual_backend_override` left blank.
- If artifacts return on the automatic X11 backend, collect the backend-status report and relevant logs before changing the transparent-surface implementation.
- Treat a future type remediation as a separate, behavior-preserving stage; do not reapply the rolled-back Stage 3.1 changes incidentally.
