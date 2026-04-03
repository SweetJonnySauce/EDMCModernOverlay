## Goal: <concise goal statement>

Follow persona details in `AGENTS.md`.
Document implementation results in the `Implementation Results` section.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear, capture it under `Open Questions`.

## Safety Rules
- Keep changes small and behavior-scoped unless the plan explicitly says otherwise.
- New feature/business logic should live outside `load.py`; keep `load.py` focused on orchestration/wiring and thin delegating methods.
- Write down invariants before changing risky edges such as I/O, sockets, timers, focus, and UI-thread-sensitive code.
- Record exact test commands run, and record skips with reasons.

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
| 1 | <phase description> | Pending |
| 2 | <phase description> | Pending |

Add as many phases as needed. Do not force a fixed phase count if the work does not justify it.

## Phase Details

### Phase N: <title>
- <summary>
- Risks: <risk summary>
- Mitigations: <mitigation summary>

| Stage | Description | Status |
| --- | --- | --- |
| N.1 | <stage description> | Pending |
| N.2 | <stage description> | Pending |

Add as many stages as needed for the phase. Do not force a fixed stage count if the work does not justify it.

#### Stage N.1 Detailed Plan
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

#### Stage N.2 Detailed Plan
- Objective:
- <objective>
- Steps:
- <step 1>
- <step 2>
- Acceptance criteria:
- <criterion 1>
- Verification to run:
- `<command>`

Duplicate the detailed-plan block for additional stages as needed.

#### Phase N Execution Order
- Document execution order only where it matters.
- If stages are independent, say so.
- If stages must be sequential, record the dependency explicitly.

#### Phase N Exit Criteria
- <exit criterion 1>
- <exit criterion 2>

Repeat the Phase N block as many times as needed.

## Test Plan (Per Iteration)
- **Env setup (once per machine):** `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- **Headless quick pass (default for each step):** `source .venv/bin/activate && python -m pytest`
- **Targeted tests:** `source .venv/bin/activate && python -m pytest <path/to/tests> -k "<pattern>"`
- **Milestone checks:** `make check` and `make test`
- **Compliance baseline check (release/compliance work):** `python scripts/check_edmc_python.py`

## Implementation Results
- Plan created on <YYYY-MM-DD>.
- Add one execution summary subsection per phase as work progresses.
- Record exact test commands and outcomes for each completed phase.

### Phase N Execution Summary
- Stage N.1:
- <result>
- Stage N.2:
- <result>

Duplicate as needed for additional stages and phases.

### Tests Run For Phase N
- `<command>`
- Result: <passed/failed/skipped + brief notes>
