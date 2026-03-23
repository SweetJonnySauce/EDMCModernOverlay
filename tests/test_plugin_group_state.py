from __future__ import annotations

import json

from overlay_plugin.plugin_group_state import PluginGroupStateManager


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_state_manager_persists_enabled_state_and_ignores_stale_entries(tmp_path):
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
    _write_json(
        user,
        {
            "_plugin_group_state": {
                "enabled": {
                    "Alpha": False,
                    "Removed Group": False,
                }
            }
        },
    )

    manager = PluginGroupStateManager(shipped_path=shipped, user_path=user)
    assert manager.state_snapshot() == {"Alpha": False, "Beta": True}
    assert manager.status_lines() == ["Alpha: Off", "Beta: On"]

    updated, unknown = manager.set_groups_enabled(False, ["Beta"])
    assert updated == ["Beta"]
    assert unknown == []

    reloaded = PluginGroupStateManager(shipped_path=shipped, user_path=user)
    assert reloaded.state_snapshot() == {"Alpha": False, "Beta": False}
    assert reloaded.status_lines() == ["Alpha: Off", "Beta: Off"]

    saved = json.loads(user.read_text(encoding="utf-8"))
    enabled_map = saved["_plugin_group_state"]["enabled"]
    assert enabled_map["Removed Group"] is False
    assert "global_enabled" not in saved["_plugin_group_state"]
    assert "overlay_enabled" not in saved["_plugin_group_state"]


def test_state_manager_drops_disabled_payload_and_tracks_hybrid_metadata(tmp_path):
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
    _write_json(
        user,
        {
            "_plugin_group_state": {
                "enabled": {"Alpha": False}
            }
        },
    )

    manager = PluginGroupStateManager(shipped_path=shipped, user_path=user)
    payload = {
        "event": "LegacyOverlay",
        "plugin": "PluginA",
        "id": "a-123",
        "type": "shape",
        "shape": "rect",
        "x": 10,
        "y": 20,
        "w": 30,
        "h": 40,
    }

    drop, group_name = manager.should_drop_payload(payload)
    assert drop is True
    assert group_name == "Alpha"

    metadata = manager.metadata_snapshot()["Alpha"]
    assert metadata["bounds"] == [10.0, 20.0, 40.0, 60.0]
    assert "last_payload_seen_at" in metadata
    assert "last_bounds_updated_at" in metadata

    counters = manager.counters()
    assert counters["disabled_payload_drop_count"] == 1
    assert counters["disabled_payload_hybrid_metadata_update_count"] == 1
    assert counters["resolver_parity_match_count"] == 1
    assert counters["resolver_parity_mismatch_count"] == 0


def test_state_manager_toggle_groups(tmp_path):
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
    _write_json(user, {"_plugin_group_state": {"enabled": {"Alpha": False}}})

    manager = PluginGroupStateManager(shipped_path=shipped, user_path=user)
    updated, unknown = manager.toggle_groups(["Alpha", "Beta", "Missing"])

    assert updated == ["Alpha", "Beta"]
    assert unknown == ["Missing"]
    assert manager.state_snapshot() == {"Alpha": True, "Beta": False}


def test_state_manager_enabled_payload_tracks_parity_without_drop_or_disabled_metadata_counter(tmp_path):
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
    payload = {
        "event": "LegacyOverlay",
        "plugin": "PluginA",
        "id": "a-1",
        "type": "shape",
        "shape": "rect",
        "x": 1,
        "y": 2,
        "w": 3,
        "h": 4,
    }

    drop, group_name = manager.should_drop_payload(payload)
    assert drop is False
    assert group_name == "Alpha"

    counters = manager.counters()
    assert counters["disabled_payload_drop_count"] == 0
    assert counters["disabled_payload_hybrid_metadata_update_count"] == 0
    assert counters["resolver_parity_match_count"] == 1
    assert counters["resolver_parity_mismatch_count"] == 0


def test_state_manager_bulk_set_updates_only_known_groups_and_keeps_stale_entries(tmp_path):
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
    _write_json(
        user,
        {
            "_plugin_group_state": {
                "enabled": {
                    "Alpha": True,
                    "Beta": True,
                    "Removed Group": True,
                }
            }
        },
    )

    manager = PluginGroupStateManager(shipped_path=shipped, user_path=user)
    updated, unknown = manager.set_groups_enabled(False, None)

    assert updated == ["Alpha", "Beta"]
    assert unknown == []
    saved = json.loads(user.read_text(encoding="utf-8"))
    enabled_map = saved["_plugin_group_state"]["enabled"]
    assert enabled_map["Alpha"] is False
    assert enabled_map["Beta"] is False
    assert enabled_map["Removed Group"] is True


def test_state_manager_profile_scoped_visibility_switches_with_active_profile(tmp_path):
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
    _write_json(
        user,
        {
            "_overlay_profile_state": {
                "profiles": ["PvE", "Default"],
                "current_profile": "Default",
            },
            "_plugin_group_state": {
                "enabled": {"Alpha": True},
                "enabled_by_profile": {
                    "Default": {"Alpha": True},
                    "PvE": {"Alpha": False},
                },
            },
        },
    )

    manager = PluginGroupStateManager(shipped_path=shipped, user_path=user)
    assert manager.state_snapshot() == {"Alpha": True}

    manager.set_current_profile("PvE")
    assert manager.state_snapshot() == {"Alpha": False}

    manager.set_current_profile("Default")
    assert manager.state_snapshot() == {"Alpha": True}


def test_state_manager_clone_and_rename_profile_preserves_visibility_map(tmp_path):
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

    manager.clone_profile("PvE", "PvP")
    manager.set_current_profile("PvP")
    assert manager.state_snapshot() == {"Alpha": True}

    manager.rename_profile("PvP", "Combat")
    manager.set_current_profile("Combat")
    assert manager.state_snapshot() == {"Alpha": True}

    manager.set_current_profile("Default")
    assert manager.state_snapshot() == {"Alpha": False}


def test_state_manager_reset_groups_to_default_restores_active_profile_visibility(tmp_path):
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

    updated, unknown = manager.reset_groups_to_default(["Alpha"])
    assert updated == ["Alpha"]
    assert unknown == []
    assert manager.state_snapshot() == {"Alpha": False}
