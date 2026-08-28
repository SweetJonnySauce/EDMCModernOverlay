# Iteration Checklist: GNOME Wayland Fullscreen Shell-Raster Routing

## Outcome

**Implementation status: complete.** Commit `0946437`
(`fix(gnome): restore native helper fallback`) fixes the native-GNOME
helper-unavailable regression introduced by fullscreen Shell-raster routing.
The native GNOME bundle now falls through to the established legacy follower
when its helper is unavailable. The compatibility raster identity remains
terminal and fail-closed.

**Release-readiness status: locally verified.** Outside the sandbox, the five
real-socket harness fixtures pass and both full project gates pass: Ruff and
mypy are clean, and each run collected **1,675 passing tests**. The local
Python 3.12.3 64-bit interpreter is still not the tested EDMC Python 3.13.9+
32-bit runtime, so that remains a release-environment compatibility check.

No production code was changed while performing this checklist.

## Phase tracking

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Reconcile approved artifacts, commits, task/code-assist records, handoffs, and worktree ownership | Completed |
| 1.2 | Audit implementation against the backend-boundary and fallback contracts | Completed |
| 1.3 | Rerun focused and project validation with `overlay_client/.venv` | Completed |
| 1.4 | Review EDMC compliance, worktree safety, and residual risks | Completed |
| 1.5 | Record iteration decision | Completed |

## Implementation and design checks

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- |
| I1 | Does the selected native GNOME bundle own presentation-runtime policy? | Yes | `GnomeShellPresentationRuntime` and neutral profile data keep compositor behavior in the GNOME bundle, not generic follow/runtime code. |
| I2 | Does eligible native GNOME fullscreen use the real-content Shell-raster route? | Yes | The native profile remains raster-active; existing helper-runtime, raster-frame, repaint, transition, and extension-contract tests are included in the independent 251-test focused suite. |
| I3 | Does windowed or ineligible GNOME retain managed PyQt? | Yes | Existing windowed, partial-screen, and ineligible helper-cycle contracts remain green in the focused suite. |
| I4 | Do fullscreen raster failures remain fail-closed? | Yes | Native profile still enables suppression of managed-PyQt fallback on unproven Shell-raster failure; focused runtime/transition coverage passes. |
| I5 | Does a raster actor clear before a managed presentation transition commits? | Yes | Existing clear-first transition coverage passes in the focused suite; this remediation does not alter that state machine. |
| I6 | Do target/helper loss and target replacement clear/reset safely? | Yes | Existing guarded loss/reset contracts remain covered by the focused runtime/transition tests; the repaired native helper-loss path now intentionally falls through to legacy follow. |
| I7 | Does native GNOME without a helper preserve legacy follow behavior? | Yes | `helper_unavailable_is_terminal=False` for native GNOME makes the runtime return `None`; the existing follow-surface integration test and a direct consumer test pass. |
| I8 | Does compatibility `gnome_shell_raster` remain fail-closed without a helper? | Yes | Its profile sets `helper_unavailable_is_terminal=True`; direct consumer coverage retains hidden `helper_unavailable` behavior and verifies no runner invocation. |
| I9 | Are X11/xcompat unchanged and generic code free of raw GNOME/raster dispatch? | Yes | The production diff is restricted to neutral runtime profile data and the GNOME bundle. `test_backend_architecture_boundary.py` passes. |
| I10 | Did this iteration alter helper protocol, payload schema, `load.py`, prefs, or EDMC lifecycle wiring? | No | Correctly excluded. Unit tests are sufficient for this deterministic profile-policy repair; no new harness test is required for its code path. |

## Validation checklist

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| V1 | Does the expanded focused native-GNOME suite pass? | Yes | `source overlay_client/.venv/bin/activate && PYQT_TESTS=1 python -m pytest` over follow-surface, backend-consumers, helper-runtime, architecture, raster-frame, repaint, transition, and extension-source suites: **251 passed in 1.24s**. |
| V2 | Does scoped lint pass? | Yes | `overlay_client/.venv/bin/python -m ruff check` over the two production files and focused test files passed. |
| V3 | Does whitespace validation pass? | Yes | `git diff --check` passed during the implementation; this checklist's documentation diff is checked before handoff. |
| V4 | Does `make check` pass using the requested overlay-client environment? | Yes | Outside the sandbox: `source overlay_client/.venv/bin/activate && make PYTHON="$VIRTUAL_ENV/bin/python" check` passed Ruff, mypy, and **1,675 tests**. |
| V5 | Does `make test` pass with that environment? | Yes | Outside the sandbox: the same command form with `test` passed **1,675 tests**. The formerly blocked socket file passes independently: **8 passed**. |
| V6 | Does the EDMC Python baseline check pass locally? | No | `source overlay_client/.venv/bin/activate && python scripts/check_edmc_python.py` reports Python 3.12.3 64-bit, while the documented tested runtime is Python 3.13.9+ 32-bit. |
| V7 | Was the live GNOME matrix accepted? | Yes, user-reported | The previously recorded six-case Wayland matrix remains accepted, with per-case diagnostic capture explicitly waived by the user. This iteration performed no live GNOME, DBus, EDMC, or Elite actions. |

## Scope and worktree safety

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| S1 | Is the fallback repair committed? | Yes | `0946437 fix(gnome): restore native helper fallback` contains only the two approved production files, `test_backend_consumers.py`, and implementation-owned task/code-assist/dashboard artifacts. |
| S2 | Is the worktree clean? | No | The local `overlay_settings.json` change and this post-validation documentation update remain unstaged. Neither is production code. |
| S3 | Were unrelated paths reset, deleted, staged, pushed, or externally mutated? | No | The iteration used read-only inspection, tests, and documentation updates only. |
| S4 | Is a real desktop screenshot or new diagnostic capture attached? | No | No live action was authorized or needed for this fallback-policy repair; the earlier user waiver remains in effect. |

## EDMC compliance review (scoped to this iteration)

| Requirement group | Yes/No | Evidence and action |
| --- | --- | --- |
| Stay aligned with EDMC core and tested Python | No | Plugin entry points were not changed, but the local validation interpreter is not the tested EDMC 3.13.9+ 32-bit runtime. Run the baseline check and relevant release validation there. |
| Use supported plugin APIs and helpers | Yes | No plugin-runtime imports, EDMC API calls, settings persistence paths, or helper protocol code changed; scope is the external overlay backend. |
| Use EDMC logging and versioning patterns | Yes | No plugin logger, version gate, or `print` path changed. |
| Keep runtime work responsive and Tk-safe | Yes | No Tk, worker-thread, network, `load.py`, or lifecycle behavior changed. |
| Integrate preferences and UI hooks correctly | Yes | No preferences, `plugin_prefs`, `prefs_changed`, `plugin_app`, or Tk UI code changed. |
| Package dependencies and debug HTTP responsibly | Yes | No dependency packaging, HTTP, or debug-routing code changed. |

## Residual risks and required follow-up

1. Run `python scripts/check_edmc_python.py` in the tested EDMC 3.13.9+
   32-bit runtime before release-grade plugin compatibility acceptance.
2. Retain the compatibility `GNOME_SHELL_RASTER` override/status cleanup as a
   separate approved compatibility-removal effort; it is not part of this fix.
3. If an independent release reviewer requires reproducible desktop proof,
   repeat the already accepted GNOME matrix and retain non-secret diagnostics.

## Iteration decision

- Reopen requirements or design: **No**.
- Rework the implemented native GNOME fallback code: **No**.
- Accept the focused implementation and all assertion-bearing tests: **Yes**.
- Treat the project-wide local release gate as fully green: **Yes**.
- Accept the routing implementation as complete: **Yes**. The only remaining
  release-environment follow-up is EDMC 3.13.9+ 32-bit compatibility validation.
