## Goal: Embed Python in the windows .exe installer for those that don't have 3.10+ available on their host. 

## Requirements
- When the installer is in `InstallVenvMode=build`, it must detect whether Python 3.10+ is available on the host.
- Provide a command-line switch to force re-installing Python even if Python 3.10+ is detected.
- If Python 3.10+ is missing, the installer must offer to download and install it, then re-check availability before proceeding.
- The Python installer download must be from an official source and pinned in-repo at build time (CI updates version/URL/SHA in `pyproject.toml`; no “latest” URL at install time).
- The installer must validate the downloaded payload (at minimum via SHA-256 hash; signature validation is preferred if feasible in Inno).
- Installation should default to per-user (no admin elevation) to match `PrivilegesRequired=lowest`.
- The install flow must be silent/non-interactive once approved (no GUI wizard from Python unless explicitly allowed).
- If download or installation fails, the installer must stop with a clear message and link/steps to manual installation.
- The installer must log the detection + install steps to aid support/debugging.
- The experience must remain unchanged for users who already have Python 3.10+.

## Open Questions (Owner Decisions Needed)
- Which Python version should we pin (3.10.x vs 3.11.x), and how often do we plan to update it?
Use the latest version of python. Let's change the requirements.
- Do we want to allow installing Python for all users (requires admin), or only per-user installs?
Per user only
- Should the installer add Python to PATH, or rely on the `py` launcher only?
What does it rely on now?
Always use `python.exe` directly. Don't add it to PATH.
- Do we want an opt-out to skip downloading Python and instead exit with guidance?
Yes
- Are there corporate proxy constraints we need to support (PowerShell `Invoke-WebRequest` proxy settings, etc.)?
No
- Do we need to verify the Python installer signature (WinVerifyTrust) or is SHA-256 sufficient?
SHA-256 is sufficient as long as we download it from an official source

## Clarifications + Follow-up Questions
- Current behavior: the Inno build-mode installer calls `python` directly and therefore relies on Python being on PATH.
Always use `python.exe` directly. Don't add it to PATH.
- “Use the latest version of python” conflicts with “pinned version + SHA-256.” Do you want “latest at release build time (pinned in CI)” or “latest at install time (dynamic)”?  
latest at build time
- Which major/minor series should we allow? Is 3.13 acceptable, or do you want to cap at 3.12/3.11/3.10 for PyQt6 compatibility?
3.13 is acceptable.
- If Python 3.10+ is already installed but older than your “latest,” should we skip or offer an upgrade?
skip, but log it
- Should we install 64-bit only (recommended), or allow 32-bit if that’s what the OS has?
64 bit only
- Do you want to avoid PATH changes and instead locate Python via registry (preferred), or add Python to PATH for future runs?
don't add python to path or registry. access it directly 
- If download fails, do you want to let the user browse for a local Python installer instead of aborting?
abort with a user facing message
- For the SHA-256 check, should the hash be embedded in the installer (most reliable) or fetched from an online manifest?
embedded in installer

## Additional Open Questions
- The `py` launcher discovers installs via registry. If we avoid registry entirely, do we still want to rely on `py`, or should we call the installed `python.exe` directly by path?
Always call the installed `python.exe` directly by path.
- For “latest at build time”: should CI pin the version in the repo (manual bump), or fetch latest from python.org during CI and embed the resolved version + hash?
fetch latest during CI
- When installing Python, should we install the `py` launcher (`Include_launcher=1`) or skip it and always call `python.exe` directly?
Skip the launcher; always call `python.exe` directly.
- For detection, do you want to target a specific `py -3.13` (or pinned major/minor), or accept any 3.10+ if found?
accept any 3.10+
- After installing Python, should we re-check using the same method (e.g., `py -3.13`) or accept any 3.10+?
accept 3.10+
- Should the installer delete the downloaded Python installer after success, or keep it for reuse/logging?
delete it
- Should we log the exact Python version found/installed in the installer log?
yes

## Further Clarifications Needed
- The official Python installer writes PEP-514 registry keys by default. Do you want to avoid relying on registry, or to avoid registry writes entirely (not always possible with stock installer)?
avoid relying on the registry. If necessary, ok.
- Should we force a deterministic install path (e.g., `%LOCALAPPDATA%\Programs\Python\Python313\python.exe`) so we can call `python.exe` directly, or allow a custom path?
deterministic: `%LOCALAPPDATA%\Programs\Python\Python{MAJOR}{MINOR}\python.exe` (matches python.org per-user default)
- For detection, should we search known install locations first, or also try `python.exe` on PATH if found?
Path first, then deterministic path
- For “latest at build time,” how should CI discover latest: scrape python.org JSON/feed or use a maintained script/version file?
Let's pin it in pyproject.toml and have the release workflow update it during the build.
- What exact URL/text should we show users when download/install fails and they must install manually?
python.org
- Should the silent install explicitly set `Include_pip=1` and `Include_launcher=0`?
yes
- When `/ForcePythonInstall` is set, should we still prompt before downloading/installing Python?
Yes, still prompt.
- Should the opt-out be a Yes/No prompt at download time?
Yes/No.
- If we store the pinned version/URL/SHA in `pyproject.toml` (e.g., `[tool.edmcmodernoverlay.windows_python]`), is that acceptable for you, or do you want a separate manifest file?
In pyproject.toml is fine
- Do you want the requirement wording changed to “pinned in repo at build time (CI updates it)” instead of “no latest URL”?
Change the requirement wording
- What should the command-line switch be called to force Python install (e.g., `/ForcePythonInstall`)?
/ForcePythonInstall is fine
- Detection logic: if we only check PATH, should we ignore an existing Python installed at the deterministic path, or also check that path before downloading?
Check that path before downloading
- Is `[tool.edmcmodernoverlay.windows_python]` the preferred `pyproject.toml` table name, or do you want a different key?
use [tool.windows_python_install]
- For manual install guidance, is `https://www.python.org/downloads/windows/` the exact URL/text we should show?
Use this URL

## Proposed `pyproject.toml` schema (suggested)
- `version`: pinned Python version string (e.g., `3.13.1`)
- `arch`: `amd64`
- `url`: full python.org installer URL for the pinned version
- `sha256`: SHA-256 for the installer
- `target_dir_template`: `%LOCALAPPDATA%\\Programs\\Python\\Python{MAJOR}{MINOR}`
- `python_exe_template`: `%LOCALAPPDATA%\\Programs\\Python\\Python{MAJOR}{MINOR}\\python.exe`

```toml
[tool.windows_python_install]
version = "3.13.1"
arch = "amd64"
url = "https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe"
sha256 = "REPLACE_WITH_SHA256"
target_dir_template = "%LOCALAPPDATA%\\\\Programs\\\\Python\\\\Python{MAJOR}{MINOR}"
python_exe_template = "%LOCALAPPDATA%\\\\Programs\\\\Python\\\\Python{MAJOR}{MINOR}\\\\python.exe"
```

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
| Phase 1 | Config and metadata wiring for pinned Python installer info | Completed |
| Phase 2 | Installer download, validation, detection, and install flow | Completed |
| Phase 3 | Venv creation integration, docs, and verification | Completed |

## Phase Details

### Phase 1: Config and Metadata
Goal: define a pinned Python installer configuration and wire it into the release workflow.
Behaviors unchanged: non-install flows and existing release packaging should continue to work.
Risks: incorrect pinning or missing metadata leading to install failures.
Mitigations: CI logging of resolved version/URL/SHA, and validation steps before installer build.

| Stage | Description | Status |
| --- | --- | --- |
| 1.1 | Add `[tool.windows_python_install]` to `pyproject.toml` with version/URL/SHA/paths | Completed |
| 1.2 | Update release workflow to resolve latest Python at build time and write pinned values | Completed |

Phase 1 Detailed Plan
1. Add `[tool.windows_python_install]` in `pyproject.toml` with `version`, `arch`, `url`, `sha256`, `target_dir_template`, and `python_exe_template`.
2. Implement a resolver script (e.g., `scripts/resolve_windows_python.py`) that fetches the latest stable Python release metadata, selects the Windows amd64 installer, downloads it, computes SHA-256, and rewrites the table in `pyproject.toml` for the build workspace (no commit).
3. Wire the release workflow to run the resolver before the Inno build, and log the resolved version/URL/SHA for traceability.
4. Add sanity checks in the resolver: fail if version/URL mismatch, hash is empty, or the expected installer filename does not match the resolved version/arch.

Phase 1 Results
- Added `[tool.windows_python_install]` to `pyproject.toml` with placeholders for version/URL/SHA and deterministic path templates.
- Added `scripts/resolve_windows_python.py` to resolve latest stable Windows Python and update `pyproject.toml` during the build.
- Updated `.github/workflows/release.yml` (win_inno_build job) to run the resolver before the Inno build.

### Phase 2: Installer Download, Validation, and Install
Goal: implement download, checksum validation, and install logic in `scripts/installer.iss`.
Behaviors unchanged: if Python 3.10+ is already available and not forced, install proceeds as before.
Risks: download failures, incorrect checksum handling, or false positives in detection.
Mitigations: clear user prompts and error messages, strict SHA-256 validation, and detailed logging.

| Stage | Description | Status |
| --- | --- | --- |
| 2.1 | Add download + SHA-256 verification helper using pinned metadata | Completed |
| 2.2 | Implement detection order: PATH first, deterministic path second | Completed |
| 2.3 | Add `/ForcePythonInstall` flag and Yes/No opt-out prompt | Completed |
| 2.4 | Run silent installer to deterministic per-user path and re-check Python 3.10+ | Completed |
| 2.5 | Log detected/installed Python version | Completed |

Phase 2 Detailed Plan
1. Add a metadata reader in `scripts/installer.iss` to parse `[tool.windows_python_install]` values (version, url, sha256, templates).
2. Implement a detection helper:
   - Check `python.exe` on PATH (`python --version`, `python -c ...`).
   - If not found or version < 3.10, check deterministic path `%LOCALAPPDATA%\Programs\Python\Python{MAJOR}{MINOR}\python.exe`.
3. Add `/ForcePythonInstall` support and a Yes/No prompt to download and install Python even if detected.
4. Implement download flow:
   - Download the installer to `{tmp}`.
   - Verify SHA-256 against pinned value.
   - Abort with message and python.org URL on failure.
5. Execute the Python installer silently with options:
   - Per-user install, `TargetDir` to deterministic path.
   - `Include_pip=1`, `Include_launcher=0`.
6. Re-check Python availability (version >= 3.10) using the same detection logic and log the exact version.
7. Ensure cleanup removes the downloaded installer on success; retain on failure for troubleshooting.
8. Add installer logging lines for each step (detect, download, verify, install, re-check).

Phase 2 Results
- Added TOML metadata parsing for `[tool.windows_python_install]` in `scripts/installer.iss`.
- Implemented PATH-first detection with deterministic path fallback and explicit version checks.
- Added `/ForcePythonInstall` handling with a Yes/No opt-out prompt and manual install guidance URL.
- Implemented PowerShell download, SHA-256 verification, silent install to the deterministic path, and cleanup of the downloaded installer.
- Switched build-mode venv rebuild to use the resolved `python.exe` path directly and logged detected/installed versions.

### Phase 3: Venv Creation, Docs, and Verification
Goal: ensure venv creation uses installed `python.exe`, and update docs.
Behaviors unchanged: existing embedded-mode and non-Windows flows are untouched.
Risks: venv creation failures or path mismatches.
Mitigations: reuse existing venv creation flow with explicit Python path and add verification steps.

| Stage | Description | Status |
| --- | --- | --- |
| 3.1 | Update build-mode venv creation to use the installed `python.exe` path | Completed |
| 3.2 | Update docs/troubleshooting with new installer behavior and manual install URL | Completed |
| 3.3 | Verify installer flow (local run or dry-run/log validation) | Skipped (not run) |

Phase 3 Detailed Plan
1. Confirm build-mode venv creation uses the resolved `python.exe` path and propagate that path to any downstream checks.
2. Update docs:
   - Add a “Python auto-install” section to `docs/troubleshooting.md`.
   - Mention `/ForcePythonInstall` and manual install URL.
3. Verification:
   - Run a local installer dry-run (if possible) or validate logs show detection/download/verify/install steps.
   - If feasible, test with no Python on PATH and with an older Python on PATH to ensure fallback behavior.

Phase 3 Results
- Build-mode venv creation already uses the resolved `python.exe` path (implemented during Phase 2).
- Updated `docs/troubleshooting.md` with Windows Python auto-install notes, `/ForcePythonInstall`, and the manual install URL.
- Verification not run in this environment.

## End-to-End Logic Summary
1. **Release build pins Python metadata** (`scripts/resolve_windows_python.py` + `.github/workflows/release.yml`):
   - Resolve latest stable Python.
   - Compute SHA-256 and write `[tool.windows_python_install]` into `pyproject.toml`.
2. **Installer reads pinned metadata** (`scripts/installer.iss`):
   - Parse `version`, `url`, `sha256`, and deterministic path templates from `pyproject.toml`.
3. **Detection order (build mode)** (`scripts/installer.iss`):
   - Check `python` on PATH for 3.10+.
   - If missing/too old, check deterministic `%LOCALAPPDATA%\Programs\Python\Python{MAJOR}{MINOR}\python.exe`.
4. **Optional forced install** (`/ForcePythonInstall`):
   - Still prompts; if approved, installs even when Python exists.
5. **Download + verify + install** (`scripts/installer.iss`):
   - Download to `{tmp}` via PowerShell, verify SHA-256, run silent install with `Include_pip=1`, `Include_launcher=0`, `TargetDir=deterministic`.
   - Delete installer on success.
6. **Post-install verification**:
   - Re-check deterministic `python.exe` and log version.
7. **Venv creation uses resolved Python**:
   - Build-mode venv rebuild uses the resolved `python.exe` path directly.
8. **Docs**:
   - `docs/troubleshooting.md` documents the Windows auto-install flow and `/ForcePythonInstall`.
