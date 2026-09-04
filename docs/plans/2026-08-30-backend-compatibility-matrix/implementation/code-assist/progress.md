# Backend Compatibility Matrix Progress

## Phase tracking

| Phase | Status |
| --- | --- |
| 1. Explore and plan | Completed |
| 2. Documentation implementation | Completed |
| 3. Validation and handoff | Completed |
| 4. User-facing terminology refinement | Completed |
| 5. Backend-name simplification | Completed |
| 6. User-facing support-table rewrite | Completed |
| 7. Issue-evidence correction | Completed |
| 8. X11 scope correction | Completed |
| 9. Matrix-dimension clarification | Completed |
| 10. Platform grouping | Completed |
| 11. Linux desktop grouping | Completed |
| 12. Consolidated Linux table | Completed |
| 13. Explicit row labels | Completed |
| 14. Matrix scope clarification | Completed |

## Checklist

- [x] Identify the existing compatibility, architecture, validation, and wiki sources.
- [x] Define acceptance criteria and choose a documentation-structural validation strategy.
- [x] Draft the authoritative wiki matrix.
- [x] Link the matrix from the wiki sidebar.
- [x] Run structural and diff validation.
- [x] Replace internal refactor wording with plain validation terminology.
- [x] Recheck wiki terminology and Markdown integrity.
- [x] Replace matrix identifiers with friendly backend names.
- [x] Add a diagnostics-only identifier note and validate the page.
- [x] Replace the technical matrix with a simple support table.
- [x] Validate the simplified page and its sidebar link.
- [x] Review all open and closed GitHub issues for compatibility evidence.
- [x] Correct the matrix rows and add the installation-context distinction.
- [x] Narrow the X11 validation claim to GNOME/Mutter on Ubuntu 24.04.4 LTS.
- [x] Split the setup column into platform/desktop and display-session columns.
- [x] Group the support matrix by Windows and Linux.
- [x] Group Linux support rows by desktop/compositor before display session.
- [x] Consolidate Linux support into one table with grouped first-column values.
- [x] Repeat desktop/compositor values on every Linux matrix row.
- [x] State that the page is a runtime display compatibility matrix, not an installer matrix.

## Notes

The default code-assist scratchpad path was read-only in this checkout. These process
artifacts therefore live in the project planning area; the published user-facing document
will be placed in `docs/wiki` as requested.

## Validation evidence

- RED structural check: failed as expected before implementation because
  `docs/wiki/Backend-Compatibility.md` and its sidebar link did not exist.
- GREEN structural check: passed after implementation; it found the required title and
  sections plus the `[[Backend Compatibility]]` sidebar entry.
- `git diff --check`: passed.
- No unit or harness test was added or run because this change affects documentation only;
  it does not alter pure logic, `load.py` hooks, or runtime lifecycle behavior.

## Terminology refinement

- Replaced user-facing `fix219` and `closure` terminology with `validated`, `not yet
  validated`, and `implemented` language.
- Confirmed the wiki page no longer contains the internal refactor identifier.

## Backend-name simplification

- The user-facing matrix now lists friendly backend names only.
- Technical `family / instance` values are retained in one diagnostics-only note for
  support reports.

## User-facing support-table rewrite

- Replaced the technical compatibility matrix with a three-column support table:
  setup, status, and next action.
- Limited the page to `Validated`, `Available`, and `Not supported`; diagnostics keep
  the technical details needed for support.

## Issue-evidence correction

- Reviewed every open and closed GitHub issue, then used compatibility-relevant reports
  to correct the public claims.
- Linux X11 and GNOME Wayland remain `Validated`; GNOME's helper requirement and the
  known Firefox/Mutter limitation are called out separately.
- KDE/KWin, Hyprland, Sway/Wayfire, and generic Wayland are now `Not yet validated`.
  XWayland is a `Fallback`; COSMIC and Gamescope remain `Not supported`.
- Added an installation-context table so Flatpak and installer dependency checks are not
  misread as backend validation.
- Structural validation passed: required page sections and all matrix rows were found,
  the sidebar link was found, and `git diff --check` passed.

## X11 scope correction

- Replaced the overly broad `Linux X11` validated row with a precise `GNOME on X11
  (Ubuntu 24.04.4 LTS)` row.
- Added `Other Linux X11 desktop or distribution` as `Not yet validated`, separating
  generic implementation capability from demonstrated support.

## Matrix-dimension clarification

- Replaced the ambiguous `Your setup` column with `Platform / desktop` and `Display
  session`.
- Split COSMIC and Gamescope into individual rows and kept XWayland explicitly scoped to
  any Wayland desktop.

## Platform grouping

- Grouped the matrix into Windows and Linux sections.
- Kept the Linux table's desktop/compositor and display-session columns so the platform
  grouping does not obscure the actual compatibility dimensions.

## Linux desktop grouping

- Replaced the Linux-wide table with desktop/compositor groups.
- Each group lists its display-session status below the group heading, allowing GNOME's
  X11 and Wayland validation to be read together.

## Consolidated Linux table

- Replaced the per-desktop tables with one Linux table.
- Omitted repeated desktop/compositor values in the first column, grouping subsequent
  display-session rows visually without using unsupported Markdown table row spans.

## Explicit row labels

- Repeated the desktop/compositor value on every row, so each display-session entry is
  independently readable without relying on visual grouping.

## Matrix scope clarification

- Renamed the page to `Overlay runtime compatibility` and defined it as a runtime
  display matrix.
- Distinguished installer recognition and dependency setup from end-to-end runtime
  validation, with a link to the installation FAQ for distro-family details.
- Added Ubuntu 24.04.4 LTS to both validated GNOME rows.

## Commit

Not created: `git commit` could not create `.git/index.lock` because the checkout exposes
the `.git` directory as read-only. No index lock or staged change was created.
