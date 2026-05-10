# EDMC Modern Overlay GNOME Shell Helper

This directory contains the GNOME Shell extension payload for the planned
`gnome_shell_wayland` helper-backed path.

Current status:

- Phase `3` helper/runtime wiring complete; install/operation docs still in progress
- owns `org.edmc.EDMCModernOverlay` on the session bus when enabled
- exports `/org/edmc/EDMCModernOverlay` with interface `org.edmc.EDMCModernOverlay.Helper`
- supports a narrow `Hello(session_token)` handshake returning helper identity and protocol version
- supports `SetOverlayInputPassthrough(enabled)` so the client can hand GNOME compositor-side click-through ownership to the helper when the promoted overlay is meant to be non-interactive
- emits `Event(message_json)` after a successful handshake
- currently emits:
  - `active_window_changed`
  - `window_geometry_changed`
  - `presentation_state_changed`
- current target matching is title-driven, scoped to Elite Dangerous windows, and retains the last matched Elite window across focus transitions until the window really disappears
- current Stage `5.2` prototype also identifies the external overlay window by its fixed title (`EDMC Modern Overlay`) and attempts a narrow GNOME-side promotion while the tracked game window is foreground/visible
- the current safe prototype intentionally avoids moving the external overlay window across monitors or workspaces; live GNOME 46 evidence showed those migration calls can destabilize Mutter for this window type
- the current helper stage also suppresses GNOME shell chrome (top panel plus Ubuntu Dock actors when present) only while the helper-backed overlay is actively promoted, continuously reapplies that suppression while promotion remains active, and restores prior visibility state immediately on blur/disable
- overlay-client GNOME helper probe, handshake, and bundle runtime paths now exist
- still awaiting live GNOME-session validation and final support signoff

Planned install target:

- `~/.local/share/gnome-shell/extensions/edmc-modern-overlay@edmc.local/`

Minimal supported install/enable flow:

1. Copy this directory to `~/.local/share/gnome-shell/extensions/edmc-modern-overlay@edmc.local/`.
2. Enable the extension with one of:
   - `gnome-extensions enable edmc-modern-overlay@edmc.local`
   - the GNOME Extensions app GUI

Minimal supported disable/uninstall flow:

1. Disable the extension with one of:
   - `gnome-extensions disable edmc-modern-overlay@edmc.local`
   - the GNOME Extensions app GUI
2. Remove `~/.local/share/gnome-shell/extensions/edmc-modern-overlay@edmc.local/` to uninstall the per-user copy.

Expected fallback/status behavior:

- disabling or uninstalling the helper should return the overlay to the existing missing-helper fallback path
- a present but unusable helper remains an `incompatible_helper` case instead

Current helper contract surface:

- bus name: `org.edmc.EDMCModernOverlay`
- object path: `/org/edmc/EDMCModernOverlay`
- interface: `org.edmc.EDMCModernOverlay.Helper`
- handshake method: `Hello(session_token) -> (helper_kind, protocol_version, helper_version)`
- control method: `SetOverlayInputPassthrough(enabled) -> applied`
- event signal: `Event(message_json)`

Current `Event(message_json)` payload shape:

```json
{
  "type": "event",
  "helper_kind": "gnome_shell_extension",
  "protocol_version": 1,
  "session_token": "session-token",
  "event": "active_window_changed",
  "payload": {
    "matched": true,
    "identifier": "stable:123",
    "title": "Elite - Dangerous (CLIENT)",
    "wm_class": "",
    "is_foreground": true,
    "is_visible": true
  }
}
```

`window_geometry_changed` uses the same envelope and currently adds `x`, `y`, `width`, and `height` to the payload.

`presentation_state_changed` uses the same envelope and reports whether the helper found the external overlay window, whether the tracked game window is foreground/visible, whether GNOME-side promotion was attempted/applied, whether compositor-side input passthrough was requested/applied for the overlay actor, and whether all targeted GNOME shell chrome is currently suppressed.

See the implementation plan for staged details:

- `docs/refactoring/gnome_shell_extension_helper_plan.md`
