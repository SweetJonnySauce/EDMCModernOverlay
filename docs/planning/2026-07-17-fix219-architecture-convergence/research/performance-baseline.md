# Performance Baseline and Regression Gate

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

The detailed design should initially propose investigation thresholds rather than claim universal hard limits before baseline data exists. A practical starting policy is:

- any invariant failure is an automatic failure;
- a sustained regression above both a relative threshold and a small absolute noise floor triggers investigation;
- helper/raster work that increases without a corresponding behavior need triggers investigation even if latency is unchanged;
- idle CPU must not materially increase;
- a user-visible hitch or black/intermediate surface blocks acceptance regardless of aggregate timing.

Final numeric tolerances are chosen from baseline variance and recorded before the first migrated comparison. Changing them later requires an explicit rationale, not silent retuning.

## Low-overhead requirement

Detailed timing, payload sizes, and high-frequency traces remain dev/diagnostic gated. Release builds retain only cheap counters/state needed for health and recent normalized failures. The performance gate must not itself create the regression it measures.

## Artifacts recommended for design

- a versioned scenario manifest;
- baseline environment record;
- raw client/helper diagnostic captures;
- summary table per scenario;
- manual smoothness/invariant checklist;
- comparison report naming investigated and accepted deviations.
