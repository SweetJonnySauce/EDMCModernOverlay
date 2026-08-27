# Shape Gallery Utility: Plan

## Acceptance Criteria

1. A command-line utility in `utils/` publishes a gallery to a running overlay.
2. The gallery includes both circles and rectangles with distinct stroke widths,
   colors, sizes, placements, and filled/unfilled examples.
3. It uses stable IDs and a configurable non-negative TTL.
4. It reports port/connection/acknowledgement errors without creating files or
   launching an overlay.

## Test Scenarios

| Input | Expected result |
| --- | --- |
| Default gallery | Contains circles and rectangles, both fill modes, multiple colors, widths, sizes, and positions. |
| `ttl=0` | Every payload is persistent. |
| `ttl=17` | Every payload has TTL 17. |
| Invalid TTL | Parser rejects a negative value before socket connection. |

## Phase Status

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Explore and plan | Completed |
| 2 | Test-first payload coverage | Completed |
| 3 | Utility implementation | Completed |
| 4 | Validation and handoff | Completed |
| 5 | Concentric-circle and solid-fill iteration | Completed |

### Phase 1: Explore and plan

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Inspect utility and client socket patterns | Completed |
| 1.2 | Select unit/manual test boundary | Completed |

### Phase 2: Test-first payload coverage

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add pure gallery payload tests and verify RED | Completed |

### Phase 3: Utility implementation

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Build the gallery payload generator | Completed |
| 3.2 | Add CLI port, TTL, socket, and acknowledgement handling | Completed |

### Phase 4: Validation and handoff

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Run focused unit and syntax checks | Completed |
| 4.2 | Record manual live-overlay instructions and results | Completed |

### Phase 5: Concentric-circle and solid-fill iteration

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Specify concentric geometry and opaque fill assertions | Completed |
| 5.2 | Add regression test and verify RED | Completed |
| 5.3 | Add circles and opaque fills | Completed |
| 5.4 | Run focused and project validation | Completed |
