from __future__ import annotations

import json
from pathlib import Path


def test_release_excludes_manifest_excludes_overlay_settings_shadow_file() -> None:
    manifest_path = Path(__file__).resolve().parent.parent / "scripts" / "release_excludes.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    files = manifest.get("files")

    assert isinstance(files, list)
    assert "overlay_groupings.user.json" in files
    assert "overlay_settings.json" in files


def test_release_excludes_manifest_excludes_preferred_font_preferences() -> None:
    manifest_path = Path(__file__).resolve().parent.parent / "scripts" / "release_excludes.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    substrings = manifest.get("substrings")

    assert isinstance(substrings, list)
    assert "overlay_client/fonts/preferred_fonts.txt" in substrings


def test_release_excludes_manifest_excludes_emoji_fallback_preferences() -> None:
    manifest_path = Path(__file__).resolve().parent.parent / "scripts" / "release_excludes.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    substrings = manifest.get("substrings")

    assert isinstance(substrings, list)
    assert "overlay_client/fonts/emoji_fallbacks.txt" in substrings
