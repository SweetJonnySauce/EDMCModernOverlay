# Implementation Orchestration: Native GNOME Fullscreen Raster Focus-Visibility Regression

## Scope and authority

Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`

Approved implementation plan:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-fullscreen-focus-visibility-regression-plan.md`

Governing artifacts:

- `AGENTS.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/progress.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/iteration-checklist.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-plan.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-execution-status.md`
- this orchestration prompt and every more-specific instruction file discovered before editing

Task-artifact root:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/tasks/native-gnome-fullscreen-focus-visibility-regression/`

Code-assist artifact root:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/code-assist/native-gnome-fullscreen-focus-visibility-regression/`

Status dashboard:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-fullscreen-focus-visibility-regression-execution-status.md`

Implement the approved regression fix autonomously. It is standing approval for
ordinary, in-scope local edits to source, tests, fixtures, plan/task/process
documentation, non-destructive tests/builds/formatters, concise handoffs under
`/home/jon/handoffs`, and scoped local Git commits after required validation.
Do not push, open a PR, reset/rebase, initialize a repository, stage unrelated
paths, or change historical artifacts except where this prompt explicitly
requires progress reconciliation.

The required product behavior is exact:

- In the native `gnome_shell_wayland` fullscreen Shell-raster route,
  `keep_overlay_visible` is the **only** authorization to set
  `allow_unfocused_target=True`.
- When the preference is unchecked and Elite is unfocused, preserve the
  existing helper protocol path that suspends/hides the Shell actor with
  `target_not_focused`; do not rely only on generic PyQt-label suppression.
- When checked, the same unfocused target remains visible by explicit choice.
- Do not change fullscreen eligibility, monitor placement, frame-provider
  choice, geometry, presenter ownership, click-through, helper protocol/schema,
  target discovery, or native X11/xcompat behavior.
- Remove the contradictory fullscreen/full-monitor geometry exception and its
  obsolete coverage. Preserve the `fix219` boundary: generic follow/runtime
  surfaces must not gain raw backend/helper enum dispatch or compositor imports.

Stop and ask the user before any action outside these limits: destructive or
broad overwrite operations; scope expansion; unresolved design conflict or
security concern; network access other than approved dependency registries or
primary documentation; credential/account/remote actions; push/PR; any change
outside this repository, its `.git`, and `/home/jon/handoffs`; or starting,
stopping, controlling, reloading, enabling, disabling, installing, or
uninstalling EDMC, Elite, GNOME Shell, or its extension. Do not issue DBus or
session-bus probes. The live acceptance matrix is manual-only and must pause
for the user to perform it and return non-secret observations/diagnostics.

## Start and restart recovery

Before edits on the initial run, every resume, every new plan step, and every
fresh remediation context:

1. Read this prompt, the approved plan, every governing artifact, applicable
   skills, and discovered instruction files in full.
2. Reconcile the plan checklist and phase/stage tables; `progress.md`; this
   dashboard; task/code-assist artifacts; `/home/jon/handoffs`; Git
   status/diff/log; and validation logs. Never trust a stale completion claim.
3. Resume at the first incomplete or unverified action. Do not redo validated
   work unless its evidence or assumptions are missing.
4. Treat dirty paths outside this regression’s task/artifact roots and the
   approved source/test scope as user-owned. Never reset, stage, or overwrite
   them.
5. Run `git diff --check` before edits and after every implementation context.
   Do not make baseline or cleanup commits for unrelated work.

Keep the plan, `progress.md`, and dashboard accurate. Before and after each
plan step, task-generator context, code-assist context, validation, commit,
or manual gate, send a main-thread update exactly in this format:

`Step: [n]; Task: [id]; Phase: [planning|implementation|validation|demo]; Action: [running|completed|blocked] [short action]; Next: [next action]`

For work lasting more than 60 seconds, send a concise heartbeat at least every
60 seconds.

## Fresh-context execution protocol

Work one implementation-plan step at a time. Never overlap code-writing
agents or contexts. The user has approved autonomous task generation and
implementation inside the stated scope; do not pause for a second approval
between an in-scope task breakdown and implementation.

### Step 1: Restore the preference-to-helper authorization contract

1. Start exactly one fresh dedicated `code-task-generator` context for Step 1.
   It must read the plan and governing artifacts, then generate only the
   smallest functional task breakdown required to implement Step 1 under the
   task-artifact root. It must not generate a test-only task. Record the
   generated files and its scope assessment in the dashboard.
2. In the main thread, review every generated task for scope, Given/When/Then
   acceptance criteria, unit-test selection, exact no-regression constraints,
   stale-helper removal, and `fix219` boundary compliance. Do this review
   autonomously; revise a task only if needed to match the approved plan.
3. For each approved generated task, start exactly one fresh, dedicated
   `code-assist` context in auto mode. Never reuse a code-assist context for
   another task or remediation. Give it the task file, repository root, all
   governing artifacts, and an isolated documentation directory under:

   `implementation/code-assist/native-gnome-fullscreen-focus-visibility-regression/stepNN/task-NN-slug/`

4. Each code-assist context must use strict RED -> GREEN -> REFACTOR and may
   edit only its approved source/test scope, its own documentation directory,
   the approved plan, `progress.md`, the dashboard, and its concise handoff.
   It must record context, selected test type, RED/GREEN/REFACTOR outcomes,
   decisions, exact commands/results, secret scan, and scoped-diff review.
5. Required Step 1 proof:

   - An unfocused full-monitor native-GNOME target with
     `keep_overlay_visible=False` produces a raster request with
     `allow_unfocused_target=False`; the helper’s `target_not_focused` result
     is a focus-risk suspension and `should_show_overlay` is false.
   - The inverse unfocused case with the preference true produces `true` and
     can present.
   - Existing focused fullscreen, windowed managed-PyQt, overview, target-loss,
     transition, extension source-contract, and X11/xcompat boundary behavior
     remain unchanged.
   - Use unit tests; no `load.py` or lifecycle behavior is in scope, so a
     harness test is not required unless scope changes.

6. Minimum validation:

   ```bash
   source overlay_client/.venv/bin/activate
   PYQT_TESTS=1 python -m pytest \
     overlay_client/tests/test_gnome_helper_presentation_runtime.py \
     overlay_client/tests/test_gnome_shell_helper_extension_source.py \
     overlay_client/tests/test_shell_raster_frame.py -q
   git diff --check
   ```

7. After green validation, the code-assist context performs a scoped diff
   review, scans changed text artifacts/logs for secrets, updates its task
   records and the dashboard, writes one dated handoff under
   `/home/jon/handoffs`, and makes one conventional scoped local commit. It
   must not include unrelated dirty paths or historical plan artifacts.
8. Require every code-assist handoff to contain exactly:
   `Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`
9. In the main thread independently review the task files, commit, handoff,
   plan/dashboard/progress stages, validation evidence, and scoped diff before
   marking Step 1 completed. Do not proceed on a stale or partial claim.

Allow one initial code-assist attempt and at most two fresh-context remediation
attempts for a generated task. A remediation needs a new documentation
directory and the previous handoff. Never rerun an unchanged failing command
more than once. Stop with evidence after the retry limit or 20 minutes without
substantive progress.

### Step 2: Automated validation and manual GNOME acceptance

Step 2 is validation-only. Start one fresh, dedicated `code-task-generator`
context to classify it and record that no functional code-assist task is
needed unless it discovers a genuine approved implementation gap. Do not create
a code-assist task solely to run tests.

In the main thread:

1. Run the focused Step 1 suite again if its independent review changes code,
   then run:

   ```bash
   source overlay_client/.venv/bin/activate
   make check
   make test
   ```

   Record exact commands and outcomes. If a check is blocked by the sandbox or
   environment, record the reason and remaining risk; do not claim it passed.
   Do not repeatedly rerun an unchanged blocked command.
2. Reconcile automated evidence and update Step 2 automated status.
3. Stop and ask the user to perform the live GNOME Wayland matrix. Do not
   manipulate their session. Ask for non-secret results covering:

   | Preference | Elite focus | Required result |
   | --- | --- | --- |
   | Unchecked | Focused | Shell raster presents normally on Elite’s monitor |
   | Unchecked | Lost | Shell actor is suspended/hidden after the normal refresh cycle; no stale content remains visible |
   | Unchecked | Regained | Shell raster resumes on Elite’s monitor without focus theft |
   | Checked | Lost | Shell raster remains visible by explicit user choice |
   | Either | Fullscreen target moves monitor | Placement remains with Elite; no duplicate PyQt surface appears |

   For the unfocused interval, request diagnostics that establish
   `target.hasFocus:false`, `allow_unfocused_target:false`, and
   `target_not_focused`/suspension when unchecked; the checked case must show
   `allow_unfocused_target:true` and normal raster presentation. If the user
   waives diagnostics, record that explicit waiver and its residual risk.
4. After user-provided evidence, update all checklist/stage states, the
   dashboard, `progress.md`, and the iteration checklist. Commit only those
   scoped documentation updates after final reconciliation, if they are not
   already included in the Step 1 commit.

## Completion and final report

Complete only when every plan step/stage and dashboard row is accurate, code
tasks/code-assist contexts have their own artifacts and handoffs, validation
evidence is recorded, the `fix219` boundary remains intact, and the user has
completed or explicitly waived the manual matrix.

For the final report, provide: completed steps and demos; generated task and
code-assist artifact paths; files changed; exact tests/builds and results;
commits; handoff paths; manual actions/outcomes; known limitations; and
confirmation that nothing was pushed. Include the scoped EDMC compliance audit
from `AGENTS.md`, with every item marked **Yes** or **No** and a reason plus
corrective action for each **No**. Passing tests never authorize external or
live actions.
