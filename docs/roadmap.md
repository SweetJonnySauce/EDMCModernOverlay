# EDMCModernOverlay Roadmap

Here you'll find the general direction I'm taking EDMCModernOverlay. But it only makes sense if it's something that could be useful to the community. Comment on the associated tracker if you want to see this feature or have thoughts on how it should work. Full disclosure, this is a hobby for me, so there are no timelines assoicated with these items. The roadmap items are loosely prioritized but does not necessarily mean they will be released in that order. Some items like Linux standalone mode will be measurably harder to complete than Per-ship profiles.

Got an idea? Please open up a new issue for consideration/tracking.

| **Roadmap Item** | **Description** | **Tracker** |
| --- | --- | --- |
| Linux standalone mode | Allow the overlay to run as a standalone selectable app. Useful for selecting it in SteamVR (potentialy). | [Issue #193](https://github.com/SweetJonnySauce/EDMCModernOverlay/issues/193) |
| Steamdeck compatibility | Updates necessary to get the overlay to display on Steamdeck | [Issue #146](https://github.com/SweetJonnySauce/EDMCModernOverlay/issues/146) |
| Linux backend | Refactor the Linux implementation to create a capability driven subsystem | |
| Per-ship profiles | Enable per-ship overlay configuration profiles to be created and used. | [Issue #159](https://github.com/SweetJonnySauce/EDMCModernOverlay/issues/159) |
| Scaling controls | Enable CMDRs to grow/shrink overlays using the Overlay Controller. Scaling Controls plus some EDR config changes is expected to address the issue of EDR navroute not spanning the entire screen width on ultrawide monitors.  | [Issue #47](https://github.com/SweetJonnySauce/EDMCModernOverlay/issues/47#issuecomment-3902228152)|
| Run Headless | Run EDMCModernOverlay without EDMC. This would allow non-EDMC apps to use EDMCModernOverlay without EDMC. In theory, nothing should be stopping other apps from using EDMCModernOverlay today (all they need to do is send a well formed message to the socket) but this feature would allow the overlay to run without EDMC | [Issue #192](https://github.com/SweetJonnySauce/EDMCModernOverlay/issues/192) |
