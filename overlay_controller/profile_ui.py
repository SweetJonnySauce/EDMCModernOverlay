from __future__ import annotations

import time
from typing import Any


def apply_profile_dropdown_selection(app: Any) -> None:
    widget = getattr(app, "profile_widget", None)
    if widget is None:
        return
    profiles = list(getattr(app, "_profile_names", [])) or ["Default"]
    selected_index = None
    current_cf = str(getattr(app, "_current_profile_name", "Default") or "Default").casefold()
    for idx, name in enumerate(profiles):
        if str(name).casefold() == current_cf:
            selected_index = idx
            break
    app._suppress_profile_selection_command = True
    try:
        widget.update_options(profiles, selected_index)
    except Exception:
        pass
    finally:
        app._suppress_profile_selection_command = False


def update_reset_button_label(app: Any) -> None:
    button = getattr(app, "reset_button", None)
    if button is None:
        return
    current = str(getattr(app, "_current_profile_name", "Default") or "Default").strip() or "Default"
    label = "Reset Overlay (All Profiles)" if current.casefold() == "default" else "Reset Profile to Default"
    try:
        button.configure(text=label)
    except Exception:
        pass


def refresh_profile_state_cache(app: Any, *, force: bool = False, min_interval_seconds: float = 1.0) -> None:
    now = time.time()
    if not force and now - float(getattr(app, "_last_profile_state_refresh_ts", 0.0) or 0.0) < min_interval_seconds:
        return
    bridge = getattr(app, "_plugin_bridge", None)
    if bridge is None:
        return
    try:
        response = bridge.profile_status()
    except Exception:
        return
    if not isinstance(response, dict):
        return
    if str(response.get("status") or "").strip().lower() != "ok":
        return

    raw_profiles = response.get("profiles")
    profiles: list[str] = []
    if isinstance(raw_profiles, list):
        for item in raw_profiles:
            token = str(item or "").strip()
            if token:
                profiles.append(token)
    if not profiles:
        profiles = ["Default"]
    current_profile = str(response.get("current_profile") or profiles[0]).strip() or profiles[0]
    old_current = str(getattr(app, "_current_profile_name", "Default") or "Default")
    app._profile_names = profiles
    app._current_profile_name = current_profile
    app._last_profile_state_refresh_ts = now
    app._apply_profile_dropdown_selection()
    app._update_reset_button_label()
    if old_current.casefold() != current_profile.casefold():
        app._refresh_idprefix_options()


def load_profile_options(app: Any) -> list[str]:
    refresh_profile_state_cache(app, force=True, min_interval_seconds=0.0)
    return list(getattr(app, "_profile_names", [])) or ["Default"]


def handle_profile_selected(app: Any, selected_profile: str | None) -> None:
    if getattr(app, "_suppress_profile_selection_command", False):
        return
    profile_name = str(selected_profile or "").strip()
    if not profile_name:
        return
    if profile_name.casefold() == str(getattr(app, "_current_profile_name", "Default")).casefold():
        return
    bridge = getattr(app, "_plugin_bridge", None)
    if bridge is None:
        app._apply_profile_dropdown_selection()
        return
    try:
        response = bridge.set_profile(profile_name)
    except Exception:
        app._apply_profile_dropdown_selection()
        return
    if not isinstance(response, dict) or str(response.get("status") or "").strip().lower() != "ok":
        app._apply_profile_dropdown_selection()
        return
    profiles_raw = response.get("profiles")
    profiles = [str(item).strip() for item in profiles_raw] if isinstance(profiles_raw, list) else []
    profiles = [item for item in profiles if item] or ["Default"]
    app._profile_names = profiles
    app._current_profile_name = str(response.get("current_profile") or profile_name).strip() or profile_name
    app._apply_profile_dropdown_selection()
    app._update_reset_button_label()
    app._refresh_idprefix_options()


def reset_group_visibility_for_custom_profile(app: Any, *, group_name: str) -> None:
    bridge = getattr(app, "_plugin_bridge", None)
    if bridge is None:
        return
    current_profile = str(getattr(app, "_current_profile_name", "Default") or "Default").strip() or "Default"
    if current_profile.casefold() != "default":
        response = bridge.reset_plugin_group_to_default(group_name=group_name)
        if isinstance(response, dict) and str(response.get("status") or "").strip().lower() == "ok":
            raw_states = response.get("plugin_group_states")
            if isinstance(raw_states, dict):
                for raw_name, raw_value in raw_states.items():
                    if isinstance(raw_name, str) and raw_name.strip():
                        app._plugin_group_enabled_states[raw_name.strip()] = bool(raw_value)
    bridge.reset_active_group_cache()
