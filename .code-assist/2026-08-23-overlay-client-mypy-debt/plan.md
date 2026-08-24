# Plan: Eliminate Overlay Client Mypy Debt

## Recommended scope

Make `python -m mypy overlay_client` pass, then add `overlay_client` to `[tool.mypy].files` so the
default project typecheck enforces the repaired surface. Do not treat only the five direct
`overlay_client.py` errors: they are symptoms of the same composite type contract and would leave
the importer graph unprotected.

The task preserves runtime behavior. It is not authorization to refactor widget lifecycle,
backend selection, rendering, focus, click-through, or native X11 behavior.

## Acceptance criteria

1. `python -m mypy overlay_client` returns zero errors under the repository's Python 3.10 config.
2. `python -m mypy` remains green after `overlay_client` is included in the configured target.
3. The shared-state contract has one authoritative type declaration per state field; mixins do not
   silently disagree on a field's type.
4. No blanket `ignore_errors`, `# type: ignore` without a documented narrow reason, or broad `Any`
   widening is introduced to suppress the baseline.
5. The X11 surface-clear behavior and its tests remain intact; no X11/compositor-specific logic is
   added to generic client paths.
6. Targeted unit/Qt tests and the project checks pass. Because `load.py` is untouched, no new
   harness test is required.

## Test strategy

Type checks are the primary RED/GREEN proof. Existing unit/Qt tests guard behavior when type
corrections touch runtime helpers.

| ID | Input / setup | Expected output |
| --- | --- | --- |
| T1 | Current `python -m mypy overlay_client` baseline | Fails with the categorized baseline; establishes the complete target. |
| T2 | Shared-state contract before declarations are reconciled | Fails on the affected mixin/class error family, not via a runtime mock. |
| T3 | State-contract implementation | Mypy accepts shared attributes and no longer reports incompatible base definitions. |
| T4 | Geometry/anchor/payload correction with valid float/string/mapping inputs | Existing focused tests continue to accept the current runtime values. |
| T5 | Renderer protocol/command correction | Existing render/vector/debug tests pass without reduced drawing behavior. |
| T6 | `OverlayWindow` transparent paint path | `test_setup_surface.py`, repaint debounce, and follow-surface tests retain the clear-first and follow contracts. |
| T7 | Configured project target after adding `overlay_client` | `python -m mypy` and `make check` both include and pass the client type surface. |

## Implementation stages

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Freeze a directory-wide mypy baseline and group errors by shared-state, pure-data, renderer, and integration family | Completed — 203 errors in 27 files, classified in `stage-2.1-baseline-inventory/inventory.md` |
| 2.2 | Add a type-only shared overlay-state contract; keep state initialization where it is | Completed — targeted mypy 53 to 5; 55 offscreen regressions passed |
| 2.3 | Reconcile mixin declarations and `OverlayWindow` inheritance conflicts, then run Qt/follow tests | Completed — all shared-state diagnostics cleared in focused target; 55 offscreen regressions passed |
| 3.1 | Correct pure geometry, anchor, legacy/payload, and override container types with focused regression tests | Pending review — all Stage 3.1 source annotations were user-directed rolled back after a runtime symptom report; retain the TTL deferral |
| 3.2 | Correct renderer protocol, command-union, debug, and render-surface typing with renderer tests | Pending review |
| 3.3 | Correct launcher/integration annotations and run affected client tests | Pending review |
| 4.1 | Confirm directory-wide client mypy is green | Pending review |
| 4.2 | Extend `pyproject.toml` enforcement only after green, then run default mypy | Pending review |
| 4.3 | Run project checks, patch hygiene, scoped review, and compliance review | Pending review |

## Design approach

### Preferred: type-only shared-state contract

Introduce a central, annotation-only contract for state owned by `OverlayWindow` and initialized
by `SetupSurfaceMixin`. Mixins reference that contract rather than independently inferring
incompatible instance attributes. Keep all assignments, timers, Qt calls, and initialization
order unchanged.

The contract must be type-only or otherwise have no constructor/runtime side effects. Avoid
adding a stateful superclass to the Qt widget's method-resolution order unless a focused proof
shows it is safe and necessary.

### Alternatives rejected for the first implementation

| Alternative | Reason |
| --- | --- |
| Add `ignore_errors = true` for `overlay_client.*` | Hides the exact error surface that currently blocks validation. |
| Add broad `Any` declarations to every mixin | Removes mypy's protection and leaves incompatible state ownership unresolved. |
| Move all shared state into `OverlayWindow.__init__` | Material runtime refactor with high lifecycle/Qt risk; outside a typing cleanup. |
| Add `overlay_client` to mypy config before cleanup | Makes project validation fail without improving type coverage. |

## Validation commands

Run in phase order, recording exact output in the task log directory:

```bash
source overlay_client/.venv/bin/activate && python -m mypy overlay_client

source overlay_client/.venv/bin/activate && QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest \
  overlay_client/tests/test_setup_surface.py \
  overlay_client/tests/test_repaint_debounce.py \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_vector_renderer.py \
  overlay_client/tests/test_transform_helpers.py -q

source overlay_client/.venv/bin/activate && python -m ruff check overlay_client

source overlay_client/.venv/bin/activate && python -m mypy

source overlay_client/.venv/bin/activate && make check
git diff --check
```

If a fix changes a pure helper's runtime behavior, add or update its unit test before that
implementation change. If no runtime behavior changes, document the type-check RED/GREEN evidence
and the focused regression tests selected for adjacent behavior.

## Risks and stop conditions

| Risk | Mitigation |
| --- | --- |
| Type changes alter mixin initialization or Qt MRO | Keep the shared contract type-only; never move timers, attributes, or `super()` calls in this task. Stop on any lifecycle ambiguity. |
| Existing broad errors hide a real behavioral mismatch | Correct the model conservatively; add a targeted unit test when an accepted input/output is uncertain. |
| Client-wide type enforcement reveals errors beyond the original 115 | Treat them as new inventory, not as justification for suppressions; update the plan before expanding scope. |
| The type cleanup overlaps the uncommitted X11 repair | Preserve its helper/tests and rerun them in every affected validation slice. |
| Fix219 backend boundary is breached | Stop; generic type contracts must not import compositor-specific modules or raw backend/helper enums. |

## Rollback and completion

Keep changes in small, family-scoped increments. If a type correction changes runtime behavior,
revert only that increment and restore the prior passing focused tests. Do not commit or push
without separate authorization. The final report must list changed files, added/updated tests,
exact commands/results, any skips, compliance answers, and manual work remaining.
