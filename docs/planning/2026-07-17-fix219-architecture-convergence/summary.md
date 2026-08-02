# PDD Summary: fix219 Architecture Convergence

## Status

Prompt-Driven Development status: **Completed**

Detailed design review: **Completed**

Implementation plan review: **Approved for PDD completion on 2026-07-19**

Implementation status: **In progress — Steps 1–2 complete; Step 3 amended and in progress**

Step 3 amendment status: **Completed on 2026-07-21**

Amendment iteration checkpoint: **Reviewed and approved — Stage 1.6 not yet authorized**

At PDD closure:

- Repository branch: `backend-refactor-implementation`
- HEAD: `5f99fc0d234fb8e9bdcdb92ea8ccfd2acd68ca03`
- Tracked implementation code is unchanged.
- The PDD artifact tree under `docs/planning/2026-07-17-fix219-architecture-convergence/` remains untracked.

Approval of this PDD does not authorize implementation code changes. Implementation begins only when the user explicitly selects work from the approved plan.

## Objective

Complete the remaining `fix219` architecture convergence so one overlay-client composition root constructs and owns one selected backend runtime, GNOME native Wayland and GNOME/Mutter native X11 have truthful supported paths, and generic consumers contain no compositor-private presentation, input, lifecycle, helper, status, or diagnostic dispatch.

The project preserves Phase 19 atomic fullscreen monitor handoff behavior and creates backend-neutral extension points for future backends without implementing KDE/KWin or another out-of-scope environment now.

## Requirements Summary

Requirements clarification produced 34 explicit decisions covering:

- GNOME Shell 46–50 policy and Ubuntu 24.04.4 initial validation scope.
- Native Wayland, native X11, and degraded XWayland support boundaries.
- Windowed/borderless modes, scale/layout matrix, and Phase 19 invariants.
- One immutable process-lifetime backend runtime and restart policy.
- Separate discovery, presentation, input, helper, and status behavior.
- Fail-closed GNOME helper prerequisites and one GNOME backend identity.
- EDMC/client/helper hierarchical ownership, heartbeats, leases, expiry, conflicts, and restart behavior.
- Independent support policy, validation evidence, and runtime health.
- Versioned backend settings/status, privacy-safe diagnostics, performance gates, EDMC compliance, and future-backend requirements.

The design-stage iteration checklist found no blocking product question, missing prerequisite research, internal contradiction, or implementation-planning blocker.

Question 35 adds the evidence-driven Step 3 correction: disable capture diagnostics, reduce
stable GNOME helper-query and unchanged repaint pressure test-first, run a controlled four-cell
helper A/B, repeat manual regression checks, and restart a clean 42-capture baseline without
mixing the 12 accepted pre-optimization captures.

## Design Overview

The approved detailed design defines:

1. `overlay_client.launcher.main()` as the production composition root.
2. One `BackendRuntime` with immutable identity and owned discovery, presentation, and input services.
3. One `gnome_shell_wayland` runtime that selects managed PyQt for supported windowed mode and Shell raster for supported borderless fullscreen.
4. A shared `native_x11` runtime with operational ICCCM/EWMH probes and an optional evidence-driven window-manager policy.
5. A distinct degraded `xwayland_compat` runtime.
6. Explicit unimplemented descriptors for other detected Wayland environments.
7. An authenticated owner channel with terminal EOF, 2-second initial heartbeat cadence, and approximately 6-second initial owner-loss bound.
8. GNOME helper protocol 4 with non-preemptive ownership, 2-second initial renewal cadence, and approximately 10-second independent expiry.
9. A schema-version-1 backend envelope separating support, evidence, health, ownership, presentation, probes, and diagnostics.
10. Contract-first migration, developer rollback until parity, formal validation/compliance gates, and final deletion of the temporary second architecture.
11. Backend-owned stable-target caching, unchanged-render repaint suppression, quiet aggregated
    diagnostics, and a clean-baseline rule that preserves immediate recovery and Phase 19
    behavior.

## Implementation Plan Overview

The implementation plan contains 24 one-to-one checklist steps across six phases:

| Phase | Steps | Outcome |
| --- | --- | --- |
| 1. Contract and Evidence Anchors | 1–3 | Pure models, behavior contracts, paper backend, and measured pre-migration baseline |
| 2. One Composition Root | 4–9 | Registry, launcher-owned runtime, routed discovery/presentation/input, and lifted GNOME behavior |
| 3. EDMC-to-Client Ownership | 10–13 | Authenticated launch, heartbeat/EOF shutdown, Tk-safe status cache, and backend-neutral plugin lifecycle |
| 4. GNOME External Ownership | 14–16 | Coordinated protocol-4 leases, independent expiry/conflict handling, and hierarchical recovery |
| 5. Selection, Status, and Evidence | 17–21 | One GNOME identity, operational X11, truthful XWayland/placeholders, schema migration, and public diagnostics/evidence |
| 6. Compliance and Closure | 22–24 | EDMC compliance, future-backend guide, full acceptance, and removal of the old GNOME architecture |

Every step includes:

- a behavior-scoped objective;
- general implementation guidance;
- required unit, harness, GUI, manual, performance, or compliance tests;
- integration with preceding work; and
- a working demonstration.

The pre-migration performance baseline in Step 3 is a hard gate before production routing in Step 5. The old GNOME route is removed only in Step 24 after automated parity, Phase 19, lifecycle, manual support, performance, privacy, and EDMC compliance gates pass.

Step 3 is now expanded within Phase 1 from evidence tooling through cold-start/capture
corrections, a paused 12/42 historical matrix, quiet configuration, helper-query reduction,
unchanged-repaint suppression, controlled A/B, manual regression/soak, and a new coherent
post-optimization matrix starting at 0/42. Thresholds remain unset until that matrix is complete
and reviewed.

The controlled A/B first establishes pressure-reduction acceptance bounds recorded in its report.
Only the completed clean 42-capture baseline establishes versioned migration-regression
thresholds for later fix219 comparisons.

## Artifacts

### Project inputs and requirements

- [`rough-idea.md`](rough-idea.md) — initial objective and source context.
- [`idea-honing.md`](idea-honing.md) — 34 authoritative requirement decisions.

### Research

- [`research-plan.md`](research/research-plan.md) — research scope and completed R.1–R.7 checklist.
- [`current-architecture.md`](research/current-architecture.md) — current selector, status, bundle, consumer, and identity flow.
- [`external-constraints.md`](research/external-constraints.md) — GNOME, Wayland, X11, and EDMC platform constraints.
- [`gnome-runtime-and-lifecycle.md`](research/gnome-runtime-and-lifecycle.md) — GNOME path, lifecycle leaks, Phase 19 invariants, and migration seam.
- [`tests-invariants-and-risks.md`](research/tests-invariants-and-risks.md) — existing coverage, required tests, risks, and reversibility.
- [`x11-backend-identity.md`](research/x11-backend-identity.md) — shared native-X11 runtime and optional window-manager policy decision.
- [`composition-root-and-ownership.md`](research/composition-root-and-ownership.md) — launcher composition root and runtime ownership sequence.
- [`owner-liveness-transport.md`](research/owner-liveness-transport.md) — authenticated EDMC-to-client ownership and heartbeat design.
- [`gnome-helper-lease-protocol.md`](research/gnome-helper-lease-protocol.md) — helper token, lease, conflict, expiry, and failure mapping.
- [`backend-contracts-and-control-plane.md`](research/backend-contracts-and-control-plane.md) — behavior interfaces and three-axis status/schema design.
- [`contract-tests-and-migration.md`](research/contract-tests-and-migration.md) — reusable contracts, GNOME specialization, harness boundary, and staged replacement.
- [`performance-baseline.md`](research/performance-baseline.md) — scenario manifest, measures, and comparison policy.
- [`gnome-helper-pressure-and-repaint.md`](research/gnome-helper-pressure-and-repaint.md) — Step 3 incident evidence, cache/repaint contracts, controlled A/B, and clean-baseline decision.
- [`validation-evidence-and-compliance.md`](research/validation-evidence-and-compliance.md) — public evidence workflow, collector privacy, and current EDMC compliance findings.

### Design and implementation planning

- [`detailed-design.md`](design/detailed-design.md) — standalone approved architecture, interfaces, models, errors, migration, testing, and alternatives.
- [`plan.md`](implementation/plan.md) — approved 24-step test-driven implementation plan and phase/checklist tracker.
- [`iteration-checklist.md`](iteration-checklist.md) — amendment traceability, readiness audit, verified evidence state, and required synchronization actions.
- [`summary.md`](summary.md) — this PDD completion summary.

## Known Starting Compliance Work

The implementation plan must remediate these currently known EDMC compliance failures:

1. The repository records the stale `3.10.3 32bit` EDMC Python baseline; research found upstream documenting 32-bit Python 3.13 and naming 3.13.9 as tested on 2026-07-19. Upstream must be checked again during implementation/release.
2. No dated release/discussion monitoring evidence was found.
3. Preferences can synchronously wait for backend status on the Tk path.
4. `load.py` performs GNOME-specific startup/shutdown cleanup.

These are implementation work, not PDD blockers. The release gate permits no unresolved `No`.

## Evidence-Driven Refinement During Implementation

The following values remain intentionally evidence-driven:

- Final owner heartbeat/loss and helper renewal/expiry timing after suspend, debugger, event-loop, half-open, and clock tests.
- Numeric performance thresholds after repeated pre-migration baseline variance is measured.
- A Mutter-specific X11 policy only if the GNOME native-X11 matrix proves generic ICCCM/EWMH handling insufficient.
- Exact Shell 47–50 evidence levels as maintainer/community reports are reviewed.
- The current upstream EDMC Python baseline at the time of implementation and release.

These do not require more requirements clarification unless evidence would change product scope or support policy.

## Validation Performed During PDD

- Verified branch, HEAD, tracked implementation state, and artifact layout.
- Verified all original 34 requirements are traceable in the detailed design; the 2026-07-21
  amendment records and traces Question 35 through research, design, and Step 3 planning.
- Verified all eight required design sections and seven Mermaid diagrams.
- Verified 24 implementation checklist titles exactly match 24 numbered steps.
- Verified every implementation step contains objective, guidance, tests, integration, and demo sections.
- Verified six implementation phases preserve 24 numbered steps; Phase 1 now expands Step 3
  into nine evidence, correction, A/B, regression, and clean-baseline tracking stages.
- Verified planning Markdown has balanced fences where applicable and no trailing whitespace.
- Revalidated the frozen reduced-v2 manifest as 14 scenarios with three repetitions and all 12
  historical captures against it; confirmed two full-v1 captures remain preserved and
  `thresholds.json` remains absent.
- Verified the synchronization leaves Stage 1.6/working Stage 3.10 not started and does not
  authorize capture resumption, settings changes, or runtime implementation.
- Recorded user approval of the threshold distinction, working sequence, tiered-testing policy,
  progress supersession rule, historical evidence hold, and synchronization as a whole.

No implementation tests, lint, typecheck, build, or GUI commands were run for the 2026-07-21
amendment because it changed documentation only. No test files were added or updated.

## Next Steps

1. Review and optionally commit the PDD artifact tree as a planning-only change.
2. Explicitly authorize Stage 1.6 before any code or configuration changes.
3. Resume Step 3 at Stage 1.6 by disabling capture diagnostics and establishing a quiet
   normal-use state.
4. Complete test-first helper-query and unchanged-repaint pressure reduction, the controlled A/B,
   manual regression/soak, and the clean GNOME 46/Ubuntu 24.04.4 baseline before Step 5 changes
   production routing.
5. Update the plan checklist, phase/stage tables, and exact test evidence after every implemented increment.
