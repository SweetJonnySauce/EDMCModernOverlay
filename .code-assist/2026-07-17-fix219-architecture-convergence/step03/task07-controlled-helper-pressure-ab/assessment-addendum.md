# Task 07 Deep-Assessment Addendum

Date: 2026-08-02

## Purpose and authority

This addendum records a read-only deep assessment of Task 07, authoritative Stage 1.9 / working
Stage 3.13. It supplements the existing `context.md`, `plan.md`, and `progress.md` and supersedes
their readiness conclusion where they describe the live host preflight as the only remaining
blocker.

The task remains governed by:

- `.agents/tasks/2026-07-17-fix219-architecture-convergence/step03/task-07-run-controlled-helper-pressure-ab.code-task.md`;
- `docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md`;
- `docs/planning/2026-07-17-fix219-architecture-convergence/research/gnome-helper-pressure-and-repaint.md`;
- the repository `AGENTS.md`; and
- the historical capture hold and threshold-separation rules already recorded for Step 03.

No runtime code, tests, captures, configuration, host process, helper state, or threshold file
was changed during the assessment. This addendum and its link from `progress.md` are the only
resulting documentation changes.

## Current disposition

Task 07 automated remediation is **complete**. Stages 7.R1-7.R6 passed on 2026-08-02 and the
implementation blocker is cleared. Stage 7.6 live preflight is ready for separate authorization
but remains not started; therefore no A1, A2, B1, or B2 acceptance cell has begun.

The July 21 automated results remain valid historical evidence for the exact coverage they ran:

- focused Task 07: 66 passed;
- integrated query/repaint/helper slice: 217 passed;
- `make check`: 1,402 passed and 21 skipped, with Ruff and mypy passing;
- `make test`: 1,402 passed and 21 skipped; and
- targeted Ruff, compileall, runner help, and patch hygiene: passed.

Those tests did not cover the real socket concurrency path, complete cell/run validation,
runner orchestration, GPU-available collection, or report rendering. They therefore do not
establish readiness for live evidence collection.

The recorded July 21 host observation is historical and may be stale. At that time Firefox was
active, Elite/EDMC/the client were absent, and unrelated load was too high. No new host preflight
was performed for this assessment.

## Stop-ship findings

### 1. Real client snapshot requests block their own transport

`SocketBroadcaster._handle_client()` invokes the synchronous ingestion callback directly on its
asyncio event-loop thread. The `pressure_snapshot` CLI handler publishes a request through that
broadcaster and then blocks on a `threading.Event` while waiting for the overlay client response.
The queued request cannot be broadcast, and the client response cannot be ingested, until the
same event loop becomes unblocked after the request timeout.

The current harness replaces `broadcaster.publish` with a synchronous callback that injects the
response immediately. It proves coordinator state cleanup but not the actual socket/broadcast/
client-response lifecycle. Source-level control flow indicates that A2 and B2 will time out on
their first client snapshot.

Required outcome: add a real socket-level failing harness test, then implement a bounded
non-blocking request/response design that preserves existing Tk/Qt and socket-thread contracts.
Do not move every CLI command to a worker thread without separately reviewing the wider
lifecycle and thread-safety consequences.

### 2. Captured cell documents cannot reach the required report

The runner emits nested `resources`, `client_work`, `helper_work`, `actor_counts`,
`warning_counts`, and `safety_failures`. `validate_complete_pressure_samples()` checks only cell,
repetition, nominal timing, and diagnostics state. `summarize_pressure_samples()` instead expects
an unrelated flat `sample["metrics"]` mapping.

There is no strict parser for a runner cell document, complete four-cell run loader, privacy
rejection pass, contrast calculator, reviewed-bound input model, or deterministic Markdown
renderer. No `pressure-ab-report.md` exists.

Required outcome: implement and test one end-to-end path from four immutable cell documents to
a complete validated run and deterministic report. The report must refuse partial, unsafe,
schema-invalid, or privacy-invalid inputs.

Remediation update: Stages 7.R2-7.R3 resolved this finding. The strict immutable four-file loader
feeds one frozen run model; a separate pure report module aggregates the runner's nested metrics,
calculates all five required contrasts, validates reviewed report-only bounds/provenance, and
renders deterministic sanitized Markdown. An end-to-end test proves four temporary cell files
reach in-memory Markdown. No real report is created before live evidence exists.

### 3. GPU collection always reports unavailable

`_gpu_sample()` returns only when `nvidia-smi` is absent. Its intended subprocess implementation
is unreachable code placed after `_normalized_warning_counts()` has already returned.

Required outcome: repair the available/unavailable paths, bound all values, handle timeout and
malformed output cleanly, and cover both paths with unit tests before accepting live data.

## Additional evidence-integrity gaps

1. Client state arguments are not an exact pair. A stopped-client cell may accidentally receive
   only `--client-pid` or only `--port-file` and pass the current state check.
2. Helper-disabled validation catches every exception. A present but malformed, unreachable,
   wrong-mode, or diagnostics-enabled helper may be misclassified as disabled. Only a proven
   missing D-Bus owner should establish the disabled state.
3. A2 does not prove the required documented unavailable/fallback backend state. B2 does not
   prove that the client selected and consumes the intended helper-backed route.
4. Helper-disabled state is not rechecked after warm-up or around every repetition. Client and
   helper origin continuity is checked only within an individual sample, not across the complete
   post-warm-up cell.
5. Saturating counters at 1,000,000 can yield a false zero delta. Saturated before/after samples
   must be rejected or the measured processes must be proven fresh.
6. The process-resource interval ends before warning collection, but ending helper/client work
   snapshots occur after warning collection. A journal query may therefore add up to five
   seconds of work to a nominal 60-second sample and produce misaligned resource, helper, and
   client windows.
7. The runner does not persist sanitized provenance for fixture/hash, source and component
   versions, display and refresh configuration, workload mode, quiet-host decision, or actual
   interleaved cell order.
8. Safety is prompted only after each sample. There is no runner check during the five-minute
   warm-up, no continuous Shell CPU stop, and no machine-enforced immediate stop for repeated
   assertions. The human operator may use Ctrl-C, but the operating procedure does not make the
   continuous-observation responsibility explicit.
9. Warning collection is broad and may miss GNOME Shell messages because `--output=cat` removes
   unit metadata while the classifier expects the message text to identify `gnome-shell`.
   Journal timeout is not converted into a clean capture failure.
10. A safety stop prevents writing the cell document, which correctly prevents partial
    acceptance but leaves no automatically generated sanitized stop record. Any diagnostic stop
    must be documented manually without retaining raw journal or host-identifying material.

Remediation update: Stage 7.R4 resolved the GPU finding and all ten runner integrity gaps. The
runner now requires exact paired client arguments and live authoritative A2/B2 route state;
proves helper absence only through `NameHasOwner=false`; validates enabled helper identity,
mode, diagnostics, counters, actors, and origin; rechecks state and continuity through warm-up
and every observation; rejects restarts, decreases, saturation, clock drift, malformed providers,
and provider availability changes; uses bounded JSON journal windows and bounded multi-GPU
aggregates; and emits only strict accepted cells or sanitized exclusive-create stop evidence.
Continuous operator observation remains mandatory for visible failure classes, while repeated
Mutter assertions and sustained high Shell CPU are machine-enforced during both timed phases.

## Reopened Phase 7 work

The original Stage 7.3-7.5 work remains historical implementation and validation evidence, but
its acceptance must be reopened through the remediation stages below.

| Stage | Description | Status |
| --- | --- | --- |
| 7.R1 | Prove and repair the real socket-level client snapshot lifecycle | Completed |
| 7.R2 | Add strict sample/cell/run schemas, privacy rejection, and state/provenance validation | Completed |
| 7.R3 | Add compatible aggregation, four-cell contrasts, reviewed-bound inputs, and report rendering | Completed |
| 7.R4 | Harden runner state, GPU, timing, restart/saturation, warning, and safety contracts | Completed |
| 7.R5 | Add the missing unit and harness coverage and rerun focused RED/GREEN | Completed |
| 7.R6 | Rerun integrated and project gates and review the implementation before live use | Completed |
| 7.6 | Establish the fixed quiet host workload and pass live preflight | Ready; not started |
| 7.7 | Run the interleaved four-cell protocol and collect all 12 samples | Not started |
| 7.8 | Review privacy/safety, derive report-only bounds, and synchronize authority | Not started |

Remediation phase status: **Completed; Stages 7.R1-7.R6 passed**. Task 07 remains in progress at
the separately authorized live Stage 7.6.

## Required test expansion — Stage 7.R5 result

Test selection remains mixed:

- unit tests for strict documents, privacy rejection, deltas, saturation/restart behavior,
  process/GPU/warning providers, exact cell state, orchestration, aggregation, contrasts, bounds,
  and deterministic report rendering;
- harness tests for the real `load.py` plus socket broadcaster request/response lifecycle,
  client absence/malformed response/timeout/shutdown cleanup, and neighboring CLI behavior; and
- the manual GNOME four-cell gate after every automated gate passes.

Stage 7.R5 completed the plan's U5-U12 and H1-H3 coverage. The H1-H3 tests exercise a real
`SocketBroadcaster` connection rather than replacing `publish()` with an immediate callback. All
four runner cells complete `_capture()` orchestration with injected clocks/providers, so tests do
not wait for the live 300/60-second intervals. Direct provider, endpoint safety, early validation,
and success/stop/failure output cases close the remaining orchestration gaps.

After remediation, rerun and record:

```bash
source overlay_client/.venv/bin/activate && python -m pytest \
  overlay_client/tests/test_pressure_ab.py \
  overlay_client/tests/test_pressure_snapshot_window.py \
  overlay_client/tests/test_backend_pressure_ab_runner.py \
  overlay_client/tests/test_gnome_shell_helper_extension_source.py \
  tests/test_harness_pressure_ab_snapshot.py -q

source overlay_client/.venv/bin/activate && python -m pytest \
  overlay_client/tests/test_gnome_helper_presentation_runtime.py \
  overlay_client/tests/test_payload_dedupe.py \
  overlay_client/tests/test_repaint_debounce.py \
  overlay_client/tests/test_follow_surface_mixin.py \
  tests/test_harness_pressure_ab_snapshot.py -q

source overlay_client/.venv/bin/activate && make check
source overlay_client/.venv/bin/activate && make test
source overlay_client/.venv/bin/activate && python -m compileall -q \
  overlay_client scripts/backend_pressure_ab.py
git diff --check
```

Exact test files added or updated and exact pass/fail/skip results must be recorded after the
remediation. No test command was run for this documentation-only assessment.

## Live protocol to freeze before execution

Before the first accepted cell, document and verify without storing personal or raw host data:

- exact representative fixture and committed hash, including its replay cadence;
- whether each observation is idle, repeated unchanged payload activity, or a fixed subdivision;
- source revision plus plugin/client/helper versions and helper protocol;
- Ubuntu/GNOME/session values, monitor A placement, 100% scale, resolution, and refresh rate;
- stable windowed Elite state and a privacy-safe process-identity check;
- the exact A2 unavailable/fallback state and B2 full-helper selected-route state;
- diagnostics off for the client and helper;
- Firefox stopped and a predeclared quiet-background-load criterion;
- actual interleaved cell order; and
- continuous operator observation plus an explicit emergency stop rule for rapidly rising Shell
  CPU. The emergency rule is separate from post-run acceptance bounds.

The four runner invocations require at least 32 minutes of warm-up and sampling before state
transition and review overhead. Short exploratory runs may prove the repaired mechanism but
cannot count toward acceptance.

## Required report analysis

Only after all 12 samples pass strict schema, privacy, state, timing, and safety validation,
calculate at least:

- enabled-idle helper cost: `B1 - A1`;
- client cost with helper disabled: `A2 - A1`;
- client cost with helper enabled: `B2 - B1`;
- helper/client interaction: `(B2 - B1) - (A2 - A1)`; and
- overall integrated cost: `B2 - A1`.

Report per-cell median plus nearest-rank p95 or full range across all three repetitions for
resource, query, repaint, paint, frame, actor, and normalized warning measures. Any safety or
visible invariant failure blocks acceptance before numeric review.

Numeric pressure-reduction bounds are selected only after the complete quiet A/B, but the
selection method must be agreed before capture: use every repetition, preserve absolute noise
floors, explain attribution, prohibit favorable-singleton reasoning, and require explicit review.
Bounds and provenance belong only in `pressure-ab-report.md`; do not create or modify
`thresholds.json`.

## R6 completion disposition

Stage 7.R6 completed on 2026-08-02. Preserve the cumulative remediation worktree, historical
12/42 reduced-v2 captures, two superseded full-v1 captures, absent migration threshold/report
artifacts, and Stage 3.16 commit boundary. Any later session may begin Stage 7.6 only with
separate live-work authorization and a fresh host preflight; R6 completion does not itself start
or authorize a cell.

Suggested skills:

- `code-assist` for the test-first remediation sequence;
- `handoff` when creating or resuming the next session handoff; and
- `review-repository` only if broader repository orientation is needed before resuming.

## Final R6 completion audit

### Demonstrated defects resolved

1. The EDMC Python baseline and checker now match the official 3.13.9 32-bit tested runtime and
   fail mismatched release validation unless the explicit development override equals `1`.
2. Tk-facing backend status reads no longer wait for the client. They queue a refresh and return
   cache or a backend-neutral hint immediately; later client pushes update a synchronized cache.
3. `load.py` no longer imports, selects, or clears GNOME raster presentation. Client launcher
   startup/shutdown retains sole cleanup ownership and its regression tests pass.

### Required validation result

- Focused Task 07: 232 passed.
- Dedicated real-socket snapshot harness: 8 passed.
- Integrated helper/query/repaint/harness: 159 passed.
- Runner orchestration: 105 passed.
- All harness marker: 43 passed, 6 condition-based skips.
- Full headless: 1,558 passed, 20 expected PyQt-disabled skips.
- GUI-enabled `make check`: Ruff passed, mypy passed 92 source files, 1,595 tests passed.
- GUI-enabled `make test`: 1,595 passed.
- Explicit Ruff, mypy, compileall, runner help, patch hygiene, boundary, privacy, and artifact
  checks: passed.

The managed sandbox cannot bind loopback sockets; its all-harness attempt produced five fixture
errors while the other 38 harnesses passed. The unchanged permitted localhost run passed all 43
selected harnesses. Windows-only Pester and the Windows Python 3.13+ `tmp_path` workaround were
not applicable on this Linux host.

### EDMC compliance decision

Every item in the detailed design's 17-row compliance gate is **Yes**, with exact evidence in
`docs/compliance/edmc_compliance.md`. The six repository-level compliance categories are also
Yes: core alignment; supported APIs/helpers; logging/versioning; responsive Tk-safe runtime;
preferences/UI integration; and dependency/debug-HTTP handling.

### Constraints preserved

Historical evidence remains exactly 12 reduced-v2 plus two superseded full-v1 captures. No live
cell, host/helper/client mutation, `pressure-ab-report.md`, `thresholds.json`, clean baseline
identity, commit, or push occurred. Branch/HEAD remain `backend-refactor-implementation` at
`14576dd` with the cumulative intentionally dirty remediation worktree.
