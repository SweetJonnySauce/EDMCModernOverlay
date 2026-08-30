# In-Chat Autonomous Merge Orchestration Prompt

## Goal

Autonomously implement the approved integration plan at
`docs/plans/2026-08-30-main-branch-merge/plan.md`: merge the current local
`main` branch into `backend-refactor-implementation`, resolve the integration
correctly, validate it, and leave the repository in a reviewable **uncommitted**
state. This prompt is for an agent operating in this chat environment, not for
Codex CLI.

## Scope and authority

Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`

Target branch: `backend-refactor-implementation`

Source branch: local `main`

Governing artifacts:

- `AGENTS.md`
- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`

Standing authority covers ordinary, in-scope local implementation work:
read-only Git inspection, a local backup ref, a non-committing merge, scoped
conflict resolution, source/test/documentation edits required by the plan, and
test/lint/type-check commands. Do not fetch, push, commit, amend, reset, abort
the merge, or use destructive Git operations unless the user explicitly asks.

`overlay_groupings.json` and `overlay_settings.json` are out of behavioral
review. The user has authorized `main` as the source of truth if either path
needs a merge resolution. At the assessment snapshot, only
`overlay_groupings.json` differs on `main` and has a local modification.

## Non-negotiable constraints

1. Never create a commit, including a documentation-only commit. Never push.
2. Preserve the `fix219` backend boundary: generic follow/runtime code must not
   import compositor-specific presentation helpers or dispatch by raw
   backend/helper enums.
3. Preserve `main`'s circle and optional shape-thickness behavior through
   normalization, processing, dedupe, bounds, painting, gallery output, and
   regression tests.
4. Do not use blanket `--ours`/`--theirs` resolutions for core code or tests.
5. Do not start a live overlay, send live payloads, access external services,
   or make a release/version decision outside the target-branch default.
6. If the source or target tip has moved, regenerate the merge assessment
   before resolving conflicts.
7. If a failure needs a product, release, or behavior decision, stop with
   evidence and ask the user. Do not conceal it by weakening a test or using an
   unexplained override.

## Status-documentation contract

Before starting and after completing every task, update both the phase/stage
tables in `plan.md` and the task row in `execution-status.md`. Record:

`Task ID; fresh context ID; status; files changed; commands and outcomes; decisions; risks; next action.`

Use these exact statuses: `Pending`, `In progress`, `Completed`, `Blocked`, or
`Skipped`. A phase becomes `Completed` only when every stage in that phase is
completed. Never mark a test stage completed before recording its exact command
and result.

## Fresh-context protocol

Do not perform this as one long implementation context.

1. Break the work into the task IDs below. Before each task, write or update a
   self-contained task brief under
   `docs/plans/2026-08-30-main-branch-merge/implementation/tasks/`.
2. Run **each task ID in its own fresh context window**. A fresh context must
   not inherit implementation dialogue from a prior task; it may use only the
   repository state and the documented plan, dashboard, and its own task brief.
3. Each fresh context must first read `AGENTS.md`, this prompt, `plan.md`, its
   task brief, and only the source/tests directly relevant to its task.
4. Run write-capable tasks sequentially. Never overlap tasks that can modify
   the worktree or merge index.
5. At task completion, write the required handoff/status record before opening
   the next context. A handoff must identify the exact next task, not merely a
   broad phase.
6. One implementation attempt and at most two fresh-context remediation tasks
   are allowed per task. Do not rerun an unchanged failing command more than
   once. After the limit, mark the task `Blocked` and return evidence to the
   user.

## Task breakdown and execution order

### Task 1 — Refresh topology and freeze the baseline

In one fresh context, re-run the Phase 1 checks from `plan.md`: branch, status,
source and target SHAs, merge base, divergence, `MERGE_HEAD`, and expected
merge scope. If no merge is active, create a verified local backup ref at the
current target SHA. If any unexpected unrelated worktree path exists, stop and
ask the user before changing it.

Expected result: a current topology record and a backup ref; no merge yet.

### Task 2 — Resolve excluded configuration and create the merge state

In one fresh context, use the user-authorized `main` version of
`overlay_groupings.json` so the existing local modification cannot block the
merge. Because `main` modifies that path, first clear the local edit from the
target version, start this exact non-committing merge, then set the merged path
to `main`:

```bash
git restore --source=HEAD --staged --worktree overlay_groupings.json
git merge --no-commit --no-ff main
git restore --source=main --staged --worktree overlay_groupings.json
```

Do not alter `overlay_settings.json` unless Git presents it as an affected path,
in which case use the same `main`-wins policy. Record the complete staged and
unmerged scope before resolving any code conflict.

Expected result: one active, uncommitted merge with configuration paths resolved
from `main` where necessary.

### Task 3 — Integrate legacy payload and renderer behavior

Use one fresh context per subtask:

- **3.1 Payload contract:** resolve `EDMCOverlay/edmcoverlay.py` and
  `overlay_client/legacy_processor.py`, preserving the target structure and
  `main`'s circle/thickness contract.
- **3.2 Renderer contract:** resolve `overlay_client/render_surface.py`; review
  auto-merged `overlay_client/paint_commands.py` and
  `overlay_client/payload_transform.py` for circle geometry, opacity, miter
  joins, cycle anchors, and transformed bounds.
- **3.3 Renderer tests:** resolve
  `overlay_client/tests/test_render_surface_mixin.py` as a coverage union and
  add/update only the tests needed to prove the merged contract.

Each subtask must run the smallest relevant unit tests before handing off. Do
not combine these subtasks into one context window.

### Task 4 — Integrate public tests, gallery, documentation, and version

Use one fresh context per subtask:

- **4.1 Shape test/gallery union:** combine the independently added
  `tests/test_edmcoverlay_shapes.py`, `tests/test_shape_gallery.py`, and
  `utils/shape_gallery.py` behavior without dropping either supported public
  API or developer-facing labels.
- **4.2 Documentation and refactoring moves:** reconcile rendering/API docs and
  the `docs/refactoring/` deletion-versus-edit paths using local history and
  current document ownership. Do not revive obsolete documents by default.
- **4.3 Version resolution:** preserve the target branch's `1.0.0` as the
  integration default, record this as a pre-release assumption, and stop only
  if current repository evidence shows that choice is incompatible. Do not make
  a release decision or a commit.

### Task 5 — Validate the combined branch

Run in fresh contexts, sequentially:

1. Targeted mixed unit/harness validation:

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
   ```

2. Project gates:

   ```bash
   python scripts/check_edmc_python.py
   make check
   make test
   git diff --check
   ```

   If parity validation is unavailable, record the exact failure and remaining
   risk; do not apply an override for release-quality validation without user
   permission.

3. Final integrity review: confirm no unresolved files, conflict markers, or
   unexpected configuration changes remain. Review the final merge diff against
   the invariants rather than relying only on test results.

### Task 6 — Update documentation and hand off

In one final fresh context, reconcile every plan phase/stage and dashboard row
with Git state and recorded validation. Report the active merge state, changed
files, commands/results, configuration disposition, unresolved risks, and the
exact user decision needed next.

Do not commit the merge. If validation passes, the required next decision is:
whether the user wants to inspect the uncommitted result and later authorize a
merge commit.

## Completion criteria

Completion means a reviewable, uncommitted merge state—not a merge commit.
Before reporting completion, confirm:

- `git diff --name-only --diff-filter=U` is empty;
- no conflict markers or whitespace errors remain;
- the two excluded configuration paths follow the documented `main`-wins
  policy if affected;
- all task briefs, plan statuses, and dashboard rows are current;
- targeted tests, boundary tests, and project gates have exact recorded
  outcomes; and
- any remaining blocker is explicit and has been returned to the user.
