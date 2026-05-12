from __future__ import annotations

import sys
from typing import Callable, Optional

from PyQt6.QtCore import Qt


class InteractionController:
    """Handles click-through, drag restoration, and keep-visible platform quirks."""

    def __init__(
        self,
        *,
        is_wayland_fn: Callable[[], bool],
        requires_focus_safe_flags_fn: Callable[[], bool],
        log_fn: Callable[..., None],
        prepare_window_fn: Callable[[object], None],
        apply_click_through_fn: Callable[[bool], None],
        set_transient_parent_fn: Callable[[object | None], None],
        clear_transient_parent_ids_fn: Callable[[], None],
        window_handle_fn: Callable[[], object | None],
        set_widget_attribute_fn: Callable[[Qt.WidgetAttribute, bool], None],
        set_window_flag_fn: Callable[[Qt.WindowType, bool], None],
        ensure_visible_fn: Callable[[], None],
        raise_fn: Callable[[], None],
        set_children_attr_fn: Callable[[bool], None],
        transparent_input_supported: bool,
        set_window_transparent_input_fn: Callable[[bool], None],
    ) -> None:
        self._is_wayland = is_wayland_fn
        self._requires_focus_safe_flags = requires_focus_safe_flags_fn
        self._log = log_fn
        self._prepare_window = prepare_window_fn
        self._apply_click_through = apply_click_through_fn
        self._set_transient_parent = set_transient_parent_fn
        self._clear_transient_parent_ids = clear_transient_parent_ids_fn
        self._window_handle = window_handle_fn
        self._set_widget_attribute = set_widget_attribute_fn
        self._set_window_flag = set_window_flag_fn
        self._ensure_visible = ensure_visible_fn
        self._raise = raise_fn
        self._set_children_attr = set_children_attr_fn
        self._transparent_input_supported = transparent_input_supported
        self._set_window_transparent_input = set_window_transparent_input_fn
        self._current_click_through: Optional[bool] = None

    def set_click_through(self, transparent: bool, *, force: bool = False, reason: str = "") -> None:
        if not force and self._current_click_through is not None and self._current_click_through == transparent:
            return
        self._current_click_through = transparent
        self._apply_click_through_state(transparent, reason or "set_click_through")

    def reapply_current(self, *, reason: str = "") -> None:
        if self._current_click_through is None:
            return
        self._apply_click_through_state(self._current_click_through, reason or "reapply_current")

    def prepare_window_flags_for_click_through(self, transparent: bool, *, reason: str = "") -> None:
        focus_flag_state = self._apply_window_identity_flags(transparent)
        self._log(
            "Prepared overlay window flags for click-through=%s (reason=%s focus_safe_window=%s)",
            transparent,
            reason or "prepare_window_flags_for_click_through",
            focus_flag_state,
        )

    def restore_drag_interactivity(self, drag_enabled: bool, drag_active: bool, format_scale_debug: Callable[[], str]) -> None:
        if not drag_enabled or drag_active:
            return
        self._log(
            "Restoring interactive overlay input because drag is enabled; %s",
            format_scale_debug(),
            "",
        )
        self.set_click_through(False, force=True, reason="restore_drag_interactivity")

    def handle_keep_overlay_visible_enter(self) -> None:
        if sys.platform.startswith("linux") and self._is_wayland():
            window_handle = self._window_handle()
            if window_handle is not None:
                try:
                    self._set_transient_parent(None)
                except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                    self._log("Failed to clear transient parent on keep-overlay-visible: %s", exc, "")
                except Exception as exc:  # pragma: no cover - unexpected Qt errors
                    self._log("Unexpected error clearing transient parent on keep-overlay-visible: %s", exc, "")
            self._clear_transient_parent_ids()
        if sys.platform.startswith("linux"):
            # Best-effort: ask the platform controller to apply transparent input, then restore desired state.
            self._apply_click_through(True)
        self.reapply_current(reason="keep_overlay_visible_enter")

    def handle_force_render_enter(self) -> None:
        """Legacy alias for the keep-overlay-visible transition."""

        self.handle_keep_overlay_visible_enter()

    def _apply_click_through_state(self, transparent: bool, reason: str) -> None:
        focus_flag_state = self._apply_window_identity_flags(transparent)
        self._ensure_visible()
        window = self._window_handle()
        self._log(
            "Set click-through to %s (reason=%s window_flag=%s focus_safe_window=%s)",
            transparent,
            reason or "unspecified",
            "unknown" if window is None else "set",
            focus_flag_state,
        )
        if window is not None:
            self._prepare_window(window)
            self._apply_click_through(transparent)
            if self._transparent_input_supported:
                self._set_window_transparent_input(transparent)
        self._raise()

    def _apply_window_identity_flags(self, transparent: bool) -> str:
        self._set_widget_attribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, transparent)
        self._set_children_attr(transparent)
        self._set_window_flag(Qt.WindowType.WindowStaysOnTopHint, True)
        self._set_window_flag(Qt.WindowType.FramelessWindowHint, True)
        self._set_window_flag(Qt.WindowType.Tool, not self._is_wayland())
        try:
            focus_safe_required = bool(self._requires_focus_safe_flags())
        except Exception as exc:  # pragma: no cover - defensive callback boundary
            self._log("Failed to evaluate focus-safe overlay flag policy: %s", exc)
            focus_safe_required = False
        if not focus_safe_required:
            return "not_required"
        focus_flag = getattr(Qt.WindowType, "WindowDoesNotAcceptFocus", None)
        if focus_flag is None:
            return "unsupported"
        self._set_window_flag(focus_flag, True)
        return "applied"
