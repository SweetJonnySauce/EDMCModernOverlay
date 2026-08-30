# Task 4.3: Resolve the Version Conflict

## Scope

Resolve the active merge conflict in `version.py` only. Retain the target
branch's `1.0.0` as the temporary integration default and record that choice
as a **pre-release integration assumption**, not as a release decision,
announcement, tag, or compatibility guarantee.

`main` supplies `0.9.2`; that historical source value is not, by itself,
evidence that the target-side `1.0.0` default is incompatible. Task 4.2
deliberately removed historical version claims from public documentation and
does not reopen a release-train decision.

## Exact file boundary

Resolve and stage only:

- `version.py`

At handoff, update only these orchestration records:

- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-4-3-version.md`

Read-only context, in this order:

1. `AGENTS.md`
2. `docs/plans/2026-08-30-main-branch-merge/implementation/orchestration-prompt.md`
3. `docs/plans/2026-08-30-main-branch-merge/plan.md`
4. `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
5. `docs/plans/2026-08-30-main-branch-merge/implementation/handoffs/task-4-2-documentation.md`
6. This task brief
7. `version.py`

Do not inspect, edit, stage, or validate unrelated source, tests,
configuration, release metadata, gallery, public documentation, or Task 5
paths. Do not touch `overlay_groupings.json` or `overlay_settings.json`.

## Decision and evidence rule

The authorized integration outcome is exactly:

```python
__version__ = "1.0.0"
```

Treat it strictly as the working default for this uncommitted integration. It
does not authorize a release-policy change, a release note, a tag, a package
upload, or a claim that `1.0.0` has shipped.

Before resolving, inspect the three-way conflict and the governing records
only far enough to verify that the target side is `1.0.0`, the source side is
`0.9.2`, and no documented local contradiction makes the target-side line
syntactically or operationally incompatible in `version.py`. Do not broaden
this into a release-train investigation. The old source value, historical
release wording, missing external-release information, and product preference
are not incompatibility evidence.

If a concrete local incompatibility is found, leave `version.py` unresolved,
make no alternative version choice, and record the exact evidence and user
decision required. Otherwise retain exactly `1.0.0` and remove only the merge
markers.

## Plan and stages

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 4 | 4.3.1 | Verify the narrow conflict and authorized pre-release-assumption boundary. | Pending |
| 4 | 4.3.2 | Resolve and stage only `version.py` with target `1.0.0`. | Pending |
| 4 | 4.3.3 | Run narrow validation and write handoff/orchestration evidence. | Pending |

Phase 4 becomes **Completed** only after Stages 4.1, 4.2, and all Task 4.3
stages are evidenced as completed. Phase 5 remains pending.

## Technical requirements

1. Preserve the complete existing `version.py` module except for eliminating
   the merge markers and selecting the target-side `__version__ = "1.0.0"`
   assignment. Do not reshape helpers, imports, exports, environment-variable
   behavior, comments, or formatting opportunistically.
2. Stage exactly `version.py` after the resolution. Do not use a broad path,
   blanket side-selection command, or merge-continuation command.
3. Keep the merge uncommitted. Do not run `git merge`, `git merge --continue`,
   `git commit`, `git amend`, `git tag`, `git push`, `git fetch`, `git pull`,
   `git rebase`, `git reset`, `git restore`, `git checkout`, `git switch`,
   `git stash`, `git clean`, or `git merge --abort`.
4. Do not access external services, launch a live overlay, send live payloads,
   or make a release decision. Do not use a public-documentation version claim
   to justify the source-side `0.9.2` value.
5. On success, update the plan and dashboard with exact command outcomes,
   changed paths, the `1.0.0` pre-release assumption, residual release risk,
   and Task 5.1 as the exact next task.

## Test selection and validation

**Test type selected before edits: no new automated test type.** This task
selects an existing version literal during merge resolution and leaves all
version-helper behavior unchanged; it is neither a new pure-helper behavior
change nor EDMC lifecycle wiring. Do not add or update tests. The residual
risk is release-policy and combined-product validation, both owned by Task 5
and the user before any release action.

Run only these narrow checks after resolving and staging the one file:

```bash
.venv/bin/python -m py_compile version.py
git diff --cached --check -- version.py
rg -n '^(<<<<<<<|=======|>>>>>>>)' version.py
git diff --name-only --diff-filter=U
git diff --cached --name-only -- version.py
```

Record every command and exact outcome. The marker scan and unmerged-path
check must produce no output; the staged-name check must identify only
`version.py`. If a check fails, do not repair unrelated paths or rerun an
unchanged failed command; record the failure and hand off the smallest bounded
remediation or user decision. Do not substitute a broad test suite: Task 5
owns mixed unit/harness tests, project gates, and final integrity review.

## Acceptance criteria

1. **Authorized version selection is bounded**
   - Given the active conflict has target `1.0.0` and source `0.9.2`
   - When Task 4.3 evaluates documented local evidence
   - Then it retains `1.0.0` as a pre-release integration assumption unless a
     concrete local incompatibility is recorded, without making a release
     decision.

2. **Module behavior is preserved**
   - Given the resolved `version.py`
   - When it is compared with the pre-resolution module outside the conflict
     hunk
   - Then imports, exports, helpers, environment-variable behavior, and all
     unrelated text are unchanged.

3. **Merge resolution is narrow and staged**
   - Given the target-side version is locally compatible
   - When the resolution is staged
   - Then only `version.py` is staged by this task, it contains no conflict
     markers, and no unmerged path remains.

4. **Narrow validation is evidence-backed**
   - Given the one-file resolution is ready for handoff
   - When the specified syntax, whitespace, marker, unmerged-path, and staged
     name checks run
   - Then their exact outcomes are recorded without claiming Task 5 tests or
     release validation have run.

5. **Orchestration remains accurate**
   - Given Task 4.3 completes successfully
   - When the task records are updated
   - Then Stage 4.3 and Phase 4 are marked Completed, the dashboard records
     the `1.0.0` pre-release assumption and residual release risk, the merge
     remains uncommitted, and Task 5.1 is named as the exact next task.

## Handoff requirements

Create `implementation/handoffs/task-4-3-version.md` with: fresh-context
identifier; status; the no-new-test rationale; conflict values and local
compatibility evidence; explicit `1.0.0` pre-release-assumption wording;
files changed and staged; every validation command and outcome; confirmation
that no unmerged path remains (or the exact blocker); residual
release/product-validation risk; and the exact next task.

On successful resolution, the exact next task is **Task 5.1 — targeted mixed
unit and harness validation**. This is not release approval or permission to
commit.
