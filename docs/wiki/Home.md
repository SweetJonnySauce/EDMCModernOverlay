# EDMC Modern Overlay (beta)
[![Github All Releases](https://img.shields.io/github/downloads/SweetJonnySauce/EDMCModernOverlay/total.svg)](https://github.com/SweetJonnySauce/EDMCModernOverlay/releases/latest)
[![GitHub Latest Version](https://img.shields.io/github/v/release/SweetJonnySauce/EDMCModernOverlay)](https://github.com/SweetJonnySauce/EDMCModernOverlay/releases/latest)
[![Build Status][build-badge]][build-url]

[build-badge]: https://github.com/SweetJonnySauce/EDMCModernOverlay/actions/workflows/ci.yml/badge.svg?branch=main
[build-url]: https://github.com/SweetJonnySauce/EDMCModernOverlay/actions/workflows/ci.yml

EDMC Modern Overlay (packaged as `EDMCModernOverlay`) replaces [EDMCOverlay](https://github.com/inorton/EDMCOverlay) and [edmcoverlay2](https://github.com/pan-mroku/edmcoverlay2). It is a cross-platform (Windows and Linux) plugin for Elite Dangerous Market Connector ([EDMC](https://github.com/EDCD/EDMarketConnector)). It streams data from other EDMC plugins to be displayed in your game window. EDMCModernOverlay supports fullscreen, borderless, and windowed mode on any display size. It also now has a standalone mode as an experimental feature in 0.7.7 for use in SteamVR. The [plugin releases](https://github.com/SweetJonnySauce/EDMC-ModernOverlay/releases/latest) include Windows (powershell and .exe) and Linux installers.

CMDRs can customize the placement of plugin payloads on their game window using the [Overlay Controller](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Overlay-Controller). You can change X/Y placement, anchor point, text justification, and add/change background colors for each plugin display.

<img width="819" height="523" alt="image" src="https://github.com/user-attachments/assets/60ad5d24-11b3-47cb-9ab1-aa8173479128" />


# Key Features
- Backwards compatibility with [EDMCOverlay](https://github.com/inorton/EDMCOverlay)
- Custom placement of Plugin overlays using the Overlay Controller (see the [Wiki for Overlay Controller](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Overlay-Controller))
- Works in borderless or windowed mode on any display size
- Cross platform for Windows and Linux
- Support 4 distributions for Linux (Debian, Fedora, OpenSUSE, Arch)
- Supports host and Flatpak installs of EDMC on Linux
- Code is 100% Python
- Numerous development features for EDMC Plugin Developers

# Installation & Upgrades

## Installation
See the [Wiki for Prerequisites and Installation](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Installation). Refer to the [Installation FAQ](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Installation-FAQs) for more OS and distro specific details.

## Upgrades
See the [Wiki for Upgrading](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Upgrading)

# Using EDMC Modern Overlay
See the [Wiki for Usage](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Usage) for how to run the game with the HUD and configure settings.

See the [Wiki for Overlay Controller ](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Overlay-Controller) for how to modify where overlays are placed on the game screen.

   
# Support
Best way to get support for this plugin is to create a github issue in this repo. This is a side project for me. As such, support is best effort only and there is no guarantee I'll be able to fix or fully address your issue/request. You can occassionally find me on [EDCD Discord](https://edcd.github.io/) in the `#edmc-plugins` channel.

# Thanks
Special thanks to [inorton](https://github.com/inorton) for the original [EDMCOverlay](https://github.com/inorton/EDMCOverlay) development.

# Blame
First and foremost, this EDMC plugin is a learning experiment in using AI for ground up development. The intent was never to get it to this point, but here we are. My goal was to avoid touching code and only use AI, and I've been very successful in reaching that goal. It was developed on VSCode using Codex (gpt-5-codex) for 99.999% of the code.
