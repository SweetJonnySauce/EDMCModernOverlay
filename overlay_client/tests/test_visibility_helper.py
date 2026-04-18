from __future__ import annotations

from overlay_client.visibility_helper import VisibilityHelper


def test_visibility_helper_calls_show_hooks_in_order() -> None:
    events: list[str] = []
    visible = False

    def is_visible() -> bool:
        return visible

    def show() -> None:
        nonlocal visible
        events.append("show")
        visible = True

    helper = VisibilityHelper(lambda *_args: None)
    helper.update_visibility(
        True,
        is_visible_fn=is_visible,
        show_fn=show,
        hide_fn=lambda: events.append("hide"),
        raise_fn=lambda: events.append("raise"),
        apply_drag_state_fn=lambda: events.append("drag"),
        format_scale_debug_fn=lambda: "debug",
        before_show_fn=lambda: events.append("before_show"),
        after_show_fn=lambda: events.append("after_show"),
    )

    assert events == ["before_show", "show", "after_show", "raise", "drag"]


def test_visibility_helper_calls_hide_hooks_in_order() -> None:
    events: list[str] = []
    visible = True

    def is_visible() -> bool:
        return visible

    def hide() -> None:
        nonlocal visible
        events.append("hide")
        visible = False

    helper = VisibilityHelper(lambda *_args: None)
    helper.update_visibility(
        False,
        is_visible_fn=is_visible,
        show_fn=lambda: events.append("show"),
        hide_fn=hide,
        raise_fn=lambda: events.append("raise"),
        apply_drag_state_fn=lambda: events.append("drag"),
        format_scale_debug_fn=lambda: "debug",
        before_hide_fn=lambda: events.append("before_hide"),
        after_hide_fn=lambda: events.append("after_hide"),
    )

    assert events == ["before_hide", "hide", "after_hide"]
