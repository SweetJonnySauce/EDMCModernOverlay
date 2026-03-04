You can launch the [Overlay Controller](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Overlay-Controller) and control a small set of Overlay settings via the in-game chat.

**Command prefix:** configurable (default `!ovr`) in EDMC Settings on the EDMCModernOverlay plugin tab

### Arguments
- **No args:** launches the overlay controller.
- **Opacity:** a number `0–100` or percent form (e.g., `50`, `75%`) sets payload opacity.
- **Test Overlay:** `test` sends a test overlay to the middle of the game window for 30 seconds
- **Toggle:** a configurable alphanumeric argument (default `t`, case-insensitive, multi-character allowed) toggles opacity on/off.

### Examples

- `!ovr` - open the Overlay Controller
- `!ovr 50%` - set overlay opacity to 50%
- `!ovr t` - toggle the overlay on/off
- `!ovr test` - sends a test overlay to the game screen

### Tips
- If you use EDR (EDRecon), don't set the chat command to `!overlay`, it will conflict with EDR.
- You can set an Elite Dangerous hotkey/keybind to enter chat mode in-game. In Elite Dangerous, go to Options > Controls > Ship Controls > Mode Switches > Quick Comm to set the hotkey/keybind. 