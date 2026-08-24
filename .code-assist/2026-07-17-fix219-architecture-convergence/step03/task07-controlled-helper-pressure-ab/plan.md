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

## Remediation stages

| Stage | Description | Status |
| --- | --- | --- |
| 7.R1 | Prove and repair the real socket-level client snapshot lifecycle | Completed |
| 7.R2 | Add strict sample/cell/run schemas, privacy rejection, and state/provenance validation | Completed |
| 7.R3 | Add compatible aggregation, contrasts, reviewed bounds inputs, and report rendering | Completed |
| 7.R4 | Harden runner state, GPU, timing, restart/saturation, warning, and safety contracts | Completed |
| 7.R5 | Complete missing unit/harness coverage and focused/integrated RED/GREEN | Completed |
| 7.R6 | Run integrated/project gates and complete the pre-live remediation audit | Completed |

Remediation phase status: **Completed; Stages 7.R1-7.R6 passed on 2026-08-02**.

## Stage 7.R2 TDD plan

### Stage table

| Stage | Description | Status |
| --- | --- | --- |
| 7.R2.1 | Verify handoff, Stage 7.R1 evidence, worktree, and Stage 7.R2 authority | Completed |
| 7.R2.2 | Freeze strict sample/cell/run shapes and test scenarios | Completed |
| 7.R2.3 | Add all schema/parser tests and record focused RED | Completed |
| 7.R2.4 | Implement the minimum runner-compatible contracts and refactor GREEN | Completed |
| 7.R2.5 | Run focused, integrated, static, privacy, and completion audits | Completed |
| 7.R2.6 | Synchronize Task 07 records and hand off Stage 7.R3 | Completed |

Stage 7.R2 status: **Completed**.

### Test type selection

- **Unit tests** are selected because strict JSON schemas, privacy checks, state matrices,
  bounded values, continuity, and complete-run parsing are pure and deterministic.
- `load.py`, plugin hooks, sockets, and lifecycle code are not changed in Stage 7.R2, so no new
  harness test is required. The completed Stage 7.R1 socket harness is retained as a regression
  gate.
- Runner tests cover only document-shape compatibility and exact client-argument pairing. Full
  live `_capture()` orchestration and provider behavior remain explicitly deferred to 7.R4/7.R5.

### Touch points and unchanged contracts

- `overlay_client/backend/pressure_ab.py`: add strict immutable sample, cell, provenance/state,
  and complete-run parsers/loaders. Keep existing work-snapshot APIs compatible.
- `overlay_client/tests/test_pressure_ab.py`: add all pure Stage 7.R2 RED cases before production
  implementation.
- `scripts/backend_pressure_ab.py`: emit the exact strict cell-document shape and validate it
  before writing; add only the metadata/argument seams needed for schema compatibility.
- `overlay_client/tests/test_backend_pressure_ab_runner.py`: prove the runner document uses the
  strict parser and client PID/port-file presence is an exact pair.
- Task 07 `context.md`, `plan.md`, `progress.md`, and `assessment-addendum.md`: record decisions,
  commands, results, and the completion audit truthfully.
- Unchanged: aggregation, per-cell summaries, contrasts, acceptance bounds, Markdown rendering,
  GPU/provider hardening, helper-disabled classification, live timing/safety orchestration,
  capture diagnostics, host/helper configuration, historical captures, Tk/Qt behavior, and the
  fix219 backend boundary.

### Required RED scenarios

| ID | Input | Expected output |
| --- | --- | --- |
| R2-U1 | Valid runner-shaped sample for each A1/A2/B1/B2 state | Frozen parsed sample with the exact nested resource/work/warning/safety fields |
| R2-U2 | Unknown field or prohibited path/PID/title/handle/command/journal/payload/token/host key or value | Privacy/schema validation rejects the evidence without retaining the value |
| R2-U3 | Negative, non-finite, boolean, overflow, malformed distribution, or saturated work counter | Bounded numeric validation rejects the sample |
| R2-U4 | Diagnostics on, safety field missing/true, counter decrease/saturation, restart, or unsafe continuity declaration | Sample is rejected as incomplete or unsafe |
| R2-U5 | A1/A2/B1/B2 state and client argument declarations | Only the exact approved client/helper/backend states and paired PID/port-file declarations pass |
| R2-U6 | Client/helper absent for a cell | Resource/work/origin fields require explicit unavailable records rather than `{}` or omission |
| R2-U7 | Three samples with mixed client/helper origins or repeated/missing repetition | Cell parsing rejects whole-cell post-warm-up discontinuity or incompleteness |
| R2-U8 | Wrong warm-up/observation timing, mutable provenance, non-quiet host, or duplicate execution order | Cell/run parsing rejects the evidence |
| R2-U9 | Four valid immutable cell documents in actual order | Complete-run loader accepts exactly A1/A2/B1/B2, three repetitions each, fixed provenance, and order 1-4 |
| R2-U10 | Missing/duplicate cell, mismatched fixed provenance, mutable file set, or privacy-invalid document | Complete-run loader fails closed |
| R2-U11 | Current runner document construction | The emitted document is accepted directly by the strict cell parser without a flat `metrics` adapter |
| R2-U12 | Running/stopped cell with one or both client arguments | Running requires both arguments; stopped requires neither; every partial/mismatched pair is rejected |

### Exact planned commands

1. Baseline compatibility:
   `overlay_client/.venv/bin/python scripts/check_edmc_python.py`.
2. Focused RED/GREEN:
   `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py -q`.
3. Focused Task 07 regression:
   `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_pressure_snapshot_window.py overlay_client/tests/test_backend_pressure_ab_runner.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_pressure_ab_snapshot.py -q` (localhost permission required for the real-socket cases).
4. Targeted Ruff:
   `overlay_client/.venv/bin/python -m ruff check overlay_client/backend/pressure_ab.py scripts/backend_pressure_ab.py overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py`.
5. Targeted mypy:
   `overlay_client/.venv/bin/python -m mypy overlay_client/backend/pressure_ab.py scripts/backend_pressure_ab.py`.
6. Compile:
   `overlay_client/.venv/bin/python -m compileall -q overlay_client/backend/pressure_ab.py scripts/backend_pressure_ab.py overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py`.
7. Patch hygiene and prohibited artifacts:
   `git diff --check` plus an explicit check that neither `thresholds.json` nor
   `pressure-ab-report.md` exists.

Project-wide `make check`/`make test`, the complete integrated helper/query/repaint slice, full
`_capture()` orchestration, and GUI-enabled gates remain mandatory at Stages 7.R5-7.R6 rather
than being claimed by this pure-contract stage.

## Stage 7.R3 TDD plan

### Stage table

| Stage | Description | Status |
| --- | --- | --- |
| 7.R3.1 | Verify handoff, prior-stage evidence, worktree, and authorities | Completed |
| 7.R3.2 | Freeze metric, contrast, bounds, rendering, and test contracts | Completed |
| 7.R3.3 | Add all analysis/report tests and record focused RED | Completed |
| 7.R3.4 | Implement the strict-run analysis/report pipeline and refactor GREEN | Completed |
| 7.R3.5 | Run focused/static validation and completion audit | Completed |
| 7.R3.6 | Synchronize Task 07 records and hand off Stage 7.R4 | Completed |

Stage 7.R3 status: **Completed**.

### Test type selection

- **Unit tests** are selected because aggregation, nearest-rank statistics, contrast arithmetic,
  reviewed-bound parsing/evaluation, and Markdown rendering are pure and deterministic.
- `load.py`, plugin hooks, sockets, runtime lifecycle, runner providers, and UI code are not
  changed, so no new harness test is required. The existing real-socket harness remains in the
  focused Task 07 regression command.

### Touch points and unchanged contracts

- `overlay_client/backend/pressure_ab.py`: retain the Stage 7.R2 strict model and remove the
  obsolete permissive flat-sample completion/summary surface.
- `overlay_client/backend/pressure_ab_report.py`: add immutable strict-run analysis,
  reviewed-bound, bound-result, and deterministic report rendering models/APIs.
- `overlay_client/tests/test_pressure_ab.py`: add all Stage 7.R3 tests before production changes,
  using only complete synthetic documents parsed by the strict Stage 7.R2 path.
- Task 07 `context.md`, `plan.md`, `progress.md`, and `assessment-addendum.md`: record decisions,
  RED/GREEN commands, completion audit, and remaining gates.
- Unchanged: raw capture schemas, parser privacy rules, runner `_capture()` and providers,
  helper/client state proof, live timing and safety behavior, `load.py`, Tk/Qt ownership,
  compositor behavior, historical evidence, capture diagnostics, and the fix219 backend boundary.
- No real report, live cell, acceptance decision, host/helper mutation, clean baseline identity,
  `thresholds.json`, commit, or push is authorized.

### Required RED scenarios

| ID | Input | Expected output |
| --- | --- | --- |
| R3-U1 | Complete strict run with distinct repetition values | Every compatible nested resource/work/actor/warning metric gets deterministic median, nearest-rank p95, minimum, maximum, and count 3 |
| R3-U2 | Stopped-client or disabled-helper cell | Client/helper resource/work/actor paths use explicit structural-zero statistics, while true provider unavailability stays unavailable |
| R3-U3 | Mixed GPU or warning availability within one cell | Analysis rejects incompatible evidence instead of coercing missing values |
| R3-U4 | Complete strict run with known cell medians | Exact values are produced for `B1-A1`, `A2-A1`, `B2-B1`, interaction, and `B2-A1` |
| R3-U5 | Any genuinely unavailable metric in a required cell | Its dependent contrast is explicitly unavailable, never zero or omitted |
| R3-U6 | Raw mapping, partial run, or forged non-strict object | Analysis rejects the input and requires `PressureAbRun` |
| R3-U7 | Strict reviewed-bound mapping with sanitized provenance and unique metric/contrast pairs | Frozen reviewed bounds are accepted and deterministically sorted |
| R3-U8 | Unknown metric/contrast, duplicate pair, invalid range, favorable-singleton method, unreviewed state, or private/path value | Reviewed-bound validation fails closed |
| R3-U9 | Observed contrast inside/outside inclusive reviewed bounds | Deterministic pass/fail bound results use the exact selected contrast |
| R3-U10 | Equivalent complete runs and bounds in different input/cell order | Markdown output is byte-for-byte identical with stable metric and bound ordering |
| R3-U11 | Deterministic report rendering | Markdown includes sanitized provenance, actual execution order, all cell statistics, five formulas, reviewed-bound provenance/results, and explicit threshold separation |
| R3-U12 | Synthetic complete evidence | Rendering remains in memory; no real report or `thresholds.json` is created |

### Exact planned commands

1. Baseline compatibility:
   `overlay_client/.venv/bin/python scripts/check_edmc_python.py`.
2. Focused RED/GREEN:
   `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py -q`.
3. Focused Task 07 regression:
   `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_pressure_snapshot_window.py overlay_client/tests/test_backend_pressure_ab_runner.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_pressure_ab_snapshot.py -q` (localhost permission required for real-socket cases).
4. Targeted Ruff:
   `overlay_client/.venv/bin/python -m ruff check overlay_client/backend/pressure_ab.py overlay_client/backend/pressure_ab_report.py overlay_client/tests/test_pressure_ab.py`.
5. Targeted mypy:
   `overlay_client/.venv/bin/python -m mypy overlay_client/backend/pressure_ab.py overlay_client/backend/pressure_ab_report.py`.
6. Compile:
   `overlay_client/.venv/bin/python -m compileall -q overlay_client/backend/pressure_ab.py overlay_client/backend/pressure_ab_report.py overlay_client/tests/test_pressure_ab.py`.
7. Patch/artifact hygiene:
   `git diff --check` plus an explicit scan proving `thresholds.json` and
   `pressure-ab-report.md` remain absent.

Project-wide and full integrated/GUI gates remain mandatory at Stages 7.R5-7.R6 and are not
weakened or claimed by this pure Stage 7.R3 context.

## Stage 7.R4 TDD plan

### Stage table

| Stage | Description | Status |
| --- | --- | --- |
| 7.R4.1 | Verify handoff, worktree, authorities, prior evidence, and capture hold | Completed |
| 7.R4.2 | Freeze runner state/provider/timing/safety/output contracts and tests | Completed |
| 7.R4.3 | Add all Stage 7.R4 runner tests and record focused RED | Completed |
| 7.R4.4 | Implement injected runner hardening and refactor GREEN | Completed |
| 7.R4.5 | Run focused/static validation and explicit completion audit | Completed |
| 7.R4.6 | Synchronize Task 07 records and hand off Stage 7.R5 | Completed |

Stage 7.R4 status: **Completed**.

### Test type selection

- **Unit tests** are selected for exact state proof, provider normalization, process/resource
  arithmetic, timing, continuity, safety, interruption, and exclusive output behavior. Every
  external dependency is injected or monkeypatched, so tests never wait through live timing or
  touch host/helper state.
- `load.py`, plugin hooks, broadcaster sockets, EDMC lifecycle, Tk/Qt, and GUI behavior are not
  changed. No new harness test is required by the touchpoint policy in this stage; the completed
  real-socket harness remains in the focused regression command. Stage 7.R5 will complete the
  broader U5-U12/H1-H3 inventory without deferring coverage for behavior changed here.

### Touch points, dependency seams, and unchanged contracts

- `scripts/backend_pressure_ab.py`: add frozen injectable clock/provider seams; exact D-Bus-owner,
  helper-health, client-runtime-backend, process/GPU, warning-window, continuity, safety-stop,
  interruption, and exclusive-create output contracts.
- `overlay_client/tests/test_backend_pressure_ab_runner.py`: add all R4 tests before production
  edits, using fake clocks and providers for complete 300/60/3 declarations without elapsed wait.
- Task 07 `context.md`, `plan.md`, `progress.md`, and `assessment-addendum.md`: record decisions,
  RED/GREEN evidence, audit, and remaining gates.
- State proof is outside each work-counter boundary: A2 requires live client-runtime status
  showing the GNOME missing-helper fallback, while B2 requires the live compositor-helper GNOME
  route with an available approved helper. Helper-disabled means only a successful
  `NameHasOwner=false`; transport, timeout, malformed, or health errors fail closed.
- One-second injected ticks align process endpoints, bounded warning subwindows, helper state
  checks, and client/helper work endpoints. Evidence still declares exactly 300 seconds, 60
  observations, and three repetitions; excessive real elapsed drift fails closed.
- A required operator-observation acknowledgement makes continuous visible-instability/Ctrl-C
  responsibility explicit. Repeated Mutter assertions and sustained high Shell CPU stop during
  warm-up or observation through machine-testable safety tracking.
- Successful and safety/interruption documents use exclusive creation. Stop documents are
  sanitized, structurally distinct non-acceptance artifacts with no partial samples, process
  identifiers, paths, raw provider output, journal text, or exception details.
- Unchanged: Stage R2 schemas, Stage R3 analysis/reporting, backend-owned runtime boundaries,
  diagnostics-off behavior, historical captures, host/helper configuration, live capture hold,
  clean baseline identity, absent report/`thresholds.json`, and the commit boundary.

### Required RED scenarios

| ID | Input | Expected output |
| --- | --- | --- |
| R4-U1 | Helper owner probe returns false, true, malformed, nonzero, or timeout | Only exact false proves disabled; every uncertain result is a clean `CaptureError` |
| R4-U2 | Enabled helper health has wrong mode/diagnostics/origin/counter/actor shape | State proof fails closed without retaining raw payload |
| R4-U3 | A2/B2 live backend-status payloads plus declared arguments | A2 proves missing-helper fallback; B2 proves selected compositor-helper route; shadow/stale/wrong route fails |
| R4-U4 | NVIDIA provider absent, valid one/multiple-GPU rows, timeout, nonzero, malformed, or out of bounds | Explicit unavailable or bounded aggregate; provider failures reject without raw output |
| R4-U5 | User-journal JSON over an exact start/end interval | Only allowlisted scoped Mutter/Shell classes are counted; raw text is discarded |
| R4-U6 | Journal timeout, nonzero, malformed JSON, reversed window, or saturation | Clean capture failure rather than unavailable, clamped, or leaked evidence |
| R4-U7 | `/proc` snapshots with valid deltas, restart identity, decrease, malformed fields, or impossible bounds | Bounded distributions or immediate rejection; restart/decrease cannot become zero |
| R4-U8 | Fake warm-up and three fake observation windows | No wall-clock wait; exact tick counts and contiguous warning windows align with work endpoints |
| R4-U9 | Client/helper origin or runtime route changes between any post-warm-up boundary | Whole cell fails before a document can be accepted |
| R4-U10 | Saturated client/helper endpoint or decreasing counter | Sample fails closed; saturation cannot yield a false zero delta |
| R4-U11 | Repeated assertions or sustained high Shell CPU during warm-up/observation | Typed safety stop identifies only fixed phase/reason/safety codes |
| R4-U12 | Keyboard interruption during warm-up/observation | Sanitized non-acceptance stop evidence is exclusively written; no partial accepted cell exists |
| R4-U13 | Existing success/stop output or a create race | Neither successful nor stopped output is overwritten |
| R4-U14 | Valid injected complete cell | Strict parser accepts three repetitions with fixed provenance and actual execution order |

### Exact planned commands

1. Baseline compatibility and focused runner baseline:
   `overlay_client/.venv/bin/python scripts/check_edmc_python.py` and
   `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py -q`.
2. Focused RED/GREEN:
   `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_pressure_ab_runner.py -q`.
3. Focused Task 07 regression:
   `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_pressure_ab.py overlay_client/tests/test_pressure_snapshot_window.py overlay_client/tests/test_backend_pressure_ab_runner.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_harness_pressure_ab_snapshot.py -q`
   (localhost permission required for real-socket cases).
4. Targeted Ruff:
   `overlay_client/.venv/bin/python -m ruff check scripts/backend_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py`.
5. Targeted mypy:
   `overlay_client/.venv/bin/python -m mypy scripts/backend_pressure_ab.py`.
6. Compile/help:
   `overlay_client/.venv/bin/python -m compileall -q scripts/backend_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py` and
   `overlay_client/.venv/bin/python scripts/backend_pressure_ab.py --help`.
7. Patch/artifact hygiene:
   `git diff --check` plus an explicit scan proving `thresholds.json`, a real
   `pressure-ab-report.md`, and a clean baseline identity remain absent.

Project-wide, integrated, GUI, and complete coverage-inventory gates remain mandatory in Stages
7.R5-7.R6 and are not claimed by this isolated runner-hardening context.

## Stage 7.R5 coverage-completion plan

### Stage table

| Stage | Description | Status |
| --- | --- | --- |
| 7.R5.1 | Verify handoff, worktree, authorities, prior evidence, and capture hold | Completed |
| 7.R5.2 | Map U5-U12, H1-H3, and runner orchestration to named tests and identify real gaps | Completed |
| 7.R5.3 | Add every genuinely missing coverage case and record RED where behavior is wrong | Completed |
| 7.R5.4 | Implement only fixes exposed by R5 RED and refactor GREEN | Completed |
| 7.R5.5 | Run focused/integrated/static validation and inventory audit | Completed |
| 7.R5.6 | Synchronize Task 07 records and hand off Stage 7.R6 | Completed |

Stage 7.R5 status: **Completed**.

### Test type selection

- **Unit tests** are selected for the residual runner/provider/orchestration gaps because clocks,
  process files, sockets, helper health, GPU, journal, and output writers can be injected or
  monkeypatched without EDMC lifecycle wiring.
- **Harness tests** remain required for H1-H3. The existing real-socket tests already cover the
  actual `load.py`/broadcaster lifecycle, so they remain a regression gate. No new harness test
  or `load.py` change is planned unless the matrix exposes a real lifecycle gap.
- The integrated query/repaint/helper suite is a required R5 regression gate. Project-wide and
  GUI final gates remain R6 scope.

### Existing coverage traceability and gaps

| ID | Required behavior | Current named evidence | R5 disposition |
| --- | --- | --- | --- |
| U5 | A1/B1 explicit stopped-client resource/work state | `test_parse_pressure_ab_sample_accepts_exact_runner_shape_for_each_cell`; `test_client_absence_requires_explicit_unavailable_fields`; A1 `_capture()` test | Covered schema; add B1 and retain all-cell orchestration proof |
| U6 | Three-repetition median/p95/min/max | `test_analysis_aggregates_nested_runner_metrics_with_nearest_rank_statistics`; `test_distribution_uses_nearest_rank_p95_and_bounded_summary` | Covered |
| U7 | Missing/short/diagnostics/unsafe evidence blocks | `test_pressure_ab_sample_rejects_unsafe_timing_bounds_continuity_or_safety`; `test_complete_run_rejects_incomplete_duplicate_or_mixed_evidence` | Covered |
| U8 | Complete four-cell attribution/contrasts | `test_complete_run_accepts_four_cells_and_preserves_actual_execution_order`; `test_analysis_computes_all_five_exact_contrasts_from_cell_medians` | Covered |
| U9 | Reviewed report-only bounds | `test_reviewed_bounds_are_strict_frozen_and_sorted`; `test_bound_evaluation_uses_exact_observed_contrast_and_inclusive_ranges`; report tests | Covered |
| U10 | Raw/private data rejection | `test_pressure_ab_cell_rejects_prohibited_or_host_identifying_data`; `test_report_is_deterministic_sanitized_and_contains_required_sections`; stop privacy tests | Covered |
| U11 | Bounded normalized `/proc` CPU/context/RSS | `test_process_sampler_aligns_fake_clock_warning_and_resource_windows`; restart/clock/GPU sampler tests | Add direct `_process_snapshot()` parsing, malformed, missing, and bounds coverage |
| U12 | GPU available/unavailable | provider absence, multi-device aggregate, timeout/nonzero/malformed/bounds tests | Add availability-change rejection through the sampler |
| H1 | Real client request/matching response | `test_pressure_snapshot_real_socket_roundtrip_keeps_transport_responsive`; synchronous roundtrip test | Covered by real broadcaster connection |
| H2 | Absent/malformed/timeout/shutdown cleanup | correlated malformed/wrong-ID, real timeout, real shutdown, and pending-state tests in `test_harness_pressure_ab_snapshot.py` | Covered |
| H3 | Neighboring CLI unchanged | `test_neighboring_cli_command_remains_on_socket_thread` | Covered |
| O1 | Full fake 300/60/3 `_capture()` for every cell | B2 complete capture and A1 stopped-cell capture | Add A2/B1 and consolidate exact all-cell success coverage |
| O2 | Exact state/continuity at every boundary | owner/status/helper/client/process/safety tests plus client/helper/route change capture tests | Covered; add disabled/helper and route regression to all-cell matrix |
| O3 | Decrease/saturation rejected through orchestration | pure client delta saturation/decrease and helper runner implementation | Add client/helper endpoint decrease/saturation `_capture()` cases |
| O4 | Warning/GPU provider availability and safety attribution | direct provider failures, aligned windows, cumulative assertion/CPU safety, phase stop tests | Add warning/GPU availability-change sampler cases and explicit unavailable warning case |
| O5 | Success/stop output and clean failures | exclusive writer and sanitized stop `main()` tests | Add successful `main()`, provider-error no-output, and write-failure normalization |
| O6 | Invalid inputs fail before timing | argument/state/provenance validators | Add fake-clock proof for order/provenance/quiet/operator rejection |
| O7 | Runner client socket/status providers | port validation and live-status priming test | Add snapshot malformed/transport and status retry-exhaustion coverage |
| O8 | Helper aggregate validation | helper identity/mode/transport tests | Add counter/actor/origin malformed cases; cover saturation through `_capture()` |

### Planned test inputs and outputs

| ID | Input | Expected output |
| --- | --- | --- |
| R5-U1 | Synthetic valid `/proc/<pid>/stat` plus status, including spaced process name | Exact start/tick/RSS/context mapping |
| R5-U2 | Missing/malformed/short/out-of-bound `/proc` data | Sanitized `CaptureError`; no host value retained |
| R5-U3 | A1/A2/B1/B2 with injected clocks/providers | Every cell yields a strict three-sample document after exactly 480 fake seconds |
| R5-U4 | GPU or warning availability flips during an observation | Capture fails instead of mixing provider populations |
| R5-U5 | Client or helper endpoints decrease or equal saturation sentinel | Full `_capture()` fails before an accepted cell exists |
| R5-U6 | Malformed helper counter/actor/origin | Helper snapshot fails closed without raw payload |
| R5-U7 | Malformed/transport-failed client snapshot or exhausted backend-status priming | Sanitized bounded failure |
| R5-U8 | Bad order/provenance/quiet/operator arguments | Failure occurs with zero injected sleep calls |
| R5-U9 | Successful `main()` | One exclusive JSON document is written and a second invocation cannot replace it |
| R5-U10 | Provider failure or output `OSError` in `main()` | Exit 2, no partial acceptance, and no raw personal path in stderr |

### Touch points and unchanged contracts

- `overlay_client/tests/test_backend_pressure_ab_runner.py`: add the missing unit/orchestration
  cases and consolidate full-cell success coverage.
- `scripts/backend_pressure_ab.py`: change only if RED exposes a real behavior gap; the expected
  candidate is clean normalization of output-write failure.
- Task 07 records: store the coverage matrix, RED/GREEN results, exact commands, and audit.
- Existing R1 harness files and `load.py` remain unchanged unless an actual H1-H3 gap is found.
- Unchanged: capture/report schemas, runtime/backend behavior, Tk/Qt ownership, diagnostics-off,
  historical captures, host/helper configuration, live capture hold, absent report/threshold/
  baseline identity, and Stage 3.16 commit boundary.

### Exact planned commands

1. Baseline compatibility and focused Task 07:
   `overlay_client/.venv/bin/python scripts/check_edmc_python.py` and the five-file focused pytest command.
2. R5 runner RED/GREEN:
   `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_pressure_ab_runner.py -q`.
3. Final focused Task 07: the five-file command from the assessment (localhost permission for
   real-socket cases).
4. Integrated query/repaint/helper: the five-file integrated command from the assessment
   (localhost permission for real-socket cases).
5. Targeted Ruff:
   `overlay_client/.venv/bin/python -m ruff check scripts/backend_pressure_ab.py overlay_client/tests/test_backend_pressure_ab_runner.py`.
6. Targeted mypy:
   `overlay_client/.venv/bin/python -m mypy scripts/backend_pressure_ab.py`.
7. Compile/help:
   `overlay_client/.venv/bin/python -m compileall -q overlay_client scripts/backend_pressure_ab.py`
   and `overlay_client/.venv/bin/python scripts/backend_pressure_ab.py --help`.
8. `git diff --check` plus prohibited-artifact scan.

`make check`, `make test`, full headless/GUI execution, EDMC upstream-baseline recheck, and final
implementation review remain Stage 7.R6 gates and are not claimed here.

## Stage 7.R6 integrated completion-audit plan

### Stage table

| Stage | Description | Status |
| --- | --- | --- |
| 7.R6.1 | Verify handoff, worktree, authorities, instructions, capture hold, and artifacts | Completed |
| 7.R6.2 | Map every R1-R6 requirement to direct evidence and freeze exact final gates | Completed |
| 7.R6.3 | Run focused, harness, integrated, orchestration, project, GUI, and static gates | Completed |
| 7.R6.4 | Review the cumulative implementation and EDMC compliance requirement by requirement | Completed |
| 7.R6.5 | Repair only demonstrated defects with touchpoint-appropriate RED/GREEN tests | Completed (D1-D3) |
| 7.R6.6 | Synchronize final records and decide whether remediation/live-preflight readiness is proven | Completed |

Stage 7.R6 status: **Completed; automated remediation is ready for the separate Stage 7.6 live preflight**.

### Test type selection

- R6 is first a **validation and review** stage, not a planned behavior change. Existing unit
  tests prove deterministic evidence schemas, analysis/reporting, providers, fake-clock capture,
  safety, and output contracts. Existing harness tests prove `load.py`, real socket correlation,
  timeout/shutdown cleanup, neighboring CLI behavior, and plugin lifecycle wiring.
- The complete `PYQT_TESTS=1` suite is the GUI/runtime integration gate. A separate headless run
  records which PyQt-only tests are deliberately skipped when the flag is absent.
- If review or a gate exposes a defect, test selection follows the touched boundary: unit for a
  pure/injected service, harness for `load.py`/hooks/socket/lifecycle, and both for mixed changes.
  A failing existing test may serve as RED only when its scope directly proves the defect.
- If no defect is found, no test or production file will be changed in R6; the residual risk is
  limited to the intentionally prohibited live GNOME A/B, which belongs to Stage 7.6 and later.

### Demonstrated defect R6-D1 — stale EDMC Python baseline

The official upstream check on 2026-08-02 found `.python-version` `3.13` and `docs/Releasing.md`
identifying Python 3.13.9 32-bit as the tested Windows runtime. The repository still records
`3.10.3 32bit`, and its checker treats that value as only a minimum. This directly contradicts
the design's known-failure/remediation requirement and cannot remain a release-compliance `Yes`.

Test type is **unit/source**: baseline parsing and runtime comparison are deterministic, while CI
configuration is a static file contract. No EDMC lifecycle or `load.py` behavior changes, so no
harness test is required for D1.

| ID | Input | Expected output |
| --- | --- | --- |
| R6-D1-U1 | Repository baseline source | Exactly `3.13.9 32bit` |
| R6-D1-U2 | Actual 3.13.9+ in the 3.13 series and 32-bit | Checker passes without override |
| R6-D1-U3 | Older/future Python series, pre-3.13.9 patch, or wrong architecture | Checker fails release validation; it is not a permissive minimum check |
| R6-D1-U4 | Same mismatch with `ALLOW_EDMC_PYTHON_MISMATCH=1` | Development/CI check exits successfully with an explicit warning |
| R6-D1-U5 | Non-parity CI Python 3.10/3.12 jobs | Workflow explicitly sets the documented development override |

D1 touchpoints are `tests/test_check_edmc_python.py`, `scripts/check_edmc_python.py`,
`docs/compliance/edmc_python_version.txt`, `.github/workflows/ci.yml`, and the current compliance
tracker. Archived release-specific compliance reports remain immutable historical records.

### Demonstrated defects R6-D2/D3 — Tk status wait and plugin-private cleanup

The cumulative source audit found both remaining known failures named by the detailed design:

- **R6-D2:** Tk-facing `get_backend_status()` calls `_request_client_backend_status()`, which
  waits on a network `threading.Event` for up to one second. It must queue a refresh and return a
  fresh/stale cache or backend-neutral shadow hint immediately.
- **R6-D3:** `load.py` still owns GNOME environment selection, imports the private GNOME helper
  presentation module, and performs startup/stop D-Bus cleanup. The overlay-client launcher
  already owns and tests this cleanup; plugin lifecycle must delete the duplicate compositor
  behavior and remain backend-neutral.

Both changes touch `load.py` orchestration, so **harness tests are mandatory**. D2 also exercises
thread-safe cache state in the real harness runtime. D3 retains the existing overlay-client unit
tests for client-owned GNOME cleanup; no generic follow/runtime implementation changes.

| ID | Input | Expected output |
| --- | --- | --- |
| R6-D2-H1 | Preferences/backend status read with a silent client | Returns backend-neutral hint well below the network timeout and queues one refresh |
| R6-D2-H2 | Valid later client status push | Replaces cache; next read returns immutable `client_runtime` status immediately |
| R6-D2-H3 | Runtime structure/source audit | No pending backend-status `Event` state or synchronous request method remains |
| R6-D3-H1 | `load.py` source/lifecycle audit | No GNOME raster constant, private import, backend enum dispatch, or D-Bus cleanup call remains |
| R6-D3-H2 | Normal/repeated plugin stop and client launcher cleanup tests | Plugin shutdown remains bounded/idempotent; client-owned cleanup behavior stays GREEN |

D2/D3 touchpoints are `load.py`, `tests/test_harness_backend_status_roundtrip.py`, and
`tests/test_harness_plugin_hooks_contract.py`. Existing client launcher code/tests are regression
gates only. After GREEN, rerun the dedicated harness/compliance slice and every full project gate.

### Requirement-to-evidence matrix

| Stage | Required completion evidence | R6 direct proof |
| --- | --- | --- |
| 7.R1 | Real request broadcast/response, strict correlation, timeout/pending cleanup, shutdown wake/teardown, neighboring CLI, thread ownership | Dedicated real-socket harness plus cumulative source review of `load.py` and `overlay_socket_server.py` |
| 7.R2 | Exact four-cell schemas/states/timing/order/provenance, bounded work, continuity, explicit unavailable fields, privacy, immutable complete loader | `test_pressure_ab.py`, runner compatibility cases, full suite, and parser/source review |
| 7.R3 | Three-repetition aggregation, median/p95/range, five contrasts, reviewed report-only bounds, deterministic sanitized Markdown, incomplete/unsafe rejection | Analysis/report unit tests, in-memory end-to-end four-file test, source/API review, prohibited-artifact scan |
| 7.R4 | Exact live state proof, provider bounds/availability, aligned 300/60/3 timing, continuity/decrease/saturation, warning/safety/stop/output behavior | 105-test runner suite, all-cell fake orchestration, CLI help, and runner source review |
| 7.R5 | U5-U12, H1-H3, full orchestration and clean output failure coverage | Named test inventory, focused/integrated gates, and test-file audit |
| 7.R6 | Every required focused/harness/integrated/project/static gate passes; cumulative implementation and six EDMC items reviewed; records truthful; no prohibited action | Exact commands/logs below, current official EDMC sources, diff/import/boundary/privacy/artifact audits, and final yes/no tables |

### Touch points and unchanged contracts

- Planned R6 writes began with the four Task 07 records and replaceable command logs. The audit
  demonstrated D1-D3, so the actual scoped touchpoints also include the Python parity source,
  CI/compliance records, `load.py`, and their unit/harness tests exactly as recorded above.
- The production changes remain behavior-scoped: exact release-parity validation, asynchronous
  cache-first backend status, and removal of duplicate plugin-side GNOME cleanup. Every affected
  focused and project gate was rerun after these changes.
- Unchanged: `fix219` backend ownership, Tk/Qt and socket thread ownership, diagnostics-off
  capture, historical 12+2 evidence, host/helper/client configuration, no-live-cell hold,
  report/threshold separation, absent clean baseline identity, and Stage 3.16 commit boundary.

### Exact planned commands

1. Compatibility and focused gates:
   `overlay_client/.venv/bin/python scripts/check_edmc_python.py`;
   the assessment's five-file focused pytest command; the dedicated harness file; the integrated
   five-file helper/query/repaint/harness command; and the runner orchestration file.
2. Headless and GUI/project gates:
   `overlay_client/.venv/bin/python -m pytest`;
   `QT_QPA_PLATFORM=offscreen make check PYTHON=overlay_client/.venv/bin/python`;
   `QT_QPA_PLATFORM=offscreen make test PYTHON=overlay_client/.venv/bin/python`.
   `make check` includes full Ruff, configured mypy, and `PYQT_TESTS=1` pytest.
3. Explicit static/build gates:
   `overlay_client/.venv/bin/python -m ruff check .`;
   `overlay_client/.venv/bin/python -m mypy`;
   `overlay_client/.venv/bin/python -m compileall -q overlay_client overlay_plugin scripts load.py`;
   `overlay_client/.venv/bin/python scripts/backend_pressure_ab.py --help`;
   `git diff --check`.
4. Current EDMC review: inspect official `EDCD/EDMarketConnector` `docs/Releasing`, `PLUGINS.md`,
   releases, and plugin-impacting discussions; compare the repository compliance baseline and CI.
5. Cumulative audits: inspect every changed source/test diff; scan generic runtime/follow modules
   for compositor-specific imports/enum dispatch; scan plugin imports/config/logger/Tk/network
   behavior; verify capture counts and unchanged evidence; and prove absence of a real
   `pressure-ab-report.md`, `thresholds.json`, clean baseline identity, commits, or live actions.

Project command output is written to replaceable files under `logs/` and summarized truthfully in
`progress.md`. No gate is weakened because it is slow, GUI-dependent, or broader than the R5
focused slice.

### Completion decision

- D1-D3 are resolved with direct unit/harness coverage. The D1 checker additionally rejects a
  non-`1` override value, matching its documented escape-hatch contract.
- The focused Task 07 suite passed 232 tests; the dedicated socket harness passed 8; the
  integrated helper/query/repaint suite passed 159; and the runner suite passed 105.
- The all-harness marker passed 43 with six condition-based skips. The full headless suite passed
  1,558 with 20 expected PyQt-disabled skips. GUI-enabled `make check` and `make test` each passed
  1,595; `make check` also passed Ruff and mypy.
- Explicit Ruff, mypy (92 source files), compileall, runner help, and `git diff --check` passed.
  The local Python 3.12.3/64-bit parity check fails without override as designed and exits zero
  with the explicit development override; nine checker unit tests pass.
- The cumulative R1-R6 implementation, backend boundary, EDMC compliance, historical evidence,
  and prohibited-artifact audits pass. No live cell, host/helper/client mutation, report,
  threshold, clean baseline identity, commit, or push occurred.

Stage 7.6 is now **ready for a separately authorized live preflight**, not completed or started.

## Stage 7.R1 TDD plan

### Touch points and unchanged contracts

- `tests/test_harness_pressure_ab_snapshot.py`: exercise two real loopback clients against the
  actual `SocketBroadcaster`; do not replace `publish()` with an immediate callback.
- `overlay_plugin/overlay_socket_server.py`: add only a command-selective non-blocking ingestion
  seam. All neighboring commands remain on the socket loop and preserve response ordering.
- `load.py`: configure only `pressure_snapshot` for deferral, synchronize pending correlation,
  and wake/clear pending requests during shutdown. No Tk or Qt operation moves threads.
- Existing backend-status, payload, startup, shutdown, and fix219 backend-owned presentation
  behavior must remain unchanged.

### Required tests before implementation

| ID | Input | Expected output |
| --- | --- | --- |
| R1-H1 | Real requester plus real client socket; matching response | Request is broadcast while the requester waits and the correlated snapshot returns successfully |
| R1-H2 | Wrong request ID, then malformed matching response, then valid matching response | Wrong/malformed input cannot resolve the pending request; valid correlated input does; state is cleared |
| R1-H3 | Real socket request with no responding client | Bounded unavailable response and empty pending state |
| R1-H4 | Runtime shutdown while a real socket request waits | Wait is woken, pending state clears, and shutdown stays bounded |
| R1-H5 | Neighboring synchronous CLI command over the real socket | Existing status/error response behavior is unchanged |

### Stage validation

1. Run the new real-socket success test against current production code and record the expected
   timeout/deadlock failure (RED).
2. Run all Stage 7.R1 socket lifecycle cases GREEN.
3. Run neighboring CLI/harness tests and the focused Task 07 command from the assessment.
4. Run targeted Ruff/mypy/compileall and `git diff --check`; broader project gates remain Stage
   7.R6 unless needed to diagnose a regression.
5. Audit correlation, malformed input, timeout, cleanup, shutdown, thread ownership, and
   neighboring behavior before marking 7.R1 complete.

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
