from __future__ import annotations

import json
from pathlib import Path

from overlay_plugin.profile_state import DEFAULT_PROFILE_NAME, OverlayProfileStore


def _read_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_profile_store_bootstraps_default_from_legacy_root(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text(
        json.dumps(
            {
                "PluginA": {
                    "idPrefixGroups": {
                        "Main": {"offsetX": 12},
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    store = OverlayProfileStore(user_path=user_path)

    status = store.status()

    assert status["profiles"] == [DEFAULT_PROFILE_NAME]
    assert status["current_profile"] == DEFAULT_PROFILE_NAME
    assert status["manual_profile"] == DEFAULT_PROFILE_NAME


def test_profile_store_manual_fallback_and_auto_override(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text("{}\n", encoding="utf-8")
    store = OverlayProfileStore(user_path=user_path)
    store.create_profile("Mining")
    store.create_profile("Combat")
    store.set_current_profile("Combat", source="manual")
    store.set_profile_rules("Combat", [{"context": "OnFoot"}])
    store.set_profile_rules("Mining", [{"context": "OnFoot"}])

    no_match = store.apply_context(context="InMainShip", ship_id=42)
    auto_match = store.apply_context(context="OnFoot", ship_id=42)
    fallback = store.apply_context(context="InMainShip", ship_id=42)

    assert no_match["current_profile"] == "Combat"
    # Non-default conflicts are resolved by persisted profile sequence.
    assert auto_match["current_profile"] == "Mining"
    # No match returns to manual profile lock.
    assert fallback["current_profile"] == "Combat"


def test_profile_store_match_prefers_non_default_over_default(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text("{}\n", encoding="utf-8")
    store = OverlayProfileStore(user_path=user_path)
    store.create_profile("On Foot")
    store.set_profile_rules("Default", [{"context": "OnFoot"}])
    store.set_profile_rules("On Foot", [{"context": "OnFoot"}])

    winner = store.match_profile(active_contexts={"OnFoot"}, ship_id=7)

    assert winner == "On Foot"


def test_default_profile_rules_always_include_all_contexts(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text("{}\n", encoding="utf-8")
    store = OverlayProfileStore(user_path=user_path)

    status = store.status()
    default_rules = status["rules"]["Default"]
    contexts = {str(item.get("context")) for item in default_rules}

    assert contexts == {"InMainShip", "InSRV", "InFighter", "OnFoot", "InWing", "InTaxi", "InMulticrew"}

    store.set_profile_rules("Default", [{"context": "OnFoot"}])
    status_after = store.status()
    contexts_after = {str(item.get("context")) for item in status_after["rules"]["Default"]}
    assert contexts_after == {"InMainShip", "InSRV", "InFighter", "OnFoot", "InWing", "InTaxi", "InMulticrew"}


def test_profile_store_updates_fleet_from_storedships_and_set_name(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text("{}\n", encoding="utf-8")
    store = OverlayProfileStore(user_path=user_path)

    changed_snapshot = store.update_fleet_from_journal(
        entry={
            "event": "StoredShips",
            "ShipsHere": [
                {"ShipID": 12, "ShipType": "krait_mkii"},
                {"ShipID": 9, "ShipType": "cobra_mk_iii"},
            ],
            "ShipsRemote": [],
        }
    )
    changed_delta = store.update_fleet_from_journal(
        entry={
            "event": "SetUserShipName",
            "ShipID": 12,
            "UserShipName": "Miner One",
            "UserShipId": "MO-01",
        }
    )
    status = store.status()

    assert changed_snapshot is True
    assert changed_delta is True
    assert [item["ship_id"] for item in status["ships"]] == [9, 12]
    ship_12 = next(item for item in status["ships"] if item["ship_id"] == 12)
    assert ship_12["ship_name"] == "Miner One"
    assert ship_12["ship_ident"] == "MO-01"


def test_profile_store_storedships_uses_localised_name_fields(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text("{}\n", encoding="utf-8")
    store = OverlayProfileStore(user_path=user_path)

    changed = store.update_fleet_from_journal(
        entry={
            "event": "StoredShips",
            "ShipsHere": [
                {"ShipID": 91, "ShipType": "lakonminer", "Name_Localised": "Type-11 Prospector", "ShipIdent": "SW-29L"}
            ],
            "ShipsRemote": [],
        }
    )
    status = store.status()

    assert changed is True
    ship_91 = next(item for item in status["ships"] if item["ship_id"] == 91)
    assert ship_91["ship_name"] == "Type-11 Prospector"
    assert ship_91["ship_ident"] == "SW-29L"


def test_profile_store_storedships_prefers_localised_ship_type(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text("{}\n", encoding="utf-8")
    store = OverlayProfileStore(user_path=user_path)

    changed = store.update_fleet_from_journal(
        entry={
            "event": "StoredShips",
            "ShipsHere": [{"ShipID": 77, "ShipType": "type9", "ShipType_Localised": "Type-9 Heavy"}],
            "ShipsRemote": [],
        }
    )
    status = store.status()

    assert changed is True
    ship_77 = next(item for item in status["ships"] if item["ship_id"] == 77)
    assert ship_77["ship_type"] == "Type-9 Heavy"


def test_profile_store_shipyardswap_prefers_localised_ship_type(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text("{}\n", encoding="utf-8")
    store = OverlayProfileStore(user_path=user_path)

    changed = store.update_fleet_from_journal(
        entry={
            "event": "ShipyardSwap",
            "ShipID": 91,
            "ShipType": "lakonminer",
            "ShipType_Localised": "Type-11 Prospector",
            "ShipName_Localised": "Type-11 Prospector",
            "ShipIdent": "SW-29L",
        }
    )
    status = store.status()

    assert changed is True
    ship_91 = next(item for item in status["ships"] if item["ship_id"] == 91)
    assert ship_91["ship_type"] == "Type-11 Prospector"
    assert ship_91["ship_name"] == "Type-11 Prospector"
    assert ship_91["ship_ident"] == "SW-29L"


def test_profile_store_shipyardswap_state_merge_does_not_downgrade_localised_type(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text("{}\n", encoding="utf-8")
    store = OverlayProfileStore(user_path=user_path)

    changed = store.update_fleet_from_journal(
        entry={
            "event": "ShipyardSwap",
            "ShipID": 93,
            "ShipType": "smallcombat01_nx",
            "ShipType_Localised": "Kestrel Mk II",
            "UserShipName": "Lily Phillips",
            "UserShipId": "PVE-05",
        },
        state={
            "ShipID": 93,
            "ShipType": "smallcombat01_nx",
            "ShipName": "Lily Phillips",
            "ShipIdent": "PVE-05",
        },
    )
    status = store.status()

    assert changed is True
    ship_93 = next(item for item in status["ships"] if item["ship_id"] == 93)
    assert ship_93["ship_type"] == "Kestrel Mk II"
    assert ship_93["ship_name"] == "Lily Phillips"
    assert ship_93["ship_ident"] == "PVE-05"


def test_profile_store_storedships_merges_active_ship_from_state_when_omitted(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text("{}\n", encoding="utf-8")
    store = OverlayProfileStore(user_path=user_path)

    store.update_fleet_from_journal(
        entry={
            "event": "LoadGame",
            "ShipID": 77,
            "Ship": "krait_mkii",
            "UserShipName": "Current Ship",
            "UserShipId": "CUR-1",
        }
    )
    changed = store.update_fleet_from_journal(
        entry={
            "event": "StoredShips",
            "ShipsHere": [{"ShipID": 12, "ShipType": "cobra_mk_iii"}],
            "ShipsRemote": [],
        },
        state={
            "ShipID": 77,
            "Ship": "krait_mkii",
            "UserShipName": "Current Ship",
            "UserShipId": "CUR-1",
        },
    )
    status = store.status()

    assert changed is True
    assert [item["ship_id"] for item in status["ships"]] == [12, 77]
    active = next(item for item in status["ships"] if item["ship_id"] == 77)
    assert active["ship_name"] == "Current Ship"
    assert active["ship_ident"] == "CUR-1"


def test_profile_store_switch_materializes_root_overrides(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text(
        json.dumps(
            {
                "PluginA": {
                    "idPrefixGroups": {
                        "Main": {"offsetX": 5},
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    store = OverlayProfileStore(user_path=user_path)
    store.create_profile("Mining")
    store.set_current_profile("Mining", source="manual")

    payload = _read_payload(user_path)

    assert payload["_overlay_profile_state"]["current_profile"] == "Mining"
    assert "PluginA" in payload
    assert "_overlay_profile_overrides" in payload


def test_default_edit_propagates_only_non_divergent_fields(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text(
        json.dumps(
            {
                "PluginA": {
                    "idPrefixGroups": {
                        "Main": {"offsetX": 5, "offsetY": 1},
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    store = OverlayProfileStore(user_path=user_path)
    store.create_profile("Mining")
    store.set_current_profile("Mining", source="manual")
    store.apply_group_fields(
        plugin_name="PluginA",
        group_label="Main",
        updates={"offsetX": 99},
        clear_fields=(),
    )
    store.set_current_profile("Default", source="manual")
    store.apply_group_fields(
        plugin_name="PluginA",
        group_label="Main",
        updates={"offsetX": 8, "offsetY": 3},
        clear_fields=(),
    )

    payload = _read_payload(user_path)
    mining = payload["_overlay_profile_overrides"]["Mining"]["PluginA"]["idPrefixGroups"]["Main"]
    default = payload["_overlay_profile_overrides"]["Default"]["PluginA"]["idPrefixGroups"]["Main"]

    # Divergent field is preserved.
    assert mining["offsetX"] == 99
    # Non-divergent field inherits the new default value.
    assert mining["offsetY"] == 3
    assert default["offsetX"] == 8
    assert default["offsetY"] == 3


def test_reset_group_for_custom_profile_reverts_to_default_profile_values(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text(
        json.dumps(
            {
                "PluginA": {
                    "idPrefixGroups": {
                        "Main": {"offsetX": 5, "offsetY": 2},
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    store = OverlayProfileStore(user_path=user_path)
    store.create_profile("Mining")
    store.set_current_profile("Mining", source="manual")
    store.apply_group_fields(
        plugin_name="PluginA",
        group_label="Main",
        updates={"offsetX": 42},
        clear_fields=(),
    )

    store.reset_group_for_active_profile(plugin_name="PluginA", group_label="Main")
    payload = _read_payload(user_path)
    mining = payload["_overlay_profile_overrides"]["Mining"]["PluginA"]["idPrefixGroups"]["Main"]
    assert mining["offsetX"] == 5
    assert mining["offsetY"] == 2


def test_reorder_profile_changes_traversal_order(tmp_path: Path) -> None:
    user_path = tmp_path / "overlay_groupings.user.json"
    user_path.write_text("{}\n", encoding="utf-8")
    store = OverlayProfileStore(user_path=user_path)
    store.create_profile("Mining")
    store.create_profile("Combat")
    store.create_profile("Trade")

    status = store.reorder_profile("Trade", 0)

    assert status["profiles"] == ["Trade", "Mining", "Combat", "Default"]
