# Task: Build Performance Summary and Comparison Tool

## Description
Build a small pure summary and comparison tool that converts sanitized client/helper performance captures into deterministic per-scenario statistics and evaluates candidate results against fixed investigation thresholds. Reuse existing instrumentation rather than adding a separate benchmark framework or release-mode tracing burden.

## Background
The current client and GNOME helper already expose detailed raster, presentation, repaint, and timing diagnostics. Phase 1 needs normalized aggregation for median, p95, maximum, counts, work rates, idle CPU, invariant failures, and visible-hitch observations. Numeric thresholds cannot be chosen until repeated baseline variance is captured, but the comparison semantics must be implemented and tested first so later thresholds cannot be silently retuned.

## Reference Documentation
**Required:**
- Design: docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/planning/2026-07-17-fix219-architecture-convergence/research/performance-baseline.md (measures, comparison policy, and low-overhead constraints)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Parse only sanitized captures associated with a validated Step 3 Task 1 scenario manifest and reject incompatible schema, scenario, environment, or fixture metadata.
2. Compute deterministic sample count, median, p95, and maximum for presentation-cycle and end-to-stable latency with an explicitly tested percentile definition.
3. Aggregate helper health/target/presentation calls, calls per transition and second, raster builds/reuse/skips/bytes/regions/encode/decode/apply time, repaint/frame work, and fixed-interval client/Shell idle CPU.
4. Keep client and extension monotonic clock domains separate; correlate records only through safe scenario/transition/frame IDs and never compare raw clock origins.
5. Treat any invariant failure, black/intermediate surface, or material visible hitch as blocking regardless of aggregate timing.
6. Compare sustained regressions using both a fixed relative threshold and absolute noise floor; separately flag unexplained helper/raster work increases and material idle-CPU growth.
7. Read thresholds from a versioned evidence artifact and never infer, auto-tune, or overwrite them during candidate comparison.
8. Produce deterministic standard-JSON summaries suitable for review and a concise human-readable view without leaking raw secrets or personal data.
9. Add unit tests for aggregation, percentile edge cases, empty/invalid samples, clock separation, redaction, blocking invariants, dual-threshold comparison, and deterministic output.

## Dependencies
- Step 3 Task 1's versioned scenario manifest and validator.
- Existing client/helper diagnostic formats are inputs; any narrow adapter must preserve their developer-gated behavior.
- Step 3 Task 3 supplies the recorded baseline variance and fixed numeric threshold artifact.

## Implementation Approach
1. Define normalized sanitized sample and summary records keyed by manifest scenario ID and clock domain.
2. Implement pure aggregation functions first, followed by threshold comparison and deterministic JSON/human formatting.
3. Add narrow adapters for existing diagnostic records only where necessary, with allowlists at ingestion.
4. Test synthetic distributions and failure cases, then run the tool against a small sanitized fixture before manual capture.

## Acceptance Criteria

1. **Deterministic Statistical Summary**
   - Given a fixed sanitized sample set
   - When the summary tool runs repeatedly
   - Then sample count, median, p95, maximum, work metrics, CPU values, and serialized output are identical

2. **Clock-Domain Safety**
   - Given client and extension records with unrelated monotonic origins but shared safe correlations
   - When transition summaries are built
   - Then elapsed values are computed only within their originating domain and raw clocks are never subtracted across processes

3. **Invariant-First Gate**
   - Given otherwise acceptable aggregate performance with an invariant failure, black/intermediate surface, or material hitch observation
   - When comparison runs
   - Then the scenario is blocked and cannot pass based on latency statistics

4. **Fixed Dual-Threshold Comparison**
   - Given committed relative thresholds and absolute noise floors plus baseline and candidate summaries
   - When a sustained regression exceeds both limits
   - Then it is flagged for investigation, while threshold values remain unchanged by the tool

5. **Work and Idle Regression Visibility**
   - Given stable latency but increased helper/raster work or materially increased idle CPU
   - When comparison runs
   - Then the tool reports a separate investigation reason rather than treating the scenario as unchanged

6. **Privacy-Safe Unit Coverage**
   - Given timing edge cases and captures containing prohibited diagnostic fields
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_performance_summary.py tests/test_debug_collectors.py -q` is run
   - Then aggregation, comparison, clock, deterministic-output, and redaction tests pass

## Metadata
- **Complexity**: High
- **Labels**: fix219, performance, statistics, comparison-gate, diagnostics, unit-tests, phase-1
- **Required Skills**: Python data processing, statistical aggregation, performance analysis, privacy-safe tooling, pytest
