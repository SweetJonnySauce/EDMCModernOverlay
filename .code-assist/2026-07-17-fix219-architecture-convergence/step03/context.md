# Step 03 Code Context

## Scope

Implement the three approved Step 03 tasks without changing production routing:

1. add a strict versioned performance-scenario manifest and pure validator;
2. add deterministic sanitized capture aggregation and fixed-threshold comparison tooling;
3. prepare, execute, and validate the pre-migration GNOME 46 baseline evidence gate.

The manifest/tooling increment may land only as pure evidence support. Step 03 itself remains
incomplete until every required real-world capture, manual invariant checklist, deterministic
summary, and baseline-derived threshold artifact exists.

## Existing Documentation

- `AGENTS.md` requires plan-first implementation, explicit test selection, pure-helper unit
  tests, privacy-safe diagnostics, unchanged production behavior, exact validation evidence,
  and numbered phase/stage tracking.
- `README.md` identifies this as the Python EDMC Modern Overlay plugin/client repository.
- `docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md`
  fixes the performance matrix, invariant-first gate, clock-domain boundary, privacy rules,
  release validation tree, and no-retuning policy.
- `docs/planning/2026-07-17-fix219-architecture-convergence/research/performance-baseline.md`
  identifies existing raster/helper/repaint instrumentation and the required measures.
- `docs/planning/2026-07-17-fix219-architecture-convergence/implementation/plan.md`
  makes the baseline a gate before Step 05 production routing and forbids marking Step 03
  complete without manual evidence.
- `.agents/tasks/2026-07-17-fix219-architecture-convergence/step03/` contains the three
  approved task specifications and acceptance criteria.

No `CODEASSIST.md` exists. The root `.venv` is the canonical development/test environment;
`overlay_client/.venv` is runtime-only.

## Current Environment and Existing Instrumentation

- The implementation host is Ubuntu 24.04.4 LTS, native Wayland, GNOME Shell 46.0.
- Two 3440x1440 displays are available. The verified 100% topology places `monitor_a` physically
  left of primary `monitor_b`. Mutter and Qt report normalized global coordinates `(0, 0)` and
  `(3440, 0)`; the manifest separately records and validates the primary-relative projection
  `(-3440, 0)` and `(0, 0)`. The uniform 125% run still requires explicit reconfiguration and
  manual capture.
- Current shipped component inputs are plugin/client version `1.0.0`, helper protocol `3`, and
  the pre-migration route at repository commit `3d2332869454d6561995203752fd239a558a95a5`.
- `overlay_client/backend/shell_raster_frame.py` emits developer-gated build, validation,
  checksum, encode, payload, region, byte, reuse, and skip measures.
- `helpers/gnome_shell_extension/extension.js` emits decode/apply/total helper timing and reuse
  measures in its own monotonic domain.
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py` exposes presentation
  results and helper-call skip/reuse diagnostics.
- `overlay_client/control_surface.py` emits developer-gated repaint/paint/ingest and text
  measure statistics.
- `tests/archive/display_all.json` is the existing representative payload fixture; its SHA-256
  is `3766f57248d032c8a01844de0994fe31f0211211a3292660a442aa9d68b923f9`.

## Requirements and Acceptance Mapping

- Standard JSON schema version 1 must reject unknown fields/versions and never coerce an
  incompatible artifact.
- The manifest fixes target environment, component/protocol references, display geometry,
  uniform 100% and 125% scale, payload fixture/hash, diagnostic configuration, clock domains,
  warm-up, observation/idle intervals, repetitions, and scenario coverage.
- The required matrix contains stable windowed and borderless-fullscreen modes, both mode
  transitions on both monitors, both fullscreen handoffs, Alt-Tab, and Overview for each
  scale. Mixed scale, vertical layouts, primary-monitor changes, and exclusive fullscreen are
  explicit outside-gate entries.
- Manifest/capture/threshold IDs are stable bounded safe identifiers. Geometry is two-monitor,
  non-overlapping, horizontal, uniformly scaled, and includes a negative X coordinate.
- Capture ingestion is allowlist-only and rejects tokens, secrets, raw owner IDs, target/window
  handles, arbitrary titles, command lines, screenshots, broad environment dumps, personal
  paths, and unsafe correlations.
- Client and helper elapsed samples retain separate declared clock domains. Only elapsed
  values already measured inside one domain are aggregated; raw cross-process timestamps are
  neither accepted nor subtracted.
- Summary output deterministically computes sample count, median, nearest-rank p95, maximum,
  normalized helper/raster/repaint/frame work, fixed-interval idle CPU, and manual/invariant
  outcomes.
- Any invariant failure, black/intermediate surface, or material visible hitch blocks a
  scenario regardless of timing.
- Candidate investigation requires both the committed relative limit and absolute noise floor.
  Work and idle-CPU increases are reported independently from latency.
- Thresholds are loaded from a separate versioned artifact with baseline provenance and cannot
  be inferred, tuned, or overwritten by comparison.
- Production imports, selectors, launcher, presentation, `load.py`, Tk, Qt, and helper
  instrumentation defaults remain unchanged.

## Dependency Map

```text
versioned scenario manifest + strict pure loader
        -> sanitized normalized capture loader
        -> per-scenario deterministic aggregation
        -> deterministic JSON and concise text summary

committed baseline summary + separately committed fixed thresholds
        -> candidate comparison
        -> invariant-first block or categorized investigation reasons

existing developer-gated client/helper diagnostics
        -> manual capture/adaptation workflow only
        -> no production routing or release-default changes
```

## Implementation Paths

- `overlay_client/backend/performance_evidence.py`: pure manifest, capture, threshold,
  aggregation, comparison, privacy, and deterministic formatting API.
- `scripts/backend_performance.py`: thin CLI for validate/summarize/compare operations; all
  behavior remains in the pure module.
- `overlay_client/tests/test_backend_performance_summary.py`: complete synthetic acceptance
  surface plus validation of committed artifacts.
- `docs/support/validation/fix219-pre-migration/performance/manifest.json`: committed scenario
  oracle for the real GNOME 46 baseline/candidate comparisons.
- `docs/support/validation/fix219-pre-migration/performance/README.md`: exact capture procedure,
  evidence layout, privacy review, manual checklist, and blocker state.
- The same evidence directory will later contain sanitized captures, generated summaries, and
  `thresholds.json` only after the real matrix and variance analysis are complete.

## Risks and Boundaries

- Automated tests cannot prove compositor-visible smoothness, focus safety, black-surface
  absence, or correct Alt-Tab/Overview identity; those remain a manual gate.
- Committing fabricated captures or placeholder numeric thresholds would defeat the baseline
  gate. Missing real evidence must remain explicit rather than being represented as passing.
- Detailed timing remains developer-gated, and the new tooling does not add hot-path tracing.
- Display reconfiguration and visible scenario execution are user-visible external actions;
  they are not silently automated by the pure tooling implementation.

## Cold-start managed-windowed unblocker

The first real repetition exposed a runtime defect rather than a performance result. On a clean
windowed start, the Qt widget can report `isVisible() == True` while its `QWindow` reports no
exposure and no paint events occur. `FollowSurfaceMixin` currently passes the widget-visible bit
to both the backend visibility policy and `VisibilityHelper`, so a backend-prepared surface that
requires mapping can be classified as already mapped and its show/remap callback is skipped.

Functional requirements for the unblocker:

- Add an explicit diagnostics-gated, allowlisted Qt presentation snapshot containing only the
  widget-visible bit, window-exposed bit, and bounded current paint count.
- Treat exposure, not widget visibility alone, as mapping proof only when the existing normalized
  `prepared_surface_requires_mapping` capability is true.
- Perform at most one controlled normal-surface remap after policy returns a show decision.
- Keep preparation side-effect-free with respect to `show()`/`showNormal()` and preserve the
  established flags, screen, geometry, platform preparation, and click-through ordering.
- Keep genuinely exposed and duplicate steady cycles as no-ops; preserve fullscreen preparation,
  warmup, unfocused prepared content, minimized-target, monitor-reconfiguration, and duplicate
  preparation behavior.
- Keep the generic follow surface backend-neutral; no raw backend/helper enum checks or private
  compositor imports are permitted.

Dependency map for the correction:

```text
backend visibility snapshot.prepared_surface_requires_mapping
        + Qt widget-visible/window-exposed presentation state
        -> backend-neutral effective mapped predicate
        -> existing visibility policy
        -> post-policy exactly-once remap callback
        -> existing geometry/flag/platform/click-through preparation order
```

Repeated host starts separated a second post-map attachment problem from target geometry. During
an unfocused failure the helper's target frame, buffer, and requested rectangle remain unchanged;
Qt is exposed, paints, and reports the requested geometry. Focusing Elite triggers one helper
presentation call without changing those rectangles, and the surface then attaches correctly.
The deferred remap therefore invalidates the helper's earlier attachment proof: the helper applied
presentation before the new Qt map existed, then its same-signature cache suppressed a second
apply. The correction must use a generic one-cycle presentation-refresh request transported
through `backend/consumers.py`; cache bypass remains owned by the GNOME bundle runtime. Generic
follow code must not import or inspect GNOME/helper types.

```text
controlled deferred Qt remap completes
        -> generic one-shot presentation-refresh request
        -> selected backend consumer forwards the request
        -> GNOME runtime bypasses matching-success/mismatch cache for one cycle
        -> helper reapplies attachment to the newly mapped surface
        -> subsequent identical cycles return to the normal cache/no-op path
```

The EDMC plugin compatibility baseline remains Python 3.10.3 32-bit for Windows, as recorded in
`docs/compliance/edmc_python_version.txt`; the controller/client independently require Python
3.10 or newer.

## Capture log-rotation invariant

The first accepted manual observation interval exposed a capture-runner defect: the overlay
client rotates `overlay_client.log` by rename while diagnostics remain active. The runner saved
only the active file's byte offset, then sought that old offset in the new, smaller active file.
It consequently reported zero events even though the rotated chain contained valid allowlisted
samples.

The runner must snapshot the active log's device/inode identity and offset at observation start.
At observation end it must locate that identity in the numeric rotation chain, read the remainder
of that file, then read each newer rotated file and the active file in chronological order. An
incomplete/expired chain must fail explicitly; it must never silently produce a partial capture.
Only already allowlisted performance events and repaint counts leave the reader.

## Reduced evidence oracle

The original 36 scenarios x five repetitions x 150 seconds produced a minimum 7.5-hour manual
gate before prompts and display changes. That cost is disproportionate for a pre-migration
comparison baseline. The approved reduced oracle keeps behavior-class coverage while removing
cross-products that repeat the same presenter/interaction contract on both scales and monitors.

- Uniform 100% retains stable managed and Shell-raster presenters on monitor A, both mode
  directions on A, stable managed placement on B, both fullscreen monitor-handoff directions,
  Alt-Tab in fullscreen, and Overview in windowed.
- Uniform 125% retains stable managed and Shell-raster presenters on A, both mode directions on
  A, and stable managed placement on B. Scale-independent shell interactions and reverse handoff
  are represented at 100% rather than repeated.
- Three repetitions preserve a minimal repeated sample for variance review.
- Fixed timing becomes 10 seconds warm-up, 15 seconds idle CPU, and 30 seconds observation.

This is 14 scenarios x three repetitions = 42 captures, approximately 38.5 minutes of fixed
timing plus prompts. The two already accepted 150-second captures belong to the superseded full
oracle and cannot be relabeled; they must remain preserved with that oracle and not count toward
the reduced matrix.
