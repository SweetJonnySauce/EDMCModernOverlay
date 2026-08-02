# Task 07 Implementation and Test Plan

## Test type selection

This is a mixed change.

- **Unit tests** are required for strict snapshot/sample schemas, cumulative-counter deltas,
  deterministic median/p95/range aggregation, acceptance-bound/report rendering, privacy
  rejection, process sampling, and CLI orchestration seams.
- **Harness tests** are required because the on-demand client snapshot coordination touches
  `load.py` orchestration and its plugin/client lifecycle state.
- The live four-cell run is an operational/manual acceptance gate and cannot be replaced by
  either test type.

## Expected unchanged behavior

- No helper query, repaint, paint, or frame behavior changes merely because counters exist.
- No detailed per-cycle log or capture diagnostic is enabled.
- Existing backend status requests, payload flow, startup/shutdown, Tk/Qt threading, Phase 19,
  recovery, and the `fix219` backend boundary remain unchanged.
- Historical captures, manifests, settings backups, and the absent `thresholds.json` remain
  untouched.

## Test scenarios

| ID | Input | Expected output |
| --- | --- | --- |
| U1 | Fixed valid client counter mappings | Schema-v1 allowlisted cumulative snapshot with no extra fields |
| U2 | Unknown key, negative value, boolean-as-int, overflow, or unsafe origin | Validation rejects the snapshot |
| U3 | Two same-origin cumulative snapshots | Exact non-negative delta for every fixed counter |
| U4 | Counter decrease, origin change, or timestamp reversal | Sample is rejected rather than mixed |
| U5 | A1/B1 sample with no client | Client-work fields are explicit zero/unavailable according to cell contract |
| U6 | Three repeated numeric samples | Deterministic median, nearest-rank p95, minimum, and maximum |
| U7 | Missing repetition/cell, shortened duration, diagnostics enabled, or unsafe invariant | Overall result remains incomplete/blocked |
| U8 | Complete A1/A2/B1/B2 evidence | Enabled-idle and client-increment deltas are computed separately |
| U9 | Report with reviewed bounds | Bounds and provenance appear only in the Markdown report vocabulary |
| U10 | Raw/private key, title, handle, command line, path, or journal text | Artifact/report validation rejects it |
| U11 | `/proc` snapshots one second apart | CPU, context-switch delta, and RSS are bounded and normalized |
| U12 | GPU provider available/unavailable | Bounded aggregates or an explicit unavailable code, never raw output |
| H1 | Plugin requests a client snapshot and receives matching response | Pending request resolves within its bound and returns strict snapshot |
| H2 | Client absent, malformed response, timeout, or shutdown | Request returns unavailable/error and clears pending state |
| H3 | Existing backend-status and payload commands | Behavior remains unchanged beside the new command |
| L1 | Each approved cell after five-minute warm-up | Three accepted 60-second samples with recorded order |
| L2 | Visible failure or repeated/rising Shell warning condition | Runner stops and Stage 3.13 remains incomplete |

## Phase 7 stages

| Stage | Description | Status |
| --- | --- | --- |
| 7.1 | Verify task/design authority, dirty worktree, capture hold, and host preconditions | Completed |
| 7.2 | Write unit and harness tests for strict quiet snapshots and A/B evidence contracts | Completed |
| 7.3 | Implement the smallest on-demand counter snapshot and bounded plugin/client request path | Completed |
| 7.4 | Implement the controlled capture CLI and deterministic report inputs | Completed |
| 7.5 | Refactor and run focused plus integrated automated gates | Completed |
| 7.6 | Establish the fixed quiet host workload and pass live preflight | Pending |
| 7.7 | Run interleaved A1/A2/B1/B2 warm-ups and three 60-second samples per cell | Pending |
| 7.8 | Review safety/privacy, derive bounds, publish report-only evidence, and synchronize plans | Pending |

Phase status: **In progress**.

## TDD and implementation sequence

1. Add all pure and harness contract tests before production edits; run focused RED and record
   only expected failures.
2. Add strict fixed-key snapshot and delta functions, then aggregate existing Task 06 counters
   and backend query/presentation-cycle counts without high-frequency logging.
3. Add the bounded plugin/client request path with request IDs, strict response validation,
   timeout cleanup, and shutdown-safe behavior. Run unit and harness GREEN.
4. Add the runner around injected clocks, `/proc` readers, optional bounded GPU sampling,
   snapshot requests, cell-state validation, and safety/manual prompts. Keep raw host strings out
   of generated evidence.
5. Generate the Markdown report only from a complete validated result document. Pressure bounds
   require an explicit reviewed decision and cannot serialize to `thresholds.json`.
6. Run focused tests, the integrated query/repaint gate, harness slice, project `make check`,
   `make test`, targeted Ruff/mypy as applicable, compileall, and `git diff --check`.
7. Run the live protocol only after Firefox is stopped, Elite is stable windowed on monitor A at
   100%, background load is quiet, and helper/client state can be verified for each cell.
8. If all 12 samples pass, review distributions, record defensible bounds and provenance in the
   A/B report, synchronize Stage 1.9/3.13 status, and leave commit/push for Stage 3.16.

## Validation commands

Planned commands, with exact paths refined after tests land:

```bash
source overlay_client/.venv/bin/activate && python -m pytest \
  overlay_client/tests/test_pressure_ab.py \
  overlay_client/tests/test_backend_pressure_ab_runner.py -q

source overlay_client/.venv/bin/activate && python -m pytest \
  tests/test_pressure_ab_harness.py -q

source overlay_client/.venv/bin/activate && python -m pytest \
  overlay_client/tests/test_gnome_helper_presentation_runtime.py \
  overlay_client/tests/test_payload_dedupe.py \
  overlay_client/tests/test_repaint_debounce.py \
  overlay_client/tests/test_follow_surface_mixin.py -q

source overlay_client/.venv/bin/activate && make check
source overlay_client/.venv/bin/activate && make test
source overlay_client/.venv/bin/activate && python -m compileall -q \
  overlay_client scripts/backend_pressure_ab.py
git diff --check
```

## Rollback and stop policy

- Code rollback is confined to the new request/snapshot/report seam; no historical evidence or
  settings restoration is coupled to it.
- Every request has a short bound and clears its pending entry on timeout/error.
- The live runner never overwrites a completed result and marks incomplete evidence explicitly.
- Stop immediately for the approved visible/Shell conditions. Retain only sanitized diagnostic
  aggregates and do not derive acceptance bounds from an incomplete run.
