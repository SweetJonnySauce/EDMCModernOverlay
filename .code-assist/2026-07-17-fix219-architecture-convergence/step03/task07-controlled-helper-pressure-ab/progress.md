# Task 07 Progress

> **Readiness correction (2026-08-02):** A read-only deep assessment found implementation and
> evidence-pipeline blockers in addition to the recorded host-preflight blocker. Live A/B work
> must not begin until remediation Stages 7.R1-7.R6 in
> [`assessment-addendum.md`](assessment-addendum.md) pass and are reviewed. The July 21 test and
> host-preflight sections below remain historical evidence rather than current run authorization.

## Implementation checklist

### Remediation checklist

- [x] Stage 7.R1: prove and repair the real socket-level client snapshot lifecycle.
- [x] Stage 7.R2: add strict evidence contracts.
- [x] Stage 7.R3: add the analysis and report pipeline.
- [x] Stage 7.R4: harden runner state, providers, timing, and safety.
- [x] Stage 7.R5: complete required unit and harness coverage.
- [x] Stage 7.R6: pass integrated gates and complete the remediation audit.

Remediation phase status: **Completed; Stages 7.R1-7.R6 passed on 2026-08-02**.

### Historical Task 07 checklist

- [x] Stage 7.1: verify task/design authority, dirty worktree, capture hold, and host preconditions.
- [x] Stage 7.2: write unit and harness tests before production edits.
- [x] Stage 7.3: implement strict on-demand work snapshots and bounded request wiring.
- [x] Stage 7.4: implement the controlled capture CLI and deterministic report inputs.
- [x] Stage 7.5: pass focused, integrated, harness, and project validation.
- [ ] Stage 7.6: establish and verify the fixed quiet host workload.
- [ ] Stage 7.7: complete all four cells with three accepted 60-second samples each.
- [ ] Stage 7.8: review evidence, derive report-only bounds, and synchronize authoritative state.

## Setup notes

- Mode: `auto`.
- Task source:
  `.agents/tasks/2026-07-17-fix219-architecture-convergence/step03/task-07-run-controlled-helper-pressure-ab.code-task.md`.
- Documentation directory:
  `.code-assist/2026-07-17-fix219-architecture-convergence/step03/task07-controlled-helper-pressure-ab/`.
- Branch/HEAD at start: `backend-refactor-implementation`, `3d23328`.
- The Step 03 worktree is intentionally dirty. No existing change may be reset, discarded, or
  bulk-staged.
- `CODEASSIST.md` is absent; creating one is a future repository-maintenance option, not Task 07
  scope.
- No commit or push is authorized. Stage 3.16 remains the approved commit point.

## Authority and design decisions

- The approved detailed design, research amendment, authoritative plan, iteration checklist,
  Step 03 records, and performance README were reviewed before implementation.
- Capture diagnostics remain off. The historical 12/42 reduced-v2 and two superseded v1
  captures remain immutable.
- Pressure bounds belong only in the reviewed A/B report; migration `thresholds.json` remains
  absent.
- The smallest viable measurement seam is an on-demand fixed-schema cumulative snapshot over
  the existing plugin/client connection. It avoids prohibited per-cycle logging and reuses the
  current bounded request/response pattern.
- Because `load.py` orchestration is involved, the selected test policy is unit plus harness.

## Host preflight observation

- GNOME Shell 46 is present.
- Firefox is running and must be stopped for acceptance.
- Elite gameplay, EDMC, and the overlay client were not active at the initial check.
- Current unrelated host activity is too high for a quiet acceptance sample.
- No A/B cell has started. These observations contain no PID, command line, title, handle, or
  personal path in committed evidence.

## TDD cycles

### Cycle 1: strict quiet snapshot and A/B evidence contracts

- Status: **Completed**.
- RED target: fixed-schema snapshots, cumulative deltas, complete-cell/repetition enforcement,
  deterministic aggregation, privacy rejection, and plugin/client lifecycle request behavior.
- The initial collection RED failed because the strict module did not yet exist. After the pure
  schema landed, 11 pure tests passed and three expected harness failures proved the missing
  plugin/client request path.
- GREEN passed 16 snapshot/schema/harness tests.

### Cycle 2: helper aggregates and controlled cell runner

- Status: **Completed**.
- Added helper source coverage before exposing saturating `target_queries` and
  `presentation_calls` plus current bounded actor counts in `GetHealth`. Diagnostics remain off
  and no per-call log was added.
- Added the fixed 300-second warm-up / three 60-second sample cell runner. It records no PID,
  command line, title, handle, raw helper payload, or journal text in output; existing output is
  never overwritten.
- Focused Task 07 GREEN passed 66 tests. The integrated query/repaint/helper slice passed 217.

## Validation evidence

- `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_pressure_snapshot_window.py overlay_client/tests/test_backend_pressure_ab_runner.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_pressure_ab_snapshot.py -q`: **66 passed**.
- Integrated focused query/repaint/helper/harness command: **217 passed**.
- `source overlay_client/.venv/bin/activate && make check`: **1,402 passed, 21 skipped**;
  repository Ruff and mypy passed. One intermediate run found a new annotation mismatch; it was
  corrected before this final green result.
- `source overlay_client/.venv/bin/activate && make test`: **1,402 passed, 21 skipped**.
- Targeted Ruff, compileall, runner `--help`, and `git diff --check`: **passed**. Ruff was not
  applied to JavaScript; helper source behavior is covered by its dedicated source tests.
- The 21 skips are the expected headless Tk widget skips already documented for Step 03.

## Live gate

Status: **Blocked before first cell by host preconditions**. Firefox remains active, Elite
gameplay/EDMC/the client are absent, and Shell/background load is not quiet. No helper reload,
warm-up, or sample was started. Stage 7.6 remains pending rather than weakening the gate.

## Commit status

No commit or push. Task 07 and Stage 3.13 remain incomplete.

## Deep-assessment addendum — 2026-08-02

- Assessment-time disposition (superseded by the R1-R6 completion record below):
  **implementation-blocked and host-preflight-blocked**.
- Stop-ship findings: the real socket snapshot path blocks its own response transport; runner
  output is incompatible with the existing completion/summary functions; and GPU-available
  sampling is unreachable.
- Additional gaps cover exact cell-state proof, fallback/helper route proof, restart/saturation
  handling, aligned measurement windows, provenance/order, immediate safety stopping, warning
  scoping, strict privacy validation, report rendering, and missing orchestration coverage.
- No live cell, host action, runtime edit, test run, capture, report, acceptance bound,
  `thresholds.json`, commit, or push occurred during the assessment.
- The self-contained findings and required continuation are recorded in
  [`assessment-addendum.md`](assessment-addendum.md). Resume at Stage 7.R1 with a real socket-level
  RED harness test; do not begin Stage 7.6 until Stages 7.R1-7.R6 pass review.

## Stage 7.R1 — socket lifecycle remediation

### Explore and plan

- Status: **Completed**.
- Mode: `auto`; only Stage 7.R1 is authorized in this context.
- Verified start: branch `backend-refactor-implementation`, HEAD `14576dd`, clean worktree. The
  loaded handoff's `3d23328`/dirty-state description is stale because the staged Step 03 work is
  now present in HEAD.
- Evidence guard: 12 reduced-v2 and two superseded full-v1 captures remain present and unchanged;
  `thresholds.json` and `pressure-ab-report.md` remain absent. No live cell or host/helper action
  is authorized.
- Test selection: harness tests for the real socket plus `load.py` lifecycle; focused tests for
  any generic broadcaster behavior changed. The RED test must use actual loopback sockets and
  the actual broadcaster queue/event loop.
- Planned correction: defer only the blocking `pressure_snapshot` ingestion command, retain all
  neighboring CLI behavior on the socket loop, synchronize request correlation, and wake pending
  requests before broadcaster shutdown.
- Pre-code compatibility command:
  `overlay_client/.venv/bin/python scripts/check_edmc_python.py`: **passed** with the expected
  64-bit-versus-recorded-32-bit warning; Python 3.12.3 satisfies the recorded >=3.10.3 baseline.

### TDD evidence

- Initial sandbox run could not bind `127.0.0.1` and failed at fixture setup; it was an
  environment limitation, not accepted RED evidence. The loopback tests were subsequently run
  outside that sandbox without changing host or helper configuration.
- Valid RED command:
  `overlay_client/.venv/bin/python -m pytest tests/test_harness_pressure_ab_snapshot.py::test_pressure_snapshot_real_socket_roundtrip_keeps_transport_responsive -q`:
  **1 failed as expected**. The real client received the request only after the requester had
  returned `client_snapshot_timeout`.
- Full pre-implementation lifecycle command:
  `overlay_client/.venv/bin/python -m pytest tests/test_harness_pressure_ab_snapshot.py -q`:
  **3 failed, 5 passed**. Success/correlation and shutdown exposed the blocking socket loop;
  existing direct timeout, malformed, and neighboring behavior remained green.
- First implementation GREEN exposed a separate active-stream shutdown bound: **7 passed,
  1 failed**, with shutdown consuming the broadcaster's full seven-second join escape hatch.
- A thread-stack probe located the remaining wait in the broadcaster's main server coroutine.
  Explicit thread-safe cancellation of only that owned task plus bounded writer cleanup reduced
  the shutdown test to **1 passed in 0.20s**.
- Final real-socket lifecycle command:
  `overlay_client/.venv/bin/python -m pytest tests/test_harness_pressure_ab_snapshot.py -q`:
  **8 passed in 0.38s**.

### Implementation result

- `SocketBroadcaster` now defers only configured blocking ingestion commands; `load.py`
  configures only `pressure_snapshot`. Neighboring commands retain synchronous socket-thread
  execution and response ordering.
- Pending pressure requests use a dedicated lock. The running-state check and registration are
  atomic with shutdown, responses require a matching request ID and strict snapshot parser, and
  runtime stop wakes and clears all pending waits before stopping the broadcaster.
- Broadcaster stop explicitly cancels its own asyncio server task and bounds active writer close;
  it does not cancel unrelated threads/tasks or move Tk/Qt work off their owning threads.

### Validation evidence

- Test file updated: `tests/test_harness_pressure_ab_snapshot.py`.
- Focused Task 07 command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_pressure_snapshot_window.py overlay_client/tests/test_backend_pressure_ab_runner.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_pressure_ab_snapshot.py -q`:
  **71 passed in 0.65s**.
- Neighboring CLI/runtime command:
  `overlay_client/.venv/bin/python -m pytest tests/test_harness_cli_ingestion.py tests/test_plugin_group_cli.py tests/test_runtime_services.py tests/test_harness_backend_status_roundtrip.py -q`:
  **13 passed in 6.36s**.
- Lifecycle tracking command:
  `overlay_client/.venv/bin/python -m pytest tests/test_lifecycle_tracking.py -q`:
  **4 passed in 0.18s**.
- `overlay_client/.venv/bin/python -m ruff check load.py overlay_plugin/overlay_socket_server.py tests/test_harness_pressure_ab_snapshot.py`:
  **passed**.
- `overlay_client/.venv/bin/python -m mypy load.py overlay_plugin/overlay_socket_server.py`:
  **passed; no issues in two source files**.
- `overlay_client/.venv/bin/python -m compileall -q load.py overlay_plugin/overlay_socket_server.py tests/test_harness_pressure_ab_snapshot.py`:
  **passed**.
- `git diff --check`: **passed**.
- Skips: **none** in the Stage 7.R1 commands. Full project and GUI-enabled gates are intentionally
  deferred to Stage 7.R6; no required Stage 7.R1 test was skipped.

### Completion audit

| Requirement | Result | Evidence |
| --- | --- | --- |
| Real broadcaster connection; no immediate `publish()` mock | Yes | Four lifecycle cases use actual loopback sockets and the actual queue/event loop |
| Reproduce and repair self-blocking request transport | Yes | Valid RED returned timeout; final correlated round trip is GREEN |
| Correlation and malformed response handling | Yes | Wrong ID and schema-invalid matching response leave the request pending; valid matching response resolves it |
| Bounded absence/timeout and cleanup | Yes | Real no-response request returns unavailable and leaves no pending entry |
| Bounded shutdown and cleanup | Yes | Runtime stop wakes the wait, clears state, cancels only broadcaster-owned work, and completes below one second |
| Neighboring CLI behavior/thread ownership | Yes | Real unsupported command preserves response behavior and executes on the broadcaster thread |
| Tk/Qt and fix219 backend boundary | Yes | Only the blocking plugin CLI handler is deferred; Qt signal dispatch and backend-owned presentation code are untouched |
| No live/host/evidence/threshold side effects | Yes | No cell, helper/host configuration, capture, report, baseline identity, or `thresholds.json` was created or changed |

### EDMC compliance review for the touched scope

- **Yes — core/API alignment:** no entry point, version gate, documented EDMC import, settings,
  player-state, or HTTP behavior changed; the recorded Python compatibility check passed.
- **Yes — logging/versioning:** no `print` or alternate logger was introduced.
- **Yes — responsive and Tk-safe runtime:** the network-bound wait is isolated from the socket
  event loop, is bounded, and is woken on shutdown; no Tk/Qt widget access changed threads.
- **Yes — prefs/UI integration:** preferences, config helpers, widgets, and UI hooks are untouched.
- **Yes — dependency/debug HTTP handling:** no dependency, HTTP client, debug sender, or packaging
  behavior changed.

### Remaining gate

At the end of its isolated context, Stage 7.R1 was complete while Stages 7.R2-7.R6 remained
pending. The following section records the later isolated Stage 7.R2 completion. Stage 7.6 live
preflight remained blocked, and no commit or push was performed.

## Stage 7.R2 — strict evidence contracts

### Explore and plan

- Status: **In progress**.
- Mode: `auto`; only Stage 7.R2 is authorized in this context. Aggregation/reporting (7.R3),
  runner hardening (7.R4), coverage completion (7.R5), and integrated completion (7.R6) must not
  begin here.
- Verified start: branch `backend-refactor-implementation`, HEAD `14576dd`, with exactly the seven
  intentional Stage 7.R1 modifications listed in its handoff. Historical captures remain held;
  no report or `thresholds.json` exists.
- Fresh compatibility/baseline command:
  `overlay_client/.venv/bin/python scripts/check_edmc_python.py && overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py -q`:
  **passed** with the expected architecture warning and **16 tests passed in 0.13s**.
- The initial in-sandbox Stage 7.R1 verification produced **3 passed, 5 fixture errors** because
  loopback bind is forbidden. Rerunning
  `overlay_client/.venv/bin/python -m pytest tests/test_harness_pressure_ab_snapshot.py -q`
  with localhost permission passed **8 tests in 0.35s**, verifying the handoff rather than
  reopening Stage 7.R1.
- Test selection: unit tests for the pure schema/parser/state/privacy contracts. No production
  `load.py` or lifecycle touchpoint is planned, so no new harness test is required. Existing
  socket harness coverage remains a focused regression gate.
- Planned implementation: one exact runner-shaped schema, frozen parsed sample/cell/run models,
  strict privacy and numeric allowlists, exact cell/state/argument validation, explicit
  unavailable values, whole-cell origin continuity, immutable four-document loading, and only
  the minimum runner metadata/output seam needed for direct compatibility.
- Expected unchanged behavior and exact planned commands are recorded in `plan.md` before any
  production edit. No live cell, host/helper mutation, flat-metrics aggregation, report,
  acceptance bound, baseline identity, commit, or push is authorized.

### TDD evidence

- Focused RED command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py -q`:
  **failed during collection as expected** with two import errors. The strict safety/sample/cell/
  run APIs and runner client-argument validator do not exist yet. No production file had been
  modified when this RED was recorded.
- RED tests added to `overlay_client/tests/test_pressure_ab.py` cover exact A1/A2/B1/B2 sample
  shapes, strict privacy rejection, numeric bounds and saturation, diagnostics and safety,
  explicit unavailable values, whole-cell origins, exact state/argument contracts, provenance,
  execution order, completeness, and distinct immutable cell files.
- RED coverage added to `overlay_client/tests/test_backend_pressure_ab_runner.py` requires exact
  PID/port-file presence for running versus stopped client cells.

### Implementation result

- Status: **Completed**.
- `overlay_client/backend/pressure_ab.py` now exposes frozen parsed distribution, resource,
  work, actor, provenance, sample, cell, and complete-run models. Exact-key parsers reject
  unknown schemas, privacy-prohibited keys/path-like values, unsafe types, non-finite or
  out-of-bound values, saturated counters, unsafe continuity, diagnostics-on samples, and any
  asserted safety failure.
- Exact cell contracts require A1/A2/B1/B2 client/helper/backend states, both-or-neither client
  PID/port-file declarations, three ordered repetitions, fixed 300/60 timing, explicit
  unavailable resource/work/origin fields, and one client/helper origin across the complete
  post-warm-up cell.
- Provenance requires a sanitized fixture hash, source revision, fixed component versions,
  monitor-A 100% display/refresh values, fixed stable-windowed workload, quiet-host decision,
  and unique actual execution order. The complete loader requires four distinct stable JSON
  files and returns exactly one frozen A1/A2/B1/B2 run in actual order.
- `scripts/backend_pressure_ab.py` now accepts the required provenance/order inputs, validates
  exact client arguments and backend state, emits explicit unavailable fields, uses a random
  safe helper evidence origin rather than serializing the raw helper clock origin, rejects
  client/helper saturation or origin changes, and parses its exact document before writing.
- The known GPU-available provider remains deliberately deferred to Stage 7.R4. Stage 7.R2
  preserves its current unavailable behavior explicitly so static typing is truthful; it does
  not move or repair the unreachable provider implementation early.
- Existing flat-metrics aggregation remains unused historical code pending the isolated Stage
  7.R3 replacement. No contrast, acceptance-bound, or Markdown report logic was added.

### Validation evidence

- Test files updated:
  `overlay_client/tests/test_pressure_ab.py` and
  `overlay_client/tests/test_backend_pressure_ab_runner.py`.
- Final Stage 7.R2 unit command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py -q`:
  **67 passed in 0.21s**.
- Final focused Task 07 command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_pressure_snapshot_window.py overlay_client/tests/test_backend_pressure_ab_runner.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_pressure_ab_snapshot.py -q`:
  **122 passed in 0.62s** with localhost permission for the real-socket cases.
- `overlay_client/.venv/bin/python -m ruff check overlay_client/backend/pressure_ab.py scripts/backend_pressure_ab.py overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py`:
  **passed**.
- `overlay_client/.venv/bin/python -m mypy overlay_client/backend/pressure_ab.py scripts/backend_pressure_ab.py`:
  **passed; no issues in two source files**.
- `overlay_client/.venv/bin/python -m compileall -q overlay_client/backend/pressure_ab.py scripts/backend_pressure_ab.py overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py`:
  **passed**.
- `overlay_client/.venv/bin/python scripts/backend_pressure_ab.py --help`: **passed** and exposes
  the strict execution-order, fixture/source/component-version, display/refresh, quiet-host, and
  backend-state arguments.
- `git diff --check`: **passed**. Explicit artifact scan found no `thresholds.json` or
  `pressure-ab-report.md`.
- Skips: **none** in Stage 7.R2 commands. Project-wide `make check`/`make test`, full integrated
  query/repaint coverage, full `_capture()` orchestration, and GUI gates remain mandatory in
  Stages 7.R5-7.R6; they were not weakened or claimed here.

### Completion audit

| Requirement | Result | Evidence |
| --- | --- | --- |
| Direct compatibility with runner nested output | Yes | Runner builds nested resource/work/actor/warning/safety documents and calls the strict cell parser before write; no flat `metrics` adapter is used |
| Exact A1/A2/B1/B2 states | Yes | Fixed state matrix covers stopped/running client, disabled/full helper, and unavailable/helper-selected backend declarations |
| Exactly three repetitions per cell | Yes | Cell parser requires the ordered tuple 1, 2, 3; complete loader requires every cell |
| Fixed 300-second warm-up and 60-second observation | Yes | Every parsed sample requires exact 300/60 values |
| Diagnostics off | Yes | Cell state and every sample fail unless diagnostics fields are false |
| Sanitized provenance and actual execution order | Yes | Strict hash/revision/version/display/workload/quiet-host schema plus unique order 1-4 |
| Safety fields | Yes | Every fixed safety field is mandatory and any true value rejects the sample |
| Bounded counters/resources | Yes | Exact work/actor/warning keys, finite distributions, fixed observation counts, and numeric maxima are enforced |
| Saturation, decrease, restart, and origin rejection | Yes | Snapshot endpoints reject saturation/decrease; strict continuity flags fail closed; cell parsing requires one safe origin across all three samples |
| Client/helper state continuity across the cell | Yes | Availability must match the cell in every sample and available origins must remain identical across the post-warm-up cell |
| Explicit unavailable fields | Yes | Stopped client and disabled helper require reason, unavailable origin, and empty fixed mappings; omission or `{}` fails |
| Exact client argument pairing | Yes | Running-client cells require both PID and port-file presence; stopped-client cells require neither; partial/extra pairs fail |
| Privacy and host-data rejection | Yes | Exact nested schemas plus prohibited key and path-like string scanning reject PIDs, paths, titles, handles, commands, journal/helper payloads, tokens, and host identity fields |
| Four immutable cell documents | Yes | Loader requires four distinct stable files, exact cell completeness, identical fixed provenance, and returns frozen models |
| Stage 7.R3 scope excluded | Yes | No compatible aggregation, contrasts, bounds, or report rendering was implemented |
| Architectural/global constraints | Yes | Generic parser imports no compositor implementation; no live cell, host/helper mutation, capture, report, baseline identity, threshold file, commit, or push occurred |

### EDMC compliance review for the touched scope

- **Yes — core/API alignment:** plugin entry points, EDMC imports/helpers, configuration, player
  state, and HTTP behavior are untouched; the compatibility command passed.
- **Yes — logging/versioning:** no plugin logger, `print`, traceback, or EDMC version behavior
  changed. Existing CLI progress output remains outside EDMC plugin hooks.
- **Yes — responsive and Tk-safe runtime:** all new contracts are pure/data-only; no Tk/Qt,
  socket, timer, or plugin-thread ownership changed.
- **Yes — prefs/UI integration:** preferences, EDMC config helpers, widgets, and UI hooks are
  untouched.
- **Yes — dependency/debug HTTP handling:** no dependency, network provider, HTTP client, debug
  sender, or packaging behavior changed.

### Remaining gate

Stage 7.R2 is complete. Stages 7.R3-7.R6 remain pending, so Stage 7.6 live preflight remains
blocked. No commit or push was performed; Stage 3.16 remains the commit boundary.

## Stage 7.R3 — analysis and report pipeline

### Explore and plan

- Status: **In progress**.
- Mode: `auto`; only Stage 7.R3 is authorized. Runner hardening (7.R4), coverage completion
  (7.R5), integrated completion (7.R6), and live preflight/capture must not begin here.
- Verified start: branch `backend-refactor-implementation`, HEAD `14576dd`, with exactly the 11
  cumulative Stage 7.R1/7.R2 modifications listed in the handoff. Patch hygiene passes;
  historical captures remain held; no report or `thresholds.json` exists.
- Fresh compatibility/baseline command:
  `overlay_client/.venv/bin/python scripts/check_edmc_python.py && overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py -q`:
  **passed** with the expected architecture warning and **67 tests passed in 0.20s**.
- Test selection: unit tests for pure strict-run analysis, contrast arithmetic, reviewed-bound
  parsing/evaluation, and deterministic Markdown. No new harness is required because no plugin,
  lifecycle, socket, runner-provider, or UI touchpoint is planned.
- Chosen analysis seam: aggregate only frozen `PressureAbRun` values. Each repetition contributes
  its resource median or exact 60-second counter/actor/warning value; all three repetitions feed
  deterministic median/p95/range statistics.
- Structural absence is distinct from provider unavailability. Stopped client/disabled helper
  measures contribute explicit zeros needed for A/B attribution; unavailable GPU/warning data
  remains unavailable and mixed availability is rejected.
- Reviewed bounds use a strict fixed method that requires all repetitions and prohibits
  favorable-singleton selection. Bounds and provenance exist only as in-memory report inputs
  and rendered Markdown; no threshold JSON serializer or real acceptance artifact is added.
- Expected unchanged behavior, required RED cases, and exact commands are recorded in `plan.md`
  before production edits.

### TDD evidence

- Focused RED command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py -q`:
  **failed during collection as expected** because `PRESSURE_AB_CONTRASTS` and the new strict-run
  analysis/bounds/report APIs do not exist. No Stage 7.R3 production code had been written.
- RED coverage in `overlay_client/tests/test_pressure_ab.py` now requires nested metric
  aggregation, structural-zero/unavailable separation, mixed-provider rejection, all five exact
  contrasts, strict-run-only input, reviewed-bound provenance/validation/evaluation,
  deterministic sanitized Markdown, and memory-only synthetic rendering.

### Implementation result

- Status: **Completed**.
- `overlay_client/backend/pressure_ab_report.py` is a new pure/data-only module that consumes
  only the frozen `PressureAbRun` model. It aggregates every fixed nested resource, client-work,
  helper-work, actor, and normalized warning metric across all three repetitions using median,
  nearest-rank p95, minimum, maximum, and count.
- Resource inputs use each 60-observation repetition median; the rendered report states this
  explicitly. Work/warning measures remain exact fixed-window counts and actor values remain
  bounded sample state.
- Stopped-client and disabled-helper measures are explicit structural zero for A/B attribution.
  GPU/warning provider unavailability remains unavailable, and mixed availability within one
  cell rejects the analysis.
- The analysis calculates exactly enabled-idle `B1-A1`, client/helper-disabled `A2-A1`,
  client/helper-enabled `B2-B1`, interaction `(B2-B1)-(A2-A1)`, and integrated `B2-A1` from
  per-cell medians. Any genuine provider absence propagates as unavailable.
- Reviewed bounds require strict sanitized provenance, `reviewed` state, the fixed
  all-repetitions/no-favorable-singleton method, unique available metric/contrast pairs,
  inclusive numeric ranges, and explicit absolute noise floors. Evaluation is deterministic and
  frozen; no JSON serializer or threshold writer exists.
- Markdown rendering has stable cell/metric/contrast/bound ordering and includes sanitized
  provenance, actual execution order, all cell statistics, five formula definitions and values,
  bound provenance/results, and an explicit pressure-bound versus migration-threshold warning.
- The permissive legacy flat `sample["metrics"]` summary and shallow completion validator were
  removed. The Stage 7.R2 strict run model is now the only analysis/report input.
- Refactor: analysis/reporting was carved out of the schema module, leaving
  `pressure_ab.py` focused on strict evidence contracts and `pressure_ab_report.py` focused on
  deterministic analysis/output.
- No runner, provider, `load.py`, socket, Tk/Qt, compositor, or live-safety behavior changed;
  those remain Stage 7.R4 or later.

### Validation evidence

- Test file updated: `overlay_client/tests/test_pressure_ab.py`.
- Valid RED:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py -q`:
  **failed during collection as expected** on missing Stage 7.R3 APIs.
- Final Stage 7.R3 unit command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py -q`:
  **72 passed in 0.32s**.
- Final focused Task 07 command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_pressure_snapshot_window.py overlay_client/tests/test_backend_pressure_ab_runner.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_pressure_ab_snapshot.py -q`:
  **141 passed in 0.72s** with localhost permission for the real-socket cases.
- `overlay_client/.venv/bin/python -m ruff check overlay_client/backend/pressure_ab.py overlay_client/backend/pressure_ab_report.py overlay_client/tests/test_pressure_ab.py`:
  **passed**.
- `overlay_client/.venv/bin/python -m mypy overlay_client/backend/pressure_ab.py overlay_client/backend/pressure_ab_report.py`:
  **passed; no issues in two source files**.
- `overlay_client/.venv/bin/python -m compileall -q overlay_client/backend/pressure_ab.py overlay_client/backend/pressure_ab_report.py overlay_client/tests/test_pressure_ab.py`:
  **passed**.
- `git diff --check`: **passed**. Explicit artifact scan found no `thresholds.json` or
  `pressure-ab-report.md`.
- Skips: **none** in Stage 7.R3 commands. Full project/integrated/GUI and `_capture()`
  orchestration gates remain mandatory at Stages 7.R5-7.R6 and were not claimed here.

### Completion audit

| Requirement | Result | Evidence |
| --- | --- | --- |
| Strict complete-run input only | Yes | Analysis requires `PressureAbRun`, rechecks four cells/order/repetitions/safety/continuity, and legacy permissive summary APIs were removed |
| Runner-compatible per-cell aggregation | Yes | Every nested resource/work/actor/warning path is extracted directly from parsed runner samples |
| Median, nearest-rank p95, and range | Yes | Every compatible cell metric uses all three repetitions and reports median/p95/minimum/maximum/count |
| Structural absence versus provider unavailability | Yes | Stopped/disabled components contribute labeled structural zero; GPU/warning absence propagates as unavailable; mixed availability rejects |
| `B1-A1` | Yes | Fixed `enabled_idle_helper` contrast and report formula |
| `A2-A1` | Yes | Fixed `client_helper_disabled` contrast and report formula |
| `B2-B1` | Yes | Fixed `client_helper_enabled` contrast and report formula |
| `(B2-B1)-(A2-A1)` | Yes | Fixed `helper_client_interaction` four-operand contrast and report formula |
| `B2-A1` | Yes | Fixed `overall_integrated` contrast and report formula |
| Reviewed acceptance-bound inputs | Yes | Strict reviewed provenance/method, unique compatible pairs, inclusive ranges, and absolute noise floors are validated and frozen |
| Bound evaluation | Yes | Exact selected contrast is evaluated deterministically with its inclusive range and preserved absolute noise floor |
| Deterministic Markdown | Yes | Equivalent run/bound order produces byte-identical sanitized output with all required sections |
| Incomplete/unsafe/schema/privacy rejection | Yes | Four-file strict loader/parser precedes analysis; analysis rejects forged partial/unsafe/mixed evidence; bound privacy/schema validation fails closed |
| End-to-end four-file pipeline | Yes | Unit test loads four distinct stable temporary files, analyzes them, validates bounds, and renders in-memory Markdown |
| Report-only bounds and threshold separation | Yes | Bounds have no JSON serializer; Markdown states separation; no real report or `thresholds.json` exists |
| Stage 7.R4 scope excluded | Yes | `_capture()`, GPU/warning/process providers, state proof, timing, safety stopping, and output behavior are untouched |
| Architectural/global constraints | Yes | Pure module imports only generic strict evidence models; no live/host/helper/config/capture/baseline/commit/push action occurred |

### EDMC compliance review for the touched scope

- **Yes — core/API alignment:** plugin entry points, EDMC APIs/helpers, configuration, player
  state, and HTTP behavior are untouched; the compatibility command passed.
- **Yes — logging/versioning:** no plugin logger, `print`, traceback, or version behavior changed.
- **Yes — responsive and Tk-safe runtime:** the new module is pure/data-only and performs no
  runtime I/O; Tk/Qt/socket ownership is untouched.
- **Yes — prefs/UI integration:** preferences, config helpers, widgets, and UI hooks are untouched.
- **Yes — dependency/debug HTTP handling:** no dependency, HTTP, debug-sender, or packaging
  behavior changed.

### Remaining gate

Stage 7.R3 is complete. Stages 7.R4-7.R6 remain pending, so Stage 7.6 live preflight remains
blocked. No commit or push was performed; Stage 3.16 remains the commit boundary.

## Stage 7.R4 — runner state/provider/timing/safety hardening

### Explore and plan

- Status: **In progress**; mode is `auto` and this isolated context is authorized for R4 only.
- Resumed the complete handoff with the `handoff` skill and reapplied the `code-assist` workflow.
  Verified branch/HEAD, cumulative worktree, patch hygiene, authorities, evidence hold, and
  absent prohibited artifacts before planning production changes.
- Baseline commands passed: `overlay_client/.venv/bin/python scripts/check_edmc_python.py`
  reported only the expected 64-bit development-architecture warning, and
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py -q`
  reported **86 passed in 0.33s**.
- Test selection is **unit** because only the standalone runner and injected pure/provider seams
  change. `load.py`, lifecycle hooks, sockets, EDMC shims, and UI are untouched; R1 harness tests
  remain in the focused regression command.
- The expanded stage table, exact input/output scenarios, touchpoints, unchanged behavior,
  timing/state/safety/output design, and exact validation commands are recorded in `plan.md`
  before production edits. No live cell, host/helper mutation, capture artifact, report,
  threshold, baseline identity, commit, or push is authorized.

### TDD evidence

- Focused RED command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_pressure_ab_runner.py -q`:
  **failed during collection as expected** because the new `CaptureProviders`/timing/safety and
  provider-validation APIs do not exist. All R4 test changes preceded production runner edits.
- RED scenarios cover exact helper owner and live A2/B2 route proof; GPU and scoped journal
  available/error paths; process restart; aligned fake-clock observation; full fake 300/60/3
  capture; whole-cell continuity; repeated-assertion/high-CPU stops; sanitized interruption
  evidence; and exclusive non-overwriting output.

### Implementation result

- Status: **Completed**.
- `scripts/backend_pressure_ab.py` now exposes frozen `CaptureProviders` and `CaptureTiming`
  seams. Unit tests advance a fake monotonic/epoch clock through the full declared 300-second
  warm-up and all three 60-observation repetitions without wall-clock waiting.
- Helper-disabled proof calls the session bus `NameHasOwner` method and accepts only exact false;
  timeouts, transport failures, nonzero status, and malformed output fail closed. Enabled helper
  health requires the exact service/kind/protocol, healthy `full_helper` state, diagnostics off,
  bounded counters/actors, a version, and a stable origin.
- Running-client cells require the exact PID/port pair plus bounded process identity. The status
  provider performs a bounded priming retry for the existing backend-status cache and accepts
  only `client_runtime` evidence. A2 requires the exact missing-helper fallback; B2 requires the
  selected compositor-helper GNOME route with one versioned available/approved helper.
- `/proc` sampling now includes process start ticks and bounded parse/CPU/context/RSS checks.
  NVIDIA absence is explicit; available multi-device results use mean utilization and total
  memory, with per-device/aggregate bounds and clean timeout/nonzero/malformed rejection.
- Journal collection uses exact `--since`/`--until` JSON windows and only allowlisted metadata to
  classify Mutter assertions and GNOME Shell warnings. Raw text is discarded; timeout, nonzero,
  malformed, wall-clock drift, availability change, and saturation fail closed.
- Warm-up and observation share one safety tracker. Two Mutter assertions anywhere in the timed
  cell or three consecutive Shell CPU samples at/above the fixed 80-percent emergency bound
  produce a typed stop. `--operator-observing` makes continuous visible-failure/Ctrl-C duty
  explicit; interruption is normalized with the active phase.
- Client snapshot origin, helper origin, process start identity, and runtime route are checked
  across the complete post-warm-up cell. Client/helper endpoint decreases and saturation reject
  the sample before any accepted document can be built.
- Accepted output and sanitized stop evidence both use exclusive creation. A stop document is a
  distinct `accepted: false` artifact with fixed phase/reason/safety/provenance fields, no partial
  samples, PIDs, paths, raw payloads, journal text, or exception details. Existing files and
  create races are never overwritten.
- Refactor removed the post-sample manual prompt and unreachable GPU block. Work/resource/helper/
  warning collection now shares one bounded tick schedule and strict parser validation remains
  the final accepted-cell gate.

### Validation evidence

- Test file updated: `overlay_client/tests/test_backend_pressure_ab_runner.py`.
- Initial focused RED: collection error on missing `CaptureProviders`, as recorded above.
- Audit RED subcycle: **10 failed, 52 passed** on exact helper identity, live-status priming,
  aggregate GPU bounds, clock alignment, cumulative assertions, and stop-provenance privacy.
- Defensive RED subcycle: **6 failed, 62 passed** on malformed tuple decoding, helper transport
  normalization, exact helper availability/version, and injected GPU bounds.
- Final runner unit command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_pressure_ab_runner.py -q`:
  **73 passed in 0.24s**.
- Final focused Task 07 command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_pressure_snapshot_window.py overlay_client/tests/test_backend_pressure_ab_runner.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_pressure_ab_snapshot.py -q`:
  **200 passed in 0.81s** with localhost permission for the existing real-socket cases.
- The same focused command first ran inside the restricted sandbox during development and
  reported **169 passed, 5 fixture errors** solely because loopback bind was denied; its
  permission-enabled rerun passed before the final expanded 200-test gate.
- `overlay_client/.venv/bin/python -m ruff check scripts/backend_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py`:
  **passed**.
- `overlay_client/.venv/bin/python -m mypy scripts/backend_pressure_ab.py`:
  **passed; no issues in one source file**.
- `overlay_client/.venv/bin/python -m compileall -q scripts/backend_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py`:
  **passed**.
- `overlay_client/.venv/bin/python scripts/backend_pressure_ab.py --help`: **passed** and exposes
  the required continuous-observation acknowledgement.
- `overlay_client/.venv/bin/python scripts/check_edmc_python.py`: **passed** with only the expected
  64-bit development-architecture warning against the recorded 32-bit preference.
- `git diff --check`: **passed**. The explicit artifact scan found no `thresholds.json`, real
  `pressure-ab-report.md`, or clean baseline identity.
- Skips: **none** in the R4 test commands. Project-wide, integrated, full coverage-inventory,
  and GUI gates remain assigned to R5-R6 and were not claimed here.

### Completion audit

| Requirement | Result | Evidence |
| --- | --- | --- |
| Exact client arguments/state | Yes | Paired PID/port contract, process identity, authoritative live backend status, exact A2/B2 validators, and boundary rechecks |
| Proven helper-disabled classification | Yes | Only exact `NameHasOwner=false` passes; uncertainty and presence reject |
| Exact enabled-helper state | Yes | Healthy service/kind/protocol/version, `full_helper`, diagnostics-off, aggregates, and stable origin are mandatory |
| A2 fallback proof | Yes | Live client-runtime status must show native GNOME selection, compositor-helper fallback, `missing_helper`, and exact unavailable helper state |
| B2 selected-route proof | Yes | Live client-runtime status must show compositor-helper/GNOME selection and one versioned available/approved helper with no fallback |
| Whole-cell continuity | Yes | Client/helper/process origins and client route are rechecked through every post-warm-up boundary/tick |
| GPU available/unavailable | Yes | Explicit absence or bounded mean-utilization/total-memory distributions; timeout/nonzero/malformed/change reject |
| Aligned fixed windows | Yes | Injected monotonic/epoch one-second schedule spans warnings/resources/helper state inside client/helper work endpoints and rejects clock/drift mismatch |
| Restart/decrease/saturation rejection | Yes | Process origins and client/helper/warning endpoints fail closed; no sentinel can become false zero |
| Warning scope/failure behavior | Yes | Exact JSON intervals, allowlisted source metadata, normalized counts only, and clean timeout/malformed failure |
| Provenance/order/privacy | Yes | Strict early provenance/order validation and final cell parser; stop evidence uses only fixed sanitized fields |
| Warm-up/observation safety | Yes | Shared assertion/CPU tracker plus explicit continuous operator/Ctrl-C responsibility and phase-aware stops |
| Interruption and stop evidence | Yes | Keyboard interruption in both timed phases becomes an exclusive sanitized non-acceptance document |
| Non-overwriting output | Yes | Success and stop writers use exclusive-create; pre-existing output and create races fail |
| No real timing in tests | Yes | Complete A1/B2 and safety/continuity orchestration advance injected fake clocks through 300/60/3 |
| Architectural/global constraints | Yes | No runtime/backend behavior, host/helper state, live cell, report, threshold, baseline identity, commit, or push changed |

### EDMC compliance review for the touched scope

- **Yes — core/API alignment:** the standalone client-side runner changes no EDMC plugin entry
  point, supported API import, settings, player-state, or HTTP behavior; the compatibility check
  passed.
- **Yes — logging/versioning:** EDMC logger wiring is untouched. Human progress output remains in
  the standalone CLI, not an EDMC hook, and evidence/error payloads contain no raw trace text.
- **Yes — responsive and Tk-safe runtime:** no Tk/Qt or EDMC hook work changed; all timing and I/O
  belong to the explicitly invoked measurement CLI.
- **Yes — prefs/UI integration:** preferences, `myNotebook`, config helpers, and UI hooks are
  untouched.
- **Yes — dependency/debug HTTP handling:** no dependency, packaging, HTTP, or debug-sender
  behavior changed.

### Remaining gate

At the R4 boundary, Stage 7.R4 was complete and Stages 7.R5-7.R6 remained pending, so Stage 7.6
live preflight remained blocked. No commit or push was performed; Stage 3.16 remains the commit
boundary.

## Stage 7.R5 — coverage completion and focused/integrated RED/GREEN

### Explore and plan

- Status: **Completed**; Context 5 was authorized for R5 only and did not start R6.
- Resumed `/tmp/handoff-20260802-084202.md` with the `handoff` and `code-assist` skills. Verified
  branch `backend-refactor-implementation`, HEAD `14576dd`, the cumulative R1-R4 worktree,
  authorities, patch hygiene, capture hold, 12 reduced-v2 plus two superseded full-v1 captures,
  and absence of a real report, `thresholds.json`, or clean baseline identity.
- Test selection was explicit before code: unit tests for deterministic/injected runner, provider,
  and output gaps; the existing real-socket harness for H1-H3 lifecycle regression. No R5
  `load.py`, hook, broadcaster, Tk/Qt, or EDMC lifecycle behavior changed, so no new harness test
  was required.
- The named U5-U12/H1-H3/O1-O8 traceability matrix, residual cases R5-U1 through R5-U10,
  touchpoints, unchanged contracts, and exact commands were recorded in `plan.md` before edits.
- Compatibility passed with only the expected 64-bit development warning. The five-file
  pre-change baseline passed **200 tests in 0.83s** with localhost permission.

### TDD evidence

- First expanded runner command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_pressure_ab_runner.py -q`:
  **2 failed, 100 passed**. One failure was an invalid new test assumption that used the process
  ceiling instead of the shared `WORK_COUNTER_MAX`; correcting that fixture proved the existing
  helper-saturation behavior was already safe. The other was valid RED: success-output
  `OSError` escaped `main()` and exposed its raw private exception.
- Corrected focused RED command:
  `overlay_client/.venv/bin/python -m pytest 'overlay_client/tests/test_backend_pressure_ab_runner.py::test_capture_rejects_unsafe_work_endpoints[helper-saturation]' overlay_client/tests/test_backend_pressure_ab_runner.py::test_main_normalizes_output_write_failure_without_private_path -q`:
  **1 failed, 1 passed**; only output-write normalization remained RED.
- Direct writer RED command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_pressure_ab_runner.py::test_exclusive_json_writer_removes_its_partial_file_on_write_failure -q`:
  **1 failed** because a serialization/write `OSError` left the exclusively created partial file.
- These tests preceded their respective production fixes. No live clock, process, helper, client,
  journal, GPU, report, or capture was used.

### Implementation result

- `overlay_client/tests/test_backend_pressure_ab_runner.py` gained 32 tests/cases completing the
  residual matrix: direct `/proc` parsing and clean failure; explicit warning absence; malformed
  helper aggregates; client transport/malformed/status exhaustion; warning/GPU availability
  transitions; exact A2/B1 fake-clock capture to complement A1/B2; pre-timing invalid-input
  rejection; client/helper decrease and saturation through `_capture()`; success/provider/write
  `main()` paths; and partial-file cleanup.
- `scripts/backend_pressure_ab.py` now removes only the exclusive output file it created if its
  serialization or write fails, then re-raises. `main()` converts output `OSError` for success,
  typed-stop, and raw-interrupt paths into a fixed sanitized message and exit status 2. Existing
  files remain untouched and raw paths are not printed.
- The R1 harness remains the H1-H3 proof: real matching socket response, malformed/wrong-ID/
  timeout/shutdown cleanup, and neighboring CLI behavior. Existing R2/R3 tests remain the U5-U10
  schema/aggregation/attribution/privacy proof.

### Validation evidence

- Test file updated: `overlay_client/tests/test_backend_pressure_ab_runner.py`.
- Production file updated in R5: `scripts/backend_pressure_ab.py`.
- Final runner unit command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_pressure_ab_runner.py -q`:
  **105 passed in 0.36s**.
- Final focused Task 07 command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_pressure_snapshot_window.py overlay_client/tests/test_backend_pressure_ab_runner.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_pressure_ab_snapshot.py -q`:
  **232 passed in 0.86s** with localhost permission.
- Integrated query/repaint/helper/harness command:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_payload_dedupe.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py tests/test_harness_pressure_ab_snapshot.py -q`:
  **159 passed in 1.45s** with localhost permission.
- `overlay_client/.venv/bin/python -m ruff check scripts/backend_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py`:
  **passed**.
- `overlay_client/.venv/bin/python -m mypy scripts/backend_pressure_ab.py`: **passed; no issues in
  one source file**.
- `overlay_client/.venv/bin/python -m compileall -q overlay_client scripts/backend_pressure_ab.py`:
  **passed**.
- `overlay_client/.venv/bin/python scripts/backend_pressure_ab.py --help`: **passed** and retains
  the required continuous-observation acknowledgement.
- `overlay_client/.venv/bin/python scripts/check_edmc_python.py`: **passed** with only the expected
  64-bit development-architecture warning against the recorded 32-bit preference.
- `git diff --check`: **passed**. Corrected inventory commands found exactly 12 reduced-v2 and two
  superseded full-v1 capture files, no changes below the performance evidence directory, and no
  real `pressure-ab-report.md`, `thresholds.json`, or clean baseline identity. An initial
  inventory command used a nonexistent root-level `performance` path and was discarded; the
  corrected repository path is `docs/support/validation/fix219-pre-migration/performance`.
- Skips: **none** in R5 commands. Project-wide `make check`, `make test`, full headless/GUI gates,
  current EDMC upstream-baseline review, and final implementation audit remain R6 scope.

### Completion audit

| Requirement | Result | Evidence |
| --- | --- | --- |
| U5-U10 strict stopped-state/schema/statistics/unsafe/four-cell/privacy coverage | Yes | Named R2/R3 tests plus full A1/A2/B1/B2 fake orchestration and focused 232-test gate |
| U11 direct bounded `/proc` aggregates | Yes | Spaced-name exact parse plus missing/short/status/bounds and sanitized-failure cases |
| U12 GPU available/unavailable behavior | Yes | Direct provider cases plus sampler availability-change rejection |
| H1 matching real response | Yes | Existing `test_pressure_snapshot_real_socket_roundtrip_keeps_transport_responsive` passed |
| H2 absence/malformed/timeout/shutdown cleanup | Yes | Existing real-socket correlation, timeout, shutdown, and pending-state cases passed |
| H3 neighboring CLI behavior | Yes | Existing `test_neighboring_cli_command_remains_on_socket_thread` passed |
| Full fixed fake orchestration | Yes | A1/A2/B1/B2 each complete three strict repetitions after exactly 480 fake seconds |
| Endpoint/provider failure closure | Yes | Client/helper decrease/saturation and GPU/warning availability transitions reject through orchestration |
| Provider input closure | Yes | Direct process/helper/client malformed, missing, transport, bound, and retry-exhaustion tests fail cleanly |
| Early validation | Yes | Order/provenance/quiet/operator failures occur before any injected sleep |
| Success/stop/failure output closure | Yes | Exclusive success/stop, provider no-output, sanitized write failure, and owned partial-file cleanup pass |
| Architectural/global constraints | Yes | No backend-boundary violation, live cell, host/helper mutation, evidence/report/threshold/baseline change, commit, or push |

### EDMC compliance review for the touched scope

| EDMC best-practice item | Yes/No | Evidence or required change |
| --- | --- | --- |
| Stay aligned with EDMC core | Yes | R5 did not change plugin layout or `plugin_start3`; the recorded Python floor check passed. Current upstream release recheck remains an explicit R6 release gate. |
| Use only supported plugin APIs/helpers | Yes | R5 changed only the standalone runner and its unit tests; plugin imports, settings, monitor/session helpers, and namespaced config behavior are untouched. |
| Follow EDMC logging/versioning patterns | Yes | Plugin logger/version wiring is untouched; fixed CLI stderr belongs to the standalone runner and contains no traceback/raw path. |
| Keep hooks responsive and Tk-safe | Yes | No hook, worker, socket ownership, Tk/Qt, shutdown, or `config.shutting_down` behavior changed in R5. |
| Integrate prefs/UI hooks correctly | Yes | `plugin_prefs`, `prefs_changed`, `plugin_app`, `myNotebook`, theme, and config helper use are untouched. |
| Package dependencies and debug HTTP responsibly | Yes | No dependency, packaging, HTTP, `requests`, `timeout_session`, or `config.debug_senders` behavior changed. |

### Remaining gate

At the R5 boundary, Stage 7.R6 remained pending and Stage 7.6 remained blocked. The R6 completion
record below supersedes that intermediate status. No commit or push was performed; Stage 3.16
remains the commit boundary.

## Stage 7.R6 — integrated completion audit

### Explore and plan

- Status: **Completed**; Context 6 was authorized for R6 only and did not start live work.
- Resumed `/tmp/handoff-20260802-085738.md` using `handoff` and `code-assist`. Verified the exact
  branch/HEAD/worktree, goal, authorities, patch hygiene, capture hold, evidence counts, and
  prohibited-artifact absence before expanding the R6 plan.
- Test selection, the R1-R6 requirement/evidence matrix, touchpoints, unchanged contracts, exact
  project commands, and review scopes are recorded in `plan.md` before production changes.
- Current official EDMC review found a real pre-gate defect: upstream `.python-version` is `3.13`
  and `docs/Releasing.md` names 3.13.9 32-bit, while the repository source/check still uses a
  permissive 3.10.3 minimum. R6-D1 is assigned pure unit/source tests; no lifecycle/harness change
  is involved. Remaining project gates pause until D1 is GREEN.

### R6-D1 TDD evidence and result

- RED command: `overlay_client/.venv/bin/python -m pytest tests/test_check_edmc_python.py -q`:
  **8 failed** on the stale source file, minimum-only comparison, future-series and wrong-arch
  acceptance, `SystemExit(0)` override behavior, and missing non-parity CI declaration.
- GREEN command: the same command reported **8 passed in 0.04s**.
- Updated `docs/compliance/edmc_python_version.txt` to `3.13.9 32bit`. The checker now requires
  3.13.9+ within the 3.13 series and exact 32-bit release parity. A mismatch fails unless the
  documented non-release/development override is explicit.
- `.github/workflows/ci.yml` now runs its main suite on Python 3.13 and sets the override because
  hosted Linux jobs are 64-bit; the existing Python 3.10 job remains a separate compatibility
  check. `docs/compliance/edmc_compliance.md` records dated official release/discussion evidence.
- Exact local release-parity command without override exited **1** as intended: local Python
  3.12.3/64-bit is not EDMC's tested 3.13.9+/3.13/32-bit runtime. The same command with
  `ALLOW_EDMC_PYTHON_MISMATCH=1` exited **0** with an explicit warning; this is development
  evidence, not a false parity claim.
- Targeted Ruff, mypy, and `git diff --check` passed for D1. No harness test was added because D1
  changes only a deterministic checker, static CI contract, and compliance sources.

### Cumulative audit findings R6-D2/D3

- R6 broad gates initially passed, but direct source review correctly treated that as insufficient
  proof: `load.py:get_backend_status()` still synchronously waits on a backend-status
  `threading.Event`, and `load.py` still imports/dispatches GNOME-specific raster cleanup.
- Both are explicit known failures in the detailed design's EDMC compliance gate and must be
  remediated before Stage 7.6 readiness. Harness RED scenarios and unchanged client-owned cleanup
  behavior are frozen in `plan.md` before implementation.

### R6-D2/D3 RED/GREEN and audit result

- RED command:
  `overlay_client/.venv/bin/python -m pytest tests/test_harness_backend_status_roundtrip.py tests/test_harness_plugin_hooks_contract.py -q`
  reported **3 failed, 3 passed**: the silent-client preferences read took about one second,
  backend-status pending `Event` state remained, and `load.py` retained private GNOME cleanup.
- `get_backend_status()` now queues a rate-limited refresh and immediately returns a fresh/stale
  client cache or backend-neutral shadow hint. Client pushes update a lock-protected cache; no
  pending status `Event` or synchronous request method remains.
- Plugin startup/stop no longer selects or clears GNOME raster state and no longer imports the
  private presentation helper. Existing launcher ownership is unchanged.
- GREEN: the two files pass **6 tests**; combined with
  `overlay_client/tests/test_launcher_shell_raster_shutdown.py`, **12 tests passed in 0.35s**.
  The first combined execution session stalled without leaving a pytest process; isolated and
  repeated combined runs passed, so no product deadlock was reproduced.

### Final validation evidence

| Gate | Exact command | Result |
| --- | --- | --- |
| Python checker unit contract | `overlay_client/.venv/bin/python -m pytest tests/test_check_edmc_python.py -q` | 9 passed |
| Focused Task 07 | `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_pressure_snapshot_window.py overlay_client/tests/test_backend_pressure_ab_runner.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_pressure_ab_snapshot.py -q` | 232 passed |
| Dedicated real-socket harness | `overlay_client/.venv/bin/python -m pytest tests/test_harness_pressure_ab_snapshot.py -q` | 8 passed |
| Integrated helper/query/repaint | `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_payload_dedupe.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py tests/test_harness_pressure_ab_snapshot.py -q` | 159 passed |
| Runner orchestration | `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_pressure_ab_runner.py -q` | 105 passed |
| Compliance slice | `overlay_client/.venv/bin/python -m pytest tests/test_harness_plugin_hooks_contract.py tests/test_harness_prefs_roundtrip.py tests/test_logging_and_version_helper.py tests/test_preferences_persistence.py tests/test_debug_collectors.py -q` | 51 passed |
| All harnesses | `overlay_client/.venv/bin/python -m pytest -m harness -q` | 43 passed, 6 skipped, 1,529 deselected |
| Full headless | `overlay_client/.venv/bin/python -m pytest -q` | 1,558 passed, 20 skipped |
| Core check + GUI suite | `QT_QPA_PLATFORM=offscreen make check PYTHON=overlay_client/.venv/bin/python` | Ruff passed; mypy passed 92 files; 1,595 tests passed |
| Project test + GUI suite | `QT_QPA_PLATFORM=offscreen make test PYTHON=overlay_client/.venv/bin/python` | 1,595 passed |
| Explicit static/build | `ruff check .`; `mypy`; `compileall`; runner `--help`; `git diff --check` | All passed |

The first sandboxed all-harness run produced five bind fixture errors because loopback binding is
blocked there; 38 other harnesses passed. Repeating the unchanged command with localhost
permission passed all 43 selected harnesses. Headless skips are the expected PyQt-disabled cases;
the GUI-enabled suites ran and passed them. Windows-only Pester and the Python 3.13 `WinError 5`
workaround were not run on Linux; neither applies to this environment.

The exact release checker without override exited 1 as designed because this development venv is
Python 3.12.3/64-bit, not EDMC's tested Python 3.13.9+/3.13/32-bit runtime. With
`ALLOW_EDMC_PYTHON_MISMATCH=1`, it exited 0 with an explicit warning. This is not release-parity
evidence.

### Test files added or updated across remediation

- `tests/test_check_edmc_python.py` (added)
- `tests/test_harness_backend_status_roundtrip.py`
- `tests/test_harness_plugin_hooks_contract.py`
- `tests/test_harness_pressure_ab_snapshot.py`
- `overlay_client/tests/test_pressure_ab.py`
- `overlay_client/tests/test_backend_pressure_ab_runner.py`

### R1-R6 completion audit

| Stage | Yes/No | Completion evidence |
| --- | --- | --- |
| 7.R1 | Yes | Real socket correlation, malformed/wrong response rejection, bounded timeout, shutdown wake/cleanup, and neighboring command ownership pass. |
| 7.R2 | Yes | Strict sample/cell/run schemas, exact states, provenance, privacy, bounded values, continuity, and immutable four-file loading pass. |
| 7.R3 | Yes | Three-repetition statistics, five contrasts, reviewed report-only bounds, unavailable semantics, and deterministic sanitized in-memory Markdown pass. |
| 7.R4 | Yes | Exact helper/client route proof, bounded providers, fixed fake-clock timing, restart/decrease/saturation rejection, safety stops, and exclusive output pass. |
| 7.R5 | Yes | U5-U12 and H1-H3 traceability plus full fake orchestration and output-failure coverage pass. |
| 7.R6 | Yes | Every focused, harness, integrated, full, GUI, static, EDMC compliance, boundary, artifact, and documentation gate passes. |

### Final scope and readiness

- Historical evidence remains exactly 12 reduced-v2 captures and two superseded full-v1
  captures. No historical file was changed.
- `pressure-ab-report.md`, `thresholds.json`, and a clean-baseline identity remain absent.
- Branch/HEAD remain `backend-refactor-implementation` / `14576dd`; no commit or push occurred.
- No live A/B cell, host preflight, helper/client state mutation, or capture was performed.
- Automated remediation is complete. Stage 7.6 is **ready for separately authorized live
  preflight**, but remains not started; Stages 7.7-7.8 remain not started.
