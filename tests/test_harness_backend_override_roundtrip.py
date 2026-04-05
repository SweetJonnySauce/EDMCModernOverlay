from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest

from tests.harness_fixtures import harness_runtime_context

pytestmark = pytest.mark.harness


@pytest.fixture
def runtime_for_backend_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[object]:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    monkeypatch.delenv("SWAYSOCK", raising=False)
    monkeypatch.delenv("HYPRLAND_INSTANCE_SIGNATURE", raising=False)
    monkeypatch.delenv("GNOME_SHELL_SESSION_MODE", raising=False)
    with harness_runtime_context(monkeypatch, tmp_path, register_journal=False, capture_overlay=False) as (
        _harness,
        runtime,
        _adapter,
    ):
        runtime._preferences.manual_backend_override = ""
        runtime._runtime_manual_backend_override = ""
        yield runtime


def test_backend_status_cli_roundtrip_reports_manual_override(runtime_for_backend_override: object) -> None:
    runtime = runtime_for_backend_override
    runtime._preferences.manual_backend_override = "xwayland_compat"

    response = runtime._handle_cli_payload({"cli": "backend_status"})

    assert response["status"] == "ok"
    backend_status = response["backend_status"]
    report = response["report"]
    assert backend_status["classification"] == "degraded_overlay"
    assert backend_status["manual_override"] == "xwayland_compat"
    assert "fallback_reason" not in backend_status
    assert report["classification"] == "degraded_overlay"
    assert report["manual_override"] == "xwayland_compat"
    assert report["warning_required"] is True


def test_backend_status_cli_roundtrip_reports_invalid_manual_override(runtime_for_backend_override: object) -> None:
    runtime = runtime_for_backend_override
    runtime._preferences.manual_backend_override = "bogus_backend"

    response = runtime._handle_cli_payload({"cli": "backend_status"})

    assert response["status"] == "ok"
    backend_status = response["backend_status"]
    report = response["report"]
    assert backend_status["selected_backend"] == {
        "family": "native_wayland",
        "instance": "kwin_wayland",
    }
    assert backend_status["manual_override"] is None
    assert backend_status["override_error"] == "bogus_backend"
    assert report["override_error"] == "bogus_backend"
    assert report["warning_required"] is True


def test_manual_xwayland_override_updates_restart_env_without_live_runtime_reselection(
    runtime_for_backend_override: object,
) -> None:
    runtime = runtime_for_backend_override
    sent_configs: list[str] = []
    watchdog_envs: list[dict[str, str]] = []

    runtime._send_overlay_config = lambda: sent_configs.append("sent")
    runtime.watchdog = type(
        "_Watchdog",
        (),
        {"set_environment": lambda self, env: watchdog_envs.append(dict(env or {}))},
    )()

    runtime.set_manual_backend_override_preference("xwayland_compat")

    assert runtime._preferences.manual_backend_override == "xwayland_compat"
    assert sent_configs == []
    assert watchdog_envs
    assert watchdog_envs[-1]["QT_QPA_PLATFORM"] == "xcb"
