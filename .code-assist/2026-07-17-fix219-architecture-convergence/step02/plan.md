# Step 02 Implementation and Test Plan

Test type: **unit tests plus a reusable behavioral contract suite**. All touched logic is
pure/deterministic with injected state, clocks, and failures. No EDMC/plugin hook, Tk/Qt,
socket, process, selector, launcher, or production runtime wiring is touched, so harness, GUI,
and real-world compositor tests are not required for this step.

## Phase Tracking

| Phase | Status |
| --- | --- |
| Phase 2: Step 02 behavioral runtime contracts | In progress |

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Verify state, read the complete design/tasks, and map existing seams | Completed |
| 2.2 | Define complete acceptance coverage, interfaces, and test plan | Completed |
| 2.3 | Write all unit/contract tests and capture expected RED failures | Completed |
| 2.4 | Implement contracts, failure runtimes, and paper backend to GREEN | Completed |
| 2.5 | Refactor and run targeted/project validation | Completed |
| 2.6 | Update authoritative evidence and commit the completed Step 02 increment | In progress |

## Test Scenarios

1. **Behavior-oriented protocol surface**
   - Input: minimal independent discovery, presentation, input, helper, and runtime stubs.
   - Output: runtime-checkable structural conformance; incomplete stubs do not conform.
2. **Separate and combined presentation/input implementations**
   - Input: one runtime exposing different service objects and one exposing a combined object.
   - Output: both conform; revisions remain independent; no identity assertion is required.
3. **Immutable normalized values**
   - Input: target, frame, rectangle/coordinate-space, presentation, interaction, helper,
     presentation-state, input-state, and lifecycle records.
   - Output: valid values compare by value and reject mutation, invalid enums/revisions/scales/
     geometry combinations raise explicit errors.
4. **Private vocabulary exclusion**
   - Input: inspect behavioral-contract source, field names, annotations, and serialized status.
   - Output: no renderer, D-Bus, Overview, helper-token, Qt/Tk, compositor-private module, or
     private target-handle vocabulary appears.
5. **Unavailable selected identity**
   - Input: supported identity plus missing-prerequisite reason and restart-required recovery.
   - Output: runtime/status identities match; support remains supported; health is unavailable;
     presentation is never visible and reports unavailable.
6. **Unimplemented detected identity**
   - Input: detected placeholder identity/environment.
   - Output: support is unimplemented, evidence is not applicable, health is unavailable,
     recovery is terminal, and no transitional Wayland presenter is constructed or imported.
7. **Stable inert services and revisions**
   - Input: repeated discovery/presentation/input/helper property and snapshot access.
   - Output: stable owned instances, deterministic values, and independent state revisions.
8. **Lifecycle permutations**
   - Input: stop-before-start, failed start then stop, repeated start, repeated stop, and start
     after terminal stop.
   - Output: one start attempt, idempotent final result, reverse cleanup, and no restart.
9. **Bounded cleanup and sanitization**
   - Input: injected cleanup steps with clock advancement and exceptions containing a secret,
     owner ID, personal path, title, command, and private identifier.
   - Output: cleanup continues while within the deadline, skips later work after expiry,
     retains bounded normalized failures, and serialized JSON contains none of the fixtures.
10. **Paper discovery lifecycle**
    - Input: start, target appearance, target loss, and recovery using injected controls.
    - Output: observer and snapshots receive deterministic availability/revision transitions.
11. **Paper presentation lifecycle**
    - Input: windowed present, injected pending, hidden request, injected unavailable, and target
      loss.
    - Output: applied/pending/hidden/unavailable results with correct visibility and monotonic
      presentation revisions; no unsupported fallback claim.
12. **Paper input lifecycle**
    - Input: click-through/focus-safe and interactive intents independent of presentation.
    - Output: deterministic applied state and an input revision unaffected by presentation-only
      changes.
13. **Partial start and owner loss**
    - Input: injected failure after acquiring selected resources, then owner loss and repeated
      stop.
    - Output: reverse single cleanup, hidden presentation, terminal runtime, and safe final
      status.
14. **Three-axis status and schema-v1 round trip**
    - Input: supported/evidence/health combinations and paper final status.
    - Output: axes remain independent; serialize/decode equality succeeds with matching runtime
      identity and bounded histories.
15. **Reusable test factory**
    - Input: a factory exposing only documented injected controls and runtime protocols.
    - Output: shared assertions exercise identity, lifecycle, services, failures, owner loss,
      status, and cleanup without importing paper implementation classes.
16. **Non-production isolation and compatibility**
    - Input: inspect production selector, bundles, launcher, consumers, and package exports;
      run retained transitional contract tests.
    - Output: no paper backend import/registration and all existing transitional assertions
      remain unchanged and passing.

## Implementation Sequence

1. Add the complete Step 02 test and reusable-suite acceptance surface first.
2. Run the focused command and capture expected missing-module/symbol failures (RED).
3. Add pure normalized records and runtime-checkable protocols beside transitional contracts.
4. Add stable inert services and unavailable/unimplemented runtime lifecycle behavior.
5. Add the test-only factory protocol, deterministic paper runtime, and injected controls.
6. Run focused tests after each seam, refactor to repository conventions, then run whole-project
   lint/type/test gates and patch hygiene.
7. Run the named deterministic paper lifecycle demo, update Step 02 evidence only after every
   acceptance item passes, and commit relevant files without pushing.

## Validation Commands

- Focused unit/contract gate:
  `.venv/bin/python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_runtime_contracts.py -q`
- Focused lint:
  `.venv/bin/python -m ruff check overlay_client/backend/runtime_contracts.py overlay_client/backend/failure_runtimes.py overlay_client/backend/__init__.py overlay_client/tests/backend_runtime_testkit.py overlay_client/tests/test_backend_runtime_contracts.py overlay_client/tests/test_backend_contracts.py`
- Focused format check:
  `.venv/bin/python -m ruff format --check overlay_client/backend/runtime_contracts.py overlay_client/backend/failure_runtimes.py overlay_client/backend/__init__.py overlay_client/tests/backend_runtime_testkit.py overlay_client/tests/test_backend_runtime_contracts.py overlay_client/tests/test_backend_contracts.py`
- Headless suite: `.venv/bin/python -m pytest`
- Core check: `make check`
- Project test target: `make test`
- EDMC compatibility-floor check:
  `ALLOW_EDMC_PYTHON_MISMATCH=1 .venv/bin/python scripts/check_edmc_python.py`
- Patch hygiene: `git diff --check`

## Rollback and Compatibility

This increment is additive. Rollback removes the new behavioral modules, public exports,
test-only paper backend/suite, focused tests, and Step 02 records. Existing selectors, bundles,
launcher, consumers, runtime presentation, control-plane consumers, and transitional tests
remain the production oracle throughout.
