## Goal: Add docstrings to public APIs and large modules to reduce “AI slop” signals

## Refactorer Persona
- Bias toward documenting intent and side effects over restating code.
- Prefer small, focused docstrings on public surfaces; avoid noise on obvious helpers.
- Keep behavior unchanged; docstrings must not imply features that do not exist.
- Call out EDMC-specific invariants, threading/IO constraints, and UI focus rules.
- Write docstrings that help future contributors decide where to make changes.

## Dev Best Practices

- Follow PEP 257: summary line, blank line, then details only when needed.
- Prefer simple imperative verbs (“Return…”, “Build…”, “Apply…”).
- Document parameters/returns only when non-obvious or side-effectful.
- Use consistent terminology already used in the codebase (EDMC, overlay client/controller).
- Avoid adding docstrings to tiny private helpers unless they clarify tricky behavior.

## Per-Iteration Test Plan
- **Headless quick pass:** `python -m pytest` (scope with `-k docstring` only if tests are added)
- **Core project checks:** `make check` if available after docstring pass
- **Notes:** docstrings should not require runtime changes; tests are optional unless behavior is touched

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Inventory and prioritize docstring targets | Planned |
| 2 | Document core runtime and API entrypoints | Planned |
| 3 | Document UI-heavy modules and utilities | Planned |
| 4 | Review, consistency pass, and verification | Planned |

## Phase Details

### Phase 1: Inventory and prioritize docstring targets
- Identify public modules/classes/functions with missing or thin docstrings.
- Prioritize by file size, churn, and user-facing impact (entrypoints first).
- Define a short style guide snippet for docstrings used in this repo.

**Docstring style snippet (Phase 1.3 draft)**
- Follow PEP 257: one-line summary, blank line, then details only when needed.
- Prefer intent + side effects over restating implementation.
- Use EDMC terminology already present in the codebase; avoid new jargon.
- Call out threading/IO/UI constraints that affect EDMC safety or UX.
- Document params/returns only when non-obvious or side-effectful (plain PEP prose).
- Keep docstrings short on helpers; expand only where behavior is subtle or error-prone.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Scan for exported/public functions lacking docstrings | Planned |
| 1.2 | Build a prioritized target list (top 20-30 items) | Planned |
| 1.3 | Agree on docstring style conventions for this pass | Planned |

### Phase 2: Document core runtime and API entrypoints
- Focus on entrypoints, runtime services, and cross-process boundaries.
- Ensure docstrings mention threading/IO side effects and EDMC log level rules.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add/update docstrings in `load.py` for runtime lifecycle helpers | Planned |
| 2.2 | Add/update docstrings in `overlay_plugin/overlay_api.py` | Planned |
| 2.3 | Add/update docstrings in `overlay_client/overlay_client.py` and `overlay_controller/overlay_controller.py` | Planned |
| 2.4 | Add/update docstrings in `overlay_client/render_surface.py` and `overlay_client/setup_surface.py` | Planned |

### Phase 3: Document UI-heavy modules and utilities
- Target large UI constructors and debug tooling where intent is currently implicit.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add/update docstrings in `overlay_plugin/preferences.py` (panel sections + callbacks) | Planned |
| 3.2 | Add/update docstrings in `utils/plugin_group_manager.py` and `utils/payload_inspector.py` | Planned |
| 3.3 | Add/update docstrings in smaller helper UIs where behavior is non-obvious | Planned |

### Phase 4: Review, consistency pass, and verification
- Ensure wording consistency, no contradictions, and no promises beyond behavior.

| Stage | Description | Status |
| --- | --- | --- |
| 4.1 | Consistency sweep (terminology, tense, and side-effect mentions) | Planned |
| 4.2 | Run selected tests or skip with notes if unchanged behavior | Planned |
| 4.3 | Final docstring lint/PEP 257 sanity check (manual) | Planned |
