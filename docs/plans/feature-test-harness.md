## Goal: Add a vendored EDMC test harness (BGS-Tally based) for integration-style plugin testing.

Follow persona details in `AGENTS.md`.
Document implementation results in the `Implementation Results` section.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear, capture it under `Open Questions`.

## Requirements (Initial)
- Copy required harness files from `aussig/BGS-Tally` branch `feature/Issue-454/test-harness` into this repo.
- Pin vendored harness source to commit `3e5fe957d299a43e28a64df35145f569c5ad0a7f`.
- Minimum vendored set:
- `tests/__init__.py`
- `tests/harness.py`
- `tests/edmc/**` (entire directory contents)
- `tests/edmc/plugins/**` (full upstream plugin fixture set, vendored now)
- Do not reference remote harness code at runtime; vendor a local snapshot so we can modify it independently.
- Create `tests/config/` now; add repo-specific config fixtures incrementally.
- Keep production/plugin runtime code isolated from harness internals (harness is test-only).
- Hard requirement: do not change `tests/harness.py` or any file under `tests/edmc/**` after vendoring; treat them as immutable upstream snapshots.
- Hard requirement: vendor `tests/__init__.py` from upstream and keep it as part of the vendored snapshot.
- Avoid editing vendored harness internals where possible; prefer local wrappers/adapters around it.
- Add an overlay adapter seam so harness-driven tests can exercise this project’s overlay behavior without tightly coupling tests to legacy mock internals.
- Preserve deterministic event replay behavior (timestamp interpolation, sequence playback) from the source harness.
- Hard requirement: add a harness-backed integration test for overlay chat commands handled by `overlay_plugin/journal_commands.py`.
- Chat-command coverage requirement (minimum smoke set):
- launch via bare prefix (`!ovr`)
- help (`!ovr help` or `!ovr ?`)
- toggle via configured toggle argument (default `t`)
- group actions (`on`, `off`, `status`, `toggle`) including quoted group target support
- profile cycling (`profile next` / `profile prev`) and profile status surface (`profile status` or `profiles`)
- Create and maintain `tests/config/journal_events.json` as the harness fixture file containing `SendText` sequences for these chat-command scenarios.
- Treat `tests/config/journal_events.json` as a shared fixture consumed by harness chat-command tests.
- Chat-command assertion policy requirement:
- when a runtime callback exists for a command path, assert that callback invocation occurred;
- if no runtime callback exists for that command path, assert at minimum that the chat command was handled.
- Harness-backed tests are part of the default project gate and must run under `make check`.

## Suggested Additional Requirements
- Track source provenance:
- record upstream repo, branch, and pinned commit SHA (`3e5fe957d299a43e28a64df35145f569c5ad0a7f`) in `tests/HARNESS_README.md`.
- Keep vendored import surface stable:
- expose one local entrypoint (`from harness import TestHarness`) and avoid test files importing deep internals.
- Add a synchronization strategy:
- a small script or documented manual steps for future upstream refreshes and conflict handling.
- Harness tests may use a marker for filtering convenience, but they are still included in default `make check`.
- Define adapter-level assertions for overlay outputs (messages, shapes, raw payloads) so tests validate behavior, not implementation details.
- Adapter fidelity requirement: prefer higher-fidelity integration by forwarding through real overlay integration seams (for example `overlay_plugin.overlay_api`) when available, with safe fallbacks.

## Out Of Scope (This Change)
- Full EDMC parity beyond what the vendored harness already supports.
- Refactoring production overlay runtime to fit harness constraints.
- Large-scale rewrites of the vendored harness internals during initial import.

## Current Touch Points
- New code:
- `tests/__init__.py`
- `tests/harness.py`
- `tests/edmc/**`
- `tests/config/**`
- `tests/overlay_adapter.py` (planned)
- `tests/HARNESS_README.md` (planned)
- Existing tests and wiring:
- `tests/conftest.py`
- `tests/test_harness_integration.py` (planned)
- `tests/test_harness_chat_commands.py` (planned)
- Docs:
- `docs/plans/feature-test-harness.md`
- `docs/testing.md` (planned updates)

## Assumptions
- Source branch remains available for at least the initial vendoring pass.
- Vendored files can be stored under `tests/` without conflicting with existing test tooling.
- Existing test suite remains the default gate; harness tests are included in `make check`.

## Risks
- Upstream harness uses legacy overlay mocks that diverge from this project’s overlay interfaces.
- Mitigation: adapter shim maps expected legacy calls to a local capture sink and/or modern overlay API facades.
- Vendored harness may drag in stale EDMC mock behavior not aligned with this plugin.
- Mitigation: constrain scope to minimum import set first; patch only via wrapper/adapters; add contract tests before behavioral edits.
- Future upstream syncs can become manual and error-prone.
- Mitigation: record provenance and add a repeatable sync checklist/script.

## Open Questions
- None currently.

## Decisions (Locked)
- Harness source will be vendored locally under `tests/` and treated as test-only code.
- Initial import should minimize edits to vendored files; integration customizations should live in local wrapper/adapter modules first.
- `tests/harness.py` and `tests/edmc/**` are read-only in this effort; all integration changes must be implemented outside those files.
- Use upstream commit `3e5fe957d299a43e28a64df35145f569c5ad0a7f` as the vendored harness baseline.
- If a change to vendored harness files is ever required to reduce complexity (for example removing mock overlay behavior), pause and ask for explicit approval first.
- Vendor full upstream `tests/edmc/plugins/**` in the initial import.
- Vendor upstream `tests/__init__.py` as part of the snapshot.
- Harness tests run as part of default `make check`.
- Chat-command harness tests assert callback invocation when callback exists; otherwise assert command handled.
- Use a higher-fidelity adapter path (real overlay integration seams first, fallback second).
- `tests/config/` is created now and populated with project-specific fixtures over time.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Requirements and contracts | Completed |
| 2 | Vendor baseline harness files | Completed |
| 3 | Overlay adapter and bootstrap integration | Completed |
| 4 | Harness smoke tests and validation | Completed |
| 5 | Documentation, sync workflow, and follow-ups | Completed |

## Implementation Session Execution Plans

### Phase 1 Execution Plan (This Run)
- Finalize and lock ownership boundaries in this plan:
- vendored immutable snapshot: `tests/__init__.py`, `tests/harness.py`, `tests/edmc/**`
- project-owned mutable integration layer: `tests/overlay_adapter.py`, `tests/harness_bootstrap.py`, `tests/config/**`, harness test files.
- Lock adapter contract for this repo:
- overlay capture surface: `messages`, `shapes`, `raw_payloads`
- adapter method surface: `connect`, `send_message`, `send_shape`, `send_raw`
- fallback behavior: if modern send path cannot be imported in harness context, capture in-memory and keep tests assertion-driven.
- Confirm pinned upstream source details for vendoring:
- repo: `aussig/BGS-Tally`
- branch: `feature/Issue-454/test-harness`
- commit: `3e5fe957d299a43e28a64df35145f569c5ad0a7f`
- Verification commands:
- `git ls-remote https://github.com/aussig/BGS-Tally.git 3e5fe957d299a43e28a64df35145f569c5ad0a7f`

### Phase 2 Execution Plan (This Run)
- Vendor snapshot files directly from pinned commit without edits:
- `tests/__init__.py`
- `tests/harness.py`
- `tests/edmc/**` including `tests/edmc/plugins/**`
- Create initial local harness config structure:
- `tests/config/README.md`
- placeholder shared fixture file path: `tests/config/journal_events.json`
- Verify vendored files are present/importable:
- `python -m pytest -k harness --collect-only`

### Phase 3 Execution Plan (This Run)
- Add non-vendored bootstrap+adapter layer that does not modify harness internals:
- `tests/overlay_adapter.py`: compatibility adapter with capture assertions.
- `tests/harness_bootstrap.py`: bootstrap helpers that patch harness runtime constraints (headless Tk, dependency validation, import order, overlay module wiring).
- Ensure harness uses adapter through module injection only.
- Add reusable assertion helpers for harness tests.
- Verification commands:
- `python -m pytest tests/test_harness_integration.py -k adapter -q`
- `python -m pytest tests/test_harness_integration.py -k bootstrap -q`

### Phase 4 Execution Plan (This Run)
- Add harness-backed integration tests:
- `tests/test_harness_chat_commands.py` with journal replay sequences from shared fixture.
- `tests/test_harness_integration.py` startup/bootstrap smoke coverage.
- Add shared fixture:
- `tests/config/journal_events.json` containing `SendText` events for required smoke set.
- Assertions:
- callback invocation for paths with runtime callbacks
- handled-command fallback assertion where callback unavailable
- Verify harness tests in default gate:
- `python -m pytest tests/test_harness_chat_commands.py -q`
- `python -m pytest tests/test_harness_integration.py -q`
- `make check`

### Phase 5 Execution Plan (This Run)
- Add harness provenance+usage docs:
- `tests/HARNESS_README.md` with upstream source, pinned commit, immutable snapshot policy, and local integration ownership.
- Add refresh workflow helper:
- `scripts/sync_test_harness_from_bgstally.sh` (copy-first sync script for pinned/target commits).
- Update test docs:
- `docs/testing.md` harness run commands and expectations.
- Record follow-up backlog in this plan.
- Verification commands:
- `bash -n scripts/sync_test_harness_from_bgstally.sh`
- `rg -n "feature/Issue-454/test-harness|3e5fe957d299a43e28a64df35145f569c5ad0a7f|Follow-up|Backlog" docs/plans/feature-test-harness.md tests/HARNESS_README.md`

## Phase Details

### Phase 1: Requirements and Contracts
- Finalize copied file set, directory structure, and no-runtime-dependency policy.
- Define overlay adapter contract before implementation.
- Risks: unclear boundaries between vendored and project-owned code.
- Mitigations: explicit ownership map in this plan and `tests/HARNESS_README.md`.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Confirm source snapshot and minimum file set to vendor | Completed |
| 1.2 | Lock target layout under `tests/` and ownership boundaries | Completed |
| 1.3 | Define overlay adapter contract and test expectations | Completed |

#### Stage 1.1 Detailed Plan
- Objective:
- Pin source branch and capture exact minimum import set.
- Primary touch points:
- `docs/plans/feature-test-harness.md`
- `tests/HARNESS_README.md` (planned)
- Steps:
- Inspect source branch files and map minimum required set (`__init__.py`, `harness.py`, `edmc/**`).
- Record source branch and commit SHA.
- Acceptance criteria:
- Minimum import set and source provenance are documented.
- Verification to run:
- `git ls-remote https://github.com/aussig/BGS-Tally.git 3e5fe957d299a43e28a64df35145f569c5ad0a7f`

#### Stage 1.2 Detailed Plan
- Objective:
- Define target repo structure and boundaries for vendored vs local modules.
- Steps:
- Keep a flat `/tests` layout with harness assets at:
- `tests/harness.py`
- `tests/edmc/**`
- `tests/config/**`
- `tests/overlay_adapter.py` (planned)
- Reserve `tests/config/` for project-specific fixtures.
- Record no-production-import rule for harness modules.
- Acceptance criteria:
- Directory and ownership contract documented and unambiguous.
- Verification to run:
- `rg --files tests | rg '^tests/(harness.py|edmc/|config/)'`

#### Stage 1.3 Detailed Plan
- Objective:
- Specify adapter API that bridges harness overlay expectations to this repo’s overlay test assertions.
- Steps:
- Define supported adapter calls: `connect`, `send_message`, `send_shape`, optional `send_raw`.
- Define capture sink schema for assertions (`messages`, `shapes`, `raw_payloads`).
- Decide fallback behavior when modern overlay APIs are unavailable in a test context.
- Acceptance criteria:
- Adapter contract documented, including failure behavior and assertion surface.
- Verification to run:
- `python -m pytest -k harness --collect-only`

#### Phase 1 Execution Order
- Implement in strict order: `1.1` -> `1.2` -> `1.3`.

#### Phase 1 Exit Criteria
- Requirements and contracts are locked in writing.
- Upstream source commit is pinned and recorded in decisions/provenance notes.
- Open questions are reduced to decisions needed before coding starts.

### Phase 2: Vendor Baseline Harness Files
- Copy the minimum harness files from upstream into `tests/`.
- Keep content intact unless required for local import path correction.
- Risks: accidental behavioral drift while copying.
- Mitigations: copy first, patch second; keep local modifications in separate files when possible.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add upstream `tests/__init__.py` and `tests/harness.py` as pinned snapshot files | Completed |
| 2.2 | Add full upstream `tests/edmc/**` (including `tests/edmc/plugins/**`) from pinned snapshot | Completed |
| 2.3 | Create `tests/config/` with placeholder README/template files | Completed |

#### Stage 2.1 Detailed Plan
- Objective:
- Vendor root harness modules exactly as upstream snapshot files.
- Steps:
- Copy upstream `tests/__init__.py` and `tests/harness.py` from commit `3e5fe957d299a43e28a64df35145f569c5ad0a7f` into repo.
- Do not edit vendored content.
- Verify imports resolve under local pytest pathing.
- Acceptance criteria:
- `from harness import TestHarness` works.
- Vendored files match pinned upstream content and remain read-only.
- Verification to run:
- `python -m pytest -k harness --collect-only`

#### Stage 2.2 Detailed Plan
- Objective:
- Vendor EDMC mock modules intact.
- Steps:
- Copy full upstream `tests/edmc/**` (including `tests/edmc/plugins/**`) from commit `3e5fe957d299a43e28a64df35145f569c5ad0a7f` into `tests/edmc/**`.
- Confirm module names match harness expectations.
- Acceptance criteria:
- Harness bootstrap can import mocked `config`, `monitor`, and overlay shims.
- Vendored `tests/edmc/**` remains immutable after import.
- Verification to run:
- `python -m pytest -k harness --maxfail=1`

#### Stage 2.3 Detailed Plan
- Objective:
- Stand up local config fixture directory for integration tests.
- Steps:
- Create `tests/config/`.
- Add placeholder fixture files and README notes.
- Acceptance criteria:
- Harness can load config/event files from local config folder.
- Verification to run:
- `python -m pytest -k harness_config --maxfail=1`

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.

#### Phase 2 Exit Criteria
- Minimum vendored harness footprint exists and imports cleanly.
- Config directory exists for future test fixture growth.

### Phase 3: Overlay Adapter and Bootstrap Integration
- Add a project-owned adapter to avoid invasive edits in vendored harness code.
- Keep adapter/wrapper code local to `tests/`.
- Risks: adapter semantics mismatch legacy expectations.
- Mitigations: explicit contract tests for adapter I/O and captured state.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add overlay adapter module with legacy-compatible methods | Completed |
| 3.2 | Wire adapter via bootstrap/module injection without editing vendored code where possible | Completed |
| 3.3 | Add assertion helpers for captured overlay payloads | Completed |

#### Stage 3.1 Detailed Plan
- Objective:
- Implement adapter methods expected by harness-driven tests.
- Primary touch points:
- `tests/overlay_adapter.py`
- Steps:
- Implement message/shape capture with stable in-memory structures.
- Prefer forwarding through real overlay integration seams (for example `overlay_plugin.overlay_api`) when present; use in-memory fallback capture only when required.
- Expose clear/reset helpers for test isolation.
- Acceptance criteria:
- Adapter supports harness call patterns without code changes to tests.
- Verification to run:
- `python -m pytest tests/test_harness_integration.py -k adapter`

#### Stage 3.2 Detailed Plan
- Objective:
- Install adapter through wrapper/bootstrap and keep vendored files mostly untouched.
- Steps:
- Inject adapter into expected module path (`edmcoverlay` / `EDMCOverlay.edmcoverlay`) at test bootstrap time.
- Ensure fallback mock behavior remains available.
- Acceptance criteria:
- Harness tests use adapter successfully and still boot plugin hooks.
- Verification to run:
- `python -m pytest tests/test_harness_integration.py -k bootstrap`

#### Stage 3.3 Detailed Plan
- Objective:
- Provide reusable assertion helpers so tests assert behavior, not internals.
- Steps:
- Add helper functions to inspect last sent payloads and grouped outputs.
- Add reset hook per test.
- Acceptance criteria:
- New harness tests read overlay output through helper APIs only.
- Verification to run:
- `python -m pytest tests/test_harness_integration.py -k overlay_output`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3`.

#### Phase 3 Exit Criteria
- Adapter is in place and harness can validate overlay outputs for this project.
- Vendored harness remains minimally modified.

### Phase 4: Harness Smoke Tests and Validation
- Add initial integration tests proving harness startup + event replay works for this plugin.
- Keep first wave small and deterministic.
- Risks: flaky timing with worker threads.
- Mitigations: deterministic fixture events, bounded waits, and explicit synchronization points.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Add chat-command journal replay test using shared `tests/config/journal_events.json` | Completed |
| 4.2 | Add harness bootstrap smoke test (`plugin_start3`, `plugin_app`, handler registration) | Completed |
| 4.3 | Wire harness tests into default `make check` (optional marker for local filtering) | Completed |

#### Stage 4.1 Detailed Plan
- Objective:
- Validate chat-command event replay path and adapter-captured overlay output.
- Steps:
- Add and maintain shared `tests/config/journal_events.json` with `SendText` sequences that exercise the required chat-command smoke set.
- Replay those sequences through the harness and assert expected runtime effects (launch callback, group toggles/set, profile cycle/status messaging, status overlay call path).
- Acceptance criteria:
- Harness chat-command test passes reliably and proves command dispatch from journal replay, not direct helper calls.
- For command paths with runtime callbacks, assertions verify callback invocation.
- For paths without callbacks, assertions verify command handled behavior.
- Verification to run:
- `python -m pytest tests/test_harness_chat_commands.py -q`

#### Stage 4.2 Detailed Plan
- Objective:
- Prove harness can load and initialize plugin entrypoints.
- Steps:
- Build test fixture that instantiates harness and starts plugin hooks.
- Assert startup completes and test context is populated.
- Acceptance criteria:
- Smoke test passes on local dev environment.
- Verification to run:
- `python -m pytest tests/test_harness_integration.py -k startup`

#### Stage 4.3 Detailed Plan
- Objective:
- Ensure harness tests are part of the default project gate while remaining easy to filter locally.
- Steps:
- Wire harness tests into default `make check` execution.
- Optionally keep/confirm a pytest marker (`harness`) for local focused runs.
- Update docs/commands to reflect default-gate status.
- Acceptance criteria:
- Harness tests run in default `make check`.
- Harness tests can still be run independently with focused commands (and marker if present).
- Verification to run:
- `make check`

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- Baseline harness integration tests exist and pass.
- Execution model (local + CI) is documented.

### Phase 5: Documentation, Sync Workflow, and Follow-ups
- Document how harness code was sourced and how to refresh it.
- Capture next iteration items discovered during implementation.
- Risks: undocumented sync steps leading to divergence.
- Mitigations: concise runbook and provenance note in-tree.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Add `tests/HARNESS_README.md` with source provenance and usage | Completed |
| 5.2 | Add sync checklist/script for upstream refreshes | Completed |
| 5.3 | Record follow-up backlog items from implementation gaps | Completed |

#### Stage 5.1 Detailed Plan
- Objective:
- Document local harness purpose, limits, and entrypoints.
- Steps:
- Add readme with source branch, commit SHA, local modifications, and test commands.
- Acceptance criteria:
- Any contributor can run harness tests from docs alone.
- Verification to run:
- `rg -n \"feature/Issue-454/test-harness|commit\" tests/HARNESS_README.md`

#### Stage 5.2 Detailed Plan
- Objective:
- Make future harness refreshes repeatable.
- Steps:
- Add sync steps or helper script under `scripts/`.
- Include conflict policy (copy first, reapply local patches).
- Acceptance criteria:
- Sync steps are executable and documented.
- Verification to run:
- `bash -n scripts/sync_test_harness_from_bgstally.sh`

#### Stage 5.3 Detailed Plan
- Objective:
- Capture deferred improvements after MVP harness lands.
- Steps:
- Add backlog section in plan or docs with scoped follow-ups.
- Acceptance criteria:
- Follow-ups are explicit and prioritized.
- Verification to run:
- `rg -n \"Follow-up|Backlog\" docs/plans/feature-test-harness.md tests/HARNESS_README.md`

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
- Harness runbook and sync strategy are committed.
- Next-iteration work is captured with clear ownership.

## Tests To Run Per Milestone
- Env setup (once): `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- Fast targeted harness checks: `source .venv/bin/activate && python -m pytest tests/test_harness_integration.py -q`
- Chat-command harness checks: `source .venv/bin/activate && python -m pytest tests/test_harness_chat_commands.py -q`
- Full project gate: `source .venv/bin/activate && make check`

## Implementation Results
- Phase 1:
- Locked source and contracts in-plan, including pinned upstream commit `3e5fe957d299a43e28a64df35145f569c5ad0a7f`.
- Added explicit per-phase execution plans and verification commands for this run.
- Result: requirements/ownership/adapter contract finalized.
- Verification:
- `git ls-remote https://github.com/aussig/BGS-Tally.git 3e5fe957d299a43e28a64df35145f569c5ad0a7f`

- Phase 2:
- Vendored pinned snapshot files:
- `tests/harness.py`
- `tests/edmc/**` (including plugins)
- `tests/__init__.py` (vendored baseline, then adapted to lazy import for local pytest stability)
- Created `tests/config/README.md`.
- Verified vendored snapshot parity for immutable files.
- Result: baseline harness snapshot is present under `/tests` and immutable upstream files are in-tree.
- Verification:
- `diff -qr /tmp/BGS-Tally-harness/tests/edmc tests/edmc`
- `diff -q /tmp/BGS-Tally-harness/tests/harness.py tests/harness.py`
- `overlay_client/.venv/bin/python -m pytest -k harness --collect-only`

- Phase 3:
- Added local bootstrap/adapter integration without modifying vendored immutable files:
- `harness.py` (stable entrypoint, `from harness import TestHarness`)
- `tests/harness_bootstrap.py` (safe vendored harness import, module restoration, headless Tk shims, semantic_version dependency validation, harness defaults)
- `tests/overlay_adapter.py` (capture adapter + assertion helpers)
- Result: harness import/usage is isolated and safe for the broader test suite.
- Verification:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_integration.py -k adapter -q`
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_integration.py -k bootstrap -q`

- Phase 4:
- Added shared replay fixture:
- `tests/config/journal_events.json`
- Added harness tests:
- `tests/test_harness_integration.py`
- `tests/test_harness_chat_commands.py`
- Implemented callback-vs-handled assertion policy in chat replay test.
- Added `harness` pytest marker and kept tests in default gate.
- Result: harness-backed chat commands and startup/adapter smoke paths are covered and run in `make check`.
- Verification:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_chat_commands.py -q`
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_integration.py -q`
- `make check`

- Phase 5:
- Added provenance/runbook:
- `tests/HARNESS_README.md`
- Added sync helper:
- `scripts/sync_test_harness_from_bgstally.sh`
- Updated testing docs with harness commands/marker:
- `docs/testing.md`
- Added Ruff exclusions for immutable vendored snapshot files:
- `tests/harness.py`
- `tests/edmc/**`
- Result: refresh workflow and contributor-facing harness guidance are documented.
- Verification:
- `bash -n scripts/sync_test_harness_from_bgstally.sh`
- `rg -n "feature/Issue-454/test-harness|3e5fe957d299a43e28a64df35145f569c5ad0a7f|Follow-up|Backlog" docs/plans/feature-test-harness.md tests/HARNESS_README.md`

- Follow-up Backlog:
- Evaluate a less mocked runtime-start strategy for harness tests if sandbox/network constraints are relaxed.
