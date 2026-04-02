# EDMC Compliance Tracker

Follow persona details in `AGENTS.md`.
Treat this as a compliance audit only: do not make code changes as part of this task.
Evaluate each compliance rule with an explicit `Yes` or `No`.
For every `No`, document: why it fails, evidence (file paths/lines or command output), and the exact change required.
Record all checks run (and checks skipped with reason) in `Implementation Results`.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear or blocked (for example, external EDMC-core docs), capture it under `Open Questions`.

----

This file tracks adherence to EDMC’s plugin best practices for the Modern Overlay project. Use it to preserve context about gaps, decisions, and verification steps so we can keep the plugin aligned with EDMC core expectations across releases.

## Compliance rules
These are EDMC best practices. Evaluate the code to make sure it's adhering to these best practices. For each item give me a clear yes or no type answer. If the answer is no, say why and what needs to change. PLUGINS.md refers to https://github.com/EDCD/EDMarketConnector/blob/main/PLUGINS.md
- Stay aligned with EDMC core: check the tested Python version in docs/Releasing before coding (PLUGINS.md:12), keep every plugin in its own directory with a load.py file (PLUGINS.md:24), implement plugin_start3 as the entry point (PLUGINS.md:297), and watch GitHub releases/discussions so you learn about plugin-impacting changes early (PLUGINS.md:41).
- Use only the supported plugin API and helpers: limit imports to the documented modules such as config, theme, monitor, timeout_session, etc. (PLUGINS.md:74), rely on helpers like monitor.game_running()/monitor.is_live_galaxy() to detect player state instead of reimplementing detection (PLUGINS.md:113), and create HTTP sessions via timeout_session.new_session or at least apply config.user_agent so your requests inherit EDMC’s defaults (PLUGINS.md:128). Persist plugin settings with config.set/get_* and namespaced keys plus share common assets through utilities like plugins/common_coreutils.py to avoid collisions or circular imports (PLUGINS.md:85) (PLUGINS.md:452) (PLUGINS.md:156). Note: The overlay client uses overlay_settings.json since it runs outside the EDMC environment. Settings are managed within EDMC for compatibility and replicated to the settings file.
- Adopt EDMC’s logging/versioning patterns: initialize a logging logger using the plugin directory name and drop print in favor of logger.info/debug/... so messages flow through EDMC’s handlers (PLUGINS.md:168). Keeping plugin_name identical to the folder name ensures the logger wiring works (PLUGINS.md:212), while logger.exception/logger.debug(..., exc_info=e) should be used for tracebacks (PLUGINS.md:230). Gate version-specific behavior with config.appversion so you stay compatible across releases (PLUGINS.md:263).
- Keep runtime work responsive and Tk-safe: offload any long-running or network-bound task to a worker thread because every hook is invoked on the Tk main loop (PLUGINS.md:335) (PLUGINS.md:599). Only touch Tk widgets on the main thread, use event_generate sparingly, never trigger it while shutting down, and treat config.shutting_down as a property to avoid hangs (PLUGINS.md:349) (PLUGINS.md:362) (PLUGINS.md:371). Use requests (ideally through timeout_session) instead of urllib to benefit from the bundled CA store and consistent timeout behavior (PLUGINS.md:397).
- Integrate with EDMC’s prefs/UI hooks: build settings tabs with plugin_prefs/prefs_changed, using myNotebook widgets, config.get_int/str/bool/list, locale-aware helpers like number_from_string, and plugin-specific prefixes for keys (PLUGINS.md:417) (PLUGINS.md:455) (PLUGINS.md:452). Return widgets or frames from plugin_app, update their look via Tk/theming helpers, and ensure all UI manipulation stays on the main thread (PLUGINS.md:530) (PLUGINS.md:585) (PLUGINS.md:587).
- Package dependencies and debug HTTP responsibly: develop inside a Python virtual environment so you know which modules must be bundled with the plugin, then copy any third-party packages from site-packages into your plugin directory when needed (PLUGINS.md:1323) (PLUGINS.md:1346). Name the plugin directory so it’s importable (no hyphens or dots) and verify imports through that namespace (PLUGINS.md:1358) (PLUGINS.md:1378). When troubleshooting network calls, respect config.debug_senders and redirect traffic to the built-in debug webserver to capture requests safely (PLUGINS.md:1387) (PLUGINS.md:1391).

## Guiding traits for EDMC plugins
- Clarity first: simple, direct logic; avoid clever tricks; prefer small functions with clear names.
- Consistent style: stable formatting, naming conventions, and file structure; follow project style guides/linters.
- Intent made explicit: meaningful names; brief comments only where intent isn’t obvious; docstrings for public APIs.
- Single responsibility: each module/class/function does one thing; separate concerns; minimize side effects.
- Predictable control flow: limited branching depth; early returns for guard clauses; avoid deeply nested code.
- Good boundaries: clear interfaces; avoid leaking implementation details; use types or assertions to define expectations.
- DRY but pragmatic: share common logic without over-abstracting; duplicate only when it improves clarity.
- Small surfaces: limit global state; keep public APIs minimal; prefer immutability where practical.
- Testability: code structured so it's easy to unit/integration test; deterministic behavior; clear seams for injecting dependencies.
- Error handling: explicit failure paths; helpful messages; avoid silent catches; clean resource management.
- Observability: surface guarded fallbacks/edge conditions with trace/log hooks so silent behavior changes don’t hide regressions.
- Documentation: concise README/usage notes; explain non-obvious decisions; update docs alongside code.
- Tooling: automated formatting/linting/tests in CI; commit hooks for quick checks; steady dependency management.
- Performance awareness: efficient enough without premature micro-optimizations; measure before tuning.

## Checks (run per release or compliance review)
- Confirm target Python compatibility meets or exceeds the minimum version stated in EDMC core `docs/Releasing`; baseline (as of this review) is Python 3.10.3, with 32-bit Windows as the preferred EDMC release parity runtime. Update this file if the baseline changes. This applies to the EDMC plugin runtime; the controller/client run in their own environments and require Python >= 3.10.
- Run `python3 scripts/check_edmc_python.py` to enforce the minimum compatibility baseline in `docs/compliance/edmc_python_version.txt` (the check fails only when the interpreter is below the minimum; `ALLOW_EDMC_PYTHON_MISMATCH=1` is an emergency non-release/dev override).
  - CI runs this via `.github/workflows/ci.yml` on both Python 3.10 and 3.12 without override to prove backward compatibility and newer-runtime support.
- Re-scan imports to ensure only supported EDMC APIs/helpers (`config`, `monitor`, `theme`, `timeout_session`, etc.) are used in plugin code.
- Verify logger wiring (`plugin_name`, folder name, logger name) aligns and that `logger.exception`/`exc_info` is used instead of `print`.
- Confirm long-running or network work runs in worker threads and that Tk widgets are only touched on the main thread.
- Review prefs/UI hooks (`plugin_prefs`, `prefs_changed`, `plugin_app`) for correct `myNotebook` usage and namespaced `config.get/set` keys.
- Validate dependency handling: venv for bundled packages, copied dependencies when needed, and debug HTTP routing via `config.debug_senders`.
- Monitor EDMC releases/discussions: subscribe to `EDCD/EDMarketConnector` GitHub Releases and Discussions; check weekly and before shipping a plugin release, logging any plugin-impacting changes here.
  - PRs must tick the compliance items in `.github/pull_request_template.md`.

## How to pass: Stay aligned with EDMC core
Use this evidence checklist for each release when deciding the `Stay aligned with EDMC core` status.

### Required evidence
- `python3 scripts/check_edmc_python.py` passes (minimum compatibility baseline met).
- `load.py` exists at plugin root.
- `plugin_start3` exists in `load.py`.
- Plugin metadata maps to plugin folder naming (`name = PLUGIN_NAME` and `plugin_name = PLUGIN_NAME`).

### Suggested capture commands
- `python3 scripts/check_edmc_python.py`
- `test -f load.py && echo "load.py present"`
- `rg -n "def plugin_start3|name = PLUGIN_NAME|plugin_name = PLUGIN_NAME" load.py`

### Status rubric
- Mark `Yes` when required evidence is satisfied and any waived sub-requirement is explicitly recorded in `Exceptions`.
- Mark `No` when minimum Python compatibility fails, plugin entrypoint/structure evidence is missing, or a waived sub-requirement is not documented as an exception.

### Exception handling
- If a release intentionally waives EDMC Releases/Discussions logging or parity-environment artifacts, record that waiver in `Exceptions` with release scope and rationale.

## Exceptions
- 0.9.0 waiver: EDMC Releases/Discussions review findings log is not required for 0.9.0 release sign-off.

## Audit scope (2026-04-02)
- Date: 2026-04-02
- Scope used for EDMC plugin compliance: `load.py` and `overlay_plugin/*` (plugin-runtime code).
- Out of scope for EDMC plugin-runtime compliance decisions: `overlay_client/*`, `overlay_controller/*`, and test/archive utilities except where installer/docs evidence is needed for dependency packaging expectations.
- Code changes made during this audit: none (compliance review only).

## Phase Overview

| Phase | Description | Status |
| --- | --- | --- |
| 1 | Evidence collection | Completed |
| 2 | Rule-by-rule evaluation | Completed |
| 3 | Reporting and audit log updates | Completed |

## Phase Details

### Phase 1: Evidence collection

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Run baseline/version checks | Completed |
| 1.2 | Scan hooks/imports/logging/threading/prefs/network usage | Completed |
| 1.3 | Gather dependency/debug-routing/release-process evidence | Completed |

### Phase 2: Rule-by-rule evaluation

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Evaluate each EDMC compliance rule with explicit Yes/No | Completed |
| 2.2 | Capture required fix for every No finding | Completed |

### Phase 3: Reporting and audit log updates

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Record commands run and skipped checks in Implementation Results | Completed |
| 3.2 | Document open questions/blockers for release sign-off | Completed |

## Implementation Results
- Ran: `python3 scripts/check_edmc_python.py`
  - Result: passed minimum compatibility check (`>= 3.10.3`) with non-fatal preferred-arch warning (found `64bit`, preferred parity is `32bit`).
- Ran: `test -f load.py && echo "load.py present"`
  - Result: `load.py present`.
- Ran: `rg -n "def plugin_start3|name = PLUGIN_NAME|plugin_name = PLUGIN_NAME" load.py`
  - Result: found required plugin entrypoint/metadata lines.
- Ran: `rg -n "^\s*print\(" load.py overlay_plugin`
  - Result: no `print` usage in plugin-runtime code.
- Ran: static scans for EDMC API/helper usage, threading, prefs hooks, and HTTP/debug routing:
  - `rg -n "plugin_prefs|prefs_changed|plugin_app|myNotebook|number_from_string|config.get_(int|str|bool|list)|config.set(|_config_key(" load.py overlay_plugin`
  - `rg -n "import monitor|monitor.game_running|monitor.is_live_galaxy|timeout_session.new_session|config.user_agent|requests.|urllib" load.py overlay_plugin`
  - `rg -n "event_generate|shutting_down" load.py overlay_plugin`
  - `rg -n "threading.Thread|Thread\(" load.py overlay_plugin`
- Ran: dependency/process evidence scans:
  - `rg -n "venv|virtualenv|.venv|pip install -r|requirements" scripts/install_linux.sh scripts/install_windows.ps1 docs/FAQ.md README.md`
  - `rg -n "EDMC Releases/Discussions reviewed|compliance items" .github/pull_request_template.md`
- Recorded release waiver:
  - EDMC Releases/Discussions findings log waived for 0.9.0 in `Exceptions`.
- Checks not run:
  - `python -m pytest`, `make check`, and GUI-enabled suites were intentionally skipped for this audit because the compliance tracker asks for policy/structure evidence, not behavioral regression testing.
  - Direct verification of upstream EDMC `docs/Releasing` was skipped in this run (external repo/network not consulted as part of this local compliance pass).

## Current compliance assessment (2026-04-02)

| Item | Status | Why / evidence | Required change (if No) |
| --- | --- | --- | --- |
| Stay aligned with EDMC core (PLUGINS.md:12/24/297/41) | Yes | Structure and entrypoint checks pass (`load.py` present; `plugin_start3` at `load.py:3583`; `name/plugin_name = PLUGIN_NAME` at `load.py:3806-3807`) and Python baseline check passes (`python3 scripts/check_edmc_python.py`). EDMC Releases/Discussions logging is explicitly waived for 0.9.0 in `Exceptions`, which satisfies the status rubric for waived sub-requirements. | N/A |
| Use only supported plugin API/helpers (PLUGINS.md:74/85/113/128/156/452) | Yes | Uses `monitor` helpers via wrappers (`load.py:20`, `load.py:255-270`, used in `load.py:702-707`), uses `timeout_session.new_session` + `config.user_agent`/`config.debug_senders` for HTTP (`overlay_plugin/version_helper.py:21`, `31`, `26`, `148-183`), and persists namespaced config keys via helper wrappers (`overlay_plugin/preferences.py:49`, `128-130`, `162-190`). | N/A |
| Adopt EDMC logging/versioning patterns (PLUGINS.md:168/212/230/263) | Yes | Logger wiring aligns with plugin name (`PLUGIN_NAME`, `LOGGER_NAME = PLUGIN_NAME` in `load.py:180-184`), metadata aligns (`load.py:3806-3808`), and traceback logging uses `LOGGER.exception`/`exc_info` (`load.py:3733-3734`, `3782-3783`, `load.py:1015`). No `print` in plugin runtime (`rg` scan). Version gating via `config.appversion` exists (`overlay_plugin/version_helper.py:82-107`). | N/A |
| Keep runtime work responsive and Tk-safe (PLUGINS.md:335/349/362/371/397/599) | Yes | Long-running/background work is threaded (`load.py:1017-1033`, `overlay_plugin/prefs_services.py` worker thread model, `overlay_plugin/overlay_watchdog.py` background watchdog). HTTP uses `requests` with `timeout_session` preference and no plugin-runtime `urllib` usage (`overlay_plugin/version_helper.py:120-162`, scan result). No `event_generate` usage found; no risky shutdown signaling path found in this runtime scan. | N/A |
| Integrate with EDMC prefs/UI hooks (PLUGINS.md:417/452/455/530/585/587) | Yes | Hooks are present (`plugin_prefs`/`prefs_changed`/`plugin_app` at `load.py:3604-3753`), preferences UI frame is returned from `plugin_prefs` (`load.py:3738-3740`), `myNotebook` is used (`overlay_plugin/preferences.py:981`), and config access uses `config.get_*`/set wrappers and locale-aware `number_from_string` (`overlay_plugin/preferences.py:23-30`, `162-190`, `223-230`). | N/A |
| Package dependencies and debug HTTP responsibly (PLUGINS.md:1323/1346/1358/1378/1387/1391) | Yes | Installers/docs provision dedicated venvs and requirement install flow (`scripts/install_linux.sh:2133-2199`, `scripts/install_windows.ps1:813-852`, `docs/FAQ.md:84`), plugin folder is importable (`EDMCModernOverlay` with root `load.py`), and debug HTTP routing through `config.debug_senders` is implemented (`overlay_plugin/version_helper.py:26`, `165-183`). | N/A |

## Open Questions
- Should this tracker also capture a manually verified EDMC-core `docs/Releasing` check date/reference for each release cycle?
