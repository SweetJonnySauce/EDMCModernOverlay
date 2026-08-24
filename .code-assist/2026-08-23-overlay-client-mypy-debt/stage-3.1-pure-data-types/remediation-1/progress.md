# Stage 3.1 Remediation 1 Progress

## Setup

- [x] Created isolated stage-local documentation and `logs/` directory.
- [x] Read governing, Stage 3.1 predecessor, and independent fix219/X11 records.
- [x] Confirmed the target worktree already contains the predecessor's annotation-only
  `follow_geometry.py` changes; `plugin_overrides.py` and `transform_helpers.py` have no prior
  worktree diff.

## Implementation

- [x] Capture normal six-module mypy RED evidence: 9 errors in 4 files.
- [x] Correct the four common-origin float declarations.
- [x] Correct the two `PrefixEntry` tuple declarations.
- [x] Correct the two point-tuple declarations.
- [x] Preserve `payload_model.py:98` unchanged; it is the sole GREEN diagnostic.

## Validation and handoff

- [x] Capture normal six-module mypy GREEN evidence: 1 retained TTL error in 1 file.
- [x] Run the prescribed pure-unit slice: 90 passed in 0.37s.
- [x] Run scoped Ruff and `git diff --check`: both passed.
- [x] Review bounded diff and write six-field handoff.

## Decision record

No runtime code path changed. `native_origin_x` and `native_origin_y` are declared `float` at
the common assignment seam before mutually exclusive branches assign them. The pre-existing
`PrefixEntry` tuple contract now matches `_clean_group_prefixes`, and two-element transformed
points are materialized as exact two-coordinate tuples. The direct `int()` TTL coercion remains
untouched because this context does not authorize a runtime input-contract decision.
