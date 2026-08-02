# Iteration Checklist: 2026-07-21 Step 3 Amendment

## Outcome

Current status: **Post-Task-06 iteration passed — Stage 1.8 is complete; Stage 1.9 is ready but
not started**

Prior synchronization status: **Synchronization reviewed and approved — Stage 1.6 required
separate authorization**

The amendment is correctly scoped inside the existing fix219 PDD. Requirements, research,
design boundaries, test selection, safety rules, and evidence-preservation decisions are
sufficient. No new PDD, product-requirements round, or external research pass is required.

The Task 06 implementation and review are complete. The controlled Task 07 A/B, later manual
gates, new baseline, and production routing remain unauthorized and not started.

## Phase tracking

| Stage | Description | Status |
| --- | --- | --- |
| 8.1 | Verify amendment requirements and focused research | Completed |
| 8.2 | Audit detailed-design contracts and architecture boundaries | Completed |
| 8.3 | Audit Step 3 sequencing, test selection, and manual gates | Completed |
| 8.4 | Verify current evidence, configuration, and cross-artifact alignment | Completed |
| 8.5 | Record readiness decision and required iteration | Completed |
| 8.6 | Synchronize threshold terms, working plan/progress, and evidence README | Completed |
| 8.7 | Review synchronization decisions with the user one at a time | Completed |

Phase 8 status: **Completed**

## Requirements and research

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| R1 | Is the amendment an explicit user-approved requirement? | Yes | Question 35 records pressure reduction, A/B validation, historical-capture preservation, and the clean 0/42 restart. |
| R2 | Is the incident attribution appropriately bounded? | Yes | The helper is documented only as a plausible load amplifier; the overlay is not claimed as the Firefox/Mutter failure's root cause. |
| R3 | Are the observed query/repaint facts separated from acceptance thresholds? | Yes | The incident sample is labeled diagnostic evidence, not a baseline or threshold source. |
| R4 | Is the stable-query mechanism grounded in an existing code seam? | Yes | Research identifies the existing 1.5-second suppression, cached state, transition-guard interaction, 500 ms follow cadence, and synchronous Shell-main-thread target query. |
| R5 | Does repaint research avoid assuming dedupe is absent? | Yes | Existing payload visual snapshots are acknowledged; request, Qt paint, and Shell raster work remain separate measurements. |
| R6 | Are privacy and safety limits explicit? | Yes | Broad logs, titles, handles, command lines, paths, and failure reproduction are excluded; instability stops measurement. |
| R7 | Is more requirements clarification or external research needed before implementation planning? | No | Current requirements and repository evidence are sufficient. The remaining unknowns are intentionally resolved by RED tests and controlled A/B measurements. |

## Detailed design

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| D1 | Is stable-target pressure reduction backend-owned? | Yes | Generic code may request refresh but cannot inspect GNOME helper/presenter enums or own cache policy. |
| D2 | Is the cache deterministic and testable? | Yes | It requires explicit state, an injected monotonic clock, and a bounded deadline. |
| D3 | Are immediate invalidation and recovery cases preserved? | Yes | Refresh, failures, target loss/recovery, mode/presenter changes, raster staleness, focus, monitor, geometry, workspace, minimize/fullscreen, and exposure recovery are named. |
| D4 | Is the cold-start deferred-remap contract preserved? | Yes | Its backend-neutral forced refresh bypasses cache exactly once, then returns to steady no-op behavior. |
| D5 | Does repaint suppression preserve necessary redraws and safe fallbacks? | Yes | Visual, expiry, animation, scale, transition, visibility/recovery, and explicit-refresh triggers remain; unknown payloads retain a safe repaint path. |
| D6 | Are diagnostics low-overhead and privacy-safe? | Yes | Quiet runs use bounded aggregate counters, state changes, and normalized failures rather than per-cycle journal events. |
| D7 | Does the A/B isolate extension-idle cost from client-driven helper-loop cost? | Yes | A1/A2/B1/B2 independently vary client and extension state with fixed environment and repeated samples. |
| D8 | Are the two kinds of numeric thresholds named unambiguously? | Yes | A/B-derived **pressure-reduction acceptance bounds** remain in its report; versioned **migration-regression thresholds** come only from the completed clean 42-capture baseline. |

## Implementation and test plan

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| P1 | Is Step 3 staged incrementally with no new project or orphaned code? | Yes | Stages 1.6–1.11 progress from quiet configuration through query/repaint work, A/B, manual validation, and clean baseline. |
| P2 | Is test type selected explicitly? | Yes | Pure/runtime cache and fingerprint logic use unit tests; a harness test becomes mandatory only if `load.py`, EDMC hooks, lifecycle, or Tk wiring changes. Real GNOME validation remains mandatory. |
| P3 | Do all named focused test files currently exist? | Yes | All seven named unit/collector test paths are present. |
| P4 | Are critical behavior and recovery tests named? | Yes | Deadline, guard, forced refresh, error/recovery, invalidation, repaint triggers, and post-remap exactly-once behavior are included. |
| P5 | Are manual behavior and compositor gates complete? | Yes | Two terminal-focused starts, one game-focused start, transitions, both monitors, Alt-Tab, Overview, and quiet soak are required. |
| P6 | Is the `.code-assist` Step 03 working plan synchronized with the amendment? | Yes | Stages 3.9–3.16 now cover the historical pause, quiet state, query/repaint work, A/B, manual gate, clean baseline, and completion; tests, commands, stop conditions, and rollback are explicit. |
| P7 | Is the Step 03 progress record synchronized? | Yes | The live checklist now reports 12/42 paused, and a dated appended section records the incident, threshold vocabulary, next-stage mapping, and capture hold without deleting history. |
| P8 | Are implementation success criteria fully numeric already? | No | Correctly deferred. The A/B establishes pressure bounds; the coherent baseline later establishes migration thresholds. Do not invent either in advance. |

## Evidence and operational state

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| E1 | Does the active manifest validate? | Yes | `fix219_gnome46_pre_migration_reduced_v2` validates with 14 scenarios and three repetitions. |
| E2 | Are exactly 12 active captures present and valid? | Yes | The capture validator accepts 12 repetitions across the four completed 100% monitor-A scenarios. |
| E3 | Are the superseded full-oracle captures preserved separately? | Yes | Two captures plus their original manifest remain under `superseded/full-matrix-v1/`. |
| E4 | Is a premature threshold artifact absent? | Yes | `thresholds.json` does not exist. |
| E5 | Has a post-optimization manifest been created prematurely? | No | Correctly deferred until pressure reduction, A/B, and manual regression gates pass. |
| E6 | Does the evidence README reflect the amendment? | Yes | A prominent capture hold preserves the 12 captures, prohibits resumption/monitor B, and labels diagnostics-enabled preflight/capture instructions as frozen history rather than the next-run path. |
| E7 | Is the current local configuration already quiet? | No | `overlay_settings.json` still has `dev_mode=true`; repaint logging/outlines remain in capture configuration. Stage 1.6 must restore the documented quiet values before ordinary use or measurement. |
| E8 | Has the user-local GNOME helper diagnostic configuration been checked and backed up in this iteration? | No | Intentionally not changed during PDD work. Stage 1.6 must read, back up, and disable diagnostics without discarding other fields. |

## Consistency and risk review

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| C1 | Does the amendment preserve the fix219 backend boundary? | Yes | Compositor-specific presentation, input, cache, and helper behavior remain under backend-owned interfaces. |
| C2 | Does it preserve Phase 19 and cold-start behavior? | Yes | Transition grace, atomic handoff, visibility/exposure, focus, click-through, and one-shot remap refresh are explicit invariants. |
| C3 | Does it prevent mixed evidence populations? | Yes | The 12 captures cannot be relabeled or included in post-optimization threshold calculations. |
| C4 | Does it retain a safe recovery/rollback posture? | Yes | Changes are staged behind unit-testable seams; measurement stops on Shell instability; no later production routing is authorized. |
| C5 | Is Step 5 still gated by Step 3? | Yes | The authoritative plan keeps production routing blocked until the clean baseline and thresholds complete. |
| C6 | Is there an unresolved product-scope or architecture decision? | No | Remaining work is plan synchronization and empirical implementation evidence, not product design. |

## Completed synchronization iteration

Completed without changing runtime code, settings, helper configuration, or evidence captures:

1. Clarified threshold vocabulary in the research, detailed design, and Step 3 plan.
2. Updated `.code-assist/2026-07-17-fix219-architecture-convergence/step03/plan.md` with the
   pressure-reduction stages, explicit test selection, validation commands, manual gates, and
   rollback/stop conditions.
3. Appended the incident, 12/42 pause, and new stage mapping to the Step 03 progress record without
   rewriting prior evidence.
4. Updated the performance evidence README to preserve the 12 captures as historical, prohibit
   capture resumption, and remove diagnostics-enabled instructions from the next-run path.
5. Confirmed Stage 1.6 remains not started. It may begin only after user review and must read and
   back up the user-local helper configuration before changing it.

## Readiness decision

- Return to requirements clarification: **No**.
- Conduct more prerequisite research: **No**.
- Reopen the architecture design: **No**.
- Perform one focused planning/evidence synchronization iteration: **Yes — completed**.
- Begin runtime implementation immediately: **No — review is approved, but Stage 1.6 still requires separate authorization**.

The synchronization has passed patch/document hygiene and user review. The amendment is ready to
enter `code-assist` only after the user separately authorizes Stage 1.6.

## User review decisions — 2026-07-21

| Decision | Result |
| --- | --- |
| Separate pressure-reduction bounds from migration-regression thresholds | Approved |
| Stage 3.9–3.16 working sequence | Approved |
| Tiered testing without silent acceptance waivers | Approved |
| Chronological progress plus explicit current-state supersession | Approved |
| Historical 12-capture hold and new-identity 0/42 policy | Approved |
| Synchronization as a whole | Approved |

This approval closes the PDD synchronization review. Stage 1.6/working Stage 3.10 remains not
started and requires a separate explicit instruction.

## Post-Task-04 iteration — 2026-07-21

### Outcome

Task 04 satisfied authoritative Stage 1.6 / working Stage 3.10 without changing runtime code or
weakening the capture hold. The client and helper configuration is quiet and reversible, the
effective helper remains healthy in full-helper mode, a bounded real-query probe produced no
high-frequency diagnostic stream, and all historical captures retained their pre-mutation
hashes. No focused remediation iteration is required before Task 05.

### Phase tracking

| Stage | Description | Status |
| --- | --- | --- |
| 9.1 | Verify Task 04 authorization, scope, and test-type selection | Completed |
| 9.2 | Audit reversible client/helper configuration changes | Completed |
| 9.3 | Audit helper reload, health, and quiet-observation evidence | Completed |
| 9.4 | Audit historical evidence and cross-artifact synchronization | Completed |
| 9.5 | Record the readiness decision for Stage 1.7 | Completed |

Phase 9 status: **Completed**

### Authorization and scope

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| A1 | Did the user explicitly authorize Task 04 / Stage 1.6? | Yes | The instruction to use Code Assist to execute Task 04 supplied the separate authorization required by the amendment review. |
| A2 | Did execution remain inside the Task 04 boundary? | Yes | It changed diagnostic configuration and documentation only; no runtime, test, selector, launcher, hook, lifecycle, Tk, capture, or routing implementation changed. |
| A3 | Was the required test type selected before mutation? | Yes | Operational configuration/evidence validation was selected. Unit and harness tests were correctly not selected because no behavior or lifecycle code changed. |
| A4 | Was Task 05 or Stage 1.7 started implicitly? | No | Stable-query implementation remains unstarted and requires its own execution instruction. |

### Configuration and recoverability

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| C1 | Is the client shadow in quiet normal-use state? | Yes | `dev_mode=false`; payload logging and the debug overlay are disabled. No persisted EDMC development-mode override exists to replace the shadow value at the next launch. |
| C2 | Are developer repaint/visual diagnostics quiet without disabling behavior? | Yes | Repaint-detail logging, tracing, outlines, and markers are disabled while repaint debounce remains enabled. |
| C3 | Was the helper configuration backed up before editing? | Yes | A non-overwriting pre-Stage-3.10 backup exists beside the user-local helper configuration. |
| C4 | Were unrelated helper fields preserved? | Yes | Normalized JSON comparison after removing `diagnostics` is identical. `enabled=true` and `mode=full_helper` remain unchanged. |
| C5 | Is the helper quiet without being functionally disabled? | Yes | After reload, health reports full-helper target/presentation capabilities and `diagnostics_enabled=false`. `dev_mode_enabled=true` reflects the still-enabled explicit full-helper configuration; it does not mean diagnostic logging remains enabled. |
| C6 | Is rollback explicit and bounded? | Yes | Restore the backed-up helper JSON and reload the extension; client-side values can be returned independently. No code rollback is involved. |

### Validation and evidence

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| V1 | Did the effective helper reload successfully? | Yes | `GetHealth` returned healthy helper version 1.0.0/protocol 3 with diagnostics disabled after the supported disable/enable lifecycle. |
| V2 | Was per-query diagnostic silence exercised rather than inferred only from JSON? | Yes | A host-session probe made 20 real `GetTargetState` calls over 10 seconds with zero call failures and zero filtered `target_query_started` events. |
| V3 | Are client repaint-detail diagnostics disabled? | Yes | The controlling client setting is false; the same bounded interval contained zero repaint-request/detail events. No EDMC/client process was active, so this is a configuration gate rather than a claim about Task 06 repaint behavior. |
| V4 | Were sandbox failures distinguished from acceptance evidence? | Yes | The restricted-session reload and probe failures were recorded and discarded; only the successful approved host-session reruns support acceptance. |
| V5 | Did patch hygiene pass? | Yes | `git diff --check` passed after synchronization. |
| V6 | Were automated tests required? | No | No runtime code, pure service, `load.py`, hook, lifecycle, or Tk wiring changed. The residual runtime behaviors are covered by the mandatory tests and live gates in Tasks 05–09. |

### Historical-evidence and plan consistency

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| E1 | Are all historical captures intact? | Yes | Pre/post SHA-256 verification passed for all 12 reduced-v2 and two superseded full-v1 captures. |
| E2 | Is the old matrix still paused? | Yes | No capture was added, replaced, moved, relabeled, or resumed; monitor B remains on hold. |
| E3 | Was a clean evidence identity or threshold artifact created early? | No | Correctly absent. No post-optimization identity, summary, or `thresholds.json` exists. |
| E4 | Do authoritative and working status records agree? | Yes | Implementation Stage 1.6, working Stage 3.10, and the performance README all report Completed; Stage 1.7/3.11 remains Not started. |
| E5 | Were historical progress statements preserved? | Yes | Earlier pending-authorization entries remain chronological history and are explicitly superseded by the appended authorization/completion record. |

### Readiness decision

- Return to requirements clarification: **No**.
- Conduct additional prerequisite research: **No**.
- Reopen or amend the detailed design: **No**.
- Perform Task 04 remediation: **No**.
- Resume the historical capture matrix: **No**.
- Create the post-optimization evidence identity: **No**.
- Proceed next to Task 05 / authoritative Stage 1.7: **Ready, but not started**.

Task 05 must follow its focused RED/GREEN contract for stable cycles, deadline expiry,
transition-guard interaction, immediate invalidation/recovery, explicit refresh, and the
cold-start post-remap exactly-once refresh. The capture hold remains active throughout it.

## Post-Task-05 iteration — 2026-07-21

### Outcome

Task 05 satisfied authoritative Stage 1.7 / working Stage 3.11 with a backend-owned correction
to the existing bounded target-query cache. Focused RED/GREEN evidence proves the transition
guard no longer forces stable mapped-suppressed queries at the generic follow cadence, while
deadline expiry, explicit refresh, failures, transitions, stale raster work, exposure recovery,
and full target/presentation identity remain protected. No remediation or design amendment is
required before Task 06.

### Phase tracking

| Stage | Description | Status |
| --- | --- | --- |
| 10.1 | Verify Task 05 authorization, scope, and unit-test selection | Completed |
| 10.2 | Audit RED coverage and expected failure evidence | Completed |
| 10.3 | Audit cache correction, invalidation paths, and backend boundary | Completed |
| 10.4 | Audit GREEN/static evidence and cross-artifact synchronization | Completed |
| 10.5 | Record readiness decision for Stage 1.8 | Completed |

Phase 10 status: **Completed**

### Authorization, design, and architecture

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| A1 | Did the user explicitly authorize Task 05 / Stage 1.7? | Yes | The instruction explicitly requested Code Assist implementation of Task 05 using the approved detailed design. |
| A2 | Did implementation stay within Task 05? | Yes | Runtime changes are limited to the GNOME cache predicate, cache invalidation, and private presentation signature; Task 06 repaint logic, A/B, manual gates, captures, and production routing were not started. |
| A3 | Was the required test type selected before code changes? | Yes | Unit tests were selected because clock/helper/target dependencies are injected. No `load.py`, EDMC hook, lifecycle, or Tk surface changed, so a harness test was not required. |
| A4 | Is the fix219 backend boundary preserved? | Yes | Generic follow and consumer interfaces are unchanged; no compositor-private import or enum dispatch was added outside the backend bundle. |

### Behavior and recovery contracts

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| B1 | Do guarded stable cycles avoid synchronous target queries inside the deadline? | Yes | The new guarded steady-state test observes target-query cache hits with no added presentation call. |
| B2 | Does deadline expiry perform one refresh and rearm suppression? | Yes | The injected monotonic test observes one target query at the exact deadline, a matching presentation reuse, then another target-query cache hit. |
| B3 | Does explicit refresh remain a one-shot bypass? | Yes | The guarded forced-refresh test performs one target and presentation call, then immediately returns to cached steady state; existing follow tests retain the deferred-remap `[False, True, False]` contract. |
| B4 | Are failure, transition, stale-raster, exposure, and recovery paths protected? | Yes | Unhealthy/non-matching paths clear matching state; held transitions and clear failure invalidate the deadline; pending preparation/commit, due raster lease, and confirmed surface recovery bypass cache use; target loss rearms recovery immediately. |
| B5 | Do named target changes invalidate presentation reuse after refresh? | Yes | Signature tests now cover token, frame/buffer/content/monitor geometry, monitor index/output/scale, workspace/showing, focus, minimize, fullscreen, visibility action, renderer/preparation, and raster-frame state. |
| B6 | Were Phase 19 and cold-start contracts changed? | No | Correctly unchanged. Existing transition, surface, focus, click-through, and post-remap exactly-once tests remain GREEN. |

### Validation and project state

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| V1 | Was focused RED captured before runtime edits? | Yes | 9 expected failures and 102 passes are recorded in the Task 05 RED log. |
| V2 | Did the mandated focused GREEN command pass? | Yes | 111 tests passed. |
| V3 | Did the generic consumer boundary pass? | Yes | `test_backend_consumers.py` passed 35 tests. |
| V4 | Did targeted static/build and patch hygiene pass? | Yes | Ruff, compileall, and `git diff --check` passed. |
| V5 | Were full project gates required at this stage? | No | The approved plan defers `make check` / `make test` to the integrated query-plus-repaint milestone after Task 06. This is a scheduled gate, not a waiver. |
| V6 | Were historical evidence and threshold state preserved? | Yes | No capture, evidence identity, summary, or `thresholds.json` was created or changed; the 12/42 hold remains active. |
| V7 | Was an increment commit or push created? | No | Correctly deferred to approved Stage 3.16; the dirty tree was not bulk-staged or reset. |

### Readiness decision

- Return to requirements clarification: **No**.
- Conduct additional prerequisite research: **No**.
- Reopen or amend the detailed design: **No**.
- Perform Task 05 remediation: **No**.
- Start Task 07 A/B, manual validation, or capture work: **No**.
- Proceed next to Task 06 / authoritative Stage 1.8: **Ready, but not started**.

Task 06 must attribute the remaining repaint requests and add pure RED/GREEN coverage before
suppressing only proven unchanged rendered work. The capture hold remains active.

## Post-Task-06 iteration — 2026-07-21

### Outcome

Task 06 satisfied authoritative Stage 1.8 / working Stage 3.12 by extending the existing pure
visual-fingerprint seam, adding fixed bounded attribution, and reusing only proven-equal
successful Shell-frame preparation. No design amendment or remediation is required before the
controlled Task 07 A/B. The historical capture hold remains active.

### Phase tracking

| Stage | Description | Status |
| --- | --- | --- |
| 11.1 | Verify Task 06 authorization, scope, and unit-test selection | Completed |
| 11.2 | Audit attribution and focused RED evidence | Completed |
| 11.3 | Audit fingerprint, scheduling, frame-reuse, fallback, and backend-boundary behavior | Completed |
| 11.4 | Audit focused/integrated/project validation and artifact synchronization | Completed |
| 11.5 | Record readiness decision for Stage 1.9 | Completed |

Phase 11 status: **Completed**

### Authorization, design, and architecture

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| A1 | Did the user explicitly authorize Task 06 / Stage 1.8? | Yes | The instruction explicitly requested Code Assist implementation of Task 06 using the approved design decisions. |
| A2 | Did implementation stay within Task 06? | Yes | Changes are limited to payload visual equivalence, bounded repaint/work attribution, generic presentation-refresh signaling, deterministic render identity, Shell-frame preparation reuse, unit tests, and synchronized records. Tasks 07–09 and production routing were not started. |
| A3 | Was the required test type selected before code changes? | Yes | Unit tests were selected for pure/injectable seams. No `load.py`, EDMC hook/lifecycle, or Tk wiring changed, so no harness test was required. |
| A4 | Is the fix219 backend boundary preserved? | Yes | Generic code still supplies only a backend-neutral raster provider and refresh flag; it imports no compositor-private presentation implementation or enum and performs no compositor dispatch. |

### Behavior, fallback, and pressure contracts

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| B1 | Are request, Qt paint, frame preparation, raster, and presentation layers distinguished? | Yes | Historical counts were separated and fixed-cardinality saturating counters now attribute ingest, scheduling/update, paint, and frame outcomes without per-cycle logs. |
| B2 | Do TTL/metadata-only supported refreshes avoid rendered work? | Yes | Matching supported fingerprints refresh expiry/lifecycle metadata without dirtying render identity, scheduling Qt update, or forcing backend refresh. |
| B3 | Are visual/group/override/animation changes preserved? | Yes | Tests cover message/rect/vector content, style, geometry and transform fields, plugin/group changes, override generations, and animation bypass. |
| B4 | Is unknown or incomplete state safe? | Yes | Unknown/malformed fingerprints repaint, stale snapshots are cleared on unsupported replacement, incomplete target/request identity is uncacheable, and failed frame results are never reused. |
| B5 | Are scale/mode/monitor/visibility/recovery/explicit-refresh paths preserved? | Yes | Frame identity covers renderer state, full target/request geometry, monitor/output/scale/workspace/focus/showing/minimize/fullscreen, and diagnostics state. Existing backend lease, recovery, transition, and one-shot refresh tests remain green. |
| B6 | Are detailed diagnostics still gated and bounded? | Yes | Release reuse adds no detailed diagnostics; counters have fixed keys and saturate at a fixed maximum; no per-cycle journal stream was added. |

### Validation and project state

| ID | Check | Yes/No | Evidence and action |
| --- | --- | --- | --- |
| V1 | Was focused RED captured before implementation? | Yes | 11 expected failures and 59 passes are recorded in the Task 06 RED log. |
| V2 | Did focused and integrated GREEN pass? | Yes | Focused passed 70; integrated query/repaint/follow passed 151; backend consumers passed 35. |
| V3 | Did static/build and full milestone gates pass? | Yes | Targeted Ruff/compileall passed. Final `make check` and `make test` each passed 1,379 tests with 21 existing skips; repository Ruff and mypy passed through `make check`. |
| V4 | Were environment-only failed attempts documented? | Yes | Unactivated system Python lacked Ruff/PyQt; the prepared environment then exposed and cleared one stale authoritative-plan environment reference before final green gates. |
| V5 | Were historical evidence and thresholds preserved? | Yes | No capture, manifest/evidence identity, summary, or `thresholds.json` changed; 12 reduced-v2 and two superseded captures remain immutable history. |
| V6 | Was an increment commit or push created? | No | Correctly deferred to approved Stage 3.16; the dirty tree was not bulk-staged or reset. |

### Readiness decision

- Return to requirements clarification: **No**.
- Conduct new prerequisite research: **No**.
- Reopen or amend the detailed design: **No**.
- Perform Task 06 remediation: **No**.
- Start manual regression, capture work, or production routing: **No**.
- Proceed next to Task 07 / authoritative Stage 1.9: **Ready, but not started**.

Task 07 must run the approved quiet controlled A1/A2/B1/B2 experiment and derive reviewed
pressure-reduction acceptance bounds. This review does not authorize it. The capture hold remains
active.

## Task-07 live-preflight iteration — 2026-07-21

### Phase tracking

| Stage | Description | Status |
| --- | --- | --- |
| 7.1 | Verify authority, worktree, capture hold, and host state | Completed |
| 7.2 | Add strict snapshot/evidence unit and harness contracts | Completed |
| 7.3 | Add diagnostics-off bounded plugin/client/helper snapshots | Completed |
| 7.4 | Add the fixed controlled cell runner | Completed |
| 7.5 | Pass focused, integrated, harness, and project validation | Completed |
| 7.6 | Establish fixed quiet live workload | Blocked before first cell |
| 7.7 | Capture A1/A2/B1/B2 repetitions | Not started |
| 7.8 | Review bounds and publish the A/B report | Not started |

Phase status: **In progress**.

### Outcome and readiness

- The existing connection now provides an on-demand strict cumulative work snapshot. It exposes
  only fixed saturating query, presentation, ingest, repaint, Qt-paint, and frame counters.
- Helper health adds fixed saturating target/presentation call counters and bounded actor counts;
  it does not enable per-call logs or capture diagnostics.
- Unit tests were selected for pure snapshot/delta/aggregation and runner helpers. Harness tests
  were selected and passed because `load.py` request coordination changed.
- Focused Task 07 tests passed 66; the integrated pressure/query/repaint slice passed 217;
  `make check` and `make test` each passed 1,402 with 21 expected headless skips. Ruff, mypy,
  compileall, and patch hygiene passed.
- Live preflight correctly refused to start: Firefox remains active, Elite gameplay/EDMC/client
  are absent, and the host is not quiet. No helper reload, warm-up, sample, report, pressure
  bound, `thresholds.json`, evidence identity, matrix capture, commit, or push occurred.

Stage 1.9 / 3.13 is **in progress but incomplete**. Resume only after the user establishes the
approved stable windowed monitor-A/100% workload with Firefox stopped.
