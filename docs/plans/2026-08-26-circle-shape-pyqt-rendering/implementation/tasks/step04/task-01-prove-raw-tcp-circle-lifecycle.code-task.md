# Task: Prove Raw/TCP Circle Lifecycle Wiring

## Description
Add focused mixed-level regression coverage proving that a raw/TCP circle crosses the EDMC runtime normalization and publication seam without losing its canonical fields, while invalid circle geometry is rejected by the authoritative client processor before it can create or replace a drawable item. This task changes tests only; the already-completed producer, normalizer, processor, and renderer behavior is not to be reshaped.

## Background
Steps 1–3 added the circle compatibility payload, raw-field preservation, centralized client validation/storage, and PyQt rendering. The plugin runtime's `_handle_legacy_tcp_payload` is the remaining lifecycle seam: it normalizes raw legacy TCP input through `normalise_legacy_payload`, adds the `LegacyOverlay` envelope, and publishes it to the client. The runtime must preserve circle `id`, `shape`, centre coordinates, `radius`, `thickness`, colours/fill, TTL, and plugin attribution exactly as the existing harness fixture observes. The runtime is deliberately not the geometry authority: malformed geometry may be normalized and published, but the client must drop it before a same-ID drawable store item is mutated.

## Reference Documentation
**Required:**
- Design: docs/plans/2026-08-26-circle-shape-pyqt-rendering/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/research/payload-and-rendering.md (raw/TCP boundary and invalid-geometry invariant)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/plan.md (Step 4 Stage 4.1 and exact validation commands)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step02/task-01-preserve-circle-raw-normalization.code-task.md (normalizer contract)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step02/task-02-validate-and-store-circle-items.code-task.md (authoritative validation/no-mutation contract)
- tests/test_harness_legacy_tcp_ingestion.py (runtime fixture and external-publication capture pattern)
- tests/test_legacy_processor.py (deterministic client-store unit-test pattern)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. **Test type selected before edits: mixed (harness plus unit).** `tests/test_harness_legacy_tcp_ingestion.py` exercises `_PluginRuntime` lifecycle wiring, its EDMC shims, and fake external publisher, so the runtime proof is a harness test. The invalid-geometry replay/store assertion is deterministic client processing with injected time/store only, so it belongs in unit coverage. No live EDMC, OAuth, external API, socket endpoint, or upload is authorized.
2. Extend `tests/test_harness_legacy_tcp_ingestion.py` using its existing `harness_runtime_context` and `_publish_external` capture. Send a raw circle containing stable `id`, `shape: "circle"`, `color`, `fill`, centre `x`/`y`, positive `radius`/`thickness`, positive `ttl`, and `plugin`; assert `_handle_legacy_tcp_payload` returns `True` and the captured `LegacyOverlay` publication retains every listed circle field and the expected `legacy_raw`/timestamp runtime metadata. Do not open a real TCP listener or modify runtime code.
3. Add a focused unit replay assertion in `tests/test_legacy_processor.py` (or the established adjacent pure test location) that starts with a valid stored circle, supplies an invalid raw-normalized circle update for the same ID, and proves `process_legacy_payload` returns the no-repaint result, logs actionable invalid-geometry evidence, and leaves the existing item unchanged. Build the payload through the established normalizer contract or reuse the canonical normalized shape fixture so the assertion explicitly anchors the raw-to-client boundary without duplicating unrelated rendering tests.
4. Keep the authority boundary explicit in test names/comments: plugin-side normalization preserves raw geometry; client-side processing rejects missing, non-numeric, zero, or negative `radius`/`thickness` before store mutation. Do not change the already-approved rule by making the runtime reject geometry itself.
5. Preserve existing message, rectangle, vector, stopped-runtime, and direct circle processor coverage. Do not alter `load.py`, `EDMCOverlay/edmcoverlay.py`, `overlay_client` production modules, paint-command tests, render-surface tests, task artifacts outside this task, the approved plan, or the execution dashboard.
6. Run the Step 4 plan commands exactly, in order, after the focused test changes:
   - `overlay_client/.venv/bin/python -m pytest -m harness tests/test_harness_legacy_tcp_ingestion.py -q`
   - `overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py overlay_client/tests/test_paint_commands.py -q`
   Do not substitute an unmarked or headless-only command for the harness command. If a command cannot run, capture the exact output and stop for main-thread review rather than weakening coverage.
7. Record the selected test types, exact commands, outcomes, and any skip reason in `docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step04-task01/progress.md`; do not update the approved plan or execution dashboard from this task context.

## Dependencies
- Steps 1–3 must remain present: canonical circle payload construction, raw normalization, authoritative storage validation, and render dispatch are already complete.
- The existing EDMC harness fixture supplies lifecycle-safe module shims and fake publication capture.
- The client `LegacyItemStore` and `process_legacy_payload` provide the pure no-drawable-item assertion without a live overlay.
- Task 02 depends on this task's accepted test evidence so its copyable documentation example can match the proven wire contract.

## Implementation Approach
1. Read the existing harness fixture, valid-message and invalid-vector lifecycle tests, plus the existing circle normalizer/processor tests. Add a failing harness test for exact valid circle publication and a failing pure replay/store test for the invalid same-ID update.
2. Use only existing test doubles and fake adapters. Assert the envelope and canonical circle fields separately from runtime-added `timestamp` and `legacy_raw` metadata; do not impose a new raw payload shape such as synthetic circle `w`/`h` fields.
3. Run the two exact Step 4 commands in order. Record results in the task record only, then provide the required handoff for independent main-thread review before Task 02 starts.

## Acceptance Criteria

1. **Valid raw/TCP circle retains the canonical wire contract**
   - Given the existing EDMC harness runtime and a raw circle with stable ID, centre coordinates, positive radius/thickness, colour, fill, TTL, and plugin attribution
   - When `_handle_legacy_tcp_payload` processes it through the fake external publisher
   - Then it returns `True` and publishes a `LegacyOverlay` shape event retaining every supplied circle field, with only established runtime metadata added.

2. **Invalid raw geometry never creates or replaces a drawable circle**
   - Given a client store containing a valid circle and a same-ID raw-normalized update with missing, non-numeric, zero, or negative radius or thickness
   - When the client processor replays that update
   - Then it returns the no-repaint result, logs the ID and invalid geometry, and preserves the original stored circle unchanged.

3. **Validation responsibility remains behavior-compatible**
   - Given malformed circle geometry reaches the plugin runtime
   - When normalization/publication and client processing are observed at their respective boundaries
   - Then the runtime preserves the raw fields for the authoritative client path, and the client—not a new runtime rule—performs the rejection before drawable-item mutation.

4. **Existing lifecycle and rendering regressions stay green**
   - Given existing raw/TCP message/vector harness coverage and circle/paint-command unit coverage
   - When the exact Step 4 plan commands run
   - Then both commands pass, including the existing rectangle/vector behavior, or their exact failure/skip evidence is recorded without waiving the gate.

## Metadata
- **Complexity**: Medium
- **Labels**: circle-shape, raw-payload, tcp, edmc-harness, lifecycle, unit-tests, harness-tests, step-4
- **Required Skills**: pytest, EDMC harness fixtures, lifecycle-safe fake adapters, legacy payload normalization, deterministic store testing
