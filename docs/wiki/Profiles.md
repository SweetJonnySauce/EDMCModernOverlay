Profiles let you save different overlay layouts/visibility sets and switch between them automatically based on what you are doing in-game (ship, SRV, fighter, on-foot, etc.).

## Open the Profiles Tab
1. Open EDMC.
2. Open `Settings` for `EDMCModernOverlay`.
3. Go to the `Profiles` tab.

## Profile Table Basics
- `#`: Profile order (priority).
- `Active`: Current active profile (`✅`).
- `Profile`: Profile name.
- `Ship / SRV / SLF / Foot / Wing / Taxi / MC`: Which auto-rule contexts are configured for that profile.

Right-click a profile row for options:
- `Insert Row Above`
- `Insert Row Below`
- `Move Row Up`
- `Move Row Down`
- `Rename`
- `Delete Row`
- `Set Active`
- `Copy` / `Paste`

## Why Profile Order Matters
Profile order is important for auto rules.

When multiple non-default profiles match at the same time, **the first one in the list wins** (top to bottom).  
`Default` is fallback behavior and is not part of non-default tie-breaking.

Practical example:
- If both `PvE Ships` and `Trading` are assigned the `On Foot` auto rule, whichever appears higher in the table becomes active.

If auto rules do not match anything, profile selection falls back to your manual selection (or `Default` if needed).

If the auto rule selected is `In Main Ship`, then profile selection will be matched with the selected ships in the "In Scope Ships" scroll box.

## Create and Use Profiles (Quick Start)
1. In the table, right-click and choose `Insert Row Above` or `Insert Row Below`.
2. Rename the new row to something meaningful (for example `PvE Ships`, `Mining`, `On Foot`).
3. Select the profile row.
4. Under `Auto rules for selected profile`, check the contexts you want (`In Main Ship`, `In SRV`, `In SLF`, `On Foot`, etc.).
5. Click `Apply` in the rules section.
6. (Optional) Click `Set Active` to force a manual switch now.
7. Use `Move Row Up/Down` to set priority order.

## Ship-Scoped Rules and First-Time Ship List Population
For `In Main Ship`, you can optionally scope a profile to specific ships using the `In scope ships (optional)` table.

Important first-time behavior:
- That ship list is populated from Elite journal fleet/ship events.
- On a fresh setup, it may be empty at first.
- If empty, **swap ships at least once** at a shipyard so EDMC receives ship updates.
- After switching ships, return to the Profiles tab and the list should populate.

## Switching Profiles Manually
You can switch profiles without waiting for auto rules or selecting the active one in settings:
- Profiles tab: right-click row -> `Set Active`
- Chat command:
  - `!ovr profile <name>`
  - `!ovr profile next`
  - `!ovr profile prev`
  - `!ovr profiles` (show list/status)
- EDMCHotkeys actions:
  - `Set Overlay Profile`
  - `Next Overlay Profile`
  - `Previous Overlay Profile`

## Tips
- `Default` is the safe baseline. You can't change the order or auto rule selection.
- Put more specific profiles higher than broad ones.
- If automatic profile switching is not what you expect, review row order first, then context checkboxes.
- You can double click to set active, rename profile, or assign auto rules.
