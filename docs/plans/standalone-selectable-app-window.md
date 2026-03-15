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
- `overlay_client/tests/test_setup_surface.py`
- `overlay_client/tests/test_control_surface_overrides.py`
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
| 3 | Automated test coverage and regression hardening | In Progress |
| 4 | Required manual validation matrix (X11/GNOME) | Pending |
| 5 | Readiness summary, sign-off package, and follow-up list | Pending |

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
- Inputs:
- Requirements, locked decisions, and phase-level risk statements in this plan.
- Existing standalone behavior contracts from:
- `tests/test_standalone_support.py`
- `tests/test_overlay_config_payload.py`
- Work breakdown:
- Convert requirements into explicit pass/fail contract statements that are testable and auditable.
- Define mandatory behavior for standalone `off` and standalone `on` separately.
- Explicitly classify each requirement as one of:
- blocking for required targets,
- non-blocking (optional/reference target), or
- exception-eligible (maintainer-approved trade-off path).
- Add explicit language that Linux standalone behavior is in-scope for this plan and must not rely on platform-specific extra toggles.
- Deliverables:
- Contract checklist section with:
- required-target pass criteria,
- blocker policy,
- restart-warning expectations,
- off/on/off transition expectations.
- Validation matrix skeleton with required vs optional targets and status columns.
- Acceptance criteria:
- A reviewer can decide pass/fail by reading only the checklist and matrix definitions.
- Contract text is implementation-agnostic (describes outcomes, not code internals).
- No contradictory requirement wording remains between requirements, decisions, and phase exits.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest tests/test_standalone_support.py tests/test_overlay_config_payload.py -q`

#### Stage 1.2 Detailed Plan
- Objective:
- Map each current “hidden overlay” behavior to required standalone app-window profile behavior.
- Inputs:
- Current runtime touch points:
- `overlay_client/setup_surface.py`
- `overlay_client/interaction_controller.py`
- `overlay_client/follow_surface.py`
- `overlay_client/control_surface.py`
- Existing tests covering profile flags and interaction reapply behavior.
- Work breakdown:
- Audit each hide-related control surface and classify it using a keep/change/conditional decision.
- Document the intended behavior by mode:
- standalone `off`,
- standalone `on` (required-target behavior),
- transition path (`off -> on`, `on -> off`).
- Build a source-to-contract mapping table:
- runtime behavior knob,
- reason it affects discoverability,
- target decision,
- owning module,
- expected test coverage.
- Validate the matrix includes interaction reapply paths so hidden-window semantics do not reappear after runtime updates.
- Deliverables:
- Explicit keep/change matrix for:
- `X11BypassWindowManagerHint`,
- `Tool`,
- `WA_ShowWithoutActivating`,
- transient-parent linkage,
- click-through reapply behavior.
- Code-owner mapping for each matrix line item.
- Acceptance criteria:
- Every candidate behavior has one explicit decision and one owner module.
- Decisions are scoped to standalone mode and preserve off-path behavior.
- Matrix contains enough detail to drive Stage 2 implementation without reopening design.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py -q`

#### Stage 1.3 Detailed Plan
- Objective:
- Lock restart and warning behavior for live-apply limitations.
- Inputs:
- Runtime transition points in:
- `overlay_client/control_surface.py`
- `overlay_client/setup_surface.py`
- `overlay_client/launcher.py`
- Locked decision requiring user-visible warnings when reliable live-apply cannot be guaranteed.
- Work breakdown:
- Define reliability criteria for live apply:
- reliable: immediate profile identity/flag effect without restart.
- degraded: runtime apply partially succeeds but identity/profile certainty is insufficient.
- restart-required: known session/compositor path where correctness depends on restart.
- Define warning contract for degraded/restart-required paths:
- when warning is emitted,
- required log message intent,
- required user-visible message intent,
- dedupe expectations (avoid warning spam during rapid toggles).
- Define fallback behavior contract:
- no crash,
- preserve current rendering/follow behavior,
- keep configuration state coherent,
- provide deterministic next-step guidance (restart).
- Deliverables:
- Restart/fallback decision table tied to runtime transitions.
- Warning/logging contract text that can be translated into source-aware test assertions.
- Acceptance criteria:
- Restart-trigger conditions and warning language are documented and non-contradictory.
- Warning contract is deterministic enough for automated coverage.
- Fallback policy preserves safety and avoids silent state drift.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py -q`

#### Stage 1.1 Implemented Contract Checklist
| Contract Item | Mode | Required Outcome | Blocking Policy |
| --- | --- | --- | --- |
| SteamVR picker discoverability | Standalone `on` | Overlay window appears as selectable app/window target on required targets. | Blocking on required targets. |
| Desktop app switcher discoverability | Standalone `on` | Overlay appears in both GNOME Activities and `Alt+Tab` on required targets. | Blocking on required targets. |
| Capture quality | Standalone `on` | No black/transparent/frozen/flickering output. | Blocking on required targets. |
| Transition stability | `off -> on -> off` | One full cycle completes with no crash/focus-loop/input regression and switcher visibility remains consistent. | Blocking on required targets. |
| Toggle model | All modes | One shared standalone toggle across platforms, default `off`, no auto-enable. | Blocking (design contract). |
| Platform-specific toggles | All modes | No Linux-specific extra user toggles introduced for this change. | Blocking (out of scope). |
| Always-on-top/frameless/click-through defaults | Standalone `on` | Preserve always-on-top over Elite, frameless presentation, and default click-through behavior. | Blocking unless approved exception path applies. |
| Exception path | Required targets only | If always-on-top conflicts with switcher visibility, record maintainer-approved non-blocking exception and follow-up work item. | Exception-eligible (maintainer approval by `jon` only; no external artifact required). |

#### Stage 1.2 Implemented Hide-Behavior Decision Matrix
| Behavior Knob | Discoverability Risk | Standalone `off` | Standalone `on` | Owner Module(s) | Coverage Anchor |
| --- | --- | --- | --- | --- | --- |
| `X11BypassWindowManagerHint` | Can suppress WM/task-switcher discoverability. | Preserve baseline behavior. | Remove/avoid hidden-overlay semantics. | `overlay_client/setup_surface.py` | `overlay_client/tests/test_setup_surface.py` |
| `Qt.WindowType.Tool` | Tool windows may be omitted from app switchers. | Preserve baseline behavior. | Prevent hidden-tool semantics during standalone profile application/reapply. | `overlay_client/interaction_controller.py`, `overlay_client/setup_surface.py` | `overlay_client/tests/test_interaction_controller.py`, `overlay_client/tests/test_setup_surface.py` |
| `WA_ShowWithoutActivating` | Non-activating windows can be de-prioritized by WM switchers. | Preserve baseline behavior. | Disable hidden-overlay/non-activating profile for standalone app-window mode. | `overlay_client/setup_surface.py` | `overlay_client/tests/test_setup_surface.py` |
| Transient-parent linkage | Parented/transient windows may inherit hidden identity or switcher suppression. | Preserve baseline follow behavior. | Skip transient-parent attachment in standalone mode; keep follow geometry behavior. | `overlay_client/follow_surface.py` | `overlay_client/tests/test_follow_surface_mixin.py`, `overlay_client/tests/test_window_controller.py` |
| Click-through runtime reapply | Runtime state updates can reintroduce hidden profile flags. | Preserve baseline interaction behavior. | Ensure standalone app-window identity survives click-through/interaction reapply paths. | `overlay_client/interaction_controller.py`, `overlay_client/control_surface.py` | `overlay_client/tests/test_interaction_controller.py`, `overlay_client/tests/test_control_surface_overrides.py` |

#### Stage 1.3 Implemented Restart/Fallback Contract
| Runtime Apply Class | Definition | Required Behavior |
| --- | --- | --- |
| Reliable | Identity/profile changes are applied immediately and deterministically at runtime. | Apply in-place with no restart warning. |
| Degraded | Runtime apply partially succeeds but discoverability/profile certainty is insufficient. | Continue safely, emit warning + restart guidance, avoid crashes/state corruption. |
| Restart-Required | Known transition/session path where correctness is not reliable without restart. | Emit explicit warning and require restart for reliable identity/profile application. |

| Warning/Logging Rule | Contract |
| --- | --- |
| User-visible warning trigger | Emit on degraded or restart-required path when standalone profile identity cannot be guaranteed live. |
| Logging requirement | Emit deterministic log entry describing transition path, reliability class, and restart guidance. |
| Dedupe requirement | Do not spam repeated warnings for rapid toggles of the same unresolved state; coalesce by transition/session context. |
| Safety fallback requirement | Never crash; preserve rendering/follow behavior and keep configuration state coherent while warning is active. |

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
- Inputs:
- Stage 1 keep/change matrix and contract checklist in this plan.
- Current baseline behavior from:
- `overlay_client/setup_surface.py`
- `overlay_client/interaction_controller.py`
- Work breakdown:
- Implement standalone-mode profile gate that applies app-window semantics only when standalone is enabled.
- Remove or avoid hidden-overlay semantics in standalone mode for:
- `X11BypassWindowManagerHint`
- `WA_ShowWithoutActivating`
- hidden `Tool` profile behavior during runtime reapply.
- Preserve baseline invariants in standalone mode:
- `WindowStaysOnTopHint` remains enabled.
- Frameless presentation remains enabled.
- Default click-through behavior remains unchanged.
- Verify interaction reapply paths (`set_click_through`, force reapply, runtime flag refresh) cannot reintroduce hidden profile semantics while standalone mode is active.
- Deliverables:
- Standalone profile application path with mode-scoped flag behavior.
- Source comments/logging notes where runtime profile branching is non-obvious.
- Regression assertions proving off-path behavior is unchanged when standalone is disabled.
- Acceptance criteria:
- Standalone `on` uses app-window profile flags while preserving always-on-top + frameless + click-through defaults.
- Standalone `off` behavior remains unchanged across startup and runtime reapply flows.
- No platform-specific extra toggle is introduced.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py -q`

#### Stage 2.2 Detailed Plan
- Objective:
- Prevent transient-parent linkage from collapsing standalone app visibility.
- Primary touch points:
- `overlay_client/follow_surface.py`
- `overlay_client/interaction_controller.py`
- Inputs:
- Stage 1 transient-parent decision and runtime safety constraints.
- Current follow pipeline behavior from `FollowSurfaceMixin` and `WindowController`.
- Work breakdown:
- Add standalone-aware bypass for transient-parent attachment in follow/interaction paths.
- Ensure any existing transient-parent state is cleared safely when switching into standalone mode.
- Preserve follow geometry calculations, WM override handling, and tracker-based position updates for both modes.
- Confirm non-standalone mode retains legacy transient-parent behavior.
- Deliverables:
- Standalone-scoped transient-parent bypass logic.
- Guarded parent-state cleanup path for mode transitions.
- Regression coverage updates for standalone and non-standalone branches.
- Acceptance criteria:
- Standalone mode no longer binds transient parent.
- Follow remains stable (geometry updates, visibility handling, WM override behavior).
- Non-standalone transient-parent behavior remains unchanged.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_window_controller.py -q`

#### Stage 2.3 Detailed Plan
- Objective:
- Ensure startup and runtime transitions apply profile/identity reliably with explicit fallback warnings.
- Primary touch points:
- `overlay_client/launcher.py`
- `overlay_client/control_surface.py`
- `overlay_client/setup_surface.py`
- Inputs:
- Stage 1 restart/fallback contract (`reliable`, `degraded`, `restart-required`).
- Current startup bootstrap and runtime mode-toggle paths.
- Work breakdown:
- Align startup identity priming and runtime reapply logic so they evaluate the same standalone profile contract.
- Implement deterministic warning behavior for degraded/restart-required transitions without warning spam.
- Ensure runtime updates do not mutate user `force_xwayland` preference/state implicitly.
- Validate platform-context updates and standalone toggles are applied safely while preserving current rendering/follow state.
- Deliverables:
- Unified startup/runtime profile application contract in code path behavior.
- Restart-guidance warning behavior aligned with Stage 1 policy.
- Deterministic logs for transition class and applied/fallback path.
- Acceptance criteria:
- Runtime path emits deterministic logs and warnings, respects runtime settings, and does not crash on unsupported transitions.
- Startup and runtime profile behavior are consistent for the same mode/context inputs.
- `force_xwayland` remains user-controlled (no auto-mutation).
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_control_surface_overrides.py overlay_client/tests/test_setup_surface.py overlay_client/tests/test_launcher_group_filter.py -q`

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
| 3.4 | Define standalone visibility policy that eliminates foreground-gated hide/show oscillation. | Completed |
| 3.5 | Implement standalone visibility gating updates in runtime follow/visibility paths. | Completed |
| 3.6 | Add regression tests for standalone foreground-flip behavior and visibility stability. | Completed |
| 3.7 | Run targeted validation and log-based acceptance checks for hide/show stability. | Blocked (runtime log evidence pending post-fix run) |
| 3.8 | Define geometry/profile oscillation acceptance criteria and remediation non-goals. | Completed |
| 3.9 | Make standalone profile application idempotent and guard `showEvent` reentry churn. | Completed |
| 3.10 | Make click-through/runtime interaction reapply idempotent to avoid redundant window mutations. | Completed |
| 3.11 | Stabilize standalone WM override retention policy to eliminate timeout clear/re-record ping-pong. | Completed |
| 3.12 | Add regression tests for profile/click-through/WM-override oscillation prevention. | Completed |
| 3.13 | Run targeted validation and log acceptance checks for geometry/profile oscillation stability. | Blocked (runtime log evidence pending post-fix run) |

#### Stage 3.1 Detailed Plan
- Objective:
- Guarantee profile-flag behavior is deterministic under startup/toggle/context-update paths.
- Primary touch points:
- `overlay_client/tests/test_setup_surface.py`
- `overlay_client/tests/test_interaction_controller.py`
- `overlay_client/tests/test_control_surface_overrides.py`
- `tests/test_standalone_support.py`
- Inputs:
- Phase 2 runtime implementation in:
- `overlay_client/setup_surface.py`
- `overlay_client/interaction_controller.py`
- `overlay_client/control_surface.py`
- `overlay_plugin/standalone_support.py`
- Stage 1 contract requirements for:
- standalone profile flags,
- runtime reapply consistency,
- restart-warning dedupe behavior.
- Work breakdown:
- Add and/or harden assertions that standalone mode disables hidden-window semantics:
- `Qt.WindowType.Tool`,
- `X11BypassWindowManagerHint`,
- `WA_ShowWithoutActivating`.
- Add runtime assertions for click-through reapply and platform-context update flows so standalone profile flags cannot regress during state transitions.
- Add warning-behavior assertions for restart-required messaging:
- warning emitted on qualifying transition,
- warning deduped for repeated identical transition context.
- Validate standalone preference handling remains cross-platform and does not regress payload propagation of `standalone_mode`.
- Deliverables:
- Source-aware test coverage proving standalone profile rules are preserved through startup + runtime transitions.
- Regression checks for standalone preference behavior in plugin payload path.
- Acceptance criteria:
- Tests fail if hidden-window profile leaks into standalone app mode.
- Tests fail if warning dedupe or transition reapply behavior regresses.
- Tests fail if standalone preference handling regresses to platform-guarded behavior.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_control_surface_overrides.py tests/test_standalone_support.py tests/test_overlay_config_payload.py -q`

#### Stage 3.2 Detailed Plan
- Objective:
- Guarantee standalone bypasses transient-parent linking without follow regressions.
- Primary touch points:
- `overlay_client/tests/test_follow_surface_mixin.py`
- `overlay_client/tests/test_window_controller.py`
- `overlay_client/tests/test_exception_scoping.py`
- Inputs:
- Phase 2 transient-parent behavior changes in:
- `overlay_client/follow_surface.py`
- `overlay_client/interaction_controller.py`
- Existing follow/window-controller behavior baselines.
- Work breakdown:
- Add explicit standalone-branch assertions that transient-parent state is cleared and not rebound while standalone mode is active.
- Preserve non-standalone assertions to confirm transient-parent binding remains functional where expected.
- Add defensive/error-path assertions that transient-parent cleanup failures remain scoped/logged and do not crash follow/runtime flows.
- Run follow/window-controller regression slices to confirm geometry/visibility paths remain unchanged.
- Deliverables:
- Standalone/non-standalone branch test coverage for transient-parent behavior.
- Regression evidence that follow/window-controller behavior remains stable.
- Acceptance criteria:
- Test coverage proves parent-link bypass is standalone-scoped and safe.
- No regressions in follow/window-controller tests.
- No unhandled exceptions introduced in transient-parent cleanup paths.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_window_controller.py overlay_client/tests/test_exception_scoping.py -q`

#### Stage 3.3 Detailed Plan
- Objective:
- Confirm project-level quality gates remain green after profile changes.
- Primary touch points:
- `overlay_client/tests/` targeted standalone/follow/interaction slices.
- Top-level quality gates (`ruff`, `mypy`, pytest aggregate).
- Inputs:
- Completed Stage 3.1 and 3.2 targeted coverage updates.
- Existing project quality gate commands.
- Work breakdown:
- Run consolidated targeted standalone regression bundle first (fast signal path).
- Run lint/static checks for touched modules.
- Run project-wide quality gate (`make check`) as final integration verification.
- Record exact outcomes including:
- total passed/skipped counts,
- any expected PyQt skips,
- any environment-related caveats.
- Deliverables:
- Documented pass/fail output for targeted + broad quality runs.
- Updated plan `Implementation Results` entries for Phase 3 with exact command outputs.
- Acceptance criteria:
- `ruff`, `mypy`, and pytest gates pass; no new failing tests introduced.
- Targeted standalone/follow/interaction slices pass before broad gate run.
- Any skipped tests are intentional and documented with reason.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "standalone or platform or interaction or follow or window" -q`
- `overlay_client/.venv/bin/python -m ruff check overlay_client/setup_surface.py overlay_client/interaction_controller.py overlay_client/follow_surface.py overlay_client/control_surface.py overlay_plugin/standalone_support.py`
- `make check`

#### Stage 3.4 Detailed Plan
- Objective:
- Lock a deterministic standalone visibility contract that removes repetitive `visible -> hidden -> visible` churn caused by foreground transitions.
- Primary touch points:
- `overlay_client/window_controller.py`
- `overlay_client/follow_surface.py`
- `overlay_client/control_surface.py`
- Inputs:
- Current visibility decision (`force_render or (state.is_visible and state.is_foreground)`).
- Observed runtime logs showing repeated visibility flips while standalone mode remains enabled.
- Work breakdown:
- Define normative visibility invariants for follow-state processing (source of truth for Stage 3.5 implementation and Stage 3.6 tests).
- Define quantitative churn-failure criteria for log validation in Stage 3.7.
- Lock non-goals for this remainder of Phase 3:
- no change to missing-tracker-state policy,
- no change to always-on-top/frameless/click-through defaults,
- no new preferences/toggles/dependencies.
- Keep `force_render` precedence unchanged across both modes.
- Standalone Visibility Invariant Matrix:

| Case | Inputs | Standalone `on` (force_render `false`) | Standalone `off` (force_render `false`) | Any mode (`force_render=true`) |
| --- | --- | --- | --- | --- |
| 3.4-A | Follow state present, `is_visible=true`, `is_foreground=true` | Show | Show | Show |
| 3.4-B | Follow state present, `is_visible=true`, `is_foreground=false` | Hide | Hide | Show |
| 3.4-C | Follow state present, `is_visible=false`, `is_foreground=true/false` | Hide | Hide | Show |
| 3.4-D | Follow state missing (`_handle_missing_follow_state`) | Unchanged from current policy in this phase remainder | Unchanged from current policy | Unchanged from current policy |

- Log Churn Failure Definition (Stage 3.7):

| Rule | Failure Condition |
| --- | --- |
| 3.4-L1 | For stable tracker segments (`same id`, `is_visible=true`, duration >= 3 follow polls), alternating visibility transitions `visible -> hidden -> visible` are observed in standalone mode. |
| 3.4-L2 | More than one visibility state transition occurs without an input-state change in standalone mode. |
- Deliverables:
- Documented standalone visibility policy and unchanged off-path behavior contract.
- Stage-scoped source mapping for visibility decision points and acceptance metrics.
- Acceptance criteria:
- A reviewer can determine from plan text whether a runtime behavior is compliant for standalone `on` vs `off`.
- The policy maps directly to concrete code points without ambiguity, including `force_render` precedence and missing-state non-goals.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_window_controller.py overlay_client/tests/test_follow_surface_mixin.py -q`

#### Stage 3.5 Detailed Plan
- Objective:
- Implement the standalone visibility policy so standalone mode does not hide on foreground loss.
- Primary touch points:
- `overlay_client/window_controller.py`
- `overlay_client/follow_surface.py`
- `overlay_client/control_surface.py`
- Work breakdown:
- Update `WindowController.post_process_follow_state(...)` to accept `standalone_mode` and compute `should_show` as:
- if `force_render` is `true`: `True`,
- else: `state.is_visible and state.is_foreground`.
- Thread `standalone_mode` from `FollowSurfaceMixin._post_process_follow_state(...)` into the window-controller call.
- Ensure standalone toggle transitions reapply the current follow-driven visibility path immediately (no wait for next tracker tick) while preserving existing interaction-controller reapply flow.
- Preserve `force_render` behavior exactly; do not alter missing-state handling in `_handle_missing_follow_state` in this stage unless a test proves it is required for the invariant matrix.
- Add temporary debug log context where needed to make visibility decisions auditable in log review:
- inputs: standalone mode, force_render, tracker `is_visible`, tracker `is_foreground`,
- output: computed `should_show`.
- Rollback criteria for this stage:
- if any non-standalone regression is detected in visibility/follow tests, revert to pre-change gating and record a blocker under Phase 3 pending work.
- Deliverables:
- Runtime visibility-gating implementation for standalone mode.
- Mode-scoped guardrails preserving off-path behavior.
- Auditable decision logs for Stage 3.7 validation.
- Acceptance criteria:
- Standalone mode no longer hides solely because `is_foreground=False` while the tracked game window remains visible.
- Non-standalone mode continues using foreground-gated visibility logic.
- `force_render` behavior remains unchanged and higher precedence than mode-specific visibility gating.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_window_controller.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_control_surface_overrides.py -q`

#### Stage 3.6 Detailed Plan
- Objective:
- Add automated regression coverage that catches standalone hide/show oscillation regressions.
- Primary touch points:
- `overlay_client/tests/test_window_controller.py`
- `overlay_client/tests/test_follow_surface_mixin.py`
- `overlay_client/tests/test_follow_helpers.py`
- Work breakdown:
- Add/adjust concrete tests with explicit assertions:

| Test File | Test Intent | Required Assertion |
| --- | --- | --- |
| `overlay_client/tests/test_window_controller.py` | Standalone foreground-loss behavior | `standalone_mode=True`, `force_render=False`, `is_visible=True`, `is_foreground=False` results in `update_follow_visibility(True)` |
| `overlay_client/tests/test_window_controller.py` | Non-standalone foreground-loss behavior | `standalone_mode=False`, `force_render=False`, `is_visible=True`, `is_foreground=False` results in `update_follow_visibility(False)` |
| `overlay_client/tests/test_window_controller.py` | Force-render precedence | `force_render=True` yields `update_follow_visibility(True)` regardless of standalone/foreground flags |
| `overlay_client/tests/test_follow_helpers.py` | Follow-surface propagation | `standalone_mode` is forwarded into `post_process_follow_state` call path |
| `overlay_client/tests/test_control_surface_overrides.py` | Runtime toggle immediate reapply | standalone toggle applies visibility decision without waiting for subsequent tracker poll |

- Add sequence-level idempotence test:
- repeated calls with unchanged standalone inputs must not emit alternating visibility updates.
- Preserve existing tests that encode non-standalone behavior; update only when they conflict with the new standalone invariant matrix.
- Deliverables:
- Focused tests covering standalone and non-standalone visibility branches.
- Regression test coverage for visibility flip sequences.
- Acceptance criteria:
- Tests fail if standalone mode regresses to foreground-gated hide behavior.
- Tests fail if non-standalone foreground gate behavior changes unexpectedly.
- Tests fail if visibility update calls oscillate under unchanged standalone inputs.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_window_controller.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_follow_helpers.py -q`

#### Stage 3.7 Detailed Plan
- Objective:
- Validate implementation behavior with targeted automation and runtime log acceptance checks.
- Primary touch points:
- `overlay_client/tests/` targeted visibility/follow/control tests.
- `/home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log`
- Work breakdown:
- Run targeted standalone/follow/control regression bundle after implementation.
- Run a runtime log review pass using explicit acceptance checks:

| Check | Command | Pass Condition |
| --- | --- | --- |
| 3.7-A | `rg -n "Tracker state:|Overlay visibility set to" /home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log | tail -n 200` | No repeated `visible -> hidden -> visible` sequence during stable tracker segments where `is_visible=true` and standalone mode is enabled |
| 3.7-B | `rg -n "Overlay visibility set to (visible|hidden)" /home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log | tail -n 120` | Visibility transitions correspond to real input-state changes only (no churn while inputs are unchanged) |
| 3.7-C | `rg -n "Applied stand-alone window profile|Tracker state" /home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log | tail -n 200` | Standalone mode is active while visibility behavior matches Stage 3.4 invariants |

- If any churn failure condition is hit:
- capture the minimal offending snippet in `Implementation Results`,
- mark Stage 3.7 as `Blocked`,
- do not mark Phase 3 complete.
- Record pass/fail evidence in `Implementation Results` with exact command outputs and concise interpretation.
- Deliverables:
- Command-level verification evidence.
- Log-based acceptance evidence for absence of repetitive hide/show oscillation under standalone mode.
- Acceptance criteria:
- Targeted tests pass.
- Runtime logs satisfy checks 3.7-A through 3.7-C with no churn failures.
- Any failure is explicitly documented with blocker status and next action.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_window_controller.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_control_surface_overrides.py overlay_client/tests/test_follow_helpers.py -q`
- `rg -n "Overlay visibility set to" /home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log | tail -n 80`

#### Stage 3.8 Detailed Plan
- Objective:
- Define explicit pass/fail criteria for standalone geometry/profile oscillation and lock remediation non-goals.
- Primary touch points:
- `docs/plans/standalone-selectable-app-window.md`
- `/home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log`
- Work breakdown:
- Define oscillation failure signatures for stable tracker segments (`same id`, stable geometry):
- repeated `WM override decision ... clear_reason=override timeout` followed by `Recorded WM authoritative rect` for the same rect,
- repeated `Applied stand-alone window profile ... reason=show_event` bursts without input-state changes.
- Define acceptance thresholds:
- after startup grace (`<= 5s`), no periodic timeout-clear/re-record loop for unchanged WM rect,
- `show_event` profile reapply logging is bounded in stable runtime segments (target `<= 2` in a 60-second stable window),
- no regression to visibility policy from stages `3.4-3.7`.
- Lock non-goals:
- no new user-facing settings,
- no change to force-render precedence,
- no expansion of Phase 4 manual validation scope.
- Deliverables:
- Stage-level oscillation acceptance matrix and fail signatures.
- Acceptance criteria:
- Pass/fail is mechanically decidable from logs.
- Verification to run:
- `rg -n "Applied stand-alone window profile: .*reason=show_event|WM override decision|Recorded WM authoritative rect|Clearing WM authoritative rect" /home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log`

#### Stage 3.9 Detailed Plan
- Objective:
- Eliminate self-induced profile churn via idempotent profile application and `showEvent` guard rails.
- Primary touch points:
- `overlay_client/setup_surface.py`
- `overlay_client/overlay_client.py`
- Work breakdown:
- Make `_set_window_flag(...)` no-op when requested state already matches current flags.
- Add profile-signature dedupe in `_apply_standalone_window_profile(...)`.
- Add `showEvent` reentry/duplication guard so unchanged profile inputs do not reapply repeatedly.
- Preserve behavior:
- real mode/context transitions still reapply immediately.
- Deliverables:
- Idempotent standalone profile path with reduced `show_event` churn.
- Acceptance criteria:
- unchanged `showEvent` inputs do not repeatedly mutate flags/attributes.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py -q`

#### Stage 3.10 Detailed Plan
- Objective:
- Remove redundant click-through/runtime interaction mutations when state is unchanged.
- Primary touch points:
- `overlay_client/interaction_controller.py`
- `overlay_client/follow_surface.py`
- Work breakdown:
- Add click-through application signature (transparent + standalone + wayland/x11 tool intent + handle availability).
- Skip redundant reapply side effects when signature is unchanged:
- `set_window_flag`,
- `ensure_visible`/`raise`,
- platform `prepare_window` + apply path.
- Preserve behavior:
- real state changes, drag restoration, and force-render paths still apply immediately.
- Deliverables:
- Idempotent interaction reapply behavior under stable state.
- Acceptance criteria:
- no repeated interaction mutations for unchanged click-through intent.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_control_surface_overrides.py -q`

#### Stage 3.11 Detailed Plan
- Objective:
- Stop standalone WM override timeout ping-pong by stabilizing override retention policy.
- Primary touch points:
- `overlay_client/follow_controller.py`
- `overlay_client/follow_geometry.py`
- `overlay_client/interaction_surface.py`
- `overlay_client/follow_surface.py`
- Work breakdown:
- Make override clear policy standalone-aware:
- do not clear on TTL alone when tracker geometry is stable and authoritative rect is unchanged,
- clear on real tracker changes, lost follow state, or mode/context transition.
- Suppress duplicate authoritative-rect recordings from `moveEvent` when rect is unchanged.
- Preserve non-standalone behavior unless tests require targeted adjustment.
- Deliverables:
- Stable standalone override handling with deterministic clear/retain rules.
- Acceptance criteria:
- no periodic `override timeout -> clear -> re-record same rect` loop for stable inputs.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_geometry.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_interaction_surface.py -q`

#### Stage 3.12 Detailed Plan
- Objective:
- Add regression tests preventing recurrence of profile/interaction/WM-override oscillation loops.
- Primary touch points:
- `overlay_client/tests/test_setup_surface.py`
- `overlay_client/tests/test_interaction_controller.py`
- `overlay_client/tests/test_follow_geometry.py`
- `overlay_client/tests/test_follow_surface_mixin.py`
- `overlay_client/tests/test_interaction_surface.py`
- Work breakdown:
- Add idempotence tests for profile and click-through reapply paths.
- Add standalone WM override stability tests:
- stable tracker + stable WM rect does not timeout-clear/re-record loop,
- tracker/lost-state transitions still clear correctly.
- Add sequence-level stable-input tests across repeated follow ticks.
- Deliverables:
- Oscillation-prevention regression suite.
- Acceptance criteria:
- tests fail if profile/WM-override loop behavior regresses.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_follow_geometry.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_interaction_surface.py -q`

#### Stage 3.13 Detailed Plan
- Objective:
- Validate oscillation remediation with targeted tests and explicit log-based acceptance checks.
- Primary touch points:
- `overlay_client/tests/` suites for stages `3.9-3.12`.
- `/home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log`
- Work breakdown:
- Run targeted regression bundle.
- Run log checks:

| Check | Command | Pass Condition |
| --- | --- | --- |
| 3.13-A | `rg -n "Applied stand-alone window profile: .*reason=show_event" /home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log` | No continuous `show_event` profile spam in stable runtime segment (bounded by Stage 3.8 threshold) |
| 3.13-B | `rg -n "WM override decision|Recorded WM authoritative rect|Clearing WM authoritative rect" /home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log` | No timeout-clear/re-record loop for same rect under stable tracker inputs |
| 3.13-C | `rg -n "Follow visibility decision|Overlay visibility set to" /home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log` | Stage 3.4 visibility invariants remain satisfied |

- On failure:
- capture minimal snippet in `Implementation Results`,
- mark failing stage(s) `Blocked`,
- keep Phase 3 open.
- Deliverables:
- Post-fix test + log evidence of oscillation stability.
- Acceptance criteria:
- Targeted tests and checks `3.13-A`..`3.13-C` pass.
- Verification to run:
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_follow_geometry.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_interaction_surface.py -q`
- `rg -n "Applied stand-alone window profile: .*reason=show_event|WM override decision|Recorded WM authoritative rect|Clearing WM authoritative rect|Follow visibility decision|Overlay visibility set to" /home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log | tail -n 300`

#### Phase 3 Remaining-Stage Execution Matrix
| Stage | Primary Code/Doc Touch Points | Required Verification | Done Definition |
| --- | --- | --- | --- |
| 3.4 | `overlay_client/window_controller.py`, `overlay_client/follow_surface.py`, `overlay_client/control_surface.py`, this plan doc | `pytest overlay_client/tests/test_window_controller.py overlay_client/tests/test_follow_surface_mixin.py -q` | Visibility invariants and churn-failure criteria are explicit and map to concrete code paths |
| 3.5 | `overlay_client/window_controller.py`, `overlay_client/follow_surface.py`, `overlay_client/control_surface.py` | `pytest overlay_client/tests/test_window_controller.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_control_surface_overrides.py -q` | Standalone visibility branch implemented with `force_render` precedence and non-standalone behavior preserved |
| 3.6 | `overlay_client/tests/test_window_controller.py`, `overlay_client/tests/test_follow_surface_mixin.py`, `overlay_client/tests/test_follow_helpers.py`, `overlay_client/tests/test_control_surface_overrides.py` | `pytest overlay_client/tests/test_window_controller.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_follow_helpers.py overlay_client/tests/test_control_surface_overrides.py -q` | Regression tests fail on standalone foreground-loop regressions and pass on expected behavior |
| 3.7 | Runtime logs + targeted tests | `pytest ...test_window_controller.py ...test_follow_surface_mixin.py ...test_control_surface_overrides.py ...test_follow_helpers.py -q`; `rg` checks 3.7-A..3.7-C | Log evidence confirms no standalone visibility churn under stable inputs |
| 3.8 | This plan doc + latest `overlay_client.log` evidence mapping | `rg -n "Applied stand-alone window profile: .*reason=show_event|WM override decision|Recorded WM authoritative rect|Clearing WM authoritative rect" .../overlay_client.log` | Geometry/profile oscillation failure signatures and acceptance thresholds are documented and testable |
| 3.9 | `overlay_client/setup_surface.py`, `overlay_client/overlay_client.py` | `pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py -q` | Profile application and `showEvent` path are idempotent for unchanged inputs |
| 3.10 | `overlay_client/interaction_controller.py`, `overlay_client/follow_surface.py` | `pytest overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_control_surface_overrides.py -q` | Click-through reapply path avoids redundant window mutations when intent is unchanged |
| 3.11 | `overlay_client/follow_controller.py`, `overlay_client/follow_geometry.py`, `overlay_client/interaction_surface.py`, `overlay_client/follow_surface.py` | `pytest overlay_client/tests/test_follow_geometry.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_interaction_surface.py -q` | Standalone WM override no longer timeout-clear/re-records same rect in stable state |
| 3.12 | `overlay_client/tests/test_setup_surface.py`, `overlay_client/tests/test_interaction_controller.py`, `overlay_client/tests/test_follow_geometry.py`, `overlay_client/tests/test_follow_surface_mixin.py`, `overlay_client/tests/test_interaction_surface.py` | `pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_follow_geometry.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_interaction_surface.py -q` | Automated suite enforces oscillation prevention across profile, interaction, and WM override paths |
| 3.13 | Runtime logs + targeted tests for 3.9-3.12 | `pytest` bundle for 3.9-3.12 plus `rg` checks 3.13-A..3.13-C | Post-fix runtime logs and tests prove oscillation loop is resolved without visibility-policy regression |

#### Phase 3 Execution Order
- Implement in strict order: `3.1` -> `3.2` -> `3.3` -> `3.4` -> `3.5` -> `3.6` -> `3.7` -> `3.8` -> `3.9` -> `3.10` -> `3.11` -> `3.12` -> `3.13`.

#### Phase 3 Exit Criteria
- Automated validation is green and documented.
- Standalone visibility no longer depends on tracker foreground state while target visibility remains true.
- No repetitive standalone visibility oscillation is observed in runtime logs under stable tracked visibility conditions.
- No periodic standalone WM override timeout clear/re-record loop is observed for unchanged tracker and WM-authoritative geometry.
- Standalone `show_event` profile reapply logs are bounded and not emitted continuously in stable runtime segments.
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
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_platform_context.py overlay_client/tests/test_setup_surface.py -q`

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
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_platform_context.py overlay_client/tests/test_setup_surface.py -q`

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
| 5.1 | Compile requirement-by-requirement evidence and blocker status. | Pending |
| 5.2 | Finalize tester handoff docs and maintainer review packet. | Pending |
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
- `overlay_client/.venv/bin/python -m pytest tests/test_standalone_support.py tests/test_overlay_config_payload.py overlay_client/tests/test_setup_surface.py -q`

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
- Phase 1 artifacts expanded on 2026-03-14 (contract checklist, hide-behavior matrix, restart/fallback contract).
- Phase 2 implemented on 2026-03-14.
- Phase 3 baseline stages (3.1-3.3) implemented on 2026-03-14.
- Phase 3 reopened on 2026-03-14 for standalone visibility-loop stabilization stages (3.4-3.7).
- Phase 3 expanded on 2026-03-15 with additional geometry/profile oscillation remediation stages (3.8-3.13).
- Phase 3 remaining implementation executed on 2026-03-15:
- stages `3.4`, `3.5`, `3.6`, `3.8`, `3.9`, `3.10`, `3.11`, and `3.12` completed,
- stages `3.7` and `3.13` are blocked pending fresh post-fix runtime log capture/validation.
- Detailed execution matrix for remaining Phase 3 stages (3.4-3.13) documented on 2026-03-14.
- Phase 4 not complete (manual required-target validation pending).
- Phase 5 not complete.

### Phase 1 Execution Summary
- Stage 1.1:
- Completed. Standalone selectable-app contract checklist was finalized with explicit pass/fail outcomes for required targets, transition stability, blocker policy, and exception eligibility.
- Stage 1.2:
- Completed. Hide-related behavior decision matrix was documented for `X11BypassWindowManagerHint`, `WA_ShowWithoutActivating`, `Tool`, transient-parent behavior, and click-through runtime reapply paths.
- Stage 1.3:
- Completed. Restart/fallback contract was finalized with reliability classes (`reliable`, `degraded`, `restart-required`) and deterministic warning/logging requirements.

### Phase 2 Execution Summary
- Stage 2.1:
- Completed. Removed Windows-only standalone runtime guard in client setup/toggle paths and implemented standalone profile application that:
- disables `X11BypassWindowManagerHint` in standalone mode on Linux,
- disables `WA_ShowWithoutActivating` in standalone mode,
- disables `Qt.WindowType.Tool` in standalone mode across runtime reapply paths,
- preserves `WindowStaysOnTopHint`, frameless presentation, and click-through defaults.
- Stage 2.2:
- Completed. Added standalone-scoped transient-parent bypass/cleanup so Linux standalone mode clears and avoids transient-parent linkage while preserving non-standalone behavior.
- Stage 2.3:
- Completed. Unified startup/runtime profile reapply wiring (`showEvent`, standalone toggle, platform-context updates) and added deduped restart-required warning messaging/logging for Linux runtime transitions where live reliability is not guaranteed.

### Additional Phase 2 Scope Completed
- Removed Windows-only standalone preference guard in plugin support (`standalone_mode_preference_value` now reflects the stored preference cross-platform).
- Updated standalone preference label to remove Windows-only wording.

### Tests Run For Phase 2
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py -q`
- Result: `7 passed, 3 skipped in 0.31s`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_window_controller.py -q`
- Result: `8 passed in 0.15s`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_control_surface_overrides.py overlay_client/tests/test_setup_surface.py overlay_client/tests/test_launcher_group_filter.py -q`
- Result: `14 passed, 3 skipped in 0.28s`
- `overlay_client/.venv/bin/python -m pytest tests/test_standalone_support.py tests/test_overlay_config_payload.py tests/test_preferences_persistence.py -q`
- Result: `6 passed in 0.23s`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_exception_scoping.py -q`
- Result: `6 passed in 0.22s`

### Phase 3 Execution Summary
- Stage 3.1:
- Completed. Focused standalone-profile regression coverage was hardened for:
- startup/runtime standalone window-profile flags,
- click-through/runtime reapply behavior,
- restart-warning dedupe behavior,
- cross-platform standalone preference payload propagation.
- Stage 3.2:
- Completed. Standalone transient-parent bypass coverage was validated alongside non-standalone behavior preservation and exception-scoping checks.
- Stage 3.3:
- Completed. Broad regression gates (`-k` targeted slice + `ruff` + `make check`) were executed and passed.
- Stage 3.4:
- Completed. Standalone visibility invariants and churn-failure criteria were documented and mapped to runtime decision points.
- Stage 3.5:
- Completed. Follow visibility now requires tracker `is_visible` and `is_foreground` unless `force_render` is enabled; standalone mode no longer bypasses foreground gating.
- Stage 3.6:
- Completed. Regression coverage now asserts standalone foreground-loss visibility behavior, non-standalone foreground gating, and stable-input non-oscillation behavior.
- Stage 3.7:
- Blocked. Targeted tests passed, but current runtime logs still contain churn signatures and require a fresh post-fix runtime capture for acceptance.
- Stage 3.8:
- Completed. Geometry/profile oscillation acceptance criteria and non-goals were explicitly defined and tied to log signatures.
- Stage 3.9:
- Completed. Standalone profile application was made idempotent via window-flag no-op guards and profile-signature dedupe, including `showEvent` reentry suppression for unchanged inputs.
- Stage 3.10:
- Completed. Click-through/runtime interaction reapply now uses application signatures to skip redundant window mutations while preserving forced reapply paths.
- Stage 3.11:
- Completed. Standalone WM override retention was stabilized:
- timeout expiry is suppressed for unchanged standalone tracker tuples,
- mode/context transitions clear overrides deterministically,
- duplicate `moveEvent` override records for identical rects are skipped.
- Stage 3.12:
- Completed. Regression coverage was added for profile idempotence, interaction idempotence, standalone WM override retention, and duplicate move-event suppression.
- Stage 3.13:
- Blocked. Current runtime log acceptance checks still show pre-fix churn signatures (`show_event` profile spam and timeout clear/re-record loops); a fresh post-fix runtime run is required.

### Tests Run For Phase 3
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_control_surface_overrides.py tests/test_standalone_support.py tests/test_overlay_config_payload.py -q`
- Result: `18 passed, 3 skipped in 0.28s`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_window_controller.py overlay_client/tests/test_exception_scoping.py -q`
- Result: `14 passed in 0.25s`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests -k "standalone or platform or interaction or follow or window" -q`
- Result: `65 passed, 12 skipped, 169 deselected in 0.39s`
- `overlay_client/.venv/bin/python -m ruff check overlay_client/setup_surface.py overlay_client/interaction_controller.py overlay_client/follow_surface.py overlay_client/control_surface.py overlay_plugin/standalone_support.py`
- Result: `All checks passed!`
- `make check`
- Result: `ruff: pass`, `mypy: pass`, `pytest: 555 passed, 25 skipped`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_control_surface_overrides.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_follow_helpers.py overlay_client/tests/test_follow_controller.py overlay_client/tests/test_interaction_surface.py overlay_client/tests/test_follow_geometry.py overlay_client/tests/test_window_controller.py -q`
- Result: `74 passed, 10 skipped in 0.50s`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_window_controller.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_control_surface_overrides.py overlay_client/tests/test_follow_helpers.py -q`
- Result: `26 passed, 3 skipped in 0.26s`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_follow_geometry.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_interaction_surface.py overlay_client/tests/test_follow_controller.py -q`
- Result: `55 passed, 7 skipped in 0.37s`
- `overlay_client/.venv/bin/python -m pytest overlay_client/tests/test_follow_geometry.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_interaction_surface.py -q`
- Result: `42 passed, 4 skipped in 0.24s`
- `overlay_client/.venv/bin/python -m ruff check overlay_client/setup_surface.py overlay_client/interaction_controller.py overlay_client/follow_controller.py overlay_client/follow_surface.py overlay_client/interaction_surface.py overlay_client/control_surface.py overlay_client/tests/test_setup_surface.py overlay_client/tests/test_interaction_controller.py overlay_client/tests/test_follow_controller.py overlay_client/tests/test_follow_surface_mixin.py overlay_client/tests/test_interaction_surface.py`
- Result: `All checks passed!`
- `rg -n "Tracker state:|Overlay visibility set to" /home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log | tail -n 200`
- Result: log still contains `visible -> hidden -> visible` churn signatures from previous runtime capture.
- `rg -n "Applied stand-alone window profile: .*reason=show_event|WM override decision|Recorded WM authoritative rect|Clearing WM authoritative rect|Follow visibility decision|Overlay visibility set to" /home/jon/.local/share/EDMarketConnector/logs/EDMCModernOverlay/overlay_client.log | tail -n 300`
- Result: log still contains repeated `reason=show_event` entries and periodic `override timeout` clear/re-record loops from previous runtime capture.

### Pending Work (Post-Phase 3)
- Phase 3 stage `3.7` is blocked pending fresh runtime log capture after deploying this patch set and rerunning standalone follow flow.
- Phase 3 stage `3.13` is blocked pending fresh runtime log capture proving `show_event` and WM-override oscillation signatures are resolved.
- Phase 4 required manual validation on Ubuntu GNOME (X11) and GNOME Wayland remains blocked pending maintainer-coordinated runs.
- Phase 5 readiness/sign-off packaging remains pending.
