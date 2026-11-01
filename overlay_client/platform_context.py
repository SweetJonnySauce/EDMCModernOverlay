"""Platform context helpers for the overlay client."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from overlay_client.platform_integration import PlatformContext  # type: ignore

if TYPE_CHECKING:
    from overlay_client.client_config import InitialClientSettings  # type: ignore


def _initial_platform_context(initial: "InitialClientSettings") -> PlatformContext:
    force_env = os.environ.get("EDMC_OVERLAY_FORCE_XWAYLAND") == "1"
    session = os.environ.get("EDMC_OVERLAY_SESSION_TYPE") or os.environ.get("XDG_SESSION_TYPE") or ""
    compositor = os.environ.get("EDMC_OVERLAY_COMPOSITOR") or ""
    flatpak_flag = os.environ.get("EDMC_OVERLAY_IS_FLATPAK") == "1"
    flatpak_app = os.environ.get("EDMC_OVERLAY_FLATPAK_ID") or ""
    xwayland_env = os.environ.get("EDMC_OVERLAY_XWAYLAND_ON_WAYLAND")
    if xwayland_env is None:
        xwayland_enabled = bool(initial.xwayland_on_wayland)
    else:
        xwayland_enabled = xwayland_env == "1"
    xwayland_on_wayland = session.lower() == "wayland" and xwayland_enabled
    return PlatformContext(
        session_type=session,
        compositor=compositor,
        force_xwayland=bool(initial.force_xwayland or force_env),
        xwayland_on_wayland=xwayland_on_wayland,
        flatpak=flatpak_flag,
        flatpak_app=flatpak_app,
    )
