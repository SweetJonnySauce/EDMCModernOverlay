"""Platform context helpers for the overlay client."""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import replace
from typing import TYPE_CHECKING, Any, Callable, Mapping, Optional

from overlay_client.backend import (
    BackendInstance,
    BackendSelectionStatus,
    BackendSelector,
    GNOME_SHELL_HELPER_DBUS_HEALTH_METHOD,
    GNOME_SHELL_HELPER_DBUS_INTERFACE,
    GNOME_SHELL_HELPER_DBUS_OBJECT_PATH,
    GNOME_SHELL_HELPER_DBUS_SERVICE,
    HelperCapabilityState,
    HelperDbusProbeError,
    HelperDbusServiceMissing,
    HelperHealthState,
    HelperHealthStatus,
    HelperKind,
    ProbeInputs,
    ProbeSource,
    SessionType,
    collect_platform_probe,
    probe_gnome_shell_helper_health,
)
from overlay_client.platform_integration import PlatformContext  # type: ignore

if TYPE_CHECKING:
    from overlay_client.client_config import InitialClientSettings  # type: ignore


def _initial_platform_context(initial: "InitialClientSettings") -> PlatformContext:
    session = os.environ.get("EDMC_OVERLAY_SESSION_TYPE") or os.environ.get("XDG_SESSION_TYPE") or ""
    compositor = os.environ.get("EDMC_OVERLAY_COMPOSITOR") or ""
    flatpak_flag = os.environ.get("EDMC_OVERLAY_IS_FLATPAK") == "1"
    flatpak_app = os.environ.get("EDMC_OVERLAY_FLATPAK_ID") or ""
    return PlatformContext(
        session_type=session,
        compositor=compositor,
        manual_backend_override=str(getattr(initial, "manual_backend_override", "") or "").strip().lower(),
        flatpak=flatpak_flag,
        flatpak_app=flatpak_app,
    )


def _client_backend_status(
    context: PlatformContext,
    *,
    source: ProbeSource,
    qt_platform_name: str,
    env: Optional[Mapping[str, str]] = None,
    sys_platform_name: Optional[str] = None,
    fetch_gnome_helper_health: Callable[[], object] | None = None,
) -> BackendSelectionStatus:
    """Build the client-authoritative backend selection status from runtime evidence first."""

    env_map = dict(os.environ if env is None else env)
    flatpak_flag = bool(context.flatpak or env_map.get("EDMC_OVERLAY_IS_FLATPAK") == "1")
    flatpak_app = str(env_map.get("EDMC_OVERLAY_FLATPAK_ID") or context.flatpak_app or "").strip()
    runtime_probe = collect_platform_probe(
        ProbeInputs(
            source=source,
            sys_platform=sys_platform_name or sys.platform,
            qt_platform_name=qt_platform_name,
            session_type="",
            compositor="",
            is_flatpak=flatpak_flag,
            flatpak_app_id=flatpak_app,
            env=env_map,
        )
    )
    session_hint = context.session_type if runtime_probe.session_type is SessionType.UNKNOWN else runtime_probe.session_type.value
    compositor_hint = context.compositor or runtime_probe.compositor
    if runtime_probe.compositor:
        compositor_hint = runtime_probe.compositor
    helper_health = _probe_gnome_helper_health_for_context(
        env_map=env_map,
        session_type=session_hint,
        compositor=compositor_hint,
        fetch_gnome_helper_health=fetch_gnome_helper_health,
    )
    available_helpers = (
        frozenset({HelperKind.GNOME_SHELL_EXTENSION})
        if helper_health is not None and helper_health.healthy
        else frozenset()
    )
    probe = collect_platform_probe(
        ProbeInputs(
            source=source,
            sys_platform=sys_platform_name or sys.platform,
            qt_platform_name=qt_platform_name,
            session_type=session_hint,
            compositor=compositor_hint,
            is_flatpak=flatpak_flag,
            flatpak_app_id=flatpak_app,
            available_helpers=available_helpers,
            env=env_map,
        )
    )
    status = BackendSelector(
        shadow_mode=False,
        stable_notes=("client_selector_result",),
    ).select(probe, manual_override=context.manual_backend_override)
    return _status_with_gnome_helper_health(status, helper_health)


def _probe_gnome_helper_health_for_context(
    *,
    env_map: Mapping[str, str],
    session_type: str,
    compositor: str,
    fetch_gnome_helper_health: Callable[[], object] | None,
) -> HelperHealthStatus | None:
    """Return GNOME helper health only for GNOME Wayland runtime contexts."""

    if str(session_type or "").strip().lower() != "wayland":
        return None
    if str(compositor or "").strip().lower() != "gnome-shell":
        return None
    fetcher = fetch_gnome_helper_health
    if fetcher is None:
        if not _session_bus_available(env_map):
            return None
        def fetch_gdbus_health() -> object:
            return _fetch_gnome_helper_health_via_gdbus(env_map)

        fetcher = fetch_gdbus_health
    return probe_gnome_shell_helper_health(fetcher)


def _fetch_gnome_helper_health_via_gdbus(env_map: Mapping[str, str] | None = None) -> object:
    """Fetch helper health through the local user session bus using gdbus."""

    child_env = os.environ.copy()
    if env_map is not None:
        runtime_dir = str(env_map.get("XDG_RUNTIME_DIR") or "").strip()
        bus_address = str(env_map.get("DBUS_SESSION_BUS_ADDRESS") or "").strip()
        if runtime_dir:
            child_env["XDG_RUNTIME_DIR"] = runtime_dir
        if bus_address:
            child_env["DBUS_SESSION_BUS_ADDRESS"] = bus_address
        elif runtime_dir:
            child_env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={runtime_dir}/bus"
    command = [
        "gdbus",
        "call",
        "--session",
        "--dest",
        GNOME_SHELL_HELPER_DBUS_SERVICE,
        "--object-path",
        GNOME_SHELL_HELPER_DBUS_OBJECT_PATH,
        "--method",
        f"{GNOME_SHELL_HELPER_DBUS_INTERFACE}.{GNOME_SHELL_HELPER_DBUS_HEALTH_METHOD}",
    ]
    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=1.5,
            env=child_env,
        )
    except FileNotFoundError as exc:
        raise HelperDbusProbeError("gdbus command not found") from exc
    except subprocess.TimeoutExpired as exc:
        raise HelperDbusProbeError("gdbus health call timed out") from exc
    output = (result.stdout or "").strip()
    diagnostic = "\n".join(part for part in (output, (result.stderr or "").strip()) if part)
    if result.returncode != 0:
        if "ServiceUnknown" in diagnostic or "NameHasNoOwner" in diagnostic:
            raise HelperDbusServiceMissing(diagnostic or "helper DBus service is not owned")
        raise HelperDbusProbeError(diagnostic or f"gdbus exited with status {result.returncode}")
    if not output:
        raise HelperDbusProbeError("gdbus health call returned no payload")
    return output


def _session_bus_available(env_map: Mapping[str, str]) -> bool:
    if str(env_map.get("DBUS_SESSION_BUS_ADDRESS") or "").strip():
        return True
    runtime_dir = str(env_map.get("XDG_RUNTIME_DIR") or "").strip()
    return bool(runtime_dir and os.path.exists(os.path.join(runtime_dir, "bus")))


def _status_with_gnome_helper_health(
    status: BackendSelectionStatus,
    helper_health: HelperHealthStatus | None,
) -> BackendSelectionStatus:
    if helper_health is None or status.selected_backend.instance is not BackendInstance.GNOME_SHELL_WAYLAND:
        return status
    helper_state = HelperCapabilityState(
        helper=HelperKind.GNOME_SHELL_EXTENSION,
        required=True,
        installed=helper_health.state is not HelperHealthState.MISSING_SERVICE,
        enabled=helper_health.healthy,
        approved=helper_health.healthy,
        version=helper_health.helper_version,
        detail=f"health_state={helper_health.state.value}",
    )
    notes = tuple(status.notes) + (f"helper_health:{helper_health.state.value}",)
    return replace(status, helper_states=(helper_state,), notes=notes)

def _backend_status_signature(
    status: BackendSelectionStatus | Mapping[str, Any] | None,
) -> Optional[tuple[str, str, str, str, bool, str, str]]:
    """Return a compact comparable signature for status objects or payload dicts."""

    if status is None:
        return None
    if isinstance(status, BackendSelectionStatus):
        fallback_reason = status.fallback_reason.value if status.fallback_reason is not None else ""
        return (
            status.selected_backend.family.value,
            status.selected_backend.instance.value,
            status.classification.value,
            fallback_reason,
            bool(status.shadow_mode),
            status.manual_override.value if status.manual_override is not None else "",
            str(status.override_error or ""),
        )
    selected_backend = status.get("selected_backend") if isinstance(status, Mapping) else None
    if not isinstance(selected_backend, Mapping):
        selected_backend = {}
    return (
        str(selected_backend.get("family") or ""),
        str(selected_backend.get("instance") or ""),
        str(status.get("classification") or ""),
        str(status.get("fallback_reason") or ""),
        bool(status.get("shadow_mode")),
        str(status.get("manual_override") or ""),
        str(status.get("override_error") or ""),
    )
