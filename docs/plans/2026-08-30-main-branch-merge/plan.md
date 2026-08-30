# Main Branch Integration Plan

## Purpose

Merge the current local `main` branch into `backend-refactor-implementation`
without weakening the `fix219` backend boundary or losing the circle and shape
work introduced on `main`. This is an integration plan only; it authorizes no
merge, conflict resolution, commit, or push by itself.

## Assessment Snapshot

- Target branch: `backend-refactor-implementation` at assessment time.
- Source branch: local `main` at `d19d9f7`.
- Merge base: `f93d7b7`.
- Divergence at assessment time: target is 158 commits ahead and 11 commits
  behind `main`.
- Predicted manual conflicts include the legacy shape pipeline, shape tests and
  gallery tooling, `version.py`, selected rendering/API documentation, and
  four refactoring-document deletion-versus-edit paths.

These references are intentionally treated as stale after any new commit or
fetch. Re-run Phase 1 immediately before starting the merge.

## Invariants

1. Preserve the `fix219` boundary: generic follow/runtime code must not import
   compositor-specific presentation helpers or dispatch on raw backend/helper
   enums.
2. Preserve `main`'s public circle and optional shape-thickness contract:
   normalization, processing, deduplication, transformed bounds, Qt painting,
   gallery output, and regression coverage must agree.
3. Do not resolve core paths with a blanket `--ours` or `--theirs` choice.
4. Treat `overlay_groupings.json` and `overlay_settings.json` as out-of-scope
   configuration. Per user direction on 2026-08-30, `main` is the authorized
   source of truth for either path if the merge needs a resolution. At the
   assessment snapshot, only `overlay_groupings.json` differs on `main` and
   has a local modification; resolve that path from `main` rather than
   preserving, inspecting, or validating its local content.
5. Do not create a merge commit or push until the user authorizes that final
   action after validation.

## Phase Status

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Freeze merge inputs and preconditions | Completed — topology refreshed and backup ref verified. |
| 2 | Create a reversible, non-committing merge state | Completed |
| 3 | Resolve the code and contract conflicts | Completed — all four integration stages are recorded; the focused boundary pytest is environment-blocked because the checked-in `.venv` lacks `pytest`, so Task 5 must rerun it after development dependencies are restored. |
| 4 | Resolve tests, documentation, and release metadata | Completed — documentation reconciled and `version.py` resolved to temporary `1.0.0` integration assumption. |
| 5 | Validate, review, and hand off | Completed — the passing targeted and boundary evidence, failed/blocked project gates, integrity review, configuration disposition, and final handoff are recorded. The merge remains intentionally uncommitted and awaits the user's explicit decision. |

## Phase 1: Freeze merge inputs and preconditions

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Confirm target branch, source branch, merge base, and divergence | Completed — 2026-08-30 refresh: target `ec66ba6ec110907d8c8cc1f2c5d3e9e1d0297e41`; source `d19d9f77e368e5f034e86bf7a3812ab03b0bc09b`; merge base `f93d7b7c131e6f7e647cbb089617d55ab79f91b8`; divergence `11\t158`. |
| 1.2 | Record the predicted conflict paths and auto-merged runtime paths requiring review | Completed — source-side scope matched the recorded legacy payload, renderer/geometry, tests/gallery, version, and documentation/refactoring categories; no material drift found. |
| 1.3 | Record the user-managed configuration exclusion and `main`-wins resolution decision | Completed |
| 1.4 | Create and verify a local backup ref at the exact target tip | Completed — `refs/backup/backend-refactor-implementation-pre-main-merge-20260830-ec66ba6e` resolves to `ec66ba6ec110907d8c8cc1f2c5d3e9e1d0297e41`. The initial sandbox-only write failure was resolved through the authorized local Git operation. |
| 1.5 | Create the in-chat orchestration prompt and execution dashboard | Completed |

### Required pre-merge checks

Run read-only checks first:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse main
git merge-base main HEAD
git rev-list --left-right --count main...HEAD
git diff --name-only "$(git merge-base main HEAD)..main"
```

`overlay_groupings.json` and `overlay_settings.json` are excluded from
behavioral review. If either needs resolution, take the `main` version as
explicitly authorized by the user. The current local modification to
`overlay_groupings.json` must not be preserved or reviewed as part of this
merge.

## Phase 2: Create a reversible, non-committing merge state

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Create a backup ref that resolves to the verified target SHA | Completed — reused Task 1's verified `refs/backup/backend-refactor-implementation-pre-main-merge-20260830-ec66ba6e`. |
| 2.2 | Run `git merge --no-commit --no-ff main` | Completed — merge started without a commit; `version.py` is the sole unmerged path. |
| 2.3 | Record every unmerged path and the complete staged merge scope | Completed — Task 2 captured `status`, unmerged, cached, and unstaged names before any core-path resolution. |
| 2.4 | Resolve either excluded configuration path from `main` if Git requires it | Completed — `overlay_groupings.json` was restored from `main` as authorized; `overlay_settings.json` was not affected. |

The merge remains uncommitted through Phases 3–5. If the scope differs
materially from the assessment, pause and reassess rather than resolving
unexpected paths opportunistically.

## Phase 3: Resolve the code and contract conflicts

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Resolve `EDMCOverlay/edmcoverlay.py` and `overlay_client/legacy_processor.py` | Completed — retained the target's legacy-processor ownership and merged `main`'s optional circle/rectangle thickness contract. Focused pytest was attempted but the checked-in `.venv` has no `pytest`; syntax and scoped whitespace checks passed. |
| 3.2 | Resolve `overlay_client/render_surface.py` and review auto-merged paint/transform modules | Completed — retained the target renderer/backend structure and the merged circle path. Semantic review confirmed explicit circle/rectangle thickness is pixel-based, omitted thickness uses the existing default, explicit rectangles retain miter joins, circle opacity/cycle anchors remain command-owned, and transformed circle bounds use all four square corners. Focused pytest remains unavailable because `.venv` lacks `pytest`; scoped compile and whitespace checks passed. |
| 3.3 | Resolve shape-related test conflicts as a union of both coverage sets | Completed — retained the staged test union: explicit and omitted pixel-width strokes, rectangle miter joins, circle geometry, and cycle metadata are covered in the renderer module; paint-command and payload-bounds modules own the distinct opacity and transformed-circle-bounds assertions. Focused pytest was attempted once but `.venv` lacks `pytest`; compile and scoped whitespace checks passed. |
| 3.4 | Re-run the backend-architecture boundary test after integration | Completed — `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_architecture_boundary.py` ran once and exited 1 before collection: `.venv/bin/python: No module named pytest`. Read-only source inspection is non-test evidence only; no implementation, test, merge-index, or version change was made. |

### Stage 3.1: Legacy payload contract

Retain the target branch's refactored ownership and add `main`'s contract for
circle payloads and optional rectangle/circle thickness. Verify that legacy
normalization, validation, item replacement, and dedupe snapshots all agree
on shape geometry and optional stroke semantics.

### Stage 3.2: Rendering and geometry contract

Retain the target renderer structure while integrating circle command building,
stroke-width policy, miter joins for explicit rectangle thickness, opacity,
cycle anchors, and transformed group bounds. Review automatically merged
`overlay_client/paint_commands.py` and `overlay_client/payload_transform.py`
semantically; their lack of text conflicts is not behavioral evidence.

### Stage 3.3: Test and gallery contract

Combine, rather than select between, the independently added shape tests and
gallery utility. The resulting gallery must retain both the public payload
builder expected by `main` and any labeled developer-inspection behavior added
on the target branch.

## Phase 4: Resolve tests, documentation, and release metadata

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Reconcile test modules and utility behavior with the final shape contract | Completed — retained the active merge's intentional union: public circle and omitted-thickness coverage, default-width rectangle/circle examples, and target-branch label messages/assertions. Focused pytest was attempted once but is environment-blocked because `.venv` lacks `pytest`; scoped compile and whitespace checks passed. |
| 4.2 | Reconcile API/rendering documentation and refactoring-document removals | Completed — corrected stale rectangle-only, required-thickness, and old-version compatibility wording across the bounded API/discovery pages; the rendering pipeline already matched the accepted circle/pixel-width contract. Local history confirms all four refactoring paths were intentionally archived, so their active paths remain deleted. Documentation-only searches, scoped whitespace, and marker checks passed. |
| 4.3 | Resolve the version conflict as a pre-release integration assumption | Completed — removed only the conflict markers from `version.py`, retained the target-side `1.0.0`, and staged that one resolved file. The value is the working default for this uncommitted integration only; it is not a release decision, announcement, tag, or compatibility guarantee. Syntax, staged-whitespace, marker, and unmerged-path checks passed. |

**Phase 4 status: Completed.** Task 4.3 recorded the target-side `1.0.0` only
as a pre-release integration assumption. Release-train, shipping, compatibility,
tagging, and package decisions remain explicitly outside this merge task and
require user authorization after Task 5 validation.

For the `docs/refactoring/` deletion-versus-edit conflicts, determine whether
`main` intentionally archived/replaced the documents. Preserve substantive
target-branch guidance in its intended replacement location rather than
reviving obsolete files by default.

### Stage 4.2 decision ledger

The public API wording was compared manually with the accepted Task 3.1--3.3
and 4.1 handoffs, the prior circle-documentation task record, and the
unified-pixel-width plan. The changed pages retain positional rectangles;
describe first-class circles rather than vector markers; require a positive
circle radius; allow either shape to omit thickness; and state that an explicit
valid thickness is an unscaled logical Qt-pixel width. The raw-client
normalization/invalid-geometry boundary remains as previously documented.

| Path | Decision and current owner |
| --- | --- |
| `docs/wiki/send_shape-API.md` | Updated the rectangle-only introduction and invalid keyword-circle example; retained positional rectangles and the circle field contract without using the obsolete `0.9.2` statement. |
| `docs/wiki/send_raw-API.md` | Retained its contract-accurate raw normalization and invalid-geometry wording; made extension/compatibility wording version-neutral. |
| `docs/wiki/Getting-Started.md` | Corrected the implication that `thickness` is required and retained the circle-versus-vector-marker distinction. |
| `docs/wiki/Concepts.md` | Kept the supported primitive list and made the circle-versus-vector-marker distinction explicit without a release claim. |
| `docs/wiki/Developer-FAQs.md` | Corrected the stale "No" rectangle-only answer and removed the old version assertion while preserving generic legacy-overlay compatibility guidance. |
| `docs/wiki/APIs.md` | Corrected the legacy message/rectangle-only summary to name the circle and explicit-thickness extensions. |
| `docs/rendering-pipeline.md` | Reviewed, unchanged: it already describes the derived circle square, shared mapping, bounded `QPainter.drawEllipse`, intentional non-uniform ellipse result, and shared explicit pixel-width rule without backend claims. |

Local history freezes the four refactoring candidates to
`client_refactor.md`, `compositor_aware_install.md`, `load_refactory.md`, and
`refactor-plan.md` only: `git diff --name-status
f93d7b7..main -- docs/refactoring/...` reports their deletion, while
`f2c68ba` renamed each target-side document to `docs/archive/refactoring/`.
No other refactoring path has this delete-versus-archival history, so none was
reviewed or edited.

| Former active path | Archived/current guidance owner | Decision |
| --- | --- | --- |
| `docs/refactoring/client_refactor.md` | `docs/archive/refactoring/client_refactor.md`; current backend decisions are owned by the three active `fix219_` architecture documents. | Leave deleted; the archive's historical header already directs readers to the current owner. |
| `docs/refactoring/compositor_aware_install.md` | `docs/archive/refactoring/compositor_aware_install.md`; deployment/install guidance is bounded by the active fix219 research and follow-up plans. | Leave deleted; no active runtime backend-selection guidance belongs in the former plan. |
| `docs/refactoring/load_refactory.md` | `docs/archive/refactoring/load_refactory.md`; current `load.py` control-plane guidance is owned by the active fix219 research/follow-up plans. | Leave deleted; the archive preserves EDMC-hook history without duplicating current ownership. |
| `docs/refactoring/refactor-plan.md` | `docs/archive/refactoring/refactor-plan.md`; current architecture work is owned by the active `fix219_` documents. | Leave deleted; its historical status and completed extraction plan would be obsolete as an active plan. |

## Phase 5: Validate, review, and hand off

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Run targeted mixed unit and harness tests for the merged shape path | Completed — remediation context `/root/task51_remediate` re-ran the prescribed Qt-enabled mixed suite once after the authorized development-dependency restore: 118 passed in 0.74s. The earlier no-`pytest` attempt remains historical environment-block evidence, not a product failure. |
| 5.2 | Run backend-boundary tests and project gates | Completed — fresh context `/root/task52_execute`: the focused boundary suite passed (6 passed in 0.04s) and `git diff --check` passed. The EDMC Python gate failed because the root `.venv` is Python 3.12.3 64-bit rather than the required 3.13-series 32-bit runtime; no override was used. `make check` failed on Ruff E402 in `scripts/monitor_to_canonical.py:22`; `make test` ran 1,716 tests with 1,690 passed, 21 skipped, and five socket-bind setup errors in `tests/test_harness_pressure_ab_snapshot.py`. |
| 5.3 | Inspect merge integrity, configuration scope, and unresolved markers | Completed — fresh read-only review found zero unmerged paths/index entries, zero true conflict markers outside `.git`/`.venv`, and no whitespace errors. `overlay_groupings.json`'s active blob matches `main` (and, coincidentally, `HEAD`); unaffected `overlay_settings.json` remains at `HEAD`. Focused diff review preserves the fix219 boundary and circle/optional-pixel-thickness contracts. |
| 5.4 | Present final results and request explicit user authorization before any commit or push | Completed — final handoff created after reconciliation with the active merge. It records that release-quality evidence is incomplete and requests one explicit user decision; no commit or push is authorized or performed. |

### Required test plan

Use the root development environment. The shape rendering path needs both unit
coverage and the EDMC lifecycle harness coverage:

```bash
source .venv/bin/activate
PYQT_TESTS=1 python -m pytest \
  tests/test_edmcoverlay_shapes.py \
  tests/test_legacy_processor.py \
  tests/test_harness_legacy_tcp_ingestion.py \
  tests/test_shape_gallery.py \
  overlay_client/tests/test_paint_commands.py \
  overlay_client/tests/test_payload_bounds.py \
  overlay_client/tests/test_render_surface_mixin.py \
  overlay_client/tests/test_backend_architecture_boundary.py
python scripts/check_edmc_python.py
make check
make test
git diff --check
```

### Task 5.1 execution record

Fresh remediation context `/root/task51_remediate` reconciled the active merge
before the prescribed re-attempt: `HEAD` remained
`ec66ba6ec110907d8c8cc1f2c5d3e9e1d0297e41`; `main` and `MERGE_HEAD` remained
`d19d9f77e368e5f034e86bf7a3812ab03b0bc09b`; and `git diff --name-only
--diff-filter=U` exited 0 with no output. Following the separately authorized
development-dependency restore, the prescribed Qt-enabled mixed unit/harness
command ran once in the root `.venv` and passed: **118 passed in 0.74s**.
No dependency installation, override, retry, interpreter/scope change,
source/test/configuration/version/index edit, merge continuation, commit, or
remote operation occurred in this remediation context. The previous Task 5.1
attempt remains recorded as an environment block (`No module named pytest`),
not as a product-test failure.

No source, test, configuration, version, merge-index, commit, or remote state
changed. The Task 4.3 `1.0.0` value remains a pre-release integration
assumption only. Phase 5 remains in progress; Task 5.2 owns the compatibility
and project gates.

### Task 5.2 execution record

Fresh context `/root/task52_execute` first confirmed the active uncommitted
merge still has `HEAD` `ec66ba6ec110907d8c8cc1f2c5d3e9e1d0297e41`,
`main`/`MERGE_HEAD` `d19d9f77e368e5f034e86bf7a3812ab03b0bc09b`, and no
unmerged paths. It then ran each prescribed gate once, in order, from the root
`.venv`, with no Python-compatibility override:

| Command | Exit status | Result |
| --- | --- | --- |
| `source .venv/bin/activate && python -m pytest overlay_client/tests/test_backend_architecture_boundary.py` | 0 | 6 passed in 0.04s. |
| `source .venv/bin/activate && python scripts/check_edmc_python.py` | 1 | Required compatibility gate failed: Python 3.12.3 64-bit does not match the tested EDMC runtime `3.13.9+` in the 3.13 series, 32-bit. |
| `source .venv/bin/activate && make check` | 2 | Ruff failed: `scripts/monitor_to_canonical.py:22:1: E402 Module level import not at top of file`. |
| `source .venv/bin/activate && make test` | 2 | 1,716 collected; 1,690 passed, 21 skipped, and 5 errors in 16.00s. Every error is the `socket_runtime_for_pressure_snapshot` fixture assertion that `SocketBroadcaster(... port=0).start()` is true, after `Cannot assign requested address out of [('127.0.0.1', 0)]`, affecting the five `tests/test_harness_pressure_ab_snapshot.py` real-socket cases. |
| `git diff --check` | 0 | No output; no whitespace errors. |

No retry, dependency installation, override (including
`ALLOW_EDMC_PYTHON_MISMATCH`), source/test/configuration/version/merge-index
edit, merge continuation, commit, or remote operation occurred. The focused
backend boundary is now validated, but release-quality compatibility is still
unproven in the required EDMC runtime; the lint failure and the full-suite
socket-fixture errors also leave project-gate evidence incomplete. The latter
may be environment-related, but has not been diagnosed in this validation-only
task. The `1.0.0` value remains a pre-release integration assumption only.
Phase 5 remains in progress; Task 5.3 owns final merge-integrity review.

### Task 5.3 execution record

Fresh context `/root/task53_execute` performed a read-only final integrity
review. `HEAD` remains `ec66ba6ec110907d8c8cc1f2c5d3e9e1d0297e41` and
`main`/`MERGE_HEAD` remain `d19d9f77e368e5f034e86bf7a3812ab03b0bc09b`.
`git diff --name-only --diff-filter=U`, `git ls-files -u`, and `git diff
--check` all returned cleanly with no output. The conflict-marker scan excluded
`.git`, `.venv`, and `__pycache__`, used exact conflict-marker forms to avoid
Markdown/test-output separators, and found no matches.

Configuration content was not inspected. Git comparisons show only
`overlay_groupings.json` changed on `main` since the merge base; its active
index blob equals `main` (`08661291799ceca41f19cb1882433322c2462a1c`) and also
equals `HEAD`, so the authorized main-wins outcome is intact. The unaffected
`overlay_settings.json` is unchanged from `HEAD` in both index and worktree.

The staged resolved diff was reviewed against the invariants: generic
follow/runtime and X11 surfaces contain none of the prohibited GNOME helper
imports/protocols or raw presentation dispatch; the only GNOME raw enums in
`consumers.py` remain in the permitted bundle factory before generic dispatch.
Circle payloads now omit an unset thickness, retain valid explicit
pixel-widths, reject invalid explicit widths/radii, retain default rendering
when omitted, preserve explicit-rectangle miter joins, draw circles through
the bounded opacity/cycle-aware ellipse command, and accumulate transformed
bounds from all four derived-square corners. Existing staged regression tests
cover those contracts.

No source, test, configuration, version, merge-index, commit, remote, reset,
abort, or merge-continuation action occurred. This creates no new blocker, but
the Task 5.2 EDMC-runtime parity, Ruff E402, and real-socket full-suite risks
remain open.

### Final documentation and handoff record

Task 6 reconciled the dashboard and plan with current Git state without
changing source, tests, configuration, the merge index, or merge lifecycle.
The merge is still active and resolved: `HEAD` is
`ec66ba6ec110907d8c8cc1f2c5d3e9e1d0297e41`, `main` and `MERGE_HEAD` are
`d19d9f77e368e5f034e86bf7a3812ab03b0bc09b`, and unmerged-path/index checks
remain empty. The index contains the 71-path resolved merge (2,974 insertions,
108 deletions); only this plan and the execution dashboard have additional
unstaged documentation updates. The durable resumption record is
`/tmp/handoff-20260830-103656.md`.

**Phase 5 status: Completed.** The targeted unit/harness and focused boundary
tests passed, integrity checks passed, and all required project-gate outcomes
are recorded. This does **not** mean the integration is release-ready: the
EDMC Python gate, Ruff gate, and real-socket full-suite cases remain open.
The exact next action is a user decision: authorize a bounded
remediation/revalidation task with no commit or push, or explicitly authorize
a merge commit despite those open gates (and separately authorize any push).

Record each command's exact outcome. If the EDMC Python compatibility command
cannot run in the required parity environment, report the failure or skip and
its remaining release risk; do not silently use an override for release
validation.

### Completion criteria

The merge is ready for user review only when:

- all conflicts are resolved and `git diff --name-only --diff-filter=U` is
  empty;
- no conflict markers or whitespace errors remain;
- unrelated local configuration has its user-approved disposition and is not
  accidentally staged;
- the targeted tests, boundary test, and project gates have recorded results;
- the version and documentation choices are explicit; and
- the resolved diff has been reviewed for both the backend boundary and
  circle/thickness behavior.

Only after those criteria are met should the user be asked whether to create a
merge commit and whether it may be pushed.
