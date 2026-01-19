## Goal: ttl=0 is implemented incorrectly

## New Requirements (EDMCOverlay parity)
- `ttl=0` must expire the payload immediately (no persistence).
- `ttl<0` should also expire immediately (same as `ttl=0` in EDMCOverlay).
- Applies consistently to legacy `message`, `rect`, and `vect` payloads.
- Clearing remains explicit: empty `text` or `shape` payloads, or `legacy_clear` events, remove by `id`.
- No hidden persistence behavior tied to `ttl=0`; if persistence is needed, it must be explicit and documented.

## Clarifications (2025-??-??)
- Expiry timing mirrors EDMCOverlay: `ttl=0` is dropped on the next draw pass (typically not rendered).
- Modern Overlay will **not** provide a persistence mechanism; callers must refresh periodically.
- EDMCOverlay provides no persistent API or flag; it relies solely on TTL and clear-by-id.
- Id-only payloads remain valid clears regardless of TTL.
- CLI/dev tools should accept `ttl=0` and replay it as "expire immediately."

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
| 1 | Align ingest TTL semantics with EDMCOverlay (`ttl<=0` expires immediately). | Planned |
| 2 | Remove/replace persistence assumptions in callers and tools. | Planned |
| 3 | Update docs/tests and validate behavior. | Planned |

## Phase Details

### Phase 1: Align TTL ingest semantics
- Goal: make `ttl<=0` expire on the next draw pass (no persistence), matching EDMCOverlay.
- Touch points: `overlay_client/legacy_processor.py`, `overlay_client/payload_model.py`.
- Invariants: `legacy_clear` still removes by id; id-only clears remain valid; negative TTL treated like 0.
- Risks: unexpected disappearance of long-lived messages; dedupe path diverges.
- Mitigations: targeted tests around TTL handling and dedupe expiry refresh.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Update legacy ingest TTL handling (`expiry` no longer `None` for `ttl<=0`). | Planned |
| 1.2 | Update dedupe refresh path to match new TTL semantics. | Planned |
| 1.3 | Add/adjust tests for `ttl=0` and negative TTL ingest. | Planned |

#### Phase 1 Detailed Plan
1) **Map current TTL semantics**
   - Confirm all TTL computations and expiry usage paths:
     - `overlay_client/legacy_processor.py` (ingest → `expiry`)
     - `overlay_client/payload_model.py` (dedupe refresh → `expiry`)
     - `overlay_client/legacy_store.py` (purge uses `expiry < now`)
   - Capture baseline behavior in notes for `ttl=0` and `ttl<0`.

2) **Implement EDMCOverlay-aligned expiry**
   - Change `ttl` handling so `ttl<=0` produces an `expiry` timestamp equal to “now” (immediate expiry), not `None`.
   - Ensure negative TTL is treated the same as zero.
   - Make the same change in the dedupe refresh path so TTL refreshes do not “resurrect” persistent items.

3) **Confirm clear semantics remain intact**
   - `legacy_clear` events remove by id.
   - id-only payloads still clear by id.
   - Empty `text` messages still clear by id (legacy path).

4) **Tests (targeted)**
   - Add/update tests to verify:
     - `ttl=0` results in an expired item on next purge.
     - `ttl<0` behaves the same as `ttl=0`.
     - `ttl>0` still expires after the specified duration.
     - Dedupe refresh updates expiry for `ttl>0` and does not set `expiry=None` for `ttl<=0`.
   - Candidate commands:
     - `python -m pytest -k legacy_processor`
     - `python -m pytest -k payload_model`

5) **Acceptance checks**
   - A payload with `ttl=0` never persists without refresh (disappears on next draw/purge).
   - Clearing still works via `legacy_clear`, id-only payloads, or empty text.
   - No new persistence pathways introduced.

### Phase 2: Remove persistence assumptions
- Goal: ensure no callers rely on `ttl=0` for persistence; require periodic refresh instead.
- Touch points: controller status payloads, CLI tools, dev helpers.
- Invariants: CLI tools still allow `ttl=0` for immediate expiry.
- Risks: controller status visibility loss until refresh behavior is implemented.
- Mitigations: replace persistent call sites with periodic refresh or explicit clears.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Remove `persistent=True` paths and adjust controller status handling. | Planned |
| 2.2 | Ensure CLI/tooling allows `ttl=0` and no longer treats it as persistent. | Planned |

### Phase 3: Documentation and validation
- Goal: update docs to reflect new TTL semantics and run focused tests.
- Touch points: `docs/send_message-API.md`, `docs/developer.md`, release notes.
- Invariants: doc examples align with EDMCOverlay behavior.
- Risks: mismatched guidance between docs and runtime.
- Mitigations: update docs in the same change set and run targeted tests.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Update documentation and release notes for `ttl=0` semantics. | Planned |
| 3.2 | Run targeted tests (legacy ingest + CLI tooling). | Planned |
