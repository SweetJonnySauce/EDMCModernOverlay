from __future__ import annotations

from types import SimpleNamespace

import load


def test_plugin_group_reset_default_cli_routes_to_runtime_reset_and_returns_states() -> None:
    calls: list[dict[str, object]] = []
    plugin = SimpleNamespace(
        _reset_plugin_groups_to_default=lambda *, group_names=None, source="": (
            calls.append({"group_names": list(group_names or []), "source": source}) or {
                "updated": ["Alpha"],
                "unknown": [],
                "cleared": ["Alpha"],
                "changed": True,
                "action": "reset_to_default",
            }
        ),
        _plugin_group_controls=SimpleNamespace(
            state_snapshot=lambda: {"Alpha": False},
            status_lines=lambda: ["Alpha: Off"],
        ),
    )

    response = load._PluginRuntime._handle_cli_payload(
        plugin,
        {"cli": "plugin_group_reset_default", "plugin_group": "Alpha"},
    )

    assert response == {
        "status": "ok",
        "updated": ["Alpha"],
        "unknown": [],
        "cleared": ["Alpha"],
        "changed": True,
        "action": "reset_to_default",
        "plugin_group_states": {"Alpha": False},
        "lines": ["Alpha: Off"],
    }
    assert calls == [{"group_names": ["Alpha"], "source": "controller_cli"}]
