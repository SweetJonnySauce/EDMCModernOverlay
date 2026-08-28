# Native GNOME Helper-Unavailable Fallback: Remediation Plan

**Status:** Proposed — discovered by the 2026-08-27 full-suite iteration.

## Problem and invariant

The fullscreen Shell-raster routing change made the native
`gnome_shell_wayland` profile return a terminal `helper_unavailable` result
whenever the GNOME helper is absent.  `follow_surface` therefore considers the
backend cycle handled and never invokes its existing legacy follow controller.
This regresses the pre-routing behavior proven by
`test_refresh_follow_geometry_uses_legacy_path_when_gnome_helper_is_not_available`.

The repair must preserve two deliberately different contracts, both owned by
the GNOME bundle rather than generic runtime code:

| Bundle identity | Helper unavailable result | Required behavior |
| --- | --- | --- |
| Native `gnome_shell_wayland` | Not handled | Return `None`; let the established legacy follow controller run. |
| Compatibility `gnome_shell_raster` | Handled/unavailable | Return the existing fail-closed unavailable result; do not show an unproven raster overlay. |

This is a fallback-policy distinction, not a fullscreen-raster capability
distinction.  It must not be inferred from `fullscreen_shell_raster_active`.

## Checklist

- [ ] Step 1: Make helper-unavailable ownership an explicit bundle profile policy.
- [ ] Step 2: Prove native fallback and compatibility fail-closed behavior.
- [ ] Step 3: Run project validation and reconcile the reopened routing plan.

## Phase status

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Bundle-owned helper-unavailable policy | Pending |
| 2 | Regression and boundary coverage | Pending |
| 3 | Full validation and progress reconciliation | Pending |

### Phase 1: Bundle-owned helper-unavailable policy

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add a neutral, explicitly named profile field for whether missing helper ownership is terminal | Pending |
| 1.2 | Set native GNOME to fall through and legacy raster to remain fail-closed | Pending |
| 1.3 | Remove the incorrect coupling to fullscreen-raster activation | Pending |

### Phase 2: Regression and boundary coverage

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Turn the failing native helper-unavailable follow-surface test green | Pending |
| 2.2 | Add direct bundle/runtime assertions for the native fall-through and legacy fail-closed cases | Pending |
| 2.3 | Confirm generic consumers retain no raw GNOME/raster dispatch | Pending |

### Phase 3: Full validation and progress reconciliation

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Run focused tests, lint, and type checking | Pending |
| 3.2 | Run the project check with the overlay-client interpreter and separate code failures from sandbox limits | Pending |
| 3.3 | Update the routing plan and iteration checklist only after the regression is resolved | Pending |

## Step 1: Make helper-unavailable ownership explicit

**Touch points:** `overlay_client/backend/presentation_runtime.py` and
`overlay_client/backend/bundles/gnome_shell_wayland.py`.

- Add one neutral profile property with semantics such as
  `helper_unavailable_is_terminal`.  It describes whether that bundle owns the
  unavailable state; it does not name a backend enum and does not affect
  raster eligibility.
- In `GnomeShellPresentationRuntime.run_presentation_cycle()`, use that policy
  when the helper is absent.  A non-terminal profile returns `None`; a terminal
  profile returns `BackendPresentationRuntimeResult(helper_unavailable=True)`.
- Set the normal native GNOME profile to non-terminal, restoring its legacy
  follower fallback.  Set the legacy raster profile to terminal, preserving
  its conservative unavailable behavior.
- Do not change helper protocol payloads, renderer selection, Shell-raster
  eligibility, managed-PyQt transition ordering, X11, xcompat, `load.py`, or
  EDMC preferences.

**Demo:** With identical unavailable helper state, native GNOME returns `None`
from its bundle runtime, while the legacy raster bundle returns the existing
unavailable result.

## Step 2: Prove both contracts before and after wiring

**Test type:** unit tests.  The policy and bundle selection are deterministic,
and no EDMC lifecycle or `load.py` hook is touched; a harness test is not
required.

- Retain and make green
  `test_refresh_follow_geometry_uses_legacy_path_when_gnome_helper_is_not_available`.
  It proves the integration consequence: the legacy controller is called once
  for native GNOME without a helper.
- Add or extend direct runtime tests in
  `overlay_client/tests/test_backend_consumers.py` (or the existing focused
  GNOME runtime test module) to assert both profile outcomes.  The
  compatibility assertion must continue to prove `should_show_overlay=False`,
  `presentation_state=helper_unavailable`, and no runner invocation.
- Retain `test_backend_architecture_boundary.py` to prove that neither
  `follow_surface` nor generic `consumers.py` grows direct compositor imports
  or raw GNOME/raster enum dispatch.

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
```

## Step 3: Validate and close the regression record

Run the project gate with the intended interpreter; activation alone does not
override the Makefile's `.venv/bin/python` selection:

```bash
make PYTHON=overlay_client/.venv/bin/python check
```

Acceptance criteria:

1. The previously failing follow-surface test passes.
2. Ruff and mypy pass under the overlay-client interpreter.
3. Native GNOME helper absence invokes legacy follow; legacy raster helper
   absence remains fail-closed.
4. The architecture-boundary test passes with no new generic
   compositor-specific dispatch.
5. If socket harness setup errors recur, record the exact loopback-binding
   sandbox limitation separately.  They do not excuse any assertion failure.
6. Only after the code regression is green, mark Phase 1 and the relevant
   Phase 4 automated stages in the fullscreen-routing plan complete.  The
   already accepted manual GNOME matrix need not be repeated for this
   non-rendering helper-loss fallback repair.

## Out of scope and residual risk

This repair does not revisit Mutter monitor placement or alter the selected
fullscreen Shell-raster route.  It restores the native helper-absence fallback
that existed before routing activation while retaining the legacy raster
identity's safety gate.  The only expected external validation limitation is
the pre-existing sandbox prohibition on loopback socket harness setup; rerun
that portion in a socket-permitting environment for a completely green release
gate.
