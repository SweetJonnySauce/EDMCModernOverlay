# Implementation Orchestration: stable Fill-mode grouping for circle payloads

## Scope and authority

Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`

Required branch: `fix/circle-group-bounds`

Approved design: `docs/plans/2026-08-29-circle-group-bounds/design/detailed-design.md`

Approved plan: `docs/plans/2026-08-29-circle-group-bounds/implementation/plan.md`

Research and requirements: `docs/plans/2026-08-29-circle-group-bounds/{rough-idea.md,idea-honing.md,research/existing-code.md,summary.md}`

Governing instructions: `AGENTS.md`

Task artifacts: `docs/plans/2026-08-29-circle-group-bounds/implementation/tasks/`

Status dashboard: `docs/plans/2026-08-29-circle-group-bounds/implementation/execution-status.md`

Implement the approved plan only. The desired outcome is radius-aware group
bounds for `LegacyItem(kind="circle")` in the Fill-mode grouping path, with
tests proving normal and transformed circle geometry. Do not modify BioScan,
the public `send_shape` API, legacy payload schema, or the circle paint command.

Standing authority covers ordinary workspace-local edits to the intended source,
tests, and plan execution records, along with non-destructive local tests,
linters, type checks, and builds. No live game, EDMC, network, credentials,
external service, installer, release, or package-install action is authorized.

### Mandatory Git and workspace safety

- **Do not commit, stage, push, amend, reset, checkout, switch, stash, clean,
  restore, or otherwise alter Git history or the index.** The user explicitly
  requires that all implementation changes remain uncommitted.
- Before every edit, inspect `git status --short` and the scoped diff.
- The workspace intentionally contains pre-existing uncommitted work. Preserve
  it exactly, including `version.py`, `utils/payload_inspector.py`,
  `tests/test_payload_inspector.py`,
  `docs/plans/2026-08-29-payload-inspector-circle-preview/`, and any changes
  outside this plan's circle-group-bounds paths.
- Stop and ask the user if the current branch is not `fix/circle-group-bounds`,
  an intended file overlaps an unexplained existing diff, the plan conflicts
  with governing instructions, or a required validation cannot be made green.

## Start and restart recovery

Before editing on the initial run and every restart:

1. Read every governing and approved artifact named above.
2. Inspect `git status --short`, relevant diffs, `execution-status.md`, plan
   checkboxes, task records, and validation logs.
3. Reconcile completion claims against source and test evidence. Resume at the
   first incomplete or unverified action; do not trust a stale status marker.
4. Confirm that the target is the pure helper
   `overlay_client/payload_transform.py::accumulate_group_bounds` and that
   `overlay_client/render_surface.py` remains the visual geometry reference.

Update `execution-status.md` before and after every plan step, code-task run,
test, build, and demo. Use this exact progress line in the interactive session:

`Step: [n]; Task: [id]; Phase: [planning|implementation|validation|demo]; Action: [completed/running action]; Next: [next action]`

Provide a heartbeat at least every 60 seconds while a test or subagent is
running.

## Fresh-context task protocol

Execute one approved plan step at a time. Do not overlap code-writing agents.

For each plan step:

1. In a **fresh, dedicated context/thread**, invoke one `code-task-generator`
   agent to create only that step's task breakdown under
   `implementation/tasks/stepNN/`. The main thread must review the generated
   task for scope before implementation.
2. For each generated task, invoke one **fresh, dedicated context/thread**
   `code-assist` agent in auto mode. Each agent gets its own documentation and
   log directory under `implementation/task-records/stepNN-taskMM/` and follows
   strict RED → GREEN → REFACTOR.
3. Run writing agents sequentially. Do not reuse an implementation agent's
   context for a later task, step, remediation, or validation task.
4. Require each task handoff to contain exactly:
   `Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`
5. The user's no-commit rule overrides any subagent workflow that normally
   commits. No subagent may stage or commit.

Allow one initial implementation attempt and at most two fresh-context
remediation attempts per task. Do not rerun an unchanged failing command more
than once. Stop with evidence after the retry limit or 20 minutes without
substantive progress.

## Step-specific acceptance criteria

### Step 1 — normal circle bounds

- Add a focused unit test in `overlay_client/tests/test_payload_bounds.py`.
- A circle centred at `(100, 200)` with radius `25` must contribute bounds
  `(75, 175)` through `(125, 225)`.
- The test must fail before implementation because the current generic fallback
  contributes only the centre point.
- Use unit tests only; no EDMC lifecycle or harness test is needed because the
  behavior is deterministic helper logic.

### Step 2 — transformed circle bounds

- Add the smallest circle branch to `accumulate_group_bounds()`.
- Derive `x-radius`, `y-radius`, `x+radius`, and `y+radius`; transform all four
  corners through the existing local transform helper; aggregate their min/max.
- Add a transformed-circle unit test that would fail if only the centre were
  transformed.
- Preserve the existing message, rectangle, vector, invalid-value, and paint
  behavior. Do not touch the payload-inspector-preview changes already in the
  working tree.

### Step 3 — integration validation

- Review the helper against the existing renderer's `x-radius`, `y-radius`,
  `diameter=2*radius` calculation.
- Verify the corrected helper is consumed by `FillGroupingHelper.prepare()`
  without API changes.
- Demonstrate locally through deterministic tests that repeated group-bound
  preparation for an unchanged circle yields identical bounds; do not launch a
  live game or EDMC instance.

## Validation and reporting

Use the existing environment; do not install dependencies. Run, in order:

1. `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_payload_bounds.py`
2. Relevant focused grouping/render tests discovered during the task.
3. `make check`

After each task, perform an independent main-thread review of its scoped diff,
test results, unowned-file preservation, and documentation updates. Scan
changed text artifacts and logs for secrets. Record exact commands and
pass/fail/skip results in the task record and `execution-status.md`.

## Stop conditions

Stop and request user direction before any external write, credential or account
access, live EDMC/game verification, dependency installation, destructive
command, scope expansion, unresolved test failure, attempt to change a
pre-existing unrelated file, or any Git staging/commit action.

## Final report

Report completed steps and their demos; files changed; generated task and
handoff artifacts; exact validation commands/results; the fact that no commit
was created; manual verification still recommended; and known limitations.
Successful tests do not authorize a commit, push, release, or external action.
