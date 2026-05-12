from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_follow_surface_does_not_import_gnome_helper_presentation_directly() -> None:
    source = (REPO_ROOT / "overlay_client" / "follow_surface.py").read_text(encoding="utf-8")

    assert "overlay_client.gnome_helper_presentation" not in source
    assert "run_gnome_shell_helper_presentation_cycle" not in source


def test_follow_surface_does_not_dispatch_gnome_helper_presentation_by_backend_enums() -> None:
    source = (REPO_ROOT / "overlay_client" / "follow_surface.py").read_text(encoding="utf-8")

    assert "BackendInstance.GNOME_SHELL_WAYLAND" not in source
    assert "HelperKind.GNOME_SHELL_EXTENSION" not in source
    assert "HelperPresentationAction" not in source
