"""Runtime GNOME helper probe helpers kept separate from the pure probe normalizer."""

from __future__ import annotations

from typing import Mapping

from .contracts import HelperKind, HelperProbeAvailability, HelperProbeState
from .helper_ipc import (
    GNOME_SHELL_HELPER_OBJECT_PATH,
    GNOME_SHELL_HELPER_SERVICE_NAME,
    HELPER_PROTOCOL_VERSION,
)


def probe_gnome_shell_helper(
    *,
    session_type: str = "",
    compositor: str = "",
    env: Mapping[str, str] | None = None,
) -> HelperProbeState | None:
    """Return GNOME helper runtime evidence when the current session is GNOME Wayland."""

    del env
    if str(session_type or "").strip().lower() != "wayland":
        return None
    if str(compositor or "").strip().lower() != "gnome-shell":
        return None

    try:
        from pydbus import SessionBus  # type: ignore
    except ModuleNotFoundError as exc:
        missing_name = str(getattr(exc, "name", "") or "").strip().lower()
        if missing_name == "gi":
            return HelperProbeState(
                helper=HelperKind.GNOME_SHELL_EXTENSION,
                availability=HelperProbeAvailability.MISSING,
                detail="host_prerequisite_missing:python3-gi",
            )
        if missing_name == "pydbus":
            return HelperProbeState(
                helper=HelperKind.GNOME_SHELL_EXTENSION,
                availability=HelperProbeAvailability.MISSING,
                detail="python_dependency_missing:pydbus",
            )
        return HelperProbeState(
            helper=HelperKind.GNOME_SHELL_EXTENSION,
            availability=HelperProbeAvailability.INCOMPATIBLE,
            detail=_detail_token("import_failed", exc),
        )
    except Exception as exc:
        return HelperProbeState(
            helper=HelperKind.GNOME_SHELL_EXTENSION,
            availability=HelperProbeAvailability.INCOMPATIBLE,
            detail=_detail_token("import_failed", exc),
        )

    try:
        helper = SessionBus().get(GNOME_SHELL_HELPER_SERVICE_NAME, GNOME_SHELL_HELPER_OBJECT_PATH)
    except Exception as exc:
        if _looks_missing_helper(exc):
            return HelperProbeState(
                helper=HelperKind.GNOME_SHELL_EXTENSION,
                availability=HelperProbeAvailability.MISSING,
                detail="service_unavailable",
            )
        return HelperProbeState(
            helper=HelperKind.GNOME_SHELL_EXTENSION,
            availability=HelperProbeAvailability.INCOMPATIBLE,
            detail=_detail_token("dbus_get_failed", exc),
        )

    try:
        helper_kind = str(getattr(helper, "HelperKind") or "").strip().lower()
        protocol_version = int(getattr(helper, "ProtocolVersion"))
        helper_version = str(getattr(helper, "HelperVersion") or "").strip()
    except Exception as exc:
        return HelperProbeState(
            helper=HelperKind.GNOME_SHELL_EXTENSION,
            availability=HelperProbeAvailability.INCOMPATIBLE,
            detail=_detail_token("property_read_failed", exc),
        )

    if helper_kind != HelperKind.GNOME_SHELL_EXTENSION.value:
        return HelperProbeState(
            helper=HelperKind.GNOME_SHELL_EXTENSION,
            availability=HelperProbeAvailability.INCOMPATIBLE,
            version=helper_version,
            detail="helper_kind_mismatch",
        )
    if protocol_version != HELPER_PROTOCOL_VERSION:
        return HelperProbeState(
            helper=HelperKind.GNOME_SHELL_EXTENSION,
            availability=HelperProbeAvailability.INCOMPATIBLE,
            version=helper_version,
            detail=f"protocol_version_mismatch:{protocol_version}",
        )
    return HelperProbeState(
        helper=HelperKind.GNOME_SHELL_EXTENSION,
        availability=HelperProbeAvailability.AVAILABLE,
        version=helper_version,
        detail="session_dbus_reachable",
    )


def _looks_missing_helper(exc: Exception) -> bool:
    text = str(exc or "").strip().lower()
    return any(
        marker in text
        for marker in (
            "serviceunknown",
            "namehasnoowner",
            "unknownobject",
            "org.freedesktop.dbus.error.serviceunknown",
            "org.freedesktop.dbus.error.namehasnoowner",
        )
    )


def _detail_token(prefix: str, exc: Exception) -> str:
    detail = str(exc or "").strip().lower()
    detail = detail.replace(" ", "_")
    if not detail:
        return prefix
    return f"{prefix}:{detail}"
