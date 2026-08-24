"""Type-only contract for setup-owned OverlayWindow state."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from PyQt6.QtCore import QPoint
    from PyQt6.QtGui import QCursor, QWindow

    from overlay_client.platform_integration import PlatformContext
    from overlay_client.window_tracking import WindowState


class OverlayWindowState(Protocol):
    """Shared state initialized by ``SetupSurfaceMixin`` for overlay surfaces."""

    _aspect_guard_skip_logged: bool
    _background_opacity: float
    _cursor_saved: bool
    _cycle_copy_clipboard: bool
    _cycle_payload_enabled: bool
    _debug_message_point_size: float
    _debug_overlay_corner: str
    _drag_active: bool
    _drag_enabled: bool
    _drag_offset: QPoint
    _enforcing_follow_size: bool
    _follow_enabled: bool
    _font_max_point: float
    _font_min_point: float
    _fullscreen_hint_logged: bool
    _gridline_spacing: int
    _keep_overlay_visible: bool
    _last_backend_mismatch_signature: tuple[
        str, str, str, str, bool, str, str, str, str, str, str, bool, str, str
    ] | None
    _last_device_ratio_log: tuple[str, float, float, float] | None
    _last_follow_state: WindowState | None
    _last_font_notice: tuple[float, float] | None
    _last_move_log: tuple[int, int] | None
    _last_normalised_tracker: tuple[tuple[int, int, int, int], tuple[int, int, int, int], str, float, float] | None
    _last_raw_window_log: tuple[int, int, int, int] | None
    _last_title_bar_offset: int
    _log_retention: int
    _move_mode: bool
    _payload_log_delay_base: float
    _payload_nudge_enabled: bool
    _payload_nudge_gutter: int
    _platform_context: PlatformContext
    _repaint_log_last: dict[str, object] | None
    _saved_cursor: QCursor
    _scale_mode: str
    _show_debug_overlay: bool
    _title_bar_enabled: bool
    _title_bar_height: int
    _transient_parent_window: QWindow | None
