# Vendored Harness Notes

This repository vendors a snapshot of the BGS-Tally EDMC test harness for
integration-style plugin testing.

## Upstream Source

- Repository: `https://github.com/aussig/BGS-Tally`
- Branch at selection time: `feature/Issue-454/test-harness`
- Pinned commit: `3e5fe957d299a43e28a64df35145f569c5ad0a7f`
- Vendored paths:
- `tests/harness.py`
- `tests/edmc/**` (including `tests/edmc/plugins/**`)
- `tests/__init__.py` was vendored, then adapted to lazy import for local pytest stability.

## Ownership Rules

- Immutable upstream snapshot:
- `tests/harness.py`
- `tests/edmc/**`
- Project-owned integration layer:
- `tests/harness_bootstrap.py`
- `tests/overlay_adapter.py`
- `tests/config/**`
- `tests/test_harness_integration.py`
- `tests/test_harness_chat_commands.py`
- `tests/test_harness_dashboard_profiles.py`

## Why Bootstrap Exists

The vendored harness executes module-level mocks and Tk setup at import time.
`tests/harness_bootstrap.py` isolates that behavior so the rest of the repo's
test suite is not contaminated by vendored global module overrides.

It also provides:
- explicit `semantic_version` dependency validation (from `requirements/dev.txt`),
- headless Tk import stubs for CI/dev shells without a display,
- deterministic harness defaults (`commander`, `is_beta`, `system`),
- a stable helper to create/stop harness-backed runtime tests.

## Running Harness Tests

- Install dev dependencies first (includes `semantic-version`):
- `python -m pip install -r requirements/dev.txt`
- Run harness tests only:
- `overlay_client/.venv/bin/python -m pytest -m harness -q`
- Run chat-command replay test only:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_chat_commands.py -q`
- Run startup/adapter smoke tests only:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_integration.py -q`
- Run dashboard/profile harness tests only:
- `overlay_client/.venv/bin/python -m pytest tests/test_harness_dashboard_profiles.py -q`

Harness tests are part of default `make check`.
