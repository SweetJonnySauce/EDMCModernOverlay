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
    GNOME_SHELL_HELPER_RECT_REASON_FRAME_FALLBACK_CLAMPED,
    GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,
    HelperDbusProbeError,
    HelperDbusServiceMissing,
    HelperHealthStatus,
    HelperPresentationAction,
    HelperPresentationRequest,
    HelperPresentationState,
    HelperPresentationStatus,
    HelperRect,
    HelperTargetStatus,
    build_gnome_shell_helper_presentation_request,
    probe_gnome_shell_helper_health,
    probe_gnome_shell_helper_presentation,
    probe_gnome_shell_helper_target,
)

GNOME_HELPER_PRESENTATION_MAX_ATTEMPTS = 2
GNOME_HELPER_PRESENTATION_DBUS_TIMEOUT_SECONDS = 0.75
GNOME_HELPER_LEGACY_GEOMETRY_IGNORED = "ignored_helper_source_of_truth"
GNOME_HELPER_PRESENTATION_FOCUSED_FRESH_SECONDS = 1.0
GNOME_HELPER_PRESENTATION_SUPPRESSED_FRESH_SECONDS = 2.0
GNOME_HELPER_HEALTH_CACHE_SECONDS = 5.0
GNOME_HELPER_HEALTH_CACHE_JITTER_SECONDS = 0.5
GNOME_HELPER_SUPPRESSED_TARGET_POLL_SECONDS = 1.5
GNOME_HELPER_SURFACE_ACTION_MAPPED_SUPPRESSED = "mapped_suppressed"
GNOME_HELPER_EXPECTED_DEGRADE_REASONS = frozenset(
    (
        GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,
        GNOME_SHELL_HELPER_RECT_REASON_FRAME_FALLBACK_CLAMPED,
    )
)


@dataclass(frozen=True, slots=True)
class GnomeHelperPresentationSignature:
    """Backend-owned no-op key for a helper presentation request."""

    target_token: str
    requested_rect: tuple[int, int, int, int] | None
    monitor_rect: tuple[int, int, int, int] | None
    rect_source: str
    visibility_action: str
    target_has_focus: bool
    target_showing_on_workspace: bool
    target_minimized: bool
    target_fullscreen: bool
    overlay_title: str
    overlay_wm_class: str
    standalone_mode: bool
    renderer: str
    rect_tolerance: int
    require_placement: bool
    require_chrome_free: bool
    require_stacking: bool
    require_click_through: bool
    require_focus_safe: bool
    request_degrade_reasons: tuple[str, ...]


@dataclass(slots=True)
class GnomeHelperPresentationRuntimeState:
    """Mutable GNOME helper presentation cache owned by the backend bundle."""

    cached_health_status: HelperHealthStatus | None = None
    health_cache_expires_at: float = 0.0
    last_target_status: HelperTargetStatus | None = None
    last_request: HelperPresentationRequest | None = None
    last_presentation_status: HelperPresentationStatus | None = None
    last_signature: GnomeHelperPresentationSignature | None = None
    last_success_at: float = 0.0
    next_suppressed_target_poll_at: float = 0.0


_DEFAULT_PRESENTATION_RUNTIME_STATE = GnomeHelperPresentationRuntimeState()


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
    presentation_skipped: bool = False
    presentation_skip_reason: str = ""
    target_poll_skipped: bool = False
    health_cache_hit: bool = False

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
            "presentation_skipped": self.presentation_skipped,
            "presentation_skip_reason": self.presentation_skip_reason,
            "target_poll_skipped": self.target_poll_skipped,
            "health_cache_hit": self.health_cache_hit,
        }


def run_gnome_shell_helper_presentation_cycle(
    *,
    standalone_mode: bool = False,
    previous_surface_action: str = "",
    fetch_health: Callable[[], object] | None = None,
    fetch_target: Callable[[], object] | None = None,
    fetch_presentation: Callable[[HelperPresentationRequest], object] | None = None,
    clock: Callable[[], float] = time.monotonic,
    max_attempts: int = GNOME_HELPER_PRESENTATION_MAX_ATTEMPTS,
    runtime_state: GnomeHelperPresentationRuntimeState | None = None,
    health_cache_jitter_seconds: Callable[[], float] | None = None,
) -> GnomeHelperPresentationCycleResult:
    """Fetch target state and apply bounded Shell-mediated presentation."""

    health_fetcher = fetch_health or fetch_gnome_shell_helper_health_via_gdbus
    target_fetcher = fetch_target or fetch_gnome_shell_helper_target_via_gdbus
    presentation_fetcher = fetch_presentation or fetch_gnome_shell_helper_presentation_via_gdbus
    state = _runtime_state_for_call(
        runtime_state,
        fetch_health=fetch_health,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
    )
    now = float(clock())

    health_status, health_cache_hit = _health_status_with_cache(
        state,
        health_fetcher,
        now_monotonic=now,
        clock=clock,
        health_cache_jitter_seconds=health_cache_jitter_seconds,
    )
    if not health_status.healthy:
        _clear_presentation_cache(state)
        return GnomeHelperPresentationCycleResult(
            health_status=health_status,
            health_cache_hit=health_cache_hit,
        )

    if _should_skip_suppressed_target_poll(
        state,
        previous_surface_action=previous_surface_action,
        now_monotonic=now,
    ):
        return GnomeHelperPresentationCycleResult(
            health_status=health_status,
            target_status=state.last_target_status,
            request=state.last_request,
            presentation_status=state.last_presentation_status,
            presentation_skipped=True,
            presentation_skip_reason="suppressed_poll_throttle",
            target_poll_skipped=True,
            health_cache_hit=health_cache_hit,
        )

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
        signature = _presentation_signature(
            target_status,
            request,
            previous_surface_action=previous_surface_action,
        )
        if attempt == 1 and _should_skip_presentation_apply(
            state,
            signature,
            request,
            previous_surface_action=previous_surface_action,
            now_monotonic=now,
        ):
            state.last_target_status = target_status
            state.last_request = request
            if previous_surface_action == GNOME_HELPER_SURFACE_ACTION_MAPPED_SUPPRESSED:
                state.next_suppressed_target_poll_at = now + GNOME_HELPER_SUPPRESSED_TARGET_POLL_SECONDS
            return GnomeHelperPresentationCycleResult(
                health_status=health_status,
                target_status=target_status,
                request=request,
                presentation_status=state.last_presentation_status,
                presentation_skipped=True,
                presentation_skip_reason="fresh_matching_presentation",
                health_cache_hit=health_cache_hit,
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

    _update_presentation_cache(
        state,
        target_status=target_status,
        request=request,
        presentation_status=presentation_status,
        previous_surface_action=previous_surface_action,
        now_monotonic=now,
    )
    return GnomeHelperPresentationCycleResult(
        health_status=health_status,
        target_status=target_status,
        request=request,
        presentation_status=presentation_status,
        attempts=attempts,
        retry_reasons=tuple(retry_reasons),
        health_cache_hit=health_cache_hit,
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


def _runtime_state_for_call(
    runtime_state: GnomeHelperPresentationRuntimeState | None,
    *,
    fetch_health: Callable[[], object] | None,
    fetch_target: Callable[[], object] | None,
    fetch_presentation: Callable[[HelperPresentationRequest], object] | None,
) -> GnomeHelperPresentationRuntimeState:
    if runtime_state is not None:
        return runtime_state
    if fetch_health is None and fetch_target is None and fetch_presentation is None:
        return _DEFAULT_PRESENTATION_RUNTIME_STATE
    return GnomeHelperPresentationRuntimeState()


def _health_status_with_cache(
    state: GnomeHelperPresentationRuntimeState,
    health_fetcher: Callable[[], object],
    *,
    now_monotonic: float,
    clock: Callable[[], float],
    health_cache_jitter_seconds: Callable[[], float] | None,
) -> tuple[HelperHealthStatus, bool]:
    cached = state.cached_health_status
    if (
        cached is not None
        and cached.healthy
        and now_monotonic < state.health_cache_expires_at
        and not cached.is_stale(now_monotonic)
    ):
        return cached, True

    health_status = probe_gnome_shell_helper_health(health_fetcher, clock=clock)
    if health_status.healthy:
        state.cached_health_status = health_status
        state.health_cache_expires_at = now_monotonic + GNOME_HELPER_HEALTH_CACHE_SECONDS + _bounded_health_jitter(
            health_cache_jitter_seconds,
        )
    else:
        state.cached_health_status = None
        state.health_cache_expires_at = 0.0
    return health_status, False


def _bounded_health_jitter(health_cache_jitter_seconds: Callable[[], float] | None) -> float:
    try:
        raw_value = (
            float(health_cache_jitter_seconds())
            if health_cache_jitter_seconds is not None
            else _default_health_cache_jitter_seconds()
        )
    except (TypeError, ValueError):
        raw_value = 0.0
    return min(max(raw_value, 0.0), GNOME_HELPER_HEALTH_CACHE_JITTER_SECONDS)


def _default_health_cache_jitter_seconds() -> float:
    return ((os.getpid() % 1000) / 1000.0) * GNOME_HELPER_HEALTH_CACHE_JITTER_SECONDS


def _should_skip_suppressed_target_poll(
    state: GnomeHelperPresentationRuntimeState,
    *,
    previous_surface_action: str,
    now_monotonic: float,
) -> bool:
    if previous_surface_action != GNOME_HELPER_SURFACE_ACTION_MAPPED_SUPPRESSED:
        return False
    if now_monotonic >= state.next_suppressed_target_poll_at:
        return False
    if state.last_target_status is None or state.last_request is None or state.last_presentation_status is None:
        return False
    return _cached_presentation_is_fresh_and_matching(
        state,
        request=state.last_request,
        previous_surface_action=previous_surface_action,
        now_monotonic=now_monotonic,
    )


def _should_skip_presentation_apply(
    state: GnomeHelperPresentationRuntimeState,
    signature: GnomeHelperPresentationSignature | None,
    request: HelperPresentationRequest,
    *,
    previous_surface_action: str,
    now_monotonic: float,
) -> bool:
    if signature is None or state.last_signature != signature:
        return False
    return _cached_presentation_is_fresh_and_matching(
        state,
        request=request,
        previous_surface_action=previous_surface_action,
        now_monotonic=now_monotonic,
    )


def _cached_presentation_is_fresh_and_matching(
    state: GnomeHelperPresentationRuntimeState,
    *,
    request: HelperPresentationRequest,
    previous_surface_action: str,
    now_monotonic: float,
) -> bool:
    status = state.last_presentation_status
    if status is None:
        return False
    if status.is_stale(now_monotonic):
        return False
    fresh_seconds = (
        GNOME_HELPER_PRESENTATION_SUPPRESSED_FRESH_SECONDS
        if previous_surface_action == GNOME_HELPER_SURFACE_ACTION_MAPPED_SUPPRESSED
        else GNOME_HELPER_PRESENTATION_FOCUSED_FRESH_SECONDS
    )
    if state.last_success_at <= 0 or (now_monotonic - state.last_success_at) > fresh_seconds:
        return False
    return _presentation_status_is_matching_success(status, request)


def _update_presentation_cache(
    state: GnomeHelperPresentationRuntimeState,
    *,
    target_status: HelperTargetStatus | None,
    request: HelperPresentationRequest | None,
    presentation_status: HelperPresentationStatus | None,
    previous_surface_action: str,
    now_monotonic: float,
) -> None:
    state.last_target_status = target_status
    state.last_request = request
    state.last_presentation_status = presentation_status
    signature = (
        _presentation_signature(target_status, request, previous_surface_action=previous_surface_action)
        if target_status is not None and request is not None
        else None
    )
    if request is not None and presentation_status is not None and _presentation_status_is_matching_success(
        presentation_status,
        request,
    ):
        state.last_signature = signature
        state.last_success_at = now_monotonic
        if previous_surface_action == GNOME_HELPER_SURFACE_ACTION_MAPPED_SUPPRESSED:
            state.next_suppressed_target_poll_at = now_monotonic + GNOME_HELPER_SUPPRESSED_TARGET_POLL_SECONDS
        else:
            state.next_suppressed_target_poll_at = 0.0
        return
    state.last_signature = None
    state.last_success_at = 0.0
    state.next_suppressed_target_poll_at = 0.0


def _clear_presentation_cache(state: GnomeHelperPresentationRuntimeState) -> None:
    state.last_target_status = None
    state.last_request = None
    state.last_presentation_status = None
    state.last_signature = None
    state.last_success_at = 0.0
    state.next_suppressed_target_poll_at = 0.0


def _presentation_status_is_matching_success(
    status: HelperPresentationStatus,
    request: HelperPresentationRequest,
) -> bool:
    if request.action is not HelperPresentationAction.ATTACH:
        return False
    if status.action is not HelperPresentationAction.ATTACH:
        return False
    if status.target_token != request.target_token:
        return False
    if status.requested_rect != request.content_rect:
        return False
    if not status.rect_match or status.applied_rect is None or not status.applied_rect.valid:
        return False
    if status.unsupported_features:
        return False
    if not (
        status.placement
        and status.chrome_free
        and status.stacking
        and status.click_through
        and status.focus_safe
        and status.pyqt_renderer_preserved
    ):
        return False
    expected_reasons = set(request.degrade_reasons)
    if not expected_reasons.issubset(GNOME_HELPER_EXPECTED_DEGRADE_REASONS):
        return False
    unexpected_reasons = set(status.degrade_reasons) - expected_reasons
    if unexpected_reasons:
        return False
    if status.state is HelperPresentationState.APPLIED:
        return not status.degrade_reasons
    return status.state is HelperPresentationState.DEGRADED and bool(expected_reasons)


def _presentation_signature(
    target_status: HelperTargetStatus | None,
    request: HelperPresentationRequest | None,
    *,
    previous_surface_action: str,
) -> GnomeHelperPresentationSignature | None:
    if target_status is None or request is None:
        return None
    target = target_status.target if target_status.found else None
    if target is None:
        return None
    return GnomeHelperPresentationSignature(
        target_token=request.target_token,
        requested_rect=_rect_signature(request.content_rect),
        monitor_rect=_rect_signature(target.monitor_rect),
        rect_source=request.rect_source,
        visibility_action=str(previous_surface_action or ""),
        target_has_focus=bool(target.has_focus),
        target_showing_on_workspace=bool(target.showing_on_workspace),
        target_minimized=bool(target.minimized),
        target_fullscreen=bool(target.fullscreen),
        overlay_title=request.overlay_title,
        overlay_wm_class=request.overlay_wm_class,
        standalone_mode=bool(request.standalone_mode),
        renderer=request.renderer,
        rect_tolerance=int(request.rect_tolerance),
        require_placement=bool(request.require_placement),
        require_chrome_free=bool(request.require_chrome_free),
        require_stacking=bool(request.require_stacking),
        require_click_through=bool(request.require_click_through),
        require_focus_safe=bool(request.require_focus_safe),
        request_degrade_reasons=tuple(request.degrade_reasons),
    )


def _rect_signature(rect: HelperRect | None) -> tuple[int, int, int, int] | None:
    if rect is None or not rect.valid:
        return None
    return (rect.x, rect.y, rect.width, rect.height)


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
