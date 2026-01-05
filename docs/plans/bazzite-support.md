## Goal: Update the Linux Installer to support Bazzite without compromising or regressing the intall for other distros.

## Situation Summary
- Issue #112 reports the Linux installer hanging on Bazzite (Fedora Silverblue-derived, rpm-ostree/immutable).
- The provided installer log stops after DNF package classification begins, suggesting rpm/dnf status checks are blocking on rpm-ostree systems.
- The user notes that Bazzite discourages rpm/dnf usage in favor of rpm-ostree layering.

## Evidence (Issue #112)
- Installer log ends immediately after: "Running dnf package classification" and "rpmdev-vercmp not available; upgrade comparisons will be skipped."
- EDMC is a Flatpak install; Wayland session detected; Fedora profile selected automatically.
- User confirms the installer hangs (does not exit).

## Initial Requirements (Draft)
- Detect rpm-ostree/immutable systems (Bazzite, Silverblue, Kinoite, etc.) even when `/etc/os-release` reports Fedora-like IDs; prefer `/run/ostree-booted` as the primary signal and use `rpm-ostree status` only when extra context is needed.
- On rpm-ostree systems, avoid running rpm/dnf package status checks that can hang; use safe detection or timeouts.
- Provide a clear, logged path to install dependencies via rpm-ostree layering (including guidance on reboot requirements) or allow a documented manual-skip path when dependencies are already satisfied.
- Log each installer command before execution to support troubleshooting on systems where the installer hangs.
- Add a dedicated `fedora-ostree` profile in `scripts/install_matrix.json` for Bazzite/Silverblue/Kinoite/uBlue variants, with package overrides as needed.
- Preserve existing Fedora (dnf) behavior on mutable systems; no regressions to current distro profiles.
- Ensure Flatpak EDMC installs remain supported (flatpak-spawn handling) in the rpm-ostree flow.
- Update Linux install documentation/FAQ to mention Bazzite/atomic Fedora variants and their dependency install approach.
- Add or update installer tests/validation steps to cover rpm-ostree detection and non-hanging behavior during dependency checks.

## Open Questions
## Decisions (Answered)
- Detection signal: standardize on `/run/ostree-booted` as the primary check; use `rpm-ostree status` only for extra context.
- Installer matrix: add a dedicated `fedora-ostree` profile in `scripts/install_matrix.json` for rpm-ostree variants.
- Installer behavior: ask permission before running any rpm-ostree layering commands.
- Declined rpm-ostree installs: prompt the user to either skip dependency installation (continue with a warning) or exit.
- Distro scope: limit the new profile mapping to Bazzite for now (i.e., only `ID=bazzite`; do not map uBlue/Kinoite/Silverblue yet).
- rpm/dnf checks: hard skip all rpm/dnf package checks on rpm-ostree systems (no timeout fallback).
- Non-interactive: support non-interactive mode; `--yes` auto-approves rpm-ostree layering.

## Open Questions
- Are any Fedora package names different or unavailable in Bazzite/uBlue images for the current dependency list? (Unknown; use the `fedora-ostree` profile to carry overrides once validated.)
  - Current status: no known differences; keep `fedora-ostree` as the override hook for future deltas.

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

## Documentation Updates (Planned)
- Add Bazzite (rpm-ostree) install guidance to README/FAQ and the external wiki, including dependency layering notes, reboot requirement, and installer prompts.

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| Phase 1 | Detect rpm-ostree + route Bazzite to `fedora-ostree` without changing mutable Fedora behavior. | Completed |
| Phase 2 | Implement rpm-ostree dependency flow (no rpm/dnf checks, prompt/--yes, flatpak-aware). | Completed |
| Phase 3 | Add command logging, docs updates, and validation coverage. | Completed |

## Phase Details

### Phase 1: rpm-ostree detection and profile routing
- Goal: detect rpm-ostree systems reliably and map `ID=bazzite` to `fedora-ostree`.
- Behavior that must remain unchanged: existing Fedora (dnf) installs on mutable systems.
- Edge cases/invariants: `/run/ostree-booted` is the primary signal; do not infer ostree from Fedora-like IDs alone.
- Risks: mis-detecting mutable Fedora as ostree; missing Bazzite IDs in os-release parsing.
- Mitigations: add targeted detection tests and keep mapping limited to Bazzite.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add rpm-ostree detection helper and Bazzite routing logic. | Completed |
| 1.2 | Add `fedora-ostree` profile in `scripts/install_matrix.json`. | Completed |
| 1.3 | Add/adjust tests for detection + profile mapping. | Completed |

#### Phase 1 Plan

Stage 1.1 (rpm-ostree detection + routing)
- Touch points: `scripts/install_linux.sh`.
- Steps:
  1) Add a small helper (e.g., `is_ostree_system`) that checks `/run/ostree-booted`; allow a test override path via env to avoid touching `/run` in tests.
  2) In `auto_detect_profile`, if ostree is detected and `ID=bazzite`, route to `fedora-ostree` before the generic matrix match.
  3) Preserve manual `--profile` overrides and existing `PROFILE_SOURCE` behavior.
- Tests: add coverage in Stage 1.3, then run `python -m pytest tests/test_install_linux.py -k ostree`.

Stage 1.2 (add fedora-ostree profile)
- Touch points: `scripts/install_matrix.json`.
- Steps:
  1) Add a new `fedora-ostree` entry under `distros` with `match.ids` set to `["bazzite"]` only.
  2) Mirror Fedora package lists for now; keep overrides empty until validated in Phase 2.
- Tests: rely on JSON parsing in existing tests; no new runtime behavior yet.

Stage 1.3 (tests for detection + profile mapping)
- Touch points: `tests/test_install_linux.py`.
- Steps:
  1) Add a test that simulates `/run/ostree-booted` (via env override) + `ID=bazzite`, then asserts `PROFILE_ID=fedora-ostree`.
  2) Add a test that confirms Fedora without the ostree marker still resolves to `fedora`.
- Tests: `python -m pytest tests/test_install_linux.py -k ostree`.

#### Phase 1 Results
- Added an ostree detection helper with test overrides and routed Bazzite to `fedora-ostree` in `scripts/install_linux.sh`.
- Added a `fedora-ostree` distro profile for `ID=bazzite` in `scripts/install_matrix.json` using rpm-ostree install commands.
- Added tests for Bazzite (ostree) and Fedora (non-ostree) profile selection in `tests/test_install_linux.py`.

### Phase 2: rpm-ostree dependency install flow
- Goal: provide a safe dependency path on ostree without rpm/dnf checks.
- Behavior that must remain unchanged: dnf/rpm checks on mutable Fedora; Flatpak EDMC installs keep working.
- Edge cases/invariants: hard skip rpm/dnf checks on ostree; prompt for rpm-ostree layering unless `--yes`.
- Risks: hanging on rpm/dnf calls; user confusion on reboot requirements.
- Mitigations: explicit prompts, clear logging, and skip/exit choices when layering is declined.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Gate rpm/dnf checks behind ostree detection (hard skip on ostree). | Completed |
| 2.2 | Implement rpm-ostree layering flow with prompt + non-interactive auto-approve. | Completed |
| 2.3 | Handle decline path (skip deps with warning or exit). | Completed |
| 2.4 | Ensure Flatpak EDMC installs remain supported in the ostree path. | Completed |

#### Phase 2 Plan

Stage 2.1 (skip rpm/dnf checks on ostree)
- Touch points: `scripts/install_linux.sh`.
- Steps:
  1) Add a guard in the dependency evaluation path to bypass `classify_package_statuses` when `is_ostree_system` is true.
  2) Ensure the guard is scoped to rpm-ostree only so mutable Fedora still runs full package checks.
  3) Log a clear message that status checks are skipped on ostree (no fallback/timeouts).
- Tests: add a bash-sourced test that sets the ostree marker and asserts package status checks are skipped.

Stage 2.2 (rpm-ostree layering flow)
- Touch points: `scripts/install_linux.sh`.
- Steps:
  1) Add a dedicated install path for `fedora-ostree` that runs `rpm-ostree install` with the computed package list.
  2) Prompt before layering; auto-approve in non-interactive mode and when `--yes` is supplied.
  3) Print guidance about the required reboot after layering completes.
- Tests: add a test that verifies the rpm-ostree install command is selected for `fedora-ostree` and that `--yes` skips the prompt.

Stage 2.3 (decline flow)
- Touch points: `scripts/install_linux.sh`.
- Steps:
  1) If the user declines rpm-ostree layering, prompt to either skip dependency installation (with a warning) or exit.
  2) Ensure the skip path keeps the installer running while clearly stating missing dependencies.
- Tests: add a non-interactive test path that simulates a decline and verifies the skip/exit behavior.

Stage 2.4 (Flatpak support on ostree)
- Touch points: `scripts/install_linux.sh`, `scripts/install_matrix.json`.
- Steps:
  1) Confirm `flatpak-spawn` stays in the `fedora-ostree` package list.
  2) Ensure the Flatpak detection branch still adds Flatpak helper packages under `fedora-ostree`.
- Tests: add coverage that `flatpak` packages are included for `fedora-ostree` when a Flatpak EDMC path is detected.

#### Phase 2 Results
- Skipped package status checks on rpm-ostree systems and treat all dependency packages as install candidates.
- Added rpm-ostree-specific prompting (auto-approve in non-interactive/`--yes`) with a skip-or-exit decline path and reboot guidance.
- Added tests to cover ostree skip behavior, non-interactive approvals, and Flatpak package inclusion in `tests/test_install_linux.py`.

### Phase 3: logging, docs, and validation
- Goal: improve troubleshooting and document Bazzite guidance.
- Behavior that must remain unchanged: existing installer logs and docs not related to Bazzite.
- Edge cases/invariants: log each installer command before execution; keep logs readable.
- Risks: noisy logs or missing commands; doc drift from actual behavior.
- Mitigations: small, consistent log lines and doc updates aligned with install flow.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Log each installer command before execution. | Completed |
| 3.2 | Update README/FAQ/wiki guidance for Bazzite/ostree. | Completed |
| 3.3 | Add/adjust validation steps for rpm-ostree detection and non-hanging behavior. | Completed |

#### Phase 3 Plan

Stage 3.1 (command logging)
- Touch points: `scripts/install_linux.sh`.
- Steps:
  1) Centralize command execution logging (e.g., wrap `run_package_install`/download steps) so each external command is logged before execution.
  2) Ensure logs are written to the log file when `--log` is enabled.
  3) Keep logs concise and include the resolved command line.
- Tests: add a test that runs with `DRY_RUN=true` and asserts the command log output contains the expected command string.

Stage 3.2 (docs updates)
- Touch points: `README.md`, any FAQ/docs referenced by install instructions.
- Steps:
  1) Add a Bazzite/ostree section with rpm-ostree layering guidance and reboot requirement.
  2) Document the non-interactive behavior (`--yes`) and the skip/exit prompts.
  3) Note that Bazzite-only mapping is intentional for now.
- Tests: n/a (docs).

Stage 3.3 (validation checklist)
- Touch points: `docs/plans/bazzite-support.md` (test plan), optionally `tests/`.
- Steps:
  1) Add a short validation checklist for Bazzite: detection, no rpm/dnf hangs, rpm-ostree prompt behavior, and Flatpak path.
  2) Ensure tests mention non-interactive auto-approve and decline path.
- Tests: update the Per-Iteration Test Plan notes with any new commands if needed.

#### Phase 3 Results
- Added command logging hooks for package installs, downloads, checksums, virtualenv setup, and rsync updates in `scripts/install_linux.sh`.
- Updated README + FAQ with Bazzite/rpm-ostree install guidance and non-interactive notes.
- Added a logging test for dry-run package installs in `tests/test_install_linux.py`.
- Captured a Bazzite validation checklist below.

#### Bazzite Validation Checklist
- Auto-detect Bazzite with `/run/ostree-booted` + `ID=bazzite` and select `fedora-ostree`.
- Ensure rpm/dnf status checks are skipped (no hangs).
- Confirm rpm-ostree prompt appears, `--yes` auto-approves, and decline path offers skip/exit.
- Verify Flatpak EDMC installs include `flatpak-spawn`.
- Confirm command logs record package manager, rpm-ostree, and rsync/pip operations when `--log` is enabled.

| Stage | Description | Status |
| --- | --- | --- |
