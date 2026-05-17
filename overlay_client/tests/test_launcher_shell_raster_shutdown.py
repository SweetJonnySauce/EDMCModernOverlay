from __future__ import annotations

from overlay_client import launcher


def test_shell_raster_startup_clear_is_env_gated() -> None:
    calls: list[str] = []

    cleared = launcher._clear_shell_raster_frame_on_startup(
        env={},
        clear_func=lambda: calls.append("clear") or True,
    )

    assert cleared is False
    assert calls == []


def test_shell_raster_startup_clear_calls_backend_when_enabled() -> None:
    calls: list[str] = []

    cleared = launcher._clear_shell_raster_frame_on_startup(
        env={launcher.GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV: "1"},
        clear_func=lambda: calls.append("clear") or True,
    )

    assert cleared is True
    assert calls == ["clear"]


def test_shell_raster_shutdown_clear_is_env_gated() -> None:
    calls: list[str] = []

    cleared = launcher._clear_shell_raster_frame_on_shutdown(
        env={},
        clear_func=lambda: calls.append("clear") or True,
    )

    assert cleared is False
    assert calls == []


def test_shell_raster_shutdown_clear_calls_backend_when_enabled() -> None:
    calls: list[str] = []

    cleared = launcher._clear_shell_raster_frame_on_shutdown(
        env={launcher.GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV: "1"},
        clear_func=lambda: calls.append("clear") or True,
    )

    assert cleared is True
    assert calls == ["clear"]
