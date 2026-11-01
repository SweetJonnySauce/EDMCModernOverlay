from __future__ import annotations

import json
import logging
import types

from overlay_client import window_tracking
from overlay_client.window_tracking import WindowState


def test_gnome_tracker_falls_back_to_x11_without_extension(monkeypatch) -> None:
    expected = WindowState(
        x=10,
        y=20,
        width=800,
        height=600,
        is_foreground=True,
        is_visible=True,
        identifier="0x1234",
    )

    class FakeFallbackTracker:
        def __init__(self, logger, title_hint, monitor_provider) -> None:
            self.monitor_provider = monitor_provider

        def set_monitor_provider(self, provider) -> None:
            self.monitor_provider = provider

        def poll(self):
            return expected

    def fail_gdbus(command, **kwargs):
        return types.SimpleNamespace(returncode=1, stdout="", stderr="GNOME extension is not installed")

    monkeypatch.setattr(window_tracking.subprocess, "run", fail_gdbus)
    monkeypatch.setattr(window_tracking, "_WmctrlTracker", FakeFallbackTracker)
    monkeypatch.setattr(window_tracking.sys, "platform", "linux")
    monkeypatch.setenv("EDMC_OVERLAY_SESSION_TYPE", "wayland")
    monkeypatch.setenv("EDMC_OVERLAY_COMPOSITOR", "gnome-shell")
    monkeypatch.setenv("EDMC_OVERLAY_FORCE_XWAYLAND", "1")

    tracker = window_tracking.create_elite_window_tracker(logging.getLogger("test.gnome"))

    assert tracker is not None
    assert tracker.poll() == expected


def test_force_xwayland_keeps_x11_tracker_for_non_gnome_wayland(monkeypatch) -> None:
    selected = []

    class FakeWaylandTracker:
        def __init__(self, logger, title_hint, monitor_provider) -> None:
            selected.append("wayland")

    class FakeFallbackTracker:
        def __init__(self, logger, title_hint, monitor_provider) -> None:
            selected.append("x11")

        def set_monitor_provider(self, provider) -> None:
            pass

        def poll(self):
            return None

    monkeypatch.setattr(window_tracking, "_SwayTracker", FakeWaylandTracker)
    monkeypatch.setattr(window_tracking, "_WmctrlTracker", FakeFallbackTracker)
    monkeypatch.setattr(window_tracking.sys, "platform", "linux")
    monkeypatch.setenv("EDMC_OVERLAY_SESSION_TYPE", "wayland")
    monkeypatch.setenv("EDMC_OVERLAY_COMPOSITOR", "sway")
    monkeypatch.setenv("EDMC_OVERLAY_FORCE_XWAYLAND", "1")

    tracker = window_tracking.create_elite_window_tracker(logging.getLogger("test.sway"))

    assert tracker is not None
    assert selected == ["x11"]


def test_gnome_tracker_falls_back_to_x11_when_elite_is_not_in_window_calls(monkeypatch) -> None:
    expected = WindowState(
        x=1080,
        y=311,
        width=1920,
        height=1080,
        is_foreground=True,
        is_visible=True,
        identifier="0x1234",
    )
    commands = []

    class FakeFallbackTracker:
        def __init__(self, logger, title_hint, monitor_provider) -> None:
            pass

        def set_monitor_provider(self, provider) -> None:
            pass

        def poll(self):
            return expected

    def fake_gdbus(command, **kwargs):
        commands.append(command)
        return types.SimpleNamespace(returncode=0, stdout=repr((json.dumps([]),)), stderr="")

    monkeypatch.setattr(window_tracking.subprocess, "run", fake_gdbus)
    monkeypatch.setattr(window_tracking, "_WmctrlTracker", FakeFallbackTracker)
    monkeypatch.setattr(window_tracking.sys, "platform", "linux")
    monkeypatch.setenv("EDMC_OVERLAY_SESSION_TYPE", "wayland")
    monkeypatch.setenv("EDMC_OVERLAY_COMPOSITOR", "gnome-shell")
    monkeypatch.setenv("EDMC_OVERLAY_FORCE_XWAYLAND", "0")
    monkeypatch.delenv("FLATPAK_ID", raising=False)

    tracker = window_tracking.create_elite_window_tracker(logging.getLogger("test.gnome"))

    assert tracker is not None
    assert tracker.poll() == expected
    assert len(commands) == 1
    assert commands[0][commands[0].index("--method") + 1].endswith(".List")


def test_gnome_tracker_uses_host_gdbus_inside_flatpak(monkeypatch) -> None:
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return types.SimpleNamespace(returncode=0, stdout=repr((json.dumps([]),)), stderr="")

    class FakeFallbackTracker:
        def __init__(self, logger, title_hint, monitor_provider) -> None:
            pass

        def set_monitor_provider(self, provider) -> None:
            pass

        def poll(self):
            return None

    monkeypatch.setattr(window_tracking.subprocess, "run", fake_run)
    monkeypatch.setattr(window_tracking, "_WmctrlTracker", FakeFallbackTracker)
    monkeypatch.setattr(window_tracking.sys, "platform", "linux")
    monkeypatch.setenv("EDMC_OVERLAY_SESSION_TYPE", "wayland")
    monkeypatch.setenv("EDMC_OVERLAY_COMPOSITOR", "gnome-shell")
    monkeypatch.setenv("EDMC_OVERLAY_FORCE_XWAYLAND", "1")
    monkeypatch.setenv("EDMC_OVERLAY_IS_FLATPAK", "1")
    monkeypatch.setenv("FLATPAK_ID", "io.edcd.EDMarketConnector")

    tracker = window_tracking.create_elite_window_tracker(logging.getLogger("test.gnome"))

    assert tracker is not None
    assert tracker.poll() is None
    assert commands[0][:4] == ["flatpak-spawn", "--host", "gdbus", "call"]