# Circle Feature / Backend Refactor Merge Progress

## Current State

The no-commit merge remains active on `backend-refactor-implementation` with
source `feature/circle-shape-pyqt-rendering`. At the latest verification,
`HEAD` was `44da98d`, `MERGE_HEAD` was `0d789cb`, and the active source merge
contained 71 staged files (4,871 additions and 100 deletions). Conflict
resolution and automated validation are complete: the user ran the GUI-enabled
`make check` in the host terminal successfully, and the authorized non-release
EDMC Python mismatch override passed with its expected warning. The user also
confirmed the rendering contract on X11. Native GNOME Wayland then placed the
overlay one monitor right before circle inspection. The user authorized merge
completion after research established that this is a separate backend-placement
defect, not a circle change; no Wayland rendering pass is claimed.

## Evidence Recorded

| Check | Result |
| --- | --- |
| Target branch state | Clean at assessment time; current commit `40d3a40`. |
| Source branch state | Circle feature tip `0d789cb`. |
| Active merge state | `backend-refactor-implementation` at `44da98d` with `MERGE_HEAD` `0d789cb`; 71 staged files, 4,871 additions, and 100 deletions. |
| Merge base | `8e375cc`. |
| Dry-run merge | Two textual conflicts: render surface and render-surface tests. |
| Managed configuration | Preserve target `overlay_groupings.json`; do not stage source change. |
| Phase 1 target tip | Verified local target `6d308e6df0107f440b601bfb571341e0286c1b80`; `origin/backend-refactor-implementation` remains `9856ff9fa066bf973f9f8b94b4454afbb006c60c`. |
| Phase 1 backup | `refs/backup/circle-feature-backend-merge/backend-refactor-implementation-20260827T163928Z` resolves to `6d308e6df0107f440b601bfb571341e0286c1b80`. |
| Automated merge validation | Mixed unit/harness pytest passed (100); host-terminal `make check` passed (1,662); staged whitespace, conflict-marker, scope, and grouping-exclusion checks passed. |
| Manual rendering validation | X11 passed by user report. Native GNOME Wayland blocked inspection by placing the overlay on the secondary monitor; research isolated it as a separate backend defect, and the user authorized the circle merge without a Wayland pass. |

## Execution Checklist

- [x] Assess branch divergence and three-way merge conflicts.
- [x] Decide grouping-configuration treatment.
- [x] Record architecture, conflict, and validation strategy.
- [x] Freeze and verify the target branch, including a local backup ref.
- [x] Start the non-committing merge and preserve the managed configuration.
- [x] Resolve and stage source/test conflicts.
- [x] Run automated validation gates.
- [x] Record manual overlay result and the separate native-Wayland blocker.
- [ ] Commit the reviewed merge.

## Commands to Record When Executed

Record the exact command and outcome for each merge, diff, test, and manual
overlay step below this section. Do not mark a phase complete until its stages
and required tests are complete.

### Documentation isolation

- `git status --short` confirmed that the only uncommitted paths were
  `docs/plans/2026-08-27-circle-feature-backend-merge/summary.md`, the
  execution dashboard, and the orchestration prompt. These plan artifacts are
  being committed separately before the merge begins.
- `git add ...` was blocked before staging: Git could not create
  `.git/index.lock` because the repository's Git metadata is read-only in this
  execution environment. No files were staged or committed.
- Git metadata write access was subsequently verified. The four in-scope plan
  artifacts were committed separately as `9d0f4fe`
  (`docs(plan): add circle merge orchestration`) before beginning merge work.

### Phase 1 / Stage 1.1 — failed first fresh-context preflight

- Fresh code-task-generator context created
  `implementation/tasks/step01/task-01-freeze-backend-baseline.code-task.md`.
- Fresh code-assist context attempted `git fetch origin` once. It failed with
  `Could not resolve host: github.com`; no backup ref, merge, staging, or
  managed-configuration change occurred.
- Local topology remains target `9856ff9fa066bf973f9f8b94b4454afbb006c60c`,
  source `0d789cbbea77dac500eb7b249d71df67c1dbde9c`, and merge base
  `8e375cce40acc0d9400bde43d6aa01070929adb4`; `MERGE_HEAD` is absent.
- No unit or harness tests ran because this is Git/documentation-only work.
  Residual risk: remote topology cannot be considered current until fetch
  succeeds. A single fresh remediation context may retry the failed command.

### Phase 1 / Stage 1.1 — retry limit reached

- A second fresh code-assist context performed the single permitted retry of
  `git fetch origin`; it failed with the same `Could not resolve host:
  github.com` DNS error.
- Its pre-fetch checks found a clean target worktree at
  `932ec52aa4312c459c3298219b69d9a523d1c715`, source
  `0d789cbbea77dac500eb7b249d71df67c1dbde9c`, merge base
  `8e375cce40acc0d9400bde43d6aa01070929adb4`, no staged paths, and no
  `MERGE_HEAD`.
- No backup ref, merge, staging, managed-configuration change, unit test, or
  harness test was performed. The unchanged failed fetch command must not be
  run again without an external network-state change.

### Post-block connectivity probe

- After a user-reported possible network recovery, the read-only command
  `git ls-remote --heads origin` was run once. It again failed with
  `Could not resolve host: github.com` for
  `https://github.com/SweetJonnySauce/EDMCModernOverlay.git`.
- This confirms the external DNS blocker remains; it did not modify refs,
  start a merge, or change the managed grouping configuration.

### Phase 1 / Stage 1.1–1.4 — final fresh remediation context

- The user subsequently ran `git fetch origin` successfully in their host
  terminal and reported zero output. The sandbox did not rerun `git fetch`,
  `git ls-remote`, or any other network command.
- Local verification commands were: `git branch --show-current`; `git status
  --short`; `git diff --cached --name-only`; `git rev-parse -q --verify
  MERGE_HEAD`; `git rev-parse HEAD`; `git rev-parse
  refs/remotes/origin/backend-refactor-implementation`; `git rev-parse
  refs/remotes/origin/feature/circle-shape-pyqt-rendering`; `git rev-parse
  feature/circle-shape-pyqt-rendering`; `git merge-base
  backend-refactor-implementation feature/circle-shape-pyqt-rendering`; and
  `git reflog show --date=iso-strict -n 3` for both origin refs.
- Results: target branch `backend-refactor-implementation`; no pre-documentation
  worktree or staged paths; `MERGE_HEAD` absent; target
  `6d308e6df0107f440b601bfb571341e0286c1b80`; origin target
  `9856ff9fa066bf973f9f8b94b4454afbb006c60c`; source and origin source
  `0d789cbbea77dac500eb7b249d71df67c1dbde9c`; merge base
  `8e375cce40acc0d9400bde43d6aa01070929adb4`. The origin reflogs show those
  current refs; source/base still match the assessment.
- `git log --oneline 9856ff9..HEAD` and `git diff --name-only 9856ff9..HEAD`
  showed only the explainable target-only merge-tracking documentation commits
  (`932ec52`, `bf0dd0b`, and `6d308e6`). Both merge-base ancestry checks
  succeeded.
- With guards satisfied and no existing backup ref, `git update-ref
  refs/backup/circle-feature-backend-merge/backend-refactor-implementation-20260827T163928Z
  6d308e6df0107f440b601bfb571341e0286c1b80` created the one required backup;
  `git rev-parse` and `git for-each-ref` verified that it resolves exactly to
  the target SHA.
- `git diff --exit-code -- overlay_groupings.json` and `git diff --cached
  --exit-code -- overlay_groupings.json` both succeeded. No merge, staging, or
  grouping-configuration modification occurred.
- Test selection: no unit or harness tests were added or run, because this task
  changes no executable behavior and only creates a Git ref plus tracking
  documentation. Residual risk: source/target topology can change after this
  preflight; the main orchestrator must repeat the non-network Step 2 guard
  before starting the merge.

### Phase 2 / Stages 2.1–2.3 — non-committing merge and inspection

- Immediately before the merge, local guards reported branch
  `backend-refactor-implementation`, empty `git status --short`, empty
  `git diff --cached --name-only`, absent `MERGE_HEAD` (`git rev-parse -q
  --verify MERGE_HEAD` exit 1), source
  `0d789cbbea77dac500eb7b249d71df67c1dbde9c`, merge base
  `8e375cce40acc0d9400bde43d6aa01070929adb4`, and backup ref
  `refs/backup/circle-feature-backend-merge/backend-refactor-implementation-20260827T163928Z`
  at `6d308e6df0107f440b601bfb571341e0286c1b80`. `HEAD` was
  `44da98dc171abc0636b37da10403ab80da23b170`; it is a descendant of the
  backup, and the three intervening commits (`adbdd59`, `1477fa2`, and
  `44da98d`) touch only the approved merge-tracking plan/progress/dashboard/task
  documentation.
- Ran exactly once: `git merge --no-commit --no-ff
  feature/circle-shape-pyqt-rendering`. It returned the expected automatic-merge
  failure with conflicts only in `overlay_client/render_surface.py` and
  `overlay_client/tests/test_render_surface_mixin.py`. No conflict was edited,
  resolved, or staged.
- Immediately after that command returned, ran exactly: `git restore
  --source=HEAD --staged --worktree overlay_groupings.json` (exit 0). Both
  `git diff --exit-code -- overlay_groupings.json` and `git diff --cached
  --exit-code -- overlay_groupings.json` exited 0; the grouping file appears in
  neither `git diff --cached --name-only` nor `git diff --cached --stat`.
- Full initial merge scope from `git status --porcelain=v1` / `git diff --cached
  --name-only`: 69 staged-or-unmerged paths, with a cached stat of 69 files,
  4,459 insertions, and 57 deletions. The paths are:

  ```text
  EDMCOverlay/edmcoverlay.py
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/design/detailed-design.md
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/idea-honing.md
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/code-assist/rectangle-miter-joins/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/code-assist/shape-gallery/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/code-assist/shape-stroke-thickness/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/{execution-status.md,orchestration-prompt.md,plan.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step01-task01-remediation2/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step01-task01/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step02-task01/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step02-task02/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step03-task01/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step03-task02/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step04-task01/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step04-task02/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step05-task01/{context.md,plan.md,progress.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step01/task-01-add-circle-compatibility-payload-contract.code-task.md
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step02/{task-01-preserve-circle-raw-normalization.code-task.md,task-02-validate-and-store-circle-items.code-task.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step03/{task-01-add-opacity-aware-circle-paint-command.code-task.md,task-02-add-circle-transform-and-render-dispatch.code-task.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step04/{task-01-prove-raw-tcp-circle-lifecycle.code-task.md,task-02-document-circle-shape-support.code-task.md}
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step05/task-01-run-release-quality-regression-review.code-task.md
  docs/plans/2026-08-26-circle-shape-pyqt-rendering/{research/payload-and-rendering.md,rough-idea.md,shape-stroke-thickness-prompt.md,summary.md}
  docs/{rendering-pipeline.md,testing.md}
  docs/wiki/{Concepts.md,FAQs.md,Getting-Started.md,send_raw-API.md,send_shape-API.md}
  overlay_client/{legacy_processor.py,paint_commands.py,render_surface.py}
  overlay_client/tests/{test_paint_commands.py,test_render_surface_mixin.py}
  tests/{test_edmcoverlay_shapes.py,test_harness_legacy_tcp_ingestion.py,test_legacy_processor.py,test_shape_gallery.py}
  utils/shape_gallery.py
  ```

- `git diff --name-only --diff-filter=U` reports exactly the two predicted
  unresolved paths: `overlay_client/render_surface.py` and
  `overlay_client/tests/test_render_surface_mixin.py`. `git diff --name-only`
  and `git diff --stat` report only those unmerged paths in the unstaged view;
  no additional conflict or unexpected non-documentation changed path was
  observed.
- The non-documentation marker scan `rg -n '^(<<<<<<<|=======|>>>>>>>)' --
  EDMCOverlay/edmcoverlay.py overlay_client/legacy_processor.py
  overlay_client/paint_commands.py overlay_client/render_surface.py
  overlay_client/tests/test_paint_commands.py
  overlay_client/tests/test_render_surface_mixin.py tests/test_edmcoverlay_shapes.py
  tests/test_harness_legacy_tcp_ingestion.py tests/test_legacy_processor.py
  tests/test_shape_gallery.py utils/shape_gallery.py` found markers only in the
  two known unresolved paths (three markers in each). `git diff --check` exited
  2 solely for those six expected leftover conflict markers; it reported no
  whitespace error. They remain intentionally unresolved for Step 3.
- Test selection: no unit or harness tests were added or run. This task changes
  Git state and tracking documentation only, so Git inspection and `git diff
  --check` are the applicable validation. Renderer/runtime behavior, including
  the auto-merged processor and paint paths, remains unvalidated and is deferred
  to Steps 3 and 4.

### Phase 3 / Stages 3.1–3.3 — conflict resolution and runtime review

- `render_surface.py` was manually resolved against the backend baseline; its
  syntax check and focused GUI paint suite passed (9).
- `test_render_surface_mixin.py` was resolved as the backend/circle-stroke test
  union; the focused GUI renderer/paint suite passed (40).
- Review found one circle dedupe-snapshot transform-freezing defect in
  `legacy_processor.py`; a focused regression test was added and the focused
  GUI processor/paint suite passed (50). `paint_commands.py` needed no change.
- Both conflicts are resolved, `git diff --cached --check` passes, and
  `overlay_groupings.json` remains absent from staged and worktree diffs.

### Phase 4 / Stages 4.1–4.3 — automated validation (blocked)

- Entry reconciliation: branch `backend-refactor-implementation`; `MERGE_HEAD`
  resolved to `0d789cbbea77dac500eb7b249d71df67c1dbde9c` (exit 0); `git diff
  --name-only --diff-filter=U` produced no paths (exit 0); and `git diff
  --cached --name-only` showed the active staged merge scope. The three
  approved tracking files and generated Step 3/4 task artifacts were also
  uncommitted at entry; no product path was changed by this validation task.
- Stage 4.1 passed once: `PYQT_TESTS=1 overlay_client/.venv/bin/python -m
  pytest overlay_client/tests/test_render_surface_mixin.py
  overlay_client/tests/test_paint_commands.py tests/test_edmcoverlay_shapes.py
  tests/test_legacy_processor.py tests/test_harness_legacy_tcp_ingestion.py
  tests/test_shape_gallery.py -q` exited 0 with `100 passed in 0.60s`. This
  is mixed validation: deterministic renderer, paint-command, public-payload,
  processor, and gallery cases are unit coverage; the raw/TCP lifecycle module
  is the required harness coverage. No tests were added or altered.
- Stage 4.2 blocked on its first required command, run once: `python3
  scripts/check_edmc_python.py` exited 1 with `[check-edmc-python] ERROR:
  Python 3.12.3 (64bit) does not match tested EDMC runtime 3.13.9+ in the
  3.13 series (32bit) (set ALLOW_EDMC_PYTHON_MISMATCH=1 to bypass)`. The
  bypass was not used. Per the task, `make check`, `git diff --check`, staged
  diff review, managed-configuration preservation checks, cached conflict-marker
  scan, and cached whitespace check were not run. No code, test,
  `overlay_groupings.json`, staging, merge, or manual-overlay action occurred.
- Stage 4.3 remains Ready and is outside this task. At that point, a fresh
  remediation context was required before any remaining validation or manual
  Step 5 request; its later override evidence is recorded below.

### Phase 4 / Stage 4.2 — fresh code-assist remediation (blocked)

- Entry reconciliation confirmed branch `backend-refactor-implementation`, an
  active merge with `MERGE_HEAD` `0d789cbbea77dac500eb7b249d71df67c1dbde9c`,
  no unresolved paths from `git diff --name-only --diff-filter=U`, and the
  active staged merge scope. The previously passed 100-test mixed
  unit/harness command was not rerun, as directed.
- With explicit user authorization for non-release development work, ran
  exactly `ALLOW_EDMC_PYTHON_MISMATCH=1 python3 scripts/check_edmc_python.py`.
  It exited 0 and emitted the expected warning that Python 3.12.3 64-bit does
  not match the tested EDMC Python 3.13.9+ 32-bit runtime.
- Ran exactly `make check`. It exited 2 at its first command, `python3 -m ruff
  check .`, because `/usr/bin/python3: No module named ruff`. Per the required
  stop-on-failure rule, `git diff --check`, staged-diff review, managed
  configuration checks, cached conflict-marker scan, cached whitespace check,
  manual overlay inspection, staging, and product-code changes were not run.
- A fresh remediation context must make the project lint dependency available
  in the selected check environment (or obtain an explicit user decision to
  defer the project gate) before rerunning `make check`; do not rerun the
  unchanged failing command in this context.

### Phase 4 / Stage 4.2 — fresh code-assist remediation 2 (blocked)

- Per explicit user instruction, activated `overlay_client/.venv` and verified
  `python`, `python3`, and `ruff` resolve there; `python --version` reported
  Python 3.12.3 and `python3 -m ruff --version` reported Ruff 0.3.7.
- Ran exactly `source overlay_client/.venv/bin/activate && make check`.
  Ruff (`python3 -m ruff check .`) and mypy (`python3 -m mypy`) both passed.
  The GUI-enabled pytest phase collected 1,662 tests and ended with 1,636
  passed, 21 skipped, and five errors in 14.77s.
- All five errors are setup failures in
  `tests/test_harness_pressure_ab_snapshot.py`: `SocketBroadcaster.start()`
  returned `False` while attempting to bind `127.0.0.1:0`. This sandbox's
  socket restriction is the observed blocker; no feature-test assertion failed.
  `make check` therefore exited nonzero.
- Per the required stop-on-failure rule, `git diff --check`, cached diff check,
  staged status/stat/hunk audit, grouping-configuration absence checks, cached
  conflict-marker scan, cached whitespace check, manual overlay inspection,
  staging, and product-code changes were not run. No code, test, staging, or
  commit change occurred in this remediation.
- A subsequent context needs either an environment where loopback socket binds
  are permitted, or an explicit user decision to defer the real-socket harness
  failures, before it may resume the remaining Step 4 integrity gates.

### Phase 4 / host validation and integrity completion

- The user ran `source overlay_client/.venv/bin/activate && make check` in the
  host terminal: Ruff and mypy passed, and the full GUI-enabled suite passed
  `1662` tests in 14.93s.
- The authorized non-release compatibility override passed. Main-context
  `git diff --check`, `git diff --cached --check`, grouping worktree/index
  checks, staged conflict-marker scan, and staged scope/stat review all passed;
  `overlay_groupings.json` is absent from the staged merge.
- Automated validation is complete. The native-Wayland placement defect is
  separately tracked; the user authorized circle-merge completion without
  claiming a Wayland rendering pass.

### Phase 4 / Stage 4.3 — manual validation disposition

- The user confirmed the circle/rectangle rendering contract on X11.
- Native GNOME Wayland could not reach circle inspection because the helper
  applied the overlay one complete monitor to the right of Elite's requested
  rectangle. Research is recorded in
  `docs/plans/2026-08-27-gnome-wayland-monitor-placement/`.
- The user explicitly determined this is not a circle-work regression and
  authorized the merge commit. This defers native-Wayland rendering validation;
  it does not mark it passed.
- Do not use Fill-mode gallery placement to judge physical concentricity:
  preserved per-ID grouping transforms can offset logically concentric circles.
- No live overlay has been started or sent by the current session. A user must
  explicitly authorize that action before it is performed.
- Run the final staged review, update this record with the commit, and create
  the local merge commit without pushing.
