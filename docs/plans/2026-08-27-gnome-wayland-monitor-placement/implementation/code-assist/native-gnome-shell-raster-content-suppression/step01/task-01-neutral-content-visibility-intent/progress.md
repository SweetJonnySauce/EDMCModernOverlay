# Progress: Neutral Content-Visibility Intent

## Checklist

- [x] Setup: created task directory and logs directory.
- [x] Explore: read task, design, lessons, orchestration, existing policy, and tests.
- [x] Plan: documented unit and boundary coverage.
- [x] RED: added tests before production implementation.
- [x] GREEN: implemented typed neutral intent derived from `content_visible`.
- [x] REFACTOR: inspected for policy duplication or boundary leakage; no further change needed.
- [x] Validate: ran focused tests, scoped lint, and `git diff --check`.
- [x] Commit: intentionally skipped; orchestration prohibits staging and commits.

## TDD record

### RED

The tests import `BackendPresentationContentVisibility` and require it on
policy decisions. The pre-change policy exposes only the boolean contract, so
the focused test run is expected to fail during import before implementation.

**Result:** expected failure confirmed. Pytest stopped during collection with
`ImportError: cannot import name 'BackendPresentationContentVisibility'` from
`overlay_client.backend.presentation_policy`.

### GREEN

Added the two-value `BackendPresentationContentVisibility` `str` enum and a
read-only `content_visibility` decision property. The property maps only the
existing `content_visible` boolean, so none of the policy return paths,
debounce thresholds, warmup logic, or lifecycle behavior changed.

**Result:** `22 passed in 0.14s` for the focused policy and architecture suite.

### REFACTOR and validation

The implementation needs no additional abstraction: the typed property is the
single policy seam and has no GNOME string, import, enum, or protocol
dependency. Ruff passed for the changed Python files and `git diff --check`
reported no whitespace errors.

## Test evidence

| Command | Result |
| --- | --- |
| `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_architecture_boundary.py -q` | RED: expected collection `ImportError` before implementation; GREEN: `22 passed in 0.14s`. |
| `source overlay_client/.venv/bin/activate && python -m ruff check overlay_client/backend/presentation_policy.py overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_architecture_boundary.py` | Passed. |
| `git diff --check` | Passed. |

## Completion status

Task complete. No files were staged or committed, as required by the
orchestration.

## Decisions

- Use a `str` enum with exactly `visible` and `suppressed`, matching backend
  enum conventions while remaining compositor-neutral.
- Derive the intent from `content_visible`; do not change policy return paths
  or follow-surface consumers.
