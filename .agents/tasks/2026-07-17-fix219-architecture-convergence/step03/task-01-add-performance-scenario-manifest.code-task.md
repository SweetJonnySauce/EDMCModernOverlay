# Task: Add Performance Scenario Manifest

## Description
Add a versioned, machine-validated scenario manifest for the required pre-migration GNOME performance baseline. The manifest must fix environment metadata, payload fixture, diagnostic configuration, display geometry, scale, warm-up, duration, repetitions, transitions, monitor handoffs, Alt-Tab, and Overview so later candidate captures remain comparable.

## Background
The project already records raster, helper, transition, repaint, and CPU diagnostics, but it lacks a repeatable scenario definition. The baseline must be captured on the shipped architecture before Step 5 changes production routing. A strict manifest prevents accidental comparison of different display layouts, fixtures, clock domains, or diagnostic settings and makes deferred or incomplete manual evidence visible.

## Reference Documentation
**Required:**
- Design: docs/planning/2026-07-17-fix219-architecture-convergence/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/planning/2026-07-17-fix219-architecture-convergence/research/performance-baseline.md (existing instrumentation, required scenarios, measures, and artifact recommendations)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Define a versioned standard-JSON manifest schema and pure loader/validator for pre-migration and candidate performance scenarios.
2. Require environment and version metadata, uniform scale, horizontal display geometry, negative-coordinate coverage, fixed payload fixture, diagnostic toggles, warm-up, observation duration, repetition count, and expected clock domains.
3. Enumerate stable windowed, stable borderless fullscreen, both mode-transition directions on each monitor, fullscreen handoffs A-to-B and B-to-A, and Alt-Tab/Overview interactions at uniform 100% and 125% scale.
4. Represent unsupported or deferred mixed-scale, vertical-layout, primary-monitor-change, and exclusive-fullscreen cases explicitly without adding them to the acceptance gate.
5. Validate positive durations/counts, stable unique scenario IDs, required bidirectional coverage, supported schema versions, and references to known payload/diagnostic configurations.
6. Reject or redact secrets, personal paths, arbitrary window titles, command lines, raw owner IDs, target handles, and broad environment dumps from manifest metadata.
7. Keep the manifest and validator independent of Qt, Tk, compositor APIs, and production routing.
8. Add unit tests for valid manifests, missing scenarios, invalid geometry/scale/timing, duplicate IDs, unknown versions, and privacy rejection.

## Dependencies
- Existing raster/helper/transition/repaint diagnostic toggles remain the data sources; this task does not replace their instrumentation.
- The detailed design's Manual Support Matrix and Performance Gate define mandatory coverage.
- The summary tooling in Step 3 Task 2 consumes only manifests accepted by this validator.

## Implementation Approach
1. Model the smallest JSON schema needed to fix comparison inputs and link scenario IDs to existing diagnostic sources.
2. Implement a pure parser and explicit validation errors with no automatic correction of incompatible captures.
3. Add the initial GNOME 46/Ubuntu 24.04.4 baseline manifest covering both scales and all required scenarios.
4. Test validation and privacy behavior using synthetic fixtures before any manual capture begins.

## Acceptance Criteria

1. **Complete Required Scenario Matrix**
   - Given the committed baseline manifest
   - When it is validated
   - Then it contains stable windowed/fullscreen states, both transition directions, both monitor handoffs, Alt-Tab, and Overview at 100% and 125% with a negative-coordinate arrangement

2. **Repeatable Capture Inputs**
   - Given baseline and candidate runs using the same manifest
   - When their metadata is compared
   - Then payload fixture, display geometry, diagnostic toggles, warm-up, duration, repetitions, scale, and environment identifiers are fixed and machine-checkable

3. **Unsupported Scope Is Explicit**
   - Given mixed scale, vertical displays, primary-monitor changes, or exclusive fullscreen
   - When the manifest's scope is inspected
   - Then those cases are identified as outside the gate and are not silently implied supported

4. **Manifest Privacy Boundary**
   - Given metadata containing a token, personal path, title, command line, raw owner ID, target handle, or broad environment value
   - When validation runs
   - Then the manifest is rejected or safely redacted before an evidence artifact can be written

5. **Pure Unit Validation**
   - Given valid and adversarial manifest fixtures
   - When `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_performance_summary.py tests/test_debug_collectors.py -q` is run
   - Then schema, coverage, timing, geometry, and privacy assertions pass without GUI or EDMC lifecycle wiring

## Metadata
- **Complexity**: Medium
- **Labels**: fix219, performance, scenario-manifest, validation, privacy, unit-tests, phase-1
- **Required Skills**: Python JSON validation, test-fixture design, performance methodology, pytest
