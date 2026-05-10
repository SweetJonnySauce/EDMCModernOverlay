from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LINUX_COLLECTOR = REPO_ROOT / "utils" / "collect_overlay_debug_linux.sh"
WINDOWS_COLLECTOR = REPO_ROOT / "utils" / "collect_overlay_debug_windows.ps1"
GNOME_HELPER_UUID = "edmc-modern-overlay-helper@edmcmodernoverlay.github.io"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_linux_collector_reports_gnome_wayland_helper_status(tmp_path: Path) -> None:
    fakebin = tmp_path / "bin"
    fakebin.mkdir()
    home_dir = tmp_path / "home"
    xdg_data_home = home_dir / ".local" / "share"
    helper_path = xdg_data_home / "gnome-shell" / "extensions" / GNOME_HELPER_UUID
    helper_path.mkdir(parents=True)

    _write_executable(
        fakebin / "gnome-shell",
        "#!/usr/bin/env bash\nprintf 'GNOME Shell 46.0\\n'\n",
    )
    _write_executable(
        fakebin / "gnome-extensions",
        f"""#!/usr/bin/env bash
if [[ "$1" == "info" && "$2" == "{GNOME_HELPER_UUID}" ]]; then
  cat <<'EOF'
{GNOME_HELPER_UUID}
  Name: EDMC Modern Overlay Helper
  Description: Test helper
  Path: {helper_path}
  Enabled: Yes
  State: ACTIVE
EOF
  exit 0
fi
exit 1
""",
    )
    _write_executable(
        fakebin / "gsettings",
        "#!/usr/bin/env bash\nprintf 'false\\n'\n",
    )
    _write_executable(
        fakebin / "gdbus",
        """#!/usr/bin/env bash
printf "('{\\"status\\":\\"healthy\\",\\"helper_kind\\":\\"gnome_shell_extension\\",\\"helper_version\\":\\"1.2.3\\",\\"helper_protocol\\":1,\\"capabilities\\":[\\"hello\\",\\"health\\"]}',)\\n"
""",
    )

    env = {
        **os.environ,
        "PATH": f"{fakebin}{os.pathsep}{os.environ.get('PATH', '')}",
        "HOME": str(home_dir),
        "XDG_DATA_HOME": str(xdg_data_home),
        "XDG_SESSION_TYPE": "wayland",
        "XDG_CURRENT_DESKTOP": "GNOME",
        "TERM": "dumb",
    }
    result = subprocess.run(
        ["bash", str(LINUX_COLLECTOR), "--log-lines", "0"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        input="",
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "=== GNOME Wayland Helper ===" in result.stdout
    assert "helper=gnome_shell_extension" in result.stdout
    assert "required=true" in result.stdout
    assert f"helper_uuid={GNOME_HELPER_UUID}" in result.stdout
    assert f"helper_install_path=~/.local/share/gnome-shell/extensions/{GNOME_HELPER_UUID}" in result.stdout
    assert "helper_installed=true" in result.stdout
    assert "helper_discovered=true" in result.stdout
    assert "helper_enabled=Yes" in result.stdout
    assert "helper_state=ACTIVE" in result.stdout
    assert "user_extensions_disabled=false" in result.stdout
    assert "dbus_health=healthy" in result.stdout
    assert "dbus_helper_kind=gnome_shell_extension" in result.stdout
    assert "dbus_helper_version=1.2.3" in result.stdout
    assert "dbus_helper_protocol=1" in result.stdout
    assert "dbus_helper_capabilities=hello,health" in result.stdout
    assert "gnome_helper_experimental=false" in result.stdout


def test_windows_collector_marks_gnome_helper_not_required_without_gnome_probes() -> None:
    content = WINDOWS_COLLECTOR.read_text(encoding="utf-8")

    assert "function Print-GnomeHelperStatus" in content
    assert 'Write-Output "state=not_required"' in content
    assert 'Write-Output "helper=gnome_shell_extension"' in content
    assert "gnome-extensions" not in content
    assert "gdbus call" not in content
