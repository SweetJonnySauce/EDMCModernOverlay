EDMCModernOverlay now supports [EDMCHotkey](github.com/SweetJonnySauce/EDMCHotkeys) actions. These allow you to map plugin actions to hotkey combinations (e.g. LCtrl+LSfhit+F1) that you can bind to controller buttons or to Voice Attack commands. 

See [EDMCHotkeys Usage](https://github.com/SweetJonnySauce/EDMCHotkeys#Usage) for information on how to set up hotkey ations

## Hotkey Actions Supported
- `Overlay On`: Turn all overlay plugin groups on. Optionally, you can specify specific plugin groups to turn on.
- `Overlay Off`: Turn all ovelay plugin groups off. Optionally, you can specify specific plugin groups to turn off.
- `Toggle Overlay`: Toggle all overlay plugin groups on or off depending on current state. Optionally, you can specify specific plugin groups to toggle.
- `Launch Overlay Controller`: Launch the Overlay Controller

You can specify specific plugin groups to turn on/off/toggle by adding a short json string to the EDMCHotkey payload field. 

**Examples:**

- Single plugin group target
  ```json
  {"plugin_group": "BGS-Tally Objectives"}
  ```

- `Multi-target plugin group target

  ```json
  {"plugin_groups": ["BGS-Tally Colonisation", "BGS-Tally Objectives"]}
  ```
