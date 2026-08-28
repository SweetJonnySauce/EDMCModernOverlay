# Fullscreen Shell-Raster Routing Plan Summary

## Status

The monitor-transfer experiment is disproven for the observed Mutter session:
both placement orders return successfully while the external PyQt window stays
on the secondary monitor. The planned production repair is therefore native
GNOME Wayland fullscreen presenter routing, not another geometry adjustment.

## Artifacts

- `research/mutter-placement-probe-and-raster-inventory.md` records the live
  probe and existing implementation inventory.
- `design/fullscreen-shell-raster-routing.md` defines the standalone backend
  design and safety rules.
- `implementation/fullscreen-shell-raster-routing-plan.md` provides the
  staged, test-first implementation plan.

## Implementation direction

The native `gnome_shell_wayland` bundle will own presenter selection: managed
PyQt for windowed targets, existing real-content Shell raster actors for
eligible fullscreen full-monitor targets. Fullscreen raster failures clear and
suppress rather than showing the known-misplaced PyQt window. X11 and xcompat
remain separate and unchanged.

## Next step

Review the design and plan, then begin Step 1: introduce the bundle-owned
runtime seam while preserving current behavior and proving the fix219 boundary
with focused tests.
