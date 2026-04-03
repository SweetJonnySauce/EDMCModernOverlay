"""Pure contract types for backend selection and backend bundle composition."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable


class OperatingSystem(str, Enum):
    """OS families that influence backend selection."""

    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


class SessionType(str, Enum):
    """Display/session families relevant to backend selection."""

    WINDOWS = "windows"
    X11 = "x11"
    WAYLAND = "wayland"
    UNKNOWN = "unknown"


class BackendFamily(str, Enum):
    """Stable support-family labels used in diagnostics and support output."""

    NATIVE_WINDOWS = "native_windows"
    NATIVE_X11 = "native_x11"
    XWAYLAND_COMPAT = "xwayland_compat"
    NATIVE_WAYLAND = "native_wayland"
    COMPOSITOR_HELPER = "compositor_helper"
    PORTAL_FALLBACK = "portal_fallback"


class BackendInstance(str, Enum):
    """Specific backend instances used for precise diagnostics."""

    WINDOWS_DESKTOP = "windows_desktop"
    NATIVE_X11 = "native_x11"
    XWAYLAND_COMPAT = "xwayland_compat"
    WAYLAND_LAYER_SHELL_GENERIC = "wayland_layer_shell_generic"
    KWIN_WAYLAND = "kwin_wayland"
    GNOME_SHELL_WAYLAND = "gnome_shell_wayland"
    SWAY_WAYFIRE_WLROOTS = "sway_wayfire_wlroots"
    HYPRLAND = "hyprland"
    COSMIC = "cosmic"
    GAMESCOPE = "gamescope"
    PORTAL_FALLBACK = "portal_fallback"
    UNKNOWN = "unknown"


class CapabilityClassification(str, Enum):
    """Truthful support classifications exposed to users and diagnostics."""

    TRUE_OVERLAY = "true_overlay"
    DEGRADED_OVERLAY = "degraded_overlay"
    UNSUPPORTED = "unsupported"


class FallbackReason(str, Enum):
    """Concrete reasons for degraded or fallback backend selection."""

    MANUAL_OVERRIDE = "manual_override"
    MISSING_PROTOCOL = "missing_protocol"
    MISSING_HELPER = "missing_helper"
    COMPOSITOR_RESTRICTION = "compositor_restriction"
    XWAYLAND_COMPAT_ONLY = "xwayland_compat_only"
    TRACKING_UNAVAILABLE = "tracking_unavailable"
    CLICK_THROUGH_UNAVAILABLE = "click_through_unavailable"
    STACKING_NOT_GUARANTEED = "stacking_not_guaranteed"
    SANDBOX_RESTRICTION = "sandbox_restriction"
    NOT_IMPLEMENTED = "not_implemented"
    INVALID_OVERRIDE = "invalid_override"


class HelperKind(str, Enum):
    """Helper-backed integrations that may participate in a backend bundle."""

    GNOME_SHELL_EXTENSION = "gnome_shell_extension"
    KWIN_SCRIPT = "kwin_script"
    KWIN_EFFECT = "kwin_effect"
    EXTERNAL_HELPER = "external_helper"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class BackendDescriptor:
    """Stable backend identity for support output and selection results."""

    family: BackendFamily
    instance: BackendInstance

    @property
    def support_label(self) -> str:
        return f"{self.family.value} / {self.instance.value}"

    def to_payload(self) -> dict[str, str]:
        return {"family": self.family.value, "instance": self.instance.value}


@dataclass(frozen=True, slots=True)
class PlatformProbeResult:
    """Pure snapshot of the local platform and capability environment."""

    operating_system: OperatingSystem = OperatingSystem.UNKNOWN
    session_type: SessionType = SessionType.UNKNOWN
    qt_platform_name: str = ""
    compositor: str = ""
    force_xwayland: bool = False
    is_flatpak: bool = False
    flatpak_app_id: str = ""
    available_protocols: frozenset[str] = field(default_factory=frozenset)
    available_helpers: frozenset[HelperKind] = field(default_factory=frozenset)

    def has_protocol(self, protocol_name: str) -> bool:
        return protocol_name in self.available_protocols

    def has_helper(self, helper: HelperKind) -> bool:
        return helper in self.available_helpers

    def to_payload(self) -> dict[str, object]:
        return {
            "operating_system": self.operating_system.value,
            "session_type": self.session_type.value,
            "qt_platform_name": self.qt_platform_name,
            "compositor": self.compositor,
            "force_xwayland": self.force_xwayland,
            "is_flatpak": self.is_flatpak,
            "flatpak_app_id": self.flatpak_app_id,
            "available_protocols": sorted(self.available_protocols),
            "available_helpers": sorted(helper.value for helper in self.available_helpers),
        }


@runtime_checkable
class PlatformProbe(Protocol):
    """Collects a platform snapshot in the client runtime environment."""

    def collect(self) -> PlatformProbeResult:
        """Return the current platform and capability snapshot."""


@runtime_checkable
class TargetDiscoveryBackend(Protocol):
    """Contract for target discovery/follow components."""

    @property
    def backend_instance(self) -> BackendInstance:
        """Return the backend instance identifier for this component."""


@runtime_checkable
class PresentationBackend(Protocol):
    """Contract for presentation/window-management components."""

    @property
    def backend_instance(self) -> BackendInstance:
        """Return the backend instance identifier for this component."""


@runtime_checkable
class InputPolicyBackend(Protocol):
    """Contract for click-through/focus/input-policy components."""

    @property
    def backend_instance(self) -> BackendInstance:
        """Return the backend instance identifier for this component."""


@runtime_checkable
class HelperIpcBackend(Protocol):
    """Contract for compositor-native helper communication components."""

    @property
    def backend_instance(self) -> BackendInstance:
        """Return the backend instance identifier for this component."""

    @property
    def helper_kind(self) -> HelperKind:
        """Return the helper identity this component communicates with."""


@dataclass(frozen=True, slots=True)
class BackendBundle:
    """Concrete bundle of backend components selected for a runtime environment."""

    descriptor: BackendDescriptor
    discovery: TargetDiscoveryBackend
    presentation: PresentationBackend
    input_policy: InputPolicyBackend
    helper_ipc: HelperIpcBackend | None = None

    @property
    def uses_helper(self) -> bool:
        return self.helper_ipc is not None
