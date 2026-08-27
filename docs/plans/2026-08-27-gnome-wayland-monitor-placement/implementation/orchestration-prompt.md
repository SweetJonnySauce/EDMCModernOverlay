# Implementation Orchestration: GNOME Wayland Monitor Placement

## Scope and authority

Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`

Approved implementation plan:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/plan.md`

Required design:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/detailed-design.md`

Required research:

- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/existing-code-and-runtime-evidence.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/mutter-window-placement.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/research-plan.md`

Governing instructions: `AGENTS.md` and any more-specific instruction files
discovered before editing.

Task-artifact directory:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/tasks/`

Code-assist artifact directory:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/code-assist/`

Status dashboard:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/execution-status.md`

Implement only the approved native GNOME Wayland monitor-placement correction:
conditionally call `Meta.Window.move_to_monitor(targetMonitor)` before the
existing frame-resize action when the trusted Elite target monitor and the
overlay's current monitor are valid and different. Preserve the existing
readback tolerance, retry, persistent-mismatch suppression, click-through,
stacking, and focus-safety gates.

The approved scope excludes changes to native X11, XWayland compatibility,
renderer selection, payload processing, generic follow surfaces, backend
selection, public helper protocol/schema, fullscreen/probe behavior, and
unrelated untracked work. Preserve the `fix219` backend boundary: generic
runtime/follow surfaces must not import, branch on, or otherwise dispatch
GNOME-helper presentation behavior.

This prompt grants standing authority for ordinary in-scope workspace work:
code, tests, fixtures, task documentation, logs, package installation of direct
development dependencies, non-destructive test/build/formatter commands, and
local commits after the relevant task passes all required validation. Never
push, create a PR, reset/rebase, initialize a repository, or alter unrelated
files.

Stop and ask the user before:

- broad/destructive operations, including deleting files outside the single
  helper UUID directory managed by the development script;
- scope expansion, an unresolved design conflict, a security concern, or an
  unchanged failing command after its permitted retry;
- network access other than direct package registries or primary documentation;
- starting, stopping, sending data to, or otherwise controlling EDMC, Elite
  Dangerous, or another live application;
- running GNOME Shell extension `install`, `update`, `reload`, `enable`,
  `disable`, or `uninstall`; issuing a session-bus presentation probe; or
  changing GNOME settings. Explain the exact command, its target extension
  directory, and the expected side effect before asking; and
- any action requiring credentials, account authorization, a remote write, or
  a live API.

If live GNOME/session-bus actions are blocked by the sandbox, do not widen the
sandbox or use an unsafe bypass. Ask the user to run the exact manual command
in their GNOME session and paste only the relevant non-secret result.

## Start and restart recovery

Before editing on every initial run, restart, new plan step, or remediation
context:

1. Read this prompt, all required artifacts, `AGENTS.md`, and any applicable
   skill instructions.
2. Reconcile the implementation checklist, phase/stage tables, status
   dashboard, generated task files, code-assist handoffs, Git status/diff, and
   available test logs. Never trust a stale completion claim.
3. Resume at the first incomplete or unverified action. Do not redo a completed
   task unless its evidence is missing or its assumptions changed.
4. Preserve all unrelated work. If the worktree contains paths outside this
   planning directory or the current approved task, stop and ask the user.

At startup, if the only uncommitted files are these GNOME Wayland planning and
orchestration artifacts, inspect them, run `git diff --check`, and make one
dedicated local documentation baseline commit before generating implementation
tasks. Use a conventional message such as `docs(plan): add GNOME Wayland
placement plan`. Do not mix it with product code. If any unrelated changes are
present, do not stage or commit anything until the user directs otherwise.

Maintain the status dashboard and phase/stage tables after every completed
task, validation result, manual gate, or blocked attempt. Before and after each
plan step, task-generation context, code-assist context, test/build, and demo,
post a main-thread update in exactly this format:

`Step: [n]; Task: [id]; Phase: [planning|implementation|validation|demo]; Action: [running/completed/blocked action]; Next: [next action]`

While a command or agent runs longer than 60 seconds, provide a concise
heartbeat at least every 60 seconds.

## Fresh-context task workflow

Work strictly one implementation-plan step at a time. Do not overlap agents
that edit code or documentation.

For each incomplete implementation-plan step:

1. Start one **new, dedicated context** for `code-task-generator`; do not reuse
   any prior generator context. Give it the approved plan path, the explicit
   step number, and this task-artifact directory. It must read the detailed
   design and only create functional code tasks—never a test-only task.
2. The generator must present its proposed task breakdown, ordering, and
   dependencies to the user. Stop for the user's explicit approval before it
   writes task files, as required by the `code-task-generator` workflow.
3. After approval, have the main thread inspect every generated task for scope,
   acceptance criteria, references, test requirements, and backend-boundary
   compliance. Do not implement an ambiguous or scope-expanding task.
4. For **each generated code task**, start one **new, dedicated context** for
   `code-assist` in `auto` mode. Never reuse a code-assist context for another
   task. Give it the task file, repository root, and an isolated documentation
   directory under the code-assist artifact directory:
   `stepNN/task-NN-slug/`.
5. Each code-assist context must follow strict RED → GREEN → REFACTOR. It may
   edit only its approved task scope and the required planning/status artifacts.
   It must run focused tests before broader checks, record all commands and
   results, review its scoped diff, and make its own conventional local commit
   only after the task's required validation passes. Never push.
6. Require the code-assist handoff to contain exactly:
   `Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`
   Record that handoff in the status dashboard before creating the next context.
7. Independently review the task's commit, status, plan checklist, and test
   evidence in the main thread. Mark a stage/phase complete only when all of
   its stages are complete. Then start the next generator context.

Allow one initial code-assist attempt and at most two fresh-context remediation
attempts per generated task. A remediation attempt must be a new context with a
new documentation directory and a handoff from the failed attempt. Never rerun
the same failing command unchanged more than once. Stop with the command output,
diff state, and diagnosis after the retry limit or 20 minutes without
substantive progress.

## Plan-specific implementation and validation rules

### Step 1: Guarded monitor transfer

- Limit production code to the GNOME Shell helper ordinary attach/presentation
  path and its focused source-contract tests.
- Add the tests before or alongside the behavior: valid mismatch moves before
  resize; matching or invalid monitor state does not move; post-operation state
  is read; transfer unavailable/error retains resize fallback and fail-closed
  readback semantics.
- Run at minimum:

  ```bash
  PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
    overlay_client/tests/test_gnome_shell_helper_extension_source.py -q
  git diff --check
  ```

### Step 2: Readback, diagnostics, and backend boundary

- Do not change the helper protocol/schema. Diagnostics may expose the normal
  decision and pre/post monitor state only through the existing optional
  diagnostic mechanism.
- Preserve the existing Python retry/backoff tests and the architecture boundary
  test. Do not add raw backend/helper enum dispatch to generic code.
- Run at minimum:

  ```bash
  PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
    overlay_client/tests/test_gnome_shell_helper_extension_source.py \
    overlay_client/tests/test_gnome_shell_helper_presentation_state.py \
    overlay_client/tests/test_gnome_helper_presentation_runtime.py \
    overlay_client/tests/test_backend_architecture_boundary.py -q
  make check
  ```

### Step 3: Manual GNOME Wayland delivery

The extension update/reload and every live test are manual-only pending explicit
user approval. Before the manual gate, prepare the exact command and explain
whether it overwrites the user-local extension directory:

```bash
./scripts/dev_gnome_helper.sh update
./scripts/dev_gnome_helper.sh status
```

After the user approves and the helper is active, ask the user to perform or
observe the following matrix and provide the relevant diagnostics:

| Case | Required evidence |
| --- | --- |
| Elite primary, overlay initially secondary | Overlay transfers to primary; requested/applied rects match |
| Elite secondary, overlay initially primary | Overlay transfers to secondary; requested/applied rects match |
| Repeated cross-monitor moves | No accumulated offset; bounded retry only if readback lags |
| Already co-located | No unnecessary transfer action |
| Click-through/focus/stacking/resize | Overlay stays click-through, does not steal focus, remains above Elite, and follows resize |

Visual placement without matching helper readback is a failure. Do not add
sleeps, coordinate guesses, fullscreen workarounds, or cross-backend fallbacks
to compensate for a failing live result. If a live-only defect remains, record
it with evidence and stop for user direction.

## Testing, compliance, and reporting

- Explicitly choose test type before each behavior change. This helper change
  requires focused deterministic/unit or source-contract coverage. A harness
  test is required only if implementation reaches `load.py` or lifecycle/hook
  wiring; that expansion requires user approval first.
- Run the project checks required by `AGENTS.md`. If the EDMC Python baseline
  check fails solely because the development interpreter is non-baseline,
  record it; use `ALLOW_EDMC_PYTHON_MISMATCH=1` only for explicitly
  non-release/development validation and label it as such.
- Do not place code in task/code-assist documentation directories. Record
  context, test plan, RED/GREEN/REFACTOR evidence, decisions, logs, and commit
  SHA there; production code and tests belong in their established locations.
- Scan changed text artifacts and logs for secrets. Do not expose session-bus
  addresses, credentials, or unrelated user data in reports.
- Before final completion, report every EDMC compliance item from `AGENTS.md`
  as **Yes** or **No**. For each **No**, identify the reason and required
  corrective work. Distinguish plugin-runtime checks from this helper-only
  scope.

## Completion and final report

Complete only when all plan steps/checklist items and phase/stage tables are
accurate, each generated task has a recorded fresh-context handoff and local
commit, focused tests and `make check` have passed or documented skips, the
scoped diff preserves all backend boundaries, and the user-approved live GNOME
matrix has passed.

Report: completed steps/demos; generated task files and code-assist artifacts;
files changed; exact validation commands and outcomes; commit SHAs; explicit
manual actions and results; the Yes/No EDMC compliance audit; known limitations;
and confirmation that nothing was pushed. Passing automated tests never
authorizes a live or external action.
