# Autonomous Implementation Orchestration: Native GNOME Helper-Unavailable Fallback

## Scope and authority

Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`

Approved design:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/native-gnome-helper-unavailable-fallback-remediation.md`

Approved implementation plan:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-helper-unavailable-fallback-implementation-plan.md`

Supporting remediation record:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-helper-unavailable-fallback-remediation-plan.md`

Governing artifacts:

- `AGENTS.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-plan.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-execution-status.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/iteration-checklist.md`

Create and maintain the remediation dashboard at:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-helper-unavailable-fallback-execution-status.md`

Use these task-artifact roots:

- Code-task breakdowns:
  `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/tasks/native-gnome-helper-unavailable-fallback/`
- Code-assist documentation:
  `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/code-assist/native-gnome-helper-unavailable-fallback/`
- Handoffs:
  `/home/jon/handoffs/`

The user grants standing approval for ordinary, in-scope local work needed to
complete this approved plan: repository-local code, tests, fixtures,
documentation, generated task artifacts, non-destructive commands, local
handoffs, and a conventional local Git commit after the stated validation gate.
Never push.  Do not use `git reset`, `git checkout`, broad cleanup, repository
initialization, or any destructive command.

Never perform live GNOME/DBus/Elite actions, modify the installed Shell
extension, use credentials, make real external API calls, change external
configuration, or write outside the repository and `/home/jon/handoffs/`.
No live matrix is required for this non-rendering helper-loss fallback repair.

Do not expand scope.  In particular, do not modify helper protocol payloads,
Mutter placement, fullscreen Shell-raster eligibility or transition ordering,
X11, xcompat, `load.py`, EDMC settings/preferences, or remove the legacy
`GNOME_SHELL_RASTER` identity.

## Worktree and Git safety

The worktree is known dirty before this run.  Treat every pre-existing tracked
change and every pre-existing untracked path as user-owned unless this
orchestration itself creates it after its preflight snapshot.  Preserve them;
never reset, delete, overwrite, stage, or commit them merely to make the tree
clean.

Before the first edit, record `git status --short`, `git diff --name-status`,
and the relevant current-plan/dashboard state in the new remediation dashboard.
After each task, identify the exact files the task changed.  A local commit is
allowed only when its index contains exclusively the implementation's source,
tests, newly generated task/code-assist artifacts, new dashboard, and any
progress records created by this orchestration.  Do not stage pre-existing
changes.  If that scoped index cannot be established safely, leave all changes
uncommitted, write a handoff explaining why, and continue to the final report.

## Start and restart recovery

On every initial run and every resume, before editing:

1. Read every governing artifact, design, implementation plan, and this prompt.
2. Reconcile the implementation-plan checklist, remediation dashboard,
   fullscreen-routing plan/dashboard, iteration checklist, generated tasks,
   code-assist progress/logs, handoffs, commits, Git status/diff, and test logs.
3. Resume at the first incomplete or unverified action.  Never trust a stale
   completion checkbox over source, test, and diff evidence.
4. Append a context-ledger row to the remediation dashboard for each separate
   generator, code-assist, remediation, validation, and main-thread review
   context.

Keep the dashboard's phase table and numbered stages current.  Mark a stage
completed only with evidence; mark a phase completed only when every stage is
completed.  Preserve the existing fullscreen-routing plan and iteration
checklist history; update their reopened fallback items only after relevant
validation passes.

Emit an inline update before and after every plan step, isolated task context,
test/build, review, and handoff.  While a command/context runs, provide a
heartbeat at least every 60 seconds.  Use this exact format:

`Step: [n]; Task: [id]; Phase: [planning|implementation|validation|review]; Action: [running/completed action]; Next: [next action]`

## Isolated-context execution protocol

Use fresh, separate agent/context windows for every code-task breakdown and
every code-assist task.  Do not reuse a generator context as a code-assist
context.  Do not overlap code-writing agents; run them sequentially.  The main
thread owns reconciliation, scoped-diff review, progress documents, handoffs,
and final reporting.

### A. One fresh code-task-generator context

Invoke `code-task-generator` in its own fresh context.  Give it the approved
design and implementation-plan paths, the task-artifact root above, and this
explicit standing authorization: the user has already approved generation and
execution, so after it presents its internal breakdown, it must review its
scope itself and proceed without asking the user.

Generate **one cohesive functional task**, not a test-only task: “restore
native GNOME helper-unavailable legacy-follow fallback.”  It combines
implementation-plan Steps 1–2 because the direct regression tests and the
profile-policy production change are one indivisible TDD increment.  The task
must require strict RED → GREEN → REFACTOR and include:

- a neutral, explicit `helper_unavailable_is_terminal`-style profile policy;
- native `gnome_shell_wayland` missing helper → `None` → existing legacy
  follower;
- legacy `gnome_shell_raster` missing helper → existing terminal fail-closed
  result;
- no runner call in either unavailable-helper case;
- no raw compositor enum dispatch/imports in generic consumer/follow code;
- no changes outside the approved scope;
- deterministic unit-test selection, explicitly noting that no `load.py` or
  lifecycle wiring changed and no harness test is required.

The generator must follow its required code-task format and save the task under
the specified task-artifact root.  The main thread must inspect the generated
task against the design before code-assist starts.  If it creates more than one
functional task, execute them sequentially, each in its own fresh code-assist
context.

### B. One fresh code-assist context per generated task

For each generated task, invoke `code-assist` in a new isolated context with:

- `mode: auto`;
- `repo_root: /home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`;
- the generated task file as `task_description`;
- the code-assist documentation root above;
- the approved design, implementation plan, governing artifacts, worktree
  safety baseline, and exact test requirements as additional context.

Require `code-assist` to use strict RED → GREEN → REFACTOR.  It must create
its own `context.md`, `plan.md`, `progress.md`, and logs in its isolated
documentation directory; code and tests belong only in normal repository
locations.  It must record all decisions, exact test commands/results, and
whether each result is pass/fail/skip.

Expected production touch points are limited to:

- `overlay_client/backend/presentation_runtime.py`
- `overlay_client/backend/bundles/gnome_shell_wayland.py`

Expected test touch points are limited to the existing relevant unit suites,
including `overlay_client/tests/test_follow_surface_mixin.py`,
`overlay_client/tests/test_backend_consumers.py`, and only any existing GNOME
runtime/architecture tests required to prove the acceptance criteria.

Each code-assist handoff written to `/home/jon/handoffs/` must contain exactly:

`Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`

Allow one implementation attempt and at most two fresh-context remediation
attempts per task.  Never rerun an unchanged failing command more than once.
If the same unresolved code failure persists, a required acceptance criterion
is ambiguous, scope must expand, or 20 minutes elapse without substantive
progress, stop implementation, write an evidence-backed handoff/dashboard
entry, and report the blocker.  Do not conceal it by weakening assertions.

## Validation and acceptance

Run the following focused test gate after the implementation task, then have
the main thread independently review its results and the scoped diff:

```bash
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_backend_consumers.py \
  overlay_client/tests/test_gnome_helper_presentation_runtime.py \
  overlay_client/tests/test_backend_architecture_boundary.py -q

overlay_client/.venv/bin/python -m ruff check \
  overlay_client/backend/presentation_runtime.py \
  overlay_client/backend/bundles/gnome_shell_wayland.py \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_backend_consumers.py

git diff --check
```

Then run the project gate exactly as follows; merely activating
`overlay_client/.venv` does not override the Makefile interpreter choice:

```bash
make PYTHON=overlay_client/.venv/bin/python check
```

Required acceptance criteria:

1. The previously failing native helper-unavailable follow-surface regression
   calls the legacy follower exactly once.
2. Native GNOME without a helper returns no backend-presentation result and
   does not invoke the helper runner.
3. Legacy raster without a helper remains hidden/fail-closed, retains
   `presentation_state=helper_unavailable`, and does not invoke the runner.
4. Available-helper native fullscreen/windowed behavior remains covered by the
   existing focused tests.
5. Architecture-boundary tests pass, and neither generic consumers nor follow
   surface gains raw GNOME/raster dispatch or compositor-specific imports.
6. Ruff, mypy, and every non-sandbox-blocked test assertion pass.

The project gate previously encountered five loopback socket harness setup
errors in this sandbox.  If they recur, capture the exact error and affected
tests separately in the dashboard and handoff.  They are an environment
limitation, not an excuse for an assertion failure.  Do not attempt to bypass
the sandbox, change network policy, disable those tests, or claim a fully green
release gate.  All non-socket failures must be fixed within the retry policy.

Use the passing focused unit suite as the safe demo.  No screenshot or live
desktop action is appropriate or authorized for this backend policy repair.

## Completion, reporting, and commit

After the main-thread validation review:

1. Update the new remediation dashboard with exact evidence and all phase/stage
   statuses.
2. Update the remediation implementation plan, fullscreen-routing plan and
   its execution status, and the iteration checklist only where the regression
   evidence justifies it.  Do not mark the full project gate green if socket
   setup is still sandbox-blocked.
3. Recheck the pre-existing-worktree baseline.  If a safely scoped local commit
   is possible and the code-assist commit preconditions are met, commit only
   the implementation-owned files using Conventional Commits; never push.
   Otherwise preserve the unstaged changes and state the exact reason.
4. Write a final main-thread handoff in `/home/jon/handoffs/` with the required
   six fields.

The final report must list completed steps, changed files, generated task and
code-assist artifacts, exact commands and pass/fail/skip results, commit hash
if any, manual actions remaining, socket-sandbox limitations, and the scoped
EDMC compliance Yes/No review required by `AGENTS.md`.  Successful tests never
authorize external actions.
