# Distro Installation Compatibility Matrix Progress

## Phase tracking

| Phase | Status |
| --- | --- |
| 1. Explore and plan | Completed |
| 2. Documentation implementation | Completed |
| 3. Validation and handoff | Completed |
| 4. Common Python requirements | Completed |

## Checklist

- [x] Identify the manifest, installer, virtual-environment, and Flatpak sources.
- [x] Define installer compatibility separately from runtime compatibility.
- [x] Document all distribution profiles and exact package dependencies.
- [x] Link the installer matrix from the runtime matrix and sidebar.
- [x] Run structural and whitespace validation.
- [x] Move common Python requirements out of the profile dependency matrix.

## Validation evidence

- Verified every manifest distribution profile, profile ID list, package manager, and
  package category appears on the wiki page.
- Verified the sidebar entry and reciprocal runtime/installer wiki links.
- `git diff --check` passed.
- No unit or harness test applies: this change does not alter runtime code, installer
  behavior, or `load.py` hooks.

## Commit

Not created: the checkout exposes `.git` as read-only, so Git cannot create its index
lock. No files were staged.

## Common Python requirements

- Moved the shared conceptual requirement—Python 3.10+, pip, and virtual-environment
  support—into the common section.
- Kept a compact profile-to-package-name table because Debian, Fedora/SUSE/Bazzite, and
  Arch provide that common capability through different package names.
- Reduced the main dependency matrix to the remaining base, Qt/X11, Wayland, and Flatpak
  packages.
