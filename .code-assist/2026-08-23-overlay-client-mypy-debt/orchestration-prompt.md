# Implementation Orchestration: Overlay Client Mypy Debt

## Goal

Complete the approved behavior-preserving overlay-client type-cleanup plan. Make
`python -m mypy overlay_client` pass, then add `overlay_client` to the default mypy target only
after that directory-wide check is green. Preserve the separate fix219 X11 surface-clear repair.

## Scope and authority

Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`

Approved plan: `.code-assist/2026-08-23-overlay-client-mypy-debt/plan.md`

Governing artifacts:

- `AGENTS.md`
- `.code-assist/2026-08-23-overlay-client-mypy-debt/context.md`
- `.code-assist/2026-08-23-overlay-client-mypy-debt/plan.md`
- `.code-assist/2026-08-23-overlay-client-mypy-debt/progress.md`
- `.code-assist/2026-08-21-fix219-x11-surface-artifacts/` (the independent X11 repair records)
- `pyproject.toml` and `Makefile`

Task-artifact root: `.code-assist/2026-08-23-overlay-client-mypy-debt/`

Status dashboard: `.code-assist/2026-08-23-overlay-client-mypy-debt/execution-status.md`

The approved plan authorizes ordinary, in-scope local changes: workspace-local source, tests,
documentation, and existing build metadata; non-destructive checks, formatters, and tests; and
normal use of the already-created virtual environment. Do not commit, stage, push, initialize a
repository, reset, clean, bulk-overwrite, install new dependencies, change CI beyond the planned
`pyproject.toml` typecheck target, use credentials, or perform live EDMC, Elite, X11, network, or
external-account actions.

Stop and ask the user before any destructive action, scope expansion, security concern, new
dependency, external write or live integration, a required product decision, or a runtime/lifecycle
ambiguity that cannot be modeled safely. A successful test never grants authority for a live X11
or game validation. Manual native-X11 validation remains outside this goal.

## Non-negotiable implementation constraints

- Preserve the intentionally dirty fix219 worktree. Do not reset it or absorb unrelated changes.
- Maintain the fix219 backend boundary: generic runtime/follow surfaces must not import
  compositor-specific presentation/helpers or dispatch presentation from raw backend/helper enums.
- Keep the shared overlay-state contract type-only. Do not alter the Qt MRO, initialization order,
  `super()` chain, timers, painting, focus, click-through, backend selection, or follow behavior.
- Preserve the clear-first transparent surface behavior and its tests in
  `overlay_client/tests/test_setup_surface.py`.
- Do not add blanket `ignore_errors`, broad `Any` declarations, or unexplained `# type: ignore`
  directives. A narrow ignore needs an adjacent reason and must be reviewed by the coordinator.
- Choose tests explicitly. Pure/runtime-helper behavior changes need focused unit tests; annotation-
  only changes use mypy RED/GREEN plus relevant regression tests. `load.py` is out of scope, so do
  not add harness tests unless the scope legitimately changes.
- Use `apply_patch` for edits. Record test commands, results, and meaningful skips.

## Start and restart recovery

Before editing, and again on every restart:

1. Read every governing artifact above, including the full `AGENTS.md`.
2. Inspect `git status --short`, the scoped diff, this plan, `progress.md`, all stage artifacts,
   `execution-status.md`, and validation logs.
3. Reconcile claims against the actual source and command output. Never trust a stale completion
   mark. Resume at the first incomplete or unverified stage.
4. Create or update `execution-status.md` with the current stage, active context, validation state,
   handoff path, blockers, and next exact action.

At least before and after every stage/context/test, update the dashboard using exactly:

`Step: [stage]; Task: [task-id]; Phase: [planning|implementation|validation|review]; Action: [running|completed action]; Next: [next exact action]`

While a command or context is running, provide a heartbeat at least every 60 seconds.

## Context isolation protocol — mandatory

**Each Code Assist task must run in its own fresh context window.** Do not reuse a Code Assist
context for a second stage or remediation attempt.

Run stages strictly serially. Never have two code-writing contexts active at the same time. The
orchestrator context is a coordinator/reviewer only: it reads the prior handoff and diff, updates
the dashboard, and then launches exactly one fresh context for the next stage. It must not silently
implement that stage itself.

For every stage below:

1. In a separate fresh planning context, use `code-task-generator` only for that one stage and
   save/review its concise task breakdown under
   `.code-assist/2026-08-23-overlay-client-mypy-debt/stage-<stage-id>-<slug>/`.
2. Review the generated task for plan scope before allowing implementation.
3. Open one new, dedicated `code-assist` context window for each generated task. The implementation
   context must read the governing artifacts and immediately preceding handoff, use strict
   RED → GREEN → REFACTOR where a behavior change is involved, and use only that stage directory
   for its notes and logs.
4. The stage context must update its `context.md`, `plan.md`, and `progress.md` before production
   edits, perform its focused validation, then leave a handoff with **exactly** these fields:

   `Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`

5. The coordinator independently reviews the scoped diff and handoff before it opens the next
   fresh context. It updates the top-level `progress.md` only after the actual evidence supports
   completion.

Allow one initial Code Assist implementation context and at most two fresh-context remediation
attempts per generated task. Never rerun an unchanged failing command more than once. Stop with
the failure evidence after the retry limit or 20 minutes without substantive progress.

## Required stage sequence

Run only the first unverified stage; do not pre-open later contexts.

| Stage | Fresh-context objective | Required proof before moving on |
| --- | --- | --- |
| 2.1 | Re-run and freeze the directory-wide mypy baseline; group failures into shared-state, pure-data, renderer, and integration families. | Exact command/output inventory and a scope-reviewed stage handoff; no code/config change merely to make the baseline smaller. |
| 2.2 | Add a centralized, annotation-only shared overlay-state contract while keeping ownership and initialization unchanged. | Mypy improvement for the targeted state family; no Qt/MRO/runtime lifecycle movement; focused affected tests. |
| 2.3 | Reconcile mixin declarations and `OverlayWindow` inheritance conflicts. | Targeted state-family mypy errors are green and offscreen Qt/follow tests pass. |
| 3.1 | Correct geometry, anchor, legacy/payload, and override container types conservatively. | Relevant unit tests plus the normal six-module mypy command (without `--follow-imports=skip`) improving; new unit coverage if a runtime helper behavior is corrected. |
| 3.2 | Correct renderer protocol, command-union, debug collection, and render-surface types. | Renderer/vector/debug tests plus mypy improvement; preserve rendering semantics. |
| 3.3 | Correct launcher/integration annotations. | Affected client tests plus mypy improvement; no runtime launch/focus behavior change. |
| 4.1 | Resolve remaining directory-wide client errors. | `source overlay_client/.venv/bin/activate && python -m mypy overlay_client` exits zero. |
| 4.2 | Only after 4.1 is independently confirmed green, add `overlay_client` to `[tool.mypy].files`. | `source overlay_client/.venv/bin/activate && python -m mypy` exits zero. |
| 4.3 | Perform final regression, hygiene, scoped review, and EDMC compliance review. | Required validation below passes; compliance report gives clear yes/no for every `AGENTS.md` compliance item. |

If a command reveals errors outside this bounded inventory, document them as new inventory, do not
suppress them, and stop for plan review before scope expands.

## Validation requirements

Record exact commands and outcomes in the active stage log. Run the smallest relevant subset
after each changed family and, at the required milestones, run:

For Stage 3.1, its focused source check must retain normal import following; the `skip` mode can
mask type propagation in `plugin_overrides.py` and `transform_helpers.py` and cannot be its GREEN
gate:

```bash
source overlay_client/.venv/bin/activate && python -m mypy \
  overlay_client/follow_geometry.py \
  overlay_client/anchor_helpers.py \
  overlay_client/legacy_processor.py \
  overlay_client/plugin_overrides.py \
  overlay_client/payload_model.py \
  overlay_client/transform_helpers.py
```

```bash
source overlay_client/.venv/bin/activate && python -m mypy overlay_client
```

```bash
source overlay_client/.venv/bin/activate && QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 python -m pytest \
  overlay_client/tests/test_setup_surface.py \
  overlay_client/tests/test_repaint_debounce.py \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_vector_renderer.py \
  overlay_client/tests/test_transform_helpers.py -q
```

```bash
source overlay_client/.venv/bin/activate && python -m ruff check overlay_client
```

After Stage 4.2:

```bash
source overlay_client/.venv/bin/activate && python -m mypy
```

At Stage 4.3:

```bash
source overlay_client/.venv/bin/activate && make check
```

```bash
git diff --check
```

Do not run a live game, a native X11 smoke test, or a full GUI test without explicit user approval.
If GUI dependencies prevent the offscreen suite, record the exact blocker and pass/skip reason;
do not claim full validation.

## Completion and final report

Finish only when every stage is evidenced, reviewed, and the dashboard/progress records agree
with the actual worktree. The final report must include:

- each completed stage and its isolated Code Assist artifact directory;
- changed production, test, configuration, and documentation files;
- tests added/updated and exact commands with pass/fail/skip results;
- the before/after mypy evidence and confirmation that default mypy now covers `overlay_client`;
- a scoped-diff review confirming the X11 repair and fix219 backend boundary were preserved;
- a yes/no answer for every EDMC compliance item in `AGENTS.md`, including any required follow-up;
- no commit/push performed; and
- remaining manual work: native-X11/long-duration game validation of the independent artifact fix.
