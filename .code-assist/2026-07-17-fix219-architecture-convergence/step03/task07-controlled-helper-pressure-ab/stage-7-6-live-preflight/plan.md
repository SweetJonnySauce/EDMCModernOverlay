# Stage 7.6 Live Preflight Plan

## Phase tracking

| Stage | Description | Status |
| --- | --- | --- |
| 7.6.1 | Verify handoff, authorities, worktree, evidence hold, and prohibited artifacts | Completed |
| 7.6.2 | Freeze operational criteria, privacy rules, operator actions, and emergency stops | In progress |
| 7.6.3 | Verify OS/session/Shell and monitor-A 100% display state | Pending |
| 7.6.4 | Verify Firefox absence, fixed workload, diagnostics-off state, and quiet host | Pending |
| 7.6.5 | Verify A2/B2 proof-method readiness and continuous operator stop path | Pending |
| 7.6.6 | Record pass/pending decision, synchronize Task 07 records, and run patch hygiene | Pending |

Stage 7.6 status: **In progress; no live host check started**.

## Test type selection

- Selected type: **operational validation**.
- Unit tests are not selected because no pure/runtime behavior change is authorized.
- Harness tests are not selected because no `load.py`, EDMC hook, lifecycle, socket, or Tk wiring
  change is authorized.
- No production or test file may be changed. A demonstrated code defect stops the preflight and
  is reported for separate remediation authorization.
- The current R6 automated evidence remains the prerequisite gate; Stage 7.6 adds only fresh live
  environment evidence.

## Expected unchanged state

- All cumulative R1-R6 source, test, CI, compliance, and Task 07 record changes remain intact.
- Historical 12+2 captures and their manifests remain byte-for-byte untouched.
- Capture diagnostics stay off; ordinary overlay functionality stays enabled.
- No capture runner, warm-up, observation, output JSON, report, bound, threshold, manifest,
  baseline identity, production-routing change, commit, or push occurs.

## Proposed fixed workload decision

The recommended workload is **repeated unchanged representative payload activity**, because Task
07 must exercise both stable helper-query and unchanged-repaint pressure:

- Use only `tests/archive/display_all.json` at its committed hash.
- Use its existing payload order, TTL values, and zero delay between entries.
- Replay one complete fixture sweep every 10 seconds so the 10-second TTL population is refreshed
  deterministically rather than allowed to expire into an idle-only run.
- Start the generator before a future Stage 7.7 cell and keep the same cadence through that cell's
  warm-up and observations; stop it between cells while cell state changes are made.
- Stage 7.6 may perform at most one explicitly approved bounded non-capture replay to prove the
  mechanism and visible stability. It must not start the periodic loop.

Tradeoff: this provides direct unchanged-repaint pressure but adds a deterministic payload burst.
The alternative is idle-after-one-replay, which isolates helper-query cost better but weakens the
unchanged-repaint portion of the approved integrated A/B. The selected cadence requires user
approval before live inspection.

## Proposed quiet-host criterion

Use a 30-second read-only preflight window divided into six five-second checks. Pass only when:

1. Firefox is absent for the full window.
2. No unrelated application has sustained CPU at or above 10 percent of one logical CPU in two
   consecutive checks.
3. GNOME Shell stays below 20 percent CPU in every check, has no rising three-check trend, and
   produces no normalized Mutter assertion during the window.
4. No package update, build/test job, browser, video encode/playback, file indexing burst, or
   other known high-load activity is active.
5. System load is stable rather than rising across the window.

Only normalized pass/fail facts and bounded CPU/load summaries may enter documentation. This is a
preflight repeatability gate, not an acceptance bound. The capture runner's separate 80-percent
three-sample emergency stop remains unchanged.

## Preflight checks and expected results

| ID | Input | Required output |
| --- | --- | --- |
| P1 | OS, session, desktop, Shell version | Ubuntu 24.04.4, native Wayland GNOME, GNOME Shell/Mutter 46.x |
| P2 | Display configuration | Two horizontal 3440x1440 displays at uniform 100%; monitor A left of primary monitor B; fixed refresh recorded |
| P3 | Elite presentation state | Elite is stable, windowed, and on monitor A; no title, handle, or raw geometry token is recorded |
| P4 | Fixture | Exact repository path/hash and approved replay cadence are fixed |
| P5 | Client configuration | `dev_mode=false`, payload logging/debug overlay off, repaint detail/tracing/outlines/markers off; repaint debounce remains on |
| P6 | Helper configuration/health | Enabled `full_helper`, diagnostics off, version 1.0.0/protocol 3, healthy fixed capability fields |
| P7 | Firefox and quiet load | Firefox absent and the approved 30-second criterion passes |
| P8 | A2 proof readiness | Planned disabled-helper state yields authoritative client-runtime native-GNOME fallback with `missing_helper` and missing service |
| P9 | B2 proof readiness | Planned enabled-helper state yields authoritative compositor-helper/GNOME selection with one available approved versioned helper and no fallback |
| P10 | Operator safety | Operator confirms continuous observation and immediate Ctrl-C for every visible or machine safety condition |

P8/P9 freeze and verify the proof mechanism without beginning a cell. Helper toggles or reloads
require a separate explicit confirmation for that exact action.

## Read-only check sequence

Each step is presented separately in interactive mode:

1. Inspect normalized OS/session/Shell/display facts.
2. Inspect normalized process presence and the proposed quiet-load window.
3. Inspect allowlisted client and helper diagnostic settings.
4. Inspect helper health and extension enabled state without reloading it.
5. Verify the fixed fixture and stable Elite workload state.
6. Verify that the existing bounded status surfaces can prove the exact future A2/B2 routes,
   without invoking the capture runner.
7. Ask the operator to confirm the visible-stop duty and Ctrl-C path.

Any necessary launch, stop, settings edit, helper toggle, or reload is an operator action. Present
one action, explain its effect and rollback, and wait for explicit confirmation before performing
or verifying it.

## Privacy and evidence rules

- Do not persist PIDs, command lines, window titles, target handles, monitor serials, usernames,
  personal paths, raw D-Bus payloads, or raw journal text.
- Host commands must reduce output to allowlisted state, bounded counts, and normalized reasons
  before anything is recorded.
- Never write host output to the performance evidence directory in Stage 7.6.
- A failed or ambiguous check leaves the stage pending. It is not converted into favorable
  evidence or bypassed by a shortened run.

## Emergency and immediate-stop rules

Stop the preflight immediately and leave Stage 7.6 pending for:

- visible flashing or a black/intermediate overlay surface;
- input loss, focus/click-through failure, or drag-feedback corruption;
- repeated Mutter assertions or any privacy-unsafe diagnostic output;
- rapidly rising Shell CPU, including the fixed future-run 80-percent/three-second machine rule;
- a required process/helper/client restart, counter-origin ambiguity, continuity loss, or state
  that cannot be proved from an authoritative source;
- any attempt to enter runner warm-up or observation.

The operator's emergency action is immediate Ctrl-C for an active bounded probe, followed by no
automatic retry until the cause is reviewed.

## Completion rules

- **Pass:** every P1-P10 condition is proven with sanitized current evidence. Mark Stage 7.6
  complete in the parent Task 07 plan/progress and iteration checklist, then stop before 7.7.
- **Pending:** any condition fails, is ambiguous, or requires an unapproved state change. Record
  the sanitized blocker and one-at-a-time recovery action; do not weaken the gate.
- Run `git diff --check` after documentation updates.
- Do not stage, commit, or push.

