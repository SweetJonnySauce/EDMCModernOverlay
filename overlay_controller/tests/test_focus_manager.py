from __future__ import annotations

import types


def test_focus_manager_registers_widget_bindings():
    import overlay_controller.overlay_controller as oc
    from overlay_controller.widgets.absolute import AbsoluteXYWidget
    from overlay_controller.widgets.background import BackgroundWidget
    from overlay_controller.widgets.group_controls import GroupControlsWidget

    class DummyBindingManager:
        def __init__(self) -> None:
            self.actions = {}

        def register_action(self, name, func, widgets=None):
            self.actions[name] = {"func": func, "widgets": widgets or []}

    class DummyAbsolute(AbsoluteXYWidget):  # type: ignore[misc]
        def __init__(self) -> None:
            self._targets = [object(), object()]

        def get_binding_targets(self):
            return self._targets

        def focus_next_field(self):
            return "next"

        def focus_previous_field(self):
            return "prev"

    class DummyBackground(BackgroundWidget):  # type: ignore[misc]
        def __init__(self) -> None:
            self._targets = [object(), object()]

        def get_binding_targets(self):
            return self._targets

        def focus_next_field(self):
            return "next-bg"

        def focus_previous_field(self):
            return "prev-bg"

    class DummyGroupControls(GroupControlsWidget):  # type: ignore[misc]
        def __init__(self) -> None:
            self._targets = [object(), object()]

        def get_binding_targets(self):
            return self._targets

        def focus_next_field(self):
            return "next-controls"

        def focus_previous_field(self):
            return "prev-controls"

    app = types.SimpleNamespace(
        absolute_widget=DummyAbsolute(),
        background_widget=DummyBackground(),
        group_controls_widget=DummyGroupControls(),
    )
    bindings = DummyBindingManager()
    fm = oc.FocusManager(app, bindings)

    fm.register_widget_bindings()

    assert "absolute_focus_next" in bindings.actions
    assert bindings.actions["absolute_focus_next"]["widgets"] == app.absolute_widget.get_binding_targets()
    assert bindings.actions["absolute_focus_prev"]["func"]() == "prev"
    assert "background_focus_next" in bindings.actions
    assert bindings.actions["background_focus_next"]["widgets"] == app.background_widget.get_binding_targets()
    assert bindings.actions["background_focus_prev"]["func"]() == "prev-bg"
    assert "group_controls_focus_next" in bindings.actions
    assert (
        bindings.actions["group_controls_focus_next"]["widgets"]
        == app.group_controls_widget.get_binding_targets()
    )
    assert bindings.actions["group_controls_focus_prev"]["func"]() == "prev-controls"
