# Plan

## Phase 1 — Contract and tests — Completed

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Confirm the client transform and default scale mode | Completed |
| 1.2 | Define inverse conversion and test cases | Completed |

### Test cases

1. A 4:3 monitor scales position and size back uniformly.
2. Default `fill` conversion on a 16:9 monitor reverses the uniform scale.
3. `fit` conversion removes horizontal letterbox offset before scaling.
4. Zero, negative, and non-finite monitor dimensions are rejected.
5. The command-line entry point emits JSON containing canonical `x`, `y`, `w`,
   and `h` values.

## Phase 2 — Implementation — Completed

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add unit tests for the conversion API and CLI | Completed |
| 2.2 | Add `scripts/monitor_to_canonical.py` | Completed |

## Phase 3 — Validation — Completed

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Run focused tests and lint the changed files | Completed |
