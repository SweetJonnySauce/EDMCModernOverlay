## Goal: Warn the CMDR on plugin start up if opacity setting is 100% transparent

## Requirements
1) When the plugin starts up and is ready to accept plugin payloads, if the Opacity setting is 0% we will display a fully opaque message on the screen warning the CMDR that the overlay is fully transparent.
2) The warning will consist of two lines. The first line will be "WARNING:" in red letters. the second line will be "The EDMCModernOverlay plugin is set to full transparency."
3) the warning will be displayed for 10 seconds.
4) make 100% configurable. We may want to set a threshold in the future.
5) This should be a simple change. If we need to make a decision between changing requirements and invasive code updates, let me know so we can iterate through the requirements

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
- Performance awareness: efficient enough without premature micro-tunings; measure before tuning.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Identify startup hook + threshold source for transparency warning | Completed |
| 2 | Implement warning display + one-time guard in client | Completed |
| 3 | Verify behavior and document testing | In Progress |

## Phase Details

### Phase 1: Hook + threshold for warning
- Goal: determine the least invasive place to trigger the warning once the client is ready to accept payloads, and decide where the configurable opacity threshold lives.
- Target behavior: warning triggers once per startup when opacity is at/below the threshold; no repeated warnings on config rebroadcasts.
- Candidate hooks: overlay client receives first `OverlayConfig` payload; plugin publishes initial config; client startup after window shown.
- Threshold source: default 0% with a configurable threshold value (likely in overlay client config until we need a plugin preference).
- Risks: warning fires before the client is ready; warning repeats on each config refresh; threshold lives in the wrong layer.
- Mitigations: add a one-time guard and log the trigger decision; keep the threshold value centralized and documented.
- Decision: use the overlay client `OverlayConfig` handler as the "ready to accept payloads" signal, since it is the first config the client applies after startup and is already the stable sync point for runtime settings.
- Decision: store the threshold as a client-side constant (default 0%) with a single guard flag to avoid re-triggering on config rebroadcasts; wire config-driven threshold only if/when we add a preference. Use the applied payload opacity state so it matches the user-facing slider.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Identify the minimal hook point that maps to "ready for payloads" and confirm it is reached after startup config | Completed |
| 1.2 | Decide where to store the threshold (client constant vs config value) and document the rationale | Completed |

### Phase 2: Warning display + guard
- Goal: show a two-line warning in the overlay client when the opacity threshold is met, bypassing payload opacity, and auto-clear after 10s.
- Target behavior: warning text is fully opaque regardless of global payload opacity; uses the existing overlay message label; appears once per startup.
- Touch points: `overlay_client/launcher.py` OverlayConfig handler, `overlay_client/control_surface.py` message label display, and a small constants/guard location in the client.
- Risks: warning rendered via payload path (gets opacity-applied); duplicate warnings on config rebroadcast; message styles conflicting with existing label styling.
- Mitigations: use the message label path directly, gate with a one-time flag, and restore prior message after timeout if needed.
- Plan:
  - Add client-side constants for the opacity threshold (default 0.0) and warning TTL (10s).
  - Add a one-time guard flag on the overlay window or helper to prevent repeated warnings on config rebroadcasts.
  - On the first `OverlayConfig` payload, compare `opacity` against the threshold and trigger the warning if at/below.
  - Render the warning through the message label using rich text so line 1 is red and line 2 uses default styling.
  - Keep the warning path isolated (no payload renderer changes); document the threshold for future configurability.
- Tests (planned): manual startup check at opacity 0 and >0; add a focused unit test if we can isolate the threshold guard without Qt.
- Results:
  - Added `TRANSPARENCY_WARNING_THRESHOLD`, `TRANSPARENCY_WARNING_TTL_SECONDS`, and the warning message in `overlay_client/control_surface.py`.
  - Added `maybe_warn_transparent_overlay` to gate and display the warning via the message label path.
  - Added a one-time guard (`_transparency_warning_shown`) in `overlay_client/setup_surface.py`.
  - Triggered the check when the client applies the first `OverlayConfig` payload in `overlay_client/launcher.py`, reading the applied payload opacity value.
  - Allowed the message label to expand to the layout width so long warnings are not clipped.
  - Sized the warning line as "Huge" and the body line as "Large" relative to the message font.
  - Shifted the warning label down by 100px total via layout top margin.
  - Set the transparency threshold to 10%; show a different body message when opacity is between 0% and 10% of the payload opacity scale.
  - Compute the "more than X% transparent" value from the configured threshold.
  - Set the warning body text color to Elite Dangerous orange (#ffa500).

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add a threshold constant + one-time guard and trigger the warning when applying the first OverlayConfig | Completed |
| 2.2 | Implement the two-line warning message with 10s TTL using the message label path | Completed |
| 2.3 | Confirm rich-text styling works with the message label (red "WARNING:" line) and restore defaults if needed | Completed |

### Phase 3: Verify + document
- Goal: confirm startup warning behavior and document tests/validation.
- Target behavior: warning appears only when opacity is at/below threshold; no warning when above threshold; no repeat on config rebroadcasts.
- Risks: missing regression coverage for startup path; edge cases in warning timing.
- Mitigations: add a focused unit test if feasible; otherwise document a manual startup check.
- Test plan:
  - Run `python3 -m pytest tests/test_overlay_api.py` for a quick headless check.
  - Manual: set overlay opacity to 0%, start the plugin, confirm the two-line warning shows for 10s and does not repeat; repeat with opacity > 0% to confirm no warning.
- Results:
  - `python3 -m pytest tests/test_overlay_api.py` (passed, 27 tests)

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add/record tests (unit or manual) and capture results in this doc | Completed |
| 3.2 | Run a manual startup check for both opacity=0% and opacity>0% | Planned |
