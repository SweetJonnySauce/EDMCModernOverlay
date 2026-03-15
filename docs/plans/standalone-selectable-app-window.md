## Goal: Make standalone mode run as a selectable app window on Linux (X11 + Wayland)

Follow persona details in `AGENTS.md`.
Document implementation results in the `Implementation Results` section.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear, capture it under `Open Questions`.

## Requirements (Initial)
- In standalone mode (`on`), the overlay client must appear as a selectable app/window target in SteamVR picker on required targets.
- In standalone mode (`on`), the overlay client must be consistently visible in desktop app switchers across `off -> on -> off` transitions on required targets.
- Keep one shared standalone toggle across platforms; standalone remains `off` by default with no auto-detection/auto-enable.
- Preserve baseline overlay behavior when standalone mode is `off`, avoid crashes, and keep implementation dependency-free.
- Required manual validation targets: one Linux X11 environment and Wayland GNOME (Mutter) for now.
- Capture quality is blocking on required targets: no black/transparent/frozen/flickering output.

## Out Of Scope (This Change)
- Introducing Linux-specific extra preference toggles.
- New third-party runtime dependencies.
- Icon-work parity changes beyond existing behavior.

## Current Touch Points
- Code:
- `overlay_client/setup_surface.py` (window flags/attributes, standalone identity apply, runtime gating)
- `overlay_client/interaction_controller.py` (runtime flag reapplication behavior)
- `overlay_client/follow_surface.py` (transient-parent behavior that can hide window identity)
- `overlay_client/control_surface.py` (standalone toggle + platform-context transition behavior)
- `overlay_client/launcher.py` (startup app identity priming)
- Tests:
- `overlay_client/tests/test_setup_surface_standalone.py`
- `overlay_client/tests/test_control_surface_standalone.py`
- `overlay_client/tests/test_follow_surface_mixin.py`
- `overlay_client/tests/test_interaction_controller.py`
- Docs/notes:
- `docs/plans/standalone-selectable-app-window.md` (includes consolidated manual validation checklist/matrix)

## Assumptions
- SteamVR app/window picker visibility is driven by a combination of WM/app identity and window manager flags/role/parenting behavior.
- Switching between overlay profile and app-window profile may require restart on some compositor/session combinations.

## Risks
- Profile changes could regress click-through/follow behavior in standalone mode.
- Mitigation: gate profile changes strictly to standalone mode and keep off-path behavior unchanged; add regression tests.
- Wayland compositor behavior may still vary by GNOME and other compositor protocol implementation details.
- Mitigation: emit clear fallback/restart warnings and block completion until required-target manual validation is complete.
- Removing/bypassing transient-parent links in standalone mode may affect follow integration.
- Mitigation: keep follow geometry logic intact; only skip parent linkage in standalone mode and add focused tests.

## Open Questions
- None currently.

## Decisions (Locked)
- One toggle for all platforms; no Linux-specific toggle.
- Standalone mode default remains disabled for all platforms; no detection-based auto-enable.
- Required targets for completion are Ubuntu GNOME (Mutter) on X11 and GNOME (Mutter) on Wayland.
- Required-target capture failures are blocking, including black/transparent/frozen/flickering output.
- Standalone mode must preserve always-on-top behavior over Elite.
- Standalone mode remains frameless.
- Standalone mode keeps click-through enabled by default.
- Dependency-free implementation unless explicitly re-approved.
- User-visible warning is required when restart is needed for reliable identity/profile application.
- Respect user `force_xwayland` runtime setting; do not auto-mutate this setting in code.
- Manual validation should prioritize `force_xwayland=false` first on Wayland.
- Sign-off is maintainer approval only; no fixed screenshot/template evidence requirement.
- Maintainer sign-off owner is `jon`; no separate artifact is required.
- Desktop app switcher validation requires both GNOME Activities overview and `Alt+Tab`.
- Off/on/off transition validation requires one full cycle.
- Manual checklist completion is non-blocking for implementation changes; checklist must still be maintained in this plan.
- SteamVR availability detection is out of scope for this change; testing coordination is maintainer-driven.
- Exception approvals (always-on-top vs switcher visibility conflicts) are maintainer-approved by `jon`.
- If a required target cannot satisfy both always-on-top and switcher visibility simultaneously, record it as a non-blocking exception for this plan and log follow-up work.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Contract + selectable app-window profile design | Completed |
| 2 | Runtime implementation of standalone app-window profile | Completed |
| 3 | Automated test coverage and regression hardening | Completed |
| 4 | Required manual validation matrix (X11/GNOME) | In Progress |
| 5 | Readiness summary, sign-off package, and follow-up list | In Progress |

## Phase Details

### Phase 1: Contract and Profile Design
- Define exact standalone app-window behavior and guardrails before changing runtime flags.
- Risks: ambiguous profile rules can cause drift across sessions/platforms.
- Mitigations: lock explicit pass/fail contract and mapping of each runtime flag decision.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Define standalone app-window contract and pass/fail checklist. | Completed |
| 1.2 | Map existing hide-related behaviors to targeted changes. | Completed |
| 1.3 | Finalize restart/fallback contract and logging requirements. | Completed |

#### Stage 1.1 Detailed Plan
- Objective:
- Freeze exact behavior that qualifies as “selectable app window” for required targets.
- Primary touch points:
- `docs/plans/standalone-selectable-app-window.md`
- Steps:
- Convert requirements into explicit checklist items for flag behavior, identity behavior, and validation outcomes.
- Define blocking/non-blocking outcomes for required and optional environments.
- Acceptance criteria:
- Checklist covers standalone `off`/`on` behavior, restart warning rules, and required-target blockers.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_standalone_support.py tests/test_overlay_config_payload.py -q`

#### Stage 1.2 Detailed Plan
- Objective:
- Map each current “hidden overlay” behavior to required standalone app-window profile behavior.
- Steps:
- Audit current flags/attributes/parenting: `X11BypassWindowManagerHint`, `Tool`, `WA_ShowWithoutActivating`, transient-parent linking.
- Produce explicit keep/change matrix scoped to standalone mode only.
- Acceptance criteria:
- Every candidate behavior has an explicit keep/change decision and code owner location.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface_standalone.py overlay_client/tests/test_interaction_controller.py -q`

#### Stage 1.3 Detailed Plan
- Objective:
- Lock restart and warning behavior for live-apply limitations.
- Steps:
- Define when runtime apply is considered reliable vs restart-required.
- Define exact user-visible warning/log requirements for fallback and incomplete contract.
- Acceptance criteria:
- Restart-trigger conditions and warning language are documented and non-contradictory.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface_standalone.py -q`

#### Phase 1 Execution Order
- Implement in strict order: `1.1` -> `1.2` -> `1.3`.

#### Phase 1 Exit Criteria
- Standalone app-window contract is fully documented with no open design ambiguity.
- Runtime implementation can proceed without introducing extra toggles/dependencies.

### Phase 2: Standalone App-Window Runtime Implementation
- Implement the standalone-mode runtime profile so it behaves like a selectable app window.
- Risks: breaking overlay interaction/follow behavior or platform parity.
- Mitigations: standalone-only gating, small scoped edits, and targeted regression coverage.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Implement standalone window-profile flag/attribute rules. | Completed |
| 2.2 | Implement standalone transient-parent and follow-safe behavior. | Completed |
| 2.3 | Finalize startup/runtime identity + fallback warning wiring. | Completed |

#### Stage 2.1 Detailed Plan
- Objective:
- Apply app-window profile behaviors under standalone mode while preserving off-path behavior.
- Primary touch points:
- `overlay_client/setup_surface.py`
- `overlay_client/interaction_controller.py`
- Steps:
- In standalone mode, remove/avoid window manager bypass and non-activating behavior that suppress app discoverability.
- Keep always-on-top behavior in standalone mode so the overlay remains in front of Elite.
- Keep frameless window presentation in standalone mode.
- Keep click-through default behavior unchanged in standalone mode.
- Ensure `Tool` behavior does not revert to hidden-window semantics during click-through/interaction state updates.
- Acceptance criteria:
- Standalone `on` uses app-window profile flags while preserving always-on-top + frameless + click-through defaults; standalone `off` behavior remains unchanged.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface_standalone.py overlay_client/tests/test_interaction_controller.py -q`

#### Stage 2.2 Detailed Plan
- Objective:
- Prevent transient-parent linkage from collapsing standalone app visibility.
- Steps:
- Skip transient-parent attachment while standalone mode is enabled.
- Preserve existing follow geometry update behavior and transient-parent behavior for non-standalone mode.
- Acceptance criteria:
- Standalone mode no longer binds transient parent; follow remains stable.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_window_controller.py -q`

#### Stage 2.3 Detailed Plan
- Objective:
- Ensure startup and runtime transitions apply profile/identity reliably with explicit fallback warnings.
- Steps:
- Verify startup identity/profile priming path and runtime toggle/platform-context reapply path are consistent.
- Keep user-visible restart warning behavior when live apply is unreliable.
- Ensure runtime behavior respects current `force_xwayland` setting and does not auto-mutate settings.
- Acceptance criteria:
- Runtime path emits deterministic logs and warnings, respects runtime settings, and does not crash on unsupported transitions.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_control_surface_standalone.py overlay_client/tests/test_setup_surface_standalone.py overlay_client/tests/test_platform_integration.py -q`

#### Phase 2 Execution Order
- Implement in strict order: `2.1` -> `2.2` -> `2.3`.

#### Phase 2 Exit Criteria
- Standalone app-window runtime profile is implemented and guarded by tests.
- No regressions in standalone `off` behavior or Windows behavior.

### Phase 3: Automated Validation and Regression Hardening
- Add and run automated coverage for selectable-app profile behavior and regression boundaries.
- Risks: incomplete coverage misses flag reapplication regressions.
- Mitigations: add source-aware assertions and cross-module regression slices.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add focused tests for standalone app-window profile flags/attributes. | Completed |
| 3.2 | Add tests for transient-parent standalone bypass and follow behavior. | Completed |
| 3.3 | Run broad regression suite and lock baseline. | Completed |

#### Stage 3.1 Detailed Plan
- Objective:
- Guarantee profile-flag behavior is deterministic under startup/toggle/context-update paths.
- Steps:
- Extend setup/control standalone tests with explicit profile assertions.
- Assert logs/warnings for fallback and incomplete contract paths.
- Acceptance criteria:
- Tests fail if hidden-window profile leaks into standalone app mode.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface_standalone.py overlay_client/tests/test_control_surface_standalone.py -q`

#### Stage 3.2 Detailed Plan
- Objective:
- Guarantee standalone bypasses transient-parent linking without follow regressions.
- Steps:
- Extend follow-surface tests to validate standalone and non-standalone branches.
- Validate no regressions in follow/window controller behavior.
- Acceptance criteria:
- Test coverage proves parent-link bypass is standalone-scoped and safe.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_window_controller.py -q`

#### Stage 3.3 Detailed Plan
- Objective:
- Confirm project-level quality gates remain green after profile changes.
- Steps:
- Run targeted overlay slices, then full check pipeline.
- Record exact pass/fail outputs and any skips.
- Acceptance criteria:
- `ruff`, `mypy`, and pytest gates pass; no new failing tests introduced.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "standalone or platform or interaction or follow or window" -q`
- `make check`

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3`.

#### Phase 3 Exit Criteria
- Automated validation is green and documented.
- Remaining risk is limited to required manual SteamVR environment validation.

### Phase 4: Manual Required-Target Validation
- Execute required manual validation for selectable-app behavior and capture quality.
- Risks: compositor/session-specific behavior may still fail despite automated pass.
- Mitigations: strict required-target matrix and blocking-quality rules.

#### Manual Validation Checklist (Consolidated)
- Scope:
- Track manual validation for standalone selectable-app-window behavior in this plan doc.
- Checklist maintenance is required; completion is non-blocking for implementation changes until maintainer-scheduled manual test runs are executed.
- Required targets:
- Ubuntu GNOME (Mutter) on X11.
- GNOME (Mutter) on Wayland (`force_xwayland=false` first).
- Pass rules:
- SteamVR picker lists overlay window as selectable app/window target.
- App switcher visibility passes in both GNOME Activities overview and `Alt+Tab`.
- Capture quality shows no black/transparent/frozen/flickering output.
- Stability passes one full `off -> on -> off` cycle with no crash/focus-loop/input regression.
- Exception policy:
- If always-on-top and switcher visibility cannot both be satisfied on a required target, record a non-blocking exception with maintainer approval (`jon`).

| Target | SteamVR Picker Listed | Activities Visible | Alt+Tab Visible | Capture Quality OK | One Full off/on/off Cycle OK | Notes | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ubuntu GNOME (Mutter/X11) | Pending | Pending | Pending | Pending | Pending | Manual validation pending maintainer-coordinated run. | Blocked |
| GNOME (Mutter/Wayland, `force_xwayland=false`) | Pending | Pending | Pending | Pending | Pending | Manual validation pending maintainer-coordinated run. | Blocked |
| GNOME (Mutter/Wayland, `force_xwayland=true`) | Optional | Optional | Optional | Optional | Optional | Always capture as reference evidence. | Optional |

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Validate Ubuntu GNOME (Mutter/X11) environment in SteamVR picker. | Blocked |
| 4.2 | Validate GNOME (Mutter/Wayland) required target (native Wayland first). | Blocked |
| 4.3 | Confirm capture quality + standalone off/on/off transition stability. | Blocked |

#### Stage 4.1 Detailed Plan
- Objective:
- Validate standalone window appears/selects as app target on Ubuntu GNOME (Mutter/X11).
- Steps:
- Run manual matrix for standalone `off`, `on`, restart path, SteamVR picker visibility, and desktop app switcher visibility.
- App switcher check must pass in both GNOME Activities overview and `Alt+Tab`.
- Capture timestamped logs for profile/identity branch and warnings.
- Acceptance criteria:
- X11 target is selectable, appears in desktop app switcher consistently, and capture output is usable.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_platform_integration.py -q`

#### Stage 4.2 Detailed Plan
- Objective:
- Validate required Wayland target GNOME (Mutter).
- Steps:
- Run full matrix in GNOME session with SteamVR picker and desktop app switcher checks.
- Prioritize validation with `force_xwayland=false` first, then optionally capture `force_xwayland=true` behavior as secondary evidence.
- App switcher check must pass in both GNOME Activities overview and `Alt+Tab`.
- Validate fallback/restart warning behavior if live apply is unreliable.
- Acceptance criteria:
- GNOME is selectable, appears in desktop app switcher consistently, and capture output is usable.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_platform_integration.py overlay_client/tests/test_setup_surface_standalone.py -q`

#### Stage 4.3 Detailed Plan
- Objective:
- Confirm capture-quality and stability acceptance gates.
- Steps:
- Validate no black/transparent/frozen/flickering output on required targets.
- Validate one full standalone `off -> on -> off` cycle with consistent desktop app switcher visibility and no crash/focus-loop/input regression.
- Acceptance criteria:
- All required-target quality/stability checks pass and are evidenced, or any always-on-top vs switcher-visibility conflict is explicitly classified as approved non-blocking exception.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "standalone or follow or interaction" -q`

#### Phase 4 Execution Order
- Implement in strict order: `4.1` -> `4.2` -> `4.3`.

#### Phase 4 Exit Criteria
- Required manual targets (`X11`, `GNOME`) are validated with evidence.
- Any required-target failure is classified as blocking and carried to Phase 5 summary, except approved always-on-top vs switcher-visibility exceptions.

### Phase 5: Readiness, Sign-Off, and Follow-Up
- Consolidate evidence and produce final disposition package.
- Risks: inconsistent evidence or incomplete blocker classification.
- Mitigations: single summary table mapping outcomes to requirements and blockers.

| Stage | Description | Status |
| --- | --- | --- |
| 5.1 | Compile requirement-by-requirement evidence and blocker status. | Completed |
| 5.2 | Finalize tester handoff docs and maintainer review packet. | Completed |
| 5.3 | Record sign-off decision and follow-up backlog. | Pending (`Awaiting maintainer sign-off`) |

#### Stage 5.1 Detailed Plan
- Objective:
- Produce complete requirement/evidence matrix from Phases 1-4.
- Steps:
- Map each requirement to code/test/manual evidence and status.
- Mark unresolved required-target failures as blocking.
- Acceptance criteria:
- Evidence matrix is complete and auditable without terminal history.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_standalone_support.py tests/test_overlay_config_payload.py overlay_client/tests/test_setup_surface_standalone.py -q`

#### Stage 5.2 Detailed Plan
- Objective:
- Align testing and plan docs with final implementation behavior.
- Steps:
- Update testing handoff and implementation result sections with exact outcomes.
- Verify docs reflect required-target blocking quality rules and approved exception handling.
- Acceptance criteria:
- Docs are internally consistent and match current behavior/policy; maintainer sign-off criteria are explicit.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_log_level_hint.py overlay_client/tests/test_launcher_group_filter.py -q`

#### Stage 5.3 Detailed Plan
- Objective:
- Record maintainer sign-off and follow-up items.
- Steps:
- Capture final pass/fail decision and any conditional release notes.
- Create prioritized follow-up items for unresolved non-blocking items.
- Acceptance criteria:
- Final decision and follow-up list are documented and explicit, with maintainer sign-off recorded.
- Verification to run:
- `make check`

#### Phase 5 Execution Order
- Implement in strict order: `5.1` -> `5.2` -> `5.3`.

#### Phase 5 Exit Criteria
- Final sign-off package is complete with clear blocker disposition.
- Plan status and stage statuses reflect actual completion state.

## Test Plan (Per Iteration)
- Env setup (once per machine):
- `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && python -m pip install -r requirements-dev.txt`
- Headless quick pass:
- `source .venv/bin/activate && python -m pytest`
- Targeted tests:
- `source .venv/bin/activate && python -m pytest <path/to/tests> -k "<pattern>"`
- Milestone checks:
- `make check`
- `make test`
- Compliance baseline check (release/compliance work):
- `python scripts/check_edmc_python.py`

## Implementation Results
- Plan created on 2026-03-09.
- Phase 1 implemented on 2026-03-09.
- Phase 2 implemented on 2026-03-09.
- Phase 3 implemented on 2026-03-09.
- Manual checklist consolidated into this plan on 2026-03-14.
- Phase 4 in progress (manual validation blocked pending maintainer-coordinated testing).
- Phase 5 in progress (awaiting maintainer sign-off).

### Phase 1 Execution Summary
- Stage 1.1:
- Completed. Standalone selectable-app contract checklist was finalized with required targets, blocking quality gates, and switcher-visibility requirements.
- Stage 1.2:
- Completed. Hide-related behavior map was documented for `X11BypassWindowManagerHint`, `WA_ShowWithoutActivating`, `Tool`, and transient-parent behavior.
- Stage 1.3:
- Completed. Restart warning and fallback contract was finalized as warning-only behavior.

### Tests Run For Phase 1
- `overlay_client/.venv/bin/python -m pytest tests/test_standalone_support.py tests/test_overlay_config_payload.py tests/test_preferences_persistence.py -q`
- Result: `11 passed in 0.13s`

### Phase 2 Execution Summary
- Stage 2.1:
- Completed. Linux standalone window profile apply path was implemented to:
- disable `X11BypassWindowManagerHint` in standalone mode,
- disable `WA_ShowWithoutActivating` in standalone mode,
- preserve `WindowStaysOnTopHint`, frameless, and click-through defaults.
- Runtime profile apply was wired into startup/show and standalone toggle transitions.
- Stage 2.2:
- Completed. Transient-parent linkage is now bypassed in standalone mode on Linux (both X11 and Wayland), with parent state cleared safely.
- Stage 2.3:
- Completed. Runtime/profile reapply now runs on standalone toggle and platform-context updates, with warning-only restart hints on incomplete apply paths.

### Tests Run For Phase 2
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface_standalone.py overlay_client/tests/test_control_surface_standalone.py overlay_client/tests/test_follow_surface_mixin.py -q`
- Result: `19 passed in 0.24s`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_window_controller.py overlay_client/tests/test_platform_integration.py -q`
- Result: `11 passed in 0.11s`

### Phase 3 Execution Summary
- Stage 3.1:
- Completed. Standalone setup/control tests were extended with profile-apply assertions and source-aware runtime/context hooks.
- Stage 3.2:
- Completed. Follow-surface tests were extended to assert standalone transient-parent bypass and non-standalone behavior preservation.
- Stage 3.3:
- Completed. Broad regression and full project gates were rerun and passed.

### Tests Run For Phase 3
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "standalone or platform or interaction or follow or window" -q`
- Result: `77 passed, 12 skipped, 169 deselected in 0.31s`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_launcher_group_filter.py overlay_client/tests/test_log_level_hint.py overlay_client/tests/test_transparency_warning.py -q`
- Result: `16 passed, 3 skipped in 0.19s`
- `make check`
- Result: `ruff: pass`, `mypy: pass`, `pytest: 572 passed, 25 skipped`

### Phase 4 Execution Summary
- Stage 4.1:
- Blocked (`Manual validation pending; target is Ubuntu GNOME (Mutter/X11)`).
- Stage 4.2:
- Blocked (`Manual validation pending; target is GNOME (Mutter/Wayland), prioritize force_xwayland=false`).
- Stage 4.3:
- Blocked (`Manual validation pending; one full off/on/off cycle remains required`).

### Tests Run For Phase 4
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_platform_integration.py overlay_client/tests/test_setup_surface_standalone.py -q`
- Result: `15 passed in 0.16s`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "standalone or follow or interaction" -q`
- Result: `61 passed, 12 skipped, 185 deselected in 0.31s`

### Phase 5 Execution Summary
- Stage 5.1:
- Completed. Requirement/evidence/blocker mapping is captured in this implementation-results section and stage status tables.
- Stage 5.2:
- Completed. Plan wording, targets, and exception policy were aligned to locked maintainer decisions.
- Stage 5.3:
- Pending (`Awaiting maintainer sign-off decision`).

### Tests Run For Phase 5
- `make check`
- Result: `ruff: pass`, `mypy: pass`, `pytest: 572 passed, 25 skipped`

### Tests Run For Checklist Consolidation (Docs-Only)
- Not rerun (documentation-only consolidation).
