## I've installed EDMCModernOverlay but I'm not seeing any of the on-screen messages like the image on the main README file?  
EDMCModernOverlay by itself doesn't display anything on screen (except for maybe a status message in the lower left hand corner if you turn it on). Other EDMC plugins send overlay messages called "payloads" to EDMCModernOverlay to display on screen for you. 

Test the overlay by following these [troubleshooting steps](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Troubleshooting#how-to-test-that-the-overlay-is-working).

## What EDMC plugins is EDMCModernOverlay compatible with?  
EDMCModernOverlay is compatible with any plugin that is also compatible with EDMC. It's up to that plugin to decide to implement an overlay feature. What is displayed on screen is decided by the other plugins, not by EDMCModernOverlay.

## Does EDMCModernOverlay work with EDR "out of the box"?
Yes! EDMCModernOverlay does work with [EDR](https://github.com/lekeno/edr) "out of the box" without any major issues. In fact, you can see four "out of the box" EDR overlays in the screenshot in the [README.md](https://github.com/SweetJonnySauce/EDMCModernOverlay/blob/main/README.md) file of this repo. There is one caveat to note though regarding aspect ratios of how the graphs are displayed that can be easily be overcome by setting some overlay configs in EDR. See https://github.com/SweetJonnySauce/EDMCModernOverlay/issues/47 for more information. There is one open issue regarding EDR Navroute not being stretched across the entire width of Ultrawide monitors. It is also described in the previously mentioned Github issue.

## I'm seeing plugin groups in the Overlay Controller that are duplicate or don't make sense.
The Overlay Controller maintains a cache of plugin groups. It maintains this cache so it knows where the overlay is placed even if it isn't being currently displayed on the screen. There are situations where updates to plugins could cause duplicate or incorrect cache entries. If you see this happen you will want to reset the Overlay Controller cache.

## How do I reset the Overlay Controller cache?
1. Go to EDMC Settings (File > Settings)
1. Navigate to the EDMCModernOverlay tab
1. Hit the "Reset Cached Values" button
<img width="778" height="452" alt="image" src="https://github.com/user-attachments/assets/d6a021c6-79a6-409b-b5c2-abf8eb94a548" />

## How come I don't see the plugin I just installed in the Overlay Controller drop down box?
That's expected under certain conditions. EDMCModernOverlay populates the cache when it first "sees" the overlay on screen. You will want to trigger the action in-game to see the overlay (i.e. Dock at a station so the LandingPad graphic is shown). Once you do that, you can then manipulate it in the Overlay Controller.

## I reset the Overlay Controller cache and now there's nothing in the Overlay Controller drop down box!
See the FAQ "How come I don't see the plugin I installed in the Overlay Controller drop down box?"

## Can I launch the Overlay Controller via a button on my controller or via an in-game control option?
In short, no. It is something I want to be able to implement but would require the plugin to intercept keyboard and controller input globally. A core tenet of the plugin is to be cross-platform compatible and Wayland on Linux would block this behavior. It is possible that this may be implemented as an Experimental feature in the future (where I'm ok with not having cross platform compatibility).

One work-around is to set an Elite Dangerous hotkey/keybind to enter chat mode in-game. In Elite Dangerous, go to Options > Controls > Ship Controls > Mode Switches > Quick Comm to set the hotkey/keybind. From there, for example, if you use a Quick Comm key of `x` then you could conceivably launch the controller using a keyboard macro that sends `x !ovr` that is bound to a key or control pad button.

## Does EDMCModernOverlay support VR?
Maybe? Sort of? Yes!?!

In SteamVR there is an option to add a floating window in the 3D space of any application that is already active and visible in the Taskbar. For example Discord, YouTube ... and now EDMCModernOverlay if the experimental feature for "Standalone Mode" is enabled.
Standalone mode is available in 0.7.7 as a windows-only experimental feature. 

To enable this feature, install EDMCModernOverlay on a Windows PC, open up EDMC Settings and navigate to the EDMCModernOverlay settings tab. On that page, go to "Experimental" and check the box to "Run overlay in standalone-mode (Windows Only)". No restart required and you should now see the overlay as a separate icon on your task bar. 

I am not certain how well this works. The feature was developed for another reason so this is a happy accident. If you try this out, I'd love to hear your results (and maybe some more details on how you got it working).

<img width="681" height="481" alt="image" src="https://github.com/user-attachments/assets/349f12e5-45f2-4ac1-976d-316d27872612" />

<img width="766" height="629" alt="image" src="https://github.com/user-attachments/assets/f6a2f6b2-022f-46bd-b677-3b81523e0ff7" />
