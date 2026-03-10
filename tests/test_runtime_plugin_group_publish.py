from __future__ import annotations

import load


class _StubBroadcaster:
    def __init__(self) -> None:
        self.published = []

    def publish(self, payload):
        self.published.append(payload)


class _StubSpamTracker:
    def __init__(self) -> None:
        self.calls = []

    def record(self, plugin_name):
        self.calls.append(plugin_name)


class _StubGroupState:
    def __init__(self, drop: bool) -> None:
        self.drop = drop
        self.calls = 0

    def should_drop_payload(self, _payload):
        self.calls += 1
        return self.drop, "Alpha"


def _make_runtime(drop: bool):
    runtime = object.__new__(load._PluginRuntime)
    runtime._plugin_group_state = _StubGroupState(drop=drop)
    runtime._payload_spam_tracker = _StubSpamTracker()
    runtime._trace_payload_event = lambda *_args, **_kwargs: None
    runtime._log_payload = lambda *_args, **_kwargs: None
    runtime._trace_payload_marker = lambda *_args, **_kwargs: None
    runtime._plugin_name_for_payload = lambda _payload: ("PluginA", "id-1")
    runtime.broadcaster = _StubBroadcaster()
    return runtime


def test_publish_payload_drops_disabled_group_before_broadcast():
    runtime = _make_runtime(drop=True)

    runtime._publish_payload({"event": "LegacyOverlay", "id": "id-1"})

    assert runtime._plugin_group_state.calls == 1
    assert runtime.broadcaster.published == []
    assert runtime._payload_spam_tracker.calls == []


def test_publish_payload_broadcasts_when_group_enabled():
    runtime = _make_runtime(drop=False)

    runtime._publish_payload({"event": "LegacyOverlay", "id": "id-1"})

    assert runtime._plugin_group_state.calls == 1
    assert runtime.broadcaster.published == [{"event": "LegacyOverlay", "id": "id-1"}]
    assert runtime._payload_spam_tracker.calls == ["PluginA"]


def test_publish_group_clear_event_broadcasts_control_payload() -> None:
    runtime = _make_runtime(drop=False)

    runtime._publish_group_clear_event(["Alpha", "alpha", ""], "chat_off")

    assert runtime.broadcaster.published == [
        {
            "event": "OverlayPluginGroupClear",
            "plugin_groups": ["Alpha"],
            "source": "chat_off",
        }
    ]
