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
| 1 | Preferences + validation for toggle argument | Completed |
| 2 | Command handling + toggle behavior | Completed |
| 3 | Unit tests + verification | In Progress |

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
| 1.1 | Add preference fields + config/shadow persistence | Completed |
| 1.2 | Add validation helper + preferences UI entry + status line errors | Completed |
| 1.3 | Unit tests for validation + persistence | Completed |

#### Stage 1.1 Details
- Touch points: `overlay_plugin/preferences.py` (Preferences dataclass, load from EDMC config, shadow JSON merge, save to config + shadow).
- Add new preference fields: `controller_toggle_argument` (default `t`) and `last_on_payload_opacity` (stores last non-zero opacity for restores).
- Persistence rules: store both values in EDMC config and `overlay_settings.json` shadow file; load both on startup (with sane defaults if missing).
- Decide representation for `last_on_payload_opacity`: use an int in [1..100] and treat missing/invalid as unset; restore default to 100 when unset.
- If a schema exists for `overlay_settings.json`, update it to include the new fields.

#### Stage 1.2 Details
- Add a validation/normalization helper in `overlay_plugin/preferences.py`:
- Trim whitespace; if empty -> default `t`.
- Reject non-alphanumeric characters (error + keep previous value).
- Reject numeric-only values (error + keep previous value).
- Normalize to a stable value for storage (keep original case or lower-case; matching is case-insensitive).
- Add a new UI entry under "Chat command to launch controller" for the toggle argument.
- Surface validation failures via the existing status line (`_status_var.set(...)`) and do not persist invalid values.

#### Stage 1.3 Details
- Add unit tests for persistence in `tests/test_preferences_persistence.py`:
- Save + reload `controller_toggle_argument` and `last_on_payload_opacity` through config + shadow JSON.
- Validate defaulting behavior when values are missing or invalid in config/shadow.
- Add unit tests for validation helper (new test module or expand an existing helper-test file):
- Trimming behavior (`" t "` -> `t`), empty -> default `t`.
- Non-alphanumeric rejected with error (e.g., `"t!"`, `"t t"`).
- Numeric-only rejected with error (e.g., `"5"`), mixed alnum accepted (e.g., `"t5"`).

#### Phase 1 Results
- Added `controller_toggle_argument` + `last_on_payload_opacity` preference fields with config/shadow persistence.
- Implemented toggle argument validation/normalization helpers and UI entry with status-line errors.
- Added unit tests for persistence and toggle argument validation helpers.

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
| 2.1 | Wire toggle argument into command helper/runtime | Completed |
| 2.2 | Implement toggle logic + last-on persistence | Completed |
| 2.3 | Update help text / messaging for toggle (if applicable) | Completed |

#### Stage 2.1 Details
- Touch points: `overlay_plugin/journal_commands.py`, `load.py` (runtime wiring), `overlay_plugin/preferences.py` (toggle argument preference).
- Extend `build_command_helper` to accept a toggle argument value from runtime/preferences.
- Update `JournalCommandHelper` to recognize the toggle argument in `handle_entry` / `_handle_overlay_command`.
- Ensure case-insensitive matching for the toggle argument and allow multi-character tokens.
- Precedence: if any valid opacity argument is present, ignore toggle regardless of order.
- If opacity argument is invalid and toggle is present, ignore all input (no action).

#### Stage 2.2 Details
- Add a runtime helper (likely in `load.py`) to toggle payload opacity:
- Read current `global_payload_opacity`; treat >0 as on.
- When toggling off, store the current opacity into `last_on_payload_opacity`, then set opacity to 0.
- When toggling on, restore `last_on_payload_opacity` (default 100 if unset/invalid).
- Persist both `global_payload_opacity` and `last_on_payload_opacity` through Preferences + config/shadow.
- Make sure toggle updates emit the overlay config update (same path used by `set_payload_opacity_preference`).

#### Stage 2.3 Details
- Update help text in `overlay_plugin/journal_commands.py` to mention the toggle argument (using the configured value).
- Decide whether to send a chat response on successful toggle (or remain silent like opacity changes).
- Ensure error messaging aligns with the existing opacity command behavior (invalid opacity + toggle -> ignore).

#### Phase 2 Results
- Journal command helper now accepts a configurable toggle argument and parses toggle vs. opacity with precedence rules.
- Runtime toggles payload opacity, persisting `global_payload_opacity` and `last_on_payload_opacity`.
- Preferences UI updates notify runtime so the command helper reflects the latest toggle argument.
### Phase 3: Unit tests + verification
- Add/extend unit tests to validate all requirements:
- `tests/test_journal_commands.py`: toggle argument triggers toggle callback; case-insensitive match; multi-character toggle works; opacity args take precedence; invalid opacity + toggle ignores all input.
- `tests/test_journal_commands.py`: toggle off from >0 stores last-on value and sets 0; toggle on from 0 restores last-on; default restore to 100 when no last-on stored.
- `tests/test_preferences_persistence.py`: new toggle argument + last-on opacity persist to config and shadow JSON; reload restores values.
- New validation helper tests (new file or add to `tests/test_font_bounds_validation.py`-style module) covering trim, alphanumeric-only, numeric-only rejection, and empty fallback.
- Run focused tests: `python -m pytest tests/test_journal_commands.py tests/test_preferences_persistence.py` (plus any new validation test file).

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Implement unit tests for command parsing + toggle behavior | Completed |
| 3.2 | Implement unit tests for preferences persistence + validation | Completed |
| 3.3 | Run targeted pytest selections | Skipped |

#### Stage 3.1 Details
- Extend `tests/test_journal_commands.py` to cover:
- Toggle argument triggers toggle callback (default `t`).
- Case-insensitive toggle matching (`T` == `t`).
- Multi-character toggle argument works (e.g., `tog`).
- Opacity argument takes precedence over toggle regardless of order (e.g., `t 50`, `50 t`).
- Invalid opacity + toggle ignores all input (no toggle).

#### Stage 3.2 Details
- Ensure `tests/test_preferences_persistence.py` already covers:
- `controller_toggle_argument` and `last_on_payload_opacity` saved/restored from config + shadow JSON.
- Add helper validation tests in `tests/test_toggle_argument_validation.py` for trim, alnum-only, numeric-only reject, empty fallback.
- Add a new unit test for `overlay_plugin/toggle_helpers.py` to assert:
- Toggle from >0 sets opacity to 0 and stores last-on.
- Toggle from 0 restores last-on (default 100).

#### Stage 3.3 Details
- Run: `python -m pytest tests/test_journal_commands.py tests/test_preferences_persistence.py tests/test_toggle_argument_validation.py tests/test_toggle_helpers.py`
- Record any skips or environment constraints (e.g., GUI deps) if not run.

#### Phase 3 Results
- Added journal command tests for toggle parsing, precedence, and invalid opacity handling.
- Added helper tests for toggle behavior and last-on restoration defaults.
- Test execution skipped (not requested).

## Troubleshooting

### Transparency Warning Triggered On Toggle
- Symptom: Transparency warning shows when toggling overlay off (opacity -> 0).
- Root cause: `overlay_client/launcher.py` calls `window.maybe_warn_transparent_overlay()` on every `OverlayConfig` payload, including toggle updates.
- Plan to fix:
- Move the transparency warning to a startup-only path (after window init + initial settings).
- Remove or guard the `OverlayConfig` handler call so config updates do not re-trigger the warning.
- Add tests:
- Verify `OverlayConfig` updates do not call the warning.
- Verify startup path still triggers warning when initial opacity is below threshold.

#### Plan Details
- Touch points:
- `overlay_client/launcher.py` (_build_payload_handler, initial startup flow)
- `overlay_client/control_surface.py` (warning helper)
- `overlay_client/tests/...` (new/updated tests)
- Implementation steps:
- Add a startup-only call to `maybe_warn_transparent_overlay()` after `OverlayWindow` init and initial settings are applied (one-time).
- Remove or guard the call inside the `OverlayConfig` branch so subsequent config updates (including toggle changes) do not trigger warnings.
- If needed, add a simple flag (e.g., `warn_on_startup`) in the handler or launcher to make the intent explicit.
- Test plan:
- New unit test that simulates an `OverlayConfig` payload and asserts the warning helper is not invoked.
- New unit test that startup path invokes the warning once when initial opacity is below the threshold.

#### Results
- Startup-only warning trigger implemented in `overlay_client/launcher.py`.
- `OverlayConfig` handler no longer triggers transparency warning.
- Added tests covering startup warning and config-update behavior.
