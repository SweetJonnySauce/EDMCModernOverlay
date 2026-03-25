from __future__ import annotations

import logging

from overlay_plugin import command_overlay_groups
from overlay_plugin.overlay_api import PluginGroupingError


def test_ensure_runtime_command_groups_calls_define_plugin_group_for_plugins_and_status(monkeypatch) -> None:
    calls: list[dict[str, object]] = []
    results = [True, False, False]

    def _fake_define_plugin_group(**kwargs):
        calls.append(dict(kwargs))
        return results.pop(0)

    monkeypatch.setattr(command_overlay_groups, "define_plugin_group", _fake_define_plugin_group)

    updated = command_overlay_groups.ensure_runtime_command_groups(logger=logging.getLogger("test-command-groups"))

    assert updated is True
    assert len(calls) == 3
    group_names = [str(call.get("plugin_group_name")) for call in calls]
    assert group_names == [
        command_overlay_groups.COMMAND_PLUGIN_STATUS_GROUP_NAME,
        command_overlay_groups.COMMAND_GROUP_STATUS_GROUP_NAME,
        command_overlay_groups.COMMAND_PROFILE_STATUS_GROUP_NAME,
    ]
    profile_call = next(
        call for call in calls if str(call.get("plugin_group_name")) == command_overlay_groups.COMMAND_PROFILE_STATUS_GROUP_NAME
    )
    assert profile_call["plugin_group_background_color"] == "black"
    assert profile_call["plugin_group_border_color"] == "black"
    assert profile_call["plugin_group_border_width"] == 3
    for call in calls:
        assert call["plugin_name"] == command_overlay_groups.COMMAND_GROUP_PLUGIN_NAME
        assert call["plugin_matching_prefixes"] == command_overlay_groups.COMMAND_GROUP_MATCHING_PREFIXES


def test_ensure_runtime_command_groups_continues_after_grouping_error(monkeypatch, caplog) -> None:
    calls = {"count": 0}

    def _fake_define_plugin_group(**kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise PluginGroupingError("bad config")
        return True

    monkeypatch.setattr(command_overlay_groups, "define_plugin_group", _fake_define_plugin_group)

    with caplog.at_level(logging.WARNING):
        updated = command_overlay_groups.ensure_runtime_command_groups(logger=logging.getLogger("test-command-groups"))

    assert updated is True
    assert calls["count"] == 3
    assert "Command overlay group setup failed" in caplog.text


def test_render_group_status_payloads_uses_status_prefix() -> None:
    payloads = command_overlay_groups.render_group_status_payloads(["Alpha: On", "Beta: Off"], ttl_seconds=7)

    assert payloads
    assert all(str(payload["id"]).startswith(command_overlay_groups.COMMAND_GROUP_STATUS_ID_PREFIX) for payload in payloads)
    assert all(int(payload["ttl"]) == 7 for payload in payloads)

    messages = [payload for payload in payloads if payload.get("type") == "message"]
    shapes = [payload for payload in payloads if payload.get("type") == "shape"]
    assert any(payload.get("text") == "Plugin Group" for payload in messages)
    assert any(payload.get("text") == "Alpha" for payload in messages)
    assert any(payload.get("text") == "Beta" for payload in messages)
    assert any(payload.get("shape") == "rect" for payload in shapes)
    assert any(payload.get("shape") == "vect" for payload in shapes)
