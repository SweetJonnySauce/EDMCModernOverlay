# Implementation Orchestration: GNOME Wayland Fullscreen Shell-Raster Routing

## Scope and authority

Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`

Approved implementation plan:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-plan.md`

Required design:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/fullscreen-shell-raster-routing.md`

Required research:

- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/mutter-placement-probe-and-raster-inventory.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/existing-code-and-runtime-evidence.md`

Governing instructions: `AGENTS.md` and every more-specific instruction file
discovered before editing.

Task-artifact root:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/tasks/fullscreen-shell-raster-routing/`

Code-assist artifact root:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/code-assist/fullscreen-shell-raster-routing/`

Status dashboard:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/fullscreen-shell-raster-routing-execution-status.md`

Historical monitor-transfer plan, prompt, tasks, and status artifacts remain
read-only evidence for this run. Do not update their checklists or re-run their
manual delivery task.

Implement only the approved native GNOME Wayland fullscreen presenter routing:

- `gnome_shell_wayland` selects the existing real-content GNOME Shell raster
  actor only for eligible fullscreen/full-monitor targets.
- Its windowed path remains managed PyQt.
- A fullscreen raster failure clears/suppresses presentation; it must not fall
  back to the known-misplaced PyQt window.
- Presenter selection moves behind a bundle-owned runtime seam so generic
  follow/runtime code never chooses behavior from raw GNOME/helper/backend
  enums.

Preserve the fix219 backend boundary. Native X11 and XWayland compatibility are
separate backends and are out of scope. Do not modify target discovery, payload
semantics, the public helper protocol/schema, or unrelated work. The existing
`GNOME_SHELL_RASTER` identity is compatibility/development scaffolding in this
scope; do not remove its selector, override, or status surface without a later
approved cleanup plan.

The plan is standing approval only for ordinary, local, in-scope code, tests,
fixtures, task/process documentation, non-destructive builds/formatters, and
local commits after required validation. Do not push, open a PR, reset/rebase,
initialize a repository, or stage unrelated paths. The session may write the
existing repository `.git` directory and `/home/jon/handoffs` only for scoped
commits and concise restart handoffs.

Stop and ask the user before:

- destructive or broad overwrite operations; changes outside the repository,
  `.git`, or `/home/jon/handoffs`; scope expansion; an unresolved design
  conflict; a security concern; or a retry-limit failure;
- network access other than direct package registries or primary documentation;
- any credential, account authorization, remote write, live API, or push;
- starting/stopping/controlling EDMC, Elite Dangerous, GNOME Shell, or another
  live application;
- installing, updating, reloading, enabling, disabling, or uninstalling the
  GNOME extension; changing GNOME settings; or issuing session-bus probes.

For a required live action, provide the exact command, target, and expected
side effect, then wait for explicit approval. If sandboxed, ask the user to
run the command in their GNOME session and provide only non-secret results.

## Start and restart recovery

Before editing on the initial run, every restart, every new plan step, and
every remediation context:

1. Read this prompt, the approved plan and design, required research,
   `AGENTS.md`, applicable skills, and discovered instruction files.
2. Reconcile the routing plan checklist and phase/stage tables, this dashboard,
   generated tasks, code-assist artifacts/handoffs, `/home/jon/handoffs`, Git
   status/diff/log, and available validation logs. Never trust a stale claim.
3. Resume at the first incomplete or unverified action. Do not redo validated
   work unless its evidence or assumptions are missing.
4. Preserve unrelated work. Treat every existing dirty path outside this
   routing artifact root or the currently approved task as user-owned.
5. Run `git diff --check` before edits. Do not create a baseline commit for
   pre-existing or historical planning artifacts.

Keep these artifacts accurate after every meaningful event:

- `implementation/fullscreen-shell-raster-routing-plan.md` — checklist plus
  phase/stage tables;
- `implementation/fullscreen-shell-raster-routing-execution-status.md` — step
  dashboard and context ledger; and
- one concise dated restart handoff under `/home/jon/handoffs` whenever a
  context ends incomplete, blocks, or hands work to a fresh context.

Before and after every plan step, generator context, code-assist context,
test/build, demo, or manual gate, send a main-thread update exactly as:

`Step: [n]; Task: [id]; Phase: [planning|implementation|validation|demo]; Action: [running|completed|blocked] [short action]; Next: [next action]`

While an action runs longer than 60 seconds, send a concise heartbeat at least
every 60 seconds.

## Fresh-context workflow

Work strictly one approved implementation-plan step at a time. Do not overlap
writing contexts.

For each incomplete plan step:

1. Create one **fresh, dedicated context window** for `code-task-generator`.
   Do not reuse a generator context. Give it this plan path, the explicit step
   number, and this run's task-artifact root. It must read the required design
   and generate only functional code tasks, never test-only tasks.
2. The generator must present its task breakdown, ordering, dependencies,
   complexity, acceptance criteria, and demo to the user. Stop for explicit
   user approval before it writes task files.
3. In the main thread, inspect every approved generated task for scope,
   references, Given/When/Then criteria, relevant test type, fail-closed rules,
   and fix219 boundary compliance. Update the routing dashboard with the
   generator outcome.
4. For **each generated code task**, create one **fresh, dedicated context
   window** for `code-assist` in `auto` mode. Never reuse a code-assist context
   for another task or remediation. Give it the task file, repository root,
   all governing/design references, and an isolated documentation directory:
   `implementation/code-assist/fullscreen-shell-raster-routing/stepNN/task-NN-slug/`.
5. Each code-assist context follows strict RED → GREEN → REFACTOR. It may edit
   only its task scope, required tests, its own documentation directory, the
   routing plan, routing dashboard, and its handoff. It must record context,
   test plan, RED/GREEN/REFACTOR outcomes, decisions, logs, exact commands,
   and scoped-diff review. Production code/tests never belong in artifact
   directories.
6. After validation, the code-assist context reviews its scoped diff, scans
   changed text/logs for secrets, updates this run's plan/dashboard, writes a
   concise `/home/jon/handoffs` handoff, and makes its own conventional local
   commit. Never push. It must not stage historical dirty files or another
   task's artifacts.
7. Every code-assist handoff must contain exactly:
   `Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`
8. In the main thread, independently review commit, handoff, plan stages,
   dashboard, tests, and scoped diff before marking the task/stage complete.
   Start the next fresh generator context only after reconciliation.

Allow one initial code-assist attempt plus at most two fresh-context
remediation attempts per task. A remediation context needs a new documentation
directory and the previous handoff. Never rerun an unchanged failing command
more than once. Stop with evidence after the retry limit or 20 minutes without
substantive progress.

## Step-specific guardrails and validation

### Step 1: Bundle-owned runtime seam

- Preserve existing behavior. Add a narrow bundle-owned GNOME presentation
  runtime/profile seam and migrate raw raster/GNOME selection predicates out
  of generic `consumers.py` dispatch.
- Do not enable native-GNOME fullscreen raster yet.
- Prove X11/xcompat do not import or receive GNOME runtime behavior.
- Use unit tests for pure/profile selection and the architecture-boundary test.
- Minimum validation:

  ```bash
  PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
    overlay_client/tests/test_backend_consumers.py \
    overlay_client/tests/test_backend_architecture_boundary.py -q
  git diff --check
  ```

### Step 2: Eligible native-GNOME fullscreen raster

- Enable the existing real-content frame provider/bridge only for eligible
  `gnome_shell_wayland` fullscreen/full-monitor targets.
- Retain managed PyQt for windowed/partial/ambiguous targets. Do not enable a
  static proof frame in production.
- Test real-content request selection, windowed/ineligible exclusion, and
  provider/no-visible-content failure suppression.
- Minimum validation:

  ```bash
  PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
    overlay_client/tests/test_gnome_helper_presentation_runtime.py \
    overlay_client/tests/test_shell_raster_frame.py \
    overlay_client/tests/test_repaint_debounce.py -q
  git diff --check
  ```

### Step 3: Safe presenter transitions and failure cleanup

- Ensure raster → managed PyQt clears the actor first; target/helper loss and
  token replacement clear/reset safely; fullscreen failures remain fail-closed.
- Preserve non-reactive actor behavior, stacking above Elite, click-through,
  focus safety, cache bounds, and existing transition guards.
- Never add sleeps, coordinate guesses, monitor-transfer variants, or a
  fullscreen PyQt fallback.
- Minimum validation:

  ```bash
  PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
    overlay_client/tests/test_gnome_helper_presentation_runtime.py \
    overlay_client/tests/test_presentation_transition.py \
    overlay_client/tests/test_gnome_shell_helper_extension_source.py \
    overlay_client/tests/test_backend_architecture_boundary.py -q
  git diff --check
  ```

### Step 4: Automated and manual native-GNOME acceptance

- Run the combined focused suite, then `make check` and `make test`. Record
  exact environment limitations rather than claiming a skipped check passed.
- No `load.py` or EDMC hook change is planned. If that scope changes, add a
  harness test before implementation.
- Do not deploy/reload the extension or run DBus calls without separate user
  approval. After approval, request non-secret evidence for this matrix:

| Case | Required result |
| --- | --- |
| Elite primary / overlay initially secondary | Shell raster visible only on Elite's monitor |
| Elite secondary / overlay initially primary | Same outcome in reverse direction |
| Elite moves monitors while fullscreen | Actor follows; no stale prior-monitor actor |
| Fullscreen → windowed → fullscreen | Clear/managed/raster transition without duplicate or focus theft |
| Target minimize/close/helper reload | Actor clears and client fails closed |
| Click-through, stacking, content update | Non-reactive actor stays above Elite and renders real updates |

Visual placement alone is not proof. Require renderer, target/monitor/rect,
transition, and degrade-reason diagnostics as well.

## Compliance, completion, and report

- Explicitly choose unit versus harness coverage before every behavior change,
  following `AGENTS.md`. A `load.py` touch requires a harness test.
- Follow the EDMC Python baseline/check rules in `AGENTS.md`; label a permitted
  `ALLOW_EDMC_PYTHON_MISMATCH=1` run as non-release development validation.
- In the final review, report every EDMC compliance item in `AGENTS.md` as
  **Yes** or **No**; each **No** needs its reason and corrective work. Distinguish
  plugin-runtime rules from this helper/backend-only scope.
- Complete only after every plan step/stage is accurate, each generated task
  has a fresh-context handoff and local commit, required validation evidence is
  recorded, the fix219 boundary is preserved, and the user-approved manual
  matrix has passed.

Final report: completed steps/demos; generated tasks and code-assist artifacts;
files changed; exact test/build results; commits; handoff paths; manual actions
and outcomes; Yes/No EDMC audit; known limitations; and confirmation that
nothing was pushed. Tests never authorize external or live actions.
