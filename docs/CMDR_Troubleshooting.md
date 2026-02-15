
Below are some basic troubleshooting steps if you can't get the overlay to work. If you can answer "Yes" to the question, move on to the next one. Otherwise, follow the remediation step.

| Troubleshooting Step | Remediation | 
|---------------------|---------------------|
|Do you have EDMCModernOverlay installed? | If you have no overlay or a legacy overlay installed, download the [latest release](https://github.com/SweetJonnySauce/EDMCModernOverlay/releases/latest) of EDMCModernOverlay and run the installer for your OS. |
| Do you have an "Enabled Plugins" list on the plugins tab of EDMC Settings? (File > Settings > Plugins) | Upgrade EDMC to version 6.1.0 or greater. Note: this is not strictly necessary but is helpful in troubleshooting below. |
| Does EDMCModernOverlay show as enabled on the plugins tab in EDMC Settings? | Go to File > Settings > plugins in EDMC and enable EDMCModernOverlay. |
| Do you have another plugin installed that has Overlay capabilities? | Install an EDMC plugin that has overlay support (e.g. BGS-Tally, Bioscan, LandingPad, EDR) |
| Is that plugin showing up as enabled on the plugins tab in EDMC Settings? | Go to File > Settings > plugins in EDMC and enable the plugin. |
| Is that plugin's Overlay capabilities enabled in EDMC Settings? | Go to the respective plugin tab (not the EDMCModernOverlay tab) in EDMC Settings (File > Settings) and enable the overlay. Test that overlay in-game to see if an overlay shows up. |
| I still don't see any in-game overlays. | Try sending a test overlay. You can trigger a test overlay by typing in the chat launch command and passing the test argument. On default install, type `!ovr test` in the game chat panel (also triggered from EDMCModernOverlay settings pane in EDMC). You should see a test overlay with black background in the middle of the game window. See [Chat Commands](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Chat-Command) for more info on `!ovr` arguements. |
| I don't see the test overlay when triggered. | Make sure the game has focus after triggering the test overlay (i.e. alt-tab to the game). |
| I still don't see the test overlay or any other plugin overlays in-game | Contact me for additional support and troubleshooting. |



