# Step 02 Task 02 Context

## Mode and scope

`code-assist` is running in auto mode for Step 2 Task 02 only. The task adds deterministic circle validation, first-class storage, and dedupe snapshots in `overlay_client/legacy_processor.py`, with unit tests in `tests/test_legacy_processor.py`. Rendering, raw normalization, lifecycle/harness wiring, the approved plan, and execution dashboard are out of scope.

Auto mode requires no further interaction; decisions and evidence are recorded here and in `progress.md`.

## Restart reconciliation

- Read the governing artifacts in the orchestration-required order, then the dashboard, Step 1/Step 2 task artifacts and records.
- Step 2 Task 01 has completed raw `radius`/`thickness` preservation and required validation. This task is the first incomplete client-storage action.
- `git status --short` shows pre-existing Step 1/Task 01 source and test changes plus the untracked plan directory. `git diff --check` is clean. No task-record validation logs exist.
- Instruction discovery found `README.md` and test READMEs, but no `CODEASSIST.md`; therefore no additional code-assist repository instructions apply.

## Test selection

Test type selected before edits: **unit**. Validation and storage are deterministic against an injected `LegacyItemStore` and trace callback. No EDMC lifecycle, `load.py`, socket, or PyQt behavior is changed; a harness test would cover the wrong boundary and remains Step 4 work.

## Requirements and implementation paths

| Area | Path | Contract |
| --- | --- | --- |
| Client processor | `overlay_client/legacy_processor.py` | Validate circle radius/thickness before `store.set`, normalize all circle integers, create `LegacyItem(kind="circle")`, and add a circle dedupe snapshot. |
| TTL store | `overlay_client/legacy_store.py` | Reuse existing `expiry = now + ttl if ttl > 0 else now` semantics unchanged. |
| Unit coverage | `tests/test_legacy_processor.py` | Cover valid/replaced circles, transparent default fill, expiry, invalid geometry/no mutation/warning, and trace snapshot variation. |

## Dependency map

Normalized compatibility/raw payload -> `process_legacy_payload` -> circle validation -> `LegacyItemStore.set` -> future Step 3 rendering. A trace callback observes the same `_hashable_payload_snapshot` used by payload-model deduplication.

## Uncertainties

None material. The established rectangle branch supplies the data/TTL/transform/timestamp/plugin patterns; this task applies those without changing rectangle/vector behavior.
