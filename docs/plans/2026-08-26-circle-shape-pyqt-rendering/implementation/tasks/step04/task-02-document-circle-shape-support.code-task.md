# Task: Document Circle Shape Support

## Description
Update the public documentation so plugin authors can discover and correctly use the completed circle shape API through `send_shape` and `send_raw`. The documentation must use the exact tested public contract, explain centre-based geometry and validation, and describe the established legacy viewport mapping and PyQt rendering behavior without changing product code or test behavior.

## Background
The public documentation currently describes `send_shape` as rectangle-only and lists only rectangle/vector shapes in several entry points. Steps 1–3 established the shipped contract: circles use a stable ID, `shape="circle"`, centre `x`/`y`, strictly positive `radius` and `thickness`, `color`, optional/transparent `fill`, and TTL replacement semantics; they are drawn with PyQt's bounded `QPainter.drawEllipse` through the same legacy transform/group/viewport mapping as rectangles. Under a non-uniform mapping, the transformed bounds can be elliptical by design. Step 4 Task 01 supplies the raw/TCP lifecycle evidence that these examples must match.

## Reference Documentation
**Required:**
- Design: docs/plans/2026-08-26-circle-shape-pyqt-rendering/design/detailed-design.md

**Additional References (if relevant to this task):**
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/research/payload-and-rendering.md (canonical payload and non-uniform mapping decision)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/plan.md (Step 4 Stage 4.2 and acceptance evidence)
- docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/tasks/step04/task-01-prove-raw-tcp-circle-lifecycle.code-task.md (proven raw/TCP contract)
- docs/wiki/send_shape-API.md (shape-helper reference)
- docs/wiki/send_raw-API.md (raw-payload reference)
- docs/wiki/Getting-Started.md (copyable first-use example)
- docs/wiki/Concepts.md and docs/wiki/FAQs.md (public support statements)
- docs/rendering-pipeline.md (runtime-to-PyQt rendering explanation)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. **Test type selected before edits: no new automated test type.** This is documentation-only work and changes no deterministic helper/service or EDMC lifecycle behavior. It depends on Task 01's mixed unit+harness evidence; manually compare every new public payload example against the exact tested API before editing. Document this scope and residual copy-drift risk in the task record.
2. Update `docs/wiki/send_shape-API.md` to describe both supported `send_shape` forms without breaking rectangle documentation: retain the positional rectangle signature, add the keyword-based circle form, give a copyable `send_shape("myplugin-radius", "circle", color=..., fill=..., x=..., y=..., radius=..., thickness=..., ttl=...)` example, and state that circle `x`/`y` are its centre and no `w`/`h` are sent.
3. In that shape reference, document the stable-ID replacement/clear behavior; positive `radius`/`thickness` requirement; warning/drop behavior for missing, non-numeric, zero, or negative geometry; transparent fill (`"none"` or empty); requested border `color`; and existing TTL semantics. Make clear that rectangle coordinates remain top-left and positional rectangle callers remain supported.
4. Update `docs/wiki/send_raw-API.md` with a canonical raw circle example and field-reference entries for `shape="circle"`, centre `x`/`y`, `radius`, and `thickness`. State that raw/TCP normalization retains the fields but client-side validation drops invalid geometry before it can replace a visible same-ID circle; do not falsely claim that runtime normalization rejects it.
5. Update `docs/wiki/Getting-Started.md` with a concise copyable circle example using the same field names/values/semantics as the tested public helper API. Keep it distinct from vector marker circles so readers do not confuse `shape="circle"` with a vector point marker.
6. Update `docs/wiki/Concepts.md` and `docs/wiki/FAQs.md` only where needed to state that circles are a supported payload primitive alongside messages, rectangles, and vectors. Preserve existing historical/support text and do not make broader compatibility guarantees.
7. Update `docs/rendering-pipeline.md` to include circle normalization/storage, the centre-minus/plus-radius square derivation through the existing transform/group/viewport pipeline, bounded `QPainter.drawEllipse` execution, requested pen/fill/opacity behavior, and the intended possibility of an elliptical result under non-uniform mapping. Keep rectangle/vector trace descriptions accurate; do not invent unavailable circle trace stages.
8. Do not update source code, tests, screenshots, generated task artifacts outside this task, the approved plan, or the execution dashboard. Do not add API behavior that documentation cannot prove. Use no external network, live EDMC, OAuth, upload, or release action.
9. Perform a local documentation review: search the touched pages for stale rectangle-only/support-list claims, compare all code/JSON examples to Task 01 and the prior Step 1 exact-payload test, and run the Step 4 plan commands exactly as the milestone evidence if Task 01 did not already provide passing results:
   - `overlay_client/.venv/bin/python -m pytest -m harness tests/test_harness_legacy_tcp_ingestion.py -q`
   - `overlay_client/.venv/bin/python -m pytest tests/test_legacy_processor.py overlay_client/tests/test_paint_commands.py -q`
   Do not rerun an unchanged failed command; record its existing evidence instead.
10. Record touched documentation, the manual example-to-test comparison, exact validation evidence reused or run, and residual documentation-only risk in `docs/plans/2026-08-26-circle-shape-pyqt-rendering/implementation/task-records/step04-task02/progress.md`; do not update the approved plan or execution dashboard from this task context.

## Dependencies
- Steps 1–3 define the exact helper, normalizer, client-storage, and PyQt rendering behavior being documented.
- Task 01 must be independently reviewed first because it proves raw/TCP publication and invalid-geometry handling at the lifecycle boundary.
- Existing public wiki and rendering-pipeline documents are the only intended implementation surfaces.
- The completion of this task depends on the exact Step 4 validation evidence, not on a live visual demo or external documentation publication.

## Implementation Approach
1. Read the existing API/wiki/pipeline pages and the exact tested payload fixtures. List each stale rectangle-only or unsupported-shape statement before editing so the update is complete but behavior-scoped.
2. Update the API references first, then use the same canonical circle example in Getting Started. Update concepts/FAQ support statements and the rendering pipeline last, taking care to distinguish true circle shapes from vector marker circles.
3. Compare every field name, centre-coordinate explanation, positive-geometry rule, fill/TTL/stable-ID claim, and mapping statement against the design and Task 01 evidence. Run or reuse the two exact Step 4 commands, record the result in the task record, and hand off for main-thread review.

## Acceptance Criteria

1. **Shape API example exactly reflects the public circle contract**
   - Given a plugin author reads `send_shape-API.md`
   - When they copy the documented circle example
   - Then it uses stable ID plus `shape="circle"`, named centre `x`/`y`, positive `radius`/`thickness`, `color`, `fill`, and `ttl`, with no synthetic `w`/`h`, matching the tested helper payload.

2. **Raw payload documentation states the correct validation boundary**
   - Given a plugin author sends a raw/TCP circle
   - When they read `send_raw-API.md`
   - Then they can identify the canonical circle fields and understand that client-side validation drops invalid geometry before same-ID drawable-item replacement, while raw normalization preserves fields for that authoritative path.

3. **Discovery documentation identifies circles unambiguously**
   - Given a reader starts in Getting Started, Concepts, or FAQs
   - When they look for supported graphical payloads
   - Then circles are listed as a supported shape and the example is clearly distinct from vector marker circles.

4. **Rendering semantics are complete and behavior-accurate**
   - Given a reader follows the rendering pipeline for a circle
   - When they reach transform and final-paint stages
   - Then the page explains the derived centre-plus/minus-radius bounding square, reuse of legacy transform/group/viewport mapping, bounded PyQt `drawEllipse`, pen/fill/opacity behavior, and possible non-uniform mapped ellipse without claiming new global render hints or trace stages.

5. **Existing public behavior remains accurately documented**
   - Given existing rectangle/vector users and the Step 4 validation commands
   - When the touched documentation is reviewed and the exact commands are run or their accepted Task 01 evidence is reused
   - Then rectangle positional semantics, vector-marker semantics, stable-ID/TTL behavior, and the documented regression evidence remain intact; any unavailable command is recorded rather than silently waived.

## Metadata
- **Complexity**: Medium
- **Labels**: circle-shape, documentation, public-api, raw-payload, rendering-pipeline, step-4
- **Required Skills**: Technical documentation, API-contract review, Markdown, Python payload semantics, regression-evidence interpretation
