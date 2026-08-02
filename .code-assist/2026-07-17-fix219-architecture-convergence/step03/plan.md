# Step 03 Implementation and Test Plan

Test type: **unit tests plus mandatory real-world manual validation**. Manifest/capture models,
aggregation, privacy, serialization, clock/cache decisions, and visual fingerprints are pure or
dependency-injected and therefore require unit tests. Runtime presentation/repaint seams use the
existing Qt-stub unit surfaces. No `load.py`, hook, Tk, socket, or EDMC lifecycle flow is expected
to change, so an EDMC harness test is not selected; if any of those touchpoints becomes necessary,
a harness test becomes mandatory before landing. GNOME compositor-visible A/B, behavior, soak,
and matrix gates cannot be substituted by unit, harness, or GUI tests.

## Phase Tracking

| Phase | Status |
| --- | --- |
| Phase 3: Step 03 pre-migration performance baseline | In progress |

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Verify state; read the complete design, research, plan, and task set | Completed |
| 3.2 | Map instrumentation and document requirements, interfaces, and test strategy | Completed |
| 3.3 | Write the complete unit acceptance surface and capture expected RED | Completed |
| 3.4 | Implement pure manifest/capture/threshold models and summary comparison to GREEN | Completed |
| 3.5 | Add the committed scenario manifest, CLI, evidence workflow, and artifact checks | Completed |
| 3.6 | Refactor and run targeted plus project validation | Completed |
| 3.7 | Prove and correct the cold-start managed-windowed exposure/remap defect | Completed |
| 3.8 | Pass two clean-start and transition manual acceptance checks | Completed |
| 3.9 | Retain the pre-optimization reduced-v2 matrix as historical evidence | Paused at 12/42 (2 superseded full-oracle captures also preserved) |
| 3.10 | Disable capture diagnostics and establish quiet normal-use state | Completed |
| 3.11 | Reduce backend-owned stable-target query pressure test-first | Completed |
| 3.12 | Attribute and suppress proven unchanged repaint work test-first | Completed |
| 3.13 | Run controlled helper A/B and review pressure-reduction acceptance bounds | In progress; automated gate passed, live preflight blocked |
| 3.14 | Repeat manual behavior regression and quiet-soak validation | Not started |
| 3.15 | Create a new identity; capture 0/42 clean baseline and freeze migration-regression thresholds | Not started |
| 3.16 | Update authoritative completion evidence and commit the completed increment | Not started |

## Test Scenarios

1. **Committed complete matrix**
   - Input: committed manifest.
   - Output: schema-v1 validation succeeds; 100% and 125% each cover stable windowed/fullscreen,
     per-monitor bidirectional transitions, bidirectional fullscreen handoff, Alt-Tab, and
     Overview with a two-monitor negative-coordinate horizontal layout.
2. **Fixed comparison inputs**
   - Input: two runs linked to one scenario.
   - Output: environment key, display configuration, fixture/hash, diagnostics, timing,
     repetitions, and clock-domain declarations are identical and machine-checkable.
3. **Explicit unsupported scope**
   - Input: committed outside-gate entries.
   - Output: mixed scale, vertical layout, primary-monitor change, and exclusive fullscreen are
     present exactly once and never appear in required scenario coverage.
4. **Schema and identifier rejection**
   - Input: unknown schema, missing/extra field, duplicate/unsafe scenario ID, or unknown
     fixture/diagnostic/display reference.
   - Output: explicit validation error; no correction or partial artifact is returned.
5. **Geometry and scale rejection**
   - Input: zero/negative dimensions, overlap/gap/non-horizontal monitors, no negative X,
     non-uniform/mixed scale, or a scale outside 100/125.
   - Output: validation fails with the offending field/coverage reason.
6. **Timing and count rejection**
   - Input: zero/negative warm-up, observation, idle interval, repetition, or non-finite value.
   - Output: validation fails.
7. **Manifest privacy boundary**
   - Input: token/secret, personal Linux/Windows path, arbitrary title, command line, raw owner
     ID, target/window handle, screenshot field, unsafe correlation, or broad environment map.
   - Output: artifact is rejected before writing evidence.
8. **Capture linkage and clock domains**
   - Input: valid normalized captures and captures with mismatched manifest/scenario/environment/
     fixture/config or undeclared/cross-origin raw clock fields.
   - Output: valid records load; incompatible or clock-unsafe records fail.
9. **Latency statistics**
   - Input: empty, singleton, even/odd, unsorted, and p95 edge distributions.
   - Output: empty required samples fail; count/median/nearest-rank-p95/max are deterministic.
10. **Work and rate aggregation**
    - Input: repeated helper health/target/presentation counts; raster build/reuse/skip/byte/
      region/encode/decode/apply values; repaint/paint/frame counts; known duration/transitions.
    - Output: totals and per-second/per-transition values are deterministic.
11. **Fixed-interval idle CPU**
    - Input: client and GNOME Shell samples with the manifest's fixed idle interval.
    - Output: deterministic mean/max/sample count; wrong interval or invalid CPU values fail.
12. **Invariant-first blocking**
    - Input: otherwise fast candidate containing one invariant code, black/intermediate surface,
      or material hitch.
    - Output: comparison is blocked regardless of numeric metrics.
13. **Dual-threshold latency comparison**
    - Input: baseline/candidate deltas below one or both thresholds and above both thresholds.
    - Output: investigation occurs only when both committed relative and absolute limits are
      exceeded; zero baselines are handled explicitly.
14. **Work and idle investigation categories**
    - Input: stable latency with excess helper/raster/repaint/frame work or idle CPU.
    - Output: separate categorized reasons remain visible.
15. **Threshold immutability/provenance**
    - Input: schema-v1 threshold artifact linked to the manifest/baseline and invalid artifacts
      with missing provenance, mutable/autotune fields, unknown metrics, or unsafe metadata.
    - Output: valid thresholds load as immutable values; invalid artifacts fail; comparison
      returns results without changing the artifact.
16. **Deterministic and privacy-safe output**
    - Input: equivalent captures in different input order plus prohibited diagnostic content.
    - Output: byte-identical sorted standard JSON and stable concise text for valid inputs;
      prohibited inputs never serialize.
17. **Synthetic end-to-end demo**
    - Input: the committed manifest, synthetic complete baseline/candidate summaries, and fixed
      synthetic thresholds.
    - Output: validate -> summarize -> compare succeeds without Qt/Tk/compositor imports.
18. **Manual GNOME 46 gate**
    - Input: shipped pre-migration route on Ubuntu 24.04.4/GNOME 46, two horizontal monitors
      including negative coordinates, uniform 100% and 125%, fixed fixture/toggles/timing.
    - Output: every configured repetition has sanitized captures, summaries, version metadata,
    and reviewed Phase 19/manual invariant checklist; variance-derived thresholds are frozen.

19. **Cold-start presentation diagnostic**
    - Input: diagnostics enabled with widget-visible/exposed and paint-count state available.
    - Output: the emitted event contains only boolean visibility/exposure and a bounded
      non-negative paint count; diagnostics disabled remains a no-op.
20. **Prepared visible-but-unexposed surface**
    - Input: `prepared_surface_requires_mapping=True`, widget visible, window not exposed, and
      policy approves show.
    - Output: preparation itself does not show; visibility handling performs exactly one
      controlled normal-surface remap after approval and reapplies map geometry/click-through.
21. **Already exposed and duplicate cycles**
    - Input: an exposed prepared surface, followed by repeated identical steady cycles.
    - Output: no hide/show/showNormal loop, no additional geometry/flag/platform preparation,
      and no focus/raise action.
22. **Visibility rejection and compatibility cases**
    - Input: visible-but-unexposed state with policy hide, plus fullscreen, minimized,
      warmup, unfocused-content, monitor-reconfiguration, and duplicate-preparation cases.
   - Output: no recovery occurs before/without show approval and all established contracts
     retain their existing outcomes.
23. **Post-remap backend attachment refresh**
    - Input: a successful cached managed-window attachment, followed by the controlled deferred
      Qt remap while the target remains unfocused and its geometry remains unchanged.
    - Output: generic follow requests one backend presentation refresh; the consumer forwards it
      without backend identity checks; the GNOME runtime bypasses its matching-success and
      persistent-mismatch skips for exactly one cycle; the helper reapplies the same rectangle;
      the next identical cycle is cached again. Unsupported/non-remapped paths remain unchanged.
24. **Capture during diagnostic log rotation**
    - Input: observation starts at an offset in the active client log; the log is renamed into
      one or more numeric rotations and a new active log receives later events.
    - Output: the runner reads the original remainder and every newer segment exactly once in
      chronological order. No-rotation behavior remains unchanged; an expired or incomplete
      chain fails explicitly rather than returning an empty/partial capture.
25. **Reduced representative matrix**
    - Input: the committed reduced manifest.
    - Output: exactly 14 scenarios and three repetitions produce a 42-capture gate; timing is
      fixed at 10-second warm-up, 15-second idle CPU, and 30-second observation. Both scales,
      managed/Shell presenters, both mode directions, both monitors, bidirectional fullscreen
      handoff, Alt-Tab, and Overview remain represented without the removed cross-products.
      Adding a removed redundant signature or omitting a retained signature fails validation.
26. **Quiet diagnostic state**
    - Input: capture flags and developer diagnostics are restored to normal-use values while
      bounded counters remain available for measurement.
    - Output: no per-query/per-repaint journal stream is emitted; unrelated configuration fields
      are preserved and helper developer configuration is backed up before editing.
27. **Stable target-query deadline**
    - Input: repeated matching target/presentation cycles with transition guard enabled and an
      injected monotonic clock before and after the bounded deadline.
    - Output: pre-deadline cycles reuse cached state without `GetTargetState`; deadline expiry
      performs one query and refreshes the deadline.
28. **Immediate invalidation and recovery**
    - Input: explicit refresh, helper failure/recovery, target loss/recovery, presenter/mode,
      focus, monitor, geometry, workspace, minimize/fullscreen, exposure, or stale-raster change.
    - Output: required immediate work bypasses the stable cache without delaying recovery; the
      cold-start deferred-remap refresh still bypasses exactly once.
29. **Unchanged repaint suppression**
    - Input: repeated supported payloads with identical rendered output and separately each
      content/style/geometry/group/override/expiry/animation/scale/mode/monitor/recovery trigger.
    - Output: identical output may refresh TTL/metadata without update/frame/presentation work;
      every real visual/recovery trigger still repaints and unknown payloads retain safe fallback.
30. **Quiet four-cell helper A/B**
    - Input: A1/A2/B1/B2 with fixed 100% monitor-A windowed state, five-minute warm-up, three
      interleaved 60-second samples, identical fixture/display/refresh, and Firefox stopped.
    - Output: median plus p95/range distinguishes enabled-idle extension cost from client-loop
      cost and produces reviewed pressure-reduction acceptance bounds without `thresholds.json`.
31. **Historical versus clean evidence boundary**
    - Input: 12 accepted reduced-v2 captures, two superseded full-v1 captures, and later
      post-optimization evidence.
    - Output: old artifacts remain immutable under original identities; new capture begins at
      0/42 under a new manifest/evidence identity and cannot mix threshold populations.
32. **Clean baseline and migration threshold provenance**
    - Input: complete new 42-capture baseline, manual Phase 19 review, and repeated variance.
    - Output: only this coherent population may produce versioned migration-regression
      `thresholds.json` for Steps 8, 16, 17, and 24.

## Cold-start correction sequence

1. Add the allowlisted diagnostic fields and unit-test their privacy/gating contract.
2. Model visible-but-unexposed and genuinely exposed window handles in the follow-surface stub.
3. Run focused tests to capture RED for exactly-once post-policy remapping and steady no-op
   behavior before changing runtime behavior.
4. Add the smallest backend-neutral effective-mapping predicate and controlled deferred remap
   path using only `prepared_surface_requires_mapping`; keep preparation free of show calls.
5. After the deferred map completes, set one generic presentation-refresh request. Transport it
   through the consumer API and let the selected GNOME runtime bypass its presentation cache for
   that one cycle; do not expose helper/backend identities to generic follow code.
6. Run focused follow/policy/consumer/runtime tests, the Step 03 gate, Ruff/format, focused mypy,
   `git diff --check`, headless pytest, `make check`, and `make test`.
7. On GNOME, prove diagnostic state on a clean windowed start, verify immediate content and
   nonzero paints on two clean restarts, then exercise borderless-to-windowed and
   windowed-to-borderless without focus/identity/intermediate-surface regressions.
8. Resume repetition 1 only if every manual invariant passes; otherwise retain Step 03 at
   0/42 and document the remaining blocker.

This sequence is historical. It justified starting reduced-v2 capture before the later pressure
incident; it does not authorize resuming the now-paused 12/42 matrix.

## Completed evidence-tooling implementation sequence

1. Add every unit/artifact test before implementation and run the focused command to capture
   expected missing-module/artifact failures.
2. Implement strict pure manifest validation and committed-matrix loading.
3. Implement strict capture ingestion, privacy checks, clock-domain separation, and summary
   statistics/work/CPU aggregation.
4. Implement immutable threshold loading, invariant-first comparison, deterministic JSON, and
   human formatting.
5. Add a thin CLI plus the committed manifest and exact real capture/evidence workflow.
6. Run focused tests after each seam, refactor to repository conventions, then run project
   gates and patch hygiene.
7. Execute the manual matrix only in the required display configurations. If any evidence is
   unavailable, leave Stage 3.7 and Step 03 incomplete and do not invent thresholds.
8. Update the authoritative plan/records and commit only when the selected completion scope is
   truthful; never push.
9. If the diagnostic log rotates during a real observation, add the rotation case RED before
   changing the runner; implement an inode/offset cursor, pass focused capture tests and lint,
   then restart the rejected repetition because no artifact was written.
10. Replace the superseded 180-capture oracle test-first with the approved 42-capture oracle,
    preserve old captures with their original manifest, rerun manifest/capture/project gates,
    and restart reduced repetition 1 without relabeling old evidence.

## Pressure-reduction continuation

1. Stage 3.10 restores `overlay_settings.json` and `dev_settings.json` to quiet values, reads and
   backs up the user-local GNOME helper developer configuration, disables its diagnostics without
   discarding other fields, and confirms stable queries no longer generate per-call journal
   events. Do not start capture.
2. Stage 3.11 adds RED unit tests for the transition-guard/stable-cache interaction, deadlines,
   invalidation, error/recovery, and one-shot forced refresh; implement the smallest backend-owned
   correction with an injected monotonic clock and run focused/project gates.
3. Stage 3.12 first uses bounded per-reason evidence to locate repaint requests, then adds RED
   unit tests at the smallest pure seam and suppresses only proven unchanged rendered output.
4. Stage 3.13 runs A1/A2/B1/B2 with diagnostics off and records pressure-reduction acceptance
   bounds in the A/B report. Stop immediately on flashing, input loss, drag corruption, repeated
   Mutter assertions, or rapidly rising Shell CPU.
5. Stage 3.14 repeats two terminal-focused clean starts, one game-focused start, both transition
   directions, both-monitor placement, Alt-Tab, Overview, and one quiet soak.
6. Stage 3.15 creates a new post-optimization manifest/evidence identity only after Stages
   3.10–3.14 pass, restarts at 0/42, completes manual review, and freezes migration-regression
   thresholds from the coherent repeated baseline.
7. Stage 3.16 updates authoritative evidence and commits only the reviewed completed increment;
   never push without separate authorization.

## Threshold vocabulary

- **Pressure-reduction acceptance bounds** come from the quiet four-cell A/B. They decide whether
  stable helper/repaint/load pressure improved enough to permit manual regression and clean
  baseline capture. They remain in the A/B report and never populate `thresholds.json`.
- **Migration-regression thresholds** come only from the complete new 42-capture baseline. They
  use the schema-v1 threshold artifact and become the comparison gate for later fix219 steps.
- Neither type is selected in advance or silently retuned. The 12 pre-optimization captures and
  two superseded captures contribute to neither population.

## Tiered test execution policy

The user approved a faster feedback cadence without waiving acceptance evidence:

1. Focused RED/GREEN unit tests remain mandatory for each stable-query cache or repaint behavior
   change. Relevant focused lint/type checks run with the touched seam.
2. `make check` and `make test` run after the integrated query-plus-repaint implementation
   milestone and again before Step 03 completion, rather than after every small edit.
3. Short exploratory A/B samples may debug the measurement setup but do not count toward
   acceptance. The accepted A/B still requires three repeated samples per A1/A2/B1/B2 cell.
4. Manual compositor checks and the 42-capture matrix may be deferred when time, environment, or
   stability requires it, but the corresponding stage remains incomplete.
5. A required test, manual case, repetition, or capture may be removed only by an explicit plan
   amendment that records the reduced coverage and residual risk. It is never silently skipped
   while reporting the stage complete.

## Validation Commands

- Pressure-reduction focused gate:
  `.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_payload_dedupe.py overlay_client/tests/test_repaint_debounce.py overlay_client/tests/test_follow_surface_mixin.py -q`
- Evidence focused gate:
  `.venv/bin/python -m pytest overlay_client/tests/test_backend_performance_capture.py overlay_client/tests/test_backend_performance_summary.py tests/test_debug_collectors.py -q`
- Focused lint/format:
  `.venv/bin/python -m ruff check <touched paths>`
  and
  `.venv/bin/python -m ruff format --check <touched paths>`
- Focused mypy:
  `.venv/bin/python -m mypy <touched source paths>`
- Headless suite: `.venv/bin/python -m pytest`
- Core check: `make check`
- Project test target: `make test`
- EDMC compatibility-floor check:
  `ALLOW_EDMC_PYTHON_MISMATCH=1 .venv/bin/python scripts/check_edmc_python.py`
- Patch hygiene: `git diff --check`

## Rollback and Compatibility

The completed evidence tooling remains additive. Preserve every accepted/historical capture and
manifest during rollback. Stage 3.10 configuration restoration is separately reversible from the
runtime changes. Stage 3.11's GNOME cache correction and Stage 3.12's repaint suppression must
remain behavior-scoped, independently testable, and independently revertible without weakening
the cold-start/remap, one-shot refresh, transition, focus, click-through, recovery, privacy, or
generic/backend-boundary contracts. No production selector, launcher, `load.py`, EDMC lifecycle,
content schema, or later fix219 migration route changes in this Step 03 continuation.
