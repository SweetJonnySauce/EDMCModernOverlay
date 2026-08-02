# Task 07 Code Context

## Summary

Task 07 is authoritative Stage 1.9 / working Stage 3.13. It must run the approved quiet
four-cell helper pressure A/B, derive reviewed pressure-reduction acceptance bounds from three
repeated 60-second samples per cell, and keep those bounds out of migration
`thresholds.json`.

The existing Task 05 and Task 06 runtime corrections are present in the intentionally dirty
Step 03 worktree. This task must preserve them and every historical capture.

## Requirements and acceptance surface

- Hold stable windowed Elite on monitor A at uniform 100% scale with fixed payload, display,
  refresh, and workload inputs. Firefox must be stopped.
- Capture A1 (client stopped/helper disabled), A2 (client running/helper disabled and fallback
  unavailable), B1 (client stopped/helper enabled in `full_helper` with diagnostics off), and
  B2 (client and helper running).
- Use a five-minute warm-up and three 60-second samples for every cell. Interleave order where
  practical and record the actual order.
- Collect only allowlisted bounded aggregates: process CPU, context-switch deltas, RSS, bounded
  GPU/VRAM when available, helper target/presentation calls, repaint requests, Qt paints,
  frame/raster work, actor counts, and normalized warning/assertion counts.
- Report per-cell median plus p95 or range. No favorable singleton can pass the gate.
- Stop immediately on flashing, input loss, drag corruption, repeated Mutter assertions, or
  rapidly rising GNOME Shell CPU. Firefox failure reproduction is prohibited.
- Do not resume the historical matrix, create a clean-baseline identity, enable capture
  diagnostics, create or modify `thresholds.json`, change production routing, commit, or push.

## Existing documentation

- `docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md` is the
  approved design. Its performance gate requires the four exact cells, quiet diagnostics,
  repeated samples, separate query/repaint/paint/frame measures, safety-first stopping, and
  report-only pressure bounds.
- `research/gnome-helper-pressure-and-repaint.md` fixes the workload and explains why helper-idle
  cost must be separated from client-driven helper-loop cost.
- `research/performance-baseline.md` separates Task 07 pressure bounds from later
  migration-regression thresholds.
- The authoritative and working plans mark Stage 1.9 / 3.13 not started and reserve the Step 03
  commit for Stage 3.16.
- The performance README preserves the capture hold at 12/42 plus two superseded v1 captures.
- No `CODEASSIST.md` exists. The repository `AGENTS.md`, task file, approved design, and Step 03
  records supply the project-specific workflow constraints.

## Existing implementation patterns

- Task 06 added fixed-cardinality saturating counters in `overlay_client/work_counters.py` and
  runtime-owned counters for ingest, repaint scheduling, Qt paint, and Shell-frame work.
- `OverlayClientBackendStatusRequest` already demonstrates a bounded request/response path:
  the plugin broadcasts a request, the Qt client handles it on the main thread, and the client
  sends a strict response back over the existing data connection.
- `overlay_plugin/overlay_socket_server.py` already accepts localhost JSON-line CLI requests,
  so a measurement runner can request two snapshots without adding a new listener.
- Existing evidence code uses strict field allowlists, deterministic nearest-rank p95, bounded
  numeric validation, and privacy rejection. Task 07 should reuse those patterns without
  altering the frozen historical capture schema.

## Dependency map

```text
Task 07 runner
  -> existing localhost plugin CLI
    -> load.py bounded snapshot request coordinator
      -> existing broadcaster request event
        -> launcher Qt-thread dispatch
          -> overlay window fixed-schema cumulative work snapshot
            -> existing client data connection response
  -> /proc bounded process samples + optional bounded GPU provider
  -> strict per-sample document
  -> deterministic reviewed Markdown A/B report
```

The overlay snapshot is cumulative; the runner records before/after snapshots and derives only
non-negative bounded deltas. A client restart invalidates a paired sample rather than silently
mixing counter origins.

## Implementation paths

- `overlay_client/backend/pressure_ab.py`: pure schemas, validation, counter snapshot/delta,
  aggregation, acceptance review inputs, and deterministic report rendering.
- `overlay_client/overlay_client.py`, `overlay_client/setup_surface.py`, and
  `overlay_client/follow_surface.py`: fixed-cardinality cumulative client work counters and
  an allowlisted snapshot method.
- `overlay_client/launcher.py`: Qt-thread request dispatch.
- `load.py`: bounded pending-request coordination and localhost CLI command.
- `scripts/backend_pressure_ab.py`: controlled preflight/capture/report CLI with explicit cell
  state and safety prompts.
- Unit tests under `overlay_client/tests/` for the pure schema, deltas, aggregation, privacy,
  and runner seams.
- Harness tests under `tests/` for the `load.py` request/response lifecycle contract.
- Final reviewed evidence report under
  `docs/support/validation/fix219-pre-migration/performance/pressure-ab-report.md` only after the
  complete live run passes privacy and safety review.

## Host readiness observation

The initial read-only host check found GNOME Shell 46 on the expected session, but Firefox is
running, Elite gameplay/EDMC/the overlay client are not running, and unrelated background load
is too high for acceptance measurement. No live cell may begin until the fixed workload and
quiet preflight are satisfied.

## Uncertainties and risks

- GPU tooling must be detected and bounded; absence is recorded as unavailable, never replaced
  by an invented value.
- Helper actor counts must come from an allowlisted health field or be recorded unavailable.
  Raw D-Bus payloads, handles, titles, command lines, and journal text cannot enter artifacts.
- `load.py` is a mandatory harness-test touchpoint. The request wait must remain off Tk hooks and
  bounded so it cannot hang shutdown.
- Live helper enable/disable and application state changes are operational actions. The runner
  should verify them and use explicit prompts rather than silently manipulate an ambiguous
  desktop state.
