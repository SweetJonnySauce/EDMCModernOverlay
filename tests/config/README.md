# Harness Config Fixtures

This directory stores project-owned fixture files used by the vendored
BGS-Tally harness snapshot.

Ownership rules:
- `tests/harness.py` and `tests/edmc/**` are immutable vendored upstream files.
- Files in `tests/config/**` are local project fixtures and may be extended over time.

Primary fixture path used by harness tests:
- `tests/config/journal_events.json`
- `tests/config/overlay_groupings.user.json` (seed profile/group override store for harness profile lifecycle tests)
