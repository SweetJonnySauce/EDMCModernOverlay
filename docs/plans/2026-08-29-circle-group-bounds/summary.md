# Circle group bounds plan summary

## Created artifacts

- `rough-idea.md`: problem statement.
- `idea-honing.md`: confirmed scope and planning decision.
- `research/existing-code.md`: data-flow and root-cause evidence.
- `design/detailed-design.md`: standalone design for radius-aware group bounds.
- `implementation/plan.md`: incremental test-driven execution plan.

## Design summary

The Fill-mode grouping helper will treat circles as their full square visual
extent after applying transform metadata to all four corners. This makes group
bounds match the existing renderer and stabilizes group anchoring across
payload refreshes.

## Next step

Implement the plan starting with the normal circle-bounds regression test.
