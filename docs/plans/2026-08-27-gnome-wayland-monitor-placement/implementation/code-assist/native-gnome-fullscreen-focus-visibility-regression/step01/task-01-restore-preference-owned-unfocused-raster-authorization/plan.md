# Plan

- [x] Confirm pure bundle policy scope and select unit tests.
- [x] RED: replace the obsolete fullscreen exception expectation with the
  unchecked-preference suspension contract, while retaining an explicit
  checked-preference presentation case.
- [x] GREEN: pass `keep_overlay_visible` directly to the Shell-raster bridge
  and delete the obsolete fullscreen geometry authorization helper.
- [x] REFACTOR: review names and surrounding contracts without changing
  fullscreen eligibility, transition ownership, or other backends.
- [x] Validate the focused test suite and `git diff --check`.
- [ ] Record scoped evidence, update approved tracking, write handoff, and
  commit only this task's files.

## Test scenarios

1. An unfocused, fullscreen, full-monitor target with the preference disabled
   emits `allow_unfocused_target=False`, receives `target_not_focused`, is
   focus-risk suspended, and does not show the overlay.
2. The otherwise identical target with the preference enabled emits `True`
   and keeps the existing successful Shell-raster presentation result.
3. Existing focused/windowed/overview/target-loss/transition coverage stays
   in the focused suite, alongside extension source and frame contract tests.

## Minimal design

The call-site boolean becomes the preference itself. Deleting the geometry
helper removes the only fullscreen exception. No new abstraction or protocol
field is necessary.
