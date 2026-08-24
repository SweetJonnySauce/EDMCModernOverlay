# Task: Correct Pure Data and Container Types

## Description

Resolve the frozen Stage 3.1 geometry, anchor, legacy payload, override-prefix,
and transform-helper mypy diagnostics with conservative annotations. Preserve
all runtime calculations, accepted payload behavior, container contents, and
the separate fix219 X11 repair.

## Background

Stage 2.1 froze 34 pure-data errors. This task owns the 20 diagnostics in the
six modules named below; the other 14 test-stub diagnostics remain outside this
task. Stage 2.3 cleared the shared-state family and its latest focused target
now retains only renderer diagnostics for Stage 3.2, so this task must not
reopen mixin, Qt, renderer, integration, configuration, or backend work.

The source establishes that geometry origin intermediates become floats before
final integer rounding; anchor trace details contain both floats and strings;
legacy vector points are heterogeneous string/integer dictionaries; parsed
prefixes are `PrefixEntry` values; and transformed rectangles are two-float
points. `PayloadModel.ingest` is the one edge: the payload boundary is typed as
`dict[str, object]`, while the pre-existing runtime code passes TTL directly to
`int()`. Do not silently narrow that accepted runtime contract.

## Reference Documentation

**Required:**

- Design: `.code-assist/2026-08-23-overlay-client-mypy-debt/plan.md`
- Context: `.code-assist/2026-08-23-overlay-client-mypy-debt/context.md`
- Orchestration: `.code-assist/2026-08-23-overlay-client-mypy-debt/orchestration-prompt.md`
- Frozen inventory: `.code-assist/2026-08-23-overlay-client-mypy-debt/stage-2.1-baseline-inventory/inventory.md`
- Prior handoff: `.code-assist/2026-08-23-overlay-client-mypy-debt/stage-2.3-mixin-declarations/remediation-1/handoff.md`
- Stage scope review: `.code-assist/2026-08-23-overlay-client-mypy-debt/stage-3.1-pure-data-types/scope-review.md`
- X11 boundary record: `.code-assist/2026-08-21-fix219-x11-surface-artifacts/`

**Note:** Read every governing artifact, the current execution status, this
task, the prior handoff, relevant sources/tests, and the scoped dirty diff
before implementation. The approved parent plan authorizes this single-task
breakdown.

## Technical Requirements

1. Resolve only these frozen error sites: `follow_geometry.py` 74/76/185/187/202/204; `anchor_helpers.py` 65/66/85/86; `legacy_processor.py` 240/310/312/315/318; `plugin_overrides.py` 514/523; `payload_model.py` 98; and `transform_helpers.py` 203/242. Do not take ownership of the remaining pure-data test-stub diagnostics, renderer, integration, or shared-state errors.
2. Keep returned geometry as `tuple[int, int, int, int]`; type only float-valued native-origin intermediates. Retain scale selection, device-ratio handling, rounding, positive width/height clamps, logging, and follow behavior byte-for-byte except for annotations needed to satisfy mypy.
3. Type anchor trace detail values as the exact numeric/string union, legacy transformed payload data as mappings, legacy vector points as their current integer/string heterogeneous shape, override-prefix locals as `tuple[PrefixEntry, ...]`, and rectangle point lists as exactly two floating coordinates. Retain all existing stored values, filtering, prefix matching, and transform arithmetic.
4. Resolve the TTL diagnostic only with a precise, behavior-preserving type representation. Do not add a new runtime validation branch, coerce through a broad `Any`, use a broad cast/ignore, or narrow accepted values based on assumption. If the current direct `int()` acceptance cannot be modeled from source/call-site evidence, leave that diagnostic unresolved and stop for coordinator review with the evidence. If any behavior change is genuinely required, add a focused unit test first and obtain coordinator review before changing code.
5. Do not alter Qt MRO, initialization, timers, painting, focus, follow behavior, backend selection, attachment/input policy, renderer semantics, `load.py`, config, or build metadata. Do not introduce compositor-specific imports or raw backend/helper enum dispatch outside backend-owned interfaces. Preserve the clear-first transparent-surface repair.
6. Do not introduce `ignore_errors`, blanket/broad `Any`, or unexplained `# type: ignore`. A narrow type-only cast needs an adjacent justification tied to a directly established runtime contract and coordinator review.
7. Before edits, record one focused RED command:

   ```bash
   source overlay_client/.venv/bin/activate && python -m mypy --follow-imports=skip \
     overlay_client/follow_geometry.py \
     overlay_client/anchor_helpers.py \
     overlay_client/legacy_processor.py \
     overlay_client/plugin_overrides.py \
     overlay_client/payload_model.py \
     overlay_client/transform_helpers.py
   ```

   After edits, rerun that identical command once as the GREEN measurement and
   record the exact error delta. Do not rerun an unchanged failing command more
   than once, and do not run the directory-wide milestone in this stage.
8. Run this focused pure-unit regression slice after the GREEN measurement:

   ```bash
   source overlay_client/.venv/bin/activate && python -m pytest \
     overlay_client/tests/test_follow_geometry.py \
     overlay_client/tests/test_anchor_helpers.py \
     overlay_client/tests/test_transform_helpers.py \
     overlay_client/tests/test_payload_dedupe.py \
     overlay_client/tests/test_override_grouping.py -q
   ```

   No harness test applies because `load.py` and EDMC lifecycle wiring are out
   of scope. Existing unit tests are the selected regression proof for a
   source-proven annotation-only change; add/update a test only before a
   behavior change, especially a TTL coercion change.
9. Update this stage directory's `context.md`, `plan.md`, and `progress.md`
   before production edits, retain command output here, and leave a handoff
   containing exactly: `Status; Files changed; Validation commands/results;
   Decisions; Risks; Next exact action.`

## Dependencies

- Stage 2.1's 203-error baseline and its 20-error pure-data subset.
- Stage 2.3 remediation handoff, which confirms shared-state work is complete
  and renderer diagnostics are deferred to Stage 3.2.
- The existing `overlay_client/.venv` with mypy and pytest.
- The intentionally dirty, independent fix219/X11 surface-clear repair.

## Implementation Approach

1. Compare every frozen diagnostic with its direct assignment and its existing
   focused unit-test contract; make only annotation or exact-container-shape
   corrections whose values are proven by current source.
2. Treat TTL coercion independently. Prefer a type-only representation that
   preserves the current direct `int()` call; stop rather than changing runtime
   input acceptance or introducing a broad typing escape hatch.
3. Capture the one focused RED/GREEN delta, run the selected pure unit slice,
   inspect the scoped diff for behavior and fix219-boundary preservation, and
   record any deliberately unresolved diagnostic for coordinator review.

## Acceptance Criteria

1. **Source-proven pure-data contracts**
   - Given the current geometry, anchor, vector, prefix, payload, and transform
     implementations
   - When their frozen annotations are corrected
   - Then float intermediates, mixed trace/vector mapping values, `PrefixEntry`
     tuples, and two-float points match their existing runtime values without
     modifying calculations, filtering, serialization, or storage.

2. **Bounded mypy improvement**
   - Given the focused RED command records the Stage 3.1 diagnostics
   - When the conservative type corrections are applied
   - Then the identical GREEN command reports the exact reduction with no
     suppressions or hidden errors; any TTL diagnostic that cannot be modeled
     precisely is preserved and documented for coordinator review.

3. **Pure behavior regression protection**
   - Given existing geometry, anchor, transform, dedupe, and override tests
   - When the required focused pytest slice runs
   - Then it passes with the same rounding/clamp, justification trace,
     transform, dedupe/TTL, and prefix-grouping behavior. If a runtime helper
     change becomes necessary, a new focused unit test is RED before the code
     change and GREEN afterward.

4. **Boundary and scope discipline**
   - Given the scoped diff and prior Stage 2.3 handoff
   - When the implementation is reviewed
   - Then it contains no lifecycle/MRO/follow/render/config change,
     compositor-specific generic import or enum dispatch, broad `Any`/ignore,
     or change to the fix219 clear-first surface contract.

## Metadata

- **Complexity**: Medium
- **Labels**: mypy, typing, overlay-client, pure-data, geometry, payload, stage-3.1
- **Required Skills**: Python typing and mypy diagnosis, pure-unit-test selection, payload/geometry contract review
