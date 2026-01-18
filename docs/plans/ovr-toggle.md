## Goal: Add a toggle argument to the overlay launch command to toggle the overlays on and off.

## Requirements
- Add a new settings field under "Chat command to launch controller" for the overlay toggle argument.
- Default toggle argument value is `t`.
- Toggle argument input validation: allow only alphanumeric characters (A-Z, a-z, 0-9); reject punctuation/whitespace.
- Toggle argument should not be numeric-only to avoid collision with the existing opacity argument.
- Toggle argument matching is case-insensitive (e.g., `T` and `t` are equivalent).
- Toggle argument may be multi-character (e.g., `tog`).
- Trim leading/trailing whitespace before validating the toggle argument.
- If the toggle argument is numeric-only, show a validation error and reject the setting.
- If the toggle argument is empty after trimming, fall back to the default `t`.
- Validation errors for the toggle argument should be surfaced in the settings UI status line (same status line used by other preferences updates).
- When the user passes the toggle argument (default `t`) as an argument to the chat command, toggle the overlay opacity.
- If both opacity and toggle arguments are provided, opacity takes precedence.
- When an opacity argument is present, ignore the toggle argument regardless of order.
- If the opacity argument is invalid, ignore all input (no toggle).
- Off is defined as opacity `0`.
- On is defined as any opacity > `0`.
- Toggle behavior: if opacity > 0, store the current opacity as the last-on value and set opacity to 0; if opacity is 0, restore the last-on value (default to 100 if none recorded).
- Toggle persists by updating the stored opacity setting.

## Refactorer Persona
- Bias toward carving out modules aggressively while guarding behavior: no feature changes, no silent regressions.
- Prefer pure/push-down seams, explicit interfaces, and fast feedback loops (tests + dev-mode toggles) before deleting code from the monolith.
- Treat risky edges (I/O, timers, sockets, UI focus) as contract-driven: write down invariants, probe with tests, and keep escape hatches to revert quickly.
- Default to “lift then prove” refactors: move code intact behind an API, add coverage, then trim/reshape once behavior is anchored.
- Resolve the “be aggressive” vs. “keep changes small” tension by staging extractions: lift intact, add tests, then slim in follow-ups so each step stays behavior-scoped and reversible.
- Track progress with per-phase tables of stages (stage #, description, status). Mark each stage as completed when done; when all stages in a phase are complete, flip the phase status to “Completed.” Number stages as `<phase>.<stage>` (e.g., 1.1, 1.2) to keep ordering clear.
- Personal rule: if asked to “Implement…”, expand/document the plan and stages (including tests to run) before touching code.
- Personal rule: keep notes ordered by phase, then by stage within that phase.

## Dev Best Practices

- Keep changes small and behavior-scoped; prefer feature flags/dev-mode toggles for risky tweaks.
- Plan before coding: note touch points, expected unchanged behavior, and tests you’ll run.
- Avoid UI work off the main thread; keep new helpers pure/data-only where possible.
- When touching preferences/config code, use EDMC `config.get_int/str/bool/list` helpers and `number_from_string` for locale-aware numeric parsing; avoid raw `config.get/set`.
- Record tests run (or skipped with reasons) when landing changes; default to headless tests for pure helpers.
- Prefer fast/no-op paths in release builds; keep debug logging/dev overlays gated behind dev mode.

## Per-Iteration Test Plan
- **Env setup (once per machine):** `python3 -m venv .venv && source .venv/bin/activate && pip install -U pip && pip install -e .[dev]`
- **Headless quick pass (default for each step):** `source .venv/bin/activate && python -m pytest` (scope with `tests/…` or `-k` as needed).
- **Core project checks:** `make check` (lint/typecheck/pytest defaults) and `make test` (project test target) from repo root.
- **Full suite with GUI deps (as applicable):** ensure GUI/runtime deps are installed (e.g., PyQt for Qt projects), then set the required env flag (e.g., `PYQT_TESTS=1`) and run the full suite.
- **Targeted filters:** use `-k` to scope to touched areas; document skips (e.g., long-running/system tests) with reasons.
- **After wiring changes:** rerun headless tests plus the full GUI-enabled suite once per milestone to catch integration regressions.

## Guiding Traits for Readable, Maintainable Code
- Clarity first: simple, direct logic; avoid clever tricks; prefer small functions with clear names.
- Consistent style: stable formatting, naming conventions, and file structure; follow project style guides/linters.
- Intent made explicit: meaningful names; brief comments only where intent isn’t obvious; docstrings for public APIs.
- Single responsibility: each module/class/function does one thing; separate concerns; minimize side effects.
- Predictable control flow: limited branching depth; early returns for guard clauses; avoid deeply nested code.
- Good boundaries: clear interfaces; avoid leaking implementation details; use types or assertions to define expectations.
- DRY but pragmatic: share common logic without over-abstracting; duplicate only when it improves clarity.
- Small surfaces: limit global state; keep public APIs minimal; prefer immutability where practical.
- Testability: code structured so it’s easy to unit/integration test; deterministic behavior; clear seams for injecting dependencies.
- Error handling: explicit failure paths; helpful messages; avoid silent catches; clean resource management.
- Observability: surface guarded fallbacks/edge conditions with trace/log hooks so silent behavior changes don’t hide regressions.
- Documentation: concise README/usage notes; explain non-obvious decisions; update docs alongside code.
- Tooling: automated formatting/linting/tests in CI; commit hooks for quick checks; steady dependency management.
- Performance awareness: efficient enough without premature micro-optimizations; measure before tuning.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Preferences + validation for toggle argument | Planned |
| 2 | Command handling + toggle behavior | Planned |
| 3 | Unit tests + verification | Planned |

## Phase Details

### Phase 1: Preferences + toggle validation
- Add preferences fields for the toggle argument (default `t`) and the last-on opacity value used for restores.
- Persist new fields in EDMC config + `overlay_settings.json` shadow file (load + save).
- Add validation/normalization helper that trims whitespace, enforces alphanumeric-only, rejects numeric-only, and falls back to `t` when empty.
- Update the preferences UI under "Chat command to launch controller" with a new entry for the toggle argument and surface validation errors via the status line.
- Risks: silently accepting invalid toggle values or losing prior opacity value on toggle.
- Mitigations: validation helper + unit tests + status-line error reporting.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add preference fields + config/shadow persistence | Planned |
| 1.2 | Add validation helper + preferences UI entry + status line errors | Planned |
| 1.3 | Unit tests for validation + persistence | Planned |

### Phase 2: Command handling + toggle behavior
- Extend the journal command helper to accept a configurable toggle argument (case-insensitive match).
- If any opacity argument is present and valid, ignore toggle (regardless of order).
- If opacity argument is invalid and toggle is present, ignore all input.
- Implement toggle logic that stores last-on opacity when switching to 0 and restores last-on (default 100) when toggling back on.
- Ensure toggle persists by updating the stored preference values.
- Risks: breaking existing opacity command parsing or making toggle precedence inconsistent with requirements.
- Mitigations: dedicated unit tests for command parsing and toggle behavior.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Wire toggle argument into command helper/runtime | Planned |
| 2.2 | Implement toggle logic + last-on persistence | Planned |
| 2.3 | Update help text / messaging for toggle (if applicable) | Planned |

### Phase 3: Unit tests + verification
- Add/extend unit tests to validate all requirements:
- `tests/test_journal_commands.py`: toggle argument triggers toggle callback; case-insensitive match; multi-character toggle works; opacity args take precedence; invalid opacity + toggle ignores all input.
- `tests/test_journal_commands.py`: toggle off from >0 stores last-on value and sets 0; toggle on from 0 restores last-on; default restore to 100 when no last-on stored.
- `tests/test_preferences_persistence.py`: new toggle argument + last-on opacity persist to config and shadow JSON; reload restores values.
- New validation helper tests (new file or add to `tests/test_font_bounds_validation.py`-style module) covering trim, alphanumeric-only, numeric-only rejection, and empty fallback.
- Run focused tests: `python -m pytest tests/test_journal_commands.py tests/test_preferences_persistence.py` (plus any new validation test file).

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Implement unit tests for command parsing + toggle behavior | Planned |
| 3.2 | Implement unit tests for preferences persistence + validation | Planned |
| 3.3 | Run targeted pytest selections | Planned |
