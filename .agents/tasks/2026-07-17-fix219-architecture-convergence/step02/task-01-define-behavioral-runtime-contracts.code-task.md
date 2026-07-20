# Task: Define Behavioral Runtime Contracts

## Description
Define the process-lifetime backend runtime and separate discovery, presentation, input-policy, and optional helper-lifecycle behavioral contracts approved by the detailed design. Add normalized intents, snapshots, stop reasons, and results without routing any production backend or generic consumer through the new interfaces yet.

## Background
The transitional `BackendBundle` exposes factories and nominal component identity, while generic consumers still reach compositor-specific behavior through shared adapters and private dispatch. The converged architecture requires explicit behavior-oriented interfaces whose parameters contain normalized intent rather than presenter names, helper actions, or compositor enums. One concrete object may implement multiple interfaces, but consumers and tests must never require that identity coupling.

## Reference Documentation
**Required:**
- Design: docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/planning/2026-07-17-fix219-architecture-convergence/research/backend-contracts-and-control-plane.md (recommended contract partition and intent/result boundaries)
- docs/planning/2026-07-17-fix219-architecture-convergence/research/contract-tests-and-migration.md (observable contract coverage and staged replacement)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Define runtime-checkable protocols for `BackendRuntime`, `DiscoveryService`, `PresentationService`, `InputPolicyService`, and optional `HelperLifecycle` with the exact ownership responsibilities from the detailed design.
2. Define immutable normalized target, frame, geometry/coordinate-space, presentation, interaction, helper-health, presentation-state, input-state, and lifecycle intent/snapshot models needed by those protocols.
3. Use Step 1's normalized operation, health, recovery, failure, and schema-v1 status types at contract boundaries.
4. Ensure presentation intent requests windowed, borderless-fullscreen, or hidden behavior without naming managed PyQt, Shell raster, Overview, D-Bus actions, helper tokens, or private target handles.
5. Keep presentation and input contracts separate and independently revisioned even when one implementation object satisfies both protocols.
6. Specify immutable runtime identity, stable component-instance access, one-start production semantics, idempotent stop, partial-start cleanup, and no restart after stop.
7. Keep the protocols pure and data-oriented; do not import Qt widgets, Tk, compositor-private modules, or concrete factories into the generic contract module.
8. Add unit tests using minimal independent stubs to prove structural conformance, value semantics, and the absence of an object-identity requirement.

## Dependencies
- Step 1's converged backend models and operation-result vocabulary.
- Existing `overlay_client/backend/contracts.py` types remain available until production replacements are proven.
- Runtime construction, registration, and launcher ownership are deferred to Steps 4 and 5.

## Implementation Approach
1. Translate the detailed design's component interfaces and intent fields into narrowly typed protocols and immutable records beside the transitional contracts.
2. Keep protocol types independent of concrete event loops and use opaque or normalized surface/observer boundaries where required.
3. Build independent test doubles for each interface, including separate presentation and input objects and one combined object that implements both.
4. Run the focused contract tests and verify no production imports or routing changed.

## Acceptance Criteria

1. **Behavior-Oriented Public Contracts**
   - Given a generic consumer needing discovery, presentation, input, or helper health
   - When it uses the new interfaces
   - Then it can express the required behavior without importing a concrete backend or naming compositor-private actions

2. **Separate Presentation and Input**
   - Given one runtime whose presentation and input services are distinct objects and another whose single object implements both
   - When both are checked against the contracts
   - Then both conform and no contract or test requires presentation and input object identity

3. **Immutable Runtime Identity and Components**
   - Given a runtime implementation and repeated component access
   - When its identity and services are observed across its lifetime
   - Then identity is immutable and the same owned service instances are returned without reconstructing a bundle

4. **Private Vocabulary Exclusion**
   - Given normalized presentation and interaction intents
   - When their fields, imports, and serialization are inspected
   - Then they contain no GNOME renderer, D-Bus, helper-token, Overview-action, or private target-handle vocabulary

5. **Pure Unit Coverage**
   - Given independent and combined protocol stubs
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_runtime_contracts.py -q` is run
   - Then new behavioral contract tests pass and the transitional contract assertions remain present and passing

## Metadata
- **Complexity**: High
- **Labels**: fix219, backend-runtime, protocols, behavioral-contracts, unit-tests, phase-1
- **Required Skills**: Python typing and protocols, immutable API design, backend architecture, pytest
