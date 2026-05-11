## Goal: GNOME Wayland Presentation And Attachment Stabilization

## Refactorer Persona
- Bias toward carving out modules aggressively while guarding behavior: no feature changes, no silent regressions.
- Prefer pure/push-down seams, explicit interfaces, and fast feedback loops (tests + dev-mode toggles) before deleting code from the monolith.
- Treat risky edges (I/O, timers, sockets, UI focus) as contract-driven: write down invariants, probe with tests, and keep escape hatches to revert quickly.
- Default to "lift then prove" refactors: move code intact behind an API, add coverage, then trim/reshape once behavior is anchored.
- Resolve the "be aggressive" vs. "keep changes small" tension by staging extractions: lift intact, add tests, then slim in follow-ups so each step stays behavior-scoped and reversible.
- Track progress with per-phase tables of stages (stage #, description, status). Mark each stage as completed when done; when all stages in a phase are complete, flip the phase status to "Completed." Number stages as `<phase>.<stage>` (e.g., 1.1, 1.2) to keep ordering clear.
- Personal rule: if asked to "Implement...", expand/document the plan and stages (including tests to run) before touching code.
- Personal rule: keep notes ordered by phase, then by stage within that phase.

## Problem Statement
The GNOME Shell helper can now be installed, enabled, and reported as available, but the overlay still behaves like a regular Wayland top-level window instead of an attached game overlay.

Observed symptoms on 2026-05-11:
- With `keep_overlay_visible` false, the overlay flashes.
- The overlay does not attach to the Elite Dangerous window position and stays visually in the upper-left corner.
- The overlay does resize to the game window size.
- `standalone_mode` is false, but the overlay appears to run as a standalone app/window. Normal overlay mode must not do that.

Working hypothesis:
- Helper health is necessary but not sufficient. The runtime appears to use helper health for status, while actual follow/presentation still depends on the legacy PyQt/window-tracker path.
- GNOME Wayland may honor the PyQt overlay size while ignoring or overriding the requested x/y position for a normal top-level window. Shell-mediated presentation must prove compositor-visible placement, stacking, chrome-free behavior, and click-through.
- The flashing likely comes from foreground-driven visibility toggling. In GNOME helper mode, a top-level overlay can affect focus/foreground state, so visibility should be driven by validated target/presentation state rather than raw "game is foreground" alone.

## Dev Best Practices

- Keep changes small and behavior-scoped; prefer feature flags/dev-mode toggles for risky tweaks.
- Plan before coding: note touch points, expected unchanged behavior, and tests you'll run.
- Avoid UI work off the main thread; keep new helpers pure/data-only where possible.
- When touching preferences/config code, use EDMC `config.get_int/str/bool/list` helpers and `number_from_string` for locale-aware numeric parsing; avoid raw `config.get/set`.
- Record tests run (or skipped with reasons) when landing changes; default to headless tests for pure helpers.
- Prefer fast/no-op paths in release builds; keep debug logging/dev overlays gated behind dev mode.

## Test Type Selection (Required Before Refactoring)
- Use **manual GNOME validation** for compositor behavior that cannot be proven headlessly: visible placement, stacking, click-through, chrome/titlebar state, focus changes, and flashing.
- Use **unit tests** for pure helper target/presentation payload parsing, visibility policy decisions, presentation state transitions, and true-overlay gate decisions.
- Use **harness tests** if implementation touches `load.py`, EDMC bridge wiring, plugin startup/shutdown, runtime lifecycle callbacks, or preferences-to-client message wiring.
- Use **script tests** for dev/helper diagnostic command behavior if this plan changes helper scripts.
- If no code changes are made in an iteration, document the manual commands and observations only.

## Testing Strategy Matrix

| Refactor Slice | Existing Behavior/Invariants To Preserve | Test Type (Unit/Harness/Manual) | Why This Level | Test File(s) | Command |
| --- | --- | --- | --- | --- | --- |
| Helper health preflight | Helper available still reports degraded until presentation gates pass | Manual/script | Confirms test environment before debugging attachment | Existing helper script | `./scripts/dev_gnome_helper.sh status` |
| Helper target state | Target geometry must come from Shell global logical coordinates and reject launcher-only states | Manual + unit when changed | Manual proves real Shell metadata; unit covers parser/scoring regressions | `overlay_client/tests/test_gnome_shell_helper_target_state.py` | `gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.GetTargetState '{}'` |
| Helper presentation state | PyQt renderer remains default; Shell proves placement/stacking/chrome/click-through before true overlay | Manual + unit when changed | Compositor actions need GNOME validation; payload gates are deterministic | `overlay_client/tests/test_gnome_shell_helper_presentation_state.py` | `gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.ApplyPresentation '<json-request>'` |
| Runtime helper wiring | Client must not rely only on legacy PyQt `setGeometry` in GNOME helper mode | Harness if touched | Runtime bridge/lifecycle wiring cannot be proven by parser tests alone | TBD | `source .venv/bin/activate && python -m pytest <touched harness tests>` |
| Visibility policy | `keep_overlay_visible=false` must not flash while target is valid and visible; target loss still hides/degrades | Unit + manual | Policy can be unit-tested; actual flashing needs GNOME validation | TBD | Manual log tail plus focused pytest |
| Chrome/standalone behavior | Normal overlay mode is chrome-free; standalone app/window mode remains explicitly setting-gated | Unit/harness + manual | Settings can be tested; Shell decoration behavior needs GNOME validation | TBD | Focused pytest plus manual GNOME test |

## Test Acceptance Gates
- [ ] Manual GNOME evidence captured for current failures before implementation.
- [ ] Unit tests added/updated for pure target/presentation/visibility decisions before behavior changes land.
- [ ] Harness tests added/updated for runtime helper wiring if touched.
- [ ] Commands executed and outcomes recorded.
- [ ] Skips/failures documented with reason and follow-up action.

## Scope
- In scope:
- Proving whether the runtime uses helper target and presentation APIs after helper health is available.
- Proving whether GNOME Shell can position, resize, stack, and identify the PyQt overlay window through `ApplyPresentation`.
- Designing the GNOME helper-mode visibility policy so `keep_overlay_visible=false` does not cause foreground/focus flashing.
- Designing normal overlay mode so it is chrome/titlebar-free and not standalone unless explicitly configured.
- Implementing helper-backed target/presentation runtime wiring in a later phase after tests identify the required path.
- Updating diagnostics so support logs clearly distinguish legacy PyQt geometry requests from Shell-applied presentation.
- Out of scope:
- Helper installation/lifecycle changes already covered by `docs/refactoring/gnome_wayland_helper.md`.
- Helper health/version/status detection already covered by `docs/refactoring/gnome_wayland_helper.md`.
- Windows, native X11, and non-GNOME Wayland behavior except to preserve existing behavior.
- Exclusive fullscreen support. Users must use Elite Dangerous windowed or borderless modes.
- Moving payload rendering into the GNOME Shell extension unless validation proves PyQt rendering cannot meet the requirements.
- Claiming GNOME Wayland `true_overlay` before placement, stacking, click-through, chrome-free, and no-flash gates all pass.

## Current Touch Points
- Code:
- `helpers/gnome_shell_extension/extension.js` exports `GetTargetState` and `ApplyPresentation`; this is the current Shell-side test surface.
- `overlay_client/backend/helper_ipc.py` validates helper health, target, and presentation payloads.
- `overlay_client/platform_context.py` currently wires helper health into backend status.
- `overlay_client/follow_surface.py` applies legacy tracker geometry through `setGeometry`, `raise_`, and foreground-driven visibility.
- `overlay_client/control_surface.py` maps `keep_overlay_visible` and forces `standalone_mode` false on non-Windows, which means the observed standalone behavior is probably not the experimental Windows setting itself.
- `overlay_client/window_controller.py` owns pure follow/visibility/geometry decisions used by the follow surface.
- Tests:
- `overlay_client/tests/test_gnome_shell_helper_target_state.py`
- `overlay_client/tests/test_gnome_shell_helper_presentation_state.py`
- `overlay_client/tests/test_platform_context.py`
- `overlay_client/tests/test_follow_surface_mixin.py`
- `overlay_client/tests/test_window_controller.py`
- Docs/notes:
- `docs/refactoring/gnome_wayland_helper.md` remains the helper lifecycle/status plan.
- This plan owns the remaining presentation, attachment, flashing, and chrome/standalone failures.

## Current Evidence
- User report on 2026-05-11: helper is available, but flashing, upper-left placement, and standalone/chrome behavior persist.
- Current code search indicates helper target/presentation helpers are implemented and unit-tested, but runtime search only shows health probing in `overlay_client/platform_context.py`.
- Follow code still applies target geometry with `self.setGeometry(QRect(*target))` and `self.raise_()` in `overlay_client/follow_surface.py`.
- Existing logs can show requested geometry and Qt `moveEvent`, but those are not sufficient proof of compositor-visible placement under GNOME Wayland.
- Prior log evidence showed the tracker selecting real Elite geometry such as `(1000,253,1440,960)` while the user observed visual upper-left placement. This is consistent with "size honored, x/y ignored or overridden" by Wayland/Shell for a normal top-level window.

## Manual Test Commands To Gather Before Coding

### 1. Helper/Session Preflight
```bash
./scripts/dev_gnome_helper.sh status
```
Record:
- GNOME Shell helper state.
- DBus health result.
- Helper version/protocol/capabilities.
- Session type and desktop.

### 2. Target State From Shell
Run while Elite Dangerous is windowed, moved away from `(0,0)`, and visible:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.GetTargetState \
  '{}'
```
Record:
- `status`
- `target.targetToken`
- `target.frameRect`
- `target.contentRect`
- `target.decorationInsets`
- `target.monitor` / `target.outputName`
- Whether launcher windows are rejected.

### 3. Runtime Log Tail While Moving/Resizing
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log | grep --line-buffered -E "Client backend status|helper|target_state|presentation|Overlay visibility|Tracker state|Raw tracker|Calculated overlay geometry|Applying geometry|Overlay moveEvent|Applying drag state|standalone|flags="
```
Record:
- Whether runtime logs ever mention helper target or presentation state.
- Whether `Overlay visibility` toggles in sync with `foreground=True/False`.
- Whether logged geometry says nonzero x/y while the visible overlay stays at `(0,0)`.

### 4. Direct Presentation Probe
After command 2 returns a target token and content rect, call `ApplyPresentation` with a narrow attach request. Replace the token and rect with the target output:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.ApplyPresentation \
  '{"action":"attach","target_token":"<targetToken>","content_rect":{"x":1000,"y":253,"width":1440,"height":960},"standalone_mode":false,"click_through_expected":true,"overlay_title":"EDMC Modern Overlay","overlay_wm_class":"EDMCModernOverlay"}'
```
Record:
- `status`
- `placement`
- `applied_rect`
- `stacking`
- `chrome_free`
- `click_through`
- `focus_safe`
- `standalone_mode`
- `unsupported_features`
- `degrade_reasons`

This test answers whether the Shell extension can find and manipulate the existing PyQt overlay window before we wire it into runtime.

### 5. Flashing Reproduction Matrix
Run each case for windowed and borderless modes:
- `keep_overlay_visible=false`, click through to the game, move focus away and back.
- `keep_overlay_visible=true`, repeat the same actions.

Record:
- Whether flashing appears.
- `Overlay visibility` log sequence.
- Target `hasFocus`, `showingOnWorkspace`, and `minimized` from `GetTargetState`.
- Whether Shell presentation state changes, if available.

## Open Questions
1. Is the running client invoking helper target and presentation APIs, or only helper health?
2. Does Qt/Wayland ignore or override top-level x/y while honoring size in this setup?
3. Can the GNOME Shell helper reliably find the PyQt overlay MetaWindow with the current title/class identity?
4. Can the GNOME Shell helper move/resize the overlay to the target `contentRect` on GNOME Shell 46?
5. Can the GNOME Shell helper keep the overlay stacked above the game after click-through/focus changes?
6. Can normal overlay mode be made chrome/titlebar-free with the PyQt renderer, or does that require a different window flag or Shell-side actor?
7. What should `keep_overlay_visible=false` mean in GNOME helper mode: hide only when target is absent/hidden/minimized/off-workspace, or also when the game loses focus?
8. What diagnostics are missing to distinguish requested Qt geometry from Shell-applied compositor-visible geometry?

## Decisions (Locked)
- Keep PyQt payload rendering as the default path unless tests prove rendering must move into the extension.
- Do not support exclusive fullscreen.
- Do not claim GNOME Wayland `true_overlay` until helper health, target discovery, presentation placement, stacking, click-through, chrome-free behavior, and no-flash behavior all pass.
- Treat helper health as necessary but not sufficient.
- Treat `keep_overlay_visible` as a visibility policy setting, not a rendering control.
- Normal overlay mode must not appear as a standalone app/window. Standalone mode must remain explicitly setting-gated.

## Per-Iteration Test Plan
- **Env setup (once per machine):** `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- **Headless quick pass (default for code changes):** `source .venv/bin/activate && python -m pytest`
- **Targeted tests:** `source .venv/bin/activate && python -m pytest <path/to/tests> -k "<pattern>"`
- **Manual GNOME pass:** run the manual commands in this plan while Elite Dangerous is windowed and borderless.
- **Milestone checks:** `make check` and `make test`
- **Compliance baseline check (release/compliance work):** `python scripts/check_edmc_python.py`
- **After wiring changes:** rerun headless tests plus manual GNOME validation for windowed and borderless modes.

## Guiding Traits for Readable, Maintainable Code
- Clarity first: simple, direct logic; avoid clever tricks; prefer small functions with clear names.
- Consistent style: stable formatting, naming conventions, and file structure; follow project style guides/linters.
- Intent made explicit: meaningful names; brief comments only where intent is not obvious; docstrings for public APIs.
- Single responsibility: each module/class/function does one thing; separate concerns; minimize side effects.
- Predictable control flow: limited branching depth; early returns for guard clauses; avoid deeply nested code.
- Good boundaries: clear interfaces; avoid leaking implementation details; use types or assertions to define expectations.
- DRY but pragmatic: share common logic without over-abstracting; duplicate only when it improves clarity.
- Small surfaces: limit global state; keep public APIs minimal; prefer immutability where practical.
- Testability: code structured so it is easy to unit/integration test; deterministic behavior; clear seams for injecting dependencies.
- Error handling: explicit failure paths; helpful messages; avoid silent catches; clean resource management.
- Observability: surface guarded fallbacks/edge conditions with trace/log hooks so silent behavior changes do not hide regressions.
- Documentation: concise README/usage notes; explain non-obvious decisions; update docs alongside code.
- Tooling: automated formatting/linting/tests in CI; commit hooks for quick checks; steady dependency management.
- Performance awareness: efficient enough without premature micro-optimizations; measure before tuning.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Evidence capture and failure classification | Not Started |
| 2 | Direct helper presentation spike without runtime code changes | Not Started |
| 3 | Runtime design decisions and contract updates | Not Started |
| 4 | Helper-backed target/presentation runtime wiring | Not Started |
| 5 | GNOME helper-mode visibility and focus policy hardening | Not Started |
| 6 | Chrome, standalone, and overlay identity hardening | Not Started |
| 7 | Manual validation matrix and true-overlay gate review | Not Started |

## Phase Details

### Phase 1: Evidence Capture And Failure Classification
- Capture current failure evidence without code changes.
- Confirm whether runtime uses helper target/presentation APIs or only helper health.
- Confirm whether the visible overlay position diverges from logged Qt geometry.
- Risks: drawing a conclusion from stale logs or mixed test modes.
- Mitigations: record exact command timestamps, game mode, settings, and observations in the execution log.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Record helper/session preflight from `./scripts/dev_gnome_helper.sh status` | Not Started |
| 1.2 | Record Shell target state for windowed Elite away from `(0,0)` | Not Started |
| 1.3 | Record runtime logs while moving/resizing target and observing visual overlay position | Not Started |
| 1.4 | Classify failure as runtime wiring, Shell placement, visibility policy, chrome/standalone, or mixed | Not Started |

### Phase 2: Direct Helper Presentation Spike
- Exercise `ApplyPresentation` directly through DBus before changing runtime code.
- Prove whether GNOME Shell can find the PyQt overlay window and move/stack it.
- Prove whether the helper reports `chrome_free`, `click_through`, and `focus_safe` gates as passing or degraded.
- Risks: manually constructed JSON can fail for quoting or stale target token reasons.
- Mitigations: derive the request directly from the immediately preceding `GetTargetState` output and record raw response.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Build a direct `ApplyPresentation` request from current target token/content rect | Not Started |
| 2.2 | Record presentation response and visible overlay behavior | Not Started |
| 2.3 | Identify unsupported Shell APIs or overlay identity mismatches | Not Started |
| 2.4 | Decide whether the PyQt renderer can remain the first implementation path | Not Started |

### Phase 3: Runtime Design Decisions And Contract Updates
- Lock the runtime contract before implementation.
- Decide which component owns target state, presentation state, visibility state, and true-overlay gate decisions.
- Define the exact GNOME helper-mode semantics for `keep_overlay_visible=false`.
- Risks: mixing legacy tracker state and helper state can create contradictory geometry/visibility decisions.
- Mitigations: make the helper path explicit and fail closed when helper target/presentation is stale or unavailable.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Decide helper-mode geometry source of truth | Not Started |
| 3.2 | Decide helper-mode visibility policy for focus loss, target hidden, target minimized, workspace change, and target missing | Not Started |
| 3.3 | Decide diagnostics fields needed for requested Qt geometry versus Shell-applied presentation | Not Started |
| 3.4 | Document unit and harness tests required for implementation phases | Not Started |

### Phase 4: Helper-Backed Target/Presentation Runtime Wiring
- Wire runtime GNOME helper mode to call target and presentation APIs when helper health is valid.
- Keep legacy PyQt geometry path available for non-GNOME and degraded fallback behavior.
- Keep `true_overlay` disabled unless all presentation gates pass.
- Risks: runtime DBus polling can block UI or introduce instability.
- Mitigations: keep DBus calls bounded, isolate pure validators, and add harness coverage if lifecycle wiring changes.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Add runtime target-state fetch path for GNOME helper mode | Not Started |
| 4.2 | Add runtime presentation request path using target `contentRect` | Not Started |
| 4.3 | Gate true-overlay status on validated presentation state | Not Started |
| 4.4 | Add unit/harness tests for helper runtime wiring and degraded fallback | Not Started |

### Phase 5: GNOME Helper-Mode Visibility And Focus Policy Hardening
- Replace foreground-flapping visibility behavior in GNOME helper mode with validated target/presentation policy.
- Ensure `keep_overlay_visible=false` does not hide/show repeatedly while the target is visible and on the current workspace.
- Preserve target-loss hiding/degrade behavior.
- Risks: relaxing foreground behavior could keep the overlay visible over unrelated apps.
- Mitigations: require target visibility, workspace, and presentation state; hide/degrade on missing/stale/hidden/minimized target.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Add pure visibility-policy tests for helper mode | Not Started |
| 5.2 | Wire helper-mode visibility policy without changing non-GNOME behavior | Not Started |
| 5.3 | Validate no flashing in windowed and borderless modes with `keep_overlay_visible=false` | Not Started |
| 5.4 | Validate target loss/minimize/workspace changes hide or degrade correctly | Not Started |

### Phase 6: Chrome, Standalone, And Overlay Identity Hardening
- Ensure normal GNOME helper overlay mode is chrome/titlebar-free and not a standalone app/window.
- Keep explicit standalone mode gated by setting and only where supported.
- Make overlay title/class identity stable enough for Shell helper discovery without exposing unrelated windows.
- Risks: changing Qt window flags can affect click-through or focus behavior.
- Mitigations: isolate GNOME helper-mode flag changes, unit-test setting behavior, and manually validate compositor behavior.

| Stage | Description | Status |
| --- | --- | --- |
| 6.1 | Prove current overlay Shell title/class/chrome state | Not Started |
| 6.2 | Define normal versus standalone mode window identity contract | Not Started |
| 6.3 | Add tests for standalone setting behavior if code changes are needed | Not Started |
| 6.4 | Validate chrome/titlebar-free behavior manually on GNOME 46 | Not Started |

### Phase 7: Manual Validation Matrix And True-Overlay Gate Review
- Run the final GNOME validation matrix for windowed and borderless modes.
- Document pass/fail/deferred gates.
- Only allow `true_overlay` if all gates pass.
- Risks: partial success could be overstated in UI/status text.
- Mitigations: keep degraded/experimental wording until every gate has evidence.

| Stage | Description | Status |
| --- | --- | --- |
| 7.1 | Validate windowed move/resize/focus/click-through/stacking/no-flash | Not Started |
| 7.2 | Validate borderless alignment/click-through/stacking/no-flash | Not Started |
| 7.3 | Validate helper reload, game exit/relaunch, target hidden/minimized/workspace changes | Not Started |
| 7.4 | Review and update status wording only if true-overlay gates pass | Not Started |

## Execution Log
- Plan created on 2026-05-11.
- No code changes are authorized yet for this plan.
- Record one execution summary subsection per completed phase.
- Record exact test commands and outcomes for each completed phase.

### Phase 1 Execution Summary
- Pending.

### Tests Run For Phase 1
- Not run yet.

