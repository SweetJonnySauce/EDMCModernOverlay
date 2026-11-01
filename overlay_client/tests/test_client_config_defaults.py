from __future__ import annotations

from pathlib import Path

from overlay_client.client_config import load_initial_settings


def test_load_initial_settings_without_shadow_file_uses_full_window_defaults(tmp_path: Path) -> None:
    settings = load_initial_settings(tmp_path / "overlay_settings.json")

    assert settings.force_xwayland is True
    assert settings.status_bottom_margin == 40
    assert settings.title_bar_height == 30
    assert settings.scale_mode == "fill"
    assert settings.payload_nudge_gutter == 20
