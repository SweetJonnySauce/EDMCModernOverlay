# Focus-Policy Remediation Plan

## Stages

| Stage | Description | Status |
| --- | --- | --- |
| R1.1 | Capture live facts and reconcile the first policy hypothesis | Completed — live log proved the active path is `presentation_not_attachable`, not managed-surface focus unreliability. |
| R1.2 | Restore the unrelated managed-surface policy behavior | Completed — no behavior change is retained for that route. |
| R2.1 | Add failing policy/consumer tests for backend-declared retained-content availability | Completed — RED rejected the missing neutral snapshot field. |
| R2.2 | Add the neutral runtime result fact and GNOME-owned declaration | Completed — GNOME declares it only for an applied matching raster frame with helper support. |
| R2.3 | Prove retained Shell-raster `visible -> suppressed -> visible` transport without Qt remap | Completed — focused policy/consumer/follow coverage proves the generic Qt surface stays unmapped. |
| R2.4 | Run focused and full automated gates; then request live retry | Completed — focused suite: 274 passed; external project gates: 1,696 passed. |
| R2.5 | Treat a retained Shell-raster actor, not the unmapped Qt widget, as visible for policy warm-up | Completed — a neutral retained-content fact now prevents focused Shell-raster content from entering the generic Qt remap warm-up; targeted regression coverage passes. |

## Test strategy

1. A valid presentation that is not Qt-attachable but declares retained-content
   availability, with unchecked preference and elapsed debounce, must be shown
   with `mapped_suppressed`, `content_visible=False`, and neutral `suppressed`.
2. The same state without that declared fact remains the existing hidden,
   fail-closed behavior.
3. The GNOME bundle declares the fact only for an applied, matching Shell-raster
   result whose helper confirms content-visibility support.
4. The follow surface sends `visible -> suppressed -> visible` without mapping
   the generic Qt surface. Existing managed-PyQt behavior is unchanged.
5. A focused retained Shell-raster actor must be treated as already visible for
   policy purposes, so it never enters `target_focused_remap_warmup` merely
   because the generic Qt surface is intentionally unmapped.

## Scope

Touch the neutral runtime result, consumer policy snapshot, GNOME bundle-owned
declaration, and unit/follow-surface tests only. Do not change helper code,
actor handling, or backend-specific dispatch in generic follow/runtime code.
