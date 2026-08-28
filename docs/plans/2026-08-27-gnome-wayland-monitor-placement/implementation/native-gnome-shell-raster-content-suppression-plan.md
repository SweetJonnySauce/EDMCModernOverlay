# Native GNOME Shell-Raster Content Suppression: Implementation Plan

**Status:** Proposed — do not implement until design approval. This replaces
the invalid direct-authorization plan and preserves the user-verified
fullscreen actor-continuity rollback.

## Checklist

- [x] Step 1: Add a neutral content-visibility intent and capability contract without changing live behavior.
- [x] Step 2: Implement helper-side reversible content suppression while preserving actor continuity.
- [x] Step 3: Wire the debounced preference intent through the native GNOME backend bundle.
- [x] Step 4: Complete automated gates and live GNOME Wayland focus-transition acceptance.

## Phase Status

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Define and prove the neutral intent/capability boundary | Completed |
| 2 | Add helper-owned content suppression with actor-continuity invariants | Completed |
| 3 | Integrate native GNOME policy and validate live behavior | Completed — user verified the focus-transition and two-monitor matrix after the retained-actor remap-warm-up correction. |

### Phase 1 stages

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Locate the existing neutral visibility policy seam and add `visible`/`suppressed` intent | Completed |
| 1.2 | Add request/result capability serialization and unsupported-helper fallback tests | Completed |

### Phase 2 stages

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Apply reversible content suppression to single-frame Shell-raster actors | Completed |
| 2.2 | Apply the same invariant-preserving behavior to region-raster actors | Completed |
| 2.3 | Add helper source/runtime assertions that ordinary focus loss cannot clear or hide the actor | Completed |

### Phase 3 stages

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Feed the existing debounced preference decision into the native GNOME bundle | Completed — neutral transport and GNOME-owned capability wiring passed main-context review. |
| 3.2 | Run automated transition, backend-boundary, and project checks | Completed — focused suite passed; external `make check` and `make test` each passed Ruff, mypy, and 1,691 tests. |
| 3.3 | Run the repeated live GNOME focus and two-monitor acceptance matrix | Completed after remediation — user verified all acceptance cases: debounce/suppression, focus return without flash or black screen, repeated cycles, and two-monitor placement. |
| 3.4 | Reconcile the managed-surface hypothesis against live client evidence | Completed — exact log shows `surface_preparation=none` and `presentation_not_attachable`; prior broad policy change was reverted. |
| 3.5 | Declare retained Shell-raster content availability through the native GNOME bundle and consume it as a neutral policy fact | Completed — supported, applied, matching Shell-raster results can remain attached for content suppression without mapping generic Qt; managed-PyQt behavior and actor continuity are unchanged. Focused suite: 274 passed; project gates: 1,696 passed. |
| 3.6 | Prevent retained Shell-raster actor visibility from entering generic Qt remap warm-up | Completed — the generic policy consumes only the neutral retained-content availability fact and treats the actor as visible when the generic Qt surface is intentionally unmapped; focused regression coverage passes. |

## Step 1: Establish a neutral intent and helper capability boundary

**Objective:** Create an explicit, backend-neutral way to request raster
content visibility while preserving the existing `allow_unfocused_target`
continuity behavior and all current live behavior by default.

**Implementation guidance:**

- Locate the existing presentation/focus policy seam and represent only
  `visible` or `suppressed` content intent there; do not import GNOME helper
  code or dispatch on raw backend/helper enums from generic runtime code.
- Extend the native GNOME bundle’s request/result types with optional
  `content_visibility` and an explicit helper capability/version signal.
- Default an unavailable, older, malformed, or unsupported helper to the
  current stable visible behavior. Never translate that fallback into
  `allow_unfocused_target=false` for the eligible fullscreen route.
- Retain the restored full-monitor fullscreen continuity guard untouched.

**Test requirements:**

- Unit-test neutral intent resolution and request serialization.
- Test supported, unsupported, malformed, and absent capability responses.
- Add architecture/boundary coverage showing generic follow/runtime remains
  independent of GNOME compositor-specific protocol types.

**Integration:** No helper actor behavior changes in this step. A helper that
does not advertise the capability receives or behaves as `visible`.

**Demo:** A test proves a suppressed intent is representable, while an
unsupported helper still receives the prior stable continuity behavior.

## Step 2: Add helper-owned, reversible raster content suppression

**Objective:** Make the GNOME helper suppress and restore raster content on an
existing actor without treating ordinary focus loss as a target-loss event.

**Implementation guidance:**

- Add one helper-owned content-visibility operation, capability-gated from the
  request contract. Apply it to both single-frame and region-raster actor
  paths.
- Preserve actor identity, parentage, monitor placement, stacking,
  non-reactivity/click-through, session token, and timeout state for
  `visible -> suppressed -> visible`.
- Do not call `_clearShellRasterFrame`, `_suspendShellRasterFrame`, actor
  `hide`, destroy/detach, or the `target_not_focused` path for an ordinary
  focus transition. Retain existing clear behavior only for hard lifecycle
  loss.
- If the chosen reversible rendering mechanism fails a live smoke test, stop
  before wiring it to the user preference and retain stable visible content.

**Test requirements:**

- Extension source/contract tests assert the suppression path cannot invoke
  focus-risk actor lifecycle operations.
- Runtime/mock-helper tests cover both raster actor forms and preserve actor
  identity, placement, input state, and fullscreen continuity.
- Test helper rejection/failure restores or retains visible content and reports
  degraded status without a presenter swap.

**Integration:** The helper reports whether visibility was applied, suppressed,
unsupported, or degraded. No managed-PyQt fallback is introduced for a valid
native fullscreen route.

**Demo:** A test cycle suppresses then restores content while the exact same
Shell actor remains attached and non-reactive.

## Step 3: Wire preference intent through the native GNOME bundle

**Objective:** Honor the existing debounced foreground-visibility decision for
the supported native GNOME route without changing other backend behavior.

**Implementation guidance:**

- Feed the existing neutral policy output into the native GNOME bundle only;
  do not duplicate focus debounce or reclassify target focus in the helper.
- For an eligible fullscreen target, keep actor-continuity authorization true
  across ordinary focus loss. Map unchecked preference to `suppressed` and
  checked preference to `visible` only when the helper capability is present.
- On focus return, request `visible` against the retained actor. On unsupported
  capability, keep content visible and surface a gated diagnostic rather than
  risking a clear.
- Keep X11, xcompat, windowed managed-PyQt, overview, target-loss, placement,
  and click-through behavior unchanged.

**Test requirements:**

- Cover focused, unchecked-unfocused, checked-unfocused, focus-return,
  unsupported-helper, hard-target-loss, and presenter-transition cases.
- Keep follow-surface and backend-boundary tests proving no generic
  compositor-specific dispatch.

**Integration:** This is the only step that changes live preference behavior.
The helper’s advertised capability is a hard gate.

**Demo:** In a supported helper test, `visible -> suppressed -> visible` occurs
for the same actor as focus moves away and returns; the unchecked route never
emits `target_not_focused` merely due to normal focus loss.

## Step 4: Validate and accept the behavior

**Objective:** Prove the new path is safe in both automated checks and the
affected live GNOME session before release.

**Automated validation:**

```bash
source overlay_client/.venv/bin/activate
PYQT_TESTS=1 python -m pytest \
  overlay_client/tests/test_gnome_helper_presentation_runtime.py \
  overlay_client/tests/test_gnome_shell_helper_extension_source.py \
  overlay_client/tests/test_gnome_shell_helper_presentation_state.py \
  overlay_client/tests/test_backend_presentation_policy.py \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_presentation_transition.py \
  overlay_client/tests/test_backend_architecture_boundary.py -q
make PYTHON="$VIRTUAL_ENV/bin/python" check
make PYTHON="$VIRTUAL_ENV/bin/python" test
```

Record exact results and any skips. Do not reload the extension or issue live
DBus commands until the user authorizes live acceptance.

**Live acceptance matrix:**

| Preference | Focus state | Required result |
| --- | --- | --- |
| Unchecked | Elite focused | Content is visible on Elite’s monitor. |
| Unchecked | Focus leaves Elite | After the existing debounce, content disappears while the actor stays attached; no black screen or flash. |
| Unchecked | Focus returns | Content restores on the same actor without remap, duplicate overlay, or black screen. |
| Checked | Focus leaves Elite | Content remains visible continuously. |
| Either | Repeated focus cycles | No black screen, actor recreation, focus theft, or placement drift. |
| Either | Two-monitor fullscreen placement | Actor remains on Elite’s monitor and remains non-reactive. |

## Completion criteria

- The prior direct-authorization plan remains invalid and its safety rollback
  remains intact.
- A supported helper suppresses only raster content for an unchecked,
  unfocused eligible fullscreen target while retaining actor continuity.
- Unsupported/failing helpers remain visibly stable and report a gated,
  diagnosable fallback.
- Both raster actor forms, hard lifecycle behavior, backend boundaries, and
  non-GNOME behavior are covered by tests.
- Focused tests, `make check`, `make test`, and the live acceptance matrix have
  recorded passing results.
