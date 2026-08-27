# Step 05 Task 01 Validation Plan

| Order | Action | Expected evidence |
| --- | --- | --- |
| 1 | EDMC baseline check | Exact pass result or an unwaived platform/version/architecture blocker. |
| 2 | Focused unit, harness, and PyQt tests | Contract, lifecycle, and render regression evidence in task-specified order. |
| 3 | Expanded headless and GUI-enabled suites | Separate pass/fail/skip counts and reasons. |
| 4 | Lint, type check, and `make check` | Release-quality static and project-check evidence. |
| 5 | Scoped diff, documentation, compliance, and secret review | No unapproved drift or secrets; explicit EDMC yes/no results. |

If an unchanged mandatory validation command fails, capture its exact evidence
and stop without rerunning it, for orchestration review.
