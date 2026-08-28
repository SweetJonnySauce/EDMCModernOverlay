# Step 3.1 Plan: Neutral Content-Intent Transport

## Test scenarios

1. A selected generic runtime receives `suppressed` when callers provide that
   neutral intent.
2. The follow surface starts with `visible`, retains `suppressed` only after
   the existing policy reaches its debounce, and sends it on the next cycle.
3. Focus return changes the retained value to `visible` and schedules exactly
   one next-cycle refresh.
4. The checked preference keeps the retained value `visible` while unfocused.
5. A hard target lifecycle loss resets the retained transport value to
   `visible`; it still uses the existing hide path.
6. Architecture tests continue to prove generic source has no GNOME helper
   import, protocol symbol, or raw backend dispatch.

## RED → GREEN → REFACTOR

- [x] RED: add focused transport and follow-lifecycle tests.
- [ ] GREEN: add the smallest neutral request and retained-state plumbing.
- [ ] REFACTOR: inspect naming, reset behavior, and bounded refresh semantics.
- [ ] Validate focused tests, Ruff, and `git diff --check`.

## Risks and mitigations

- The intent is known only after a cycle. Store it for the following cycle and
  use the existing one-shot refresh flag; do not add a second debounce.
- A hard lifecycle result may arrive after a prior suppressed request. Reset
  the retained next-cycle value to visible while preserving the existing hide
  decision.
