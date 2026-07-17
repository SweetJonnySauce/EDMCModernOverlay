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
- 2026-05-11 Phase 1 evidence:
- `./scripts/dev_gnome_helper.sh status` reported the helper installed, enabled, `ACTIVE`, and DBus-healthy with capabilities `hello`, `health`, `version`, `protocol`, `capabilities`, `target_state`, and `presentation_state`.
- `GetTargetState '{}'` reported `status=target_found`, one client candidate, one launcher rejected, and target token `meta:110` for `Elite - Dangerous (CLIENT)`.
- The helper target returned `frameRect=(1000,216,1440,997)` and `bufferRect=(986,204,1468,1026)`, but `contentRect=null` and `decorationInsets=null`. This means target discovery is working, but final content alignment is not yet proven for this windowed case.
- Runtime logs contained no helper `target_state` or `presentation` activity during movement/resizing. They showed legacy tracker geometry and `setGeometry` calls only.
- Runtime logs showed repeated `Overlay visibility set to hidden` followed by `Applying drag state` and `Overlay visibility set to visible` while `keep_overlay_visible=false`, confirming the flashing is visibility-policy driven.
- Runtime logs showed requested nonzero overlay geometry and Qt `moveEvent` positions such as `(1087,293)`, `(1482,236)`, and `(628,307)`, but the user observed the visible overlay staying in the upper-left. This supports the conclusion that Qt-reported geometry is not sufficient proof of compositor-visible placement on GNOME Wayland.
- 2026-05-11 direct presentation probe:
- `ApplyPresentation` with target token `meta:110` and requested rect `(1000,216,1440,997)` returned `status=presentation_applied`, `overlay_token=meta:134`, `placement=true`, `stacking=true`, `chrome_free=true`, `click_through=true`, `focus_safe=true`, and no degrade reasons.
- The user observed the overlay move in the positive X and Y directions, proving the Shell helper can find and affect the PyQt overlay window.
- The same response reported `applied_rect=(0,29,1920,800)`, which does not match the requested rect. This means the current helper presentation success gate is too weak: `move_resize_frame` returning without exception is not enough. Presentation must require actual Shell-reported geometry to match the requested target rect within an explicit tolerance.
- Follow-up direct presentation probe used fresh target `frameRect=(628,270,1920,837)` from `GetTargetState` because `contentRect` remained null. `ApplyPresentation` returned `presentation_applied`, but reported `applied_rect=(1000,216,1920,800)`. This looks like either asynchronous Shell geometry readback lag, a client-side resize constraint, or both. The x/y values matched the previous presentation request while the size remained the prior overlay size.
- User observation after the direct presentation probe: the overlay did move to the game window. It still did not continue moving with the game window afterward. This confirms direct Shell placement can work on demand, while continuous runtime presentation/follow wiring is missing or inactive.
- Repeating `ApplyPresentation` with the same requested rect after moving the game slightly returned `applied_rect=(628,270,1920,800)`. This confirms the x/y readback can settle to the requested position on a later call, but height remained constrained to `800` rather than the requested `837`.
- Requesting the exact accepted rect `(628,270,1920,800)` returned `applied_rect=(628,270,1920,800)` with `presentation_applied`. This proves Shell-mediated presentation can exactly place and size the PyQt overlay for an accepted rect. The remaining size mismatch is likely due to using target `frameRect` instead of final content/client geometry, or due to the legacy runtime/Qt overlay size policy feeding back into the result.

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
1. Answered in Phase 1: the running client invokes helper health only; target/presentation are not wired into runtime follow yet.
2. Answered in Phases 1-2: Qt `setGeometry`/`moveEvent` is not proof of compositor-visible position. Shell presentation can move the PyQt overlay.
3. Answered in Phase 2: the helper can find the PyQt overlay with current title/class and returned `overlay_token=meta:134`.
4. Partially answered in Phase 2: the helper can move/resize to an accepted rect on GNOME Shell 46, but `contentRect` is currently null for the tested windowed target, so exact content alignment still needs validation.
5. Partially answered in Phase 2: direct presentation reported `stacking=true` and `focus_safe=true`; runtime stacking after click-through remains a manual validation gate.
6. Partially answered in Phase 2: direct presentation reported `chrome_free=true`; normal runtime mode still needs validation because the user observed standalone/chrome-like behavior.
7. Answered in Phase 3: helper mode must not hide on single-sample foreground/focus loss; it hides/degrades on target unavailable states and uses debounced focus loss when `keep_overlay_visible=false`.
8. Answered in Phase 3: diagnostics must log both requested Qt geometry and Shell presentation requested/applied rects, including deltas and visibility reasons.

## Decisions (Locked)
- Keep PyQt payload rendering as the default path unless tests prove rendering must move into the extension.
- Do not support exclusive fullscreen.
- Do not claim GNOME Wayland `true_overlay` until helper health, target discovery, presentation placement, stacking, click-through, chrome-free behavior, and no-flash behavior all pass.
- Treat helper health as necessary but not sufficient.
- Treat `keep_overlay_visible` as a visibility policy setting, not a rendering control.
- Normal overlay mode must not appear as a standalone app/window. Standalone mode must remain explicitly setting-gated.

## Phase 3 Runtime Contract

### Geometry Source Of Truth
- In GNOME helper mode, Shell helper target state is the authoritative source for target identity, monitor/workspace state, and compositor-coordinate target geometry.
- Legacy tracker geometry must not drive visible GNOME helper-mode placement. It can be retained for non-GNOME backends, degraded fallback diagnostics, and side-by-side comparison logs.
- Qt `setGeometry`, Qt `frameGeometry`, and Qt `moveEvent` are not accepted as compositor-visible placement proof under GNOME Wayland.
- Runtime GNOME helper mode must call `GetTargetState` and then `ApplyPresentation` repeatedly while the target is eligible. One-shot presentation is not enough because the overlay does not continue following later game movement.
- Target correlation must use the helper `targetToken` and helper sequence/timestamps. Stale, missing, launcher-only, ambiguous, or malformed target state fails closed.

### Target Rect Selection
- Preferred target rect: valid helper `contentRect`.
- If `contentRect` is missing but helper `frameRect` is valid, the first implementation may use a controlled `frameRect` fallback for placement so the overlay attaches to the game window instead of staying upper-left.
- A `frameRect` fallback must be marked in diagnostics as `rect_source=frame_rect_fallback` and must block final `true_overlay` support claims until content alignment is manually validated.
- The observed windowed target returned `contentRect=null`, `frameRect=(628,270,1920,837)`, and an accepted overlay rect of `(628,270,1920,800)`. Implementation must therefore tolerate missing `contentRect` without silently claiming final content alignment.
- Runtime should avoid mixing legacy tracker position into the helper path. If legacy tracker dimensions are used as a temporary size comparison, log that separately as diagnostic data rather than presenting it as Shell-authored geometry.

### Presentation Success Gate
- `ApplyPresentation` returning without exception is not sufficient.
- `presentation_applied` is trusted only when all required gates are true and the Shell-reported `applied_rect` matches the requested rect within an explicit tolerance.
- Initial tolerance: `<= 2` logical pixels for x, y, width, and height. Any mismatch outside tolerance is `presentation_pending` or degraded, not applied.
- Because Shell readback can lag by one request, runtime may retry presentation with fresh target state before degrading. A retry must be bounded and non-blocking.
- Required gates before any future `true_overlay` claim: helper healthy, target found, rect resolved, placement true, applied rect match, stacking true, click-through true, focus-safe true, chrome-free true, standalone false, no unsupported features, no degrade reasons, and no visibility flashing in manual validation.

### Visibility Policy
- GNOME helper mode must stop using raw legacy foreground state as the only show/hide decision.
- Target unavailable states always hide or degrade: missing target, launcher-only target, ambiguous target, stale target state, minimized target, hidden target, off-workspace target, helper unhealthy, and presentation unavailable.
- `keep_overlay_visible=true`: keep the overlay attached while the target is valid and visible on the current workspace, even when the game is not foreground.
- `keep_overlay_visible=false`: show/attach while the target is valid and either focused or recently focused/presented. Do not hide on a single false focus/foreground sample caused by showing, raising, or click-through behavior.
- Use a short debounced focus-loss policy for `keep_overlay_visible=false`. Initial design target: require at least two consecutive helper samples, or roughly one second, of target not focused before hiding. The exact value should be a named constant and covered by unit tests.
- Do not call `raise_()` as the primary stacking mechanism in GNOME helper mode once Shell presentation is active; use helper presentation/stacking instead.

### Diagnostics Contract
- Logs and debug metrics must distinguish:
- legacy tracker target rect
- Qt requested geometry
- Qt move/frame geometry
- helper target `frameRect`, `contentRect`, `bufferRect`, `targetToken`, sequence, and freshness
- presentation requested rect
- presentation applied rect
- rect source (`content_rect`, `frame_rect_fallback`, or degraded)
- rect delta and match/mismatch result
- presentation state, sequence, unsupported features, and degrade reasons
- visibility decision and reason
- `keep_overlay_visible`, `standalone_mode`, click-through, chrome-free, stacking, and focus-safe state
- This diagnostic split is required before runtime wiring can be considered complete, because Phase 1 proved Qt geometry logs can disagree with visible Shell placement.

### Required Tests For Implementation Phases
- Unit tests:
- target rect resolver: content rect preferred, frame rect fallback marked, missing/malformed rect degrades.
- presentation gate: applied rect mismatch degrades, exact/tolerance match applies, unsupported feature/degrade reason fails closed.
- settled retry policy: one stale/mismatched readback can retry without claiming applied.
- GNOME helper-mode visibility policy: valid focused target shows, single-sample focus loss does not flash, sustained focus loss hides when `keep_overlay_visible=false`, target unavailable states hide/degrade.
- true-overlay gate: remains degraded unless all helper/presentation/visibility gates pass.
- Harness tests:
- runtime GNOME helper mode calls helper target/presentation when health is valid.
- runtime GNOME helper mode does not rely on legacy `setGeometry` as the visible placement proof.
- non-GNOME and degraded fallback behavior remains unchanged.
- preferences/client bridge still sends `keep_overlay_visible` and `standalone_mode` without changing semantics.
- Manual validation:
- windowed mode move/resize follow, click-through, stacking, no flashing, and chrome-free presentation.
- borderless mode alignment, click-through, stacking, no flashing, and chrome-free presentation.
- target minimized, hidden, workspace change, game exit/relaunch, helper reload, and helper disabled/error states.

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
| 1 | Evidence capture and failure classification | Completed |
| 2 | Direct helper presentation spike without runtime code changes | Completed |
| 3 | Runtime design decisions and contract updates | Completed |
| 4 | Helper-backed target/presentation runtime wiring | Completed |
| 4A | Backend ownership correction for GNOME helper presentation wiring | Completed |
| 5 | GNOME helper-mode visibility and focus policy hardening | Follow-up Implemented; Blocked By Phase 6 Focus Safety |
| 6 | Chrome, standalone, and overlay identity hardening | Manual Validation Failed; Phase 6A Planned |
| 6A | Mapped suppression for GNOME helper-mode focus loss | No-Flash Manual Validation Passed; Workspace Deferred |
| 6B | Frame fallback monitor-bounds clamp | Manual Monitor-Bounds Passed; 6A Recheck Passed |
| 7 | Manual validation matrix and true-overlay gate review | In Progress |
| 8 | Performance stabilization addendum for GNOME helper presentation churn | Phase 8.9 Manual Pause Validation Passed; Broader GNOME Regression Pending |
| 9 | GNOME content-rect and alignment proof | Phase 9.1 Headless Diagnostics Implemented; Phase 9.2 Manual Evidence In Progress |
| 9.9A | Borderless wrong-monitor mismatch addendum | Headless Implementation Complete; Manual Validation Pending |
| 9B | Borderless full-monitor work-area constraint fix | Managed PyQt Path Not Viable; Evidence Retained |
| 10 | GNOME Shell-native borderless/fullscreen small proof | Active-Fullscreen Proof Passed; Phase 11 Unblocked |
| 11 | GNOME Shell-native PyQt raster bridge architecture | Completed; Phase 12 Ready |
| 12 | GNOME Shell-native PyQt raster bridge small production proof | Completed; Persistent Runtime Safety Deferred To Phase 13 |
| 13 | GNOME Shell-native PyQt raster bridge lifecycle/focus hardening and support gate | Completed; Opt-In Experimental Proof Mode Only |
| 14 | GNOME Shell-native PyQt raster parity/performance expansion | Completed |
| 15 | Productionization and GNOME support gate | Borderless/Fullscreen Manual Validation Complete; Experimental Support Gate Held For Phase 16 |
| 16 | Deferred GNOME fallback cleanup | Target-Actor Parenting Remediation Implemented; Manual Reload Validation Pending |
| 17 | Extended hardening and release validation | Pending Phase 16 |
| 18 | Stable managed-window preparation and multi-monitor transitions | In Progress; Windowed Handoff Passed, Remap/Standalone Follow-Up Unvalidated |
| 19 | Atomic fullscreen monitor handoff without managed-window fallback exposure | Planned; Live Reproduction Captured |

## Phase Details

### Phase 1: Evidence Capture And Failure Classification
- Capture current failure evidence without code changes.
- Confirm whether runtime uses helper target/presentation APIs or only helper health.
- Confirm whether the visible overlay position diverges from logged Qt geometry.
- Risks: drawing a conclusion from stale logs or mixed test modes.
- Mitigations: record exact command timestamps, game mode, settings, and observations in the execution log.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Record helper/session preflight from `./scripts/dev_gnome_helper.sh status` | Completed |
| 1.2 | Record Shell target state for windowed Elite away from `(0,0)` | Completed |
| 1.3 | Record runtime logs while moving/resizing target and observing visual overlay position | Completed |
| 1.4 | Classify failure as runtime wiring, Shell placement, visibility policy, chrome/standalone, or mixed | Completed |

### Phase 2: Direct Helper Presentation Spike
- Exercise `ApplyPresentation` directly through DBus before changing runtime code.
- Prove whether GNOME Shell can find the PyQt overlay window and move/stack it.
- Prove whether the helper reports `chrome_free`, `click_through`, and `focus_safe` gates as passing or degraded.
- Risks: manually constructed JSON can fail for quoting or stale target token reasons.
- Mitigations: derive the request directly from the immediately preceding `GetTargetState` output and record raw response.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Build a direct `ApplyPresentation` request from current target token/content rect | Completed |
| 2.2 | Record presentation response and visible overlay behavior | Completed |
| 2.3 | Identify unsupported Shell APIs or overlay identity mismatches | Completed |
| 2.4 | Decide whether the PyQt renderer can remain the first implementation path | Completed |

### Phase 3: Runtime Design Decisions And Contract Updates
- Lock the runtime contract before implementation.
- Decide which component owns target state, presentation state, visibility state, and true-overlay gate decisions.
- Define the exact GNOME helper-mode semantics for `keep_overlay_visible=false`.
- Risks: mixing legacy tracker state and helper state can create contradictory geometry/visibility decisions.
- Mitigations: make the helper path explicit and fail closed when helper target/presentation is stale or unavailable.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Decide helper-mode geometry source of truth | Completed |
| 3.2 | Decide helper-mode visibility policy for focus loss, target hidden, target minimized, workspace change, and target missing | Completed |
| 3.3 | Decide diagnostics fields needed for requested Qt geometry versus Shell-applied presentation | Completed |
| 3.4 | Document unit and harness tests required for implementation phases | Completed |

### Phase 4: Helper-Backed Target/Presentation Runtime Wiring
- Wire runtime GNOME helper mode to call target and presentation APIs when helper health is valid.
- Keep legacy PyQt geometry path available for non-GNOME and degraded fallback behavior.
- Keep `true_overlay` disabled unless all presentation gates pass.
- Touch points:
- `overlay_client/backend/helper_ipc.py`: pure target rect fallback, presentation request/gate, applied-rect tolerance, and rect diagnostics.
- `overlay_client/gnome_helper_presentation.py`: runtime helper presentation cycle, DBus fetchers, settled retry policy, and cycle diagnostics.
- `overlay_client/follow_surface.py`: route GNOME helper mode through the helper presentation cycle and do not use legacy `setGeometry` as visible placement proof when helper presentation is active.
- `overlay_client/setup_surface.py`: initialize helper presentation state using the existing follow timer cadence.
- Expected unchanged behavior:
- Non-GNOME, Windows, native X11, generic Wayland, and missing-helper fallback behavior keep their existing code paths.
- PyQt rendering remains the renderer.
- `keep_overlay_visible` semantics are not fully redesigned in this phase; Phase 5 owns focus-loss debounce. Phase 4 may show the overlay when a valid helper target is being presented so legacy hidden state does not prevent attachment.
- Initial cadence: reuse the existing follow timer interval, currently 500 ms, for helper target/presentation polling.
- Rect tolerance: `<= 2` Shell logical pixels for x, y, width, and height.
- Retry behavior: at most two presentation attempts per poll cycle. A first applied-rect mismatch can retry after a fresh target state read; the cycle must not claim applied unless the final applied rect matches within tolerance.
- Tests to run:
- Unit tests for target rect resolver and `frame_rect_fallback`.
- Unit tests for applied-rect match/mismatch and degraded presentation gates.
- Unit tests for settled retry policy.
- Mixin/harness-style tests for GNOME helper mode using helper presentation instead of legacy geometry.
- Targeted existing helper target/presentation tests.
- `make check`.
- Risks: runtime DBus polling can block UI or introduce instability.
- Mitigations: keep DBus calls bounded, isolate pure validators, and add harness coverage if lifecycle wiring changes.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Add runtime target-state fetch path for GNOME helper mode | Completed |
| 4.2 | Add runtime presentation request path using target `contentRect` | Completed |
| 4.3 | Gate true-overlay status on validated presentation state | Completed |
| 4.4 | Add unit/harness tests for helper runtime wiring and degraded fallback | Completed |

### Phase 4A: Backend Ownership Correction For Helper Presentation Wiring
- Correct the Phase 4 runtime wiring so GNOME helper presentation is backend-owned instead of imported directly by generic follow/runtime code.
- Preserve Phase 4 behavior while moving ownership to the backend bundle/consumer boundary.
- Do not implement Phase 5 visibility debounce, Phase 6 chrome/standalone fixes, or Phase 7 validation/docs closeout.
- Architecture source:
- `fix219_backend_architecture_refactor_plan.md` says runtime tracking/presentation/input consumers should consume the client-selected backend bundle instead of re-resolving or importing compositor-specific behavior directly.
- `fix219_backend_architecture_followup_cleanup_plan.md` says Linux presentation/input behavior must be backend-owned in `PresentationBackend` / `InputPolicyBackend` terms, and generic consumers should query backend capabilities rather than compositor-specific branches.
- `gnome_wayland_helper.md` lists `overlay_client/backend/bundles/gnome_shell_wayland.py` as the GNOME bundle helper ownership point and requires Shell-mediated presentation/attachment to be helper-backed.
- Problem found after Phase 4:
- `overlay_client/follow_surface.py` imports `overlay_client.gnome_helper_presentation` directly.
- That makes generic follow/runtime code aware of a GNOME-specific helper implementation.
- This violates the `fix219` backend-boundary direction even though the Phase 4 behavior is otherwise useful.
- Phase 4A audit findings to fix:
- `overlay_client/follow_surface.py` must not import `overlay_client.gnome_helper_presentation`, `GnomeHelperPresentationCycleResult`, or `run_gnome_shell_helper_presentation_cycle` directly.
- `overlay_client/follow_surface.py` must not decide helper-presentation availability by checking `BackendInstance.GNOME_SHELL_WAYLAND` and `HelperKind.GNOME_SHELL_EXTENSION` directly. That decision belongs behind a backend-owned consumer/bundle interface.
- `overlay_client/follow_surface.py` should not reason about GNOME helper protocol details such as `HelperPresentationAction.ATTACH` as the primary runtime contract. It should consume a backend-facing presentation result with generic fields such as visibility recommendation, applied rect, scale rect, diagnostics payload, and degraded/unsupported reasons.
- `overlay_client/gnome_helper_presentation.py` is compositor-specific runtime presentation code in a top-level client module. Move it under backend ownership, likely `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py` or an equivalent backend-private module.
- `overlay_client/setup_surface.py` currently stores `_last_gnome_helper_presentation` and `_last_gnome_helper_presentation_log`. Rename these to backend-generic diagnostic names if the state remains on the generic surface, such as `_last_backend_presentation` and `_last_backend_presentation_log`.
- `overlay_client/platform_context.py` has GNOME helper health probing for client-authoritative backend status. Phase 4A should review this separately: either leave it documented as status/probe boundary behavior, or consolidate the duplicated `gdbus` health fetcher behind a backend-owned helper probe utility. It is not the same runtime presentation violation, but it should not drift into presentation/follow policy.
- Expected corrective shape:
- Update `AGENTS.md` during Phase 4A so future implementation prompts preserve the `fix219` backend architecture boundary.
- The `AGENTS.md` guidance should explicitly say generic follow/runtime surfaces must not import compositor-specific helper/presentation implementations directly; compositor-specific helper presentation belongs behind backend-owned bundle/consumer interfaces.
- Update `docs/compliance/edmc_compliance.md` during Phase 4A so compliance reviews explicitly check the `fix219` backend architecture boundary.
- Move the helper presentation runtime cycle under backend ownership, likely to `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py` or an equivalent backend-owned module.
- Expose helper presentation through `overlay_client/backend/consumers.py` or the GNOME Shell Wayland bundle instead of through a direct `follow_surface.py` import.
- Keep `overlay_client/backend/helper_ipc.py` as the pure helper transport/message validation boundary.
- Keep `follow_surface.py` as a generic runtime consumer that asks the backend layer whether helper presentation is available and runs it through a backend-owned interface.
- Add a narrow backend-facing interface that can return "no helper presentation for this backend" for non-GNOME paths and a presentation cycle result for GNOME helper mode.
- Keep GNOME-specific logging payload construction behind the backend-owned implementation; `follow_surface.py` may log a generic payload returned by the backend-facing result.
- Preserve current Phase 4 behavior:
- GNOME helper mode still probes health, fetches target state, applies presentation, validates applied rect, and skips legacy `setGeometry` as compositor-visible proof when helper presentation is active.
- Non-GNOME, Windows, native X11, XWayland compatibility, generic Wayland, and missing-helper fallback paths remain unchanged.
- Phase 4A implementation notes:
- Touch points are `AGENTS.md`, `docs/compliance/edmc_compliance.md`, `overlay_client/backend/consumers.py`, `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`, `overlay_client/follow_surface.py`, `overlay_client/setup_surface.py`, and the targeted tests.
- Chosen interface: add a backend-facing presentation consumer in `overlay_client/backend/consumers.py` that returns `None` when the selected backend has no backend-owned runtime presentation cycle, or a generic result object when a backend owns presentation for the current status.
- The generic result object exposes only backend-neutral fields to `follow_surface.py`: `should_show_overlay`, optional `scale_size`, and a stable diagnostics payload/signature. GNOME helper protocol details stay inside the backend-owned implementation.
- The GNOME helper runtime implementation moves to `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`; the existing tests will be updated to import through backend ownership.
- `platform_context.py` health probing remains an intentional client-authoritative status/probe boundary for Phase 4A. It may call the backend helper validation contract, but it must not make runtime presentation/follow decisions.
- Test selection:
- Unit tests for backend consumer routing and the moved GNOME helper presentation cycle.
- Follow-surface mixin tests for the backend-facing runtime wiring.
- Static/import-boundary test for `follow_surface.py`.
- Existing Phase 4 helper target/presentation tests and `make check`.
- Tests to run:
- Existing Phase 4 helper target/presentation/runtime tests.
- Backend consumer/bundle tests that prove GNOME helper presentation is exposed through backend ownership.
- Follow-surface mixin tests that prove generic follow code calls the backend-facing presentation interface rather than importing GNOME helper implementation directly.
- Add a static/import-boundary test that fails if `overlay_client/follow_surface.py` imports `overlay_client.gnome_helper_presentation` or references GNOME helper backend enums for presentation dispatch.
- `make check`.

| Stage | Description | Status |
| --- | --- | --- |
| 4A.1 | Update `AGENTS.md` and `docs/compliance/edmc_compliance.md` with the `fix219` backend-boundary rule for compositor-specific helper presentation | Completed |
| 4A.2 | Move helper presentation runtime cycle behind a backend-owned module/interface | Completed |
| 4A.3 | Update `follow_surface.py` to consume backend-owned helper presentation instead of GNOME-specific imports, backend enum checks, or GNOME helper protocol action checks | Completed |
| 4A.4 | Rename generic-surface GNOME-specific diagnostic state to backend-generic names if retained | Completed |
| 4A.5 | Review `platform_context.py` helper health probing and either document it as an intentional status/probe boundary or consolidate duplicated DBus health fetch code behind backend ownership | Completed |
| 4A.6 | Add/update backend consumer, follow-surface, and static boundary tests for the corrected ownership boundary | Completed |
| 4A.7 | Record tests and update Phase 4A status before starting Phase 5 | Completed |

### Phase 5: GNOME Helper-Mode Visibility And Focus Policy Hardening
- Replace foreground-flapping visibility behavior in GNOME helper mode with validated target/presentation policy.
- Ensure `keep_overlay_visible=false` does not hide/show repeatedly while the target is visible and on the current workspace.
- Preserve target-loss hiding/degrade behavior.
- Phase 5 must not start until Phase 4A is completed, because the visibility policy should build on the backend-owned helper presentation boundary rather than on a direct GNOME-specific `follow_surface.py` import.
- Risks: relaxing foreground behavior could keep the overlay visible over unrelated apps.
- Mitigations: require target visibility, workspace, and presentation state; hide/degrade on missing/stale/hidden/minimized target.
- Phase 5 touch points:
- `overlay_client/backend/presentation_policy.py` for pure backend-neutral visibility state and debounce decisions.
- `overlay_client/backend/consumers.py` for backend-facing target/presentation visibility fields derived from the GNOME helper runtime result.
- `overlay_client/follow_surface.py` for consuming the backend-neutral visibility decision without direct GNOME helper imports or raw GNOME backend/helper enum dispatch.
- `overlay_client/setup_surface.py` for initializing visibility-debounce state if runtime state is retained on the overlay surface.
- Tests under `overlay_client/tests/` for pure policy, backend consumer result shape, follow-surface wiring, and static boundary preservation.
- Expected unchanged behavior:
- Non-GNOME, Windows, native X11, XWayland compatibility, generic Wayland, and missing-helper fallback paths still use their existing visibility paths.
- GNOME helper mode still uses backend-owned helper target/presentation as the runtime source of truth.
- Missing/unhealthy/stale/incompatible helpers remain degraded and do not claim `true_overlay`.
- Phase 6 chrome/standalone behavior and Phase 7 validation/docs remain untouched.
- Visibility state machine:
- Target unavailable, minimized, hidden/off-workspace, or presentation unavailable states hide immediately and reset focus-loss debounce state.
- With `keep_overlay_visible=true`, a valid visible target remains visible even when unfocused.
- With `keep_overlay_visible=false`, a focused target shows immediately and resets focus-loss debounce state.
- With `keep_overlay_visible=false`, an unfocused but valid/presentable target remains visible while focus loss is debouncing, then hides only after both the sample and elapsed-time debounce thresholds are reached. This prevents 500 ms helper focus flicker from causing a hide/show loop.
- Named constants:
- `BACKEND_PRESENTATION_FOCUS_LOSS_HIDE_SAMPLES = 2`
- `BACKEND_PRESENTATION_FOCUS_LOSS_DEBOUNCE_SECONDS = 1.0`
- Phase 5 follow-up remap/warm-up state machine:
- If the overlay is hidden and the backend presentation policy decides it should become visible, prime the Qt top-level with a backend-authored presentation rect before `show()`. This is map hygiene only; it is not compositor-visible placement proof.
- The priming rect should come from the backend-facing presentation result, preferring a matching applied rect and otherwise using the requested helper rect. Legacy tracker geometry must not be used for this priming path.
- After a hidden-to-visible transition, enter a short backend presentation warm-up state.
- During warm-up, transient focus-loss samples do not hide the overlay while the target remains valid, visible on workspace, and presentation remains attachable.
- Warm-up completes once the helper has found the overlay window and reported a matching applied rect at least once.
- Warm-up expires after a bounded sample/time limit; after expiry, normal focus-loss debounce can hide the overlay again.
- Hard target-loss and unsupported states bypass warm-up and hide/degrade immediately: helper unhealthy/unavailable, target missing, launcher-only, ambiguous, stale, minimized, hidden/off-workspace, presentation unavailable, or presentation unsupported/not attachable.
- Named warm-up constants:
- `BACKEND_PRESENTATION_REMAP_WARMUP_MAX_SAMPLES = 4`
- `BACKEND_PRESENTATION_REMAP_WARMUP_SECONDS = 2.0`
- Backend-boundary preservation:
- `follow_surface.py` must continue to consume only backend-facing presentation result and pure visibility-policy objects.
- `follow_surface.py` must not import GNOME helper runtime modules, check `BackendInstance.GNOME_SHELL_WAYLAND`, check `HelperKind.GNOME_SHELL_EXTENSION`, or reason about `HelperPresentationAction`.
- Tests to run:
- Pure backend presentation visibility-policy tests.
- Backend consumer tests if the backend-facing result shape changes.
- Follow-surface mixin tests for debounce wiring.
- Follow-surface mixin tests for hidden-to-visible backend rect priming and warm-up behavior.
- Static backend architecture boundary tests.
- Existing Phase 4 helper target/presentation tests.
- `make check`.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Add pure visibility-policy tests for helper mode | Completed |
| 5.2 | Wire helper-mode visibility policy without changing non-GNOME behavior | Completed |
| 5.3 | Validate no flashing in windowed and borderless modes with `keep_overlay_visible=false` | Failed Manual GNOME Validation; Phase 6 Focus Safety Required |
| 5.4 | Validate target loss/minimize/workspace changes hide or degrade correctly | Headless Policy Tests Complete; Manual GNOME Validation Pending |
| 5.5 | Add hidden-to-visible backend rect priming and presentation warm-up after remap | Headless Follow-up Complete; Manual Revalidation Shows Phase 6 Focus Safety Gap |

### Phase 6: Chrome, Standalone, And Overlay Identity Hardening
- Ensure normal GNOME helper overlay mode is chrome/titlebar-free and not a standalone app/window.
- Keep explicit standalone mode gated by setting and only where supported.
- Make overlay title/class identity stable enough for Shell helper discovery without exposing unrelated windows.
- Phase 6 touch points:
- `overlay_client/backend/consumers.py` for backend-owned policy that decides whether the selected backend needs focus-safe overlay window flags.
- `overlay_client/platform_integration.py` for exposing that backend-owned policy to generic UI setup without leaking GNOME helper details.
- `overlay_client/interaction_controller.py` for applying Qt window identity/focus flags before native click-through and before GNOME helper remap `show()`.
- `overlay_client/setup_surface.py` for wiring the platform policy into the interaction controller.
- `overlay_client/follow_surface.py` only for invoking a backend-neutral pre-show flag preparation path before showing a remapped helper-mode overlay.
- Tests under `overlay_client/tests/` for backend policy, platform exposure, interaction flag behavior, follow pre-show ordering, and backend-boundary preservation.
- Expected unchanged behavior:
- PyQt rendering remains the default and stays outside the GNOME Shell extension.
- GNOME helper mode still uses backend-owned Shell helper target/presentation state as the runtime source of truth.
- Generic follow/runtime code must not import GNOME helper runtime modules, check GNOME backend/helper enums, or reason about helper protocol actions.
- Legacy tracker geometry must not drive visible GNOME helper-mode placement.
- Missing/unhealthy/stale/incompatible helpers remain degraded and do not claim `true_overlay`.
- Hidden-to-visible map rect priming and warm-up from Phase 5 remain intact.
- Installer lifecycle remains unchanged.
- Focus/chrome/standalone identity contract:
- Normal GNOME helper overlay mode is a frameless, always-on-top PyQt-rendered overlay surface.
- Normal GNOME helper overlay mode must not use the explicit standalone app/window identity path.
- Normal GNOME helper overlay mode should set `Qt.WindowDoesNotAcceptFocus` where available so the overlay does not steal focus from the game.
- `Qt.Tool` remains disabled for Wayland unless separately proven safe.
- `WA_ShowWithoutActivating`, transparent mouse input, frameless flags, and platform click-through stay in force.
- Standalone mode remains explicitly setting-gated and is not enabled by GNOME helper normal overlay mode.
- Chosen Qt flag strategy:
- Add a backend-owned consumer policy for "focus-safe overlay window flags required" and expose it through `PlatformController`.
- Extend `InteractionController` with a backend-neutral callback so it can apply `Qt.WindowDoesNotAcceptFocus` without knowing about GNOME.
- Refactor click-through flag application into a reusable pre-show preparation method. GNOME helper remap can call this before `show()` so focus-safe flags are already set when the top-level maps.
- Treat pre-show flag preparation and Qt geometry priming as map hygiene only, not compositor-visible placement proof.
- Backend-boundary preservation:
- `follow_surface.py` may call a generic interaction-controller pre-show preparation method, but must not dispatch on GNOME helper/backend enums or import GNOME helper implementation modules.
- GNOME-specific helper protocol details stay behind backend-owned consumer/bundle interfaces.
- Tests to run:
- Unit tests for backend focus-safe flag policy.
- Platform-controller tests for exposing that policy without changing non-GNOME behavior.
- Interaction-controller tests for `WindowDoesNotAcceptFocus`, `FramelessWindowHint`, `Qt.Tool` Wayland behavior, and pre-show preparation without `show()`/raise.
- Follow-surface mixin tests for pre-show flag preparation before remap `show()`.
- Static backend architecture boundary tests.
- Existing Phase 5 presentation/focus policy tests.
- `make check`.
- Risks: changing Qt window flags can affect click-through or focus behavior.
- Mitigations: isolate GNOME helper-mode flag changes, unit-test setting behavior, and manually validate compositor behavior.

| Stage | Description | Status |
| --- | --- | --- |
| 6.1 | Prove current overlay Shell title/class/chrome state | Manual Evidence Captured In Phase 5; Focus Safety Gap Identified |
| 6.2 | Define normal versus standalone mode window identity contract | Completed |
| 6.3 | Add tests for standalone/focus-safe setting behavior if code changes are needed | Headless Tests Passed |
| 6.4 | Validate chrome/titlebar-free behavior manually on GNOME 46 | Failed Manual GNOME Validation; Focus-Safe Flag Insufficient |

### Phase 6 Execution Summary
- Stage 6.1: Manual evidence from Phase 5 identified the remaining focus-safety gap: after correct helper placement and remap priming, GNOME still reports `target_focus=false` while the overlay is mapped, causing `keep_overlay_visible=false` to hide and remap in a slower flash loop.
- Stage 6.2: Completed. Normal GNOME helper overlay mode remains PyQt-rendered, frameless, always-on-top, non-standalone, transparent to mouse input when drag mode is off, and now requests non-focus-stealing window identity through a backend-owned policy.
- Stage 6.3: Headless tests passed. Added a backend-owned `requires_focus_safe_overlay_flags(...)` consumer, exposed it through `PlatformController`, wired `InteractionController` to apply `Qt.WindowDoesNotAcceptFocus` when that backend-neutral policy requires it, and made the GNOME helper remap path prepare window flags before `show()`.
- Backend boundary remains preserved: `follow_surface.py` calls only backend-facing presentation and generic interaction-controller APIs. It still does not import GNOME helper runtime modules, check GNOME backend/helper enums, or reason about helper protocol actions.
- The pre-show flag preparation is map/focus hygiene only. Runtime placement proof remains helper presentation applied-rect matching, not Qt geometry or Qt flag application.
- Stage 6.4 failed manual GNOME validation on 2026-05-11. `focus_safe_window=applied` confirms `Qt.WindowDoesNotAcceptFocus` was applied before remap `show()`, but it was not sufficient to eliminate the focus/visibility loop.
- Manual log evidence from 2026-05-11:
- Hidden state still reports `overlay_window_not_found`, as expected while the PyQt top-level is unmapped.
- On focus return, runtime logs `Prepared overlay window flags for click-through=True (reason=backend_presentation_pre_show focus_safe_window=applied)` before `show()`, confirming the Phase 6 pre-show flag path is active.
- After remap, helper presentation reports matching applied rects such as `applied={'x': 489, 'y': 188, 'width': 1440, 'height': 997}` and `overlay_window_found=True`, so the upper-left/tiny-geometry remap issue remains fixed.
- Despite the focus-safe flag, GNOME later reports sustained `target_focus=False` for multiple samples while the applied rect still matches. The visibility policy then hides at `visibility_reason=focus_lost_debounced`, causing another hidden/remap cycle.
- Interpretation: Phase 6 proved the Qt no-focus flag path is active but insufficient on this GNOME Wayland setup. The remaining problem is not helper placement or pre-show rect priming; it is that GNOME target focus still becomes false while the overlay is mapped. Further work should investigate a different focus source or a different normal-mode mapping strategy rather than increasing debounce again.
- Phase 6 follow-up validation on 2026-05-11 with `keep_overlay_visible=true` proved the mapped-overlay hypothesis:
- Runtime reported continuous matching helper presentation rects with `overlay_window_found=True`, `visibility=visible`, and `visibility_reason=keep_overlay_visible`.
- During the same stable mapped period, helper target focus still reported `target_focus=False` for long stretches, later flipping back to `true`, without breaking placement.
- No hidden/remap cycle appeared while `keep_overlay_visible=true` kept the PyQt top-level mapped.
- Interpretation: `target_focus` is not reliable enough to drive Qt mapped/unmapped state on GNOME helper mode. It may still drive whether overlay content is visible, but it should not directly call `hide()` while the target is otherwise valid, visible on workspace, and presentable.
- Next fix direction: when `keep_overlay_visible=false` and a valid/presentable GNOME helper target becomes unfocused, keep the overlay top-level mapped and helper-attached, but visually suppress overlay content. Continue to hard-hide/degrade for real target-loss states such as helper unhealthy, target missing, launcher-only, ambiguous, stale, minimized, hidden/off-workspace, or presentation unsupported.

### Tests Run For Phase 6
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py`
- Result: passed; 49 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py`
- Result: passed; 90 passed.
- `overlay_client/.venv/bin/python -m py_compile overlay_client/backend/consumers.py overlay_client/platform_integration.py overlay_client/interaction_controller.py overlay_client/follow_surface.py overlay_client/setup_surface.py`
- Result: passed.
- `git diff --check`
- Result: passed.
- `make check`
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 960 passed and 21 skipped.

### Phase 6A: Mapped Suppression For GNOME Helper-Mode Focus Loss
- Replace GNOME helper-mode focus-loss `hide()` behavior with a mapped-but-visually-suppressed state when the target is still valid and presentable.
- Preserve hard hide/degrade behavior for real target-loss or unsupported states.
- Do not implement Phase 7 validation/support claim wording.
- Evidence driving this phase:
- With `keep_overlay_visible=false`, the overlay hides on sustained `target_focus=false`; once hidden, helper presentation reports `overlay_window_not_found`, so focus return requires remapping and can loop.
- With `keep_overlay_visible=true`, helper presentation remains stable and matched while `target_focus=false` appears for long stretches. This proves the mapped overlay can remain helper-attached without placement instability.
- `Qt.WindowDoesNotAcceptFocus` was applied before remap but did not eliminate `target_focus=false`, so the fix should not depend on another debounce increase or the existing no-focus flag alone.
- Phase 6A touch points:
- `overlay_client/backend/presentation_policy.py` for pure policy that distinguishes hard hide/degrade from soft focus-loss suppression.
- `overlay_client/backend/consumers.py` only if the backend-facing presentation result needs a backend-neutral content/surface visibility recommendation.
- `overlay_client/follow_surface.py` for applying mapped suppression without direct GNOME helper imports or raw GNOME backend/helper enum dispatch.
- `overlay_client/setup_surface.py` or a small helper if runtime suppression state must be initialized.
- Rendering/content surfaces if the safest suppression mechanism is to hide/clear payload content, set effective opacity, or temporarily suppress paint while keeping the Qt top-level mapped.
- Expected unchanged behavior:
- PyQt rendering remains the default.
- GNOME helper mode still uses backend-owned Shell helper target/presentation state as the runtime source of truth.
- Generic follow/runtime code must keep using backend-owned consumer interfaces.
- Legacy tracker geometry must not drive visible GNOME helper-mode placement.
- Missing/unhealthy/stale/incompatible helpers remain degraded.
- Normal non-GNOME visibility behavior remains unchanged.
- Installer lifecycle and helper package remain unchanged.
- Mapped suppression policy:
- Hard hide/degrade immediately when the helper is unhealthy/unavailable, target is missing, launcher-only, ambiguous, stale, minimized, hidden/off-workspace, presentation is unavailable, presentation is unsupported, or helper presentation is not attachable.
- With `keep_overlay_visible=true`, keep current visible/attached behavior.
- With `keep_overlay_visible=false` and target focused, show overlay content while keeping the mapped helper-attached top-level.
- With `keep_overlay_visible=false` and target loses focus but remains valid, visible on workspace, and presentable, keep the top-level mapped and helper-attached, but suppress overlay content after the existing debounce.
- Do not call Qt `hide()` for soft focus loss in GNOME helper mode.
- On focus return, restore content visibility without remapping the Qt top-level whenever the helper still reports `overlay_window_found=True` and matching applied rect.
- Suppression mechanism selection:
- Prefer the narrowest content-only suppression that keeps the Qt top-level mapped and click-through: for example, suppress/clear rendered content or set an effective overlay opacity/content opacity to zero.
- Treat `setWindowOpacity(0)` as a candidate only if it keeps the Shell MetaWindow discoverable and helper presentation stable; add tests around whatever abstraction is chosen.
- Do not use screenshots, broad window dumps, or unrelated window title dumps for diagnostics.
- Chosen implementation mechanism:
- Add backend-neutral policy output that separates mapped surface state from content visibility: `surface_action=hidden`, `surface_action=mapped_visible`, and `surface_action=mapped_suppressed`.
- Keep `show` as the mapped/unmapped top-level decision for compatibility with existing visibility wiring.
- Add `content_visible` / `content_suppressed` to the pure decision object.
- In GNOME helper presentation mode, soft focus loss after debounce returns `show=True`, `surface_action=mapped_suppressed`, and `content_visible=False`.
- Content suppression is local to the PyQt renderer: set a runtime `_backend_presentation_content_suppressed` flag, hide the message label, request repaint, and make `paintEvent` clear/skip overlay painting while suppressed.
- Do not use `setWindowOpacity(0)` for the first implementation, because opacity changes could affect Shell presentation/readback or click-through behavior more broadly than a content-only paint suppression.
- Diagnostics:
- Log `surface_action` or equivalent as `mapped_visible`, `mapped_suppressed`, or `hidden`.
- Log whether suppression is due to soft focus loss or hard target loss.
- Log `content_visible` / `content_suppressed`, `keep_overlay_visible`, target focus/workspace/minimized state, overlay window found, applied rect match, and presentation reasons.
- Backend-boundary preservation:
- `follow_surface.py` must not import GNOME helper runtime modules or check `BackendInstance.GNOME_SHELL_WAYLAND`, `HelperKind.GNOME_SHELL_EXTENSION`, or `HelperPresentationAction`.
- Tests to run:
- Unit tests for pure policy: focused visible, soft focus loss maps/suppresses instead of hides, focus return restores content, hard target-loss states still hide/degrade.
- Follow-surface mixin tests proving soft focus loss does not call `hide()` in backend presentation mode and does call the chosen suppression/restoration hooks.
- Backend consumer/result tests if result shape changes.
- Static backend-boundary tests.
- Existing Phase 5/6 presentation, focus, and interaction tests.
- `make check`.

| Stage | Description | Status |
| --- | --- | --- |
| 6A.1 | Add pure mapped-suppression policy for soft focus loss versus hard target loss | Completed |
| 6A.2 | Add runtime suppression/restoration hook while keeping helper-attached top-level mapped | Completed |
| 6A.3 | Preserve non-GNOME visibility behavior and backend-boundary guardrails | Completed |
| 6A.4 | Add/update unit, follow-surface, backend-boundary, and regression tests | Headless Tests Passed |
| 6A.5 | Manually validate no flash with `keep_overlay_visible=false` after implementation | Core Manual Validation Passed; Helper Reload Recheck Passed; Workspace Deferred |

### Phase 6A Execution Summary
- Stage 6A.1: Completed. `BackendPresentationVisibilityDecision` now separates mapped-surface state from content visibility through `surface_action` (`hidden`, `mapped_visible`, `mapped_suppressed`) and `content_visible` / `content_suppressed`.
- Stage 6A.1: Completed. Soft focus loss after the existing debounce now returns `show=True`, `surface_action=mapped_suppressed`, and `content_visible=False` instead of hiding the PyQt top-level. Hidden overlays stay hidden until the target regains focus, preserving the focused remap/warm-up path from Phase 5.
- Stage 6A.1: Completed. Hard loss states still return `surface_action=hidden` and `content_visible=False`, including target unavailable, minimized, off-workspace, presentation unavailable, presentation not attachable, and warm-up expiry without focus.
- Stage 6A.2: Completed. GNOME helper presentation mode now applies content suppression after the visibility decision without calling `hide()` for soft focus loss. Suppression hides the message label, requests repaint, and makes `paintEvent` clear/skip overlay painting while keeping the Qt top-level mapped.
- Stage 6A.2: Completed. Focus return restores content without remapping when the helper-attached top-level is still mapped.
- Stage 6A.3: Completed. Non-GNOME follow behavior remains on the legacy path. `follow_surface.py` still consumes backend-owned presentation policy/results and does not import GNOME helper runtime modules or branch on raw GNOME backend/helper enums.
- Stage 6A.4: Headless tests passed. Added policy tests for hidden, mapped-visible, mapped-suppressed, and hard-hide outcomes; follow-surface tests for suppress-without-hide, restore-without-remap, and hard-hide restoration; and setup/paint assertions for the suppression flag.
- Stage 6A.5: No-flash validation passed on 2026-05-11. Manual GNOME logs show sustained soft focus loss using `visibility=visible`, `visibility_reason=focus_lost_suppressed`, `surface_action=mapped_suppressed`, `content_visible=False`, `overlay_window_found=True`, and matching applied rects. No `Overlay visibility set to hidden` or remap warm-up occurred during this soft focus-loss interval.
- Stage 6A.5: Focus return validation passed on 2026-05-11. Logs show `visibility_reason=target_focused`, `surface_action=mapped_visible`, `content_visible=True`, focus-loss counters reset, and `Backend presentation content restored (reason=target_focused)` without remapping.
- Stage 6A.5: Click-through validation passed on 2026-05-11 while visible and while mapped/suppressed. The mapped-suppressed click test showed no `Overlay visibility set to hidden`, no remap warm-up, no primed Qt map geometry, and no visible flash/focus steal after clicking where the overlay would normally be.
- Stage 6A.5: Target minimize validation is not applicable. The tested Elite Dangerous window does not expose a minimize action in this environment, and Phase 7 should validate target-loss/game-exit behavior instead of carrying minimize as a pending gate.
- Stage 6A.5: Game exit/target missing and game relaunch/target reacquire validation passed on 2026-05-11.
- Stage 6A.5: Workspace/off-workspace validation is deferred. The overlay currently behaves as a standalone-like GNOME window even when standalone mode is not selected, so testing off-workspace behavior requires moving both the game and overlay together. This does not block the Phase 6A no-flash fix, but it remains part of the standalone/identity work.
- Stage 6A.5 recheck on 2026-05-12 after GNOME helper logout/login reload and Phase 6B.6 DisplayConfig monitor inventory: user confirmed the overlay is not flashing at all.

### Phase 6A Manual GNOME Validation Evidence
- Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay visibility|visibility_reason|target_focus|overlay_window_found|remap_warmup|focus_loss"
```
- Result on 2026-05-11: no-flash path passed for the tested focus-loss cycle with `keep_overlay_visible=false`.
- Evidence summary:
- During focus loss, helper presentation stayed attached and matched: `applied={'x': 654, 'y': 261, 'width': 1440, 'height': 997}`, `delta=[0, 0, 0, 0]`, `rect_match=True`, and `overlay_window_found=True`.
- The visibility policy suppressed content instead of hiding the Qt top-level: `visibility=visible`, `visibility_reason=focus_lost_suppressed`, `surface_action=mapped_suppressed`, and `content_visible=False`.
- Remap remained inactive during soft focus loss: `remap_warmup=inactive`.
- On focus return, content restored without remap: `visibility_reason=target_focused`, `surface_action=mapped_visible`, `content_visible=True`, `focus_loss_samples=0`, and `Backend presentation content restored (reason=target_focused)`.
- Click-through while visible and while mapped/suppressed was manually validated. Suppressed-state click-through evidence included `visibility_reason=focus_lost_suppressed`, `surface_action=mapped_suppressed`, `content_visible=False`, `overlay_window_found=True`, `rect_match=True`, `remap_warmup=inactive`, and no hide/remap/prime lines after clicking where the overlay would normally be.
- Target minimize validation is not applicable because the tested Elite Dangerous window cannot be minimized in the current environment. Phase 7 should validate target-loss/game-exit behavior instead.
- Game exit/target missing and game relaunch/target reacquire were manually validated on 2026-05-11.
- Workspace/off-workspace validation is deferred until the standalone-like overlay identity behavior is fixed; current workspace movement requires moving both the game and overlay, which does not prove the intended off-workspace hard-hide policy.
- Additional manual evidence from 2026-05-11 identified a separate monitor-boundary issue when Elite is resized to a mode whose frame fallback exceeds the monitor height. The helper requested `{'x': 760, 'y': 29, 'width': 1920, 'height': 1477}` on a 1440-high primary monitor. GNOME then moved/constrained the overlay to the second monitor, logging `Overlay moveEvent: pos=(3440,0) frame=(3440, 0, 1920, 1440) ... monitor=HDMI-1 3440x1440@(3440,0)`, and subsequent helper presentation reported `applied={'x': 3440, 'y': 0, 'width': 1920, 'height': 1440}` with `applied_rect_mismatch`.
- Interpretation: this is not the Phase 6A no-flash bug. It is a frame-rect fallback bounds bug. When `contentRect` is unavailable and `frameRect` exceeds the target monitor bounds, the runtime asks GNOME to place the PyQt overlay outside the monitor. GNOME may then rehome or constrain the overlay to another output. Follow-up should add target monitor geometry to the helper payload and clamp `frame_rect_fallback` presentation rects to that monitor before calling `ApplyPresentation`.

### Tests Run For Phase 6A
- `overlay_client/.venv/bin/python -m py_compile overlay_client/backend/presentation_policy.py overlay_client/follow_surface.py overlay_client/overlay_client.py overlay_client/setup_surface.py`
- Result: passed.
- `git diff --check`
- Result: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_setup_surface.py overlay_client/tests/test_backend_architecture_boundary.py`
- Result: passed; 29 passed, 4 skipped. Skips were PyQt-marked setup/paint tests without `PYQT_TESTS=1` in this targeted headless command.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_setup_surface.py`
- Result: passed; 94 passed, 4 skipped. Skips were PyQt-marked setup/paint tests without `PYQT_TESTS=1` in this targeted headless command.
- `make check`
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 965 passed and 21 skipped.

### Phase 6B: Frame Fallback Monitor-Bounds Clamp
- Fix the monitor jump that happens when GNOME helper mode uses `frame_rect_fallback` and the fallback rect extends outside the target monitor.
- Evidence driving this phase:
- On 2026-05-11, resizing Elite to a mode associated with 1440-height output produced helper presentation `requested={'x': 760, 'y': 29, 'width': 1920, 'height': 1477}`.
- The primary monitor height is 1440, so the requested fallback rect bottom was `1506`, outside the target output.
- GNOME then moved/constrained the PyQt overlay to the second monitor: `Overlay moveEvent: pos=(3440,0) frame=(3440, 0, 1920, 1440) ... monitor=HDMI-1 3440x1440@(3440,0)`.
- Subsequent helper presentation reported `applied={'x': 3440, 'y': 0, 'width': 1920, 'height': 1440}` and `applied_rect_mismatch`.
- Interpretation:
- This is a frame-fallback bounds bug, not a focus/no-flash regression.
- `contentRect` is still unavailable in the tested window mode, so runtime uses `frameRect`.
- A frame rect can include decorations or compositor margins that extend beyond the target output. Passing that oversized rect directly to `move_resize_frame` lets GNOME constrain or rehome the overlay.
- Goal:
- Never ask GNOME to place the PyQt overlay outside the target monitor when the request comes from `frame_rect_fallback`.
- Preserve the current behavior when a valid `contentRect` exists.
- Keep the result degraded while using `frame_rect_fallback`; this phase prevents wrong-monitor placement but does not make a `true_overlay` claim.
- Touch points:
- `helpers/gnome_shell_extension/extension.js`: include target monitor geometry in target payloads, e.g. `monitorRect` / `monitor_rect`, using the same monitor index already reported as `monitor`.
- Phase 6B.6 corrective touch point after failed manual validation: `helpers/gnome_shell_extension/extension.js` must derive monitor bounds from `org.gnome.Mutter.DisplayConfig.GetCurrentState` instead of relying on `global.display.get_monitor_geometry`, which returned no usable monitor geometry in the validated GNOME 46 session.
- The DisplayConfig parser should map the target window's `monitor` index to the logical monitor list, derive `x`, `y`, `width`, `height`, connector/output identity, and scale, and cache the result briefly so helper polling does not hammer DBus.
- Conservative fallback policy: if DisplayConfig lookup or parsing fails, try the old `global.display.get_monitor_geometry` path; if both fail, emit `monitorRect=null` and keep the existing backend missing-monitor fallback behavior. Do not infer monitor bounds from primary-monitor assumptions or overlay position.
- `overlay_client/backend/helper_ipc.py`: add `monitor_rect` to `HelperTargetWindow`, parse it from helper target payloads, include it in `to_payload()`, and use it in `resolve_gnome_shell_helper_target_rect(...)`.
- `overlay_client/backend/helper_ipc.py`: add a small pure rect clamp/intersection helper for frame-fallback presentation rects.
- `overlay_client/tests/test_gnome_shell_helper_target_state.py`: validate parsing and payload round-trip of helper monitor rect.
- `overlay_client/tests/test_gnome_shell_helper_presentation_state.py`: validate that an over-tall `frame_rect_fallback` is clamped to the monitor before presentation request construction.
- Existing backend consumer and helper runtime tests if payload/result shapes change.
- Expected unchanged behavior:
- PyQt rendering remains the default.
- GNOME helper mode still uses backend-owned helper target/presentation state as runtime source of truth.
- Generic follow/runtime code continues using backend-owned consumer interfaces; no direct GNOME helper imports or enum dispatch in `follow_surface.py`.
- `contentRect` remains preferred and must not be clamped unless it is invalid or outside a later explicitly documented policy.
- Missing/unhealthy/stale/incompatible helper remains degraded overlay.
- Phase 5 remap priming/warm-up remains intact.
- Phase 6 focus-safe window flags remain intact.
- Phase 6A mapped suppression remains intact.
- Installer lifecycle remains unchanged, though manual validation after changing the extension code will require reinstalling/reloading the helper extension.
- Clamp policy:
- Preferred rect remains valid `contentRect`.
- If `contentRect` is missing and `frameRect` is valid, use `frame_rect_fallback`.
- If `frame_rect_fallback` and target `monitorRect` is valid, clamp the fallback rect to the monitor bounds before building the `ApplyPresentation` request.
- The clamp must never move the request to another monitor.
- The clamped rect must keep positive width/height. If the intersection is empty or invalid, degrade with a clear reason instead of calling `ApplyPresentation`.
- Add a diagnostic degrade reason such as `frame_rect_clamped_to_monitor` when clamping changes the fallback rect.
- Keep `frame_rect_fallback` in degrade reasons even after clamping so final support remains degraded until content alignment is proven.
- Diagnostics:
- Log/record target `monitor`, `outputName`, `monitorRect`, `frameRect`, selected presentation rect, and clamp reason.
- Existing runtime presentation logs should make the before/after visible through `requested`, `applied`, `delta`, `rect_match`, and `reasons`.
- Backend-boundary preservation:
- Keep the clamp inside helper IPC/backend-owned presentation request construction.
- Do not put monitor-boundary logic in `follow_surface.py`.
- Tests to run:
- Unit tests for monitor rect parsing and `HelperTargetWindow.to_payload()`.
- Unit tests for `resolve_gnome_shell_helper_target_rect(...)`: content rect wins; frame fallback inside monitor unchanged; over-tall frame fallback clamps; non-overlapping frame fallback degrades.
- Source/static tests for helper extension DisplayConfig lookup, cache, and old monitor-geometry fallback.
- Backend consumer/runtime tests touched by payload shape changes.
- Static backend-boundary test.
- Existing Phase 5/6/6A presentation, focus, interaction, and follow tests.
- `make check`.
- Manual GNOME validation:
- Reproduce the 1440-height window mode that previously jumped to the second monitor.
- Expected: helper requested rect is clamped inside the target monitor, overlay stays on the same monitor as Elite, and no `Overlay moveEvent` to `HDMI-1` occurs.
- Expected: `frame_rect_fallback` remains in reasons, and `frame_rect_clamped_to_monitor` appears when the clamp changed the request.
- Expected: no regression to Phase 6A no-flash behavior.

| Stage | Description | Status |
| --- | --- | --- |
| 6B.1 | Add helper target monitor geometry to GNOME Shell target payloads | Completed |
| 6B.2 | Parse/store monitor rect in backend helper target model | Completed |
| 6B.3 | Clamp over-bound `frame_rect_fallback` presentation rects to target monitor bounds | Completed |
| 6B.4 | Add parser, clamp-policy, backend-boundary, and regression tests | Headless Tests Passed |
| 6B.5 | Manually validate 1440-height resize no longer jumps overlay to second monitor | Failed; helper emitted no monitor rect |
| 6B.6 | Replace helper monitor geometry lookup with Mutter DisplayConfig-backed monitor inventory | Headless Tests Passed |
| 6B.7 | Reinstall/reload helper and revalidate 1440-height wrong-monitor case | Completed |

### Phase 6B Execution Summary
- Stage 6B.1: Completed. The GNOME Shell helper target payload now includes `monitorRect` derived from the target window's monitor index. The payload continues to report `monitor`, `outputName`, and `monitorScale`.
- Stage 6B.2: Completed. Backend helper target parsing now stores optional `monitor_rect` on `HelperTargetWindow`, includes it in `to_payload()`, and exposes monitor/frame diagnostics in runtime presentation logs.
- Stage 6B.3: Completed. `contentRect` remains preferred and unchanged. When `contentRect` is missing and `frame_rect_fallback` is used, the backend intersects the frame rect with the target monitor rect before building `ApplyPresentation`. If the frame fallback misses the monitor, the request degrades instead of applying presentation.
- Stage 6B.3: Completed. `frame_rect_fallback` remains in degrade reasons after clamping, and `frame_rect_clamped_to_monitor` is added only when the selected fallback rect changes. This preserves the conservative degraded state and does not claim `true_overlay`.
- Stage 6B.4: Headless tests passed. Added parser coverage for `monitorRect`, clamp-policy tests for primary and non-primary monitors, content-rect pass-through coverage, missing-monitor backward compatibility, non-overlap degradation, and reran backend-boundary/regression checks.
- Stage 6B.5: Manual GNOME validation failed after helper reinstall and EDMC restart on 2026-05-11. Runtime logs showed `target_monitor=0`, `output=`, and `monitor_rect=None`, so the backend clamp never had monitor bounds to use. The helper continued requesting the unbounded frame fallback, e.g. `requested={'x': 760, 'y': 29, 'width': 1920, 'height': 1477}`, and GNOME again moved/constrained the overlay to the second monitor with `Overlay moveEvent: pos=(3440,0) frame=(3440, 0, 1920, 1440) ... monitor=HDMI-1`.
- Stage 6B.5 interpretation: the backend clamp policy is still the correct behavior, but the helper-side monitor geometry source was wrong for this environment. `global.display.get_monitor_geometry` did not produce a usable monitor rect in the tested GNOME 46 session.
- Stage 6B.6 validation probe: `org.gnome.Mutter.DisplayConfig.GetCurrentState` is available and returns the required logical monitor layout. A read-only GJS probe returned monitor `0` as `DP-2` at `(0,0,3440,1440)` and monitor `1` as `HDMI-1` at `(3440,0,3440,1440)`. Applying the planned clamp to the failing frame rect `(760,29,1920,1477)` yields `(760,29,1920,1411)`, which is inside the Elite target monitor and should avoid GNOME rehoming the overlay to `HDMI-1`.
- Stage 6B.6 note: `org.gnome.Shell.Eval` is not a reliable validation path in this session; the probe returned `(false, '')`.
- Stage 6B.6: Headless implementation complete. The helper now prefers `org.gnome.Mutter.DisplayConfig.GetCurrentState`, maps the target window's monitor index to the logical monitor list, derives `monitorRect`, `outputName`, and `monitorScale`, and caches the DisplayConfig monitor inventory for one second.
- Stage 6B.6: Conservative fallback preserved. If DisplayConfig lookup or parsing fails, the helper falls back to `global.display.get_monitor_geometry`; if that also fails, it emits `monitorRect=null` and the existing backend missing-monitor behavior remains unchanged. The backend clamp itself was not rolled back or moved.
- Stage 6B.7 partial manual validation on 2026-05-11: after logout/login reloaded the GNOME Shell extension source, `GetTargetState` returned `monitorRect={"x":0,"y":0,"width":3440,"height":1440}` and `monitorScale=1` for the Elite target. `outputName` was still empty, but this does not block the backend clamp.
- Stage 6B.7 decision: empty `outputName` is diagnostic-only and is not a Phase 7 blocker. Placement, clamping, target selection, and support gating use `monitorRect` and presentation state, not the connector label.
- Stage 6B.7 partial manual validation on 2026-05-11: user confirmed the 1440-height reproduction now stays on the intended screen instead of jumping to the wrong monitor.
- Stage 6B.7 manual log validation on 2026-05-12: runtime logs showed `monitor_rect={'x': 0, 'y': 0, 'width': 3440, 'height': 1440}` for `target_monitor=0`; the failing frame fallback `{'x': 760, 'y': 29, 'width': 1920, 'height': 1477}` was presented as the clamped request `{'x': 760, 'y': 29, 'width': 1920, 'height': 1411}`; reasons included `frame_rect_fallback` and `frame_rect_clamped_to_monitor`; and the next sample reported matching `applied={'x': 760, 'y': 29, 'width': 1920, 'height': 1411}` with `rect_match=True`.
- Stage 6B.7 manual log validation on 2026-05-12: no wrong-monitor `Overlay moveEvent` to `HDMI-1` appeared in the supplied reproduction logs.
- Stage 6B.7: Completed. Phase 6A no-flash behavior was rechecked after the helper reload and still passed; user reported no flashing at all.
- Backend boundary remains preserved: the clamp lives in backend helper IPC/request construction. `follow_surface.py` only logs backend-owned diagnostics and still does not import GNOME helper runtime modules, branch on raw GNOME backend/helper enums, or check helper protocol actions.

### Tests Run For Phase 6B
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_backend_architecture_boundary.py`
- Result: passed; 33 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_setup_surface.py`
- Result: passed; 99 passed, 4 skipped. Skips were PyQt-marked setup tests without `PYQT_TESTS=1` in this targeted headless command.
- `overlay_client/.venv/bin/python -m py_compile overlay_client/backend/helper_ipc.py overlay_client/backend/__init__.py overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/backend/consumers.py overlay_client/follow_surface.py`
- Result: passed.
- `make check`
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 970 passed and 21 skipped.
- `git diff --check`
- Result: passed.
- Manual validation after helper reinstall/reload and EDMC restart on 2026-05-11:
- Result: failed. Logs showed `monitor_rect=None` and `output=` for `target_monitor=0`; no `frame_rect_clamped_to_monitor` reason appeared; the request remained the oversized `frame_rect_fallback`; GNOME moved the overlay to `HDMI-1`.
- `gdbus call --session --dest org.gnome.Mutter.DisplayConfig --object-path /org/gnome/Mutter/DisplayConfig --method org.gnome.Mutter.DisplayConfig.GetCurrentState`
- Result: passed. Mutter DisplayConfig returned the active logical monitor layout, including `DP-2` at `(0,0)` and `HDMI-1` at `(3440,0)`.
- `gjs -c '<DisplayConfig GetCurrentState probe and clamp calculation>'`
- Result: passed. The probe produced logical monitors `DP-2 (0,0,3440,1440)` and `HDMI-1 (3440,0,3440,1440)`, and calculated the failing frame rect clamp as `(760,29,1920,1411)`.
- `overlay_client/.venv/bin/python -m pytest tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_backend_architecture_boundary.py`
- Result: passed; 41 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_setup_surface.py tests/test_gnome_shell_extension_manifest.py`
- Result: passed; 107 passed, 4 skipped. Skips were PyQt-marked setup tests without `PYQT_TESTS=1` in this targeted headless command.
- `git diff --check`
- Result: passed.
- `make check`
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 971 passed and 21 skipped.

### Phase 7: Manual Validation Matrix And True-Overlay Gate Review
- Run the final GNOME validation matrix for windowed and borderless modes.
- Document pass/fail/deferred gates.
- Only allow `true_overlay` if all gates pass.
- If a validation gap remains, do not treat it as accepted unless the user explicitly signs off on that named gap. Record the sign-off, the exact residual risk, and the support/status wording that will remain conservative because of it.
- Phase 7 sequencing decision: start with windowed mode first, then borderless after the windowed matrix is documented.
- Phase 7 validation style decision: use numbered validation items with one narrow log/tail command per item where possible.
- Phase 7 support-wording decision: keep GNOME Wayland support degraded/experimental while `frame_rect_fallback` remains the active rect source. Do not claim `true_overlay` unless `contentRect` or an equivalent content-alignment proof passes all required gates.
- Risks: partial success could be overstated in UI/status text.
- Mitigations: keep degraded/experimental wording until every gate has evidence.
- Test type selection: Phase 7 is compositor-visible manual validation. Use the narrow tail/GDBus commands below for evidence. Add or rerun headless tests only if Phase 7 requires code or test changes.
- Non-blocking/deferred items:
- Workspace/off-workspace validation is deferred because current workspace behavior requires moving both Elite and the overlay together, which does not prove the intended hard-hide policy.
- Minimize validation is not applicable because the tested Elite Dangerous window cannot be minimized in this environment. Validate target-loss/game-exit instead.
- Empty `outputName` is diagnostic-only and is not a blocker because placement and support gates use `monitorRect`, helper presentation state, and degrade reasons.

#### Phase 7 Common Setup
- Start EDMC with GNOME helper mode active.
- Use Elite Dangerous windowed mode for Stage 7.1. Borderless validation waits until windowed evidence is recorded.
- Keep `keep_overlay_visible=false` for no-flash focus validation.
- Use narrow log commands and stop each tail with `Ctrl-C` after the specific action is observed.

#### Phase 7 Windowed Validation Matrix
1. Target discovery and helper health.
Command:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.GetHealth

gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.GetTargetState '{}'
```
Expected pass: health `status=healthy`, target `status=target_found`, target title contains `Elite - Dangerous (CLIENT)`, `monitorRect` is non-null, `showingOnWorkspace=true`, and target is not minimized.
Expected fail: helper unhealthy/unavailable, target missing/launcher-only/ambiguous, stale payload, or `monitorRect` missing after helper reload.

2. Windowed move follows target.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay moveEvent" \
  | grep --line-buffered -E "requested=|applied=|delta=|rect_match=|Overlay moveEvent|target_monitor=|monitor_rect="
```
Action: move the Elite window to a new position on the same monitor.
Expected pass: `requested` and `applied` update to the moved target, `delta=[0, 0, 0, 0]`, `rect_match=True`, and no wrong-monitor `Overlay moveEvent`.
Expected fail: applied rect remains stale, delta persists outside tolerance, or overlay moves to a different monitor.

3. Windowed resize follows target.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay moveEvent" \
  | grep --line-buffered -E "frame_rect=|requested=|applied=|delta=|rect_match=|reasons=|size="
```
Action: resize the Elite window to a normal non-1440-height windowed size.
Expected pass: `requested` and `applied` follow the new size, `rect_match=True`, and existing degrade reasons stay limited to expected fallback reasons.
Expected fail: repeated `applied_rect_mismatch`, stale size, wrong-monitor move, or new unsupported/degrade reasons.

4. 1440-height frame fallback remains clamped and does not jump monitors.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay moveEvent" \
  | grep --line-buffered -E "monitor_rect=|frame_rect_clamped_to_monitor|requested=|applied=|rect_match=|Overlay moveEvent"
```
Action: reproduce the windowed `<any horizontal>x1440` mode.
Expected pass: `monitor_rect` is non-null; over-tall `frame_rect` is requested as a clamped rect inside the monitor; reasons include `frame_rect_fallback` and `frame_rect_clamped_to_monitor`; `applied` matches the clamped request; no `Overlay moveEvent` to the wrong monitor.
Expected fail: `monitor_rect=None`, unbounded `requested` height, no clamp reason when clamp is needed, or wrong-monitor `Overlay moveEvent`.

5. Focus loss with `keep_overlay_visible=false` suppresses content without hide/remap flash.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay visibility|Backend presentation content|primed Qt map geometry" \
  | grep --line-buffered -E "focus_lost_suppressed|mapped_suppressed|content_visible=False|Overlay visibility set to hidden|remap_warmup|primed Qt map geometry|overlay_window_found"
```
Action: alt-tab or focus away from Elite.
Expected pass: after debounce, log shows `visibility_reason=focus_lost_suppressed`, `surface_action=mapped_suppressed`, `content_visible=False`, `overlay_window_found=True`, and `remap_warmup=inactive`; no `Overlay visibility set to hidden` for soft focus loss.
Expected fail: hide/show loop, remap warm-up during soft focus loss, primed map geometry during soft focus loss, visible flash, or focus steal.

6. Focus return restores content without remap flash.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay visibility|Backend presentation content|primed Qt map geometry" \
  | grep --line-buffered -E "target_focused|mapped_visible|content_visible=True|content restored|Overlay visibility set to visible|remap_warmup|primed Qt map geometry"
```
Action: return focus to Elite from the suppressed state.
Expected pass: `visibility_reason=target_focused`, `surface_action=mapped_visible`, `content_visible=True`, and content restore log appears without remapping or upper-left flash.
Expected fail: remap flash, `Overlay visibility set to visible` from a hidden state, primed map geometry, or overlay window lost/recreated.

7. Click-through works while visible.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Prepared overlay window flags|focus_safe_window|target_focus|click"
```
Action: with overlay visible over Elite, click through an overlay-covered area and confirm Elite receives input.
Expected pass: user-observed click reaches Elite; logs keep `target_focus=True` or recover without hide/remap; focus-safe flags remain applied.
Expected fail: overlay captures input, target focus is lost due to the overlay, or hide/remap occurs.

8. Click-through works while mapped/suppressed.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay visibility|Backend presentation content|primed Qt map geometry" \
  | grep --line-buffered -E "focus_lost_suppressed|mapped_suppressed|content_visible=False|Overlay visibility set to hidden|remap_warmup|primed Qt map geometry"
```
Action: while suppressed, click where overlay content would normally be and confirm no overlay focus/capture behavior.
Expected pass: click does not reveal/capture overlay, no hide/remap/prime lines, and suppressed state remains stable until focus policy changes.
Expected fail: overlay captures input, remaps, flashes, or changes visibility because of the click.

9. Stacking remains above Elite while visible and focused.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation" \
  | grep --line-buffered -E "target_focused|mapped_visible|overlay_window_found=True|rect_match=True|state=|reasons="
```
Action: focus Elite and move/resize enough to confirm overlay remains visually above the game.
Expected pass: user observes overlay above Elite; helper reports `overlay_window_found=True`, `rect_match=True`, and no new stacking/focus-safe degrade reason.
Expected fail: overlay falls behind Elite, disappears while target remains valid, or logs add stacking/focus-safe degrade reasons.

10. Game exit/target loss hard hides or degrades correctly.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay visibility" \
  | grep --line-buffered -E "target_not_found|target_unavailable|target_hidden|visibility=hidden|surface_action=hidden|Overlay visibility set to hidden"
```
Action: exit Elite or otherwise remove the target.
Expected pass: helper target becomes missing/unavailable and runtime hard hides/degrades instead of mapped-suppressing.
Expected fail: overlay remains mapped/visible after real target loss, stale target continues to drive placement, or soft suppression is used for hard target loss.

11. Game relaunch/target reacquire restores correctly.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay visibility|Prepared overlay window flags|primed Qt map geometry" \
  | grep --line-buffered -E "target_found|target_focused|mapped_visible|overlay_window_found=True|rect_match=True|focus_safe_window=applied|primed Qt map geometry"
```
Action: relaunch Elite and focus the game.
Expected pass: new target token is found, focus-safe flags are applied before show, overlay attaches to the target rect, and `rect_match=True` after warm-up.
Expected fail: stale token use, overlay not found indefinitely, wrong-monitor placement, or remap flashing.

12. Confirm `frame_rect_fallback` remains degraded and blocks `true_overlay`.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation" \
  | grep --line-buffered -E "rect_source=|state=|reasons=|frame_rect_fallback|content_rect"
```
Expected pass: while `rect_source=frame_rect_fallback`, presentation remains `presentation_degraded` and reasons include `frame_rect_fallback`; support wording must stay degraded/experimental.
Expected fail: logs or UI claim `true_overlay` while `frame_rect_fallback` or any unresolved degrade reason remains active.

#### Phase 7 Borderless Validation Matrix
Run after Stage 7.1 windowed evidence is recorded.

1. Borderless target discovery and helper health.
Command:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.GetTargetState '{}'
```
Expected pass: target found, fullscreen/borderless state matches the selected mode, target rects are valid, and monitor rect is non-null.

2. Borderless placement aligns to target bounds.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay moveEvent" \
  | grep --line-buffered -E "rect_source=|requested=|applied=|delta=|rect_match=|reasons=|Overlay moveEvent"
```
Expected pass: requested and applied rect match the borderless target bounds, no wrong-monitor move, and no unexpected degrade reasons.

3. Borderless focus loss/return has no flash.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay visibility|Backend presentation content|primed Qt map geometry" \
  | grep --line-buffered -E "focus_lost_suppressed|target_focused|mapped_suppressed|mapped_visible|content_visible|remap_warmup|primed Qt map geometry|Overlay visibility set"
```
Expected pass: same mapped suppression and restore behavior as windowed mode, with no hide/remap flash.

4. Borderless click-through works.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Prepared overlay window flags|focus_safe_window|target_focus"
```
Expected pass: click-through reaches Elite and focus-safe behavior remains stable.

5. Borderless stacking remains correct.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation" \
  | grep --line-buffered -E "overlay_window_found=True|rect_match=True|stacking|focus_safe|reasons="
```
Expected pass: overlay stays visually above Elite while focused, with no stacking/focus-safe degradation.

6. Borderless target loss/reacquire works.
Command:
```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|Overlay visibility" \
  | grep --line-buffered -E "target_not_found|target_found|visibility=hidden|surface_action=hidden|mapped_visible|rect_match=True"
```
Expected pass: hard hide/degrade on target loss and clean reattach on target reacquire.

7. Confirm whether `contentRect` or equivalent alignment proof exists.
Command:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.GetTargetState '{}'
```
Expected pass for `true_overlay` eligibility: target payload exposes valid `contentRect`, or documented equivalent evidence proves content-aligned placement. If `contentRect` remains null and runtime uses `frame_rect_fallback`, support stays degraded/experimental.

#### Phase 7 Support Gate
- Only mark `true_overlay` if all required gates pass:
- helper healthy
- target found
- presentation placement applies
- applied rect matches requested rect
- stacking true
- click-through true
- focus-safe true
- chrome-free true
- no flash
- no wrong-monitor movement
- no unsupported features
- no unresolved degrade reasons
- content alignment proven by `contentRect` or documented equivalent evidence
- If `frame_rect_fallback` remains the rect source, keep status degraded/experimental.
- If a gap is user-approved, record the named gap and residual risk, but still keep support/status wording conservative unless all `true_overlay` gates pass.

| Stage | Description | Status |
| --- | --- | --- |
| 7.1 | Validate windowed move/resize/focus/click-through/stacking/no-flash | In Progress |
| 7.2 | Validate borderless alignment/click-through/stacking/no-flash | Pending Windowed Evidence |
| 7.3 | Validate helper reload, game exit/relaunch, target hidden/workspace changes | Pending Windowed Evidence |
| 7.4 | Review and update status wording only if true-overlay gates pass | Pending Validation Evidence |

### Phase 7 Execution Summary
- Stage 7.1 item 1, windowed target discovery and helper health: Passed on 2026-05-12. `GetHealth` returned `status=healthy`, helper protocol `3`, and the expected helper service/object/interface. `GetTargetState` returned `status=target_found`, `targetToken=meta:20`, title `Elite - Dangerous (CLIENT)`, `monitorRect={"x":0,"y":0,"width":3440,"height":1440}`, `showingOnWorkspace=true`, `minimized=false`, and `fullscreen=false`. `contentRect` remained null and `frameRect` was the active geometry source, so this does not change the degraded/experimental support wording.
- Stage 7.1 item 2, windowed move follows target: Passed on 2026-05-12. While moving the Elite window on the same monitor, runtime logs showed `requested` and `applied` following the target through positions including `{'x': 183, 'y': 313, 'width': 1920, 'height': 837}`, `{'x': 147, 'y': 221, 'width': 1920, 'height': 837}`, `{'x': 292, 'y': 380, 'width': 1920, 'height': 837}`, and final settled `{'x': 312, 'y': 385, 'width': 1920, 'height': 837}`. Each settled sample had `delta=[0, 0, 0, 0]`, `rect_match=True`, `overlay_window_found=True`, and `monitor_rect={'x': 0, 'y': 0, 'width': 3440, 'height': 1440}`. No wrong-monitor `Overlay moveEvent` appeared in the supplied evidence. `rect_source=frame_rect_fallback` and `state=presentation_degraded` remain expected and continue to block `true_overlay`.
- Stage 7.1 item 3, windowed resize follows target: Passed on 2026-05-12. Resizing from `{'x': 312, 'y': 385, 'width': 1920, 'height': 837}` to `{'x': 920, 'y': 246, 'width': 1600, 'height': 937}` produced one expected transient `applied_rect_mismatch` retry, followed by repeated settled samples with `requested={'x': 920, 'y': 246, 'width': 1600, 'height': 937}`, `applied={'x': 920, 'y': 246, 'width': 1600, 'height': 937}`, `delta=[0, 0, 0, 0]`, `rect_match=True`, and `overlay_window_found=True`. Reasons remained limited to expected `frame_rect_fallback`, so support remains degraded/experimental and `true_overlay` remains blocked.
- Stage 7.1 item 4, 1440-height frame fallback clamp: Passed on 2026-05-12. Reproducing the `<any horizontal>x1440` windowed mode produced `monitor_rect={'x': 0, 'y': 0, 'width': 3440, 'height': 1440}` and over-tall `frame_rect={'x': 760, 'y': 29, 'width': 1920, 'height': 1477}`. Runtime requested the clamped rect `{'x': 760, 'y': 29, 'width': 1920, 'height': 1411}` with reasons `['frame_rect_fallback', 'frame_rect_clamped_to_monitor']`; settled samples reported matching `applied={'x': 760, 'y': 29, 'width': 1920, 'height': 1411}`, `delta=[0, 0, 0, 0]`, and `rect_match=True`. No wrong-monitor `Overlay moveEvent` appeared in the supplied evidence.
- Stage 7.1 item 5, focus loss suppresses content without hide/remap flash: Passed on 2026-05-12. With `keep_overlay_visible=false`, focus loss transitioned from `focus_loss_debouncing` to `visibility_reason=focus_lost_suppressed`, `surface_action=mapped_suppressed`, and `content_visible=False` while keeping `visibility=visible`, `overlay_window_found=True`, `rect_match=True`, and `remap_warmup=inactive`. Runtime logged `Backend presentation content suppressed (reason=focus_lost_suppressed)`. No `Overlay visibility set to hidden` or `primed Qt map geometry` appeared in the supplied evidence.
- Stage 7.1 item 6, focus return restores content without remap flash: Passed on 2026-05-12. Returning focus from the suppressed state changed runtime logs to `visibility_reason=target_focused`, `surface_action=mapped_visible`, `content_visible=True`, and `target_focus=True`, with `focus_loss_samples=0`, `focus_loss_elapsed=0.000s`, `remap_warmup=inactive`, `overlay_window_found=True`, and `rect_match=True`. Runtime logged `Backend presentation content restored (reason=target_focused)`. No `Overlay visibility set to visible` from hidden state, no `primed Qt map geometry`, and no remap flash evidence appeared in the supplied logs.
- Stage 7.1 item 7, click-through works while visible: Passed on 2026-05-12. User confirmed Elite received click input through an overlay-covered area while runtime logs showed the overlay visible and attached with `visibility_reason=target_focused`, `surface_action=mapped_visible`, `content_visible=True`, `target_focus=True`, `overlay_window_found=True`, `remap_warmup=inactive`, and matching requested/applied rects. No hide/remap evidence appeared in the supplied logs. `rect_source=frame_rect_fallback` and degraded reasons remain expected and continue to block `true_overlay`.

### Phase 8: Performance Stabilization Addendum
- Reduce GNOME helper-mode CPU/compositor overhead without changing the validated attachment, no-flash, click-through, monitor-clamp, or degraded-support behavior from Phases 4-7.
- Treat this phase as a behavior-preserving performance fix, not a support-status upgrade. `frame_rect_fallback` still blocks `true_overlay`.
- Primary fix area: the backend-owned GNOME helper presentation cycle currently runs every 500 ms, spawns external `gdbus` subprocesses for health/target/presentation, and asks GNOME Shell to move/resize/raise the overlay even when the target rect and presentation state are unchanged.
- Payload logging and high-frequency payload bursts are explicitly out of scope for Phase 8 implementation. They remain a later follow-up after presentation churn is fixed.
- Investigation summary from 2026-05-13:
- Host process sampling showed the load spread across EDMC, the overlay client, and GNOME Shell rather than one obvious pegged process. Representative samples: EDMC `python3` around `8-12%` CPU, overlay client around `3-4%`, and GNOME Shell around `10%`.
- `pidstat -p <edmc>,<overlay>,<gnome-shell> -dur 1 5` showed low IO and no major memory pressure, so the visible slowdown is primarily CPU/event-loop/compositor work.
- Runtime logs showed the GNOME helper presentation loop continuing while the overlay was `mapped_suppressed` with `content_visible=False`.
- `helpers/gnome_shell_extension/extension.js` currently applies `move_resize_frame(...)` and `make_above()` for each `ApplyPresentation` call.
- Payload logs also showed bursty third-party payload activity, but that is deferred so Phase 8 stays focused on compositor-facing presentation churn.
- Risks: throttling the helper loop too aggressively could make move/resize/focus reacquire feel laggy; suppressing redundant presentation too broadly could miss a real target change.
- Mitigations: use explicit signatures and bounded stale windows, keep hard target-loss states fast, add dev-mode diagnostics for skipped presentation work, and validate with the same Phase 7 manual matrix after performance changes.
- Test type selection:
- Unit tests for pure presentation-signature/dedupe decisions, health-cache freshness, jitter behavior, and throttling cadence.
- Harness or mixin tests if follow/setup timer wiring or backend consumer result contracts change.
- Static/source tests for GNOME Shell extension no-op behavior if implemented by source inspection.
- Manual GNOME validation for compositor-visible responsiveness, CPU sampling, move/resize latency, focus loss/return, click-through, and 1440-height monitor clamp.
- `make check` for any code/test changes.
- Phase 8 decisions locked on 2026-05-13:
- Implement presentation churn first; defer payload logging until after presentation churn is fixed.
- The no-op presentation signature must include `targetToken`, selected requested rect after clamp, `monitorRect`, rect source, visibility action, target focus/workspace/minimized/fullscreen flags, overlay identity, and relevant presentation options.
- Superseded for compositor apply decisions on 2026-05-13: the original fresh successful applied presentation window of about `1.0s` while focused/visible and about `2.0s` while mapped-suppressed must not force timed `ApplyPresentation` refreshes. Keep freshness windows only where they are useful for target-poll confidence or other non-compositor work. Actual `ApplyPresentation` should be event-driven after a matching successful apply.
- Cache healthy compatible helper status for about `5s`, with small jitter where practical so repeated clients do not line up health probes.
- Keep suppressed-state polling slower, around `1-2s`, while still detecting focus return and hard target changes promptly.
- Start Shell-side no-op work by skipping redundant `move_resize_frame(...)`; keep `make_above()` unless stacking can be proven cheaply.
- Do not replace `gdbus` subprocesses with a persistent DBus client in this phase. Dedupe, cache, and throttle first.

#### Phase 8 Target Behavior
- Do not call `ApplyPresentation` when the helper target token, selected requested rect, monitor rect, visibility action, focus/workspace/minimized state, overlay identity, and relevant presentation options are unchanged and the last applied presentation was matching. The no-op decision must not expire solely because a short freshness window elapsed.
- Use fresh/stale windows for health checks, target polling confidence, and bounded failure handling, not as a reason to periodically re-enter GNOME Shell presentation for an unchanged successful signature.
- Do not run helper health through `gdbus` on every presentation cycle. Cache healthy compatible helper status for about `5s` with small jitter where practical, while still failing closed on explicit command errors and startup/unavailable states.
- Slow down soft-focus suppressed polling where safe. In `mapped_suppressed` with a valid target and matching last presentation, poll enough to detect focus return and target changes but avoid repeated no-op compositor writes.
- Keep hard states fast: helper unavailable, target missing, target token changes, target minimized/hidden/off-workspace, monitor rect changes, requested rect changes, unsupported presentation, and applied-rect mismatch must bypass no-op suppression and retry through the existing bounded path.
- In the GNOME Shell extension, skip `move_resize_frame(...)` when the overlay frame already matches the requested rect within the existing tolerance, and skip `make_above()` when the helper can prove the overlay is already correctly stacked. If stacking cannot be proven cheaply, prefer keeping the raise but no-op the move/resize first.
- Preserve Phase 6B monitor clamp exactly: over-tall `frame_rect_fallback` still clamps to `monitorRect`, emits `frame_rect_clamped_to_monitor` only when changed, and remains degraded.
- Preserve Phase 6A mapped suppression: focus loss with `keep_overlay_visible=false` suppresses content without unmapping/remapping for soft focus loss.
- Preserve fix219 boundaries: generic follow/runtime code must consume backend-owned presentation interfaces and must not import GNOME helper runtime modules, check raw GNOME backend/helper enums, or reason about helper protocol actions.

#### Deferred Payload/Logging Follow-Up
- Payload logging is not in Phase 8 implementation scope.
- Decisions already agreed for the later payload/logging follow-up:
- Default payload logging should be off in release/non-dev mode.
- Disabled payload logging should gate before expensive serialization.
- Start with diagnostic spam summaries and logging suppression rather than changing valid payload delivery semantics.
- Do not add producer-specific behavior for `BGS-Tally`; treat it as a generic high-frequency payload producer case.
- Keep support diagnostics available through explicit dev/debug settings.

#### Phase 8 Payload Logging Gate Addendum
- Narrow addendum started on 2026-05-13 after the presentation-churn implementation: gate overlay payload body logs behind the EDMC effective log level.
- Locked decisions:
- Payload body logging requires both the existing payload logging preference/debug config and EDMC `DEBUG` logging.
- Dev override alone must not enable payload body logging.
- Existing defaults remain unchanged.
- Scope is only payload body logging and avoiding payload serialization when logs will not emit.
- Out of scope: payload delivery, payload shape, BGS-Tally behavior, spam detection, presentation logs, generic payload dedupe, GNOME helper presentation behavior, and support-status wording.
- Touch point: `load.py` `_PluginRuntime._log_payload`.
- Expected implementation: return before payload serialization unless `_edmc_debug_logging_active()` is true; when EDMC is `DEBUG`, call `_load_payload_debug_config()`, require `_payload_logging_enabled`, keep plugin exclusions before serialization, and preserve the existing emitted log format when logging is allowed.
- Test type selection: unit tests are sufficient because the change is pure logging-gate behavior with injected helper functions and logger handlers. No manual GNOME validation is required because presentation/runtime placement behavior is not touched.
- Targeted tests planned: EDMC non-DEBUG suppresses payload body logs even when diagnostics/dev override is active; EDMC DEBUG plus enabled payload logging emits at DEBUG; non-DEBUG avoids payload serialization; excluded plugin payloads avoid serialization/logging.

| Stage | Description | Status |
| --- | --- | --- |
| 8.1 | Add performance instrumentation and baseline commands for EDMC, overlay client, GNOME Shell, helper cycle counts, skipped cycles, and presentation apply volume | Pre/Post/Off/Latest Baselines Captured |
| 8.2 | Add backend-owned presentation signature/freshness model and tests for safe no-op `ApplyPresentation` suppression | Headless Tests Passed |
| 8.3 | Cache helper health compatibility checks with bounded freshness, jitter, and tests | Headless Tests Passed |
| 8.4 | Add suppressed-state polling/throttling that keeps hard target changes fast and tests the policy | Headless Tests Passed |
| 8.5 | Add GNOME Shell extension no-op guards for unchanged move/resize/raise work | Headless Tests Passed |
| 8.6 | Run targeted presentation performance validation plus Phase 7 regression checks and record before/after evidence | Off Baseline Captured; Manual GNOME Validation Pending |
| 8.7 | Gate payload body logging behind EDMC DEBUG and avoid serialization when logs will not emit | Headless Tests Passed |
| 8.8 | Replace timed fresh-window `ApplyPresentation` refreshes with event-driven apply after a matching successful signature | Headless Tests Passed |
| 8.9 | Remove remaining stable-state target-poll and Shell monitor-lookup pauses | Manual Pause Validation Passed |

#### Phase 8 Implementation Plan
- Touch points started on 2026-05-13: `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py` for backend-owned presentation signature, freshness windows, suppressed-state target polling throttle, and helper health cache; `overlay_client/backend/consumers.py` and `overlay_client/follow_surface.py` only for backend-owned previous visibility-action wiring; `helpers/gnome_shell_extension/extension.js` for the Shell-side unchanged-frame no-op guard.
- Expected unchanged behavior: PyQt rendering remains default; GNOME helper mode remains the target/presentation source of truth; `contentRect` stays preferred; `frame_rect_fallback` remains degraded and still blocks `true_overlay`; Phase 6A mapped suppression and Phase 6B monitor clamp remain intact; generic follow/runtime code continues to consume backend-owned interfaces without GNOME helper imports or helper-protocol checks.
- Test type selection: unit tests for presentation signature equality/inequality, freshness windows, hard-change bypasses, no-op suppression, suppressed polling throttle, and helper health cache freshness/jitter; follow/backend consumer tests only for the backend-owned visibility-action wiring contract; static/source tests for the GNOME Shell extension no-op guard because no JS runtime seam exists in the test suite; manual GNOME validation remains required for CPU/cadence and Phase 7 compositor-visible behavior.
- Targeted test commands planned before `make check`: `python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_gnome_shell_helper_extension_source.py`, plus existing Phase 6A/6B/backend-boundary slices if not covered by the targeted files.

#### Phase 8 Validation Commands
Capture a baseline before coding and repeat after each performance milestone:
```bash
ps -eo pid,ppid,stat,pcpu,pmem,rss,comm,args --sort=-pcpu | head -n 30
```

```bash
pidstat -p <edmc_pid>,<overlay_client_pid>,<gnome_shell_pid> -dur 1 10
```

```bash
tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log \
  | grep --line-buffered -E "GNOME helper presentation|presentation_skipped|ApplyPresentation|mapped_suppressed|target_focused|applied_rect_mismatch|frame_rect_clamped_to_monitor"
```

Expected pass after Phase 8:
- Stable attached/focused windowed mode produces far fewer `ApplyPresentation` calls than the 500 ms timer cadence.
- Stable `mapped_suppressed` focus-loss state does not repeatedly move/resize/raise the overlay.
- Move, resize, focus return, target token changes, game exit/relaunch, and 1440-height monitor clamp still react promptly.
- GNOME Shell and overlay client CPU drop measurably during stable attached and stable suppressed states.
- Phase 7 windowed checks that already passed still pass.

#### Phase 8 Baseline Capture
- Captured on 2026-05-13 at roughly 20:22-20:23 UTC before Phase 8 code changes.
- Command:
```bash
ps -eo pid,ppid,stat,pcpu,pmem,rss,comm,args --sort=-pcpu | head -n 40
```
- Result: top host consumers included Elite Dangerous at `312%` CPU, Firefox RDD at `89.1%`, OneDrive at `59.1%`, Firefox at `18.4%`, GNOME Shell PID `3533` at `9.9%`, EDMC PID `44195` at `9.1%`, and overlay client PID `44230` at `3.6%`. This confirms the desktop is already under heavy load, with overlay-related cost spread across EDMC, overlay client, and GNOME Shell.
- Command:
```bash
pidstat -p 3533,44195,44230 -dur 1 5
```
- Result: five-second clean target average was GNOME Shell `6.40%` CPU, EDMC `7.40%` CPU, and overlay client `3.00%` CPU. RSS was roughly `575414 KB` for GNOME Shell, `215428 KB` for EDMC, and `93396 KB` for the overlay client. Average write IO was low: EDMC `14.40 kB/s`, overlay client `1.60 kB/s`, GNOME Shell `0.00 kB/s`. No major faults or read IO were observed. This supports the CPU/event-loop/compositor-work diagnosis rather than memory pressure or disk IO.
- Command:
```bash
tail -n 120 /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log
```
- Result: recent runtime logs showed stable suppressed presentation work with `visibility_reason=focus_lost_suppressed`, `surface_action=mapped_suppressed`, `content_visible=False`, `target_focus=False`, `rect_match=True`, `attempts=1`, and `retries=[]`. The target was unchanged at `token=meta:27` with `requested` and `applied` both `{'x': 920, 'y': 246, 'width': 1600, 'height': 937}` and `state=presentation_degraded` due to `frame_rect_fallback`.
- Presentation cadence baseline: helper presentation sequence advanced from `seq=3603` at `2026-05-13 20:21:08.988 UTC` to `seq=3786` at `2026-05-13 20:22:40.487 UTC`, which is `183` intervals over about `91.5s`, or roughly `2.0` presentation cycles per second while the overlay was already stably mapped-suppressed and matching. Phase 8 should reduce this steady-state no-op presentation work.

#### Phase 8 Fresh Baseline Capture
- Redone on 2026-05-13 at roughly 21:03-21:08 UTC after the Phase 8 backend implementation was running. Runtime logs showed the Phase 8 backend skip diagnostics active. This sample does not separately prove the GNOME Shell extension no-op guard was reloaded; helper reinstall/reload remains part of manual validation.
- Command:
```bash
ps -eo pid,ppid,stat,pcpu,pmem,rss,comm,args --sort=-pcpu | head -n 40
```
- Result: top host consumers still included Elite Dangerous at `336%` CPU, Firefox RDD at `79.6%`, OneDrive at `55.2%`, Firefox at `17.1%`, GNOME Shell PID `3533` at `9.5%`, EDMC PID `146092` at `9.4%`, and overlay client PID `146118` at `3.2%`. The one-shot `ps` command itself briefly appeared at the top and is ignored as measurement overhead. The desktop is still under heavy non-overlay load, so process-level CPU is noisy.
- Command:
```bash
pidstat -p 3533,146092,146118 -dur 1 10
```
- Result: ten-second average was GNOME Shell `8.70%` CPU, EDMC `7.80%` CPU, and overlay client `2.80%` CPU. RSS was roughly `636674 KB` for GNOME Shell, `213228 KB` for EDMC, and `92180 KB` for the overlay client. Average write IO stayed low: EDMC `14.00 kB/s`, overlay client `2.80 kB/s`, GNOME Shell `0.00 kB/s`, with no major faults. This remains a CPU/event-loop/compositor-work profile, not disk or memory pressure.
- Command:
```bash
perl -ne '
if (/GNOME helper presentation/) {
    $total++;
    $skipped++ if /presentation_skipped=True/;
    $throttle++ if /skip_reason=suppressed_poll_throttle/;
    $fresh++ if /skip_reason=fresh_matching_presentation/;
    $applies++ if /attempts=1/;
    if (!$first) { $first = substr($_, 0, 23); /seq=(\d+)/ and $firstseq = $1; }
    $last = substr($_, 0, 23); /seq=(\d+)/ and $lastseq = $1;
}
END { print "total=$total skipped=$skipped throttle=$throttle fresh=$fresh attempts1=$applies first=$first firstseq=$firstseq last=$last lastseq=$lastseq\n"; }
' /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log
```
- Result for the fresh log window: `total=248 skipped=194 throttle=151 fresh=43 attempts1=54 first=2026-05-13 21:03:11.726 firstseq=177 last=2026-05-13 21:05:14.966 lastseq=273`.
- Interpretation: the runtime still emits a GNOME helper presentation diagnostic about every 500 ms, but most cycles no longer perform presentation work. `194/248` cycles were skipped (`78%`), `151/248` skipped target polling under `suppressed_poll_throttle`, and only `54/248` had `attempts=1`. Across about `123.2s`, target-state sequence advanced by `96`, or roughly `0.78` target polls/sec, and `ApplyPresentation` attempts ran at roughly `0.44`/sec. The pre-Phase 8 steady suppressed baseline was about `2.0` presentation cycles/sec with no no-op suppression, so the compositor/DBus apply volume is substantially lower even though debug log cadence remains unchanged.
- Evidence quality: this validates that backend-owned no-op suppression and suppressed-state polling throttle are active. It does not close Phase 8 manual validation by itself because user-visible responsiveness, move/resize latency, focus return, click-through, 1440-height monitor clamp, and helper-side no-op reload still need manual GNOME confirmation.

#### Phase 8 EDMC/Helper Off Baseline Capture
- Captured on 2026-05-13 at roughly 21:13 UTC after the user uninstalled the GNOME helper and shut down EDMC. This is an environment baseline for comparison against EDMC/overlay-on samples, not a Phase 8 behavior validation.
- Command:
```bash
pgrep -af "EDMarketConnector|overlay_client|org.edmc.ModernOverlay|gnome-shell"
```
- Result: only GNOME Shell/session processes and the VS Code workspace path matched. No `EDMarketConnector.py`, no `overlay_client.overlay_client`, and no `org.edmc.ModernOverlay.Helper` process/service owner appeared in the host process search.
- Command:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.GetHealth
```
- Result: `GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown: The name org.edmc.ModernOverlay.Helper was not provided by any .service files`, confirming the helper DBus service was unavailable.
- Command:
```bash
ps -eo pid,ppid,stat,pcpu,pmem,rss,comm,args --sort=-pcpu | head -n 40
```
- Result: top host consumers still included Elite Dangerous at `337%` CPU, Firefox RDD at `78.9%`, OneDrive at `54.9%`, Firefox at `17.0%`, GNOME Shell PID `3533` at `9.4%`, VS Code-related processes, Steam helpers, and GNOME System Monitor. EDMC and the overlay client were absent from the top process list. The one-shot `ps` command itself briefly appeared at the top and is ignored as measurement overhead.
- Command:
```bash
pidstat -p 3533 -dur 1 10
```
- Result: ten-second GNOME Shell average with EDMC/overlay/helper off was `12.20%` CPU, RSS about `630531 KB`, no read/write IO, and no major faults. The GNOME Shell off-baseline was higher than the immediately prior overlay-on `pidstat` sample (`8.70%`), so the current GNOME Shell CPU is dominated by broader desktop/game activity and short-window sampling noise rather than the overlay alone.
- Interpretation: shutting down EDMC and removing the helper eliminates the overlay client and helper service, but it does not make the desktop idle. Elite, Firefox RDD, OneDrive, GNOME Shell, Steam, and VS Code remain substantial active consumers. Use this as a control point: Phase 8 reduced overlay presentation work, but process-level GNOME Shell CPU is not a reliable single metric while the rest of the desktop load remains this high.

#### Phase 8 Baseline Comparison Table
| Capture | State | Host process snapshot | 10s `pidstat` average | Presentation cadence | Interpretation |
| --- | --- | --- | --- | --- | --- |
| 2026-05-13 ~20:22 UTC | Pre-Phase 8, EDMC/overlay/helper on | Elite `312%`, Firefox RDD `89.1%`, OneDrive `59.1%`, Firefox `18.4%`, GNOME Shell `9.9%`, EDMC `9.1%`, overlay client `3.6%` | GNOME Shell `6.40%`, EDMC `7.40%`, overlay client `3.00%`; low IO | `183` sequence intervals over `91.5s`, about `2.0` presentation cycles/sec while stably mapped-suppressed | Confirms CPU/event-loop/compositor churn with repeated no-op presentation work. |
| 2026-05-13 ~21:03-21:08 UTC | Post Phase 8 presentation changes, EDMC/overlay/helper on | Elite `336%`, Firefox RDD `79.6%`, OneDrive `55.2%`, Firefox `17.1%`, GNOME Shell `9.5%`, EDMC `9.4%`, overlay client `3.2%` | GNOME Shell `8.70%`, EDMC `7.80%`, overlay client `2.80%`; low IO | `248` diagnostics, `194` skipped (`78%`), `54` apply attempts over about `123.2s`; target polls about `0.78`/sec, apply attempts about `0.44`/sec | Backend no-op suppression and suppressed polling throttle are active; process CPU remains noisy under heavy desktop/game load. |
| 2026-05-13 ~21:13 UTC | EDMC shut down, helper uninstalled | EDMC, overlay client, and helper absent; Elite `337%`, Firefox RDD `78.9%`, OneDrive `54.9%`, Firefox `17.0%`, GNOME Shell `9.4%` | GNOME Shell only: `12.20%`; no IO | Not applicable | Control point shows the desktop is not idle without the overlay; GNOME Shell CPU alone is not a clean overlay metric. |
| 2026-05-13 ~21:35 UTC | Latest sample after Phase 8 presentation changes and payload logging gate, EDMC/overlay/helper on | Elite `339%`, Firefox RDD `75.1%`, OneDrive `53.6%`, Firefox `16.6%`, EDMC `12.4%`, GNOME Shell `9.5%`, overlay client `3.6%`; helper health `healthy`, protocol `3` | GNOME Shell `5.20%`, EDMC `9.20%`, overlay client `3.40%`; RSS about `635684 KB`, `213616 KB`, and `91862 KB`; write IO `0.00`, `17.60`, and `2.40 kB/s` respectively | Last `500` log lines: `309` diagnostics over about `154.0s`, `239` skipped (`77%`), `183` suppressed-throttle skips, `56` fresh-matching skips, `70` apply attempts; apply attempts about `0.45`/sec | Current runtime still has reduced apply volume, but timed fresh-window expiry still permits periodic real `ApplyPresentation` calls. User-visible pauses every few seconds make this the next Phase 8 fix. |
| 2026-05-13 ~21:53-21:54 UTC | Post Phase 8.8 event-driven apply, EDMC/overlay/helper on, stable mapped-suppressed | Elite `337%`, Firefox RDD `72.2%`, OneDrive `56.1%`, EDMC `16.5%`, Firefox `16.2%`, GNOME Shell `9.4%`, overlay client `3.9%`; helper health `healthy`, protocol `3` | GNOME Shell `11.30%`, EDMC `8.80%`, overlay client `3.30%`; RSS about `635662 KB`, `215560 KB`, and `92140 KB`; write IO `0.00`, `0.00`, and `2.00 kB/s` respectively | Matching presentation lines after restart: `71` diagnostics over about `35.0s`, `71` skipped (`100%`), `0` apply attempts; diagnostics about `2.0`/sec, apply attempts `0.0`/sec | Phase 8.8 event-driven apply is active: unchanged stable suppressed cycles no longer re-enter `ApplyPresentation`. CPU remains noisy under heavy desktop/game load, and target polling/log cadence remains separate follow-up evidence. |
| 2026-05-13 ~22:13-22:15 UTC | Post Phase 8.9, EDMC/overlay/helper on, stable mapped-suppressed | Elite `326%`, OneDrive `28.0%`, VS Code utility `16.6%`, Firefox `12.1%`, EDMC `11.3%`, GNOME Shell `9.0%`, overlay client `3.4%`; helper health `healthy`, protocol `3`, helper recently restarted | GNOME Shell `9.80%`, EDMC `8.60%`, overlay client `3.20%`; RSS about `449582 KB`, `214556 KB`, and `92200 KB`; write IO `0.00`, `0.00`, and `2.40 kB/s` respectively | Last `200` lines: `200` diagnostics over about `99.5s`, `198` skipped (`99%`), `126` target-poll-throttle skips, `72` fresh-matching skips, `2` apply attempts; direct `GetTargetState` probe: `20/20` calls were `8-10 ms` | Phase 8.9 behavior is present: stable suppressed cycles now skip target polling between bounded polls, and the DisplayConfig `~250 ms` timing spikes are gone in the direct helper probe. |

#### Phase 8 Latest Baseline Capture
- Captured on 2026-05-13 at roughly 21:35 UTC after the Phase 8 presentation-churn implementation and the payload logging DEBUG gate were present in the working tree. EDMC, overlay client, and the GNOME Shell helper were running.
- Initial sandboxed process sampling saw only the sandbox PID namespace and was discarded. The usable host process sampling was rerun outside the sandbox.
- Command:
```bash
pgrep -af "EDMarketConnector|overlay_client|org.edmc.ModernOverlay|gnome-shell"
```
- Result: GNOME Shell PID `3533`, EDMC PID `172685`, and overlay client PID `172721` were running. The helper is hosted inside GNOME Shell rather than a separate process.
- Command:
```bash
gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.GetHealth
```
- Result: helper returned `status=healthy`, `helper_kind=gnome_shell_extension`, `helper_version=1.0.0`, `helper_protocol=3`, and the expected health/target/presentation capabilities.
- Command:
```bash
ps -eo pid,ppid,stat,pcpu,pmem,rss,comm,args --sort=-pcpu | head -n 40
```
- Result: top host consumers included Elite Dangerous at `339%` CPU, Firefox RDD at `75.1%`, OneDrive at `53.6%`, Firefox at `16.6%`, EDMC at `12.4%`, GNOME Shell at `9.5%`, and overlay client at `3.6%`.
- Command:
```bash
pidstat -p 3533,172685,172721 -dur 1 10
```
- Result: ten-second average was GNOME Shell `5.20%` CPU, EDMC `9.20%` CPU, and overlay client `3.40%` CPU. RSS was roughly `635684 KB` for GNOME Shell, `213616 KB` for EDMC, and `91862 KB` for the overlay client. Average write IO stayed low: GNOME Shell `0.00 kB/s`, EDMC `17.60 kB/s`, and overlay client `2.40 kB/s`, with no major faults.
- Command:
```bash
tail -n 500 /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log | perl -ne '
if (/GNOME helper presentation/) {
    $total++;
    $skipped++ if /presentation_skipped=True/;
    $throttle++ if /skip_reason=suppressed_poll_throttle/;
    $fresh++ if /skip_reason=fresh_matching_presentation/;
    $applies++ if /attempts=1/;
    if (!$first) { $first = substr($_, 0, 23); /seq=(\d+)/ and $firstseq = $1; }
    $last = substr($_, 0, 23); /seq=(\d+)/ and $lastseq = $1;
}
END { print "total=$total skipped=$skipped throttle=$throttle fresh=$fresh attempts1=$applies first=$first firstseq=$firstseq last=$last lastseq=$lastseq\n"; }
'
```
- Result: `total=309 skipped=239 throttle=183 fresh=56 attempts1=70 first=2026-05-13 21:33:01.984 firstseq=11 last=2026-05-13 21:35:35.967 lastseq=136`.
- Interpretation: the runtime still emits presentation diagnostics at roughly the existing timer cadence, but `239/309` recent diagnostics were no-op skipped and only `70/309` had `attempts=1`. Across about `154s`, apply attempts ran at about `0.45`/sec, close to the earlier post-Phase 8 sample and far below the pre-Phase 8 steady `2.0` presentation cycles/sec. The payload logging gate is not expected to alter presentation cadence; it reduces payload body logging and serialization cost when EDMC is not at `DEBUG`.

#### Phase 8.8 Event-Driven Apply Baseline Capture
- Captured on 2026-05-13 at roughly 21:53-21:54 UTC after the Phase 8.8 backend change was running. EDMC had restarted since the previous sample. EDMC PID was `193762`, overlay client PID was `193787`, and GNOME Shell PID remained `3533`.
- Command:
```bash
gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.GetHealth
```
- Result: helper returned `status=healthy`, `helper_kind=gnome_shell_extension`, `helper_version=1.0.0`, `helper_protocol=3`, and the expected health/target/presentation capabilities.
- Command:
```bash
ps -eo pid,ppid,stat,pcpu,pmem,rss,comm,args --sort=-pcpu | head -n 40
```
- Result: top host consumers included Elite Dangerous at `337%` CPU, Firefox RDD at `72.2%`, OneDrive at `56.1%`, EDMC at `16.5%`, Firefox at `16.2%`, GNOME Shell at `9.4%`, and overlay client at `3.9%`. The one-shot `ps` command itself briefly appeared near the top and is ignored as measurement overhead.
- Command:
```bash
pidstat -p 3533,193762,193787 -dur 1 10
```
- Result: ten-second average was GNOME Shell `11.30%` CPU, EDMC `8.80%` CPU, and overlay client `3.30%` CPU. RSS was roughly `635662 KB` for GNOME Shell, `215560 KB` for EDMC, and `92140 KB` for the overlay client. Average write IO was GNOME Shell `0.00 kB/s`, EDMC `0.00 kB/s`, and overlay client `2.00 kB/s`, with no major faults.
- Command:
```bash
rg "GNOME helper presentation" /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log | tail -n 500 | perl -ne '
$total++;
$skipped++ if /presentation_skipped=True/;
$throttle++ if /skip_reason=suppressed_poll_throttle/;
$fresh++ if /skip_reason=fresh_matching_presentation/;
$applies++ if /attempts=1/;
if (!$first) { $first = substr($_, 0, 23); /seq=(\d+)/ and $firstseq = $1; }
$last = substr($_, 0, 23); /seq=(\d+)/ and $lastseq = $1;
END { print "total=$total skipped=$skipped throttle=$throttle fresh=$fresh attempts1=$applies first=$first firstseq=$firstseq last=$last lastseq=$lastseq\n"; }
'
```
- Result: `total=71 skipped=71 throttle=0 fresh=71 attempts1=0 first=2026-05-13 21:53:29.475 firstseq=1087 last=2026-05-13 21:54:04.475 lastseq=1157`.
- Interpretation: Phase 8.8 event-driven apply is active. In this stable mapped-suppressed sample, every matching presentation diagnostic skipped compositor apply with `skip_reason=fresh_matching_presentation`, and there were no real `ApplyPresentation` attempts after the successful attach. The diagnostic cadence remains about `2.0`/sec and target polling/log cadence remains separate from compositor apply volume.

#### Phase 8.9 Remaining Pause Evidence
- User reported after Phase 8.8 that the system still pauses about every `2s`; the pause is not perceived as a `500 ms` cadence.
- Live log summary captured on 2026-05-13 after Phase 8.8:
```bash
rg "GNOME helper presentation" /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log | tail -n 200 | perl -ne '...'
```
- Result: `total=200 presentation_skipped=198 target_poll_skipped=0 target_poll_not_skipped=200 throttle=0 fresh=198 attempts1=2 first=2026-05-13 21:54:37.475 firstseq=1223 last=2026-05-13 21:56:16.976 lastseq=1422`.
- Interpretation: Phase 8.8 eliminated most real `ApplyPresentation` calls, but every stable presentation cycle still fetched fresh target state from GNOME Shell. The suppressed-state target-poll throttle is effectively disabled after the old freshness window because `_should_skip_suppressed_target_poll(...)` still depends on `_cached_presentation_is_fresh_and_matching(...)`.
- Direct helper timing probe:
```bash
for i in $(seq 1 20); do
  start=$(date +%s%3N)
  gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.GetTargetState '{}' >/dev/null
  end=$(date +%s%3N)
  printf '%02d %dms\n' "$i" "$((end-start))"
  sleep 0.2
done
```
- Result: most calls were `8-13 ms`, but calls `1`, `5`, `9`, `13`, and `17` took about `228-262 ms`.
- Interpretation: the recurring `~250 ms` stalls match `DISPLAY_CONFIG_DBUS_TIMEOUT_MS = 250` in the GNOME Shell extension. `GetTargetState` enumerates windows and calls `_monitorForIndex(...)`; the hot path currently prefers `_displayConfigMonitorForIndex(...)`, which performs a synchronous `Gio.DBus.session.call_sync(...)` to `org.gnome.Mutter.DisplayConfig.GetCurrentState` when its `1s` monitor cache expires, then falls back to legacy monitor geometry on failure. Running that synchronous DBus call from the Shell extension hot path can block GNOME Shell long enough to be visible as a desktop pause.
- Direct helper health calls were mostly `8-10 ms`, with occasional unrelated spikes, so the health cache is not the primary remaining pause source.
- Phase 8.9 target fix:
- Backend: make stable `mapped_suppressed` target-poll throttle independent of the old presentation freshness window. It should require a previous matching successful presentation, unchanged cached request/target state, and no hard-change signal, but elapsed time beyond the old `2s` presentation freshness window must not force `GetTargetState` on every follow tick.
- Shell helper: remove synchronous DisplayConfig lookup from the hot `GetTargetState` path where legacy monitor geometry is available. Prefer `global.display.get_monitor_geometry(...)`/`get_monitor_scale(...)` for target-state `monitorRect` and use DisplayConfig only as a cold fallback or longer-lived/asynchronous diagnostic source for connector metadata.
- Helper lifecycle script: add a `reload` action to `./scripts/dev_gnome_helper.sh`, not `install_linux.sh`. The development reload action disables/removes/reinstalls/enables the helper and prints status for manual validation. It is documented but must not be executed automatically.
- Expected validation after Phase 8.9: stable suppressed logs should show `target_poll_skipped=True` between bounded target polls, direct `GetTargetState` timing should no longer show recurring `~250 ms` stalls, and user-visible pauses should disappear or be materially reduced.

#### Phase 8.9 Fresh Baseline Capture
- Captured on 2026-05-13 at roughly 22:13-22:15 UTC after the Phase 8.9 backend and Shell helper changes were running. EDMC PID was `225457`, overlay client PID was `225492`, and GNOME Shell PID was `219361`.
- Command:
```bash
pgrep -af "EDMarketConnector|overlay_client|org.edmc.ModernOverlay|gnome-shell"
```
- Result: GNOME Shell, EDMC, and overlay client were running with PIDs `219361`, `225457`, and `225492`.
- Command:
```bash
gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.GetHealth
```
- Result: helper returned `status=healthy`, UUID `edmc-modern-overlay-helper@edmcmodernoverlay.github.io`, helper protocol `3`, and the expected health/target/presentation capabilities. `started_at_unix_ms=1778710231981` showed the helper had recently restarted.
- Command:
```bash
ps -eo pid,ppid,stat,pcpu,pmem,rss,comm,args --sort=-pcpu
```
- Result: top host consumers included Elite Dangerous at `326%` CPU, OneDrive at `28.0%`, VS Code utility process at `16.6%`, Firefox at `12.1%`, EDMC at `11.3%`, GNOME Shell at `9.0%`, and overlay client at `3.4%`. The one-shot `ps` command itself briefly appeared near the top and is ignored as measurement overhead.
- Command:
```bash
pidstat -p 219361,225457,225492 -dur 1 10
```
- Result: ten-second average was GNOME Shell `9.80%` CPU, EDMC `8.60%` CPU, and overlay client `3.20%` CPU. RSS was roughly `449582 KB` for GNOME Shell, `214556 KB` for EDMC, and `92200 KB` for the overlay client. Average write IO was GNOME Shell `0.00 kB/s`, EDMC `0.00 kB/s`, and overlay client `2.40 kB/s`, with no major faults.
- Command:
```bash
rg "GNOME helper presentation" /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log | tail -n 200 | perl -ne '...'
```
- Result: `total=200 skipped=198 target_poll_skipped=126 target_poll_not_skipped=74 throttle=126 fresh=72 attempts1=2 first=2026-05-13 22:13:34.974 firstseq=13 last=2026-05-13 22:15:14.472 lastseq=106`.
- Interpretation: over about `99.5s` of stable `mapped_suppressed` logs, `99%` of diagnostics skipped presentation apply, `126/200` cycles skipped target polling under `suppressed_poll_throttle`, and only `2/200` lines had real `attempts=1`. The log tail overlapped direct helper timing probes, so helper `seq` advancement is not used as a pure runtime target-poll rate here.
- Command:
```bash
for i in $(seq 1 20); do
  start=$(date +%s%3N)
  gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.GetTargetState '{}' >/dev/null
  end=$(date +%s%3N)
  printf '%02d %dms\n' "$i" "$((end-start))"
  sleep 0.2
done
```
- Result: all `20` direct `GetTargetState` calls completed in `8-10 ms` after rerunning outside the sandbox DBus restriction.
- Interpretation: the recurring `~250 ms` DisplayConfig stalls observed before Phase 8.9 did not reproduce after the helper restart. This supports the hot-path monitor-lookup fix.

#### Phase 8.9 Manual Pause Validation
- Recorded on 2026-05-13 after the Phase 8.9 backend and Shell helper changes were running.
- User observation: system performance issues appear to have gone away.
- Result: passed for the Phase 8.9 pause/performance target. The prior user-visible screen pause every few seconds was no longer observed after the stable target-poll throttle fix and the hot-path DisplayConfig avoidance.
- Supporting evidence: the fresh Phase 8.9 baseline showed `198/200` stable presentation diagnostics skipped, `126/200` cycles target-poll-throttled, only `2/200` real `ApplyPresentation` attempts, and direct `GetTargetState` timing at `8-10 ms` for all `20` calls.
- Residual scope: this validates the performance/pause fix only. It does not change support wording, does not claim `true_overlay`, and does not close broader Phase 7/Phase 8 GNOME behavior checks such as move/resize, click-through, focus return, target loss/reacquire, and 1440-height clamp regression rechecks.

#### Phase 8 Pause Evidence And Event-Driven Apply Follow-Up
- User reported on 2026-05-13 that the GNOME helper path still causes screen pauses every few seconds.
- Runtime evidence from recent stable `mapped_suppressed` logs shows that the first Phase 8 no-op suppression works between real applies, but the backend still intentionally re-enters `ApplyPresentation` when the short successful-presentation freshness window expires.
- Representative stable suppressed evidence:
- `2026-05-13 21:36:45.236 UTC`: `attempts=1`, `presentation_skipped=False`, unchanged target `meta:27`, unchanged requested/applied `{'x': 920, 'y': 246, 'width': 1600, 'height': 937}`.
- `2026-05-13 21:36:45.466 UTC` through `21:36:46.473 UTC`: skipped cycles with `skip_reason=suppressed_poll_throttle`.
- `2026-05-13 21:36:47.226 UTC`: skipped with `skip_reason=fresh_matching_presentation`.
- `2026-05-13 21:36:47.488 UTC`: real `attempts=1` apply for the same target and rect.
- The pattern repeats at roughly multi-second intervals, including real applies around `21:36:50.232`, `21:36:51.994`, `21:38:14.490`, `21:38:17.236`, and `21:38:18.985`, while the target signature remains stable and matching.
- Diagnosis: the remaining compositor-visible churn is no longer the original 500 ms apply loop, but the timed freshness expiry still forces periodic `ApplyPresentation` calls into GNOME Shell. That cadence matches the user-visible pauses every few seconds.
- Phase 8.8 decision: after a successful matching `ApplyPresentation`, unchanged target polls should skip presentation indefinitely until a hard-change or failure condition occurs. Freshness windows may still bound target-poll throttling or health-cache behavior, but they must not by themselves force a compositor-facing reapply.
- Required hard-change bypasses remain: helper unavailable/error, target missing, target token changes, requested rect changes, monitor rect changes, visibility action changes, focus/workspace/minimized/fullscreen changes, overlay identity/options changes, unsupported/degraded presentation beyond expected `frame_rect_fallback`, and any previous applied-rect mismatch.
- Implementation touch point for Phase 8.8: `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py` no-op policy and its unit tests in `overlay_client/tests/test_gnome_helper_presentation_runtime.py`.
- Expected test updates for Phase 8.8: remove or rewrite tests that expect focused/suppressed freshness expiry alone to force a new apply; add tests proving unchanged matching signatures continue skipping after the old `1.0s`/`2.0s` windows; keep tests proving real hard changes still bypass the no-op path.
- Implementation touch points started on 2026-05-13: `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py` and `overlay_client/tests/test_gnome_helper_presentation_runtime.py`.
- Test type selection for Phase 8.8: unit tests are required and sufficient for the no-op policy because the behavior is pure/deterministic with injected helper fetchers and clocks. Follow/backend consumer tests are not expected unless result shape or generic runtime wiring changes.
- Helper restart detection note: existing parsed `HelperHealthStatus` exposes compatible version/protocol/capabilities and observed time, but not helper UUID or start timestamp. Phase 8.8 will rely on existing fail-closed cache clearing for helper health failure, protocol incompatibility, version incompatibility, or missing capabilities. Same-version helper restart is not detectable from the current parsed boundary and will remain documented rather than inferred.

#### Phase 8 Execution Summary
- Stage 8.2: Completed for headless coverage. Added backend-owned `GnomeHelperPresentationSignature` and runtime state that suppresses `ApplyPresentation` only when the target token, selected requested rect after clamp, monitor rect, rect source, previous visibility action, target focus/workspace/minimized/fullscreen flags, overlay title/class, renderer, tolerance, required gates, standalone mode, and expected degradation reasons are unchanged. Suppression requires a fresh matching prior presentation and does not apply after applied-rect mismatch, unexpected degradation, unsupported features, stale status, missing target, hidden target, or request changes.
- Stage 8.3: Completed for headless coverage. Healthy compatible helper status is cached for `5.0s` plus bounded jitter up to `0.5s`; explicit unhealthy/error results clear presentation state and fail closed. This does not replace the current `gdbus` transport.
- Stage 8.4: Completed for headless coverage. Stable `mapped_suppressed` state introduced redundant target-poll throttling to about `1.5s`; Phase 8.9 later removed its dependency on the old short presentation freshness window. Focus return, rect changes, monitor changes, target changes, and invalid presentation state still force the normal target/presentation path.
- Stage 8.5: Completed for headless coverage. The GNOME Shell extension now reads the current overlay frame and skips redundant `move_resize_frame(...)` when it already matches the requested rect within `rect_tolerance`. `make_above()` remains in place because stacking proof is not yet cheap or explicit.
- Stage 8.6: Headless regression passed. Manual GNOME performance validation remains pending after helper reinstall/reload and EDMC restart. Support wording remains degraded/experimental; `frame_rect_fallback` still blocks `true_overlay`.
- Stage 8.7: Completed for headless coverage. `_PluginRuntime._log_payload` now requires EDMC `DEBUG` via `_edmc_debug_logging_active()` before payload body logging can emit. The existing payload logging preference/debug config remains an additional enable switch, but dev override alone no longer unlocks payload body logs. Payload and legacy raw serialization now happens only after the EDMC DEBUG gate, payload logging enablement, and plugin-exclusion checks pass. Existing payload delivery, payload shape, spam detection, presentation logs, GNOME helper behavior, BGS-Tally behavior, generic dedupe, and support wording were not changed.
- Stage 8.8: Completed for headless coverage. The backend no-op apply policy now skips `ApplyPresentation` indefinitely for an unchanged signature after a previous matching successful apply; elapsed time beyond the old `1.0s` focused and `2.0s` suppressed windows no longer forces a compositor-facing reapply. Target polling throttle/freshness behavior remains in place for stable `mapped_suppressed` polling, health refresh alone does not cause reapply, and hard signature changes or previous applied-rect mismatch still force apply. Manual GNOME validation remains pending to confirm the every-few-seconds pause is gone or materially reduced.
- Stage 8.9: Completed for headless and manual pause validation. Stable `mapped_suppressed` target-poll throttling now depends on the next target-poll deadline and a previous matching successful presentation, not the old short presentation freshness/stale window. This prevents elapsed time beyond the old `2s` window from forcing `GetTargetState` on every follow tick. The GNOME Shell helper now prefers local legacy monitor geometry before falling back to synchronous DisplayConfig lookup, so the `GetTargetState` hot path should avoid recurring `250 ms` DisplayConfig stalls when GNOME exposes monitor geometry locally. Added and documented `./scripts/dev_gnome_helper.sh reload` for manual helper lifecycle validation; `install_linux.sh` intentionally has no reload action. User reported on 2026-05-13 that the system performance issues appear to have gone away.

#### Tests Run For Phase 8
- Command:
```bash
python3 -m py_compile overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `16 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_setup_surface.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `124 passed`, `4 skipped`. Skips were the existing PyQt-marked setup tests without `PYQT_TESTS=1` in this targeted headless command.
- Command:
```bash
python3 -m py_compile load.py tests/test_logging_and_version_helper.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest tests/test_logging_and_version_helper.py -k log_payload
```
- Result: passed; `4 passed`, `30 deselected`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest tests/test_logging_and_version_helper.py
```
- Result: passed; `34 passed`.
- Command:
```bash
python3 -m py_compile overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/backend/consumers.py overlay_client/follow_surface.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `52 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_setup_surface.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `117 passed`, `4 skipped`. Skips were the existing PyQt-marked setup tests without `PYQT_TESTS=1` in this targeted headless command.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `990 passed`, `21 skipped`.
- Command:
```bash
python3 -m py_compile overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_helper_presentation_runtime.py tests/test_dev_gnome_helper_script.py
```
- Result: passed.
- Command:
```bash
bash -n scripts/dev_gnome_helper.sh scripts/install_linux.sh
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `16 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest tests/test_dev_gnome_helper_script.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_gnome_shell_extension_manifest.py
```
- Result: passed; `22 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_setup_surface.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_dev_gnome_helper_script.py
```
- Result: passed; `135 passed`, `4 skipped`. Skips were the existing PyQt-marked setup tests without `PYQT_TESTS=1` in this targeted headless command.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `991 passed`, `21 skipped`.

#### Phase 8 Remaining Manual GNOME Validation
- Reinstall/reload the GNOME Shell helper extension and restart EDMC so the extension monitor-lookup change and backend cadence changes are both live. Use `./scripts/dev_gnome_helper.sh reload` manually; this command is documented but was not run during headless validation.
- Repeat the Phase 8 validation commands during stable focused/visible and stable `mapped_suppressed` states.
- Expected log evidence: repeated stable cycles should show `presentation_skipped=True` with `skip_reason=fresh_matching_presentation` or `skip_reason=suppressed_poll_throttle`, reduced `attempts=1` apply volume, and unchanged requested/applied rect behavior for moves, resizes, focus return, target loss/reacquire, and 1440-height monitor clamp.
- Phase 8.8-specific evidence: in stable focused and stable `mapped_suppressed` states, unchanged signatures should no longer show periodic real `attempts=1` applies after the old `1.0s`/`2.0s` windows. `target_poll_skipped=True` may still appear during suppressed throttling, and `skip_reason=fresh_matching_presentation` should appear after target polls confirm the unchanged signature.
- Phase 8.9-specific pause validation passed on 2026-05-13: user reported that the system performance issues appear to have gone away. Keep checking for regression during the broader GNOME behavior pass.
- Confirm Phase 7 windowed behavior still holds: no wrong-monitor movement, click-through still works while visible and mapped-suppressed, focus loss/return still has no hide/remap flash, and `frame_rect_fallback` remains degraded.

### Phase 9: GNOME Content Rect And Alignment Proof
- Goal: replace `frame_rect_fallback` as the active GNOME helper-mode rect source only when the helper can provide a valid content-aligned rectangle or a documented equivalent proof that passes the support gate.
- Current blocker: the tested Elite windowed target exposes valid `frameRect` and `bufferRect`, but `contentRect=null` and `decorationInsets=null`. Runtime therefore uses `frame_rect_fallback`, which works operationally but still includes unresolved content/chrome alignment risk.
- Non-goals:
- Do not claim `true_overlay` during diagnostics.
- Do not remove the Phase 6B monitor clamp.
- Do not regress Phase 6A mapped suppression, Phase 8 performance throttling, click-through, stacking, or PyQt rendering.
- Do not hardcode an Elite-specific titlebar height or decoration inset unless repeated evidence proves it is stable and safe for the documented window mode.
- Preserve fix219 boundaries: GNOME geometry discovery and rect-source decisions stay behind backend/helper-owned interfaces. Generic follow/runtime code must not import GNOME helper implementation modules or branch on raw helper protocol details.

#### Phase 9 Target Behavior
- Preferred pass path: helper target payload provides a valid `contentRect`; backend selects `rect_source=content_rect`; presentation applies; `applied` matches `requested`; no unresolved degrade reasons remain.
- Equivalent-proof path: if GNOME cannot expose a direct content rect, a derived or mode-specific content rect may be considered only if all of these are true:
- the derivation is documented and deterministic for the validated mode;
- repeated windowed sizes/positions prove stable decoration/content insets;
- borderless mode proves chrome-free alignment separately;
- move, resize, focus loss/return, click-through, stacking, target loss/reacquire, and monitor clamp checks still pass;
- logs expose enough diagnostics to audit the selected rect source and residual risk.
- Fail/conservative path: if content alignment cannot be proven, keep using `frame_rect_fallback` as degraded/experimental and do not claim `true_overlay`.

#### Phase 9 Proposed Implementation Scope
- Add a helper-side geometry diagnostic payload for target windows. Capture available GNOME/Mutter geometry methods/properties without changing placement behavior first.
- Probe at least:
- `get_frame_rect`
- `get_buffer_rect`
- `get_client_area_rect` availability/result
- any other MetaWindow geometry/client-area/work-area methods discoverable on the runtime object
- monitor geometry/scale and workspace/fullscreen/windowed state
- Compute and log candidate insets between frame, buffer, and any client/content rect candidates.
- Keep diagnostics gated so normal release logs are not flooded.
- If a native content rect exists and is stable, wire it as the preferred helper `contentRect`.
- If no native content rect exists, decide whether a derived rect is acceptable for windowed mode; otherwise leave windowed degraded and consider whether borderless can independently satisfy the equivalent-proof gate.

#### Phase 9 Validation Matrix
1. Windowed geometry diagnostics across multiple positions and sizes.
2. Windowed candidate content rect stability across move/resize.
3. Windowed overlay alignment against visible game content, not titlebar/chrome.
4. 1440-height windowed clamp still prevents wrong-monitor movement.
5. Focus loss/return still has no hide/remap flash.
6. Click-through still works while visible and mapped-suppressed.
7. Stacking still remains above Elite while visible and focused.
8. Game exit/relaunch target loss/reacquire still works.
9. Borderless geometry diagnostics and chrome-free alignment.
10. Borderless move/focus/click-through/stacking/target-loss checks.
11. Support gate review: only remove degraded/experimental wording if `content_rect` or equivalent proof passes every required gate.

#### Phase 9 Locked Decisions Before Implementation
- Diagnostics-first is required for the first patch. Gather helper geometry candidates before changing runtime rect selection.
- Windowed and borderless may land with different support wording. Borderless may be provable before decorated windowed mode.
- If `contentRect` remains unavailable, acceptable equivalent proof requires repeated evidence across positions/sizes, documented deterministic insets or mode-specific alignment rules, and unchanged Phase 7 behavior. A single visual check is not enough.
- A derived content rect must not be enabled by default until the derivation is proven stable and tested. Use diagnostics/dev gating first if needed.
- `frame_rect_fallback` must not be treated as user-approved for `true_overlay` just because it looks good. It can remain usable/degraded, but not `true_overlay`.
- Support wording must not be upgraded as part of the implementation patch. Keep support wording changes as the final Phase 9 gate after manual evidence is recorded.

| Stage | Description | Status |
| --- | --- | --- |
| 9.1 | Add helper-side geometry diagnostics for all available target-window rect candidates without changing runtime placement | Headless Tests Passed |
| 9.2 | Capture windowed geometry evidence across multiple positions, sizes, and the 1440-height case | Partial Evidence Captured |
| 9.3 | Capture borderless geometry evidence and chrome-free alignment evidence | Partial Evidence Captured; Wrong-Monitor Placement Observed |
| 9.4 | Decide whether native `contentRect`, derived rect, borderless-only proof, or continued degraded fallback is supportable | Pending Evidence |
| 9.5 | Implement selected rect-source behavior behind backend/helper-owned interfaces, if evidence supports a change | Pending Decision |
| 9.6 | Add/update unit and static/source tests for geometry candidate parsing, rect-source selection, degradation reasons, and fix219 boundaries | Headless Tests Passed |
| 9.7 | Run Phase 7 regression matrix for the selected rect-source behavior | Pending Implementation |
| 9.8 | Update support/status wording only if all `true_overlay` gates pass; otherwise keep degraded/experimental wording | Pending Validation |
| 9.9A | Addendum: scope persistent borderless wrong-monitor `applied_rect_mismatch` and retry churn | Headless Implementation Complete |
| 9.10 | Implement persistent mismatch visible fail-soft/backoff policy | Headless Tests Passed |
| 9.11 | Add opt-in presentation diagnostics for target/overlay monitor and pre/post rect state | Headless Tests Passed |
| 9.12 | Revalidate borderless placement and decide borderless support wording | Manual Validation Found Same-Monitor Offset Mismatch |
| 9B.1 | Scope proper fix for borderless full-monitor overlay constrained to GNOME work area | Completed |
| 9B.2 | Prove whether Qt-side fullscreen/chrome-free presentation can place the PyQt overlay at full monitor bounds | Manual Validation Failed |
| 9B.3 | Prove whether helper-side fullscreen/full-monitor presentation can bypass work-area clamping while preserving click-through/focus safety | Partial Manual Evidence; Non-Fullscreen Probes Failed |
| 9B.4 | Implement the selected full-monitor presentation path or explicitly keep borderless degraded if no PyQt path can satisfy the gate | Qt Path Rejected; Proper Fix Pending |
| 9B.5 | Add unit/static/harness coverage for selected path, readback mismatch degradation, and fix219 boundaries | Headless Tests Passed |
| 9B.6 | Manually validate borderless full-monitor placement, click-through, no flash, and no presentation churn | Failed For Qt Fullscreen Attempt |

#### Phase 9.1 Implementation Plan
- Touch points:
- `helpers/gnome_shell_extension/extension.js`: emit gated target-window geometry diagnostics in `GetTargetState` payloads without changing placement or `contentRect` selection.
- `overlay_client/backend/helper_ipc.py`: parse and preserve geometry diagnostics on the backend-owned helper target model.
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: expose concise geometry diagnostics in runtime log payloads without letting diagnostics drive placement.
- `overlay_client/follow_surface.py`: log backend-provided geometry diagnostics only when present, without importing GNOME helper modules or branching on helper protocol details.
- Tests: static/source coverage for the GNOME Shell extension diagnostics seam, backend unit tests for parsing and non-placement behavior, follow-surface harness coverage for optional diagnostic logging, and existing GNOME presentation runtime tests for unchanged degraded `frame_rect_fallback` behavior.
- Test type selection: unit tests are required for backend parsing and rect-source behavior because this is pure helper payload validation. Static/source tests are required for the GNOME Shell extension because there is no JS runtime seam in the current test suite. Manual GNOME validation remains pending for Phase 9.2+ evidence capture.

#### Phase 9.1 Implementation Summary
- Implemented on 2026-05-13 as diagnostics-first only. Placement behavior remains unchanged: diagnostic geometry candidates do not drive selected rects, and `frame_rect_fallback` remains degraded and blocks `true_overlay`.
- Helper changes: `GetTargetState` now accepts an opt-in query flag (`include_geometry_diagnostics` / `includeGeometryDiagnostics`) and, only when requested, includes `geometryDiagnostics` on target window payloads. The diagnostic payload records `get_frame_rect`, `get_buffer_rect`, `get_client_area_rect`, `get_work_area_current_monitor`, selected helper content rect, candidate insets, monitor data, and focus/workspace/fullscreen state.
- Follow-up parser hardening: after direct manual probes initially omitted `geometryDiagnostics`, the helper query parser was updated to unwrap single-argument DBus tuple/Variant shapes before parsing the JSON query string. This should allow `gdbus ... GetTargetState '{"include_geometry_diagnostics":true}'` to activate diagnostics after the helper is reloaded.
- Backend/runtime changes: `EDMC_OVERLAY_GNOME_GEOMETRY_DIAGNOSTICS=1` makes the runtime `GetTargetState` query request geometry diagnostics. Backend helper IPC parses and preserves those diagnostics on `HelperTargetWindow`; runtime presentation logs expose them only when present.
- Manual direct probe option:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.GetTargetState \
  '{"include_geometry_diagnostics":true}'
```
- Manual runtime option: launch/restart EDMC or the overlay client with `EDMC_OVERLAY_GNOME_GEOMETRY_DIAGNOSTICS=1`, then capture `GNOME helper presentation` logs. This option is intentionally off by default to avoid normal release log/performance churn.
- Reload guidance: try `./scripts/dev_gnome_helper.sh reload` first. Log out and back in only if reload reports the helper is inactive/not discovered, DBus health does not respond, or the direct diagnostic probe still lacks `geometryDiagnostics` after reload.
- Files changed for Phase 9.1: `helpers/gnome_shell_extension/extension.js`, `overlay_client/backend/helper_ipc.py`, `overlay_client/backend/__init__.py`, `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`, `overlay_client/follow_surface.py`, `overlay_client/tests/test_gnome_shell_helper_target_state.py`, `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, `overlay_client/tests/test_gnome_shell_helper_extension_source.py`, and `overlay_client/tests/test_follow_surface_mixin.py`.

#### Tests Run For Phase 9.1
- Command:
```bash
python3 -m py_compile overlay_client/backend/helper_ipc.py overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/follow_surface.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_follow_surface_mixin.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `26 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `4 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_surface_mixin.py
```
- Result: passed; `14 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_consumers.py
```
- Result: passed; `66 passed`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `995 passed`, `21 skipped`.

#### Phase 9.2 Windowed Evidence
- Partial windowed evidence captured on 2026-05-13 after logout/login caused GNOME Shell to load the updated helper code.
- Windowed normal sample:
- `frameRect={"x":499,"y":210,"width":1920,"height":837}`
- `bufferRect={"x":485,"y":198,"width":1948,"height":866}`
- `contentRect=null`; `decorationInsets=null`.
- `geometryDiagnostics.candidates.client_area`: unavailable and invalid.
- `geometryDiagnostics.candidates.selected_content`: unavailable and invalid.
- `geometryDiagnostics.insets.frame_to_buffer`: `{"left":-14,"top":-12,"right":-14,"bottom":-17}`.
- Windowed moved sample:
- `frameRect={"x":56,"y":139,"width":1920,"height":837}`
- `bufferRect={"x":42,"y":127,"width":1948,"height":866}`
- `contentRect=null`; `decorationInsets=null`.
- `geometryDiagnostics.candidates.client_area`: unavailable and invalid.
- `geometryDiagnostics.candidates.selected_content`: unavailable and invalid.
- `geometryDiagnostics.insets.frame_to_buffer`: `{"left":-14,"top":-12,"right":-14,"bottom":-17}`.
- Windowed resized sample:
- `frameRect={"x":696,"y":120,"width":2048,"height":1189}`
- `bufferRect={"x":682,"y":108,"width":2076,"height":1218}`
- `contentRect=null`; `decorationInsets=null`.
- `geometryDiagnostics.candidates.client_area`: unavailable and invalid.
- `geometryDiagnostics.candidates.selected_content`: unavailable and invalid.
- `geometryDiagnostics.insets.frame_to_buffer`: `{"left":-14,"top":-12,"right":-14,"bottom":-17}`.
- Windowed 1440-height sample:
- `frameRect={"x":760,"y":29,"width":1920,"height":1477}`
- `bufferRect={"x":746,"y":17,"width":1948,"height":1506}`
- `contentRect=null`
- `decorationInsets=null`
- `monitorRect={"x":0,"y":0,"width":3440,"height":1440}`
- `geometryDiagnostics.candidates.frame`: available and valid; matches `frameRect`.
- `geometryDiagnostics.candidates.buffer`: available and valid; matches `bufferRect`.
- `geometryDiagnostics.candidates.client_area`: unavailable and invalid; `get_client_area_rect` is not available for this target in this GNOME/Mutter path.
- `geometryDiagnostics.candidates.work_area_current_monitor`: available and valid; returned `{"x":0,"y":29,"width":3440,"height":1411}`. This is monitor work-area geometry, not target content geometry.
- `geometryDiagnostics.candidates.selected_content`: unavailable and invalid because the helper still has no valid content rect candidate.
- `geometryDiagnostics.insets.frame_to_buffer`: `{"left":-14,"top":-12,"right":-14,"bottom":-17}`. Negative insets confirm `bufferRect` is larger than `frameRect` and is not a content rect.
- Interpretation: these samples confirm the diagnostics path is live and show stable GNOME/Mutter geometry availability across windowed normal, moved, resized, and 1440-height states. No native `contentRect`, client-area rect, selected-content rect, or decoration inset is available. The stable frame-to-buffer delta is diagnostic only because `bufferRect` is larger than `frameRect`; it does not identify Elite's content area.
- Result: windowed mode remains on degraded `frame_rect_fallback`; the evidence does not support a `true_overlay` claim and does not justify switching runtime placement away from `frame_rect_fallback`.
- Evidence still needed for Phase 9.2/9.3: focus loss/return confirmation with diagnostics live, borderless presentation logs for the wrong-monitor placement, and any repeated samples needed to prove whether borderless has a native or equivalent chrome-free content-alignment signal.

#### Phase 9.3 Borderless Evidence
- Partial borderless evidence captured on 2026-05-13.
- User observation: in windowed-borderless mode, the overlay is visible on the second monitor, not over Elite. This fails the wrong-monitor gate even though the helper target payload reports monitor `0`.
- Borderless normal sample:
- `frameRect={"x":0,"y":0,"width":3440,"height":1440}`
- `bufferRect={"x":0,"y":0,"width":3440,"height":1440}`
- `contentRect={"x":0,"y":0,"width":3440,"height":1440}`
- `decorationInsets={"left":0,"top":0,"right":0,"bottom":0}`
- `monitorRect={"x":0,"y":0,"width":3440,"height":1440}`
- `fullscreen=true`; `showingOnWorkspace=true`; `minimized=false`.
- `geometryDiagnostics.candidates.frame`: available and valid; matches `frameRect`.
- `geometryDiagnostics.candidates.buffer`: available and valid; matches `bufferRect`.
- `geometryDiagnostics.candidates.client_area`: unavailable and invalid.
- `geometryDiagnostics.candidates.selected_content`: available and valid; matches `contentRect`.
- `geometryDiagnostics.insets.frame_to_buffer`: `{"left":0,"top":0,"right":0,"bottom":0}`.
- `geometryDiagnostics.insets.frame_to_selected_content`: `{"left":0,"top":0,"right":0,"bottom":0}`.
- Interpretation: borderless mode exposes a native chrome-free `contentRect` and selected-content candidate matching the monitor-sized frame/buffer rect. This is promising for borderless content alignment, but current visible placement is wrong-monitor, so borderless cannot pass Phase 9 or `true_overlay` gates until runtime presentation logs explain and fix the monitor placement failure.
- Borderless runtime presentation evidence:
- Target payload stayed on `target_monitor=0` with `monitor_rect={"x":0,"y":0,"width":3440,"height":1440}` and `rect_source=content_rect`.
- Runtime requested `{"x":0,"y":0,"width":3440,"height":1440}` from the native `contentRect`.
- Helper readback consistently returned `applied={"x":3440,"y":0,"width":3440,"height":1440}`.
- `delta=[3440,0,0,0]`, `rect_match=False`, `state=presentation_degraded`, `reasons=["applied_rect_mismatch"]`, and `attempts=2`.
- The same applied-rect mismatch persisted in both `mapped_suppressed` and `mapped_visible` / `target_focused` states.
- Interpretation: backend rect selection is not choosing the second monitor; it requests the monitor-0 content rect. GNOME/Mutter or the overlay window placement path moves or leaves the PyQt overlay one monitor width to the right. Because every presentation attempt mismatches, Phase 8 no-op suppression cannot engage in this state and the runtime retries presentation every cycle.
- Result: borderless has a valid content rect but fails the wrong-monitor and applied-rect-match gates. The next implementation decision must treat persistent applied-rect mismatch as both a placement bug and a churn hazard.

#### Phase 9.9A Addendum: Borderless Wrong-Monitor Mismatch
- Problem statement: borderless mode now proves a native chrome-free `contentRect`, but `ApplyPresentation` cannot currently attach the PyQt overlay to the same monitor. The backend requests the target's monitor-0 rect, while helper readback reports the overlay at `x=3440`, one 3440-wide monitor to the right. This fails the wrong-monitor and applied-rect-match gates.
- Performance risk: every cycle reports `applied_rect_mismatch`, so the Phase 8 event-driven no-op cache never becomes eligible. Borderless mode can therefore reintroduce repeated compositor-facing presentation attempts even after the Phase 8 churn fixes.
- Goal: keep the overlay visible while backing off safely when the same presentation signature repeatedly produces the same wrong-monitor applied rect, while gathering enough opt-in diagnostics to identify whether Mutter/fullscreen policy, overlay-window identity, or coordinate-space handling is responsible.
- Non-goals:
- Do not claim `true_overlay`.
- Do not enable borderless as supported until wrong-monitor placement is fixed or explicitly marked unsupported.
- Do not move rendering into the GNOME Shell extension.
- Do not change windowed `frame_rect_fallback` behavior.
- Do not undo Phase 8 event-driven presentation suppression.
- Locked decisions:
- Visible fail-soft is required: keep the overlay mapped/visible according to the current focus/content visibility policy; do not hide/unmap solely because borderless placement mismatches.
- Use a threshold of `2` consecutive identical wrong-monitor `applied_rect_mismatch` results before treating the mismatch as persistent.
- After the threshold, retry only on hard changes: target token, target rect/monitor, visibility action, focus/workspace/fullscreen state, helper restart, overlay identity, or mode switch.
- Do not add a slow timed recovery retry in the first implementation.
- Add concise degradation reasons for both `wrong_monitor_applied_rect` and `persistent_applied_rect_mismatch`.
- Preserve current mapped-visible/mapped-suppressed content behavior. If `keep_overlay_visible=false` and Elite is unfocused, content should remain suppressed as it does today.
- Add opt-in diagnostics for overlay pre/post frame rect, buffer rect, monitor, selected overlay token/title/class, requested rect, target monitor, and whether `move_resize_frame` was called.
- Gate detailed diagnostics behind an environment/dev diagnostic flag, off by default. Normal logs should show only concise reasons and skip/backoff state.
- Do not update support wording or claim `true_overlay`; borderless has `contentRect`, but wrong-monitor placement still fails the gate.
- Phase 9.9A implementation touch points:
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: add backend-owned persistent wrong-monitor mismatch tracking, visible fail-soft backoff, concise log fields, and opt-in presentation diagnostics request wiring.
- `overlay_client/backend/helper_ipc.py`: add request/response fields for opt-in presentation diagnostics and preserve the helper response payload behind backend-owned types.
- `helpers/gnome_shell_extension/extension.js`: add opt-in `ApplyPresentation` diagnostics for selected overlay identity, pre/post rects, monitor state, target monitor, requested rect, and move/resize action.
- `overlay_client/tests/test_gnome_helper_presentation_runtime.py`: add unit coverage for mismatch threshold, backoff skip, hard-change resets, current visibility policy preservation, same-monitor mismatch classification, and success clearing.
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`: add static/source coverage for the gated helper presentation diagnostics seam.
- Test type selection: unit tests are required for the backend mismatch detector because it is deterministic state logic. Static/source tests are required for the GNOME Shell helper diagnostics because there is no JS runtime seam. Existing runtime tests continue to cover Phase 8 no-op suppression and Phase 6A/6B behavior where represented in the backend harness.
- Recommended implementation scope:
1. Add a backend-owned persistent mismatch detector keyed by presentation signature, requested rect, applied rect, and target token.
2. After a small threshold of identical mismatches, stop immediate `ApplyPresentation` retries for that unchanged signature.
3. Use visible fail-soft behavior for wrong-monitor mismatches: keep the overlay mapped and preserve the normal content visibility policy, but mark presentation degraded and suppress immediate re-apply churn for the unchanged bad signature. Re-attempt only when a hard-change occurs, such as target token change, target rect/monitor change, visibility action change, focus/workspace/fullscreen change, helper restart, overlay identity change, or an explicit bounded retry interval if a retry is selected.
4. Add a clear reason such as `persistent_applied_rect_mismatch` and preserve the original `applied_rect_mismatch` evidence in diagnostics.
5. Add opt-in presentation diagnostics around `ApplyPresentation`, gated behind an environment/dev diagnostic flag, capturing target token/state, requested rect, target monitor/rect, selected overlay token/title/class, overlay pre/post frame and buffer rects, overlay monitor before/after, and whether the helper called `move_resize_frame` or skipped it.
6. Keep normal logs concise. Detailed presentation diagnostics must not emit by default.
- Test type selection:
- Unit tests for backend persistent mismatch state, threshold behavior, hard-change reset conditions, and visible fail-soft/backoff result shape.
- Unit tests for parser/model support if presentation diagnostics are added to helper response payloads.
- Static/source tests for GNOME Shell extension diagnostic fields and gated emission because no JS runtime seam exists.
- Existing GNOME helper presentation runtime tests must continue to prove Phase 8 no-op suppression still works after successful matching applies.
- Manual validation required after implementation:
- Borderless with Elite fullscreen/borderless on monitor 0: confirm repeated wrong-monitor applies stop after the threshold while the overlay remains visible according to the current focus/content visibility policy.
- Switch back to windowed mode: confirm normal Phase 7 windowed behavior still works and the mismatch cache clears on signature change.
- Borderless focus loss/return: confirm no renewed infinite retry loop.
- Capture one diagnostic sample with opt-in presentation diagnostics enabled to identify overlay pre/post monitor and rect state.
- Support decision after validation: if wrong-monitor mismatch persists, borderless must remain degraded/unsupported for true-overlay purposes despite having a valid `contentRect`. If diagnostics reveal a safe same-monitor attach fix, implement that fix in a later Phase 9 stage before revisiting support wording.

#### Phase 9.9A Implementation Summary
- Implemented on 2026-05-13 as visible fail-soft/backoff only. Support wording remains unchanged and `true_overlay` is not claimed.
- Backend runtime now tracks repeated wrong-monitor `applied_rect_mismatch` results by presentation signature, target token, requested rect, and applied rect. After `2` identical wrong-monitor mismatches, unchanged signatures skip immediate `ApplyPresentation` with `presentation_skip_reason=persistent_applied_rect_mismatch`.
- The overlay remains mapped/visible according to the existing focus/content policy. In `mapped_suppressed`, content suppression remains unchanged when `keep_overlay_visible=false`.
- Runtime diagnostics now add concise fields for `persistent_mismatch_count` and `persistent_mismatch_backoff`, and persistent failures include `wrong_monitor_applied_rect` plus `persistent_applied_rect_mismatch`.
- Hard changes bypass the backoff and re-attempt presentation: target token, rect, monitor rect, focus/workspace/fullscreen, visibility action, overlay/request options, and diagnostic-request mode changes.
- Helper IPC now supports an opt-in `include_presentation_diagnostics` request flag and preserves optional `presentation_diagnostics` response payloads behind backend-owned types.
- GNOME Shell helper `ApplyPresentation` can now return opt-in presentation diagnostics with selected overlay identity, target monitor/rect, requested rect, overlay pre/post frame and buffer rects, overlay monitor before/after, and `moveResizeAction`.
- Detailed presentation diagnostics remain off by default. Enable with `EDMC_OVERLAY_GNOME_PRESENTATION_DIAGNOSTICS=1` when launching EDMC/overlay client or when issuing direct helper requests that include `include_presentation_diagnostics`.
- Files changed for Phase 9.9A: `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`, `overlay_client/backend/helper_ipc.py`, `helpers/gnome_shell_extension/extension.js`, `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, `overlay_client/tests/test_gnome_shell_helper_extension_source.py`, and this document.

#### Tests Run For Phase 9.9A
- Command:
```bash
python3 -m py_compile overlay_client/backend/helper_ipc.py overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `29 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `6 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py
```
- Result: passed; `110 passed`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1009 passed`, `21 skipped`.
- Command:
```bash
git diff --check
```
- Result: passed.

#### Phase 9.9A Manual Validation Pending
- Reload helper with `./scripts/dev_gnome_helper.sh reload` because `helpers/gnome_shell_extension/extension.js` changed.
- Restart EDMC/overlay client.
- Enter Elite windowed-borderless mode.
- Confirm the overlay remains visible.
- Confirm repeated `attempts=2` stops after persistent mismatch threshold for the unchanged signature.
- Confirm logs show `wrong_monitor_applied_rect`, `persistent_applied_rect_mismatch`, and `presentation_skip_reason=persistent_applied_rect_mismatch`.
- Confirm focus loss/return does not restart an infinite retry loop.
- Switch back to windowed mode and confirm Phase 7 windowed behavior still works.
- Optional diagnostic run: launch with `EDMC_OVERLAY_GNOME_PRESENTATION_DIAGNOSTICS=1`, capture one presentation sample, and inspect overlay pre/post monitor and rect state.

#### Phase 9.12 Manual Validation Evidence
- Partial manual validation captured on 2026-05-13.
- User could not reproduce the click-through or idle flashing during the supplied capture.
- Borderless placement changed from the earlier wrong-monitor `x=3440` applied rect to a same-monitor top-offset mismatch:
- `requested={"x":0,"y":0,"width":3440,"height":1440}`
- `applied={"x":0,"y":29,"width":3440,"height":1440}`
- `delta=[0,29,0,0]`, `rect_match=False`, `state=presentation_degraded`, `reasons=["applied_rect_mismatch"]`, `attempts=2`.
- The mismatch repeated every cycle in both `mapped_suppressed` and `mapped_visible` / `target_focused` states. No `presentation_skipped=True` or `persistent_applied_rect_mismatch` backoff appeared.
- Interpretation: Phase 9.9A's wrong-monitor-specific detector did not trigger because the applied rect overlaps the target monitor. The remaining churn is a stable same-monitor `applied_rect_mismatch`, likely caused by Mutter constraining the overlay below the top panel/work-area boundary at `y=29` while the borderless target reports full-monitor content at `y=0`.
- Result: wrong-monitor placement appears improved in this run, but borderless still fails the applied-rect-match gate and can still retry `ApplyPresentation` every cycle. Phase 9B now owns the proper fix for the `work_area_top_offset_applied_rect` case; broadening mismatch backoff alone is not the desired solution.

#### Phase 9B Addendum: Borderless Full-Monitor Work-Area Constraint Fix
- Goal: implement the correct borderless/full-monitor attachment path for GNOME helper mode so a PyQt-rendered overlay can attach to a fullscreen borderless Elite target at the target monitor bounds instead of being constrained to the GNOME work area. This is a proper placement fix, not another retry/backoff band-aid.
- Diagnostic evidence captured on 2026-05-13:
- `GetTargetState` for borderless Elite returned `contentRect={"x":0,"y":0,"width":3440,"height":1440}`, matching `frameRect`, `bufferRect`, and `selected_content`.
- The same target reported `work_area_current_monitor={"x":0,"y":29,"width":3440,"height":1411}`.
- Direct `ApplyPresentation` with `include_presentation_diagnostics=true` requested `{"x":0,"y":0,"width":3440,"height":1440}` for target token `meta:18`.
- The helper selected overlay token `meta:25`, reported `chrome_free=true`, `stacking=true`, `click_through=true`, `focus_safe=true`, and called `move_resize_frame`.
- Presentation diagnostics showed the overlay before rect was already `{"x":0,"y":29,"width":3440,"height":1440}` and after rect remained `{"x":0,"y":29,"width":3440,"height":1440}`.
- Interpretation: the offset is not caused by a titlebar or missing chrome-free flags. Mutter appears to constrain the managed PyQt overlay to the work area below the GNOME top panel even when the target is fullscreen and the helper requests full monitor bounds.
- Secondary diagnostic correctness issue: the helper returned `status="presentation_applied"` with no degrade reasons even though post-apply readback did not match the requested rect. The backend currently catches the mismatch, but helper-side presentation status should also degrade on readback mismatch.
- Non-goals:
- Do not solve this with a broader persistent mismatch backoff alone. Backoff may remain a churn guard, but it is not the Phase 9B fix.
- Do not claim `true_overlay` or upgrade support wording until borderless readback matches requested bounds and Phase 7/8 behavior remains valid.
- Do not move rendering into GNOME Shell in the first implementation patch.
- Do not change windowed `frame_rect_fallback` behavior.
- Do not regress Phase 6A mapped suppression, Phase 6B monitor clamp, Phase 8 event-driven suppression, or Phase 9.9A visible fail-soft behavior.
- Preserve fix219 boundaries: GNOME-specific placement strategy stays behind backend/helper-owned interfaces under `overlay_client/backend/`; generic follow/runtime code must not import helper implementations or branch on raw helper protocol details.
- Locked decisions accepted on 2026-05-13:
- Try Qt-side fullscreen/chrome-free presentation first for borderless/fullscreen targets. PyQt owns the overlay window; the helper remains responsible for target truth, stacking, click-through, focus-safe proof, and readback validation.
- Keep Phase 9B borderless/fullscreen-only. Do not change windowed `frame_rect_fallback`.
- Activate only when the helper target reports `fullscreen=true` and a valid `contentRect` matching monitor bounds.
- Start behind a dev/runtime gate first. Promote to default only after manual GNOME validation proves placement, click-through, focus safety, no flashing, and no presentation churn.
- Keep visible fail-soft behavior on failure. If fullscreen presentation fails or readback remains offset, keep the overlay visible under current mapped-visible/mapped-suppressed policy, mark presentation degraded, and avoid retry churn.
- Correct helper-side readback semantics: helper `ApplyPresentation` should degrade when the post-apply rect does not match the requested rect, even if `move_resize_frame` returned successfully.
- Keep Phase 9.9A as a churn guard only. Do not expand backoff as the primary Phase 9B fix.
- Preserve helper protocol compatibility where possible by adding only optional request/response fields.
- If Qt-side fullscreen cannot satisfy the gate, test helper-side fullscreen/full-monitor APIs next. If neither path preserves `chrome_free`, `click_through`, `focus_safe`, and matching readback, keep borderless degraded and scope a larger alternate-surface approach separately.
- Candidate fix paths to evaluate in order:
1. Qt-side fullscreen presentation for borderless targets: have the PyQt overlay enter a true fullscreen/chrome-free state on the target `QScreen` before helper stacking/click-through validation. Verify this changes Shell readback to `y=0` and preserves click-through/focus safety.
2. Helper-side fullscreen/full-monitor presentation: if Mutter exposes a safe `MetaWindow` API for fullscreening the overlay window from the extension, prototype it behind an opt-in diagnostic path, then verify readback, stacking, click-through, and focus safety.
3. If a managed PyQt top-level cannot bypass work-area clamping while preserving click-through, keep borderless degraded and scope a larger alternate-surface approach separately, such as a layer-shell-capable surface or Shell-rendered overlay. This is not part of the first Phase 9B implementation.
- Phase 9B touch points:
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: select and request any new borderless/full-monitor presentation mode behind backend-owned policy; preserve current degraded behavior unless the selected path proves readback match.
- `overlay_client/backend/helper_ipc.py`: add request/response fields only if the selected helper protocol needs an explicit fullscreen/full-monitor presentation option.
- `helpers/gnome_shell_extension/extension.js`: add helper-side fullscreen/full-monitor presentation only if the helper API path is selected; also degrade helper presentation responses when post-apply readback mismatches requested rect.
- `overlay_client/follow_surface.py` or the backend consumer seam: add Qt-side fullscreen/chrome-free overlay presentation only if needed, without importing GNOME helper implementation modules or dispatching on raw helper enums in generic code.
- Tests: unit tests for backend policy/readback mismatch handling, static/source tests for helper readback degradation and optional fullscreen diagnostics, harness tests if Qt window flag/fullscreen wiring changes, and manual GNOME validation for compositor placement.
- Phase 9B.2 implementation plan:
- Add a backend-owned, generic surface-preparation request type used by the GNOME helper presentation bundle and consumed by `follow_surface.py` through `run_backend_presentation_cycle(..., prepare_surface=...)`.
- Gate the first implementation behind `EDMC_OVERLAY_GNOME_BORDERLESS_FULLSCREEN_PREP=1`.
- Keep eligibility pure and narrow: request action must be attach, target must be fullscreen, target `contentRect` must be valid, `contentRect` must match `monitorRect` within the existing presentation tolerance, and runtime must still use `rect_source=content_rect`.
- In `follow_surface.py`, implement a backend-neutral preparation handler that makes the PyQt surface chrome-free/click-through-safe, selects the target `QScreen` from the requested full-monitor rect, primes the geometry, and calls `showFullScreen()` before helper validation.
- Preserve existing map-prime/show behavior for non-9B paths and windowed `frame_rect_fallback`.
- In `helpers/gnome_shell_extension/extension.js`, add helper-side degradation for post-apply readback mismatch so direct `ApplyPresentation` no longer reports `presentation_applied` when `applied_rect` differs from `requested_rect`.
- Test type selection for Phase 9B.2:
- Unit tests are required for backend fullscreen-prep eligibility because this is deterministic policy logic.
- Harness/follow-surface tests are required because Qt surface preparation reaches `follow_surface.py` and changes window state calls.
- Static/source tests are required for the GNOME Shell extension readback mismatch degradation because there is no JS runtime seam.
- Manual GNOME validation remains pending for Phase 9B.6.
- Test type selection:
- Unit tests are required for backend selection policy, degraded state mapping, and helper IPC parsing because these are deterministic.
- Static/source tests are required for GNOME Shell extension behavior if no JS runtime seam exists.
- Harness tests are required if Phase 9B changes PyQt window flags, fullscreen state, or backend-to-surface wiring.
- Manual GNOME validation is required because work-area clamping, fullscreen behavior, click-through, focus safety, and visual flashing are compositor behavior.
- Manual validation requirements after implementation:
- Reload helper with `./scripts/dev_gnome_helper.sh reload` if helper files change.
- Restart EDMC/overlay client.
- Enter Elite windowed-borderless mode on monitor 0.
- Confirm helper target still reports `contentRect={"x":0,"y":0,"width":3440,"height":1440}` or the current monitor-equivalent bounds.
- Confirm runtime/helper presentation applies with `requested` and `applied` matching at `y=0`, not `y=29`.
- Confirm `chrome_free=true`, `stacking=true`, `click_through=true`, and `focus_safe=true`.
- Confirm no repeated `attempts=2` or periodic `ApplyPresentation` churn returns after a successful matching attach.
- Confirm click-through, focus loss/return, no flashing, and target loss/reacquire behavior still match Phase 7/8 expectations.
- Confirm windowed mode still uses degraded `frame_rect_fallback` and remains operational.

#### Phase 9B Implementation Summary
- Implemented on 2026-05-13 as a dev-gated Qt-side fullscreen preparation path. Support wording remains degraded/experimental, and `true_overlay` is not claimed.
- Added backend-owned surface preparation request plumbing through `BackendPresentationSurfacePreparation`. The GNOME helper presentation bundle creates this request only when `EDMC_OVERLAY_GNOME_BORDERLESS_FULLSCREEN_PREP=1`, the helper target is fullscreen, the request action is attach, `rect_source=content_rect`, and the target content rect matches the target monitor rect within the existing presentation tolerance.
- `follow_surface.py` now accepts the backend-owned preparation callback from `run_backend_presentation_cycle`. For `fullscreen_monitor` preparation, it prepares click-through/focus-safe window flags, selects the target `QScreen` from the requested full-monitor rect, primes geometry, calls `showFullScreen()`, prepares the platform window, and reapplies click-through before helper `ApplyPresentation` validates stacking/readback/click-through/focus safety.
- The GNOME Shell helper now adds `applied_rect_mismatch` to `degrade_reasons` when post-apply readback does not match the requested rect within tolerance. Direct helper calls should no longer report `presentation_applied` for the known `y=29` work-area mismatch.
- The Phase 9.9A persistent mismatch guard remains a guard, not the primary fix. With the 9B fullscreen-prep gate enabled, repeated same-signature applied-rect mismatches back off after the existing threshold so a failed Qt-side fullscreen attempt does not reintroduce immediate `ApplyPresentation` churn.
- Files changed for Phase 9B: `overlay_client/backend/surface_preparation.py`, `overlay_client/backend/__init__.py`, `overlay_client/backend/consumers.py`, `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`, `overlay_client/follow_surface.py`, `helpers/gnome_shell_extension/extension.js`, `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, `overlay_client/tests/test_backend_consumers.py`, `overlay_client/tests/test_follow_surface_mixin.py`, `overlay_client/tests/test_gnome_shell_helper_extension_source.py`, and this document.
- Test files added/updated for Phase 9B: `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, `overlay_client/tests/test_backend_consumers.py`, `overlay_client/tests/test_follow_surface_mixin.py`, and `overlay_client/tests/test_gnome_shell_helper_extension_source.py`.

#### Tests Run For Phase 9B
- Command:
```bash
python3 -m py_compile overlay_client/backend/surface_preparation.py overlay_client/backend/__init__.py overlay_client/backend/consumers.py overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/follow_surface.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `89 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_setup_surface.py
```
- Result: passed; `114 passed`, `4 skipped`. The skips were existing PyQt-marked setup tests in the targeted command without `PYQT_TESTS=1`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1022 passed`, `21 skipped`.

#### Phase 9B Manual Validation Evidence
- Validation date: 2026-05-13.
- Qt-side fullscreen prep was tested with `EDMC_OVERLAY_GNOME_BORDERLESS_FULLSCREEN_PREP=1`.
- Result: failed. The overlay became completely black and opaque. This rejects the Qt `showFullScreen()` preparation path even though it was dev-gated, because it breaks the transparent PyQt compositing surface.
- The original no-flag startup command was retested:
```bash
source /home/jon/Applications/EDMC/EDMarketConnector-6.1.2/venv/bin/activate && python3 /home/jon/Applications/EDMC/EDMarketConnector-6.1.2/EDMarketConnector.py
```
- Result: the overlay returned to the second-monitor placement failure, but with no title bar. This confirms the titlebar/chrome hypothesis is not the root cause. The overlay can be chrome-free while Mutter still places the managed PyQt top-level on the wrong output or constrains it away from the requested full-monitor rect.
- Conclusion: keep the Qt-side fullscreen prep gate off by default and do not promote it. Phase 9B.3 should now scope a helper/compositor-side full-monitor placement path or an alternate surface strategy. Phase 9.9A remains only a churn guard; broader backoff is still not the proper fix.

#### Phase 9B.3 Scope: Helper-Side Full-Monitor Presentation Proof
- Goal: prove whether the GNOME Shell helper can place the existing transparent PyQt overlay at borderless/full-monitor target bounds using Shell/Mutter-side window APIs, without Qt `showFullScreen()` and without changing rendering ownership.
- Status: scoped on 2026-05-13. This is a diagnostic/proof stage. Do not promote support wording, do not claim `true_overlay`, and do not make helper-side fullscreen behavior default in this stage.
- Core question: can a managed PyQt top-level remain transparent/click-through/focus-safe while Shell/Mutter places it at the fullscreen target monitor rect, or is a normal managed PyQt window fundamentally constrained to work-area/monitor-placement behavior under GNOME Wayland?
- In-scope hypotheses to test:
- `move_to_monitor(target_monitor)` before `move_resize_frame(...)` may correct the second-monitor placement case without changing fullscreen state.
- `move_resize_frame(...)` followed by `move_to_monitor(...)`, or the reverse order, may have different Mutter behavior and should be proven with readback.
- Shell-side fullscreen APIs such as `make_fullscreen()` / `unmake_fullscreen()`, if available on the overlay `MetaWindow`, may bypass work-area clamping. This must be tested for transparency, click-through, focus safety, and readback, because Qt-side fullscreen already failed visually.
- Overlay workspace/state APIs such as `change_workspace(...)`, `move_to_workspace(...)`, `stick(...)`, or equivalent methods may be needed only if diagnostics show workspace or monitor migration is part of the failure.
- It may be impossible for a managed PyQt top-level to occupy full-monitor bounds under GNOME Wayland while preserving transparency. If so, Phase 9B should explicitly keep borderless degraded and scope a later alternate-surface path.
- Out of scope:
- No Qt `showFullScreen()` retry or promotion.
- No broader mismatch backoff as the primary fix.
- No Shell-rendered overlay implementation in 9B.3.
- No payload logging, BGS-Tally, generic payload dedupe, windowed `frame_rect_fallback`, support wording, or `true_overlay` changes.
- No direct GNOME helper runtime imports or helper protocol checks in `follow_surface.py`; preserve the fix219 boundary.
- Proposed helper diagnostics:
- Add an opt-in `ApplyPresentation` diagnostic/probe option, off by default, for helper-side placement strategies.
- Report which overlay `MetaWindow` methods exist before attempting them: at minimum `move_to_monitor`, `move_resize_frame`, `move_frame`, `make_fullscreen`, `unmake_fullscreen`, `make_above`, workspace movement/stick methods, fullscreen state fields, monitor index, frame rect, buffer rect, and work area.
- For each attempted strategy, capture pre/post frame rect, buffer rect, monitor, fullscreen state, workspace, requested rect, target monitor rect, action order, and any thrown error.
- Keep diagnostics optional and concise in normal runtime logs; large strategy payloads should appear only when explicitly requested.
- Candidate strategy probes, in order:
1. `normal_move_resize`: current control path, to keep evidence comparable.
2. `move_to_monitor_then_resize`: move overlay to target monitor, then call `move_resize_frame(...)`.
3. `resize_then_move_to_monitor`: call `move_resize_frame(...)`, then move overlay to target monitor.
4. `make_fullscreen_then_resize`: call helper-side fullscreen on the overlay, then resize/read back.
5. `resize_then_make_fullscreen`: resize first, then call helper-side fullscreen/read back.
6. `fullscreen_only`: helper-side fullscreen without explicit resize, to see Mutter's native fullscreen rect for the selected overlay.
- Strategy safety requirements:
- All strategy probes must be opt-in and limited to borderless/fullscreen targets where helper target state has `fullscreen=true`, valid `contentRect`, and `contentRect` matching `monitorRect`.
- If a probe leaves the overlay fullscreen or moved unexpectedly and the strategy is not selected as a success, the helper should attempt best-effort restoration to the pre-probe state or document why restoration is not safe.
- A successful strategy must prove all of: applied rect matches requested full-monitor rect within tolerance, overlay remains visually transparent, no black/opaque surface appears, `chrome_free=true`, `stacking=true`, `click_through=true`, `focus_safe=true`, no repeated `ApplyPresentation` churn, and Phase 6A/6B/8 behavior remains intact.
- Failure handling:
- If every managed-window strategy fails, mark Phase 9B.3 as failed and keep borderless degraded. The next phase should scope an alternate surface architecture, such as a real layer-shell surface or a Shell-side rendering bridge, instead of continuing to tune managed PyQt top-level placement.
- Phase 9B.3 touch points:
- `helpers/gnome_shell_extension/extension.js`: add opt-in strategy probing and diagnostics around overlay `MetaWindow` placement methods.
- `overlay_client/backend/helper_ipc.py`: parse optional strategy diagnostics only if the helper response shape changes.
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: add backend-owned request options and diagnostic surfacing only behind an explicit development gate.
- Tests: static/source tests for helper strategy gates and diagnostic fields; unit tests for backend option eligibility/parser handling if touched; backend-boundary tests if any runtime wiring changes.
- Phase 9B.3 implementation status:
- Marked in progress on 2026-05-13.
- Intended touch points for this implementation: `helpers/gnome_shell_extension/extension.js`, `overlay_client/tests/test_gnome_shell_helper_extension_source.py`, and this document. Backend parser/runtime files should remain untouched unless the helper response needs structured runtime parsing beyond optional JSON passthrough.
- Test type selection for this implementation:
- Static/source tests are required for the GNOME Shell extension strategy probe because there is no JS runtime seam in the current test suite.
- Backend parser/unit tests are not required if the new strategy diagnostics remain nested under the existing optional `presentation_diagnostics` response payload and are not parsed into typed backend models.
- Harness tests are not required because normal runtime wiring and PyQt window state should not change in this diagnostic-only patch.
- Manual GNOME validation remains required before any strategy can be selected for Phase 9B.4.
- Manual validation plan:
- Reload helper with `./scripts/dev_gnome_helper.sh reload`.
- Start EDMC without `EDMC_OVERLAY_GNOME_BORDERLESS_FULLSCREEN_PREP=1`.
- Enter Elite windowed-borderless mode on monitor 0 and confirm target `contentRect` equals `monitorRect`.
- Run direct `ApplyPresentation` strategy probes with diagnostics enabled for each candidate strategy.
- For each probe, record requested/applied rect, overlay monitor, fullscreen state, `chrome_free`, `stacking`, `click_through`, `focus_safe`, visual transparency, click-through, focus loss/return, and whether any flashing or black/opaque surface occurs.
- Only after a strategy passes manually should Phase 9B.4 implement it as the selected path, still behind a dev/runtime gate first.

#### Phase 9B.3 Implementation Summary
- Implemented on 2026-05-13 as an opt-in helper-side strategy probe. Normal `ApplyPresentation` behavior is unchanged unless a request explicitly sets `presentation_strategy_probe` / `presentationStrategyProbe` or `include_presentation_strategy_diagnostics` / `includePresentationStrategyDiagnostics`.
- The helper now supports diagnostic probes for `normal_move_resize`, `move_to_monitor_then_resize`, `resize_then_move_to_monitor`, `make_fullscreen_then_resize`, `resize_then_make_fullscreen`, and `fullscreen_only`.
- Probes are gated to borderless/fullscreen target state: target `fullscreen=true`, valid `contentRect`, valid `monitorRect`, target `contentRect` matching `monitorRect`, and requested rect matching `monitorRect` within the existing tolerance. If the gate fails, diagnostics explain why and no strategy actions run.
- Per-strategy diagnostics are nested under existing `presentation_diagnostics.strategyProbe`; backend parser/runtime behavior is unchanged and diagnostics do not drive placement.
- Strategy diagnostics record method availability, target monitor/content rect, requested rect, pre/post overlay frame/buffer rect, monitor, fullscreen state, workspace, action order, errors, readback match, monitor/fullscreen changes, and best-effort restoration after fullscreen probes.
- Helper-side fullscreen probes attempt `unmake_fullscreen()` and a move/resize back to the pre-probe frame when the overlay was not fullscreen before the probe.
- Files changed for Phase 9B.3: `helpers/gnome_shell_extension/extension.js`, `overlay_client/tests/test_gnome_shell_helper_extension_source.py`, and this document.
- Test files added/updated for Phase 9B.3: `overlay_client/tests/test_gnome_shell_helper_extension_source.py`.

#### Tests Run For Phase 9B.3
- Command:
```bash
python3 -m py_compile overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `13 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `53 passed`.
- Command:
```bash
git diff --check
```
- Result: passed.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1028 passed`, `21 skipped`.

#### Phase 9B.3 Manual Validation Pending
- Reload helper with `./scripts/dev_gnome_helper.sh reload` because `helpers/gnome_shell_extension/extension.js` changed.
- Start EDMC without `EDMC_OVERLAY_GNOME_BORDERLESS_FULLSCREEN_PREP=1`.
- Enter Elite windowed-borderless mode on monitor 0.
- Confirm target reports `fullscreen=true` and `contentRect == monitorRect`.
- Run one direct `ApplyPresentation` call per candidate strategy with `presentation_strategy_probe` set to the strategy name and `include_presentation_diagnostics=true`.
- For each strategy, capture requested rect, applied rect, overlay monitor, overlay fullscreen state, method availability, match result, restoration result, visual transparency, click-through, focus loss/return, and flashing/opaque-black behavior.
- Keep Phase 9B.4 pending until manual evidence proves whether any helper-side strategy can satisfy all placement and behavior gates.

#### Phase 9B.3 Manual Validation Evidence
- Validation date: 2026-05-14.
- Current borderless target: `targetToken=meta:19`, `fullscreen=true`, `contentRect={"x":0,"y":0,"width":3440,"height":1440}`, `monitorRect={"x":0,"y":0,"width":3440,"height":1440}`, `work_area_current_monitor={"x":0,"y":29,"width":3440,"height":1411}`.
- Baseline strategy probe `normal_move_resize`:
- Returned `status="presentation_degraded"`, `degrade_reasons=["applied_rect_mismatch"]`.
- Requested `{"x":0,"y":0,"width":3440,"height":1440}`; applied/readback `{"x":0,"y":29,"width":3440,"height":1440}`.
- `strategyProbe.eligible=true`, `actions=[move_resize_frame ok]`, `rectMatch=false`, `monitorChanged=false`, `fullscreenChanged=false`.
- `chrome_free=true`, `stacking=true`, `click_through=true`, and `focus_safe=true` were reported by the helper, but the user visually observed a title bar on the overlay while it was on the primary monitor and in front.
- Strategy probe `move_to_monitor_then_resize`:
- Returned `status="presentation_degraded"`, `degrade_reasons=["applied_rect_mismatch"]`.
- Requested `{"x":0,"y":0,"width":3440,"height":1440}`; applied/readback remained `{"x":0,"y":29,"width":3440,"height":1440}`.
- `strategyProbe.eligible=true`, `actions=[move_to_monitor ok, move_resize_frame ok]`, `rectMatch=false`, `monitorChanged=false`, `fullscreenChanged=false`.
- User observations: overlay remained on the primary monitor and in front; it behaved like a standalone app and had a visible title bar on the primary monitor; click-through could flash; when the game/overlay moved to the secondary monitor the title bar disappeared, but clicking through sometimes moved the overlay behind the game and it did not return to foreground.
- Follow-on normal non-strategy diagnostic confirmed the same state: helper selected overlay token `meta:30`, `moveResizeAction="move_resize_frame"`, before/after rects both `{"x":0,"y":29,"width":3440,"height":1440}`, monitor `0`, and `degrade_reasons=["applied_rect_mismatch"]`.
- Runtime logs during this state showed repeated `GNOME helper presentation` attempts with `attempts=2`, `retries=["applied_rect_mismatch"]`, `presentation_skipped=false`, `rect_match=false`, and `delta=[0,29,0,0]`. Because the mismatch is same-monitor/work-area rather than wrong-monitor, Phase 9.9A's wrong-monitor backoff does not engage.
- Interpretation: `move_to_monitor` does not address the work-area top offset. Helper `chrome_free=true` is not sufficient proof of the user-visible no-titlebar/no-normal-managed-window behavior in this GNOME Wayland/XWayland path. Do not promote a non-fullscreen helper-side move strategy. Fullscreen probes remain unvalidated and potentially risky because Qt-side fullscreen already produced a black/opaque surface.

### Phase 10: GNOME Shell-Native Borderless/Fullscreen Small Proof
- Goal: prove the smallest possible GNOME Shell-owned presentation surface can satisfy the borderless/fullscreen compositor gates that a normal managed PyQt top-level cannot satisfy under GNOME Wayland.
- Current conclusion from Phase 9B evidence: the managed PyQt top-level path is not the correct borderless/fullscreen architecture. Mutter constrains or treats the PyQt overlay as a managed application window: normal helper moves can leave it at work-area `y=29` or on the wrong monitor, and Qt-side fullscreen can become black/opaque. Keep that evidence, but do not keep tuning managed-window placement as the primary fix.
- Phase 10 is proof-only. It must not implement payload rendering, production scene transport, runtime automatic selection, support wording changes, or `true_overlay` claims.
- Preserve existing behavior:
- PyQt rendering remains the default path for windowed mode, non-GNOME behavior, and all production runtime behavior during this phase.
- Windowed GNOME helper mode remains operational through the existing backend/helper presentation path, with `frame_rect_fallback` degraded.
- Phase 6A mapped suppression, Phase 6B clamp, Phase 8 event-driven suppression, Phase 9.9A churn guard, and Phase 9B evidence remain intact.
- Preserve fix219 boundaries: GNOME Shell-native proof policy must stay behind backend/helper-owned interfaces. Generic follow/runtime code must not import GNOME helper implementation modules or branch on raw helper protocol details.

#### Phase 10 Small Proof Scope
- Build a transparent GNOME Shell/St/Clutter actor, owned by the extension, positioned at the target `contentRect`/monitor rect above Elite in borderless fullscreen mode.
- The proof actor should render only a hardcoded diagnostic label/box or minimal overlay marker. It does not need payload rendering, layout parity, live scene updates, or user-facing production UI.
- The proof actor must be opt-in/dev-gated and off by default.
- Proposed dev gate name for the first proof: `EDMC_OVERLAY_GNOME_SHELL_ACTOR_PROOF=1` or an equivalent helper/backend proof flag. The exact name can change during implementation, but the gate must be off by default.
- The proof actor must be borderless/fullscreen-only:
- target `fullscreen=true`;
- target has a valid `contentRect`;
- `contentRect` matches the target monitor bounds within existing tolerance;
- target is on the current workspace and not minimized.
- The proof actor must not steal focus and should not receive pointer input. Manual validation must confirm click-through to Elite still works.
- The proof actor should be destroyed or hidden promptly on target loss, workspace mismatch, minimized target, helper disable, or dev gate disable.

#### Phase 10 Locked Decisions
- Trigger: expose a direct manual/helper proof path first. Do not add automatic runtime selection in Phase 10.
- Actor content: use a simple visible diagnostic marker, such as a small label plus outline rectangle. It does not need to resemble the production overlay.
- Eligibility: use strict borderless/fullscreen gating only. Refuse the proof unless the target is fullscreen, has a valid `contentRect`, and that `contentRect` matches the target monitor bounds within tolerance.
- Click-through: the proof actor must be non-reactive/click-through. If it blocks clicks, Phase 10 fails rather than deferring that to a later production phase.
- Layer/parent probing: start with one Shell actor parent/layer candidate at a time and record the chosen parent/layer in diagnostics. Do not automatically cycle multiple parent candidates in the first implementation.
- Cleanup: remove the actor on explicit clear, target loss, helper disable/reload, and stale proof timeout.
- Stale timeout: use about `5s` for the proof actor unless it is refreshed by an explicit proof/update request.
- Runtime impact: do not suppress PyQt content, do not alter normal EDMC overlay behavior, and do not implement payload rendering or production scene transport in Phase 10.
- Pass/fail bar: Phase 10 passes only if the proof actor satisfies the full acceptance gate below. A partial pass is evidence, not permission to start Phase 11.
- Follow-up gate: Phase 11 starts only after Phase 10 passes. If Phase 10 fails, record the failed gate and scope another GNOME-native proof option before content-bridge work.

#### Phase 10 Refactor Staging
| Stage | Description | Status |
| --- | --- | --- |
| 10.1 | Scope Shell-native small-proof goals, boundaries, non-goals, and test type selection | Completed |
| 10.2 | Add a dev-gated Shell-native proof actor in the GNOME Shell extension without changing normal runtime placement | Headless Tests Passed |
| 10.3 | Add direct helper command/request fields to show, update, and clear the proof actor without automatic runtime selection | Headless Tests Passed |
| 10.4 | Add static/source and parser/unit coverage for the proof actor gate, lifecycle, response fields, and fix219 boundaries | Headless Tests Passed |
| 10.5 | Manually validate the proof actor in borderless fullscreen: full-monitor geometry, no `y=29` offset, no titlebar, transparency, click-through, focus safety, no flashing, no presentation churn, monitor/workspace behavior, and target loss/reacquire | Active-Fullscreen Proof Passed; Production Lifecycle Hardening Deferred |
| 10.6 | Try single fullscreen-aware Shell actor parent/layer candidates after `Main.uiGroup` failed the active-fullscreen visibility gate | `trackFullscreen=true` Failed; `trackFullscreen=false` Failed; `global.stage` Failed; `global.top_window_group` Failed |
| 10.7 | Add proof-only Shell/Mutter group diagnostics to report available global actor groups and child/order metadata before choosing another candidate | Headless Tests Passed; Manual Diagnostics Pending |
| 10.8 | Refine proof-only Shell/Mutter diagnostics with `uiGroup` ordering, `global.window_group` MetaWindowActor details, visible proof actor sibling metadata, and optional target-token matching | Headless Tests Passed; Manual Diagnostics Pending |
| 10.9 | Try the single evidence-based `global.window_group` proof parent so the Shell proof actor is appended after current window actors | `global.window_group` Failed |
| 10.10 | Try the single `target_window_actor_child` proof parent by attaching the proof actor directly to the Elite fullscreen MetaWindowActor | Manual Validation Passed |
| 10.11 | Record Phase 10 decision: Shell actor proof passed and Phase 11 may start, or proof failed and alternate GNOME-native options must be scoped | Completed; Phase 11 Unblocked |

#### Phase 10 Implementation Plan
- Implementation status: started on 2026-05-14.
- Intended touch points:
- `helpers/gnome_shell_extension/extension.js`: add direct opt-in `shell_actor_proof` handling, strict borderless/fullscreen eligibility, Shell actor creation/positioning, diagnostics, explicit clear, stale timeout cleanup, and disable cleanup.
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`: add source/static tests for proof opt-in behavior, eligibility, actor non-reactive/click-through setup, parent/layer diagnostics, stale timeout, explicit clear, cleanup paths, and preservation of normal `ApplyPresentation`.
- This document: record implementation plan, files changed, commands, and outcomes.
- Backend/runtime files are intentionally out of scope for the first implementation unless helper response parsing forces a typed Python model. No automatic runtime selection should be added in Phase 10.
- Test type selection:
- Static/source tests are required for the GNOME Shell extension proof actor because there is no JS runtime seam in the current headless suite.
- Unit/parser tests are not required unless backend helper IPC parsing changes.
- Harness tests are not required because the proof is direct helper-triggered and should not change follow-surface lifecycle or backend consumer contracts.
- Manual GNOME validation remains required for compositor behavior and keeps Phase 10.5 pending.

#### Phase 10 Follow-Up Implementation Plan
- Implementation status: implemented on 2026-05-15 after manual validation showed the first `Main.uiGroup` candidate can draw at full-monitor bounds but does not stay above active fullscreen Elite.
- Intended touch points:
- `helpers/gnome_shell_extension/extension.js`: replace the proof actor's single parent/layer candidate with `Main.layoutManager.addChrome(...)` using fullscreen tracking and an input-region-neutral configuration. Preserve the direct proof command, eligibility gate, stale timeout, and normal managed PyQt `ApplyPresentation` path.
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`: update static/source assertions for the new single parent/layer candidate, cleanup through Shell layout manager tracking, and click-through-oriented chrome options.
- This document: record follow-up scope, files changed, commands, outcomes, and manual validation requirements.
- Test type selection:
- Static/source tests remain sufficient because this patch only changes GNOME Shell extension proof actor source and there is no JS runtime seam in the headless suite.
- Unit/parser tests are not required because the helper IPC shape is unchanged.
- Harness/backend-boundary tests are not required unless backend/follow wiring changes. This follow-up should not touch backend/follow wiring.
- Manual GNOME validation remains required to prove active-fullscreen stacking, click-through, transparency, no taskbar/Alt-Tab Shell actor entry, stale cleanup, and no flashing.

#### Phase 10 Second Follow-Up Implementation Plan
- Implementation status: implemented on 2026-05-15 after manual validation showed `Main.layoutManager.addChrome(trackFullscreen=true,affectsInputRegion=false)` loaded correctly and reported full-monitor actor bounds, but the marker still stayed with the VS Code/normal-window layer rather than active fullscreen Elite.
- Intended touch points:
- `helpers/gnome_shell_extension/extension.js`: keep the same layout-manager chrome candidate and direct proof command, but switch the single candidate option from `trackFullscreen=true` to `trackFullscreen=false` while preserving `affectsInputRegion=false`.
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`: update static/source assertions for the current single candidate.
- This document: record the failed `trackFullscreen=true` evidence, the new candidate, and test/manual validation requirements.
- Test type selection:
- Static/source tests remain sufficient because the helper IPC shape and backend/follow wiring are unchanged.
- Manual GNOME validation remains required because only the compositor can prove active-fullscreen stacking.

#### Phase 10 Third Follow-Up Implementation Plan
- Implementation status: implemented on 2026-05-15 after manual validation showed both layout-manager chrome candidates had correct full-monitor actor bounds but still stayed with the VS Code/normal-window layer instead of active fullscreen Elite.
- Intended touch points:
- `helpers/gnome_shell_extension/extension.js`: replace the single proof parent/layer candidate with `global.stage`, a lower-level Shell scene graph candidate. Preserve the same direct proof request fields, strict eligibility gate, marker styling, stale timeout, explicit clear, and normal managed PyQt `ApplyPresentation` path.
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`: update static/source assertions for the new single candidate and cleanup path.
- This document: record failed candidate evidence, current `global.stage` candidate, files changed, commands, outcomes, and manual validation requirements.
- Test type selection:
- Static/source tests remain sufficient because this patch changes only GNOME Shell extension proof actor source and does not change helper IPC shape.
- Backend/parser tests are not required unless response shape changes.
- Harness tests are not required because runtime wiring must remain unchanged.
- Manual GNOME validation remains required because only the compositor can prove active-fullscreen stacking.

#### Phase 10 Fourth Follow-Up Implementation Plan
- Implementation status: implemented on 2026-05-15 after manual validation showed `global.stage` loaded correctly and reported full-monitor actor bounds, but still stayed with the VS Code/normal-window layer instead of active fullscreen Elite.
- Intended touch points:
- `helpers/gnome_shell_extension/extension.js`: replace the single proof parent/layer candidate with `global.top_window_group`, a Mutter/Shell top-window group candidate. Preserve the same direct proof request fields, strict eligibility gate, marker styling, stale timeout, explicit clear, and normal managed PyQt `ApplyPresentation` path.
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`: update static/source assertions for the new single candidate and unchanged cleanup path.
- This document: record failed candidate evidence, current `global.top_window_group` candidate, files changed, commands, outcomes, and manual validation requirements.
- Test type selection:
- Static/source tests remain sufficient because this patch changes only GNOME Shell extension proof actor source and does not change helper IPC shape.
- Backend/parser tests are not required unless response shape changes.
- Harness tests are not required because runtime wiring must remain unchanged.
- Manual GNOME validation remains required because only the compositor can prove active-fullscreen stacking.

#### Phase 10 Group Diagnostics Implementation Plan
- Implementation status: implemented on 2026-05-15 after `Main.uiGroup`, both layout-manager chrome variants, `global.stage`, and `global.top_window_group` all placed a transparent actor at full-monitor bounds but failed active-fullscreen stacking. Manual GNOME diagnostics are pending.
- Goal: add a proof-only helper command that reports available global GNOME Shell/Mutter actor groups and concise child/order metadata so the next single parent/layer candidate is chosen from evidence rather than guessed.
- Intended touch points:
- `helpers/gnome_shell_extension/extension.js`: add an opt-in `shell_actor_proof_action="diagnose_groups"` path under the existing Shell actor proof command family. It must not create, move, or destroy proof actors and must not change normal `ApplyPresentation`.
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`: add static/source assertions that group diagnostics are opt-in, include known global group names, include child/order metadata, are bounded, and do not auto-cycle candidates.
- This document: record diagnostics scope, files changed, commands, outcomes, and manual command.
- Test type selection:
- Static/source tests are required because there is no JS runtime seam for the GNOME Shell extension in the headless suite.
- Backend/parser tests are not required because the helper IPC shape remains JSON with optional diagnostics fields and no backend parser is touched.
- Harness tests are not required because runtime wiring remains unchanged.
- Manual GNOME validation remains required to inspect the returned group metadata from the actual compositor session.
- Locked boundaries:
- Do not add runtime selection, auto-cycling, payload rendering, PyQt suppression, support wording changes, or `true_overlay` claims.
- Do not touch `follow_surface.py` or backend/follow wiring.
- Keep `show` and `clear` proof behavior unchanged.

#### Phase 10 Group Diagnostics Follow-Up Implementation Plan
- Implementation status: implemented on 2026-05-15 after the first `diagnose_groups` response showed that `global.stage` only exposes `UiActor:uiGroup` and `UIAreaIndicator`, while the ordering needed for fullscreen analysis is inside `uiGroup`. Manual diagnostics with a fresh target token are pending.
- Goal: keep the same proof-only diagnostics command but add enough bounded scene-graph detail to identify the active fullscreen target window actor, the proof actor's sibling position if visible, and the relevant `uiGroup` ordering before choosing another single proof parent.
- Intended touch points:
- `helpers/gnome_shell_extension/extension.js`: enrich `shell_actor_proof_action="diagnose_groups"` with `uiGroup` child order, `global.window_group` child MetaWindowActor details, optional `target_token` matching, and visible proof actor metadata. Do not create/move/destroy actors and do not change normal `ApplyPresentation`.
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`: extend static/source assertions for bounded `uiGroup` diagnostics, window actor metadata fields, target-token matching, and proof actor sibling metadata.
- This document: record scope, commands, outcomes, and the manual diagnostics command.
- Test type selection:
- Static/source tests remain required because there is no JS runtime seam for the GNOME Shell extension.
- Backend/parser tests remain unnecessary because the response remains optional JSON diagnostics and no backend parser is touched.
- Harness tests remain unnecessary because runtime wiring must not change.
- Manual GNOME validation remains required to inspect live compositor actor metadata and choose the next single candidate.
- Locked boundaries:
- Do not add runtime selection, parent auto-cycling, payload rendering, PyQt suppression, support wording changes, or `true_overlay` claims.
- Do not change the current proof actor parent candidate in this patch.
- Do not touch `follow_surface.py` or backend/follow wiring.

#### Phase 10 Window Group Candidate Implementation Plan
- Implementation status: implemented on 2026-05-15 after active-fullscreen diagnostics showed Elite moves inside `global.window_group` from child index `6` to child index `7` when focused, with VS Code moving behind it. This indicates Mutter's active window stacking is represented inside `global.window_group`. Manual GNOME validation is pending.
- Goal: keep the direct proof path proof-only and change the single proof parent candidate to `global.window_group`, appending the proof actor after current window actors to test whether that layer can stay above focused Elite borderless fullscreen.
- Intended touch points:
- `helpers/gnome_shell_extension/extension.js`: replace the current `global.top_window_group` proof parent with `global.window_group`. Preserve direct proof request fields, strict borderless/fullscreen gate, marker styling, stale timeout, explicit clear, diagnostics, and normal managed PyQt `ApplyPresentation`.
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`: update static/source assertions for the new single candidate and ensure no auto-cycling or old UI/chrome candidates are reintroduced.
- This document: record candidate rationale, files changed, commands, outcomes, and manual validation requirements.
- Test type selection:
- Static/source tests remain sufficient because this patch changes only GNOME Shell extension proof actor source and does not change helper IPC shape.
- Backend/parser tests are not required because diagnostics and direct proof request fields are unchanged.
- Harness tests are not required because runtime wiring must remain unchanged.
- Manual GNOME validation remains required because only the compositor can prove active-fullscreen stacking, transparency, click-through, and focus behavior.
- Locked boundaries:
- Do not add runtime selection, parent auto-cycling, payload rendering, PyQt suppression, support wording changes, or `true_overlay` claims.
- Do not touch `follow_surface.py` or backend/follow wiring.

#### Phase 10 Target Window Actor Child Candidate Implementation Plan
- Implementation status: implemented on 2026-05-15 after manual validation showed `global.window_group` reported full-monitor actor bounds and preserved transparency, but the marker stayed attached to the VS Code/normal-window view, click-through worked only over VS Code, and the marker disappeared immediately when Elite gained focus. Manual GNOME validation is pending.
- Goal: keep Phase 10 proof-only and test whether a Shell actor attached directly to the Elite fullscreen MetaWindowActor can render above Elite borderless fullscreen.
- Intended touch points:
- `helpers/gnome_shell_extension/extension.js`: replace the current `global.window_group` proof parent with a `target_window_actor_child` candidate. Resolve the target MetaWindowActor from `target_token`, attach the proof actor as a direct child, preserve strict eligibility, stale timeout, explicit clear, diagnostics, and normal managed PyQt `ApplyPresentation`.
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`: update static/source assertions for the new single candidate, target MetaWindowActor lookup, target-token matching, and absence of old active proof parents.
- This document: record failed candidate evidence, new candidate, files changed, commands, outcomes, and manual validation requirements.
- Test type selection:
- Static/source tests remain sufficient because this patch changes only GNOME Shell extension proof actor source and does not change helper IPC shape.
- Backend/parser tests are not required unless response shape changes.
- Harness tests are not required because runtime wiring must remain unchanged.
- Manual GNOME validation remains required because only the compositor can prove active-fullscreen stacking, transparency, click-through, focus behavior, and cleanup.
- Locked boundaries:
- Do not add runtime selection, parent auto-cycling, content-subactor cycling, payload rendering, PyQt suppression, support wording changes, or `true_overlay` claims.
- Do not touch `follow_surface.py` or backend/follow wiring.

#### Phase 10 Touch Points
- `helpers/gnome_shell_extension/extension.js`: create, position, stack, hide/destroy, and report the Shell-native proof actor. Keep all behavior opt-in and preserve existing helper protocol compatibility through optional fields.
- `overlay_client/backend/helper_ipc.py`: parse optional proof actor request/response fields only if direct proof commands need typed Python parsing.
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: touched only if the proof is requested through an existing backend-owned helper interface. Do not add production runtime selection in Phase 10.
- `overlay_client/backend/consumers.py` and `overlay_client/follow_surface.py`: should remain untouched unless a narrow backend-owned proof request path is unavoidable. No generic runtime policy should be added in Phase 10.
- Tests:
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py` for static/source proof that the actor is dev-gated, borderless/fullscreen-gated, non-reactive/click-through-oriented, lifecycle-managed, and does not replace the normal `ApplyPresentation` path.
- Backend parser tests only if request/response contracts change.
- `overlay_client/tests/test_backend_architecture_boundary.py` if any backend/follow wiring changes.

#### Phase 10 Handoff Context
- The GNOME Shell helper already owns reliable target discovery through `GetTargetState`. In borderless mode it can report a native `contentRect` equal to the target monitor bounds.
- The existing helper `ApplyPresentation` path can find and manipulate the PyQt overlay window, but the PyQt window is still a managed top-level. That managed-window role is the problem for borderless fullscreen on GNOME Wayland.
- Phase 10 should stop trying to make the PyQt top-level be the fullscreen borderless presentation surface. The PyQt path remains valuable for windowed mode and for fallback.
- The Shell-native proof should treat the GNOME Shell extension as the compositor-side presenter. EDMC/overlay client remains the owner of overlay state, plugin settings, and payload interpretation in later phases.
- First implementation should be direct and reversible: one proof actor, one dev gate, one manual command path, and no automatic runtime selection.

#### Phase 10 Proof Data Flow
1. `GetTargetState` proves the borderless target is eligible.
2. A direct helper command asks the extension to show a proof actor at the target rect.
3. Helper response reports actor visibility, requested rect, applied actor bounds, target token, target monitor, actor parent/layer, and any degradation reason.
4. Manual validation confirms visual behavior.
5. A direct clear request, target loss, helper disable, or stale proof state removes the actor.

#### Phase 10 Test Type Selection
- Static/source tests are required for the GNOME Shell extension proof actor because there is no JS runtime seam in the current headless suite.
- Unit tests are required for any new backend parsing or eligibility helpers because those decisions are deterministic.
- Harness tests are not required unless Phase 10 changes follow-surface lifecycle wiring, backend consumer contracts, or surface visibility calls.
- Manual GNOME validation is mandatory for compositor behavior: placement above borderless fullscreen, transparency, click-through, no focus steal, no flashing, monitor/workspace behavior, and no presentation churn.

#### Phase 10 Non-Goals
- Do not move the full overlay renderer into GNOME Shell in Phase 10.
- Do not implement production scene transport or payload rendering.
- Do not add automatic runtime selection for Shell-native presentation.
- Do not remove or replace the existing PyQt renderer.
- Do not claim `true_overlay` or update support wording.
- Do not change windowed `frame_rect_fallback` behavior.
- Do not reintroduce timed `ApplyPresentation` churn.
- Do not solve non-GNOME compositors or other operating systems.

#### Phase 10 Acceptance Gates
- Small proof passes only if a Shell-native actor appears over Elite borderless fullscreen on the target monitor at full-monitor bounds with no work-area `y=29` offset.
- The actor must remain transparent except for intentional diagnostic marks; no black/opaque fullscreen surface is acceptable.
- Click-through must still work.
- Elite focus must remain stable enough for mapped-visible/mapped-suppressed policy to behave as intended.
- The actor must not appear as a standalone app, titlebar, taskbar item, or Alt-Tab target.
- There must be no recurring compositor-facing placement churn for an unchanged target.
- Target loss, minimize, workspace changes, monitor changes, helper reload, and EDMC shutdown must remove or hide the actor cleanly.
- Only after Phase 10 passes should Phase 11 choose a production content bridge.

#### Phase 10 Implementation Summary
- Implemented on 2026-05-14 as a helper-side direct proof path only. No automatic runtime selection, payload rendering, production scene transport, PyQt content suppression, support wording change, or `true_overlay` claim was added.
- `ApplyPresentation` now accepts optional `shell_actor_proof` / `shellActorProof` and `shell_actor_proof_action` / `shellActorProofAction` request fields. These fields are off by default and are required for the Shell actor proof path to run.
- `shell_actor_proof_action="show"` validates strict borderless/fullscreen eligibility, creates an extension-owned `St.Widget` actor under one single candidate Shell parent/layer, positions it at the requested target content rect, renders a transparent diagnostic outline plus `EDMC Shell Proof` label, records actor parent/layer diagnostics, and starts a `5s` stale timeout.
- Initial Phase 10 used `Main.uiGroup` as the single candidate parent. The first 2026-05-15 follow-up kept the one-candidate rule and changed the candidate to `Main.layoutManager.addChrome(trackFullscreen=true,affectsInputRegion=false)`.
- Manual validation showed the `trackFullscreen=true` candidate loaded and preserved full-monitor actor bounds, but still failed active-fullscreen stacking by staying attached to the normal-window/VS Code layer. The second 2026-05-15 follow-up keeps `Main.layoutManager.addChrome(...)` but changes the current candidate to `Main.layoutManager.addChrome(trackFullscreen=false,affectsInputRegion=false)` to test whether fullscreen tracking was hiding or reordering the actor behind active fullscreen windows.
- Manual validation showed the `trackFullscreen=false` candidate also loaded and preserved full-monitor actor bounds, but still failed active-fullscreen stacking by staying attached to the normal-window/VS Code layer. The third 2026-05-15 follow-up changes the current single candidate to `global.stage` to test a lower-level Shell scene graph parent.
- Manual validation showed the `global.stage` candidate also loaded and preserved full-monitor actor bounds, but still failed active-fullscreen stacking by staying attached to the normal-window/VS Code layer. The fourth 2026-05-15 follow-up changes the current single candidate to `global.top_window_group` to test a Mutter/Shell top-window group candidate.
- The `global.top_window_group` proof candidate reported `shell_actor_proof.actor_parent="global.top_window_group"` after helper reload.
- The fifth 2026-05-15 follow-up changed the current single candidate to `global.window_group`, appending the proof actor after current window actors based on active-fullscreen diagnostics showing Elite becomes the later/top child in that group when focused.
- Manual validation showed the `global.window_group` candidate reported full-monitor actor bounds and preserved transparency, but the marker stayed attached to VS Code/normal-window view, click-through worked only over VS Code, and the marker disappeared immediately when Elite gained focus. The sixth 2026-05-15 follow-up changes the current single candidate to `target_window_actor_child`, resolving the Elite MetaWindowActor from `target_token` and attaching the proof actor directly to that target actor.
- Manual validation showed the `target_window_actor_child` candidate passes the Phase 10 active-fullscreen proof: the marker appeared above focused Elite borderless fullscreen, stayed at `0,0,3440,1440` with no `y=29` work-area offset, preserved transparency with no black/opaque surface, allowed click-through to Elite, and remained visible until the `5s` stale timeout.
- Phase 10 decision: a GNOME Shell-owned actor attached to the target fullscreen MetaWindowActor is viable for GNOME/Wayland borderless fullscreen. Phase 11 may start design/contract work for the production content bridge. Support remains degraded/experimental, and no `true_overlay` claim is made.
- Follow-up cleanup now removes the proof actor from its current parent where possible and then destroys it, so the cleanup path works for `global.stage` without layout-manager chrome registration.
- `shell_actor_proof_action="clear"` removes the proof actor without requiring a target or overlay window.
- `shell_actor_proof_action="diagnose_groups"` returns proof-only GNOME Shell/Mutter group diagnostics without requiring a target, creating an actor, changing the active proof candidate, or changing normal runtime behavior. The payload is bounded and reports known global group availability, parent/index, visibility/mapped/reactive state, bounds, child counts, bounded child summaries, and `global.stage` child order.
- The refined `diagnose_groups` payload also reports `ui_group_child_order`, `window_group_child_order` with MetaWindowActor window details, `proof_actor` sibling/parent metadata when the proof actor is visible, and `target_window_actor` matches when a `target_token` is supplied.
- The proof actor is explicitly non-reactive/click-through oriented (`reactive: false` plus `set_reactive(false)` on actor and child marker widgets). Manual validation still owns the actual click-through proof.
- Ineligible target states do not create/show the actor and return `shell_actor_proof` diagnostics with concise eligibility reasons. Ineligible show requests also clear any existing proof actor.
- Cleanup paths cover explicit clear, ineligible target refresh, stale timeout, replacement of an existing actor, and helper disable/reload.
- The normal managed PyQt `ApplyPresentation` path remains available and unchanged unless proof fields are explicitly present.
- Files changed for Phase 10: `helpers/gnome_shell_extension/extension.js`, `overlay_client/tests/test_gnome_shell_helper_extension_source.py`, and this document.
- Test files added/updated for Phase 10: `overlay_client/tests/test_gnome_shell_helper_extension_source.py`.

#### Tests Run For Phase 10
- Command:
```bash
python3 -m py_compile overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `18 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `58 passed`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1033 passed`, `21 skipped`.
- Command:
```bash
git diff --check
```
- Result: passed.

#### Tests Run For Phase 10 Follow-Up
- Command:
```bash
python3 -m py_compile overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `18 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `58 passed`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1033 passed`, `21 skipped`.
- Command:
```bash
git diff --check
```
- Result: passed.

#### Tests Run For Phase 10 Second Follow-Up
- Command:
```bash
python3 -m py_compile overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `18 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `58 passed`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1033 passed`, `21 skipped`.
- Command:
```bash
git diff --check
```
- Result: passed.

#### Tests Run For Phase 10 Third Follow-Up
- Command:
```bash
python3 -m py_compile overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `18 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `58 passed`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1033 passed`, `21 skipped`.
- Command:
```bash
git diff --check
```
- Result: passed.

#### Tests Run For Phase 10 Fourth Follow-Up
- Command:
```bash
python3 -m py_compile overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `18 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `58 passed`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1033 passed`, `21 skipped`.
- Command:
```bash
git diff --check
```
- Result: passed.

#### Tests Run For Phase 10 Group Diagnostics
- Command:
```bash
python3 -m py_compile overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `19 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `59 passed`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1034 passed`, `21 skipped`.
- Command:
```bash
git diff --check
```
- Result: passed.

#### Tests Run For Phase 10 Group Diagnostics Follow-Up
- Command:
```bash
python3 -m py_compile overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `19 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `59 passed`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1034 passed`, `21 skipped`.
- Command:
```bash
git diff --check
```
- Result: passed.

#### Tests Run For Phase 10 Window Group Candidate
- Command:
```bash
python3 -m py_compile overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `19 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `59 passed`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1034 passed`, `21 skipped`.
- Command:
```bash
git diff --check
```
- Result: passed.

#### Tests Run For Phase 10 Target Window Actor Child Candidate
- Command:
```bash
python3 -m py_compile overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py
```
- Result: passed; `19 passed`.
- Command:
```bash
overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_helper_presentation_runtime.py
```
- Result: passed; `59 passed`.
- Command:
```bash
make check
```
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `1034 passed`, `21 skipped`.
- Command:
```bash
git diff --check
```
- Result: passed.

#### Phase 10 Manual Validation Commands
- Reload helper:
```bash
./scripts/dev_gnome_helper.sh reload
```
- Start EDMC normally. Do not enable `EDMC_OVERLAY_GNOME_BORDERLESS_FULLSCREEN_PREP=1`.
- Enter Elite windowed-borderless mode and capture current target token/rect:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.GetTargetState \
  '{"include_geometry_diagnostics":true}'
```
- Confirm target reports `fullscreen=true` and `contentRect == monitorRect`.
- Capture proof-only Shell/Mutter group diagnostics:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.ApplyPresentation \
  '{"shell_actor_proof":true,"shell_actor_proof_action":"diagnose_groups"}'
```
- Expected diagnostics response: `status="shell_actor_group_diagnostics"` with `shell_actor_proof.group_diagnostics` containing the bounded global group and child/order metadata.
- Capture refined group diagnostics with the current target token to identify the Elite MetaWindowActor:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.ApplyPresentation \
  '{"target_token":"<targetToken>","shell_actor_proof":true,"shell_actor_proof_action":"diagnose_groups"}'
```
- Expected refined diagnostics fields: `ui_group_child_order`, `window_group_child_order`, `target_window_actor`, and `proof_actor`.
- Trigger proof actor for the current `target_window_actor_child` candidate. Replace token and rect with the current target payload:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.ApplyPresentation \
  '{"action":"attach","target_token":"<targetToken>","content_rect":{"x":0,"y":0,"width":3440,"height":1440},"standalone_mode":false,"shell_actor_proof":true,"shell_actor_proof_action":"show"}'
```
- Expected proof response after helper reload: `shell_actor_proof.actor_parent="target_window_actor_child"`.
- To validate over active fullscreen, run the proof command with a delay and focus Elite before it executes:
```bash
sleep 5; gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.ApplyPresentation \
  '{"action":"attach","target_token":"<targetToken>","content_rect":{"x":0,"y":0,"width":3440,"height":1440},"standalone_mode":false,"shell_actor_proof":true,"shell_actor_proof_action":"show"}'
```
- Clear proof actor explicitly:
```bash
gdbus call --session \
  --dest org.edmc.ModernOverlay.Helper \
  --object-path /org/edmc/ModernOverlay/Helper \
  --method org.edmc.ModernOverlay.Helper.ApplyPresentation \
  '{"shell_actor_proof":true,"shell_actor_proof_action":"clear"}'
```
- Validation evidence checklist:
- diagnostic marker appears above Elite;
- marker is on the correct monitor;
- marker has no `y=29` work-area offset;
- no titlebar/taskbar/Alt-Tab entry appears;
- background remains transparent with no black/opaque fullscreen surface;
- click-through works;
- Elite focus remains stable;
- no flashing;
- proof actor clears after explicit clear;
- proof actor clears after the `5s` stale timeout if not refreshed;
- target loss/minimize/workspace mismatch clears or hides actor.
- Phase 10 active-fullscreen proof is complete once the `target_window_actor_child` evidence below is supplied. Broader production lifecycle hardening, target-change handling, and content transport belong to Phase 11+.

#### Phase 10 Manual Validation Evidence
- Validation date: 2026-05-15.
- After helper reload/log-in, the new proof path was active. A stale target token returned `target_unavailable` with a `shell_actor_proof` diagnostics payload, confirming the new helper code was loaded and the proof path was executing.
- Fresh target state:
- `targetToken="meta:16"`.
- `fullscreen=true`.
- `contentRect={"x":0,"y":0,"width":3440,"height":1440}`.
- `monitorRect={"x":0,"y":0,"width":3440,"height":1440}`.
- `work_area_current_monitor={"x":0,"y":29,"width":3440,"height":1411}`.
- Proof command response:
- `status="shell_actor_proof_visible"`.
- `renderer="gnome_shell_actor_proof"`.
- `requested_rect={"x":0,"y":0,"width":3440,"height":1440}`.
- `applied_rect={"x":0,"y":0,"width":3440,"height":1440}`.
- `shell_actor_proof.actor_visible=true`.
- `shell_actor_proof.applied_actor_bounds={"x":0,"y":0,"width":3440,"height":1440}`.
- `shell_actor_proof.actor_parent="Main.uiGroup"`.
- `degrade_reasons=[]`.
- Manual observations:
- The `EDMC Shell Proof` marker/outline appeared above Elite.
- The marker/background was transparent; no black/opaque fullscreen surface appeared.
- No titlebar and no taskbar entry appeared.
- An Alt-Tab entry was observed. This still needs attribution: a Shell actor should not create an Alt-Tab entry, so the observed entry may be the existing PyQt overlay window left running during the proof, but Phase 10 cannot pass the Alt-Tab gate until confirmed.
- Click-through remains unresolved. User was unsure; when alt-tabbing to the game, the marker disappeared. This may be the expected `5s` stale timeout or focus/stacking behavior, but it needs a refreshed proof test before Phase 10.5 can pass.
- The proof actor disappeared after about `5s`, matching the stale-timeout requirement.
- Interpretation: Phase 10 now has a strong geometry/transparency/stale-cleanup proof. It proves a Shell-owned actor can occupy the full monitor at `y=0` above the borderless target, bypassing the managed PyQt work-area `y=29` constraint. Phase 10 remains incomplete pending explicit Alt-Tab attribution and click-through/focus validation.
- Follow-up observation: the taskbar/Alt-Tab entry was confirmed to be a `python3` icon that looks like the existing PyQt overlay window, currently on the second monitor. Treat this as a PyQt coexistence artifact, not evidence that the Shell actor creates a taskbar entry. PyQt coexistence/suppression belongs to Phase 11/12, not Phase 10.
- Refreshed proof-loop observation: the proof marker appeared over VS Code and clicks passed through to VS Code, which supports the non-reactive/click-through behavior of the Shell actor. When the user alt-tabbed to Elite, the marker disappeared. This means the first parent/layer candidate, `Main.uiGroup`, does not yet satisfy the "stays above active fullscreen Elite" gate. Phase 10 should remain open and try the next single parent/layer candidate in a follow-up proof patch, rather than moving to Phase 11.
- Layout-manager `trackFullscreen=true` observation: after helper reload/log-in, the proof response reported `shell_actor_proof.actor_parent="Main.layoutManager.addChrome(trackFullscreen=true,affectsInputRegion=false)"` and full-monitor actor bounds at `{"x":0,"y":0,"width":3440,"height":1440}`, but the marker still stayed attached to the VS Code/normal-window layer instead of active fullscreen Elite. This candidate fails the active-fullscreen gate.
- Layout-manager `trackFullscreen=false` observation: after helper reload/log-in, the proof response reported `shell_actor_proof.actor_parent="Main.layoutManager.addChrome(trackFullscreen=false,affectsInputRegion=false)"` and full-monitor actor bounds at `{"x":0,"y":0,"width":3440,"height":1440}`. Manual validation while Elite was in borderless mode showed the marker was still attached to VS Code, not Elite. This candidate also fails the active-fullscreen gate.
- `global.stage` observation: after helper reload/log-in, the proof response reported `shell_actor_proof.actor_parent="global.stage"` and full-monitor actor bounds at `{"x":0,"y":0,"width":3440,"height":1440}`. Manual validation while Elite was in borderless mode showed the marker was still attached to VS Code, not Elite. This candidate also fails the active-fullscreen gate.
- `global.top_window_group` observation: after helper reload/log-in, the proof response reported `shell_actor_proof.actor_parent="global.top_window_group"` and full-monitor actor bounds at `{"x":0,"y":0,"width":3440,"height":1440}`. Manual validation while Elite was in borderless mode showed the marker was still attached to VS Code, was visible over non-fullscreen application windows, and disappeared when alt-tabbing to Elite or another window. This candidate also fails the active-fullscreen gate.
- Interpretation: `Main.uiGroup`, both `Main.layoutManager.addChrome(...)` variants, `global.stage`, and `global.top_window_group` can place a transparent Shell actor at the right full-monitor geometry, but none of those layers stays above active fullscreen Elite. Phase 10 still proves the geometry and transparency mechanism, but not the fullscreen stacking layer. The next step should inspect actual GNOME Shell/Mutter group ordering and available fullscreen/overlay groups before choosing another single candidate, not continue guessing generic Shell parents and not broaden into production bridge work yet.

#### Phase 10 Group Diagnostics Scope
- Add direct helper proof action: `shell_actor_proof_action="diagnose_groups"`.
- The command may be called without `target_token` or `content_rect`; it is not an attach/show request.
- It should return a `shell_actor_proof.group_diagnostics` object with:
- schema version;
- known group names checked;
- available/unavailable state per group;
- parent name and index within parent where available;
- actor type/class name;
- visibility/mapped/reactive state where available;
- bounds where available;
- child count and a bounded child summary list;
- stage child order summary if `global.stage` is available.
- `uiGroup` child order summary;
- `global.window_group` child order with bounded MetaWindowActor metadata;
- proof actor parent/sibling metadata if the proof actor is visible;
- target-window match metadata when `target_token` is supplied.
- Keep diagnostics concise and bounded; do not serialize arbitrary actor trees.
- Use the result to choose the next single proof candidate only after manual review.

#### Phase 10 Follow-Up Scope: Fullscreen-Aware Chrome Candidate
- Follow-up goal: keep the same direct proof command and strict borderless/fullscreen gate, but change only the Shell actor parent/layer candidate from `Main.uiGroup` to a fullscreen-aware GNOME Shell chrome registration.
- First candidate: `Main.layoutManager.addChrome(actor, { trackFullscreen: true, affectsInputRegion: false })`.
- Reason: local GNOME Shell extensions use `Main.layoutManager.addChrome(...)` for Shell-owned chrome, including `trackFullscreen: true` for fullscreen-aware actors. The proof actor remains non-reactive, and `affectsInputRegion: false` keeps the candidate click-through-oriented.
- Manual result: this candidate loaded and reported `shell_actor_proof.actor_parent="Main.layoutManager.addChrome(trackFullscreen=true,affectsInputRegion=false)"`, but it still stayed with the VS Code/normal-window layer and failed the active-fullscreen gate.
- Second candidate: `Main.layoutManager.addChrome(actor, { trackFullscreen: false, affectsInputRegion: false })`.
- Second candidate reason: if `trackFullscreen=true` makes Shell track or hide chrome around fullscreen windows, `trackFullscreen=false` may leave the proof actor in the Shell chrome layer instead of letting fullscreen-window tracking push it behind active fullscreen content.
- Implementation result: the proof actor used this candidate and reported `shell_actor_proof.actor_parent="Main.layoutManager.addChrome(trackFullscreen=false,affectsInputRegion=false)"` in proof diagnostics after helper reload.
- Manual result: this candidate loaded correctly, but the marker was still attached to VS Code/normal-window focus rather than active fullscreen Elite. It does not pass Phase 10.
- Third candidate: `global.stage`.
- Third candidate reason: `global.stage` tests a lower-level Shell scene graph parent instead of Shell chrome/layout-manager registration. This remains proof-only and single-candidate.
- Implementation result: the proof actor used this candidate and reported `shell_actor_proof.actor_parent="global.stage"` in proof diagnostics after helper reload.
- Manual result: this candidate loaded correctly, but the marker was still attached to VS Code/normal-window focus rather than active fullscreen Elite. It does not pass Phase 10.
- Fourth candidate: `global.top_window_group`.
- Fourth candidate reason: `global.top_window_group` tests a Mutter/Shell top-window group rather than a Shell UI/chrome/stage group, which may be closer to the fullscreen window stacking layer.
- Implementation result: the proof actor used this candidate and reported `shell_actor_proof.actor_parent="global.top_window_group"` in proof diagnostics after helper reload.
- Manual result: this candidate loaded correctly, but the marker was still attached to VS Code/non-fullscreen window focus and disappeared when alt-tabbing to Elite or another window. It does not pass Phase 10.
- Diagnostic result: focused Elite moves to a later/top child index inside `global.window_group`, while VS Code moves behind it. `global.top_window_group` is above `global.window_group` in `uiGroup` order but still fails active-fullscreen visibility.
- Fifth candidate: `global.window_group`.
- Fifth candidate reason: adding the proof actor directly to `global.window_group` appends it after current window actors, which tests the same stacking layer that Mutter uses for the active fullscreen game.
- Implementation result: the proof actor uses this candidate and should report `shell_actor_proof.actor_parent="global.window_group"` after helper reload.
- Manual result: this candidate reported full-monitor actor bounds and preserved transparency, but it stayed attached to VS Code/normal-window view, click-through worked only over VS Code, and the marker disappeared immediately when Elite gained focus. It does not pass Phase 10.
- Sixth candidate: `target_window_actor_child`.
- Sixth candidate reason: direct attachment to the Elite MetaWindowActor tests whether content inside the fullscreen window actor tree can render above the active fullscreen game when global Shell/window groups cannot.
- Implementation result: the proof actor uses this candidate and should report `shell_actor_proof.actor_parent="target_window_actor_child"` after helper reload.
- Manual result: this candidate passes the active-fullscreen proof. The response reported `shell_actor_proof.actor_parent="target_window_actor_child"`, `applied_rect={"x":0,"y":0,"width":3440,"height":1440}`, and `degrade_reasons=[]`. User observed the marker above focused Elite, no `y=29` offset, transparent/no black background, click-through to Elite, and visibility until the stale timeout.
- Phase 10 decision: Shell-native attachment to the target fullscreen MetaWindowActor is viable. Phase 11 may proceed to production bridge design and contracts.
- Scope boundary: do not auto-cycle parent/layer candidates. If this candidate fails active-fullscreen validation, record the failed gate and scope the next single GNOME-native proof option.
- Backend/runtime impact: none expected. No automatic runtime selection, no PyQt content suppression, no payload rendering, no support wording change, and no `true_overlay` claim.
- Manual validation required after the patch:
- reload helper with `./scripts/dev_gnome_helper.sh reload`;
- start EDMC normally without `EDMC_OVERLAY_GNOME_BORDERLESS_FULLSCREEN_PREP=1`;
- keep Elite in borderless fullscreen with `contentRect == monitorRect`;
- run the existing Phase 10 proof show command repeatedly or refresh within the `5s` timeout;
- confirm `shell_actor_proof.actor_parent` reports the current candidate;
- confirm the marker appears over active fullscreen Elite, not only over other apps;
- confirm click-through, transparency, no taskbar/Alt-Tab Shell actor entry, no flashing, and stale/explicit cleanup.

### Phase 11: GNOME Shell-Native PyQt Raster Bridge Architecture
- Goal: after the Phase 10 proof passes, define the production bridge that keeps PyQt as the renderer while using a GNOME Shell actor as the GNOME/Wayland borderless/fullscreen presentation surface.
- Phase 11 is design and contract work. It may add small parser/model prototypes if needed, but it must not enable production Shell-native rendering by default.
- Preserve existing behavior and support wording from Phase 10.
- Locked direction: PyQt remains required. GNOME Shell must not become the primary overlay renderer in this plan. The Shell extension should display PyQt-generated raster content only for the GNOME/Wayland borderless/fullscreen case that cannot be solved with a managed PyQt top-level window.

#### Phase 11 Refactor Staging
| Stage | Description | Status |
| --- | --- | --- |
| 11.1 | Review Phase 10 manual proof evidence and record whether Shell-native borderless presentation is viable | Completed; Phase 10 Proof Passed |
| 11.2 | Choose content bridge option: Shell-rendered primitives, client-generated raster frames/textures, or hybrid scene protocol | Completed; PyQt-generated raster frames/textures selected |
| 11.3 | Define frame/update/clear protocol, frame versioning, target-token binding, scale handling, stale-frame timeout, and compatibility rules | Completed; File-Based PNG Frame Contract Locked |
| 11.4 | Define helper-side Shell presentation controller boundaries so proof actor, frame updates, lifecycle cleanup, and diagnostics are not spread through unrelated helper code | Completed; Helper Controller Boundary Locked |
| 11.5 | Define backend-owned Python models and IPC helpers without leaking GNOME-specific protocol details into generic follow/runtime code | Completed; Backend-Owned Frame Model Boundary Locked |
| 11.6 | Decide PyQt coexistence policy for Shell-native production mode: suppress PyQt content, keep PyQt as fallback, or use an explicit transition/debug mode | Completed; PyQt renderer retained, managed PyQt window remains default/fallback, Shell actor displays raster only for gated borderless/fullscreen |
| 11.7 | Decide whether renderer parity can fit in Phase 12 or must be deferred to Phase 14; default expectation is to defer broad parity work | Completed; Phase 12 is a small raster proof, broader parity/performance work moves to Phase 14+ |
| 11.8 | Record Phase 12 implementation prompt, touch points, test plan, manual validation plan, and explicit out-of-scope renderer parity items | Completed; Phase 12 Prompt Recorded |

#### Phase 11.8 Documentation Plan
- Implementation type: documentation/contract handoff only. No Phase 12 runtime behavior, automatic runtime selection, helper code, backend code, or PyQt presentation behavior should change in Phase 11.8.
- Intended touch point: this document.
- Test type selection: `git diff --check -- docs/refactoring/gnome_wayland_presentation_attachment.md` is sufficient for this doc-only contract update. Unit/static/harness tests are not required unless code is touched.
- Support wording remains degraded/experimental. Do not claim `true_overlay`.

#### Phase 11 Locked Decisions
- PyQt remains the renderer. The project must not switch to Shell-rendered primitives as the primary overlay rendering path.
- GNOME Shell becomes the presentation surface only for the GNOME/Wayland borderless/fullscreen case proven in Phase 10.
- The selected content bridge is client-generated raster frames/textures produced from PyQt-rendered overlay content.
- Shell-rendered primitives are rejected for the first production bridge because they require recreating the overlay renderer in GNOME Shell.
- A hybrid bridge is deferred. It may be reconsidered only after the PyQt raster bridge has a measured limitation that justifies more contract surface.
- The raster bridge must behave like UI snapshots, not video streaming: event-driven updates, no-op suppression, bounded cadence, byte/size guards, stale cleanup, and visible fallback are required before runtime use.
- Phase 12 must stay intentionally small. It should prove one transparent PyQt-generated frame or cropped frame displayed by the Phase 10 target-window-actor path, not full renderer parity.
- Phase 13 owns hardening and support gates for the minimal bridge. Phase 14+ owns broader parity, performance tuning, transfer strategy refinement, and feature expansion.
- Scope is GNOME Wayland windowed-borderless/full-monitor only. Windowed Elite remains on the existing managed PyQt overlay path unless a future phase scopes a separate reason to change it.
- Transfer starts with local PNG files under a controlled EDMC overlay runtime/cache directory. Shared memory, raw buffers, and direct texture transfer are deferred until performance evidence requires them.
- Raster frames should be cropped to the overlay content bounds with placement metadata. Full-monitor transparent frames are allowed only for a specific proof or fallback case.
- Runtime activation is off by default behind `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`.

#### Phase 11 Accepted Recommendations
- Frame transport: PyQt writes PNG files to a controlled runtime/cache directory; the helper receives only validated paths under that directory.
- Frame shape: use cropped frames plus `x`, `y`, `width`, and `height` placement metadata. Avoid full `3440x1440` frames in the steady state.
- Update trigger: event-driven only. Do not send new frames unless overlay content or target binding changes.
- Update suppression: include a checksum/signature and suppress unchanged frames before IPC.
- Update cadence: start with a conservative `2-5 FPS` maximum for the Phase 12 proof/hardening path, then adjust only after measuring GNOME Shell responsiveness.
- Path/security rule: reject arbitrary paths and any path traversal; only accept regular image files under the configured EDMC overlay runtime/cache directory.
- Clear behavior: support explicit clear plus stale timeout. Clear on target loss, token change, workspace mismatch, minimize, helper reload/disable, EDMC shutdown, overlay client shutdown, and stale-frame expiry.
- PyQt coexistence: keep PyQt as the renderer and default/fallback presenter. Suppress or hide the managed PyQt overlay window only while the gated Shell raster path is active and healthy for borderless/full-monitor mode.
- Fallback: if the Shell frame path fails validation, load, texture apply, target binding, or readback, clear the Shell actor and fall back visibly to the current degraded PyQt helper path.
- Phase 12 scope: one transparent PyQt-generated test frame or cropped frame over Elite via `target_window_actor_child`; no full overlay parity.

#### Phase 11 Frame Protocol Contract
- The Phase 12 request fields should be optional and backward-compatible with the existing helper protocol.
- Request actions:
- `update`: validate target/path/frame metadata, load the PNG frame, attach or refresh the Shell texture actor under the target fullscreen MetaWindowActor, and acknowledge the applied frame version.
- `clear`: remove the Shell raster actor and associated stale timer without requiring an overlay window or a currently valid frame file.
- Suggested optional request fields:
- `shell_raster_frame`: boolean gate for the raster-frame path.
- `shell_raster_frame_action`: `"update"` or `"clear"`.
- `frame_version`: monotonically increasing integer or string version for no-op and acknowledgement tracking.
- `target_token`: helper target token that the frame is bound to.
- `target_rect`: target content/full-monitor rect used for eligibility validation.
- `frame_rect`: placement rect for the raster frame within GNOME Shell global logical coordinates.
- `scale`: logical-to-render scale used when producing the frame.
- `image_path`: absolute path to the PNG frame under the allowed runtime/cache directory.
- `checksum`: content checksum used for no-op suppression and optional helper-side diagnostics.
- `byte_size`: frame file size, used for diagnostics and guardrails.
- `stale_timeout_ms`: required stale cleanup deadline.
- Required response fields:
- `status`: success/degraded/clear result.
- `frame_version`: acknowledged frame version, when applicable.
- `target_token`: target token used by the helper.
- `applied_actor_bounds`: Shell actor bounds after apply.
- `frame_rect`: accepted placement rect.
- `frame_dimensions`: decoded image dimensions.
- `cleanup_action`: clear/stale action, if any.
- `degrade_reasons`: concise failure reasons.
- Required degradation/failure reasons:
- `target_unavailable`: target token could not be resolved.
- `target_not_borderless_full_monitor`: target does not satisfy the GNOME Wayland windowed-borderless/full-monitor gate.
- `workspace_mismatch`: target is not showing on the current workspace.
- `target_minimized`: target is minimized.
- `invalid_frame_path`: frame path is missing, malformed, non-absolute, or otherwise invalid.
- `path_outside_allowed_cache_dir`: frame path is not under the configured EDMC overlay runtime/cache directory.
- `frame_file_missing`: frame path does not exist or is not a regular file.
- `frame_file_too_large`: frame file exceeds the configured byte-size guard.
- `frame_decode_failed`: helper could not decode/load the image.
- `texture_apply_failed`: helper could not create or apply the Shell texture actor.
- `stale_frame`: frame update expired or stale cleanup fired.
- `frame_rect_mismatch`: applied actor bounds do not match the requested frame rect.
- Compatibility:
- All new request/response fields remain optional and backward-compatible.
- No helper protocol bump is required for Phase 12 unless implementation proves the optional-field contract is insufficient.
- Existing `ApplyPresentation` behavior must remain unchanged unless `shell_raster_frame=true` is explicitly supplied.

#### Phase 11 Controller Boundaries
- Helper-side Shell presentation control should be isolated from the Phase 10 proof code before production use. The controller owns frame actor creation, target-window-actor attachment, texture/image loading, stale cleanup, explicit clear, diagnostics, and helper-disable cleanup.
- The existing proof path may remain for manual diagnostics, but production frame update/clear behavior should not be interleaved with proof-only marker code.
- Backend-owned Python code owns eligibility policy, runtime gate checks, frame signatures, path construction, request building, response parsing, fallback decisions, and concise logging.
- Generic follow/runtime code must call backend-owned presentation interfaces only. It must not import GNOME helper implementation details, check raw helper protocol fields, or dispatch behavior based on compositor-specific enum/string checks.

#### Phase 11 Phase 12 Touch Point Handoff
- `helpers/gnome_shell_extension/extension.js` or a helper-local module split: helper-side Shell raster presentation controller, target-window-actor attachment, PNG decode/texture actor lifecycle, explicit clear, stale timeout, diagnostics, and disable/reload cleanup.
- `overlay_client/backend/helper_ipc.py`: typed optional request/response parsing for raster frame update/clear fields.
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: GNOME-specific eligibility, runtime gate, frame signature/no-op policy, request construction, response interpretation, and fail-soft fallback.
- Backend-owned frame model/helper module if needed: frame metadata model, checksum/signature generation, cache-dir/path validation, byte-size guards, and update cadence helpers.
- PyQt rendering/export touch point: produce one transparent PNG frame or cropped frame for the Phase 12 proof without changing normal windowed presentation behavior.
- Tests: helper source/static tests, backend model/unit tests, runtime policy tests, backend-boundary tests, and harness tests only if runtime selection or PyQt window suppression wiring changes.

#### Phase 11 Content Bridge Options
- Option A: Shell-rendered primitives.
- Decision: not selected for the first production bridge.
- Reason: primitives would make GNOME Shell a second overlay renderer and would require recreating PyQt visual behavior in St/Clutter.
- Keep this only as a possible future optimization for very small static elements if the raster bridge later proves too expensive.
- Option B: client-generated raster frames/textures.
- Decision: selected.
- Python/PyQt renders transparent overlay content into a bounded raster frame or cropped frame; the Shell extension displays that frame as a texture attached to the target fullscreen MetaWindowActor.
- Pros: preserves PyQt as renderer, preserves visual parity direction, avoids the managed PyQt top-level window placement/stacking problem, and builds directly on the Phase 10 actor proof.
- Cons: heavier than primitives, requires careful transfer, cadence, memory, and stale-frame controls.
- Option C: hybrid scene protocol.
- Decision: deferred.
- Reason: hybrid adds contract surface before there is evidence that a bounded PyQt raster bridge is insufficient.

#### Phase 11 Production Data Flow Design
1. Existing EDMC/plugin logic continues to produce overlay state.
2. PyQt renders overlay content into a transparent raster frame or cropped frame without relying on the managed PyQt top-level window as the GNOME borderless presentation surface.
3. Overlay client converts that frame into a backend-owned Shell frame/update model.
4. Backend/helper IPC sends frame version, target token, target/content bounds, scale, visibility/action, frame reference or transfer handle, checksum/signature, byte dimensions, and stale timeout to the helper.
5. Extension validates the target token and bounds, then displays the frame as a Shell texture actor attached to the target fullscreen MetaWindowActor.
6. Extension acknowledges applied frame version, actor bounds, frame dimensions, and cleanup state.
7. Backend logs concise state, suppresses no-op updates, and enforces bounded update cadence before any compositor-facing work.

#### Phase 11 Test Type Selection
- Unit tests are required for schema/model decisions because frame eligibility, versioning, and no-op signatures are deterministic.
- Static/source tests are required for planned extension controller boundaries if prototype code is added.
- Harness tests are required only if runtime lifecycle or backend consumer contracts change during prototyping.

### Phase 12: GNOME Shell-Native PyQt Raster Bridge Small Production Proof
- Goal: implement the first selected PyQt raster bridge behind a dev/runtime gate, preserving managed PyQt helper presentation as the default for windowed, unsupported, and fallback paths.
- Phase 12 should start with the smallest useful raster proof: one static transparent PyQt-generated test frame or cropped frame displayed by the Phase 10 target-window-actor path.
- Broad renderer parity is not in Phase 12. Larger visual parity, high-cadence transfer, richer cropping/damage tracking, and performance expansion move to Phase 14+.
- Support wording remains degraded/experimental throughout Phase 12.

#### Phase 12 Refactor Staging
| Stage | Description | Status |
| --- | --- | --- |
| 12.1 | Extract helper-side Shell presentation controller/class from the Phase 10 proof code | Completed |
| 12.2 | Add backend-owned Shell frame models, request builders, response parsers, and optional helper capability fields | Completed |
| 12.3 | Implement frame/update/clear IPC in the helper with backward-compatible optional request/response fields | Completed |
| 12.4 | Implement the selected minimal PyQt raster bridge behind a dev/runtime gate, with explicit limits on frame dimensions, bytes, cadence, and supported transparency behavior | Completed For Static PNG Proof |
| 12.5 | Wire runtime selection for GNOME borderless/fullscreen Shell-native presentation through backend-owned interfaces only | Completed Behind `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` |
| 12.6 | Preserve PyQt presentation for windowed mode and add visible fail-soft fallback for unsupported/failing Shell-native presentation | Completed; no windowed-mode migration |
| 12.7 | Add frame signatures/no-op suppression and bounded update cadence before enabling any runtime loop | Completed For Static Proof Signature; broader cadence hardening remains Phase 13 |
| 12.8 | Add headless unit/static/harness coverage for parser, policy, backend boundaries, fallback behavior, and regression slices from Phases 6A, 6B, 8, 9.9A, and 9B | Completed |
| 12.9 | Run targeted tests and `make check`; leave manual production validation to Phase 13 | Completed |
| 12.10 | Record unsupported renderer features and required Phase 14 parity work before Phase 12 closes | Completed; real overlay parity remains Phase 14+ |
| 12.11 | Fix Phase 12 raster lifecycle cleanup after EDMC/overlay-client shutdown so Shell actors cannot persist as orphaned proof surfaces | Completed; Persistent Runtime Retest Failed, Deferred To Phase 13 |
| 12.12 | Suppress the managed PyQt overlay window after a successful Shell raster frame apply while preserving visible PyQt fallback on failure | Completed; Persistent Runtime Retest Failed, Deferred To Phase 13 |
| 12.13 | Add an extra explicit dev gate for persistent Shell raster runtime after manual focus/overview instability, keeping Phase 12 proof behavior disabled by default even when the bridge flag is present | Completed; Safe-Flag Manual Retest Passed |

#### Phase 12 Accepted Recommendations
- Proof frame source: start with a static PyQt-generated transparent PNG test frame. Do not export or stream the full live overlay in Phase 12.
- Real overlay content timing: defer actual overlay snapshots/cropped panels to Phase 14 after Phase 12 proves the frame pipeline and Phase 13 hardens runtime lifecycle. Pulling a tiny real-content slice into late Phase 12 is allowed only if the static proof is clean and the scope remains explicitly bounded.
- Cache directory: use a per-user runtime/cache directory, preferably `$XDG_RUNTIME_DIR/EDMCModernOverlay/shell-raster/`, with a private `/tmp` fallback if needed. Directory permissions should be user-only, such as `0700`.
- Image format: PNG RGBA only. Do not add JPEG, SVG, raw buffers, shared memory, or texture handles in Phase 12.
- Frame limits: decoded dimensions must fit within the target rect; `frame_rect` must be inside the target rect; file size must be capped. Full-monitor PNGs are acceptable only for a specific proof/fallback case, not as the steady-state target.
- Helper API shape: use optional fields on the existing helper request path. Do not require a helper protocol bump unless optional fields prove insufficient.
- Helper implementation shape: extract or isolate a small helper-side Shell raster controller rather than adding production frame behavior into the Phase 10 proof marker path.
- Runtime wiring: keep the path off by default. After Phase 12.13, `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` alone is not sufficient to apply persistent Shell raster updates; live runtime presentation also requires the explicit dev gate `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1`. This prevents accidental persistent fullscreen child actors while Phase 13 focus/lifecycle hardening is pending.
- PyQt window suppression: keep suppression minimal. Suppress/hide the managed PyQt overlay only after the Shell frame path successfully applies, and restore or fall back visibly on failure.
- No-op/cadence: implement checksum/signature suppression before repeated updates and avoid sending unchanged frames.

#### Phase 12.1 Implementation Plan
- Started: 2026-05-15.
- Intended touch points:
- `helpers/gnome_shell_extension/extension.js`: add an opt-in Shell raster frame controller path separate from the Phase 10 proof marker path, with image actor lifecycle, strict borderless/full-monitor eligibility, path/image guards, stale timeout, explicit clear, and normal `ApplyPresentation` preservation.
- `overlay_client/backend/helper_ipc.py`: add backend-owned optional raster frame request/response models and parser fields.
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: add GNOME-specific runtime gate, static PyQt PNG proof frame request construction, frame signatures/no-op behavior, and fail-soft handling behind backend-owned interfaces.
- New backend-owned helper module if useful: static PyQt PNG proof frame creation, runtime/cache directory management, checksum/signature, and path validation helpers.
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`: static/source coverage for helper raster opt-in, target-window-actor attachment, path validation, image load/decode failure handling, stale timeout, explicit clear, non-reactive actor behavior, helper-disable cleanup, and normal `ApplyPresentation` preservation.
- Backend unit/runtime tests: frame model/cache/signature/path validation, request payload fields, response parsing, runtime gate/eligibility/no-op/fallback behavior, and backend-boundary preservation.
- Test type selection:
- Unit tests are required for backend frame model, checksum/signature, path validation, eligibility, no-op, and fallback decisions.
- Static/source tests are required for helper-side Shell raster source because there is no JS runtime seam in headless tests.
- Harness tests are required only if generic runtime selection or PyQt window suppression wiring changes.
- Backend-boundary tests are required if backend/follow wiring changes. Generic `follow_surface.py` must not import GNOME helper implementation details or check raw helper protocol fields.
- Support wording remains degraded/experimental. No `true_overlay` claim.

#### Phase 12 Implementation Summary
- Completed: 2026-05-15.
- Helper-side implementation:
- Added an isolated, opt-in `shell_raster_frame` path to `helpers/gnome_shell_extension/extension.js`.
- Supported `shell_raster_frame_action="update"` and `"clear"` with optional backward-compatible request fields.
- Attached the raster actor under the proven `target_window_actor_child` path.
- Added strict borderless/full-monitor eligibility, PNG/RGBA decode validation, allowed-cache path validation, file-size checks, non-reactive actor behavior, stale timeout, explicit clear, and helper-disable cleanup.
- Backend implementation:
- Added `HelperRasterFrameRequest` and optional raster response parsing in `overlay_client/backend/helper_ipc.py`.
- Added `overlay_client/backend/shell_raster_frame.py` for cache-dir construction, `0700` cache creation, path validation, checksum generation, static PyQt PNG test-frame export, and borderless/full-monitor request eligibility.
- Wired the runtime gate in `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py` behind `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`.
- Preserved the existing PyQt path when the gate is off, when the target is not borderless/full-monitor, or when the static frame cannot be built.
- Existing windowed mode remains on the managed PyQt presentation path. No generic `follow_surface.py` wiring changed.
- Files changed:
- `docs/refactoring/gnome_wayland_presentation_attachment.md`
- `helpers/gnome_shell_extension/extension.js`
- `overlay_client/backend/__init__.py`
- `overlay_client/backend/helper_ipc.py`
- `overlay_client/backend/shell_raster_frame.py`
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`
- `overlay_client/tests/test_gnome_shell_helper_presentation_state.py`
- `overlay_client/tests/test_gnome_helper_presentation_runtime.py`
- `overlay_client/tests/test_shell_raster_frame.py`
- Validation commands and outcomes:
- `python3 -m py_compile overlay_client/backend/helper_ipc.py overlay_client/backend/shell_raster_frame.py overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: passed.
- `python3 -m py_compile overlay_client/tests/test_shell_raster_frame.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_gnome_shell_helper_extension_source.py`: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_shell_raster_frame.py`: 4 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py`: 24 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_presentation_state.py`: 24 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py`: 41 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_architecture_boundary.py`: 2 passed.
- `git diff --check`: passed.
- `make check`: ruff passed, mypy passed, full pytest passed with 1047 passed and 21 skipped.
- Manual validation evidence:
- 2026-05-16 user validation with EDMC launched using `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`: the user saw `EDMC PyQt Raster Proof` in a green box in the upper-left corner while Elite had focus. This proves the static PyQt-generated PNG frame is visible above active Elite borderless fullscreen through the Shell raster path.
- The user reported no titlebar for the proof frame, focus remained stable, and there was no black/opaque background or flashing.
- Exact `y=0` offset remains visually inconclusive because the Phase 12 frame is intentionally a small cropped proof box, not a full-screen image.
- Click-through directly under the proof box remains inconclusive because there was no clickable game control under the small proof frame. Click-through elsewhere still worked.
- Stale-timeout behavior remains inconclusive while EDMC is running because the runtime refreshes the frame. The user reported the proof disappears after closing EDMC, which is useful cleanup evidence but is not yet a standalone stale-timeout proof.
- 2026-05-16 follow-up validation patch scope: enlarge the static proof PNG to nearly the full target rect with a 10 px inset. This keeps the test as a cropped/static proof while making offset and click-through validation practical.
- 2026-05-16 follow-up validation result: with the near-fullscreen 10 px inset proof frame, the user confirmed the green box is at true monitor origin with no `y=29` offset and confirmed click-through works into the game under the proof frame.
- 2026-05-16 lifecycle bug report: after EDMC shutdown, the EDMC/overlay window surface did not close cleanly and the Shell raster proof remained visible even though the user could not find a remaining EDMC process to kill. This means Phase 12 needs an explicit shutdown clear path in addition to helper-side stale timeout and manual clear.
- Phase 12.11 intended touch points:
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: add a backend-owned best-effort Shell raster clear request helper for shutdown paths.
- `overlay_client/launcher.py`: clear the Shell raster frame during overlay-client quit when `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`.
- `load.py`: clear the Shell raster frame during EDMC plugin stop when the Phase 12 gate is enabled.
- Tests: unit tests for the backend clear request and launcher shutdown hook; harness test for plugin-stop cleanup wiring. Static helper tests remain unchanged unless helper JS is touched.
- Phase 12.11 implementation result:
- Added a backend-owned `build_shell_raster_frame_clear_request()` and `clear_gnome_shell_raster_frame_via_gdbus()` shutdown cleanup helper.
- Added an overlay-client Qt shutdown hook that sends `shell_raster_frame_action="clear"` when `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`.
- Added an EDMC plugin-stop backup clear path, including the idempotent stop path.
- Added tests:
- `overlay_client/tests/test_gnome_helper_presentation_runtime.py`: shutdown clear request and fetcher coverage.
- `overlay_client/tests/test_launcher_shell_raster_shutdown.py`: overlay-client env-gated shutdown clear coverage.
- `tests/test_harness_plugin_hooks_contract.py`: plugin stop clear helper coverage under the harness.
- Phase 12.11 validation commands and outcomes:
- `python3 -m py_compile load.py overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/launcher.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_launcher_shell_raster_shutdown.py tests/test_harness_plugin_hooks_contract.py`: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_launcher_shell_raster_shutdown.py tests/test_harness_plugin_hooks_contract.py`: 48 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_backend_architecture_boundary.py`: 26 passed.
- `git diff --check`: passed.
- `make check`: ruff passed, mypy passed, full pytest passed with 1052 passed and 21 skipped.
- 2026-05-16 managed-window suppression bug report: after restart and rerun with `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`, shutdown still left a visible `EDMC Modern Overlay` window actor. Helper group diagnostics showed a stale managed PyQt overlay window actor (`title="EDMC Modern Overlay"`, `wm_class="python3"`, bounds `0,29,640,480`) with no corresponding live process. Root cause: Phase 12 applied the Shell raster frame but still exposed `should_show_overlay=True` to the generic PyQt surface path, so the managed overlay window remained visible instead of being suppressed after successful Shell raster presentation.
- Phase 12.12 intended touch points:
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: return `should_show_overlay=False` only when the Shell raster frame path has successfully applied and matched the requested rect.
- `overlay_client/backend/consumers.py` or related tests if backend result visibility expectations need coverage.
- `overlay_client/tests/test_gnome_helper_presentation_runtime.py`: add/update runtime tests proving Shell raster success suppresses the managed PyQt overlay and Shell raster fallback/failure keeps PyQt visible.
- Keep windowed mode on the existing managed PyQt path, and keep support wording degraded/experimental.
- Phase 12.12 implementation result:
- Added `shell_raster_frame_presented` to the GNOME helper presentation runtime result.
- Changed `should_show_overlay` to return `False` only when the Shell raster frame renderer has successfully applied with a matching valid applied rect.
- Preserved visible PyQt fallback when the Shell raster frame path is gated off, cannot build a frame, fails eligibility, or falls back to normal PyQt presentation.
- Phase 12.12 validation commands and outcomes:
- `python3 -m py_compile overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_launcher_shell_raster_shutdown.py tests/test_harness_plugin_hooks_contract.py`: 48 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_architecture_boundary.py`: 30 passed.
- `git diff --check`: passed.
- `make check`: ruff passed, mypy passed, full pytest passed with 1052 passed and 21 skipped.
- Manual validation remains pending for:
- Reload helper with `./scripts/dev_gnome_helper.sh reload --yes`.
- Start EDMC normally with `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` and without `EDMC_OVERLAY_GNOME_BORDERLESS_FULLSCREEN_PREP=1`.
- Put Elite in GNOME Wayland windowed-borderless/full-monitor mode.
- Confirm target state reports `fullscreen=true` and `contentRect == monitorRect`.
- Confirm explicit clear, stale timeout after refresh stops, invalid path fail-soft, changed target token fail-soft, and windowed mode still using the existing PyQt path.
- Confirm EDMC/overlay-client shutdown clears the Shell raster proof and does not leave a blank/stuck window surface.
- Confirm a successful Shell raster frame no longer leaves a visible `EDMC Modern Overlay` managed PyQt window actor while Elite borderless/fullscreen is active.
- 2026-05-16 focus/overview instability report: after logging out/in and retesting with `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`, EDMC still did not shut down cleanly, the proof remained visible, and GNOME Shell Alt-Tab/Super overview behavior became inconsistent while EDMC was running. Immediate cleanup commands cleared both the `shell_raster_frame` actor and the Phase 10 `shell_actor_proof` actor, and `pgrep` found no remaining EDMC/overlay-client process. This means the persistent Phase 12 runtime path is too risky to leave behind the single bridge flag; the static proof remains valid, but persistent runtime presentation must move behind an additional explicit dev gate until Phase 13 lifecycle/focus hardening.
- Phase 12.13 intended touch points:
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: require a second explicit runtime gate before replacing normal PyQt presentation requests with Shell raster frame updates.
- `overlay_client/tests/test_gnome_helper_presentation_runtime.py`: update gate coverage so `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` alone preserves the PyQt path, and only the bridge flag plus the explicit runtime flag sends the static Shell raster frame.
- `docs/refactoring/gnome_wayland_presentation_attachment.md`: record the manual failure, gate decision, and retest instructions.
- Test type selection: unit tests for backend runtime gate behavior; no helper JS, generic follow/runtime, or harness changes expected. Manual GNOME validation remains required before any persistent runtime can be promoted beyond the extra dev gate.
- Phase 12.13 implementation result:
- Added `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1` as a second explicit dev gate for backend-driven Shell raster frame updates.
- Preserved shutdown/clear cleanup under the original `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` gate so stale actors can still be cleared during plugin or overlay-client shutdown.
- Updated runtime tests so the bridge flag alone keeps the existing PyQt path, while bridge plus runtime flags sends the static Shell raster frame.
- Phase 12.13 validation commands and outcomes:
- `python3 -m py_compile overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py`: 43 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_launcher_shell_raster_shutdown.py tests/test_harness_plugin_hooks_contract.py overlay_client/tests/test_backend_architecture_boundary.py`: 7 passed.
- `git diff --check`: passed.
- `make check`: ruff passed, mypy passed, full pytest passed with 1052 passed and 21 skipped.
- Manual retest expectation:
- Launching EDMC with only `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` should not show the Shell raster proof and should not affect Alt-Tab/Super overview behavior.
- Do not use `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1` for normal testing. That flag is now a dangerous proof-only runtime gate until Phase 13 hardens focus, overview, stale actor cleanup, and shutdown behavior.
- 2026-05-16 manual retest result: launching EDMC with `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` and without `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1` showed no proof actor, Alt-Tab and Super overview worked normally, and EDMC shut down cleanly. This confirms Phase 12.13 mitigates the focus/overview/shutdown regression by disabling persistent Shell raster runtime under the single bridge flag.
- Phase 12 closeout:
- Phase 12 is complete as a small proof: PyQt can generate a transparent PNG, GNOME Shell can present it through `target_window_actor_child` above active Elite borderless fullscreen, the actor can appear at true monitor bounds without the `y=29` work-area offset, and click-through was manually confirmed with the enlarged proof frame.
- Phase 12 does not close as production-ready persistent runtime. Persistent Shell raster updates exposed focus/overview/shutdown risks, so that work is explicitly deferred to Phase 13.
- The safe Phase 12 exit state is: `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` alone does not show the proof actor and does not affect Alt-Tab, Super overview, or EDMC shutdown; `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1` remains proof-only and unsafe for normal use until Phase 13.

#### Phase 12 Touch Points
- `helpers/gnome_shell_extension/extension.js` or a helper-local module if the extension is split: Shell presentation controller, frame actor updates, cleanup, diagnostics.
- `overlay_client/backend/helper_ipc.py`: typed optional frame request/response parsing.
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: GNOME-specific runtime policy for Shell-native presentation eligibility, frame signatures, fallback, and diagnostics.
- `overlay_client/backend/consumers.py` and `overlay_client/follow_surface.py`: only neutral backend presentation calls; no raw GNOME helper protocol checks.
- Existing PyQt rendering paths: touched only where needed to produce the bounded transparent raster frame and to suppress duplicate managed-window visibility for the gated GNOME borderless/fullscreen path.

#### Phase 12 Test Type Selection
- Unit tests are required for frame signatures, eligibility, fallback decisions, response parsing, and no-op suppression.
- Static/source tests are required for helper actor lifecycle, diagnostic gating, non-reactive actor behavior, and normal `ApplyPresentation` preservation.
- Harness tests are required for runtime selection/fallback wiring and any PyQt content-suppression lifecycle.
- Manual GNOME validation can be sampled during Phase 12, but support-gate validation is Phase 13.

#### Phase 12 Manual Validation Plan
- Reload helper with `./scripts/dev_gnome_helper.sh reload --yes` if helper files changed.
- Start EDMC normally with `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`.
- Put Elite in GNOME Wayland windowed-borderless/full-monitor mode.
- Confirm helper target state reports `fullscreen=true` and `contentRect == monitorRect`.
- Trigger one static transparent PyQt-generated PNG test frame or cropped frame update.
- Confirm the frame appears above active Elite via the `target_window_actor_child` path.
- Confirm actor/frame bounds match the requested rect with no `y=29` work-area offset.
- Confirm transparency/no black background.
- Confirm click-through and focus stability.
- Confirm explicit clear removes the frame.
- Confirm stale timeout removes the frame if updates stop.
- Confirm invalid image path and target-token-change failures clear/fail soft and do not leave stale actors.
- Confirm windowed Elite still uses the existing managed PyQt overlay path.

#### Phase 12 Implementation Prompt
```text
Implement Phase 12 of docs/refactoring/gnome_wayland_presentation_attachment.md.

Follow AGENTS.md. Start by reading:
- Phase 10 Manual Validation Evidence
- Phase 10 Target Window Actor Child Candidate Implementation Plan
- Phase 11 Locked Decisions
- Phase 11 Accepted Recommendations
- Phase 11 Frame Protocol Contract
- Phase 11 Controller Boundaries
- Phase 11 Phase 12 Touch Point Handoff
- Phase 12 Manual Validation Plan
- fix219 backend-boundary rules

Before touching code:
- Update Phase 12 stage statuses and record intended touch points plus test type selection.
- Keep support/status wording degraded/experimental.
- Do not claim `true_overlay`.
- Do not implement full overlay parity.
- Do not export or stream real overlay content in the default Phase 12 scope.
- Do not enable Shell raster presentation by default.
- Do not move rendering into GNOME Shell primitives.
- Do not change windowed-mode presentation behavior.

Goal:
Implement a small PyQt PNG raster proof for GNOME Wayland windowed-borderless/full-monitor mode.

This is Phase 12 small production proof only. PyQt remains the renderer. GNOME Shell is only the presentation surface for the borderless/full-monitor case proven by Phase 10.

Locked decisions:
- Runtime activation is off by default behind `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`.
- Scope is GNOME Wayland windowed-borderless/full-monitor only.
- Windowed Elite remains on the existing managed PyQt overlay path.
- The first transport is local PNG files under a controlled EDMC overlay runtime/cache directory.
- The Phase 12 frame source is a static PyQt-generated transparent PNG test frame.
- Prefer cropped frames with `frame_rect` placement metadata.
- Use event-driven updates only.
- Add checksum/no-op suppression before compositor-facing frame update work.
- Start with a conservative `2-5 FPS` maximum update cadence.
- Add byte-size guards and reject arbitrary paths/path traversal.
- Add explicit clear and stale timeout cleanup.
- Visible fail-soft fallback is required.
- All helper request/response fields must be optional and backward-compatible.
- Do not add shared memory, raw buffers, direct texture transfer, high-rate streaming, Shell primitives, real overlay content export by default, non-GNOME support, windowed-mode migration, support wording promotion, or `true_overlay`.

Implementation requirements:

1. Documentation first
- Mark Phase 12.1 in progress and record Phase 12 touch points.
- Record test type selection:
  - unit tests for frame model/signature/path validation/eligibility/fallback decisions
  - static/source tests for helper actor lifecycle, image loading, path validation, stale cleanup, explicit clear, and normal `ApplyPresentation` preservation
  - harness tests if runtime selection or PyQt window suppression is wired
  - backend-boundary tests if backend/follow wiring changes

2. Helper-side Shell raster controller
In `helpers/gnome_shell_extension/extension.js`, or a helper-local module if split:
- Add an isolated Shell raster presentation controller separate from the Phase 10 proof marker code.
- Support optional request fields:
  - `shell_raster_frame`
  - `shell_raster_frame_action`
  - `frame_version`
  - `target_token`
  - `target_rect`
  - `frame_rect`
  - `scale`
  - `image_path`
  - `checksum`
  - `byte_size`
  - `stale_timeout_ms`
- Support actions:
  - `update`
  - `clear`
- For `update`:
  - require strict target eligibility: target exists, `fullscreen=true`, valid `contentRect`, valid `monitorRect`, `contentRect == monitorRect`, target on current workspace, target not minimized
  - validate the frame path is under the allowed EDMC overlay runtime/cache directory
  - reject missing, non-regular, oversized, or undecodable image files
  - attach/update the image actor under the target MetaWindowActor using the proven `target_window_actor_child` path
  - position at `frame_rect`
  - keep the actor non-reactive/click-through oriented
  - refresh stale timeout
- For `clear`:
  - remove the frame actor and stale timer without requiring a valid target or image path
- Preserve the existing `ApplyPresentation` path unless `shell_raster_frame=true` is explicitly requested.

3. Backend-owned frame model and IPC
In backend-owned code under `overlay_client/backend/`:
- Add typed frame request/response models or helpers as needed.
- Add checksum/signature generation and no-op suppression for unchanged target/frame content.
- Add cache-dir/path construction and validation before request construction.
- Add response parsing for frame version, actor bounds, frame dimensions, cleanup action, and degrade reasons.
- Keep GNOME-specific policy behind backend-owned bundle/consumer interfaces.
- Preserve fix219 boundaries:
  - no direct GNOME helper imports in `follow_surface.py`
  - no raw GNOME backend/helper enum dispatch in generic follow/runtime
  - no helper protocol action checks in `follow_surface.py`

4. PyQt PNG proof export
- Add the smallest PyQt-rendered transparent PNG export needed for the proof.
- Use a static/cropped test frame first.
- Do not implement full overlay visual parity.
- Do not export or stream real overlay content unless explicitly scoped as a tiny post-proof slice.
- Do not migrate windowed mode.
- Do not enable high-rate frame streaming.

5. Runtime gate and fallback
- Shell raster path may run only when:
  - `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`
  - GNOME helper mode is active
  - target is windowed-borderless/full-monitor
  - helper capability/protocol supports the optional raster fields
- If validation/load/apply/readback fails:
  - clear/stale the Shell actor
  - keep overlay visible under current policy
  - fall back to the existing degraded PyQt helper path
  - avoid repeated compositor-facing churn for unchanged failures

6. Tests
Add/update tests based on touched files:
- Unit tests for frame model, checksum/signature, cache-dir/path validation, no-op decisions, eligibility, and fallback decisions.
- Static/source tests for helper raster code:
  - opt-in only
  - normal `ApplyPresentation` remains available
  - target-window-actor attachment is used
  - path validation exists
  - image load/decode failure is handled
  - stale timeout exists
  - explicit clear exists
  - actor remains non-reactive/click-through oriented
  - helper disable/reload cleanup exists
- Harness tests if runtime selection or PyQt window suppression is wired.
- Backend-boundary tests if backend/follow wiring changes.

7. Validation commands
Run targeted tests first, based on touched files. Expected baseline:
- `python3 -m py_compile` for touched Python tests/modules
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py`
- relevant backend model/parser/runtime tests
- relevant backend-boundary tests

Then run:
- `make check`
- `git diff --check`

8. Manual validation to leave pending for user
- Reload helper with `./scripts/dev_gnome_helper.sh reload --yes`.
- Start EDMC normally with `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`.
- Put Elite in GNOME Wayland windowed-borderless/full-monitor mode.
- Confirm `fullscreen=true` and `contentRect == monitorRect`.
- Trigger one transparent PyQt-generated PNG frame/cropped frame update.
- Confirm the frame appears above active Elite via `target_window_actor_child`.
- Confirm no `y=29` offset.
- Confirm transparency/no black background.
- Confirm click-through and focus stability.
- Confirm explicit clear.
- Confirm stale timeout.
- Confirm invalid path and stale/changed target token fail soft.
- Confirm windowed mode still uses the existing PyQt overlay path.

After implementation:
- Record files changed.
- Record exact commands and outcomes.
- Keep Phase 13 pending.
- Keep support wording degraded/experimental.
- Do not mark Phase 13 support gates complete.
```

### Phase 13: GNOME Shell-Native PyQt Raster Bridge Lifecycle/Focus Hardening And Support Gate
- Goal: make the Phase 12 Shell raster path safe for persistent runtime before any real overlay content or support promotion work starts.
- Current baseline: Phase 10 proved a Shell actor attached to `target_window_actor_child` can draw above active Elite borderless fullscreen at true monitor bounds. Phase 12 proved a PyQt-generated transparent PNG can be presented through that path with no `y=29` offset and click-through preserved in the manual proof.
- Current blocker: persistent runtime presentation using the Shell raster actor caused GNOME Shell focus/overview instability. Manual evidence showed inconsistent Alt-Tab/Super overview behavior, unreliable shutdown cleanup, and a proof actor persisting until explicitly cleared. Phase 12.13 therefore made `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` safe by itself and moved persistent runtime behind the additional proof-only gate `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1`.
- Phase 13 owns lifecycle/focus safety for the minimal Shell-native PyQt raster path, not full renderer parity. Do not start real overlay content export, high-rate streaming, support wording promotion, or `true_overlay` claims until persistent actor safety passes.
- If Phase 13 proves persistent `target_window_actor_child` actors are not compatible with GNOME Shell overview/window switching, keep the feature proof-only and scope an alternate design before Phase 14.

#### Phase 13 Refactor Staging
| Stage | Description | Status |
| --- | --- | --- |
| 13.1 | Scope lifecycle/focus safety invariants and diagnostics for persistent Shell raster actors, including Alt-Tab/Super overview behavior, shutdown cleanup, target-window child lifetime, and proof-only runtime gates | Completed |
| 13.2 | Add safe actor lease/lifecycle controls: startup clear, clear-before-update, owner/session id or frame generation guard, target token/monitor/workspace/minimize validation, helper reload cleanup, EDMC shutdown cleanup, overlay-client shutdown cleanup, and stale timeout | Headless Implementation Complete; Manual Validation Pending |
| 13.3 | Add GNOME focus/overview safety behavior: detect or conservatively clear/suspend raster actors during overview/window switching/focus transitions, then restore only after the target is valid and focused again | Headless Implementation Complete; Manual Validation Pending |
| 13.4 | Replace persistent proof refresh with a safer runtime mode, starting with one-shot or short-lease frame application before any long-lived actor mode is reconsidered | Headless Implementation Complete; Manual Validation Pending |
| 13.5 | Add observability and no-churn guards for the hardened path: concise normal logs, gated diagnostics, frame version, actor bounds, update skip/apply reasons, cleanup events, no-op suppression, and bounded cadence | Headless Implementation Complete; Manual Validation Pending |
| 13.6 | Run targeted unit/static/harness coverage plus full `make check` after lifecycle/focus hardening | Completed |
| 13.7 | Run manual validation matrix on primary and secondary monitor borderless modes, including Alt-Tab/Super overview responsiveness and clean EDMC shutdown | Manual Validation Failed; 13.7A Planned |
| 13.7A | Prevent managed PyQt fallback remap during Shell raster focus/overview-risk clears so the proof path fails soft without flashing or exposing a managed titlebar | Core Manual Validation Passed |
| 13.7B | Validate Shell raster applied actor bounds against the proof frame rect so inset proof frames do not falsely trigger managed PyQt fallback remap | Core Manual Validation Passed |
| 13.7C | Refresh unchanged Shell raster proof frames before the short helper lease expires while keeping managed PyQt no-op suppression behavior unchanged | Core Manual Validation Passed |
| 13.7D | Honor `keep_overlay_visible=true` for Shell raster focus loss by allowing an unfocused but visible target while preserving overview/workspace safety clears | Core Manual Validation Passed |
| 13.8 | Decide whether the hardened minimal subset is shippable as an opt-in GNOME borderless mode or remains proof-only | Completed; Opt-In Experimental Proof Mode Only |
| 13.9 | Update support/status wording only if all gates pass for the implemented subset; otherwise keep degraded/experimental wording and record remaining blockers | Completed; Keep Degraded/Experimental, No `true_overlay` Claim |

#### Phase 13 Production Hardening Plan
#### Phase 13 Accepted Recommendations
- Runtime style: start Phase 13 with short-lease / one-shot Shell raster frames, not persistent forever actors.
- Actor lifecycle: clear before every new update in the first hardened proof, clear on startup, clear on EDMC shutdown, clear on overlay-client shutdown, clear on target loss, and clear on stale timeout.
- Focus/overview behavior: clear or suspend the Shell raster actor during GNOME overview/window switching/focus-risk transitions, then restore only after Elite is valid again. If reliable overview detection is not available, prefer conservative short leases and clear-on-risk behavior.
- Default flag behavior: `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` remains safe and non-presenting by itself.
- Runtime proof flag behavior: `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1` remains proof-only until Phase 13 passes the lifecycle/focus manual matrix.
- First stale timeout target: start around `1500-2000 ms`, shorter than the Phase 12 `5s` proof timeout.
- First update strategy: prefer clear-before-update over in-place actor mutation until lifecycle safety is proven.
- Phase 13 scope: harden the static PyQt raster proof path only. Real overlay content export, broad renderer parity, high-rate streaming, and support wording promotion remain Phase 14+.
- Phase 13.1 pass criteria: proof appears above Elite, clears on timeout, Alt-Tab works, Super overview works, EDMC shuts down cleanly, and no stale actor remains.
- Phase 13.1 fail criteria: broken Alt-Tab/Super behavior, stuck actor, EDMC shutdown hang, persistent stale actor, wrong target/layer attachment, or any regression to windowed PyQt behavior.

- Starting invariant:
- `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` alone must remain safe and must not show persistent Shell raster actors.
- Persistent runtime remains behind `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1` until Phase 13 proves Alt-Tab, Super overview, stale cleanup, and shutdown safety.
- Phase 13.1 must explicitly decide whether the first hardened runtime proof uses a short lease/one-shot actor instead of a continuously refreshed actor.
- Eligibility:
- Shell-native production path is eligible only for GNOME Wayland helper mode, borderless/fullscreen targets, valid target `contentRect`, `contentRect` matching monitor bounds, current workspace, not minimized, helper protocol/capability support, and an enabled runtime/dev gate until support is promoted.
- Fallback:
- If the Shell-native path is unavailable, fails target validation, fails frame apply, or returns stale/mismatched target token, fallback must leave the overlay visible under the current policy and use the existing degraded PyQt helper path where appropriate.
- Failure must be concise in normal logs and detailed only with diagnostics enabled.
- Lifecycle:
- Clear Shell actors on startup before first update, target loss, target token change, monitor/workspace mismatch, minimize, helper disable/reload, EDMC shutdown, overlay client shutdown, stale frame timeout, and any detected unsafe GNOME overview/window-switching transition.
- A stale frame timeout is required so a crashed client cannot leave a permanent Shell actor on screen.
- Runtime actor ownership must be explicit enough to avoid clearing unrelated proof actors while still cleaning stale EDMC actors after crashes/restarts.
- Clear operations must be idempotent and safe when the helper is unavailable.
- Focus/overview safety:
- Persistent Shell raster actors must not interfere with Alt-Tab, Super overview, window switching, focus return, or EDMC shutdown.
- If GNOME overview/window-switching state cannot be reliably detected from the extension, the first hardened path should conservatively use short actor leases and clear-on-focus-transition behavior instead of a long-lived actor.
- Manual validation must include using Alt-Tab and Super repeatedly while EDMC is running with the runtime gate enabled.
- Performance:
- Do not send frame updates every follow tick if the frame and target signature are unchanged.
- Add frame signatures or versioned no-op suppression before any production runtime mode is enabled.
- Bound update cadence separately from target polling.
- Gate large diagnostics and any raster/frame payload logging behind explicit debug/dev settings.
- Observability:
- Normal logs should show mode, target token, actor visible, requested/applied bounds, frame version, update skipped/applied, and concise reasons.
- Diagnostic logs should include actor parent/layer, target monitor/workspace, scale, content bridge type, frame count/version, frame dimensions, frame bytes, and cleanup events.
- Compatibility:
- The helper protocol must remain backward-compatible. New request/response fields must be optional until a new protocol version is intentionally required.
- The existing PyQt helper presentation path must remain available for windowed mode and as a fallback while Shell-native support is being proven.
- Scope control:
- No real overlay content export, renderer parity, high-rate frame streaming, shared memory, raw buffers, Shell primitives, non-GNOME support, support promotion, or `true_overlay` claim in Phase 13. Those remain Phase 14+ or later after lifecycle/focus safety is proven.

#### Phase 13.1 Implementation Plan
- Started: 2026-05-16.
- Scope: first lifecycle/focus hardening slice for the static PyQt PNG proof only. Keep `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` safe and non-presenting by itself; keep `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1` as the explicit proof-only runtime gate.
- Intended touch points:
- `overlay_client/backend/shell_raster_frame.py`: change the proof lease timeout to `1500 ms`, include a process/session generation component in `frame_version`, and keep static PNG proof generation unchanged otherwise.
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: preserve the two-stage runtime gate and use the short-lease proof request.
- `helpers/gnome_shell_extension/extension.js`: enforce helper-side clear-before-update, track the frame session/generation from `frame_version`, clear on session mismatch, clear/suspend on GNOME overview/focus-risk conditions, and keep explicit/stale/helper-disable cleanup intact.
- `overlay_client/launcher.py`: add startup clear in addition to existing Qt shutdown clear when the bridge flag is set.
- `load.py`: add EDMC plugin startup clear in addition to existing plugin-stop clear when the bridge flag is set.
- Tests: update backend raster frame/unit tests, GNOME helper runtime tests, GNOME extension source/static tests, launcher lifecycle tests, plugin harness lifecycle tests, and backend-boundary tests if generic wiring changes.
- Test type selection:
- Unit tests for backend short lease, session/generation `frame_version`, runtime gate behavior, and fallback/no-op policy.
- Static/source tests for helper clear-before-update, session mismatch cleanup, stale timeout, overview/focus-risk cleanup, and normal `ApplyPresentation` preservation.
- Harness tests for EDMC plugin startup/stop cleanup because `load.py` lifecycle wiring is touched.
- Launcher lifecycle tests for startup/shutdown cleanup because `overlay_client/launcher.py` is touched.
- Manual GNOME validation remains required for Alt-Tab, Super overview, focus, click-through, stale timeout, and clean shutdown behavior.
- Support wording remains degraded/experimental; no `true_overlay` claim.

#### Phase 13.1 Implementation Summary
- Completed headless implementation on 2026-05-16. Manual GNOME validation remains pending, and support/status wording stays degraded/experimental.
- Runtime gates:
- Preserved the two-stage runtime gate. `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` alone remains non-presenting; runtime proof updates still require `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1`.
- The Shell raster runtime remains proof-only and static. No real overlay content export, full renderer parity, high-rate streaming, or default Shell raster runtime was added.
- Backend short lease/session behavior:
- Changed the static raster proof lease to `1500 ms`.
- Added a process/session generation component to the Shell raster `frame_version`, formatted as the Phase 13 static proof version, session id, and checksum digest.
- Kept the existing no-op/signature behavior so unchanged successful frames do not continuously re-enter compositor-facing presentation.
- Helper actor lifecycle:
- The helper now treats Shell raster actors as short-lease actors, with stale-timeout cleanup at the requested lease.
- The helper clears before applying a new raster frame. Decode, dimension, target-actor, eligibility, and path failures clear the existing Shell actor and allow the managed PyQt fallback to remain visible.
- The helper records the session id from `frame_version` and reports `session_id` in the raster diagnostics payload. A new frame from a different session clears with `session_generation_mismatch`.
- Explicit clear, stale timeout, target loss, target token mismatch through replacement, workspace mismatch, minimized target, invalid frame, helper disable/reload, and session mismatch all route through best-effort cleanup.
- Focus/overview safety:
- The helper imports GNOME overview state, clears/suspends raster actors when overview state is active, and connects overview signals to clear existing actors.
- If the target payload reports `hasFocus=false`, the raster actor is cleared and the request degrades with `target_not_focused`, leaving the existing PyQt fallback path available.
- Overview signal handlers are disconnected during helper disable.
- Startup/shutdown cleanup:
- Added overlay-client startup clear and retained overlay-client Qt shutdown clear when the bridge flag is set.
- Added EDMC plugin startup clear and retained plugin-stop clear when the bridge flag is set.
- Clear calls are best-effort, idempotent, and safe if helper DBus is unavailable.
- Backend boundary:
- Generic `follow_surface.py` was not touched. GNOME-specific raster behavior remains behind backend/helper-owned code, preserving the `fix219` boundary.
- Files changed for the Phase 13 slice:
- `docs/refactoring/gnome_wayland_presentation_attachment.md`
- `helpers/gnome_shell_extension/extension.js`
- `load.py`
- `overlay_client/launcher.py`
- `overlay_client/backend/shell_raster_frame.py`
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`
- `overlay_client/tests/test_shell_raster_frame.py`
- `overlay_client/tests/test_gnome_helper_presentation_runtime.py`
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`
- `overlay_client/tests/test_launcher_shell_raster_shutdown.py`
- `tests/test_harness_plugin_hooks_contract.py`
- Test evidence:
- `python3 -m py_compile overlay_client/backend/shell_raster_frame.py overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/launcher.py load.py overlay_client/tests/test_shell_raster_frame.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_launcher_shell_raster_shutdown.py tests/test_harness_plugin_hooks_contract.py`: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_shell_raster_frame.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`: 48 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py`: 25 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_launcher_shell_raster_shutdown.py tests/test_harness_plugin_hooks_contract.py`: 8 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_architecture_boundary.py`: 2 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_setup_surface.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_shell_raster_frame.py overlay_client/tests/test_launcher_shell_raster_shutdown.py tests/test_harness_plugin_hooks_contract.py`: 192 passed, 4 skipped. Skips were existing PyQt-marked setup tests without `PYQT_TESTS=1` in the targeted command.
- `git diff --check`: passed.
- `make check`: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 1057 passed and 21 skipped.
- Manual validation still pending:
- Reload helper with `./scripts/dev_gnome_helper.sh reload --yes`, restart EDMC, and run with both `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` and `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1`.
- Confirm proof appears above active Elite borderless/full-monitor with no `y=29` offset, transparency preserved, and click-through preserved.
- Confirm the proof actor clears after the `1500 ms` lease when not refreshed, Alt-Tab works repeatedly, Super overview works repeatedly, EDMC shuts down cleanly, and no proof actor remains after shutdown.
- Confirm stale target token, target loss, minimize, workspace switch, helper reload/disable, and focus/overview transitions clear/fail soft.
- Confirm launching with only `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` still shows no proof and remains safe.
- Confirm windowed mode still uses the existing managed PyQt path.

#### Phase 13.7 Manual Validation Evidence
- Captured on 2026-05-16 after Phase 13.1 headless implementation.
- Safe single-flag validation with only `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` passed:
- No proof appeared.
- Alt-Tab worked.
- Super overview worked.
- EDMC shut down cleanly.
- There was no proof actor left to remove.
- Runtime proof validation with both bridge gates partially passed:
- `GetTargetState '{}'` returned `status=target_found`, `targetToken=meta:18`, `contentRect={"x":0,"y":0,"width":3440,"height":1440}`, `monitorRect={"x":0,"y":0,"width":3440,"height":1440}`, `fullscreen=true`, `showingOnWorkspace=true`, `minimized=false`, and `hasFocus=false`.
- The proof appeared above active Elite.
- There was no `y=29` offset.
- Transparency was preserved.
- Click-through worked.
- Super overview appeared improved, but the user was not fully confident it is fixed.
- Runtime proof validation failed:
- Alt-Tab did not work in some cases.
- When Alt-Tabbing back to the game, the proof flashed and occasionally exposed a titlebar.
- EDMC shutdown and target-loss/minimize/workspace/helper-reload cases were not completed because the focus/titlebar failure blocked continued validation.
- Interpretation:
- The safe bridge flag remains acceptable.
- The both-gate proof runtime is still not safe enough for persistent validation.
- The flashing/titlebar symptom is consistent with the backend returning to the managed PyQt fallback when the Shell raster helper clears/degrades for focus or overview risk. For borderless Shell raster proof mode, focus/overview-risk clears should remove the Shell actor and fail soft without remapping the managed PyQt top-level.

#### Phase 13.7A Implementation Plan
- Scope: adjust the proof-only Shell raster runtime fallback policy for focus/overview-risk clears.
- Touch point:
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`: when the helper returns Shell raster renderer degradation for `target_not_focused` or `gnome_overview_active`, keep the managed PyQt overlay suppressed instead of treating the degradation as a visible PyQt fallback.
- Tests:
- Add unit coverage proving Shell raster focus/overview-risk degradation clears/suppresses without `should_show_overlay=True`.
- Existing fallback behavior for frame export/build failure should remain visible PyQt fallback.
- Re-run targeted GNOME helper runtime tests and backend-boundary checks.

#### Phase 13.7A Implementation Summary
- Implemented on 2026-05-16.
- Added backend-owned focus/overview-risk fallback suppression for Shell raster proof mode.
- When the Shell raster helper degrades with `target_not_focused` or `gnome_overview_active`, runtime now keeps `should_show_overlay=False` instead of remapping the managed PyQt fallback window.
- Frame export/build failure still keeps visible PyQt fallback behavior, preserving the intended fail-soft path for real raster build/apply failures.
- Generic `follow_surface.py` remains untouched and the `fix219` backend boundary remains preserved.
- Test evidence:
- `python3 -m py_compile overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py`: 45 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_architecture_boundary.py`: 2 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_setup_surface.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_shell_raster_frame.py overlay_client/tests/test_launcher_shell_raster_shutdown.py tests/test_harness_plugin_hooks_contract.py`: 194 passed, 4 skipped. Skips were existing PyQt-marked setup tests without `PYQT_TESTS=1` in the targeted command.
- `git diff --check`: passed.
- `make check`: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 1059 passed and 21 skipped.
- Manual revalidation still pending:
- Rerun both-gate proof validation and specifically retest Alt-Tab back to Elite.
- Expected: Shell proof may clear/suspend on focus risk, but the managed PyQt window should not flash in with a titlebar.
- Continue to require clean EDMC shutdown and no stale actor before advancing Phase 13 support gates.

#### Phase 13.7B Manual Failure Evidence
- Captured on 2026-05-16 after Phase 13.7A headless implementation.
- Runtime still flashed in the both-gate Shell raster proof mode.
- Logs showed the Shell raster proof actor applying the expected inset proof frame, e.g. `applied={'x': 10, 'y': 10, 'width': 3420, 'height': 1420}`, while the backend still compared that applied rect against the full target request `requested={'x': 0, 'y': 0, 'width': 3440, 'height': 1440}`.
- That produced `delta=[10, 10, -20, -20]`, `rect_match=False`, `state=presentation_degraded`, and `reasons=['applied_rect_mismatch']`.
- Because the status was degraded, runtime entered the managed PyQt remap path with `visibility_reason=target_focused_remap_warmup`, logged `primed Qt map geometry`, then logged `Overlay visibility set to visible`. Shortly after, focus-risk degradation hid the PyQt window again. This repeated and exposed the managed window/titlebar flash.
- Interpretation: Phase 13.7A suppressed fallback for explicit focus/overview-risk clears, but a separate false mismatch still caused fallback. Shell raster `rect_match` must validate compositor-applied actor bounds against the raster `frame_rect`, not the full target `content_rect`.

#### Phase 13.7B Implementation Summary
- Implemented on 2026-05-16.
- The helper IPC validator now keeps `requested_rect` as the target presentation rect for diagnostics, but validates Shell raster applied bounds against the expected raster `frame_rect`.
- `rect_delta` and `rect_match` for Shell raster responses now describe actor-frame readback correctness. The real proof-frame case `requested=(0,0,3440,1440)` plus `applied=(10,10,3420,1420)` now matches when the `shell_raster_frame.frame_rect` is `(10,10,3420,1420)`.
- Shell raster proof statuses are still blocked from `true_overlay_ready`, even when the proof frame applies and all compositor gates pass. Phase 13 remains proof-only and degraded/experimental.
- The runtime Shell raster success test now mimics the manual logs by returning an inset `applied_rect` matching the proof `frame_rect`; it asserts the managed PyQt overlay remains suppressed.
- Generic `follow_surface.py` remains untouched and the `fix219` backend boundary remains preserved.
- Test evidence:
- `python3 -m py_compile overlay_client/backend/helper_ipc.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`: 69 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_architecture_boundary.py`: 2 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_setup_surface.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_shell_raster_frame.py overlay_client/tests/test_launcher_shell_raster_shutdown.py tests/test_harness_plugin_hooks_contract.py`: 194 passed, 4 skipped. Skips were existing PyQt-marked setup tests without `PYQT_TESTS=1` in the targeted command.
- `git diff --check`: passed.
- `make check`: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 1059 passed and 21 skipped.
- Manual revalidation still pending:
- Restart EDMC/overlay client because backend Python changed. Helper reload is not required for this backend-only fix unless the helper extension is not already on the Phase 13 code.
- Run both gates again: `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` and `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1`.
- Expected: inset proof-frame applies should no longer produce `applied_rect_mismatch`; `Overlay visibility set to visible/hidden` should not loop for the managed PyQt window; the proof may still clear/suspend on focus/overview risk.
- Continue to require Alt-Tab, Super overview, clean EDMC shutdown, and no stale actor before advancing Phase 13 support gates.

#### Phase 13.7C Manual Failure Evidence
- Captured on 2026-05-16 after Phase 13.7B.
- The false mismatch was fixed: logs showed `applied={'x': 10, 'y': 10, 'width': 3420, 'height': 1420}`, `delta=[0, 0, 0, 0]`, `rect_match=True`, `state=presentation_applied`, and empty `reasons=[]`.
- The proof still disappeared a few seconds after Elite regained focus.
- Runtime then logged repeated skipped cycles with `attempts=0`, `presentation_skipped=True`, and `skip_reason=fresh_matching_presentation`.
- Interpretation: the helper actor uses a short `1500 ms` stale lease, but the backend no-op policy skipped unchanged Shell raster updates indefinitely after a matching apply. That allowed the helper stale timeout to clear the proof actor even though the target and frame signature remained valid.

#### Phase 13.7C Implementation Summary
- Implemented on 2026-05-16.
- Added a Shell-raster-specific lease refresh gate to the backend no-op policy.
- Managed PyQt presentation keeps the Phase 8 event-driven no-op behavior. Only Shell raster `update` requests bypass no-op suppression once enough time has elapsed since the last matching success.
- The initial refresh deadline is half of the helper stale timeout, with a small minimum refresh interval. With the current `1500 ms` proof lease, unchanged frames may skip briefly but should refresh before the helper can clear the actor as stale.
- Added runtime coverage proving an unchanged Shell raster frame skips an early cycle, then refreshes before the short lease expires.
- Test evidence:
- `python3 -m py_compile overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py`: 46 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_setup_surface.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_shell_raster_frame.py overlay_client/tests/test_launcher_shell_raster_shutdown.py tests/test_harness_plugin_hooks_contract.py`: 195 passed, 4 skipped. Skips were existing PyQt-marked setup tests without `PYQT_TESTS=1` in the targeted command.
- `git diff --check`: passed.
- `make check`: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 1060 passed and 21 skipped.
- Manual revalidation on 2026-05-16:
- The proof stayed visible for at least 20 seconds after Elite gained focus.
- A focused log sample showed `state=presentation_applied`, `rect_match=True`, `delta=[0, 0, 0, 0]`, `applied={'x': 10, 'y': 10, 'width': 3420, 'height': 1420}`, and empty `reasons=[]`.
- Runtime showed the intended short-lease cadence: `attempts=1` refresh, then `attempts=0` with `presentation_skipped=True` and `skip_reason=fresh_matching_presentation`, then another `attempts=1` refresh before the proof disappeared.
- Alt-Tab worked reliably.
- Alt-Tab back to Elite returned cleanly, without flashing a titlebar or managed PyQt fallback window.
- Super overview opened normally.
- Returning from Super overview to Elite recovered cleanly.
- Click-through through the proof area worked.
- EDMC shut down cleanly and the proof disappeared.
- Follow-up managed PyQt suppression validation passed on 2026-05-16. During two Alt-Tab away/back cycles, logs showed clean Shell raster applies with `rect_match=True`, no `applied_rect_mismatch`, no `Overlay visibility` lines, no `primed Qt map geometry`, no `target_focused_remap_warmup`, and no `presentation_warmup` lines after Shell raster success. The user observed no titlebar or flashing.
- Target loss/relaunch validation passed on 2026-05-16. Exiting Elite cleared the proof, EDMC stayed running, relaunching Elite restored the proof, and logs showed clean reacquire on `token=meta:105`. The user reported no stale proof, titlebar, or managed PyQt flash during exit/relaunch.
- Secondary-monitor validation passed on 2026-05-16 after manually moving Elite to the second monitor. The same previously validated proof behavior passed on that monitor: correct proof placement over Elite, no `y=29` offset, no titlebar/managed PyQt flash, click-through, Alt-Tab/Super behavior, and shutdown cleanup. Caveat: Elite starts on the primary monitor in this environment, so this validates runtime behavior after manual move rather than startup monitor selection.
- Helper disable/enable validation passed on 2026-05-16 using `./scripts/dev_gnome_helper.sh disable --yes`, `sleep 3`, `./scripts/dev_gnome_helper.sh enable --yes`, and `status`. Runtime logged `target=helper_unhealthy` with `reasons=['missing_service']` while the helper was disabled, then recovered after enable with target sequence reset to `1` and returned to `state=presentation_applied`, `rect_match=True`, `delta=[0, 0, 0, 0]`, and empty `reasons=[]` for `token=meta:107`. No `Overlay visibility`, remap, or `applied_rect_mismatch` lines appeared in the supplied reload capture. The user confirmed the proof visibly disappeared while the helper was disabled, so no stale proof remained during the disabled interval.
- Workspace validation passed on 2026-05-16. User reported matrix checks 1 through 6 passed, and the workspace return case had no titlebar and no flashing.
- Keep-visible validation failed on 2026-05-16. With `Keep overlay visible when Elite Dangerous is not the foreground window` set to true, the Shell raster proof disappeared when the game lost focus. This is the first explicit Phase 13 test of the keep-visible preference against the Shell raster focus-risk path.
- Interpretation: Phase 13.7C stabilized the short-lease proof path for normal focus return, workspace switching, helper disable/enable, target relaunch, and managed PyQt suppression. The remaining bug is preference plumbing: Shell raster focus-risk handling still treats `target_not_focused` as a hard clear even when `keep_overlay_visible=true`. `gnome_overview_active`, off-workspace, minimized, helper-unhealthy, and target-loss clears must remain hard safety gates.

#### Phase 13.7D Implementation Summary
- Implemented headless on 2026-05-16. Manual GNOME revalidation remains pending, and support/status wording stays degraded/experimental.
- Backend/runtime preference plumbing:
- `overlay_client/follow_surface.py` now passes the current `_keep_overlay_visible` setting into the backend-owned presentation consumer.
- `overlay_client/backend/consumers.py` carries the neutral `keep_overlay_visible` argument into the GNOME presentation runner without exposing GNOME helper implementation details to generic follow/runtime code.
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py` maps `keep_overlay_visible=true` to a Shell-raster request flag named `allow_unfocused_target`.
- Shell raster request/protocol behavior:
- `HelperRasterFrameRequest` now includes optional `allow_unfocused_target`, emits it in the helper payload, and includes it in the request signature so toggling the preference forces a fresh helper apply instead of reusing a stale no-op decision.
- `helpers/gnome_shell_extension/extension.js` accepts `allow_unfocused_target` / `allowUnfocusedTarget`. When true, an unfocused target no longer triggers `target_not_focused` cleanup for Shell raster frames.
- GNOME overview remains a hard safety clear. The new flag does not bypass `gnome_overview_active`, target loss, off-workspace, minimized, helper disable, invalid frame, or stale/session cleanup.
- Helper diagnostics now preserve `allow_unfocused_target` in the Shell raster payload so opt-in captures can distinguish keep-visible focus behavior from normal focus-risk clears.
- Test type selection:
- Unit/runtime tests cover deterministic backend policy: keep-visible propagation, unfocused Shell raster apply, request signature invalidation when the preference toggles, and the default `keep_overlay_visible=false` focus-risk clear.
- Static/source tests cover the helper-side optional request field and focus-risk guard because there is no JS runtime seam in headless tests.
- Existing parser/model tests cover request payload emission and response payload preservation.
- No new harness test was required because `load.py` orchestration, plugin startup/shutdown, and EDMC hook wiring were not touched in this slice.
- Files changed for Phase 13.7D:
- `helpers/gnome_shell_extension/extension.js`
- `overlay_client/backend/helper_ipc.py`
- `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`
- `overlay_client/backend/consumers.py`
- `overlay_client/follow_surface.py`
- `overlay_client/tests/test_gnome_helper_presentation_runtime.py`
- `overlay_client/tests/test_backend_consumers.py`
- `overlay_client/tests/test_follow_surface_mixin.py`
- `overlay_client/tests/test_gnome_shell_helper_extension_source.py`
- `overlay_client/tests/test_gnome_shell_helper_presentation_state.py`
- `overlay_client/tests/test_shell_raster_frame.py`
- Test evidence:
- `python3 -m py_compile overlay_client/backend/helper_ipc.py overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/backend/consumers.py overlay_client/follow_surface.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_shell_raster_frame.py`: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_shell_raster_frame.py`: 146 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_platform_controller_backend_status.py overlay_client/tests/test_setup_surface.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_shell_raster_frame.py overlay_client/tests/test_launcher_shell_raster_shutdown.py tests/test_harness_plugin_hooks_contract.py`: 197 passed, 4 skipped. Skips were existing PyQt-marked setup tests without `PYQT_TESTS=1` in the targeted command.
- `git diff --check`: passed.
- `make check`: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 1062 passed and 21 skipped.
- Manual revalidation pending:
- Reload helper with `./scripts/dev_gnome_helper.sh reload --yes` because `helpers/gnome_shell_extension/extension.js` changed.
- Restart EDMC/overlay client because backend Python changed.
- Launch with both `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` and `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1`.
- Set `Keep overlay visible when Elite Dangerous is not the foreground window` to true.
- With Elite borderless/full-monitor and visible on the current workspace, Alt-Tab to another window. Expected: the Shell raster proof remains visible and attached; logs should not degrade with `target_not_focused`; no managed PyQt titlebar or flash appears.
- Press Super / enter GNOME overview. Expected: the proof clears or suspends for `gnome_overview_active` and returns cleanly after Elite is valid again.
- Set `Keep overlay visible when Elite Dangerous is not the foreground window` back to false and repeat a focus-loss cycle. Expected: existing Phase 13.7C behavior remains: no managed PyQt flash/titlebar, and the proof may clear or suppress while Elite is not foreground.
- Keep workspace/off-workspace, minimize, target exit/relaunch, helper disable/enable, and shutdown safety gates in the Phase 13 matrix until rechecked after this helper/backend change.
- Manual revalidation on 2026-05-16:
- Keep-visible true focus loss passed. The Shell raster proof remained visible when Elite lost focus.
- Super overview passed. Overview cleared/suspended and recovered cleanly.
- Keep-visible false focus loss/return passed. No managed PyQt titlebar or flash was observed.
- Minimize/unminimize was skipped because Elite could not be minimized/maximized in the tested mode.
- Borderless resolution changes passed. The proof updated correctly while Elite remained borderless/full-monitor.
- Switching from borderless to windowed cleared the Shell raster proof as expected, but the managed PyQt/windowed overlay did not appear correctly sized to the game window. This needs separate windowed fallback classification because Phase 13 Shell raster mode is intentionally borderless/full-monitor only.
- Follow-up evidence for the borderless-to-windowed switch:
- Runtime logs immediately before the switch still showed the borderless Shell raster path with `targetToken=meta:21`, `fullscreen` implied by `content_rect`, `frame_rect={"x":0,"y":0,"width":3440,"height":1440}`, `rect_source=content_rect`, `applied={"x":10,"y":10,"width":3420,"height":1420}`, `rect_match=True`, `renderer=gnome_shell_raster_frame`, `keep_overlay_visible=True`, and managed PyQt hidden.
- No new `GNOME helper presentation` log appeared in the supplied capture when switching from borderless to windowed, even though a direct helper query immediately afterward returned `fullscreen=false`, `contentRect=null`, and `frameRect={"x":920,"y":283,"width":1600,"height":937}` for the same `targetToken=meta:21`.
- Interpretation: the Shell helper correctly sees the windowed target and the raster proof correctly becomes ineligible. The suspicious part is the runtime/fallback transition: the overlay client should log a new frame-rect-fallback presentation cycle and prime the managed PyQt window to the helper `frameRect`. If no runtime cycle appears, or if the PyQt surface remains at the prior borderless/fullscreen size after becoming visible, treat this as a Phase 13 fallback transition regression until proven otherwise.
- Follow-up classification: when EDMC starts while Elite is already windowed, the managed PyQt overlay is correctly sized and follows the game window. This means the windowed sizing/follow path still works on a clean windowed startup. The bad sizing is therefore specific to the borderless-to-windowed transition/state reset, not a general windowed sizing regression.
- Remaining windowed behavior issue: in windowed GNOME Wayland mode, the managed PyQt overlay still behaves like a standalone/top-level app even when `standalone_mode=false`, and the titlebar compensation setting has no visible effect. This is not fixed by Phase 13 because Shell raster mode is borderless/full-monitor only. It remains a separate chrome/standalone/windowed fallback issue, also constrained by the helper reporting `contentRect=null` and `decorationInsets=null` for windowed Elite.
- Deferred follow-ups to avoid losing track:
- `Phase 13.F1`: after the Phase 13 borderless/fullscreen support decision, fix the borderless-to-windowed fallback transition. Expected fix shape: when the target changes from Shell-raster-eligible `fullscreen=true/content_rect` to windowed `fullscreen=false/frame_rect_fallback`, explicitly clear Shell raster state and reset the managed PyQt surface out of fullscreen/hidden-suppressed mode before showing the fallback. This is deferred because clean windowed startup works and the current Phase 13 decision should stay focused on borderless/fullscreen.
- `Phase 13.F2`: after `13.F1`, revisit the older GNOME windowed managed-PyQt chrome/standalone limitation. Normal overlay mode still appears standalone-like in windowed GNOME Wayland, and titlebar compensation cannot be validated while the helper reports `contentRect=null` and `decorationInsets=null`.
- EDMC shutdown passed cleanly.
- Safe single-flag validation passed again after Phase 13.7D. Launching with `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` and without `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1` showed no proof actor, Alt-Tab/Super behaved normally, and shutdown was clean.
- Idle churn/performance sanity passed on 2026-05-16 with `keep_overlay_visible=true`. The proof remained visible and stable for the sampled idle window. Logs alternated between bounded refreshes (`attempts=1`) and no-op skips (`attempts=0`, `presentation_skipped=True`, `skip_reason=fresh_matching_presentation`) while keeping `state=presentation_applied`, `rect_match=True`, `delta=[0,0,0,0]`, and empty `reasons=[]`. No `applied_rect_mismatch`, repeated `presentation_degraded`, or managed `Overlay visibility` loop appeared in the supplied sample.

#### Phase 13.8 Decision
- Decided on 2026-05-16.
- Lifecycle/focus safety for the Phase 13 borderless/fullscreen Shell raster proof path is accepted as passed for the tested GNOME Wayland environment.
- Support status remains opt-in experimental/proof mode only. Do not promote this to normal GNOME support, do not claim `true_overlay`, and do not remove the explicit runtime proof gate yet.
- Reason: the hardened path is still a static PyQt raster proof frame, not real overlay content/parity. Phase 14 owns real overlay raster export, parity, transfer/performance work, and any future support wording promotion.
- Deferred issues `Phase 13.F1` and `Phase 13.F2` are tracked and do not block the Phase 13 borderless/fullscreen decision. They must be resolved before release/support promotion that involves windowed fallback behavior.
- Phase 14 is unblocked for planning.

#### Phase 13 Production Validation Matrix
1. Borderless fullscreen on primary monitor: actor appears at full-monitor bounds, no `y=29` offset, no titlebar, no Alt-Tab/taskbar entry.
2. Borderless fullscreen on secondary monitor: actor follows target monitor and stays above Elite.
3. Click-through: pointer/keyboard focus remains with Elite when interacting through the overlay area.
4. Focus loss/return: mapped-visible/mapped-suppressed behavior remains stable and does not flash.
5. GNOME Shell controls: Alt-Tab and Super overview remain responsive and accurate while EDMC is running with the runtime proof gate enabled.
6. Target loss/relaunch: actor clears on loss and reacquires only for the new target token.
7. Workspace switch: actor hides or clears when Elite is not on the current workspace and returns cleanly when appropriate.
8. Minimize/unminimize: actor hides on minimize and restores only after target state is valid.
9. Resolution/mode change: actor updates bounds after borderless resolution changes and does not leave stale geometry.
10. Helper reload/disable: actor is removed and runtime falls back visibly without hanging.
11. EDMC shutdown/crash simulation: actor clears by explicit shutdown or stale-frame timeout.
12. Safe bridge flag: `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` without `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1` shows no proof actor and keeps EDMC shutdown plus GNOME Shell controls normal.
13. Performance: no recurring compositor-visible placement churn for unchanged target/frame; GNOME Shell responsiveness remains acceptable.
14. Regression: windowed `frame_rect_fallback`, Phase 6A mapped suppression, Phase 6B clamp, Phase 8 no-op suppression, and Phase 9.9A churn guard still pass.

### Phase 14: GNOME Shell-Native PyQt Raster Parity And Performance Expansion
- Status: Completed on 2026-05-17; Phase 14.7 handoff is ready for Phase 15 support-gate review.
- Goal: expand the Shell-native PyQt raster bridge from the hardened minimal subset toward current overlay visual/functionality parity while keeping PyQt as the renderer.
- Phase 14 starts after Phase 13's lifecycle/focus decision. Phase 13 kept the current implementation opt-in experimental/proof-only, so Phase 14 must plan real overlay parity and production-readiness gates before any support promotion.
- Phase 14 scope depends on the Phase 12 raster subset and Phase 13 performance evidence.
- Raster bridge path: harden frame generation, transfer mechanism, texture lifetime, cropping/damage strategy, update cadence, memory limits, and stale-frame cleanup.
- If Phase 13 proves raster transfer is too expensive for some content, Phase 14 may split additional sub-phases for transfer optimization or a narrowly justified hybrid optimization. Do not reintroduce Shell primitives as the primary renderer without a new explicit decision.
- Phase 14 may need multiple sub-phases. Do not force all renderer parity into one patch if the bridge choice makes that large or risky.

#### Phase 14 Accepted Planning Decisions
- First real-content slice: target BGS-Tally first, then use EDMC-LogEventMiner as the second representative validation source before attempting broad parity.
- Initial parity target includes text with correct font, lines, colors, transparency/alpha, opacity, scaling, transforms, payload updates, group visibility, and any other visual state required to match current overlay behavior.
- Updates must be event-driven. Do not drive content changes from a polling repaint loop. Lease/health refreshes may continue only when they are no-op suppressed and do not create compositor-visible churn.
- Real content must use cropped raster frames around the changed overlay content. Full-monitor or near-fullscreen frames are allowed for proof/debug cases only.
- Transparency and click-through are mandatory before any real-content slice is considered successful.
- Fallback behavior must stay conservative: Shell-raster failures clear the Shell actor and return to the visible PyQt fallback without managed-PyQt titlebar flash during focus, overview, or helper transitions.
- Debug diagnostics should include frame dimensions, byte size, checksum or equivalent identity, encode/decode/apply timing, update reason, skip reason, apply result, cadence, and dropped/throttled frame counts. Keep this debug-gated.
- Keep both Phase 13 environment gates through Phase 14. Do not add UI/settings exposure or support wording until Phase 15.

#### Phase 14 Transfer And Performance Decision Notes
- A PNG path under `$XDG_RUNTIME_DIR` would normally avoid persistent disk because that directory is memory-backed on GNOME/Linux systems, but it still uses filesystem semantics and still pays encode/decode/open/read/update overhead.
- Because Phase 13 proof mode already shows jerky movement/pauses on the test machine, Phase 14 must not assume filesystem transport is acceptable for real overlay content.
- Measure the current PNG/tmpfs proof path first, then decide whether to switch transport before expanding parity.
- Preferred no-filesystem transport candidate 1: DBus Unix FD passing with `memfd` or an equivalent anonymous in-memory file descriptor carrying encoded PNG or raw RGBA bytes.
- Preferred no-filesystem transport candidate 2: AF_UNIX local socket stream for frame bytes if FD passing is not practical from GJS/Gio.
- Preferred no-filesystem transport candidate 3: shared-memory/raw buffer transport only if simpler encoded transfer cannot meet performance or responsiveness targets.
- Starting performance targets are conservative until measured: no compositor-visible churn for unchanged frames, no repeated `presentation_degraded` retries while stable, no `Overlay visibility` loop, no `applied_rect_mismatch` churn, and no visible GNOME Shell responsiveness loss.
- First real-content slice should start at a low event-driven content rate, provisionally no more than 2 content frames per second unless a real overlay event requires a burst. Increase only after timing and manual responsiveness are acceptable.
- Record encode time, transfer time where observable, helper decode/apply time, frame dimensions, byte count, and skip/throttle decisions for each performance test.

#### Phase 14 Performance Contingency Path
- Current decision: keep PNG files under the runtime/tmpfs cache for the Phase 15 support-gate review. Multi-region cropping, helper-side unchanged-region reuse, client-side region reuse, and all-region payload reuse are working. No-filesystem transport remains a contingency path only.
- Performance trigger: reopen transport work if changed real-content frames cause visible game/GNOME Shell pauses, if helper decode/apply or Python build time regularly exceeds the manual responsiveness budget, if byte size grows back toward full-monitor frames, or if broader Phase 15/release validation shows update cadence problems.
- Contingency sequence:
  1. First reduce bytes/work in the existing model: tighten dirty-region detection, avoid repainting unchanged regions, lower burst cadence with latest-frame coalescing, and keep stale-frame dropping rather than queuing. Phase 14.6.10 reuses client-side cached PNG metadata for unchanged regions before QImage painting, PNG save, and checksum work. Phase 14.6.11 adds an all-region payload reuse/no-op diagnostics path so fully unchanged frames do not rebuild large contributor diagnostics or report stale helper decode status.
  2. If PNG encode/decode/open/read remains the bottleneck, spike DBus Unix FD passing with `memfd` or an equivalent anonymous in-memory descriptor. Keep the same region/payload contract so the change is transport-only where possible.
  3. If FD passing is not practical from GJS/Gio, spike an AF_UNIX local socket frame stream for region bytes.
  4. Only if encoded transfer remains too expensive, evaluate shared-memory/raw RGBA buffers, with explicit lifecycle/cleanup tests because that path has the highest resource-management risk.
- Contingency guardrails: preserve both Shell raster environment gates, preserve the backend-owned presentation boundary, keep default managed PyQt behavior unchanged, and require focused tests plus manual GNOME validation before replacing PNG/tmpfs.

#### Phase 14 Refactor Staging
| Stage | Description | Status |
| --- | --- | --- |
| 14.1 | Inventory current overlay visual/features against BGS-Tally first, then EDMC-LogEventMiner, plus the Phase 12 supported Shell-native subset | Completed |
| 14.2 | Measure the current PNG/tmpfs proof path and decide whether the first real-content slice needs no-filesystem transport first | Completed |
| 14.3 | Split raster parity and performance work into independently testable cropped-frame slices based on the Phase 12/13/14.2 evidence | Completed |
| 14.4 | Implement the first real-content parity slice behind the existing Shell-native gates | Completed |
| 14.5 | Tighten real-content Shell raster crop bounds and add crop contributor diagnostics | Completed |
| 14.6 | Repeat parity slices until the supported GNOME Shell-native overlay feature set is explicitly complete or remaining gaps are documented | Completed; Manual Validation Passed |
| 14.7 | Hand off real-content parity/performance evidence, remaining gaps, and support blockers to Phase 15 | Completed |

#### Phase 14.1 Inventory Results
- Status: Completed on 2026-05-16.
- Test type decision: read-only inventory; no tests required for the inventory itself. Follow-up instrumentation uses unit/static tests because it touches pure frame-building helpers, helper IPC payload shape, backend diagnostic payloads, and static GNOME extension source contracts. No `load.py` or EDMC hook lifecycle paths were changed, so no harness test is required for this slice.
- BGS-Tally is the first real-content target. Its overlay path exercises ModernOverlay message lines plus shape payloads: text with plugin-defined sizes and colors, title/highlight colors, TTL, fit-to-text sizing, grouped frame/background rectangles, indicator rectangles, progress-bar segments, and centered/right/bottom anchoring through group placement.
- EDMC-LogEventMiner is the second validation target. It exercises group backgrounds with alpha, event/status text lines, font-size tokens, per-line alpha fade, animated Y-offset movement, and higher-frequency redraw behavior. It should validate performance/cadence after BGS-Tally parity is grounded.
- Phase 12/13 Shell-native subset remains a static cropped PNG proof frame under strict borderless/full-monitor eligibility, attached to the target window actor, with clear/stale-timeout/fallback safety. It is still proof-only and still gated by both `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` and `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1`.

#### Phase 14.2 Measurement Instrumentation
- Status: Completed on 2026-05-16.
- Added debug-gated client-side metrics for the current PNG/tmpfs proof path: frame dimensions, byte count, checksum prefix, transport identity, update reason, encode time, validation time, checksum time, total build time, cache hit, transfer observability, and dropped/throttled counters.
- Added helper-side timing diagnostics in the GNOME Shell extension for raster decode, actor apply, and total helper handling time. These are reported in the `shell_raster_frame.diagnostics` status payload when request diagnostics are present.
- Added backend logging of `shell_raster_metrics` only when presentation diagnostics are enabled, so release/no-diagnostics paths stay quiet and unchanged frames continue to be no-op suppressed by the existing presentation signature path.
- Added in-process static proof frame reuse so unchanged proof frames do not repeatedly invoke the PyQt PNG writer or checksum path. This is not the final real-content cache strategy; it exists to make Phase 14.2 measurement less noisy.
- First live measurement evidence from 2026-05-16: stable proof frames reported client-side cached PNG work as cheap (`cache_hit=True`, `encode_ms=0`, `checksum_ms=0`, and `build_ms` generally below 1 ms), while helper-side PNG decode was repeatedly expensive at roughly `65-96 ms`. Helper apply was cheap at roughly `0.06-0.17 ms`. This identifies helper-side unchanged-frame decode/replacement as the immediate bottleneck, not Python-side proof generation.
- Added a helper-side same-frame reuse fast path before PNG decode/replacement. If the existing Shell raster actor already matches `frameVersion`, `checksum`, `imagePath`, `byteSize`, `targetToken`, `targetRect`, `frameRect`, and parent target actor, the helper now refreshes the stale timeout, shows/raises the existing actor, and reports `helper_reused_frame=true`, `helper_decode_skipped=true`, `helper_decode_ms=0`, and `helper_update_reason="reused_existing_frame"` instead of reloading the PNG.
- Post-reuse live measurement from 2026-05-16: first apply decoded normally (`helper_decode_ms=94.964`, `helper_reused_frame=false`, `helper_update_reason="decoded_new_frame"`), then repeated stable proof frames reused the existing actor with `helper_reused_frame=true`, `helper_decode_skipped=true`, `helper_decode_ms=0`, and `helper_update_reason="reused_existing_frame"`. Helper total time for reused frames dropped to roughly `0.15-0.45 ms`, while client-side cached build work remained sub-ms. The same sample showed no `applied_rect_mismatch` or `Overlay visibility` churn. A later `presentation_degraded` with `target_not_focused` was expected because `keep_overlay_visible=false`.
- Transport decision for Phase 14.4: keep PNG/tmpfs for the first narrow BGS-Tally real-content slice. The unchanged-frame decode bottleneck has been removed, and there is not yet measured evidence that filesystem transport blocks the first low-rate cropped-content slice. No-filesystem transport remains a Phase 14 contingency if real-content metrics regress, especially if changed cropped frames show helper decode, transfer, or Shell responsiveness costs that are visible to the user.
- Manual measurement command shape for real-content slices: restart with both Shell raster gates and `EDMC_OVERLAY_GNOME_PRESENTATION_DIAGNOSTICS=1`, then watch for `shell raster metrics` lines in `overlay_client.log` while validating borderless/fullscreen focus, Alt-Tab/Super overview, keep-visible true/false, helper reload/disable, and EDMC shutdown. Stable unchanged content should continue to report `helper_reused_frame=true`, `helper_decode_skipped=true`, and `helper_decode_ms=0`; changed cropped frames may decode, but should stay bounded in dimensions, byte count, and visible responsiveness.

#### Phase 14.3 Cropped Real-Content Slice Plan
- Status: Completed on 2026-05-16.
- Test type decision: Phase 14.3 is a documentation/planning step, so no code tests are required for this step. Phase 14.4 must add unit tests for any pure crop/bounds/frame-export helpers, focused runtime tests for backend/provider wiring, and static GNOME extension tests only if helper source changes.
- First implementation slice remains generic even though BGS-Tally is the first manual validation source. Do not add BGS-Tally-specific branches, payload IDs, or producer heuristics.
- Slice 1: add a backend-owned raster-frame provider seam so the GNOME helper presentation bundle can request either the existing static proof frame or a client-generated cropped overlay-content PNG without generic follow/runtime code importing GNOME-specific implementation directly.
- Slice 2: implement cropped PyQt overlay-content export from the existing render command path. The crop rect must be the union of visible payload/group-background bounds plus a small paint-margin for line widths and antialiasing. Empty payload state falls back to the existing proof/fallback behavior rather than sending a full-monitor transparent frame.
- Slice 3: start with BGS-Tally-compatible primitives already present in the legacy renderer: message text with the configured font, colors/alpha, group backgrounds, rectangles, vector lines/markers/text, global payload opacity, and click-through. Do not attempt broad overlay parity beyond these existing render commands in the first code patch.
- Slice 4: keep updates event-driven. Ingest, purge, override, and geometry changes may produce a new content frame; unchanged content must continue to be no-op/reuse suppressed, and rapid updates should coalesce to the latest frame rather than queue stale frames.
- Slice 5: collect diagnostics for changed real-content frames: crop/global frame rect, frame dimensions, byte count, checksum identity, build/encode/checksum time, helper decode/apply time, update reason, skip/reuse reason, and dropped/throttled counts.
- Slice 6: manually validate with BGS-Tally in borderless/fullscreen first. EDMC-LogEventMiner remains the second validation source after BGS-Tally metrics are acceptable.

#### Phase 14.4 First Real-Content Slice
- Status: Completed on 2026-05-17; manual BGS-Tally validation remains Phase 14.5.
- Test type decision: unit tests were added for pure crop/bounds and real-content frame metadata helpers. Focused runtime tests were added for the backend-owned provider seam and fallback selection. Existing render-surface, paint-command, backend-consumer, and follow-surface focused tests were run. No harness tests were required because `load.py` and EDMC hook/lifecycle wiring were not changed. No static GNOME extension source tests were added because `extension.js` was not changed in this slice.
- Implemented a backend-owned raster-frame provider path. Generic follow-surface code now passes an optional provider through the backend consumer boundary, and the GNOME helper presentation bundle consumes it without generic runtime code importing the GNOME-specific presentation implementation directly.
- Implemented cropped real-content PNG export from the existing PyQt render path. The export uses current legacy render commands and paints into a transparent `QImage` with the painter origin translated to the crop rect, so existing text, colors, alpha, rectangles/backgrounds, vectors, group placement, and global opacity remain owned by the existing renderer.
- Crop behavior: visible payload bounds are unioned in target-local coordinates, expanded by the 8 px crop margin, and clamped to the target/content rect. Empty, invalid, or fully off-target bounds produce no crop and no normal real-content Shell actor.
- Runtime selection: with both Shell raster gates enabled, visible payload content sends `real_content_cropped_overlay` frames through the existing PNG/tmpfs transport. If no visible content exists or export fails, the runtime keeps the managed PyQt fallback path instead of sending a stale or transparent real-content Shell actor.
- Event-driven update path: repaint requests refresh backend presentation while managed PyQt content is suppressed, so ingest/purge/debounced repaint changes can produce a new cropped Shell raster frame without waiting only on geometry polling. Rapid debounced repaint requests still coalesce to the latest frame through the existing repaint timer.
- Static proof behavior is now explicit proof/debug behavior, not the default real-content path. The static raster proof remains available for tests/debug through `EDMC_OVERLAY_GNOME_SHELL_RASTER_PROOF=1` in addition to the two existing Shell raster gates.
- Diagnostics: real-content frame requests report crop/frame dimensions, byte count, checksum prefix, PNG path transport, update reason `real_content_cropped_overlay`, build/encode/validate/checksum timings, and the existing dropped/throttled counters. Helper decode/apply timing and same-frame reuse diagnostics continue to come from the Phase 14.2 helper path.
- Transport decision: PNG/tmpfs is retained for the first real-content slice. This decision must be revisited after BGS-Tally metrics show changed-frame byte size, decode/apply time, and visible responsiveness.
- Remaining gaps/blockers: manual validation with BGS-Tally is still needed; EDMC-LogEventMiner remains the second validation workload. Real-content no-filesystem transport remains pending evidence, and higher-cadence animation/update behavior is not considered proven by this slice.
- Manual validation command shape:
  - Start EDMC with `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1`, `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1`, and `EDMC_OVERLAY_GNOME_PRESENTATION_DIAGNOSTICS=1`.
  - Keep Elite in borderless/fullscreen.
  - Enable BGS-Tally overlay content and watch `shell raster metrics`.
  - Expected: real overlay content appears via Shell raster, stable unchanged content reports `helper_reused_frame=true`, `helper_decode_skipped=true`, and `helper_decode_ms=0`, changed frames remain cropped, managed PyQt stays hidden during successful Shell raster presentation, Alt-Tab/Super remain normal, and EDMC shutdown clears the actor.

#### Phase 14.5 Crop Bounds Tightening And Diagnostics
- Status: Completed on 2026-05-17; manual post-crop metrics are still required before changing the transport decision.
- Test type decision: add unit tests for pure crop/contributor filtering and diagnostics because the change is deterministic local render metadata logic. Add focused runtime/provider tests only if the backend request/status contract changes. No harness tests are required because `load.py`, EDMC hooks, and lifecycle wiring are not touched.
- Triggering evidence from 2026-05-17 manual validation: real-content Shell raster was active and attached correctly (`update_reason="real_content_cropped_overlay"`), moved with Elite between monitors, survived Keep Visible off/on, and reused stable unchanged frames with `helper_decode_ms=0`; however changed real-content frames were nearly full-monitor at roughly `3430x1440`, Python encode/build cost was roughly `190-223 ms`, and changed-frame helper decode was roughly `76-92 ms`.
- Diagnosis: the Phase 14.4 crop used broad translated group bounds. Those bounds can include placement/background extents and can produce near-fullscreen frames even when the actual painted overlay content is much smaller.
- Implementation: Shell raster crops now use actual visible paint command contributors instead of broad group bounds. Message, rectangle, and vector command bounds are evaluated with the same anchor/justification/nudge offsets used by painting. Vector lines with zero height/width remain valid crop contributors, and vector markers/text are included in the estimated paint bounds.
- Contributor filtering: empty text, zero-size rectangles, fully transparent text/rect/background colors, and groups without visible command contributors do not expand the crop. Group backgrounds are included only when they visibly paint for a group that has visible command content.
- Diagnostics: real-content frame diagnostics now include `crop_source`, `content_bounds`, `crop_rect`, `crop_margin_px`, `crop_clamp_rect`, `crop_contributor_count`, `crop_largest_contributors`, and `crop_outlier`. A near-full-target crop reports the largest contributor so manual validation can identify whether the broad frame is caused by real visible content or a remaining bounds bug.
- Transport decision remains unchanged for this stage: keep PNG/tmpfs until post-crop metrics show whether tighter frames make changed-frame encode/decode acceptable.
- Automated evidence: focused Shell raster/render tests passed, `git diff --check` passed, and `make check` passed with ruff, mypy, and the full PyQt-enabled pytest suite (`1084 passed, 21 skipped`).
- Manual validation still needed: rerun BGS-Tally and EDMC-LogEventMiner with both Shell raster gates plus presentation diagnostics, then confirm crop dimensions shrink from the prior `3430x1440` sample unless a diagnostic outlier shows genuine visible content spanning the target.

#### Phase 14.6 Multi-Region Cropped Real-Content Raster
- Status: Completed on 2026-05-17; manual validation passed and evidence handed off through Phase 14.7.
- Test type decision: add unit tests for pure region clustering, cap/merge, and frame identity helpers; add focused runtime tests for the backend-owned provider/payload contract; add static GNOME extension source tests because `helpers/gnome_shell_extension/extension.js` must manage multiple actors. No harness tests are planned because this slice does not touch `load.py`, EDMC hooks, or plugin lifecycle wiring.
- Triggering evidence from 2026-05-17 post-14.5 logs: the corrected single crop accurately reported visible contributors, but BGS-Tally and EDMC-LogEventMiner content were far apart, so one correct union crop still became near-full-monitor (`3435x1440`). Stable unchanged frames reused correctly with `helper_decode_ms=0`, but changed frames remained expensive because the PNG was large.
- Implementation: real-content Shell raster export now clusters visible paint contributors into multiple cropped regions using generic geometry, not plugin-specific branches. Contributors merge when overlapping or within the 8 px cluster distance, and region output is capped at 8 by deterministic nearest/smallest merges. The runtime keeps the existing single-frame/static proof behavior for proof/debug paths.
- GNOME Shell behavior: the helper payload now carries `shell_raster_regions` for multi-region real-content frames. The extension keys actors by stable region id, skips decode for unchanged regions, decodes only changed regions, and clears actors for regions that disappear. Explicit clear, stale timeout, overview safety, disable/reload, and shutdown cleanup remove both single-frame and multi-region actors.
- Diagnostics: multi-region request metrics now report aggregate timings/byte count plus `region_count`, per-region crop/content bounds, per-region contributor counts, per-region largest contributors, per-region checksum/byte/timing data, and merge reasons when the 8-region cap applies. Helper diagnostics include per-region status payloads where observable and aggregate helper timing.
- Gating/default-behavior guarantee: multi-region export is only reachable through the existing GNOME Shell raster provider path, which still requires both `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` and `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1`. Default managed PyQt behavior is unchanged when those gates are absent.
- Transport decision remains unchanged for this stage: keep PNG/tmpfs until post-multi-region metrics show whether smaller changed regions make encode/decode acceptable.
- Automated evidence: focused Shell raster/runtime/extension/render tests passed, the requested focused test set passed, full requested `py_compile` passed, and `make check` passed with ruff, mypy, and the full PyQt-enabled pytest suite (`1095 passed, 21 skipped`).
- Post-multi-region manual evidence from 2026-05-17: after reloading the helper and logging back in, Shell raster real content attached correctly with `update_reason="real_content_multi_region_overlay"`, `region_count=2`, byte size around `8.6 KB`, Python build around `4 ms`, and stable frames using `helper_reused_frame=True`, `helper_decode_skipped=True`, and `helper_decode_ms=0`.
- Keep Visible regression evidence from 2026-05-17: toggling Keep Visible back on could collapse the Shell raster presentation to the managed fallback surface size (`frame_width=62`, `frame_height=185`, `applied={'x': 0, 'y': 0, 'width': 62, 'height': 185}`, `size=46x173px`, `scale_x=0.18`, `scale_y=0.18`). This indicated the real-content export viewport and top-level multi-region frame rect were being contaminated by the tiny hidden Qt surface after remap.
- Keep Visible regression fix: Shell raster real-content export now uses the target/content rect as a scoped render-size override while collecting contributors and painting region PNGs, so legacy render context, viewport mapping, and font scale use the game-sized target instead of the transient managed Qt surface. Multi-region top-level helper presentation geometry now remains the full target rect while each region still carries its cropped `frame_rect`.
- Post-fix manual evidence from 2026-05-17: toggling Keep Visible off/on no longer shrinks or moves the overlay. Logs show `applied={'x': 0, 'y': 0, 'width': 3440, 'height': 1440}` with `frame_width=3440`, `frame_height=1440`, `region_count=3`, and cropped regions around `152x82`, `298x72`, and `207x771`. Stable frames continue to report `helper_reused_frame=True`, `helper_decode_skipped=True`, and `helper_decode_ms=0`. The managed Qt window still reports `size=46x173px`, but this is now informational only because `legacy_geometry=ignored_helper_source_of_truth`.
- Final Phase 14.6 manual validation: user-reported gameplay validation looked good after the Keep Visible regression fix. No further Phase 14.6 code changes are currently justified by the observed behavior.
- Current transport read: keep PNG/tmpfs for the Phase 14.7 evidence handoff. The post-fix multi-region payload is much smaller than the pre-crop full-monitor frame, stable frames skip helper decode, and changed-frame builds around `25-29 ms` with roughly `58 KB` did not produce a reported visual blocker in the latest manual pass. If Phase 15 or broader release validation finds user-visible update pauses, follow the Phase 14 Performance Contingency Path: first reduce changed-region work, then spike `memfd`/DBus FD passing, then AF_UNIX socket transfer, then shared-memory/raw buffers only if the simpler transport changes fail.
- Startup cleanup regression fix: EDMC plugin startup can clear stale GNOME Shell raster actors without importing PyQt-only native Wayland integration. `overlay_client.backend.bundles` now exposes bundle builders lazily, so importing `_gnome_shell_helper_presentation` for cleanup no longer imports `gnome_shell_wayland` and `_linux_window_integration` in the EDMC process.
- High-usage manual evidence from 2026-05-17: with BioScan, BGS-Tally, EDMC-LogEventMiner, NavRoute, and Pioneer visible, multi-region export hit the 8-region cap and produced roughly `113 KB` of PNG data. Helper-side performance was acceptable (`helper_decode_ms` around `0.94-1.4 ms` on changed frames and `0 ms` on reused frames), with no dropped/throttled frames and no `applied_rect_mismatch`, repeated `presentation_degraded`, or `Overlay visibility` loop. The bottleneck moved to client-side PNG generation: changed frames spent roughly `92-94 ms` encoding and `105-107 ms` building, while frames that the helper reused still spent roughly `81-103 ms` in client build/encode work because the client rebuilt unchanged regions before the helper could skip decode.
- Client-side region reuse implementation: each multi-region crop now carries a stable content identity built from region id, crop/content/frame rects, target rect, scale, contributor order/source/plugin/item/group/bounds, command visual content, global payload opacity, font/vector render parameters, and group background visual properties. If a region identity matches the prior export and the cached PNG metadata still matches the file stat, the client reuses the prior image path, checksum, byte size, and frame version without creating a `QImage`, repainting, saving PNG, or recomputing the checksum.
- Diagnostics added for the client-side cache path: aggregate metrics now include `client_reused_region_count` and `client_encoded_region_count`; per-region diagnostics include `client_reused_region` and `client_reuse_skip_reason`. Stable unchanged all-region frames should report all regions reused, zero encoded regions, aggregate `cache_hit=true`, and near-zero aggregate encode/checksum time before helper-side reuse.
- Test type decision for 14.6.10: unit tests cover pure identity/cache invalidation and export behavior; the focused runtime/render/backend/follow/debounce suite remains the regression level because no `load.py`, EDMC hook, or lifecycle wiring changed. Static GNOME extension tests were not required because `extension.js` was not changed in this slice.
- Transport decision after 14.6.10 implementation: keep PNG/tmpfs through the 14.6.11 no-op diagnostics follow-up and final high-usage validation. If changed-region or mixed-update frames later produce visible pauses after unchanged-region encode suppression, continue the Phase 14 Performance Contingency Path with dirty-region cadence tuning before any no-filesystem transport spike.
- Post-cache manual evidence from 2026-05-17: the client-side region cache works. Fully reused high-usage frames reported `client_reused_region_count=8`, `client_encoded_region_count=0`, `encode_ms=0`, and `build_ms` around `11-13 ms`. Mixed updates improved proportionally: one changed region reported roughly `encode_ms=12 ms` and `build_ms=30 ms`, while four changed regions reported roughly `encode_ms=49 ms` and `build_ms=62 ms`. No dropped/throttled frames, `applied_rect_mismatch`, repeated `presentation_degraded`, or `Overlay visibility` loop were observed. Remaining caveat: fully reused frames could still carry stale helper status such as `helper_update_reason="decoded_changed_regions"` because the runtime reused the last helper status when skipping a fresh matching apply.
- Client-side payload reuse/no-op implementation: when every region is reused and the aggregate multi-region payload identity is unchanged, the builder now reuses the prior request metadata and cached region diagnostics instead of rebuilding large contributor diagnostics. It updates only cheap aggregate timing/reuse fields and keeps stable region ids, image paths, checksums, byte sizes, frame versions, target rects, and frame rects. Changed regions, crop/target/frame changes, contributor identity changes, missing regions, or payload identity changes continue through the normal changed-payload path.
- No-op helper diagnostics fix: the backend runtime now synthesizes clear Shell raster status diagnostics when it skips a fresh matching all-region-reused payload. Metrics report `helper_reused_frame=true`, `helper_decode_skipped=true`, `helper_decode_ms=0`, `helper_call_skipped=true`, and `helper_update_reason="client_reused_all_regions"` instead of carrying stale `decoded_changed_regions` from the previous helper call.
- Diagnostics added for 14.6.11: aggregate request metrics now include `client_reused_all_regions`, `client_payload_reused`, `client_payload_reuse_skip_reason`, `helper_call_skipped`, `client_region_build_ms`, `client_region_identity_ms`, `client_payload_assembly_ms`, and `client_diagnostics_assembly_ms`, while preserving the existing per-region encoded/reused counters.
- Test type decision for 14.6.11: unit tests cover pure payload reuse/cache diagnostics and invalidation behavior; focused GNOME helper runtime tests cover the helper-call suppression/status diagnostics contract. No harness tests are required because `load.py`, EDMC hooks, and lifecycle wiring were not changed. Static GNOME extension tests are not required because `extension.js` was not changed.
- Post-no-op manual evidence from 2026-05-17: the all-region payload reuse path works. Stable no-op high-usage frames reported `client_reused_region_count=8`, `client_encoded_region_count=0`, `client_payload_reused=true`, `encode_ms=0`, `build_ms` around `8 ms`, `helper_decode_ms=0`, `helper_total_ms=0`, and `helper_update_reason="client_reused_all_regions"`. Mixed changed frames remained bounded: a 3-encoded/5-reused frame reported `encode_ms=38.754 ms`, `build_ms=49.097 ms`, and helper total `1.323 ms`; a 4-encoded/4-reused frame reported `encode_ms=46.982 ms`, `build_ms=57.564 ms`, and helper total `2.198 ms`.
- Final Phase 14.6 performance validation: no dropped/throttled frames were observed, and recent `applied_rect_mismatch`, repeated `presentation_degraded`, and `Overlay visibility` churn counts were zero. A 5 second CPU sample during the high-usage overlay set showed the EDMC process averaging roughly `10.0%` CPU and the overlay client averaging roughly `12.6%` CPU.
- Final Phase 14 transport decision: keep PNG/tmpfs for Phase 15 review. Changed-region rendering/encoding is now the main remaining cost, but no user-visible pauses were reported in the validated scenario. If changed-region performance becomes visible later, use the Phase 14 Performance Contingency Path and tune dirty-region/cadence behavior before changing transport.

| Stage | Description | Status |
| --- | --- | --- |
| 14.6.1 | Add pure visible-contributor clustering with 8 px adjacency and an 8-region cap | Completed |
| 14.6.2 | Export one transparent PNG per region through the existing PyQt render path | Completed |
| 14.6.3 | Extend the gated helper presentation payload with multi-region metadata while preserving single-frame/static proof behavior | Completed |
| 14.6.4 | Update the GNOME Shell extension to key, reuse, and clear multiple region actors independently | Completed |
| 14.6.5 | Add per-region diagnostics and update focused tests | Completed |
| 14.6.6 | Capture post-multi-region manual metrics before revisiting transport | Completed |
| 14.6.7 | Fix Keep Visible remap regression that collapsed Shell raster export/presentation size to the hidden Qt surface | Completed |
| 14.6.8 | Capture post-Keep-Visible-regression manual metrics before revisiting transport | Completed |
| 14.6.9 | Fix startup Shell raster cleanup import so EDMC does not require PyQt6 for best-effort stale actor clear | Completed |
| 14.6.10 | Reuse unchanged multi-region PNG metadata on the client before repaint/encode/checksum work | Completed |
| 14.6.11 | Reuse unchanged aggregate multi-region payload diagnostics and synthesize no-op helper status for skipped applies | Completed |

#### Phase 14.7 Phase 15 Handoff
- Status: Completed on 2026-05-17.
- Test type decision: documentation-only closeout; no unit or harness tests are required for this stage because no code changed. The required check is `git diff --check`.
- Implemented Shell raster capabilities: gated GNOME Shell raster presentation for borderless/fullscreen Wayland targets, static proof/debug mode, real-content cropped export from the existing PyQt render path, multi-region clustering with 8 px adjacency and an 8-region cap, independent region actors in the Shell helper, helper-side unchanged-region reuse, client-side region PNG metadata reuse, all-region payload reuse, stale actor cleanup, Keep Visible remap safety, helper reload/disable cleanup, EDMC shutdown cleanup, click-through preservation, and conservative fallback to managed PyQt on export/apply failure.
- Performance evidence: high-usage overlays including BioScan, BGS-Tally, EDMC-LogEventMiner, NavRoute, and Pioneer validate the 8-region path. Stable no-op frames now avoid PNG encode and helper decode (`client_payload_reused=true`, `encode_ms=0`, `build_ms≈8 ms`, `helper_decode_ms=0`, `helper_total_ms=0`). Changed frames stay bounded to changed regions, with recent 3-region and 4-region updates measuring roughly `49-58 ms` build time and `1-2 ms` helper total time. No dropped/throttled frames or presentation/visibility churn were observed in the latest validation.
- Transport decision: keep PNG/tmpfs for now. The performance bottleneck moved from full-monitor frames and helper decode to changed-region PyQt render/PNG encode cost. Do not switch to DBus FD, AF_UNIX socket, shared memory, or raw-buffer transport before Phase 15 unless changed-region pauses become visible. If they do, first tune dirty-region/cadence and latest-frame coalescing, then follow the documented no-filesystem transport contingency sequence.
- Known limitations and unsupported status: GNOME Shell raster remains opt-in and experimental. Both `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` and `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1` are still required. Diagnostics remain gated by `EDMC_OVERLAY_GNOME_PRESENTATION_DIAGNOSTICS=1`. No settings UI, release/support wording, default behavior change, or supported-GNOME claim belongs in Phase 14.
- Testing status: focused Shell raster/runtime/render/backend/follow/debounce checks passed during implementation stages. The unrelated `overlay_client/tests/test_exception_scoping.py::test_viewport_state_defaults_ratio_and_logs` full-check blocker was fixed by updating the test stub to match the current `_viewport_state()` render-surface size contract. The latest full `make check` now passes.
- Phase 15 support-gate questions: decide whether this remains environment-gated only, becomes a settings-gated experimental option, or can ever become the preferred GNOME Wayland borderless path; decide support/status wording; decide whether PNG/tmpfs metrics are good enough for any user-facing exposure; decide whether the now-clean `make check` result is sufficient for support-gate review; decide whether Phase 16 fallback cleanup blocks release/support wording.

### Phase 15: Productionization And GNOME Support Gate
- Goal: decide whether any GNOME Wayland Shell raster mode can move from opt-in proof/experimental status toward supported behavior.
- Phase 15 starts only after Phase 14 proves enough real overlay content parity and performance to evaluate user-facing support honestly.
- Do not promote support wording, remove proof gates, or claim `true_overlay` until Phase 15 explicitly passes its support gate.
- Accepted direction so far: use the existing overlay backend selection surface for user exposure, but represent Shell raster as an explicit experimental GNOME Wayland raster mode/backend. Do not silently make the existing GNOME/managed-PyQt backend switch to Shell raster, and do not keep the broken managed-PyQt GNOME Wayland path as a user-facing/default GNOME Wayland option.
- Accepted Phase 15 decisions:
  - Settings selection replaces the two Shell raster runtime environment gates for normal use. Keep `EDMC_OVERLAY_GNOME_PRESENTATION_DIAGNOSTICS=1` or an equivalent debug gate for verbose diagnostics.
  - `Auto` must not silently choose the experimental Shell raster path. Users must explicitly select the GNOME Shell raster mode/backend.
  - If Shell raster fails for GNOME Wayland borderless/fullscreen, clear Shell actors and report degraded/unsupported instead of remapping a broken managed-PyQt or `xwayland-compat` overlay window over the game.
  - Because Phase 15 is targeting a stronger supported option, Phase 16 fallback cleanup is a release/support blocker rather than a post-release cleanup.
  - PNG/tmpfs remains acceptable for Phase 15 unless changed-region updates cause visible pauses; if they do, use the Phase 14 Performance Contingency Path before changing transport.
  - Performance gates: stable unchanged frames must reuse/no-op (`client_payload_reused=true`, `client_encoded_region_count=0`, `encode_ms=0`, `helper_decode_ms=0`), stable fully reused `build_ms` should stay near the current `~8-10 ms` baseline, changed frames must stay region-bounded and normally under the current `~60 ms` high-usage build baseline, no backlog/churn should appear, and manual validation must show no visible pauses/titlebar flashes/stale actors.
  - Backend option name: `GNOME Shell Raster`, labelled/status-qualified as experimental until the support gate passes.
  - Settings location: use the existing backend selector, not a separate checkbox.
  - Config value: add a stable backend value such as `gnome_shell_raster`; do not overload existing `gnome_wayland`, `auto`, or `xwayland_compat` values.
  - Helper missing/unhealthy behavior: report a concise degraded status such as `GNOME Shell helper unavailable`, keep verbose diagnostics debug-gated, and do not remap a managed-PyQt borderless/fullscreen overlay.
  - Windowed/non-borderless behavior: use managed PyQt only after Phase 16 transition cleanup proves raster-to-PyQt fallback works. Until then, report degraded/unsupported for Shell-raster-selected windowed transitions.
  - Support wording after Phase 16: claim support only for tested GNOME Wayland borderless/fullscreen configurations; do not imply all GNOME versions, layouts, or window modes are covered.
  - Final manual matrix: high-usage overlays, primary/secondary monitor, monitor move, Keep Visible toggle, focus loss/return, Alt-Tab/Super overview, helper reload/disable, EDMC shutdown, and borderless/windowed flips in both directions.

#### Phase 15 Refactor Staging
| Stage | Description | Status |
| --- | --- | --- |
| 15.1 | Review Phase 14 parity/performance evidence and classify support blockers | Completed |
| 15.2 | Decide runtime gating/default behavior for GNOME Shell raster mode | Completed |
| 15.3 | Update backend status/support wording, diagnostics, settings UI, and release notes only if support gates pass | Implementation Complete; Keep Experimental Pending Phase 16 |
| 15.4 | Add or update unit/harness/manual validation for any productionization behavior changes | Headless Tests Added; Borderless/Fullscreen Manual Matrix Complete |
| 15.5 | Decide whether Phase 16 fallback cleanup blocks release/support promotion | Completed; Phase 16 Remains Blocking |
| 15.6 | Validate borderless-to-windowed and windowed-to-borderless transitions, including Shell raster to rendered managed-PyQt fallback and back | Pending Phase 16 Cleanup |

#### Phase 15.1 Evidence And Support Gate Classification
- Test type decision: documentation/status review plus focused unit/harness tests for implementation follow-ups. Phase 14 evidence is sufficient to expose a user-selected experimental backend, not sufficient to make it Auto/default or broadly supported.
- Phase 14 evidence accepted for Phase 15: real-content multi-region Shell raster works in GNOME Wayland borderless/fullscreen, high-usage overlays validated, stable no-op frames skip client encode/helper decode, and no recent `applied_rect_mismatch`, `presentation_degraded`, or `Overlay visibility` churn was observed.
- Support blockers retained: Phase 16 fallback cleanup, windowed/non-borderless transitions, helper missing/unhealthy UX, and final manual validation across monitor moves, Keep Visible, focus, overview, helper reload/disable, and shutdown.

#### Phase 15.2 Runtime Gating Decision
- Implemented direction: add an explicit backend/config value `gnome_shell_raster` labelled `GNOME Shell Raster`.
- `Auto` remains conservative and does not select Shell raster.
- Selecting `GNOME Shell Raster` through the existing backend selector enables the Shell raster runtime path without requiring `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` or `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1`.
- Backend selection changes require an EDMC restart before validation or normal use. The selected backend is consumed by startup/runtime wiring, so users should be told to restart EDMC after changing `Overlay backend`.
- Existing environment gates remain as developer/proof compatibility paths. Verbose raster diagnostics remain debug-gated with `EDMC_OVERLAY_GNOME_PRESENTATION_DIAGNOSTICS=1`.

#### Phase 15.3 Headless Implementation Notes
- Added `BackendInstance.GNOME_SHELL_RASTER` and exposed it through backend selector/status/override-option code as `GNOME Shell Raster`.
- GNOME Shell raster is available only as an explicit manual backend option on GNOME Wayland; it is not offered by `Auto` and is not substituted for `gnome_shell_wayland`, `xwayland_compat`, or any non-GNOME backend.
- Runtime presentation now treats selected `gnome_shell_raster` as the production Shell raster gate and suppresses managed-PyQt fallback on Shell raster frame/export failure by sending a clear/degrade helper request instead.
- Startup/shutdown Shell raster cleanup now runs when `gnome_shell_raster` is selected, even without the old bridge environment flag.
- Helper missing/unhealthy remains degraded, with user-facing status routed through existing backend status reporting and verbose detail left in diagnostics.

#### Phase 15.4 Test Coverage
- Added/updated unit tests for backend selection, override options, status labels/warnings, backend consumers, and GNOME helper runtime Shell raster gating/failure behavior.
- Added/updated harness tests for backend override persistence and plugin startup/shutdown Shell raster cleanup when the selected backend is `gnome_shell_raster`.
- Manual validation still required: select `GNOME Shell Raster`, restart EDMC without the two runtime env flags, validate high-usage overlays on GNOME Wayland borderless/fullscreen, move the game between monitors, toggle Keep Visible, test focus/Alt-Tab/Super, helper reload/disable, shutdown cleanup, and borderless/windowed flips.

#### Phase 15 Manual Validation Log
- 2026-05-25, item 1: Passed. With the backend selector on `Auto` and EDMC started without `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE=1` or `EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME=1`, the live runtime status reported `Backend: GNOME Shell helper | Mode: Degraded overlay | Source: Live runtime | Helper: GNOME Shell extension available`, not `GNOME Shell Raster`. This confirms `Auto` does not silently choose Shell raster.
- 2026-05-25, item 2: Passed. After selecting `GNOME Shell Raster` and restarting EDMC without the two Shell raster runtime environment gates, the status reported `Backend: GNOME Shell Raster | Mode: Degraded overlay | Source: Live runtime | Overlay backend: GNOME Shell Raster | Helper: GNOME Shell extension available`. Logs showed `GNOME helper presentation shell raster metrics` with `renderer='gnome_shell_raster_frame'`, `update_reason='real_content_multi_region_overlay'`, `transport='png_path'`, `region_count=2`, `client_encoded_region_count=0`, `client_payload_reused=true`, and `encode_ms=0`. This confirms settings selection alone starts the Shell raster runtime path.
- 2026-05-25, item 3: Passed. With `GNOME Shell Raster` selected and Elite running in borderless/fullscreen, real overlay content appeared over the game. User-visible validation confirmed no titlebar, no separate standalone overlay window, and click-through behavior remained correct.
- 2026-05-25, item 4: Passed. Stable unchanged high-content frame metrics showed `region_count=3`, `client_reused_region_count=3`, `client_encoded_region_count=0`, `client_reused_all_regions=true`, `client_payload_reused=true`, `encode_ms=0`, `checksum_ms=0`, `build_ms≈3.96 ms`, `dropped_frames=0`, and `throttled_frames=0`. Helper-side reuse also worked on the sampled helper call with `helper_reused_frame=true`, `helper_decode_skipped=true`, `helper_decode_ms=0`, and `helper_total_ms≈0.194 ms`. A later `target_not_focused` degraded sample appeared after focus moved away during logging/copying and is not treated as focused-stable churn.
- 2026-05-25, item 5: Passed after rerun. Changed overlay updates stayed region-bounded and within the Phase 15 high-usage baseline during focused presentation. The clean rerun showed 11 changed frames, 10 while `presentation_applied`, `target_focus=True`, and `rect_match=True`; focused changed-frame `build_ms` min/avg/max was `7.079/17.075/27.600`, with `dropped_frames=0` and `throttled_frames=0`. An earlier isolated focused spike reached `build_ms=128.070 ms`, but it did not reproduce and no visible pause was reported.
- 2026-05-25, item 6: Passed. Monitor-follow validation showed Shell raster presentation moving from monitor `0` to monitor `1` and back to monitor `0`, with `presentation_applied`, `target_focus=True`, and `rect_match=True`. Manual validation confirmed overlay content followed the monitor, no stale actors remained on the old monitor, no titlebar or separate PyQt window appeared, and click-through still worked.
- 2026-05-25, item 7: Passed. Keep Visible toggle validation exercised `keep_overlay_visible=True` and `keep_overlay_visible=False`. With Keep Visible on, unfocused samples stayed `presentation_applied`, `reasons=[]`, and `rect_match=True`; with Keep Visible off, unfocused samples degraded cleanly with `reasons=['target_not_focused']`. No `applied_rect_mismatch`, errors, dropped frames, or throttled frames were observed.
- 2026-05-25, item 8: Passed. Focus loss/return validation with Keep Visible off showed repeated clean transitions from `target_focus=False`, `presentation_degraded`, `reasons=['target_not_focused']` back to `target_focus=True`, `presentation_applied`, `reasons=[]`, and `rect_match=True`. No flashing, titlebar, stale actor, separate PyQt window, errors, or frame churn were observed.
- 2026-05-25, item 9: Passed. Alt-Tab and GNOME Super overview validation produced expected `gnome_overview_active` degraded samples and clean recovery to `presentation_applied`, `target_focus=True`, `reasons=[]`, and `rect_match=True`. Manual validation found no overview instability, stale actors, titlebar, separate PyQt window, or focus/input issue.
- 2026-05-25, item 10: Passed. Helper reload/disable validation observed helper interruption as `health=missing_service`, `target=unknown`, `state=not_attempted`, and `visibility_reason=target_unavailable`, then recovered to `health=healthy` and `presentation_applied` with `rect_match=True`. No managed-PyQt fallback window, stale actor, `applied_rect_mismatch`, errors, dropped frames, or throttled frames were observed.
- 2026-05-25, item 11: Passed with diagnostic note. EDMC shutdown cleanup validation confirmed EDMC quit cleanly, the overlay disappeared, no stale actors or windows remained, and `pgrep -af 'overlay_client|EDMCModernOverlay|EDMarketConnector'` returned nothing. The last client log included one hidden `state=malformed_payload` sample with `requested=None`; because `visibility=hidden`, `surface_action=hidden`, and there was no stale visible actor, this is recorded as a shutdown diagnostic note rather than a validation failure.
- Phase 15 borderless/fullscreen manual matrix conclusion: explicit `GNOME Shell Raster` is validated as an experimental GNOME Wayland borderless/fullscreen path. Do not promote it to Auto/default or broad supported GNOME behavior until Phase 16 resolves windowed/fallback cleanup and Phase 17 completes extended hardening.

#### Phase 15.5 Phase 16 Blocker Decision
- Phase 16 remains blocking for stronger support/default promotion. Until Phase 16 proves raster-to-managed-PyQt transition cleanup, selected Shell raster should remain experimental/support-gated and windowed/non-borderless transitions should report degraded/unsupported rather than remapping broken managed PyQt over the game.

#### Phase 15 Managed-PyQt Suppression Notes For Future Gate
- Current behavior: when `GNOME Shell Raster` is selected and Shell raster successfully owns presentation, the managed PyQt overlay top-level is intentionally hidden. The overlay client process remains alive and continues to own state, rendering, export, input policy, and diagnostics, but the visible overlay content is presented by GNOME Shell raster actors rather than by the PyQt window.
- Why this was done: the managed PyQt GNOME Wayland window could appear as a standalone app/window with chrome/titlebar-like behavior. Hiding the PyQt top-level after successful Shell raster presentation removed the user-visible titlebar/standalone-window regression while preserving the client-side render/export pipeline.
- Runtime path to preserve: `overlay_client/follow_surface.py` calls `run_backend_presentation_cycle(...)` before legacy follow geometry. `overlay_client/backend/consumers.py` passes `shell_raster_runtime_enabled=True` and `suppress_pyqt_fallback_on_shell_raster_failure=True` when the selected backend is `BackendInstance.GNOME_SHELL_RASTER`. A successful raster presentation makes `GnomeHelperPresentationCycleResult.should_show_overlay` return `False`, which becomes `presentation_attachable=False` in the backend-neutral visibility snapshot. `overlay_client/backend/presentation_policy.py` then returns `show=False`, `visibility_reason="presentation_not_attachable"`, `surface_action="hidden"`, and `content_visible=False`, and `overlay_client/follow_surface.py` applies that by calling `self.hide()` on the managed PyQt top-level. This hidden state is expected and does not indicate Shell raster failure.
- Failure path to preserve through Phase 16: if Shell raster export/provider/apply fails while `GNOME Shell Raster` is selected, `_shell_raster_bridge_request(...)` builds a degrade/clear request instead of remapping managed PyQt over the game. This keeps stale Shell actors cleared and avoids resurrecting the broken PyQt overlay path in borderless/fullscreen GNOME Wayland.
- Diagnostic signature: expected successful-raster/hidden-PyQt logs include `visibility=hidden`, `visibility_reason=presentation_not_attachable`, `surface_action=hidden`, and `content_visible=False` while Shell raster metrics continue to report real content frames. This means the managed PyQt window is suppressed because Shell raster is presenting content.
- Future gate option A, safer fallback-only gate: allow managed PyQt to show only after Shell raster failure, and only after Phase 16 proves raster-to-managed-PyQt cleanup without titlebar, stale actor, focus, or monitor regressions. The primary hook is the `suppress_pyqt_fallback_on_shell_raster_failure` decision in `overlay_client/backend/consumers.py`.
- Future gate option B, riskier debug/side-by-side gate: allow the managed PyQt window to remain visible even while Shell raster succeeds. This would deliberately reverse the current titlebar/standalone-window fix and must be gated as a developer/debug feature, not a user default. It would need an explicit override around `GnomeHelperPresentationCycleResult.should_show_overlay`, plus visibility-policy and runtime tests proving no focus steal, titlebar flash, monitor jump, or stale content actor regression.
- Recommended future order: implement and validate fallback-only first if needed; avoid side-by-side PyQt visibility unless there is a concrete debugging or support need.

### Phase 16: Deferred GNOME Fallback Cleanup
- Goal: resolve deferred fallback issues discovered during Phase 13 without mixing them into the borderless/fullscreen Shell raster proof decision.
- Phase 16 owns `Phase 13.F1` and `Phase 13.F2`; Phase 15 decided these are blockers for broader GNOME support promotion.
- `Phase 13.F1`: borderless-to-windowed fallback transition reset. When target state changes from Shell-raster-eligible `fullscreen=true/content_rect` to windowed `fullscreen=false/frame_rect_fallback`, runtime must clear Shell raster state and reset the managed PyQt surface out of fullscreen/hidden-suppressed mode before showing fallback.
- `Phase 13.F2`: GNOME windowed managed-PyQt standalone/titlebar behavior. Normal overlay mode still appears standalone-like in windowed GNOME Wayland, and titlebar compensation cannot currently be proven because helper target state reports `contentRect=null` and `decorationInsets=null`.
- `Phase 16.C1`: GNOME Wayland managed-PyQt code cleanup. After Phase 15 settles the user-facing backend/support model, remove or quarantine the obsolete user-facing/default GNOME Wayland managed-PyQt path while preserving non-GNOME behavior and any explicitly documented fallback/degraded-mode contracts.
- Clean windowed startup currently sizes and follows the game correctly, so Phase 16 should preserve that invariant while fixing transitions and chrome/identity behavior.
- Locked support target: GNOME Wayland windowed mode is supported. Do not document windowed mode away as unsupported/degraded for `GNOME Shell Raster`; Phase 16 must provide a production-safe windowed path.
- Locked windowed path decision: use managed PyQt for GNOME Wayland windowed mode unless implementation evidence proves Shell raster should cover windowed mode too.
- Locked transition contract: borderless/fullscreen uses Shell raster; when the target becomes windowed/non-borderless, clear Shell raster actors, reset hidden/suppressed PyQt state, and show the managed PyQt windowed path only after it is correctly sized, positioned, focus-safe, and click-through.
- Locked acceptance gate: clean windowed startup, borderless-to-windowed, and windowed-to-borderless must pass with no stale actors, no titlebar or separate PyQt window, no focus steal, correct monitor placement, click-through intact, and stable Alt-Tab/Super overview behavior.
- Test type decision: use unit tests for pure transition/visibility/surface-state policy; use focused runtime/backend tests for Shell-raster-to-PyQt reset contracts; use harness tests if Phase 16 touches `load.py`, startup/shutdown, preferences, or EDMC hook flow; use manual GNOME validation for titlebar/chrome, focus, click-through, monitor placement, Alt-Tab/Super, and stale-actor behavior.

#### Phase 16 Implementation Plan
- Touch points expected before coding: `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py` for GNOME-owned presentation and clear/reset policy, `overlay_client/backend/consumers.py` only if backend-neutral result translation needs a new field, `overlay_client/backend/presentation_policy.py` only if pure visibility state needs a new backend-neutral action, `overlay_client/follow_surface.py` only if the existing backend-neutral decision/prime-geometry contract is insufficient, and focused tests under `overlay_client/tests/`.
- Touch points intentionally avoided unless evidence requires them: `load.py`, EDMC plugin hooks, startup/shutdown wiring, preferences/settings UI, backend selection/default promotion, helper installation scripts, and broad support wording. Touching any lifecycle or preference hook adds a harness-test requirement.
- Unchanged behavior to preserve: selected Shell raster still owns borderless/fullscreen presentation; successful Shell raster presentation still hides/suppresses the managed PyQt top-level; Shell raster export/provider failure in borderless/fullscreen still clears/degrades instead of remapping broken PyQt over the game; Auto/default backend selection is not promoted; non-GNOME and non-Shell-raster backends keep their existing visibility/follow behavior; clean windowed startup remains correctly sized and followed.
- Implementation direction: keep compositor-specific transition decisions inside the GNOME backend bundle or backend-owned consumer contracts. Generic follow/runtime code must continue to consume backend-neutral results and must not branch on GNOME helper enums or raw compositor backend names.
- Test type selection for Phase 16: unit tests are required for pure transition/visibility/surface-state policy; focused backend/runtime tests are required for Shell-raster-to-managed-PyQt reset behavior; harness tests are required only if `load.py`, EDMC hook flow, startup/shutdown lifecycle, preference wiring, or settings replication are touched; manual GNOME validation remains required for compositor-visible chrome, focus, click-through, monitor placement, stale actors, Alt-Tab, and Super overview.
- Exact focused automated tests planned before broad checks: run `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_presentation_policy.py -k "shell_raster or windowed or fallback or mapped_suppressed or presentation_policy"` after adding/changing focused tests; run narrower file-level tests first if failures need isolation.
- Exact broad automated checks planned after focused tests pass: run `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_presentation_policy.py`; run `source overlay_client/.venv/bin/activate && python -m pytest` if touched code is not limited to backend presentation policy/runtime; run `make check` only if broader project wiring, lint-sensitive surfaces, or shared interfaces are changed.
- Manual validation steps to run after automated tests: clean windowed startup, borderless/fullscreen startup, borderless/fullscreen to windowed, windowed to borderless/fullscreen, monitor move in both modes, Keep Visible toggle in both modes, focus loss/return, click-through while visible and suppressed, Alt-Tab, Super overview, helper reload/disable, and EDMC shutdown cleanup.

#### Phase 16.8 Helper-Loaded Compositor Instrumentation Plan
- Current direction: instrument first before remediation. The exact GNOME/Mutter/NVIDIA failure mechanism is unknown, and Isolation A proved the overlay client and tracked Shell raster actors are not required for the visible failure. Do not implement actor-cleanup or focus-change remediation until the helper feature-gate data identifies the failing capability.
- Touch points expected before coding: `helpers/gnome_shell_extension/extension.js` and `helpers/gnome_shell_extension/constants.js` for helper-local feature gating and structured diagnostics; `helpers/gnome_shell_extension/metadata.json` only if the helper version/protocol metadata must change; source/static tests under `overlay_client/tests/test_gnome_shell_helper_extension_source.py`, `overlay_client/tests/test_gnome_shell_helper_dbus_health.py`, `overlay_client/tests/test_gnome_shell_helper_presentation_state.py`, and `tests/test_gnome_shell_extension_manifest.py`.
- Touch points intentionally avoided unless evidence requires them: `load.py`, EDMC hooks, preferences/settings UI, settings replication, backend selection/default promotion, Shell raster support wording, and generic follow/runtime compositor dispatch. If any EDMC lifecycle or preference wiring is touched, add harness tests per the AGENTS.md test gate.
- Feature flag contract: add a dev-only JSON feature flag read by the GNOME extension during `enable()`. Use a user-config JSON file rather than EDMC preferences so the helper can be bisected while EDMC/client are stopped. Mode changes require extension reload; if Elite/Proton enters the black-screen repeating state, log out/in before the next mode because live-disabling the helper did not recover the bad compositor/session state.
- Instrumentation contract: emit structured GNOME Shell journal diagnostics for helper `enable()`/`disable()`, selected mode, DBus export/unexport, target-query activation, overview/focus/window signal attachment, raster subsystem initialization, actor create/destroy/clear/apply decisions, actor counts, and any caught helper exceptions. Return diagnostics over DBus only in modes where DBus is enabled.
- Initial feature-gate modes: `lifecycle_only`, `dbus_health_only`, `target_query_enabled`, `overview_hooks_enabled`, `raster_code_enabled_no_actor`, `raster_actor_enabled`, and `full_helper`.
- Validation matrix per mode: start from a clean login when changing modes; verify EDMC/client are stopped unless intentionally testing client-driven behavior; run Elite borderless for about 10 minutes; repeat Alt-Tab away/back and Super overview entry/exit; watch for Elite black screen, Alt-Tab trapping, visible flashing in Firefox or other apps, GNOME Shell frame-clock assertions, NVIDIA DRM allocation fallbacks, and helper diagnostics. A single user-visible black-screen/focus-trap failure is enough to stop that mode and record the failing capability boundary.
- Test type selection for 16.8: use source/unit tests for JSON mode parsing defaults, mode-gated helper source behavior, DBus health availability by mode, and diagnostic strings/fields. Use harness tests only if EDMC lifecycle, `load.py`, preferences, runtime lifecycle wiring, or settings replication are touched.
- Exact focused automated tests planned for 16.8: run `source overlay_client/.venv/bin/activate && python -m pytest tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_gnome_shell_helper_dbus_health.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py` after instrumentation changes; add narrower `-k` filters while developing if failures need isolation.
- Exact broad automated checks planned for 16.8: run `source overlay_client/.venv/bin/activate && python -m pytest` if helper protocol/source contracts or shared test fixtures change; run `make check` before marking 16.8 complete if touched files include Python wrappers, scripts, or shared interfaces.
- Remediation decision guide: if `lifecycle_only` fails, the extension being loaded is enough and Phase 16 must pause support promotion until Shell-side lifecycle effects are understood. If `dbus_health_only` fails, inspect service export/object lifecycle. If `target_query_enabled` fails, focus on Meta window enumeration, monitor geometry, or target-window polling. If `overview_hooks_enabled` fails, inspect overview/focus/workspace signal hooks. If `raster_code_enabled_no_actor` fails, inspect raster imports, timers, or image processing even without actor parenting. If `raster_actor_enabled` fails, actor construction/parenting/paint lifecycle is the leading suspect. If only `full_helper` fails, isolate the interaction between client-driven apply, target updates, raster actors, and cleanup.

#### Phase 16.8 Implementation Notes
- Code touch points changed on 2026-05-27: `helpers/gnome_shell_extension/constants.js` and `helpers/gnome_shell_extension/extension.js`.
- Test touch points changed on 2026-05-27: `tests/test_gnome_shell_extension_manifest.py`, `overlay_client/tests/test_gnome_shell_helper_extension_source.py`, and `overlay_client/tests/test_gnome_shell_helper_dbus_health.py`.
- Dev-only config contract implemented: the helper reads `~/.config/EDMCModernOverlay/gnome_helper_dev_mode.json` during extension `enable()`. It also supports `EDMC_MODERN_OVERLAY_GNOME_HELPER_DEV_CONFIG` as an explicit config-path override for sessions that launch GNOME Shell with that environment available. With no config file, behavior remains `full_helper`.
- Supported config shape: `{"enabled": true, "mode": "lifecycle_only", "diagnostics": true}`. `enabled=false` or no config file restores default `full_helper`; invalid or malformed dev config falls back to `lifecycle_only` with diagnostics so the helper fails quiet rather than loading the full behavior accidentally.
- Implemented feature-gate modes: `lifecycle_only`, `dbus_health_only`, `target_query_enabled`, `overview_hooks_enabled`, `raster_code_enabled_no_actor`, `raster_actor_enabled`, and `full_helper`.
- Mode behavior implemented: `lifecycle_only` skips DBus export entirely; `dbus_health_only` exports health with reduced capabilities only; `target_query_enabled` adds target query; `overview_hooks_enabled` adds overview cleanup signal hooks; `raster_code_enabled_no_actor` allows presentation parsing/eligibility/validation while blocking actor creation; `raster_actor_enabled` enables raster actor paths; `full_helper` preserves the previous default behavior.
- Structured diagnostics implemented: dev-mode logs include helper enable/disable, selected mode/config source, DBus export/unexport/name loss, target query start/block, overview hook attach/remove/cleanup, raster code/actor block decisions, raster actor create/apply/destroy/clear decisions, actor counts, and caught helper exceptions. DBus payloads include a `feature_gate` object only where DBus is available.
- Behavior intentionally unchanged: no `load.py`, EDMC hooks, startup/shutdown lifecycle wiring, preferences/settings UI, settings replication, backend selection/default promotion, or generic follow/runtime compositor dispatch was touched. GNOME Shell Raster remains experimental and is not promoted to Auto/default.
- Harness test decision: no harness tests were required because Phase 16.8 only changed helper-local GNOME Shell extension code and source/unit tests. No EDMC lifecycle, preference, `load.py`, or runtime wiring was touched.

#### Phase 16 Refactor Staging
| Stage | Description | Status |
| --- | --- | --- |
| 16.1 | Expand implementation plan, touch points, unchanged behavior, test type selection, and exact test commands before coding | Completed 2026-05-25 |
| 16.2 | Reproduce/instrument borderless-to-windowed fallback transition and add focused regression tests | Completed 2026-05-25 |
| 16.3 | Implement Shell-raster-to-managed-PyQt surface reset without regressing clean windowed startup | Completed 2026-05-25; Clean Windowed Revalidation Pending |
| 16.4 | Re-evaluate GNOME windowed standalone/titlebar compensation limits with helper diagnostics | In Progress; Title-Bar Compensation Retest Pending |
| 16.5 | Implement windowed chrome/identity fixes needed for supported managed-PyQt windowed mode | Pending Manual GNOME Validation Outcome |
| 16.6 | Run focused manual validation for borderless-to-windowed, windowed-to-borderless, clean windowed startup, normal borderless mode, click-through, monitor placement, and Alt-Tab/Super | Blocked; Borderless Alt-Tab Black-Screen Regression With Helper Active |
| 16.7 | Remove or quarantine obsolete user-facing GNOME Wayland managed-PyQt backend/default path after Phase 15 support decisions | Pending 16.4-16.6 Outcome |
| 16.8 | Add helper-loaded compositor instrumentation and dev-only feature-gate modes to isolate the borderless black-screen trigger | Completed 2026-05-27 |
| 16.9 | Run clean-session helper feature-gate bisect matrix against Elite borderless, Alt-Tab, Super overview, Firefox/app flashing, and journal diagnostics | Completed 2026-05-28; No Feature-Gate Boundary Failure Reproduced |
| 16.10 | Run client-driven Shell raster validation before selecting remediation or updating the Phase 16 support gate | In Progress; Initial Client-Driven Pass Complete; Longer Soak/Windowed Retest Pending |
| 16.11 | Remove direct target-window actor parenting for helper proof/raster actors and validate the safer Shell overlay-group parent | Implemented 2026-06-15; Manual Reload Validation Pending |

#### Phase 16 Automated Implementation Notes
- Code touch points changed on 2026-05-25: `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`, `overlay_client/backend/surface_preparation.py`, `overlay_client/backend/consumers.py`, `overlay_client/backend/presentation_policy.py`, and `overlay_client/follow_surface.py`.
- Test touch points changed on 2026-05-25: `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, `overlay_client/tests/test_follow_surface_mixin.py`, `overlay_client/tests/test_backend_consumers.py`, and `overlay_client/tests/test_backend_presentation_policy.py`.
- Behavior implemented: when `GNOME Shell Raster` is selected and the target is windowed/non-fullscreen, the GNOME backend bundle allows the managed PyQt path instead of treating raster ineligibility as a borderless/fullscreen export failure. If the previous runtime state was Shell raster, it first sends a Shell raster clear request and blocks PyQt fallback if that clear fails.
- Surface reset implemented: backend-owned presentation can now request a backend-neutral `managed_windowed` Qt surface preparation. The generic follow surface consumes that request by applying focus-safe/click-through window flags, resetting fullscreen window state, selecting the target screen, and setting geometry before the existing visibility path calls `show()`.
- Clean-windowed follow-up implemented after manual attempt 1: explicit `GNOME Shell Raster` logs showed `managed_windowed` surface preparation succeeded, but startup while the target was unfocused returned `visibility_reason=focus_lost_hidden`, so the PyQt surface never mapped and the helper repeatedly reported `overlay_window_not_found`. Backend consumer translation now marks successful `managed_windowed` preparation as `prepared_surface_requires_mapping`, and the pure visibility policy maps that prepared surface as `mapped_suppressed` with `content_visible=False` until focus returns.
- Title-bar compensation follow-up implemented after manual finding: the preference was present in replicated settings, but the GNOME helper path used the helper `frame_rect_fallback` directly instead of the legacy compensated geometry path. Generic follow now passes the title-bar compensation preference through the backend-owned presentation contract, and the GNOME backend bundle applies it only to non-fullscreen managed-PyQt `frame_rect_fallback` attach requests. Borderless/fullscreen Shell raster and real `content_rect` presentation remain unchanged.
- Windowed focus follow-up implemented after manual attempt 2: logs showed corrected compensated geometry (`frame_rect` y `113` / height `997`, requested/applied y `143` / height `967`, `rect_match=True`) but GNOME helper target focus stayed false for windowed Elite, including a direct `GetTargetState` query. Because the previous visibility policy trusted that focus bit, it kept `surface_action=mapped_suppressed` and `content_visible=False` indefinitely. Backend consumer translation now marks successful managed-windowed preparation as allowing content when focus is unreliable, and the pure visibility policy restores content once the prepared surface is found and rect-matched while still hiding for unavailable, minimized, or off-workspace targets.
- Behavior preserved: borderless/fullscreen Shell raster success still suppresses the managed PyQt top-level; borderless/fullscreen Shell raster export/provider failure still clears/degrades and does not remap managed PyQt; Auto/default support wording is unchanged; no `load.py`, EDMC hooks, startup/shutdown lifecycle, preferences, or settings replication code was touched.
- Harness test decision: no new harness tests were required because Phase 16 did not touch `load.py`, plugin hooks, startup/shutdown lifecycle, preferences, or settings wiring. Existing harness tests were included in the full pytest and `make check` runs.

#### Phase 16 Automated Test Results
- `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py::test_selected_shell_raster_windowed_transition_clears_then_uses_managed_pyqt overlay_client/tests/test_gnome_helper_presentation_runtime.py::test_selected_shell_raster_windowed_startup_uses_managed_pyqt_without_clear overlay_client/tests/test_gnome_helper_presentation_runtime.py::test_selected_shell_raster_windowed_transition_blocks_pyqt_when_clear_fails overlay_client/tests/test_follow_surface_mixin.py::test_backend_managed_windowed_surface_preparation_resets_fullscreen_state_without_showing`
  - Result: passed, 4 passed.
- `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_backend_presentation_policy.py::test_backend_presentation_visibility_maps_prepared_surface_suppressed_until_focus_returns overlay_client/tests/test_backend_consumers.py::test_backend_presentation_cycle_marks_managed_windowed_surface_as_requiring_mapping`
  - Result: passed, 2 passed.
- `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py::test_selected_shell_raster_windowed_title_bar_compensation_offsets_managed_pyqt_request overlay_client/tests/test_backend_consumers.py::test_backend_presentation_cycle_wraps_gnome_helper_result_when_helper_available overlay_client/tests/test_follow_surface_mixin.py::test_refresh_follow_geometry_uses_gnome_helper_presentation_and_skips_legacy_refresh`
  - Result: passed, 3 passed.
- `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_backend_presentation_policy.py::test_backend_presentation_visibility_shows_matched_prepared_surface_when_focus_is_unreliable overlay_client/tests/test_backend_consumers.py::test_backend_presentation_cycle_marks_managed_windowed_surface_as_requiring_mapping`
  - Result: passed, 2 passed.
- `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_follow_surface_mixin.py -k "shell_raster or windowed or fallback or mapped_suppressed or presentation_policy or surface_preparation or prepared_surface or title_bar or focus_unreliable"`
  - Result: passed, 53 passed, 74 deselected.
- `source overlay_client/.venv/bin/activate && python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_follow_surface_mixin.py`
  - Result: passed, 127 passed.
- `source overlay_client/.venv/bin/activate && python -m pytest`
  - Result: passed, 1094 passed, 40 skipped. Skips are existing headless/optional GUI skips.
- `git diff --check`
  - Result: passed.
- `make check`
  - Result: passed. `ruff check .` passed, `mypy` passed with no issues in 92 source files, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 1130 passed and 21 skipped.
- `source overlay_client/.venv/bin/activate && python -m pytest tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_gnome_shell_helper_dbus_health.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py`
  - Phase 16.8 result: passed, 94 passed.
- `source overlay_client/.venv/bin/activate && python -m pytest`
  - Phase 16.8 result: passed, 1103 passed, 40 skipped. Skips are existing headless/optional GUI skips.
- `make check`
  - Phase 16.8 result: skipped because this step touched helper JavaScript, source/unit tests, and docs only; no Python wrappers, scripts, shared interfaces, EDMC lifecycle wiring, or lint/type-sensitive runtime code was changed.

#### Phase 16 Manual Validation Notes
- Clean windowed startup attempt 1 on 2026-05-25 failed with explicit `GNOME Shell Raster`: user observed the overlay flashing to the top, wrong size, and wrong position.
- The same windowed scenario with backend `Auto` restarted into the `GNOME Shell helper` degraded PyQt path and correctly sized/followed the game window, including moving to another monitor. This is useful baseline evidence but is not a Phase 16 pass for selected `GNOME Shell Raster`.
- Log interpretation for the explicit `GNOME Shell Raster` failure: `managed_windowed` surface preparation succeeded and selected the target rect, but the visibility policy kept the hidden overlay hidden because the target was unfocused at startup. That prevented the helper from finding the overlay window and caused repeated `overlay_window_not_found` degraded cycles.
- Follow-up fix is automated and covered by tests; clean windowed startup must be retested with selected `GNOME Shell Raster`.
- Title-bar compensation manual finding: user reported `Compensate for Elite Dangerous title bar` was checked but not respected in the windowed GNOME path. Follow-up fix is automated and covered by tests; windowed startup retest should confirm the overlay content starts below the configured title-bar height.
- Clean windowed startup attempt 2 on 2026-05-25 still failed with explicit `GNOME Shell Raster`: user observed wrong size/position, one flash, disappearance when the game gained focus, and a separate standalone-app-like window. Logs showed title-bar compensation and rect placement were now correct internally, but content was suppressed indefinitely because GNOME helper reported `target_focus=False` for windowed Elite. Follow-up focus-unreliable policy fix is automated and covered by tests; standalone-app-like behavior still needs manual retest and may remain a Phase 16.5 blocker.
- Borderless Alt-Tab validation blocker on 2026-05-26: user reported that after the game and overlay had run for a while, Alt-Tab back to Elite Dangerous in borderless mode could make the game window go black and temporarily trap focus so Alt-Tab away did not work until the game recovered several seconds later. The user reproduced the issue with EDMC/plugin running and also without EDMC/plugin running, then disabled the GNOME helper and logged out/in and could not reproduce it. After re-enabling/running the helper path, the user triggered another instance for log capture.
- Log evidence for the 2026-05-26 blocker: `gsettings get org.gnome.shell enabled-extensions` included `edmc-modern-overlay-helper@edmcmodernoverlay.github.io`, `gdbus ... GetHealth` returned healthy helper protocol `3`, and DBus owner lookup returned an active owner for `org.edmc.ModernOverlay.Helper`. The helper status script was unreliable from the Snap-confined terminal (`not_discovered`), but the GNOME enabled-extension list and DBus health showed the helper was active. Around the repro window, `overlay_client.log*` showed Shell raster presentation active for full-monitor borderless rects (`3440x1440`) and later repeated `target_not_focused`/hidden diagnostics, with no overlay-client exception. The user journal showed GNOME Shell compositor warnings near the repro window: `(../clutter/clutter/clutter-frame-clock.c:1146):clutter_frame_clock_dispatch: code should not be reached` at `2026-05-26 14:29:27 PDT` and `14:30:55 PDT`, plus an earlier NVIDIA DRM allocation fallback at `14:27:57 PDT`.
- Follow-up evidence for the 2026-05-26 blocker: a later triggered instance showed another GNOME Shell Clutter frame-clock assertion at `2026-05-26 15:00:57 PDT`, followed by NVIDIA DRM NVKMS GEM video-memory allocation fallbacks at `15:03:02 PDT` and `15:03:47 PDT`. The overlay client still showed no exception; current samples after recovery repeatedly reported `state=presentation_degraded`, `reasons=['target_not_focused']`, `visibility=hidden`, `surface_action=hidden`, `content_visible=False`, `keep_overlay_visible=False`, and `target_focus=False`.
- Isolation A result on 2026-05-26: with EDMC and `overlay_client` fully stopped (`pgrep -af 'overlay_client|EDMarketConnector|EDMCModernOverlay'` returned nothing), a DBus Shell raster clear returned `status="shell_raster_frame_cleared"` with `cleanup_action=""`, `actor_visible=false`, and no regions. The black-screen/focus-trap then reproduced immediately twice. The helper was still enabled and healthy. Fresh journal evidence for that immediate repro showed two NVIDIA DRM NVKMS GEM video-memory allocation fallbacks at `2026-05-26 16:24:01 PDT`; no matching GNOME Shell user-journal line was emitted in the last 10 minutes.
- Escalation after Isolation A on 2026-05-26: the user reported the black-screen was happening repeatedly without needing Alt-Tab. At `16:28:13 PDT`, EDMC/client were still stopped, the helper was still enabled and healthy, and no new GNOME Shell user-journal entries appeared in the last 5 minutes; the last visible system evidence remained the `16:24:01 PDT` NVIDIA DRM fallbacks. The helper was then live-disabled with `gnome-extensions disable edmc-modern-overlay-helper@edmcmodernoverlay.github.io`; verification showed the helper UUID absent from `org.gnome.shell enabled-extensions`, `gdbus ... GetHealth` returned `ServiceUnknown`, and `pgrep -af 'overlay_client|EDMarketConnector|EDMCModernOverlay'` returned no EDMC/client processes.
- Post-live-disable result on 2026-05-26: the user reported that the black-screen happened as soon as they Alt-Tabbed back to the game and then repeated every few seconds while in-game, even with the helper unloaded and EDMC/client stopped. Follow-up journal capture showed a GNOME Shell frame-clock assertion at `2026-05-26 16:28:57 PDT`. This means live-disabling the helper does not recover the current GNOME session once the failure mode is active.
- Clean-session control preflight on 2026-05-26: after logout/login with Elite not yet started, `org.gnome.shell enabled-extensions` did not include the EDMC helper UUID and `gdbus ... GetHealth` returned `ServiceUnknown`. This confirms the next Elite-only test starts from a helper-disabled GNOME session.
- Clean-session helper-disabled control result on 2026-05-26: with EDMC/client still stopped, helper UUID absent, and helper DBus service absent, the user played Elite in borderless for about 10 minutes and Alt-Tabbed away/back many times with no black-screen issue. A later verification still showed no EDMC/client processes and helper `ServiceUnknown`. The journal included one GNOME Shell frame-clock assertion at `2026-05-26 17:01:47 PDT`, but it was not accompanied by the user-visible repeating black-screen failure.
- Clean-session helper-enabled preflight on 2026-05-26: the user enabled `edmc-modern-overlay-helper@edmcmodernoverlay.github.io` while EDMC/client remained stopped. `org.gnome.shell enabled-extensions` included the helper UUID, `gdbus ... GetHealth` returned healthy helper protocol `3`, and `pgrep -af '[o]verlay_client|[E]DMarketConnector|[E]DMCModernOverlay'` returned no EDMC/client processes. The user then began the Elite-only borderless play/Alt-Tab control with the helper loaded.
- Clean-session helper-enabled control result on 2026-05-26: Elite itself did not show the black-screen issue, but Firefox rapidly flashed while Elite/Proton was present and returned to normal after the user quit the game. Follow-up verification still showed helper enabled/healthy and no EDMC/client runtime. Process state showed Steam/Proton `AppId=359320` / `EDLaunch.exe` processes and Firefox processes. Journal evidence included GNOME Shell frame-clock assertions at `2026-05-26 17:07:07 PDT` and `17:12:27 PDT`, NVIDIA DRM NVKMS GEM allocation fallbacks at `17:08:05`, `17:13:54`, and `17:14:06 PDT`, and a Firefox minidump path at `17:12:01 PDT`. This indicates the helper-loaded + Elite/Proton condition can destabilize compositor/client presentation outside the overlay client.
- Clean-session helper-enabled retry on 2026-05-27: before restarting Elite, `pgrep -af 'Elite|EDLaunch|steam_app_359320|AppId=359320'` returned nothing. The user restarted Elite while Firefox remained usable, and Firefox continued to work normally. Verification at `2026-05-27 17:12 PDT` showed the helper UUID enabled, `gdbus ... GetHealth` healthy for protocol `3`, Elite/Proton and Firefox processes running, and no EDMC/overlay client runtime. The journal contained a GNOME Shell frame-clock assertion at `17:10:39 PDT`, but no user-visible black-screen or Firefox flashing was reported. This makes the helper-loaded + Elite/Proton compositor symptom intermittent rather than immediately deterministic.
- Clean-session helper-enabled retry follow-up on 2026-05-27: the user then reported the Elite black screen had already happened several times after restart. Capture at `17:13 PDT` showed the helper UUID enabled and healthy, no EDMC/overlay client runtime under the tightened process check (`pgrep -f '[o]verlay_client\\.overlay_client|[E]DMarketConnector\\.py'` returned nothing), and Elite/Proton running. The journal showed a GNOME Shell frame-clock assertion at `2026-05-27 17:13:20 PDT`, shortly before capture. The helper was live-disabled at `17:14 PDT`; verification showed the helper UUID absent from enabled extensions, `gdbus ... GetHealth` returned `ServiceUnknown`, and no EDMC/overlay client runtime.
- Post-live-disable retry result on 2026-05-27: the user reported the Elite black-screen issue was still happening after the helper was unloaded. Verification at `17:19 PDT` showed the helper UUID still absent, `gdbus ... GetHealth` still `ServiceUnknown`, and no EDMC/overlay client runtime. Journal evidence showed repeated GNOME Shell frame-clock assertions after live-disable at `17:14:25`, `17:15:45`, `17:18:02`, and `17:19:00 PDT`. A kernel warning also occurred at `17:18:23 PDT` in `fs/exec.c:path_noexec` from a Chromium `Media` process with NVIDIA modules loaded; the user confirmed this Chromium media-process warning is separate from the Elite/helper isolation and should not be treated as evidence for the Phase 16 blocker.
- Clean-session helper-disabled restart control on 2026-05-27: after logout/login, the user started Elite with the helper still disabled. Verification at `17:30 PDT` showed the helper UUID absent from enabled extensions, `gdbus ... GetHealth` returned `ServiceUnknown`, `pgrep -f '[o]verlay_client\\.overlay_client|[E]DMarketConnector\\.py'` returned no EDMC/client runtime, and Elite processes were present. The last 5 minutes of journal output had no GNOME Shell frame-clock assertion or NVIDIA DRM entry, only an unrelated GNOME sound panel launch.
- Clean-session helper-disabled restart control result on 2026-05-27: the user reported no black-screen returned during the helper-disabled Elite test and then closed the game. Follow-up verification at `17:42 PDT` still showed the helper UUID absent, `gdbus ... GetHealth` returned `ServiceUnknown`, and no EDMC/overlay client runtime. Journal output showed one GNOME Shell frame-clock assertion at `17:31:13 PDT`, but it was not accompanied by a visible black-screen failure. The full game executable was closed, while Steam/Proton launcher wrapper and `EDLaunch.exe` processes remained present after the user closed the game.
- Interpretation for the 2026-05-26/2026-05-27 blocker: this is a compositor/driver-facing manual validation failure correlated with the GNOME helper being loaded, not merely a client visibility-policy issue. Because it affects Alt-Tab recovery and can trap focus on a black game surface, Phase 16 must not pass the Alt-Tab/Super acceptance gate until the helper-active borderless path is isolated and fixed. Keep GNOME Shell Raster experimental and do not promote it to Auto/default or broad support while this blocker is open.
- Immediate isolation conclusion: explicit Shell raster clear returned `cleanup_action=""`, `actor_visible=false`, and no regions, and the failure reproduced with EDMC/client stopped. Live-disabling the helper did not recover the bad session, while a clean logout/login with the helper disabled did. That makes active overlay-client updates and tracked Shell raster actors insufficient as the root explanation. Actor cleanup remains a candidate only if the feature-gate bisect later implicates actor creation or actor persistence.

#### Phase 16 Helper-Loaded Borderless Isolation Plan
- Isolation A, helper enabled but EDMC/client stopped: completed and failed. With no EDMC/client runtime and no tracked Shell raster actors, Elite borderless still reproduced black-screen/focus-trap behavior. This shifted the investigation away from client-side fallback policy.
- Isolation B, helper live-disabled in the already-bad session: completed and failed. The helper UUID disappeared, DBus returned `ServiceUnknown`, and no EDMC/client runtime was present, but black-screen behavior continued. This proves live helper disable is not a valid recovery signal after the compositor/session has entered the bad state.
- Isolation C, clean-session helper-disabled control: completed and passed twice. After logout/login with helper absent and EDMC/client stopped, Elite borderless ran through repeated Alt-Tab cycles without visible black-screen recurrence. This is the current clean baseline.
- Isolation D, clean-session helper-enabled with EDMC/client stopped: completed with intermittent failures. The helper loaded cleanly and DBus health was healthy, then Elite/Proton plus helper-loaded state correlated with Firefox flashing on 2026-05-26 and repeated Elite black-screen on 2026-05-27. This proves the next investigation must bisect helper-loaded capabilities without requiring overlay-client runtime.
- Next isolation method: implement the Phase 16.8 feature-gated helper modes and run each mode from a clean login. Start with `lifecycle_only`; then add DBus health, target query, overview/focus hooks, raster code without actors, raster actor creation, and finally full helper behavior. Do not select a remediation until one of those capability boundaries fails.
- Candidate remediation path after bisect: if actor creation/persistence is the first failing boundary, implement helper-side actor lifecycle cleanup or focus-change cleanup and retest. If target query or overview/focus hooks fail first, remediate that Shell integration directly. If lifecycle-only fails, the helper cannot be user-facing on this environment until a safer Shell-extension lifecycle approach is found.

#### Phase 16.9 Manual Feature-Gate Validation Steps
- Start each mode from a clean login whenever practical. If Elite/Proton enters the repeating black-screen state, log out/in before testing another mode because live-disabling the helper did not recover the bad session.
- Before each mode, stop EDMC and the overlay client unless intentionally testing client-driven behavior. Verify with `pgrep -af '[o]verlay_client|[E]DMarketConnector|[E]DMCModernOverlay'`.
- Write the dev config for the mode under test: `mkdir -p ~/.config/EDMCModernOverlay && printf '{"enabled":true,"mode":"lifecycle_only","diagnostics":true}\n' > ~/.config/EDMCModernOverlay/gnome_helper_dev_mode.json`, replacing `lifecycle_only` with the current mode.
- Reload the helper after changing the file: `gnome-extensions disable edmc-modern-overlay-helper@edmcmodernoverlay.github.io` then `gnome-extensions enable edmc-modern-overlay-helper@edmcmodernoverlay.github.io`.
- Capture helper state and diagnostics: `gsettings get org.gnome.shell enabled-extensions`, `gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.GetHealth` for DBus-enabled modes, and `journalctl --user -b -o short-iso | grep -E 'edmc-modern-overlay-helper|edmc_modern_overlay_gnome_helper|clutter-frame-clock|NVIDIA|NVKMS'`.
- For each mode, run Elite borderless for about 10 minutes, repeatedly Alt-Tab away/back, enter/exit Super overview, and watch for Elite black screen, Alt-Tab trapping, Firefox or other app flashing, GNOME Shell frame-clock assertions, NVIDIA DRM allocation fallbacks, and helper diagnostic events.
- Test order: `lifecycle_only`, `dbus_health_only`, `target_query_enabled`, `overview_hooks_enabled`, `raster_code_enabled_no_actor`, `raster_actor_enabled`, then `full_helper`.
- Stop at the first mode that reproduces a visible black-screen/focus-trap or app flashing failure. Record the mode, whether DBus health was available, the latest helper diagnostics, and the relevant journal entries.
- Restore normal helper behavior after the matrix by removing the dev config file or setting `{"enabled":false}` and reloading the helper.

#### Phase 16.9 Manual Feature-Gate Results
- `lifecycle_only`, 2026-05-28 09:52-10:47 PDT: passed user-visible validation. The helper was enabled with `mode="lifecycle_only"`, `dbus_enabled=false`, no EDMC/client runtime was present, `GetHealth` returned `ServiceUnknown` as expected, and journal diagnostics showed `helper_enable` plus `dbus_export_skipped`. User ran Elite borderless, Alt-Tabbed, and used Super overview several times with no black screen, no focus trap, and no app flashing. Journal showed one GNOME Shell frame-clock assertion at `2026-05-28 09:55:45 PDT`, but it was not accompanied by visible failure.
- `dbus_health_only`, 2026-05-28 10:52-11:17 PDT: passed user-visible validation. The helper was enabled with `mode="dbus_health_only"`, DBus health responded healthy, capabilities were reduced to `hello`, `health`, `version`, `protocol`, and `capabilities`, and target query, presentation, overview hooks, raster code, and raster actors were disabled. User ran Elite borderless with repeated Alt-Tab/Super activity and reported no black screen, no Alt-Tab trap, and no Firefox/app flashing. Journal showed GNOME Shell frame-clock assertions at `10:53:08`, `10:53:11`, `10:57:49`, and `11:16:44 PDT`, but they were not accompanied by visible failure.
- `target_query_enabled`, 2026-05-28 11:34-11:48 PDT: passed user-visible validation. The helper was enabled with `mode="target_query_enabled"`, DBus health responded healthy, capabilities included `target_state` but not `presentation_state`, and presentation, overview hooks, raster code, and raster actors were disabled. `GetTargetState` found Elite as `target_found` with token `meta:127`, fullscreen/borderless content and monitor rects of `3440x1440`, and one launcher rejected. User ran Elite borderless with repeated Alt-Tab/Super activity and reported no black screen, no Alt-Tab trap, and no Firefox/app flashing. Journal showed GNOME Shell frame-clock assertions at `11:34:54`, `11:47:47`, and `11:47:52 PDT`, but they were not accompanied by visible failure.
- `overview_hooks_enabled`, 2026-05-28 11:50-12:03 PDT: passed user-visible validation. The helper was enabled with `mode="overview_hooks_enabled"`, DBus health responded healthy, capabilities included `target_state` but not `presentation_state`, and presentation, raster code, and raster actors were disabled. Journal showed `overview_hook_attached` for `showing`, `shown`, and `hiding`, plus repeated `overview_signal_cleanup` and `raster_clear_decision` events with zero proof/raster actors through repeated Super overview cycles. `GetTargetState` continued to find Elite as `target_found` with token `meta:127` and fullscreen/borderless content and monitor rects of `3440x1440`. User reported no black screen, no Alt-Tab trap, and no Firefox/app flashing. Journal showed one GNOME Shell frame-clock assertion at `11:51:54 PDT`, but it was not accompanied by visible failure.
- `raster_code_enabled_no_actor`, 2026-05-28 12:08-12:18 PDT: passed user-visible validation. The helper was enabled with `mode="raster_code_enabled_no_actor"`, DBus health responded healthy, capabilities included `target_state` and `presentation_state`, and feature gate diagnostics showed `presentation_enabled=true`, `overview_hooks_enabled=true`, `raster_code_enabled=true`, and `raster_actor_enabled=false`. `GetTargetState` found Elite as `target_found` with token `meta:127`, fullscreen/borderless content and monitor rects of `3440x1440`, and one launcher rejected. A direct `ApplyPresentation` Shell-raster update using a valid PNG under `/tmp/EDMCModernOverlay-shell-raster-jon/` returned `presentation_degraded` with `degrade_reasons=["raster_actor_disabled_by_mode"]`, `actor_visible=false`, `region_count=0`, and no cleanup action. During runtime validation, repeated Super overview cycles logged `overview_signal_cleanup` and `raster_clear_decision` with zero proof/raster actors. User reported no black screen, no Alt-Tab trap, and no Firefox/app flashing. Journal showed GNOME Shell frame-clock assertions at `12:11:02` and `12:17:37 PDT`, but they were not accompanied by visible failure.
- `raster_actor_enabled`, 2026-05-28 12:29-12:59 PDT: passed extended user-visible validation. The helper was enabled with `mode="raster_actor_enabled"`, DBus health responded healthy, capabilities included `target_state` and `presentation_state`, and feature gate diagnostics showed `presentation_enabled=true`, `overview_hooks_enabled=true`, `raster_code_enabled=true`, and `raster_actor_enabled=true`. `GetTargetState` found Elite as `target_found` with token `meta:17`, fullscreen/borderless content and monitor rects of `3440x1440`, and one launcher rejected. The first direct `ApplyPresentation` Shell-raster update using the inline 1x1 probe PNG returned `presentation_degraded` with `degrade_reasons=["decode_load_failed"]`, `actor_visible=false`, and no applied actor bounds; the immediate clear returned `shell_raster_frame_cleared` with `actor_visible=false`. A retry using repo asset `assets/icon_green_tick_16x16.png` copied under `/tmp/EDMCModernOverlay-shell-raster-jon/` returned `presentation_applied` with `actor_visible=true`, `applied_actor_bounds={"x":0,"y":0,"width":16,"height":16}`, `actor_parent="target_window_actor_child"`, no degrade reasons, and helper decode/apply timing diagnostics. The immediate explicit clear returned `shell_raster_frame_cleared` with `cleanup_action="explicit_clear"` and `actor_visible=false`. Runtime validation kept the helper healthy, logged repeated `overview_signal_cleanup` and `raster_clear_decision` events with zero proof/raster actors after the explicit clear, and the user reported no black screen, no Alt-Tab trap, and no Firefox/app flashing. Journal showed GNOME Shell frame-clock assertions at `12:34:24`, `12:58:21`, and `12:58:22 PDT`, but they were not accompanied by visible failure.
- `full_helper`, 2026-05-28 13:01-13:10 PDT: passed user-visible validation. The helper was enabled with `mode="full_helper"`, DBus health responded healthy, capabilities included `target_state` and `presentation_state`, and feature gate diagnostics showed all gate booleans enabled. `GetTargetState` found Elite as `target_found` with token `meta:17`, fullscreen/borderless content and monitor rects of `3440x1440`, and one launcher rejected. Runtime capture kept the helper healthy and logged repeated `overview_signal_cleanup` and `raster_clear_decision` events with zero proof/raster actors. User reported no black screen, no Alt-Tab trap, and no Firefox/app flashing. Journal showed one GNOME Shell frame-clock assertion at `13:08:37 PDT`, but it was not accompanied by visible failure; the pasted journal excerpt did not show NVIDIA/NVKMS entries or helper exceptions during this capture.
- Phase 16.9 conclusion: all helper-only feature-gate modes passed user-visible validation, including `full_helper`, and the original helper-loaded Elite borderless black-screen/focus-trap did not reproduce during this controlled matrix. No specific helper capability boundary was implicated. Actor creation and explicit clear were directly validated in `raster_actor_enabled`, then extended runtime stayed clean with zero stale actor counts. Do not select an actor-cleanup-only remediation from this matrix alone; Phase 16.10 needs a support/remediation decision based on the intermittent nature of the original failure and follow-up client-driven/longer-duration validation.

#### Phase 16.10 Client-Driven Validation Plan
- Decision before coding: do not implement remediation yet. Phase 16.9 passed every helper-only feature-gate mode, including direct actor creation/clear and full helper runtime with no client. The remaining evidence gap is whether the failure requires EDMC/overlay_client actively driving `ApplyPresentation` and real Shell raster frame updates over time.
- Test type selection for 16.10: use manual GNOME runtime validation for this step. No unit or harness tests are required before the next capture because this is a docs-only plan/status update and no code behavior is changing. If Phase 16.10 leads to runtime implementation changes, use unit tests for pure policy/helper code and harness tests only if `load.py`, EDMC hooks, preferences, startup/shutdown lifecycle, or settings replication are touched.
- Validation setup: keep the helper dev config at `{"enabled":true,"mode":"full_helper","diagnostics":true}` and reload the extension if that file changes. Run Elite in borderless/fullscreen. Start EDMC normally so the overlay client is active and the GNOME Shell Raster path can issue real presentation updates.
- Required preflight evidence: capture `START_TS`, helper health, EDMC/overlay process presence, target state if needed, the latest `/home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log` tail, and the GNOME Shell/user journal tail filtered for helper, raster, frame-clock, NVIDIA, and NVKMS entries.
- Runtime exercise: run for about 10 minutes with overlay content active or changing, repeat Alt-Tab away/back and Super overview entry/exit, and watch for Elite black screen, Alt-Tab trapping, Firefox/other-app flashing, stale actors after overview/focus changes, click-through regression, and overlay visibility loss.
- Failure handling: if black-screen/focus-trap/app flashing occurs, do not change helper modes before capturing evidence. Immediately capture helper health, process list, overlay log tail, journal tail, and visible outcome notes. Log out/in before retesting another mode because live helper disable previously did not recover a bad compositor/session state.
- Pass handling: if the short client-driven run passes, record that helper-only plus short client-driven validation did not reproduce the original failure. Keep GNOME Shell Raster experimental; the next decision should be longer Phase 17 soak or a targeted windowed fallback retest, not support promotion.

#### Phase 16.10 Client-Driven Validation Results
- Initial client-driven borderless run, 2026-05-28 13:17-13:37 PDT: passed user-visible validation with EDMC and overlay_client active. Preflight showed EDMC running as PID `672774`, overlay_client running as PID `672793`, helper health `healthy`, helper mode `full_helper`, and client runtime selection `manual_backend_override=gnome_shell_raster`. The overlay client issued real Shell raster presentation updates; preflight logs showed `state=presentation_applied`, `rect_match=True`, and `applied={'x': 0, 'y': 0, 'width': 3440, 'height': 1440}` at `13:17:18 PDT`. During the final capture, the client remained alive, helper health remained healthy, and the log tail showed repeated GNOME helper presentation cycles, including active client-driven `presentation_applied` samples with `rect_match=True` and expected `presentation_degraded` samples for `target_not_focused` or `gnome_overview_active` during focus/overview transitions. User reported no Elite black screen, no Alt-Tab trap, no Firefox/other-app flashing, overlay remained visible and click-through, and no stale actors remained after Super/Alt-Tab.
- Filtered journal evidence for the initial client-driven run: after the absolute timestamp retry, the pasted journal excerpt showed repeated `target_query_started` and `raster_clear_decision` events in `mode="full_helper"`, with all feature-gate booleans enabled and repeated `reason="target_not_focused"` clear decisions. Actor counts stayed zero: `shell_actor_proof_visible=false`, `shell_raster_frame_visible=false`, and `shell_raster_region_count=0`. The pasted excerpt did not show GNOME Shell frame-clock assertions, NVIDIA/NVKMS entries, helper exceptions, stale actor counts, or visible raster actors during the final tail.
- Interpretation: short helper-only validation plus the initial short client-driven Shell raster validation did not reproduce the original intermittent black-screen/focus-trap/app-flash failure. Do not select a remediation from this pass alone, and do not promote GNOME Shell Raster. The remaining decision should be based on a longer Phase 17-style soak or a targeted windowed fallback retest.

#### Phase 16 Manual Validation Steps
- Clean windowed startup retest: select `GNOME Shell Raster`, start EDMC/client while Elite is windowed, and confirm managed PyQt appears correctly sized/positioned, respects the title-bar compensation setting, remains click-through/focus-safe, and has no titlebar or separate-window behavior.
- Normal borderless/fullscreen startup: start in borderless/fullscreen and confirm Shell raster presents content while the managed PyQt top-level remains suppressed/hidden.
- Borderless/fullscreen to windowed: switch Elite from borderless/fullscreen to windowed and confirm Shell raster actors clear, managed PyQt appears only after correct geometry, no stale actors remain, click-through works, no focus steal occurs, and Alt-Tab/Super overview remain stable.
- Windowed to borderless/fullscreen: switch back to borderless/fullscreen and confirm Shell raster resumes, no stale managed PyQt window remains visible, monitor placement is correct, and click-through/focus behavior remains stable.
- Regression checks: move the target between monitors in both modes, toggle Keep Visible in both modes, test focus loss/return, test click-through while visible and suppressed, test helper reload/disable, and test EDMC shutdown cleanup.

#### Phase 16 Remaining Risk
- Manual GNOME validation is still required for compositor-visible facts that unit tests cannot prove: titlebar/chrome absence, no separate PyQt window in overview/Alt-Tab, no focus steal, actual click-through, monitor placement, stale Shell actor cleanup, and Super overview behavior.
- A manual blocker remains open for borderless Alt-Tab/Super stability: the helper-loaded borderless path previously correlated with temporary Elite black screen and Alt-Tab trapping after longer runtime. The Phase 16.9 helper-only feature-gate matrix and initial Phase 16.10 client-driven run did not reproduce the failure and did not implicate a specific helper capability boundary. Remaining risk is intermittent and must be handled through longer client-driven validation.
- Phase 16 should not promote GNOME Shell Raster to Auto/default or broad support until the manual validation matrix above passes and Phase 17 hardening completes.

#### Phase 16.11 Target-Actor Parenting Remediation
- Decision before coding: remove the riskiest compositor mutation first. The helper previously attached proof and raster actors directly under Elite's `MetaWindowActor` through the `target_window_actor_child` path. That path passed short visible proofs, but it also couples overlay lifecycle to the target fullscreen window actor and is the strongest plausible helper-owned source for a persistent black-screen/focus-trap session state.
- Touch points: `helpers/gnome_shell_extension/extension.js` and `overlay_client/tests/test_gnome_shell_helper_extension_source.py`.
- Behavior change: proof and Shell raster actors no longer attach as children of the target window actor. The remediation first tried `global.overlay_group`; after manual diagnostics showed that group is unavailable on this GNOME Shell, the helper now uses a target-window sibling model under `global.window_group`.
- Behavior preserved: helper target discovery, DBus health, presentation payload shape, explicit raster clear, overview cleanup hooks, stale actor cleanup, and backend/client contracts remain unchanged.
- Test type selection: source-contract/unit-style tests are sufficient for this change because it is local helper presentation logic and no EDMC `load.py` hooks, preferences, settings replication, journal/dashboard callbacks, or plugin lifecycle wiring changed. No harness test was required.
- Tests run: `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_helper_presentation_runtime.py` passed with `109 passed`.
- Additional checks run: `overlay_client/.venv/bin/python -m py_compile overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/backend/helper_ipc.py` passed. `git diff --check -- helpers/gnome_shell_extension/extension.js overlay_client/tests/test_gnome_shell_helper_extension_source.py` passed.
- Manual validation finding, 2026-06-15: after helper reload, the installed helper source matched the repo copy and DBus health was healthy, but GNOME Shell did not expose `global.overlay_group`. Runtime presentation degraded with `shell_raster_parent_unavailable`, then the client incorrectly mapped the managed PyQt fallback over fullscreen Elite. User observed focus/minimize/maximize churn and a visible title bar, confirming the titled Qt fallback was being shown.
- Follow-up behavior change: add `shell_raster_parent_unavailable` to the Shell-raster hard-degrade reasons that suppress managed PyQt fallback. In fullscreen/borderless mode, if Shell raster cannot attach, the overlay now hides instead of mapping a titled Qt window and stealing focus.
- Follow-up test type selection: unit/runtime tests are sufficient because this is backend-owned pure presentation policy/runtime state and no EDMC lifecycle, preferences, hooks, or settings replication changed.
- Follow-up tests run: `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py -k "shell_raster"` passed with `24 passed, 38 deselected`. `overlay_client/.venv/bin/python -m py_compile overlay_client/backend/bundles/_gnome_shell_helper_presentation.py` passed.
- Follow-up manual finding: after restarting EDMC/overlay_client, the focus/titlebar churn stopped, but no overlay appeared because Shell raster still degraded with `shell_raster_parent_unavailable`. Direct `diagnose_groups` showed `global.overlay_group` is unavailable on this GNOME Shell, while Elite's target `MetaWindowActor` is a child of `global.window_group`.
- Second follow-up behavior change: move proof/raster actors from the unavailable `global.overlay_group` parent to a target-window sibling model. The helper resolves Elite's `MetaWindowActor`, uses the actor parent when available, otherwise falls back to `global.window_group` only when the target actor is confirmed as a child, then places the extension-owned actor above the target window actor with `set_child_above_sibling`. This avoids direct target-window child parenting while restoring a fullscreen-capable Shell actor layer candidate.
- Second follow-up diagnostics: missing-parent logs now include sibling-parent source and `global.window_group` target index fields so a failed attach distinguishes missing target actor, missing actor parent, and missing window-group membership.
- Second follow-up tests run: `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_helper_presentation_runtime.py` passed with `110 passed`. `git diff --check -- helpers/gnome_shell_extension/extension.js overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_gnome_helper_presentation_runtime.py docs/refactoring/gnome_wayland_presentation_attachment.md` passed.
- Manual validation finding: the installed helper file matched the sibling-parent repo source, but a direct DBus proof call still returned `actor_parent="global.overlay_group"`. GNOME Shell is still executing the older imported extension module in the live Wayland session, so a logout/login is required before retesting this source change. Expected diagnostics after login should show `actor_parent="target_window_actor_sibling"` and no `target_window_actor_child` usage.
- Post-login manual validation finding: a direct DBus proof call against the current Elite target succeeded with `actor_parent="target_window_actor_sibling"`, proving the helper actor-parenting change is active and Shell actor stacking is no longer blocked by the unavailable `global.overlay_group`.
- Third follow-up behavior change: selected `gnome_shell_raster` runtime now treats GNOME's fullscreen Elite focus bit as unreliable only for a narrow fullscreen/borderless case: target found, fullscreen, on current workspace, not minimized, target content rect matches monitor rect, and requested content rect matches monitor rect. In that case the client sends `allow_unfocused_target=true` to the helper so Shell raster can attach even when `MetaWindow.has_focus()` reports false. Legacy/env-only raster proof behavior and windowed managed-PyQt behavior remain unchanged.
- Third follow-up tests run: `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py::test_selected_shell_raster_allows_focus_unreliable_fullscreen_target` passed with `1 passed`. `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py -k "shell_raster and not static_frame"` passed with `24 passed, 39 deselected`. `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_helper_presentation_runtime.py::test_selected_shell_raster_allows_focus_unreliable_fullscreen_target` passed with `49 passed`. `python3 -m py_compile overlay_client/backend/bundles/_gnome_shell_helper_presentation.py` passed. `git diff --check -- helpers/gnome_shell_extension/extension.js overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_gnome_helper_presentation_runtime.py docs/refactoring/gnome_wayland_presentation_attachment.md` passed.
- Test caveat: `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py -k "shell_raster"` aborts in the existing static PyQt test-frame writer on this headless terminal path; the non-static focused subset above excludes that unrelated Qt crash path.
- Fourth follow-up manual finding: after logout/login and restarting Elite/EDMC, Shell raster actors were visible only while holding Alt-Tab or when VS Code had focus, where the overlay appeared behind the VS Code window and over the running game. This proves raster actor rendering and sibling parenting are active, but the focused fullscreen window can still restack above the raster actors during normal gameplay.
- Fourth follow-up behavior change: after each single-frame apply, multi-region update, or unchanged single-frame reuse, the helper now schedules bounded stacking refreshes at 50 ms, 150 ms, and 300 ms. The refresh re-applies `set_child_above_sibling(actor, targetActor)` for current raster actors matching the same target token and parent, without changing the parent layer and without reintroducing direct target-window child parenting.
- Fourth follow-up test type selection: source-contract tests are sufficient for this helper-only GJS stacking refresh because no EDMC lifecycle hooks, preferences, settings replication, journal/dashboard callbacks, or backend policy contracts changed. Manual GNOME validation remains required for active-fullscreen compositor stacking.
- Fourth follow-up tests run: `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_helper_presentation_runtime.py::test_selected_shell_raster_allows_focus_unreliable_fullscreen_target` passed with `50 passed`.
- Fifth follow-up manual finding: after logout/login, the delayed sibling stacking refresh did not change the user-visible result. A live `diagnose_groups` query showed Elite's fullscreen `MetaWindowActorX11` at `global.window_group` child index `9` and current Shell raster actors visible/mapped at child indices `10` and `11`, already above Elite in normal child order. The overlay was still hidden while Elite had focus but visible during Alt-Tab or with another window above Elite. This proves ordinary `global.window_group` sibling order is insufficient for focused fullscreen composition on this setup.
- Fifth follow-up behavior change: keep proof and single full-frame raster actors on the safer target-window sibling model, but use target-window child attachment only for the cropped multi-region raster path used by normal runtime. Region coordinates are converted from GNOME global logical coordinates to target-window-local coordinates. This scopes the previously working active-fullscreen layer to small current raster regions instead of reintroducing full-monitor child actors.
- Fifth follow-up test type selection: source-contract tests are sufficient for this helper-only GJS parent/coordinate-selection change because no EDMC lifecycle hooks, preferences, settings replication, journal/dashboard callbacks, or backend policy contracts changed. Manual GNOME validation remains required for focused-fullscreen visibility and black-screen/focus-trap risk.
- Fifth follow-up tests run: `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_gnome_shell_extension_manifest.py overlay_client/tests/test_gnome_helper_presentation_runtime.py::test_selected_shell_raster_allows_focus_unreliable_fullscreen_target` passed with `51 passed`.

### Phase 17: Extended Hardening And Release Validation
- Goal: split the remaining GNOME Shell Raster risk into two separately measurable problems: long-session runtime pressure and shutdown/cleanup-induced fullscreen instability.
- Phase 17 is a hardening phase, not a feature-expansion phase. Do not promote GNOME Shell Raster to Auto/default or broad GNOME Wayland support while either issue remains open.
- Validation must include game relaunches, EDMC restarts/shutdowns, helper reload/disable, GNOME overview/Alt-Tab cycles, monitor moves, resolution/mode changes, workspace changes, stale-frame cleanup, and performance under real overlay updates.
- Release support must remain conservative if Phase 17 finds stale actors, focus traps, Shell churn, bad shutdown cleanup, windowed fallback regressions, or unbounded runtime pressure.

#### Phase 17 Current Failure Evidence
- Long-session report, 2026-06-27: after a borderless/fullscreen session with `GNOME Shell Raster` active, the user observed signs of resource pressure. EDMC shutdown was followed by Elite black screen and Alt-Tab trap while Elite remained running.
- Prior short-window `pidstat` captures did not implicate simple CPU saturation, RSS growth, or disk I/O as sufficient explanations. Treat the long-session symptom as possible event-loop, compositor, GPU/texture, DBus, file-descriptor, timer, actor, socket, journal/logging, or Proton/launcher pressure until proven narrower.
- Pre-disable capture: `/home/jon/edmc-logs/EDMCModernOverlay/focused_overlay_retest_20260627_084018.log`. EDMC and `overlay_client` were absent, the GNOME helper was healthy, Elite target `meta:740` was fullscreen at `3440x1440`, and actor diagnostics showed the Elite actor with `child_count=1`. No stale Shell raster children were attached at capture time.
- Pre-disable process snapshot: Elite `EliteDangerous6` used about `4.25 GB` RSS, `EDLaunch.exe` used about `3.0 GB` RSS, and `gnome-shell` used about `547 MB` RSS. Treat these as a single data point, not a baseline.
- Live helper-disable test: disabling `edmc-modern-overlay-helper@edmcmodernoverlay.github.io` made helper DBus health fail with `ServiceUnknown`, but the user reported the black screen and Alt-Tab trap continued.
- Post-disable capture: `/home/jon/edmc-logs/EDMCModernOverlay/focused_overlay_retest_20260627_084404.log`. EDMC and `overlay_client` were absent, helper DBus was unavailable, and Elite remained in the bad fullscreen state.
- Current interpretation: Phase 17 now has two separate failure classes. First, Elite/NVIDIA/GNOME can produce black-screen, Alt-Tab trap, Super-key failure, audio pressure, and compositor symptoms with EDMC, `overlay_client`, and the GNOME helper fully out of path. Second, the overlay/helper can still be a pressure amplifier when enabled in an already stressed fullscreen game session through Shell-raster actor/texture work, helper DBus/log cadence, focus/overview churn, or compositor sampling of helper/client surfaces. Do not treat every black-screen trap as overlay-owned, but keep reducing overlay-owned pressure sources because they may still push the session over the edge.
- Runtime pressure captures, 2026-06-27: baseline `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_baseline_20260627_092047.log`, soak samples `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_soak_sample_20260627_095156.log` and `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_soak_sample_20260627_095329.log`, and Firefox/taskbar symptom sample `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_soak_sample_firefox_unresponsive_taskbar_flash_20260627_095409.log`.
- Runtime pressure interpretation: EDMC and `overlay_client` did not show FD/RSS growth across the samples. EDMC stayed at about `50` FDs and `174 MB` RSS; `overlay_client` stayed at about `29` FDs and `109 MB` RSS. Overlay log cadence stayed around `4.3-4.5` lines/sec with about `1.0` presentation attempt/sec. System RAM, swap, and disk I/O pressure stayed normal for the bad-state samples.
- GPU pressure finding: NVIDIA memory use rose from `9556 MiB / 11264 MiB` at baseline, with Elite at `8438 MiB`, to `10752 MiB / 11264 MiB` during the Firefox/taskbar symptom, with Elite at `9927 MiB`. The kernel logged `Failed to allocate NVKMS video memory for GEM object, trying to fall back to sysmem` at `09:53:22` and `09:53:51`.
- Shell-raster correlation: the first NVKMS allocation fallback at `09:53:22` occurred immediately after the helper created and attached three Shell-raster region actors under the fullscreen Elite target window actor. Actor create/apply/destroy counts remained balanced in the captures, so this is not currently an actor-count leak. The current leading theory is GPU/texture allocation churn while Elite is already close to VRAM exhaustion.
- User-visible pressure symptom: during the Firefox/taskbar sample, Firefox stopped responding to mouse clicks. Attempting to restart Firefox caused rapid taskbar flashing and no browser window appeared. This aligns better with GNOME/NVIDIA/VRAM pressure than with EDMC CPU, system RAM, swap, or disk I/O saturation.
- Recovery observation: before logging out, the user closed Elite and then Firefox reopened normally while EDMC was still running. VS Code remained unresponsive until logout/login. This suggests Elite/GPU pressure is a primary trigger and EDMC alone is not enough to keep Firefox broken, but the desktop session can remain partially wedged after the pressure event.
- Post-mitigation validation, 2026-06-27 through 2026-06-28: after the transient Shell-raster suspend/reuse patch, the user reported more than two hours of clean game-plus-overlay runtime, clean EDMC shutdown, and clean Firefox restart. Captures include `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_soak_sample_after_raster_suspend_patch_20260627_125746.log`, `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_post_edmc_shutdown_confirmed_clean_after_raster_suspend_patch_20260627_155829.log`, and `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_post_heavy_use_edmc_shutdown_after_raster_suspend_patch_20260627_165421.log`.
- Long game-plus-overlay observation, 2026-06-28: `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_long_soak_currently_clean_game_plus_overlay_20260628_064925.log` was captured after a long run where the game and overlay still appeared fine. Firefox flashing later reproduced while the game and overlay remained usable; closing EDMC did not clear the Firefox flashing, but closing Elite and restarting Firefox recovered the browser. Related captures: `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_firefox_still_flashing_after_edmc_shutdown_game_running_20260628_065732.log` and `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_firefox_recovered_after_elite_exit_and_firefox_restart_20260628_070159.log`.
- Game-only controls, 2026-06-28: with the helper disabled and EDMC/`overlay_client` stopped, Elite still produced pressure symptoms and high GPU memory use. `runtime_pressure_game_only_discord_audio_scratching_20260628_074716.log` showed scratchy Discord audio with GPU memory at `7139 MiB / 11264 MiB`, Elite at `6223 MiB`, and GNOME Shell at `404 MiB`. `runtime_pressure_game_only_late_soak_20260628_132832.log` later showed `10745 MiB / 11264 MiB`, Elite at `9881 MiB`, and GNOME Shell at `337 MiB`. `runtime_pressure_game_only_12h_soak_20260628_214539.log` still showed `10608 MiB / 11264 MiB`, Elite at `9675 MiB`, and GNOME Shell at `413 MiB`. After Elite exit, `runtime_pressure_game_only_after_elite_exit_20260628_214740.log` dropped to `1034 MiB / 11264 MiB` with no Elite process.
- Game-only caveat updated, 2026-07-02: earlier game-only controls had not reproduced Firefox blinking, but later controls did reproduce black-screen and Alt-Tab/Super-key trapping with helper disabled and EDMC never started after reboot. The working model is therefore not "Elite alone explains everything" and not "the helper explains every trap"; it is "Elite/Proton/NVIDIA/GNOME owns an independent fullscreen failure path, and overlay/helper work may still aggravate resource pressure or presentation failure in adjacent runs."
- No-game overlay controls, 2026-06-29: `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_overlay_only_8h_soak_20260629_072435.log` is an EDMC-only/helper-disabled control, not a valid overlay-client/helper soak, because helper DBus returned `ServiceUnknown` and `overlay_client` was absent. The corrected initial no-game capture `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_overlay_client_helper_enabled_no_game_initial_20260629_073828.log` had EDMC PID `212968`, `overlay_client` PID `212983`, helper health healthy, helper target state `launcher_only`, no Elite target, and low GPU memory at `1174 MiB / 11264 MiB`.
- Idle no-target finding, 2026-06-29: with `overlay_client` and the helper active but no game target, the client still polls/presents about every `0.5s`, logs repeated `target=launcher_only` / `state=malformed_payload`, and asks the helper for repeated `explicit_clear` operations. Actor counts are zero, so this is not Shell-raster texture churn, but it is idle DBus/journal/log chatter. Track follow-up reduction in GitHub issue `https://github.com/SweetJonnySauce/EDMCModernOverlay/issues/247`.
- Game-plus-overlay Firefox blinking reproduction, 2026-06-29: `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_firefox_blinking_game_overlay_running_after_1h_20260629_084454.log` captured Firefox blinking after about one hour with Elite, EDMC, `overlay_client`, and the helper active. GPU memory was `10769 MiB / 11264 MiB`, Elite used `9966 MiB`, GNOME Shell used `318 MiB`, and Firefox used `96 MiB`. The helper was reusing existing raster region actors with `helper_decode_skipped=True`, `helper_reused_frame=True`, and `helper_update_reason='reused_existing_regions'`; this capture does not show fresh helper-side PNG decode/texture allocation as the immediate trigger.
- EDMC shutdown control for the same 2026-06-29 reproduction: after EDMC and `overlay_client` were stopped, `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_firefox_blinking_after_edmc_shutdown_game_running_20260629_084707.log` still showed Firefox blinking with Elite running. GPU memory remained high at `10751 MiB / 11264 MiB`, Elite still used `9966 MiB`, GNOME Shell used `337 MiB`, and Firefox logged repeated `[GFX1]: Error in eglSetDamageRegion: 0x3009`. This proves the active EDMC/overlay client was not maintaining the bad Firefox state in this run.
- Elite-exit recovery for the same 2026-06-29 reproduction: `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_firefox_blinking_after_elite_exit_before_firefox_restart_20260629_084934.log` was captured after Elite exited but before Firefox was restarted. GPU memory had dropped to `1007 MiB / 11264 MiB`, no Elite process remained, GNOME Shell used `418 MiB`, and Firefox still had earlier EGL damage-region errors in the journal tail. After Firefox restart, `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_firefox_recovered_after_elite_exit_and_firefox_restart_again_20260629_085012.log` showed GPU memory at `1020 MiB / 11264 MiB`, no Elite process, and the user observed Firefox opening normally. This strengthens the model that Elite/NVIDIA/GNOME VRAM pressure can wedge Firefox presentation independently, while the browser process may still need restart after pressure is released.
- Helper-disabled overlay-client A/B blocker, 2026-06-29: the intended `game + EDMC/overlay_client + helper disabled` run was invalid because `overlay_client` crashed during startup before it could remain active. The EDMC debug log showed repeated watchdog launches ending in `KeyError: 'target_token'` from `overlay_client/follow_surface.py` while logging a degraded/malformed missing-helper presentation result. Capture `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_game_plus_overlay_client_helper_disabled_initial_20260629_134158.log` showed helper disabled, EDMC present, no persistent `overlay_client`, GPU memory at `10578 MiB / 11264 MiB`, Elite at `9385 MiB`, and GNOME Shell at `496 MiB`. A follow-up symptom capture `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_game_plus_overlay_VS_code_just_hanged_20260629_134526.log` showed VS Code hanging under similar high GPU pressure while `overlay_client` was still not running. This made the missing-diagnostic crash fix a prerequisite for the helper-disabled overlay-client A/B stage.
- Helper-active no-EDMC audio pressure, 2026-07-01: after reboot with EDMC and `overlay_client` absent, the user reported scratchy Discord audio while the helper was still active. Capture `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_game_only_discord_audio_scratchy_after_reboot_edmc_never_started_20260701_172658.log` showed helper health healthy, target found, GPU memory at `10572 MiB / 11264 MiB`, Elite at `9784 MiB`, and NVKMS fallback messages. After helper disable in the same session, `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_game_only_discord_audio_improved_after_helper_disable_same_session_20260701_173540.log` showed helper DBus `ServiceUnknown`, EDMC/`overlay_client` still absent, GPU memory still high at `10707 MiB / 11264 MiB`, and NVKMS messages continuing. This suggests the helper can aggravate user-visible pressure even without `overlay_client`, but the underlying GPU pressure was not created or cleared solely by the helper.
- Helper-disabled black-screen independent repro, 2026-07-02: after reboot, with helper disabled and EDMC never started, the user reported black screen, Alt-Tab trap, and Super-key failure. Capture `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_game_only_black_screen_alt_tab_trap_after_reboot_helper_disabled_edmc_never_started_20260702_125050.log` showed helper DBus `ServiceUnknown`, no EDMC/`overlay_client`, GPU memory at `7656 MiB / 11264 MiB`, Elite at `6735 MiB`, no direct NVKMS/Xid/EGL markers in the checked tail, and GNOME Shell/Mutter messages including a stack-position assertion, repeated game-window MWM hint warnings, and `clutter_frame_clock_dispatch: code should not be reached`. After killing Elite, `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_game_only_after_elite_kill_recovery_helper_disabled_edmc_never_started_20260702_125418.log` showed no Elite process, the launcher/Proton wrapper still present, helper still disabled, no EDMC/`overlay_client`, and GPU memory down to `924 MiB / 11264 MiB`. This proves at least one black-screen/Alt-Tab trap path is outside the overlay.

#### Phase 17 Boundary Update
- Release and debug language must separate overlay-owned pressure/churn from the external Elite/Proton/NVIDIA/GNOME fullscreen trap. The overlay can still be a catalyst and must be hardened, but the July 2 helper-disabled/EDMC-never-started repro means GNOME Shell Raster cannot be treated as the sole root cause of black-screen trapping.
- Continue Phase 17 overlay work on the surfaces we control: reduce idle no-target chatter, make helper behavior inert when no active presentation session exists, keep raster actor reuse bounded, and make shutdown cleanup conservative. Track the independent game/driver trap as a support caveat and as context for validation, not as a blocker that overlay code can fully fix.

#### Phase 17 Online Research Findings
- Research recorded on 2026-06-29. These findings are external corroborating evidence only; they do not prove the overlay bug by themselves. They do, however, closely match the observed symptom cluster: high NVIDIA VRAM use, NVKMS GEM allocation failures, Wayland/GNOME presentation stalls, Firefox window blinking or invisible window contents, audio continuing while rendering is wedged, and recovery only after the high-VRAM game exits.
- NVIDIA open kernel module source contains the matching failure string, `Failed to allocate NVKMS video memory for GEM object, trying to fall back to sysmem`, in the NVIDIA DRM NVKMS GEM memory allocation path. This supports interpreting our journal line as a failed video-memory allocation with a fallback attempt, not as an EDMC process-memory leak. Source: `https://raw.githubusercontent.com/NVIDIA/open-gpu-kernel-modules/main/kernel-open/nvidia-drm/nvidia-drm-gem-nvkms-memory.c`.
- NVIDIA forum reports on Linux VRAM exhaustion describe browser launch/render failures, desktop instability, and `Failed to allocate NVKMS memory for GEM object` when VRAM fills. This matches our Firefox blinking/invisible-window behavior under `10700+ MiB / 11264 MiB` GPU memory pressure, but those reports are broader NVIDIA/Linux behavior, not EDMC-specific evidence. Source: `https://forums.developer.nvidia.com/t/non-existent-shared-vram-on-nvidia-linux-drivers/260304`.
- A separate NVIDIA Wayland forum thread describes sporadic application render freezes where audio and input continue, and includes `Failed to allocate NVKMS memory for GEM object` in logs. That closely matches our distinction between the game/desktop still partially running and client windows failing to present. Source: `https://forums.developer.nvidia.com/t/wayland-applications-freezing-sporadically-suspected-vram-issues/329684`.
- A 2026 NVIDIA forum report about driver `595.71.05` claims VRAM may not be reclaimed for sampled cross-process `dma_buf` imports until the importing process exits. This is especially relevant because Wayland compositors sample client buffers across processes, and our helper path adds compositor-owned Shell-raster actors/textures. Treat this as a high-value hypothesis to test, not as confirmed root cause. Source: `https://forums.developer.nvidia.com/t/bug-report-vram-not-reclaimed-for-sampled-cross-process-dma-buf-imports-in-595-71-05-driver/374816`.
- Firefox's `[GFX1]: Error in eglSetDamageRegion: 0x3009` maps to `EGL_BAD_MATCH`. The Khronos `EGL_KHR_partial_update` specification says `eglSetDamageRegionKHR` can raise `EGL_BAD_MATCH` when the surface is not postable, is not the current draw surface, or has incompatible swap behavior. In our captures, this is best treated as Firefox failing its EGL partial-update path after the compositor/GPU state is already unhealthy, not as the first cause. Sources: `https://raw.githubusercontent.com/KhronosGroup/EGL-Registry/main/api/EGL/egl.h` and `https://raw.githubusercontent.com/KhronosGroup/EGL-Registry/main/extensions/KHR/EGL_KHR_partial_update.txt`.
- Follow-up black-screen research recorded on 2026-07-02. The closest direct external match is Valve Proton issue `6434`, where Elite Dangerous is explicitly listed and the reported symptom is that the game goes black after Alt-Tab/switching to another program and then stops responding. Treat this as strong precedent for an Elite/Proton fullscreen transition failure independent of this overlay. Source: `https://github.com/ValveSoftware/Proton/issues/6434`.
- Valve's main Elite Dangerous Proton issue remains active and carries NVIDIA-driver and regression labels. Its original report is not the same Alt-Tab trap, but it establishes Elite Dangerous as a long-running Proton compatibility surface with driver involvement. Source: `https://github.com/ValveSoftware/Proton/issues/150`.
- The Mutter warning `meta_window_set_stack_position_no_sync: assertion 'window->stack_position >= 0' failed` appears in unrelated GNOME Shell/Wayland failure reports involving tiling, focus flicker, dock flashing, disappearing workspace/window state, and Alt-Tab-visible apps. These reports are not Elite-specific, but they support interpreting our log as GNOME Shell's window stack entering invalid state rather than as an EDMC/overlay diagnostic. Sources: `https://github.com/forge-ext/forge/issues/531`, `https://github.com/MoonshotAI/kimi-code/issues/1090`, and `https://github.com/material-shell/material-shell/issues/955`.
- Mutter source confirms that `meta_window_set_stack_position_no_sync` guards against windows with negative stack positions before changing stacking order. Seeing that assertion during the bad Elite session means Mutter tried to stack a window whose stack position was already invalid or removed. This is a compositor/window-manager invariant failure at the GNOME layer. Source: `https://gitlab.gnome.org/GNOME/mutter/-/raw/gnome-46/src/core/stack.c`.
- Mutter/Clutter source shows `clutter_frame_clock_dispatch` is part of the compositor frame-clock state machine. The logged `code should not be reached` message is emitted by GLib/Mutter unexpected-state checks in that code path. In our 2026-07-02 capture, those frame-clock warnings are best treated as evidence that GNOME Shell/Clutter had entered an unexpected presentation state during/after the Elite fullscreen transition, not as evidence of overlay helper activity. Source: `https://gitlab.gnome.org/GNOME/mutter/-/raw/gnome-46/clutter/clutter/clutter-frame-clock.c`.
- Updated working model: Elite is the dominant VRAM consumer and can independently drive NVIDIA/GNOME near failure, including at least one black-screen/Alt-Tab trap with EDMC and the helper out of path. The overlay/helper is still a likely catalyst for some pressure runs: Shell-raster actor/texture work, compositor sampling of overlay/client buffers, helper DBus/log cadence, or focus/overview presentation churn may be enough to push an already high-VRAM session into a bad Wayland presentation state.
- Next evidence needed: run a stricter A/B matrix that isolates `overlay_client` and helper capabilities under the same Elite load: game-only with helper disabled; game plus EDMC/overlay_client with helper disabled; game plus helper enabled with `raster_actor_enabled=false`; and game plus helper enabled with `raster_actor_enabled=true`. If Firefox blinking appears before raster actors are enabled, the client/Qt/Wayland surface or DBus cadence is suspect. If it appears only with raster actors enabled, Shell-raster texture/compositor sampling remains the primary overlay-owned suspect.

#### Phase 17.5 Missing-Helper Crash Fix Notes
- Plan recorded before code edits on 2026-06-29, per `AGENTS.md`.
- Touch points: `overlay_client/follow_surface.py`, `overlay_client/tests/test_follow_surface_mixin.py`, and this document. Preserve the `fix219` backend boundary; do not touch `load.py`, backend selection policy, helper GJS, preferences, or settings replication.
- Invariant: degraded, missing-helper, launcher-only, or malformed backend presentation diagnostics may hide/degrade presentation, but they must not crash the overlay client or trigger a watchdog restart loop.
- Test type selection: unit test the follow-surface logging/visibility path with partial diagnostics. No harness test is required because EDMC lifecycle wiring and plugin startup/shutdown are not changed.
- Implementation: `_log_backend_presentation_result` now reads diagnostic fields defensively with `.get()` defaults instead of indexing required keys such as `target_token`. Healthy/full diagnostics keep the same log shape; partial diagnostics still produce a useful degraded log line.
- Runtime validation completed on 2026-06-29: after the missing-diagnostic crash fix, helper-disabled runs could keep both EDMC and `overlay_client` alive. Captures include `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_game_plus_overlay_client_helper_disabled_with_client_after_crash_fix_20260629_135319.log` and `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_helper_disabled_overlay_client_alive_clean_soak_20260629_145805.log`. Helper-enabled restart validation then showed the overlay again after EDMC restart, with captures `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_helper_enabled_overlay_client_restarted_initial_20260629_150330.log` and `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_helper_enabled_overlay_client_restarted_clean_soak_20260629_171850.log`.

#### Phase 17.5 Missing-Helper Crash Fix Tests Run
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_surface_mixin.py`
- Result: passed with `18 passed`.

#### Phase 17 Research Documentation Tests Run
- `git diff --check -- docs/refactoring/gnome_wayland_presentation_attachment.md`
- Result: passed.
- 2026-07-02 boundary update: `git diff --check -- docs/refactoring/gnome_wayland_presentation_attachment.md`
- Result: passed.
- 2026-07-02 external black-screen research update: `git diff --check -- docs/refactoring/gnome_wayland_presentation_attachment.md`
- Result: passed.
- Unit/harness tests: not added or run. Reason: this update documents external research findings only and does not change plugin lifecycle, backend runtime, helper GJS, preferences, settings replication, or pure helper/service behavior.

#### Phase 17 Test Type Selection
- Phase 17.2 implementation touches a standalone passive shell diagnostic script and this documentation only. No unit or harness tests are required because no plugin lifecycle, EDMC hook flow, backend runtime, helper GJS, preferences, or settings replication behavior changes.
- Future runtime-pressure telemetry changes should use unit tests for pure samplers, parsers, counters, cache-prune decisions, event-loop lag calculations, and thresholds.
- Future helper GJS changes should use source-contract tests for safe clear/deferred destroy behavior, actor-parent rules, and diagnostic payload fields. Manual GNOME validation remains required for compositor-visible behavior.
- Future `overlay_client` shutdown/runtime changes should use unit tests for pure policy and runtime-state transitions. Add harness tests if `load.py`, EDMC hook flow, plugin startup/shutdown lifecycle, preferences, or settings replication are touched.
- Future soak validation is manual/system validation: capture resource snapshots over time, verify EDMC shutdown/restart behavior while Elite remains fullscreen, and confirm no black screen, Alt-Tab trap, titlebar fallback, or stale actor remains.

#### Phase 17 Refactor Staging
| Stage | Description | Status |
| --- | --- | --- |
| 17.1 | Record 2026-06-27 resource/shutdown failure evidence and update the risk model | Completed |
| 17.2 | Add deep runtime-pressure telemetry and capture support: process RSS/thread/FD/socket counts, event-loop lag, helper actor/timer counts, raster cache size, frame/region churn, DBus/journal/log volume, GPU/compositor/NVIDIA markers, Elite/launcher/gnome-shell state, and sampled pressure indicators | Completed for passive capture; future heartbeat/timer diagnostics remain optional follow-ups |
| 17.3 | Harden Shell-raster shutdown cleanup: hide/suspend immediately, stop new raster updates, and defer or avoid target-window-child actor destruction while fullscreen Elite is still present | Pending; explicit shutdown/helper-disable cleanup is still destructive |
| 17.4 | Bound long-session runtime pressure: prune raster/cache state, cap diagnostics sampling, verify actor/texture/timer reuse, reduce DBus/log churn, and log any skipped frames/regions explicitly | In progress; transient suspend/reuse mitigation implemented and early/overnight validation improved; idle no-target chatter remains tracked by issue #247 |
| 17.5 | Run A/B soak matrix: overlay off, helper enabled without raster, raster enabled, EDMC shutdown/restart while Elite remains running, helper disable/re-enable, and game relaunch | In progress; matrix now includes a helper-disabled/EDMC-never-started black-screen trap and helper-active/no-EDMC audio-pressure correlation, but the overlay-owned catalyst boundary is still incomplete |
| 17.6 | Resolve release blockers or downgrade support wording before release | Pending 17.5; release wording must distinguish overlay-owned pressure mitigation from external game/driver fullscreen traps |

#### Phase 17.2 Deep Runtime-Pressure Capture Plan
- First work product: add a dedicated deep capture script, tentatively `scripts/capture_runtime_pressure.sh`, instead of overloading the quick focused-overlay capture. The script should be passive, bounded, and safe to run while the system is already in a bad state.
- Decisions accepted on 2026-06-27: create a new script; use passive snapshots and short bounded samples only; keep stdout concise with `CAPTURE_LOG=...`; treat optional tools as nonfatal; defer event-loop heartbeat instrumentation until passive captures prove insufficient; summarize descriptor categories with short samples rather than dumping every path.
- Capture labels: support explicit labels such as `baseline`, `soak_sample`, `pre_edmc_shutdown`, `post_edmc_shutdown_bad_state`, and `post_recovery`. Every run should print `CAPTURE_LOG=...` to stdout, write a `.latest` pointer, and record the label in the log.
- Process census: capture EDMC, `overlay_client`, Elite, launcher, Steam/Proton wrapper, `gnome-shell`, Xwayland, and relevant NVIDIA helper process summaries. Include `pid`, `ppid`, `stat`, elapsed time, CPU percent snapshot, RSS, VSZ, thread count, command, and parent/child relationships.
- Descriptor/socket census: for each target process, count total file descriptors, sockets, pipes, eventfds, timerfds, inotify descriptors, memfds, deleted files, and open files under `/tmp`, `$XDG_RUNTIME_DIR`, and `/home/jon/edmc-logs`. Do not dump every descriptor path by default; summarize top categories and include a short sample.
- Kernel/process pressure: capture `/proc/pressure/{cpu,memory,io}` when available, `/proc/meminfo`, `free`, `vmstat` snapshot, `/proc/<pid>/status`, `/proc/<pid>/io`, and `/proc/<pid>/smaps_rollup` if readable. These are still supporting signals, not the primary theory.
- Overlay/client pressure: parse recent `overlay_client.log` lines for presentation cycles/sec, `ApplyPresentation` attempts, target polls, skipped cycles, raster frame build timing, PNG size, changed-region count, decode/apply timing, explicit clears, hidden/suspended transitions, and shutdown cleanup events.
- Event-loop lag: if existing logs do not expose it, add a low-overhead overlay-client heartbeat metric in a later implementation step. The heartbeat should report scheduler lag without calling GNOME helper APIs and should be unit-tested as pure timing/counter logic where possible.
- Helper diagnostics: capture `GetHealth`, `GetTargetState`, current target actor diagnostics, shell raster actor counts, actor parent type, region counts, visibility/mapped flags, last clear/apply decision, and any helper feature-gate state. If timer counts are not exposed, add helper diagnostics before using them as acceptance criteria.
- DBus/journal/log pressure: count helper-related DBus calls from overlay logs where possible, count log lines/sec for `overlay_client.log`, and capture filtered user/system journal windows for `edmc-modern-overlay-helper`, `edmc_modern_overlay_gnome_helper`, `gnome-shell`, `Mutter`, `clutter-frame-clock`, `NVIDIA`, `NVKMS`, `nvkms`, `nv_drm`, `Xwayland`, and Steam/Proton warnings.
- GPU/compositor indicators: capture `nvidia-smi` summary if available, but treat it as optional. Do not require privileged `/sys/kernel/debug/dri` or heavy tracing for the first pass. Record unavailable tools explicitly instead of failing the capture.
- Safety rules: avoid `strace`, `perf`, continuous `nvidia-smi dmon`, or high-frequency polling in the first implementation. The script should gather snapshots and short bounded samples only, because intrusive probes can change the timing of the bug.
- Decision rules:
  - If FD/socket/timer/thread/actor counts grow across soak samples, fix the owning leak or missing cleanup first.
  - If log/DBus/presentation cadence grows while counts stay stable, throttle or coalesce that path first.
  - If event-loop lag grows without CPU/RSS/disk pressure, prioritize overlay-client scheduling, helper call cadence, and compositor interaction.
  - If GPU/compositor journal markers appear near the bad state, prioritize shutdown cleanup conservatism and raster actor lifecycle changes.
  - If telemetry remains normal until EDMC shutdown, implement Phase 17.3 safe shutdown cleanup before broader resource tuning.

#### Phase 17.2 Implementation Notes
- Added `scripts/capture_runtime_pressure.sh` as a new dedicated passive capture script. It does not modify or depend on `scripts/capture_focused_overlay_retest.sh`.
- Stdout is intentionally concise: the script prints `CAPTURE_LOG=...`, a start line with the label, and a completion/failure line. Detailed output goes to `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure_<label>_<timestamp>.log`, and `/home/jon/edmc-logs/EDMCModernOverlay/runtime_pressure.latest` points at the latest log.
- Label support is free-form and sanitized for filenames. The intended labels remain `baseline`, `soak_sample`, `pre_edmc_shutdown`, `post_edmc_shutdown_bad_state`, and `post_recovery`.
- Captured process data includes matched process command lines, `ps` summaries, optional `pstree` ancestry, descriptor summaries, short `lsof` samples, `ss` socket samples, `/proc/<pid>/status`, `/proc/<pid>/io`, `/proc/<pid>/smaps_rollup`, and process children where readable.
- Descriptor output is category-based and sampled. It counts total descriptors, sockets, pipes, eventfds, timerfds, inotify descriptors, memfds, deleted paths, `/tmp`, `$XDG_RUNTIME_DIR`, EDMC log paths, and Shell-raster paths, then includes only a short FD sample.
- Captured system pressure includes `/proc/pressure/{cpu,memory,io}` when available, `/proc/meminfo`, `free -h`, a bounded `vmstat 1 2`, uptime, and a targeted `df` snapshot.
- Captured overlay/helper data includes Shell-raster cache summaries, helper `GetHealth`, helper `GetTargetState`, passive `diagnose_groups` actor diagnostics for the current target token, recent `overlay_client.log` counts/rates from the latest 1000 lines, recent overlay log tail, and EDMC debug log tail.
- Captured journal/GPU data includes bounded filtered user/system journal windows and optional `nvidia-smi` plus one `nvidia-smi pmon -c 1` sample when available. Missing tools or read-protected files are logged as unavailable instead of failing capture.
- Audio glitch evidence added on 2026-06-27: scratchy speaker output is a user-visible resource-pressure symptom. The capture script now includes PipeWire, WirePlumber, PulseAudio, ALSA, xrun, underrun, and audio markers in process/journal collection, plus optional `systemctl --user`, `pactl`, `wpctl`, `pw-cli`, and `/proc/asound` snapshots when available.
- Firefox/taskbar evidence added on 2026-06-27: Firefox click failure and taskbar flashing are user-visible compositor/session pressure symptoms. The capture script now includes Firefox and `xdg-desktop-portal` / `xdg-document-portal` process and journal probes. The first Firefox/taskbar symptom capture was recorded before those probes were added, so it only captured Firefox through actor diagnostics and `nvidia-smi`; future captures should include first-class Firefox/portal process details.
- Known limitation: the script does not add event-loop heartbeat instrumentation. If passive captures do not explain the long-session pressure, add a low-overhead overlay-client heartbeat in a later stage with unit coverage for pure timing/counter logic.
- Known limitation: helper timer counts are not currently exposed over DBus. This script captures actor/group diagnostics already available through `diagnose_groups`; helper-side timer diagnostics would require a later helper GJS change and source-contract tests.

#### Phase 17.2 Tests Run
- `bash -n scripts/capture_runtime_pressure.sh`
- Result: passed.
- `bash scripts/capture_runtime_pressure.sh --help`
- Result: passed; printed usage without creating a capture log.
- Audio-marker follow-up: updated `scripts/capture_runtime_pressure.sh` to include audio service/process/journal/status probes after scratchy speaker output was identified as a pressure symptom.
- Firefox/portal follow-up: updated `scripts/capture_runtime_pressure.sh` to include Firefox and portal service process/journal probes after Firefox click failure and taskbar flashing were identified as pressure symptoms.
- `git diff --check -- scripts/capture_runtime_pressure.sh docs/refactoring/gnome_wayland_presentation_attachment.md`
- Result: passed.
- Unit/harness tests: not added or run. Reason: Phase 17.2 added a standalone passive shell capture script and documentation only; no EDMC lifecycle, backend runtime, helper GJS, preferences, settings replication, or pure Python helper/service logic changed.

#### Phase 17 Remediation Approach
- First, classify pressure before optimizing. The next implementation step should make the existing capture path record enough deep telemetry to identify whether EDMC, `overlay_client`, the helper, GNOME Shell, Elite, the launcher, raster frame generation, compositor/GPU work, DBus/journal churn, event-loop lag, file-descriptor/socket growth, actor/timer accumulation, or raster cache growth is the dominant pressure source. CPU/RSS/disk snapshots alone are not sufficient.
- Second, make shutdown cleanup conservative. On EDMC or `overlay_client` shutdown, the Shell-raster path should stop presenting new frames and make actors invisible quickly, but avoid aggressive target-window-child removal while a fullscreen target is still alive unless a follow-up capture proves that immediate removal is harmless.
- Third, bound runtime pressure. Once telemetry identifies the growth surface, cap or prune that surface with explicit diagnostics so the long-session path cannot silently accumulate raster frames, temporary files, GJS actors, textures, timers, sockets, DBus traffic, or log volume.
- Fourth, validate with A/B soaks. The overlay-owned pressure path must be tested with helper disabled, helper enabled but raster inactive, raster active, and no active game target, and each pass should include EDMC shutdown while Elite remains running when practical. A short clean startup test is not sufficient for Phase 17. The known helper-disabled/EDMC-never-started trap must be documented separately as an external game/driver/compositor failure path.
- Operational note: after live helper-disable diagnostics, re-enable the helper before raster retests with `gnome-extensions enable edmc-modern-overlay-helper@edmcmodernoverlay.github.io`.

#### Phase 17.3/17.4 First Mitigation Plan
- Plan recorded before code edits on 2026-06-27, per `AGENTS.md`.
- Touch points: `helpers/gnome_shell_extension/extension.js` for helper-side Shell-raster lifecycle behavior, `overlay_client/tests/test_gnome_shell_helper_extension_source.py` for source-contract tests, and this document for implementation/test evidence. Do not touch backend policy or generic follow/runtime surfaces.
- Invariants: `target_not_focused` and `gnome_overview_active` are transient clears that should hide existing Shell-raster actors and keep their identity records for bounded reuse; stale timeout and real cleanup/error paths must still destroy actors; hidden actors must not remain visible, must not persist forever, and must remain gated by existing helper feature gates.
- Test type selection: use source-contract tests for GNOME Shell JS because normal pytest cannot execute Mutter/GJS actor behavior. No harness test is required unless `load.py`, EDMC lifecycle wiring, preferences, settings replication, or overlay-client backend code is touched.
- Runtime validation plan: after unit/source checks pass, run one short in-game soak with `bash scripts/capture_runtime_pressure.sh soak_sample_after_raster_suspend_patch`; if it does not reproduce black screen, Alt-Tab trap, app flashing, or NVKMS pressure, proceed to a longer soak before considering Phase 17.3/17.4 complete.

#### Phase 17.3/17.4 First Mitigation Implementation Notes
- Implemented on 2026-06-27. The GNOME helper now treats only `target_not_focused` and `gnome_overview_active` as transient Shell-raster clears.
- Transient clears call a bounded suspend path: existing single-frame and multi-region Shell-raster actors are hidden, their records are retained, and diagnostics emit `raster_actor_suspend_decision` plus `raster_clear_decision` with `cleanup_action="suspend_transient_clear"` when actors were present.
- The suspend path intentionally does not remove or refresh the existing Shell-raster stale timeout. If the target does not resume and reuse the actors before that timer fires, the existing `stale_timeout` path still performs destructive cleanup.
- Reuse now emits `raster_actor_reuse_decision` with `was_suspended` so soak captures can distinguish hidden-actor reuse from fresh texture decode/allocation. Existing reuse still shows/re-raises actors and refreshes the stale timeout only after an eligible frame is presented again.
- Destructive cleanup remains unchanged for `stale_timeout`, `helper_disable`, invalid frames, decode/apply failure, missing parent, stale region removal, session/identity replacement, explicit clear/replacement, and other non-transient reasons.
- Known limitation: this is not the full Phase 17.3 shutdown cleanup hardening. EDMC shutdown/helper-disable explicit cleanup is still destructive and remains a separate stage.
- Known limitation: this does not reduce Elite VRAM use directly. It reduces helper-side Clutter texture allocation churn during focus/overview transitions so the next soak can test whether NVKMS fallback pressure becomes less likely.

#### Phase 17.3/17.4 First Mitigation Tests Run
- `bash -n scripts/capture_runtime_pressure.sh`
- Result: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py tests/test_gnome_shell_extension_manifest.py`
- Result: passed with `51 passed`.
- `git diff --check -- helpers/gnome_shell_extension/extension.js overlay_client/tests/test_gnome_shell_helper_extension_source.py docs/refactoring/gnome_wayland_presentation_attachment.md scripts/capture_runtime_pressure.sh`
- Result: passed.
- Test files updated: `overlay_client/tests/test_gnome_shell_helper_extension_source.py`.
- Harness tests: not added or run. Reason: this change does not touch `load.py`, EDMC lifecycle wiring, preferences, settings replication, or overlay-client backend/runtime policy.

### Phase 18: Stable Managed-Window Preparation And Multi-Monitor Transitions
- Status: In progress. Initial windowed-mode live validation passed stable attachment and two-way monitor handoff, but exposed a visible remap-warmup intermediate and confirmed that Linux standalone selection is still incorrectly unavailable. Borderless round-trip validation also remains pending.
- Goal: stop GNOME/Wayland windowed-mode flashing by separating presentation refresh from destructive Qt surface preparation while preserving focus-aware visibility and correct multi-monitor following.
- Failure evidence, 2026-07-12: changing Elite from borderless fullscreen to windowed mode correctly selected managed PyQt presentation, but helper focus samples changed repeatedly and the client prepared the managed surface about every `500 ms`. The overlay stayed logically visible, which localizes the flashing risk to repeated mapped-surface flag, state, screen, geometry, and platform mutations rather than visibility-policy hide/show decisions.
- Multi-monitor evidence: during the same transition, the stable Elite target token was first reported on HDMI-1 and then on DP-2 while Proton/GNOME settled the new windowed geometry. Multi-monitor following is a required contract. Transitional samples must not cause repeated mappings, while a stable real monitor change must cause exactly one screen transition.

#### Phase 18 Plan And Invariants
- Touch points: `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`, `overlay_client/follow_surface.py`, `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, `overlay_client/tests/test_follow_surface_mixin.py`, and this document. `overlay_client/interaction_controller.py` and its unit tests are optional only if generic flag idempotence cannot be kept inside the existing surface-preparation consumer.
- Unchanged behavior: focus remains part of backend presentation and visibility policy; Shell-raster fullscreen presentation and transition clear behavior remain backend-owned; generic follow/runtime code does not inspect raw GNOME helper/backend enums; genuine target, mode, geometry, monitor, screen, or surface-loss changes remain recoverable.
- Preparation identity includes preparation mode, target token, requested target rectangle, rectangle source, target monitor identity/rectangle, and the selected generic Qt screen where the consumer resolves it. Negative and vertically offset global coordinates remain valid.
- Cache only successful surface preparations. Invalidate on target loss, mode change, target-token change, requested-rectangle change, monitor/screen change, fullscreen/windowed transition, preparation failure, or confirmed surface loss.
- Focus-only and visibility-only presentation changes may refresh helper presentation and visibility policy but must not reprepare an unchanged mapped Qt surface.
- A new or changed managed-window identity must stabilize for two compatible target samples before preparation. The existing stable preparation remains authoritative during a pending move; a stale surface must never be presented concurrently on both monitors.
- Genuine surface loss may retry the same preparation only through a bounded recovery interval, never at the normal `500 ms` poll cadence.
- Generic Qt preparation is defensive and idempotent: do not reapply window state, screen, geometry, or identity flags when current state already proves the requested value.
- Observability remains low-overhead: cycle diagnostics report preparation applied, reused, stabilization pending, invalidated, failed, or bounded recovery without introducing release-only polling or compositor calls.
- A newly mapped managed surface may exist long enough for the helper to discover and place it, but its rendered content must stay suppressed until the helper reports the overlay window at the requested rect. The bounded warmup fallback remains available if confirmation never arrives.
- The managed PyQt surface used for GNOME windowed mode must be absent from taskbar/window-list and Alt-Tab surfaces in normal mode. Explicit standalone mode must be user-selectable on Linux and must restore normal app-window listing for that managed surface. Borderless fullscreen continues to use the Shell-raster path, which suppresses the PyQt top-level and remains non-standalone. GNOME-specific window-list control and cleanup remain helper-owned under `overlay_client/backend/` and `helpers/gnome_shell_extension/`; generic follow/runtime code only forwards the existing setting and consumes backend-neutral visibility decisions.
- Helper disable/reload must restore any window-list entries it hid so extension lifecycle changes cannot strand a live overlay in hidden app-window state.
- Rollback: the change is isolated to backend runtime state/decision helpers and generic no-op guards. Reverting Phase 18 restores the previous eager preparation path without changing helper protocol, settings, extension installation, renderer selection, or EDMC lifecycle wiring.

#### Phase 18 Test Type Selection
- Use unit tests for deterministic backend preparation identity, stabilization, invalidation, recovery timing, and generic Qt no-op behavior. Dependencies are injectable and no EDMC/plugin lifecycle wiring is involved.
- Use unit tests for remap content-suppression decisions, generic follow application, cross-platform standalone preference/payload behavior, and forwarding the existing standalone setting into the backend presentation consumer.
- Use GNOME Shell extension source-contract tests for `hide_from_window_list`/`show_in_window_list`, expected-state verification, and helper-disable restoration because normal pytest cannot execute Mutter/GJS window-list behavior.
- No harness test is required because Phase 18 does not touch `load.py`, plugin hooks, startup/shutdown orchestration, journal/dashboard callbacks, preferences, or settings replication.
- The existing preferences-to-client callback and settings replication wiring remain unchanged; their pure payload seam is covered by unit tests. If `load.py` or callback orchestration becomes necessary, add a harness test before that edit.
- Manual GNOME/Wayland validation remains required after automated gates because pytest cannot prove compositor-visible non-flashing, taskbar/Alt-Tab identity, real Qt surface recreation behavior, or physical monitor handoff.

#### Phase 18 Refactor Staging
| Stage | Description | Status |
| --- | --- | --- |
| 18.1 | Record the flashing evidence, multi-monitor contract, invariants, test selection, exact commands, and rollback boundary | Completed |
| 18.2 | Add pure backend-owned preparation identity and decision helpers; preserve focus in the full presentation signature | Completed |
| 18.3 | Add two-sample stabilization for new/changed managed-window monitor/geometry identities and bounded same-identity surface-loss recovery | Completed |
| 18.4 | Cache only successful preparations; invalidate on target/mode/geometry/monitor/failure transitions; expose diagnostic decision reasons | Completed |
| 18.5 | Add generic Qt no-op guards for unchanged screen, window state, geometry, and preparation identity without importing GNOME policy | Completed |
| 18.6 | Add unit coverage for focus-only refresh, invalidation/recovery, fullscreen/windowed handoff, multi-monitor moves, negative/offset layouts, monitor reconfiguration, and duplicate generic preparation | Completed |
| 18.7 | Run targeted pytest, full pytest, `make check`, `make test`, and `git diff --check`; record exact outcomes | Completed |
| 18.8 | Perform live GNOME/Wayland validation for windowed stability and DP-2/HDMI-1 handoff | Partial: stable attachment and two-way handoff passed; visible remap intermediate found; borderless round trip not yet run |
| 18.9 | Record the live remap/standalone findings, unchanged behavior, test selection, and helper lifecycle contract | Completed |
| 18.10 | Keep managed-window remap content suppressed until helper window discovery and matching applied-rect confirmation | Pending |
| 18.11 | Make standalone selection cross-platform and add helper-owned GNOME window-list hide/show plus disable-time restoration | Pending |
| 18.12 | Add unit/source-contract regression coverage and run targeted/full automated gates | Pending |
| 18.13 | Repeat live windowed movement, DP-2/HDMI-1 handoff, standalone off/on/off identity, and borderless/windowed round trip | Pending manual validation |

#### Phase 18 Planned Test Commands
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_presentation_policy.py`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_extension_source.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_control_surface_overrides.py tests/test_standalone_support.py tests/test_overlay_config_payload.py tests/test_preferences_persistence.py`
- If `overlay_client/interaction_controller.py` changes: `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_interaction_controller.py`.
- `source .venv/bin/activate && python -m pytest`
- `make check`
- `make test`
- `git diff --check`

#### Phase 18 Implementation Notes
- Added a backend-owned managed-surface preparation identity containing the generic preparation mode, target token, requested rectangle, rectangle source, helper monitor index/output/rectangle, and recovery intent. Focus remains in `GnomeHelperPresentationSignature`; it is intentionally not part of the preparation identity.
- New or changed managed-window identities require two compatible target samples. The first sample records `surface_preparation_action="stabilizing"`, does not call the Qt preparer, does not call helper presentation, and keeps the old surface hidden. This prevents a transient HDMI-1 sample from moving the old overlay before the DP-2 geometry settles.
- Successful preparations are cached separately from presentation freshness. Focus-only presentation refreshes now report `surface_preparation_action="reused"` and continue through helper presentation/visibility policy without mutating the Qt surface.
- Failed preparation is not cached and uses a `2.0s` retry interval. Four observed helper presentation samples without an overlay token permit a forced same-identity recovery, also bounded to `2.0s`, rather than retrying every `500 ms`.
- Target loss, renderer/mode change, target-token change, requested-rectangle change, monitor/output/monitor-rectangle change, or helper health loss invalidates pending/cached preparation state. Windowed-to-borderless Shell raster presentation clears the managed preparation and keeps the PyQt surface hidden.
- The generic Qt consumer now avoids redundant `setScreen`, `setWindowState`, `setGeometry`, identity-flag, platform-prepare, and click-through calls. Same-monitor moves update geometry only; monitor replacement or explicit recovery performs one identity refresh. Negative global coordinates are passed unchanged to `QGuiApplication.screenAt` and `QRect`.
- Diagnostics now include `surface_preparation_ready`, `surface_preparation_action`, and `surface_preparation_reason`, and those fields participate in debug-log deduplication.
- The `fix219` boundary remains intact: GNOME transition/stabilization/recovery policy stays under `overlay_client/backend/bundles/`; `follow_surface.py` consumes only the generic `BackendPresentationSurfacePreparation` contract.

#### Phase 18 Tests Run
- Test files updated: `overlay_client/tests/test_gnome_helper_presentation_runtime.py`, `overlay_client/tests/test_follow_surface_mixin.py`, and `overlay_client/tests/test_backend_consumers.py`.
- `overlay_client/.venv/bin/python -m pytest -q overlay_client/tests/test_gnome_helper_presentation_runtime.py -k "windowed or managed_window"`
- Result: passed with `10 passed, 59 deselected`.
- `overlay_client/.venv/bin/python -m pytest -q overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_presentation_policy.py`
- Result: passed with `71 passed`.
- `overlay_client/.venv/bin/python -m pytest -q overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_presentation_policy.py -k "not shell_raster_bridge_sends_static_frame_when_eligible"`
- Result: passed with `139 passed, 1 deselected`. The deselected pre-existing static proof test creates a `QPainter` without a `QGuiApplication` under the normal headless command and aborts the interpreter before pytest can report a result.
- `overlay_client/.venv/bin/python -m ruff check .`
- Result: passed.
- `overlay_client/.venv/bin/python -m mypy`
- Result: passed with `Success: no issues found in 92 source files`.
- `make check`
- Result: partial. Ruff and mypy passed; the nested `make test` aborted in the same pre-existing static PyQt proof test because the Makefile does not create a headless `QApplication`.
- `make test`
- Result: failed with exit `134` at `test_shell_raster_bridge_sends_static_frame_when_eligible` for the same missing-application precondition; it did not reach Phase 18 failures.
- `QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 overlay_client/.venv/bin/python -c 'from PyQt6.QtWidgets import QApplication; app = QApplication([]); import pytest; raise SystemExit(pytest.main(["-q", "-k", "not shell_raster_bridge_sends_static_frame_when_eligible"]))'`
- Result: passed with `1154 passed, 21 skipped, 1 deselected`. This is the full project suite with a headless `QApplication` and only the unrelated nondeterministic static proof test excluded.
- `git diff --check`
- Result: passed.
- Harness tests: not added. No `load.py`, EDMC hook/lifecycle orchestration, preferences, settings replication, journal callbacks, or dashboard callbacks changed.
- Manual/system validation: pending. Required evidence is one live borderless-to-windowed run, focus/Alt-Tab cycles without recurring preparation, same-monitor movement, DP-2/HDMI-1 handoff, return to borderless, and confirmation that logs show one preparation per stable identity rather than the prior `500 ms` loop.

#### Phase 18 Initial Live Validation Findings, 2026-07-14
- The overlay client was restarted into the current uncommitted code before validation. The GNOME helper was healthy and acquired Elite token `meta:578` in windowed mode.
- Initial windowed attachment, two same-monitor moves, DP-2 to HDMI-1, and HDMI-1 to DP-2 all stabilized. Each new identity produced one `stabilizing` sample followed by one `apply`; unchanged samples reported `reused`. No preparation failure or recurring `500 ms` preparation loop appeared.
- The user confirmed final attachment and both monitor directions were correct. All tests in this sample were windowed; borderless behavior was not exercised and remains pending.
- The visible defect occurs between the stabilization and settled samples: the overlay first disappears, then briefly appears monitor-relative, then attaches correctly to the game. Logs align this with the mapped remap warmup: the first post-prepare sample shows the Qt surface before the helper has found the overlay window, and the next sample reports a matching applied rect.
- `overlay_settings.json` and the live request both held `standalone_mode=false`, yet the normal PyQt top-level remained selectable in the taskbar/Alt-Tab. The Linux preferences control was disabled by the legacy Windows-only gate, so the user could not explicitly choose standalone versus normal identity.
- The user confirmed this standalone-like identity occurs in windowed mode only. Borderless fullscreen uses Shell-raster presentation and does not appear as a standalone/task-switcher window; that behavior must remain unchanged.
- Chosen remap correction: keep the surface mapped but suppress rendered content during warmup. This preserves helper discovery/placement while eliminating the visible monitor-relative intermediate. Restore content only after overlay-window discovery plus matching rect, or after the existing bounded fallback expires.
- Chosen standalone correction: retain one existing default-off preference across platforms. The GNOME helper owns compositor-specific window-list behavior using Mutter's supported hide/show window-list operations; false hides normal mode, true shows standalone mode, and helper disable restores entries hidden by the helper.

### Phase 19: Atomic Fullscreen Monitor Handoff Without Managed-Window Fallback Exposure
- Status: Planned on 2026-07-14. Live reproduction and settled-state evidence are captured; no Phase 19 runtime code has been implemented.
- Goal: preserve Shell-raster ownership while GNOME transiently changes Elite's fullscreen/maximized metadata during a Shift+Super+Arrow monitor move, so the managed PyQt fallback cannot appear as a standalone, decorated, focus-affecting top-level window.
- Scope boundary: Phase 19 fixes renderer ownership and surface lifecycle during a fullscreen monitor handoff. It does not redefine maximized windows as fullscreen, change normal managed-window behavior, or select a new Linux taskbar/Alt-Tab implementation.

#### Phase 19 Live Failure Evidence, 2026-07-14
- Normal startup in borderless fullscreen works: GNOME reports Elite token `meta:21` with `fullscreen=true`, frame/content rect `(0,0,3440,1440)`, monitor rect `(0,0,3440,1440)`, and Shell-raster regions remain attached and reusable.
- The failure is reproducible by moving the fullscreen game with Shift+Super+Arrow. During the handoff, GNOME temporarily reports the same Elite target as `fullscreen=false` with rect `(0,29,3440,1411)` against a `(0,0,3440,1440)` monitor. The missing 29 pixels are the GNOME top panel/work area, not Elite decoration; the target reports zero decoration insets.
- The runtime reacts to that transient sample as a real renderer-mode change and enters managed PyQt presentation. The helper finds overlay token `meta:30` and repeatedly attempts managed-window presentation while the game is in the transitional maximized state.
- `overlay_settings.json` holds `standalone_mode=false`, `keep_overlay_visible=false`, and `manual_backend_override="gnome_shell_raster"`. The failure is therefore not caused by selecting standalone mode or the wrong backend override.
- The live helper reports `window_list_visibility_decision` with `expected_hidden=true`, `supported=false`, `matchesExpected=false`, and `action="unsupported"`. The Phase 18 experimental `hide_from_window_list`/`show_in_window_list` approach is not available on this installed GNOME/Mutter runtime and must not be a prerequisite for Phase 19 correctness.
- Once GNOME settles, the same target returns to `fullscreen=true` and Shell-raster region reuse resumes. The bad state is the exposed intermediate/fallback lifecycle: the Qt top-level may remain standalone-like or decorated even though Shell raster has resumed.
- A separate earlier incident involved multiple overlay/raster producers racing over one helper surface. That lifecycle issue is real but is not required for this reproduction: the Shift+Super+Arrow failure was reproduced with one overlay client.

#### Phase 19 Plan And Invariants
- Fullscreen/borderless invariant: stable Shell-raster presentation owns rendering; the managed PyQt surface stays hidden and cannot appear in the taskbar, Alt-Tab, GNOME Overview, or with a title bar.
- Windowed invariant: initial and stable windowed targets continue directly through the existing Phase 18 managed-window path. Same-monitor geometry-only updates, cross-monitor preparation stabilization, negative/offset coordinates, focus policy, and explicit standalone selection remain unchanged.
- Transition invariant: one transient `fullscreen=false` sample cannot change renderer ownership when the immediately preceding stable state was Shell raster, the target token is unchanged, and the visible target is undergoing a monitor/geometry transition.
- The transition policy must use prior stable mode plus bounded time/sample evidence. It must not permanently classify every work-area-sized or maximized window as fullscreen because that would change normal windowed behavior.
- During a pending fullscreen handoff, do not prepare, map, show, present, or mutate the managed PyQt surface. Retain Shell-raster ownership; allow target-actor parenting to follow the game, or temporarily suspend raster actors if the target actor is unavailable. A brief overlay disappearance during this handoff is explicitly acceptable; exposing a standalone, decorated, black, focus-affecting, or wrong-monitor Qt surface is not.
- If the same target returns to fullscreen within the bound, settle directly back to Shell raster without a managed-surface cycle. If non-fullscreen state persists beyond the bound, commit once to the existing stable managed-window path. The initial grace-period default is `1.5s`, expressed as a named backend-owned parameter and injected into the pure policy for tests. It must not be a hard-coded branch literal. Phase 19 does not add a user-facing preference; a later dev-config override may be wired without changing the policy contract if live timing evidence requires it.
- Target loss, target-token replacement, minimization, workspace removal, helper failure, and game exit bypass the grace period and preserve their existing immediate hide/clear behavior.
- Renderer changes must be atomic. Shell raster to managed PyQt prepares a content-suppressed, frameless, focus-safe surface and confirms geometry before raster cleanup/content reveal. Managed PyQt to Shell raster proves raster attachment before hiding and resetting the Qt surface.
- Returning to Shell raster explicitly invalidates managed remap/preparation state and clears content suppression so a later real windowed transition starts from a known state.
- Diagnostics must identify the stable state, pending reason, elapsed time/sample count, target/monitor identity, chosen action (`hold_raster`, `commit_raster`, `commit_managed`, or `hide_all`), and cleanup result without adding release-only polling.
- Rollback: gate the new transition arbiter behind a narrow GNOME backend-owned toggle during manual validation. Disabling it restores the pre-Phase 19 renderer transition policy without changing helper protocol, settings, EDMC lifecycle wiring, or stable windowed preparation.
- Patch separation: do not land Phase 19 together with the unsupported experimental Linux window-list implementation. Research and validation of a GNOME-version-compatible standalone/window-list mechanism remains a separate follow-up.

#### Phase 19 Decision Record, 2026-07-15
- Transition appearance: accepted. The overlay may briefly disappear during Shift+Super+Arrow movement when safe Shell-actor following cannot be proven.
- Handoff bound: accepted with a tuneable `1.5s` backend default. The pure policy receives the value as an argument so unit tests and future evidence-based tuning do not require rewriting transition logic.
- Handoff classification: accepted. Prior stable Shell-raster mode, the same target token, a visible/non-minimized target, and monitor or monitor-relative geometry transition evidence are required before transient `fullscreen=false` is held.
- Shell actor policy: accepted. Reuse/reparent when the target actor remains valid; suspend when it does not; never expose managed PyQt merely to bridge the pending interval.
- Deliberate fullscreen-to-windowed latency: accepted. A real mode change may take up to the bounded handoff interval before managed-window presentation commits.
- Linux window-list experiment: accepted for separation. Remove or disable it from the Phase 19 patch, retain the historical/current implementation record below, and solve supported GNOME standalone identity independently.
- Rollback: accepted. Use a narrow backend-owned developer toggle for live proof; do not add another user preference for the transition arbiter.
- Qt cleanup: accepted. Successful Shell-raster authority explicitly hides and resets managed Qt preparation, remap, and content-suppression state.
- Multiple-client protection: accepted as separate lifecycle work. Phase 19 manual runs still require a one-client preflight so renderer-transition evidence is trustworthy.

#### Standalone Identity Implementation Reference
- Stable Windows mechanism: the existing standalone preference is implemented through Qt window identity. Normal overlay mode applies `Qt.Tool`; Windows standalone mode prevents that tool-window flag, leaving a normal app window that capture tools, the taskbar, and Alt-Tab can identify. `_apply_standalone_window_identity()` then applies the standalone window icons. Historically, non-Windows clients forced the preference false.
- Generic flag mechanism: `InteractionController._apply_window_identity_flags()` applies `WindowStaysOnTopHint`, `FramelessWindowHint`, click-through attributes, and `Qt.Tool` only when the backend is not Wayland. `OverlayWindow._set_window_flag()` contains the Windows standalone exception that disables `Qt.Tool` while standalone mode is enabled. Preserve this reference when refactoring; past regressions have come from changing tool/window flags during native-surface recreation.
- Borderless GNOME mechanism: Shell-raster presentation has no visible managed PyQt top-level and is therefore naturally absent from taskbar, Alt-Tab, and Overview. Standalone selection does not apply to this renderer.
- Current GNOME managed-window experiment: the cross-platform preference is forwarded to the helper, where normal mode attempts `hide_from_window_list()` and standalone mode attempts `show_in_window_list()`. On the tested GNOME/Mutter runtime both methods probe as unsupported. Consequently, `standalone=true` appears to work only because the managed PyQt surface is already a normal top-level; `standalone=false` cannot reliably remove it from task switching. This experiment is evidence, not an accepted production mechanism.
- Historical reference: repository branch `origin/linux_standalone` contains earlier broad Linux standalone work. It may be inspected for intent, but must not be cherry-picked wholesale; any reusable behavior requires current backend-boundary review and focused tests.
- Future GNOME standalone work must first prove a version-compatible compositor or Qt identity mechanism in an isolated spike. It must preserve `FramelessWindowHint`, click-through, focus safety, helper discovery, windowed multi-monitor attachment, and helper-disable cleanup before replacing the unsupported experiment.

#### Phase 19 Test Type Selection
- Use unit tests for the pure transition state machine because target token, fullscreen state, monitor identity, geometry, elapsed time, and sample count are deterministic and injectable.
- Use backend runtime-contract tests for renderer ownership, raster hold/cleanup, preparation call counts, invalidation, and diagnostic actions.
- Use PyQt tests for frameless/focus-safe flag preservation, mapped-content suppression, and managed-surface cleanup across renderer changes.
- No harness test is required unless implementation touches `load.py`, EDMC startup/shutdown hooks, preferences replication, journal/dashboard callbacks, or client process orchestration. If one of those touchpoints becomes necessary, add a harness test before editing it.
- Manual GNOME/Wayland validation remains mandatory because headless tests cannot prove titlebar absence, taskbar/Alt-Tab/Overview identity, focus safety, or physical two-monitor movement.

#### Phase 19 Refactor Staging
| Stage | Description | Status |
| --- | --- | --- |
| 19.1 | Record the fullscreen/windowed invariants, one-client reproduction, unsupported window-list evidence, test selection, and rollback boundary | Completed |
| 19.2 | Extract a pure backend presentation-transition policy with stable Shell-raster, pending fullscreen-handoff, and stable managed-window states; inject a named `1.5s` default | Pending |
| 19.3 | Wire transition state through the backend-owned GNOME bundle and backend-neutral consumer contract without crossing the `fix219` boundary | Pending |
| 19.4 | Make renderer transitions atomic: retain/suspend Shell raster during handoff and explicitly suppress/reset managed PyQt surfaces | Pending |
| 19.5 | Add unit, backend runtime-contract, and PyQt lifecycle regression coverage for stable modes and every transition outcome | Pending |
| 19.6 | Run targeted tests, full headless/GUI suites, Ruff, mypy, architecture checks, `make check`, `make test`, and `git diff --check` | Pending |
| 19.7 | Perform the two-monitor manual matrix with the transition toggle enabled, then disabled as a rollback proof | Pending |
| 19.8 | Record evidence and commit Phase 19 separately from Linux standalone/window-list identity work | Pending |

#### Phase 19 Planned Touch Points
- New pure policy candidate: `overlay_client/backend/presentation_transition.py`.
- Backend-owned runtime state: `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`.
- Backend-neutral result transport only if needed: `overlay_client/backend/consumers.py` and existing backend result contracts.
- Generic surface action application only: `overlay_client/follow_surface.py`; it must not inspect GNOME helper/backend enums.
- Tests: a new `overlay_client/tests/test_presentation_transition.py` plus focused additions to `test_gnome_helper_presentation_runtime.py`, `test_backend_consumers.py`, `test_backend_presentation_policy.py`, `test_follow_surface_mixin.py`, `test_setup_surface.py`, and `test_interaction_controller.py` as required by actual touchpoints.
- The GNOME extension should not require a protocol or window-list change for Phase 19. Helper changes are allowed only if target-actor suspend/reuse diagnostics prove insufficient, and must receive source-contract coverage.

#### Phase 19 Planned Test Commands
- `overlay_client/.venv/bin/python -m pytest -q overlay_client/tests/test_presentation_transition.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_follow_surface_mixin.py`
- `QT_QPA_PLATFORM=offscreen PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest -q overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_follow_surface_mixin.py`
- `overlay_client/.venv/bin/python -m pytest -q overlay_client/tests/test_backend_architecture_boundary.py`
- `overlay_client/.venv/bin/python -m ruff check .`
- `overlay_client/.venv/bin/python -m mypy`
- `source .venv/bin/activate && python -m pytest`
- `make check`
- `make test`
- `git diff --check`

#### Phase 19 Manual Regression Matrix And Acceptance Gate
- Start directly in borderless fullscreen on each monitor; verify Shell raster only and no Qt app-window identity.
- Move once in each direction with Shift+Super+Arrow; repeat rapidly and reverse direction before GNOME settles.
- Open Alt-Tab and GNOME Overview during and after movement; verify no overlay entry, title bar, black surface, or focus trap.
- Deliberately change fullscreen to windowed and windowed to fullscreen; verify the bounded policy eventually commits to the correct stable renderer exactly once.
- Move a stable windowed game within one monitor and across monitors; verify Phase 18 preparation reuse/stabilization and final attachment remain unchanged.
- Minimize/restore, change workspace, lose/regain focus, and exit the game in both modes; verify existing immediate hide/clear contracts.
- With one overlay client, verify no simultaneous Shell-raster and visible managed-PyQt renderer. Record process identity, helper target token, renderer decision, preparation action, and raster actor counts for every run.
- Acceptance allows a brief overlay disappearance during fullscreen monitor handoff. It requires no title bar, taskbar/Alt-Tab/Overview entry, black screen, focus trap, or monitor-relative Qt intermediate, while stable fullscreen and stable windowed behavior match their pre-Phase 19 baselines.

## Execution Log
- Plan created on 2026-05-11.
- Phase 4 runtime wiring was authorized and implemented on 2026-05-11.
- Record one execution summary subsection per completed phase.
- Record exact test commands and outcomes for each completed phase.

### Phase 1 Execution Summary
- Stage 1.1: Completed. Helper was installed, enabled, `ACTIVE`, and DBus-healthy. Session was GNOME Wayland.
- Stage 1.2: Completed. Shell helper found the Elite target and rejected one launcher candidate. The windowed target had valid frame/buffer rects, but `contentRect` and `decorationInsets` were null.
- Stage 1.3: Completed. Runtime logs showed legacy tracker + PyQt `setGeometry` activity and no helper target/presentation activity. User observed visual overlay stuck in the upper-left while resize followed the game size.
- Stage 1.4: Completed. Current failures are mixed:
- Runtime wiring gap: helper health is used, but helper target/presentation is not being used by the running client.
- Shell placement gap: Qt `moveEvent` reports nonzero positions, but compositor-visible placement stays upper-left.
- Visibility policy gap: `keep_overlay_visible=false` causes repeated hide/show flashing.
- Geometry contract gap: helper target discovery did not produce `contentRect` for the tested decorated/windowed state, so final content alignment remains unresolved.

### Tests Run For Phase 1
- `./scripts/dev_gnome_helper.sh status`
- Result: passed; helper installed/enabled/active and DBus health returned healthy payload.
- `gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.GetTargetState '{}'`
- Result: passed; `target_found` with target token `meta:110`, frame/buffer rects present, content rect missing.
- `tail -f /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log | grep --line-buffered -E "Client backend status|helper|target_state|presentation|Overlay visibility|Tracker state|Raw tracker|Calculated overlay geometry|Applying geometry|Overlay moveEvent|Applying drag state|standalone|flags="`
- Result: passed; captured legacy geometry path, visibility flashing, and no helper target/presentation runtime activity.

### Phase 2 Execution Summary
- Stage 2.1: Completed. Used direct DBus `ApplyPresentation` with target token `meta:110` and frameRect-derived requested rect `(1000,216,1440,997)` because `contentRect` was null in the target payload.
- Stage 2.2: Completed. The overlay visibly moved in positive X and Y directions. The helper found overlay token `meta:134` and reported placement/stacking/chrome/click-through/focus-safe gates as true.
- Stage 2.3 initial finding: The first response reported `applied_rect=(0,29,1920,800)` instead of the requested rect. This is not a reliable applied presentation even though the helper returned `presentation_applied`.
- Stage 2.3 update: A fresh-geometry retry requested `(628,270,1920,837)` and returned `applied_rect=(1000,216,1920,800)`. The overlay visibly moved to the game window, but did not continue following later game movement. This strengthens the need for a settled/applied readback check, a rect-match gate, and runtime wiring that repeatedly applies presentation from fresh helper target state.
- Stage 2.3 update: Repeating the same presentation request later returned `applied_rect=(628,270,1920,800)`. Position can settle, but height remains constrained. Need to determine whether `800` is the PyQt overlay's current client size, a Shell/window-manager constraint, or feedback from the legacy runtime follow path.
- Stage 2.3: Completed. No unsupported Shell APIs or overlay identity mismatches were observed in the direct tests. The helper found `overlay_token=meta:134` and reported placement, stacking, chrome-free, click-through, and focus-safe gates as true. The outstanding issue is not basic Shell capability; it is rect selection/settled validation/runtime wiring.
- Stage 2.4: Completed. Keep the PyQt renderer as the first implementation path. Direct Shell-mediated presentation can place and stack the PyQt overlay. No evidence currently requires moving rendering into the extension.

### Tests Run For Phase 2
- `gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.ApplyPresentation '{"action":"attach","target_token":"meta:110","content_rect":{"x":1000,"y":216,"width":1440,"height":997},"standalone_mode":false,"click_through_expected":true,"overlay_title":"EDMC Modern Overlay","overlay_wm_class":"EDMCModernOverlay"}'`
- Result: partial pass. Shell helper found and affected the overlay, but the returned `applied_rect` did not match the requested rect. The presentation gate must not treat this as a full success.
- `gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.ApplyPresentation '{"action":"attach","target_token":"meta:110","content_rect":{"x":628,"y":270,"width":1920,"height":837},"standalone_mode":false,"click_through_expected":true,"overlay_title":"EDMC Modern Overlay","overlay_wm_class":"EDMCModernOverlay"}'`
- Result: partial pass. Shell helper again found and affected the overlay, but returned `applied_rect=(1000,216,1920,800)` instead of the requested rect. Need settled readback and rect-match validation.
- Repeated the same command after slight game movement.
- Result: partial pass. Shell helper returned `applied_rect=(628,270,1920,800)`. Position settled to the requested x/y; height remained constrained to `800`.
- `gdbus call --session --dest org.edmc.ModernOverlay.Helper --object-path /org/edmc/ModernOverlay/Helper --method org.edmc.ModernOverlay.Helper.ApplyPresentation '{"action":"attach","target_token":"meta:110","content_rect":{"x":628,"y":270,"width":1920,"height":800},"standalone_mode":false,"click_through_expected":true,"overlay_title":"EDMC Modern Overlay","overlay_wm_class":"EDMCModernOverlay"}'`
- Result: passed for accepted rect. Shell helper returned `applied_rect=(628,270,1920,800)`, matching the requested rect exactly.

### Phase 3 Execution Summary
- Stage 3.1: Completed. GNOME helper mode will use Shell helper target state as the target identity and geometry source of truth. Legacy tracker geometry remains for non-GNOME behavior, degraded fallback diagnostics, and comparison only; Qt geometry is not placement proof under GNOME Wayland.
- Stage 3.2: Completed. Visibility in GNOME helper mode will be target/presentation-state driven. Target unavailable states hide/degrade. `keep_overlay_visible=false` will use debounced focus loss rather than hiding on a single foreground/focus false sample.
- Stage 3.3: Completed. Required diagnostics are defined for legacy tracker geometry, Qt requested/move geometry, helper target rects, presentation requested/applied rects, rect deltas, visibility reasons, and presentation gate results.
- Stage 3.4: Completed. Required unit, harness, and manual validation tests are documented for Phase 4 and later implementation.

### Tests Run For Phase 3
- No runtime tests were run; Phase 3 was a docs/design phase.
- `git diff --check -- docs/refactoring/gnome_wayland_presentation_attachment.md`
- Result: passed.

### Phase 4 Execution Summary
- Stage 4.1: Completed. Added a runtime GNOME helper presentation cycle that probes helper health, fetches `GetTargetState`, and validates target state through the existing helper IPC contracts.
- Stage 4.2: Completed. Added bounded `ApplyPresentation` runtime calls through DBus. Runtime GNOME helper mode now uses helper target/presentation state and bypasses legacy tracker `setGeometry` as compositor-visible placement proof while the helper is available.
- Stage 4.3: Completed. Presentation validation now requires applied-rect match within the documented `<= 2` logical pixel tolerance, placement, stacking, click-through, focus-safe, chrome-free, PyQt renderer, non-standalone mode, no unsupported features, and no degrade reasons. Missing `contentRect` can use `frame_rect_fallback`, but that remains degraded and blocks `true_overlay_ready`.
- Stage 4.4: Completed. Added tests for target rect fallback, applied rect match/mismatch, settled retry behavior, and GNOME helper-mode runtime bypass of the legacy geometry path.
- Post-Phase 4 architecture review: the behavior is directionally correct, but the helper presentation runtime cycle was imported directly by `follow_surface.py`. Phase 4A now owns correcting that boundary before Phase 5 starts.

### Tests Run For Phase 4
- `overlay_client/.venv/bin/python -m py_compile overlay_client/backend/helper_ipc.py overlay_client/gnome_helper_presentation.py overlay_client/follow_surface.py overlay_client/setup_surface.py`
- Result: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py`
- Result: passed; 34 passed.
- `make check`
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 933 passed and 21 skipped.

### Phase 4A Execution Summary
- Stage 4A.1: Completed. Added the `fix219` backend-boundary rule to `AGENTS.md` and the matching compliance check to `docs/compliance/edmc_compliance.md`.
- Stage 4A.2: Completed. Moved the GNOME helper presentation runtime cycle under backend ownership at `overlay_client/backend/bundles/_gnome_shell_helper_presentation.py`.
- Stage 4A.3: Completed. `overlay_client/follow_surface.py` now calls the backend-facing `run_backend_presentation_cycle(...)` consumer and no longer imports the GNOME helper runtime module or dispatches helper presentation by checking GNOME backend/helper enums or helper protocol actions.
- Stage 4A.4: Completed. Generic follow/setup diagnostic state was renamed from `_last_gnome_helper_presentation*` to `_last_backend_presentation*`.
- Stage 4A.5: Completed. `overlay_client/platform_context.py` helper health probing remains documented as an intentional client-authoritative status/probe boundary for Phase 4A. It uses backend helper validation contracts and must not grow runtime presentation/follow policy.
- Stage 4A.6: Completed. Added backend consumer tests and a static import-boundary test for `follow_surface.py`.
- Stage 4A.7: Completed. Phase 4A tests and `make check` were recorded; Phase 5 may now build on the backend-owned helper presentation boundary.

### Tests Run For Phase 4A
- `overlay_client/.venv/bin/python -m py_compile overlay_client/backend/consumers.py overlay_client/backend/bundles/_gnome_shell_helper_presentation.py overlay_client/follow_surface.py overlay_client/setup_surface.py`
- Result: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py`
- Result: passed; 34 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_backend_consumers.py`
- Result: passed; 60 passed.
- `make check`
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 937 passed and 21 skipped.

### Phase 5 Execution Summary
- Stage 5.1: Completed. Added pure backend presentation visibility-policy tests covering target unavailable, minimized, off-workspace, presentation unavailable, `keep_overlay_visible=true`, focused target, single-sample focus-loss debounce, sample-threshold hide, and time-threshold hide.
- Stage 5.2: Completed. Added backend-neutral visibility snapshot/result fields and wired `follow_surface.py` to use the pure debounce policy while continuing to consume only backend-owned presentation results.
- Stage 5.3: Failed manual GNOME validation. Headless tests prove that one unfocused helper sample does not hide the overlay and the second consecutive unfocused sample hides it when `keep_overlay_visible=false`, but real GNOME validation still flashes on focus return.
- Stage 5.4: Headless policy tests complete; manual GNOME validation pending. Target unavailable, minimized, hidden/off-workspace, and presentation unavailable states hide immediately in pure policy tests.
- The named debounce constants are `BACKEND_PRESENTATION_FOCUS_LOSS_HIDE_SAMPLES = 2` and `BACKEND_PRESENTATION_FOCUS_LOSS_DEBOUNCE_SECONDS = 1.0`.
- Backend boundary remains preserved: `follow_surface.py` still has no direct GNOME helper runtime import or raw GNOME backend/helper enum dispatch.
- Manual validation update on 2026-05-11:
- The overlay now moves with the game window. This confirms Phase 4/4A helper-backed placement is active in the runtime path.
- With `keep_overlay_visible=false`, the overlay is visible while the game has focus and hidden while the game does not have focus. That matches the current Phase 5 policy.
- Failure: when alt-tabbing back to the game, the overlay flashes between the game window and a very small geometry window in the upper-left corner. Clicking the game while the overlay is on the main game window stops the flashing.
- Interpretation: the no-flash gate is not satisfied. The remaining problem appears to be the focus-regain/show/presentation transition, not basic helper target tracking. Follow-up work must determine whether the overlay is being shown before Shell presentation settles, whether the helper cannot reliably present a hidden PyQt window, or whether stale/lagged presentation readback is causing a bad small default geometry sample.
- Log evidence from 2026-05-11 confirms the hidden-to-visible failure mode:
- While the overlay is hidden, helper presentation returns `overlay_window_not_found`, so the Shell helper cannot attach/present the unmapped PyQt window.
- When the game regains focus, the visibility policy shows the overlay from the hidden state before helper presentation has a usable overlay MetaWindow. Qt maps the overlay as a tiny `(46x173)` surface at the upper-left.
- The next helper cycle sees `applied={'x': 0, 'y': 29, 'width': 46, 'height': 173}` with `applied_rect_mismatch`. A later cycle can correct the rect to the target `(431,167,1440,997)`, but focus has often flipped false by then and the two-sample debounce hides the overlay again.
- Clicking the game stabilizes `target_focus=True`; after that the helper reports repeated matching applied rects and the overlay remains visible.
- Phase 5 follow-up should treat "showing from hidden/unmapped" as a special transition. Candidate fixes are: prime Qt geometry to the last known/requested backend rect before `show()`, add a backend-presentation warm-up state that does not hide on focus loss until the overlay MetaWindow is found and applied rect matches for at least one cycle, or keep the overlay mapped but visually suppressed instead of fully hiding it in GNOME helper mode.
- Stage 5.5: Headless follow-up complete; manual GNOME revalidation pending. Added backend-neutral `prime_rect` fields so follow/runtime can prime the Qt top-level from backend-authored presentation geometry before `show()`. Added a bounded remap warm-up policy so transient focus loss after remapping does not immediately hide the overlay until helper presentation finds the overlay window and reports a matching applied rect, or until the warm-up expires.
- The named warm-up constants are `BACKEND_PRESENTATION_REMAP_WARMUP_MAX_SAMPLES = 4` and `BACKEND_PRESENTATION_REMAP_WARMUP_SECONDS = 2.0`.
- The priming path sets Qt geometry for map hygiene only and logs it as not placement proof. Runtime placement proof remains the helper-applied rect match.
- Manual revalidation after Stage 5.5 showed the tiny upper-left remap was fixed, but the overlay still cycled between attached, hidden, and upper-left-correctly-sized states.
- New log evidence: after remap warm-up completed, helper focus flipped false for two 500 ms samples and the policy hid the overlay at `focus_loss_elapsed=0.500s`; a later helper sample often returned `target_focus=True`, causing another remap. The remaining Phase 5 issue is the soft focus-loss debounce being too aggressive for GNOME focus flicker.
- Follow-up adjustment: soft focus-loss hide now requires both the configured sample threshold and the configured elapsed-time threshold. Hard target-loss and unsupported presentation states still hide immediately.
- Manual revalidation after the focus-loss debounce adjustment showed the overlay still flashes, but slower. The tiny remap is fixed: the overlay now maps at the correct size and target rect before showing.
- New log evidence: after warm-up completion, the helper repeatedly reports matching applied rects while `target_focus=False`; the overlay then hides after the configured focus-loss debounce, the target later reports focused again, and the overlay remaps. This means the mapped overlay is still causing, or at least correlated with, GNOME reporting the game as unfocused.
- Classification update: Phase 5 visibility mechanics are now behaving as designed. The remaining no-flash failure depends on Phase 6 focus/identity work: normal overlay mode must be non-focus-stealing and not standalone-like before `keep_overlay_visible=false` can be validated without a visibility-policy workaround.
- Do not keep increasing the focus-loss debounce as the primary fix. That would make `keep_overlay_visible=false` less truthful when the user actually alt-tabs away. Phase 6 must prove a focus-safe/chrome-free overlay identity, likely by changing or validating Qt/Shell focus behavior such as `WindowDoesNotAcceptFocus`, Wayland-safe window flags, or helper-reported overlay focus state.

### Tests Run For Phase 5
- `overlay_client/.venv/bin/python -m py_compile overlay_client/backend/presentation_policy.py overlay_client/backend/consumers.py overlay_client/follow_surface.py overlay_client/setup_surface.py`
- Result: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py`
- Initial result: failed once because `test_backend_presentation_visibility_hides_after_focus_loss_time_threshold` compared floating-point elapsed time exactly (`1.0999999999999996` vs `1.1`). The assertion was changed to `pytest.approx`.
- Re-run result: passed; 42 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`
- Result: passed; 70 passed.
- `make check`
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 947 passed and 21 skipped.
- Phase 5 follow-up:
- `overlay_client/.venv/bin/python -m py_compile overlay_client/backend/presentation_policy.py overlay_client/backend/consumers.py overlay_client/follow_surface.py overlay_client/setup_surface.py`
- Result: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py`
- Result: passed; 49 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`
- Result: passed; 77 passed.
- `git diff --check`
- Result: passed.
- `make check`
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 954 passed and 21 skipped.
- Phase 5 focus-loss debounce follow-up after manual revalidation:
- `overlay_client/.venv/bin/python -m py_compile overlay_client/backend/presentation_policy.py overlay_client/follow_surface.py`
- Result: passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_backend_architecture_boundary.py`
- Result: passed; 50 passed.
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_backend_presentation_policy.py overlay_client/tests/test_backend_consumers.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_backend_architecture_boundary.py overlay_client/tests/test_gnome_shell_helper_target_state.py overlay_client/tests/test_gnome_shell_helper_presentation_state.py overlay_client/tests/test_gnome_helper_presentation_runtime.py`
- Result: passed; 78 passed.
- `git diff --check`
- Result: passed.
- `make check`
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with 955 passed and 21 skipped.
