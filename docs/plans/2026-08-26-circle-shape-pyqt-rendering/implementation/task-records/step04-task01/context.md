# Step 04 Task 01 Context

## Mode and scope

`code-assist` runs in auto mode for Step 4 Task 01 only. The task adds mixed harness and unit regression coverage for the raw/TCP circle lifecycle. It must not change production code, the approved plan, or the execution dashboard. No real EDMC runtime, TCP listener, API, OAuth, upload, or external publisher is used.

## Restart reconciliation

- Read the governing artifacts in the orchestration-required order, the task artifact, dashboard, existing task records, and available validation evidence.
- Steps 1–3 are implemented and evidenced; Step 4 Task 01 is the first incomplete implementation task. No pre-existing Step 4 Task 01 record/log exists.
- `git status --short` contains the expected pre-existing Steps 1–3 source/test changes and the untracked planning directory. `git diff --check` is clean. Those changes are out of scope and will not be altered.
- Instruction discovery found `README.md` and harness notes, with no `CODEASSIST.md`; no further code-assist repository instructions apply.

## Test selection

Test type selected before edits: **mixed**.

- **Harness:** `tests/test_harness_legacy_tcp_ingestion.py` calls `_PluginRuntime._handle_legacy_tcp_payload` through the existing EDMC shims and a fake `_publish_external` capture. It proves the lifecycle/publication boundary without a socket or live EDMC.
- **Unit:** `tests/test_legacy_processor.py` replays a normalised raw circle against an injected `LegacyItemStore`, fixed state, and `caplog`. It proves client-side invalid-geometry rejection/no mutation deterministically.

## Requirements and dependency map

| Area | Path | Contract |
| --- | --- | --- |
| Runtime harness | `tests/test_harness_legacy_tcp_ingestion.py` | A valid raw circle is normalised, wrapped in `LegacyOverlay`, and externally published with canonical fields plus `legacy_raw` and timestamp metadata. |
| Raw normaliser | `EDMCOverlay.edmcoverlay.normalise_legacy_payload` | Preserves raw circle geometry; it does not become a geometry authority. |
| Client processor | `overlay_client.legacy_processor.process_legacy_payload` | Rejects invalid radius/thickness before `LegacyItemStore` mutation and logs actionable ID/field/value evidence. |
| Unit proof | `tests/test_legacy_processor.py` | Replays an invalid raw-normalised same-ID update after a valid circle is stored. |

Raw/TCP circle -> runtime normalisation -> fake external `LegacyOverlay` publication -> client normalisation replay -> authoritative processor validation -> unchanged drawable store item.

## Constraints and uncertainties

The existing direct processor tests already exercise all invalid radius/thickness forms. This task adds the raw-normalised replay seam explicitly, while keeping the focused assertion parameterized over missing, non-numeric, zero, and negative geometry. No material uncertainty remains.
