# Stage 2.3 Context — Mixin Declarations

## Scope and invariants

Reconcile only the 19 inherited declaration conflicts at `OverlayWindow` and
the five Stage 2.2 residual diagnostics. The current Qt base list, assignment
owners/defaults, constructors, `super()` chain, timers, paint/clear-first
behavior, focus/click-through, backend selection, and follow behavior are
fixed. The existing `OverlayWindowState` protocol is a type-only seam and must
remain so; no runtime base or storage may be added.

## Evidence reviewed

- Governing `AGENTS.md`, orchestration plan, top-level context/plan/progress,
  status dashboard, Stage 2.1 inventory/handoff, Stage 2.2 records/handoff,
  Stage 2.3 task/scope review, and the intentionally dirty scoped diff.
- Stage 2.2 reduced the focused target from 53 errors to five unsuppressed
  residuals. Stage 2.3 owns the remaining inherited conflicts plus those
  residuals.
- The independent fix219 transparent surface-clear work is already dirty in
  `overlay_client.py` and `test_setup_surface.py`; it remains out of scope.

## Implementation seams

The affected declarations live in the existing mixins and setup-owned
`OverlayWindowState` protocol. Candidate changes are exact class-variable
annotations or precisely typed local values only. No source behavior, import
boundary, test fixture, configuration, or `load.py` wiring is planned.

## Test selection

This is declaration-only work: the prescribed five-file focused mypy command
is the static RED/GREEN proof. The prescribed offscreen setup, repaint-debounce,
and follow-surface slice is the behavior-regression proof. No test update or
harness test applies unless an established runtime contract unexpectedly needs
a precise fixture seam; that would require reassessment before changing it.

## Stop condition

Stop and return evidence if a required type cannot be stated precisely without
changing runtime ownership/lifecycle or widening with `Any`/an ignore, or if
the focused command exposes a new error family outside this approved inventory.
