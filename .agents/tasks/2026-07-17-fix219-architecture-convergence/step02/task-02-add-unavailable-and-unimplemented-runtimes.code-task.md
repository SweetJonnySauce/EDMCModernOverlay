# Task: Add Unavailable and Unimplemented Runtimes

## Description
Implement generic unavailable and unimplemented backend runtimes that satisfy the new lifecycle, component, result, and status contracts. These runtimes provide truthful fail-closed representations for construction failures and detected placeholders without constructing a presenter or leaking backend-private behavior.

## Background
The detailed design forbids selection and construction from drifting apart and rejects `None` or nominal shared-Wayland fallbacks for known failures. Before the registry is introduced, Phase 1 needs deterministic runtime implementations that retain the selected identity, expose stable inert services, report normalized reasons, and clean up safely regardless of start state.

## Reference Documentation
**Required:**
- Design: docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/planning/2026-07-17-fix219-architecture-convergence/research/backend-contracts-and-control-plane.md (placeholder selection and generic boundary rules)
- docs/planning/2026-07-17-fix219-architecture-convergence/research/contract-tests-and-migration.md (lifecycle and unsupported-fallback contracts)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Implement an unavailable runtime for a known selected identity whose construction prerequisite failed and an unimplemented runtime for a detected environment with no backend implementation.
2. Return the same immutable identity and stable owned discovery, presentation, and input service instances for the runtime lifetime.
3. Make start behavior deterministic, prevent visible presentation, return normalized unavailable or rejected results, and expose support/evidence/health without collapsing those axes.
4. Make stop safe before, during, or after start, idempotent on repetition, terminal after completion, and able to report bounded sanitized cleanup failures.
5. Ensure unavailable GNOME-style restart-required failures can be represented distinctly from live-recoverable post-start health loss without embedding GNOME-specific code.
6. Ensure unimplemented environments never construct or delegate to transitional shared Wayland presentation.
7. Use the Step 1 schema serializer for status snapshots and prohibit secret/private diagnostic content.
8. Add unit tests for lifecycle permutations, stable components, identity/status equality, hidden presentation, unsupported fallback prevention, revision stability, and sanitization.

## Dependencies
- Step 2 Task 1's behavioral runtime and service protocols.
- Step 1's identity, status-axis, result, failure, recovery, and schema-v1 models.
- Registry construction results are not added until Step 4; these implementations must remain directly constructible for tests.

## Implementation Approach
1. Create small inert service implementations that satisfy discovery, presentation, and input contracts with explicit unavailable or unimplemented results.
2. Compose them into lifecycle-safe runtimes sharing a narrow generic base only where behavior is truly identical.
3. Model restart-required versus terminal/unimplemented recovery explicitly in status and operation results.
4. Exercise every start/stop ordering with injected failures and verify no concrete backend or GUI dependency is imported.

## Acceptance Criteria

1. **Selected Identity Is Preserved**
   - Given a known backend construction failure or a detected unimplemented environment
   - When the corresponding runtime and serialized status are inspected
   - Then runtime identity, selected identity, and status identity match exactly

2. **Fail-Closed Presentation**
   - Given an unavailable or unimplemented runtime
   - When presentation is requested
   - Then no surface is shown, no fallback presenter is constructed, and a normalized unavailable or rejected result explains recovery

3. **Stable Inert Components**
   - Given repeated access to discovery, presentation, and input services
   - When the runtime is not startable or implementable
   - Then access returns stable owned instances with independent interfaces and deterministic snapshots

4. **Idempotent Terminal Cleanup**
   - Given stop before start, stop after a failed start, or repeated stop calls
   - When cleanup executes
   - Then it completes within the injected bound, continues past individual cleanup failures, and never resumes the stopped runtime

5. **Truthful Independent Status**
   - Given a supported identity with a missing prerequisite and an unimplemented identity
   - When schema-v1 status is serialized
   - Then the former can remain supported but unavailable/restart-required while the latter is unimplemented and unavailable

6. **Unit Contract Coverage**
   - Given the unavailable and unimplemented runtime factories used by focused tests
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_contracts.py overlay_client/tests/test_backend_runtime_contracts.py -q` is run
   - Then lifecycle, status, sanitization, and no-fallback assertions pass

## Metadata
- **Complexity**: Medium
- **Labels**: fix219, backend-runtime, unavailable, unimplemented, fail-closed, unit-tests, phase-1
- **Required Skills**: Python lifecycle modeling, interface implementation, error normalization, pytest
