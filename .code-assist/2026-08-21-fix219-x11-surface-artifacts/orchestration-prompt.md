# Implementation Orchestration: fix219 native-X11 surface artifacts

## Scope and authority

Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`

Approved plan: `.code-assist/2026-08-21-fix219-x11-surface-artifacts/plan.md`

Task context and dashboard:

- `.code-assist/2026-08-21-fix219-x11-surface-artifacts/context.md`
- `.code-assist/2026-08-21-fix219-x11-surface-artifacts/progress.md`
- `.code-assist/2026-08-21-fix219-x11-surface-artifacts/execution-status.md` (create and maintain)

Governing artifacts:

- `AGENTS.md`
- `pyproject.toml`
- `Makefile`
- `docs/compliance/edmc_compliance.md`
- `docs/planning/2026-07-17-fix219-architecture-convergence/iteration-checklist.md`

Objective: fix the native-X11 transparent-overlay surface artifact where stale, duplicated tiles,
including old game-scene pixels, appear after long-running play and window/focus movement. The
first implementation must use the plan's narrow, reversible repair: establish a transparent ARGB
clear before every normal overlay paint, sharing the existing suppressed-content clear behavior.

This plan authorizes ordinary, in-scope workspace-local changes only: client code, tests, task
documentation, and non-destructive validation. It does **not** authorize changing overlay
settings, helper configuration, live EDMC/Elite state, window-manager settings, external APIs,
network activity other than approved dependency/package registries and primary documentation,
commits, pushes, PRs, resets, destructive commands, or changes outside this repository.

Do not treat a passing test as authorization for native-X11 live work. Manual X11 validation stays
manual and user-gated. Do not run a long game session, launch/stop Elite or EDMC, change focus,
or alter window-manager state. Never collect or write window IDs, process IDs, command lines,
window titles, raw environment dumps, raw journal text, or screenshots containing private data.

Preserve the intentionally dirty fix219 worktree. Do not reset, discard, bulk-stage, commit, or
modify unrelated files. Do not add compositor-specific helper imports or enum dispatch outside
`overlay_client/backend/`; the generic paint helper must remain backend-neutral.

## Start and restart recovery

Before editing, and again after every restart:

1. Read every governing artifact and the three task documents above.
2. Inspect `git status --short`, targeted diffs, and prior validation evidence. Treat all existing
   changes as user work unless this task's dashboard identifies them.
3. Reconcile plan/progress/dashboard status. Resume at the first incomplete or unverified stage;
   never trust an unverified completion claim.
4. Create/update `execution-status.md` with a phase table and a stage checklist. Preserve the
   existing plan's numbered stages.

Send a concise update before and after every stage, test, or review, and at least every 60 seconds
while a command runs, using exactly:

`Step: [n]; Task: [id]; Phase: [planning|implementation|validation]; Action: [completed/running action]; Next: [next action]`

## Execute one stage at a time

### Stage 2.1 — RED tests

Use the repository's existing PyQt testing style. Add `pyqt_required` unit tests that initially
fail on the current normal paint path and prove:

- normal `paintEvent` clears transparent pixels before `_paint_overlay`;
- the painter is restored to ordinary source-over composition before active drawing;
- the backend-suppressed path still clears once and skips `_paint_overlay`;
- paint-count behavior is unchanged; and
- repeated normal paints cannot retain prior-frame regions at the test seam.

Use a small test seam around painter operations rather than brittle full-screen snapshots. This is
a UI-local behavior change, so unit tests are required. Do not add a harness test unless the
touchpoints expand to `load.py` or lifecycle wiring.

Run the focused RED test and record the expected failure. If testability requires an extracted
helper, it must remain private, backend-neutral, and narrowly scoped to the transparent overlay
surface.

### Stage 2.2 — GREEN repair

Implement one private helper used by both normal and backend-suppressed paint paths. It must clear
the overlay's own transparent surface before a new frame and restore the painter composition mode
before current-frame drawing. Do not disable `WA_NoSystemBackground`, transparent input, follow
mode, native X11 support, or `X11BypassWindowManagerHint` in this first patch.

Keep changes behavior-scoped and readable. Do not add render-loop logging or diagnostics in
release paths. Preserve `super().paintEvent`, antialiasing, content-suppression semantics, and
paint metric accounting unless the tests establish a necessary correction.

Run focused tests until GREEN, then perform a scoped diff review for accidental fix219 boundary
or behavior changes.

### Stage 2.3 / 4.1 — automated validation

Run and record exact outcomes for:

```bash
source overlay_client/.venv/bin/activate && python -m pytest \
  overlay_client/tests/test_setup_surface.py \
  overlay_client/tests/test_repaint_debounce.py \
  overlay_client/tests/test_follow_surface_mixin.py -q

source overlay_client/.venv/bin/activate && python -m ruff check \
  overlay_client/overlay_client.py \
  overlay_client/tests/test_setup_surface.py

source overlay_client/.venv/bin/activate && python -m mypy overlay_client/overlay_client.py

source overlay_client/.venv/bin/activate && make check
git diff --check
```

Use the project's GUI-capable test environment as required. If a command is unavailable or fails
for a pre-existing/environmental reason, do not loop on it: capture the exact evidence, make one
meaningful diagnosis/remediation attempt, then stop and report the blocker.

### Stage 3 — manual native-X11 validation gate

After automated validation, stop and ask the user for explicit approval before performing or
requesting any native-X11 test. The manual test must verify overlay visibility, click-through,
following, bounded move/focus stress, and absence of stale/duplicated tiles. A representative
extended game session remains manual-only. Record only sanitized pass/fail facts and duration.

If the artifact persists after the clear repair, do not change `X11BypassWindowManagerHint` in
this run. Stop with evidence and propose a separate reversible experiment covering stacking,
focus, click-through, and follow behavior.

## Validation and completion

Before reporting implementation complete:

1. Confirm every automated acceptance criterion and Stage 2 checklist item has evidence.
2. Update `progress.md` and `execution-status.md` in phase/stage order, including test files
   changed, exact commands, pass/fail/skip results, risks, and the manual gate still outstanding.
3. Review the scoped diff and verify no unrelated dirty work was changed.
4. Include a clear EDMC compliance assessment for the touched scope: core/API alignment,
   logging/versioning, responsive/Tk-safe behavior, preferences/UI, and dependencies/debug HTTP.
5. Do not mark the manual X11 criterion complete without user-performed evidence.

## Final report

Report: completed stages; changed files; test files added/updated; exact validation results;
manual X11 actions remaining; known limitations; rollback (revert only the narrow surface-clear
change); and confirmation that no commit/push/external or live-game action occurred.
