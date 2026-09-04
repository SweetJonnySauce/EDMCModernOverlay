# Backend Compatibility Matrix Plan

## Acceptance criteria

1. A wiki page gives one concise matrix for Windows, X11, XWayland, named Wayland
   backends, unsupported environments, and Flatpak context.
2. Every row distinguishes the runtime classification from its validation/evidence status.
3. Requirements, fallbacks, and the supported diagnostic path are clear to users.
4. The page is linked from the wiki sidebar.

## Test strategy

This is a documentation-only change. A unit or harness test would not exercise a changed
behavior, so none will be added. Structural validation will instead confirm the new page,
its required headings, and its sidebar link; `git diff --check` will confirm Markdown
whitespace.

## Implementation stages

| Phase | Stage | Description | Status |
| --- | --- | --- | --- |
| 1 | 1.1 | Collect current selector vocabulary, fix219 policy, validation evidence, and wiki style | Completed |
| 2 | 2.1 | Draft the compatibility and backend matrix with evidence-aware language | Completed |
| 2 | 2.2 | Add the wiki navigation entry | Completed |
| 3 | 3.1 | Validate structure and review the final diff | Completed |
| 4 | 4.1 | Replace internal fix219/closure wording with user-facing validation terminology | Completed |
| 4 | 4.2 | Recheck terminology and Markdown integrity | Completed |
| 5 | 5.1 | Replace technical family/instance pairs in the user-facing matrix with friendly backend names | Completed |
| 5 | 5.2 | Retain the technical identifiers in a diagnostics-only note and validate the page | Completed |
| 6 | 6.1 | Replace the technical matrix with a user-facing support table based on common documentation patterns | Completed |
| 6 | 6.2 | Remove implementation detail from the main page and validate the simplified page | Completed |
| 7 | 7.1 | Map open and closed GitHub issues to each runtime row | Completed |
| 7 | 7.2 | Correct unsupported validation claims and separate installation contexts | Completed |
| 8 | 8.1 | Narrow the native-X11 validation claim to its actual GNOME/Ubuntu environment | Completed |
| 9 | 9.1 | Split the user setup column into platform/desktop and display-session columns | Completed |
| 10 | 10.1 | Group the support matrix by Windows and Linux, retaining desktop/session detail | Completed |
| 11 | 11.1 | Group Linux support rows by desktop/compositor before display session | Completed |
| 12 | 12.1 | Consolidate Linux desktop groups into one table with grouped first-column values | Completed |
| 13 | 13.1 | Repeat desktop/compositor values on every Linux matrix row | Completed |
| 14 | 14.1 | State the matrix scope and distinguish runtime validation from installer support | Completed |
