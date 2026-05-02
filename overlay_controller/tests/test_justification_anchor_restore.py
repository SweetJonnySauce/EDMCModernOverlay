from __future__ import annotations

from types import SimpleNamespace

import overlay_controller.overlay_controller as oc


def test_handle_justification_changed_captures_and_restores_anchor_position() -> None:
    capture_calls: list[tuple[str, str]] = []
    restore_calls: list[tuple[str, str]] = []
    refresh_calls: list[bool] = []
    write_calls: list[str] = []
    invalidate_calls: list[tuple[str, str]] = []

    selection = ("PluginA", "Group1")
    controller = SimpleNamespace(
        _get_current_group_selection=lambda: selection,
        _capture_anchor_restore_state=lambda selected: capture_calls.append(selected) or True,
        _schedule_anchor_restore=lambda selected: restore_calls.append(selected),
        _refresh_current_group_snapshot=lambda force_ui=True: refresh_calls.append(bool(force_ui)),
        _groupings_data={"PluginA": {"idPrefixGroups": {"Group1": {}}}},
        _groupings_cache={},
        _group_state=None,
        _edit_controller=SimpleNamespace(
            schedule_groupings_config_write=lambda: write_calls.append("scheduled"),
        ),
        _invalidate_group_cache_entry=lambda plugin, label: invalidate_calls.append((plugin, label)),
        _last_edit_ts=0.0,
        _offset_live_edit_until=0.0,
        _mode_timers=None,
        _edit_nonce="seed",
    )

    oc.OverlayConfigApp._handle_justification_changed(controller, "left")

    group = controller._groupings_data["PluginA"]["idPrefixGroups"]["Group1"]
    assert group["payloadJustification"] == "left"
    assert capture_calls == [selection]
    assert refresh_calls == [True]
    assert restore_calls == [selection]
    assert write_calls == ["scheduled"]
    assert invalidate_calls == [selection]
    assert isinstance(controller._edit_nonce, str) and controller._edit_nonce


def test_restore_anchor_offsets_uses_absolute_change_handler_when_available() -> None:
    selection = ("PluginA", "Group1")
    absolute_calls: list[tuple[float | None, float | None]] = []
    axis_calls: list[str] = []
    sync_calls: list[bool] = []
    draw_calls: list[str] = []

    controller = SimpleNamespace(
        _anchor_restore_handles={},
        _anchor_restore_state={selection: {"x": 333.0, "y": 222.0, "x_ts": 1.0, "y_ts": 1.0}},
        _get_current_group_selection=lambda: selection,
        _absolute_user_state={},
        absolute_widget=SimpleNamespace(set_px_values=lambda x, y: absolute_calls.append((x, y))),
        _handle_absolute_changed=lambda axis: axis_calls.append(str(axis)),
        _sync_absolute_for_current_group=lambda **kwargs: sync_calls.append(True),
        _draw_preview=lambda: draw_calls.append("draw"),
        _offset_write_debounce_ms=25,
        after_cancel=lambda _handle: None,
    )

    oc.OverlayConfigApp._restore_anchor_offsets(controller, selection)

    assert absolute_calls == [(333.0, 222.0)]
    assert axis_calls == [""]
    assert not sync_calls
    assert not draw_calls
    saved = controller._absolute_user_state[selection]
    assert saved["x"] == 333.0
    assert saved["y"] == 222.0
