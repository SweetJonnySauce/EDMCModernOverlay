You can launch the [Overlay Controller](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Overlay-Controller) and control overlay actions via in-game chat.

**Command prefix:** configurable in EDMC Settings (default `!ovr`).

### Arguments
- **No args:** launches the Overlay Controller.
- **On:** `on [plugin_group_name]` turns groups on (all groups if no target is provided).
- **Off:** `off [plugin_group_name]` turns groups off (all groups if no target is provided).
- **Toggle:** `toggle [plugin_group_name]` flips group state on or off (all groups if no target is provided).
- **Status:** `status` lists plugin groups with `Enabled|Not Enabled|Unknown|Ignored`, `Seen|Not Seen`, and `On|Off` states.
- **Opacity:** number `0-100` or percent form (for example `50%`, `75%`) sets visual opacity. 0 is fully transparent, 100 is fully visible.
- **Test Overlay:** `test` sends a test overlay to the middle of the game window.
- **Plugins:** `plugins` logs installed plugin scan details.

### Chat Command Equivalents
For `on`', `off`, and `toggle`, the following forms are equivalent:

- `!ovr on BGS-Tally Objectives`
- `!ovr BGS-Tally Objectives on`
- `!ovr turn BGS-Tally Objectives on`
- `!ovr turn on BGS-Tally Objectives`

### Usage Examples
- `!ovr` opens Overlay Controller.
- `!ovr on` turns all plugin groups on.
- `!ovr off BGS-Tally Objectives` turns only that plugin group off.
- `!ovr toggle` toggles all plugin groups on or off.
- `!ovr t` toggles all plugin groups using the default toggle token.
- `!ovr status` shows a table overlay with columns `Plugin Group | Plugin | Seen | State` using values from `<plugin_group_name>: Enabled|Not Enabled|Unknown|Ignored, Seen|Not Seen, On|Off`. Seen means the plugin group has been seen in your current session.
- `!ovr 50%` sets visual overlay opacity to 50%.
- `!ovr test` sends a test overlay payload.

### Notes
- If you use EDR (EDRecon), avoid `!overlay` as your command prefix to prevent conflicts.
- You can set an Elite Dangerous hotkey/keybind to enter chat mode in-game: `Options > Controls > Ship Controls > Mode Switches > Quick Comm`.
