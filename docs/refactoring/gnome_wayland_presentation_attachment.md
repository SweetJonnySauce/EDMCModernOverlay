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
| 8 | Performance stabilization addendum for GNOME helper presentation churn | Latest Baseline Captured; Manual Validation Pending; Payload Gate Headless Tests Passed |

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
- Use a fresh successful applied presentation window of about `1.0s` while focused/visible and about `2.0s` while mapped-suppressed, unless tests show these values are too coarse.
- Cache healthy compatible helper status for about `5s`, with small jitter where practical so repeated clients do not line up health probes.
- Keep suppressed-state polling slower, around `1-2s`, while still detecting focus return and hard target changes promptly.
- Start Shell-side no-op work by skipping redundant `move_resize_frame(...)`; keep `make_above()` unless stacking can be proven cheaply.
- Do not replace `gdbus` subprocesses with a persistent DBus client in this phase. Dedupe, cache, and throttle first.

#### Phase 8 Target Behavior
- Do not call `ApplyPresentation` when the helper target token, selected requested rect, monitor rect, visibility action, focus/workspace/minimized state, overlay identity, and relevant presentation options are unchanged and the last applied presentation is still fresh and matching.
- Do not run helper health through `gdbus` on every presentation cycle. Cache healthy compatible helper status for about `5s` with small jitter where practical, while still failing closed on explicit command errors and startup/unavailable states.
- Slow down soft-focus suppressed polling where safe. In `mapped_suppressed` with a valid target and matching last presentation, poll enough to detect focus return and target changes but avoid repeated no-op compositor writes.
- Keep hard states fast: helper unavailable, target missing, target token changes, target minimized/hidden/off-workspace, monitor rect changes, requested rect changes, stale presentation, unsupported presentation, and applied-rect mismatch must bypass no-op suppression and retry through the existing bounded path.
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
| 2026-05-13 ~21:35 UTC | Latest sample after Phase 8 presentation changes and payload logging gate, EDMC/overlay/helper on | Elite `339%`, Firefox RDD `75.1%`, OneDrive `53.6%`, Firefox `16.6%`, EDMC `12.4%`, GNOME Shell `9.5%`, overlay client `3.6%`; helper health `healthy`, protocol `3` | GNOME Shell `5.20%`, EDMC `9.20%`, overlay client `3.40%`; RSS about `635684 KB`, `213616 KB`, and `91862 KB`; write IO `0.00`, `17.60`, and `2.40 kB/s` respectively | Last `500` log lines: `309` diagnostics over about `154.0s`, `239` skipped (`77%`), `183` suppressed-throttle skips, `56` fresh-matching skips, `70` apply attempts; apply attempts about `0.45`/sec | Current runtime still has reduced apply volume. Payload logging gate does not change presentation cadence; EDMC CPU remains variable under active game/desktop load. |

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

#### Phase 8 Execution Summary
- Stage 8.2: Completed for headless coverage. Added backend-owned `GnomeHelperPresentationSignature` and runtime state that suppresses `ApplyPresentation` only when the target token, selected requested rect after clamp, monitor rect, rect source, previous visibility action, target focus/workspace/minimized/fullscreen flags, overlay title/class, renderer, tolerance, required gates, standalone mode, and expected degradation reasons are unchanged. Suppression requires a fresh matching prior presentation and does not apply after applied-rect mismatch, unexpected degradation, unsupported features, stale status, missing target, hidden target, or request changes.
- Stage 8.3: Completed for headless coverage. Healthy compatible helper status is cached for `5.0s` plus bounded jitter up to `0.5s`; explicit unhealthy/error results clear presentation state and fail closed. This does not replace the current `gdbus` transport.
- Stage 8.4: Completed for headless coverage. Stable `mapped_suppressed` state throttles redundant target polling to about `1.5s` only while the previous matching presentation remains fresh; focus return, rect changes, monitor changes, target changes, and stale status still force the normal target/presentation path.
- Stage 8.5: Completed for headless coverage. The GNOME Shell extension now reads the current overlay frame and skips redundant `move_resize_frame(...)` when it already matches the requested rect within `rect_tolerance`. `make_above()` remains in place because stacking proof is not yet cheap or explicit.
- Stage 8.6: Headless regression passed. Manual GNOME performance validation remains pending after helper reinstall/reload and EDMC restart. Support wording remains degraded/experimental; `frame_rect_fallback` still blocks `true_overlay`.
- Stage 8.7: Completed for headless coverage. `_PluginRuntime._log_payload` now requires EDMC `DEBUG` via `_edmc_debug_logging_active()` before payload body logging can emit. The existing payload logging preference/debug config remains an additional enable switch, but dev override alone no longer unlocks payload body logs. Payload and legacy raw serialization now happens only after the EDMC DEBUG gate, payload logging enablement, and plugin-exclusion checks pass. Existing payload delivery, payload shape, spam detection, presentation logs, GNOME helper behavior, BGS-Tally behavior, generic dedupe, and support wording were not changed.

#### Tests Run For Phase 8
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
- Result: passed. Ruff passed, mypy passed, and `PYQT_TESTS=1 overlay_client/.venv/bin/python -m pytest` passed with `983 passed`, `21 skipped`.

#### Phase 8 Manual GNOME Validation Pending
- Reinstall/reload the GNOME Shell helper extension and restart EDMC so the extension no-op guard and backend cadence changes are both live.
- Repeat the Phase 8 validation commands during stable focused/visible and stable `mapped_suppressed` states.
- Expected log evidence: repeated stable cycles should show `presentation_skipped=True` with `skip_reason=fresh_matching_presentation` or `skip_reason=suppressed_poll_throttle`, reduced `attempts=1` apply volume, and unchanged requested/applied rect behavior for moves, resizes, focus return, target loss/reacquire, and 1440-height monitor clamp.
- Confirm Phase 7 windowed behavior still holds: no wrong-monitor movement, click-through still works while visible and mapped-suppressed, focus loss/return still has no hide/remap flash, and `frame_rect_fallback` remains degraded.

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
