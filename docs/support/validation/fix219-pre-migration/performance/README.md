# fix219 Pre-Migration Performance Evidence

## Gate status

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Versioned scenario manifest and strict privacy/schema validation | Completed |
| 3.2 | Deterministic summary and fixed-threshold comparison tooling | Completed |
| 3.9 | Pre-optimization reduced-v2 captures retained as historical evidence | Paused at 12/42 (2 superseded v1 captures also preserved) |
| 3.10 | Quiet diagnostic configuration and normal-use state | Completed |
| 3.11 | Backend-owned stable-target query pressure reduction | Completed |
| 3.12 | Proven unchanged-repaint suppression | Completed |
| 3.13 | Controlled helper A/B and reviewed pressure-reduction acceptance bounds | In progress; automated gate passed, live preflight blocked |
| 3.14 | Manual behavior regression and quiet-soak validation | Not started |
| 3.15 | New-identity 42-capture baseline and migration-regression thresholds | Not started |

### Current capture hold

**Do not resume the reduced-v2 matrix, enable its capture diagnostics, or continue with monitor
B.** The 12 accepted captures remain valid historical pre-optimization/incident-era evidence
under their original manifest, but helper-query and repaint behavior will change before the next
baseline. Pre- and post-optimization samples cannot share a summary or threshold population.

Stages 3.10–3.14 must pass first. Stage 3.15 then creates a new post-optimization
manifest/evidence identity and starts a coherent matrix at 0/42. No new identity, summary, or
threshold artifact is created during this documentation synchronization.

The user reviewed and approved this evidence hold on 2026-07-21. That approval does not
authorize Stage 3.10, change diagnostic configuration, or start a new capture.

The user separately authorized Stage 3.10 later on 2026-07-21. The client shadow now has
development mode disabled; repaint-debounce logging, tracing, payload logging, visual outlines,
and the debug overlay are disabled while repaint debounce remains enabled. The helper developer
configuration was backed up, retained enabled full-helper mode, and now has diagnostics disabled.
After the supported helper reload, health reported version 1.0.0/protocol 3 with diagnostics off.
A bounded 10-second probe completed 20 real target queries with zero failures and zero filtered
per-query or repaint-detail journal events. All 12 reduced-v2 and two superseded full-v1 capture
hashes were then revalidated. Stage 3.11 subsequently completed its backend-owned 1.5-second
stable-target cache correction with focused RED/GREEN unit evidence. Stage 3.12 subsequently
completed evidence-led unchanged-work suppression at the existing visual-fingerprint and
Shell-frame preparation seams. Stage 3.13 now has strict diagnostics-off work snapshots, bounded
helper pressure/actor health aggregates, a fixed cell runner, and passing focused/integrated/
project automated gates. Its live preflight has not passed because Firefox and the fixed Elite/
EDMC/client workload are not in the approved quiet state. No warm-up or cell sample has started,
and the capture hold remains in force.

Step 03 and the production-routing gate remain incomplete while any stage above is not
completed. In particular, there is intentionally no `thresholds.json`: numeric limits must
come from the real repeated baseline, not placeholder values or synthetic tests.

## Historical full-v1 attempt

The counts and blocker narrative in this section describe the superseded 180-capture v1 oracle.
They are retained to explain the cold-start correction and capture-runner hardening, not as the
current collection requirement.

The first 100% repetition was aborted on 2026-07-20 before artifact write. Elite was confirmed
windowed on `monitor_a`; the backend reported a healthy target, prepared/mapped managed surface,
matched rectangle, and visible content, while the client accepted the fixed fixture and emitted
repaint requests but recorded zero Qt paint events. The user saw neither fixture content over
Elite nor in the separate overlay application surface. Switching Elite to borderless fullscreen
made Shell-raster content visible; switching back to windowed then restored Qt painting (6-12
paint events per sampled interval). This isolates a cold-start managed-windowed remap/exposure
failure that the mode round trip masks. It is not an accepted baseline sample. Production
routing remains gated until the behavior is corrected and the matrix restarts from repetition 1.

The correction is now implemented locally and automated validation passes, but it has not yet
been accepted on the compositor. The generic follow surface uses the existing normalized
`prepared_surface_requires_mapping` contract to distinguish widget visibility from real
`QWindow` exposure and performs one post-policy controlled remap per managed-surface generation.
Capture-only diagnostics now report allowlisted widget-visible, window-exposed, and bounded
paint-count fields. A clean windowed EDMC/client restart, two-start visual acceptance, and both
fullscreen transition directions remain required before this blocker can be cleared. The gate
therefore remains at 0/180 and no capture or threshold artifact has been written.

Host attempt 1 with that local correction still failed. The first ordinary mapping briefly
became exposed and painted eight times, but exposure then dropped and paint intervals returned
to zero. The controlled recovery had been incorrectly consumed by the initial ordinary show.
The implementation and test contract now distinguish initial mapping from recovery so that a
hidden prepared surface receives one later controlled remap if it remains unexposed. This
follow-up still requires a new clean-start host check before the blocker can be cleared.

Repeated terminal-focused restarts showed that immediate hide/show recovery is itself racy: it
can expose and paint briefly, then lose exposure permanently, while other runs remain healthy.
One run also held a stale target rectangle until Elite gained focus, producing temporary wrong
placement. The recovery is now deferred to the next Qt main-loop turn so Mutter can observe the
unmap before remapping. Safe diagnostic booleans distinguish target focus, normalized mapping
requirement, Qt exposure, paints, and Qt/requested geometry agreement. This iteration remains
unaccepted until repeated terminal-focused and game-focused clean starts are deterministic.
Automated validation is green: the Step 03 focused gate passes with 126 tests, while
`make check` and `make test` passed the deferred-remap iteration with 1,335 tests and 21 existing
environment/runtime skips. A focused redacted geometry sample then showed no target rectangle
change when Elite gained focus. Instead, focus caused one helper presentation call after steady
unfocused cycles had reused attachment success cached before the remap. The correction now sends
one generic presentation-refresh request after the deferred Qt map completes; the GNOME backend
bypasses its matching cache for that cycle and immediately returns to normal caching afterward.
The backend/follow selection passes 139 tests, the Step 03 gate passes 126, and the updated
`make check`/`make test` gates each pass with 1,336 tests and the same 21 existing skips. The next
evidence must come from a clean host restart that loads this post-remap refresh iteration; the
running pre-restart client cannot validate it.

The first post-remap-refresh clean restart passed with the terminal focused throughout startup.
The overlay appeared correctly attached and placed without focusing Elite. Diagnostics showed
one deferred remap, one attachment reapply on the next cycle while the target remained unfocused,
then cached steady cycles with exposure, geometry agreement, and paints intact. This clears the
cold-start correction stage but supplies only 1/2 required clean-start checks. A second clean
start and both windowed/fullscreen transition directions remain required before baseline capture
can resume; the matrix remains 0/180.

The second clean terminal-focused start also passed and reproduced the same safe diagnostic
sequence. The clean-start requirement is therefore 2/2. Only the live windowed-to-borderless and
borderless-to-windowed acceptance checks remain before the baseline matrix can restart; it stays
at 0/180 until those transitions pass.

Repeated live transitions subsequently passed in both directions. Three reviewed
fullscreen-to-windowed sequences held the Shell raster through handoff, stabilized and applied
managed-surface preparation, then reached a visible/exposed, geometry-matched Qt window with the
overlay window found. The interval contains no warning/error, preparation-failure,
persistent-rectangle-mismatch, or wrong-monitor marker. The user reported one possible brief
missing-overlay observation but could not reproduce it; it is retained as an unconfirmed
handoff watch item, not an accepted invariant failure. The manual pre-capture gate is complete,
and the fixed baseline may restart at repetition 1. The matrix remains 0/180 until that capture
is accepted.

The first capture attempt then completed its timing and manual checks but was rejected before
write because the active diagnostic log rotated during observation and the runner's old
offset-only read returned no events. The runner now tracks device/inode/offset and reads the
original remainder plus every newer numeric rotation in chronological order, failing explicitly
for expired or incomplete history. Unit and full project gates pass. The complete repetition was
rerun twice and independently validated with zero manual failures and no prohibited raw fields.
Those two long-form captures are preserved with the superseded full v1 oracle and do not count
toward the approved reduced v2 matrix, which starts at 0/42.

## Historical reduced-v2 gate

The reduced v2 oracle contains 14 representative scenarios and three repetitions. It keeps both
scales, managed and Shell-raster presenters, both mode-transition directions, placement on both
monitors, bidirectional fullscreen handoff, Alt-Tab, and Overview. It removes redundant
interaction/transition and per-monitor cross-products. Fixed timing is 10 seconds warm-up,
15 seconds idle CPU, and 30 seconds observation, for about 38.5 minutes plus prompts.

Twelve captures completed before the pressure-reduction amendment. Preserve this manifest and
every capture under its identity for historical validation only; do not complete its remaining
30 repetitions.

## Fixed oracle

`manifest.json` is the frozen schema-version-1 oracle for the historical reduced-v2 captures. It
remains machine-valid so those artifacts can be reviewed, but it is not the manifest for the
future clean baseline or later candidate comparisons. It fixes:

- Ubuntu 24.04.4 LTS, native Wayland, GNOME Shell/Mutter 46.0;
- shipped pre-migration plugin/client version 1.0.0, helper protocol 3, and source revision
  `3d2332869454d6561995203752fd239a558a95a5` for baseline captures;
- two 3440x1440 horizontal monitors, with `monitor_a` physically left of primary `monitor_b`;
- observed GNOME Shell global logical geometry `(0,0,3440,1440)` /
  `(3440,0,3440,1440)` at 100%, and `(0,0,2752,1152)` /
  `(2752,0,2752,1152)` at 125%;
- the corresponding primary-monitor-relative projection
  `(-3440,0,3440,1440)` / `(0,0,3440,1440)` at 100%, and
  `(-2752,0,2752,1152)` / `(0,0,2752,1152)` at 125%;
- `tests/archive/display_all.json` as the representative payload fixture, identified by its
  committed SHA-256;
- 10 seconds of warm-up, 30 seconds of observation, a fixed 15-second idle CPU interval, and
  three repetitions;
- separate client `perf_counter` and GNOME Shell monotonic elapsed domains;
- stable managed/Shell presenters and both mode-transition directions on monitor A at both
  scales, stable managed placement on monitor B at both scales, both fullscreen handoff
  directions at 100%, Alt-Tab in fullscreen, and Overview in windowed.

Mixed per-monitor scale, vertical layouts, runtime primary-monitor changes, and exclusive
fullscreen are explicitly outside this acceptance gate.

Validate the oracle from the repository root:

```bash
python3 scripts/backend_performance.py validate-manifest \
  docs/support/validation/fix219-pre-migration/performance/manifest.json
```

## Historical reduced-v2 preflight (frozen; do not run)

The following procedure documents how the 12 historical captures were produced. It is retained
for provenance and must not be used as the next-run workflow. In particular, do not enable the
diagnostic settings below after the current capture hold.

Before collecting evidence, verify all of the following without recording monitor serials,
usernames, process command lines, window titles, raw target handles, or tokens:

1. `/etc/os-release` reports Ubuntu 24.04.4 LTS.
2. `gnome-shell --version` reports GNOME Shell 46.x.
3. `XDG_SESSION_TYPE=wayland` and the desktop is GNOME.
4. The installed helper reports healthy protocol 3 and is running in `full_helper` mode with
   diagnostics enabled.
5. EDMC, the overlay client, and helper use the baseline versions/revision fixed in the
   manifest.
6. The representative fixture hash matches the manifest.
7. Both monitors are configured exactly as the selected display configuration, with
   `monitor_b` remaining primary.

The initial sandboxed helper query was a false negative. Host-session rechecks on 2026-07-20
confirmed EDMC, Elite, and the overlay client running; helper version `1.0.0`/protocol `3`
healthy on D-Bus with the full target/presentation feature gate; and a live `target_found`,
rectangle-matched `presentation_applied` cycle. The 100% display topology is now verified with
`monitor_a` left of primary `monitor_b`. Mutter and Qt normalize the observed global coordinates
from the leftmost display, so the manifest records those real values separately from its
machine-validated primary-relative negative-coordinate projection.

For capture only, start EDMC so the overlay client inherits:

```bash
MODERN_OVERLAY_DEV_MODE=1
EDMC_OVERLAY_GNOME_PRESENTATION_DIAGNOSTICS=1
```

Set `log_repaint_debounce=true` in the dev-mode `dev_settings.json`. Keep repaint debounce
enabled and visual overlays disabled. Configure the GNOME helper's existing developer file as
`{"enabled":true,"mode":"full_helper","diagnostics":true}` and reload the helper before
preflight. Restore normal diagnostic settings after capture.

## Historical reduced-v2 capture execution (frozen; do not run)

Create one sanitized schema-version-1 capture JSON document for every manifest scenario and
repetition. The pure validator is the authoritative field contract; a capture contains only:

- manifest/capture/scenario IDs, role, and repetition;
- the exact allowlisted environment and component versions;
- fixed display/fixture/diagnostic references and timing values;
- already elapsed latency samples with their declared originating clock domain and safe random
  correlation IDs;
- allowlisted helper/raster/repaint/frame work values;
- fixed-interval client and GNOME Shell CPU samples;
- the complete boolean manual invariant checklist plus optional safe note codes; and
- a safe diagnostic reference, never a personal path.

For each scale:

1. Apply the exact display configuration and confirm both monitors are horizontally contiguous,
   with `monitor_a` physically left of primary `monitor_b`. Verify both the observed compositor
   geometry and its manifest-defined primary-relative negative projection.
2. Start from a clean EDMC/client/helper state and allow the 10-second warm-up.
3. Run scenarios in manifest order. For stable scenarios, observe both the idle interval and
   representative fixture activity. For transition scenarios, perform the named direction on
   the named monitor. For handoffs, move fullscreen A-to-B or B-to-A as named. For shell
   interactions, perform Alt-Tab or Overview entry/exit before, during, and after the named
   stable/transition state.
4. Repeat each scenario three times without changing fixture, diagnostics, layout, scale, or
   timing.
5. During every repetition review all manual checklist items. Any `true` item blocks the
   baseline rather than becoming an accepted sample.
6. Sanitize the raw client/helper/CPU material before it enters this tree, then validate the
   normalized capture documents:

```bash
python3 scripts/backend_performance.py validate-captures MANIFEST CAPTURE [CAPTURE ...]
```

Use the interactive capture runner for each repetition. It reads only the new allowlisted
`BACKEND_PERFORMANCE_SAMPLE` JSON events and numeric `Repaint stats` intervals from the client
log; process command lines and broad logs are never copied into the output. The runner performs
the fixed warm-up, a separate idle-CPU interval, the observation interval, and the complete
manual checklist, then sends the resulting document back through the strict capture validator
before writing it:

```bash
python3 scripts/backend_performance_capture.py MANIFEST \
  --scenario SCENARIO_ID --repetition REPETITION \
  --client-pid CLIENT_PID --gnome-shell-pid GNOME_SHELL_PID \
  --client-log OVERLAY_CLIENT_LOG --output CAPTURE
```

Existing output is never overwritten. At the manual prompt enter `none` only after reviewing
all eight invariants, or enter the exact comma-separated field names that occurred. A true
manual observation remains valid diagnostic evidence but blocks acceptance.

Raw monotonic clock origins are forbidden. Record only elapsed values computed within their
originating process. Shared safe correlations may associate client and helper events, but no
tool subtracts one process's clock from another's.

## Pressure-reduction A/B evidence

The quiet four-cell A/B uses diagnostics off and records only allowlisted bounded aggregate
counters, state changes, normalized failures, and narrowly scoped resource samples. It produces
reviewed **pressure-reduction acceptance bounds** for stable helper-query/repaint work, resource
load, and safety. Those bounds remain in the A/B report and decide whether Stage 3.14 may begin.
They are not stored in `thresholds.json` and are not later migration comparison limits.

The new Stage 3.15 capture instructions and identity are written only after the A/B and manual
regression/quiet-soak gates pass. Do not clone the historical diagnostics-enabled procedure into
that workflow.

## Required manual checklist

Every repetition must explicitly record `false` for all of these before it can be accepted:

- `dual_visible_presenters`
- `title_bar_intermediate`
- `monitor_relative_intermediate`
- `black_surface`
- `focus_trap`
- `unexpected_identity`
- `premature_commitment`
- `material_hitch`

If any item is observed, stop that scenario, retain only sanitized diagnostic evidence, and
investigate. Timing aggregates never override a visible/invariant failure.

## Historical evidence layout and future clean summary

The historical captures remain in their current layout. A future clean identity uses its own
new evidence root and may adopt this internal shape only after Stage 3.15 begins:

```text
captures/<scale>/<scenario-id>/repetition-<n>.json
summaries/baseline-summary.json
summaries/baseline-summary.txt
thresholds.json
```

Do not add screenshots, arbitrary prose notes, broad environment dumps, personal paths,
command lines, raw IDs/handles, or unsanitized logs. Keep any reviewed raw diagnostic material
outside the repository if it cannot satisfy the normalized capture schema.

Do not generate a complete summary from the 12 historical captures. Generate the deterministic
clean baseline summary only after every required capture exists under the new Stage 3.15
identity:

```bash
python3 scripts/backend_performance.py summarize NEW_MANIFEST \
  --summary-id NEW_POST_OPTIMIZATION_SUMMARY_ID \
  --require-complete CAPTURE [CAPTURE ...] > NEW_EVIDENCE_ROOT/summaries/baseline-summary.json
```

Use `--format text` for the concise review view.

## Freezing migration-regression thresholds

Analyze repeated variance only after the new coherent 42-capture baseline and manual review pass.
Create schema-version-1 `thresholds.json` containing every required latency, helper/raster/
repaint/frame-work, and idle-CPU metric. These are **migration-regression thresholds** for later
fix219 steps, distinct from the earlier A/B pressure bounds. Each entry must contain both:

- a relative investigation limit; and
- a positive absolute noise floor.

The provenance must name the baseline summary, capture date, three repetitions, reviewed/frozen
state, sanitized diagnostic references, and rationale. Candidate comparison never infers or
overwrites thresholds. Later changes require an explicit documented re-review.

Compare a candidate only after the frozen artifact is committed:

```bash
python3 scripts/backend_performance.py compare \
  NEW_MANIFEST BASELINE_SUMMARY CANDIDATE_SUMMARY THRESHOLDS
```

Any invariant/visible failure reports `blocked`. A numeric regression reports `investigate`
only when it exceeds both its fixed relative limit and absolute noise floor. Work and idle-CPU
regressions remain separate reasons even when latency is stable.
