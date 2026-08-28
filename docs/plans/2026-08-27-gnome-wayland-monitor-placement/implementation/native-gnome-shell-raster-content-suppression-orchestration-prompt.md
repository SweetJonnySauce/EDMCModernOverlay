# Autonomous Implementation Orchestration: Native GNOME Shell-Raster Content Suppression

## Scope and authority

Repository: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`

Authoritative implementation plan:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-shell-raster-content-suppression-plan.md`

Read these governing artifacts in full before each start or restart:

- `AGENTS.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/native-gnome-shell-raster-content-suppression-lessons.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/native-gnome-shell-raster-content-suppression.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-shell-raster-content-suppression-plan.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-shell-raster-content-suppression-execution-status.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/iteration-checklist.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/progress.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-fullscreen-focus-visibility-regression-plan.md`

Create task artifacts beneath:
`docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/code-assist/native-gnome-shell-raster-content-suppression/`

This prompt authorizes ordinary, in-repository implementation work: source,
tests, fixtures, status/planning documentation, and non-destructive test/build
commands using the existing `overlay_client/.venv`. It does not authorize any
write outside this repository, credential use, real account/API actions, live
D-Bus commands, GNOME Shell/extension reload, EDMC or Elite startup, Git
configuration changes, resets, pushes, history rewrites, or broad deletion.

**No-commit rule:** Never create a commit. Do not push. Leave all completed
work uncommitted for explicit user inspection and approval. Do not stage files
unless a local, non-commit verification strictly requires it; if so, unstage
them before the final report.

**Manual-only live gate:** Tests using fake helpers and source contracts are
authorized. Do not run the live GNOME Wayland matrix, reload an extension, or
issue a D-Bus command. Stop after automated validation and ask the user for
explicit approval before any live action.

## Safety invariants

The previous direct-authorization approach is invalid. Never map the unchecked
preference directly to `allow_unfocused_target=false` for an eligible native
GNOME fullscreen Shell-raster target.

During an ordinary focus transition, retain the selected fullscreen actor's
identity, parentage, session, monitor placement, stacking,
non-reactivity/click-through, and timeout state. Do not call
`_clearShellRasterFrame`, `_suspendShellRasterFrame`, actor `hide`, detach,
destroy, or the `target_not_focused` path to implement ordinary focus-loss
content suppression. Existing cleanup for genuine target/session/lifecycle loss
must remain unchanged.

Preserve the `fix219` boundary. Generic follow/runtime code may express a
neutral `visible`/`suppressed` intent only. It must not import GNOME helper
implementations/protocol types or dispatch by raw backend/helper enum. The
native GNOME bundle owns helper capability checks and protocol mapping.

Unsupported, malformed, older, or failing helper capability must retain the
stable **visible** state with a diagnosable degraded result. It must never fall
back to focus-risk actor suspension, actor recreation, or a managed-PyQt
presenter swap for a valid native fullscreen route.

## Start and restart recovery

Before editing on every initial run and restart:

1. Read the governing artifacts and relevant source/tests.
2. Inspect `git status --short`, `git diff`, generated task artifacts, handoffs,
   validation logs, plan checkboxes, phase tables, and the status dashboard.
3. Reconcile all claims with current source and tests. Resume at the first
   incomplete or unverified action; never trust a stale completion marker.
4. Update the dashboard and plan/progress stages only after concrete evidence.

Before and after each plan step, task generator, code-assist context,
remediation, test/build, and review, send exactly:

`Step: <n>; Task: <id>; Phase: <planning|implementation|validation|demo>; Action: <running or completed action>; Next: <next action>.`

While a command or subagent runs, send a heartbeat at least every 60 seconds.
Every task-generator and code-assist handoff must contain exactly:
`Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`

## Context isolation and execution protocol

Execute one plan step at a time. Never overlap code-writing contexts.

For each of Steps 1–3:

1. Spawn one dedicated `code-task-generator` context. It reads only the
   current step plus relevant source/tests and creates scoped code-task files.
   It must not edit production code.
2. In the main context, review each generated task against this orchestration,
   the design, current source, and the `fix219` boundary. Reject/revise any task
   proposing direct focus-risk authorization, ordinary-focus actor lifecycle
   operations, or unrelated refactoring.
3. For every accepted task, spawn exactly one fresh `code-assist` context. It
   alone may edit code for that task. Require strict RED → GREEN → REFACTOR,
   a behavior-scoped diff, tests selected under `AGENTS.md`, and its own
   progress/handoff artifact.
4. In the main context, independently inspect the diff and validation evidence.
   Update the dashboard, plan checkboxes, and phase/stage tables only when the
   accepted task's criteria are proved.

Run task contexts sequentially. Allow one initial implementation and at most
two fresh-context remediations per task. Never rerun an unchanged failing
command more than once. Stop with evidence after that retry limit or after 20
minutes without substantive progress.

For Step 4, spawn a dedicated `code-task-generator` context to confirm whether
there is a code task. If not, record that conclusion, then run only automated
validation in the main context. It does not authorize the manual live matrix.

## Step-specific direction

### Step 1 — neutral intent and capability boundary

Add neutral `visible`/`suppressed` content intent at the existing policy seam
and native-GNOME-owned optional request/result capability handling. Do not
change helper actor behavior. Preserve the restored fullscreen/full-monitor
actor-continuity authorization. Add unit and architecture-boundary coverage for
intent resolution, request serialization, and supported/unsupported/malformed/
absent capability responses. Unsupported helpers preserve current visible
behavior.

### Step 2 — helper-side reversible content suppression

Behind the explicit capability gate, add one helper-owned operation that
suppresses/restores content for the existing single-frame and region-raster
actors. Prove every `visible -> suppressed -> visible` cycle retains identity,
parentage, session, placement, stacking, non-reactivity, and timeout state.
Source/contract tests must prove ordinary-focus suppression cannot call the
focus-risk clear/suspend/hide/detach/destroy operations.

If no reversible content mechanism can meet those invariants in the available
test environment, stop before Step 3 and report the blocker. Do not replace it
with risky actor lifecycle manipulation.

### Step 3 — preference wiring in the native GNOME bundle

Feed the existing debounced preference decision into the native GNOME bundle
only. With a supported helper, map unchecked-unfocused to `suppressed` and
checked-unfocused to `visible`, retaining actor-continuity authorization for an
eligible fullscreen target. On focus return request `visible` on the same
actor. Unsupported helpers stay visible with a gated diagnostic.

Cover focused, unchecked-unfocused, checked-unfocused, focus-return,
unsupported-helper, hard-target-loss, presenter-transition, follow-surface,
and backend-boundary cases. Do not change X11, xcompat, windowed managed-PyQt,
overview, target-loss, placement, or click-through behavior.

### Step 4 — automated validation and manual handoff

Use the project environment exactly:

```bash
source overlay_client/.venv/bin/activate
PYQT_TESTS=1 python -m pytest \
  overlay_client/tests/test_gnome_helper_presentation_runtime.py \
  overlay_client/tests/test_gnome_shell_helper_extension_source.py \
  overlay_client/tests/test_gnome_shell_helper_presentation_state.py \
  overlay_client/tests/test_backend_presentation_policy.py \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_presentation_transition.py \
  overlay_client/tests/test_backend_architecture_boundary.py -q
make PYTHON="$VIRTUAL_ENV/bin/python" check
make PYTHON="$VIRTUAL_ENV/bin/python" test
```

Record exact pass/fail/skip outcomes. Run `git diff --check`, inspect the
scoped diff, update the iteration checklist, and perform the EDMC compliance
review required by `AGENTS.md` with a clear yes/no answer for each applicable
category.

Then stop. Present this manual matrix for user authorization: unchecked/focused
visible; unchecked/unfocused content suppressed with actor attached and no
flash/black screen; unchecked/focus-return restores without remap/recreation;
checked/unfocused remains visible; repeated focus cycles stay stable; and
two-monitor fullscreen placement stays correct.

## Final report

Only mark Steps 1–3 complete when independent review and focused tests pass.
Step 4 remains awaiting user live acceptance until separately authorized.

Report completed/deferred steps; dashboard and plan status; all changed and
generated-task files; exact tests and results; proof of actor-continuity and
`fix219` boundary preservation; no-commit state; the manual live actions still
required; EDMC compliance yes/no results; and known limitations, including the
stable-visible fallback for unsupported helpers. Never claim live acceptance or
create a commit without a new explicit user instruction.

