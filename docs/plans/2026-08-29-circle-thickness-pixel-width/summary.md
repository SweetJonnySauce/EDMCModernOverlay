# Summary: pixel-width circle strokes

The plan changes only circle stroke semantics: explicit circle thickness is a
stable Qt logical-pixel width, matching legacy vector lines. Rectangle
thickness remains viewport-scaled.

Artifacts:

- `rough-idea.md`
- `idea-honing.md`
- `research/existing-code.md`
- `design/detailed-design.md`
- `implementation/plan.md`

No runtime or test code has changed. The next implementation step is the
focused red/green contract work in Step 1.
