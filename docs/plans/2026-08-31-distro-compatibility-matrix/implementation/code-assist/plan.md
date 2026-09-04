# Distro Installation Compatibility Matrix Plan

## Acceptance criteria

1. A wiki page defines itself as installer compatibility, not runtime display support.
2. Every `install_matrix.json` distribution profile, recognized ID, package manager, and
   dependency category appears in the matrix.
3. Python, Wayland virtual-environment dependencies, and Flatpak permission requirements
   are documented.
4. The runtime matrix and wiki sidebar link to the new page.

## Test strategy

This is a documentation-only change. No unit or harness test applies. Structural checks
will confirm the new page's required sections, all five distribution profiles, and both
wiki links. `git diff --check` will verify whitespace.

## Implementation stages

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 1 | 1.1 | Read installer manifest, Linux installer behavior, and existing wiki style | Completed |
| 2 | 2.1 | Draft installer compatibility page with profile-specific dependencies | Completed |
| 2 | 2.2 | Link the runtime matrix and wiki sidebar | Completed |
| 3 | 3.1 | Validate page structure, package coverage, and final diff | Completed |
| 4 | 4.1 | Factor common Python requirements out of the profile dependency matrix | Completed |
