## Goal: Provide a limited set of additional command that a CMDR can type into the in-game chat

## Requirements (Initial)
- The Overlay Controller launch command remains configurable via the EDMC preferences pane (no change).
- When only the launch command is entered (default `!ovr`), the plugin launches the Overlay Controller (no change).
- Additional parameters may be provided in the in-game chat, and must be prefixed with the configured launch command.
- Initial parameter: a number in the range 0-100 (optionally suffixed with `%`) that sets payload opacity.
  - Example: `!ovr 0` sets payload opacity to 0.
  - Example: `!ovr 45` sets payload opacity to 45.
  - Example: `!ovr 100%` sets payload opacity to 100.

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
| 1 | Requirements capture + design for chat parameter parsing | Completed |
| 2 | Implement command parsing + payload opacity updates | Completed |
| 3 | Tests, docs, and verification | Completed |

## Phase Details

### Phase 1: Requirements + parsing design
- Define the command grammar for the launch command with optional opacity parameter (`0-100` or `0%-100%`).
- Confirm unchanged behavior when only the launch command is used (launch controller).
- Identify touch points (`overlay_plugin/journal_commands.py`, `load.py` launch helpers, preference setters).
- Note error/edge behavior: out-of-range values, non-numeric tokens, multiple tokens.
- Risks: unintended command handling or regression in launch behavior.
- Mitigations: targeted unit tests + logging for parse failures in dev mode.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Define chat command grammar and examples (including `%` suffix) | Completed |
| 1.2 | Enumerate edge cases and expected responses (ignored/handled) | Completed |
| 1.3 | Map implementation touch points and test targets | Completed |

Phase 1 Outcomes:
- Command grammar: `<prefix>` launches the controller; `<prefix> <opacity>` or `<prefix> <opacity>%` sets payload opacity.
- Opacity rules: integer `0-100` inclusive; optional `%` suffix allowed; single argument only.
- Edge behavior: non-numeric tokens, out-of-range values, or extra tokens are treated as unknown commands (no change, no message), but the command is still consumed.
- Touch points: `overlay_plugin/journal_commands.py` for parsing + dispatch, `load.py` for `set_payload_opacity_preference` and controller launch, `tests/test_journal_commands.py` for new parsing cases.

### Phase 2: Implement command parsing + opacity update
- Extend chat command parsing to recognize optional opacity parameter.
- Keep default launch behavior intact when no parameter is provided.
- Route valid opacity values to the existing preference setter (`set_payload_opacity_preference`).
- Ignore or report invalid parameters (per Phase 1 outcomes).
- Risks: mis-parsing commands or changing launch command behavior.
- Mitigations: keep parsing isolated in `JournalCommandHelper`; preserve existing command flow.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add opacity parsing helper (0-100 or % suffix) | Completed |
| 2.2 | Wire parsing into command handling without breaking launch path | Completed |
| 2.3 | Update runtime behavior to apply opacity preference | Completed |

Phase 2 Outcomes:
- Added `_parse_opacity_argument` to parse `0-100` with optional `%` suffix.
- Chat handler now recognizes a single numeric argument and applies it as payload opacity.
- Opacity updates are routed to `set_payload_opacity_preference`; existing launch behavior remains unchanged.

### Phase 3: Tests, docs, verification
- Add/extend unit tests for chat command parsing (valid/invalid, `%` suffix).
- Document behavior in plan + any user-facing docs as needed.
- Run targeted tests and note results.
- Risks: insufficient coverage for edge cases.
- Mitigations: expand `tests/test_journal_commands.py` with new cases.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add/adjust unit tests for opacity command parsing | Completed |
| 3.2 | Update docs/notes for chat command usage | Completed |
| 3.3 | Run targeted tests (`pytest -k journal_commands`) | Completed |

Phase 3 Outcomes:
- Added unit coverage for opacity parsing and edge cases in `tests/test_journal_commands.py`.
- Documented chat command usage and opacity examples in `docs/FAQ.md`.
- Tests run: `python3 -m pytest tests/test_journal_commands.py`.
