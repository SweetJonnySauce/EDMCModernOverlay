"""Platform context helpers for the overlay client."""
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any, Mapping, Optional

from overlay_client.backend import BackendSelectionStatus, BackendSelector, ProbeInputs, ProbeSource, SessionType, collect_platform_probe
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
    probe = collect_platform_probe(
        ProbeInputs(
            source=source,
            sys_platform=sys_platform_name or sys.platform,
            qt_platform_name=qt_platform_name,
            session_type=session_hint,
            compositor=compositor_hint,
            is_flatpak=flatpak_flag,
            flatpak_app_id=flatpak_app,
            env=env_map,
        )
    )
    return BackendSelector(
        shadow_mode=False,
        stable_notes=("client_selector_result",),
    ).select(probe, manual_override=context.manual_backend_override)

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
