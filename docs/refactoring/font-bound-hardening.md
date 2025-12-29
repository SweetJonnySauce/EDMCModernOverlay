## Goal: Harden the font bounds settings so it limits the extents of what can be done

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
| 0 | Discovery: current behavior and issue 80 findings | Completed |
| 1 | Requirements: preference UI bounds + apply behavior | Pending |
| 2 | Implementation plan: preference clamps + apply flow | Pending |

## Phase Details

### Phase 0: Discovery and Current Behavior
- Goal: document how font bounds are applied today and why the UI feels broken in issue 80.
- Current behavior summary:
  - Bounds are clamps on scaled point size, not fixed sizes. `overlay_client/viewport_transform.py` clamps `base_point * diagonal_scale` to `font_min_point` and `font_max_point`.
  - Legacy preset sizes are derived from the scaled "normal" size plus a step offset in `overlay_client/window_utils.py`. The step can push beyond `font_max_point` because only the base clamp is applied.
  - Defaults come from multiple sources: `overlay_settings.json` (min 6.0, max 12.0), `overlay_client/client_config.py` defaults (min 6.0, max 24.0), and plugin preferences stored in `overlay_plugin/preferences.py` and sent via `load.py`.
- UI behavior (root of issue 80):
  - The preferences UI uses `tk.DoubleVar` for min/max and attaches `trace_add("write", ...)`.
  - `_apply_font_bounds` immediately clamps and writes back to the variables, which fires during partial edits.
  - Result: typing edits are overwritten mid-entry (example: "72" backspace -> "2" clamps to 6.0; typing "12" becomes "62"), and the spinboxes appear to stop responding after one increment.
  - `load.py` enforces the same clamps and forces `max >= min`, which can lock both to the same value if the min jumps up.
- External context (issue 80):
  - Reporter observes the partial-edit clamping behavior and inconsistent saved values.
  - Maintainer response: bounds are intended as clamps for scaling; step is clamped 0-10; a tighter allowed range (e.g., 6-18) might be preferable.

| Stage | Description | Status |
| --- | --- | --- |
| 0.1 | Capture current clamp rules, UI wiring, and issue 80 repro notes | Completed |

### Phase 1: Requirements (Preferences-Only)
- Scope: settings/preferences UI and persistence only; no rendering changes.
- Requirements:
  - Minimum font bound cannot go below 6.
  - Maximum font bound cannot go above 32.
  - Minimum bound cannot exceed maximum bound.
  - Maximum bound cannot go below minimum bound.
  - Remove any in-focus validation/clamping; validate only after the setting loses focus (no live updates while typing).
  - Add a tooltip to the "Font scaling bounds (pt)" label describing that these settings clamp auto-scaled font size, not set a fixed size.
  - Add unit tests covering the new clamp helper and invalid ordering cases.
  - Apply the same focus-out-only validation to Font Step.
- Clarifications:
  - Enforce bounds in plugin preference setters as well, but centralize min/max limits in one place.
  - When min > max or max < min, block/revert the edited value and keep the other value unchanged.
  - Validate on each field's focus-out (tabbing between min/max/step), not only when the full group loses focus.
  - Invalid edits revert to the last committed valid value (no snap-to-bound while typing).
  - While any font field has focus, do not auto-apply; validation happens after focus leaves the field.
  - Preview should force-apply current fields before sending.
  - Tooltip wording will be drafted during implementation.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Document preference-only clamp rules, UI apply triggers, and clarifications | Pending |

### Phase N: Title Placeholder
- Describe the extraction/decoupling goal for this phase.
- Note the APIs you intend to introduce and the behaviors that must remain unchanged.
- Call out edge cases and invariants that need tests before and after the move.
- Risks: list potential regressions unique to this phase.
- Mitigations: planned tests, flags, and rollout steps to contain those risks.

| Stage | Description | Status |
| --- | --- | --- |
