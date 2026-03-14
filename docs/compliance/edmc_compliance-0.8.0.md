# EDMC 0.8.0 Compliance Review Quick Start

Follow persona details in `AGENTS.md`.
Treat this as a compliance audit only: do not make code changes as part of this task.
Evaluate each compliance rule with an explicit `Yes` or `No`.
For every `No`, document: why it fails, evidence (file paths/lines or command output), and the exact change required.
Record all checks run (and checks skipped with reason) in `Implementation Results`.
After each stage is complete, change stage status to `Completed`.
When all stages in a phase are complete, change phase status to `Completed`.
If something is unclear or blocked (for example, external EDMC-core docs), capture it under `Open Questions`.

---

# EDMC Compliance Tracker

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

## Exceptions
- EDMC Releases/Discussions review findings are not required to be logged for 0.8.0 release sign-off.
- A successful `python3 scripts/check_edmc_python.py` run in a Windows 32-bit EDMC-matching environment artifact is not required for 0.8.0; maintainer attestation is acceptable.

## Audit scope (0.8.0)
- Date: 2026-03-14
- Scope used for EDMC plugin compliance: `load.py` and `overlay_plugin/*` (plugin-runtime code).
- Out of scope for EDMC plugin-runtime compliance decisions: `overlay_client/*` and `overlay_controller/*` except where installer/docs evidence is needed for dependency packaging expectations.
- Code changes made during this audit: none.

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
| 1.1 | Run required baseline/version checks | Completed |
| 1.2 | Scan plugin-runtime hooks/imports/logging/threading/prefs usage | Completed |
| 1.3 | Gather dependency/debug-routing evidence from docs/installers | Completed |

### Phase 2: Rule-by-rule evaluation

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Evaluate each EDMC compliance rule with explicit Yes/No | Completed |
| 2.2 | Capture required fixes for every No finding | Completed |

### Phase 3: Reporting and audit log updates

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Record commands run and skipped checks in Implementation Results | Completed |
| 3.2 | Document open questions/blockers for release sign-off | Completed |

## Implementation Results
- Ran: `python3 scripts/check_edmc_python.py`
  - Result: failed (`python: command not found` in this environment).
- Ran: `python3 scripts/check_edmc_python.py`
  - Result: passed minimum compatibility check (Python 3.12.3 >= 3.10.3); emitted non-fatal preferred-arch warning (expected 32bit, found 64bit).
- Ran: `ALLOW_EDMC_PYTHON_MISMATCH=1 python3 scripts/check_edmc_python.py`
  - Result: not required under the minimum-compatibility policy; override is now reserved for emergency non-release/dev cases when running below the minimum version.
- Ran static compliance scans (entrypoints/imports/logging/threading/prefs/network/debug routing):
  - `rg -n "def plugin_start3|def plugin_prefs|def prefs_changed|def plugin_app|..."`
  - `rg -n "import config|monitor|timeout_session|..."`
  - `rg -n "config.get_(int|str|bool|list)|number_from_string|new_session|debug_senders|..."`
  - `rg -n "\\bprint\\(" load.py overlay_plugin -g '*.py'`
  - `rg -n "event_generate|shutting_down" load.py overlay_plugin -g '*.py'`
- Reviewed supporting files:
  - `load.py`
  - `overlay_plugin/preferences.py`
  - `overlay_plugin/version_helper.py`
  - `overlay_plugin/prefs_services.py`
  - `overlay_plugin/overlay_watchdog.py`
  - `.github/pull_request_template.md`
  - `docs/FAQ.md`
  - `scripts/install_linux.sh`
  - `scripts/install_windows.ps1`
- Tests not run in this audit:
  - `python -m pytest`, `make check`, and GUI-enabled suites were skipped because this task was a compliance-only review with no code changes; this audit focused on checklist evidence and required compliance commands.

## Current compliance assessment (2026-03-14)

| Item | Status | Why / evidence | Required change (if No) |
| --- | --- | --- | --- |
| Stay aligned with EDMC core (PLUGINS.md:12/24/297/41) | Yes | Structure and entrypoint are correct (`load.py` exists at plugin root, `plugin_start3` at `load.py:3342`, `plugin_name = PLUGIN_NAME` at `load.py:3542`), baseline is pinned (`docs/compliance/edmc_python_version.txt`), and the updated checker passes on newer runtimes (`python3 scripts/check_edmc_python.py` reports Python 3.12.3 meets minimum >= 3.10.3, with a non-fatal preferred-arch warning). Release/discussion logging is explicitly exempted for 0.8.0 under Exceptions. | N/A |
| Use only supported plugin API/helpers (PLUGINS.md:74/85/113/128/156/452) | Yes | Plugin-runtime imports are limited to supported EDMC APIs/helpers (`monitor` in `load.py:20`; `config` + `number_from_string` in `overlay_plugin/preferences.py:21-23`; `timeout_session.new_session`, `config.user_agent`, `config.debug_senders` in `overlay_plugin/version_helper.py:21-33`). Monitor helpers are used via wrappers (`load.py:232-245`) and gated in journal handling (`load.py:663-668`). Settings use namespaced keys (`CONFIG_PREFIX = "edmc_modern_overlay."` in `overlay_plugin/preferences.py:45`) with `config.get_*`/`set` wrapper calls (`overlay_plugin/preferences.py:101-205`, `633-676`) and JSON shadow replication (`overlay_plugin/preferences.py:619-632`). | N/A |
| Adopt EDMC logging/versioning patterns (PLUGINS.md:168/212/230/263) | Yes | Logger naming is aligned with folder/plugin name (`PLUGIN_NAME = "EDMCModernOverlay"` and `LOGGER_NAME = PLUGIN_NAME` in `load.py:166-169`), logger bridge is configured (`load.py:350-405`), and plugin metadata maps to `PLUGIN_NAME` (`load.py:3541-3542`). No `print(` usage found in plugin-runtime (`rg -n "\\bprint\\(" load.py overlay_plugin`). Tracebacks use `exc_info` patterns (for example `load.py:675`, `716`, `918`; `overlay_plugin/hotkeys.py:73`). Version gating uses `config.appversion` parsing in `overlay_plugin/version_helper.py:82-109`. | N/A |
| Keep runtime work responsive and Tk-safe (PLUGINS.md:335/349/362/371/397/599) | Yes | Long-running/network tasks are off the Tk hook path using worker threads (`threading.Thread` start in `load.py:579`, `920`, `929`; worker infrastructure in `overlay_plugin/prefs_services.py:10-69`; watchdog thread in `overlay_plugin/overlay_watchdog.py:38-61`). Journal hook remains lightweight and delegates runtime work (`load.py:657-706`). No `event_generate` or `shutting_down` usage in plugin-runtime (`rg -n "event_generate|shutting_down" load.py overlay_plugin`). HTTP uses `requests` and prefers `timeout_session.new_session` (`overlay_plugin/version_helper.py:21`, `149-160`) with no `urllib` usage in plugin-runtime scan. | N/A |
| Integrate with EDMC prefs/UI hooks (PLUGINS.md:417/452/455/530/585/587) | Yes | Hooks are present (`plugin_app`, `plugin_prefs`, `prefs_changed` at `load.py:3363`, `3368`, `3492`). `plugin_prefs` returns the settings frame (`load.py:3480-3481`). UI uses `myNotebook` (`overlay_plugin/preferences.py:972`) and config helpers with locale-aware parsing via `number_from_string` (`overlay_plugin/preferences.py:23`, `216-223`). Keys are plugin-prefixed via `CONFIG_PREFIX`/`_config_key` (`overlay_plugin/preferences.py:45`, `117-118`). | N/A |
| Package dependencies and debug HTTP responsibly (PLUGINS.md:1323/1346/1358/1378/1387/1391) | Yes | Plugin directory is importable (`EDMCModernOverlay`) and installer/docs manage dedicated venvs for runtime dependencies (`scripts/install_linux.sh:2166-2176`, `scripts/install_windows.ps1:813-852`, `docs/FAQ.md` venv guidance section). HTTP debug routing honors `config.debug_senders` in `overlay_plugin/version_helper.py:26`, `168-183`. | N/A |

## Open Questions
- None currently.
