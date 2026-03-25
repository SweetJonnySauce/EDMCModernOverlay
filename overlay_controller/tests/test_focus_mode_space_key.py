from __future__ import annotations

from types import SimpleNamespace

from overlay_controller import overlay_controller as oc


class _DummyWidget:
    def __init__(self, widget_class: str) -> None:
        self._widget_class = widget_class

    def winfo_class(self) -> str:
        return self._widget_class


def test_space_in_text_input_does_not_exit_focus_mode() -> None:
    exit_calls: list[str] = []
    handle_calls: list[str] = []
    active_widget = SimpleNamespace(
        handle_key=lambda _keysym, _event=None: handle_calls.append("called") or False
    )
    app = SimpleNamespace(
        widget_select_mode=False,
        _get_active_focus_widget=lambda: active_widget,
        _is_text_input_widget=oc.OverlayConfigApp._is_text_input_widget,
        exit_focus_mode=lambda: exit_calls.append("exit"),
    )
    event = SimpleNamespace(widget=_DummyWidget("Entry"))

    handled = oc.OverlayConfigApp._handle_active_widget_key(app, "space", event)

    assert handled is False
    assert handle_calls == []
    assert exit_calls == []


def test_space_on_non_text_widget_still_exits_when_unhandled() -> None:
    exit_calls: list[str] = []
    active_widget = SimpleNamespace(handle_key=lambda _keysym, _event=None: False)
    app = SimpleNamespace(
        widget_select_mode=False,
        _get_active_focus_widget=lambda: active_widget,
        _is_text_input_widget=oc.OverlayConfigApp._is_text_input_widget,
        exit_focus_mode=lambda: exit_calls.append("exit"),
    )
    event = SimpleNamespace(widget=_DummyWidget("Button"))

    handled = oc.OverlayConfigApp._handle_active_widget_key(app, "space", event)

    assert handled is True
    assert exit_calls == ["exit"]

