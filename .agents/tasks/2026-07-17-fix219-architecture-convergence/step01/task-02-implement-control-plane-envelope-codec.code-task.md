# Task: Implement Control-Plane Envelope Codec

## Description
Implement deterministic serialization and strict deserialization for the immutable schema-version-1 backend control-plane envelope. Enforce bounded histories, allowlisted diagnostic fields, secret redaction, and explicit rejection of unknown or malformed versions while leaving existing content, settings, and transitional backend-status payloads unchanged.

## Background
The converged architecture needs one backend envelope that can eventually be shared by the client, plugin, controller, preferences, collector, and tests. Step 1 introduces it only as a pure model and diagnostic comparison artifact. Production consumers do not migrate until Step 20, so this task must provide a safe codec without creating a second behavioral control path.

## Reference Documentation
**Required:**
- Design: docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/planning/2026-07-17-fix219-architecture-convergence/research/backend-contracts-and-control-plane.md (schema recommendation and generic/private boundary)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Define the complete immutable backend envelope for schema version 1, including producer, revision, selected runtime, selection, support/evidence, health/recovery, probes, presentation, input, helper, ownership, lifecycle, and recent failures.
2. Serialize to deterministic standard JSON with stable field shapes and ordering suitable for repeatable tests and comparison artifacts.
3. Deserialize through strict type and required-field validation; reject unknown schema versions with a normalized, explicit incompatible-schema result rather than guessing or silently coercing.
4. Bound envelope size-sensitive collections, especially recent failures and diagnostic/event histories, according to named constants covered by tests.
5. Allowlist backend-private evidence and diagnostic keys at their owning boundaries and redact prohibited secrets and personal data before string formatting or serialization.
6. Preserve immutable collection semantics after decoding so caller-owned dictionaries or lists cannot mutate an accepted envelope.
7. Do not alter the separate backend settings schema, existing content/rendering payloads, or `BackendSelectionStatus.to_payload()` in this task.
8. Add unit tests for deterministic round trips, malformed inputs, unknown versions, collection bounds, immutable decoded state, and redaction of adversarial fixtures.

## Dependencies
- Step 1 Task 1's converged enums and immutable status models.
- Existing JSON transport conventions may be reused only where they do not weaken the design's schema, size, privacy, or incompatibility rules.
- Production migration of every producer and consumer is deferred to implementation Step 20.

## Implementation Approach
1. Build the schema-v1 envelope from the Task 1 models using explicit encoder/decoder functions and narrow validation helpers.
2. Centralize version, history-size, and diagnostic allowlist policies as named constants rather than scattering implicit limits.
3. Copy and freeze accepted nested values at the model boundary, then serialize only normalized primitives.
4. Add positive and adversarial unit fixtures covering every top-level section and the documented privacy exclusions.

## Acceptance Criteria

1. **Deterministic Schema-V1 Round Trip**
   - Given a complete representative schema-version-1 backend envelope
   - When it is serialized, deserialized, and serialized again
   - Then the normalized JSON output is deterministic and the decoded value is equivalent and immutable

2. **Explicit Version Failure**
   - Given an envelope with an unknown, missing, stale, or invalid schema version
   - When deserialization is attempted
   - Then it fails safely with a clear incompatible-schema result and never interprets the payload as version 1

3. **Bounded Status History**
   - Given more normalized failures or diagnostic entries than the configured bound
   - When an envelope is constructed or decoded
   - Then the retained history follows the documented deterministic bound and the serialized envelope cannot grow without limit

4. **Pre-Serialization Privacy Enforcement**
   - Given diagnostics containing tokens, raw owner IDs, target handles, arbitrary titles, command lines, exception payloads, or personal paths
   - When they cross the codec boundary
   - Then prohibited data is removed or replaced with the constant redaction marker before formatting and cannot appear in serialized JSON

5. **Payload Compatibility Boundary**
   - Given existing backend-status, content, layout, rendering, and settings payload producers
   - When the new codec is added
   - Then their current output and consumers remain unchanged and no production consumer reads the new envelope for behavior

6. **Unit Regression Coverage**
   - Given valid, malformed, oversized, and secret-bearing fixtures
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_status.py overlay_client/tests/test_backend_control_plane.py -q` is run
   - Then all codec and transitional status tests pass

## Metadata
- **Complexity**: High
- **Labels**: fix219, backend, schema-v1, serialization, privacy, unit-tests, phase-1
- **Required Skills**: Python serialization, schema validation, immutable data structures, privacy-safe diagnostics, pytest
