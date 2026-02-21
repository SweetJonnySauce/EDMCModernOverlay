## Goal: Allow for custom font sizing of marker labels while maintaining backwards compatibility

## Requirements
- Allow marker label text size to be specified in legacy vector payloads (`send_raw`).
- Reuse the existing `size` semantic from `send_message()` (presets: `small`, `normal`, `large`, `huge`).
- Default to `normal` when the field is missing/empty/invalid.
- Backwards compatibility: existing payloads must render exactly as before.
- Per-point override: when present on a point with `text`, it affects only that label.
- Optional payload-level default is allowed and must not break per-point precedence.
- `size` on a point without `text` is ignored silently.
- Only legacy presets are accepted; numeric point sizes are not supported (matches `send_message()`).
- No plugin-specific logic; behavior must be data-driven and generic.
- Invalid values are ignored without crashing (fallback to `normal`).
 
## Refactorer Persona
- Bias toward carving out modules aggressively while guarding behavior: no feature changes, no silent regressions.
- Prefer pure/push-down seams, explicit interfaces, and fast feedback loops (tests + dev-mode toggles) before deleting code from the monolith.
- Treat risky edges (I/O, timers, sockets, UI focus) as contract-driven: write down invariants, probe with tests, and keep escape hatches to revert quickly.
- Default to “lift then prove” refactors: move code intact behind an API, add coverage, then trim/reshape once behavior is anchored.
- Resolve the “be aggressive” vs. “keep changes small” tension by staging extractions: lift intact, add tests, then slim in follow-ups so each step stays behavior-scoped and reversible.
- Track progress with per-phase tables of stages (stage #, description, status). Mark each stage as completed when done; when all stages in a phase are complete, flip the phase status to “Completed.” Number stages as `<phase>.<stage>` (e.g., 1.1, 1.2) to keep ordering clear.
- Personal rule: if asked to “Implement…”, expand/document the plan and stages (including tests to run) before touching code.
- Personal rule: keep notes ordered by phase, then by stage within that phase.

## Dev Best Practices

- Keep changes small and behavior-scoped; prefer feature flags/dev-mode toggles for risky tweaks.
- Plan before coding: note touch points, expected unchanged behavior, and tests you’ll run.
- Avoid UI work off the main thread; keep new helpers pure/data-only where possible.
- When touching preferences/config code, use EDMC `config.get_int/str/bool/list` helpers and `number_from_string` for locale-aware numeric parsing; avoid raw `config.get/set`.
- Record tests run (or skipped with reasons) when landing changes; default to headless tests for pure helpers.
- Prefer fast/no-op paths in release builds; keep debug logging/dev overlays gated behind dev mode.

## Per-Iteration Test Plan
- **Env setup (once per machine):** `python3 -m venv .venv && source .venv/bin/activate && pip install -U pip && pip install -e .[dev]`
- **Headless quick pass (default for each step):** `source .venv/bin/activate && python -m pytest` (scope with `tests/…` or `-k` as needed).
- **Core project checks:** `make check` (lint/typecheck/pytest defaults) and `make test` (project test target) from repo root.
- **Full suite with GUI deps (as applicable):** ensure GUI/runtime deps are installed (e.g., PyQt for Qt projects), then set the required env flag (e.g., `PYQT_TESTS=1`) and run the full suite.
- **Targeted filters:** use `-k` to scope to touched areas; document skips (e.g., long-running/system tests) with reasons.
- **After wiring changes:** rerun headless tests plus the full GUI-enabled suite once per milestone to catch integration regressions.

## Guiding Traits for Readable, Maintainable Code
- Clarity first: simple, direct logic; avoid clever tricks; prefer small functions with clear names.
- Consistent style: stable formatting, naming conventions, and file structure; follow project style guides/linters.
- Intent made explicit: meaningful names; brief comments only where intent isn’t obvious; docstrings for public APIs.
- Single responsibility: each module/class/function does one thing; separate concerns; minimize side effects.
- Predictable control flow: limited branching depth; early returns for guard clauses; avoid deeply nested code.
- Good boundaries: clear interfaces; avoid leaking implementation details; use types or assertions to define expectations.
- DRY but pragmatic: share common logic without over-abstracting; duplicate only when it improves clarity.
- Small surfaces: limit global state; keep public APIs minimal; prefer immutability where practical.
- Testability: code structured so it’s easy to unit/integration test; deterministic behavior; clear seams for injecting dependencies.
- Error handling: explicit failure paths; helpful messages; avoid silent catches; clean resource management.
- Observability: surface guarded fallbacks/edge conditions with trace/log hooks so silent behavior changes don’t hide regressions.
- Documentation: concise README/usage notes; explain non-obvious decisions; update docs alongside code.
- Tooling: automated formatting/linting/tests in CI; commit hooks for quick checks; steady dependency management.
- Performance awareness: efficient enough without premature micro-optimizations; measure before tuning.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Define payload semantics + normalization path | Completed |
| 2 | Renderer plumbing + adapter support | Completed |
| 3 | Tests + docs + release notes | Completed |

## Phase Details

### Phase 1: Payload Semantics + Normalization
- Goal: define the `size` field usage for marker labels and carry it through legacy normalization.
- Behavior invariants: missing/invalid `size` keeps current default (`normal`); no behavior change for existing payloads.
- Edge cases: `text` missing but `size` present; size set on a point without marker/text; mixed sizes across points.
- Risks: silently breaking existing payloads; inconsistent default between message and marker labels.
- Mitigations: explicit default handling + tests covering default + override.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Document payload field (`size`) and precedence rules | Completed |
| 1.2 | Extend legacy normalization to retain per-point `size` | Completed |

#### Phase 1 Detailed Plan
1. **Confirm existing `send_message()` size contract**  
   - Verify that `send_message()` accepts only string presets and does not support numeric sizes.  
   - Document that marker labels follow the same preset-only contract.
2. **Define payload-level default semantics**  
   - Add a payload-level `size` default for `shape:vect` payloads (optional).  
   - Precedence rules: per-point `size` overrides payload-level `size`; missing/invalid -> `normal`.
3. **Specify point-level behavior**  
   - Point `size` applies only when `text` is present; otherwise ignore silently.  
   - No change to marker drawing or line rendering.
4. **Normalization changes (legacy path)**  
   - In `overlay_client/legacy_processor.py`, when normalizing vector points, capture `size` if it is a valid preset.  
   - Ignore invalid values (fallback to `normal` downstream).  
   - Do not introduce new fields for non-text points.
5. **Documented invariants (explicit in doc)**  
   - Missing size -> `normal`.  
   - Only presets accepted.  
   - Backwards compatibility guaranteed (no change when size not provided).

#### Phase 1 Results
- Added preset validation (`small|normal|large|huge`) for marker label sizes in legacy vector normalization.
- Per-point `size` is retained only when the point has `text`; otherwise ignored.
- Payload-level default captured as `text_size` on vector payloads (for Phase 2 renderer usage).
- Dedupe snapshot now includes marker label size data so changes invalidate cached payloads.
- Files touched: `overlay_client/legacy_processor.py`.
- Tests: not run (Phase 1 only).

### Phase 2: Renderer + Adapter Wiring
- Goal: thread `size` through vector renderer and Qt adapter.
- Behavior invariants: rendering unchanged when `size` absent; defaults to `normal`.
- Risks: font sizing inconsistency between marker labels and legacy messages; text measurement mismatch.
- Mitigations: adapt `measure_text_block` and `draw_text` to accept optional size; keep same font fallback logic.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add optional size to vector renderer interfaces | Completed |
| 2.2 | Use legacy preset size in `_QtVectorPainterAdapter` | Completed |

#### Phase 2 Detailed Plan
1. **Vector payload defaults**
   - Define how payload-level `text_size` (from Phase 1) maps to a point size fallback.
   - Precedence: per-point `size` → payload `text_size` → `normal`.
2. **Vector renderer API changes**
   - Extend `VectorPainterAdapter` to accept `text_size` for `measure_text_block()` and `draw_text()`.
   - Update `render_vector()` to pass `text_size` when drawing/measurements are required.
3. **Qt adapter implementation**
   - Update `_QtVectorPainterAdapter._text_font()` to accept a size token.
   - Use `self._window._legacy_preset_point_size(size, state, mapper)` with fallback to `normal`.
4. **Text height measurement**
   - Ensure `_measure_text_height()` uses the same size‑aware adapter measurement to keep alignment correct.
5. **Compatibility guardrails**
   - Keep the default path identical when no `size` data is present.
   - Avoid changing marker placement logic or line rendering behavior.
6. **Touchpoints**
   - `overlay_client/vector_renderer.py`
   - `overlay_client/paint_commands.py`
   - Any adapter interface updates and call sites.

#### Phase 2 Results
- Added optional `text_size` to vector renderer adapter interfaces and wiring.
- Resolved effective size with precedence: per-point `size` → payload `text_size`/`size` → `normal`.
- `_QtVectorPainterAdapter` now selects legacy preset size per call; defaults to `normal`.
- Files touched: `overlay_client/vector_renderer.py`, `overlay_client/paint_commands.py`.
- Tests: not run (Phase 2 only).

### Phase 3: Tests + Docs + Release Notes
- Goal: lock behavior with tests and update docs.
- Risks: test gaps allow regressions; undocumented fields confuse plugin authors.
- Mitigations: add targeted tests + update docs + release notes.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Add tests for default + override sizes | Completed |
| 3.2 | Update docs + release notes | Completed |

#### Phase 3 Detailed Plan
1. **Tests (unit)**
   - Add/extend vector renderer tests to cover:
     - Default size when no `size` present (expects `normal`).
     - Per‑point override (`size="large"`) beats payload default.
     - Payload‑level `text_size`/`size` applies when point is missing size.
     - Size ignored when point has no `text`.
   - Add a regression test to confirm backward‑compat adapter call path (no `text_size` kwarg required).
2. **Docs**
   - Update the relevant payload documentation (legacy vector payloads) with the new `size` field semantics.
   - Clarify precedence: point `size` → payload `text_size`/`size` → `normal`.
3. **Release notes**
   - Add a bullet describing marker label sizes (legacy vectors) and the default (`normal`).
4. **Test run record**
   - Note which tests were run, and why any were skipped.

#### Phase 3 Results
- Added vector renderer tests covering default size, per-point override, payload-level defaults, ignored size on non-text points, and legacy adapter fallback.
- Updated payload documentation with legacy vector `size` semantics.
- Updated release notes for marker label size support.
- Tests: `python3 -m pytest tests/test_vector_renderer.py`
