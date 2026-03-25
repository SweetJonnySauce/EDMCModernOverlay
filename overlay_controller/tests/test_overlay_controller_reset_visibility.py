from __future__ import annotations

from types import SimpleNamespace

import overlay_controller.overlay_controller as oc


def test_reset_clicked_on_custom_profile_resets_group_visibility_to_default() -> None:
    reset_calls: list[tuple[str, str, str]] = []
    bridge_calls: list[tuple[str, object]] = []

    class _Bridge:
        def reset_plugin_group_to_default(self, *, group_name=None):
            bridge_calls.append(("reset_plugin_group_to_default", group_name))
            return {"status": "ok", "plugin_group_states": {"Group1": False}}

        def reset_active_group_cache(self):
            bridge_calls.append(("reset_active_group_cache", None))

    controller = SimpleNamespace(
        _get_current_group_selection=lambda: ("PluginA", "Group1"),
        _group_state=SimpleNamespace(
            reset_group_overrides=lambda plugin, label, edit_nonce="": reset_calls.append((plugin, label, edit_nonce)),
            _groupings_data={},
        ),
        _groupings_data={},
        _group_snapshots={("PluginA", "Group1"): object()},
        _last_preview_signature="sig",
        _offset_live_edit_until=1.0,
        _last_edit_ts=0.0,
        _mode_timers=None,
        _plugin_bridge=_Bridge(),
        _last_active_group_sent=("PluginA", "Group1"),
        _handle_idprefix_selected=lambda: bridge_calls.append(("handle_idprefix_selected", None)),
        _edit_controller=SimpleNamespace(
            _emit_override_reload_signal=lambda: bridge_calls.append(("emit_override_reload_signal", None))
        ),
        _plugin_group_enabled_states={},
        _current_profile_name="PvE",
        _user_overrides_nonce="",
    )

    oc.OverlayConfigApp._handle_reset_clicked(controller)

    assert reset_calls and reset_calls[0][0:2] == ("PluginA", "Group1")
    assert ("reset_plugin_group_to_default", "Group1") in bridge_calls
    assert controller._plugin_group_enabled_states["Group1"] is False
    assert ("reset_active_group_cache", None) in bridge_calls
