## Goal: Add support to make the overlay capturable by OBS.

## Findings (Issue #108)
- The overlay window is forced into `Qt.WindowType.Tool` whenever click-through is applied, and click-through is applied on startup because drag is disabled by default. Tool windows are commonly hidden from OBS Window Capture on Windows, matching the "not selectable" report.
- Windows click-through sets `WS_EX_LAYERED | WS_EX_TRANSPARENT`, which can also cause OBS to ignore or fail to capture the window depending on capture method.

## Requirements (Draft)
- Provide a capture-friendly mode that allows OBS Window Capture to see/select the overlay window on Windows.
- Keep click-through enabled in capture-friendly mode (no in-game input interference).
- Allow users to opt into the mode without altering default behavior for existing users.
- Ensure this mode can be toggled without affecting overlay positioning/follow behavior.
- Enable capture-friendly mode via a preferences pane setting.
- Preferences pane control is Windows-only (shown but disabled/greyed out on non-Windows OSs).

## Questions (Draft)
- Should we also offer an optional opaque/black background sub-mode for chroma key workflows? (Deferred; do not add in initial scope.)

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
| 1 | Preferences + config plumbing (Windows-only toggle) | Completed |
| 2 | Windows windowing behavior changes for capture-friendly mode | Completed |
| 3 | Validation + docs | In Progress |

## Phase Details

### Phase 1: Preferences + Config Plumbing (Windows-only toggle)
- Goal: introduce a preferences pane toggle that persists a capture-friendly mode flag and is disabled on non-Windows OSs.
- Behavior invariants: default behavior unchanged when toggle is off; click-through remains enabled when toggle is on.
- Edge cases: missing/invalid config values; OS detection for disabling the control; existing configs with no new key.
- Risks: incorrect default or config wiring silently enabling the mode.
- Mitigations: explicit default off; add unit coverage around config parsing and defaulting.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Define the new preference key and default value (off) in settings schema/config models. | Completed |
| 1.2 | Wire preference persistence to overlay config payloads (read/write) without changing defaults. | Completed |
| 1.3 | Add preferences UI control: visible but disabled on non-Windows, with short help text. | Completed |
| 1.4 | Extract OBS helpers + overlay config payload building into helper modules to keep `load.py`/preferences lighter. | Completed |

#### Phase 1 Plan (Detail)
- Scope: preferences only (no runtime behavior changes yet).
- Touch points (expected):
  - Preferences UI (add toggle + help text, disable when not Windows).
  - Overlay config model/payload plumbing (add new boolean field, default false).
  - Settings persistence (read/write to user config).
- Data shape:
  - New boolean setting key (name TBD) with default `false`.
  - UI binds directly to the new key and writes through existing config plumbing.
- UI requirements:
  - Label should mention OBS and Windows-only behavior.
  - Disabled on non-Windows with a brief hint (e.g., "Windows only").
- Acceptance criteria:
  - New toggle appears in preferences on Windows and is enabled.
  - Same toggle appears but is disabled on non-Windows.
  - Default remains off for existing users and new installs.
  - Toggling persists and is reflected in the config payload sent to the overlay client.
- Tests (targeted, Phase 1):
  - Unit test for config parsing/defaulting of the new boolean.
  - Optional UI test or manual check to confirm disablement on non-Windows.

#### Phase 1 Results
- Added `obs_capture_friendly` preference (default off) across settings persistence and overlay config payloads.
- Preferences pane now shows "OBS capture-friendly mode (Windows only)" and disables it on non-Windows OSs.
- Added persistence coverage in preferences tests for the new boolean setting.
- Refactored OBS support strings/platform gating and overlay config payload assembly into helper modules.

### Phase 2: Windows Windowing Behavior Changes
- Goal: make the overlay window selectable in OBS Window Capture when capture-friendly mode is enabled on Windows.
- Behavior invariants: click-through remains enabled; overlay remains always-on-top and positioned correctly; non-Windows behavior unchanged.
- Edge cases: drag-enabled mode toggling; interaction controller reapplying window flags; startup apply-drag-state overwriting flags.
- Risks: breaking overlay input behavior or causing focus/activation issues on Windows.
- Mitigations: gate changes behind the new preference; keep logging around flag changes; add a safe fallback to revert to current behavior; log and skip flag changes if window handle/flag application fails.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Introduce a capture-friendly flag in the overlay client state and ensure it is Windows-only. | Completed |
| 2.2 | Adjust window flag application to skip `Qt.WindowType.Tool` when capture-friendly is enabled on Windows. | Completed |
| 2.3 | Ensure click-through stays enabled while avoiding regressions in drag/move handling. | Completed |

#### Phase 2 Plan (Detail)
- Scope: runtime windowing behavior on Windows only; no UI changes.
- Touch points (expected):
  - Overlay client config handling (`overlay_client/client_config.py`, `overlay_client/developer_helpers.py`).
  - Window flag application path (`overlay_client/interaction_controller.py`, possibly `overlay_client/setup_surface.py`).
  - Windows click-through integration (`overlay_client/platform_integration.py`) if needed.
- Proposed behavior:
  - When `obs_capture_friendly` is true on Windows, avoid applying `Qt.WindowType.Tool` so the overlay appears as a standard window for OBS Window Capture.
  - Keep click-through enabled; do not change opacity or z-order behavior.
- Acceptance criteria:
  - On Windows with capture-friendly enabled, OBS Window Capture lists the overlay window.
  - On Windows with capture-friendly disabled, behavior matches current baseline.
  - Non-Windows behavior remains unchanged and pref is ignored.
  - No regression in drag-enabled mode or follow positioning.
  - Window flag application failures are logged and do not crash the overlay.
- Implementation notes:
  - Gate any flag changes behind the `obs_capture_friendly` preference and a Windows platform check.
  - Ensure flag changes are re-applied during drag state changes (because `_apply_drag_state()` is called on startup and toggles flags).
  - Handle missing window handles or flag application errors with a log + safe no-op.
- Tests (targeted, Phase 2):
  - Unit test to verify window flag decision logic (if extracted to a helper).
  - Manual validation on Windows + OBS Window Capture.

#### Phase 2 Results
- Added Windows-only capture-friendly state to the overlay client and applied it via config updates.
- Window flag application now clears the Tool flag when capture-friendly is enabled on Windows, keeping click-through intact.
- Added error handling for window flag application to avoid crashes on flag/handle failures.

### Phase 3: Validation + Docs
- Goal: verify the new mode on Windows and document usage/limitations.
- Behavior invariants: no regression in default mode; toggle is disabled on non-Windows.
- Risks: OBS capture still failing due to other window styles (e.g., layered/transparent).
- Mitigations: document known limitations and add a follow-up note if further OBS tuning is needed.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add/adjust unit tests for config parsing/defaults and flag gating (where feasible). | Completed |
| 3.2 | Manual validation checklist for Windows + OBS Window Capture (note exact steps). | Pending |
| 3.3 | Update README/RELEASE_NOTES with the new preference and Windows-only behavior. | Completed |

#### Phase 3 Plan (Detail)
- Scope: validation + documentation only (no feature changes).
- Validation checklist (Windows):
  - Enable “OBS capture-friendly mode” in preferences.
  - Restart overlay client.
  - In OBS, add Window Capture source and verify the overlay window is selectable.
  - Confirm overlay remains click-through and always-on-top during gameplay.
  - Disable the toggle and confirm previous behavior returns.
- Documentation updates:
  - Note Windows-only behavior and that the overlay may appear in Alt-Tab/taskbar.
  - Describe the OBS Window Capture flow and any known limitations (e.g., transparency handling).
- Acceptance criteria:
  - Manual checklist completed on Windows.
  - Release notes and README mention the new preference and its Windows-only scope.
  - Tests (if added) pass.

#### Phase 3 Results
- Added unit coverage for OBS capture preference gating.
- Documented OBS capture-friendly mode in README and release notes.
- Manual validation checklist recorded in this plan (pending execution).
- Tests: `python3 -m pytest tests/test_obs_capture_support.py tests/test_preferences_persistence.py`

#### Manual Tests (To Run)
- Windows: enable “OBS capture-friendly mode”, restart overlay, confirm OBS Window Capture can select the overlay window.
- Windows: verify overlay remains click-through and always-on-top during gameplay.
- Windows: disable the toggle and confirm prior behavior returns (overlay no longer selectable in OBS Window Capture).
