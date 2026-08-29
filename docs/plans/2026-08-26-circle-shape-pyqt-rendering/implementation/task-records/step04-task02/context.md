# Step 04 Task 02 Context

## Mode and scope

`code-assist` runs in auto mode for this documentation-only task. It may update
only the six public documentation pages named in the task and this task record.
It must not change product code, tests, generated task artifacts outside this
record, the approved plan, or the execution dashboard. No network, live EDMC,
OAuth, upload, release, commit, or push action is authorized.

## Restart reconciliation

- Read the governing artifacts in the orchestration-required order, the Step 4
  task artifacts, status dashboard, available task records, `git status --short`,
  and `git diff --check`.
- Step 4 Task 01 is independently recorded as passing both required commands:
  the harness command reported `4 passed in 0.14s`; the processor/paint command
  reported `44 passed in 0.17s`.
- The worktree contains expected prior Steps 1--3 source/test changes and the
  untracked plan directory. They are outside this task and will not be altered.
- Instruction discovery found `README.md` and the harness notes, with no
  `CODEASSIST.md`.

## Test selection and evidence boundary

Test type selected before edits: **no new automated test type**. This task
changes only documentation, not a pure helper/service or EDMC lifecycle wiring.
Every new public helper or raw-payload example will instead be manually compared
with the exact Step 1 payload test and Task 01 lifecycle evidence. The residual
risk is copy drift in prose/examples; the existing mixed harness/unit evidence
does not parse these Markdown pages.

## Contract and dependency map

| Surface | Contract to document |
| --- | --- |
| `send_shape` | Retain positional rectangle calls. The circle form uses stable ID, `shape="circle"`, named centre `x`/`y`, positive `radius`/`thickness`, `color`, `fill`, and `ttl`; it emits no `w`/`h`. |
| `send_raw` / TCP | Raw normalization preserves circle fields; authoritative client validation drops invalid geometry before same-ID drawable-store mutation. |
| Rendering | Derive `centre - radius` / `centre + radius` square, pass it through legacy group/viewport mapping, then draw bounded `QPainter.drawEllipse` with the requested pen/fill and payload opacity. Non-uniform mapping may yield an ellipse. |
| Discovery docs | Present circles as a shape primitive, distinctly from `marker: "circle"` on a vector point. |

## Stale claims found before editing

- `send_shape-API.md` calls the helper rectangle-only, says only `rect` is
  supported, and describes every `x`/`y` as a rectangle top-left.
- `send_raw-API.md` lists only `rect`/`vect`, makes `x`/`y` rectangle-only, and
  has no circle field reference or validation-boundary note.
- `Getting-Started.md` has no circle example and can confuse a vector marker
  named `circle` with a circle shape.
- `Concepts.md` lists text, rectangles, and vectors only.
- `FAQs.md` has no graphical-payload support statement.
- `rendering-pipeline.md` has no circle storage, transform, or final-paint
  explanation.
