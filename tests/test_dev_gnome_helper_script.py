from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "dev_gnome_helper.sh"
HELPER_UUID = "edmc-modern-overlay-helper@edmcmodernoverlay.github.io"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _fake_env(tmp_path: Path) -> tuple[dict[str, str], Path]:
    fakebin = tmp_path / "bin"
    fakebin.mkdir()
    home = tmp_path / "home"
    xdg_data_home = home / ".local" / "share"
    extension_base = xdg_data_home / "gnome-shell" / "extensions"
    log_path = tmp_path / "gnome-extensions.log"

    _write_executable(
        fakebin / "gnome-extensions",
        f"""#!/usr/bin/env bash
set -euo pipefail
case "${{1:-}}" in
  info)
    if [[ "${{FAKE_GNOME_EXTENSIONS_INFO_FAIL:-0}}" == "1" ]]; then
      exit 1
    fi
    if [[ "${{2:-}}" == "{HELPER_UUID}" && -d "$FAKE_EXTENSION_BASE/{HELPER_UUID}" ]]; then
      cat <<EOF
{HELPER_UUID}
  Name: EDMC Modern Overlay Helper
  Path: $FAKE_EXTENSION_BASE/{HELPER_UUID}
  Enabled: ${{FAKE_GNOME_EXTENSIONS_ENABLED:-Yes}}
  State: ${{FAKE_GNOME_EXTENSIONS_STATE:-ACTIVE}}
EOF
      exit 0
    fi
    exit 1
    ;;
  enable|disable)
    printf '%s %s\\n' "$1" "${{2:-}}" >> "$FAKE_GNOME_EXTENSIONS_LOG"
    exit 0
    ;;
esac
exit 1
""",
    )
    _write_executable(
        fakebin / "gsettings",
        "#!/usr/bin/env bash\nprintf 'false\\n'\n",
    )
    _write_executable(
        fakebin / "gdbus",
        "#!/usr/bin/env bash\nprintf \"('{\\\"status\\\":\\\"healthy\\\"}',)\\n\"\n",
    )
    _write_executable(
        fakebin / "gjs",
        "#!/usr/bin/env bash\nexit 0\n",
    )

    env = {
        **os.environ,
        "PATH": f"{fakebin}{os.pathsep}{os.environ.get('PATH', '')}",
        "HOME": str(home),
        "XDG_DATA_HOME": str(xdg_data_home),
        "MODERN_OVERLAY_GNOME_HELPER_EXTENSION_BASE": str(extension_base),
        "SNAP": "",
        "SNAP_REAL_HOME": "",
        "XDG_SESSION_TYPE": "wayland",
        "XDG_CURRENT_DESKTOP": "GNOME",
        "DBUS_SESSION_BUS_ADDRESS": "unix:path=/tmp/fake-session-bus",
        "FAKE_EXTENSION_BASE": str(extension_base),
        "FAKE_GNOME_EXTENSIONS_LOG": str(log_path),
        "TERM": "dumb",
    }
    return env, log_path


def test_dev_gnome_helper_script_has_valid_shell_syntax() -> None:
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_dev_gnome_helper_install_copies_source_and_enables(tmp_path: Path) -> None:
    env, log_path = _fake_env(tmp_path)
    result = subprocess.run(
        ["bash", str(SCRIPT), "install", "--yes"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    install_dir = Path(env["XDG_DATA_HOME"]) / "gnome-shell" / "extensions" / HELPER_UUID
    assert (install_dir / "metadata.json").is_file()
    assert (install_dir / "extension.js").is_file()
    assert f"enable {HELPER_UUID}" in log_path.read_text(encoding="utf-8")
    assert "Log out and log back in" in result.stdout


def test_dev_gnome_helper_uninstall_removes_only_helper_directory(tmp_path: Path) -> None:
    env, log_path = _fake_env(tmp_path)
    base_dir = Path(env["XDG_DATA_HOME"]) / "gnome-shell" / "extensions"
    helper_dir = base_dir / HELPER_UUID
    other_dir = base_dir / "other-extension@example.test"
    helper_dir.mkdir(parents=True)
    other_dir.mkdir()
    (helper_dir / "metadata.json").write_text("{}", encoding="utf-8")
    (other_dir / "metadata.json").write_text("{}", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SCRIPT), "uninstall", "--yes"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert not helper_dir.exists()
    assert other_dir.exists()
    assert f"disable {HELPER_UUID}" in log_path.read_text(encoding="utf-8")


def test_dev_gnome_helper_status_reports_missing_helper(tmp_path: Path) -> None:
    env, _log_path = _fake_env(tmp_path)
    result = subprocess.run(
        ["bash", str(SCRIPT), "status"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "Files installed: false" in result.stdout
    assert "Extension state: not_discovered" in result.stdout


def test_dev_gnome_helper_status_explains_installed_but_not_discovered(tmp_path: Path) -> None:
    env, _log_path = _fake_env(tmp_path)
    env["FAKE_GNOME_EXTENSIONS_INFO_FAIL"] = "1"
    install_dir = Path(env["XDG_DATA_HOME"]) / "gnome-shell" / "extensions" / HELPER_UUID
    install_dir.mkdir(parents=True)
    (install_dir / "metadata.json").write_text("{}", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SCRIPT), "status"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "Files installed: true" in result.stdout
    assert "Extension state: not_discovered" in result.stdout
    assert "GNOME Shell has not discovered the helper yet" in result.stdout
    assert "Log out and log back in" in result.stdout


def test_dev_gnome_helper_status_reports_disabled_without_dbus_probe(tmp_path: Path) -> None:
    env, _log_path = _fake_env(tmp_path)
    env["FAKE_GNOME_EXTENSIONS_ENABLED"] = "No"
    env["FAKE_GNOME_EXTENSIONS_STATE"] = "INITIALIZED"
    install_dir = Path(env["XDG_DATA_HOME"]) / "gnome-shell" / "extensions" / HELPER_UUID
    install_dir.mkdir(parents=True)
    (install_dir / "metadata.json").write_text("{}", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SCRIPT), "status"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "Enabled: No" in result.stdout
    assert "State: INITIALIZED" in result.stdout
    assert "Helper state: disabled" in result.stdout
    assert "dev_gnome_helper.sh enable" in result.stdout
    assert "DBus health:" not in result.stdout


def test_dev_gnome_helper_enable_action_enables_discovered_helper(tmp_path: Path) -> None:
    env, log_path = _fake_env(tmp_path)
    env["FAKE_GNOME_EXTENSIONS_ENABLED"] = "No"
    env["FAKE_GNOME_EXTENSIONS_STATE"] = "INITIALIZED"
    install_dir = Path(env["XDG_DATA_HOME"]) / "gnome-shell" / "extensions" / HELPER_UUID
    install_dir.mkdir(parents=True)
    (install_dir / "metadata.json").write_text("{}", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SCRIPT), "enable", "--yes"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert f"enable {HELPER_UUID}" in log_path.read_text(encoding="utf-8")
    assert "GNOME helper enable requested" in result.stdout


def test_dev_gnome_helper_enable_reports_immediate_active_health(tmp_path: Path) -> None:
    env, _log_path = _fake_env(tmp_path)
    install_dir = Path(env["XDG_DATA_HOME"]) / "gnome-shell" / "extensions" / HELPER_UUID
    install_dir.mkdir(parents=True)
    (install_dir / "metadata.json").write_text("{}", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SCRIPT), "enable", "--yes"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "GNOME helper is ACTIVE and DBus health responded" in result.stdout
    assert "Logout/login is not required for this enable step" in result.stdout
    assert "Log out and log back in" not in result.stdout


def test_dev_gnome_helper_uses_snap_real_home_for_extension_base(tmp_path: Path) -> None:
    env, _log_path = _fake_env(tmp_path)
    real_home = tmp_path / "real-home"
    snap_home = tmp_path / "snap" / "code" / "237"
    real_extension_base = real_home / ".local" / "share" / "gnome-shell" / "extensions"
    env.update(
        {
            "HOME": str(snap_home),
            "XDG_DATA_HOME": str(snap_home / ".local" / "share"),
            "MODERN_OVERLAY_GNOME_HELPER_EXTENSION_BASE": "",
            "SNAP": "/snap/code/237",
            "SNAP_REAL_HOME": str(real_home),
            "FAKE_EXTENSION_BASE": str(real_extension_base),
        }
    )

    result = subprocess.run(
        ["bash", str(SCRIPT), "install", "--yes"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert (real_extension_base / HELPER_UUID / "metadata.json").is_file()
    assert not (Path(env["XDG_DATA_HOME"]) / "gnome-shell" / "extensions" / HELPER_UUID).exists()


def test_dev_gnome_helper_uses_account_home_when_snap_real_home_missing(tmp_path: Path) -> None:
    env, _log_path = _fake_env(tmp_path)
    fakebin = Path(env["PATH"].split(os.pathsep, 1)[0])
    real_home = tmp_path / "passwd-home"
    snap_home = tmp_path / "snap" / "code" / "237"
    real_extension_base = real_home / ".local" / "share" / "gnome-shell" / "extensions"
    _write_executable(
        fakebin / "id",
        "#!/usr/bin/env bash\nif [[ \"${1:-}\" == \"-un\" ]]; then printf 'devuser\\n'; else /usr/bin/id \"$@\"; fi\n",
    )
    _write_executable(
        fakebin / "getent",
        f"#!/usr/bin/env bash\nif [[ \"${{1:-}}\" == \"passwd\" ]]; then printf 'devuser:x:1000:1000:Dev User:{real_home}:/bin/bash\\n'; fi\n",
    )
    env.update(
        {
            "HOME": str(snap_home),
            "XDG_DATA_HOME": str(snap_home / ".local" / "share"),
            "MODERN_OVERLAY_GNOME_HELPER_EXTENSION_BASE": "",
            "SNAP": "/snap/code/237",
            "SNAP_REAL_HOME": "",
            "FAKE_EXTENSION_BASE": str(real_extension_base),
        }
    )

    result = subprocess.run(
        ["bash", str(SCRIPT), "install", "--yes"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert (real_extension_base / HELPER_UUID / "metadata.json").is_file()
    assert str(snap_home) not in result.stdout
