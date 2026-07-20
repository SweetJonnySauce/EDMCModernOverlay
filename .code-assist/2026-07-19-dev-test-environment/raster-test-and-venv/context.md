# Raster Test and Developer Environment Context

## Scope

Deliver two independent maintenance increments:

1. isolate the GNOME raster bridge forwarding test from real filesystem/PyQt frame creation;
2. make the repository-root `.venv` the canonical local developer environment.

Neither increment installs the GNOME helper or changes production raster, helper, presentation,
plugin, or packaging behavior.

## Existing Documentation and Evidence

- `AGENTS.md` declares root `.venv` as the per-machine developer environment but currently
  names the nonexistent `requirements-dev.txt` and a nested Windows interpreter path.
- `requirements/dev.txt` is the tracked CI source for PyQt6, Wayland dependencies, pytest,
  ruff, mypy, stubs, and test utilities.
- `.github/workflows/ci.yml` installs `requirements/dev.txt` into the selected CI Python and
  runs `make check`; CI does not create `overlay_client/.venv`.
- `Makefile` currently prefers `overlay_client/.venv`, which is an installed client runtime
  and may legitimately omit developer tools.
- `docs/planning/2026-07-17-fix219-architecture-convergence/implementation/plan.md` still
  names the nested runtime for validation despite the detailed design and `AGENTS.md` using
  root `.venv`.
- No `CODEASSIST.md` exists. `AGENTS.md` supplies the project-specific implementation and
  test constraints; a separate file can be added later if reusable SOP overrides are needed.

## Raster Test Cause

`test_shell_raster_bridge_sends_static_frame_when_eligible` uses the real static-frame
builder even though it asserts against a predefined `HelperRasterFrameRequest`. That creates
two accidental dependencies:

- writable `XDG_RUNTIME_DIR` storage under `/run/user/...`;
- real PyQt font rendering without a `QGuiApplication` fixture.

Adjacent bridge tests already replace the builder with `ShellRasterFrameBuildResult`, while
`test_shell_raster_frame.py` separately covers cache paths and static builder behavior using
`tmp_path` and injected writers. The bridge test should therefore use the established fake
builder seam and continue asserting the exact forwarded request.

## Dependency Map

```text
bridge unit fixture -> fake static frame builder -> presentation-cycle forwarding assertions
                                              (no filesystem, Qt, or GNOME helper)

requirements/dev.txt -> root .venv -> Makefile lint/typecheck/test
                                      -> local developer and CI parity

overlay_client/requirements/* -> installed overlay_client/.venv -> shipped client runtime
                                                        (no dev-tool dependency)
```

## Implementation Paths

- `overlay_client/tests/test_gnome_helper_presentation_runtime.py`: fake only the static
  builder in the affected bridge test.
- `tests/test_dev_environment_contract.py`: enforce root-venv/tooling documentation wiring.
- `Makefile`: choose root `.venv/bin/python`, otherwise system `python3`; never select the
  installed client runtime for development checks.
- `AGENTS.md`: correct the requirements path and root Windows interpreter path.
- `docs/planning/2026-07-17-fix219-architecture-convergence/implementation/plan.md`: update
  active validation commands from the nested runtime to root `.venv`.

## Risks and Boundaries

- Do not weaken or skip the raster bridge assertion; only replace unrelated I/O/rendering.
- Do not add pytest/ruff/mypy to `overlay_client/requirements/`; those files feed packaging.
- Do not alter historical/archive plans solely for command normalization.
- Preserve the nine pre-existing untracked `.agents` task files.
