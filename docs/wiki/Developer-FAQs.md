## What should I use for `msgid`?
Use a stable, lowercase prefix for your plugin, then a semantic suffix for the widget or slot, and finally any sort of unique identifier you may need  e.g. `myplugin-status-01`, `myplugin-alert-1`, `myplugin-dockhint-msg`. Keep it stable across updates so you can replace/clear the same item reliably. Using this naming structure is important for defining plugin groups.

## How do I handle multiple lines of text?
You can add `\n` to your message to get a newline. However, many plugin developers manage multiple lines by handling each line individually. The latter is the preferred approach.

## What is a plugin group and why do I want to define it?
EDMCModernOverlay allows for the grouping of payloads to facilitate placement in the game window and other features such as text justification and background colors. These groupings are defined by the `msgid` prefixes. 

Plugin groups only need to be defined once per plugin and in fact, EDMCModernOverlay ships with several pre-built plugin groups. The recommended good practice is to set your groups via `define_plugin_group` when the plugin starts.

>⚠️ `define_plugin_group` is not compatible with other overlays (EDMCOverlay, edmcoverlay2, etc). If you implement this, make sure to wrap it in a try/catch block and handle the error.

For graphics (typically built using vectors), plugin groups are also needed to make sure the image is scaled uniformly. Without groups, you'll get some pretty interesting results. Here's LandingPad without a defined Plugin Group...
<img width="357" height="307" alt="image" src="https://github.com/user-attachments/assets/3776499b-58ee-4395-a0ff-98943082f6d5" />

## Can I add my plugin group to `overlay_groupings.json` and submit it for a PR?
You can, but I encourage you to implement it via `define_plugin_group` instead. That gives you total control over how your overlay is grouped.

## Do I really need to define a plugin group?
It depends, but it is a good practice. If you have simple payloads that only consist of text then you probably could get away with not having to define a plugin group. However, if you have something more complex like a vector image or are mixing text, shapes, and raw payloads you will need to define a plugin group so the overlay scales correctly.

## Where is the X/Y relative to my text string?
The X/Y position is the upper left point of the text string.

## Are any other shapes aside from rectangles supported?
No. If you want to do more complex objects, use send_raw and vect images.

## How do I add emojis to my text?
Just include the actual Unicode emoji in the text you send; Modern Overlay is Unicode‑safe end‑to‑end (i.e. `text="Mission logged 📝"`). If you prefer escape names in Python, use N{...} in a normal string (not a raw string). 

## What's the size different for the named font sizes?
Normal is 12 pixels and the difference between other named sizes (font step) is about 4 pixels in the legacy overlays. In EDMCModernOverlay font step defaults to 4 and is CMDR configurable in settings.

<img width="353" height="214" alt="image" src="https://github.com/user-attachments/assets/bb10d9c9-6fe9-4a61-8e8a-fe40db3783ab" />


