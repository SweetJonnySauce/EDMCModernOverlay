The plugin makes the following network connections:

### Installation
- To Linux repos to install dependencies during plugin installation.

### Runtime
- To [GitHub](https://api.github.com/repos/SweetJonnySauce/EDMCModernOverlay/releases/latest) to check the version of the plugin to see whether there is a newer version available.

### GNOME Wayland helper

The GNOME Wayland helper is local-only. It is a GNOME Shell extension that communicates with the overlay client over the user's local session DBus service, `org.edmc.ModernOverlay.Helper`.

The helper does not create a network listener and does not make network connections. It observes limited GNOME Shell window metadata needed for overlay attachment, such as Elite Dangerous window title/class/app id, geometry, monitor, focus/visibility state, helper version, and helper protocol.

It does not capture screen contents, screenshots, keyboard input, mouse input, game data, or network traffic. Default diagnostics avoid broad process dumps, command lines, unrelated window-title dumps, and screenshots.
