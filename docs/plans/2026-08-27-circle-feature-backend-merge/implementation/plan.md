# Circle Feature / Backend Refactor Merge Plan

## Checklist

- [x] Step 1: Freeze and verify the target branch.
- [ ] Step 2: Create a non-committing merge and preserve managed configuration.
- [ ] Step 3: Resolve renderer and test conflicts against the backend baseline.
- [ ] Step 4: Review auto-merged runtime behavior and run automated gates.
- [ ] Step 5: Perform manual overlay checks and commit the validated merge.

## Phase Status

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Preflight and scope confirmation | Completed |
| 2 | Non-committing merge and configuration preservation | Ready |
| 3 | Conflict resolution and runtime review | Ready |
| 4 | Automated and manual validation | Ready |
| 5 | Commit and handoff | Ready |

### Phase 1: Preflight and scope confirmation

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Fetch remote refs and verify a clean target worktree | Completed: user confirmed successful host-terminal `git fetch origin`; local post-fetch guards were clean/no-merge. |
| 1.2 | Create a local backup ref for the target tip | Completed: `refs/backup/circle-feature-backend-merge/backend-refactor-implementation-20260827T163928Z` resolves to `6d308e6df0107f440b601bfb571341e0286c1b80`. |
| 1.3 | Confirm source branch, merge base, and intended scope | Completed: source remains `0d789cbbea77dac500eb7b249d71df67c1dbde9c`; base remains `8e375cce40acc0d9400bde43d6aa01070929adb4`; target-only advances are documented tracking commits. |
| 1.4 | Record preservation of target `overlay_groupings.json` | Completed |

#### Phase 1 verification evidence

- The user ran `git fetch origin` successfully in the host terminal (zero
  output) after the documented sandbox DNS failures. Per the remediation scope,
  the sandbox did not retry any network Git command.
- Local commands confirmed `backend-refactor-implementation` at
  `6d308e6df0107f440b601bfb571341e0286c1b80`, clean/no-staged-path state, and
  absent `MERGE_HEAD`; `origin/backend-refactor-implementation` is
  `9856ff9fa066bf973f9f8b94b4454afbb006c60c` and
  `origin/feature/circle-shape-pyqt-rendering` is
  `0d789cbbea77dac500eb7b249d71df67c1dbde9c`.
- `git reflog show` confirmed the refreshed local origin refs; `git log` and
  `git diff --name-only 9856ff9..HEAD` show that the target-only advance is
  limited to merge-tracking documentation. `git merge-base` remains
  `8e375cce40acc0d9400bde43d6aa01070929adb4`.
- `git diff --exit-code -- overlay_groupings.json` and its cached equivalent
  succeeded. No unit or harness tests were selected or run because this is
  Git/documentation-only work; residual risk is limited to subsequent topology
  changes before Step 2, which requires a new pre-merge guard check.

### Phase 2: Non-committing merge and configuration preservation

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Start `git merge --no-commit --no-ff feature/circle-shape-pyqt-rendering` | Ready |
| 2.2 | Restore target `overlay_groupings.json` to index and worktree | Ready |
| 2.3 | Inspect staged files and confirm the configuration file is absent | Ready |

### Phase 3: Conflict resolution and runtime review

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Resolve `render_surface.py` with backend architecture as baseline | Ready |
| 3.2 | Resolve `test_render_surface_mixin.py` as a union of backend and circle coverage | Ready |
| 3.3 | Review the auto-merged legacy processor and paint command paths | Ready |

### Phase 4: Automated and manual validation

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Run focused shape, paint, renderer, and TCP harness tests | Ready |
| 4.2 | Run GUI-enabled renderer tests, EDMC Python compatibility, and `make check` | Ready |
| 4.3 | Inspect circles and rectangles on a live overlay | Ready |

### Phase 5: Commit and handoff

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Recheck staged diff, conflict markers, and configuration preservation | Ready |
| 5.2 | Commit only after all gates pass | Ready |
| 5.3 | Record the commit, tests, and manual-verification result | Ready |

## Step 1: Freeze and verify the target branch

**Objective:** Establish a recoverable, current backend-refactor baseline.

Run `git fetch origin`, confirm `backend-refactor-implementation` is clean,
and create a local backup ref at its current tip. Confirm the source feature
still points at the reviewed commit and inspect the merge-base comparison.

**Test requirements:** No code tests; record branch tips and verify the
worktree is clean.

**Integration:** Protects the active refactor before any merge state exists.

**Demo:** The current backend tip can be restored immediately if the merge is
abandoned.

## Step 2: Create a non-committing merge and preserve managed configuration

**Objective:** Materialize the source changes for review without creating a
commit.

Start a no-commit, no-fast-forward merge. Restore `overlay_groupings.json` from
the target `HEAD` in both index and worktree, then ensure it has no staged diff.

**Test requirements:** Run `git diff --check`; verify no conflict marker is
left and no grouping-configuration diff is staged.

**Integration:** Brings all coupled feature code, tests, docs, and utility
changes into one reviewable index.

**Demo:** `git diff --cached --stat` shows the feature scope but no
`overlay_groupings.json` entry.

## Step 3: Resolve renderer and test conflicts against the backend baseline

**Objective:** Preserve backend architecture while incorporating the circle
feature completely.

Resolve the render-surface conflict by retaining current backend structure and
adding the source's bounded shape/stroke behavior. Resolve the test conflict by
retaining backend imports/helpers and adding circle dependencies/tests. Review
the auto-merged processor and paint command code before staging.

**Test requirements:** Run focused renderer/paint and processor tests after
the files compile; add no replacement tests unless a merged contract differs.

**Integration:** Connects the source feature to the refactored target without
discarding either behavior set.

**Demo:** Targeted tests prove circle dispatch and explicit rectangle thickness
work under the merged render surface.

## Step 4: Review auto-merged runtime behavior and run automated gates

**Objective:** Prove correctness across public API, raw/TCP processing, Qt
painting, and the project baseline.

Run focused tests, then the GUI-enabled renderer tests, EDMC Python check, and
`make check`. Treat any failure as a merge blocker until resolved or explicitly
deferred with the user.

**Test requirements:**

```bash
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
  overlay_client/tests/test_render_surface_mixin.py \
  overlay_client/tests/test_paint_commands.py \
  tests/test_edmcoverlay_shapes.py \
  tests/test_legacy_processor.py \
  tests/test_harness_legacy_tcp_ingestion.py \
  tests/test_shape_gallery.py -q
python3 scripts/check_edmc_python.py
make check
```

**Integration:** Verifies the feature at every layer it crosses.

**Demo:** All automated gates pass on the merged backend branch.

## Step 5: Perform manual overlay checks and commit the validated merge

**Objective:** Confirm user-visible rendering and create the merge commit.

Use the gallery or direct shape calls to inspect circle fill/border/thickness,
explicit-thickness rectangle miter corners, and omitted-thickness rectangle
legacy appearance. Record the known Fill-mode gallery grouping caveat rather
than modifying `overlay_groupings.json`. Recheck the staged diff before
committing.

**Test requirements:** Manual overlay result must be recorded. The staged diff
must be whitespace-clean and free of conflict markers.

**Integration:** Produces a reviewable backend branch containing the complete,
validated feature.

**Demo:** A live overlay renders the intended shape variants, and the merge
commit contains no managed grouping configuration change.
