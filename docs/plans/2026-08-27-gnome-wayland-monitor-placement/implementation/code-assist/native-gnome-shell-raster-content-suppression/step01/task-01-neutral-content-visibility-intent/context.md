# Context: Neutral Content-Visibility Intent

## Task setup

- **Mode:** auto; the orchestration authorizes autonomous execution with no
  further interaction.
- **Scope:** the pure backend-neutral policy seam and its unit/boundary tests.
- **Out of scope:** GNOME helper protocol, actor behavior, `allow_unfocused_target`,
  live validation, staging, and commits.

## Existing documentation

- `README.md` identifies a cross-platform EDMC overlay project.
- No `CODEASSIST.md` or `CONTRIBUTING.md` file was found. The repository
  `AGENTS.md`, task, design, lessons, and orchestration prompt govern this
  work instead.
- The design separates a neutral `visible`/`suppressed` intent from
  native-GNOME helper capability and actor behavior. The lessons prohibit
  mapping ordinary focus loss to actor lifecycle operations.

## Relevant structure and patterns

- `overlay_client/backend/presentation_policy.py` is pure Python and contains
  `BackendPresentationVisibilityDecision`, the existing boolean
  `content_visible`, and all debounce/warmup decisions.
- `overlay_client/follow_surface.py` consumes the existing boolean to control
  managed-PyQt content; it must not change in this task.
- `overlay_client/tests/test_backend_presentation_policy.py` asserts policy
  facts with direct enum/field equality.
- `overlay_client/tests/test_backend_architecture_boundary.py` uses source
  assertions to prevent generic runtime ownership from leaking GNOME details.

## Dependency map

```text
snapshot + prior debounce state
    -> presentation_policy decision.content_visible
    -> derived neutral decision.content_visibility
    -> later native GNOME bundle consumer (not part of this task)

follow_surface -> existing content_visible/content_suppressed behavior (unchanged)
```

## Requirements and acceptance mapping

| Requirement | Evidence |
| --- | --- |
| Typed, exactly two-value neutral intent | New policy unit tests import and compare the enum. |
| Focused and keep-visible resolve visible | Existing focused/keep-visible tests gain explicit intent assertions. |
| Debounced and prepared suppression resolve suppressed | Existing debounced and prepared tests gain explicit intent assertions. |
| Hard loss remains hidden and exposes deterministic intent | Existing unavailable/minimized/off-workspace tests gain suppressed intent assertions. |
| No GNOME dispatch at generic seam | New architecture-boundary source test. |

## Decision

Derive the typed property solely from `content_visible`. This provides a
single source of truth and preserves every existing return path, including
debounce, warmup, and lifecycle handling.
