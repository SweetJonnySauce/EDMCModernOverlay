"""Runtime GNOME Shell helper presentation cycle for Wayland placement."""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field, replace
from typing import Callable, Mapping

from overlay_client.backend import (
    GNOME_SHELL_HELPER_DBUS_HEALTH_METHOD,
    GNOME_SHELL_HELPER_DBUS_INTERFACE,
    GNOME_SHELL_HELPER_DBUS_OBJECT_PATH,
    GNOME_SHELL_HELPER_DBUS_PRESENTATION_METHOD,
    GNOME_SHELL_HELPER_DBUS_SERVICE,
    GNOME_SHELL_HELPER_DBUS_TARGET_METHOD,
    GNOME_SHELL_HELPER_RECT_REASON_FRAME_FALLBACK_CLAMPED,
    GNOME_SHELL_HELPER_RECT_SOURCE_CONTENT,
    GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,
    HELPER_PROTOCOL,
    HelperDbusProbeError,
    HelperDbusServiceMissing,
    HelperHealthStatus,
    HelperPresentationAction,
    HelperPresentationRequest,
    HelperPresentationState,
    HelperPresentationStatus,
    HelperRasterFrameRequest,
    HelperRect,
    HelperTargetStatus,
    build_gnome_shell_helper_presentation_request,
    probe_gnome_shell_helper_health,
    probe_gnome_shell_helper_presentation,
    probe_gnome_shell_helper_target,
)
from overlay_client.backend.shell_raster_frame import (
    SHELL_RASTER_FRAME_RENDERER,
    build_static_shell_raster_frame_request,
)
from overlay_client.backend.surface_preparation import BackendPresentationSurfacePreparation

GNOME_HELPER_PRESENTATION_MAX_ATTEMPTS = 2
GNOME_HELPER_PRESENTATION_DBUS_TIMEOUT_SECONDS = 0.75
GNOME_HELPER_LEGACY_GEOMETRY_IGNORED = "ignored_helper_source_of_truth"
GNOME_HELPER_PRESENTATION_FOCUSED_FRESH_SECONDS = 1.0
GNOME_HELPER_PRESENTATION_SUPPRESSED_FRESH_SECONDS = 2.0
GNOME_HELPER_HEALTH_CACHE_SECONDS = 5.0
GNOME_HELPER_HEALTH_CACHE_JITTER_SECONDS = 0.5
GNOME_HELPER_SUPPRESSED_TARGET_POLL_SECONDS = 1.5
GNOME_HELPER_SURFACE_ACTION_MAPPED_SUPPRESSED = "mapped_suppressed"
GNOME_HELPER_GEOMETRY_DIAGNOSTICS_ENV = "EDMC_OVERLAY_GNOME_GEOMETRY_DIAGNOSTICS"
GNOME_HELPER_PRESENTATION_DIAGNOSTICS_ENV = "EDMC_OVERLAY_GNOME_PRESENTATION_DIAGNOSTICS"
GNOME_HELPER_BORDERLESS_FULLSCREEN_PREP_ENV = "EDMC_OVERLAY_GNOME_BORDERLESS_FULLSCREEN_PREP"
GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV = "EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE"
GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV = "EDMC_OVERLAY_GNOME_SHELL_RASTER_BRIDGE_RUNTIME"
GNOME_HELPER_SHELL_RASTER_LEASE_REFRESH_FRACTION = 0.5
GNOME_HELPER_SHELL_RASTER_MIN_REFRESH_SECONDS = 0.25
GNOME_HELPER_PERSISTENT_MISMATCH_THRESHOLD = 2
GNOME_HELPER_REASON_APPLIED_RECT_MISMATCH = "applied_rect_mismatch"
GNOME_HELPER_REASON_WRONG_MONITOR_APPLIED_RECT = "wrong_monitor_applied_rect"
GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH = "persistent_applied_rect_mismatch"
GNOME_HELPER_REASON_SURFACE_PREPARATION_FAILED = "surface_preparation_failed"
GNOME_HELPER_REASON_SHELL_RASTER_OVERVIEW_ACTIVE = "gnome_overview_active"
GNOME_HELPER_REASON_SHELL_RASTER_TARGET_NOT_FOCUSED = "target_not_focused"
GNOME_HELPER_SURFACE_PREPARATION_FULLSCREEN_MONITOR = "fullscreen_monitor"
GNOME_HELPER_SHELL_RASTER_SUPPRESS_FALLBACK_REASONS = frozenset(
    (
        GNOME_HELPER_REASON_SHELL_RASTER_OVERVIEW_ACTIVE,
        GNOME_HELPER_REASON_SHELL_RASTER_TARGET_NOT_FOCUSED,
    )
)
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
    include_presentation_diagnostics: bool
    surface_preparation_mode: str
    request_degrade_reasons: tuple[str, ...]
    shell_raster_frame_signature: tuple[object, ...] | None = None


@dataclass(frozen=True, slots=True)
class GnomeHelperPersistentMismatchKey:
    """Stable key for repeated wrong-monitor applied rect mismatches."""

    signature: GnomeHelperPresentationSignature
    target_token: str
    requested_rect: tuple[int, int, int, int]
    applied_rect: tuple[int, int, int, int]


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
    persistent_mismatch_key: GnomeHelperPersistentMismatchKey | None = None
    persistent_mismatch_count: int = 0
    persistent_mismatch_status: HelperPresentationStatus | None = None
    last_surface_preparation: BackendPresentationSurfacePreparation | None = None


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
    persistent_mismatch_count: int = 0
    persistent_mismatch_backoff: bool = False
    surface_preparation: BackendPresentationSurfacePreparation | None = None
    surface_preparation_failed: bool = False

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
    def shell_raster_frame_presented(self) -> bool:
        status = self.presentation_status
        return (
            status is not None
            and status.renderer == SHELL_RASTER_FRAME_RENDERER
            and status.state is HelperPresentationState.APPLIED
            and status.rect_match
            and status.applied_rect is not None
            and status.applied_rect.valid
        )

    @property
    def shell_raster_frame_suspended_for_focus_risk(self) -> bool:
        status = self.presentation_status
        return (
            status is not None
            and status.renderer == SHELL_RASTER_FRAME_RENDERER
            and bool(set(status.degrade_reasons) & GNOME_HELPER_SHELL_RASTER_SUPPRESS_FALLBACK_REASONS)
        )

    @property
    def should_show_overlay(self) -> bool:
        if self.shell_raster_frame_presented:
            return False
        if self.shell_raster_frame_suspended_for_focus_risk:
            return False
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
            "target_geometry_diagnostics": (
                target.geometry_diagnostics.to_payload()
                if target is not None and target.geometry_diagnostics is not None
                else None
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
            "presentation_diagnostics": (
                dict(self.presentation_status.presentation_diagnostics)
                if self.presentation_status is not None and self.presentation_status.presentation_diagnostics is not None
                else None
            ),
            "attempts": self.attempts,
            "retry_reasons": list(self.retry_reasons),
            "legacy_geometry_policy": self.legacy_geometry_policy,
            "presentation_skipped": self.presentation_skipped,
            "presentation_skip_reason": self.presentation_skip_reason,
            "target_poll_skipped": self.target_poll_skipped,
            "health_cache_hit": self.health_cache_hit,
            "persistent_mismatch_count": self.persistent_mismatch_count,
            "persistent_mismatch_backoff": self.persistent_mismatch_backoff,
            "surface_preparation": self.surface_preparation.mode if self.surface_preparation is not None else "",
            "surface_preparation_rect": (
                {
                    "x": self.surface_preparation.rect[0],
                    "y": self.surface_preparation.rect[1],
                    "width": self.surface_preparation.rect[2],
                    "height": self.surface_preparation.rect[3],
                }
                if self.surface_preparation is not None
                else None
            ),
            "surface_preparation_failed": self.surface_preparation_failed,
            "shell_raster_frame": (
                self.request.shell_raster_frame.to_payload()
                if self.request is not None and self.request.shell_raster_frame is not None
                else None
            ),
            "shell_raster_status": (
                dict(self.presentation_status.shell_raster_frame)
                if self.presentation_status is not None and self.presentation_status.shell_raster_frame is not None
                else None
            ),
            "shell_raster_metrics": _shell_raster_metrics_payload(self.request, self.presentation_status),
        }


def run_gnome_shell_helper_presentation_cycle(
    *,
    standalone_mode: bool = False,
    keep_overlay_visible: bool = False,
    previous_surface_action: str = "",
    fetch_health: Callable[[], object] | None = None,
    fetch_target: Callable[[], object] | None = None,
    fetch_presentation: Callable[[HelperPresentationRequest], object] | None = None,
    clock: Callable[[], float] = time.monotonic,
    max_attempts: int = GNOME_HELPER_PRESENTATION_MAX_ATTEMPTS,
    runtime_state: GnomeHelperPresentationRuntimeState | None = None,
    health_cache_jitter_seconds: Callable[[], float] | None = None,
    prepare_surface: Callable[[BackendPresentationSurfacePreparation], bool] | None = None,
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
    include_presentation_diagnostics = _env_flag_enabled(os.environ.get(GNOME_HELPER_PRESENTATION_DIAGNOSTICS_ENV, ""))
    target_status: HelperTargetStatus | None = None
    request: HelperPresentationRequest | None = None
    presentation_status: HelperPresentationStatus | None = None
    surface_preparation: BackendPresentationSurfacePreparation | None = None
    surface_preparation_failed = False
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
            include_presentation_diagnostics=include_presentation_diagnostics,
        )
        request = _shell_raster_bridge_request(
            target_status,
            request,
            env=os.environ,
            allow_unfocused_target=keep_overlay_visible,
        )
        surface_preparation = _borderless_fullscreen_surface_preparation(
            target_status,
            request,
            env=os.environ,
        )
        signature = _presentation_signature(
            target_status,
            request,
            previous_surface_action=previous_surface_action,
            surface_preparation=surface_preparation,
        )
        if attempt == 1 and _should_skip_presentation_apply(
            state,
            signature,
            request,
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
                surface_preparation=surface_preparation,
            )
        if attempt == 1 and _should_skip_persistent_mismatch_apply(state, signature):
            state.last_target_status = target_status
            state.last_request = request
            state.last_presentation_status = state.persistent_mismatch_status
            return GnomeHelperPresentationCycleResult(
                health_status=health_status,
                target_status=target_status,
                request=request,
                presentation_status=state.persistent_mismatch_status,
                presentation_skipped=True,
                presentation_skip_reason=GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH,
                health_cache_hit=health_cache_hit,
                persistent_mismatch_count=state.persistent_mismatch_count,
                persistent_mismatch_backoff=True,
                surface_preparation=surface_preparation,
            )
        if attempt == 1 and surface_preparation is not None:
            if not _apply_surface_preparation(surface_preparation, prepare_surface):
                surface_preparation_failed = True
                presentation_status = _surface_preparation_failed_status(
                    target_status,
                    request,
                    surface_preparation=surface_preparation,
                    now_monotonic=now,
                )
                break
        presentation_status = probe_gnome_shell_helper_presentation(
            presentation_fetcher,
            health_status=health_status,
            target_status=target_status,
            request=request,
            clock=clock,
        )
        presentation_status = _presentation_status_with_wrong_monitor_reason(
            presentation_status,
            target_status,
        )
        attempts = attempt
        if _should_retry_presentation(presentation_status) and attempt < attempts_allowed:
            retry_reasons.append("applied_rect_mismatch")
            continue
        break

    signature = (
        _presentation_signature(
            target_status,
            request,
            previous_surface_action=previous_surface_action,
            surface_preparation=surface_preparation,
        )
        if target_status is not None and request is not None
        else None
    )
    presentation_status = _update_persistent_mismatch_cache(
        state,
        signature=signature,
        request=request,
        presentation_status=presentation_status,
    )
    _update_presentation_cache(
        state,
        target_status=target_status,
        request=request,
        presentation_status=presentation_status,
        previous_surface_action=previous_surface_action,
        now_monotonic=now,
        surface_preparation=surface_preparation,
    )
    return GnomeHelperPresentationCycleResult(
        health_status=health_status,
        target_status=target_status,
        request=request,
        presentation_status=presentation_status,
        attempts=attempts,
        retry_reasons=tuple(retry_reasons),
        health_cache_hit=health_cache_hit,
        persistent_mismatch_count=state.persistent_mismatch_count,
        persistent_mismatch_backoff=(
            state.persistent_mismatch_count >= GNOME_HELPER_PERSISTENT_MISMATCH_THRESHOLD
            and state.persistent_mismatch_key is not None
        ),
        surface_preparation=surface_preparation,
        surface_preparation_failed=surface_preparation_failed,
    )


def fetch_gnome_shell_helper_health_via_gdbus() -> object:
    """Fetch helper health through the local user session bus using gdbus."""

    return _call_gnome_shell_helper_method(GNOME_SHELL_HELPER_DBUS_HEALTH_METHOD)


def fetch_gnome_shell_helper_target_via_gdbus() -> object:
    """Fetch helper target state through the local user session bus using gdbus."""

    return _call_gnome_shell_helper_method(
        GNOME_SHELL_HELPER_DBUS_TARGET_METHOD,
        _target_query_payload(os.environ),
    )


def fetch_gnome_shell_helper_presentation_via_gdbus(request: HelperPresentationRequest) -> object:
    """Apply helper presentation through the local user session bus using gdbus."""

    payload = json.dumps(request.to_payload(), separators=(",", ":"))
    return _call_gnome_shell_helper_method(GNOME_SHELL_HELPER_DBUS_PRESENTATION_METHOD, payload)


def build_shell_raster_frame_clear_request() -> HelperPresentationRequest:
    """Build a helper request that only clears the Shell raster frame actor."""

    dummy_rect = HelperRect(0, 0, 1, 1)
    return HelperPresentationRequest(
        action=HelperPresentationAction.DEGRADE,
        target_token="",
        content_rect=None,
        renderer=SHELL_RASTER_FRAME_RENDERER,
        require_placement=False,
        require_chrome_free=False,
        require_stacking=False,
        require_click_through=False,
        require_focus_safe=False,
        shell_raster_frame=HelperRasterFrameRequest(
            action="clear",
            frame_version="shutdown-clear",
            target_token="",
            target_rect=dummy_rect,
            frame_rect=dummy_rect,
            scale=1.0,
            image_path="",
            checksum="",
            byte_size=0,
            stale_timeout_ms=0,
        ),
    )


def clear_gnome_shell_raster_frame_via_gdbus(
    fetch_presentation: Callable[[HelperPresentationRequest], object] | None = None,
) -> bool:
    """Best-effort shutdown cleanup for Phase 12 Shell raster frame actors."""

    fetcher = fetch_presentation or fetch_gnome_shell_helper_presentation_via_gdbus
    try:
        fetcher(build_shell_raster_frame_clear_request())
    except Exception:
        return False
    return True


def _should_retry_presentation(status: HelperPresentationStatus) -> bool:
    return (
        status.state is HelperPresentationState.DEGRADED
        and GNOME_HELPER_REASON_APPLIED_RECT_MISMATCH in status.degrade_reasons
    )


def _shell_raster_bridge_request(
    target_status: HelperTargetStatus | None,
    request: HelperPresentationRequest | None,
    *,
    env: Mapping[str, str],
    allow_unfocused_target: bool = False,
) -> HelperPresentationRequest | None:
    if request is None:
        return None
    if not _env_flag_enabled(env.get(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "")):
        return request
    if not _env_flag_enabled(env.get(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "")):
        return request
    result = build_static_shell_raster_frame_request(
        target_status,
        request,
        env=env,
        include_diagnostics=_env_flag_enabled(env.get(GNOME_HELPER_PRESENTATION_DIAGNOSTICS_ENV, "")),
    )
    if result.request is None:
        return request
    shell_raster_frame = replace(
        result.request,
        allow_unfocused_target=bool(allow_unfocused_target),
    )
    return replace(
        request,
        renderer=SHELL_RASTER_FRAME_RENDERER,
        shell_raster_frame=shell_raster_frame,
    )


def _borderless_fullscreen_surface_preparation(
    target_status: HelperTargetStatus | None,
    request: HelperPresentationRequest | None,
    *,
    env: Mapping[str, str],
) -> BackendPresentationSurfacePreparation | None:
    if not _env_flag_enabled(env.get(GNOME_HELPER_BORDERLESS_FULLSCREEN_PREP_ENV, "")):
        return None
    if target_status is None or request is None or request.action is not HelperPresentationAction.ATTACH:
        return None
    if request.shell_raster_frame is not None:
        return None
    target = target_status.target if target_status.found else None
    if target is None or not target.fullscreen:
        return None
    if request.rect_source != GNOME_SHELL_HELPER_RECT_SOURCE_CONTENT:
        return None
    if (
        target.content_rect is None
        or target.monitor_rect is None
        or request.content_rect is None
        or not target.content_rect.valid
        or not target.monitor_rect.valid
        or not request.content_rect.valid
    ):
        return None
    tolerance = int(max(0, request.rect_tolerance))
    if not _helper_rects_match(target.content_rect, target.monitor_rect, tolerance=tolerance):
        return None
    if not _helper_rects_match(request.content_rect, target.monitor_rect, tolerance=tolerance):
        return None
    rect = _rect_signature(request.content_rect)
    if rect is None:
        return None
    return BackendPresentationSurfacePreparation(
        mode=GNOME_HELPER_SURFACE_PREPARATION_FULLSCREEN_MONITOR,
        rect=rect,
        reason="gnome_borderless_full_monitor",
        target_token=request.target_token,
        rect_source=request.rect_source,
    )


def _apply_surface_preparation(
    surface_preparation: BackendPresentationSurfacePreparation,
    prepare_surface: Callable[[BackendPresentationSurfacePreparation], bool] | None,
) -> bool:
    if prepare_surface is None:
        return False
    try:
        return bool(prepare_surface(surface_preparation))
    except Exception:
        return False


def _surface_preparation_failed_status(
    target_status: HelperTargetStatus | None,
    request: HelperPresentationRequest,
    *,
    surface_preparation: BackendPresentationSurfacePreparation,
    now_monotonic: float,
) -> HelperPresentationStatus:
    target_token = request.target_token
    target = target_status.target if target_status is not None else None
    if target is not None and not target_token:
        target_token = target.target_token
    return HelperPresentationStatus(
        state=HelperPresentationState.DEGRADED,
        action=request.action,
        helper_protocol=HELPER_PROTOCOL,
        target_token=target_token,
        rect_source=request.rect_source,
        requested_rect=request.content_rect,
        renderer=request.renderer,
        standalone_mode=request.standalone_mode,
        pyqt_renderer_preserved=request.renderer == "pyqt",
        degrade_reasons=tuple(
            dict.fromkeys(request.degrade_reasons + (GNOME_HELPER_REASON_SURFACE_PREPARATION_FAILED,))
        ),
        observed_at_monotonic=now_monotonic,
        presentation_diagnostics={
            "surface_preparation": {
                "mode": surface_preparation.mode,
                "rect": {
                    "x": surface_preparation.rect[0],
                    "y": surface_preparation.rect[1],
                    "width": surface_preparation.rect[2],
                    "height": surface_preparation.rect[3],
                },
                "reason": surface_preparation.reason,
                "failed": True,
            }
        },
        detail="surface preparation failed before helper presentation",
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


def _target_query_payload(env: Mapping[str, str]) -> str:
    if not _env_flag_enabled(env.get(GNOME_HELPER_GEOMETRY_DIAGNOSTICS_ENV, "")):
        return "{}"
    return json.dumps({"include_geometry_diagnostics": True}, separators=(",", ":"))


def _env_flag_enabled(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "debug"}


def _shell_raster_metrics_payload(
    request: HelperPresentationRequest | None,
    presentation_status: HelperPresentationStatus | None,
) -> dict[str, object] | None:
    request_metrics = None
    if request is not None and request.shell_raster_frame is not None:
        request_metrics = request.shell_raster_frame.diagnostics
    status_metrics = None
    if presentation_status is not None and presentation_status.shell_raster_frame is not None:
        shell_raster_frame = presentation_status.shell_raster_frame
        if isinstance(shell_raster_frame, Mapping):
            raw_metrics = shell_raster_frame.get("diagnostics")
            if isinstance(raw_metrics, Mapping):
                status_metrics = dict(raw_metrics)
    if request_metrics is None and status_metrics is None:
        return None
    return {
        "request": dict(request_metrics) if request_metrics is not None else None,
        "status": status_metrics,
    }


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
    return _cached_presentation_is_matching_success(
        state,
        request=state.last_request,
    )


def _should_skip_presentation_apply(
    state: GnomeHelperPresentationRuntimeState,
    signature: GnomeHelperPresentationSignature | None,
    request: HelperPresentationRequest,
    *,
    now_monotonic: float,
) -> bool:
    if signature is None or state.last_signature != signature:
        return False
    if _shell_raster_frame_refresh_due(state, request, now_monotonic=now_monotonic):
        return False
    return _cached_presentation_is_matching_success(
        state,
        request=request,
    )


def _shell_raster_frame_refresh_due(
    state: GnomeHelperPresentationRuntimeState,
    request: HelperPresentationRequest,
    *,
    now_monotonic: float,
) -> bool:
    frame = request.shell_raster_frame
    if frame is None or frame.action != "update":
        return False
    if state.last_success_at <= 0:
        return False
    stale_timeout_seconds = max(0.0, float(frame.stale_timeout_ms) / 1000.0)
    if stale_timeout_seconds <= 0:
        return True
    refresh_after = max(
        GNOME_HELPER_SHELL_RASTER_MIN_REFRESH_SECONDS,
        stale_timeout_seconds * GNOME_HELPER_SHELL_RASTER_LEASE_REFRESH_FRACTION,
    )
    return (float(now_monotonic) - float(state.last_success_at)) >= refresh_after


def _should_skip_persistent_mismatch_apply(
    state: GnomeHelperPresentationRuntimeState,
    signature: GnomeHelperPresentationSignature | None,
) -> bool:
    if signature is None or state.persistent_mismatch_key is None:
        return False
    if state.persistent_mismatch_count < GNOME_HELPER_PERSISTENT_MISMATCH_THRESHOLD:
        return False
    return state.persistent_mismatch_key.signature == signature


def _cached_presentation_is_matching_success(
    state: GnomeHelperPresentationRuntimeState,
    *,
    request: HelperPresentationRequest,
) -> bool:
    if state.last_success_at <= 0:
        return False
    status = state.last_presentation_status
    if status is None:
        return False
    return _presentation_status_is_matching_success(status, request)


def _presentation_status_with_wrong_monitor_reason(
    status: HelperPresentationStatus,
    target_status: HelperTargetStatus | None,
) -> HelperPresentationStatus:
    if not _presentation_status_is_wrong_monitor_mismatch(status, target_status):
        return status
    return _presentation_status_with_reasons(status, GNOME_HELPER_REASON_WRONG_MONITOR_APPLIED_RECT)


def _presentation_status_is_wrong_monitor_mismatch(
    status: HelperPresentationStatus,
    target_status: HelperTargetStatus | None,
) -> bool:
    if status.rect_match:
        return False
    if GNOME_HELPER_REASON_APPLIED_RECT_MISMATCH not in status.degrade_reasons:
        return False
    if status.applied_rect is None or not status.applied_rect.valid:
        return False
    target = target_status.target if target_status is not None else None
    if target is None or target.monitor_rect is None or not target.monitor_rect.valid:
        return False
    return not _rects_overlap(status.applied_rect, target.monitor_rect)


def _update_persistent_mismatch_cache(
    state: GnomeHelperPresentationRuntimeState,
    *,
    signature: GnomeHelperPresentationSignature | None,
    request: HelperPresentationRequest | None,
    presentation_status: HelperPresentationStatus | None,
) -> HelperPresentationStatus | None:
    key = _persistent_mismatch_key(
        signature,
        request=request,
        presentation_status=presentation_status,
    )
    if key is None:
        _clear_persistent_mismatch_cache(state)
        return presentation_status

    if state.persistent_mismatch_key == key:
        state.persistent_mismatch_count += 1
    else:
        state.persistent_mismatch_key = key
        state.persistent_mismatch_count = 1

    status = presentation_status
    if _presentation_status_is_wrong_monitor_persistent_candidate(presentation_status):
        status = _presentation_status_with_reasons(
            status,
            GNOME_HELPER_REASON_WRONG_MONITOR_APPLIED_RECT,
        )
    if state.persistent_mismatch_count >= GNOME_HELPER_PERSISTENT_MISMATCH_THRESHOLD:
        status = _presentation_status_with_reasons(
            status,
            GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH,
        )
    state.persistent_mismatch_status = status
    return status


def _persistent_mismatch_key(
    signature: GnomeHelperPresentationSignature | None,
    *,
    request: HelperPresentationRequest | None,
    presentation_status: HelperPresentationStatus | None,
) -> GnomeHelperPersistentMismatchKey | None:
    if signature is None or request is None or presentation_status is None:
        return None
    if not _presentation_status_is_persistent_mismatch_candidate(signature, presentation_status):
        return None
    requested_rect = _rect_signature(presentation_status.requested_rect or request.content_rect)
    applied_rect = _rect_signature(presentation_status.applied_rect)
    if requested_rect is None or applied_rect is None:
        return None
    target_token = presentation_status.target_token or request.target_token
    if not target_token:
        return None
    return GnomeHelperPersistentMismatchKey(
        signature=signature,
        target_token=target_token,
        requested_rect=requested_rect,
        applied_rect=applied_rect,
    )


def _presentation_status_is_persistent_mismatch_candidate(
    signature: GnomeHelperPresentationSignature,
    status: HelperPresentationStatus,
) -> bool:
    if status.rect_match:
        return False
    if GNOME_HELPER_REASON_APPLIED_RECT_MISMATCH not in status.degrade_reasons:
        return False
    return _presentation_status_is_wrong_monitor_persistent_candidate(status) or bool(
        signature.surface_preparation_mode
    )


def _presentation_status_is_wrong_monitor_persistent_candidate(status: HelperPresentationStatus) -> bool:
    return GNOME_HELPER_REASON_WRONG_MONITOR_APPLIED_RECT in status.degrade_reasons


def _presentation_status_with_reasons(
    status: HelperPresentationStatus,
    *reasons: str,
) -> HelperPresentationStatus:
    merged_reasons = tuple(dict.fromkeys(status.degrade_reasons + tuple(reason for reason in reasons if reason)))
    if merged_reasons == status.degrade_reasons:
        return status
    return replace(status, degrade_reasons=merged_reasons)


def _clear_persistent_mismatch_cache(state: GnomeHelperPresentationRuntimeState) -> None:
    state.persistent_mismatch_key = None
    state.persistent_mismatch_count = 0
    state.persistent_mismatch_status = None


def _update_presentation_cache(
    state: GnomeHelperPresentationRuntimeState,
    *,
    target_status: HelperTargetStatus | None,
    request: HelperPresentationRequest | None,
    presentation_status: HelperPresentationStatus | None,
    previous_surface_action: str,
    now_monotonic: float,
    surface_preparation: BackendPresentationSurfacePreparation | None,
) -> None:
    state.last_target_status = target_status
    state.last_request = request
    state.last_presentation_status = presentation_status
    signature = (
        _presentation_signature(
            target_status,
            request,
            previous_surface_action=previous_surface_action,
            surface_preparation=surface_preparation,
        )
        if target_status is not None and request is not None
        else None
    )
    if request is not None and presentation_status is not None and _presentation_status_is_matching_success(
        presentation_status,
        request,
    ):
        state.last_signature = signature
        state.last_success_at = now_monotonic
        _clear_persistent_mismatch_cache(state)
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
    _clear_persistent_mismatch_cache(state)


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
    surface_preparation: BackendPresentationSurfacePreparation | None,
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
        include_presentation_diagnostics=bool(request.include_presentation_diagnostics),
        surface_preparation_mode=surface_preparation.mode if surface_preparation is not None else "",
        request_degrade_reasons=tuple(request.degrade_reasons),
        shell_raster_frame_signature=(
            request.shell_raster_frame.signature() if request.shell_raster_frame is not None else None
        ),
    )


def _rect_signature(rect: HelperRect | None) -> tuple[int, int, int, int] | None:
    if rect is None or not rect.valid:
        return None
    return (rect.x, rect.y, rect.width, rect.height)


def _rects_overlap(left: HelperRect, right: HelperRect) -> bool:
    return (
        max(left.x, right.x) < min(left.x + left.width, right.x + right.width)
        and max(left.y, right.y) < min(left.y + left.height, right.y + right.height)
    )


def _helper_rects_match(left: HelperRect, right: HelperRect, *, tolerance: int) -> bool:
    return (
        abs(left.x - right.x) <= tolerance
        and abs(left.y - right.y) <= tolerance
        and abs(left.width - right.width) <= tolerance
        and abs(left.height - right.height) <= tolerance
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
