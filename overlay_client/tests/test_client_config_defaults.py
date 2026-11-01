from __future__ import annotations

import json
from pathlib import Path

from overlay_client.client_config import load_initial_settings


def test_load_initial_settings_without_shadow_file_uses_full_window_defaults(tmp_path: Path) -> None:
    settings = load_initial_settings(tmp_path / "overlay_settings.json")

    assert settings.force_xwayland is True
    assert settings.xwayland_on_wayland is False
    assert settings.status_bottom_margin == 40
    assert settings.title_bar_height == 30
    assert settings.scale_mode == "fill"
    assert settings.payload_nudge_gutter == 20


def test_load_initial_settings_reads_xwayland_on_wayland(tmp_path: Path) -> None:
    settings_path = tmp_path / "overlay_settings.json"
    settings_path.write_text(json.dumps({"xwayland_on_wayland": True}), encoding="utf-8")

    settings = load_initial_settings(settings_path)

    assert settings.xwayland_on_wayland is True
