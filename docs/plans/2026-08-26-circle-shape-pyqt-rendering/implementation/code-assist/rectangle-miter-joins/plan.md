# Explicit Rectangle Miter Joins: Plan

## Test Strategy

| Scenario | Input | Expected result | Test type |
| --- | --- | --- | --- |
| Explicit rectangle thickness | `rect`, color, `thickness=2` | Command pen has `MiterJoin`; its scaled width remains correct. | Unit |
| Omitted rectangle thickness | `rect`, color, no `thickness` | Command pen remains `BevelJoin` and keeps the existing unscaled default width. | Unit |
| Circle regression guard | `circle`, `thickness=2` | Circle's pen retains its existing default join. | Unit |

## Phase Status

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Explore and plan | Completed |
| 2 | Test-first join-style coverage | Completed |
| 3 | Minimal renderer update | Completed |
| 4 | Validation and handoff | Completed |

### Phase 1: Explore and plan

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Inspect rectangle pen construction and paint path | Completed |
| 1.2 | Select explicit-only compatibility boundary and unit test type | Completed |

### Phase 2: Test-first join-style coverage

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add command-pen join assertions | Completed |
| 2.2 | Run the focused test and record its expected RED failure | Completed |

### Phase 3: Minimal renderer update

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Set `MiterJoin` on explicit rectangle command pens only | Completed |
| 3.2 | Run focused tests and inspect the minimal diff | Completed |

### Phase 4: Validation and handoff

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Run GUI-enabled renderer tests and static checks | Completed |
| 4.2 | Record results and compatibility outcome | Completed |
