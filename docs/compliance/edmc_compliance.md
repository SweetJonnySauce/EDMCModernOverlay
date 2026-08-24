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
- Confirm the target Python series, tested patch floor, and architecture match EDMC core
  `docs/Releasing`; the 2026-08-02 upstream review records Python 3.13.9+ in the 3.13 series,
  32-bit Windows. This applies to the EDMC plugin runtime; the controller/client remain Python
  >= 3.10.
- Run `python3 scripts/check_edmc_python.py` to enforce the tested runtime in
  `docs/compliance/edmc_python_version.txt`. `ALLOW_EDMC_PYTHON_MISMATCH=1` is only an explicit
  non-release/development override.
  - CI exercises Python 3.10 compatibility and Python 3.13, with the override because hosted
    Linux runners are 64-bit and therefore cannot establish Windows release parity.
- Re-scan imports to ensure only supported EDMC APIs/helpers (`config`, `monitor`, `theme`, `timeout_session`, etc.) are used in plugin code.
- Verify logger wiring (`plugin_name`, folder name, logger name) aligns and that `logger.exception`/`exc_info` is used instead of `print`.
- Confirm long-running or network work runs in worker threads and that Tk widgets are only touched on the main thread.
- Review prefs/UI hooks (`plugin_prefs`, `prefs_changed`, `plugin_app`) for correct `myNotebook` usage and namespaced `config.get/set` keys.
- Validate dependency handling: venv for bundled packages, copied dependencies when needed, and debug HTTP routing via `config.debug_senders`.
- Monitor EDMC releases/discussions: subscribe to `EDCD/EDMarketConnector` GitHub Releases and Discussions; check weekly and before shipping a plugin release, logging any plugin-impacting changes here.
  - PRs must tick the compliance items in `.github/pull_request_template.md`.
- Check the `fix219` backend architecture boundary for overlay-client runtime work:
  - Generic follow/runtime surfaces such as `overlay_client/follow_surface.py`, `overlay_client/setup_surface.py`, and `overlay_client/platform_integration.py` must not import compositor-specific helper/presentation implementations directly.
  - Generic follow/runtime surfaces must not dispatch compositor-specific presentation behavior by checking raw backend/helper enums such as `BackendInstance.GNOME_SHELL_WAYLAND` or `HelperKind.GNOME_SHELL_EXTENSION`.
  - Compositor-specific runtime presentation, attachment, input policy, and helper-mediated behavior must be owned by backend bundle/consumer modules under `overlay_client/backend/`.
  - Backend helper message validation may remain in `overlay_client/backend/helper_ipc.py`; diagnostic, installer, and status surfaces may mention helpers when they are not making runtime presentation/follow decisions.
  - For GNOME helper work, run the project boundary/static tests when available, and manually inspect imports if those tests are missing.

## How to pass: Stay aligned with EDMC core
Use this evidence checklist for each release when deciding the `Stay aligned with EDMC core` status.

### Required evidence
- `python3 scripts/check_edmc_python.py` passes in a matching runtime, or the current work is
  explicitly non-release/development and records the mismatch plus override evidence.
- `load.py` exists at plugin root.
- `plugin_start3` exists in `load.py`.
- Plugin metadata maps to plugin folder naming (`name = PLUGIN_NAME` and `plugin_name = PLUGIN_NAME`).

### Suggested capture commands
- `python3 scripts/check_edmc_python.py`
- `test -f load.py && echo "load.py present"`
- `rg -n "def plugin_start3|name = PLUGIN_NAME|plugin_name = PLUGIN_NAME" load.py`

### Status rubric
- Mark `Yes` when required evidence is satisfied and any waived sub-requirement is explicitly recorded in `Exceptions`.
- Mark `No` when tested-runtime parity is falsely claimed, plugin entrypoint/structure evidence is
  missing, or a waived sub-requirement is not documented as an exception.

### Exception handling
- If a release intentionally waives EDMC Releases/Discussions logging or parity-environment artifacts, record that waiver in `Exceptions` with release scope and rationale.

## Exceptions
- 0.9.0 waiver: EDMC Releases/Discussions review findings log is not required for 0.9.0 release sign-off.

## Upstream monitoring evidence

### 2026-08-02 — fix219 remediation review

- Checked official EDMC `main` `.python-version`, `docs/Releasing.md`, `PLUGINS.md`, GitHub
  Releases, and public Discussions before the R6 project gates.
- Current source targets Python 3.13; `docs/Releasing.md` names 3.13.9 32-bit as the tested Windows
  runtime. Updated the repository baseline/check from the stale permissive 3.10.3 minimum.
- Latest stable release observed: 6.1.2 (published 2026-01-29). The 6.1 series adds the Plugin
  Browser/registration system, strengthens plugin versioning guidance, deprecates `util.gzip`,
  moves downloaded ship/module data expectations, and changes config persistence internals.
- Public Plugin Development discussions were reviewed. The two most recently updated entries were
  #2504 (Courier Mission Plugin, updated 2026-06-16) and #2506 (`system_url()` behavior, updated
  2026-06-08); neither adds a compositor, Tk ownership, socket, preferences-hook, or helper API
  requirement affecting this remediation.
- Follow-up: continue watching Releases and Discussions weekly and immediately before release;
  this dated review proves only the state checked above.

## Implementation Results — 2026-08-02 fix219 R6

### Detailed-design compliance gate

| Compliance item | Yes/No | Current evidence |
| --- | --- | --- |
| Current upstream tested EDMC Python/architecture baseline recorded | Yes | Official sources checked 2026-08-02; baseline is `3.13.9 32bit`; checker tests pass. |
| Own importable plugin directory and `load.py` | Yes | Directory is `EDMCModernOverlay` and root `load.py` exists. |
| `plugin_start3` entry point | Yes | `load.py` exports `plugin_start3`. |
| Dated EDMC release/discussion monitoring evidence | Yes | The dated evidence above records official sources, release 6.1.2, and current Plugin Development discussions. |
| Supported EDMC imports/helpers only | Yes | Plugin code uses documented `config`, `monitor`, `timeout_session`, logging, and UI surfaces; no unsupported EDMC-core import was found. |
| EDMC monitor helpers used for player state where applicable | Yes | `load.py` imports and uses `monitor.game_running` and `monitor.is_live_galaxy`. |
| `timeout_session`/EDMC user agent and debug routing for HTTP | Yes | `version_helper.py` prefers `timeout_session.new_session`, applies the EDMC user agent, and retains a bounded fallback. |
| Namespaced typed config and locale numeric parsing | Yes | Preferences use `edmc_modern_overlay.*`, typed getters, `config.set`, and `number_from_string`; the external client shadow file remains outside EDMC. |
| Logger name/exception handling and no operational `print` | Yes | Plugin logger is `EDMCModernOverlay`; operational plugin paths use logging with exception context. CLI progress output is confined to the standalone runner. |
| `config.appversion` gates real version differences | Yes | `version_helper.py` gates session/debug behavior using parsed `config.appversion`. |
| Long/network work absent from Tk hook path | Yes | Version checks use a worker; backend-status reads queue refresh and return cache/shadow immediately. Harness timing proves the silent-client path is non-blocking. |
| Tk access main-thread/shutdown safe | Yes | Preferences widgets are built/used by EDMC hooks; no worker touches Tk and no shutdown `event_generate` path was found. |
| Worker/process ownership and bounded joins | Yes | Lifecycle/socket tests cover bounded stop, pending wake, repeated stop, and teardown; the full harness suite passes. |
| No backend-private cleanup in `load.py` | Yes | Source contract test rejects GNOME private imports/constants/cleanup; launcher cleanup regressions pass. |
| Preferences hooks/`myNotebook`/widget returns correct | Yes | `plugin_prefs` constructs the `myNotebook` panel, returns its frame, and `prefs_changed` applies it; `plugin_app` intentionally has no main-window widget. |
| Dependencies tested and packaged from isolated environment | Yes | Validation ran in `overlay_client/.venv`; Linux installer/release-excludes tests pass in the full suite, and runtime requirements remain explicitly declared/vendored by scope. |
| Debug HTTP respects `config.debug_senders` | Yes | `_apply_debug_sender` reads EDMC `config.debug_senders`; focused logging/version tests pass. |

All 17 required results are Yes. The four known failures named by the detailed design are
resolved. This closes automated remediation only; it does not claim a matching Windows release
runtime or authorize the separate live pressure A/B.

### Repository compliance categories

| AGENTS.md category | Yes/No | Reason |
| --- | --- | --- |
| Stay aligned with EDMC core | Yes | Current tested runtime, plugin layout/entry point, and dated upstream monitoring are recorded and tested. |
| Use only supported plugin API and helpers | Yes | Supported monitor/config/session helpers, namespaced typed settings, and the external-client shadow boundary are preserved. |
| Adopt EDMC logging/versioning patterns | Yes | Plugin-name logger wiring, exception context, user agent, and real `config.appversion` gates pass their focused tests. |
| Keep runtime responsive and Tk-safe | Yes | Network work is off the Tk path; status reads are non-blocking; socket/worker shutdown is bounded and harness-tested. |
| Integrate prefs/UI hooks | Yes | `plugin_prefs`, `prefs_changed`, `myNotebook`, locale parsing, and frame-return behavior pass focused persistence/harness tests. |
| Package dependencies and debug HTTP responsibly | Yes | Isolated-environment full/install tests pass, runtime dependencies remain declared/vendored by scope, and debug sender routing is tested. |

### Exact validation evidence

- `overlay_client/.venv/bin/python -m pytest tests/test_check_edmc_python.py -q`: 9 passed.
- Compliance-focused pytest slice: 51 passed.
- `overlay_client/.venv/bin/python -m pytest -m harness -q` with localhost permission: 43 passed,
  6 skipped, 1,529 deselected.
- `QT_QPA_PLATFORM=offscreen make check PYTHON=overlay_client/.venv/bin/python`: Ruff passed,
  mypy passed 92 source files, and 1,595 tests passed.
- `QT_QPA_PLATFORM=offscreen make test PYTHON=overlay_client/.venv/bin/python`: 1,595 passed.
- Explicit full Ruff, mypy, compileall, runner help, and `git diff --check`: passed.
- Direct checker without override: expected failure on local Python 3.12.3/64-bit. Direct checker
  with `ALLOW_EDMC_PYTHON_MISMATCH=1`: explicit development warning and exit 0.
