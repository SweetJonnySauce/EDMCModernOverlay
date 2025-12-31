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
- Confirm target Python version matches the version stated in EDMC core `docs/Releasing`; baseline (as of this review) is Python 3.10.3 32-bit for Windows builds. Update this file if the baseline changes. This applies to the EDMC plugin runtime; the controller/client run in their own environments and require Python >= 3.10.
- Run `python scripts/check_edmc_python.py` to enforce the plugin baseline in `docs/compliance/edmc_python_version.txt` (override with `ALLOW_EDMC_PYTHON_MISMATCH=1` only for non-release/dev work).
  - CI runs this via `.github/workflows/ci.yml` (override enabled because CI uses non-baseline Python/arch).
- Re-scan imports to ensure only supported EDMC APIs/helpers (`config`, `monitor`, `theme`, `timeout_session`, etc.) are used in plugin code.
- Verify logger wiring (`plugin_name`, folder name, logger name) aligns and that `logger.exception`/`exc_info` is used instead of `print`.
- Confirm long-running or network work runs in worker threads and that Tk widgets are only touched on the main thread.
- Review prefs/UI hooks (`plugin_prefs`, `prefs_changed`, `plugin_app`) for correct `myNotebook` usage and namespaced `config.get/set` keys.
- Validate dependency handling: venv for bundled packages, copied dependencies when needed, and debug HTTP routing via `config.debug_senders`.
- Monitor EDMC releases/discussions: subscribe to `EDCD/EDMarketConnector` GitHub Releases and Discussions; check weekly and before shipping a plugin release, logging any plugin-impacting changes here.
  - PRs must tick the compliance items in `.github/pull_request_template.md`.

## Current compliance assessment

| Item | Status | Notes/Actions |
| --- | --- | --- |
| Stay aligned with EDMC core (PLUGINS.md:12/24/297/41) | Yes | Baseline pinned at `docs/compliance/edmc_python_version.txt` and enforced via `scripts/check_edmc_python.py`; plugin ships as `EDMCModernOverlay/` with `plugin_start3` entrypoint (load.py:2839); EDMC release/discussion review captured in `.github/pull_request_template.md`. Local run of `python3 scripts/check_edmc_python.py` in this review failed due to Python 3.12 64-bit (use the baseline or set `ALLOW_EDMC_PYTHON_MISMATCH=1` for dev). |
| Use only supported plugin API/helpers (PLUGINS.md:74/85/113/128/156/452) | Yes | Journal handling gates on `monitor.game_running()`/`monitor.is_live_galaxy()` (load.py:576-607); release checks create HTTP sessions via `timeout_session.new_session`/`config.user_agent` and respect `config.debug_senders` (overlay_plugin/version_helper.py:148-183); settings use namespaced keys with `overlay_settings.json` shadowing for the external client (overlay_plugin/preferences.py:18-95). |
| Logging/versioning patterns (PLUGINS.md:168/212/230/263) | Yes | Logger/tag `EDMCModernOverlay` matches the folder; plugin uses `logger.exception`/`exc_info` for tracebacks (load.py:589-592, load.py:2948-2996) and gates EDMC helper selection on `config.appversion` (overlay_plugin/version_helper.py:82-168). |
| Responsive & Tk-safe runtime (PLUGINS.md:335/349/362/397/599) | Yes | Long-running work runs on threads (prefs worker, watchdog, broadcaster, version check, config rebroadcast timers) and network I/O uses `requests` via helpers; Tk touches are limited to `plugin_prefs`/`prefs_changed` on the main thread (load.py:2839-2997). |
| Prefs/UI hooks (PLUGINS.md:417/452/455/530/585/587) | Yes | Preferences now read via EDMC config helpers with locale-aware parsing (`number_from_string`) and use namespaced keys; regression test covers comma-decimal config values (overlay_plugin/preferences.py:50-240, tests/test_preferences_persistence.py). |
| Dependencies & HTTP debug (PLUGINS.md:1323/1346/1358/1378/1387/1391) | Yes | Plugin folder is importable (`EDMCModernOverlay/`); installers build `overlay_client/.venv` from `overlay_client/requirements/*` and preserve it; HTTP debug routing honors `config.debug_senders` and `user_agent` plumbing (overlay_plugin/version_helper.py:148-191, scripts/install_linux.sh, scripts/install_windows.ps1). |

## Exceptions
- None noted for 0.7.6; plugin folder now matches `PLUGIN_NAME`.

## Key gaps to address (ordered by importance)
- **A. Prefs/UI config helpers**

  | Stage | Description | Status |
  | --- | --- | --- |
| 1 | Replace raw EDMC config access in `overlay_plugin/preferences.py` with `config.get_int/str/bool/list` and apply `number_from_string` for locale-aware numeric fields (font bounds, grid spacing, gutters) so preferences parsing follows PLUGINS.md. | Complete |

## Remediation plan

### A. Prefs/UI config helpers
- Scope: `overlay_plugin/preferences.py` config access and numeric parsing for font bounds, grid spacing, and gutters.

| Step | Action | Output |
| --- | --- | --- |
| 1 | Inventory all config reads/writes and numeric fields; map each to the correct `config.get_*` type and identify locale-sensitive fields (font min/max, gridline spacing, status/payload gutters). | Checklist of keys, types, and parsing rules. |
| 2 | Replace raw `EDMC_CONFIG.get/set` access with EDMC `config.get_int/str/bool/list` and `config.set` helpers; apply `number_from_string` before numeric casts for locale-aware fields. | Updated config helper layer and parsing logic. |
| 3 | Add/adjust tests or manual verification notes to cover locale decimal inputs and confirm defaults remain unchanged. | Test notes or new tests documenting expected parsing. |
| 4 | Update `docs/refactoring/_template.md` to call out EDMC config helper usage and locale-aware numeric parsing when touching preferences/config code. | Template updated with EDMC config guidance. |
| 5 | Re-run compliance checks and update this file with the new status. | Compliance table updated to Yes. |

#### Step 1 inventory results
| Config key | Current type | Proposed helper | Locale-sensitive | Parsing/constraints |
| --- | --- | --- | --- | --- |
| `edmc_modern_overlay.state_version` | int | `config.get_int` | No | `>= 1` |
| `edmc_modern_overlay.overlay_opacity` | float | `config.get_str` + `number_from_string` | No | clamp `0.0-1.0` |
| `edmc_modern_overlay.global_payload_opacity` | int | `config.get_int` | No | clamp `0-100` |
| `edmc_modern_overlay.show_connection_status` | bool | `config.get_bool` | No | none |
| `edmc_modern_overlay.debug_overlay_corner` | str | `config.get_str` | No | allowed `NW/NE/SW/SE` |
| `edmc_modern_overlay.client_log_retention` | int | `config.get_int` | No | clamp `>= 1` |
| `edmc_modern_overlay.gridlines_enabled` | bool | `config.get_bool` | No | none |
| `edmc_modern_overlay.gridline_spacing` | int | `config.get_str` + `number_from_string` | Yes | clamp `>= 10` |
| `edmc_modern_overlay.force_render` | bool | `config.get_bool` | No | none |
| `edmc_modern_overlay.force_xwayland` | bool | `config.get_bool` | No | none |
| `edmc_modern_overlay.physical_clamp_enabled` | bool | `config.get_bool` | No | none |
| `edmc_modern_overlay.physical_clamp_overrides` | JSON string | `config.get_str` | No | JSON -> `Dict[str, float]` |
| `edmc_modern_overlay.show_debug_overlay` | bool | `config.get_bool` | No | none |
| `edmc_modern_overlay.min_font_point` | float | `config.get_str` + `number_from_string` | Yes | clamp `FONT_BOUND_MIN-FONT_BOUND_MAX` |
| `edmc_modern_overlay.max_font_point` | float | `config.get_str` + `number_from_string` | Yes | clamp `min_font_point-FONT_BOUND_MAX` |
| `edmc_modern_overlay.legacy_font_step` | int | `config.get_int` | No | clamp `FONT_STEP_MIN-FONT_STEP_MAX` |
| `edmc_modern_overlay.title_bar_enabled` | bool | `config.get_bool` | No | none |
| `edmc_modern_overlay.title_bar_height` | int | `config.get_int` | No | clamp `>= 0` |
| `edmc_modern_overlay.cycle_payload_ids` | bool | `config.get_bool` | No | none |
| `edmc_modern_overlay.copy_payload_id_on_cycle` | bool | `config.get_bool` | No | none |
| `edmc_modern_overlay.scale_mode` | str | `config.get_str` | No | allowed `fit/fill` |
| `edmc_modern_overlay.nudge_overflow_payloads` | bool | `config.get_bool` | No | none |
| `edmc_modern_overlay.payload_nudge_gutter` | int | `config.get_str` + `number_from_string` | Yes | clamp `0-500` |
| `edmc_modern_overlay.status_message_gutter` | int | `config.get_str` + `number_from_string` | Yes | clamp `0-STATUS_GUTTER_MAX` |
| `edmc_modern_overlay.log_payloads` | bool | `config.get_bool` | No | none |
| `edmc_modern_overlay.payload_log_delay_seconds` | float | `config.get_str` + `number_from_string` | No | clamp `>= 0.0` |
| `edmc_modern_overlay.controller_launch_command` | str | `config.get_str` | No | normalise via `_normalise_launch_command` |

#### Step 2 implementation notes
- `overlay_plugin/preferences.py` now routes config reads through `config.get_int/str/bool/list` helpers with fallbacks for non-EDMC environments.
- Locale-aware numeric reads (font bounds, grid spacing, gutters, overlay opacity, payload log delay) now use `number_from_string` before coercion.

#### Step 3 implementation notes
- Added a locale parsing regression test in `tests/test_preferences_persistence.py` that feeds comma-decimal values through config and verifies a non-numeric value falls back to the default.

#### Step 4 implementation notes
- Updated `docs/refactoring/_template.md` to require EDMC config helpers and locale-aware numeric parsing when preferences/config code is touched.

#### Step 5 implementation notes
- Compliance table updated to reflect the prefs/config helper remediation; review performed by code inspection and test additions (no automated test run logged here).
