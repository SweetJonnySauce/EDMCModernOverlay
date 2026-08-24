# Stage 2.3 Remediation 1 Context

## Bounded scope

This fresh remediation context owns exactly two remaining Stage 2.3 diagnostics
in `overlay_client/follow_surface.py`: the guarded `preparation.rect` member
used for integer geometry, and the later device-ratio snapshot local that
reuses an incompatible inferred name. It must not change renderer diagnostics,
tests/config/top-level progress, Qt lifecycle/MRO/timers/painting/focus/follow
behavior, backend selection, or the fix219/X11 boundary.

## Invariants and evidence

The preceding Stage 2.3 GREEN log leaves 11 deferred renderer errors plus the
two owned diagnostics. `preparation` is already guarded at the call site; this
attempt may model its existing runtime shape only with a precise structural
type, not `Any`, an unchecked broad cast, or a suppression. The later local
will receive a distinct exact tuple type and name. These are annotation/local
typing changes only, so the focused mypy RED/GREEN target and prescribed
offscreen three-file slice are the selected proof; no test or harness update
applies because `load.py` and runtime behavior are excluded.

## Stop condition

Stop with saved evidence if the source cannot establish the preparation-rect
shape precisely, or if the focused target reveals any error family beyond the
11 inventoried renderer diagnostics and these two owned errors.
