from __future__ import annotations

import json
from pathlib import Path

from overlay_client.client_config import load_initial_settings


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
