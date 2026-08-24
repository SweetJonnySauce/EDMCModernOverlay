# Stage 7.6 Live Preflight Context

## Summary

Stage 7.6 is the fresh live-host gate for Task 07. It may establish and verify the fixed quiet
workload, but it may not start a five-minute warm-up, a 60-second observation, or any A1/A2/B1/B2
cell. Stage 7.7, report generation, pressure bounds, migration thresholds, the clean baseline,
commit, and push remain outside this authorization.

## Parameters and authority

- Mode: interactive.
- Repository root: `/home/jon/.local/share/EDMarketConnector/plugins/EDMCModernOverlay`.
- Parent Task 07 records: `.code-assist/2026-07-17-fix219-architecture-convergence/step03/task07-controlled-helper-pressure-ab/`.
- Handoff: `/home/jon/Downloads/handoff-20260802-093056.md`.
- Controlling sources: repository `AGENTS.md`, the Task 07 code task, approved detailed design,
  Task 07 plan/progress/context/assessment addendum, compliance tracker, and iteration checklist.
- `CODEASSIST.md` is absent. Repository instructions and the named Task 07 authorities control.

## Verified repository state before host work

- Branch: `backend-refactor-implementation`.
- HEAD: `14576dd79fdbcbd97b85efb87cc9c087af490d55`.
- The cumulative R1-R6 worktree is intentionally dirty and matches the handoff plus the later
  iteration-checklist update. It must not be reset, discarded, staged, committed, or pushed.
- `git diff --check` passes.
- Historical evidence remains 12 reduced-v2 repetitions plus two superseded full-v1 repetitions;
  no evidence file is modified in the current worktree.
- `pressure-ab-report.md` and `thresholds.json` are absent. No clean-baseline identity exists.
- Automated remediation Stages 7.R1-7.R6 and their unit, harness, integrated, project,
  GUI-enabled, static, boundary, and EDMC compliance gates are complete.

## Fixed repository inputs

- Representative fixture: `tests/archive/display_all.json`.
- Committed fixture SHA-256:
  `3766f57248d032c8a01844de0994fe31f0211211a3292660a442aa9d68b923f9`.
- Source revision for the prospective A/B: current HEAD above, subject to re-verification before
  Stage 7.7.
- Plugin/client source version: `1.0.0`.
- Expected helper contract: version `1.0.0`, protocol `3`; live health must verify this rather
  than inherit it from historical evidence.
- Fixed presentation workload: stable windowed Elite on monitor A at uniform 100% scale.
- Capture runner constants: 300-second warm-up, three 60-second observations, Shell CPU emergency
  bound at 80 percent for three consecutive one-second observations, and stop after two Mutter
  assertions. The capture runner must not be invoked in Stage 7.6.

## Operational dependency map

```text
repository inputs and immutable guards
  -> read-only OS/session/Shell/display verification
  -> read-only process and quiet-load verification
  -> read-only client/helper diagnostic-state verification
  -> stable Elite/fixture/workload verification
  -> A2/B2 proof-method readiness and operator stop readiness
  -> Stage 7.6 pass or pending decision
```

No preflight result is an A/B sample. Host checks may report only fixed allowlisted facts; project
records must not contain PIDs, process command lines, window titles, target handles, monitor
serials, usernames, personal paths, raw journal text, or broad environment dumps.

## Decisions requiring interactive approval

The approved sources require a fixed payload workload and a predeclared quiet-host criterion but
do not freeze their exact cadence or numeric preflight bounds. The operational plan therefore
proposes explicit values for user review before host inspection. These values are preflight
controls, not pressure-reduction acceptance bounds and not migration thresholds.

