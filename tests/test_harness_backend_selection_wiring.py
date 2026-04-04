from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

from tests.harness_fixtures import harness_runtime_context

pytestmark = pytest.mark.harness


@pytest.fixture
def harness_runtime(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[tuple[object, Any, Any]]:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)

    with harness_runtime_context(monkeypatch, tmp_path, register_journal=False, capture_overlay=True) as (
        harness,
        runtime,
        adapter,
    ):
        assert adapter is not None
        runtime._preferences.manual_backend_override = ""
        runtime._runtime_manual_backend_override = ""
        yield harness, runtime, adapter


def test_runtime_publishes_shadow_backend_status_in_overlay_config(
    harness_runtime: tuple[object, Any, Any]
) -> None:
    _harness, runtime, adapter = harness_runtime
    adapter.reset()

    runtime._send_overlay_config()

    config_payloads = [
        payload for payload in adapter.raw_payloads if str(payload.get("event") or "") == "OverlayConfig"
    ]
    assert config_payloads, "Expected an OverlayConfig payload to be published"

    payload = config_payloads[-1]
    platform_context = payload["platform_context"]
    shadow = platform_context["shadow_backend_status"]

    assert platform_context["session_type"] == "wayland"
    assert platform_context["compositor"] == "kwin"
    assert "force_xwayland" not in platform_context
    assert shadow["shadow_mode"] is True
    assert shadow["selected_backend"] == {
        "family": "native_wayland",
        "instance": "kwin_wayland",
    }
    assert shadow["classification"] == "true_overlay"
    assert shadow["report"]["family"] == "native_wayland"
    assert shadow["report"]["instance"] == "kwin_wayland"
    assert shadow["report"]["classification"] == "true_overlay"
    assert shadow["report"]["summary"].startswith(
        "family=native_wayland instance=kwin_wayland classification=true_overlay"
    )
    assert shadow["probe"]["qt_platform_name"] == "wayland"
    assert "shadow_selector_result" in shadow["notes"]
