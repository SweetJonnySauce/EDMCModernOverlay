# Task: Harden Native Helper Readback Diagnostics

## Description
Make the guarded native GNOME Wayland monitor-transfer decision supportable through the existing optional presentation-diagnostics mechanism, while proving that helper readback remains the sole authority for healthy placement. Preserve the client retry, persistent-mismatch backoff, and backend-owned presentation boundary.

## Background
Step 1 added a guarded `move_to_monitor()` before the existing normal resize path. The helper already has an optional diagnostics mechanism and the Python client already validates the helper-reported applied rectangle, retries a transient mismatch, and suppresses persistent wrong-monitor placement. This task locks those behaviors together without adding a protocol field, changing a helper schema/version, or teaching generic follow code about GNOME presentation details.

## Reference Documentation
**Required:**
- Design: `docs/plans/2026-08-27-gnome-wayland-monitor-placement/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/existing-code-and-runtime-evidence.md`
- `docs/plans/2026-08-27-gnome-wayland-monitor-placement/research/mutter-window-placement.md`

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Use only the established optional `include_presentation_diagnostics` / `presentation_diagnostics` mechanism to make normal-path monitor-transfer decisions diagnosable. When diagnostics are requested, retain evidence for the action label, trusted target monitor, overlay pre/post monitor, and existing requested/applied rectangle readback; do not emit diagnostics by default.
2. Preserve the current helper protocol, helper protocol/version constants, capabilities, request payload shape, top-level presentation-result schema, and diagnostic schema version. Do not add a public preference, a new payload field, or backend/client selector behavior.
3. Preserve the existing applied-rectangle tolerance, one-cycle retry, wrong-monitor classification, persistent-mismatch backoff, degraded/suppressed visibility behavior, and fail-closed readiness rule. A successful helper method call or diagnostic record must never substitute for matching applied-rectangle readback.
4. Add deterministic source-contract and Python unit coverage in the existing helper source, presentation-state, and presentation-runtime test suites. No `load.py`, EDMC lifecycle, journal, dashboard, or plugin hook work is in scope, so do not add a harness test.
5. Preserve the `fix219` boundary: do not edit generic follow/runtime surfaces to import GNOME helper implementations or branch on raw backend/helper enums. Do not modify native X11, XWayland compatibility, renderer selection, payload processing, or backend-bundle interfaces.

## Dependencies
- Step 1's guarded normal-path transfer commit `fa94da3c76a4136fe7f034e45fa2fbc9a7c0d9cd` and its existing source-contract coverage.
- Existing optional presentation diagnostics in `helpers/gnome_shell_extension/extension.js` and validated presentation state/runtime behavior under `overlay_client/backend/`.
- The existing architecture boundary test protecting `overlay_client/follow_surface.py` from GNOME-specific imports and enum dispatch.

## Implementation Approach
1. Start with RED coverage that specifies the optional normal-path diagnostics contract and confirms diagnostic data is observational only; use the established source-contract tests where GNOME Shell JavaScript cannot be directly executed, plus deterministic Python unit tests for presentation-state/runtime behavior.
2. Make only the smallest helper-side correction required by failing coverage to retain stable normal-path action, target/pre/post monitor, and requested/applied readback evidence behind the existing diagnostics flag. If the implementation already satisfies the RED contract, do not manufacture a production change.
3. Prove a transient lag is ready only after a matching readback and a persistent one-monitor-right applied rectangle remains wrong-monitor, degraded, and bounded by backoff. Run the architecture boundary test without changing generic code.
4. Inspect the scoped diff to confirm no protocol/schema, backend-boundary, X11/XWayland, renderer, payload, or lifecycle scope expansion occurred.

## Acceptance Criteria

1. **Optional normal-path diagnostics expose the guarded decision**
   - Given a normal GNOME helper presentation request with existing presentation diagnostics enabled
   - When the helper evaluates a valid monitor mismatch, matching monitor, unavailable transfer, or transfer error
   - Then deterministic source-contract/unit coverage proves the optional diagnostics retain the normal action label, trusted target monitor, overlay pre/post monitor, and existing requested/applied rectangle evidence without enabling diagnostics by default

2. **No helper protocol or schema expansion occurs**
   - Given the completed helper diagnostics implementation
   - When its request/result and diagnostic contract are inspected
   - Then helper protocol/version/capabilities, request payload shape, top-level result schema, and diagnostic schema version remain unchanged, with no new public preference or client/backend selector branch

3. **Readback remains the fail-closed readiness authority**
   - Given a presentation cycle whose first helper response has an applied rectangle outside the existing tolerance and whose next response matches
   - When the deterministic runtime unit test runs
   - Then it retries only under the established policy and reports ready only after the matching readback, regardless of transfer action or diagnostics

4. **Persistent wrong-monitor placement remains degraded and bounded**
   - Given repeated helper responses whose applied rectangle is one monitor width from the request
   - When deterministic runtime coverage runs consecutive presentation cycles
   - Then it retains `wrong_monitor_applied_rect`, records persistent mismatch, backs off after the existing limit, and keeps the overlay degraded/suppressed rather than reporting healthy placement

5. **Backend ownership remains intact**
   - Given the completed implementation and tests
   - When `overlay_client/tests/test_backend_architecture_boundary.py` inspects generic follow code
   - Then no direct GNOME-helper import, raw `BackendInstance.GNOME_SHELL_WAYLAND` dispatch, `HelperKind.GNOME_SHELL_EXTENSION` dispatch, or compositor-specific presentation behavior appears outside the backend-owned boundary

6. **Required deterministic validation passes**
   - Given the completed scoped change
   - When running the following commands
   - Then the focused source-contract/unit suite and whitespace check pass; report any `make check` environment limitation exactly and do not claim that full gate passed if it cannot run

```bash
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest \
  overlay_client/tests/test_gnome_shell_helper_extension_source.py \
  overlay_client/tests/test_gnome_shell_helper_presentation_state.py \
  overlay_client/tests/test_gnome_helper_presentation_runtime.py \
  overlay_client/tests/test_backend_architecture_boundary.py -q
make check
git diff --check
```

## Metadata
- **Complexity**: Medium
- **Labels**: GNOME Wayland, Native Helper, Diagnostics, Readback, Backend Boundary, Regression
- **Required Skills**: GNOME Shell JavaScript, Mutter Meta.Window API, Python pytest, Source-contract testing, Backend architecture boundaries
