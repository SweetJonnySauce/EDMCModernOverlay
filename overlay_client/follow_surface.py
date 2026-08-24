"""Follow/window orchestration and platform hooks mixin for the overlay window."""

from __future__ import annotations

import json
import logging
import math
import os
import sys
import time
from typing import TYPE_CHECKING, Callable, Mapping, Optional, Tuple, cast

from PyQt6.QtCore import Qt, QPoint, QRect, QSize, QTimer
from PyQt6.QtGui import QGuiApplication, QWindow, QScreen
from PyQt6.QtWidgets import QApplication

from overlay_client.backend.consumers import BackendPresentationCycleResult, run_backend_presentation_cycle
from overlay_client.backend.presentation_policy import (
    BACKEND_PRESENTATION_SURFACE_HIDDEN,
    BackendPresentationVisibilityDecision,
    BackendPresentationVisibilityState,
    decide_backend_presentation_visibility,
)
from overlay_client.backend.surface_preparation import (
    BACKEND_PRESENTATION_SURFACE_PREPARATION_FULLSCREEN_MONITOR,
    BACKEND_PRESENTATION_SURFACE_PREPARATION_MANAGED_WINDOWED,
    BackendPresentationSurfacePreparation,
)
from overlay_client.follow_geometry import (
    ScreenInfo,
    _apply_aspect_guard,
    _apply_title_bar_offset,
    _convert_native_rect_to_qt,
)
from overlay_client.window_tracking import WindowState
from overlay_client.work_counters import WORK_COUNTER_MAX, increment_bounded_counter

if TYPE_CHECKING:
    from overlay_client.overlay_state import OverlayWindowState


_BACKEND_PERFORMANCE_DIAGNOSTICS_ENV = "EDMC_OVERLAY_GNOME_PRESENTATION_DIAGNOSTICS"
_BACKEND_PERFORMANCE_EVENT_PREFIX = "BACKEND_PERFORMANCE_SAMPLE "
_BACKEND_PERFORMANCE_PAINT_COUNT_MAX = 1_000_000


def _performance_number(value: object) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(numeric) or numeric < 0:
        return 0.0
    return round(numeric, 6)


def _performance_count(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if not isinstance(value, (int, float, str)):
        return 0
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, numeric)


def _performance_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _build_backend_performance_sample(
    result: BackendPresentationCycleResult,
    *,
    elapsed_ms: float,
    qt_widget_visible: bool = False,
    qt_window_exposed: bool = False,
    qt_paint_count: object = 0,
    target_has_focus: bool = False,
    prepared_surface_requires_mapping: bool = False,
    qt_geometry_match: bool = False,
) -> dict[str, object]:
    """Build one allowlisted dev-only presentation sample without private target data."""

    diagnostics = _performance_mapping(result.diagnostics)
    raster_metrics = _performance_mapping(diagnostics.get("shell_raster_metrics"))
    raster_request = _performance_mapping(raster_metrics.get("request"))
    raster_status = _performance_mapping(raster_metrics.get("status"))
    helper_metrics = _performance_mapping(raster_status.get("helper"))
    helper_call_skipped = bool(
        raster_request.get("helper_call_skipped", raster_status.get("helper_call_skipped", False))
    )
    frame_preparation_skipped = bool(raster_request.get("frame_preparation_skipped", False))
    cache_hit = bool(raster_request.get("cache_hit", False))
    has_raster_request = bool(raster_request)
    return {
        "schema_version": 1,
        "event": "backend_presentation_cycle",
        "presentation_cycle_ms": _performance_number(elapsed_ms),
        "helper_health_calls": 1 if diagnostics.get("health_cache_hit") is False else 0,
        "helper_target_calls": 1 if diagnostics.get("target_poll_skipped") is False else 0,
        "helper_presentation_calls": (
            0 if diagnostics.get("presentation_skipped") is True else _performance_count(diagnostics.get("attempts", 0))
        ),
        "transition_state": str(diagnostics.get("transition_state", "")),
        "transition_elapsed_ms": _performance_number(
            _performance_number(diagnostics.get("transition_elapsed_seconds", 0.0)) * 1000.0
        ),
        "raster_builds": 1 if has_raster_request and not cache_hit and not helper_call_skipped else 0,
        "raster_reuses": 1 if has_raster_request and cache_hit else 0,
        "raster_skips": 1 if has_raster_request and helper_call_skipped else 0,
        "raster_bytes": _performance_count(raster_request.get("byte_size", 0)),
        "raster_regions": _performance_count(raster_request.get("region_count", 0)),
        "raster_encode_ms": _performance_number(raster_request.get("encode_ms", 0.0)),
        "raster_build_ms": _performance_number(raster_request.get("build_ms", 0.0)),
        "helper_decode_ms": _performance_number(helper_metrics.get("helper_decode_ms", 0.0)),
        "helper_apply_ms": _performance_number(helper_metrics.get("helper_apply_ms", 0.0)),
        "frame_builds": 1 if has_raster_request and not helper_call_skipped and not frame_preparation_skipped else 0,
        "qt_widget_visible": bool(qt_widget_visible),
        "qt_window_exposed": bool(qt_window_exposed),
        "qt_paint_count": min(_performance_count(qt_paint_count), _BACKEND_PERFORMANCE_PAINT_COUNT_MAX),
        "target_has_focus": bool(target_has_focus),
        "prepared_surface_requires_mapping": bool(prepared_surface_requires_mapping),
        "qt_geometry_match": bool(qt_geometry_match),
    }


def _backend_performance_diagnostics_enabled() -> bool:
    return os.getenv(_BACKEND_PERFORMANCE_DIAGNOSTICS_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _record_backend_work_counts(target: object, result: BackendPresentationCycleResult) -> None:
    """Accumulate fixed work counts without logging per-cycle details."""

    counts = getattr(target, "_backend_work_counts", None)
    if not isinstance(counts, dict):
        return
    increment_bounded_counter(counts, "cycles", limit=WORK_COUNTER_MAX)
    diagnostics = _performance_mapping(result.diagnostics)
    if diagnostics.get("health_cache_hit") is False:
        increment_bounded_counter(counts, "helper_health_calls", limit=WORK_COUNTER_MAX)
    if diagnostics.get("target_poll_skipped") is False:
        increment_bounded_counter(counts, "helper_target_calls", limit=WORK_COUNTER_MAX)
    if diagnostics.get("presentation_skipped") is True:
        return
    attempts = min(_performance_count(diagnostics.get("attempts", 0)), WORK_COUNTER_MAX)
    current = max(0, int(counts.get("helper_presentation_calls", 0)))
    counts["helper_presentation_calls"] = min(WORK_COUNTER_MAX, current + attempts)


def _log_backend_performance_sample(
    result: BackendPresentationCycleResult,
    *,
    elapsed_ms: float,
    qt_widget_visible: bool,
    qt_window_exposed: bool,
    qt_paint_count: int,
    target_has_focus: bool,
    prepared_surface_requires_mapping: bool,
    qt_geometry_match: bool,
) -> None:
    if not _backend_performance_diagnostics_enabled():
        return
    sample = _build_backend_performance_sample(
        result,
        elapsed_ms=elapsed_ms,
        qt_widget_visible=qt_widget_visible,
        qt_window_exposed=qt_window_exposed,
        qt_paint_count=qt_paint_count,
        target_has_focus=target_has_focus,
        prepared_surface_requires_mapping=prepared_surface_requires_mapping,
        qt_geometry_match=qt_geometry_match,
    )
    _CLIENT_LOGGER.debug(
        "%s%s",
        _BACKEND_PERFORMANCE_EVENT_PREFIX,
        json.dumps(sample, sort_keys=True, separators=(",", ":")),
    )


_CLIENT_LOGGER = logging.getLogger("EDMC.ModernOverlay.Client")

# Keep defaults local to avoid import cycles while matching overlay_client values.
DEFAULT_WINDOW_BASE_WIDTH = 1280
DEFAULT_WINDOW_BASE_HEIGHT = 960


class FollowSurfaceMixin:
    """Follow/window orchestration, platform hooks, and visibility helpers."""

    _last_backend_presentation: BackendPresentationCycleResult | None
    _last_backend_presentation_log: tuple[object, ...] | None
    _last_backend_surface_preparation_key: tuple[object, ...]
    _last_device_ratio_log: tuple[str, float, float, float] | None
    _last_follow_state: WindowState | None
    _last_normalised_tracker: tuple[tuple[int, int, int, int], tuple[int, int, int, int], str, float, float] | None
    _last_raw_window_log: tuple[int, int, int, int] | None
    _last_screen_name: str | None
    _last_set_geometry: tuple[int, int, int, int] | None
    _transient_parent_id: str | None

    def _apply_drag_state(self) -> None:
        overlay_state = cast("OverlayWindowState", self)
        window = self.windowHandle()
        _CLIENT_LOGGER.debug(
            "Applying drag state: drag_enabled=%s transparent=%s move_mode=%s window=%s flags=%s",
            self._drag_enabled,
            not self._drag_enabled,
            overlay_state._move_mode,
            bool(window),
            hex(int(window.flags())) if window is not None else "none",
        )
        self._interaction_controller.set_click_through(not self._drag_enabled, force=True, reason="apply_drag_state")
        if not self._drag_enabled:
            self._move_mode = False
            self._drag_active = False
            self._follow_controller.set_drag_state(self._drag_active, self._move_mode)
            if overlay_state._cursor_saved:
                self.setCursor(overlay_state._saved_cursor)
                overlay_state._cursor_saved = False
        self.raise_()

    def _poll_modifiers(self) -> None:
        overlay_state = cast("OverlayWindowState", self)
        if not self._drag_enabled or self._drag_active:
            return
        modifiers = QApplication.queryKeyboardModifiers()
        alt_down = bool(modifiers & Qt.KeyboardModifier.AltModifier)
        if alt_down and not self._move_mode:
            self._move_mode = True
            self._suspend_follow(0.75)
            if not overlay_state._cursor_saved:
                overlay_state._saved_cursor = self.cursor()
                overlay_state._cursor_saved = True
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif not alt_down and self._move_mode:
            self._move_mode = False
            if overlay_state._cursor_saved:
                self.setCursor(overlay_state._saved_cursor)
                overlay_state._cursor_saved = False

    def _set_click_through(self, transparent: bool) -> None:
        self._interaction_controller.set_click_through(transparent, force=True, reason="external_set_click_through")

    def _restore_drag_interactivity(self) -> None:
        self._interaction_controller.restore_drag_interactivity(
            self._drag_enabled, self._drag_active, self.format_scale_debug
        )

    def _set_children_click_through(self, transparent: bool) -> None:
        for child_name in ("message_label",):
            child = getattr(self, child_name, None)
            if child is not None:
                try:
                    child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, transparent)
                except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                    _CLIENT_LOGGER.debug("Failed to set click-through on child %s: %s", child_name, exc)
                except Exception as exc:  # pragma: no cover - unexpected Qt errors
                    _CLIENT_LOGGER.warning("Unexpected error setting click-through on child %s: %s", child_name, exc)

    def _clear_transient_parent_ids(self) -> None:
        self._transient_parent_window = None
        self._transient_parent_id = None

    # Follow mode ----------------------------------------------------------

    def _start_tracking(self) -> None:
        if not self._window_tracker or not self._follow_enabled:
            return
        self._follow_controller.set_follow_enabled(True)
        self._follow_controller.set_drag_state(self._drag_active, self._move_mode)
        self._follow_controller.start()

    def _stop_tracking(self) -> None:
        self._follow_controller.stop()

    def _set_wm_override(
        self,
        rect: Tuple[int, int, int, int],
        tracker_tuple: Optional[Tuple[int, int, int, int]],
        reason: str,
        classification: str = "wm_intervention",
    ) -> None:
        self._follow_controller.record_override(rect, tracker_tuple, reason, classification)

    def _clear_wm_override(self, reason: str) -> None:
        self._follow_controller.clear_override(reason)

    def _suspend_follow(self, delay: float = 0.75) -> None:
        self._follow_controller.suspend(delay)

    def _refresh_follow_geometry(self) -> None:
        if self._refresh_backend_presentation():
            return
        state = self._follow_controller.refresh()
        if state is None:
            if self._follow_controller.last_poll_attempted and self._follow_controller.last_state_missing:
                self._handle_missing_follow_state()
            return
        self._last_tracker_state = self._follow_controller.last_tracker_state
        self._apply_follow_state(state)

    def _refresh_backend_presentation(self) -> bool:
        cycle_started_ns = time.perf_counter_ns()
        presentation_refresh_requested = bool(getattr(self, "_backend_presentation_refresh_requested", False))
        try:
            result = run_backend_presentation_cycle(
                getattr(self, "_client_backend_status", None),
                standalone_mode=False,
                keep_overlay_visible=bool(getattr(self, "_keep_overlay_visible", False)),
                previous_surface_action=str(getattr(self, "_last_backend_presentation_surface_action", "")),
                title_bar_compensation_enabled=bool(getattr(self, "_title_bar_enabled", False)),
                title_bar_compensation_height=int(getattr(self, "_title_bar_height", 0) or 0),
                presentation_refresh_requested=presentation_refresh_requested,
                prepare_surface=self._prepare_backend_presentation_surface,
                raster_frame_provider=getattr(self, "_build_backend_shell_raster_content_frame", None),
            )
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            _CLIENT_LOGGER.warning("Backend presentation cycle failed: %s", exc)
            return True
        if result is None:
            return False
        _record_backend_work_counts(self, result)
        if presentation_refresh_requested:
            self._backend_presentation_refresh_requested = False
        if _backend_performance_diagnostics_enabled():
            (
                qt_widget_visible,
                qt_window_exposed,
                qt_paint_count,
                target_has_focus,
                prepared_surface_requires_mapping,
                qt_geometry_match,
            ) = self._backend_qt_presentation_diagnostics(result)
            _log_backend_performance_sample(
                result,
                elapsed_ms=(time.perf_counter_ns() - cycle_started_ns) / 1_000_000.0,
                qt_widget_visible=qt_widget_visible,
                qt_window_exposed=qt_window_exposed,
                qt_paint_count=qt_paint_count,
                target_has_focus=target_has_focus,
                prepared_surface_requires_mapping=prepared_surface_requires_mapping,
                qt_geometry_match=qt_geometry_match,
            )
        self._last_backend_presentation = result
        if result.reset_surface_state:
            self._reset_backend_presentation_surface_state()
        currently_visible = self._backend_presentation_surface_is_mapped(result)
        decision = decide_backend_presentation_visibility(
            result.visibility_snapshot,
            keep_overlay_visible=bool(getattr(self, "_keep_overlay_visible", False)),
            previous=getattr(self, "_backend_presentation_visibility_state", None),
            now_monotonic=time.monotonic(),
            currently_visible=currently_visible,
        )
        self._backend_presentation_visibility_state = decision.state
        self._last_backend_presentation_surface_action = decision.surface_action
        self._log_backend_presentation_result(result, decision)
        self._update_backend_presentation_visibility(decision, result)
        if decision.show and result.scale_size is not None:
            self._update_auto_legacy_scale(*result.scale_size)
        return True

    def _reset_backend_presentation_surface_state(self) -> None:
        """Hide and invalidate generic managed-surface state after backend takeover."""

        self._set_backend_presentation_content_suppressed(False, reason="backend_surface_reset")
        if self.isVisible():
            self.hide()
        self._backend_managed_surface_prepared = False
        self._backend_managed_surface_mapping_generation = 0
        self._backend_managed_surface_remapped_generation = -1
        self._backend_managed_surface_remap_pending_generation = -1
        self._backend_presentation_refresh_requested = False
        self._last_backend_surface_preparation_key = ()
        self._backend_presentation_visibility_state = BackendPresentationVisibilityState()
        self._last_backend_presentation_surface_action = BACKEND_PRESENTATION_SURFACE_HIDDEN

    def _prepare_backend_presentation_surface(self, preparation: BackendPresentationSurfacePreparation) -> bool:
        mode = preparation.mode
        rect = preparation.rect
        try:
            x, y, width, height = (int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
        except (TypeError, ValueError, IndexError):
            return False
        if width <= 0 or height <= 0:
            return False
        if mode == BACKEND_PRESENTATION_SURFACE_PREPARATION_FULLSCREEN_MONITOR:
            return self._prepare_backend_fullscreen_surface(preparation, (x, y, width, height))
        if mode == BACKEND_PRESENTATION_SURFACE_PREPARATION_MANAGED_WINDOWED:
            return self._prepare_backend_managed_windowed_surface(preparation, (x, y, width, height))
        return False

    def _prepare_backend_fullscreen_surface(
        self,
        preparation: object,
        target: tuple[int, int, int, int],
    ) -> bool:
        x, y, width, height = target
        screen = self._screen_for_backend_presentation_rect((x, y, width, height))
        if screen is None:
            _CLIENT_LOGGER.debug(
                "Backend fullscreen surface preparation failed: no Qt screen for rect=%s reason=%s",
                (x, y, width, height),
                getattr(preparation, "reason", ""),
            )
            return False
        show_fullscreen = getattr(self, "showFullScreen", None)
        if not callable(show_fullscreen):
            return False
        try:
            self._interaction_controller.prepare_window_flags_for_click_through(
                True,
                reason="backend_presentation_fullscreen_prepare",
            )
            window = self.windowHandle()
            current_screen = window.screen() if window is not None and hasattr(window, "screen") else None
            if window is not None and hasattr(window, "setScreen") and current_screen is not screen:
                window.setScreen(screen)
            self._last_set_geometry = target
            self.setGeometry(QRect(*target))
            show_fullscreen()
            window = self.windowHandle()
            if window is not None:
                self._platform_controller.prepare_window(window)
            self._platform_controller.apply_click_through(True)
            self._backend_managed_surface_prepared = False
            self._backend_managed_surface_mapping_generation = 0
            self._backend_managed_surface_remapped_generation = -1
            self._backend_managed_surface_remap_pending_generation = -1
            self._backend_presentation_refresh_requested = False
            self._last_backend_surface_preparation_key = ()
            _CLIENT_LOGGER.debug(
                "Prepared backend fullscreen surface rect=%s screen=%s reason=%s; %s",
                target,
                self._describe_screen(screen),
                getattr(preparation, "reason", ""),
                self.format_scale_debug(),
            )
            return True
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            _CLIENT_LOGGER.debug("Backend fullscreen surface preparation failed: %s", exc)
            return False

    def _prepare_backend_managed_windowed_surface(
        self,
        preparation: object,
        target: tuple[int, int, int, int],
    ) -> bool:
        x, y, width, height = target
        screen = self._screen_for_backend_presentation_rect((x, y, width, height))
        if screen is None:
            _CLIENT_LOGGER.debug(
                "Backend windowed surface preparation failed: no Qt screen for rect=%s reason=%s",
                (x, y, width, height),
                getattr(preparation, "reason", ""),
            )
            return False
        try:
            window = self.windowHandle()
            current_screen = window.screen() if window is not None and hasattr(window, "screen") else None
            screen_changed = current_screen is not screen
            force_recovery = bool(getattr(preparation, "force_recovery", False))
            preparation_key = self._backend_surface_preparation_key(preparation)
            unchanged = (
                not force_recovery
                and bool(getattr(self, "_backend_managed_surface_prepared", False))
                and getattr(self, "_last_backend_surface_preparation_key", None) == preparation_key
                and not screen_changed
                and getattr(self, "_last_set_geometry", None) == target
            )
            if unchanged:
                _CLIENT_LOGGER.debug(
                    "Reused backend managed-windowed surface rect=%s screen=%s reason=unchanged_preparation; %s",
                    target,
                    self._describe_screen(screen),
                    self.format_scale_debug(),
                )
                return True

            identity_refresh_required = (
                force_recovery or screen_changed or not bool(getattr(self, "_backend_managed_surface_prepared", False))
            )
            if identity_refresh_required:
                self._backend_managed_surface_mapping_generation = (
                    int(getattr(self, "_backend_managed_surface_mapping_generation", 0)) + 1
                )
                self._backend_managed_surface_remapped_generation = -1
                self._backend_managed_surface_remap_pending_generation = -1
                self._interaction_controller.prepare_window_flags_for_click_through(
                    True,
                    reason="backend_presentation_windowed_prepare",
                )
                if screen_changed and window is not None and hasattr(window, "setScreen"):
                    window.setScreen(screen)
                if not self._reset_backend_managed_windowed_state():
                    return False

            if force_recovery or getattr(self, "_last_set_geometry", None) != target:
                self._last_set_geometry = target
                self.setGeometry(QRect(*target))

            window = self.windowHandle()
            if identity_refresh_required and window is not None:
                self._platform_controller.prepare_window(window)
                self._platform_controller.apply_click_through(True)
            self._backend_managed_surface_prepared = True
            self._last_backend_surface_preparation_key = preparation_key
            _CLIENT_LOGGER.debug(
                "Prepared backend managed-windowed surface rect=%s screen=%s reason=%s identity_refresh=%s force_recovery=%s; %s",
                target,
                self._describe_screen(screen),
                getattr(preparation, "reason", ""),
                identity_refresh_required,
                force_recovery,
                self.format_scale_debug(),
            )
            return True
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            _CLIENT_LOGGER.debug("Backend managed-windowed surface preparation failed: %s", exc)
            return False

    @staticmethod
    def _backend_surface_preparation_key(preparation: object) -> tuple[object, ...]:
        return (
            str(getattr(preparation, "mode", "") or ""),
            tuple(getattr(preparation, "rect", ()) or ()),
            str(getattr(preparation, "target_token", "") or ""),
            str(getattr(preparation, "rect_source", "") or ""),
            getattr(preparation, "target_monitor", None),
            str(getattr(preparation, "target_output_name", "") or ""),
            getattr(preparation, "target_monitor_rect", None),
        )

    def _reset_backend_managed_windowed_state(self) -> bool:
        window_state = getattr(self, "windowState", None)
        set_window_state = getattr(self, "setWindowState", None)
        fullscreen_state = getattr(getattr(Qt, "WindowState", object), "WindowFullScreen", None)
        if callable(window_state) and callable(set_window_state) and fullscreen_state is not None:
            current_state = window_state()
            try:
                next_state = current_state & ~fullscreen_state
            except TypeError:
                try:
                    fullscreen_value = getattr(fullscreen_state, "value", fullscreen_state)
                    current_value = getattr(current_state, "value", current_state)
                    next_state = int(current_value) & ~int(fullscreen_value)
                except (TypeError, ValueError):
                    return False
            if next_state == current_state:
                return True
            set_window_state(next_state)
            return True
        show_normal = getattr(self, "showNormal", None)
        if callable(show_normal) and self.isVisible():
            show_normal()
            return True
        return False

    def _backend_window_exposure_state(self) -> bool | None:
        try:
            window = self.windowHandle()
            is_exposed = getattr(window, "isExposed", None) if window is not None else None
            if not callable(is_exposed):
                return None
            return bool(is_exposed())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return None

    def _backend_qt_presentation_diagnostics(
        self,
        result: BackendPresentationCycleResult,
    ) -> tuple[bool, bool, int, bool, bool, bool]:
        widget_visible = bool(self.isVisible())
        window_exposed = self._backend_window_exposure_state()
        paint_stats = getattr(self, "_paint_stats", None)
        paint_count = paint_stats.get("paint_count", 0) if isinstance(paint_stats, Mapping) else 0
        snapshot = result.visibility_snapshot
        return (
            widget_visible,
            bool(window_exposed),
            min(_performance_count(paint_count), _BACKEND_PERFORMANCE_PAINT_COUNT_MAX),
            bool(snapshot.target_has_focus),
            bool(snapshot.prepared_surface_requires_mapping),
            self._backend_qt_geometry_matches(result.prime_rect),
        )

    def _backend_qt_geometry_matches(self, target: tuple[int, int, int, int] | None) -> bool:
        if target is None:
            return False
        try:
            geometry = self.frameGeometry()
            actual = (geometry.x(), geometry.y(), geometry.width(), geometry.height())
            expected = tuple(int(value) for value in target)
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return False
        return all(abs(actual_value - expected_value) <= 2 for actual_value, expected_value in zip(actual, expected))

    def _backend_managed_surface_requires_remap(self, result: BackendPresentationCycleResult) -> bool:
        if not result.visibility_snapshot.prepared_surface_requires_mapping or not self.isVisible():
            return False
        if self._backend_window_exposure_state() is not False:
            return False
        generation = int(getattr(self, "_backend_managed_surface_mapping_generation", 0))
        pending_generation = int(getattr(self, "_backend_managed_surface_remap_pending_generation", -1))
        if pending_generation == generation:
            return False
        attempted_generation = int(getattr(self, "_backend_managed_surface_remapped_generation", -1))
        return attempted_generation != generation

    def _backend_presentation_surface_is_mapped(self, result: BackendPresentationCycleResult) -> bool:
        generation = int(getattr(self, "_backend_managed_surface_mapping_generation", 0))
        pending_generation = int(getattr(self, "_backend_managed_surface_remap_pending_generation", -1))
        if pending_generation == generation:
            return True
        widget_visible = bool(self.isVisible())
        if not widget_visible or not result.visibility_snapshot.prepared_surface_requires_mapping:
            return widget_visible
        if self._backend_window_exposure_state() is not False:
            return True
        return not self._backend_managed_surface_requires_remap(result)

    def _schedule_backend_managed_surface_remap(self, callback: Callable[[], None]) -> None:
        QTimer.singleShot(0, callback)

    def _complete_backend_managed_surface_remap(self, generation: int) -> None:
        pending_generation = int(getattr(self, "_backend_managed_surface_remap_pending_generation", -1))
        if pending_generation != generation:
            return
        self._backend_managed_surface_remap_pending_generation = -1
        try:
            self.show()
            window = self.windowHandle()
            if window is not None:
                self._platform_controller.prepare_window(window)
            self._platform_controller.apply_click_through(True)
            self._backend_presentation_refresh_requested = True
            _CLIENT_LOGGER.debug(
                "Remapped backend managed-windowed Qt surface after deferred unexposed recovery; %s",
                self.format_scale_debug(),
            )
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            _CLIENT_LOGGER.debug("Deferred backend managed-windowed remap failed: %s", exc, exc_info=exc)

    def _screen_for_backend_presentation_rect(self, rect: tuple[int, int, int, int]) -> QScreen | None:
        x, y, width, height = rect
        center = QPoint(x + max(0, width // 2), y + max(0, height // 2))
        try:
            screen = QGuiApplication.screenAt(center)
        except (AttributeError, RuntimeError, TypeError, ValueError):
            screen = None
        if screen is not None:
            return screen
        target_rect = QRect(x, y, width, height)
        try:
            screens = list(QGuiApplication.screens() or ())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            screens = []
        for candidate in screens:
            try:
                if candidate.geometry().intersects(target_rect):
                    return candidate
            except (AttributeError, RuntimeError, TypeError, ValueError):
                continue
        if len(screens) == 1:
            return screens[0]
        return None

    def _update_backend_presentation_visibility(
        self,
        decision: BackendPresentationVisibilityDecision,
        result: BackendPresentationCycleResult,
    ) -> None:
        def _apply_helper_click_through() -> None:
            generation = int(getattr(self, "_backend_managed_surface_mapping_generation", 0))
            pending_generation = int(getattr(self, "_backend_managed_surface_remap_pending_generation", -1))
            if pending_generation == generation:
                return
            self._platform_controller.apply_click_through(True)

        def _hide_backend_surface() -> None:
            self._set_backend_presentation_content_suppressed(False, reason=decision.reason)
            self.hide()

        def _show_with_backend_prime() -> None:
            controlled_remap = self._backend_managed_surface_requires_remap(result)
            self._set_backend_presentation_content_suppressed(decision.content_suppressed, reason=decision.reason)
            self._interaction_controller.prepare_window_flags_for_click_through(
                True,
                reason="backend_presentation_pre_show",
            )
            if controlled_remap:
                self.hide()
            self._prime_backend_presentation_map_geometry(result)
            if controlled_remap:
                generation = int(getattr(self, "_backend_managed_surface_mapping_generation", 0))
                self._backend_managed_surface_remapped_generation = generation
                self._backend_managed_surface_remap_pending_generation = generation
                self._schedule_backend_managed_surface_remap(
                    lambda: self._complete_backend_managed_surface_remap(generation)
                )
                _CLIENT_LOGGER.debug(
                    "Scheduled deferred backend managed-windowed remap after unexposed state; %s",
                    self.format_scale_debug(),
                )
                return
            self.show()

        new_state = self._visibility_helper.update_visibility(
            decision.show,
            is_visible_fn=(lambda: self._backend_presentation_surface_is_mapped(result))
            if decision.show
            else (lambda: self.isVisible()),
            show_fn=_show_with_backend_prime,
            hide_fn=_hide_backend_surface,
            raise_fn=lambda: None,
            apply_drag_state_fn=_apply_helper_click_through,
            format_scale_debug_fn=self.format_scale_debug,
        )
        if decision.show:
            self._set_backend_presentation_content_suppressed(decision.content_suppressed, reason=decision.reason)
        self._last_visibility_state = new_state

    def _set_backend_presentation_content_suppressed(self, suppressed: bool, *, reason: str) -> None:
        next_value = bool(suppressed)
        current_value = bool(getattr(self, "_backend_presentation_content_suppressed", False))
        if current_value == next_value:
            return
        self._backend_presentation_content_suppressed = next_value
        child = getattr(self, "message_label", None)
        if child is not None:
            try:
                child.setVisible(not next_value)
            except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                _CLIENT_LOGGER.debug("Failed to update backend presentation message visibility: %s", exc)
        update_fn = getattr(self, "update", None)
        if callable(update_fn):
            try:
                update_fn()
            except (RuntimeError, TypeError, ValueError) as exc:
                _CLIENT_LOGGER.debug("Failed to repaint backend presentation suppression state: %s", exc)
        _CLIENT_LOGGER.debug(
            "Backend presentation content %s (reason=%s); %s",
            "suppressed" if next_value else "restored",
            reason or "unspecified",
            self.format_scale_debug(),
        )

    def _prime_backend_presentation_map_geometry(self, result: BackendPresentationCycleResult) -> None:
        rect = result.prime_rect
        if rect is None:
            return
        try:
            x, y, width, height = (int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
        except (TypeError, ValueError, IndexError):
            return
        if width <= 0 or height <= 0:
            return
        target = (x, y, width, height)
        self._last_set_geometry = target
        self.setGeometry(QRect(*target))
        _CLIENT_LOGGER.debug(
            "%s: primed Qt map geometry rect=%s source=%s; map hygiene only, not placement proof; %s",
            result.log_prefix,
            target,
            result.prime_rect_source,
            self.format_scale_debug(),
        )

    def _log_backend_presentation_result(
        self,
        result: BackendPresentationCycleResult,
        decision: BackendPresentationVisibilityDecision,
    ) -> None:
        payload = result.diagnostics
        signature = result.diagnostic_signature() + (
            decision.show,
            decision.reason,
            decision.state.focus_loss_samples,
            decision.state.remap_warmup_active,
            decision.state.remap_warmup_samples,
            decision.remap_warmup_status,
            decision.surface_action,
            decision.content_visible,
        )
        if signature == getattr(self, "_last_backend_presentation_log", None):
            return
        self._last_backend_presentation_log = signature
        _CLIENT_LOGGER.debug(
            "%s: health=%s target=%s token=%s seq=%s target_monitor=%s output=%s monitor_rect=%s frame_rect=%s rect_source=%s "
            "requested=%s applied=%s prime=%s prime_source=%s delta=%s rect_match=%s state=%s reasons=%s attempts=%s retries=%s "
            "presentation_skipped=%s skip_reason=%s target_poll_skipped=%s "
            "surface_preparation=%s surface_preparation_failed=%s surface_preparation_ready=%s "
            "surface_preparation_action=%s surface_preparation_reason=%s "
            "transition_state=%s transition_reason=%s transition_action=%s transition_elapsed=%.3fs "
            "transition_samples=%s transition_token=%s transition_monitor=%s surface_reset=%s "
            "visibility=%s visibility_reason=%s surface_action=%s content_visible=%s keep_overlay_visible=%s target_focus=%s target_workspace=%s "
            "target_minimized=%s focus_loss_samples=%s focus_loss_elapsed=%.3fs remap_warmup=%s "
            "remap_warmup_samples=%s remap_warmup_elapsed=%.3fs overlay_window_found=%s legacy_geometry=%s; %s",
            result.log_prefix,
            payload.get("helper_health", ""),
            payload.get("target_state", ""),
            payload.get("target_token", ""),
            payload.get("target_sequence", ""),
            payload.get("target_monitor"),
            payload.get("target_output_name"),
            payload.get("target_monitor_rect"),
            payload.get("target_frame_rect"),
            payload.get("rect_source", ""),
            payload.get("requested_rect"),
            payload.get("applied_rect"),
            payload.get("prime_rect"),
            payload.get("prime_rect_source"),
            payload.get("rect_delta"),
            payload.get("rect_match"),
            payload.get("presentation_state", ""),
            payload.get("presentation_reasons", ()),
            payload.get("attempts", 0),
            payload.get("retry_reasons", ()),
            payload.get("presentation_skipped"),
            payload.get("presentation_skip_reason"),
            payload.get("target_poll_skipped"),
            payload.get("surface_preparation"),
            payload.get("surface_preparation_failed"),
            payload.get("surface_preparation_ready"),
            payload.get("surface_preparation_action"),
            payload.get("surface_preparation_reason"),
            payload.get("transition_state", ""),
            payload.get("transition_reason", ""),
            payload.get("transition_action", ""),
            float(payload.get("transition_elapsed_seconds", 0.0) or 0.0),
            payload.get("transition_sample_count", 0),
            payload.get("transition_target_token", ""),
            payload.get("transition_target_monitor"),
            payload.get("managed_surface_reset_requested", False),
            "visible" if decision.show else "hidden",
            decision.reason,
            decision.surface_action,
            decision.content_visible,
            bool(getattr(self, "_keep_overlay_visible", False)),
            payload.get("target_has_focus"),
            payload.get("target_showing_on_workspace"),
            payload.get("target_minimized"),
            decision.state.focus_loss_samples,
            decision.focus_loss_elapsed_seconds,
            decision.remap_warmup_status,
            decision.state.remap_warmup_samples,
            decision.remap_warmup_elapsed_seconds,
            payload.get("overlay_window_found"),
            payload.get("legacy_geometry_policy", ""),
            self.format_scale_debug(),
        )
        geometry_diagnostics = payload.get("target_geometry_diagnostics")
        if geometry_diagnostics:
            _CLIENT_LOGGER.debug(
                "%s geometry diagnostics: %s",
                result.log_prefix,
                geometry_diagnostics,
            )
        shell_raster_metrics = payload.get("shell_raster_metrics")
        if shell_raster_metrics:
            _CLIENT_LOGGER.debug(
                "%s shell raster metrics: %s",
                result.log_prefix,
                shell_raster_metrics,
            )

    def _convert_native_rect_to_qt(
        self,
        rect: Tuple[int, int, int, int],
    ) -> Tuple[Tuple[int, int, int, int], Optional[Tuple[str, float, float, float]]]:
        screen_info = self._screen_info_for_native_rect(rect)
        clamp_enabled = bool(getattr(self, "_physical_clamp_enabled", False))
        overrides = getattr(self, "_physical_clamp_overrides", None) if clamp_enabled else None
        return _convert_native_rect_to_qt(
            rect,
            screen_info,
            physical_clamp_enabled=clamp_enabled,
            physical_clamp_overrides=overrides,
        )

    def _apply_title_bar_offset(
        self,
        geometry: Tuple[int, int, int, int],
        *,
        scale_y: float = 1.0,
    ) -> Tuple[Tuple[int, int, int, int], int]:
        overlay_state = cast("OverlayWindowState", self)
        adjusted, offset = _apply_title_bar_offset(
            geometry,
            title_bar_enabled=overlay_state._title_bar_enabled,
            title_bar_height=overlay_state._title_bar_height,
            scale_y=scale_y,
            previous_offset=overlay_state._last_title_bar_offset,
        )
        overlay_state._last_title_bar_offset = offset
        return adjusted, offset

    def _apply_aspect_guard(
        self,
        geometry: Tuple[int, int, int, int],
        *,
        original_geometry: Optional[Tuple[int, int, int, int]] = None,
        applied_title_offset: int = 0,
    ) -> Tuple[int, int, int, int]:
        overlay_state = cast("OverlayWindowState", self)
        adjusted, overlay_state._aspect_guard_skip_logged = _apply_aspect_guard(
            geometry,
            base_width=DEFAULT_WINDOW_BASE_WIDTH,
            base_height=DEFAULT_WINDOW_BASE_HEIGHT,
            original_geometry=original_geometry,
            applied_title_offset=applied_title_offset,
            aspect_guard_skip_logged=overlay_state._aspect_guard_skip_logged,
        )
        return adjusted

    def _apply_follow_state(self, state: WindowState) -> None:
        self._lost_window_logged = False

        tracker_qt_tuple, tracker_native_tuple, normalisation_info, desired_tuple = self._normalise_tracker_geometry(
            state
        )

        target_tuple = self._resolve_and_apply_geometry(tracker_qt_tuple, desired_tuple)
        self._post_process_follow_state(state, target_tuple)

    def _normalise_tracker_geometry(
        self,
        state: WindowState,
    ) -> Tuple[
        Tuple[int, int, int, int],
        Tuple[int, int, int, int],
        Optional[Tuple[str, float, float, float]],
        Tuple[int, int, int, int],
    ]:
        overlay_state = cast("OverlayWindowState", self)
        tracker_global_x = state.global_x if state.global_x is not None else state.x
        tracker_global_y = state.global_y if state.global_y is not None else state.y
        width = max(1, state.width)
        height = max(1, state.height)
        tracker_native_tuple = (
            tracker_global_x,
            tracker_global_y,
            width,
            height,
        )
        if tracker_native_tuple != overlay_state._last_raw_window_log:
            _CLIENT_LOGGER.debug(
                "Raw tracker window geometry: pos=(%d,%d) size=%dx%d",
                tracker_global_x,
                tracker_global_y,
                width,
                height,
            )
            overlay_state._last_raw_window_log = tracker_native_tuple

        tracker_qt_tuple, normalisation_info = self._convert_native_rect_to_qt(tracker_native_tuple)
        if normalisation_info is not None and tracker_qt_tuple != tracker_native_tuple:
            screen_name, norm_scale_x, norm_scale_y, device_ratio = normalisation_info
            snapshot = (tracker_native_tuple, tracker_qt_tuple, screen_name, norm_scale_x, norm_scale_y)
            if snapshot != overlay_state._last_normalised_tracker:
                _CLIENT_LOGGER.debug(
                    "Normalised tracker geometry using screen '%s': native=%s scale=%.3fx%.3f dpr=%.3f -> qt=%s",
                    screen_name,
                    tracker_native_tuple,
                    norm_scale_x,
                    norm_scale_y,
                    device_ratio,
                    tracker_qt_tuple,
                )
                overlay_state._last_normalised_tracker = snapshot
        else:
            overlay_state._last_normalised_tracker = None

        window_handle = self.windowHandle()
        if window_handle is not None:
            try:
                window_dpr = window_handle.devicePixelRatio()
            except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                _CLIENT_LOGGER.debug("Failed to read devicePixelRatio, defaulting to 0.0: %s", exc)
                window_dpr = 0.0
            except Exception as exc:  # pragma: no cover - unexpected Qt errors
                _CLIENT_LOGGER.warning("Unexpected devicePixelRatio failure, defaulting to 0.0: %s", exc)
                window_dpr = 0.0
            if window_dpr and normalisation_info is not None:
                screen_name, norm_scale_x, norm_scale_y, device_ratio = normalisation_info
                device_ratio_snapshot: tuple[str, float, float, float] = (
                    screen_name,
                    float(window_dpr),
                    norm_scale_x,
                    norm_scale_y,
                )
                if device_ratio_snapshot != overlay_state._last_device_ratio_log:
                    _CLIENT_LOGGER.debug(
                        "Device pixel ratio diagnostics: window_dpr=%.3f screen='%s' scale_x=%.3f scale_y=%.3f device_ratio=%.3f",
                        float(window_dpr),
                        screen_name,
                        norm_scale_x,
                        norm_scale_y,
                        device_ratio,
                    )
                    overlay_state._last_device_ratio_log = device_ratio_snapshot

        scale_y = normalisation_info[2] if normalisation_info is not None else 1.0
        desired_tuple, applied_title_offset = self._apply_title_bar_offset(tracker_qt_tuple, scale_y=scale_y)
        desired_tuple = self._apply_aspect_guard(
            desired_tuple,
            original_geometry=tracker_qt_tuple,
            applied_title_offset=applied_title_offset,
        )
        return tracker_qt_tuple, tracker_native_tuple, normalisation_info, desired_tuple

    def _resolve_and_apply_geometry(
        self,
        tracker_qt_tuple: Tuple[int, int, int, int],
        desired_tuple: Tuple[int, int, int, int],
    ) -> Tuple[int, int, int, int]:
        override_rect = self._follow_controller.wm_override
        override_tracker = self._follow_controller.wm_override_tracker
        override_expired = self._follow_controller.override_expired()

        def _current_geometry() -> Tuple[int, int, int, int]:
            current_rect = self.frameGeometry()
            return (
                current_rect.x(),
                current_rect.y(),
                current_rect.width(),
                current_rect.height(),
            )

        def _move_to_screen(target: Tuple[int, int, int, int]) -> None:
            self._move_to_screen(QRect(*target))

        def _set_geometry(target: Tuple[int, int, int, int]) -> None:
            self._last_set_geometry = target
            self.setGeometry(QRect(*target))
            self.raise_()

        def _classify_override(target: Tuple[int, int, int, int], actual: Tuple[int, int, int, int]) -> str:
            classification = self._classify_geometry_override(target, actual)
            if classification == "layout":
                try:
                    size_hint = self.sizeHint()
                except Exception:
                    size_hint = None
                try:
                    min_hint = self.minimumSizeHint()
                except Exception:
                    min_hint = None
                _CLIENT_LOGGER.debug(
                    "Adopting layout-constrained geometry from WM: tracker=%s actual=%s sizeHint=%s minimumSizeHint=%s",
                    tracker_qt_tuple,
                    actual,
                    size_hint,
                    min_hint,
                )
            else:
                _CLIENT_LOGGER.debug(
                    "Adopting WM authoritative geometry: tracker=%s actual=%s (classification=%s)",
                    tracker_qt_tuple,
                    actual,
                    classification,
                )
            return classification

        target_tuple = self._window_controller.resolve_and_apply_geometry(
            tracker_qt_tuple,
            desired_tuple,
            override_rect=override_rect,
            override_tracker=override_tracker,
            override_expired=override_expired,
            current_geometry_fn=_current_geometry,
            move_to_screen_fn=_move_to_screen,
            set_geometry_fn=_set_geometry,
            sync_base_dimensions_fn=self._sync_base_dimensions_to_widget,
            classify_override_fn=_classify_override,
            clear_override_fn=self._clear_wm_override,
            set_override_fn=self._set_wm_override,
            format_scale_debug_fn=self.format_scale_debug,
        )

        self._last_geometry_log = target_tuple
        return target_tuple

    def _post_process_follow_state(
        self,
        state: WindowState,
        target_tuple: Tuple[int, int, int, int],
    ) -> None:
        overlay_state = cast("OverlayWindowState", self)
        def _ensure_parent(identifier: str) -> None:
            self._ensure_transient_parent(state)

        def _fullscreen_hint() -> bool:
            if (
                not sys.platform.startswith("linux")
                or overlay_state._fullscreen_hint_logged
                or self._window_controller._fullscreen_hint_logged  # internal flag mirrors hint emission
                or not state.is_foreground
            ):
                return False
            screen = self.windowHandle().screen() if self.windowHandle() else None
            if screen is None:
                screen = QGuiApplication.primaryScreen()
            if screen is None:
                return False
            geometry = screen.geometry()
            if state.width >= geometry.width() and state.height >= geometry.height():
                _CLIENT_LOGGER.info(
                    "Overlay running in compositor-managed mode; for true fullscreen use borderless windowed in Elite or enable compositor vsync. (%s)",
                    self.format_scale_debug(),
                )
                overlay_state._fullscreen_hint_logged = True
                return True
            return False

        normalized_state = WindowState(
            x=state.x,
            y=state.y,
            width=state.width,
            height=state.height,
            is_foreground=state.is_foreground,
            is_visible=state.is_visible,
            identifier=state.identifier,
            global_x=state.global_x if state.global_x is not None else state.x,
            global_y=state.global_y if state.global_y is not None else state.y,
        )

        self._window_controller.post_process_follow_state(
            normalized_state,
            target_tuple,
            keep_overlay_visible=self._keep_overlay_visible,
            update_follow_visibility_fn=self._update_follow_visibility,
            update_auto_scale_fn=self._update_auto_legacy_scale,
            ensure_transient_parent_fn=_ensure_parent,
            fullscreen_hint_fn=_fullscreen_hint,
            is_visible_fn=lambda: self.isVisible(),
        )
        # Mirror controller flag back to overlay state for future checks.
        overlay_state._fullscreen_hint_logged = self._window_controller._fullscreen_hint_logged

    def _ensure_transient_parent(self, state: WindowState) -> None:
        overlay_state = cast("OverlayWindowState", self)
        if not sys.platform.startswith("linux"):
            return
        if not self._platform_controller.uses_transient_parent():
            if overlay_state._transient_parent_window is not None:
                window_handle = self.windowHandle()
                if window_handle is not None:
                    try:
                        window_handle.setTransientParent(None)
                    except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                        _CLIENT_LOGGER.debug("Failed to clear transient parent on Wayland: %s", exc)
                    except Exception as exc:  # pragma: no cover - unexpected Qt errors
                        _CLIENT_LOGGER.warning("Unexpected error clearing transient parent on Wayland: %s", exc)
                overlay_state._transient_parent_window = None
                self._transient_parent_id = None
            return
        identifier = state.identifier
        if not identifier or identifier == self._transient_parent_id:
            return
        window_handle = self.windowHandle()
        if window_handle is None:
            return
        try:
            native_id = int(identifier, 16)
        except ValueError:
            return
        try:
            parent_window = QWindow.fromWinId(native_id)
        except Exception as exc:  # pragma: no cover - defensive guard
            _CLIENT_LOGGER.debug("Failed to wrap native window %s: %s; %s", identifier, exc, self.format_scale_debug())
            return
        if parent_window is None:
            return
        window_handle.setTransientParent(parent_window)
        overlay_state._transient_parent_window = parent_window
        self._transient_parent_id = identifier
        _CLIENT_LOGGER.debug(
            "Set overlay transient parent to Elite window %s; %s", identifier, self.format_scale_debug()
        )

    def _handle_missing_follow_state(self) -> None:
        overlay_state = cast("OverlayWindowState", self)
        if not self._lost_window_logged:
            _CLIENT_LOGGER.debug(
                "Elite Dangerous window not found; waiting for window to appear; %s", self.format_scale_debug()
            )
            self._lost_window_logged = True
        if overlay_state._last_follow_state is None:
            if self._keep_overlay_visible:
                self._update_follow_visibility(True)
                if sys.platform.startswith("linux"):
                    self._platform_controller.apply_click_through(True)
                    self._restore_drag_interactivity()
            else:
                self._update_follow_visibility(False)
            return
        if self._keep_overlay_visible:
            self._update_follow_visibility(True)
            if sys.platform.startswith("linux"):
                self._platform_controller.apply_click_through(True)
                self._restore_drag_interactivity()
        else:
            self._last_follow_state = None
            self._clear_wm_override(reason="follow state lost")
            self._update_follow_visibility(False)

    def _update_follow_visibility(self, show: bool) -> None:
        new_state = self._visibility_helper.update_visibility(
            show,
            is_visible_fn=lambda: self.isVisible(),
            show_fn=lambda: self.show(),
            hide_fn=lambda: self.hide(),
            raise_fn=lambda: self.raise_(),
            apply_drag_state_fn=self._apply_drag_state,
            format_scale_debug_fn=self.format_scale_debug,
        )
        # keep compatibility for any consumers expecting cached state
        self._last_visibility_state = new_state

    def _move_to_screen(self, rect: QRect) -> None:
        window = self.windowHandle()
        if window is None:
            return
        screen = self._screen_for_rect(rect)
        if screen is not None and window.screen() is not screen:
            _CLIENT_LOGGER.debug(
                "Moving overlay to screen %s; %s",
                self._describe_screen(screen),
                self.format_scale_debug(),
            )
            window.setScreen(screen)
            self._last_screen_name = self._describe_screen(screen)
        elif screen is not None:
            self._last_screen_name = self._describe_screen(screen)

    def _screen_for_rect(self, rect: QRect):
        screens = QGuiApplication.screens()
        if not screens:
            return None
        best_screen = None
        best_area = 0
        for screen in screens:
            area = rect.intersected(screen.geometry())
            intersection_area = area.width() * area.height()
            if intersection_area > best_area:
                best_area = intersection_area
                best_screen = screen
        if best_screen is not None:
            return best_screen
        primary = QGuiApplication.primaryScreen()
        return primary or screens[0]

    def _screen_for_native_rect(self, rect: QRect) -> Optional[QScreen]:
        screens = QGuiApplication.screens()
        if not screens:
            return None
        best_screen: Optional[QScreen] = None
        best_area = 0
        for screen in screens:
            try:
                native_geometry = screen.nativeGeometry()
            except AttributeError:
                native_geometry = screen.geometry()
            area = rect.intersected(native_geometry)
            intersection_area = max(area.width(), 0) * max(area.height(), 0)
            if intersection_area > best_area:
                best_area = intersection_area
                best_screen = screen
        if best_screen is not None:
            return best_screen
        return QGuiApplication.primaryScreen()

    def _screen_info_for_native_rect(self, rect: Tuple[int, int, int, int]) -> Optional[ScreenInfo]:
        native_rect = QRect(*rect)
        screen = self._screen_for_native_rect(native_rect)
        if screen is None:
            return None
        try:
            native_geometry = screen.nativeGeometry()
        except AttributeError:
            native_geometry = screen.geometry()
        logical_geometry = screen.geometry()
        device_ratio = 1.0
        screen_name = screen.name() or screen.manufacturer() or "unknown"
        try:
            device_ratio = float(screen.devicePixelRatio())
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            _CLIENT_LOGGER.debug("devicePixelRatio unavailable for screen %s; defaulting to 1.0 (%s)", screen_name, exc)
            device_ratio = 1.0
        if device_ratio <= 0.0:
            device_ratio = 1.0
        return ScreenInfo(
            name=screen_name,
            logical_geometry=(
                logical_geometry.x(),
                logical_geometry.y(),
                logical_geometry.width(),
                logical_geometry.height(),
            ),
            native_geometry=(
                native_geometry.x(),
                native_geometry.y(),
                native_geometry.width(),
                native_geometry.height(),
            ),
            device_ratio=device_ratio,
        )

    def _describe_screen(self, screen) -> str:
        if screen is None:
            return "unknown"
        try:
            geometry = screen.geometry()
            return f"{screen.name()} {geometry.width()}x{geometry.height()}@({geometry.x()},{geometry.y()})"
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            _CLIENT_LOGGER.debug("Failed to describe screen %r: %s", screen, exc)
            return str(screen)
        except Exception as exc:  # pragma: no cover - unexpected Qt errors
            _CLIENT_LOGGER.warning("Unexpected error describing screen %r: %s", screen, exc)
            return str(screen)

    def _sync_base_dimensions_to_widget(self) -> None:
        width_px, height_px = self._current_physical_size()
        self._base_width = max(int(round(width_px)), 1)
        self._base_height = max(int(round(height_px)), 1)

    def _classify_geometry_override(
        self,
        tracker_tuple: Tuple[int, int, int, int],
        actual_tuple: Tuple[int, int, int, int],
    ) -> str:
        """Identify whether a WM override stems from internal layout constraints."""
        try:
            min_hint = self.minimumSizeHint()
        except Exception:
            min_hint = None
        try:
            size_hint = self.sizeHint()
        except Exception:
            size_hint = None
        return self._compute_geometry_override_classification(tracker_tuple, actual_tuple, min_hint, size_hint)

    @staticmethod
    def _compute_geometry_override_classification(
        tracker_tuple: Tuple[int, int, int, int],
        actual_tuple: Tuple[int, int, int, int],
        min_hint: Optional[QSize],
        size_hint: Optional[QSize],
        *,
        tolerance: int = 2,
    ) -> str:
        tracker_width = tracker_tuple[2]
        tracker_height = tracker_tuple[3]
        actual_width = actual_tuple[2]
        actual_height = actual_tuple[3]
        width_diff = actual_width - tracker_width
        height_diff = actual_height - tracker_height

        if width_diff < 0 or height_diff < 0:
            return "wm_intervention"

        min_width = max(min_hint.width() if isinstance(min_hint, QSize) else 0, 0)
        min_height = max(min_hint.height() if isinstance(min_hint, QSize) else 0, 0)
        size_width = max(size_hint.width() if isinstance(size_hint, QSize) else 0, 0)
        size_height = max(size_hint.height() if isinstance(size_hint, QSize) else 0, 0)

        within_preferred_width = size_width <= 0 or actual_width <= size_width + tolerance
        within_preferred_height = size_height <= 0 or actual_height <= size_height + tolerance

        width_constrained = (
            width_diff > 0 and min_width > 0 and actual_width >= (min_width - tolerance) and within_preferred_width
        )
        height_constrained = (
            height_diff > 0 and min_height > 0 and actual_height >= (min_height - tolerance) and within_preferred_height
        )

        if width_constrained or height_constrained:
            return "layout"
        return "wm_intervention"
