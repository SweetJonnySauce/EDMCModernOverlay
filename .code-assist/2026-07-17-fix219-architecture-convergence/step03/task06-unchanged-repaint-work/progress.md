# Task 06 Progress: Proven Unchanged Repaint Work

## Checklist

- [x] Stage 1.1: verify authorization, artifacts, repository state, and dirty-tree constraints.
- [x] Stage 1.2: audit payload, repaint, Qt paint, frame, raster, and presentation paths.
- [x] Stage 1.3: record evidence-led attribution and select unit tests.
- [x] Stage 1.4: create context, explicit test plan, phase/stage tracking, and validation plan.
- [x] Stage 2.1: add payload fingerprint/lifecycle/trigger/fallback tests.
- [x] Stage 2.2: add bounded scheduling and generic refresh tests.
- [x] Stage 2.3: add frame reuse/invalidation/failure/performance tests.
- [x] Stage 2.4: capture expected focused RED.
- [x] Stage 3.1: implement pure fingerprint/lifecycle changes.
- [x] Stage 3.2: implement bounded request/scheduling/paint attribution.
- [x] Stage 3.3: implement render identity and successful frame-result reuse.
- [x] Stage 3.4: implement allowlisted frame-skip interpretation.
- [x] Stage 4.1: pass focused GREEN and refactor review.
- [x] Stage 4.2: pass integrated/static/boundary checks.
- [x] Stage 4.3: pass `make check` and `make test` milestone gates.
- [x] Stage 4.4: synchronize Task 06 and PDD progress artifacts.
- [x] Stage 4.5: review final scope and preserve the Stage 3.16 commit gate.

## Setup and exploration notes

- Mode: `auto`; repository root is the current workspace; documentation root is the existing
  Step 03 Code Assist directory; task record is `task06-unchanged-repaint-work`.
- No `CODEASSIST.md` exists. The mandatory discovery command found the root README plus archive,
  harness, config, and pytest-cache READMEs; task-relevant PDD and project instructions were read
  directly.
- Starting branch/HEAD: `backend-refactor-implementation` at `3d23328`. The existing dirty Step
  03 tree is preserved.
- Baseline focused command: 41 passed in 0.46s (`logs/baseline-focused.log`).
- Unit tests are selected. No harness test is required unless the implementation crosses into
  `load.py`, EDMC hooks, lifecycle, or Tk wiring.

## Attribution decision

- Historical request counts are not treated as material-work counts. Managed and Shell-raster
  examples separate 841 requests from 49/0 paints, 0/60 frame preparations, 0/1 raster builds,
  0/59 raster reuses, and 0/30 helper presentation calls.
- The existing supported-payload snapshot is retained as the dedupe seam. It will be made
  explicitly safe for animation, grouping/plugin changes, and unknown payloads.
- The smallest downstream repeated-work seam is successful Shell-frame preparation keyed by
  complete target/request context and the render pipeline's deterministic identity. Encoding
  cache and backend lease/presentation ownership remain unchanged.
- Detailed per-cycle logs remain out of scope. Fixed saturating aggregate counters provide the
  requested attribution without unbounded keys or journal spam.

## TDD cycles

### Cycle 1: RED

- Added every Task 06 behavior test before changing implementation files.
- Exact focused command produced 11 expected failures and 59 passes; log:
  `logs/red-focused.log`.
- Failures cover lifecycle metadata refresh/attribution, group and plugin identity, animation
  bypass, unknown-shape safe fallback, generic presentation-refresh signaling, bounded repaint
  scheduling counters, and successful unchanged Shell-frame preparation reuse/counters.
- Existing visual-trigger, override-generation, invalidation-family, performance allowlist, and
  prior behavior tests remained green. No unexpected framework or environment failure occurred.

## Commit status

No commit or push. The approved Step 03 plan reserves the reviewed increment commit for Stage
3.16, which overrides Code Assist's generic commit default for this task.

### Cycle 2: GREEN and refactor

- Focused attempt 1 reduced RED to six failures caused by one missing local counter-map binding;
  the design and tests did not change. Focused attempt 2 and the final refactor run passed 70
  tests (`logs/green-focused-final.log`).
- The implementation reuses the existing fingerprint/dedupe seam, adds safe plugin/group and
  animation/unknown handling, fixed saturating counters, a render revision/identity, and narrow
  successful Shell-frame result reuse. Renderer-wide opacity/nudge/font/line-width state is
  included; unsupported replacements clear stale snapshots; release-mode reuse adds no detailed
  diagnostic payload.
- Integrated query/repaint/follow: 151 passed. Backend consumers: 35 passed. Targeted Ruff and
  compileall passed. `git diff --check` and the three-test developer-environment contract passed.
  A scoped Ruff format check passed for the new module and already-formatted Task 06
  test/performance surfaces. A broad check reported eight shared dirty files would be reformatted;
  that non-gating bulk rewrite was deliberately skipped to preserve earlier Step 03 changes.
- Unactivated `make` failed because `/usr/bin/python3` lacks Ruff/PyQt. Prepared-environment
  attempts ran 1,378 passes/21 skips and exposed one stale nested-environment command in the
  authoritative plan. After fixing that documentation contract, final `make check` and `make
  test` each passed 1,379 tests with 21 existing environment/runtime skips; `make check` also
  passed repository Ruff and mypy.
- No harness test was added because plugin/Tk lifecycle was untouched. No live GNOME A/B or
  manual evidence was run because those begin in Tasks 07–08.
