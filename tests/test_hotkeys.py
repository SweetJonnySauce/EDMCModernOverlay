from __future__ import annotations

import logging
from typing import Any, List

from overlay_plugin import hotkeys


class _HostState:
    def __init__(self, *, opacity: int = 100, running: bool = True) -> None:
        self.opacity = opacity
        self.running = running
        self.toggle_calls = 0

    def is_running(self) -> bool:
        return self.running

    def get_payload_opacity(self) -> int:
        return self.opacity

    def toggle_payload_opacity(self) -> None:
        self.toggle_calls += 1
        self.opacity = 0 if self.opacity > 0 else 64


class _FakeAction:
    def __init__(self, **kwargs: Any) -> None:
        self.id = kwargs.get("id")
        self.label = kwargs.get("label")
        self.plugin = kwargs.get("plugin")
        self.callback = kwargs.get("callback")
        self.thread_policy = kwargs.get("thread_policy")
        self.cardinality = kwargs.get("cardinality")
        self.enabled = kwargs.get("enabled")


class _FakeHotkeysApi:
    def __init__(self, register_results: List[Any] | None = None) -> None:
        self.registered: List[_FakeAction] = []
        self._register_results = list(register_results or [])

    def register_action(self, action: _FakeAction) -> bool:
        self.registered.append(action)
        if self._register_results:
            result = self._register_results.pop(0)
            if isinstance(result, Exception):
                raise result
            return bool(result)
        return True

def _make_manager(state: _HostState) -> hotkeys.HotkeysManager:
    return hotkeys.HotkeysManager(
        is_running=state.is_running,
        get_payload_opacity=state.get_payload_opacity,
        toggle_payload_opacity=state.toggle_payload_opacity,
        logger=logging.getLogger("test-hotkeys"),
        plugin_name="EDMCModernOverlay",
    )


def _patch_hotkeys_imports(
    monkeypatch,
    *,
    api: Any | None = None,
    api_error: Exception | None = None,
    action_error: Exception | None = None,
) -> None:
    def _fake_import_hotkeys_api_module():
        if api_error is not None:
            raise api_error
        return api

    def _fake_import_hotkeys_action_class():
        if action_error is not None:
            raise action_error
        return _FakeAction

    monkeypatch.setattr(hotkeys, "_import_hotkeys_api_module", _fake_import_hotkeys_api_module)
    monkeypatch.setattr(hotkeys, "_import_hotkeys_action_class", _fake_import_hotkeys_action_class)


def test_hotkeys_start_registers_overlay_actions(monkeypatch):
    state = _HostState()
    manager = _make_manager(state)
    api = _FakeHotkeysApi()

    _patch_hotkeys_imports(monkeypatch, api=api)

    assert manager.start() is True
    assert [action.label for action in api.registered] == ["Overlay On", "Overlay Off"]
    assert [action.id for action in api.registered] == [
        hotkeys.HOTKEYS_OVERLAY_ON_ACTION_ID,
        hotkeys.HOTKEYS_OVERLAY_OFF_ACTION_ID,
    ]
    assert [action.thread_policy for action in api.registered] == ["main", "main"]
    assert [action.cardinality for action in api.registered] == ["single", "single"]


def test_hotkeys_callbacks_enforce_noop_boundaries():
    state = _HostState(opacity=50)
    manager = _make_manager(state)

    manager._overlay_on_callback()
    assert state.toggle_calls == 0
    assert state.opacity == 50

    state.opacity = 0
    manager._overlay_on_callback()
    assert state.toggle_calls == 1
    assert state.opacity == 64

    state.opacity = 0
    manager._overlay_off_callback()
    assert state.toggle_calls == 1
    assert state.opacity == 0

    state.opacity = 40
    manager._overlay_off_callback()
    assert state.toggle_calls == 2
    assert state.opacity == 0


def test_import_failures_schedule_exponential_retry(monkeypatch):
    state = _HostState()
    manager = _make_manager(state)
    created_timers: List[Any] = []

    class _FakeTimer:
        def __init__(self, interval, function, args=None, kwargs=None):
            self.interval = interval
            self.function = function
            self.args = args or ()
            self.kwargs = kwargs or {}
            self.cancelled = False
            created_timers.append(self)

        def start(self):
            return

        def cancel(self):
            self.cancelled = True

        def fire(self):
            self.function(*self.args, **self.kwargs)

    monkeypatch.setattr(hotkeys.threading, "Timer", _FakeTimer)
    _patch_hotkeys_imports(monkeypatch, api_error=ModuleNotFoundError("EDMCHotkeys"))

    assert manager.start() is False
    idx = 0
    while idx < len(created_timers):
        timer = created_timers[idx]
        idx += 1
        timer.fire()

    assert [timer.interval for timer in created_timers] == list(hotkeys.HOTKEYS_RETRY_DELAYS_SECONDS)


def test_registration_false_schedules_retry(monkeypatch):
    state = _HostState()
    manager = _make_manager(state)
    created_timers: List[Any] = []
    api = _FakeHotkeysApi(register_results=[False, True, True])

    class _FakeTimer:
        def __init__(self, interval, function, args=None, kwargs=None):
            self.interval = interval
            self.function = function
            self.args = args or ()
            self.kwargs = kwargs or {}
            created_timers.append(self)

        def start(self):
            return

        def cancel(self):
            return

        def fire(self):
            self.function(*self.args, **self.kwargs)

    monkeypatch.setattr(hotkeys.threading, "Timer", _FakeTimer)
    _patch_hotkeys_imports(monkeypatch, api=api)

    assert manager.start() is False
    assert [timer.interval for timer in created_timers] == [hotkeys.HOTKEYS_RETRY_DELAYS_SECONDS[0]]
    created_timers[0].fire()
    assert set(manager._registered_action_ids) == {
        hotkeys.HOTKEYS_OVERLAY_ON_ACTION_ID,
        hotkeys.HOTKEYS_OVERLAY_OFF_ACTION_ID,
    }


def test_registration_exception_does_not_retry(monkeypatch):
    state = _HostState()
    manager = _make_manager(state)
    created_timers: List[Any] = []
    api = _FakeHotkeysApi(register_results=[RuntimeError("boom")])

    class _FakeTimer:
        def __init__(self, interval, function, args=None, kwargs=None):
            created_timers.append(self)

        def start(self):
            return

        def cancel(self):
            return

    monkeypatch.setattr(hotkeys.threading, "Timer", _FakeTimer)
    _patch_hotkeys_imports(monkeypatch, api=api)

    assert manager.start() is False
    assert created_timers == []


def test_stop_cancels_retry_and_leaves_registrations_managed(monkeypatch):
    state = _HostState()
    manager = _make_manager(state)
    created_timers: List[Any] = []
    api = _FakeHotkeysApi()
    fail_import = {"value": True}

    class _FakeTimer:
        def __init__(self, interval, function, args=None, kwargs=None):
            self.cancelled = False
            created_timers.append(self)

        def start(self):
            return

        def cancel(self):
            self.cancelled = True

    def _fake_import_hotkeys_api_module():
        if fail_import["value"]:
            raise ModuleNotFoundError("EDMCHotkeys")
        return api

    monkeypatch.setattr(hotkeys.threading, "Timer", _FakeTimer)
    monkeypatch.setattr(hotkeys, "_import_hotkeys_api_module", _fake_import_hotkeys_api_module)
    monkeypatch.setattr(hotkeys, "_import_hotkeys_action_class", lambda: _FakeAction)

    # First start schedules a retry timer due to import failure.
    assert manager.start() is False
    assert len(created_timers) == 1
    manager.stop()
    assert created_timers[0].cancelled is True

    # Second start succeeds and stop keeps local registration state intact.
    fail_import["value"] = False
    assert manager.start() is True
    manager.stop()
    assert sorted(manager._registered_action_ids) == sorted(
        [hotkeys.HOTKEYS_OVERLAY_ON_ACTION_ID, hotkeys.HOTKEYS_OVERLAY_OFF_ACTION_ID]
    )
