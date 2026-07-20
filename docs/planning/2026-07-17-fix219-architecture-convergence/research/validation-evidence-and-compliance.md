# Validation Evidence, Diagnostics, and EDMC Compliance

## Evidence workflow

Keep policy and accumulated evidence as version-controlled documentation, not mutable runtime truth. Recommended artifacts under `docs/support/` in the eventual design:

- a machine-readable support/evidence matrix (JSON or YAML) reviewed with code;
- a generated/public Markdown matrix and terminology guide;
- a structured success/failure report template;
- safe collector instructions and privacy statement;
- release-specific validation records linking environment, versions, result, issue/report reference, and review date.

Runtime status embeds the matching policy/evidence record ID and project release, while current health comes from live probes. Community reports should be triaged into success, reproducible failure, mixed evidence, or insufficient evidence through a reviewed change. Reports never silently change support policy.

## Collector extension

`utils/collect_overlay_debug_linux.sh` already reports a bounded environment allowlist, dependency availability, GNOME helper installation/health, settings, and optional recent logs; tests cover its helper parsing and Windows not-required behavior.

Add one redacted versioned backend report obtained from the client control plane, containing:

- support policy/evidence key and selected runtime identity;
- normalized operational probes and failure codes;
- helper protocol compatibility and non-secret ownership state;
- EDMC owner/client/backend lifecycle events;
- active presenter/transition summary;
- bounded recent normalized failures and performance summary when diagnostics are enabled.

Do not add screenshots, general process/window enumeration, command lines, unrelated titles, tokens, raw ownership IDs, broad environment dumps, or absolute personal paths. The collector must write a reviewable local artifact before the user shares it.

## Current EDMC compliance review

This is research evidence for the design gate, not final release certification. Upstream `docs/Releasing.md` currently specifies 32-bit Python 3.13 for Windows and identifies 3.13.9 as the tested version. The repository baseline `docs/compliance/edmc_python_version.txt` still says `3.10.3 32bit`, so its check is stale.

| Compliance item | Yes/No | Evidence and required change |
|---|---|---|
| Current tested EDMC Python baseline recorded | **No** | Upstream now documents Python 3.13/3.13.9 32-bit; update the compliance baseline/check and test compatibility before release. |
| Own importable plugin directory with `load.py` | **Yes** | `EDMCModernOverlay/load.py`; directory name is importable. |
| `plugin_start3` entry point | **Yes** | `load.py` defines `plugin_start3`. |
| Release/discussion monitoring demonstrated | **No** | The repository instruction says to monitor weekly/before release, but no dated monitoring log was found; add release evidence. |
| Imports limited to supported EDMC APIs | **Yes, with release re-scan required** | Plugin-facing code uses documented config/UI/logging helpers; no contrary core import was found in this focused scan. Preserve a mechanical import audit gate. |
| Player-state detection uses EDMC monitor helpers | **Yes / not applicable** | No replacement game-running/live-galaxy detection was found in the touched backend paths. |
| HTTP uses `timeout_session` or EDMC user agent | **Yes** | `overlay_plugin/version_helper.py` prefers `timeout_session.new_session` and applies debug routing/fallback handling. |
| Namespaced typed config helpers and locale numeric parsing | **Yes** | Preferences use namespaced wrappers over typed getters/setters and locale-aware helpers. Re-scan any convergence edits. |
| EDMC logger naming and no operational `print` | **Yes** | `load.py` uses the plugin logger and exception logging; print-like hits are in tools/scripts, not normal plugin hooks. |
| Version-specific behavior gated with `config.appversion` where needed | **Yes / no current conditional need** | No convergence behavior currently branches on unsupported inferred versions; add gating only if a real core-version difference appears. |
| Long/network work off Tk main thread | **No** | `get_backend_status()` can synchronously wait on a `threading.Event` for a client response; when called from preferences this may block Tk. Redesign status retrieval as cached/asynchronous. Startup broadcaster readiness also blocks up to five seconds and should be assessed in final hook responsiveness tests. |
| Tk access confined to main thread and shutdown-safe | **Yes, with harness verification required** | UI construction/update paths are main-thread oriented; no background `event_generate` path was found here. Preserve shutdown tests. |
| Plugin lifecycle owns and joins workers | **Yes, but architecture violation remains** | Watchdog/server/workers have bounded stop paths. However, `load.py` directly performs GNOME raster startup/stop cleanup; convergence must remove this private backend behavior. |
| Preferences/UI use `plugin_prefs`, `prefs_changed`, `myNotebook`, and return widgets | **Yes** | Required hooks and notebook-backed panel exist. |
| Dependencies developed/tested in isolated environments and bundled appropriately | **Partial / release evidence missing** | Plugin and client requirements/venv guidance exist, but final packaged dependency/import verification remains a release gate. |
| Debug HTTP respects `config.debug_senders` | **Yes** | Version helper contains explicit debug-webserver routing. |

## Compliance design consequences

- Update the Python compliance source of truth from upstream before implementation begins and avoid retaining the obsolete “minimum >=3.10.3” interpretation for the EDMC plugin runtime.
- Convert client status refresh to push/cached state or a worker-mediated request; Tk callbacks must not synchronously wait on the network path.
- Remove GNOME imports and cleanup from `load.py`; add harness tests proving backend-neutral start/stop.
- Run the final yes/no table again against the implementation and attach exact commands/results as release evidence.

## Sources

- [EDMC plugin documentation](https://github.com/EDCD/EDMarketConnector/blob/main/PLUGINS.md)
- [EDMC release environment](https://github.com/EDCD/EDMarketConnector/blob/main/docs/Releasing.md#environment)
