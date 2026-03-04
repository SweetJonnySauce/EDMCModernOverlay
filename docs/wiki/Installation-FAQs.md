## Python Environment:
All installations require the overlay client to have its own python environment. This is required for PyQt support. The installations will automatically build the environment for you. In the case of upgrades, you can chose rebuild the python environment or skip it.

## I'm on Windows and I'm getting a `System Python 3.10+ check failed` error. Why?

> 🔥🔥🔥 **Note:** As of release [0.7.7 Hotfix #2](https://github.com/SweetJonnySauce/EDMCModernOverlay/releases/tag/0.7.7-hotfix-2), the Windows .exe installer now downloads Python (with your permission) if it can't find or access a suitable version.🔥🔥🔥

EDMC Modern Overlay requires Python 3.10 or greater and the Windows installer was not able to validate that it has access to this dependency. You can check what version you're running by following these steps:
1. Hit Win+R
1. Type `cmd` and hit Enter
1. Enter the following. You should get a `0` in response if you have the correct version of Python installed.
    ```
    python -c "import sys; print(sys.version); sys.exit(0 if sys.version_info >= (3,10) else 1)" & echo ExitCode=%ERRORLEVEL%
    ```
1. Alternatively, if it doesn't recognize "python", you could try
    ```
    py -3-c "import sys; print(sys.version); sys.exit(0 if sys.version_info >= (3,10) else 1)" & echo ExitCode=%ERRORLEVEL%
    ```

Now verify that Python is available in your $PATH. In the same cmd window type the following. You should get back the location of where Python is installed.
``` 
where python
```


If these steps fail or give you an error, you'll need to correct the issue before you install EDMC Modern Overlay

## EUROCAPS.ttf: 
The install asks you to confirm you have a license to install EUROCAPS.ttf. [Why do I need a license for EUROCAPS.ttf?](docs/FAQ.md#why-do-i-need-a-license-for-eurocapsttf)

## Integrity checks: 
Releases ship a `checksums.txt` manifest. Both installers (`install_linux.sh` and `install_windows.ps1`) verify the extracted bundle and the installed plugin files against that manifest; if verification fails, re-download the release and re-run the installer.

## Linux Dependency Packages:
`install_linux.sh` reads `install_matrix.json` and installs the distro-specific prerequisites for the overlay client. The manifest currently checks for and pulls in if necessary:
  - Debian / Ubuntu: `python3`, `python3-venv`, `python3-pip`, `rsync`, `curl`, `wmctrl`, plus Qt helpers `libxcb-cursor0`, `libxkbcommon-x11-0` and Wayland helpers `x11-utils`
  - Fedora / RHEL / CentOS Stream: `python3`, `python3-pip`, `python3-virtualenv`, `rsync`, `curl`, `wmctrl`, `libxkbcommon`, `libxkbcommon-x11`, `xcb-util-cursor`, and Wayland helpers `xwininfo`, `xprop`
  - openSUSE / SLE: `python3`, `python3-pip`, `python3-virtualenv`, `rsync`, `curl`, `wmctrl`, plus Qt helpers `libxcb-cursor0`, `libxkbcommon-x11-0`, and Wayland helpers `xprop`, `xwininfo`
  - Arch / Manjaro / SteamOS: `python`, `python-pip`, `rsync`, `curl`, `wmctrl`, plus Qt helpers `libxcb`, `xcb-util-cursor`, `libxkbcommon`, and Wayland helpers `xorg-xprop`, `xorg-xwininfo`
  - Wayland-only Python dependency `pydbus` is installed inside `overlay_client/.venv` from `overlay_client/requirements/wayland.txt` when a Wayland session is detected; no system package is required.
  
## Compositor-aware overrides (Linux): 
`install_linux.sh` detects your compositor (via `install_matrix.json`) and can offer compositor-specific env overrides (e.g., Qt scaling tweaks on KDE/Wayland). Use `--compositor auto|<id>|none` to control this and `--yes` to auto-apply. Accepted overrides are stored in `overlay_client/env_overrides.json` with provenance; user-set env vars always win at runtime. Force Xwayland is only set when the manifest entry requests it.

## Installation dependency for x11 tools isn't found 
If you do a Linux install and you get an error that the x11 dependency can't be found or installed, you may be hitting this [bug](https://github.com/SweetJonnySauce/EDMC-ModernOverlay/issues/15). There isn't a fix for this yet but you may be able to work around this. You specifically need `xwininfo` and `xprop`. If you have those installed, or can install them manually, then you should be able to install without the needed dependency.

## Clamp fractional desktop scaling (physical clamp):
Opt-in setting in EDMC → File → Settings → EDMCModernOverlay. Fractional scaling means your OS display scale is a non-integer (e.g., 125%, 140%) to make UI elements larger; on some setups that can shrink or offset the overlay. Turn this on to keep a 1:1 mapping in those cases; leave it off for integer scales, true HiDPI, or mixed-DPI displays.

## Flatpack Sandboxing:
The Flatpak version of EDMC runs in a sandboxed environment. The sandboxed environment does not include the packages needed to run the overlay client. Because of this, the client will be launched outside of the sandboxed environment. You should only run this plugin if you trust the plugin code and the system where it runs.

  > **Caution:** Enabling the host launch runs the overlay client outside the Flatpak sandbox, so it inherits the host user’s privileges. Only do this if you trust the plugin code and the system where it runs.

## Flatpak D-Bus access:
Running the plugin via Flatpak EDMC requires a user permission to be added to enable D-Bus access to `org.freedesktop.Flatpak`. The Linux installer now detects for this and prompts you to grant permission. It does not automatically grant that permission. This is needed because the plugin client uses the following override when launching the client:
  ```bash
  flatpak override --env=EDMC_OVERLAY_HOST_PYTHON=/path/to/python io.edcd.EDMarketConnector
  ```

  The Flatpak host launch requires D-Bus access to `org.freedesktop.Flatpak`. Grant it once (per-user if the Flatpak was installed with `--user`):
  ```bash
  flatpak override --user io.edcd.EDMarketConnector --talk-name=org.freedesktop.Flatpak
  ```
  The auto-detection prioritises `EDMC_OVERLAY_HOST_PYTHON`; otherwise it falls back to `overlay_client/.venv/bin/python`.

## The overlay becomes crunchy/difficult to read on Proton
A CMDR using the Windows version of EDMCModernOverlay within Proton reported heavy distortion of the overlay (reported on <https://github.com/SweetJonnySauce/EDMCModernOverlay/issues/169>). Their solution was to use Proton Experimental when they launch Elite Dangerous.

## ⚠️ Breaking upgrade notice:
Modern Overlay as of 0.7.4 now installs into the `EDMCModernOverlay/` directory. Running the installer will disable any existing `EDMC-ModernOverlay/` folder by renaming it to `EDMC-ModernOverlay.disabled`, `EDMC-ModernOverlay.1.disabled`, etc. Settings are **not** migrated automatically; keep the disabled folder if you need to roll back.