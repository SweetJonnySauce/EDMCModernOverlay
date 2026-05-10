# Prerequisites

- Python 3.10+
- Elite Dangerous Market Connector installed
- On Windows, Powershell 3 or greater is required for the Powershell installation option

# Installation Options
Chose one of three installation options (details below):
  - **[Option 1](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Installation#option-1--windows-standalone-exe):**  Windows (standalone EXE)
  - **[Option 2](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Installation#option-2-windows-powershell-script):** Windows (Powershell script)
  - **[Option 3](https://github.com/SweetJonnySauce/EDMCModernOverlay/wiki/Installation#option-3-linux-distro-aware):** Linux (distro aware)

## **Option 1:**  Windows (standalone EXE)
`EDMCModernOverlay-windows-<version>.exe` 

Download the latest `EDMCModernOverlay-windows-<version>.exe` file from Assets at the bottom of the [GitHub Releases](https://github.com/SweetJonnySauce/EDMC-ModernOverlay/releases/latest) section and run it. You will need to accept the "Microsoft Defender SmartScreen prevented an unrecognized app from starting." warning when installing by clicking on "More info...". This will take you to the next prompt where you choose "Run Anyway".

<img width="263" height="244" alt="image" src="https://github.com/user-attachments/assets/65c2d350-0a0e-43e7-adc7-7d0ee54f0dca" />


## **Option 2:** Windows (Powershell script)
`EDMCModernOverlay-windows_powershell-<version>.zip`

Download the latest EDMCModernOverlay-windows_powershell-<version>.zip file from Assets at the bottom of the [GitHub Releases](https://github.com/SweetJonnySauce/EDMC-ModernOverlay/releases/latest) section.
This will include `EDMCModernOverlay/`, `install_windows.ps1` so you can inspect and run the script directly, and `checksums.txt` which is used to ensure file integrity of the downloaded zip file. Extract the files and run `install_windows.ps1` in PowerShell from the extracted directory.

Run from a powershell prompt as `.\install_windows.ps1 -?` for more options.

## **Option 3:** Linux (distro aware)
`EDMCModernOverlay-linux-<version>.tar.gz`

Download the latest `EDMCModernOverlay-linux-<version>.tar.gz` file from Assets at the bottom of the [GitHub Releases](https://github.com/SweetJonnySauce/EDMC-ModernOverlay/releases/latest) section.
This will include `EDMCModernOverlay/`, `install_linux.sh`, the distro manifest `install_matrix.json`, and `checksums.txt` which is used to ensure file integrity of the downloaded archive file. Extract the archive and run `install_linux.sh` from the extracted directory via a terminal window.

Run `./install_linux.sh -h` from the command line for more options.

### GNOME Wayland helper

On GNOME Wayland, Modern Overlay uses a local GNOME Shell extension helper for overlay attachment. The helper is installed only when the Linux installer detects a GNOME Wayland session and you approve the helper install.

The helper install flow checks for:
- a GNOME Shell Wayland session
- a user DBus session bus
- `gnome-extensions`
- `gjs`
- `gdbus`
- the packaged helper source directory, `helpers/gnome_shell_extension/`

When approved, the installer copies the helper source directory to:

```bash
~/.local/share/gnome-shell/extensions/edmc-modern-overlay-helper@edmcmodernoverlay.github.io/
```

The installer does not silently change GNOME's global user-extension setting. If user extensions are globally disabled, it prints the manual remediation command for you to run. After helper install, update, disable, or uninstall, log out and log back in before treating the helper state as final.

If you installed Modern Overlay while using X11 and later switch to GNOME Wayland, rerun the Linux installer while logged into GNOME Wayland. The installer will detect the GNOME Wayland session and offer the helper install flow.

Use this command after logging back in to check helper state:

```bash
./install_linux.sh --gnome-helper-action status
```

GNOME Wayland overlay use supports Elite Dangerous windowed and borderless fullscreen modes. Exclusive fullscreen is not a supported mode for the GNOME Wayland overlay path.
