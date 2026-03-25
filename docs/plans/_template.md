## Goal: <concise goal statement>

Follow persona details in `AGENTS.md`.
Document implementation results in the `Implementation Results` section.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear, capture it under `Open Questions`.

## Requirements (Initial)
- <required behavior/outcome #1>
- <required behavior/outcome #2>
- <required behavior/outcome #3>
- Keep `load.py` minimal: new feature/business logic should be implemented in helper modules/services, with `load.py` limited to orchestration/wiring and thin delegating methods.

## Testing Strategy (Required Before Implementation)

| Change Area | Behavior / Invariant | Test Type (Unit/Harness) | Why This Level | Test File(s) | Command |
| --- | --- | --- | --- | --- | --- |
| <area> | <invariant> | <Unit/Harness> | <why> | <path> | `<command>` |

## Test Scope Decision (Required)
- Unit-only? Why: <answer>
- Harness required? Why: <answer>
- Mixed (Unit + Harness)? Why: <answer>

## Test Acceptance Gates (Required)
- [ ] Unit tests added/updated for pure logic changes.
- [ ] Harness tests added/updated for lifecycle/wiring changes.
- [ ] Exact commands listed and executed.
- [ ] Any skips documented with reasons.

## Out Of Scope (This Change)
- <explicit non-goal #1>
- <explicit non-goal #2>

## Current Touch Points
- Code:
- `<path/to/file.py>` (<what is touched>)
- `<path/to/file2.py>` (<what is touched>)
- Tests:
- `<path/to/test_file.py>`
- Docs/notes:
- `<path/to/doc.md>`

## Assumptions
- <assumption #1>
- <assumption #2>

## Risks
- <risk #1>
- Mitigation: <mitigation #1>
- <risk #2>
- Mitigation: <mitigation #2>

## Open Questions
- None currently.

## Decisions (Locked)
- <decision #1>
- <decision #2>

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | <contract/design> | Pending |
| 2 | <implementation> | Pending |
| 3 | <tests/validation> | Pending |
| 4 | <docs/release notes> | Pending |
| 5 | <rollout/follow-up> | Pending |

## Phase Details

### Phase 1: <title>
- <summary>
- Risks: <risk summary>
- Mitigations: <mitigation summary>

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | <stage description> | Pending |
| 1.2 | <stage description> | Pending |
| 1.3 | <stage description> | Pending |

#### Stage 1.1 Detailed Plan
- Objective:
- <objective>
- Primary touch points:
- `<path/to/file>`
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- <criterion 2>
- Verification to run:
- `<command>`

#### Stage 1.2 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Stage 1.3 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Phase 1 Execution Order
- Implement in strict order: `1.1` -> `1.2` -> `1.3`.

#### Phase 1 Exit Criteria
- <exit criterion 1>
- <exit criterion 2>

### Phase 2: <title>
- <summary>
- Risks: <risk summary>
- Mitigations: <mitigation summary>

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | <stage description> | Pending |
| 2.2 | <stage description> | Pending |
| 2.3 | <stage description> | Pending |

#### Stage 2.1 Detailed Plan
- Objective:
- <objective>
- Primary touch points:
- `<path/to/file>`
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Stage 2.2 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Stage 2.3 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.

#### Phase 2 Exit Criteria
- <exit criterion 1>
- <exit criterion 2>

### Phase 3: <title>
- <summary>
- Risks: <risk summary>
- Mitigations: <mitigation summary>

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | <stage description> | Pending |
| 3.2 | <stage description> | Pending |
| 3.3 | <stage description> | Pending |

#### Stage 3.1 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Stage 3.2 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Stage 3.3 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3`.

#### Phase 3 Exit Criteria
- <exit criterion 1>
- <exit criterion 2>

### Phase 4: <title>
- <summary>
- Risks: <risk summary>
- Mitigations: <mitigation summary>

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | <stage description> | Pending |
| 4.2 | <stage description> | Pending |
| 4.3 | <stage description> | Pending |

#### Stage 4.1 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Stage 4.2 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Stage 4.3 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- <exit criterion 1>
- <exit criterion 2>

### Phase 5: <title>
- <summary>
- Risks: <risk summary>
- Mitigations: <mitigation summary>

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | <stage description> | Pending |
| 5.2 | <stage description> | Pending |
| 5.3 | <stage description> | Pending |

#### Stage 5.1 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Stage 5.2 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Stage 5.3 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
- <exit criterion 1>
- <exit criterion 2>

## Test Plan (Per Iteration)
- Env setup (once per machine):
- `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- Headless quick pass:
- `source .venv/bin/activate && python -m pytest`
- Targeted tests:
- `source .venv/bin/activate && python -m pytest <path/to/tests> -k "<pattern>"`
- Milestone checks:
- `make check`
- `make test`
- Compliance baseline check (release/compliance work):
- `python scripts/check_edmc_python.py`

## Implementation Results
- Plan created on <YYYY-MM-DD>.
- Phase 1 <not started / implemented on YYYY-MM-DD>.
- Phase 2 <not started / implemented on YYYY-MM-DD>.
- Phase 3 <not started / implemented on YYYY-MM-DD>.
- Phase 4 <not started / implemented on YYYY-MM-DD>.
- Phase 5 <not started / implemented on YYYY-MM-DD>.

### Phase 1 Execution Summary
- Stage 1.1:
- <result>
- Stage 1.2:
- <result>
- Stage 1.3:
- <result>

### Tests Run For Phase 1
- `<command>`
- Result: <passed/failed/skipped + brief notes>

### Phase 2 Execution Summary
- Stage 2.1:
- <result>
- Stage 2.2:
- <result>
- Stage 2.3:
- <result>

### Tests Run For Phase 2
- `<command>`
- Result: <passed/failed/skipped + brief notes>

### Phase 3 Execution Summary
- Stage 3.1:
- <result>
- Stage 3.2:
- <result>
- Stage 3.3:
- <result>

### Tests Run For Phase 3
- `<command>`
- Result: <passed/failed/skipped + brief notes>

### Phase 4 Execution Summary
- Stage 4.1:
- <result>
- Stage 4.2:
- <result>
- Stage 4.3:
- <result>

### Tests Run For Phase 4
- `<command>`
- Result: <passed/failed/skipped + brief notes>

### Phase 5 Execution Summary
- Stage 5.1:
- <result>
- Stage 5.2:
- <result>
- Stage 5.3:
- <result>

### Tests Run For Phase 5
- `<command>`
- Result: <passed/failed/skipped + brief notes>
