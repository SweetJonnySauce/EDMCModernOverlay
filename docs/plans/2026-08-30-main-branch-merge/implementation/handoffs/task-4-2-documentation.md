# Task 4.2 Handoff — Documentation and Refactoring Ownership Completed

## Status and test selection

Task 4.2 completed documentation-only reconciliation for the active,
uncommitted merge. **No new automated test type applies:** this task changed
Markdown and merge-document ownership, not a pure helper/service or EDMC
lifecycle wiring. No test files were added or updated. The remaining risk is
copy drift that product tests do not parse; Task 5 still owns all product,
mixed unit/harness, boundary, compatibility, and project-gate evidence.

## Frozen candidate inventory and decisions

The public pages were manually compared with the Task 3.1--3.3 and 4.1
handoffs, the completed 2026-08-26 circle documentation task record, and
`docs/plans/2026-08-30-unify-shape-thickness-pixels/implementation/plan.md`.

| Candidate | Decision |
| --- | --- |
| `docs/wiki/send_shape-API.md` | Changed. The opening now names both primitives; the circle example uses the public positional ID/shape form; field wording remains centre/radius/optional-thickness accurate; obsolete `0.9.2` compatibility wording was removed. |
| `docs/wiki/send_raw-API.md` | Changed only to make extension compatibility wording version-neutral. Its canonical circle example and the bounded normalization-versus-client-validation wording remain accurate. |
| `docs/wiki/Getting-Started.md` | Changed. Corrected `thickness` from implied-required to optional; explicit positive width remains unscaled logical Qt pixels. |
| `docs/wiki/Concepts.md` | Changed. Retains circle support and explicitly distinguishes a circle primitive from a vector `marker: "circle"`. |
| `docs/wiki/Developer-FAQs.md` | Changed. Replaced the stale rectangle-only answer; retained a generic compatibility explanation without a release-version claim. |
| `docs/wiki/APIs.md` | Changed. Corrected the message/rectangle-only summary to name the circle and explicit-thickness extensions. |
| `docs/rendering-pipeline.md` | Reviewed, unchanged. It already describes centre-plus/minus-radius square derivation, shared bounded mapping, bounded `QPainter.drawEllipse`, and intentional non-uniform ellipse results without inventing a trace or backend contract. |

The exact refactoring inventory comes from local history, not a directory-wide
sweep: `git diff --name-status f93d7b7..main -- docs/refactoring/...` reports
only these four deletions, and `f2c68ba` records an `R100` archive move for
each. That evidence resolves the task brief's deletion-versus-edit ambiguity:
`main` deleted the active originals, while the target retains their historical
content in the archive and later adds current-owner headers.

| Original active path | Target-side/current owner | `main` intent and decision |
| --- | --- | --- |
| `docs/refactoring/client_refactor.md` | `docs/archive/refactoring/client_refactor.md`; active `fix219_` architecture documents own current backend decisions. | Deleted by `main`; leave deleted. The archive preserves extraction history and directs readers to the current plans. |
| `docs/refactoring/compositor_aware_install.md` | `docs/archive/refactoring/compositor_aware_install.md`; active fix219 research/follow-up own current deployment and boundary guidance. | Deleted by `main`; leave deleted. No active runtime-selection guidance is revived. |
| `docs/refactoring/load_refactory.md` | `docs/archive/refactoring/load_refactory.md`; active fix219 research/follow-up own `load.py` control-plane guidance. | Deleted by `main`; leave deleted. The archive retains hook history without duplicating current ownership. |
| `docs/refactoring/refactor-plan.md` | `docs/archive/refactoring/refactor-plan.md`; active `fix219_` documents own current architecture work. | Deleted by `main`; leave deleted. Its completed historical plan is not revived as a current work plan. |

No other `docs/refactoring/` path met that exact deletion-versus-archive
history, so no other refactoring document was changed.

## Files changed

- `docs/wiki/send_shape-API.md`
- `docs/wiki/send_raw-API.md`
- `docs/wiki/Getting-Started.md`
- `docs/wiki/Concepts.md`
- `docs/wiki/Developer-FAQs.md`
- `docs/wiki/APIs.md`
- `docs/plans/2026-08-30-main-branch-merge/plan.md`
- `docs/plans/2026-08-30-main-branch-merge/implementation/execution-status.md`
- This handoff

`docs/rendering-pipeline.md` and all four historical refactoring paths were
reviewed but intentionally left unchanged.

## Validation evidence

| Command | Outcome |
| --- | --- |
| `rg -n -i 'only.*rect|rectangles? supported|logical.*thickness|scale[sd]?.*thickness'` over all seven candidate public pages | Ran successfully. Matches were classified as correct: the FAQ heading now has a correct positive answer; `logical thickness` describes the required unscaled explicit-pixel policy; the grouping sentence is unrelated. No stale rectangle-only, required-thickness, or scaling claim remains. |
| `git diff --check --` for the six changed public pages | Passed with no scoped whitespace errors. |
| `rg -n '^(<<<<<<<|=======|>>>>>>>)'` over all seven candidate public pages | Passed with no output; no conflict markers. |
| Local merge/history inspection (`git diff --name-status`, `git show --name-status f2c68ba`, archive-header comparison) | Confirmed the exact four refactoring decisions above. |

`version.py` remains the sole unresolved path. No source, test, configuration,
release metadata, version, gallery, Task 5, or refactoring-document path was
changed by this task.

## Exact next task

Run **Task 4.3 — release-version resolution** in a fresh context. Resolve only
the `version.py` conflict by preserving the target `1.0.0` as the documented
pre-release assumption unless current repository evidence proves it
incompatible; do not make a release decision, commit, or push.
