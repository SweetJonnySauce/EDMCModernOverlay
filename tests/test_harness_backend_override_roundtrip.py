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
        runtime._preferences.force_xwayland = False
        yield runtime


def test_backend_status_cli_roundtrip_reports_manual_override(runtime_for_backend_override: object) -> None:
    runtime = runtime_for_backend_override
    runtime._preferences.manual_backend_override = "xwayland_compat"

    response = runtime._handle_cli_payload({"cli": "backend_status"})

    assert response["status"] == "ok"
    backend_status = response["backend_status"]
    report = response["report"]
    assert backend_status["manual_override"] == "xwayland_compat"
    assert backend_status["fallback_reason"] == "manual_override"
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
