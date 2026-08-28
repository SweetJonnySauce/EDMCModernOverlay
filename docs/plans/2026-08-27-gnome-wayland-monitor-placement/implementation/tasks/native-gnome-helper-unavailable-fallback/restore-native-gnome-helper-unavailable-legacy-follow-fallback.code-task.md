# Task: Restore Native GNOME Helper-Unavailable Legacy-Follow Fallback

## Description
Restore the pre-routing native GNOME Wayland behavior when the GNOME Shell
helper is unavailable: the selected `gnome_shell_wayland` bundle must return
`None` so the existing legacy follower performs its normal refresh. Preserve
the deliberately different compatibility `gnome_shell_raster` contract: a
missing helper remains terminal and fail-closed. Deliver the profile-policy
change and its direct regression evidence as one indivisible strict
RED -> GREEN -> REFACTOR increment.

## Background
The GNOME bundle currently derives helper-loss ownership from
`fullscreen_shell_raster_active`. Because both native GNOME Wayland and the
legacy raster identity activate the fullscreen Shell-raster route, they both
return the terminal `helper_unavailable` result. Generic consumers correctly
interpret that neutral result as a handled hidden-overlay cycle, but that
prevents `follow_surface` from invoking its historical legacy follower for
native GNOME Wayland.

Helper-loss ownership is a bundle-profile policy, not fullscreen-raster
eligibility. The neutral runtime profile must express that distinction without
making generic consumers or follow code aware of GNOME-specific identities.
This repair is intentionally limited to backend runtime profile data, the
missing-helper branch, and deterministic unit coverage; it changes no helper
protocol, renderer route, lifecycle, UI, or EDMC integration.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/native-gnome-helper-unavailable-fallback-remediation.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-helper-unavailable-fallback-implementation-plan.md` (Steps 1-2 and exact focused validation)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-helper-unavailable-fallback-remediation-plan.md` (fallback invariant and regression record)
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/implementation/native-gnome-helper-unavailable-fallback-orchestration-prompt.md` (scope, boundary, and validation guardrails)
- `AGENTS.md` (fix219 boundary and required test-selection policy)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context. The approved
scope combines implementation-plan Steps 1-2 into this single functional TDD
increment; do not split policy production work from its regression tests.

## Technical Requirements
1. Add one neutral, explicitly named profile policy such as `helper_unavailable_is_terminal` to `BackendPresentationRuntimeProfile`. Its meaning must be whether a selected bundle owns a missing-helper state; it must not name a compositor enum and must remain independent of `fullscreen_shell_raster_active`.
2. Update only the GNOME bundle runtime's missing-helper branch so a non-terminal profile returns `None`, while a terminal profile returns the existing `BackendPresentationRuntimeResult(helper_unavailable=True)`. Do not call the injected or default presentation runner in either missing-helper case.
3. Configure the normal `gnome_shell_wayland` profile as non-terminal and the compatibility `gnome_shell_raster` profile as terminal. Preserve the existing fullscreen Shell-raster activation and managed-PyQt fallback-suppression settings for both profiles.
4. Begin strictly RED: add or adjust deterministic unit coverage before production changes. Retain the native follow-surface regression and add direct selected-bundle/runtime assertions for both unavailable-helper outcomes, including the no-runner-call invariant.
5. Make GREEN with the smallest production change that satisfies the tests. REFACTOR only after GREEN for clear neutral policy naming and local readability; do not alter behavior beyond the stated helper-unavailable contracts.
6. Preserve the fix219 backend boundary: generic `consumers.py` and `follow_surface` must not import compositor-specific helper/presentation implementations or dispatch on raw GNOME/raster/backend enums. Retain and run the architecture-boundary coverage.
7. Do not expand scope into helper protocol payloads, renderer selection, fullscreen Shell-raster eligibility or transition ordering, monitor/Mutter behavior, X11, xcompat, `load.py`, EDMC hooks, preferences, settings, or removal of the legacy raster identity.
8. Select unit tests explicitly: this policy and injected runtime behavior are deterministic, and neither `load.py` nor EDMC lifecycle wiring changes. A harness test is not required; record that rationale, test files changed, exact commands, and outcomes in the implementation documentation and handoff.

## Dependencies
- The existing neutral `BackendPresentationRuntimeProfile`, `BackendPresentationRuntimeResult`, selected bundle runtime seam, and generic consumer translation of neutral results.
- Existing focused regression suites: `overlay_client/tests/test_follow_surface_mixin.py`, `overlay_client/tests/test_backend_consumers.py`, `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, and `overlay_client/tests/test_backend_architecture_boundary.py`.
- The approved remediation design and implementation-plan Steps 1-2; their native fall-through and legacy-raster fail-closed contracts are authoritative.

## Implementation Approach
1. Inspect the existing native helper-unavailable follow-surface regression, selected bundle construction, and neutral consumer translation. Establish RED with deterministic direct tests proving native GNOME helper absence returns no runtime result and invokes no runner, while legacy raster helper absence returns the existing unavailable result and invokes no runner. Confirm the existing follow-surface regression demonstrates exactly one legacy refresh for native GNOME.
2. Add the neutral terminal-helper-unavailable policy to the profile and use it only in `GnomeShellPresentationRuntime.run_presentation_cycle()` when helper availability is false. Configure native GNOME Wayland to fall through and legacy raster to remain terminal, leaving `fullscreen_shell_raster_active` responsible only for its existing raster-route semantics.
3. Make the RED tests GREEN, retaining the legacy raster hidden/fail-closed diagnostics (`should_show_overlay=False`, `presentation_state=helper_unavailable`) and the native legacy-follow consequence. Verify available-helper fullscreen/windowed tests remain covered by the existing focused suite.
4. REFACTOR only if it improves clarity without broadening the diff. Inspect generic consumers and follow code for prohibited raw compositor enum dispatch/imports, then run the focused test/lint gate and `git diff --check`.

## Acceptance Criteria

1. **Native GNOME Helper Loss Falls Through to Legacy Follow**
   - Given a selected native `gnome_shell_wayland` backend whose GNOME Shell helper is unavailable
   - When its bundle runtime and the follow-surface refresh path run
   - Then the runtime returns `None`, the presentation runner is not called, and the existing legacy follower refreshes exactly once

2. **Legacy Raster Helper Loss Remains Terminal and Fail-Closed**
   - Given a selected compatibility `gnome_shell_raster` backend whose GNOME Shell helper is unavailable
   - When its bundle runtime and generic consumer cycle run
   - Then the runtime returns the existing terminal unavailable result, the runner is not called, the resulting overlay is hidden/fail-closed, and diagnostics retain `presentation_state=helper_unavailable`

3. **Helper-Loss Ownership Is a Neutral Explicit Profile Policy**
   - Given the two GNOME bundle runtime profiles
   - When their missing-helper behavior is selected
   - Then their only helper-loss distinction is an explicit neutral `helper_unavailable_is_terminal`-style policy, and `fullscreen_shell_raster_active` is not used to decide terminal helper-loss ownership

4. **Generic Boundary and Approved Scope Are Preserved**
   - Given the completed change
   - When `follow_surface`, generic consumers, and backend architecture tests are inspected and exercised
   - Then no generic consumer/follow code imports compositor-specific presentation helpers or dispatches on raw GNOME/raster/backend enums, and no changes appear outside the approved production/test scope

5. **Strict TDD and Deterministic Unit Evidence Are Recorded**
   - Given the functional policy increment
   - When implementation proceeds from RED through GREEN and REFACTOR
   - Then the direct unit tests precede the production policy change, focused tests cover both unavailable-helper contracts and the legacy-follow regression, and documentation records that no harness test is required because `load.py` and lifecycle wiring are untouched

6. **Focused Validation Passes**
   - Given the scoped implementation and updated unit tests
   - When running the following commands
   - Then every non-sandbox-blocked assertion and lint check passes, and any loopback socket harness setup limitation is recorded separately rather than treated as a passing result:

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

## Metadata
- **Complexity**: Medium
- **Labels**: GNOME Wayland, Helper Unavailable, Legacy Follow, Fail Closed, Backend Boundary, fix219, TDD, Unit Tests
- **Required Skills**: Python backend-runtime design, dataclass profile policy, pytest, architecture-boundary testing, failure-mode testing
