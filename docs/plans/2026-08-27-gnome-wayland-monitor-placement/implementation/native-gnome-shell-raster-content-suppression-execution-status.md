# Native GNOME Shell-Raster Content Suppression: Execution Status

**Authoritative plan:**
`implementation/native-gnome-shell-raster-content-suppression-plan.md`

**Execution authority:**
`implementation/native-gnome-shell-raster-content-suppression-orchestration-prompt.md`

## Step Dashboard

| Step | Status | Evidence / decision | Next action |
| --- | --- | --- | --- |
| 1 | Completed | Two isolated tasks added neutral intent and a GNOME-owned, capability-gated contract; unsupported helpers send no visibility field and retain visible behavior. Main-context focused review passed. | Generate and review Step 2 code tasks. |
| 2 | Completed | Capability-gated helper operation applies `set_opacity(0|255)` to retained single/region records and restores visible content on failure. Main-context helper suite passed. | Generate and review Step 3 code tasks. |
| 3 | Completed | Task 3.1 transported neutral intent; Task 3.2 wires it in the GNOME-owned runtime, preserving actor continuity and capability-gating the optional field. Main-context focused suite: 228 passed. | Start Step 4 automated validation; live acceptance remains user-gated. |
| 4 | Completed | The helper remained active and capable. Neutral retained-actor availability prevents `target_focused_remap_warmup` from intermittently suppressing focused Shell-raster content while generic Qt remains unmapped. Focused suite: 275 passed; external project gates: 1,697 passed. User verified the complete live focus/monitor matrix. | Await explicit commit approval. |

## Context Ledger

Add one row after every generator, code-assist, remediation, validation, or
main-thread review context. Every implementation handoff must contain exactly:
`Status; Files changed; Validation commands/results; Decisions; Risks; Next exact action.`

| Step | Context ID | Kind | Status | Summary | Handoff path |
| --- | --- | --- | --- | --- | --- |
| 0 | `orchestration-setup-2026-08-28` | Main-thread planning | Completed | Invalidated the unsafe direct-authorization plan and prepared the replacement design, plan, status dashboard, and autonomous orchestration prompt. | N/A |
| 1 | `step01-task-generator-2026-08-28` | Fresh code-task-generator | Completed | Generated separate neutral-policy and GNOME-capability tasks; neither permits actor behavior or preference wiring. | `implementation/code-assist/native-gnome-shell-raster-content-suppression/step01/` |
| 1 | `step01-task01-code-assist-2026-08-28` | Fresh code-assist | Completed | Added the pure `visible`/`suppressed` decision intent. Focused policy/boundary pytest: 22 passed; Ruff and diff check passed. | `implementation/code-assist/native-gnome-shell-raster-content-suppression/step01/task-01-neutral-content-visibility-intent/handoff.md` |
| 1 | `step01-task02-code-assist-2026-08-28` | Fresh code-assist | Completed | Added optional GNOME-owned request/result capability contract. Unsupported helpers omit the wire field and remain visible; continuity authorization is unchanged. Focused pytest: 134 passed; Ruff and diff check passed. | `implementation/code-assist/native-gnome-shell-raster-content-suppression/step01/task-02-gnome-content-visibility-capability-contract/handoff.md` |
| 1 | `step01-main-review-2026-08-28` | Main-thread review | Completed | Independently inspected source/test diffs and reran focused policy, architecture, and helper presentation tests: 52 passed; Ruff and diff check passed. | N/A |
| 2 | `step02-task-generator-2026-08-28` | Fresh code-task-generator | Completed | Generated one helper-only task requiring actor continuity for single and region raster paths while preserving hard lifecycle cleanup. | `implementation/code-assist/native-gnome-shell-raster-content-suppression/step02/` |
| 2 | `step02-task01-code-assist-2026-08-28` | Fresh code-assist | Completed | Added capability advertisement and reversible retained-actor opacity handling with source contracts; no preference wiring or live action. Focused pytest: 162 passed; Ruff and diff check passed. | `implementation/code-assist/native-gnome-shell-raster-content-suppression/step02/task-01-helper-owned-reversible-raster-content-suppression/handoff.md` |
| 2 | `step02-main-review-2026-08-28` | Main-thread review | Completed | Independently reran the extension source, presentation-state, and runtime suite: 162 passed; Ruff and diff check passed. | N/A |
| 3 | `step03-task01-code-assist-2026-08-28` | Fresh code-assist | Completed | Transported debounced neutral intent through generic runtime/follow surfaces without GNOME protocol imports. | `implementation/code-assist/native-gnome-shell-raster-content-suppression/step03/task-01-transport-debounced-neutral-content-intent/handoff.md` |
| 3 | `step03-task02-code-assist-2026-08-28` | Fresh code-assist | Completed — awaiting main review | Native GNOME bundle now resolves the healthy-helper capability, sends supported `visible`/`suppressed` values, preserves eligible fullscreen continuity, and keeps unsupported suppression visibly stable with diagnostics. Focused suite: 228 passed. | `implementation/code-assist/native-gnome-shell-raster-content-suppression/step03/task-02-wire-native-gnome-content-visibility/handoff.md` |
| 3 | `step03-main-review-2026-08-28` | Main-thread review | Completed | Independently reran the focused GNOME/runtime/policy/follow/transition/boundary suite: 228 passed; Ruff and diff check passed. | N/A |
| 4 | `step04-automated-validation-2026-08-28` | Main-thread validation | Blocked | Focused suite: 228 passed. `make check`: Ruff and mypy passed, then pytest reported 1 fake-runner signature failure and 5 sandbox loopback-socket setup errors. Per stop protocol, no source remediation or redundant `make test` run occurred. | N/A — fresh remediation required |
| 4 | `step04-fake-runner-contract-remediation-2026-08-28` | Fresh code-assist | Completed | Updated only the stale test double to accept, record, and assert neutral `content_visibility`. RED reproduced the signature failure; GREEN exact test: 1 passed; consumer/boundary suite: 47 passed; Ruff and diff check passed. | `implementation/code-assist/native-gnome-shell-raster-content-suppression/step04/fake-runner-contract-remediation/handoff.md` |
| 4 | `step04-external-project-gates-2026-08-28` | Main-thread validation | Completed | Outside the socket-restricted sandbox, `make check` and `make test` each passed Ruff, mypy, and 1,691 tests; diff check passed. | N/A |
| 4 | `step04-helper-update-2026-08-28` | User-authorized deployment | Completed | `scripts/dev_gnome_helper.sh update --yes --no-enable` copied the helper to the user extension directory. Source and installed files match; no enable/reload action was performed. | User logout/login, then `scripts/dev_gnome_helper.sh status` |
| 4 | `step04-helper-status-after-login-2026-08-28` | User-reported prerequisite check | Completed | GNOME Wayland session; extension is enabled and ACTIVE; DBus health is healthy and advertises `shell_raster_content_visibility` with raster code/actors enabled. | User-approved live focus/monitor acceptance matrix |
| 4 | `step04-live-focus-suppression-2026-08-28` | User-reported live acceptance | Failed | With “Keep overlay visible when Elite Dangerous is not the foreground window” unchecked, the overlay remained visible after focus loss. Source diagnosis confirms the generic `prepared_surface_allows_unfocused_content` escape hatch bypasses the new suppression intent. | Narrow policy remediation; do not alter helper deployment or actor-continuity behavior. |
| 4 | `step04-focus-policy-remediation-2026-08-28` | Main-thread code assist | Superseded | The first diagnosis targeted the managed-surface escape hatch. Subsequent live logs proved that route inactive (`surface_preparation=none`), so the policy change was reverted and no behavior from that attempt remains. | Use the retained-content boundary remediation instead. |
| 4 | `step04-retained-content-boundary-remediation-2026-08-28` | Main-thread code assist | Completed | Live client log proved the previous hypothesis inactive and was restored. Added a GNOME-owned retained-content fact for applied/matching/helper-supported Shell-raster frames, passed it through neutral runtime/consumer/policy paths, and proved generic Qt does not map. Focused suite: 274 passed; external `make check` and `make test`: 1,696 passed each. | User restarts overlay client; no helper update/reload; repeat live acceptance. |
| 4 | `step04-retained-actor-remap-warmup-remediation-2026-08-28` | Main-thread code assist | Completed | A second live-log diagnosis showed the deliberately unmapped Qt surface triggered `target_focused_remap_warmup`, intermittently suppressing focused content. A neutral retained actor is now treated as visible for policy warm-up; the helper and actor lifecycle are unchanged. Focused suite: 275 passed; external `make check` and `make test`: 1,697 passed each. | User restarts EDMC; no helper update/reload; repeat live acceptance. |
| 4 | `step04-live-acceptance-after-remap-warmup-remediation-2026-08-28` | User-reported live acceptance | Completed | User verified all matrix cases: focused visibility without flashing; checkbox-off debounce then content suppression without black screen; focus return without flash; checkbox-on continuity; repeated focus cycles; and two-monitor fullscreen placement. | Await explicit commit approval. |

## Reconciliation Checklist

- [x] Historical unsafe plan and user-verified rollback reconciled.
- [x] Replacement research, design, plan, status dashboard, and orchestration prompt created.
- [x] Step 1 task breakdown independently reviewed and implemented.
- [x] Step 2 task breakdown independently reviewed and implemented.
- [x] Step 3 task breakdown implemented in isolated contexts.
- [x] Step 3 main-context review complete.
- [x] Automated validation complete.
- [x] User-approved live GNOME Wayland acceptance complete.
- [ ] User explicitly approves any commit.
