from __future__ import annotations

import logging
from typing import Any, List, Optional, Sequence

from overlay_plugin import hotkeys


class _HostState:
    def __init__(self, *, running: bool = True) -> None:
        self.running = running
        self.set_calls: list[tuple[bool, Optional[tuple[str, ...]], str]] = []
        self.toggle_calls: list[tuple[Optional[tuple[str, ...]], str]] = []
        self.launch_calls = 0
        self.launch_should_fail = False
        self.profile_calls: list[str] = []
        self.profile_cycle_calls: list[int] = []
        self.states = {
            "Group A": True,
            "Group B": True,
        }

    def is_running(self) -> bool:
        return self.running

    def set_group_state(self, enabled: bool, *, group_names: Optional[Sequence[str]] = None, source: str = "") -> None:
        targets = tuple(group_names) if group_names is not None else None
        self.set_calls.append((bool(enabled), targets, source))
        resolved = list(group_names) if group_names is not None else list(self.states.keys())
        for name in resolved:
            if name in self.states:
                self.states[name] = bool(enabled)

    def toggle_group_state(self, *, group_names: Optional[Sequence[str]] = None, source: str = "") -> None:
        targets = tuple(group_names) if group_names is not None else None
        self.toggle_calls.append((targets, source))
        resolved = list(group_names) if group_names is not None else list(self.states.keys())
        for name in resolved:
            if name in self.states:
                self.states[name] = not self.states[name]

    def launch_controller(self) -> None:
        if self.launch_should_fail:
            raise RuntimeError("boom")
        self.launch_calls += 1

    def set_profile(self, name: str) -> None:
        self.profile_calls.append(str(name))

    def cycle_profile(self, direction: int) -> None:
        self.profile_cycle_calls.append(int(direction))


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
        set_group_state=state.set_group_state,
        toggle_group_state=state.toggle_group_state,
        launch_controller=state.launch_controller,
        set_profile=state.set_profile,
        cycle_profile=state.cycle_profile,
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
    assert [action.label for action in api.registered] == [
        "Overlay On",
        "Overlay Off",
        "Toggle Overlay",
        hotkeys.HOTKEYS_LAUNCH_CONTROLLER_LABEL,
        hotkeys.HOTKEYS_SET_PROFILE_LABEL,
        hotkeys.HOTKEYS_PROFILE_NEXT_LABEL,
        hotkeys.HOTKEYS_PROFILE_PREV_LABEL,
    ]
    assert [action.id for action in api.registered] == [
        hotkeys.HOTKEYS_OVERLAY_ON_ACTION_ID,
        hotkeys.HOTKEYS_OVERLAY_OFF_ACTION_ID,
        hotkeys.HOTKEYS_OVERLAY_TOGGLE_ACTION_ID,
        hotkeys.HOTKEYS_LAUNCH_CONTROLLER_ACTION_ID,
        hotkeys.HOTKEYS_SET_PROFILE_ACTION_ID,
        hotkeys.HOTKEYS_PROFILE_NEXT_ACTION_ID,
        hotkeys.HOTKEYS_PROFILE_PREV_ACTION_ID,
    ]
    assert [action.thread_policy for action in api.registered] == [
        "main",
        "main",
        "main",
        "main",
        "main",
        "main",
        "main",
    ]
    assert [action.cardinality for action in api.registered] == [
        "multi",
        "multi",
        "multi",
        "single",
        "single",
        "single",
        "single",
    ]


def test_hotkeys_launch_controller_callback_delegates():
    state = _HostState()
    manager = _make_manager(state)

    manager._launch_controller_callback()

    assert state.launch_calls == 1


def test_hotkeys_launch_controller_callback_handles_errors():
    state = _HostState()
    state.launch_should_fail = True
    manager = _make_manager(state)

    manager._launch_controller_callback()

    assert state.launch_calls == 0


def test_hotkeys_set_profile_callback_delegates() -> None:
    state = _HostState()
    manager = _make_manager(state)

    manager._set_profile_callback(payload={"profile": "Mining"})

    assert state.profile_calls == ["Mining"]


def test_hotkeys_set_profile_callback_requires_profile_name() -> None:
    state = _HostState()
    manager = _make_manager(state)

    manager._set_profile_callback(payload={})

    assert state.profile_calls == []


def test_hotkeys_profile_cycle_callbacks_delegate() -> None:
    state = _HostState()
    manager = _make_manager(state)

    manager._cycle_profile_callback(direction=1)
    manager._cycle_profile_callback(direction=-1)

    assert state.profile_cycle_calls == [1, -1]


def test_hotkeys_callbacks_apply_global_and_targeted_actions():
    state = _HostState()
    manager = _make_manager(state)

    manager._overlay_on_callback()
    assert state.set_calls[-1] == (True, None, "hotkey_overlay_on")
    assert state.states == {"Group A": True, "Group B": True}

    manager._overlay_off_callback()
    assert state.set_calls[-1] == (False, None, "hotkey_overlay_off")
    assert state.states == {"Group A": False, "Group B": False}

    manager._overlay_toggle_callback()
    assert state.toggle_calls[-1] == (None, "hotkey_overlay_toggle")
    assert state.states == {"Group A": True, "Group B": True}

    manager._overlay_off_callback(payload={"plugin_group": "Group A"})
    assert state.set_calls[-1] == (False, ("Group A",), "hotkey_overlay_off")
    assert state.states == {"Group A": False, "Group B": True}

    manager._overlay_toggle_callback(payload={"plugin_groups": ["Group A", "Group B", "Group A"]})
    assert state.toggle_calls[-1] == (("Group A", "Group B"), "hotkey_overlay_toggle")
    assert state.states == {"Group A": True, "Group B": False}


def test_hotkeys_target_payload_unions_plugin_group_and_plugin_groups() -> None:
    state = _HostState()
    manager = _make_manager(state)

    manager._overlay_off_callback(
        payload={
            "plugin_group": "Group B",
            "plugin_groups": ["Group A", "group b", "Group A"],
        }
    )

    assert state.set_calls[-1] == (False, ("Group B", "Group A"), "hotkey_overlay_off")
    assert state.states == {"Group A": False, "Group B": False}


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
    api = _FakeHotkeysApi(register_results=[False, True, True, True])

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
        hotkeys.HOTKEYS_OVERLAY_TOGGLE_ACTION_ID,
        hotkeys.HOTKEYS_LAUNCH_CONTROLLER_ACTION_ID,
        hotkeys.HOTKEYS_SET_PROFILE_ACTION_ID,
        hotkeys.HOTKEYS_PROFILE_NEXT_ACTION_ID,
        hotkeys.HOTKEYS_PROFILE_PREV_ACTION_ID,
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
        [
            hotkeys.HOTKEYS_OVERLAY_ON_ACTION_ID,
            hotkeys.HOTKEYS_OVERLAY_OFF_ACTION_ID,
            hotkeys.HOTKEYS_OVERLAY_TOGGLE_ACTION_ID,
            hotkeys.HOTKEYS_LAUNCH_CONTROLLER_ACTION_ID,
            hotkeys.HOTKEYS_SET_PROFILE_ACTION_ID,
            hotkeys.HOTKEYS_PROFILE_NEXT_ACTION_ID,
            hotkeys.HOTKEYS_PROFILE_PREV_ACTION_ID,
        ]
    )
