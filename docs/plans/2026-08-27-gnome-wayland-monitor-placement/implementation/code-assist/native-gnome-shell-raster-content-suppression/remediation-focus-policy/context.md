# Focus-Policy Remediation Context

## Requirement

For a valid, matched native GNOME Shell-raster presentation, an unchecked
“Keep overlay visible” preference must request reversible raster-content
suppression after the existing focus-loss debounce. The eligible fullscreen
actor-continuity authorization remains true; no actor lifecycle operation,
placement behavior, or non-GNOME backend behavior changes.

## Diagnosis and dependency map

The first source diagnosis was incomplete. Live client evidence shows
`surface_preparation=none`, `target_focus=False`, `keep_overlay_visible=False`,
and `visibility_reason=presentation_not_attachable`; it also records an
outbound helper request with `content_visibility=visible`. The Shell-raster
result intentionally reports `should_show_overlay=False` so generic Qt does
not map, but the consumer incorrectly equates that with an unavailable
presentation and resets the next neutral content request to visible.

The correction needs a backend-bundle-declared neutral fact: a supported
renderer can retain its actor and accept a content-visibility update while
ordinary managed-window attachment is unavailable. The generic policy can use
that fact without importing or inspecting GNOME-specific types. The existing
managed-surface focus-unreliability escape hatch remains unchanged.

## Invariants

- Checked preference remains visible across focus loss.
- Unchecked preference remains visible during the established debounce, then
  returns `mapped_suppressed` and neutral `suppressed` intent when the selected
  backend declares retained content visibility support.
- Focus return restores visible intent.
- Hard target loss still hides/resets.
- No change to `allow_unfocused_target`, actor opacity handling, helper
  capability gates, X11, xcompat, or placement.
- Existing managed-PyQt focus-unreliability behavior remains unchanged.
- A retained actor must count as mapped for generic policy warm-up decisions;
  the deliberately unmapped Qt widget must not start a focused remap warm-up.

## Existing documentation

Reviewed `AGENTS.md`, the authoritative content-suppression plan, execution
dashboard, `README.md`, policy tests, and follow-surface tests. No
`CODEASSIST.md` is present.
