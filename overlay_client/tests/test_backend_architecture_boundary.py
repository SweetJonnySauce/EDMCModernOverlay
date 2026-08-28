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


def test_generic_backend_runtime_consumer_does_not_dispatch_gnome_presentation_policy() -> None:
    source = (REPO_ROOT / "overlay_client" / "backend" / "consumers.py").read_text(encoding="utf-8")
    runtime_source = source[source.index("def run_backend_presentation_cycle"):]

    assert "BackendInstance.GNOME_SHELL_WAYLAND" not in runtime_source
    assert "BackendInstance.GNOME_SHELL_RASTER" not in runtime_source
    assert "HelperKind.GNOME_SHELL_EXTENSION" not in runtime_source
    assert "_gnome_shell_helper_presentation" not in runtime_source


def test_x11_bundles_do_not_import_gnome_presentation_implementations() -> None:
    for bundle_name in ("native_x11.py", "xwayland_compat.py"):
        source = (REPO_ROOT / "overlay_client" / "backend" / "bundles" / bundle_name).read_text(encoding="utf-8")

        assert "_gnome_shell_helper_presentation" not in source
        assert "shell_raster_frame" not in source
