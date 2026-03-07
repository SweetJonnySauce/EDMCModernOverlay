from __future__ import annotations

from overlay_plugin.group_status_enrichment import (
    build_enriched_group_status_lines,
    normalise_plugin_status_label,
)


def test_normalise_plugin_status_label_maps_expected_tokens() -> None:
    assert normalise_plugin_status_label("enabled") == "Enabled"
    assert normalise_plugin_status_label("disabled") == "Not Enabled"
    assert normalise_plugin_status_label("ignored") == "Ignored"
    assert normalise_plugin_status_label("unknown") == "Unknown"
    assert normalise_plugin_status_label("other") == "Unknown"
    assert normalise_plugin_status_label(None) == "Unknown"


def test_build_enriched_group_status_lines_sorts_and_maps_states() -> None:
    lines = build_enriched_group_status_lines(
        group_names=["Group B", "Group A", "Group C"],
        group_owner_map={
            "Group A": "PluginA",
            "Group B": "PluginB",
        },
        plugin_status_map={
            "plugina": "enabled",
            "pluginb": "ignored",
        },
        group_state_map={
            "Group A": True,
            "Group B": False,
            "Group C": True,
        },
        metadata_snapshot={
            "group a": {"last_payload_seen_at": "2026-03-01T00:00:00+00:00"},
            "group b": {"last_payload_seen_at": ""},
        },
    )

    assert lines == [
        "Group A: Enabled, Seen, On",
        "Group B: Ignored, Not Seen, Off",
        "Group C: Unknown, Not Seen, On",
    ]
