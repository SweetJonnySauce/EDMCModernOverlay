# Task: Build Paper Backend Contract Suite

## Description
Build a deterministic in-memory paper backend under test support and a reusable parameterized backend-runtime contract suite. The paper backend must exercise the complete public extension point without importing compositor code or becoming selectable in production.

## Background
The new runtime interfaces need behavioral proof before production backends are lifted behind them. A paper backend supplies controlled discovery, presentation, input, health, failure, owner-loss, and lifecycle transitions. Its reusable test factory becomes the contract suite that GNOME, native X11, and XWayland adopt incrementally in later steps.

## Reference Documentation
**Required:**
- Design: docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/planning/2026-07-17-fix219-architecture-convergence/research/contract-tests-and-migration.md (reusable suite, observable assertions, and staged replacement)
- docs/planning/2026-07-17-fix219-architecture-convergence/research/backend-contracts-and-control-plane.md (behavioral partition and normalized result model)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Implement a paper runtime and deterministic in-memory discovery, presentation, input, and optional helper-lifecycle components under test support only.
2. Provide an injected test factory capable of constructing fresh runtimes, controlling clocks/failures, publishing target appearance/loss, and observing owned-resource cleanup.
3. Create a reusable parameterized contract suite covering immutable matching identity, one start, stable services, partial-start cleanup, idempotent bounded stop, and terminal shutdown.
4. Cover discovery appearance/loss/recovery, presentation applied/pending/hidden/unavailable results, independent input click-through/focus state, and independent revisions.
5. Cover support/evidence/health separation, schema-v1 round trips, normalized failures, diagnostic redaction, owner-loss cleanup, and prevention of unsupported fallback claims.
6. Assert observable results and state transitions rather than private class identity so future backend implementations can use different internal composition.
7. Do not register or import the paper backend from production selection, registry, launcher, or generic consumers.
8. Retain existing `test_backend_contracts.py` assertions, including transitional combined-adapter coverage, until production replacement parity exists.

## Dependencies
- Step 2 Tasks 1 and 2 provide behavioral protocols and generic failure runtimes.
- Step 1 provides schema-v1 status serialization and normalized operation/failure models.
- Production backends adopt the test factory incrementally in Steps 7–19; this task does not modify their routing.

## Implementation Approach
1. Define a small paper-backend state model and explicit injected controls for targets, presentation outcomes, interaction state, failures, and owner loss.
2. Implement the paper services and runtime with no Qt, Tk, sockets, timers, or compositor dependencies.
3. Factor reusable contract assertions around a documented backend test-factory protocol.
4. Run the paper backend through the full lifecycle demo and serialize its final status through Step 1's envelope.

## Acceptance Criteria

1. **Deterministic Full Lifecycle**
   - Given a fresh paper runtime and injected target events
   - When it starts, observes a target, presents, changes input state, loses its owner, and receives repeated stop calls
   - Then every result and revision is deterministic, resources are cleaned once, and the final runtime is stopped

2. **Reusable Backend Test Factory**
   - Given another runtime implementation with injected platform dependencies
   - When it supplies the documented test factory
   - Then the shared suite can exercise it without depending on paper-backend classes or concrete compositor modules

3. **Independent Behavioral Services**
   - Given paper presentation and input services backed by separate objects
   - When presentation visibility and interaction policy change independently
   - Then each service reports its own state and revision without object-identity coupling

4. **Safe Failure and Owner-Loss Behavior**
   - Given injected partial-start, presentation, cleanup, or owner-loss failures containing prohibited diagnostic values
   - When the runtime normalizes and serializes the results
   - Then cleanup remains bounded, failures are retained within limits, and secret or personal data does not survive

5. **Non-Production Isolation**
   - Given the production selector, bundles, launcher, and package exports
   - When imports and registrations are inspected
   - Then the paper backend is not selectable or imported by production code and contains no GNOME, X11, XWayland, Qt, or Tk implementation

6. **Targeted Step Validation**
   - Given the complete Step 2 implementation
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_runtime_contracts.py -q` and `git diff --check` are run
   - Then all new contract tests and retained transitional assertions pass

## Metadata
- **Complexity**: High
- **Labels**: fix219, paper-backend, contract-suite, lifecycle, unit-tests, phase-1
- **Required Skills**: Python test architecture, dependency injection, state-machine testing, backend contracts, pytest
