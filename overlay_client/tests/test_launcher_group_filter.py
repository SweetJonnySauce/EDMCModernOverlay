from __future__ import annotations

from overlay_client import launcher


class _StubHelper:
    def __init__(self) -> None:
        self.config_calls = 0
        self.legacy_calls = 0

    def apply_config(self, _window, _payload) -> None:
        self.config_calls += 1

    def handle_legacy_payload(self, _window, _payload) -> None:
        self.legacy_calls += 1


class _StubWindow:
    def __init__(self) -> None:
        self.controller_signal_calls = 0
        self.messages = []
        self.clear_calls = []

    def handle_controller_active_signal(self) -> None:
        self.controller_signal_calls += 1

    def display_message(self, text: str, ttl=None) -> None:
        self.messages.append((text, ttl))

    def clear_plugin_groups(self, group_names, *, resolve_group_name=None) -> None:
        self.clear_calls.append((list(group_names), bool(callable(resolve_group_name))))


class _StubFilter:
    def __init__(self, allow: bool) -> None:
        self.allow = allow
        self.config_updates = 0

    def update_from_config(self, _payload) -> None:
        self.config_updates += 1

    def allow_payload(self, _payload) -> bool:
        return self.allow

    def resolve_group_name(self, payload) -> str | None:
        return payload.get("plugin_group")


def test_payload_handler_updates_group_filter_on_overlay_config() -> None:
    helper = _StubHelper()
    window = _StubWindow()
    group_filter = _StubFilter(allow=True)
    handler = launcher._build_payload_handler(helper, window, group_filter=group_filter)

    handler({"event": "OverlayConfig"})

    assert helper.config_calls == 1
    assert group_filter.config_updates == 1


def test_payload_handler_drops_legacy_overlay_when_filter_blocks() -> None:
    helper = _StubHelper()
    window = _StubWindow()
    group_filter = _StubFilter(allow=False)
    handler = launcher._build_payload_handler(helper, window, group_filter=group_filter)

    handler({"event": "LegacyOverlay", "type": "message", "id": "x", "text": "hello"})

    assert helper.legacy_calls == 0


def test_payload_handler_processes_legacy_overlay_when_filter_allows() -> None:
    helper = _StubHelper()
    window = _StubWindow()
    group_filter = _StubFilter(allow=True)
    handler = launcher._build_payload_handler(helper, window, group_filter=group_filter)

    handler({"event": "LegacyOverlay", "type": "message", "id": "x", "text": "hello"})

    assert helper.legacy_calls == 1


def test_payload_handler_clears_plugin_groups_on_control_event() -> None:
    helper = _StubHelper()
    window = _StubWindow()
    group_filter = _StubFilter(allow=True)
    handler = launcher._build_payload_handler(helper, window, group_filter=group_filter)

    handler({"event": "OverlayPluginGroupClear", "plugin_groups": ["Alpha", "alpha", ""]})

    assert window.clear_calls == [(["Alpha"], True)]
    assert helper.legacy_calls == 0
