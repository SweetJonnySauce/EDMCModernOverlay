## Goal: Modernize `define_plugin_group` argument names without breaking callers

Follow persona details in `AGENTS.md`.
Document implementation results in the Implementation Results section.
After each stage is complete, change stage status to Completed.
When all stages in a phase are complete, change phase status to Completed.
If something is not clear, ask clarifying questions.

## Requirements (Initial)
- Preserve existing behavior for all current callers of `overlay_plugin.overlay_api.define_plugin_group(...)`.
- Introduce clearer canonical argument names for new usage.
- Support old and new argument names during the transition window.
- Keep runtime behavior/data output unchanged:
- same validation semantics.
- same `overlay_groupings.json` field names and structure.
- same return value and error types (`PluginGroupingError`).
- Detect and reject conflicting old/new duplicate inputs in the same call.
- Emit legacy-alias compatibility warnings for legacy argument names (log-only; no hard failure in this milestone).
- Add focused tests before and after rewiring argument handling.

## Out Of Scope (This Change)
- Changing persisted grouping JSON key names (`matchingPrefixes`, `idPrefixGroups`, etc.).
- Changing grouping semantics or validation rule behavior.
- Updating third-party plugins automatically.
- Removing legacy argument names in this release train.

## Current Touch Points
- API surface:
- `overlay_plugin/overlay_api.py` (`define_plugin_group`, normalisers, error text).
- Internal consumers:
- `utils/plugin_group_manager.py` (`_apply_define_plugin_group(**kwargs)` passthrough).
- Existing behavior coverage:
- `tests/test_overlay_api.py`.
- Docs/release notes:
- `RELEASE_NOTES.md`
- plugin docs/wiki references for `define_plugin_group` usage (follow-up docs pass).

## Schema Handling
- Scope rule: argument renaming is API-input compatibility only; persisted grouping schema is unchanged.
- `schemas/overlay_groupings.schema.json` remains the contract for stored data.
- `define_plugin_group(...)` old/new argument names must normalize into the same existing JSON keys:
- `matchingPrefixes`
- `idPrefixGroups`
- `idPrefixes`
- `idPrefixGroupAnchor`
- `offsetX` / `offsetY`
- `payloadJustification`
- `markerLabelPosition`
- `controllerPreviewBoxMode`
- `backgroundColor` / `backgroundBorderColor` / `backgroundBorderWidth`
- No schema migration is included in this plan.
- Tests must assert old-name and new-name API calls produce schema-equivalent output.

## Open Questions
- None currently.

## Naming Table for new `define_plugin_group` compatible API

| Old Name (Current API) | New Name (New compat API) | Schema Mapping (Persisted JSON) | Notes |
| --- | --- | --- | --- |
| `plugin_group` | `plugin_name` | top-level key (for example `BGS-Tally`) -> value validated by `$defs.pluginGroup` | Required plugin name |
| `matching_prefixes` | `plugin_matching_prefixes` | `matchingPrefixes` | Top-level prefix match list |
| `id_prefix_group` | `plugin_group_name`  | `idPrefixGroups.<plugin_group_name>` (group object key) | Plugin group name. This appears in Overlay Controller dropdown list. |
| `id_prefixes` | `plugin_group_prefixes` | `idPrefixGroups.<plugin_group_name>.idPrefixes` | Prefix entries for that group |
| `id_prefix_group_anchor` | `plugin_group_anchor` | `idPrefixGroups.<plugin_group_name>.idPrefixGroupAnchor` | Anchor for the group |
| `id_prefix_offset_x` | `plugin_group_offset_x` | `idPrefixGroups.<plugin_group_name>.offsetX` | Group X offset |
| `id_prefix_offset_y` | `plugin_group_offset_y` | `idPrefixGroups.<plugin_group_name>.offsetY` | Group Y offset |
| `payload_justification` | No Change | `idPrefixGroups.<plugin_group_name>.payloadJustification` | Payload text justification |
| `marker_label_position` | No Change | `idPrefixGroups.<plugin_group_name>.markerLabelPosition` | Marker label placement |
| `controller_preview_box_mode` | No Change | `idPrefixGroups.<plugin_group_name>.controllerPreviewBoxMode` | Controller preview sizing mode |
| `background_color` | `plugin_group_background_color` | `idPrefixGroups.<plugin_group_name>.backgroundColor` | Group background color |
| `background_border_color` | `plugin_group_border_color` | `idPrefixGroups.<plugin_group_name>.backgroundBorderColor` | Group border color |
| `background_border_width` | `plugin_group_border_width` | `idPrefixGroups.<plugin_group_name>.backgroundBorderWidth` | Group border width |

## Decisions (Locked)
- Backward compatibility is mandatory in this milestone: legacy names remain accepted.
- Conflict policy: if legacy and canonical aliases are both provided with different values, raise `PluginGroupingError`.
- Warnings policy: legacy-name usage logs warning(s), but behavior remains functional.
- Canonical meaning lock:
- `plugin_name` maps to schema `pluginGroup` (top-level plugin bucket).
- `plugin_group_name` maps to current `id_prefix_group` (controller dropdown group label).
- If both old and new names are provided with the same value: accept, treat new name as authoritative, and log legacy-alias compatibility warning.
- No fixed legacy-alias removal timeline is planned at this time; aliases remain supported indefinitely until explicitly revised.
- Docs rollout needs its own phase: update in-repo docs now and track out-of-repo docs/wiki updates as follow-up work items.
- Validation/error messaging uses both names during compatibility mode: `new_name (legacy_name)`.
- Legacy-name warning emission is once per process per legacy argument per calling plugin (to limit log noise).
- Signature strategy lock: `define_plugin_group` exposes canonical/new argument names, and accepts legacy names via compatibility alias adapter (`**kwargs`) at the API boundary.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Lock canonical naming contract + compatibility matrix | Completed |
| 2 | Implement argument alias adapter in `overlay_api.define_plugin_group` | Completed |
| 3 | Expand tests for backward compatibility + conflict handling | Completed |
| 4 | Release notes + implementation-results documentation | Completed |
| 5 | External docs alignment tracking (out-of-repo) | Completed |

## Phase Details

### Phase 1: Lock canonical naming contract + compatibility matrix
- Define the canonical argument names and explicit alias mapping from legacy names.
- Confirm behavior guarantees that must remain unchanged.
- Define conflict resolution and warning behavior before code changes.
- Risks: ambiguous names or accidental semantic drift during rename.
- Mitigations: explicit mapping table, targeted tests, no storage schema changes.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Inventory current argument names/usages and define proposed canonical names | Completed |
| 1.2 | Freeze alias matrix, conflict policy, and warning policy | Completed |
| 1.3 | Document acceptance criteria and no-regression invariants | Completed |

Phase 1 Outcomes:
- Canonical argument naming table is finalized and mapped to persisted schema keys.
- Compatibility contract is locked (old/new alias behavior, conflict handling, warning behavior).
- Schema boundary is locked (API rename only; no storage schema/key migration).

#### Phase 1 Execution Order
- Implement/document in strict order: `1.1` -> `1.2` -> `1.3`.
- Do not modify runtime behavior or schema during this phase; phase is contract-definition only.
- Exit gate for Phase 1:
- naming table complete and reviewed.
- compatibility/warning/conflict rules locked in Decisions.
- schema-handling boundary documented and explicit.

#### Stage 1.1 Detailed Plan
- Objective:
- Capture current API behavior and define the canonical naming map before implementation changes.
- Primary touch points:
- `overlay_plugin/overlay_api.py` (`define_plugin_group`, normalisers, error text).
- `utils/plugin_group_manager.py` (`_apply_define_plugin_group(**kwargs)` passthrough).
- `tests/test_overlay_api.py` (baseline behavior/validation contract).
- Steps:
- Inventory all current API arguments and categorize by semantic area (plugin bucket, group config, display config, styling).
- Confirm persisted-schema destination for each argument in `overlay_groupings.json`.
- Draft canonical names and populate mapping table with old name, new name, and schema mapping.
- Validate terminology against schema intent:
- `plugin_name` = top-level plugin bucket (`$defs.pluginGroup` value container).
- `plugin_group_name` = `idPrefixGroups` entry key used in controller dropdown.
- Acceptance criteria:
- Naming table is fully populated for all `define_plugin_group` arguments.
- Each row includes clear schema mapping and notes.
- No unresolved naming ambiguities remain.
- Verification to run:
- `python3 -m pytest tests/test_overlay_api.py -k "define_plugin_group"`

#### Stage 1.2 Detailed Plan
- Objective:
- Lock deterministic alias-resolution behavior so implementation can proceed without policy churn.
- Steps:
- Define alias policy for each call shape:
- legacy-only input: accepted, legacy-alias compatibility warning emitted.
- canonical-only input: accepted, no compatibility warning.
- both old/new with equal values: accepted, canonical/new authoritative, warning emitted.
- both old/new with different values: reject via `PluginGroupingError`.
- Define warning cardinality:
- once per process per legacy argument per calling plugin.
- Define error-message naming policy:
- validation/conflict errors use both names (`new_name (legacy_name)`).
- Acceptance criteria:
- Alias/conflict/warning policy is explicitly captured in Decisions.
- Policy wording is consistent across phase/stage sections.
- Verification to run:
- N/A (contract/policy locking stage; implementation and tests occur in Phases 2-3).

#### Stage 1.3 Detailed Plan
- Objective:
- Freeze no-regression invariants and boundary constraints for implementation/testing phases.
- Invariants to lock:
- output JSON content remains unchanged for equivalent old/new inputs.
- persisted key schema remains unchanged (`matchingPrefixes`, `idPrefixGroups`, etc.).
- existing valid/invalid call patterns retain pass/fail behavior.
- failures continue to use `PluginGroupingError`.
- no change to grouping semantics (only input-name compatibility layer).
- Artifacts to lock in this plan:
- `Schema Handling` section with explicit no-migration rule.
- `Naming Table` with API-to-schema mapping.
- `Decisions` section with signature strategy and warning policy.
- Acceptance criteria:
- Phase 1 artifacts are complete and internally consistent.
- Phase 2 can execute without further naming/policy decisions.
- Verification to run:
- `python3 -m pytest tests/test_overlay_api.py -k "requires_fields or requires_id_group_for_prefixes or validates"`

### Phase 2: Implement argument alias adapter in `overlay_api.define_plugin_group`
- Introduce a bounded argument-normalization layer at API boundary.
- Keep downstream validation/data update logic unchanged as much as possible.
- Risks: subtle behavior changes if normalization order differs from current signature handling.
- Mitigations: isolate adapter, keep existing normalizers and update path intact.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Finalize API signature strategy for compatibility adapter (`define_plugin_group` boundary) | Completed |
| 2.2 | Add alias normalization helper(s) and conflict detection | Completed |
| 2.3 | Wire canonicalized arguments into existing validation/update flow | Completed |
| 2.4 | Add one-time legacy-alias compatibility warning emission for legacy names | Completed |

#### Stage 2.1 Detailed Plan
- Objective:
- Finalize the concrete function-boundary shape before wiring aliases.
- Primary touch points:
- `overlay_plugin/overlay_api.py` (`define_plugin_group` signature, call boundary parsing).
- `utils/plugin_group_manager.py` (kwargs passthrough behavior compatibility check).
- Design decisions to apply:
- Keep canonical/new names as public API signature parameters.
- Accept legacy names through compatibility alias adapter kwargs at API boundary.
- Ensure no ambiguity in canonical-vs-legacy precedence.
- Ensure signature remains discoverable for plugin developers (docstring/help/type hints).
- Acceptance criteria:
- Signature strategy is implemented exactly as locked in Decisions.
- Existing kwargs-based internal call paths remain compatible.
- No runtime behavior changes beyond argument-name normalization.
- Verification to run after stage:
- `python3 -m pytest tests/test_overlay_api.py -k "define_plugin_group"`

#### Stage 2.2 Detailed Plan
- Objective:
- Build a deterministic alias normalization layer that converts old/new inputs into one canonical argument set.
- Primary touch points:
- `overlay_plugin/overlay_api.py` helper surface (new private compatibility helpers).
- Steps:
- Add a dedicated alias map (legacy -> canonical) matching the locked naming table.
- Add canonicalization helper that:
- ingests provided canonical args + legacy kwargs.
- merges into one canonical payload.
- tracks which legacy aliases were used for warning emission.
- Add conflict helper that:
- compares canonical value and legacy-derived value when both provided.
- accepts equal values (canonical authoritative).
- raises `PluginGroupingError` on non-equal values using `new_name (legacy_name)` format.
- Keep helper logic pure (no store writes/no side effects besides structured result + conflict exceptions).
- Acceptance criteria:
- Canonicalization rules are centralized in one boundary layer.
- Conflict behavior matches locked policy for all aliases.
- Error messages include both names.
- Verification to run after stage:
- `python3 -m pytest tests/test_overlay_api.py -k "define_plugin_group or validates"`

#### Stage 2.3 Detailed Plan
- Objective:
- Connect normalized canonical inputs to existing validation/update pipeline with no semantic drift.
- Primary touch points:
- `overlay_plugin/overlay_api.py` (`define_plugin_group` body, normaliser calls, `_GroupingUpdate` construction).
- `utils/plugin_group_manager.py` (compatibility validation only; code changes only if required).
- Steps:
- Replace direct raw-parameter use in `define_plugin_group` with canonicalized values from compatibility adapter.
- Preserve current downstream flow:
- normaliser calls (`_normalise_prefixes`, `_normalise_anchor`, etc.)
- `_GroupingUpdate` construction
- store apply behavior and mutation semantics
- Confirm schema output keys remain unchanged (camelCase persisted keys).
- Keep failure type unchanged (`PluginGroupingError`).
- Acceptance criteria:
- Existing define/update behavior remains unchanged for equivalent inputs.
- No changes to `_GroupingUpdate` schema or storage key names.
- Internal manager passthrough remains functional.
- Verification to run after stage:
- `python3 -m pytest tests/test_overlay_api.py -k "define_plugin_group"`

#### Stage 2.4 Detailed Plan
- Objective:
- Add low-noise, non-breaking warning behavior for legacy alias usage.
- Primary touch points:
- `overlay_plugin/overlay_api.py` logging helpers/state.
- Steps:
- Add process-level warning registry keyed by legacy argument name.
- Emit legacy-alias compatibility warning only the first time each legacy alias is seen in process lifetime.
- Ensure warning emission is non-blocking and does not alter return values or exception paths.
- Ensure same-value old+new input still warns once (per legacy arg) while succeeding.
- Preserve `new_name (legacy_name)` wording for compatibility errors.
- Acceptance criteria:
- Warning emission cardinality is once-per-process per legacy alias.
- No warning spam from repeated calls with same legacy alias.
- No change to functional behavior besides logging side effect.
- Verification to run after stage:
- `python3 -m pytest tests/test_overlay_api.py -k "define_plugin_group"`
- `python3 -m pytest tests/test_overlay_api.py -k "warning or validates"`

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3` -> `2.4`.
- Do not change schema, store format, or grouping semantics during Phase 2.
- Keep refactor footprint bounded to API boundary and compatibility helpers.

#### Phase 2 Exit Criteria
- Canonical/new public signature is in place and legacy aliases are accepted through compatibility adapter.
- Conflicts raise `PluginGroupingError` with dual-name messages.
- Legacy-alias compatibility warnings emit once per process per legacy argument per calling plugin.
- Existing `define_plugin_group` behavior remains unchanged for canonical-equivalent inputs.

### Phase 3: Expand tests for backward compatibility + conflict handling
- Add regression tests that prove old and new argument names behave equivalently.
- Add conflict-path tests for mixed alias usage.
- Risks: incomplete coverage misses edge behavior.
- Mitigations: preserve existing tests and add focused matrix tests.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add tests for legacy-only and canonical-only parity | Completed |
| 3.2 | Add mixed-input tests (equal values accepted, conflicting values rejected) | Completed |
| 3.3 | Re-run existing `test_overlay_api` no-regression coverage | Completed |
| 3.4 | Add warning-behavior tests (once-per-process emission per legacy argument) | Completed |

#### Stage 3.1 Detailed Plan
- Objective:
- Prove old-name and new-name call shapes produce equivalent persisted grouping results.
- Primary touch points:
- `tests/test_overlay_api.py`
- `overlay_plugin/overlay_api.py` (only if small testability seams are required).
- Steps:
- Add table-driven tests that call `define_plugin_group` with:
- legacy aliases only.
- canonical/new names only.
- equivalent mixed forms where values match.
- Assert parity on stored JSON output:
- same top-level plugin bucket content.
- same `matchingPrefixes` / `idPrefixGroups` structure and values.
- same return behavior.
- Acceptance criteria:
- Parity tests pass for every alias pair in the naming table.
- No schema-key drift in persisted output.
- Verification to run after stage:
- `python3 -m pytest tests/test_overlay_api.py -k "define_plugin_group and parity"`

#### Stage 3.2 Detailed Plan
- Objective:
- Lock mixed-input conflict semantics for canonical+legacy dual usage.
- Primary touch points:
- `tests/test_overlay_api.py`
- Steps:
- Add tests for each representative alias class where both names are passed:
- same values -> succeeds, canonical value remains authoritative, warning path still eligible.
- conflicting values -> raises `PluginGroupingError`.
- Assert conflict messages include both names in compatibility format:
- `new_name (legacy_name)`.
- Acceptance criteria:
- Mixed-input success and failure behavior exactly matches locked policy.
- Conflict errors consistently include both names.
- Verification to run after stage:
- `python3 -m pytest tests/test_overlay_api.py -k "conflict or mixed"`

#### Stage 3.3 Detailed Plan
- Objective:
- Ensure no regression in pre-existing overlay API behavior outside new compatibility cases.
- Steps:
- Run full `tests/test_overlay_api.py`.
- Run targeted downstream tests that rely on grouping behavior:
- `tests/test_plugin_group_manager_api.py`
- `tests/test_groupings_loader.py`
- `tests/test_groupings_migration.py`
- Acceptance criteria:
- Existing test coverage remains green with no expectation rewrites unrelated to alias compatibility.
- Verification to run after stage:
- `python3 -m pytest tests/test_overlay_api.py tests/test_plugin_group_manager_api.py tests/test_groupings_loader.py tests/test_groupings_migration.py`

#### Stage 3.4 Detailed Plan
- Objective:
- Verify warning cardinality and warning-trigger behavior for legacy aliases.
- Primary touch points:
- `tests/test_overlay_api.py`
- `overlay_plugin/overlay_api.py` warning-state globals (patched/reset in tests as needed).
- Steps:
- Add warning-behavior tests that confirm:
- first use of a legacy arg emits one legacy-alias compatibility warning.
- repeated use of same legacy arg in same process does not emit additional warnings.
- different legacy args each emit once.
- same-value old+new mixed call still goes through warning flow for that legacy arg.
- Ensure tests reset warning registry state between cases to keep deterministic behavior.
- Acceptance criteria:
- Warning emission matches once-per-process-per-legacy-argument-per-calling-plugin policy.
- Warning behavior remains non-blocking and does not change function output/error behavior.
- Verification to run after stage:
- `python3 -m pytest tests/test_overlay_api.py -k "warning"`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3` -> `3.4`.
- Keep phase scoped to tests unless a minimal behavior-preserving code fix is required to satisfy locked policy.
- Do not change schema or data-model behavior in this phase.

#### Phase 3 Exit Criteria
- Parity tests prove legacy/canonical inputs produce equivalent persisted output.
- Mixed-input conflict tests enforce dual-name error messaging.
- Warning-behavior tests confirm once-per-process-per-legacy-argument-per-calling-plugin cardinality.
- Full overlay API and targeted downstream grouping tests pass.

### Phase 4: Release notes + implementation-results documentation
- Update release notes/changelog with compatibility guidance.
- Record exact implementation outcomes and tests run in this plan.
- Risks: incomplete release communication causes migration confusion.
- Mitigations: concise release-note callout + explicit implementation-results section updates.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Add compatibility note to release notes for `0.8.0` | Completed |
| 4.2 | Record final implementation results + tests run | Completed |
| 4.3 | Add migration summary block in plan for maintainers/reviewers | Completed |

#### Stage 4.1 Detailed Plan
- Objective:
- Publish user-facing release guidance for the argument-compatibility update in `0.8.0`.
- Primary touch points:
- `RELEASE_NOTES.md`
- existing changelog/release sections related to overlay API updates.
- Steps:
- Add/expand `0.8.0` release note bullets describing:
- canonical/new `define_plugin_group` names are now available.
- legacy aliases remain accepted for compatibility.
- compatibility warnings are emitted for legacy aliases (once per process per legacy arg).
- no fixed alias-removal timeline is planned.
- Include one concise migration pointer to plan/docs mapping table.
- Acceptance criteria:
- Release notes contain accurate behavior summary and migration posture.
- Wording matches locked decisions (no implied forced deprecation timeline).
- Verification to run after stage:
- Manual doc read-through for consistency with Decisions + Naming Table.

#### Stage 4.2 Detailed Plan
- Objective:
- Record a complete execution artifact for implemented phases and verification evidence.
- Primary touch points:
- `docs/plans/define-plugin-group-argument-compat.md` (`Implementation Results`).
- Steps:
- Update implementation status lines (phase completion and remaining phases).
- Add execution summary bullets for completed stage outcomes.
- Record exact commands/results for:
- targeted phase verification.
- any broader project checks run during implementation.
- Keep results date-stamped and ordered by phase/stage.
- Acceptance criteria:
- `Implementation Results` reflects actual completed work and exact test outcomes.
- No placeholder “pending” text remains for completed phase entries.
- Verification to run after stage:
- Manual plan audit for status/result consistency.

#### Stage 4.3 Detailed Plan
- Objective:
- Provide maintainers/reviewers a quick migration reference without scanning all phases.
- Primary touch points:
- `docs/plans/define-plugin-group-argument-compat.md` migration summary subsection.
- Steps:
- Add a compact migration summary block containing:
- canonical naming table pointer.
- alias/conflict policy summary.
- warning behavior summary.
- schema-handling reminder (no schema key/storage changes).
- Include clear “what changed vs what did not change” bullets.
- Acceptance criteria:
- Migration summary is concise, accurate, and references authoritative sections in the plan.
- Reviewers can understand rollout impact in under one minute.
- Verification to run after stage:
- Manual cross-check against Decisions/Schema Handling sections.

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.
- Keep this phase documentation-only; no runtime code changes unless a doc-accuracy fix requires correcting implementation notes.

#### Phase 4 Exit Criteria
- `RELEASE_NOTES.md` accurately describes compatibility behavior for `0.8.0`.
- Plan Implementation Results are complete and consistent with executed work/tests.
- Migration summary block is present and aligned with locked decisions.

### Phase 5: External docs alignment tracking (out-of-repo)
- Record external docs/wiki pages that need updates but are not writable from this workspace.
- Provide a clear follow-up checklist and handoff notes.
- Risks: partial doc rollout causes mixed naming guidance.
- Mitigations: explicit external-doc checklist in plan and release handoff notes.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Create external-doc follow-up checklist (wiki/other systems) | Completed |
| 5.2 | Capture owner/status/tracking links for each external doc update | Completed |
| 5.3 | Add release handoff notes listing remaining non-repo doc actions | Completed |

#### Stage 5.1 Detailed Plan
- Objective:
- Build a concrete external-doc update checklist driven by the current wiki content scan.
- Scope:
- GitHub wiki pages mirrored under `docs/wiki` in this repo are used as source-of-truth for planning.
- Do not execute wiki edits in this stage; capture exact targets and required edits only.
- Initial findings captured for this phase:
- Must update:
- `define_plugin_group-API`: examples used legacy args (`plugin_group`, `matching_prefixes`, `id_prefix_group`, `id_prefixes`, `id_prefix_group_anchor`, `background_color`, `background_border_width`).
- `Getting-Started`: startup snippet used legacy args and contained `define_plugin_groups` typo (plural) that should be `define_plugin_group`.
- Likely update for terminology consistency:
- `Concepts`: legacy terminology in `Prefix Names` section referenced `idPrefixGroup`; align to canonical API naming while preserving compatibility context.
- Reference-only pages (link-only mentions; no argument rewrite required):
- `Developer-FAQs`, `send_message-API`, `send_raw-API`, `send_shape-API`, `Examples`, `_Sidebar`.
- Steps:
- Create a page-by-page checklist with update intent and status.
- Classify each page as `Must Update`, `Should Update`, or `No Change`.
- Add notes for exact section-level edits to prevent scope drift.
- Acceptance criteria:
- External checklist includes all wiki pages where `define_plugin_group` is called or documented with arguments.
- Must-update pages are explicitly separated from reference-only pages.
- Verification to run after stage:
- Manual scan validation:
- `rg -n "define_plugin_group|plugin_group=|matching_prefixes=|id_prefix_group=|id_prefixes=" docs/wiki --glob "*.md"`

#### Stage 5.2 Detailed Plan
- Objective:
- Add actionable ownership/tracking metadata for each external wiki task.
- Steps:
- For each checklist row, capture:
- page title/path.
- canonical wiki location/slug.
- owner (`TBD` if not yet assigned).
- status (`Pending`, `Ready`, `In Progress`, `Completed`).
- tracking artifact (issue/PR/link) when available; otherwise keep `TBD`.
- Add implementation notes for each page describing:
- canonical argument names that should be shown in examples.
- whether to include a legacy compatibility note and expected wording.
- Acceptance criteria:
- Every `Must Update`/`Should Update` row has owner and status fields populated (owner may be `TBD` but explicit).
- Every row has a tracking placeholder to avoid orphaned work.
- Verification to run after stage:
- Manual table audit for required fields and no `TBD` page names.

#### Stage 5.3 Detailed Plan
- Objective:
- Provide release handoff guidance so remaining wiki work is visible before/after `0.8.0` tagging.
- Steps:
- Add a release handoff block summarizing:
- which wiki pages must be updated before release notes are considered complete.
- which pages are optional polish and can follow immediately after release.
- required wording policy:
- canonical names shown first in examples.
- legacy names called out as compatibility aliases (no removal timeline).
- Include a completion check statement that Phase 5 can only be marked `Completed` when all `Must Update` rows are complete or explicitly deferred with a reason.
- Acceptance criteria:
- Handoff notes clearly separate blocking vs non-blocking external docs work.
- Migration messaging in handoff notes matches locked Decisions (dual-name compatibility, no schema changes, no forced deprecation timeline).
- Verification to run after stage:
- Manual consistency check against:
- `Decisions (Locked)`
- `Schema Handling`
- `Migration Summary (Maintainers/Reviewers)`

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.
- Keep this phase documentation-tracking only (no runtime code changes).

#### Phase 5 Exit Criteria
- Wiki task list is complete and accurately reflects the current argument-compatibility rollout state.
- All `Must Update` wiki pages are either completed or explicitly deferred with owner + reason + tracking link.
- Release handoff notes are present and aligned with locked compatibility decisions.

#### External Docs Checklist

Legend:
- `Must Update` = blocking for complete API naming rollout.
- `Should Update` = recommended terminology consistency.
- `No Change` = reference-only mention; currently acceptable.

| External Doc/Page | Location | Owner | Status | Tracking Link | Notes |
| --- | --- | --- | --- | --- | --- |
| `define_plugin_group-API` | Local mirror: `docs/wiki/define_plugin_group-API.md` (GitHub wiki: `define_plugin_group-API`) | EDMCModernOverlay maintainers | Completed (`Must Update`) | In-repo mirror update (2026-03-04) | Updated examples to canonical names and added compatibility note for legacy aliases. |
| `Getting-Started` | Local mirror: `docs/wiki/Getting-Started.md` (GitHub wiki: `Getting-Started`) | EDMCModernOverlay maintainers | Completed (`Must Update`) | In-repo mirror update (2026-03-04) | Updated startup example to canonical names and fixed `define_plugin_groups` typo. |
| `Concepts` | Local mirror: `docs/wiki/Concepts.md` (GitHub wiki: `Concepts`) | EDMCModernOverlay maintainers | Completed (`Should Update`) | In-repo mirror update (2026-03-04) | Updated Prefix Names terminology to canonical + legacy alias wording. |
| `Developer-FAQs` | Local mirror: `docs/wiki/Developer-FAQs.md` (GitHub wiki: `Developer-FAQs`) | EDMCModernOverlay maintainers | Completed (`No Change`) | N/A | Reviewed; no argument examples to rewrite. |
| `send_message-API` | Local mirror: `docs/wiki/send_message-API.md` (GitHub wiki: `send_message-API`) | EDMCModernOverlay maintainers | Completed (`No Change`) | N/A | Reviewed; reference/link only. |
| `send_raw-API` | Local mirror: `docs/wiki/send_raw-API.md` (GitHub wiki: `send_raw-API`) | EDMCModernOverlay maintainers | Completed (`No Change`) | N/A | Reviewed; reference/link only. |
| `send_shape-API` | Local mirror: `docs/wiki/send_shape-API.md` (GitHub wiki: `send_shape-API`) | EDMCModernOverlay maintainers | Completed (`No Change`) | N/A | Reviewed; reference/link only. |
| `Examples` | Local mirror: `docs/wiki/Examples.md` (GitHub wiki: `Examples`) | EDMCModernOverlay maintainers | Completed (`No Change`) | N/A | Reviewed; conceptual mention only. |
| `_Sidebar` | Local mirror: `docs/wiki/_Sidebar.md` (GitHub wiki: `_Sidebar`) | EDMCModernOverlay maintainers | Completed (`No Change`) | N/A | Reviewed; nav entry already correct. |

#### Release Handoff Notes (Phase 5)
- In-repo wiki mirror updates are complete for blocking and recommended pages.
- If publishing to external GitHub wiki is a separate sync step, publish these updated mirror pages:
- `define_plugin_group-API`
- `Getting-Started`
- `Concepts`
- Messaging policy to keep consistent across all wiki pages:
- canonical/new names are authoritative in examples.
- legacy names are compatibility aliases and remain supported.
- no schema key changes and no fixed deprecation timeline.

## Test Plan (Per Iteration)
- Env setup (once per machine):
- `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- Headless quick pass:
- `python3 -m pytest tests/test_overlay_api.py`
- Targeted compatibility suite (when added):
- `python3 -m pytest -k "overlay_api and define_plugin_group"`
- Milestone checks:
- `make check`
- `make test`

## Implementation Results
- Plan created on 2026-03-04.
- Phase 1 implemented on 2026-03-04.
- Phase 2 implemented on 2026-03-04.
- Phase 3 implemented on 2026-03-04.
- Phase 4 implemented on 2026-03-04.
- Phase 5 implemented on 2026-03-04.

### Phase 1 Execution Summary
- Stage 1.1 completed:
- Audited `define_plugin_group` API surface in `overlay_plugin/overlay_api.py` and locked canonical names in the naming table.
- Confirmed schema mapping for each argument, including top-level plugin bucket mapping (`plugin_name` -> top-level key, value validated by `$defs.pluginGroup`).
- Stage 1.2 completed:
- Locked alias-resolution policy for legacy/new names (legacy-only accepted with warning, canonical-only accepted, same-value dual input accepted with canonical authority, conflicting dual input rejected).
- Locked warning behavior to once-per-process per legacy argument.
- Locked compatibility error messaging format to include both names (`new_name (legacy_name)`).
- Stage 1.3 completed:
- Locked no-regression invariants and schema boundary:
- API input naming compatibility only.
- persisted JSON schema/keys unchanged.
- `PluginGroupingError` remains failure type.

### Tests Run For Phase 1
- Targeted API behavior verification (passed):
- `python3 -m pytest tests/test_overlay_api.py -k "define_plugin_group"`
- Result: 26 passed, 1 deselected.
- Targeted validation invariants verification (passed):
- `python3 -m pytest tests/test_overlay_api.py -k "requires_fields or requires_id_group_for_prefixes or validates"`
- Result: 5 passed, 22 deselected.

### Phase 2 Execution Summary
- Stage 2.1 completed:
- Updated `define_plugin_group` API boundary to canonical/new argument names.
- Added compatibility alias adapter path via legacy kwargs handling to preserve existing callers.
- Stage 2.2 completed:
- Added centralized legacy->canonical alias merge helpers and unknown-alias guard.
- Implemented explicit conflict detection for dual-name inputs with dual-name error messaging.
- Stage 2.3 completed:
- Wired canonicalized arguments into existing normalisation/update flow without changing persisted schema keys or `_GroupingUpdate` shape.
- Preserved downstream grouping-store behavior and `PluginGroupingError` failure model.
- Stage 2.4 completed:
- Added once-per-process legacy-alias compatibility warning emission per legacy argument.
- Added compatibility error-message rewriting for renamed fields using `new_name (legacy_name)` format.

### Tests Run For Phase 2
- Overlay API full module (passed):
- `python3 -m pytest tests/test_overlay_api.py`
- Result: 27 passed, 0 failed.
- Downstream grouping compatibility checks (passed):
- `python3 -m pytest tests/test_plugin_group_manager_api.py tests/test_groupings_loader.py tests/test_groupings_migration.py`
- Result: 12 passed, 0 failed.
- Project checks (passed):
- `make check`
- Result: `ruff` passed, `mypy` passed, full pytest passed (484 passed, 25 skipped).
- `make test`
- Result: full pytest passed (484 passed, 25 skipped).

### Phase 3 Execution Summary
- Stage 3.1 completed:
- Added parity test coverage showing legacy-name and canonical-name API calls persist equivalent grouping payloads.
- Stage 3.2 completed:
- Added mixed-input behavior tests for:
- same-value old/new combinations (accepted and persisted correctly).
- conflicting old/new combinations (raise `PluginGroupingError` with dual-name message fragments).
- Stage 3.3 completed:
- Re-ran full `test_overlay_api` plus targeted downstream grouping tests (`plugin_group_manager_api`, `groupings_loader`, `groupings_migration`) to confirm no regressions.
- Stage 3.4 completed:
- Added warning-behavior tests validating once-per-process emission per legacy argument.
- Added mixed old/new same-value warning-path test coverage.

### Tests Run For Phase 3
- Stage 3.1 parity verification (passed):
- `python3 -m pytest tests/test_overlay_api.py -k "define_plugin_group and parity"`
- Result: 1 passed, 34 deselected.
- Stage 3.2 mixed/conflict verification (passed):
- `python3 -m pytest tests/test_overlay_api.py -k "conflict or mixed"`
- Result: 5 passed, 30 deselected.
- Stage 3.4 warning verification (passed):
- `python3 -m pytest tests/test_overlay_api.py -k "warning"`
- Result: 2 passed, 33 deselected.
- Stage 3.3 regression verification (passed):
- `python3 -m pytest tests/test_overlay_api.py tests/test_plugin_group_manager_api.py tests/test_groupings_loader.py tests/test_groupings_migration.py`
- Result: 47 passed, 0 failed.

### Phase 4 Execution Summary
- Stage 4.1 completed:
- Updated `RELEASE_NOTES.md` for `0.8.0` with `define_plugin_group` compatibility guidance:
- canonical/new names available.
- legacy aliases still supported.
- once-per-process-per-legacy-argument-per-calling-plugin compatibility warning behavior.
- no schema/storage key migration required.
- Stage 4.2 completed:
- Updated this plan's `Implementation Results` with current phase completion state and recorded phase outcomes.
- Stage 4.3 completed:
- Added migration summary block below for maintainers/reviewers with changed vs unchanged behavior references.

### Tests Run For Phase 4
- Documentation consistency verification (manual):
- Confirmed release-note wording matches locked Decisions and Schema Handling sections in this plan.
- No runtime code changes were introduced in Phase 4, so no additional automated test execution was required.

### Phase 5 Execution Summary
- Stage 5.1 completed:
- Executed full `docs/wiki` scan for `define_plugin_group` references and argument usage.
- Created and finalized a page-by-page external docs checklist with `Must Update`, `Should Update`, and `No Change` classification.
- Stage 5.2 completed:
- Updated tracked wiki pages in the in-repo mirror:
- `docs/wiki/define_plugin_group-API.md`: migrated examples to canonical argument names and added legacy alias compatibility note.
- `docs/wiki/Getting-Started.md`: migrated startup snippet to canonical argument names and fixed `define_plugin_groups` typo.
- `docs/wiki/Concepts.md`: aligned Prefix Names terminology to canonical `plugin_group_name` with legacy alias note.
- Updated checklist ownership/status/tracking fields to completion state.
- Stage 5.3 completed:
- Updated release handoff notes to reflect completed in-repo mirror updates and external wiki sync guidance (if separate publish path is used).

### Tests Run For Phase 5
- Wiki/doc scan verification (manual, passed):
- `rg -n "define_plugin_group|plugin_group=|matching_prefixes=|id_prefix_group=|id_prefixes=" docs/wiki --glob "*.md"`
- Result: no remaining legacy-argument examples in updated canonical docs (`define_plugin_group-API`, `Getting-Started`); remaining hits are legacy-context references in planning/docs where expected.
- Documentation consistency verification (manual, passed):
- Confirmed Phase 5 checklist/status, execution order, exit criteria, and release handoff notes are aligned and complete.

### Migration Summary (Maintainers/Reviewers)
- What changed:
- `define_plugin_group` now has canonical/new argument names with legacy alias compatibility.
- Legacy alias usage emits compatibility warnings (once per process per legacy argument per calling plugin).
- Conflict handling is explicit for mixed old/new inputs with dual-name error messaging.
- What did not change:
- Persisted `overlay_groupings.json` schema keys/shape.
- Grouping semantics and downstream store/update behavior.
- Failure type (`PluginGroupingError`) for validation/compatibility errors.
- Quick references:
- Naming + API-to-schema map: `Naming Table for new define_plugin_group compatible API`.
- Compatibility behavior rules: `Decisions (Locked)`.
- Schema boundary rules: `Schema Handling`.
