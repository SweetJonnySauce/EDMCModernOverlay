from __future__ import annotations

import json
import logging
from pathlib import Path

from overlay_plugin.plugin_group_controls import PluginGroupControlService, resolve_payload_group_targets
from overlay_plugin.plugin_group_state import PluginGroupStateManager


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_resolve_payload_group_targets_unions_and_dedupes() -> None:
    payload = {
        "plugin_group": "Alpha",
        "plugin_groups": ["Beta", "alpha", "Beta", "", 123],
    }
    assert resolve_payload_group_targets(payload) == ["Alpha", "Beta"]


def test_plugin_group_control_service_set_and_toggle(tmp_path: Path) -> None:
    shipped = tmp_path / "overlay_groupings.json"
    user = tmp_path / "overlay_groupings.user.json"
    _write_json(
        shipped,
        {
            "PluginA": {
                "idPrefixGroups": {
                    "Alpha": {"idPrefixes": ["a-"]},
                    "Beta": {"idPrefixes": ["b-"]},
                }
            }
        },
    )
    _write_json(user, {})
    manager = PluginGroupStateManager(shipped_path=shipped, user_path=user)

    publishes: list[str] = []
    clears: list[tuple[list[str], str]] = []
    service = PluginGroupControlService(
        state_manager=manager,
        publish_config=lambda: publishes.append("published"),
        publish_group_clear=lambda groups, source: clears.append((list(groups), source)),
    )

    result = service.set_enabled(False, group_names=["Alpha"], source="test")
    assert result["updated"] == ["Alpha"]
    assert result["unknown"] == []
    assert result["cleared"] == ["Alpha"]
    assert publishes == ["published"]
    assert clears == [(["Alpha"], "test")]

    toggled = service.toggle(group_names=["Alpha", "Beta"], source="test")
    assert toggled["updated"] == ["Alpha", "Beta"]
    assert toggled["unknown"] == []
    assert toggled["cleared"] == ["Beta"]
    assert toggled["action"] == "toggle"
    assert clears == [(["Alpha"], "test"), (["Beta"], "test")]
    assert service.state_snapshot() == {"Alpha": True, "Beta": False}

    turned_on = service.set_enabled(True, group_names=["Beta"], source="test_on")
    assert turned_on["updated"] == ["Beta"]
    assert turned_on["cleared"] == []
    assert clears == [(["Alpha"], "test"), (["Beta"], "test")]


def test_plugin_group_control_service_global_toggle_clears_only_when_toggled_off(tmp_path: Path) -> None:
    shipped = tmp_path / "overlay_groupings.json"
    user = tmp_path / "overlay_groupings.user.json"
    _write_json(
        shipped,
        {
            "PluginA": {
                "idPrefixGroups": {
                    "Alpha": {"idPrefixes": ["a-"]},
                    "Beta": {"idPrefixes": ["b-"]},
                }
            }
        },
    )
    _write_json(user, {})
    manager = PluginGroupStateManager(shipped_path=shipped, user_path=user)

    clears: list[tuple[list[str], str]] = []
    service = PluginGroupControlService(
        state_manager=manager,
        publish_config=lambda: None,
        publish_group_clear=lambda groups, source: clears.append((list(groups), source)),
    )

    first = service.toggle(source="toggle_off")
    second = service.toggle(source="toggle_on")

    assert first["updated"] == ["Alpha", "Beta"]
    assert first["cleared"] == ["Alpha", "Beta"]
    assert second["updated"] == ["Alpha", "Beta"]
    assert second["cleared"] == []
    assert clears == [(["Alpha", "Beta"], "toggle_off")]


def test_plugin_group_control_service_warns_once_per_unknown_group(tmp_path: Path, caplog) -> None:
    shipped = tmp_path / "overlay_groupings.json"
    user = tmp_path / "overlay_groupings.user.json"
    _write_json(
        shipped,
        {
            "PluginA": {
                "idPrefixGroups": {
                    "Alpha": {"idPrefixes": ["a-"]},
                }
            }
        },
    )
    _write_json(user, {})
    manager = PluginGroupStateManager(shipped_path=shipped, user_path=user)
    service = PluginGroupControlService(state_manager=manager, publish_config=lambda: None)

    with caplog.at_level(logging.WARNING, logger="EDMC.ModernOverlay.PluginGroupControls"):
        result = service.set_enabled(
            False,
            group_names=["Missing Group", "missing group", "Other Group", "other group"],
            source="test_warn",
        )

    assert result["updated"] == []
    assert result["unknown"] == ["Missing Group", "Other Group"]
    warnings = [record.getMessage() for record in caplog.records if record.levelno == logging.WARNING]
    assert sum("Missing Group" in message for message in warnings) == 1
    assert sum("Other Group" in message for message in warnings) == 1


def test_plugin_group_control_service_global_off_clears_all_defined_groups_even_when_idempotent(tmp_path: Path) -> None:
    shipped = tmp_path / "overlay_groupings.json"
    user = tmp_path / "overlay_groupings.user.json"
    _write_json(
        shipped,
        {
            "PluginA": {
                "idPrefixGroups": {
                    "Alpha": {"idPrefixes": ["a-"]},
                    "Beta": {"idPrefixes": ["b-"]},
                }
            }
        },
    )
    _write_json(user, {})
    manager = PluginGroupStateManager(shipped_path=shipped, user_path=user)

    publishes: list[str] = []
    clears: list[tuple[list[str], str]] = []
    service = PluginGroupControlService(
        state_manager=manager,
        publish_config=lambda: publishes.append("published"),
        publish_group_clear=lambda groups, source: clears.append((list(groups), source)),
    )

    first = service.set_enabled(False, source="global_off")
    second = service.set_enabled(False, source="global_off_repeat")

    assert first["updated"] == ["Alpha", "Beta"]
    assert first["cleared"] == ["Alpha", "Beta"]
    assert second["updated"] == []
    assert second["cleared"] == ["Alpha", "Beta"]
    assert publishes == ["published"]
    assert clears == [
        (["Alpha", "Beta"], "global_off"),
        (["Alpha", "Beta"], "global_off_repeat"),
    ]


def test_plugin_group_control_service_unknown_only_targeted_off_emits_no_clear(tmp_path: Path) -> None:
    shipped = tmp_path / "overlay_groupings.json"
    user = tmp_path / "overlay_groupings.user.json"
    _write_json(
        shipped,
        {
            "PluginA": {
                "idPrefixGroups": {
                    "Alpha": {"idPrefixes": ["a-"]},
                }
            }
        },
    )
    _write_json(user, {})
    manager = PluginGroupStateManager(shipped_path=shipped, user_path=user)

    clears: list[tuple[list[str], str]] = []
    service = PluginGroupControlService(
        state_manager=manager,
        publish_config=lambda: None,
        publish_group_clear=lambda groups, source: clears.append((list(groups), source)),
    )

    result = service.set_enabled(False, group_names=["Missing Group"], source="unknown_only")
    assert result["updated"] == []
    assert result["unknown"] == ["Missing Group"]
    assert result["cleared"] == []
    assert clears == []


def test_plugin_group_control_service_reset_to_default_restores_group_visibility(tmp_path: Path) -> None:
    shipped = tmp_path / "overlay_groupings.json"
    user = tmp_path / "overlay_groupings.user.json"
    _write_json(
        shipped,
        {
            "PluginA": {
                "idPrefixGroups": {
                    "Alpha": {"idPrefixes": ["a-"]},
                }
            }
        },
    )
    _write_json(user, {})
    manager = PluginGroupStateManager(shipped_path=shipped, user_path=user)
    manager.set_groups_enabled(False, ["Alpha"])
    manager.create_profile("PvE")
    manager.set_current_profile("PvE")
    manager.set_groups_enabled(True, ["Alpha"])
    assert manager.state_snapshot() == {"Alpha": True}

    clears: list[tuple[list[str], str]] = []
    publishes: list[str] = []
    service = PluginGroupControlService(
        state_manager=manager,
        publish_config=lambda: publishes.append("published"),
        publish_group_clear=lambda groups, source: clears.append((list(groups), source)),
    )
    result = service.reset_to_default(group_names=["Alpha"], source="reset_test")

    assert result["updated"] == ["Alpha"]
    assert result["unknown"] == []
    assert result["cleared"] == ["Alpha"]
    assert result["action"] == "reset_to_default"
    assert publishes == ["published"]
    assert clears == [(["Alpha"], "reset_test")]
    assert service.state_snapshot() == {"Alpha": False}
