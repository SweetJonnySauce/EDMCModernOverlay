
A very, VERY, common issue is **"I've installed the overlay but nothing is showing"**. This is often attributed to the CMDR installing the overlay, with no other plugins installed or configured to use the overlay. EDMC nor EDMCModernOverlay show anything in the game window by default. If you're here and are having the same issue **you will need another plugin with overlay capabilities**.

Below are some basic troubleshooting steps if you can't get the overlay to work. If you can answer "Yes" to the question, move on to the next one. Otherwise, follow the remediation step.

| Troubleshooting Step | Remediation | 
|---------------------|---------------------|
|Do you have EDMCModernOverlay installed? | If you have no overlay or a legacy overlay installed, download the [latest release](https://github.com/SweetJonnySauce/EDMCModernOverlay/releases/latest) of EDMCModernOverlay and run the installer for your OS. |
| Do you have an "Enabled Plugins" list on the plugins tab of EDMC Settings? (File > Settings > Plugins) | Upgrade EDMC to version 6.1.0 or greater. Note: this is not strictly necessary but is helpful in troubleshooting below. |
| Does EDMCModernOverlay show as enabled on the plugins tab in EDMC Settings? | Go to File > Settings > plugins in EDMC and enable EDMCModernOverlay. |
| Do you have another plugin installed that has Overlay capabilities? | Install an EDMC plugin that has overlay support (e.g. BGS-Tally, Bioscan, LandingPad, EDR) |
| Is that plugin showing up as enabled on the plugins tab in EDMC Settings? | Go to File > Settings > plugins in EDMC and enable the plugin. |
| Is that plugin's Overlay capabilities enabled in EDMC Settings? | Many plugins require you to enable the overlay feature first. Go to the respective plugin tab (not the EDMCModernOverlay tab) in EDMC Settings (File > Settings) and enable the overlay capability of that plugin (varies based on plugin). Test that overlay in-game to see if an overlay shows up. |
| I still don't see any in-game overlays. | Try sending a test overlay. You can trigger a test overlay by typing in the chat launch command and passing the test argument. On default install, type `!ovr test` in the game chat panel (also triggered from EDMCModernOverlay settings pane in EDMC). You should see a test overlay with black background in the middle of the game window. See [Chat Commands](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Chat-Command) for more info on `!ovr` arguements. |
| I don't see the test overlay when triggered. | Make sure the game has focus after triggering the test overlay (i.e. alt-tab to the game). |
| I still don't see the test overlay or any other plugin overlays in-game | Contact me for additional support and troubleshooting. |

## GNOME Wayland helper checks

On GNOME Wayland, the helper must be installed, enabled, active, reachable over the local session bus, and protocol-compatible before GNOME Wayland true-overlay behavior can be claimed. If the helper is missing or unhealthy, Modern Overlay should report `degraded_overlay`.

Run these commands from a terminal:

```bash
gnome-shell --version
printf 'session=%s desktop=%s\n' "$XDG_SESSION_TYPE" "$XDG_CURRENT_DESKTOP"
gsettings get org.gnome.shell disable-user-extensions
gnome-extensions info edmc-modern-overlay-helper@edmcmodernoverlay.github.io
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.GetHealth
```

Common results:
- `Extension ... doesn't exist`: rerun the Linux installer while logged into GNOME Wayland and approve the helper install.
- `disable-user-extensions` is `true`: GNOME user extensions are globally disabled. Re-enable them manually, then log out and back in.
- `State` is not `ACTIVE`: log out and back in after install/enable. If it still is not active, rerun the installer or collect diagnostics.
- DBus `ServiceUnknown`: the helper is not active or did not publish its local session DBus service.
- Protocol/version mismatch: reinstall or update Modern Overlay so the plugin and helper versions match.

If you originally installed Modern Overlay while using X11, switch to GNOME Wayland first, then rerun the Linux installer. The helper install path is intentionally installer-driven; in-settings helper install/uninstall buttons are deferred.

For a support bundle on Linux, run:

```bash
utils/collect_overlay_debug_linux.sh
```

The default collector includes GNOME/session/helper facts and Modern Overlay status lines when available. It does not dump screenshots, broad process lists, command lines, or unrelated window titles by default.


