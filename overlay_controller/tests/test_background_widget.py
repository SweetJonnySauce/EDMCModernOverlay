import types

import pytest


@pytest.fixture()
def background_widget():
    try:
        import tkinter as tk
    except Exception as exc:  # pragma: no cover - environment guard
        pytest.skip(f"tkinter unavailable: {exc}")
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - headless guard
        pytest.skip(f"Tk root unavailable: {exc}")
    root.withdraw()

    from overlay_controller.widgets.background import BackgroundWidget

    widget = BackgroundWidget(root)
    widget.pack()
    root.update_idletasks()
    yield widget
    try:
        root.destroy()
    except Exception:
        pass


def test_background_widget_left_right_respects_entry_cursor(background_widget):
    import tkinter as tk

    entry = background_widget._entry
    entry.delete(0, tk.END)
    entry.insert(0, "abcd")
    try:
        entry.selection_clear()
    except Exception:
        pass
    entry.icursor(2)
    background_widget._set_active_field("color")

    event = types.SimpleNamespace(widget=entry)
    result = background_widget.handle_key("Right", event)
    assert background_widget._active_field == "color"
    assert result is False

    entry.icursor(tk.END)
    try:
        entry.selection_clear()
    except Exception:
        pass
    result = background_widget.handle_key("Right", event)
    assert background_widget._active_field == "pick"
    assert result is True


def test_background_widget_left_right_respects_spin_cursor(background_widget):
    import tkinter as tk

    spin = background_widget._spin
    spin.delete(0, tk.END)
    spin.insert(0, "12")
    try:
        spin.selection_clear()
    except Exception:
        pass
    spin.icursor(1)
    background_widget._set_active_field("border")

    event = types.SimpleNamespace(widget=spin)
    result = background_widget.handle_key("Left", event)
    assert background_widget._active_field == "border"
    assert result is False

    spin.icursor(0)
    try:
        spin.selection_clear()
    except Exception:
        pass
    result = background_widget.handle_key("Left", event)
    assert background_widget._active_field == "border_pick"
    assert result is True


def test_background_widget_picker_applies_alpha(background_widget, monkeypatch):
    import overlay_controller.widgets.background as background

    widget = background_widget
    widget._set_opacity_percent(25)
    widget._color_var.set("#11223344")
    captured = {}

    def fake_askcolor(color=None, **_kwargs):
        captured["color"] = color
        return ((170, 187, 204), "#aabbcc")

    monkeypatch.setattr(background.colorchooser, "askcolor", fake_askcolor)

    widget._open_color_picker("color")

    assert captured["color"] == "#223344"
    assert widget._color_var.get() == "#40AABBCC"


def test_background_widget_picker_cancel_keeps_value(background_widget, monkeypatch):
    import overlay_controller.widgets.background as background

    widget = background_widget
    widget._color_var.set("#ABCDEF88")

    def fake_askcolor(*_args, **_kwargs):
        return (None, None)

    monkeypatch.setattr(background.colorchooser, "askcolor", fake_askcolor)

    widget._open_color_picker("color")

    assert widget._color_var.get() == "#ABCDEF88"


def test_background_widget_manual_background_alpha_updates_slider(background_widget):
    widget = background_widget
    widget._color_var.set("#80112233")
    widget._border_color_var.set("")

    widget._emit_change()

    assert widget._opacity_var.get() == 50
    assert widget._opacity_label_var.get() == "50%"


def test_background_widget_slider_commit_updates_valid_field_when_sibling_invalid(background_widget):
    widget = background_widget
    captured: list[tuple[object, object, object]] = []
    widget.set_change_callback(lambda c, bc, bw: captured.append((c, bc, bw)))

    widget.set_values("#FF010203", "#FF112233", 2)
    widget._color_var.set("invalid_color")
    widget._entry.configure(background="#ffdddd")
    widget._set_opacity_percent(50, mark_pending=True)
    widget._commit_opacity_changes()

    assert widget._color_var.get() == "invalid_color"
    assert widget._entry.cget("background") == "#ffdddd"
    assert widget._border_color_var.get() == "#80112233"
    assert captured[-1] == ("#FF010203", "#80112233", 2)


def test_background_widget_slider_exit_mode_keeps_focus_and_restores_horizontal_navigation(background_widget):
    widget = background_widget
    widget._focus_field("opacity", slider_adjust_mode=True)
    widget._set_opacity_percent(60)

    assert widget.handle_key("Left") is True
    assert widget._opacity_var.get() == 59
    assert widget._active_field == "opacity"
    assert widget._opacity_adjust_mode is True

    assert widget.handle_key("space") is True
    assert widget._active_field == "opacity"
    assert widget._opacity_adjust_mode is False

    assert widget.handle_key("Left") is True
    assert widget._active_field == "border"


def test_background_widget_binding_targets_exclude_opacity_slider(background_widget):
    targets = background_widget.get_binding_targets()
    assert background_widget._opacity_scale not in targets


def test_background_widget_entries_do_not_bind_space_to_exit(background_widget):
    color_space_binding = background_widget._entry.bind("<space>")
    border_space_binding = background_widget._border_entry.bind("<space>")
    assert color_space_binding in ("", None)
    assert border_space_binding in ("", None)


def test_background_widget_accepts_space_separated_named_color(background_widget):
    widget = background_widget
    token = widget._normalise_color_text("light green")
    assert token == "light green"


def test_background_widget_slider_commit_preserves_border_when_alpha_differs(background_widget):
    widget = background_widget
    captured: list[tuple[object, object, object]] = []
    widget.set_change_callback(lambda c, bc, bw: captured.append((c, bc, bw)))
    widget.set_values("#FF010203", "#80112233", 2)

    widget._set_opacity_percent(50, mark_pending=True)
    widget._commit_opacity_changes()

    assert widget._color_var.get() == "#80010203"
    assert widget._border_color_var.get() == "#80112233"
    assert captured[-1] == ("#80010203", "#80112233", 2)


def test_background_widget_slider_commit_updates_border_when_alpha_matches(background_widget):
    widget = background_widget
    captured: list[tuple[object, object, object]] = []
    widget.set_change_callback(lambda c, bc, bw: captured.append((c, bc, bw)))
    widget.set_values("#FF010203", "#FF112233", 2)

    widget._set_opacity_percent(50, mark_pending=True)
    widget._commit_opacity_changes()

    assert widget._color_var.get() == "#80010203"
    assert widget._border_color_var.get() == "#80112233"
    assert captured[-1] == ("#80010203", "#80112233", 2)


def test_background_widget_named_border_color_is_canonicalized_to_argb(background_widget):
    widget = background_widget
    widget.set_values("#80010203", "light green", 2)
    rgb = widget._resolve_named_color_rgb("light green")
    assert rgb is not None
    red, green, blue = rgb
    expected = f"#FF{red:02X}{green:02X}{blue:02X}"

    widget._emit_change()

    assert widget._border_color_var.get() == expected


def test_background_widget_traps_tab_navigation_on_all_controls(background_widget):
    widgets = (
        background_widget._entry,
        background_widget._picker_btn,
        background_widget._border_entry,
        background_widget._border_picker_btn,
        background_widget._spin,
        background_widget._opacity_scale,
    )
    for widget in widgets:
        assert widget.bind("<Tab>") not in ("", None)
        assert widget.bind("<Shift-Tab>") not in ("", None)
        assert widget.bind("<ISO_Left_Tab>") not in ("", None)
