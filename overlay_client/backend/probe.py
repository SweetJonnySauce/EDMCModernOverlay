"""Pure platform probe helpers for the backend selector."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .contracts import HelperKind, OperatingSystem, PlatformProbeResult, SessionType


class ProbeSource(str, Enum):
    """Origin of the probe inputs for diagnostics and future wiring."""

    INITIAL_HINTS = "initial_hints"
    RUNTIME_UPDATE = "runtime_update"
    TEST = "test"


@dataclass(frozen=True, slots=True)
class ProbeInputs:
    """Normalized inputs used to build a pure platform probe snapshot."""

    source: ProbeSource = ProbeSource.TEST
    sys_platform: str = ""
    qt_platform_name: str = ""
    session_type: str = ""
    compositor: str = ""
    is_flatpak: bool = False
    flatpak_app_id: str = ""
    available_protocols: frozenset[str] = field(default_factory=frozenset)
    available_helpers: frozenset[HelperKind] = field(default_factory=frozenset)
    env: Mapping[str, str] = field(default_factory=dict)


def collect_platform_probe(inputs: ProbeInputs) -> PlatformProbeResult:
    """Build a normalized platform probe snapshot from pure inputs."""

    env = inputs.env
    operating_system = _normalize_operating_system(inputs.sys_platform)
    session_type = _normalize_session_type(inputs.session_type or env.get("XDG_SESSION_TYPE", ""))
    qt_platform_name = str(inputs.qt_platform_name or "").strip().lower()
    compositor = _normalize_compositor(inputs.compositor) or _infer_compositor_from_env(env)
    available_protocols = frozenset(str(name).strip().lower() for name in inputs.available_protocols if str(name).strip())
    available_helpers = frozenset(inputs.available_helpers)
    return PlatformProbeResult(
        operating_system=operating_system,
        session_type=session_type,
        qt_platform_name=qt_platform_name,
        compositor=compositor,
        is_flatpak=bool(inputs.is_flatpak),
        flatpak_app_id=str(inputs.flatpak_app_id or "").strip(),
        available_protocols=available_protocols,
        available_helpers=available_helpers,
    )


def _normalize_operating_system(sys_platform: str) -> OperatingSystem:
    token = str(sys_platform or "").strip().lower()
    if token.startswith("win"):
        return OperatingSystem.WINDOWS
    if token.startswith("linux"):
        return OperatingSystem.LINUX
    if token.startswith("darwin"):
        return OperatingSystem.MACOS
    return OperatingSystem.UNKNOWN


def _normalize_session_type(session_type: str) -> SessionType:
    token = str(session_type or "").strip().lower()
    if token == "windows":
        return SessionType.WINDOWS
    if token == "x11":
        return SessionType.X11
    if token == "wayland":
        return SessionType.WAYLAND
    return SessionType.UNKNOWN


def _normalize_compositor(compositor: str) -> str:
    token = str(compositor or "").strip().lower()
    if token in {"mutter"}:
        return "gnome-shell"
    return token


def _infer_compositor_from_env(env: Mapping[str, str]) -> str:
    if env.get("SWAYSOCK"):
        return "sway"
    if env.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "hyprland"
    desktop = str(env.get("XDG_CURRENT_DESKTOP") or "").upper()
    if "KDE" in desktop or env.get("KDE_FULL_SESSION"):
        return "kwin"
    if "GNOME" in desktop or env.get("GNOME_SHELL_SESSION_MODE"):
        return "gnome-shell"
    return ""
