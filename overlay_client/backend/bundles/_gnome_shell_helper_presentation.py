"""Runtime GNOME Shell helper presentation cycle for Wayland placement."""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import Callable, Mapping

from overlay_client.backend import (
    GNOME_SHELL_HELPER_DBUS_HEALTH_METHOD,
    GNOME_SHELL_HELPER_DBUS_INTERFACE,
    GNOME_SHELL_HELPER_DBUS_OBJECT_PATH,
    GNOME_SHELL_HELPER_DBUS_PRESENTATION_METHOD,
    GNOME_SHELL_HELPER_DBUS_SERVICE,
    GNOME_SHELL_HELPER_DBUS_TARGET_METHOD,
    HelperDbusProbeError,
    HelperDbusServiceMissing,
    HelperHealthStatus,
    HelperPresentationRequest,
    HelperPresentationState,
    HelperPresentationStatus,
    HelperTargetStatus,
    build_gnome_shell_helper_presentation_request,
    probe_gnome_shell_helper_health,
    probe_gnome_shell_helper_presentation,
    probe_gnome_shell_helper_target,
)

GNOME_HELPER_PRESENTATION_MAX_ATTEMPTS = 2
GNOME_HELPER_PRESENTATION_DBUS_TIMEOUT_SECONDS = 0.75
GNOME_HELPER_LEGACY_GEOMETRY_IGNORED = "ignored_helper_source_of_truth"


@dataclass(frozen=True, slots=True)
class GnomeHelperPresentationCycleResult:
    """One runtime helper presentation poll cycle and its diagnostics."""

    health_status: HelperHealthStatus | None = None
    target_status: HelperTargetStatus | None = None
    request: HelperPresentationRequest | None = None
    presentation_status: HelperPresentationStatus | None = None
    attempts: int = 0
    retry_reasons: tuple[str, ...] = field(default_factory=tuple)
    legacy_geometry_policy: str = GNOME_HELPER_LEGACY_GEOMETRY_IGNORED

    @property
    def helper_healthy(self) -> bool:
        return self.health_status is not None and self.health_status.healthy

    @property
    def target_found(self) -> bool:
        return self.target_status is not None and self.target_status.found

    @property
    def presentation_ready(self) -> bool:
        return self.presentation_status is not None and self.presentation_status.true_overlay_ready

    @property
    def should_show_overlay(self) -> bool:
        return (
            self.target_found
            and self.request is not None
            and self.request.action.value == "attach"
        )

    def to_log_payload(self) -> dict[str, object]:
        """Return a compact, stable diagnostics payload for log/debug consumers."""

        target = self.target_status.target if self.target_status is not None else None
        return {
            "helper_health": self.health_status.state.value if self.health_status is not None else "unknown",
            "target_state": self.target_status.state.value if self.target_status is not None else "unknown",
            "target_token": target.target_token if target is not None else "",
            "target_sequence": self.target_status.sequence if self.target_status is not None else 0,
            "target_monitor": target.monitor if target is not None else None,
            "target_output_name": target.output_name if target is not None else "",
            "target_monitor_rect": (
                target.monitor_rect.to_payload() if target is not None and target.monitor_rect is not None else None
            ),
            "target_frame_rect": (
                target.frame_rect.to_payload() if target is not None and target.frame_rect is not None else None
            ),
            "rect_source": self.request.rect_source if self.request is not None else "unavailable",
            "requested_rect": (
                self.request.content_rect.to_payload()
                if self.request is not None and self.request.content_rect is not None
                else None
            ),
            "presentation_state": (
                self.presentation_status.state.value if self.presentation_status is not None else "not_attempted"
            ),
            "applied_rect": (
                self.presentation_status.applied_rect.to_payload()
                if self.presentation_status is not None and self.presentation_status.applied_rect is not None
                else None
            ),
            "rect_match": bool(self.presentation_status.rect_match) if self.presentation_status is not None else False,
            "rect_delta": list(self.presentation_status.rect_delta) if self.presentation_status is not None else [],
            "presentation_reasons": (
                list(self.presentation_status.degrade_reasons) if self.presentation_status is not None else []
            ),
            "attempts": self.attempts,
            "retry_reasons": list(self.retry_reasons),
            "legacy_geometry_policy": self.legacy_geometry_policy,
        }


def run_gnome_shell_helper_presentation_cycle(
    *,
    standalone_mode: bool = False,
    fetch_health: Callable[[], object] | None = None,
    fetch_target: Callable[[], object] | None = None,
    fetch_presentation: Callable[[HelperPresentationRequest], object] | None = None,
    clock: Callable[[], float] = time.monotonic,
    max_attempts: int = GNOME_HELPER_PRESENTATION_MAX_ATTEMPTS,
) -> GnomeHelperPresentationCycleResult:
    """Fetch target state and apply bounded Shell-mediated presentation."""

    health_fetcher = fetch_health or fetch_gnome_shell_helper_health_via_gdbus
    target_fetcher = fetch_target or fetch_gnome_shell_helper_target_via_gdbus
    presentation_fetcher = fetch_presentation or fetch_gnome_shell_helper_presentation_via_gdbus

    health_status = probe_gnome_shell_helper_health(health_fetcher, clock=clock)
    if not health_status.healthy:
        return GnomeHelperPresentationCycleResult(health_status=health_status)

    attempts_allowed = max(1, int(max_attempts))
    target_status: HelperTargetStatus | None = None
    request: HelperPresentationRequest | None = None
    presentation_status: HelperPresentationStatus | None = None
    retry_reasons: list[str] = []
    attempts = 0
    for attempt in range(1, attempts_allowed + 1):
        target_status = probe_gnome_shell_helper_target(
            target_fetcher,
            health_status=health_status,
            clock=clock,
        )
        request = build_gnome_shell_helper_presentation_request(
            target_status,
            standalone_mode=standalone_mode,
        )
        presentation_status = probe_gnome_shell_helper_presentation(
            presentation_fetcher,
            health_status=health_status,
            target_status=target_status,
            request=request,
            clock=clock,
        )
        attempts = attempt
        if _should_retry_presentation(presentation_status) and attempt < attempts_allowed:
            retry_reasons.append("applied_rect_mismatch")
            continue
        break

    return GnomeHelperPresentationCycleResult(
        health_status=health_status,
        target_status=target_status,
        request=request,
        presentation_status=presentation_status,
        attempts=attempts,
        retry_reasons=tuple(retry_reasons),
    )


def fetch_gnome_shell_helper_health_via_gdbus() -> object:
    """Fetch helper health through the local user session bus using gdbus."""

    return _call_gnome_shell_helper_method(GNOME_SHELL_HELPER_DBUS_HEALTH_METHOD)


def fetch_gnome_shell_helper_target_via_gdbus() -> object:
    """Fetch helper target state through the local user session bus using gdbus."""

    return _call_gnome_shell_helper_method(GNOME_SHELL_HELPER_DBUS_TARGET_METHOD, "{}")


def fetch_gnome_shell_helper_presentation_via_gdbus(request: HelperPresentationRequest) -> object:
    """Apply helper presentation through the local user session bus using gdbus."""

    payload = json.dumps(request.to_payload(), separators=(",", ":"))
    return _call_gnome_shell_helper_method(GNOME_SHELL_HELPER_DBUS_PRESENTATION_METHOD, payload)


def _should_retry_presentation(status: HelperPresentationStatus) -> bool:
    return (
        status.state is HelperPresentationState.DEGRADED
        and "applied_rect_mismatch" in status.degrade_reasons
    )


def _call_gnome_shell_helper_method(method: str, argument: str | None = None) -> object:
    command = [
        "gdbus",
        "call",
        "--session",
        "--dest",
        GNOME_SHELL_HELPER_DBUS_SERVICE,
        "--object-path",
        GNOME_SHELL_HELPER_DBUS_OBJECT_PATH,
        "--method",
        f"{GNOME_SHELL_HELPER_DBUS_INTERFACE}.{method}",
    ]
    if argument is not None:
        command.append(argument)
    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=GNOME_HELPER_PRESENTATION_DBUS_TIMEOUT_SECONDS,
            env=_session_bus_env(os.environ),
        )
    except FileNotFoundError as exc:
        raise HelperDbusProbeError("gdbus command not found") from exc
    except subprocess.TimeoutExpired as exc:
        raise HelperDbusProbeError(f"gdbus {method} call timed out") from exc
    output = (result.stdout or "").strip()
    diagnostic = "\n".join(part for part in (output, (result.stderr or "").strip()) if part)
    if result.returncode != 0:
        if "ServiceUnknown" in diagnostic or "NameHasNoOwner" in diagnostic:
            raise HelperDbusServiceMissing(diagnostic or "helper DBus service is not owned")
        raise HelperDbusProbeError(diagnostic or f"gdbus exited with status {result.returncode}")
    if not output:
        raise HelperDbusProbeError(f"gdbus {method} call returned no payload")
    return output


def _session_bus_env(env: Mapping[str, str]) -> dict[str, str]:
    child_env = os.environ.copy()
    runtime_dir = str(env.get("XDG_RUNTIME_DIR") or "").strip()
    bus_address = str(env.get("DBUS_SESSION_BUS_ADDRESS") or "").strip()
    if runtime_dir:
        child_env["XDG_RUNTIME_DIR"] = runtime_dir
    if bus_address:
        child_env["DBUS_SESSION_BUS_ADDRESS"] = bus_address
    elif runtime_dir:
        child_env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={runtime_dir}/bus"
    return child_env
