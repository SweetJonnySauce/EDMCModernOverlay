from __future__ import annotations

from overlay_client.legacy_store import LegacyItem, LegacyItemStore
from overlay_client.plugin_group_clear import clear_store_for_groups, parse_clear_targets


def test_parse_clear_targets_unions_and_dedupes() -> None:
    payload = {
        "plugin_group": "Alpha",
        "plugin_groups": ["Beta", "alpha", "Beta", "", 123],
    }
    assert parse_clear_targets(payload) == ["Alpha", "Beta"]


def test_clear_store_for_groups_removes_only_targeted_payloads() -> None:
    store = LegacyItemStore()
    store.set("a-1", LegacyItem(item_id="a-1", kind="message", data={"text": "a"}, plugin="PluginA"))
    store.set("b-1", LegacyItem(item_id="b-1", kind="message", data={"text": "b"}, plugin="PluginA"))
    store.set("c-1", LegacyItem(item_id="c-1", kind="message", data={"text": "c"}, plugin="PluginA"))

    def _resolve_group(payload):
        payload_id = str(payload.get("id") or "")
        if payload_id.startswith("a-"):
            return "Alpha"
        if payload_id.startswith("b-"):
            return "Beta"
        return None

    removed = clear_store_for_groups(
        store=store,
        target_groups=["alpha"],
        resolve_group_name=_resolve_group,
    )

    assert removed == 1
    assert store.get("a-1") is None
    assert store.get("b-1") is not None
    assert store.get("c-1") is not None
