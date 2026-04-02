EDMCModernOverlay supports [EDMCHotkeys](https://github.com/SweetJonnySauce/EDMCHotkeys) actions. These let you map overlay actions to hotkey combinations (for example `LCtrl+LShift+F1`) that can also be triggered from controller bindings or VoiceAttack commands.

See [EDMCHotkeys Usage](https://github.com/SweetJonnySauce/EDMCHotkeys#Usage) for setup details.

## Hotkey Actions Supported
- `Overlay On`: Turn all overlay plugin groups on, or target specific groups via payload.
- `Overlay Off`: Turn all overlay plugin groups off, or target specific groups via payload.
- `Toggle Overlay`: Toggle all overlay plugin groups, or target specific groups via payload.
- `Launch Overlay Controller`: Launch the Overlay Controller.
- `Set Overlay Profile`: Switch to a specific profile.
- `Next Overlay Profile`: Cycle to the next profile.
- `Previous Overlay Profile`: Cycle to the previous profile.

## Payload Examples
Use the EDMCHotkeys action payload field with JSON.

### Group Targeting (`Overlay On` / `Overlay Off` / `Toggle Overlay`)
- Single target:
```json
{"plugin_group": "BGS-Tally Objectives"}
```
- Multiple targets:
```json
{"plugin_groups": ["BGS-Tally Colonisation", "BGS-Tally Objectives"]}
```

### Profile Selection (`Set Overlay Profile`)
- Any of these keys are accepted: `profile`, `profile_name`, or `name`.
```json
{"profile": "Mining"}
```
```json
{"profile_name": "On Foot"}
```
```json
{"name": "Default"}
```

`Next Overlay Profile` and `Previous Overlay Profile` do not require a payload.
