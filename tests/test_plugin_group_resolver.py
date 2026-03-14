from __future__ import annotations

import json

from overlay_plugin.plugin_group_resolver import PluginGroupResolver


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_resolver_matches_group_by_payload_id_and_plugin(tmp_path):
    shipped = tmp_path / "overlay_groupings.json"
    user = tmp_path / "overlay_groupings.user.json"
    _write_json(
        shipped,
        {
            "PluginA": {
                "matchingPrefixes": ["plugina-"],
                "idPrefixGroups": {
                    "Group One": {"idPrefixes": ["plugina-one-"]},
                    "Group Two": {"idPrefixes": ["plugina-two-"]},
                },
            }
        },
    )
    _write_json(user, {})

    resolver = PluginGroupResolver(shipped_path=shipped, user_path=user)
    payload = {"event": "LegacyOverlay", "plugin": "PluginA", "id": "plugina-two-123"}

    assert resolver.resolve_group_name(payload) == "Group Two"


def test_resolver_uses_nested_fields_and_known_groups_sorted(tmp_path):
    shipped = tmp_path / "overlay_groupings.json"
    user = tmp_path / "overlay_groupings.user.json"
    _write_json(
        shipped,
        {
            "PluginB": {
                "matchingPrefixes": ["pluginb-"],
                "idPrefixGroups": {
                    "Zeta": {"idPrefixes": ["pluginb-zeta-"]},
                    "Alpha": {"idPrefixes": ["pluginb-alpha-"]},
                },
            }
        },
    )
    _write_json(user, {})

    resolver = PluginGroupResolver(shipped_path=shipped, user_path=user)
    payload = {
        "event": "LegacyOverlay",
        "raw": {"id": "pluginb-alpha-001", "plugin_name": "PluginB"},
    }

    assert resolver.resolve_group_name(payload) == "Alpha"
    assert resolver.known_group_names() == ("Alpha", "Zeta")


def test_resolver_exposes_group_owner_map_with_ambiguous_groups_as_unknown(tmp_path):
    shipped = tmp_path / "overlay_groupings.json"
    user = tmp_path / "overlay_groupings.user.json"
    _write_json(
        shipped,
        {
            "PluginA": {
                "idPrefixGroups": {
                    "Shared": {"idPrefixes": ["a-shared-"]},
                    "Alpha": {"idPrefixes": ["a-alpha-"]},
                },
            },
            "PluginB": {
                "idPrefixGroups": {
                    "Shared": {"idPrefixes": ["b-shared-"]},
                    "Beta": {"idPrefixes": ["b-beta-"]},
                },
            },
        },
    )
    _write_json(user, {})

    resolver = PluginGroupResolver(shipped_path=shipped, user_path=user)
    owners = resolver.group_owner_map()

    assert owners["Alpha"] == "PluginA"
    assert owners["Beta"] == "PluginB"
    assert owners["Shared"] is None
