# Distro Installation Compatibility Matrix Context

## Task

Publish a wiki page that documents Linux installer-recognition profiles and the exact
dependencies installed for each profile, without making runtime-backend claims.

## Existing documentation

- `scripts/install_matrix.json` is the source of truth for distribution IDs, package
  managers, and package lists.
- `scripts/install_linux.sh` installs core and Qt packages for all recognized sessions,
  Wayland packages only for detected Wayland sessions, and Flatpak add-ons only for a
  Flatpak EDMC installation.
- `overlay_client/requirements/base.txt` supplies `PyQt6`; `requirements/wayland.txt`
  supplies Wayland-specific Python dependencies.
- `Backend-Compatibility.md` is the separate runtime display matrix and must link here.

## Dependency map

`Distro-Installation-Compatibility.md` -> `install_matrix.json` (package source)

`Backend-Compatibility.md` -> `Distro-Installation-Compatibility.md` (scope boundary)

`_Sidebar.md` -> `Distro-Installation-Compatibility.md` (wiki navigation)

## Constraints and decisions

- Use the exact package names from the manifest.
- State that the profiles recognize distribution families rather than particular release
  versions.
- Document Python 3.10+, virtual-environment packages, Wayland-only dependencies, and
  Flatpak host-launch permission.
- No code or runtime behavior changes are required; documentation structural validation
  is the appropriate test type.
