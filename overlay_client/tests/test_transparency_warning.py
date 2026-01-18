from __future__ import annotations

from overlay_client import launcher


class _StubHelper:
    def __init__(self) -> None:
        self.config_calls = 0

    def apply_config(self, _window, _payload) -> None:
        self.config_calls += 1


class _StubWindow:
    def __init__(self) -> None:
        self.warn_calls = 0

    def maybe_warn_transparent_overlay(self) -> None:
        self.warn_calls += 1


def test_overlay_config_does_not_trigger_warning() -> None:
    helper = _StubHelper()
    window = _StubWindow()
    handler = launcher._build_payload_handler(helper, window)

    handler({"event": "OverlayConfig"})

    assert helper.config_calls == 1
    assert window.warn_calls == 0


def test_warn_transparent_on_startup_invokes_warning_once() -> None:
    window = _StubWindow()

    launcher._warn_transparent_on_startup(window)

    assert window.warn_calls == 1
