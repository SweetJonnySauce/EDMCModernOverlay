# Task 06 Context: Proven Unchanged Repaint Work

## Summary

Task 06 implements authoritative Stage 1.8 / working Stage 3.12 only. The approved design
requires evidence-led suppression at existing pure/runtime seams, without Task 07 A/B, manual
compositor work, capture changes, thresholds, production routing, or generic knowledge of GNOME
presentation details.

## Existing documentation

- The Task 06 code-task requires bounded per-reason attribution, RED/GREEN unit evidence,
  deterministic supported-payload fingerprints, lifecycle-only refresh, safe unknown fallback,
  and preservation of all real repaint/recovery triggers.
- The detailed design requires identical rendered output to avoid Qt update, frame rebuild, and
  presentation refresh while keeping content, style, geometry, group, override, expiry,
  animation, scale, mode/monitor, visibility/recovery, and explicit-refresh work intact.
- The pressure/repaint research says request, Qt paint, frame preparation, raster encode/reuse,
  and helper presentation are separate contracts. It explicitly forbids a competing dedupe
  system because supported-payload visual snapshots already exist.
- The Step 03 plan selects unit tests for pure fingerprints and runtime seams. Harness tests
  become mandatory only if `load.py`, EDMC hooks, lifecycle, or Tk wiring changes.
- The post-Task-05 iteration review found no design remediation prerequisite and authorizes Task
  06 as the next isolated increment. The integrated `make check` and `make test` gates are due
  after this task; the reviewed commit remains reserved for Stage 3.16.
- The repository README confirms this is the EDMC Modern Overlay plugin/client project. No
  `CODEASSIST.md` was found. Repository `AGENTS.md` and the approved PDD artifacts therefore
  supply the project-specific implementation constraints.

## Repository and baseline

- Branch: `backend-refactor-implementation`; starting HEAD `3d23328`.
- The working tree already contains the broader uncommitted Step 03 implementation and evidence
  artifacts. Task 06 must not reset, bulk-stage, or infer ownership from the full diff.
- Pre-change focused command passed with 41 tests. Evidence is in `logs/baseline-focused.log`.
- EDMC plugin-runtime baseline tracking remains a separate known compliance item. Task 06 is
  confined to the Python >=3.10 overlay client and does not change plugin-runtime syntax or
  dependencies.

## Attribution observation

Historical reduced-v2 captures establish request volume but not equivalent work:

| Layer | Stable managed example | Stable Shell-raster example | Existing seam |
| --- | ---: | ---: | --- |
| Repaint requests | 841 | 841 | `_request_repaint` reason counts |
| Qt paints | 49 | 0 | bounded paint count |
| Frame preparations | 0 | 60 | backend performance sample |
| Raster encodes/builds | 0 | 1 | Shell-raster cache diagnostics |
| Raster payload reuse | 0 | 59 | Shell-raster cache diagnostics |
| Helper presentation calls | 0 | 30 | backend presentation result |

The current supported message/rect/vector snapshot already ignores TTL and incidental metadata,
so identical supported payloads refresh expiry without `_request_repaint`. Remaining correctness
gaps are that unknown types are currently eligible for JSON-based dedupe, animation is not an
explicit bypass, and plugin/group identity is outside the visual comparison. Separately, every
eligible Shell-raster target refresh enters frame preparation even when render identity and
target context are unchanged; encoding is reused later, but command/crop/frame preparation is
still repeated.

## Dependency map

1. `RenderSurfaceMixin._handle_legacy` applies overrides and supplies plugin/group/generation
   context to `PayloadModel.ingest`.
2. `PayloadModel` uses the pure legacy visual fingerprint to decide visual change versus
   lifecycle-only refresh. A visual change dirties `LegacyRenderPipeline` and requests repaint.
3. `ControlSurfaceMixin._request_repaint` attributes immediate, debounced, coalesced, Qt-update,
   and backend-refresh scheduling with fixed bounded counters.
4. `LegacyRenderPipeline` supplies a deterministic render identity combining context and a
   monotonic visual revision. Dirtying the pipeline invalidates frame reuse.
5. `RenderSurfaceMixin._build_backend_shell_raster_content_frame` reuses only a successful frame
   result whose render identity and complete target/request context match. Missing/unprovable
   state and failures are never cached.
6. The existing GNOME backend remains the presentation owner. Generic code supplies a frame
   provider and a generic one-shot presentation-refresh flag; it does not import private GNOME
   enums or make compositor decisions.

## Implementation paths

- Pure supported-payload fingerprint and ingest attribution:
  `overlay_client/legacy_processor.py`, `overlay_client/payload_model.py`.
- Render identity and Shell frame reuse:
  `overlay_client/render_pipeline.py`, `overlay_client/render_surface.py`.
- Bounded request/scheduling/paint attribution and generic refresh signal:
  `overlay_client/control_surface.py`, `overlay_client/overlay_client.py`.
- Allowlisted frame-skip performance interpretation:
  `overlay_client/follow_surface.py`.
- Unit tests:
  `overlay_client/tests/test_payload_dedupe.py`,
  `overlay_client/tests/test_repaint_debounce.py`, and
  `overlay_client/tests/test_follow_surface_mixin.py`.

## Uncertainties and safe choices

- Unknown or malformed payload equivalence is not provable. It must repaint on every accepted
  ingest rather than use a broad serialized fallback fingerprint.
- A cached Shell frame is safe only when all target geometry, monitor/output/scale/workspace,
  visibility/mode facts, request facts, diagnostics mode, and render identity are complete and
  equal. Otherwise the provider rebuilds.
- Cached failures could delay recovery, so only eligible results with a concrete update request
  are reusable.
- TTL/metadata refresh may update lifecycle state but cannot dirty the render revision. Expiry
  removal still dirties and repaints through the existing purge path.
