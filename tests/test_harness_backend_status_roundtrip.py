from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest

from tests.harness_fixtures import harness_runtime_context

pytestmark = pytest.mark.harness


@pytest.fixture
def runtime_for_backend_status(
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


def test_backend_status_cli_roundtrip_returns_plugin_hint_report(runtime_for_backend_status: object) -> None:
    runtime = runtime_for_backend_status
    runtime._request_client_backend_status = lambda **_kwargs: None

    response = runtime._handle_cli_payload({"cli": "backend_status"})

    assert isinstance(response, dict)
    assert response["status"] == "ok"
    backend_status = response["backend_status"]
    report = response["report"]
    assert backend_status["shadow_mode"] is True
    assert backend_status["selected_backend"] == {
        "family": "native_wayland",
        "instance": "kwin_wayland",
    }
    assert report["source"] == "plugin_hint"
    assert report["support_label"] == "native_wayland / kwin_wayland"
    assert report["classification"] == "true_overlay"


def test_backend_status_cli_roundtrip_prefers_client_runtime_report(runtime_for_backend_status: object) -> None:
    runtime = runtime_for_backend_status
    published: list[dict[str, object]] = []

    def _publish(payload: dict[str, object]) -> None:
        published.append(dict(payload))
        if str(payload.get("event") or "") != "OverlayClientBackendStatusRequest":
            return
        runtime._handle_cli_payload(
            {
                "cli": "client_runtime_backend_status",
                "request_id": payload.get("request_id"),
                "backend_status": {
                    "probe": {
                        "operating_system": "linux",
                        "session_type": "wayland",
                        "qt_platform_name": "wayland",
                        "compositor": "kwin",
                    },
                    "selected_backend": {
                        "family": "native_wayland",
                        "instance": "kwin_wayland",
                    },
                    "classification": "true_overlay",
                    "shadow_mode": False,
                    "helper_states": [],
                    "review_required": False,
                    "review_reasons": [],
                    "notes": ["client_selector_result"],
                    "manual_override": None,
                    "override_error": "",
                },
            }
        )

    runtime.broadcaster.publish = _publish

    response = runtime._handle_cli_payload({"cli": "backend_status"})

    assert published
    assert published[-1]["event"] == "OverlayClientBackendStatusRequest"
    assert response["status"] == "ok"
    backend_status = response["backend_status"]
    report = response["report"]
    assert backend_status["shadow_mode"] is False
    assert backend_status["selected_backend"] == {
        "family": "native_wayland",
        "instance": "kwin_wayland",
    }
    assert report["source"] == "client_runtime"
    assert report["support_label"] == "native_wayland / kwin_wayland"
    assert report["classification"] == "true_overlay"
