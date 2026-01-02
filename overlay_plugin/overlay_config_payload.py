"""Helpers for building overlay config payloads."""
from __future__ import annotations

from typing import Any, Dict, Mapping

from overlay_plugin.obs_capture_support import obs_capture_preference_value


def build_overlay_config_payload(
    preferences: object,
    *,
    diagnostics_enabled: bool,
    force_render: bool,
    client_log_retention: int,
    platform_context: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build the OverlayConfig payload from preferences and runtime context."""
    show_debug_overlay = bool(getattr(preferences, "show_debug_overlay", False) and diagnostics_enabled)
    return {
        "event": "OverlayConfig",
        "opacity": float(getattr(preferences, "overlay_opacity", 0.0)),
        "global_payload_opacity": int(getattr(preferences, "global_payload_opacity", 100)),
        "show_status": bool(getattr(preferences, "show_connection_status", False)),
        "debug_overlay_corner": str(getattr(preferences, "debug_overlay_corner", "NW") or "NW"),
        "status_bottom_margin": int(getattr(preferences, "status_bottom_margin")()),
        "client_log_retention": int(client_log_retention),
        "gridlines_enabled": bool(getattr(preferences, "gridlines_enabled", False)),
        "gridline_spacing": int(getattr(preferences, "gridline_spacing", 120)),
        "force_render": bool(force_render),
        "obs_capture_friendly": obs_capture_preference_value(preferences),
        "title_bar_enabled": bool(getattr(preferences, "title_bar_enabled", False)),
        "title_bar_height": int(getattr(preferences, "title_bar_height", 0)),
        "show_debug_overlay": show_debug_overlay,
        "physical_clamp_enabled": bool(getattr(preferences, "physical_clamp_enabled", False)),
        "physical_clamp_overrides": dict(getattr(preferences, "physical_clamp_overrides", {}) or {}),
        "min_font_point": float(getattr(preferences, "min_font_point", 6.0)),
        "max_font_point": float(getattr(preferences, "max_font_point", 24.0)),
        "legacy_font_step": int(getattr(preferences, "legacy_font_step", 2)),
        "cycle_payload_ids": bool(getattr(preferences, "cycle_payload_ids", False)),
        "copy_payload_id_on_cycle": bool(getattr(preferences, "copy_payload_id_on_cycle", False)),
        "scale_mode": str(getattr(preferences, "scale_mode", "fit") or "fit"),
        "nudge_overflow_payloads": bool(getattr(preferences, "nudge_overflow_payloads", False)),
        "payload_nudge_gutter": int(getattr(preferences, "payload_nudge_gutter", 30)),
        "payload_log_delay_seconds": float(getattr(preferences, "payload_log_delay_seconds", 0.0)),
        "platform_context": dict(platform_context),
    }
