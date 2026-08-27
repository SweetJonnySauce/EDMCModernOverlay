# Task: Run Release-Quality Circle Regression Review

## Description
Perform the final release-quality validation and read-only review for the completed circle-shape work. Establish reproducible evidence that the compatibility payload, raw/TCP lifecycle, client validation/storage, PyQt ellipse rendering, and existing rectangle/vector behavior remain healthy. This task must not change product behavior, update version/package/release metadata, publish anything, or push.

## Background
Steps 1–4 have completed the circle payload contract, raw normalization and authoritative validation, transform-aware `QPainter.drawEllipse` rendering, EDMC harness coverage, and public documentation. Step 5 is the release gate for that accumulated scoped diff. The approved plan requires the EDMC plugin-runtime Python baseline check before release evaluation; focused tests before broad tests; a GUI-enabled PyQt suite; lint, type checking, and `make check`; and reproducible recording of exact commands, outcomes, skips, and environment limitations. Existing implementation evidence includes the focused compatibility, processor, paint/render, and harness commands, but the final gate must rerun the prescribed release-quality checks against the final combined workspace state.

## Reference Documentation
**Required:**
- Design: docs/plans/2026-08-26-circle-shape-pyqt-rendering/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/plan.md (Step 5, Phase 5 stages, and required commands)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/orchestration-prompt.md (restart, stop, validation, evidence, and no-release protocols)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/research/payload-and-rendering.md (legacy contract and regression surfaces)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step01/task-01-add-circle-compatibility-payload-contract.code-task.md (payload/rectangle compatibility evidence)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step02/task-02-validate-and-store-circle-items.code-task.md (validation, no-mutation, and dedupe evidence)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step03/task-01-add-opacity-aware-circle-paint-command.code-task.md and docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step03/task-02-add-circle-transform-and-render-dispatch.code-task.md (PyQt regression surfaces)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step04/task-01-prove-raw-tcp-circle-lifecycle.code-task.md (harness lifecycle evidence)
- AGENTS.md (EDMC compliance checklist, test policy, and required final evidence)
- Makefile and pyproject.toml (authoritative lint, type-check, and GUI test targets)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. **Test type selected before edits: validation/review only, using the already-required unit, harness, and GUI integration suites.** This task changes no pure helper or EDMC lifecycle code and therefore adds no tests. It must execute the existing unit tests for deterministic contracts, the marked harness test for raw/TCP runtime wiring, and PyQt-enabled integration tests for production drawing. Document this choice and the remaining environment risk in the task record.
2. Before commands, perform the orchestration restart checks for this task: reread the governing artifacts; reconcile `execution-status.md`, plan Step 5, prior task artifacts/records, `git status --short`, `git diff --check`, and available command evidence. Do not alter the approved plan or dashboard from this context. Do not overwrite any task artifact or task record.
3. Run the EDMC Python baseline command exactly before release evaluation: `overlay_client/.venv/bin/python scripts/check_edmc_python.py`. Do not use `ALLOW_EDMC_PYTHON_MISMATCH=1` for this release gate. If it fails because this non-Windows host cannot satisfy the documented 3.10.3 32-bit runtime baseline, capture the exact result as a blocker for main-thread review; do not misreport it as passing.
4. Run focused regression tests before broader tests, capturing exact command text and result for each. The focused evidence must cover (a) compatibility helper and positional rectangle behavior, (b) centralized legacy processing including invalid geometry/no-mutation, (c) raw/TCP harness lifecycle, and (d) PyQt paint/render integration. Use these commands in this order where the environment permits:
   - `overlay_client/.venv/bin/python -m pytest tests/test_edmcoverlay_shapes.py tests/test_legacy_processor.py -q`
   - `overlay_client/.venv/bin/python -m pytest -m harness tests/test_harness_legacy_tcp_ingestion.py -q`
   - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_paint_commands.py overlay_client/tests/test_render_surface_mixin.py -q`
5. Run expanded headless and GUI-enabled suite evidence after focused checks, recording pass/fail/skips and their reasons without waiving failures:
   - `overlay_client/.venv/bin/python -m pytest`
   - `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest`
   The GUI-enabled command is required even when focused PyQt tests pass. Treat expected PyQt marker skips in the headless command as skips, not passes; record their count/reason. On Windows Python 3.13+ only, use the documented safe pytest launcher if `tmp_path` fails with `WinError 5`; do not use that Windows-only workaround on this host.
6. Run the release-quality static/build commands after test evidence: `make lint`, `make typecheck`, and `make check`. `make check` is the required final command from the approved plan and must not be substituted with a narrower command. Do not rerun an unchanged failing command more than once; capture its output and stop for the orchestration/main-thread review if a permitted remediation cannot resolve it.
7. Conduct a scoped, read-only release review after validations: run `git diff --check`; inspect `git status --short` and the scoped diff; confirm circle-only behavior changes are limited to the intended compatibility, normalizer/processor, render, tests, harness, and documentation surfaces; and verify no unintended rectangle, vector, global render-hint, API, version, packaging, or release changes appear. Check documentation examples against the tested canonical circle contract: stable ID, `shape="circle"`, centre `x`/`y`, positive `radius`/`thickness`, `color`, `fill`, and `ttl`, with no circle `w`/`h`.
8. Complete the applicable EDMC compliance review with an explicit yes/no result and corrective action for every `AGENTS.md` compliance item: supported Python baseline; plugin directory/`load.py`/`plugin_start3`; supported API/helpers and EDMC config persistence; logger/versioning; worker-thread/Tk safety; prefs/UI-hook safety; dependency/importability/debug-HTTP practices; and release/discussion-monitoring status. Inspect changed plugin code only; do not access the network, subscribe to releases/discussions, use credentials, or change configuration. Record any item that cannot be proven from the workspace as `No — external/manual verification required`.
9. Scan the scoped changed text, task records, validation logs, and any screenshots for credentials/secrets before handoff. Use local, read-only search only. Record the scan scope and result, but do not print or propagate any possible secret; stop and escalate through the main thread if one is found.
10. Record the selected test types, exact command text, exit status/outcome, pass/fail/skip counts, failure output location or concise reason, environment limitation, diff/compliance/secret-review outcomes, and residual risk in `docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step05-task01/progress.md`. Do not update source code, tests, documentation, the approved plan, execution dashboard, versions, packages, release artifacts, or Git history. Do not push or perform any external action.

## Dependencies
- Accepted Steps 1–4 implementation and test/doc artifacts must remain present and unmodified by this task.
- `overlay_client/.venv/bin/python` must provide pytest, Ruff, mypy, and PyQt dependencies used by the documented commands.
- The Makefile defines the final `lint`, `typecheck`, `test`, and `check` targets; `make check` runs lint, type checking, and a GUI-enabled pytest suite.
- The main orchestration thread owns plan/dashboard stage completion, final report, remediation authorization, and any stop-protocol escalation.

## Implementation Approach
1. Reconcile the final candidate state and prior evidence without changing any governed artifact. Create only the Step 5 task-record location required for command evidence.
2. Execute baseline, focused, expanded headless, expanded GUI, lint, type check, and `make check` in the stated order. Preserve raw output in the task record/log location as needed and never duplicate an unchanged failing command.
3. Perform the scoped diff, documentation-contract, EDMC-compliance, and secret reviews. Hand the complete evidence to the orchestration thread, which alone updates the plan/dashboard and decides whether failed validation needs a fresh remediation context.

## Acceptance Criteria

1. **EDMC baseline is evaluated before release validation**
   - Given the final circle-change workspace and the required plugin runtime baseline
   - When `overlay_client/.venv/bin/python scripts/check_edmc_python.py` runs before release tests
   - Then its exact pass result, or exact platform/version/architecture blocker, is recorded without using a mismatch override or treating a failure as waived.

2. **Focused contracts prove every circle boundary and legacy regression surface**
   - Given the completed compatibility, client, renderer, and runtime work
   - When the focused helper/processor, marked harness, and PyQt paint/render commands run in order
   - Then they prove canonical circle fields, positional rectangle compatibility, invalid-geometry no-mutation, raw/TCP publication, bounded `drawEllipse` mapping, and existing rectangle/vector behavior, with exact outcomes recorded.

3. **Expanded headless and GUI suites are independently evidenced**
   - Given focused checks have completed
   - When `overlay_client/.venv/bin/python -m pytest` and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` run
   - Then the headless suite's expected GUI skips and the GUI-enabled suite's results are separately recorded, and no failing suite is waived without explicit documented user approval.

4. **Release-quality lint, type, and project check complete**
   - Given the final candidate state
   - When `make lint`, `make typecheck`, and `make check` run after the test suites
   - Then each exact result is recorded, `make check` is not replaced by a narrower command, and any unresolved failure stops advancement with captured evidence.

5. **Scoped release, compliance, and secret reviews find no unapproved drift**
   - Given the final scoped diff, changed documentation, task records, and validation logs
   - When `git diff --check`, status/diff inspection, canonical-example comparison, local secret scan, and every applicable EDMC compliance item are reviewed
   - Then formatting is clean, no credentials/secrets are reported or exposed, no unintended behavior/version/package/release change is present, and each compliance item has an explicit yes/no result with a stated corrective action for every `No`.

6. **Evidence is handoff-ready without completing orchestration-owned artifacts**
   - Given all commands and reviews are complete or a stop condition is reached
   - When the task record is written and the dedicated-agent handoff is prepared
   - Then it lists exact command outcomes, skips/reasons, review results, residual risks, and the next exact orchestration action, while leaving the approved plan and execution dashboard untouched.

## Metadata
- **Complexity**: Medium
- **Labels**: circle-shape, regression, release-gate, pytest, pyqt, harness, lint, typecheck, edmc-compliance, security-review, step-5
- **Required Skills**: pytest, PyQt test execution, Make, Ruff, mypy, EDMC plugin compliance review, Git diff review, local secret scanning, evidence recording
