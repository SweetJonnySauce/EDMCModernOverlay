# Performance Baseline and Regression Gate

## 2026-07-21 Step 3 amendment

The first reduced matrix is paused after 12 accepted captures. Those captures remain valid as
sanitized pre-optimization/incident-era evidence, but stable GNOME helper queries and repaint
requests will change before capture resumes. Mixing them with later samples would invalidate
the like-for-like baseline.

Step 3 now requires the following sequence:

1. disable capture diagnostics and establish a quiet normal-use state;
2. reduce unnecessary stable-target helper queries behind the GNOME backend boundary;
3. trace and suppress repaint requests that are proven not to change rendered output;
4. run the controlled helper-disabled/helper-enabled A/B described in
   `gnome-helper-pressure-and-repaint.md`;
5. repeat the manual Phase 19/startup/focus/placement safety checks; and
6. create a new evidence identity and restart the reduced 14-scenario by three-repetition
   matrix at 0/42.

The 12 existing captures cannot contribute to post-optimization thresholds and must not be
deleted, overwritten, relabeled, or silently mixed with the clean baseline. Thresholds remain
unset until the new repeated baseline is complete and reviewed.

### Two distinct threshold types

This amendment uses two deliberately separate numeric decisions:

1. **Pressure-reduction acceptance bounds** are reviewed from the quiet A/B repetitions. They
   decide whether stable helper-query/repaint work and Shell/client load fell materially without
   a behavior or stability regression. They are recorded in the A/B report, are provisional to
   this pressure-reduction gate, and are not written to `thresholds.json`.
2. **Migration-regression thresholds** are derived only from the complete coherent 42-capture
   post-optimization baseline. They use the versioned threshold schema, relative limit plus
   absolute noise floor, and become the comparison gate for later fix219 migration steps.

The A/B may therefore approve the pressure correction without preselecting or freezing the
later migration-regression thresholds.

## Existing instrumentation

The project already measures much of the expensive GNOME path:

- client raster building uses `perf_counter_ns()` and records build, validation, checksum, encode, payload assembly, and diagnostic assembly times;
- extension raster application records monotonic decode/apply/total timings and frame/region metrics;
- presentation results include transition elapsed state and helper-call skip/reuse data;
- repaint diagnostics track burst, ingest, paint, dedupe, and text-measure activity;
- developer toggles can enable presentation diagnostics without imposing release-mode cost.

The missing piece is a repeatable scenario runner and normalized summary, not a new benchmark framework.

## Baseline scenarios

Capture before migration on GNOME 46/Ubuntu 24.04.4, separately at uniform 100% and 125% scale:

1. stable windowed, idle and representative payload activity;
2. stable borderless fullscreen, idle and representative payload activity;
3. windowed to fullscreen and fullscreen to windowed on each monitor;
4. fullscreen monitor A to B and B to A, including negative coordinates;
5. Alt-Tab and Overview entry/exit around stable modes and transitions.

Use the same payload fixture, display geometry, observation duration, dev diagnostic configuration, and warm-up period for baseline and candidates.

For the clean post-optimization baseline, diagnostic configuration must also be quiet and
identical across repetitions. High-frequency per-query journal events are excluded; only
allowlisted bounded counters, state changes, and normalized failures may be collected.

## Measures

- presentation-cycle and end-to-stable transition latency (median, p95, maximum, sample count);
- helper health/target/presentation calls per second and calls per transition;
- raster builds, cache reuse/skips, encoded bytes, regions, and encode/decode/apply time;
- repaint/paint counts and frame-build work;
- client and GNOME Shell idle CPU sampled over a fixed stable interval;
- invariant failures and visible hitch observations from the manual checklist.

Use monotonic/performance clocks for elapsed data. Correlate client and extension records with safe random transition/frame IDs rather than attempting to compare their monotonic clock origins.

## Comparison policy

Store raw sanitized logs plus a small generated summary with environment/version metadata. Repeat each transition enough times to avoid treating one cold sample as the gate. Compare like-for-like distributions.

The detailed design should initially propose migration-regression investigation thresholds
rather than claim universal hard limits before baseline data exists. A practical starting policy
is:

- any invariant failure is an automatic failure;
- a sustained regression above both a relative threshold and a small absolute noise floor triggers investigation;
- helper/raster work that increases without a corresponding behavior need triggers investigation even if latency is unchanged;
- idle CPU must not materially increase;
- a user-visible hitch or black/intermediate surface blocks acceptance regardless of aggregate timing.

Final migration-regression tolerances are chosen from the coherent baseline variance and recorded
before the first migrated comparison. Changing them later requires an explicit rationale, not
silent retuning.

## Low-overhead requirement

Detailed timing, payload sizes, and high-frequency traces remain dev/diagnostic gated. Release builds retain only cheap counters/state needed for health and recent normalized failures. The performance gate must not itself create the regression it measures.

## Artifacts recommended for design

- a versioned scenario manifest;
- baseline environment record;
- raw client/helper diagnostic captures;
- summary table per scenario;
- manual smoothness/invariant checklist;
- comparison report naming investigated and accepted deviations.
