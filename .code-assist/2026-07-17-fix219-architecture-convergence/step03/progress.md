# Step 03 Progress

Current-state rule: the implementation checklist below and the newest dated section are
authoritative. Older statements such as “ready to restart” remain chronological evidence of the
state at that time and are superseded by later dated decisions; do not use them as current run
instructions.

## Implementation Checklist

- [x] Stage 3.1: verified branch/HEAD/worktree and read the complete required design/task set.
- [x] Stage 3.2: selected pure unit tests plus mandatory manual validation and documented the
  acceptance surface, touchpoints, environment, and dependency map.
- [x] Stage 3.3: wrote the complete test surface before implementation and recorded RED evidence.
- [x] Stage 3.4: implemented pure manifest/capture/threshold validation and summary comparison.
- [x] Stage 3.5: added the committed scenario manifest, CLI, evidence workflow, and artifact tests.
- [x] Stage 3.6: refactored and passed targeted/project validation.
- [x] Stage 3.7: prove and correct the cold-start managed-windowed exposure/remap defect.
- [x] Stage 3.8: pass two clean-start and transition manual acceptance checks.
- [ ] Stage 3.9: retain the pre-optimization reduced-v2 matrix as historical evidence
  (paused at 12/42; two superseded full-v1 captures also preserved).
- [x] Stage 3.10: disable capture diagnostics and establish quiet normal-use state.
- [x] Stage 3.11: reduce backend-owned stable-target query pressure test-first.
- [x] Stage 3.12: attribute and suppress proven unchanged repaint work test-first.
- [ ] Stage 3.13: run the controlled helper A/B and review pressure-reduction acceptance bounds.
- [ ] Stage 3.14: repeat manual behavior regression and quiet-soak validation.
- [ ] Stage 3.15: create a new identity, capture a clean 0/42 baseline, and freeze
  migration-regression thresholds.
- [ ] Stage 3.16: update authoritative completion evidence and commit without pushing.

## Setup Notes

- Mode: auto.
- Documentation directory:
  `.code-assist/2026-07-17-fix219-architecture-convergence/step03/`.
- Branch: `backend-refactor-implementation`.
- Initial HEAD: `3d2332869454d6561995203752fd239a558a95a5`.
- Initial branch divergence: 0 ahead / 0 behind.
- Initial worktree: clean.
- Root `.venv` is the canonical development/test environment.
- No `CODEASSIST.md` exists; `AGENTS.md` and the approved fix219 artifacts govern.
- Test selection: unit tests for all pure behavior plus mandatory real-world GNOME validation.
  Harness/GUI tests are not selected because no plugin lifecycle or UI/runtime wiring changes.
- Cold-start fix test selection: unit tests cover the backend-neutral Qt exposure predicate,
  exactly-once post-policy remap, preparation no-show contract, and steady-state no-op behavior.
  Manual GNOME validation remains mandatory because compositor exposure, paint delivery, focus,
  and visible intermediate surfaces cannot be proven by stubs. No `load.py`/hook flow is touched,
  so the harness-test gate does not apply.

## Environment Evidence

- Host: Ubuntu 24.04.4 LTS, native Wayland, GNOME Shell 46.0.
- Displays: two 3440x1440 monitors at uniform 100% scale. The verified topology places
  `monitor_a` physically left of primary `monitor_b`.
- Mutter and Qt normalize the observed global geometry to `(0, 0)` and `(3440, 0)`. The manifest
  now records those actual coordinates separately from its derived primary-relative projection
  `(-3440, 0)` and `(0, 0)`; the validator proves the projection rather than claiming Mutter
  emits negative global coordinates. The 125% configuration has not yet been captured.
- The initial sandboxed helper query was a false negative. A host-session recheck on 2026-07-20
  confirmed EDMC, Elite, and the overlay client running; helper version `1.0.0`/protocol `3`
  healthy on D-Bus with the full target/presentation feature gate; and live rectangle-matched
  `target_found`/`presentation_applied` cycles. Only the required display reconfiguration and
  manual capture remain blocked on user-visible interaction.

## TDD Cycles

### Cycle 1: Complete Step 03 acceptance surface

- Added `overlay_client/tests/test_backend_performance_summary.py` before implementation.
- The first attempted command found that the root `.venv` referenced by the handoff is absent
  in the current workspace. System Python 3.12.3 has pytest 7.4.4, so the same focused command
  was rerun with `python3` without installing or changing dependencies.
- The focused command exited 2 during collection with the expected missing pure evidence module
  (`overlay_client.backend.performance_evidence`); output is in `logs/red-targeted.log`.
- No fixture, test-framework, collector-test, Qt, or EDMC harness failure occurred.

### Cycle 2: Pure manifest, capture, summary, and comparison contracts

- Added strict schema-v1 immutable models and allowlist-only parsers in
  `overlay_client/backend/performance_evidence.py`.
- Kept client/helper elapsed domains separate, used nearest-rank p95, normalized work by the
  fixed observation/transition counts, and made invariant failures block before numeric gates.
- The first GREEN attempt passed 76 tests and exposed one Windows-path privacy regex gap plus
  three incorrect test expectations. The regex was hardened and the arithmetic/message/
  immutability assertions were corrected without weakening behavior.

### Cycle 3: Committed manifest and CLI

- Added the 36-scenario GNOME 46 manifest for the observed two-3440x1440 hardware at fixed
  uniform 100%/125% left-of-primary layouts, with normalized compositor geometry and a
  validated primary-relative negative projection.
- Added the thin `scripts/backend_performance.py` validate/summarize/compare CLI only after its
  subprocess test produced the expected missing-script RED failure (`logs/red-cli.log`).
- Added the exact manual capture, privacy review, evidence layout, invariant checklist, and
  threshold-freeze workflow under the validation tree.
- Focused GREEN result: 82 passed (`logs/green-cli.log`).

### Cycle 4: Privacy-safe live capture seam and runner

- Rejected the legacy broad diagnostic scripts for committed evidence because they collect
  command lines, raw helper target data, and unsanitized logs.
- Added a diagnostics-gated, allowlist-only presentation-cycle event at the existing generic
  backend consumer seam. Its unit contract proves that target tokens, titles, and personal
  paths cannot enter the event.
- Added a pure capture adapter for strict event/repaint parsing, fixed-interval CPU arithmetic,
  normalized latency/work assembly, and revalidation through the evidence schema.
- Added an interactive runner that enforces the manifest warm-up, idle-CPU and observation
  intervals plus the complete manual checklist, refuses overwrite, and writes no raw log or
  process metadata.
- Focused RED was the missing event builder/logger and missing capture module; focused GREEN is
  30 tests across the capture and follow-surface unit files. Focused Ruff, format, and mypy pass.

## Validation Evidence

- Focused unit/collector gate: 85 passed after the live-coordinate correction (the earlier
  84-test result remains in `logs/targeted-final.log`).
- Focused Ruff and format checks: passed (`logs/ruff-focused-final.log` and
  `logs/format-focused-final.log`).
- Focused mypy: passed for the pure evidence module and CLI (`logs/mypy-focused-final.log`).
- Headless suite: 1,280 passed, 41 skipped after the live-coordinate correction (the earlier
  1,279-test result remains in `logs/headless-pytest-final.log`).
- `make check PYTHON=overlay_client/.venv/bin/python`: whole-repository Ruff passed, configured
  mypy passed for 92 source files, and GUI-enabled pytest passed with 1,316 passed and 21
  skipped (`logs/make-check-final.log`).
- `make test PYTHON=overlay_client/.venv/bin/python`: GUI-enabled pytest passed with 1,316
  passed and 21 skipped (`logs/make-test-final.log`).
- Manifest CLI validation: 36 scenarios and five repetitions passed
  (`logs/manifest-validation.log`).
- EDMC compatibility-floor check passed under the documented development override and repeated
  the existing 64-bit-versus-preferred-32-bit warning (`logs/edmc-python-check.log`).
- Compile and patch-hygiene checks passed (`logs/compileall.log` and `logs/diff-check.log`).
- The 41 headless and 21 GUI-enabled skips retain their existing environment/runtime gates.
- The first full-suite attempt with system Python failed during collection because it exposes
  only incomplete PyQt shims. The root `.venv` named by the handoff is absent; the intact
  `overlay_client/.venv` provides pytest 8.3.3, Ruff, mypy, and real PyQt and was therefore used
  for every final gate.

## Manual Gate

Preflight is cleared for the 100% configuration. The host matches Ubuntu 24.04.4/GNOME Shell 46, the source and
fixture hashes match the manifest, and two physical 3440x1440 monitors are present. A
host-session recheck confirmed EDMC, Elite, and the overlay client running plus helper version
`1.0.0`/protocol `3` healthy on D-Bus with live rectangle-matched
`target_found`/`presentation_applied` cycles. The 100% left-of-primary topology now matches the
corrected observed/primary-relative manifest geometry. EDMC/client were cleanly restarted with
the two capture-only flags, repaint diagnostic logging enabled, and visual outlines disabled.
The running client emitted a real allowlisted performance marker accepted by the new parser.
The first 100% repetition was aborted without writing an artifact. Elite was verified windowed
on `monitor_a`; fixture messages were acknowledged and repaint requests ran, but every sampled
five-second interval recorded zero Qt paint events while backend diagnostics incorrectly
reported the managed surface mapped and content visible. The user saw no overlay content over
Elite or in the separate application surface. A borderless-fullscreen round trip restored the
windowed overlay and Qt paint counts immediately rose from zero to 6-12 per sampled interval.
This isolates a cold-start managed-windowed remap/exposure defect; using the round trip as an
undocumented priming workaround would invalidate the stable-windowed baseline. This blocks the
matrix before repetition 1. The 100% and 125% repetitions, later 125% reconfiguration, summary,
and threshold freeze remain.
The exact procedure and blocker are recorded in
`docs/support/validation/fix219-pre-migration/performance/README.md`.

Step 03 and Phase stage 1.3 remain incomplete/in progress. Step 05 production routing remains
blocked. No raw capture, summary, or placeholder threshold artifact was fabricated.

## Commit Status

No Step 03 commit exists because the selected step's mandatory manual evidence is incomplete.
Nothing has been pushed.

## Cold-start correction resume — 2026-07-20

- Verified the handoff against branch `backend-refactor-implementation`, HEAD
  `3d2332869454d6561995203752fd239a558a95a5`, the intentionally dirty Step 03 worktree, temporary
  capture settings, and absent repetition-1 artifact.
- Confirmed the failure seam: `FollowSurfaceMixin` passes `isVisible()` into policy and
  `VisibilityHelper`; the helper therefore skips the existing show callback when a prepared Qt
  widget is visible but its `QWindow` is not exposed.
- Selected a backend-neutral correction driven only by the existing normalized
  `prepared_surface_requires_mapping` flag. Raw helper/backend dispatch remains forbidden.
- Added diagnostic and remap acceptance tests before runtime changes. Focused RED produced the
  expected three failures: missing allowlisted Qt presentation fields in direct/logged samples,
  and no visibility events for a widget-visible but unexposed prepared surface. Seven neighboring
  tests passed; evidence is in `logs/red-cold-start-remap.log`.
- Implemented a backend-neutral effective-mapping predicate that consults `QWindow.isExposed()`
  only when the normalized preparation contract requires mapping. A generation marker permits
  one controlled post-policy remap and makes duplicate unexposed cycles no-ops.
- The recovery order is flags, hide, prime geometry, show, platform preparation, then the
  existing helper-driven click-through application. Preparation still does not show or hide.
- Added allowlisted `qt_widget_visible`, `qt_window_exposed`, and bounded `qt_paint_count`
  diagnostic fields. The strict capture parser required a matching schema update: its RED was
  five expected unexpected-field/validation failures in `logs/red-cold-start-capture-schema.log`;
  GREEN is 7 passed in `logs/green-cold-start-capture-schema.log`.
- New diagnostic/remap selection: 10 passed; complete follow/policy/consumer focus: 81 passed
  (`logs/green-cold-start-remap-attempt-1.log`, `logs/green-cold-start-focused.log`).
- Stage 3.7 remains in progress pending automated gates and host proof.

## Cold-start correction automated validation

- Step 03 focused gate:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_performance_summary.py overlay_client/tests/test_backend_performance_capture.py overlay_client/tests/test_follow_surface_mixin.py tests/test_debug_collectors.py -q`
  passed with 122 tests (`logs/step03-focused-cold-start-final.log`).
- Complete repository-venv pytest passed with 1,294 tests and 41 existing skips
  (`logs/pytest-venv-cold-start-final.log`). The first attempt had one test-order-only logging
  failure because another test intentionally disabled logger propagation; the diagnostic test
  now owns/restores that global state.
- `make check PYTHON=overlay_client/.venv/bin/python` passed whole-repository Ruff, configured
  mypy for 92 source files, and GUI-enabled pytest with 1,331 passed and 21 existing skips
  (`logs/make-check-cold-start.log`).
- `make test PYTHON=overlay_client/.venv/bin/python` passed with 1,331 tests and 21 existing
  skips (`logs/make-test-cold-start.log`).
- Focused Ruff, format, pure capture-module mypy, `git diff --check`, and the EDMC Python-floor
  check passed. The Python-floor check retained the expected 64-bit-versus-preferred-32-bit
  warning.
- Direct mypy over the unconfigured `follow_surface.py` mixin plus the capture module reports 22
  longstanding errors in `follow_geometry.py` and unannotated mixin attributes; the new
  remap-generation assignment error seen on the first attempt was removed. The project-configured
  mypy gate passes, and focused mypy for the pure changed capture module passes.
- System-Python headless collection remains unavailable because its partial PyQt shims cause 21
  import errors before tests run. This matches the prior Step 03 environment limitation; the
  intact repository venv supplied both complete non-GUI and GUI-enabled evidence.
- The currently running overlay client predates the correction: its events lack the new Qt
  diagnostic fields. A clean EDMC/client restart is required before host proof.

## Cold-start correction host attempt 1

- The first clean windowed restart with the correction failed manual acceptance; the user saw
  the standalone application surface but no overlay on the game window. Step 03 remains 0/180.
- Privacy-safe diagnostics proved the hidden-start sequence: preparation ran while the widget
  was hidden, the first ordinary show briefly became exposed and produced eight paints, then
  exposure dropped to false and five-second paint counts returned to zero permanently.
- No controlled-remap marker was logged. Root cause: the implementation marked every ordinary
  show as the generation's recovery attempt, so the later visible-but-unexposed state was
  treated as already recovered.
- Added the exact hidden-start/initial-show/exposure-loss sequence as a RED test. It failed with
  only `show` instead of expected `show, hide, show`; evidence is in
  `logs/red-cold-start-hidden-map-recovery.log`.
- Changed the marker so only a controlled remap consumes the one recovery attempt. An initial
  hidden-surface show may therefore be followed by exactly one controlled remap if exposure is
  absent on the next presentation cycle. The diagnostic/managed-windowed selection passes with
  11 tests in `logs/green-cold-start-hidden-map-recovery.log`.

## Cold-start correction host attempts 2–5

- Four terminal-focused cold restarts produced inconsistent manual outcomes: no overlay, an
  overlay at the wrong position until Elite gained focus, and correct immediate presentation.
  None is accepted; Step 03 remains 0/180.
- Every new run scheduled the one controlled remap. In the failed presentation, immediate
  hide/show briefly produced exposure and ten paints, then exposure dropped permanently; later
  Elite focus changes did not recover it. Successful runs retained exposure and nonzero paints.
- The wrong-position run used one stable helper target rectangle while Elite was unfocused; the
  same target's rectangle shifted when Elite later gained focus, after which ordinary geometry
  preparation corrected placement. This is a target-geometry/focus race distinct from Qt
  exposure and requires further evidence before changing target policy.
- Replaced same-stack hide/show with one main-event-loop-deferred recovery. The recovery now
  hides and primes geometry synchronously, suppresses duplicate cycles while pending, then shows,
  reapplies platform preparation, and reapplies click-through from the queued main-thread
  callback. Only the deferred recovery consumes the generation marker.
- Added safe boolean diagnostics for target focus, the normalized mapping requirement, and
  Qt-frame-versus-requested-geometry agreement. No identities or coordinates enter the event or
  normalized capture evidence.
- RED contained the expected 12 missing-deferred/schema failures in
  `logs/red-deferred-remap-geometry-diagnostics.log`; targeted GREEN passes and the expanded
  follow/policy/consumer/capture suite passes with 93 tests
  (`logs/green-deferred-remap-geometry-diagnostics-attempt-1.log`,
  `logs/green-deferred-remap-focused.log`).

## Deferred-remap automated validation

- The exact Step 03 focused gate passed with 126 tests:
  `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_performance_summary.py overlay_client/tests/test_backend_performance_capture.py overlay_client/tests/test_follow_surface_mixin.py tests/test_debug_collectors.py -q`
  (`logs/green-deferred-remap-focused-final.log`).
- Focused Ruff, Ruff format, and `git diff --check` passed for the changed follow-surface,
  capture, and test files.
- `make check PYTHON=overlay_client/.venv/bin/python` passed whole-repository Ruff, configured
  mypy for 92 source files, and GUI-enabled pytest with 1,335 passed and 21 existing skips
  (`logs/make-check-deferred-remap.log`).
- `make test PYTHON=overlay_client/.venv/bin/python` passed with 1,335 tests and 21 existing
  skips (`logs/make-test-deferred-remap.log`).
- No `load.py`, plugin hook, Tk lifecycle, socket, or controller wiring changed, so the required
  test type remains unit tests plus real compositor acceptance; no new harness test is selected.
- Stage 3.7 remains in progress until repeated clean-start host checks prove the deferred remap
  and geometry behavior. The performance matrix remains blocked at 0/180.

## Cold-start correction host attachment diagnosis

- Repeated terminal-focused starts now consistently expose and paint the deferred-remapped Qt
  surface, but it is not attached correctly until Elite gains focus.
- Safe event data reports `qt_geometry_match=true` both before and after focus. A redacted direct
  helper sample showed stable frame and buffer rectangles, no content rectangle, and only the
  focus bit changing. The target rectangle did not move during the observed focus transition.
- The client log showed the decisive behavioral change: the unfocused steady path reused a
  cached successful presentation, while focus triggered one helper presentation call for the
  same requested rectangle and the user observed correct attachment immediately afterward.
- Root cause: the helper's successful attachment was cached before the controlled deferred Qt
  remap. Remapping creates a new compositor map, but the unchanged presentation signature causes
  later cycles to skip attachment reapplication.
- Selected correction: a one-shot backend-neutral presentation-refresh request after deferred
  map completion. `backend/consumers.py` transports it; the GNOME runtime owns the one-cycle cache
  bypass. Tests are unit-level because the logic is deterministic/injectable and no `load.py`,
  EDMC hook, Tk lifecycle, or socket wiring changes. Real compositor proof remains mandatory.

## Post-remap attachment refresh implementation

- RED produced four expected failures: the generic consumer and GNOME runner lacked the refresh
  argument, follow did not request a refresh after remap, and both matching-success and persistent-
  mismatch caches suppressed reapplication
  (`logs/red-post-remap-presentation-refresh.log`).
- Added one optional `presentation_refresh_requested` boolean to the generic consumer call. It is
  forwarded behind the backend boundary; generic follow does not inspect a backend/helper enum or
  import compositor implementation code.
- Deferred-remap completion sets the request only after `show()`, platform preparation, and
  click-through succeed. The next successful backend cycle consumes it; exceptions retain it for
  retry, and reset/fullscreen paths clear it.
- The GNOME runtime bypasses suppressed-poll, matching-success, and persistent-mismatch cache
  exits for that requested cycle. It does not clear surface-preparation or transition state, and
  the following identical cycle returns to the normal cached no-op path.
- Targeted GREEN: 4 passed (`logs/green-post-remap-presentation-refresh-attempt-1.log`). Backend
  boundary/consumer/GNOME-runtime/follow selection: 139 passed
  (`logs/green-post-remap-presentation-refresh-focused-final.log`). Step 03 focused gate: 126
  passed (`logs/step03-focused-post-remap-presentation-refresh.log`).
- Focused Ruff and format checks plus `git diff --check` passed. `make check` passed repository
  Ruff, configured mypy for 92 source files, and GUI-enabled pytest with 1,336 passed/21 existing
  skips (`logs/make-check-post-remap-presentation-refresh.log`). `make test` passed with the same
  1,336/21 result (`logs/make-test-post-remap-presentation-refresh.log`).
- The running client predates this attachment-refresh iteration. Stage 3.7 and the 0/180 matrix
  remain blocked until a clean restart proves correct terminal-focused attachment without first
  focusing Elite.

## Post-remap attachment host acceptance 1

- The first clean restart with terminal focus passed visually: the overlay started attached and
  correctly placed without Elite receiving focus.
- Safe diagnostics confirmed the intended sequence. The managed surface lost exposure, scheduled
  and completed one deferred remap, then the next cycle made one helper presentation call while
  `target_has_focus=false`. The following steady cycles made zero presentation calls.
- Exposure recovered to true, geometry agreement remained true, paints rose immediately, and
  those conditions remained stable while Elite stayed unfocused.
- Stage 3.7 is completed. Stage 3.8 is in progress at 1/2 required clean starts; a second clean
  terminal-focused restart and both mode-transition directions are still required. The baseline
  matrix remains at 0/180 until the full manual acceptance gate passes.

## Post-remap attachment host acceptance 2

- The second independent clean terminal-focused restart also passed visually: immediate correct
  attachment and placement without first focusing Elite.
- Diagnostics repeated the expected contract: one deferred remap, one next-cycle presentation
  refresh with `target_has_focus=false`, then cached steady cycles with exposure, geometry
  agreement, and nonzero paints.
- The clean-start requirement is now 2/2. Stage 3.8 remains in progress only for the live
  windowed-to-borderless and borderless-to-windowed transition checks. The matrix remains 0/180
  until those checks pass and repetition 1 can restart from its fixed baseline.

## Post-remap mode-transition host acceptance

- Repeated windowed-to-borderless/fullscreen and borderless/fullscreen-to-windowed transitions
  passed visually in both directions.
- Three recorded fullscreen-to-windowed sequences each held the Shell raster during handoff,
  stabilized the managed-surface preparation, then reached a visible and exposed Qt window with
  the overlay window found and geometry matched. No warning/error, preparation-failure,
  persistent-rectangle-mismatch, or wrong-monitor marker was present in the reviewed interval.
- The user may have seen the overlay missing briefly on one fullscreen-to-windowed transition,
  but could not reproduce it. This remains an unconfirmed handoff watch item rather than a
  recorded invariant failure; the reviewed transitions all completed successfully.
- Stage 3.8 is completed. Stage 3.9 is unblocked and ready to restart the fixed baseline at
  repetition 1; no sample has yet been accepted, so the matrix remains 0/180.

## Capture runner log-rotation defect

- The first restarted `scale_100_stable_windowed_monitor_a` repetition completed its fixed
  30-second warm-up, 60-second idle CPU interval, 60-second observation, and manual review with
  all eight invariants false.
- The runner correctly refused to write an artifact because it received zero parsed performance
  events. Review showed that `overlay_client.log` rotated during the observation: valid events
  continued in the renamed/current chain, but the runner sought the old byte offset in the new,
  smaller active file.
- Repetition 1 remains unaccepted at 0/180; no capture file was written. Test type is unit because
  cursor/rotation traversal is deterministic filesystem logic with `tmp_path`; no `load.py`, hook,
  EDMC lifecycle, or Tk flow changes, so no harness test is selected.
- Planned RED/GREEN: prove one- and multi-rotation chronological reads plus explicit expired-chain
  rejection, implement an inode/offset cursor in the capture script, run the focused capture
  tests and Ruff/format/diff checks, then repeat the entire fixed repetition.
- RED produced four expected missing-cursor failures
  (`logs/red-capture-log-rotation.log`). The runner now snapshots device/inode/offset, reads a
  stable bounded snapshot of the original remainder and every newer numeric segment, and rejects
  expired, incomplete, truncated, or concurrently changed chains.
- Capture tests pass 15/15 (`logs/green-capture-log-rotation.log`); the complete Step 03 focused
  gate passes 130 tests (`logs/step03-focused-capture-log-rotation.log`). Focused Ruff, format,
  and `git diff --check` pass. The rejected real repetition must now be rerun from its warm-up.
- `make check PYTHON=overlay_client/.venv/bin/python` passed repository Ruff, configured mypy
  for 92 source files, and GUI-enabled pytest with 1,340 passed/21 existing skips
  (`logs/make-check-capture-log-rotation.log`). `make test` passed with the same 1,340/21 result
  (`logs/make-test-capture-log-rotation.log`).
- The full fixed repetition was rerun and accepted. Independent capture validation reports one
  valid repetition with 122 latency samples, 60 client CPU samples, 60 GNOME Shell CPU samples,
  93 paints, 1,682 repaints, and zero manual invariant failures. The prohibited-field scan was
  empty. Stage 3.9 is now 1/180.
- Stable-windowed monitor-A repetition 2 independently validated with 122 latency samples,
  90 paints, 1,682 repaints, 60 client and 60 Shell CPU samples, zero manual failures, and an
  empty prohibited-field scan. Stage 3.9 is now 2/180.

## Reduced matrix redesign

- The user stopped repetition 3 before warm-up and approved replacing the 180-capture gate with
  a substantially smaller representative matrix.
- The selected contract is 14 scenarios x three repetitions = 42 captures, with fixed timing of
  10 seconds warm-up, 15 seconds idle CPU, and 30 seconds observation (about 38.5 minutes plus
  prompts). It retains both scales, both presenters, both mode directions, both monitors,
  bidirectional fullscreen handoff, Alt-Tab, and Overview while dropping redundant cross-products.
- The two accepted long-form captures remain truthful evidence for the superseded full oracle and
  will be preserved with its original manifest. They do not count toward the reduced matrix,
  which restarts at 0/42.
- Test type is unit/artifact: manifest coverage/timing/completeness are deterministic. No runtime,
  `load.py`, plugin-hook, EDMC lifecycle, or Tk wiring changes, so no harness test is selected.
- RED captured 41 expected failures from the old full-coverage validator and committed manifest
  (`logs/red-reduced-performance-matrix.log`). The active oracle now has manifest ID
  `fix219_gnome46_pre_migration_reduced_v2`, exact scale-specific signatures, reduced timing, and
  three repetitions. The manifest suite passes 84 tests after adding explicit compatibility for
  the preserved full-v1 profile (`logs/green-reduced-performance-matrix-with-superseded-compatibility.log`).
- A separate expected RED proved the superseded v1 profile was initially unreadable under the
  new validator (`logs/red-superseded-full-matrix-compatibility.log`); manifest-ID-owned coverage
  profiles now keep both v1 and v2 machine-valid. CLI checks report active v2 at 14 scenarios/3
  repetitions, superseded v1 at 36/5, and both preserved v1 captures valid.
- The final Step 03 focused gate passes 131 tests
  (`logs/step03-focused-reduced-performance-matrix-final.log`). `make check` passes repository
  Ruff, configured mypy for 92 source files, and GUI-enabled pytest with 1,341 passed/21 existing
  skips (`logs/make-check-reduced-performance-matrix.log`); `make test` passes with the same
  1,341/21 result (`logs/make-test-reduced-performance-matrix.log`). Focused format and
  `git diff --check` pass. The reduced matrix is ready at 0/42.
- Reduced-v2 stable-windowed monitor-A repetition 1 independently validates with exact 10/15/30
  timing, 62 latency samples, 15 client and 15 Shell CPU samples, 49 paints, 841 repaints, zero
  manual failures, and an empty prohibited-field scan. Stage 3.9 is now 1/42.
- Reduced-v2 stable-windowed monitor-A repetition 2 independently validates with 62 latency
  samples, 50 paints, 841 repaints, zero manual failures, and an empty prohibited-field scan.
  Stage 3.9 is now 2/42.
- Reduced-v2 stable-windowed monitor-A repetition 3 independently validates with 62 latency
  samples, 46 paints, 841 repaints, zero manual failures, and an empty prohibited-field scan.
  All three captures for the first scenario validate together; Stage 3.9 is now 3/42.
- Reduced-v2 stable-borderless-fullscreen monitor-A repetition 1 independently validates with
  91 latency samples, one Shell-raster build, zero Qt paints as expected for the Shell presenter,
  zero manual failures, and an empty prohibited-field scan. Stage 3.9 is now 4/42.
- Reduced-v2 stable-borderless-fullscreen monitor-A repetition 2 independently validates with
  91 latency samples, one Shell-raster build, zero Qt paints, 830 repaints, zero manual failures,
  and an empty prohibited-field scan. Stage 3.9 is now 5/42.
- Reduced-v2 stable-borderless-fullscreen monitor-A repetition 3 independently validates with
  95 latency samples, one Shell-raster build, zero Qt paints, 816 repaints, zero manual failures,
  and an empty prohibited-field scan. All three fullscreen captures validate together; Stage 3.9
  is now 6/42.
- The first windowed-to-fullscreen attempt was cancelled before artifact write because the user
  did not see the transition cue; it is not counted. The retry used an explicit `go` handshake
  followed by a visible `NOW` cue after the observation timer started.
- Reduced-v2 windowed-to-fullscreen monitor-A repetition 1 independently validates with 78
  latency samples, two raster builds, 29 Qt paints before Shell ownership, 841 repaints, zero
  manual failures, and an empty prohibited-field scan. `end_to_stable_ms=0.0` is retained: this
  direction commits directly to `stable_shell_raster` without a timed pending phase, while the
  presentation-cycle samples, extra raster build, and explicit manual action establish the
  transition. Stage 3.9 is now 7/42.
- Reduced-v2 windowed-to-fullscreen monitor-A repetition 2 independently validates with 82
  latency samples, one raster build, 26 pre-handoff Qt paints, 841 repaints, zero manual failures,
  and an empty prohibited-field scan. Direct Shell commitment again reports
  `end_to_stable_ms=0.0`. Stage 3.9 is now 8/42.
- Reduced-v2 windowed-to-fullscreen monitor-A repetition 3 independently validates with 82
  latency samples, two raster builds, 30 pre-handoff Qt paints, zero manual failures, and an
  empty prohibited-field scan. Direct Shell commitment again reports `end_to_stable_ms=0.0`.
  All three captures for this transition validate together; Stage 3.9 is now 9/42.
- Reduced-v2 fullscreen-to-windowed monitor-A repetition 1 independently validates with 77
  latency samples, `end_to_stable_ms=2000.568`, 23 managed-surface paints after handoff, 841
  repaints, zero manual failures, and an empty prohibited-field scan. Stage 3.9 is now 10/42.
- Reduced-v2 fullscreen-to-windowed monitor-A repetition 2 independently validates with 77
  latency samples, `end_to_stable_ms=2000.189`, 38 managed-surface paints after handoff, zero
  manual failures, and an empty prohibited-field scan. Stage 3.9 is now 11/42.
- Reduced-v2 fullscreen-to-windowed monitor-A repetition 3 independently validates with 71
  latency samples, `end_to_stable_ms=1500.480`, 39 managed-surface paints after handoff, zero
  manual failures, and an empty prohibited-field scan. All three reverse-transition captures
  validate together; Stage 3.9 is now 12/42.

## Pressure-reduction planning synchronization — 2026-07-21

- The 12 accepted reduced-v2 captures remain valid and immutable under manifest
  `fix219_gnome46_pre_migration_reduced_v2`; they are now classified as historical
  pre-optimization/incident-era evidence. The two full-v1 captures remain preserved under their
  original superseded manifest. No capture is deleted, overwritten, moved, or relabeled by this
  planning synchronization.
- The matrix is paused at 12/42. Do not continue with monitor B, enable capture diagnostics, or
  create summaries/thresholds from a mixed pre/post-optimization population.
- During the desktop incident, the helper emitted 3,601 target-query-start events in 30 minutes,
  exactly two per second, while reduced captures also showed approximately 816–841 repaint
  requests per 30 seconds. The overlay/helper is not established as the Firefox/Mutter failure's
  cause; it is treated only as a plausible load amplifier whose unnecessary stable work should
  be reduced and measured safely.
- The approved PDD amendment is recorded in Question 35, the focused GNOME pressure/repaint
  research, the detailed design, and authoritative Step 3 Stages 1.6–1.11. This working plan maps
  that continuation to Stages 3.10–3.16 while preserving Stages 3.1–3.9 as execution history.
- **Pressure-reduction acceptance bounds** come from the quiet A1/A2/B1/B2 experiment and remain
  in its reviewed report. They decide whether the work may proceed to manual regression and a
  clean baseline; they do not populate `thresholds.json`.
- **Migration-regression thresholds** come only from a new complete 42-capture coherent baseline
  and become the versioned comparison gate for later fix219 steps. There is intentionally no
  `thresholds.json` yet.
- Test selection for Stages 3.11–3.12 is unit tests for dependency-injected monotonic cache logic,
  runtime seams, and pure visual fingerprints. No harness test is selected while `load.py`, EDMC
  hooks, lifecycle, and Tk wiring remain untouched; touching any of them makes a harness test
  mandatory. Real GNOME A/B, behavior, soak, and matrix evidence remain mandatory.
- Documentation-only synchronization changed no runtime code, settings, user-local helper file,
  or evidence capture. Stage 3.10 is the next action but remains not started pending user review.

## Synchronization review approval — 2026-07-21

- The user approved the separation between A/B pressure-reduction acceptance bounds and clean-
  baseline migration-regression thresholds.
- The user approved the Stage 3.9–3.16 sequence, with a tiered-testing caveat: focused RED/GREEN
  tests remain mandatory, full project gates run at meaningful milestones, exploratory A/B may
  be shorter but cannot count as acceptance, and deferred manual/matrix evidence leaves the
  affected stage incomplete.
- The user approved preserving chronological progress with the explicit current-state
  supersession rule above.
- The user approved the 12-capture historical hold, frozen diagnostics-enabled procedure, and
  new-identity 0/42 policy.
- The synchronization review is complete. This approval covers planning documents only; it does
  not authorize Stage 3.10/authoritative Stage 1.6, which remains not started pending a separate
  user instruction.

## Quiet diagnostic state — 2026-07-21

- The user separately authorized Task 04, beginning authoritative Stage 1.6 / working Stage 3.10.
- Restored the client shadow to `dev_mode=false` and repaint-debounce diagnostics to
  `log_repaint_debounce=false`. Tracing, visual outlines, payload logging, and the debug overlay
  remain disabled; repaint debounce itself remains enabled. No persisted EDMC `dev_mode`
  override was present to overwrite the quiet shadow on the next launch.
- Read the user-local helper developer configuration, created the non-overwriting backup
  `gnome_helper_dev_mode.json.pre-stage-3.10-20260721.bak`, and changed only `diagnostics` from
  true to false. `enabled=true` and `mode=full_helper` were preserved.
- Reloaded the GNOME helper through its supported disable/enable lifecycle. `GetHealth` then
  reported healthy helper version 1.0.0/protocol 3, full-helper capabilities, and
  `diagnostics_enabled=false`.
- No EDMC or overlay-client process was active, so no running process required restart. The next
  launch will consume the quiet shadow settings. To prove the helper gate directly, a bounded
  10-second host-session probe issued 20 real `GetTargetState` calls with zero call failures.
  The filtered user journal contained zero `target_query_started`, `Repaint request`, or repaint
  detail events for the interval. No target response, title, handle, or other private field was
  recorded.
- Revalidated the pre-mutation SHA-256 inventory: all 12 reduced-v2 captures and both superseded
  full-v1 captures passed. No capture, manifest identity, summary, or `thresholds.json` was
  created or changed.
- Test selection remained operational: no runtime code, `load.py`, hook, lifecycle, or Tk wiring
  changed, so no unit or harness tests were added or run. JSON validation, configuration-field
  preservation, live helper health, bounded journal counts, evidence hashes, and
  `git diff --check` passed.
- Stage 3.10 is complete. Stage 3.11 is next but has not started.

## Stable-target query pressure reduction — 2026-07-21

- The user separately authorized Task 05, beginning authoritative Stage 1.7 / working Stage 3.11.
- Selected unit tests because the cache, helper calls, target payloads, and monotonic clock are
  injected behind the GNOME backend. No `load.py`, EDMC hook, lifecycle, or Tk wiring changed, so
  no harness test was required.
- Added all Task 05 tests before runtime edits. Focused RED produced 9 expected failures and 102
  passes: transition-guard stable cycles queried every follow tick, mapped-suppressed target
  caching delayed a required Shell-raster lease refresh, and six target facts were absent from
  the presentation signature.
- The implementation retains the existing 1.5-second backend deadline and removes only the
  transition guard's unconditional cache veto. Pending handoffs/commits, explicit refresh,
  helper/presentation failure, target loss/recovery, surface preparation, confirmed exposure
  recovery, stale raster leases, and caller-visible exposure changes remain bypass/invalidation
  paths.
- The private presentation signature now includes frame and buffer rectangles, monitor index,
  output name, monitor scale, and workspace in addition to the already-covered target token,
  requested/monitor geometry, focus, showing/minimized/fullscreen, renderer, preparation, and
  raster-frame state. Generic consumers gained no compositor-private imports or enum checks.
- Exact focused command passed with 111 tests. The generic backend-consumer boundary passed with
  35 tests. Targeted ruff, compileall, and `git diff --check` passed. Full `make check` and
  `make test` remain deferred to the approved integrated query-plus-repaint milestone.
- No commit or push was created; Stage 3.16 remains the approved commit point. The historical
  12/42 capture hold and absence of `thresholds.json` remain unchanged.
- Stage 3.11 is complete. Stage 3.12 / Task 06 is next but has not started.

## Proven unchanged-repaint suppression — 2026-07-21

- The user separately authorized Task 06, beginning authoritative Stage 1.8 / working Stage
  3.12, and required the approved detailed design to remain authoritative.
- Selected unit tests for pure fingerprints/counters and injectable Qt/runtime seams. No
  `load.py`, EDMC hook/lifecycle, or Tk wiring changed, so no harness test was required.
- Attribution kept request, Qt paint, frame preparation, raster encode/reuse, and helper
  presentation separate. Historical examples showed 841 requests versus 49 managed paints and,
  separately, 60 Shell-frame preparations versus one raster build/59 reuses.
- Added every behavior test before runtime edits. RED produced 11 expected failures and 59
  passes for lifecycle metadata, plugin/group identity, animation, unknown fallback, bounded
  scheduling, generic presentation refresh, and unchanged frame preparation.
- Extended the existing supported visual fingerprint. Matching TTL/metadata updates refresh
  lifecycle state without repaint; plugin/group/override changes, animation, and unknown or
  malformed state repaint safely. Fixed-key saturating counters attribute ingest, scheduling,
  Qt update/paint, and Shell-frame work without per-cycle logs.
- Successful Shell-frame preparation now reuses a result only when deterministic render state,
  target/request geometry, monitor/output, scale, workspace, focus/visibility/mode, and
  diagnostics state match. Failures/incomplete state are never cached; lease refresh,
  presentation ownership, Phase 19, recovery, and explicit refresh remain intact.
- Focused GREEN passed 70 tests. The integrated query/repaint/follow slice passed 151; the
  backend-consumer boundary passed 35; targeted Ruff and compileall passed. Initial unactivated
  `make` attempts failed because system Python lacked Ruff/PyQt, then the prepared environment
  exposed one stale nested-venv command in the authoritative plan. After synchronizing that
  documentation contract, `make check` and `make test` each passed with 1,379 tests and 21
  existing skips; `make check` also passed repository Ruff and mypy.
- No Task 07 A/B, manual compositor gate, capture, evidence identity, summary, threshold,
  settings change, production routing, commit, or push was performed. Stage 3.13 is next but
  remains not started; Stage 3.16 remains the approved commit point.
