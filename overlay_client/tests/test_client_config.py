from __future__ import annotations

import json
from pathlib import Path

from overlay_client.client_config import DeveloperHelperConfig, load_initial_settings


def _write_settings(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_initial_settings_reads_manual_backend_override(tmp_path: Path) -> None:
    settings_path = tmp_path / "overlay_settings.json"
    _write_settings(settings_path, {"manual_backend_override": "xwayland_compat"})

    settings = load_initial_settings(settings_path)

    assert settings.manual_backend_override == "xwayland_compat"


def test_load_initial_settings_normalises_auto_backend_override(tmp_path: Path) -> None:
    settings_path = tmp_path / "overlay_settings.json"
    _write_settings(settings_path, {"manual_backend_override": "auto"})

    settings = load_initial_settings(settings_path)

    assert settings.manual_backend_override == ""


def test_load_initial_settings_preserves_invalid_manual_backend_override(tmp_path: Path) -> None:
    settings_path = tmp_path / "overlay_settings.json"
    _write_settings(settings_path, {"manual_backend_override": "bogus_backend"})

    settings = load_initial_settings(settings_path)

    assert settings.manual_backend_override == "bogus_backend"


def test_load_initial_settings_migrates_legacy_force_xwayland(tmp_path: Path) -> None:
    settings_path = tmp_path / "overlay_settings.json"
    _write_settings(settings_path, {"force_xwayland": True})

    settings = load_initial_settings(settings_path)

    assert settings.manual_backend_override == "xwayland_compat"


def test_load_initial_settings_reads_keep_overlay_visible(tmp_path: Path) -> None:
    settings_path = tmp_path / "overlay_settings.json"
    _write_settings(settings_path, {"keep_overlay_visible": True})

    settings = load_initial_settings(settings_path)

    assert settings.keep_overlay_visible is True
    assert settings.force_render is True


def test_load_initial_settings_accepts_legacy_force_render(tmp_path: Path) -> None:
    settings_path = tmp_path / "overlay_settings.json"
    _write_settings(settings_path, {"force_render": True})

    settings = load_initial_settings(settings_path)

    assert settings.keep_overlay_visible is True


def test_load_initial_settings_prefers_keep_overlay_visible_over_legacy_force_render(tmp_path: Path) -> None:
    settings_path = tmp_path / "overlay_settings.json"
    _write_settings(settings_path, {"keep_overlay_visible": False, "force_render": True})

    settings = load_initial_settings(settings_path)

    assert settings.keep_overlay_visible is False


def test_developer_helper_config_keep_overlay_visible_precedence() -> None:
    config = DeveloperHelperConfig.from_payload({"keep_overlay_visible": False, "force_render": True})

    assert config.keep_overlay_visible is False
    assert config.force_render is False


def test_developer_helper_config_accepts_legacy_force_render() -> None:
    config = DeveloperHelperConfig.from_payload({"force_render": True})

    assert config.keep_overlay_visible is True
