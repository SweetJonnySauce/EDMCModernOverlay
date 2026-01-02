from __future__ import annotations

import json
from pathlib import Path

import pytest

from overlay_plugin import preferences as prefs
from overlay_plugin.obs_capture_support import OBS_CAPTURE_PREF_KEY


class DummyConfig:
    """Minimal EDMC config stub with get/set support."""

    def __init__(self, initial: dict[str, object] | None = None) -> None:
        self.store: dict[str, object] = dict(initial or {})

    def get(self, key: str, default: object | None = None) -> object | None:
        return self.store.get(key, default)

    def get_str(self, key: str, default: object | None = None) -> object | None:
        return self.store.get(key, default)

    def get_int(self, key: str, default: object | None = None) -> object | None:
        return self.store.get(key, default)

    def get_bool(self, key: str, default: object | None = None) -> object | None:
        return self.store.get(key, default)

    def get_list(self, key: str, default: object | None = None) -> object | None:
        return self.store.get(key, default)

    def set(self, key: str, value: object) -> None:
        self.store[key] = value


def _shadow(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def plugin_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_preferences_save_persists_config_and_shadow(plugin_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = DummyConfig()
    monkeypatch.setattr(prefs, "EDMC_CONFIG", config)

    preferences = prefs.Preferences(plugin_dir, dev_mode=True)
    preferences.status_message_gutter = 30
    preferences.title_bar_height = 25
    preferences.payload_nudge_gutter = 40
    preferences.physical_clamp_overrides = {"DisplayPort-2": 1.0}
    preferences.obs_capture_friendly = True
    preferences.save()

    shadow = _shadow(plugin_dir / prefs.PREFERENCES_FILE)
    assert shadow["status_message_gutter"] == 30
    assert shadow["title_bar_height"] == 25
    assert shadow["payload_nudge_gutter"] == 40
    assert shadow["physical_clamp_overrides"] == {"DisplayPort-2": 1.0}
    assert shadow["obs_capture_friendly"] is True

    assert config.store[prefs._config_key("status_message_gutter")] == 30
    assert config.store[prefs._config_key("title_bar_height")] == 25
    assert config.store[prefs._config_key("payload_nudge_gutter")] == 40
    assert json.loads(config.store[prefs._config_key("physical_clamp_overrides")]) == {"DisplayPort-2": 1.0}
    assert config.store[prefs._config_key(OBS_CAPTURE_PREF_KEY)] is True


def test_preferences_reload_merges_shadow_when_config_empty(plugin_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first_config = DummyConfig()
    monkeypatch.setattr(prefs, "EDMC_CONFIG", first_config)

    first = prefs.Preferences(plugin_dir, dev_mode=True)
    first.status_message_gutter = 30
    first.title_bar_height = 25
    first.payload_nudge_gutter = 40
    first.physical_clamp_overrides = {"DisplayPort-2": 1.0, "HDMI-0": 1.25}
    first.obs_capture_friendly = True
    first.save()

    # Simulate a restart where EDMC's config lost the values but the shadow JSON still exists.
    reloaded_config = DummyConfig()
    monkeypatch.setattr(prefs, "EDMC_CONFIG", reloaded_config)

    reloaded = prefs.Preferences(plugin_dir, dev_mode=True)
    assert reloaded.status_message_gutter == 30
    assert reloaded.title_bar_height == 25
    assert reloaded.payload_nudge_gutter == 40
    assert reloaded.physical_clamp_overrides == {"DisplayPort-2": 1.0, "HDMI-0": 1.25}
    assert reloaded.obs_capture_friendly is True

    # After merge, values should be written back into EDMC config as well.
    assert reloaded_config.store[prefs._config_key("status_message_gutter")] == 30
    assert reloaded_config.store[prefs._config_key("title_bar_height")] == 25
    assert reloaded_config.store[prefs._config_key("payload_nudge_gutter")] == 40
    assert json.loads(reloaded_config.store[prefs._config_key("physical_clamp_overrides")]) == {
        "DisplayPort-2": 1.0,
        "HDMI-0": 1.25,
    }
    assert reloaded_config.store[prefs._config_key(OBS_CAPTURE_PREF_KEY)] is True


def test_preferences_locale_numbers_from_config(plugin_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def number_from_string(value: str) -> float:
        return float(value.replace(",", "."))

    config = DummyConfig(
        {
            prefs._config_key("overlay_opacity"): "0,75",
            prefs._config_key("min_font_point"): "7,5",
            prefs._config_key("max_font_point"): "15,5",
            prefs._config_key("gridline_spacing"): "123,4",
            prefs._config_key("payload_nudge_gutter"): "42,0",
            prefs._config_key("status_message_gutter"): "33,0",
            prefs._config_key("payload_log_delay_seconds"): "1,25",
            prefs._config_key("client_log_retention"): "not-a-number",
        }
    )
    monkeypatch.setattr(prefs, "_edmc_number_from_string", number_from_string)
    monkeypatch.setattr(prefs, "EDMC_CONFIG", config)

    preferences = prefs.Preferences(plugin_dir, dev_mode=True)
    assert preferences.overlay_opacity == pytest.approx(0.75)
    assert preferences.min_font_point == pytest.approx(7.5)
    assert preferences.max_font_point == pytest.approx(15.5)
    assert preferences.gridline_spacing == 123
    assert preferences.payload_nudge_gutter == 42
    assert preferences.status_message_gutter == 33
    assert preferences.payload_log_delay_seconds == pytest.approx(1.25)
    assert preferences.client_log_retention == prefs.DEFAULT_CLIENT_LOG_RETENTION
