# GNOME Wayland monitor placement

Investigate and fix the native GNOME Wayland backend when Elite Dangerous is on
the primary monitor but the EDMC Modern Overlay is applied to the secondary
monitor. Keep the circle feature merge unchanged and preserve the distinct X11,
XWayland-compatibility, and native-Wayland backend boundaries.

Known runtime evidence on 2026-08-27: the helper resolved Elite's requested
rectangle as `(0, 248, 3440, 1440)` but reported the overlay applied at
`(3440, 248, 3440, 1440)`, a one-monitor-right displacement. The user wants a
research-backed, implementation-ready plan before any behavior change.
