# Task: Add Shadow Status Adapter

## Description
Add a developer-only adapter that translates the current `BackendSelectionStatus` into a schema-version-1 backend control-plane snapshot for diagnostic comparison. The adapter must conservatively expose independent support, evidence, and health dimensions while leaving the shipped selector, status payload, settings, presentation, and generic consumer behavior unchanged.

## Background
Steps 4 and 20 need a comparison artifact that shows how transitional backend selection maps into the converged schema before the new envelope controls behavior. The current status model combines classifications, fallbacks, helper observations, and internal identities, so the shadow mapping must be explicit, deterministic, privacy-safe, and incapable of becoming an accidental production dispatch input.

## Reference Documentation
**Required:**
- Design: docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/planning/2026-07-17-fix219-architecture-convergence/research/backend-contracts-and-control-plane.md (three-dimensional status and staged schema migration)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Implement a pure adapter from current `BackendSelectionStatus` plus explicit producer/evidence inputs to the schema-version-1 envelope, and keep its developer-only revision tracker as a small injected producer concern.
2. Map support policy, validation evidence, and live health independently and conservatively; do not infer validation claims solely from a compositor label, current health, or the transitional true/degraded classification.
3. Represent GNOME Wayland, native X11, XWayland compatibility, and detected unimplemented environments using the detailed design's stable converged identities in shadow output only.
4. Normalize helper and fallback information without exposing private D-Bus actions, tokens, target handles, or using an opaque presenter label as behavior dispatch.
5. Gate production of comparison output behind the existing developer/diagnostic mechanism or an equally cheap process-start developer toggle, with a no-op release path.
6. Preserve `BackendSelectionStatus.to_payload()`, current status messages, content/settings payloads, selector decisions, bundle resolution, and all presentation behavior.
7. Extend `test_backend_status.py` and the focused control-plane tests with representative GNOME, native-X11, XWayland, and unimplemented fixtures plus unchanged/change/decrease revision behavior and redaction assertions.

## Dependencies
- Step 1 Tasks 1 and 2 provide the normalized models and schema-version-1 codec.
- The transitional `BackendSelectionStatus` remains the only production status input during this step.
- The resulting comparison artifact is consumed by implementation Steps 4 and 20, not by generic behavior in Phase 1.

## Implementation Approach
1. Write a table-driven mapping specification from transitional fields to each independent schema-v1 dimension, documenting conservative defaults where the old model lacks evidence.
2. Implement the adapter as a pure function and serialize its result only through the Task 2 codec.
3. Add representative fixtures that demonstrate the required support/evidence/health combinations and prove the old payload remains byte-for-byte behaviorally equivalent.
4. Verify the adapter has no imports from compositor-private presentation modules and no production consumer uses its output for dispatch.

## Acceptance Criteria

1. **Independent Shadow Dimensions**
   - Given transitional fixtures for supported-but-unavailable GNOME, validated native X11, degraded XWayland, and unimplemented Wayland
   - When the shadow adapter produces schema-version-1 snapshots
   - Then support policy, evidence level, and runtime health are represented independently and truthfully for each fixture

2. **Conservative Missing Evidence**
   - Given a current status that identifies an environment but contains no reviewed validation record
   - When it is adapted
   - Then the snapshot reports the approved unknown or not-yet-reported evidence state instead of manufacturing a support claim

3. **Monotonic Shadow Revisions**
   - Given two equivalent shadow snapshots followed by a user-visible status change
   - When the developer-only shadow producer emits them within one process
   - Then equivalent snapshots retain their revision, the changed snapshot receives a higher revision, and no emitted revision decreases

4. **Production Behavior Remains Unchanged**
   - Given shadow output is enabled or disabled
   - When current selection, bundle resolution, status publishing, content/settings handling, and presentation execute
   - Then their decisions and existing payloads are unchanged and no generic consumer dispatches on the new envelope

5. **Developer-Only Cheap Path**
   - Given a normal release configuration
   - When backend status changes
   - Then shadow comparison work is absent or a documented cheap no-op and detailed output is emitted only in developer/diagnostic mode

6. **Representative Step Demo**
   - Given GNOME, native-X11, XWayland, and unimplemented inputs
   - When their shadow snapshots are serialized
   - Then each schema-version-1 artifact clearly shows selected identity, support, evidence, health, probes, and bounded failures while the shipped runtime path remains active

7. **Targeted Validation**
   - Given the completed Step 1 implementation
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_status.py overlay_client/tests/test_backend_control_plane.py -q` and `git diff --check` are run
   - Then both commands pass and transitional assertions have not been removed

## Metadata
- **Complexity**: Medium
- **Labels**: fix219, backend, shadow-mode, status-adapter, migration, unit-tests, phase-1
- **Required Skills**: Python data transformation, compatibility-preserving refactoring, backend status modeling, pytest
