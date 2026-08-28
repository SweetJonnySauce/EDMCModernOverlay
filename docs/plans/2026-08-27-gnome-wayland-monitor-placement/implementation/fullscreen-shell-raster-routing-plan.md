# GNOME Wayland Fullscreen Shell-Raster Routing: Implementation Plan

**Status:** Completed with sandbox-limited project gate. This supersedes the monitor-transfer approach
for the observed GNOME/Mutter fullscreen failure. It leaves its diagnostics and
commits intact as evidence; it does not overwrite the in-progress delivery
artifacts for that approach.

## Checklist

- [x] Step 1: Lift native-GNOME presentation configuration behind a bundle-owned seam (native helper-unavailable legacy-follow fallback restored and regression-tested).
- [x] Step 2: Enable real-content Shell raster for eligible native-GNOME fullscreen targets.
- [x] Step 3: Wire safe presenter transitions and fullscreen failure suppression.
- [ ] Step 4: Validate the native GNOME route and record live evidence (all assertions are green; project gate remains blocked by five sandbox loopback socket setups).

## Phase Status

| Phase | Description | Status |
| --- | --- | --- |
| 0 | Evidence and replacement design | Completed |
| 1 | Backend-boundary seam | Completed |
| 2 | Fullscreen raster routing | Completed |
| 3 | Transition/failure wiring | Completed |
| 4 | Automated and live acceptance | Reopened — manual matrix and all assertions pass, but the project gate has five sandbox-blocked loopback socket setups |

### Phase 0: Evidence and replacement design

| Stage | Description | Status |
| --- | --- | --- |
| 0.1 | Confirm target/overlay monitor mismatch through helper readback | Completed |
| 0.2 | Probe both PyQt monitor-transfer orderings | Completed: both calls are silent no-ops in the observed Mutter session |
| 0.3 | Inventory existing real-content raster, Shell actor, and transition paths | Completed |

### Phase 1: Backend-boundary seam

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add a bundle-owned GNOME presentation runtime/profile seam | Completed: remediation restored the normal native profile to capable-but-inactive; legacy raster remains active |
| 1.2 | Move raw GNOME/raster selection decisions out of generic consumer dispatch | Completed |
| 1.3 | Prove X11/xcompat remain outside the GNOME runtime path | Completed — fallback regression restored; focused architecture coverage passed |

### Phase 2: Fullscreen raster routing

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Select real-content raster for eligible `gnome_shell_wayland` fullscreen targets | Completed — normal bundle profile now selects the existing neutral real-content provider route |
| 2.2 | Preserve managed PyQt for windowed targets | Completed — existing helper-cycle windowed/partial/ambiguous unit contracts passed unchanged |
| 2.3 | Fail closed when fullscreen raster cannot be built or proven | Completed — native profile now forwards existing fallback suppression; failure contracts passed unchanged |

### Phase 3: Transition and lifecycle safety

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Clear Shell actor before committing managed PyQt | Completed — deterministic helper-cycle recording proves acknowledged clear before preparation and managed attach |
| 3.2 | Clear/reset on target loss, helper loss, and target replacement | Completed — guarded HIDE_ALL exits with cached raster ownership clear/reset safely; unavailable helper remains local fail-closed |
| 3.3 | Confirm no duplicate visible surface or focus/input regression | Completed — focused transition, extension-contract, and architecture suites passed; live acceptance remains Step 4 |

### Phase 4: Acceptance

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Run focused automated tests and architecture gate | Completed — native fallback-focused suite passed 157 tests, including architecture coverage |
| 4.2 | Run project checks and record limitations | Completed with sandbox limitation — `make PYTHON=overlay_client/.venv/bin/python check` passes Ruff/mypy and all assertions (1,649 passed, 21 skipped); five pressure-snapshot setups cannot bind loopback |
| 4.3 | Perform live GNOME two-monitor acceptance matrix | Completed — user confirmed the Wayland matrix passes and explicitly approved skipping diagnostic capture |

## Step 1: Lift native-GNOME presentation configuration behind a bundle-owned seam

**Objective:** Make the selected backend bundle—not generic follow/runtime
code—the owner of whether GNOME helper presentation can use fullscreen Shell
raster.

**Implementation guidance:**

- First add a narrow runtime profile/adapter to the GNOME bundle. Preserve the
  existing runner behavior while moving `GNOME_SHELL_RASTER` enum predicates
  out of `consumers.py` and away from the generic caller.
- The normal `gnome_shell_wayland` bundle must declare support for the new
  fullscreen-raster mode; X11 and xcompat must declare nothing and gain no
  imports.
- Keep the existing raster identity usable only as compatibility/development
  scaffolding. Do not remove its selector, override, or user-facing status in
  this increment.

**Test requirements:**

- Add/update unit tests around bundle resolution/runtime-profile selection.
- Update the architecture-boundary test to reject generic raw GNOME/raster
  presentation dispatch and direct compositor imports.
- Run:

  ```bash
  PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
    overlay_client/tests/test_backend_consumers.py \
    overlay_client/tests/test_backend_architecture_boundary.py -q
  ```

**Integration:** This is behavior-preserving plumbing: the old raster identity
continues to produce the same runtime flags while native GNOME now has a
backend-owned capability to opt in during Step 2.

**Demo:** A test can resolve native X11, xcompat, and native GNOME bundles and
show that only the native GNOME bundle exposes fullscreen-raster capability.

## Step 2: Enable real-content Shell raster for eligible native-GNOME fullscreen targets

**Objective:** Route a fullscreen, full-monitor `gnome_shell_wayland` target
through the existing real-content frame provider and Shell actor.

**Implementation guidance:**

- Make the GNOME runtime profile enable the existing raster bridge and
  fullscreen PyQt-fallback suppression for the native GNOME bundle.
- Reuse `_build_backend_shell_raster_content_frame` and the existing cropped
  real-content request builder. Do not enable static proof frames in production.
- Retain the current strict eligibility checks. Windowed, partial-screen, or
  ambiguous targets must remain managed PyQt.
- Record a concise diagnostic presenter mode/reason using the existing
  presentation diagnostics surface; do not change the DBus protocol.

**Test requirements:**

- Add a native-GNOME selected-backend case that submits a real-content
  `gnome_shell_raster_frame` request for an eligible fullscreen target.
- Add windowed and ineligible fullscreen cases proving no raster frame is sent.
- Cover provider failure and no-visible-content cases, asserting clear/degraded
  behavior instead of PyQt fullscreen fallback.
- Run:

  ```bash
  PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
    overlay_client/tests/test_gnome_helper_presentation_runtime.py \
    overlay_client/tests/test_shell_raster_frame.py \
    overlay_client/tests/test_repaint_debounce.py -q
  ```

**Integration:** The new route consumes the neutral frame-provider callback
already supplied by the render surface. It changes only the internal native
GNOME presenter selection.

**Demo:** A controlled fullscreen target yields an actual-content raster frame
request; the same target after becoming windowed yields the ordinary PyQt
attach request.

## Step 3: Wire safe presenter transitions and fullscreen failure suppression

**Objective:** Ensure exactly one presenter owns the overlay and all exits from
fullscreen leave no stale actor or misplaced PyQt window.

**Implementation guidance:**

- Exercise and, only if necessary, complete the existing transition state
  machine: fullscreen raster → windowed managed PyQt must clear the actor
  first; target/helper loss and token replacement must clear/reset both sides.
- Keep fullscreen raster failures fail-closed. Do not introduce sleeps,
  coordinate guesses, or monitor-transfer retries as a fallback.
- Verify the extension actor remains non-reactive, above the target, and
  detached/cleared on clear requests. Preserve click-through and focus safety.

**Test requirements:**

- Add/extend tests for fullscreen → windowed, target loss, token replacement,
  actor-clear failure, and repeated monitor handoff while fullscreen.
- Retain source-contract coverage for non-reactive actor parenting/clearing.
- Run:

  ```bash
  PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
    overlay_client/tests/test_gnome_helper_presentation_runtime.py \
    overlay_client/tests/test_presentation_transition.py \
    overlay_client/tests/test_gnome_shell_helper_extension_source.py \
    overlay_client/tests/test_backend_architecture_boundary.py -q
  ```

**Integration:** Step 2's selected raster path becomes safe across all
presenter ownership changes. No `load.py` or EDMC lifecycle hook is touched;
if that scope changes, add a harness test before proceeding.

**Demo:** A simulated fullscreen-to-windowed transition records an actor clear
before the managed attach, while a failed fullscreen raster build leaves both
the actor and PyQt fullscreen presentation absent.

## Step 4: Validate the native GNOME route and record live evidence

**Objective:** Prove the actual GNOME session renders on Elite's monitor and
does not regress input, stacking, or renderer transitions.

**Implementation guidance:**

- Deploy/reload the helper only after Steps 1–3 are green. Enable existing
  presentation diagnostics only for the validation session.
- Capture target monitor/rect, renderer, actor/request status, applied rect,
  transition decision, and degrade reasons for each case.
- Do not treat a normal API return as success; require matching diagnostics and
  visual results.

**Test requirements:**

```bash
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
  overlay_client/tests/test_backend_consumers.py \
  overlay_client/tests/test_backend_architecture_boundary.py \
  overlay_client/tests/test_gnome_helper_presentation_runtime.py \
  overlay_client/tests/test_shell_raster_frame.py \
  overlay_client/tests/test_presentation_transition.py \
  overlay_client/tests/test_gnome_shell_helper_extension_source.py -q
make check
make test
```

If a project check cannot run, record the exact environmental reason and its
remaining risk; do not claim it passed.

Manual GNOME matrix:

| Case | Required result |
| --- | --- |
| Elite primary, overlay initially secondary | Shell raster is selected and visible only on Elite's monitor |
| Elite secondary, overlay initially primary | Same result in reverse direction |
| Elite moves monitors while fullscreen | Actor follows the target; no stale actor remains on prior monitor |
| Fullscreen → windowed → fullscreen | Clear/managed/raster transitions occur without duplicate surface or focus theft |
| Target minimized, closes, or helper reloads | Actor clears and client fails closed |
| Click-through, stacking, content update | Actor is non-reactive, above Elite, and renders real updated content |

**Integration:** This validates the complete native GNOME path only. X11 and
xcompat receive their normal focused regression test coverage but no live
behavioral change.

**Demo:** On the affected session, the helper reports a Shell-raster renderer
and the overlay remains on the same monitor as fullscreen Elite in both
directions.

## Completion Criteria

- All focused test commands pass and `make check`/`make test` results are
  recorded.
- Architecture tests prove generic runtime code has not gained compositor enum
  dispatch or direct GNOME imports.
- Fullscreen native GNOME uses real-content raster; windowed native GNOME uses
  managed PyQt.
- Raster failure, target loss, and transition cases clear/suppress safely.
- The live two-monitor matrix passes with renderer and geometry diagnostics.
- X11/xcompat scopes remain unchanged in code review.
