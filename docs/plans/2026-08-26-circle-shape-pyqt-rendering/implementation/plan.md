# Circle Shape Support: Implementation Plan

## Checklist

- [x] Step 1: Add the backward-compatible circle payload contract and unit coverage.
- [x] Step 2: Normalize, validate, and store circles without disrupting existing shapes.
- [x] Step 3: Add PyQt circle paint-command rendering and transform integration.
- [x] Step 4: Prove raw/TCP lifecycle wiring and update public documentation.
- [x] Step 5: Run the full release-quality regression gate and record results.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Public contract and compatibility API | Completed |
| 2 | Client normalization and storage | Completed |
| 3 | Transform and PyQt rendering | Completed |
| 4 | Harness wiring and documentation | Completed |
| 5 | Regression validation | Completed |

## Phase Details

### Phase 1: Public contract and compatibility API

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add a circle form without changing positional rectangle callers | Completed |
| 1.2 | Lock the emitted payload shape with unit tests | Completed |

### Step 1: Add the backward-compatible circle payload contract and unit coverage

**Objective:** Extend the legacy `Overlay.send_shape` helper to publish a `shape="circle"` payload with stable ID, centre coordinates, radius, thickness, colour, fill, and TTL, while preserving every current rectangle call.

**Implementation guidance:**

- Keep `shapeid` and `shape` as the first two arguments.
- Preserve the current positional rectangle form exactly.
- Permit the circle form with named `x`, `y`, `radius`, `thickness`, `color`, `fill`, and `ttl` arguments; do not manufacture `w` or `h` for circle payloads.
- Preserve the existing publisher/unavailable-warning behavior.
- Do not add rendering logic in this step.

**Test requirements:**

- Add focused compatibility-helper unit tests for the exact circle wire payload.
- Add a regression test proving an existing positional rectangle call still emits its current payload unchanged.
- Add a test that circle calls retain a stable ID and TTL as passed.

**Integration:** This step creates the sole public producer of canonical circle payloads. Step 2 will make the client accept these payloads.

**Demo:** A small test-double publisher receives a `LegacyOverlay` payload containing `shape: "circle"`, centre `x/y`, `radius`, `thickness`, border `color`, `fill`, and `ttl`; an existing rectangle test continues to pass.

**Commands:**

```bash
overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py -q
overlay_client/.venv/bin/python -m pytest tests -k 'send_shape or legacy' -q
```

### Phase 2: Client normalization and storage

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Preserve circle fields through raw payload normalization | Completed |
| 2.2 | Validate and store circles as a first-class legacy item | Completed |

### Step 2: Normalize, validate, and store circles without disrupting existing shapes

**Objective:** Make the client accept valid circles from all legacy sources and drop invalid geometry with an actionable warning before store mutation.

**Implementation guidance:**

- Extend raw legacy normalization to retain `radius` and `thickness` for `shape="circle"`.
- Add a circle branch to the centralized legacy processor before the unknown-shape fallback.
- Coerce circle geometry consistently, then require strictly positive `radius` and `thickness`.
- On invalid geometry, log the ID and invalid field/value, return the no-repaint result, and leave a same-ID stored item untouched.
- Store valid data under a dedicated `circle` kind with all visual fields, TTL, transform metadata, timestamp, and plugin attribution.
- Extend the deduplication snapshot so radius, thickness, colour, fill, centre, and transform changes are visible.

**Test requirements:**

- Add unit tests for valid circle storage, transparent/default fill, replacement by ID, and TTL behavior.
- Add parameterized invalid-radius and invalid-thickness tests that assert warning output, no store mutation, and no repaint.
- Add raw-normalization coverage for circle fields and preserve rectangle/vector regression cases.

**Integration:** This step consumes Step 1’s wire payload and produces a renderable client item for Step 3.

**Demo:** A valid circle payload appears as a `circle` item in the legacy store; an invalid update is warned and the previous circle remains unchanged.

**Commands:**

```bash
overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py -q
overlay_client/.venv/bin/python -m pytest -k 'legacy_processor or legacy_tcp' -q
```

### Phase 3: Transform and PyQt rendering

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add an opacity-aware circle paint command | Completed |
| 3.2 | Reuse existing shape transforms and render dispatch | Completed |

### Step 3: Add PyQt circle paint-command rendering and transform integration

**Objective:** Render stored circles through PyQt while inheriting all existing group, viewport, opacity, anchor, and cycle-target behavior.

**Implementation guidance:**

- Add a dedicated circle paint command beside the rectangle command.
- Apply the same defensive pen/brush copy and payload-opacity behavior used by rectangles.
- Call `QPainter.drawEllipse` with the transformed bounding rectangle.
- Add render-surface dispatch for the `circle` item kind.
- Derive the logical square from centre/radius and use the current rectangle-transform machinery; do not fork group/Fill/anchor math.
- Build the pen from the requested thickness, use the existing no-pen behavior for missing/invalid border colour, and retain transparent-fill handling.
- Report transformed square bounds and its centre for group layout and cycle targeting.

**Test requirements:**

- Extend the recording painter with precise ellipse assertions.
- Add paint-command unit tests for transformed offsets, pen width, fill, transparent fill, and global opacity.
- Add render-surface integration tests for dispatch, mapped bounds, group anchoring, and cycle-anchor placement.
- Preserve existing rectangle and vector tests as regressions.

**Integration:** This step makes Step 2’s client item visually functional using PyQt without changing any existing primitive.

**Demo:** A recording PyQt painter receives `drawEllipse` with the expected mapped bounding square and the requested pen/brush; a running dev overlay displays a correctly placed, filled and outlined circle.

**Commands:**

```bash
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_paint_commands.py overlay_client/tests/test_render_surface_mixin.py -q
PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest -k 'paint_commands or render_surface' -q
```

### Phase 4: Harness wiring and documentation

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Prove raw/TCP circle publication through the EDMC harness | Completed |
| 4.2 | Update public shape and rendering documentation | Completed |

### Step 4: Prove raw/TCP lifecycle wiring and update public documentation

**Objective:** Verify the runtime ingestion seam and make the public API discoverable and unambiguous.

**Implementation guidance:**

- Add an EDMC harness test that sends a raw/TCP circle and checks the published `LegacyOverlay` payload retains all circle fields.
- Add an invalid-geometry harness/replay assertion at the appropriate layer to ensure invalid circles never become drawable items.
- Update the shape API reference with circle signature, centre coordinates, radius/thickness validation, colours/fill, TTL, and stable-ID replacement behavior.
- Update raw API, getting-started, FAQ/concepts, and rendering-pipeline material to state that circles are supported and rendered by PyQt.
- Document that a circle follows the same legacy viewport mapping as other shapes and can appear elliptical if a mode applies non-uniform mapping.

**Test requirements:**

- Mark all hook/lifecycle coverage as `harness` and use the existing runtime fixture pattern.
- Add a documentation example that matches the tested public API exactly.

**Integration:** This step proves the feature works beyond the direct helper and aligns user documentation with the shipped behavior.

**Demo:** A harness-driven raw circle travels through runtime publication, and the documentation provides a copyable, tested plugin example.

**Commands:**

```bash
overlay_client/.venv/bin/python -m pytest -m harness tests/test_harness_legacy_tcp_ingestion.py -q
overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py overlay_client/tests/test_paint_commands.py -q
```

### Phase 5: Regression validation

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Run focused, headless, and GUI-enabled checks | Completed |
| 5.2 | Record outcomes and release/compliance evidence | Completed |

### Step 5: Run the full release-quality regression gate and record results

**Objective:** Demonstrate that the new primitive is wired end-to-end and no legacy shape behavior regressed.

**Implementation guidance:**

- Run focused tests after each prior step; repair failures before proceeding.
- Run the required Python baseline check before release evaluation.
- Run lint, type checks, complete PyQt-enabled tests, and the full project check.
- Record exact commands, pass/fail outcomes, skips, and environment limitations in the implementation results section of this plan.
- Update every completed stage and phase status as work lands.

**Test requirements:**

- No failing focused, harness, lint, type-check, or GUI-enabled suite may be waived without an explicit, documented reason and user approval.
- Verify existing rectangle, vector marker, and raw/TCP test suites continue to pass.

**Integration:** This is the release-quality proof for Steps 1–4; it changes no product behavior.

**Demo:** `make check` completes successfully and the implementation record contains reproducible evidence for the complete circle flow.

**Commands:**

```bash
overlay_client/.venv/bin/python scripts/check_edmc_python.py
overlay_client/.venv/bin/python -m pytest
make check
```

## Implementation Results

### Step 1

- Completed `Overlay.send_shape` circle payload support without altering the positional rectangle payload branch. Added unit coverage for the exact circle event, stable ID/TTL pass-through, and positional rectangle compatibility.
- Fixed the pre-existing `tests/test_legacy_processor.py` collection path shadowing so the required plan command imports the actual `overlay_client` package; this is test-only and does not change production behavior.
- Validation: `overlay_client/.venv/bin/python -m pytest tests/test_edmcoverlay_shapes.py -q` — 3 passed; `overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py -q` — 8 passed; `overlay_client/.venv/bin/python -m pytest tests -k 'send_shape or legacy' -q` — 28 passed, 370 deselected; `overlay_client/.venv/bin/python -m ruff check EDMCOverlay/edmcoverlay.py tests/test_edmcoverlay_shapes.py` — passed.

### Step 2

- Completed unit-tested raw circle geometry preservation, and centralized first-class circle validation, storage, TTL/replacement, transform/plugin propagation, warning/no-mutation behavior, and dedupe snapshot coverage.
- Validation: `overlay_client/.venv/bin/python -m pytest tests/test_edmcoverlay_shapes.py -q` — 8 passed; `overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py -q` — 27 passed; `overlay_client/.venv/bin/python -m pytest -k 'legacy_processor or legacy_tcp' -q` — 30 passed, 6 expected PyQt skips, 710 deselected; relevant Ruff checks and `git diff --check` passed.

### Step 3

- Completed an opacity-safe `_CirclePaintCommand` using only bounded `QPainter.drawEllipse`, plus circle dispatch and a shared bounded-shape transform path. Circles derive `centre ± radius` bounds and retain group, viewport, anchor, cycle, opacity, fill, and requested-stroke-width behavior.
- Validation: `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_paint_commands.py -q` — 9 passed; `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_paint_commands.py overlay_client/tests/test_render_surface_mixin.py -q` — 25 passed; `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest -k 'paint_commands or render_surface' -q` — 25 passed, 746 deselected; relevant Ruff checks and `git diff --check` passed.
- Demo: not run. The active X11 session has no isolated documented circle-demo launcher; an unscoped live-client capture could expose desktop/overlay content. No screenshot was created.

### Step 4

- Added mixed coverage: the fake EDMC harness proves raw/TCP circle publication retains canonical fields; a unit replay proves invalid raw-normalized geometry cannot replace a drawable same-ID circle. No live EDMC or socket was used.
- Updated the shape/raw API references, Getting Started, Concepts, FAQs, and rendering pipeline. Examples match the test fixtures and distinguish `shape="circle"` from vector circle markers.
- Validation: `overlay_client/.venv/bin/python -m pytest -m harness tests/test_harness_legacy_tcp_ingestion.py -q` — 4 passed; `overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py overlay_client/tests/test_paint_commands.py -q` — 44 passed; relevant Ruff checks and `git diff --check` passed.

### Step 5

- Final evidence: `overlay_client/.venv/bin/python scripts/check_edmc_python.py` — passed (Python 3.12.3 64-bit meets the configured >=3.10.3 floor; checker warns that 32-bit is the preferred EDMC baseline); focused helper/processor — 43 passed; harness — 4 passed; focused PyQt paint/render — 25 passed; headless suite — 724 passed, 39 expected PyQt skips; GUI suite — 759 passed, 21 skipped; `make lint`, `make typecheck`, and `make check` — all passed (`make check`: 759 passed, 21 skipped).
- Final scoped diff, documentation-contract, EDMC compliance, and secure metadata-only credential review found no local release-blocking defect. The potential generic token-pattern match was triaged without exposing content and cleared as ordinary terminology/identifiers.
- Manual release checks remain: verify in the actual Python 3.10.3 32-bit Windows EDMC runtime and check EDMC Releases/Discussions for plugin-impacting changes before shipping. No version, package, release, external action, commit, or push was performed.
