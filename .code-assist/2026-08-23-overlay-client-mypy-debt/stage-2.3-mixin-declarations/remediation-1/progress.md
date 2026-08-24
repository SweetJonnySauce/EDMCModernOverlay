# Stage 2.3 Remediation 1 Progress

## Checklist

- [x] 2.3.6 Create remediation-local context, plan, progress, and log directory before source edits.
- [x] 2.3.6 Run the focused five-file mypy RED command exactly once and save raw output.
- [x] 2.3.7 Verify the preparation producer/consumer shape and make the two bounded typing changes.
- [x] 2.3.8 Run the identical focused mypy GREEN command exactly once and save raw output.
- [x] 2.3.8 Run the prescribed offscreen three-file regression slice exactly once.
- [x] 2.3.9 Run `git diff --check`, review the scoped diff, and write the exact six-field handoff.

## Test selection

Static mypy RED/GREEN plus the existing offscreen regression slice were selected
before source edits. No unit, harness, or test-file change is needed because no
runtime behavior or `load.py` wiring is in scope; the residual risk is whether
the enforced preparation shape is represented exactly.

## RED evidence

The prescribed command exited 1 and reported 12 errors in two files: the 11
unchanged Stage 3.2 renderer diagnostics and exactly two owned diagnostics at
`follow_surface.py:388` and `follow_surface.py:992`. The callback is passed to
`run_backend_presentation_cycle`, whose `BackendPresentationSurfacePreparer`
contract supplies `BackendPresentationSurfacePreparation`; that frozen,
backend-owned data class declares `rect: tuple[int, int, int, int]`. The local
device-ratio log has the separate existing state-contract type
`tuple[str, float, float, float] | None`.

## GREEN evidence

The identical command exited 1 with `Found 10 errors in 1 file (checked 5
source files)`. All remaining diagnostics are the deferred Stage 3.2
renderer-family errors in `render_surface.py`; both owned Stage 2.3 diagnostics
are absent. No suppression or broad `Any`/unchecked rect cast was added.

## Regression and review evidence

The required offscreen slice passed: 55 tests in 0.92s. No test file was added
or changed because this remediation changes only static method/local typing and
does not alter runtime values, `load.py`, or lifecycle wiring. `git diff
--check` exited 0. Review of the bounded source delta confirms it uses the
existing generic backend callback data class, changes no backend selection or
raw enum dispatch, and leaves Qt MRO, initialization, timers, painting, focus,
click-through, and follow control flow unchanged.
