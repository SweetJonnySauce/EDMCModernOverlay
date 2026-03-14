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
- None
