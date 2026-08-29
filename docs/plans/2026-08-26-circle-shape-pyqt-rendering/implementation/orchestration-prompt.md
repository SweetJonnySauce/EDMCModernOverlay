# Implementation Orchestration: Circle Shape Support

## Scope and authority

Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`

Approved plan: `docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/plan.md`

Governing artifacts, in reading order:

1. `AGENTS.md`
2. `docs/plans/2026-08-26-circle-shape-pyqt-rendering/idea-honing.md`
3. `docs/plans/2026-08-26-circle-shape-pyqt-rendering/research/payload-and-rendering.md`
4. `docs/plans/2026-08-26-circle-shape-pyqt-rendering/design/detailed-design.md`
5. `docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/plan.md`
6. This orchestration prompt

Task-artifact directory: `docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks`

Status dashboard: `docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/execution-status.md`

The approved plan authorizes ordinary, in-scope workspace-local work only: source code, tests, fixtures, documentation, build metadata, generated task artifacts, non-destructive validation, and local commits after validation. Never push.

Stop and ask the user before real network/API activity beyond normal approved package installation or primary documentation lookup; credential use, OAuth/account authorization, external writes, uploads, releases, PRs, destructive commands, broad overwrites, Git reset/clean, changes outside this workspace, scope expansion, security concerns, missing product decisions, or an unresolved failure.

Do not use `--dangerously-bypass-approvals-and-sandbox` or any equivalent sandbox-bypass mechanism.

## Goal

Implement every unchecked step in the approved plan, in order:

1. Backward-compatible circle payload contract and unit coverage.
2. Circle raw normalization, validation, storage, and deduplication.
3. Transform-aware PyQt `QPainter.drawEllipse` rendering.
4. Raw/TCP EDMC harness wiring and public documentation.
5. Release-quality regression validation and evidence recording.

For every plan step, first generate an execution-ready code-task breakdown, then implement every generated task with `code-assist`. Update the approved plan and status dashboard as work proceeds.

## Start and restart recovery

Before every initial run, restart, or resume:

1. Read all governing artifacts in the listed order.
2. Inspect `execution-status.md` if it exists; create it otherwise.
3. Reconcile the status dashboard, plan checklist/stage tables, generated task files, task progress records, `git status --short`, `git diff --check`, and available validation logs.
4. Treat stale completion claims as untrusted. Resume at the first incomplete or unverified action.
5. Do not overwrite generated task artifacts; create a new task artifact only when the current plan step has none, or update it only when review demonstrates a requirement gap.

Maintain the dashboard throughout the run. Before and after every plan step, task-generation agent, implementation agent, test, build, and demo, write this exact one-line status format:

```text
Step: [n]; Task: [id or none]; Phase: [planning|implementation|validation|demo]; Action: [completed or running action]; Next: [next action]
```

Send the same compact progress update to the user-facing main thread. Emit a heartbeat at least every 60 seconds while an agent, test, or build is still running.

## Isolation rule: fresh context for every task role

Use fresh, separate context windows/threads; never reuse an agent context across roles or tasks.

For each plan step:

1. Start **one new, dedicated `code-task-generator` context** for that plan step only. Give it the approved plan path, the exact step number, the task-artifact directory, and the governing artifacts. It must generate the required `stepNN` task files and then finish. Do not use its context for implementation.
2. The main thread reviews every generated task for plan scope, acceptance criteria, references, test requirements, and non-overlap. Correct only task artifacts before implementation if needed.
3. For **each generated code task**, start **one new, dedicated `code-assist` context** with that task file and the governing artifacts. The `code-assist` agent must implement only that task, follow RED → GREEN → REFACTOR, update its task record, run its required tests, and finish. Do not carry its chat context into the next task.
4. Use a new implementation context for the next generated task, even when it is in the same plan step.

If this Codex CLI environment cannot start separate contexts/agents, stop and report that limitation. Do not silently have the orchestration context perform code-task generation or `code-assist` work itself.

Require every dedicated-agent handoff to contain exactly:

```text
Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.
```

Run code-editing contexts sequentially. Do not overlap writers. Allow one initial implementation attempt and at most two fresh-context remediation attempts per task. Do not rerun an unchanged failing command more than once. Stop with captured evidence after the retry limit or 20 minutes without substantive progress.

## Plan-step protocol

### Step 1: Backward-compatible circle payload contract

Generate Step 1 task files, review them, then run a dedicated `code-assist` context for each task. Preserve positional rectangle callers while accepting a stable-ID `shape="circle"` form with centre `x/y`, `radius`, `thickness`, `color`, `fill`, and `ttl`. Do not add rendering in this step.

Acceptance evidence includes exact emitted circle payload fields, unchanged existing positional rectangle payload behavior, and stable ID/TTL behavior. Run the focused tests stated in the plan before advancing.

When complete, mark Stages 1.1 and 1.2 as `Completed`, mark Phase 1 `Completed`, check Step 1, and append exact results to the plan’s `Implementation Results` section.

### Step 2: Client normalization, validation, and storage

Generate/review Step 2 task files in a fresh code-task-generator context, then implement each task in a separate fresh `code-assist` context. Preserve circle fields through raw normalization, validate positive numeric radius/thickness in the centralized client path, log and drop invalid geometry before any same-ID store mutation, store valid first-class circle items, and update dedupe snapshots.

Use unit tests for pure normalization/storage. Confirm valid storage, transparent fill, replacement/TTL, radius/thickness rejection with warning/no mutation, and unchanged rectangle/vector behavior.

When complete, mark Stages 2.1 and 2.2 and Phase 2 `Completed`, check Step 2, and append exact results.

### Step 3: Transform-aware PyQt circle rendering

Generate/review Step 3 task files in a fresh code-task-generator context, then run each implementation task in its own fresh `code-assist` context. Add a dedicated opacity-aware circle paint command and render dispatch. Derive the square `center ± radius` and reuse the established rectangle/group/viewport transform flow. Render only through `QPainter.drawEllipse` with the requested pen width, stroke colour, and fill behavior. Do not alter rectangle/vector rendering contracts or global render hints.

Use unit tests for paint-command behavior and render integration. With GUI dependencies enabled, prove `drawEllipse` arguments, opacity behavior, group/anchor/cycle bounds, and rectangle/vector regressions. Capture a safe local screenshot of the documented demo if the existing environment can run it; otherwise record why it is unavailable.

When complete, mark Stages 3.1 and 3.2 and Phase 3 `Completed`, check Step 3, and append exact results.

### Step 4: Harness wiring and documentation

Generate/review Step 4 task files in a fresh code-task-generator context, then run each implementation task in its own fresh `code-assist` context. Add a harness test for raw/TCP circle publication and invalid geometry behavior. Update public shape, raw payload, getting-started, FAQ/concepts, and rendering-pipeline documentation so that examples match the tested API and state mapping semantics.

Because this step touches runtime ingestion/wiring, it requires at least one `harness` test plus unit coverage. No live EDMC, OAuth, external API, or upload action is authorized; use the existing harness and fake adapters only.

When complete, mark Stages 4.1 and 4.2 and Phase 4 `Completed`, check Step 4, and append exact results.

### Step 5: Regression evidence and release-quality review

Generate/review Step 5 task files in a fresh code-task-generator context, then run each task in its own fresh `code-assist` context. Execute the Python baseline check, focused/expanded tests, GUI-enabled tests, lint, type check, and `make check` as documented by the plan and `AGENTS.md`. Record exact command text, outcomes, skips, and reasons.

Review the scoped diff for behavior drift. Recheck EDMC compliance requirements relevant to changed plugin code. Do not update a version, package a release, publish artifacts, or push. If a failure cannot be resolved in the permitted remediation attempts, leave the plan incomplete and stop with evidence.

When complete, mark Stages 5.1 and 5.2 and Phase 5 `Completed`, check Step 5, and append exact results.

## Validation and completion criteria

For every task and step:

- Choose and document the test type before editing: unit for pure logic; harness for EDMC lifecycle/hook wiring; both for mixed work.
- Run focused tests before broader checks.
- Run the headless suite after each milestone and the GUI-enabled suite when rendering/wiring work is complete.
- Run `python scripts/check_edmc_python.py`, lint, type check, and `make check` before calling the work complete.
- Treat tests as safety checks, not authorization for external operations.
- Scan changed text artifacts, logs, and any screenshot for credentials/secrets before reporting.
- Update the plan phase table and stage rows in numerical order. Never mark a stage or plan step complete without its acceptance evidence.

Before final completion, perform an independent main-thread review of the scoped diff, plan status, generated code tasks, execution dashboard, tests, and documented demo. Preserve the clean separation between task-generator contexts and code-assist contexts.

## Final report

Report completed and incomplete plan steps, demos, changed files, generated code-task artifacts, exact validation evidence, commits (if any), manual actions remaining, known limitations, and any user decisions still needed. A successful implementation or test run never authorizes real external actions.
