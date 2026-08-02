# Task 06 Plan: Proven Unchanged Repaint Work

## Scope and invariants

Touch only pure payload comparison, generic repaint attribution/refresh signaling, render
identity, Shell-frame preparation reuse, allowlisted performance interpretation, and focused
unit tests. Preserve content/style/geometry/group/override/expiry/removal/animation/scale/
mode/monitor/visibility/recovery/explicit-refresh behavior, Phase 19, startup/remap, focus,
click-through, privacy, and the backend boundary.

## Test type selection

**Unit tests** are required and selected because fingerprints, counters, render identities,
target/request snapshots, timers, frame builders, and presentation callbacks are pure or
injectable. **Harness tests are not selected** because Task 06 will not touch `load.py`, EDMC
hooks, plugin lifecycle, or Tk wiring. If that scope changes, add a harness test before landing.

## Test scenarios

| ID | Input | Expected output |
| --- | --- | --- |
| T1 | Same supported message with only TTL and metadata changed | Expiry/lifecycle metadata refreshes; ingest reports no visual change and no repaint/update/backend refresh occurs |
| T2 | Same supported message, rect, or vector with one content/style/geometry/transform field changed | Ingest reports visual change and schedules repaint |
| T3 | Same supported payload with plugin or resolved group changed | Visual equivalence is rejected and repaint is preserved |
| T4 | Same supported payload with a new override generation | Visual equivalence is rejected and repaint is preserved |
| T5 | Same animated supported payload | Dedupe is bypassed and immediate repaint is preserved |
| T6 | Repeated unknown, incomplete, or fingerprint-error payload | Safe fallback reports change and repaints every time |
| T7 | Identical supported payload followed by expiry purge | Refresh itself is a no-op; removal dirties state and repaints |
| T8 | Immediate, debounced, and already-pending repaint requests | Fixed bounded counters distinguish request, Qt update, timer start, and coalescing paths |
| T9 | Content-suppressed visual repaint | Generic one-shot presentation refresh is set before the backend cycle; Qt update still occurs |
| T10 | Same successful Shell frame request with equal render/target/request identity | Frame builder runs once; second call reuses the result and records an unchanged-visual frame skip |
| T11 | Content, style, grouping/override, scale, mode, monitor/output, workspace, visibility, geometry, or diagnostics identity changes | Frame reuse key changes and the frame builder runs |
| T12 | Missing/unprovable target/request state or failed/ineligible frame result | Result is not reused; each call takes the safe build/recovery path |
| T13 | Explicit repaint/presentation refresh with unchanged pixels | Required Qt update and helper presentation path runs; only proven identical frame preparation may reuse bytes/results |
| T14 | Allowlisted backend performance sample for a reused frame preparation | `frame_builds=0`, frame skip/reuse remains distinguishable from raster encode and helper-call reuse |
| T15 | Counter increment beyond the configured maximum | Value saturates and key cardinality remains fixed |

## Implementation phases

### Phase 1: Explore and plan

Phase status: **Completed**

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Verify authorization, handoff, dirty tree, Task 06, design, research, plans, and iteration review | Completed |
| 1.2 | Audit payload snapshots, TTL/metadata, repaint debounce/update, paint, frame, raster, and presentation paths | Completed |
| 1.3 | Attribute historical request/paint/frame/raster/presentation layers and select the smallest seams | Completed |
| 1.4 | Select unit tests, record touchpoints/invariants, and define explicit RED scenarios | Completed |

### Phase 2: RED tests

Phase status: **Completed**

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add all fingerprint, TTL/metadata, visual trigger, animation, grouping, override, expiry, and unknown-fallback tests | Completed |
| 2.2 | Add bounded repaint scheduling and generic presentation-refresh tests | Completed |
| 2.3 | Add Shell-frame reuse/invalidation/failure and performance attribution tests | Completed |
| 2.4 | Run the mandated focused command and record expected pre-fix failures | Completed |

### Phase 3: GREEN implementation

Phase status: **Completed**

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Harden the pure supported-payload visual fingerprint and lifecycle-only refresh result | Completed |
| 3.2 | Add fixed saturating per-reason request/scheduling/paint counters and generic refresh signaling | Completed |
| 3.3 | Add deterministic render identity and narrow successful Shell-frame result reuse | Completed |
| 3.4 | Update allowlisted performance interpretation for frame-preparation skips | Completed |

### Phase 4: Refactor and validate

Phase status: **Completed**

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Run focused GREEN and review nearby conventions/boundaries | Completed |
| 4.2 | Run payload/repaint/follow/GNOME integrated slice, Ruff, compileall, and diff hygiene | Completed |
| 4.3 | Run milestone `make check` and `make test` gates | Completed |
| 4.4 | Synchronize authoritative/working plans, progress, evidence README, and iteration review | Completed |
| 4.5 | Review scope and leave the increment uncommitted because Stage 3.16 is the approved commit point | Completed |

## Validation commands

- Focused RED/GREEN:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_payload_dedupe.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py -q`
- Integrated query/repaint/follow:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_payload_dedupe.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py -q`
- Boundary regression:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_consumers.py -q`
- Static/build checks: targeted Ruff, targeted `compileall`, `git diff --check`.
- Milestone gates: `make check` and `make test`.

## Risks and mitigations

- **Silent stale pixels:** reuse requires complete equal identities; unknown/missing state rebuilds.
- **Animation loss:** animated payloads explicitly bypass dedupe.
- **Grouping/override drift:** plugin, resolved group, and generation participate in equivalence.
- **Recovery delayed by cached failure:** only successful eligible update results are cached.
- **Lease expiry:** frame-result reuse does not suppress the backend-owned timed helper refresh.
- **Boundary leakage:** no generic GNOME enums or private presentation imports are introduced.
- **Measurement overhead:** counters have fixed keys and saturating values; detailed diagnostics
  remain gated.
