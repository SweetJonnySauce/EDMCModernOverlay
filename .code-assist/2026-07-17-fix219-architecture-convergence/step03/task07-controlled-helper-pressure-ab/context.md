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

- `overlay_client/backend/pressure_ab.py`: pure schemas, validation, and counter snapshot/delta.
- `overlay_client/backend/pressure_ab_report.py`: strict-run aggregation, contrasts, acceptance
  review inputs/evaluation, and deterministic report rendering.
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

## Stage 7.R1 verified context — 2026-08-02

- The loaded handoff's dirty-worktree claim is stale. Current Git authority is branch
  `backend-refactor-implementation`, HEAD `14576dd`, with a clean worktree; the complete Step 03
  increment, including the August 2 assessment, is present in that commit. This remediation
  preserves that clean starting state and does not commit or push.
- Historical evidence remains unchanged at 12 reduced-v2 captures plus two superseded full-v1
  captures. `thresholds.json` and `pressure-ab-report.md` are absent.
- The EDMC compatibility check passes under the available development interpreter (Python
  3.12.3 64-bit) against the recorded 3.10.3 32-bit minimum; it emits only the expected
  non-Windows architecture warning.
- `SocketBroadcaster._handle_client()` currently calls every ingestion handler on its asyncio
  loop. The `pressure_snapshot` handler then publishes a client request and synchronously waits
  on a `threading.Event`, preventing the loop from broadcasting the request or ingesting the
  response until the timeout expires.
- The smallest bounded seam is command-selective ingestion deferral owned by the broadcaster
  configuration: only the blocking `pressure_snapshot` command may execute outside the socket
  loop. Fast neighboring CLI commands retain their current synchronous ordering and thread.
- Pending request correlation and shutdown cleanup must be synchronized because the deferred
  requester and client-response handler execute on different threads. Shutdown must wake a
  pending wait before stopping the socket loop; it must not move Tk/Qt work to a worker.

## Stage 7.R2 verified context — 2026-08-02

- The Stage 7.R1 handoff now matches branch `backend-refactor-implementation`, HEAD `14576dd`,
  and the seven-file intentional dirty worktree. A fresh localhost-permitted rerun of
  `tests/test_harness_pressure_ab_snapshot.py` passed all eight cases; the managed sandbox
  cannot bind loopback sockets and produced five fixture errors rather than product failures.
- `overlay_client/backend/pressure_ab.py` currently validates only cell/repetition/timing and
  diagnostics state. Its summary function expects a flat `metrics` mapping that the runner
  never emits.
- `scripts/backend_pressure_ab.py` emits nested `resources`, `client_work`, `helper_work`,
  `actor_counts`, `warning_counts`, and `safety_failures`, but its cell document has no strict
  parser, fixed provenance, execution-order field, complete-run loader, explicit unavailable
  values, or whole-cell continuity proof.
- Stage 7.R2 will establish one strict JSON-compatible runner document shape and a frozen parsed
  run model. The schema will use exact field allowlists, bounded numeric values, safe identifiers,
  fixed cell-state declarations, explicit unavailable records, complete safety fields, and
  post-warm-up continuity declarations. Unknown/prohibited privacy keys or host-identifying
  strings fail closed.
- Runner edits in this stage are limited to producing and validating that strict shape. GPU,
  helper-disabled proof, backend-route proof, warning behavior, live timing, safety polling, and
  full `_capture()` orchestration remain Stage 7.R4 concerns; aggregation, contrasts, bounds, and
  Markdown remain Stage 7.R3 concerns.

## Stage 7.R3 verified context — 2026-08-02

- The Context 3 handoff matches branch `backend-refactor-implementation`, HEAD `14576dd`, the 11
  cumulative Stage 7.R1/7.R2 modified files, clean patch hygiene, and absent
  `thresholds.json`/`pressure-ab-report.md`. A fresh Stage 7.R2 baseline passed 67 tests.
- Stage 7.R3 consumes only the frozen `PressureAbRun` returned by the strict Stage 7.R2 parser or
  loader. Raw mappings, partial cells, unsafe evidence, and privacy-invalid input cannot enter
  analysis through a permissive compatibility adapter.
- Per-repetition scalar inputs are the median of each 60-observation resource distribution plus
  the exact 60-second work, actor, and normalized warning counts. The per-cell layer reports
  median, deterministic nearest-rank p95, minimum, and maximum across all three repetitions.
- Intentionally stopped clients and disabled helpers are structural zero for their own resource,
  work, and actor metrics so required A/B contrasts remain meaningful. GPU or warning provider
  unavailability remains explicitly unavailable; mixed provider availability within a cell is
  rejected rather than coerced to zero.
- The five fixed contrast names map exactly to `B1-A1`, `A2-A1`, `B2-B1`,
  `(B2-B1)-(A2-A1)`, and `B2-A1`. Contrasts use per-cell medians and remain unavailable when a
  genuine provider value is unavailable.
- Reviewed bounds are strict in-memory report inputs with a fixed all-repetitions/no-favorable-
  singleton method, sanitized provenance, unique metric/contrast pairs, and inclusive numeric
  ranges. Stage 7.R3 does not create a JSON threshold artifact or infer bounds from synthetic
  tests.
- Deterministic Markdown may be rendered in memory from complete synthetic test runs, but no
  real `pressure-ab-report.md` may be written before live evidence exists. Runner/provider,
  timing, warning, GPU, and safety hardening remains Stage 7.R4 scope.

## Stage 7.R4 verified context — 2026-08-02

- Context 4 resumed from `/tmp/handoff-20260802-080915.md` and verified branch
  `backend-refactor-implementation`, HEAD `14576dd`, the cumulative R1-R3 dirty files, clean
  patch hygiene, immutable historical captures, and absence of a real report, migration
  threshold file, or clean baseline identity.
- Fresh compatibility plus focused schema/runner baseline passed: the EDMC check retained only
  its expected architecture warning and pytest reported 86 passed. The R1-R3 claims remain
  current.
- At the start of R4, the runner still had every gap named by the addendum: broad helper-disabled exception
  classification, declared rather than live A2/B2 state, unavailable-only GPU behavior with
  unreachable code, broad warning text collection, misaligned end work, post-sample-only manual
  safety, no interruption artifact, and direct global timing/providers.
- Chosen seam: frozen injected provider/timing bundles feed pure validation and one orchestrator.
  Tests advance a fake monotonic/epoch clock while production defaults retain exact 300-second
  warm-up, 60 one-second observations, and three repetitions.
- Dependency flow is `CLI arguments -> exact state/provenance -> live state proof -> warm-up
  safety ticks -> aligned repetition endpoints/providers -> strict cell parser -> exclusive
  success output`; safety/interrupt paths instead produce an exclusive sanitized non-acceptance
  document. No raw status/helper/journal/process data enters either artifact.
- No `load.py`, plugin lifecycle, socket, Tk/Qt, or generic follow/runtime touchpoint is planned,
  so R4 uses unit tests. The R1 real-socket harness remains a regression gate and the broader
  missing coverage inventory remains assigned to R5.
- R4 completion replaced those gaps with exact owner/health/runtime-route validators, bounded
  process/GPU/journal providers, one-second aligned clock windows, whole-cell continuity, fixed
  safety tracking, and exclusive success/stop writers. Final runner tests use only fake clocks
  and injected providers; no live interval or host state was touched.

## Stage 7.R5 verified context — 2026-08-02

- Context 5 resumed `/tmp/handoff-20260802-084202.md` and verified branch
  `backend-refactor-implementation`, HEAD `14576dd`, the cumulative R1-R4 dirty file set, patch
  hygiene, capture hold, historical evidence, and absent prohibited artifacts.
- The R1 real-socket harness already covers H1-H3. The R2/R3 strict model/report tests cover
  U5-U10, and R4 covers most U11/U12 and orchestration behavior. R5 therefore uses a named
  traceability matrix instead of duplicating passing tests blindly.
- Residual coverage is local to direct `/proc` parsing, all-four-cell fake orchestration,
  provider availability changes, full-capture endpoint decrease/saturation, malformed helper/
  client providers, early validation, and `main()` success/write-failure behavior.
- New tests are unit tests because these gaps use injected providers/clocks or monkeypatched local
  I/O. Existing harness tests remain the required lifecycle regression gate; no new `load.py`
  change is planned.
- R5 completed with 32 additional runner tests/cases. The valid RED exposed unhandled output
  write failure and retained partial output; the runner now cleans only its newly created partial
  file and normalizes success/stop write `OSError` to fixed exit-2 stderr.
- Final R5 evidence is 105 runner tests, 232 focused Task 07 tests, and 159 integrated helper/
  query/repaint/harness tests passing. Targeted Ruff, mypy, compileall, help, compatibility, and
  patch/artifact audits also pass. There were no skips.
- Historical captures remain exactly 12 reduced-v2 plus two superseded full-v1 files and are
  unchanged. No live cell, host/helper mutation, real report, `thresholds.json`, clean baseline
  identity, commit, or push occurred. Context 6 must begin at Stage 7.R6 only.

## Stage 7.R6 verified context — 2026-08-02

- Context 6 resumed `/tmp/handoff-20260802-085738.md` and verified branch
  `backend-refactor-implementation`, HEAD `14576dd`, the exact cumulative R1-R5 dirty file set,
  clean patch hygiene, active persisted goal, historical evidence counts, and absent prohibited
  report/threshold/baseline artifacts.
- The original goal prompt authorizes R6 only: complete focused, socket/harness, integrated,
  full-orchestration, `make check`, `make test`, Ruff, mypy, compileall, patch hygiene, cumulative
  review, per-stage completion audit, and truthful readiness decision without a live A/B cell.
- R6 plans no behavior change. Existing unit/harness/GUI tests are direct evidence; any discovered
  defect must first receive touchpoint-appropriate RED coverage before a scoped fix.
- Dependency flow under audit is `EDMC hooks -> backend-neutral runtime/socket lifecycle ->
  overlay client backend-owned consumers -> strict capture documents -> frozen four-cell run ->
  pure analysis/reviewed bounds -> deterministic in-memory report`. Compositor-specific behavior
  must remain behind `overlay_client/backend/`, and report-only bounds must remain unable to
  serialize to migration `thresholds.json`.

## Stage 7.R6 completion context — 2026-08-02

- Official EDMC sources now establish the checked release contract: `.python-version` is 3.13,
  `docs/Releasing.md` identifies Python 3.13.9 32-bit, the latest stable release checked is 6.1.2,
  and the two most recently updated Plugin Development discussions add no requirement relevant to
  this socket/preferences/backend remediation.
- The local checker enforces 3.13.9+ only within the 3.13 series and exact 32-bit parity. Only the
  explicit value `ALLOW_EDMC_PYTHON_MISMATCH=1` permits a development/CI mismatch.
- Preferences/backend status dependency flow is now `Tk read -> immediate cache/shadow result +
  queued refresh -> later client push -> lock-protected cache`; no Tk hook waits on a network
  `Event`.
- GNOME raster cleanup dependency flow is now exclusively overlay-client-owned. `load.py` has no
  GNOME raster constants, private presentation import, raw backend/helper dispatch, or D-Bus
  cleanup call.
- The complete current-source suite passed headless and GUI-enabled gates. The real-socket
  harness requires localhost permission in this managed environment; its sandbox bind failures
  were environmental and its permitted run passed.
- All R1-R6 completion evidence is recorded in `progress.md`. The cumulative worktree remains
  intentionally dirty on HEAD `14576dd`; no commit, live cell, host mutation, report, threshold,
  or new baseline identity was created.
