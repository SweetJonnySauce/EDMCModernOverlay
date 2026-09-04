# Overlay runtime compatibility

This is a **runtime display compatibility matrix**. It describes whether the overlay can
work with a particular desktop/compositor and display session after installation.

It is not an operating-system installation matrix. A Linux distribution being recognized
by `install_linux.sh` means the installer can select its prerequisite packages; it does
not mean every desktop/session on that distribution is validated. See [[Distro Installation Compatibility]]
for the installer-supported Linux distribution families and prerequisites.

The overlay normally chooses the right display path automatically; you do not need to
know the technical backend name.

## What the status means

- **Validated** — tested end-to-end on the distribution and desktop/session named in
  the row.
- **Available** — the overlay includes a path for this setup, but it needs more
  validation before we make a stronger support claim.
- **Not yet validated** — the overlay detects this setup, but we have not confirmed a
  reliable overlay path for it.
- **Fallback** — a compatibility path that may help when the normal path cannot; it
  is not equivalent to a validated native setup.
- **Not supported** — the overlay does not currently provide a supported path.

## Supported setups

### Windows

| Display session | Status | What to do |
| --- | --- | --- |
| Windows desktop | Available | Install normally. |

### Linux

| Desktop / compositor | Display session | Status | What to do |
| --- | --- | --- | --- |
| GNOME | X11 | Validated | Validated on Ubuntu 24.04.4 LTS. Install normally. |
| GNOME | Wayland | Validated | Validated on Ubuntu 24.04.4 LTS. Install and enable the GNOME helper when prompted. See the GNOME notes below. |
| KDE Plasma / KWin | Wayland | Not yet validated | Do not rely on this for normal use yet. A support report is welcome. |
| Sway or Wayfire | Wayland | Not yet validated | Do not rely on this for normal use yet. A support report is welcome. |
| Hyprland | Wayland | Not yet validated | Do not rely on this for normal use yet. Current workarounds may require compositor rules. |
| Other Linux desktop | X11 | Not yet validated | The generic X11 path may work, but do not rely on it for normal use yet. A support report is welcome. |
| Other Linux desktop | Wayland | Not yet validated | Do not rely on this for normal use yet. A support report is welcome. |
| Any Wayland desktop | XWayland compatibility | Fallback | Use only if the normal path cannot work. It has a smaller validation scope than native X11 or GNOME Wayland. |
| COSMIC | Wayland | Not supported | There is no supported overlay path yet. |
| Gamescope | Wayland | Not supported | There is no supported overlay path yet. |

## Installation context

The installer prepares dependencies and optional helpers. This is a prerequisite for the
runtime matrix above, but it is not runtime validation.

| Installation context | What is required |
| --- | --- |
| Linux host install | Run the Linux installer so it can install the selected distro's client, Qt, X11, and Wayland prerequisites. |
| Flatpak EDMC install | Use the status for your desktop session above. The installer must also grant the Flatpak host-launch D-Bus permission so the overlay client can run outside the sandbox. |

The installer may apply compositor-specific setup, such as KDE scaling overrides or the
GNOME helper. That setup makes a route possible; it does not change a **Not yet
validated** row into a **Validated** one.

## GNOME Wayland notes

GNOME Wayland needs a healthy, protocol-compatible GNOME helper. If it is missing or
unhealthy, rerun the Linux installer while logged into GNOME Wayland, approve the helper
installation, and then log out and back in. For the most reliable presentation, run
Elite in windowed or borderless fullscreen mode.

Firefox on GNOME Wayland has a separate, known Firefox/Mutter drag-and-drop limitation.
It does not mean that the overlay intercepted input, but the overlay's diagnostics and
helper work can add compositor load. See [[Troubleshooting]] if you encounter it.

## If it does not work

Start with [[Troubleshooting]]. On Linux, create a support bundle with:

```bash
utils/collect_overlay_debug_linux.sh
```

Include the result when reporting an issue, but do not include credentials, tokens, or
unrelated system data.

## Technical details for support

The overlay records the selected display path, any fallback, and helper health in its
diagnostics. You do not need to change these details yourself. They help us investigate
problems and decide which setups to validate next.
