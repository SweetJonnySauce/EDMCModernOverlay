# Step 04 Task 02 Progress

## Setup

- [x] Restart protocol completed: governing artifacts, status dashboard, task
  artifacts/records, status/diff checks, and Task 01 validation evidence were
  reconciled.
- [x] Writable task-record and `logs/` directories created under
  `implementation/task-records/step04-task02`.
- [x] Instruction discovery completed; no `CODEASSIST.md` exists.
- [x] Test type selected before edits: no new automated test type; this is
  documentation-only work with manual example-to-test comparison.

## Phase tracking

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 4 | 4.2 | Update public shape and rendering documentation | Completed (Task 02) |

Phase 4 Task 02 status: **Completed (Task 02 scope)**. The orchestration context owns
independent review and approved plan/dashboard updates.

## Review evidence

- Task 01 accepted mixed evidence is available for reuse: `overlay_client/.venv/bin/python -m pytest -m harness tests/test_harness_legacy_tcp_ingestion.py -q` -> `4 passed in 0.14s`; `overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py overlay_client/tests/test_paint_commands.py -q` -> `44 passed in 0.17s`.
- Before editing, the exact helper fixture and Task 01 raw/TCP capture confirm
  the canonical values: ID `myplugin-radius`, `shape="circle"`, `color="#80d0ff"`,
  `fill="#1a1a1acc"`, centre `x=100`, `y=100`, `radius=50`, `thickness=2`, and
  `ttl=5`, without `w`/`h`.

## TDD applicability

RED -> GREEN -> REFACTOR does not apply to this task because it adds no
executable behavior or test. The documentation review uses the existing exact
fixture and accepted lifecycle evidence as the contract before and after the
edits.

## Documentation implementation and validation

- [x] Updated `send_shape-API.md` with the preserved positional rectangle form,
  a keyword circle form, the exact Step 1 helper example/payload, stable-ID
  replacement/clear and TTL behaviour, transparent fill, requested border,
  centre geometry, and client-side invalid-geometry warning/drop behaviour.
- [x] Updated `send_raw-API.md` with the Task 01 raw/TCP circle fields and the
  normalization-versus-client-validation boundary.
- [x] Added the matching first-use circle example and explicit vector-marker
  distinction to `Getting-Started.md`; added scoped primitive support statements
  to `Concepts.md` and `FAQs.md`.
- [x] Updated `rendering-pipeline.md` with circle storage, centre-plus/minus
  radius bounds, existing mapping, bounded `QPainter.drawEllipse`, pen/fill/
  opacity, and intended non-uniform mapped ellipse behaviour. No
  `paint:circle_*` trace stage was claimed.

### Manual example-to-test comparison

| Documentation example/claim | Compared evidence | Result |
| --- | --- | --- |
| `send_shape` code and emitted JSON | `tests/test_edmcoverlay_shapes.py::test_send_shape_emits_exact_circle_payload` | Exact stable ID, shape, color, fill, centre, radius, thickness, TTL, and no `w`/`h`. |
| Getting Started circle code | Same exact helper fixture | Exact field names, values, and centre semantics. |
| `send_raw` circle JSON | `tests/test_harness_legacy_tcp_ingestion.py::test_legacy_tcp_raw_circle_preserves_canonical_fields_through_publication` | Exact Task 01 raw/TCP ID, shape, color, fill, centre, radius, thickness, TTL, and plugin fields. |
| Validation and rendering prose | Task 01 processor assertion plus Step 3 paint/render evidence | Client drops invalid geometry before same-ID mutation; bounded ellipse uses the shared mapping and can be elliptical after non-uniform mapping. |

### Validation evidence

- Reused unchanged accepted Task 01 command evidence; product/tests did not
  change in this task, so the commands were not rerun:
  - `overlay_client/.venv/bin/python -m pytest -m harness tests/test_harness_legacy_tcp_ingestion.py -q` -> `4 passed in 0.14s`.
  - `overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py overlay_client/tests/test_paint_commands.py -q` -> `44 passed in 0.17s`.
- Local documentation review: stale rectangle-only/support-list scan found no
  remaining targeted claims in the six touched pages.
- `git diff --check` -> passed after removing one introduced trailing-space
  issue.
- Scoped credential scan -> no secrets found; the word `token` appears only in
  the public API phrase “shape token.”

## Residual risk and commit status

Residual risk: Markdown examples and prose are not executable, so future API
changes can reintroduce copy drift. The exact fixture and Task 01 evidence now
anchor all newly added circle examples; no test or product risk was introduced.

Commit status: deferred. This task must neither commit nor push while the
approved multi-step plan remains unfinished.
