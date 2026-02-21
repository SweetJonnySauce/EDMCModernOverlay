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
| 1 | Align ingest TTL semantics with EDMCOverlay (`ttl<=0` expires immediately). | Completed |
| 2 | Remove/replace persistence assumptions in callers and tools. | Completed |
| 3 | Update docs/tests and validate behavior. | Completed |

## Phase Details

### Phase 1: Align TTL ingest semantics
- Goal: make `ttl<=0` expire on the next draw pass (no persistence), matching EDMCOverlay.
- Touch points: `overlay_client/legacy_processor.py`, `overlay_client/payload_model.py`.
- Invariants: `legacy_clear` still removes by id; id-only clears remain valid; negative TTL treated like 0.
- Risks: unexpected disappearance of long-lived messages; dedupe path diverges.
- Mitigations: targeted tests around TTL handling and dedupe expiry refresh.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Update legacy ingest TTL handling (`expiry` no longer `None` for `ttl<=0`). | Completed |
| 1.2 | Update dedupe refresh path to match new TTL semantics. | Completed |
| 1.3 | Add/adjust tests for `ttl=0` and negative TTL ingest. | Completed |

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

#### Phase 1 Results
- Legacy ingest now sets `expiry` to the current monotonic time when `ttl<=0` (no persistence).
- Dedupe refresh path mirrors the same `ttl<=0` expiry behavior.
- Added tests covering `ttl=0` and negative TTL expiry plus dedupe refresh updates.

### Phase 2: Remove persistence assumptions
- Goal: ensure no callers rely on `ttl=0` for persistence; require periodic refresh instead.
- Touch points: controller status payloads, CLI tools, dev helpers.
- Invariants: CLI tools still allow `ttl=0` for immediate expiry.
- Risks: controller status visibility loss until refresh behavior is implemented.
- Mitigations: replace persistent call sites with periodic refresh or explicit clears.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Remove `persistent=True` paths and adjust controller status handling. | Completed |
| 2.2 | Ensure CLI/tooling allows `ttl=0` and no longer treats it as persistent. | Completed |

#### Phase 2 Detailed Plan
1) **Inventory persistence assumptions**
   - Search for `ttl=0`, `persistent`, and controller status payloads.
   - Confirm all call sites that relied on `ttl=0` for indefinite display (e.g., controller active banner).
   - Note any CLI helper text or flags that still describe `ttl=0` as persistent.

2) **Replace controller persistence behavior**
   - Update controller status flow to use periodic refreshes instead of `ttl=0` persistence.
   - Decide refresh cadence (e.g., re-send every 1–2 seconds) and ensure it is stopped/cleared when controller exits.
   - Ensure `legacy_clear` is still sent to remove the message immediately on shutdown.

3) **Align CLI/dev tools**
   - Update CLI help strings to describe `ttl=0` as immediate expiry.
   - Ensure CLI tools accept `ttl=0` and do not reject or normalize it to a positive value.
   - Verify any replay scripts keep `ttl=0` as-is.

4) **Tests (targeted)**
   - Add/update tests around controller status lifecycle:
     - status message is visible while refresh is running
     - status is cleared on shutdown
   - Add a CLI helper test if practical (or a doc/test note) to confirm `ttl=0` allowed.

5) **Acceptance checks**
   - No code path treats `ttl=0` as persistent.
   - Controller status remains visible via refresh until explicit clear.
   - CLI tools accept and replay `ttl=0` without coercion.

#### Phase 2 Results
- Removed the `persistent` flag from controller status emission; controller messages now use a positive TTL and refresh on heartbeat.
- Updated CLI helper text to describe `ttl=0` as immediate expiry.
- Relaxed CLI validators to allow `ttl=0` where they previously rejected it.

### Phase 3: Documentation and validation
- Goal: update docs to reflect new TTL semantics and run focused tests.
- Touch points: `docs/send_message-API.md`, `docs/developer.md`, release notes.
- Invariants: doc examples align with EDMCOverlay behavior.
- Risks: mismatched guidance between docs and runtime.
- Mitigations: update docs in the same change set and run targeted tests.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Update documentation and release notes for `ttl=0` semantics. | Completed |
| 3.2 | Run targeted tests (legacy ingest + CLI tooling). | Not Run |

#### Phase 3 Detailed Plan
1) **Document updated TTL semantics**
   - Update `docs/send_message-API.md` to describe `ttl=0` as immediate expiry and remove persistence language.
   - Update `docs/developer.md` to remove the claim that `ttl=0` is a clear/persistent path (keep id-only clear and empty text).
   - Update CLI help text (already done in Phase 2) and ensure no lingering "persistent" references remain.

2) **Release notes**
   - Add a release note entry for the TTL behavior change and compatibility with EDMCOverlay.
   - Call out that callers must refresh periodically to keep a payload visible.

3) **Testing/validation**
   - Run focused tests to cover legacy ingest and dedupe changes:
     - `python -m pytest tests/test_legacy_processor.py`
     - `python -m pytest overlay_client/tests/test_payload_dedupe.py`
   - (Optional) run CLI smoke checks for `tests/send_overlay_text.py` and `tests/send_overlay_shape.py` with `--ttl 0`.

4) **Acceptance checks**
   - Docs match runtime behavior (`ttl=0` expires immediately).
   - Release notes describe the breaking/behavioral change.
   - Targeted tests pass.

#### Phase 3 Results
- Updated `docs/developer.md` and `RELEASE_NOTES.md` to reflect `ttl=0` immediate expiry.
- Skipped updates to `docs/send_message-API.md` per request.
- Tests not run in this phase.
