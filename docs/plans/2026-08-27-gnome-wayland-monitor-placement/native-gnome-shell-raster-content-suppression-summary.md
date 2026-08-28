# Native GNOME Shell-Raster Content Suppression Summary

The prior fullscreen focus-visibility implementation is invalid because it
mapped the unchecked user preference directly to compositor actor
authorization. Live GNOME Wayland testing showed that the resulting actor
suspension can black-screen the game on focus return. The rollback is
user-verified and remains the required baseline.

The replacement work separates neutral overlay-content visibility from native
GNOME actor continuity. It uses an explicit helper capability gate and requires
both actor-form test coverage and repeated live focus-transition validation.

Artifacts:

- Research: `research/native-gnome-shell-raster-content-suppression-lessons.md`
- Design: `design/native-gnome-shell-raster-content-suppression.md`
- Implementation plan: `implementation/native-gnome-shell-raster-content-suppression-plan.md`

