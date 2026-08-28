# Implementation Plan: Native GNOME Helper-Unavailable Legacy-Follow Fallback

**Status:** Completed with sandbox-limited project gate

**Design:** [Native GNOME Helper-Unavailable Legacy-Follow Fallback](../design/native-gnome-helper-unavailable-fallback-remediation.md)

## Checklist

- [x] Step 1: Establish regression coverage and the neutral policy contract.
- [x] Step 2: Implement native fall-through and legacy-raster fail-closed profiles.
- [x] Step 3: Validate, reconcile progress documents, and commit only if requested.

## Phase status

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Contract and regression tests | Completed |
| 2 | Bundle-profile implementation | Completed |
| 3 | Validation and progress reconciliation | Completed with sandbox limitation |

### Phase 1: Contract and regression tests

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Confirm the existing native helper-loss integration test is red | Completed — observed during `make check`: legacy refresh count was 0, expected 1 |
| 1.2 | Add/adjust direct runtime tests for both unavailable-helper contracts | Completed — RED 3 expected failures; focused direct/consumer coverage is green |
| 1.3 | Preserve architecture-boundary coverage | Completed — focused architecture suite passed |

### Phase 2: Bundle-profile implementation

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add a neutral `helper_unavailable_is_terminal` profile field | Completed |
| 2.2 | Use that field in the GNOME runtime's missing-helper branch | Completed |
| 2.3 | Configure normal native GNOME as non-terminal and legacy raster as terminal | Completed |
| 2.4 | Inspect the narrow diff for unintended routing or protocol changes | Completed — main-thread scoped review found no protocol/routing expansion |

### Phase 3: Validation and progress reconciliation

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Run focused unit/architecture tests and scoped Ruff | Completed — 157 passed; Ruff and diff check passed |
| 3.2 | Run project check using the overlay-client interpreter | Completed with sandbox limitation — 1,649 passed, 21 skipped, 5 loopback socket setup errors |
| 3.3 | Record code result separately from any sandbox socket-harness limitation | Completed — no assertion failures remain |
| 3.4 | Mark the fullscreen-routing plan/iteration stages only after a green regression result | Completed |

## Step 1: Establish regression coverage and contract

**Files:**

- `overlay_client/tests/test_follow_surface_mixin.py`
- `overlay_client/tests/test_backend_consumers.py` and/or the existing GNOME
  presentation-runtime test module
- `overlay_client/tests/test_backend_architecture_boundary.py`

Keep the existing follow-surface test as the integration regression guard.
Add direct tests that construct unavailable GNOME helper state and assert:

- selected native GNOME produces no backend presentation result and does not
  call the injected helper runner;
- selected legacy raster produces the existing unavailable result, with hidden
  presentation diagnostics, and does not call that runner.

This is a test-first change: direct tests should express the profile distinction
before the production policy is changed.

## Step 2: Implement the backend-owned policy

**Files:**

- `overlay_client/backend/presentation_runtime.py`
- `overlay_client/backend/bundles/gnome_shell_wayland.py`

Add the neutral profile field and update the missing-helper branch to use it.
Set only the two GNOME profiles differently.  Do not change generic
`consumers.py` or `follow_surface`; their existing neutral result handling is
the required separation boundary.

Inspect for these unchanged invariants:

- `fullscreen_shell_raster_active` still only controls raster-route activation.
- native helper-available fullscreen, windowed, and failure paths are unchanged.
- legacy raster remains fail-closed.
- X11 and xcompat do not import GNOME presentation code.

## Step 3: Validation and progress

Run:

```bash
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_backend_consumers.py \
  overlay_client/tests/test_gnome_helper_presentation_runtime.py \
  overlay_client/tests/test_backend_architecture_boundary.py -q

overlay_client/.venv/bin/python -m ruff check \
  overlay_client/backend/presentation_runtime.py \
  overlay_client/backend/bundles/gnome_shell_wayland.py \
  overlay_client/tests/test_follow_surface_mixin.py \
  overlay_client/tests/test_backend_consumers.py

git diff --check
make PYTHON=overlay_client/.venv/bin/python check
```

Expected result: the focused suite is green, as are Ruff/mypy.  If the same
loopback socket harness setup errors recur, record them as sandbox limitations;
do not accept any remaining test assertion failure.  Because this repair is
only the native helper-loss fallback, the user-accepted live GNOME renderer
matrix does not need repetition unless the focused or full tests reveal a
presentation-path change.

Update the routing plan and iteration checklist after validation.  Do not
commit or stage user-owned worktree changes without a separate request.
