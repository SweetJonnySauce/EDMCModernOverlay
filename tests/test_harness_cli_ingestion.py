from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

import load
from overlay_plugin.profile_state import OverlayProfileStore
from tests.harness_fixtures import harness_runtime_context

pytestmark = pytest.mark.harness


@pytest.fixture
def runtime_with_capture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[tuple[Any, list[dict[str, Any]]]]:
    with harness_runtime_context(monkeypatch, tmp_path, register_journal=False, capture_overlay=False) as (
        _harness,
        runtime,
        _adapter,
    ):
        profile_store_path = tmp_path / "overlay_groupings.user.json"
        runtime._groupings_user_path = profile_store_path
        runtime._profile_store = OverlayProfileStore(user_path=profile_store_path, logger=load.LOGGER)
        runtime._send_overlay_config = lambda *args, **kwargs: None

        published: list[dict[str, Any]] = []
        runtime._publish_payload = lambda payload: published.append(dict(payload))
        yield runtime, published


def test_cli_profile_commands_route_through_runtime(runtime_with_capture: tuple[Any, list[dict[str, Any]]]) -> None:
    runtime, published = runtime_with_capture

    created = runtime._handle_cli_payload({"cli": "profile_create", "profile": "Mining"})
    assert created is not None
    assert created["status"] == "ok"
    assert "Mining" in created["profiles"]

    switched = runtime._handle_cli_payload({"cli": "profile_set", "profile": "Mining"})
    assert switched is not None
    assert switched["status"] == "ok"
    assert switched["current_profile"] == "Mining"

    status = runtime._handle_cli_payload({"cli": "profile_status"})
    assert status is not None
    assert status["status"] == "ok"
    assert status["current_profile"] == "Mining"

    assert any(payload.get("event") == "OverlayProfileChanged" for payload in published)


def test_cli_legacy_and_controller_commands_publish_expected_payloads(
    runtime_with_capture: tuple[Any, list[dict[str, Any]]]
) -> None:
    runtime, published = runtime_with_capture

    response = runtime._handle_cli_payload(
        {
            "cli": "legacy_overlay",
            "payload": {"type": "message", "id": "msg-1", "text": "Harness CLI", "x": 10, "y": 20},
        }
    )
    assert response == {"status": "ok"}

    status = runtime._handle_cli_payload({"cli": "plugin_group_status"})
    assert status is not None
    assert status["status"] == "ok"
    assert isinstance(status.get("plugin_group_states"), dict)
    assert isinstance(status.get("lines"), list)
    assert isinstance(status.get("counters"), dict)

    active = runtime._handle_cli_payload(
        {
            "cli": "controller_active_group",
            "plugin": "EDR",
            "label": "Docking",
            "anchor": "top",
            "edit_nonce": "nonce-1",
        }
    )
    assert active == {"status": "ok"}

    assert any(
        payload.get("event") == "LegacyOverlay" and payload.get("text") == "Harness CLI" for payload in published
    )
    assert any(
        payload.get("event") == "OverlayControllerActiveGroup"
        and payload.get("plugin") == "EDR"
        and payload.get("label") == "Docking"
        for payload in published
    )


def test_cli_unsupported_command_returns_error(runtime_with_capture: tuple[Any, list[dict[str, Any]]]) -> None:
    runtime, _published = runtime_with_capture

    response = runtime._handle_cli_payload({"cli": "does_not_exist"})

    assert response is not None
    assert response["status"] == "error"
    assert "Unsupported CLI command" in str(response["error"])
