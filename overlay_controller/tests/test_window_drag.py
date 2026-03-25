from __future__ import annotations

from types import SimpleNamespace

from overlay_controller import overlay_controller as oc


class _DummyWidget:
    def __init__(self, widget_class: str, toplevel: object) -> None:
        self._widget_class = widget_class
        self._toplevel = toplevel

    def winfo_class(self) -> str:
        return self._widget_class

    def winfo_toplevel(self) -> object:
        return self._toplevel


def test_window_drag_blocked_widget_classes_include_scale_and_entry() -> None:
    assert oc.OverlayConfigApp._is_window_drag_blocked_widget(_DummyWidget("Scale", object())) is True
    assert oc.OverlayConfigApp._is_window_drag_blocked_widget(_DummyWidget("Entry", object())) is True
    assert oc.OverlayConfigApp._is_window_drag_blocked_widget(_DummyWidget("Frame", object())) is False


def test_start_window_drag_ignores_scale_widget() -> None:
    app = SimpleNamespace(
        _drag_offset=(99, 99),
        winfo_rootx=lambda: 100,
        winfo_rooty=lambda: 200,
        _is_window_drag_blocked_widget=oc.OverlayConfigApp._is_window_drag_blocked_widget,
    )
    event = SimpleNamespace(
        widget=_DummyWidget("Scale", app),
        x_root=150,
        y_root=260,
    )

    oc.OverlayConfigApp._start_window_drag(app, event)

    assert app._drag_offset is None


def test_start_window_drag_sets_offset_for_frame_widget() -> None:
    app = SimpleNamespace(
        _drag_offset=None,
        winfo_rootx=lambda: 100,
        winfo_rooty=lambda: 200,
        _is_window_drag_blocked_widget=oc.OverlayConfigApp._is_window_drag_blocked_widget,
    )
    event = SimpleNamespace(
        widget=_DummyWidget("Frame", app),
        x_root=132,
        y_root=244,
    )

    oc.OverlayConfigApp._start_window_drag(app, event)

    assert app._drag_offset == (32, 44)

