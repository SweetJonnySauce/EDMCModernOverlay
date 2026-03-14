from __future__ import annotations

from overlay_client.control_surface import ControlSurfaceMixin
from overlay_client.legacy_store import LegacyItem, LegacyItemStore


class _PayloadModel:
    def __init__(self, store: LegacyItemStore) -> None:
        self.store = store


class _Window(ControlSurfaceMixin):
    def __init__(self) -> None:
        self._payload_model = _PayloadModel(LegacyItemStore())
        self._cycle_payload_enabled = False
        self.sync_calls = 0
        self.cache_dirty_calls = 0
        self.repaint_calls: list[tuple[str, bool]] = []

    def _sync_cycle_items(self) -> None:
        self.sync_calls += 1

    def _mark_legacy_cache_dirty(self) -> None:
        self.cache_dirty_calls += 1

    def _request_repaint(self, reason: str, *, immediate: bool = False) -> None:
        self.repaint_calls.append((reason, bool(immediate)))


def test_clear_plugin_groups_removes_targeted_items_and_repaints() -> None:
    window = _Window()
    window._payload_model.store.set(
        "a-1",
        LegacyItem(item_id="a-1", kind="message", data={"text": "alpha"}, plugin="PluginA"),
    )
    window._payload_model.store.set(
        "b-1",
        LegacyItem(item_id="b-1", kind="message", data={"text": "beta"}, plugin="PluginA"),
    )

    def _resolve_group(payload):
        payload_id = str(payload.get("id") or "")
        if payload_id.startswith("a-"):
            return "Alpha"
        if payload_id.startswith("b-"):
            return "Beta"
        return None

    removed = window.clear_plugin_groups(["alpha"], resolve_group_name=_resolve_group)

    assert removed == 1
    assert window._payload_model.store.get("a-1") is None
    assert window._payload_model.store.get("b-1") is not None
    assert window.cache_dirty_calls == 1
    assert window.repaint_calls == [("plugin_group_clear", True)]


def test_clear_plugin_groups_noop_when_no_matches() -> None:
    window = _Window()
    window._payload_model.store.set(
        "a-1",
        LegacyItem(item_id="a-1", kind="message", data={"text": "alpha"}, plugin="PluginA"),
    )

    removed = window.clear_plugin_groups(["beta"], resolve_group_name=lambda _payload: "Alpha")

    assert removed == 0
    assert window._payload_model.store.get("a-1") is not None
    assert window.cache_dirty_calls == 0
    assert window.repaint_calls == []
