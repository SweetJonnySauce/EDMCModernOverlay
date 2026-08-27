# Decisions and Requirements

## Q: What is the merge direction?

**Answer:** Merge `feature/circle-shape-pyqt-rendering` into
`backend-refactor-implementation`. The backend refactor remains the structural
baseline.

## Q: What happens to `overlay_groupings.json`?

**Answer:** Preserve the backend branch version in full. Do not include the
circle branch change in the merge commit.

## Q: What must be validated before committing?

**Answer:** Resolve all source/test conflicts, review auto-merged core paths,
run focused shape tests, run the GUI-enabled renderer tests, run the EDMC Python
compatibility script, run `make check`, and perform a manual overlay inspection.

## Q: What visual caveat must remain visible to reviewers?

**Answer:** The gallery's concentric circles share logical coordinates but do
not share a grouping transform. In Fill mode, they can appear offset when the
grouping file is intentionally preserved. This is not a circle geometry defect
and must not be used as an acceptance test for physical concentricity.
