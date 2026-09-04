# Backend Compatibility Matrix Context

## Task

Publish one wiki page that describes backend selection, compatibility classification,
requirements, evidence status, and fallbacks without promoting planned or unvalidated
environments to supported status.

## Existing documentation

- `docs/wiki/_Sidebar.md` is the wiki navigation surface. User-facing pages use concise
  Markdown and wiki links.
- `docs/plugin-compat.md` lists payload and desktop-scaling issues, not backend support.
- `docs/refactoring/fix219_cross_platform_overlay_architecture_research.md` defines the
  backend families, classifications, and planning matrix.
- `docs/refactoring/fix219_backend_architecture_followup_cleanup_plan.md` records that
  final environment validation and signoff remain open in Phase 5.
- `overlay_client/backend/contracts.py` defines the runtime family/instance/classification
  vocabulary; `selector.py` provides the current selection policy.

## Dependency map

`Backend-Compatibility.md` -> `docs/wiki/_Sidebar.md` (discoverability)

The page reports the backend selector's public vocabulary. It does not change runtime
selection, installer profiles, capability probes, or support classifications.

## Constraints and decisions

- Separate runtime classification from validation evidence.
- Describe `xwayland_compat` as a deliberate degraded compatibility path, not a failure.
- Mark environments lacking recorded closure evidence as pending/deferred.
- Treat Flatpak as an execution context, not a backend.
- No code or hook behavior changes are required, so no unit or harness test is applicable.

## Issue-history review

The full open and closed GitHub issue history was reviewed on 2026-08-30. It confirms
that only GNOME Wayland and Linux X11 have an end-to-end validation claim for this page.
KDE/KWin has unresolved attachment, scaling, and multi-monitor reports; Hyprland has
unresolved separate-window, focus, and placement reports. Sway, Wayfire, and generic
Wayland have detected code paths but no validation evidence. XWayland remains a distinct
degraded compatibility fallback. Flatpak, distribution packages, and dependency
installation are execution prerequisites, not backend validation evidence.

The X11 claim is environment-specific: GNOME/Mutter on Ubuntu 24.04.4 LTS is the
validation target. Reusing the generic native-X11 implementation does not validate every
X11 desktop or Linux distribution.

The public matrix separates the platform/desktop from the display session. This prevents
GNOME, KDE/KWin, and Hyprland from being conflated with Wayland/X11/XWayland, and keeps
the Windows row intelligible without calling Windows a Linux desktop environment.
