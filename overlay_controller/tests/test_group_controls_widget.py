from __future__ import annotations

import pytest


@pytest.fixture()
def group_controls_widget():
    try:
        import tkinter as tk
    except Exception as exc:  # pragma: no cover - environment guard
        pytest.skip(f"tkinter unavailable: {exc}")
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - headless guard
        pytest.skip(f"Tk root unavailable: {exc}")
    root.withdraw()

    from overlay_controller.widgets.group_controls import GroupControlsWidget

    widget = GroupControlsWidget(root)
    widget.pack(fill="both", expand=True)
    root.update_idletasks()
    yield widget
    try:
        root.destroy()
    except Exception:
        pass


def test_group_controls_binding_targets(group_controls_widget):
    targets = group_controls_widget.get_binding_targets()
    assert targets == [group_controls_widget.enabled_checkbox, group_controls_widget.reset_button]


def test_group_controls_keyboard_navigation_and_activation(group_controls_widget):
    enabled_values: list[bool] = []
    reset_calls: list[str] = []
    group_controls_widget.set_enabled_change_callback(lambda value: enabled_values.append(value))
    group_controls_widget.set_reset_callback(lambda: reset_calls.append("reset"))

    assert group_controls_widget._active_field == "enabled"

    assert group_controls_widget.handle_key("Down") is True
    assert group_controls_widget._active_field == "reset"
    assert group_controls_widget.handle_key("space") is True
    assert reset_calls == ["reset"]

    assert group_controls_widget.handle_key("Up") is True
    assert group_controls_widget._active_field == "enabled"
    group_controls_widget.group_enabled_var.set(True)
    assert group_controls_widget.handle_key("space") is True
    assert enabled_values[-1] is False


def test_group_controls_requests_focus_on_click(group_controls_widget):
    requests: list[str] = []
    group_controls_widget.set_focus_request_callback(lambda: requests.append("focus"))

    group_controls_widget._handle_enabled_click()
    group_controls_widget._handle_reset_click()

    assert requests == ["focus", "focus"]
    assert group_controls_widget._active_field == "reset"


def test_group_controls_disabled_blocks_navigation(group_controls_widget):
    group_controls_widget.set_enabled(False)
    assert group_controls_widget.handle_key("Down") is False
