# Implementation Orchestration: Circle Feature into Backend Refactor

## Scope and authority

Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`

Target branch: `backend-refactor-implementation`

Source branch: `feature/circle-shape-pyqt-rendering`

Approved plan: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/plan.md`

Governing artifacts:

- `AGENTS.md`
- `docs/plans/2026-08-27-circle-feature-backend-merge/design/detailed-design.md`
- `docs/plans/2026-08-27-circle-feature-backend-merge/research/merge-assessment.md`
- `docs/plans/2026-08-27-circle-feature-backend-merge/idea-honing.md`
- `docs/plans/2026-08-27-circle-feature-backend-merge/progress.md`

Task artifacts: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/tasks/`

Status dashboard: `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/execution-status.md`

This is standing approval for ordinary, in-scope local work only: creating and
updating task artifacts, editing files needed to resolve this merge, updating
the plan/progress/dashboard, non-destructive Git inspection, `git fetch`, local
backup refs, test/build/lint commands, and a local merge commit only after the
manual-visual gate passes. Never push.

Do not use `git reset`, `git checkout --`, broad destructive commands, force
operations, repository reinitialization, version changes, dependency changes,
or work outside this repository. Do not overwrite or delete unrelated work.

Stop and ask the user before:

- starting or sending to a live overlay, or any other external/network write;
- changing `overlay_groupings.json` (the target-branch version is mandatory);
- modifying scope beyond the approved plan;
- accepting an unresolved test failure, a new security concern, or a behavior
  conflict requiring a product decision;
- committing the merge before the user confirms manual visual inspection.

## Non-negotiable integration constraints

1. Work only on `backend-refactor-implementation`; merge only from
   `feature/circle-shape-pyqt-rendering`.
2. Treat the backend refactor as the structural baseline. Never resolve a
   conflict by wholesale selection of the source file.
3. Restore the target `overlay_groupings.json` after the merge begins. It must
   have no staged diff in the merge commit.
4. Resolve the two known textual conflicts:
   `overlay_client/render_surface.py` and
   `overlay_client/tests/test_render_surface_mixin.py`.
5. Review auto-merged runtime paths before staging:
   `overlay_client/legacy_processor.py` and
   `overlay_client/paint_commands.py`.
6. Preserve the circle contract and explicit rectangle stroke-thickness
   contract, including mitered explicit rectangle corners and unchanged
   omitted-thickness rectangle behavior.
7. The shape gallery's logical concentric circles are not a Fill-mode physical
   concentricity test because the intentionally preserved grouping configuration
   can transform each ID independently.

## Start and restart recovery

Before every initial run and restart:

1. Read every governing artifact above completely.
2. Inspect `git status --short`, the current branch, merge state, staged diff,
   source/target branch tips, the plan checklist, progress tracker, dashboard,
   generated task files, and prior task handoffs.
3. Reconcile conflicting status claims using Git state and test output as the
   source of truth. Resume at the first incomplete or unverified stage.
4. If a merge is in progress, do not start another merge. Continue its current
   stage or abort only with user approval.

Maintain the status dashboard and the approved plan/progress documents. Before
and after every plan stage, task breakdown, code-assist task, test/build, and
manual gate, report exactly:

`Step: [n]; Task: [id]; Phase: [planning|implementation|validation|manual]; Action: [completed/running action]; Next: [next action]`

Send a heartbeat with that format at least every 60 seconds while a task or
long-running command is active.

## Context-isolated task protocol

Do not implement this as one long agent context.

For each plan step that changes repository state (Steps 1 through 4):

1. Open one **fresh, dedicated code-task-generator context/window** for that
   plan step only. It must read the approved plan and directly relevant design
   and research documents. It may generate task files only for that one step.
   Do not reuse or resume a prior task-generator context.
2. The main orchestrator reviews the proposed/generated task scope against this
   prompt before implementation. Reject tasks that alter managed grouping
   configuration, broaden scope, or duplicate a completed task.
3. For **each** accepted task, open one **fresh, dedicated code-assist
   context/window** in auto mode. It must have no preceding task-agent dialogue,
   read `AGENTS.md`, this prompt, the approved plan, and its task file, then use
   strict RED → GREEN → REFACTOR where code changes are required.
4. Run writing code-assist agents sequentially. Never overlap code-editing
   contexts. A completed context may not be reused for another task.
5. Each task handoff must contain exactly:
   `Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`
6. Permit one implementation run and at most two fresh-context remediation runs
   per task. Never rerun an unchanged failing command more than once. Stop with
   evidence after the retry limit or 20 minutes without substantive progress.

For Step 5, use the main orchestrator only: manual visual verification is
user-gated and must not be delegated to an implementation context.

## Execution sequence

### Step 0 — Ensure the plan is trackable

First inspect the worktree. If the only uncommitted files are the merge-plan
documentation under `docs/plans/2026-08-27-circle-feature-backend-merge/`,
commit them separately before beginning the merge using the repository's normal
Git conventions. Do not include any other file. If unrelated changes exist,
stop and ask the user how to isolate them.

Record the documentation commit in `progress.md` and the dashboard.

### Step 1 — Freeze the backend baseline

Use a fresh code-task-generator context, then fresh code-assist context(s), to
perform Plan Step 1. Fetch remote refs, confirm a clean target worktree, verify
the source/target tips and merge base, and create a local backup ref. Do not
merge yet.

Update Phase 1 stages only after their Git evidence is recorded. If the source
tip differs materially from the assessed tip, rerun the merge assessment before
continuing.

### Step 2 — Create and inspect the non-committing merge

Use fresh task-generator and code-assist contexts for Plan Step 2. Start:

```bash
git merge --no-commit --no-ff feature/circle-shape-pyqt-rendering
```

Immediately preserve the target configuration:

```bash
git restore --source=HEAD --staged --worktree overlay_groupings.json
```

Confirm it has no staged diff. Do not resolve source/test conflicts until the
full staged/conflicted scope is inspected and recorded.

### Step 3 — Resolve and review the core paths

Use fresh task-generator and then separate fresh code-assist contexts for each
generated resolution task. Keep the backend branch structure and integrate only
the source feature behavior required by the plan.

- In `render_surface.py`, retain the backend refactor structure and integrate
  bounded shape/stroke resolution, circle dispatch, circle command creation,
  and explicit-rectangle `MiterJoin` behavior.
- In `test_render_surface_mixin.py`, retain backend test dependencies and add
  the circle/stroke test dependencies and coverage.
- Review the auto-merged legacy processor and paint-command paths for API,
  opacity, fill, validation, and no-shared-pen-mutation behavior.

Run focused tests after every resolution task. Update plan stage statuses and
record exact commands/results in progress notes.

### Step 4 — Validate the integrated branch

Use fresh task-generator and code-assist contexts for Plan Step 4. Run, record,
and review these gates:

```bash
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
  overlay_client/tests/test_render_surface_mixin.py \
  overlay_client/tests/test_paint_commands.py \
  tests/test_edmcoverlay_shapes.py \
  tests/test_legacy_processor.py \
  tests/test_harness_legacy_tcp_ingestion.py \
  tests/test_shape_gallery.py -q
python3 scripts/check_edmc_python.py
make check
git diff --check
```

Do an independent main-context review of the staged diff, conflict-marker scan,
and `overlay_groupings.json` absence from the staged merge. Tests passing does
not waive that review.

### Step 5 — Manual gate, merge commit, and handoff

Stop and ask the user to perform or explicitly authorize manual overlay
inspection. Tell them to verify circle color/fill/thickness, explicit thick
rectangle square corners, omitted-thickness rectangle legacy behavior, and the
known Fill-mode gallery caveat.

Only after the user confirms manual inspection passed:

1. Recheck `git status`, `git diff --cached --check`, staged paths, and the
   absence of `overlay_groupings.json`.
2. Update every completed plan stage and phase, progress notes, and dashboard.
3. Create the local merge commit using a conventional message that references
   `docs/plans/2026-08-27-circle-feature-backend-merge/implementation/plan.md`.
4. Do not push.

## Completion criteria and final report

Do not claim completion until every plan checkbox and phase/stage status is
reconciled with Git state, validation evidence, and the manual gate.

The final report must include:

- completed steps, task artifacts, and context-isolation record;
- changed files and a compatibility summary;
- exact test/build commands and pass/fail/skip results;
- the documentation and merge commit hashes;
- confirmation that `overlay_groupings.json` was excluded;
- the manual overlay result and known Fill-mode gallery limitation;
- remaining risks or follow-up work.
