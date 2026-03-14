from __future__ import annotations

from types import SimpleNamespace

import load


def test_runtime_status_lines_use_enriched_composer(monkeypatch) -> None:
    runtime = SimpleNamespace(
        _plugin_group_controls=SimpleNamespace(
            state_snapshot=lambda: {
                "Group B": False,
                "Group A": True,
            }
        ),
        _plugin_group_state=SimpleNamespace(
            group_owner_map=lambda: {
                "Group A": "PluginA",
                "Group B": None,
            },
            metadata_snapshot=lambda: {
                "group a": {"last_payload_seen_at": "2026-03-01T00:00:00+00:00"}
            },
        ),
    )

    monkeypatch.setattr(load, "get_cached_plugin_statuses", lambda *, refresh_if_empty=False: {"plugina": "enabled"})
    lines = load._PluginRuntime.get_plugin_group_status_lines(runtime)
    assert lines == [
        "Group A: Enabled, Seen, On",
        "Group B: Unknown, Not Seen, Off",
    ]
