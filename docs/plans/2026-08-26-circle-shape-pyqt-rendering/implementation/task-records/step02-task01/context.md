# Step 02 Task 01 Context

## Mode and scope

`code-assist` is running in auto mode for Step 2 Task 01 only. The task extends the pure `normalise_legacy_payload` mapping boundary to retain raw circle geometry and adds its unit coverage. Client validation/storage, lifecycle wiring, rendering, the approved plan, and the execution dashboard are out of scope.

## Restart reconciliation

- Governing artifacts, the dashboard, Step 2 task artifacts, and prior Step 1 records were read in the required order.
- The dashboard correctly places this task after reviewed Step 2 artifacts, although it contains one stale Step 1 running entry; no task-owned dashboard edit is permitted.
- `git status --short` contains pre-existing Step 1 source/test changes and untracked plan artifacts. This task will not alter them.
- `git diff --check` is clean. No applicable validation logs existed for this task.
- Instruction discovery found `README.md` and test READMEs but no `CODEASSIST.md`; no additional project-specific code-assist constraints apply.

## Test selection

Test type selected before edits: **unit**. `normalise_legacy_payload` is deterministic and accepts mappings without EDMC lifecycle, socket, `load.py`, or rendering setup. A harness test would cover the wrong boundary and is deferred to Step 4.

## Requirements and implementation paths

| Area | Path | Contract |
| --- | --- | --- |
| Raw normalizer | `EDMCOverlay/edmcoverlay.py` | Preserve canonical and title-cased raw circle `radius`/`thickness` values without geometry validation. |
| Focused unit coverage | `tests/test_edmcoverlay_shapes.py` | Assert circle field pass-through plus rect/vector normalization regressions. |
| Next consumer | `overlay_client/legacy_processor.py` | Task 02 alone validates and stores circle geometry. |

## Dependency map

Raw mapping -> `normalise_legacy_payload` -> normalized shape event -> Step 2 client validator. The normalizer must retain all geometry, including malformed values, so the single validator can reject it without an early drop.

## Existing behavior to preserve

- Rectangle fields (`x`, `y`, `w`, `h`), colours/fill defaults, TTL coercion, and plugin attribution.
- `vect` point validation/rejection and vector preservation behavior.
- ID-only clear behavior and all non-circle paths.

## Uncertainties

None material. Existing alias conventions use canonical and title-cased keys (for example `x`/`X`, `shape`/`Shape`), so circle geometry follows `radius`/`Radius` and `thickness`/`Thickness`.
