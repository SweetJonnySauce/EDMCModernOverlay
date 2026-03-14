from __future__ import annotations

from pathlib import Path

from overlay_plugin import plugin_scan
from overlay_plugin.plugin_scan_services import PluginScanService


def test_get_cached_statuses_refreshes_once_when_empty(monkeypatch, tmp_path: Path) -> None:
    scan_calls = {"count": 0}

    def _scan_plugins(_root: Path, *, include_disabled: bool = False, self_root: Path | None = None):
        scan_calls["count"] += 1
        return [
            plugin_scan.PluginEntry(name="PluginA", path=tmp_path / "PluginA", disabled=False),
            plugin_scan.PluginEntry(name="PluginB", path=tmp_path / "PluginB", disabled=False),
            plugin_scan.PluginEntry(name="PluginIgnored", path=tmp_path / "PluginIgnored", disabled=False),
            plugin_scan.PluginEntry(name="PluginUnknown", path=tmp_path / "PluginUnknown", disabled=False),
        ]

    def _load_known_plugins() -> dict[str, dict[str, object]]:
        return {
            "plugina": {"config_key": "plugina_enabled", "enabled_values": ["Yes"]},
            "pluginb": {"config_key": "pluginb_enabled", "enabled_values": ["Yes"]},
            "pluginignored": {"ignore": True},
        }

    def _evaluate_overlay_status(name: str, _known: dict[str, dict[str, object]]):
        if name == "PluginA":
            return "enabled", "plugina_enabled", "Yes"
        return "disabled", "pluginb_enabled", "No"

    monkeypatch.setattr(plugin_scan, "scan_plugins", _scan_plugins)
    monkeypatch.setattr(plugin_scan, "load_known_plugins", _load_known_plugins)
    monkeypatch.setattr(plugin_scan, "evaluate_overlay_status", _evaluate_overlay_status)

    service = PluginScanService(plugin_dir=tmp_path / "EDMCModernOverlay", send_overlay_message=lambda _payload: True)
    first = service.get_cached_statuses(refresh_if_empty=True)
    second = service.get_cached_statuses(refresh_if_empty=True)

    assert scan_calls["count"] == 1
    assert dict(first) == {
        "plugina": "enabled",
        "pluginb": "disabled",
        "pluginignored": "ignored",
        "pluginunknown": "unknown",
    }
    assert dict(second) == dict(first)


def test_report_plugins_refreshes_cache(monkeypatch, tmp_path: Path) -> None:
    def _scan_plugins(_root: Path, *, include_disabled: bool = False, self_root: Path | None = None):
        return [plugin_scan.PluginEntry(name="PluginA", path=tmp_path / "PluginA", disabled=False)]

    def _load_known_plugins() -> dict[str, dict[str, object]]:
        return {"plugina": {"config_key": "plugina_enabled", "enabled_values": ["Yes"]}}

    def _evaluate_overlay_status(name: str, _known: dict[str, dict[str, object]]):
        assert name == "PluginA"
        return "enabled", "plugina_enabled", "Yes"

    monkeypatch.setattr(plugin_scan, "scan_plugins", _scan_plugins)
    monkeypatch.setattr(plugin_scan, "load_known_plugins", _load_known_plugins)
    monkeypatch.setattr(plugin_scan, "evaluate_overlay_status", _evaluate_overlay_status)

    sent_payloads: list[dict[str, object]] = []

    service = PluginScanService(
        plugin_dir=tmp_path / "EDMCModernOverlay",
        send_overlay_message=lambda payload: sent_payloads.append(dict(payload)) or True,
    )
    service.report_plugins()

    assert dict(service.get_cached_statuses()) == {"plugina": "enabled"}
    assert sent_payloads
