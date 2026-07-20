# Task: Add Converged Backend Status Models

## Description
Add the immutable normalized backend identity, environment, operational-probe, support, evidence, health, operation-result, failure, and lifecycle models approved by the fix219 detailed design. Introduce them beside the transitional backend types without changing production selection, presentation, status payloads, or settings behavior.

## Background
The current `BackendSelectionStatus` and bundle contracts collapse several concerns and retain transitional identities. Phase 1 needs pure types that keep project support policy, reviewed validation evidence, and live runtime health independent before any production consumer is routed through the new architecture. These models become the shared vocabulary for the schema-version-1 envelope, runtime contracts, registry, status UI, and diagnostics in later steps.

## Reference Documentation
**Required:**
- Design: docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/planning/2026-07-17-fix219-architecture-convergence/research/backend-contracts-and-control-plane.md (contract partition, three-axis status, and intent/result recommendations)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Add frozen, slotted dataclasses and string enums for `BackendIdentity`, `EnvironmentKey`, `ProbeState`, `CapabilityProbe`, `SupportPolicy`, `EvidenceLevel`, `RuntimeHealth`, `OperationOutcome`, `RecoveryClass`, `OperationResult`, normalized failures, selection, ownership, and lifecycle summaries required by schema version 1.
2. Preserve the exact enum values and stable Linux identities defined by the detailed design; do not remove or reinterpret transitional `BackendDescriptor`, `BackendSelectionStatus`, or existing enums in this task.
3. Keep support policy, validation evidence, and runtime health as independent fields with no helper that derives one axis solely from another.
4. Represent backend-private evidence and diagnostics through immutable, JSON-compatible sanitized mappings without exposing compositor actions, helper tokens, target handles, or presenter selection inputs.
5. Define immutable revision fields, local-age semantics, and normalized failure-record fields without enforcing cross-snapshot monotonicity or collection bounds in this task; Task 2 owns history bounding and Task 3 owns shadow-producer revision behavior.
6. Keep capture exclusion as capability vocabulary only; do not introduce a capture behavior contract.
7. Add focused unit tests for enum values, record immutability, identity stability, independent status axes, revision validation, and safe diagnostic-map construction.

## Dependencies
- Existing transitional types in `overlay_client/backend/contracts.py` and `overlay_client/backend/status.py` remain production-compatible and available.
- The detailed design's Data Models and Configuration and Control-Plane Requirements sections are authoritative if existing names or classifications conflict.
- This is the first task in Step 1 and has no dependency on later runtime-contract or routing work.

## Implementation Approach
1. Inventory the exact approved model fields from the detailed design and map them into a cohesive pure module under `overlay_client/backend/` beside the transitional types.
2. Implement the enums and immutable records with explicit validation at construction boundaries and minimal public exports.
3. Add unit tests in the focused control-plane test module, keeping existing transitional assertions intact.
4. Run the targeted model tests and confirm no production consumer has been changed to read the new records.

## Acceptance Criteria

1. **Stable Normalized Vocabulary**
   - Given the approved backend identity, probe, support, evidence, health, outcome, and recovery values
   - When the new enum types are inspected or serialized by value
   - Then every value exactly matches the detailed design and no obsolete presenter is introduced as a new production identity

2. **Immutable Independent Status Axes**
   - Given a backend that is project-supported but currently unavailable with limited validation evidence
   - When its normalized records are constructed
   - Then support, evidence, and health retain those independent values and the frozen records reject mutation

3. **Safe Backend Evidence Boundary**
   - Given backend-private probe evidence or operation diagnostics
   - When it is accepted into a normalized record
   - Then only JSON-compatible sanitized data is retained and tokens, raw owner IDs, target handles, titles, command lines, and personal paths are rejected or redacted at the boundary

4. **Revision and Failure Record Semantics**
   - Given an individual status revision, local age, and normalized failure record
   - When the immutable records are constructed
   - Then their field values are validated without comparing cross-process monotonic clocks, while history bounding and cross-snapshot revision changes remain assigned to Tasks 2 and 3

5. **Unit Regression Coverage**
   - Given the new pure models and the unchanged transitional status types
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_status.py overlay_client/tests/test_backend_control_plane.py -q` is run
   - Then model tests and existing transitional status assertions pass without requiring EDMC lifecycle or GUI wiring

## Metadata
- **Complexity**: Medium
- **Labels**: fix219, backend, control-plane, data-models, unit-tests, phase-1
- **Required Skills**: Python dataclasses and enums, immutable data modeling, API boundary design, pytest
