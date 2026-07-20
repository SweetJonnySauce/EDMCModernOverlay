# Raster Test and Developer Environment Plan

## Phase Tracking

| Phase | Status |
| --- | --- |
| Phase 1: Raster bridge test isolation | Completed |
| Phase 2: Canonical root developer environment | Completed |

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Verify state and inspect test/build/dependency boundaries | Completed |
| 1.2 | Define tests, touchpoints, and two-commit sequence | Completed |
| 1.3 | Capture existing raster failure and tooling-contract RED | Completed |
| 1.4 | Isolate raster test, validate, and commit | Completed |
| 2.1 | Update root-venv Makefile and active developer documentation | Completed |
| 2.2 | Validate current/fresh dependency contract and full project gates | Completed |
| 2.3 | Commit tooling and workflow evidence | Completed |

## Test Type Selection

- Raster test: **unit test**. Helper/platform responses and the frame builder are injectable;
  no real GNOME, D-Bus, filesystem, or Qt lifecycle belongs in this bridge-forwarding case.
- Developer environment: **unit/contract test** over tracked configuration files. No EDMC
  lifecycle or plugin hooks change, so harness coverage is not required.

## Test Scenarios

1. **Existing raster RED**
   - Input: run the named bridge test in the sandbox without a helper.
   - Output before fix: failure creating `/run/user/...`, proving accidental filesystem work.
2. **Isolated bridge forwarding**
   - Input: eligible fake builder result containing the predefined frame request.
   - Output: exact request reaches `fetch_presentation`; renderer/status assertions remain.
3. **Canonical developer interpreter**
   - Input: tracked Makefile text.
   - Output: root `.venv/bin/python` is preferred, `python3` is fallback, and
     `overlay_client/.venv` is absent from the development selector.
4. **Reproducible dependency source**
   - Input: `requirements/dev.txt`.
   - Output: pytest, ruff, mypy, and PyQt6 are declared through the existing CI source.
5. **Active documentation agreement**
   - Input: `AGENTS.md` and the active fix219 implementation plan.
   - Output: setup uses `requirements/dev.txt`; validation commands use root `.venv`; the
     Windows workaround uses `.venv\\Scripts\\python`.
6. **End-to-end project gates**
   - Input: canonical root environment with existing pinned dependencies.
   - Output: named raster test, tooling contract, `make check`, and `make test` pass without
     helper installation, Python override, deselection, `/run` write, or Qt abort.

## Implementation Sequence and Commits

1. Run the existing raster test to capture RED.
2. Add the developer-environment contract test and confirm its expected RED assertions.
3. Replace the real raster builder only in the affected bridge test; rerun focused and raster
   suites; commit as `test(gnome): isolate raster bridge forwarding`.
4. Update Makefile and active documentation to the already-tracked root development
   dependency source; make the contract test GREEN.
5. Run full lint/typecheck/test gates without `PYTHON=` overrides, plus patch hygiene.
6. Commit as `build(dev): standardize root test environment`, including code-assist records.

## Expected Unchanged Behavior

- Static raster builders and writers remain production-identical.
- GNOME helper detection/installation and presentation runtime are unchanged.
- CI continues installing `requirements/dev.txt` and invoking `make check`.
- Packaged client requirements and `overlay_client/.venv` remain runtime-only.
