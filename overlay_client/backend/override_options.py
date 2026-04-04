"""Backend-owned metadata for manual backend override choices."""

from __future__ import annotations

from typing import Any, Mapping

from .contracts import BackendInstance, BackendOverrideOption


_REGISTERED_OVERRIDE_OPTIONS: dict[str, BackendOverrideOption] = {
    BackendInstance.WINDOWS_DESKTOP.value: BackendOverrideOption(
        value=BackendInstance.WINDOWS_DESKTOP.value,
    ),
    BackendInstance.NATIVE_X11.value: BackendOverrideOption(
        value=BackendInstance.NATIVE_X11.value,
    ),
    BackendInstance.XWAYLAND_COMPAT.value: BackendOverrideOption(
        value=BackendInstance.XWAYLAND_COMPAT.value,
        restart_required=True,
    ),
    BackendInstance.KWIN_WAYLAND.value: BackendOverrideOption(
        value=BackendInstance.KWIN_WAYLAND.value,
    ),
    BackendInstance.GNOME_SHELL_WAYLAND.value: BackendOverrideOption(
        value=BackendInstance.GNOME_SHELL_WAYLAND.value,
    ),
    BackendInstance.SWAY_WAYFIRE_WLROOTS.value: BackendOverrideOption(
        value=BackendInstance.SWAY_WAYFIRE_WLROOTS.value,
    ),
    BackendInstance.HYPRLAND.value: BackendOverrideOption(
        value=BackendInstance.HYPRLAND.value,
    ),
    BackendInstance.COSMIC.value: BackendOverrideOption(
        value=BackendInstance.COSMIC.value,
    ),
    BackendInstance.GAMESCOPE.value: BackendOverrideOption(
        value=BackendInstance.GAMESCOPE.value,
    ),
    BackendInstance.WAYLAND_LAYER_SHELL_GENERIC.value: BackendOverrideOption(
        value=BackendInstance.WAYLAND_LAYER_SHELL_GENERIC.value,
    ),
}


def backend_override_option(value: Any) -> BackendOverrideOption | None:
    """Return the backend-owned metadata for an override token, if any."""

    token = _normalise_override_token(value)
    if not token:
        return None
    option = _REGISTERED_OVERRIDE_OPTIONS.get(token)
    if option is not None:
        return option
    return BackendOverrideOption(value=token)


def backend_override_requires_restart(previous: Any, current: Any) -> bool:
    """Return whether switching between two override values requires restart."""

    previous_option = backend_override_option(previous)
    current_option = backend_override_option(current)
    previous_value = previous_option.value if previous_option is not None else ""
    current_value = current_option.value if current_option is not None else ""
    return previous_value != current_value and any(
        option is not None and option.restart_required
        for option in (previous_option, current_option)
    )


def backend_override_options_for_status(
    status: Mapping[str, Any],
    *,
    current_value: str = "",
) -> tuple[BackendOverrideOption, ...]:
    """Return the backend-owned override options appropriate for a status payload."""

    probe = status.get("probe") if isinstance(status, Mapping) else None
    selected_backend = status.get("selected_backend") if isinstance(status, Mapping) else None
    options: list[BackendOverrideOption] = []
    seen: set[str] = set()

    def _add(token: Any) -> None:
        option = backend_override_option(token)
        if option is None or option.value in seen:
            return
        seen.add(option.value)
        options.append(option)

    if isinstance(selected_backend, Mapping):
        _add(selected_backend.get("instance"))
    if isinstance(probe, Mapping):
        operating_system = str(probe.get("operating_system") or "")
        session_type = str(probe.get("session_type") or "")
        compositor = str(probe.get("compositor") or "").lower()
        if operating_system == "windows":
            _add(BackendInstance.WINDOWS_DESKTOP.value)
        elif operating_system == "linux":
            if session_type == "x11":
                _add(BackendInstance.NATIVE_X11.value)
            elif session_type == "wayland":
                _add(BackendInstance.XWAYLAND_COMPAT.value)
                if compositor == "kwin":
                    _add(BackendInstance.KWIN_WAYLAND.value)
                elif compositor == "gnome-shell":
                    _add(BackendInstance.GNOME_SHELL_WAYLAND.value)
                elif compositor == "hyprland":
                    _add(BackendInstance.HYPRLAND.value)
                elif compositor in {"sway", "wayfire", "wlroots"}:
                    _add(BackendInstance.SWAY_WAYFIRE_WLROOTS.value)
                elif compositor == "cosmic":
                    _add(BackendInstance.COSMIC.value)
                elif compositor == "gamescope":
                    _add(BackendInstance.GAMESCOPE.value)
                else:
                    _add(BackendInstance.WAYLAND_LAYER_SHELL_GENERIC.value)
    _add(current_value)
    return tuple(options)


def _normalise_override_token(value: Any) -> str:
    try:
        token = str(value or "").strip().lower()
    except Exception:
        return ""
    if token == "auto":
        return ""
    return token
