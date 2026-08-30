# Autonomous in-session implementation goal: pixel-width circle strokes

## Objective

Implement the approved plan so an overlay circle with `thickness=1` uses a
one-pixel logical Qt pen at Fit/Fill scales 0.5, 1.0, and 2.0, matching the
legacy vector line. Explicit rectangle thickness must remain viewport-scaled.

This prompt is for the current in-session agent environment. Do not invoke
Codex CLI or create an external orchestration process.

## Scope and authority

- Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`
- Approved plan: `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/plan.md`
- Design: `docs/plans/2026-08-29-circle-thickness-pixel-width/design/detailed-design.md`
- Code findings: `docs/plans/2026-08-29-circle-thickness-pixel-width/research/existing-code.md`
- Requirements: `docs/plans/2026-08-29-circle-thickness-pixel-width/idea-honing.md`
- Governing instructions: `AGENTS.md`
- Generated tasks: `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/tasks/`
- Task records: `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/task-records/`
- Dashboard: `docs/plans/2026-08-29-circle-thickness-pixel-width/implementation/execution-status.md`

Standing approval covers only in-scope, workspace-local source, tests,
task artifacts, and non-destructive test/lint/type-check commands. Do not make
network calls or external writes.

### Non-negotiable Git rule

**Do not commit this work.** Also do not stage, push, amend, reset, restore,
stash, clean, checkout, switch branches, rebase, merge, or otherwise alter
Git history or the index. Use read-only Git status/diff checks only. Preserve
all pre-existing work exactly as found.

### Scope boundary

Change only circle stroke-width resolution and focused coverage. Do not change
circle geometry/radius, Fill grouping, transform metadata, `send_shape`
arguments, payload validation, payload inspector code, rectangle behavior,
vector behavior, line-width configuration, or public APIs. Stop and ask the
user if the approved plan cannot be fulfilled without a new product decision.

## Start and restart recovery

Before every initial run or restart:

1. Read all governing and planning artifacts above.
2. Inspect `git status --short`, `git diff --check`, the scoped diff, plan
   checklist, task artifacts, task records, validation logs, and dashboard.
3. Reconcile claims with filesystem evidence; resume at the first incomplete
   or unverified task rather than trusting stale status.
4. Update the dashboard before and after every step. Use stages `1.1`, `2.1`,
   `2.2`, `2.3`, and `3.1`; mark a phase complete only when all its stages are
   complete.

Send a concise main-thread update before and after every task generation,
implementation, validation, and review, plus a heartbeat at least every 60
seconds while a subagent or long command is running. Format each update as:

`Step: <number>; Task: <id>; Phase: <planning|implementation|validation>; Action: <action>; Next: <next action>.`

## Isolated-context execution protocol

Every code task must run in its own **fresh context window**. Never reuse a
code-writing or validation subagent for a later task. Run worktree-writing
agents sequentially.

For each plan step, perform this exact sequence:

1. Spawn one fresh `code-task-generator` subagent to create exactly one task
   breakdown under `implementation/tasks/stepNN/`. It reads the approved plan
   and design but makes no source or test edits.
2. Main thread reviews that generated task for scope, target paths, test type,
   no-commit compliance, and preservation of unrelated work.
3. Spawn a different fresh `code-assist` subagent to execute only that reviewed
   task. It must read the code-assist skill and write its record under
   `implementation/task-records/stepNN-task01/`.
4. Main thread independently reviews the diff, task handoff, command results,
   and worktree safety before advancing.

Each subagent receives only its immediate task. Its handoff must use exactly
these headings: `Status; Files changed; Validation commands/results; Decisions;
Risks; Next exact action.`

Allow one implementation attempt and at most two remediation attempts, each in
a new fresh context, for any task. Never rerun an unchanged failing command
more than once. Stop with evidence after the retry limit or 20 minutes without
substantive progress. A passing test never authorizes a commit or scope change.

## Required task sequence

### Step 1 — establish separate contracts

Generate and execute a test-first task limited to
`overlay_client/tests/test_render_surface_mixin.py` plus its task record.

- Split the shared shape scaling assertion into rectangle and circle contracts.
- Rectangles: `thickness=2` remains scale-aware, yielding 1, 2, and 4 at
  scales 0.5, 1.0, and 2.0.
- Circles: `thickness=1` must yield 1 at those scales; add a non-unit case such
  as `thickness=3` at scale 2.0 yielding 3.
- Run `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py -k thickness`.
- The new circle assertions are expected to be red. Record that exact result
  and do not modify production source in Step 1.

### Step 2 — implement the pixel policy seam

Generate and execute a fresh task limited to `overlay_client/render_surface.py`,
`overlay_client/tests/test_render_surface_mixin.py`, and its task record.

- Add a clearly named explicit pixel-width field to `_StrokeWidthSpec`; do not
  overload the rectangle default-width field.
- Resolve the pixel policy as a rounded, minimum-one Qt width without
  multiplying it by `group_ctx.scale`.
- Preserve the logical-width branch exactly for rectangles.
- Wire only `_build_circle_command()` to pass validated circle thickness using
  the new pixel policy.
- Do not change geometry, grouping, transforms, payload validation, public API,
  vector rendering, or `render_config.json`.
- First rerun the Step 1 focused command and require green, then run the full
  `test_render_surface_mixin.py` module with `PYQT_TESTS=1` and `git diff --check`.

### Step 3 — validate integrated behavior

Generate and execute a fresh validation-only task. It must not edit source or
tests. If it finds a scoped defect, stop and request direction instead of
fixing it during validation.

Run all of these commands exactly:

- `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_render_surface_mixin.py tests/test_legacy_processor.py tests/test_edmcoverlay_shapes.py`
- `make check`
- `git diff --check`
- `git status --short`

Review the scoped diff and confirm behavior is confined to circle stroke width
and its tests. Report all pass, fail, and skip results exactly. A manual visual
overlay comparison is not authorized by this prompt; list it as a follow-up.

## Completion criteria and final report

Report completion only when circle `thickness=1` is one pixel at all three
scales; a non-unit circle thickness is unscaled; rectangle thickness still
scales; focused and broad validation pass (or out-of-scope failures are proven
and reported); `git diff --check` passes; and no prohibited Git operation
occurred.

Final report must list completed steps, changed source/test/doc files, exact
test commands and outcomes, manual verification remaining, known limitations,
and an explicit confirmation that no commit was made.
