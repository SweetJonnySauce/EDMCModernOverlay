from overlay_client.backend import (
    BackendDescriptor,
    BackendFamily,
    HelperCapabilityState,
    HelperKind,
    BackendInstance,
    BackendSelectionStatus,
    CapabilityClassification,
    FallbackReason,
    OperatingSystem,
    PlatformProbeResult,
    SessionType,
)
from overlay_client.backend.status import (
    build_status_report,
    format_status_report_line,
    format_status_ui_summary,
    format_status_ui_warning,
    format_status_window_title,
)


def _probe() -> PlatformProbeResult:
    return PlatformProbeResult(
        operating_system=OperatingSystem.LINUX,
        session_type=SessionType.WAYLAND,
        qt_platform_name="xcb",
        compositor="kwin",
    )


def test_backend_status_reports_xwayland_fallback_as_degraded_overlay():
    status = BackendSelectionStatus(
        probe=_probe(),
        selected_backend=BackendDescriptor(BackendFamily.XWAYLAND_COMPAT, BackendInstance.XWAYLAND_COMPAT),
        classification=CapabilityClassification.DEGRADED_OVERLAY,
        fallback_from=BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.KWIN_WAYLAND),
        fallback_reason=FallbackReason.XWAYLAND_COMPAT_ONLY,
        notes=("client_selector_result",),
        shadow_mode=False,
    )

    payload = status.to_payload()

    assert status.uses_fallback is True
    assert status.has_review_guard is False
    assert payload["fallback_from"] == {
        "family": "native_wayland",
        "instance": "kwin_wayland",
    }
    assert payload["fallback_reason"] == "xwayland_compat_only"
    assert payload["review_required"] is False
    assert payload["review_reasons"] == []
    assert payload["report"]["family"] == "xwayland_compat"
    assert payload["report"]["instance"] == "xwayland_compat"
    assert payload["report"]["source"] == "client_runtime"
    assert payload["report"]["fallback_from"] == "native_wayland / kwin_wayland"
    assert payload["report"]["warning_required"] is True
    assert payload["report"]["summary"] == (
        "family=xwayland_compat instance=xwayland_compat classification=degraded_overlay "
        "fallback_from=native_wayland/kwin_wayland fallback_reason=xwayland_compat_only "
        "manual_override=none override_error=none review_required=false "
        "review_reasons=none helpers=none helper_details=none gnome_helper_experimental=false"
    )
    assert format_status_ui_summary(payload) == (
        "Backend: XWayland compatibility | Mode: Degraded overlay | Source: Live runtime"
    )
    assert format_status_ui_warning(payload) == (
        "Warning: Some overlay guarantees are reduced in this mode.; "
        "Using XWayland compatibility mode because a native Wayland path is not active."
    )
    assert format_status_window_title(payload) == (
        "Overlay Controller - xwayland_compat / xwayland_compat [degraded_overlay, client_runtime] - "
        "Some overlay guarantees are reduced in this mode.; "
        "Using XWayland compatibility mode because a native Wayland path is not active."
    )


def test_backend_status_defaults_review_metadata_to_clear_state():
    status = BackendSelectionStatus(
        probe=_probe(),
        selected_backend=BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.KWIN_WAYLAND),
        classification=CapabilityClassification.TRUE_OVERLAY,
        notes=("client_selector_result",),
        shadow_mode=False,
    )

    payload = status.to_payload()

    assert status.uses_fallback is False
    assert status.has_review_guard is False
    assert payload["review_required"] is False
    assert payload["review_reasons"] == []
    assert "fallback_reason" not in payload
    assert payload["report"]["source"] == "client_runtime"
    assert payload["report"]["warning_required"] is False
    assert payload["report"]["summary"] == (
        "family=native_wayland instance=kwin_wayland classification=true_overlay "
        "fallback_from=none fallback_reason=none manual_override=none override_error=none "
        "review_required=false review_reasons=none helpers=none helper_details=none "
        "gnome_helper_experimental=false"
    )
    assert format_status_ui_warning(payload) == ""


def test_backend_status_report_helpers_accept_payload_dicts():
    status = BackendSelectionStatus(
        probe=_probe(),
        selected_backend=BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.GNOME_SHELL_WAYLAND),
        classification=CapabilityClassification.TRUE_OVERLAY,
        fallback_from=BackendDescriptor(BackendFamily.COMPOSITOR_HELPER, BackendInstance.GNOME_SHELL_WAYLAND),
        fallback_reason=FallbackReason.MISSING_HELPER,
        notes=("client_selector_result",),
        shadow_mode=False,
    )

    payload = status.to_payload()
    report = build_status_report(payload)

    assert status.is_true_overlay is False
    assert payload["classification"] == "degraded_overlay"
    assert report["family"] == "native_wayland"
    assert report["instance"] == "gnome_shell_wayland"
    assert report["classification"] == "degraded_overlay"
    assert report["fallback_reason"] == "missing_helper"
    assert report["helper_details"] == []
    assert report["gnome_helper_experimental"] is False
    assert format_status_report_line(payload) == report["summary"]
    assert "classification=degraded_overlay" in report["summary"]
    assert format_status_ui_summary(payload) == (
        "Backend: GNOME Wayland | Mode: Degraded overlay | Source: Live runtime"
    )
    assert format_status_ui_warning(payload) == (
        "Warning: Some overlay guarantees are reduced in this mode.; "
        "A required helper for compositor_helper / gnome_shell_wayland is not available. "
        "Re-run the Linux installer while logged into GNOME Wayland to install or repair it."
    )


def test_backend_status_downgrades_gnome_true_overlay_payload_when_required_helper_inactive():
    payload = {
        "selected_backend": {"family": "native_wayland", "instance": "gnome_shell_wayland"},
        "classification": "true_overlay",
        "fallback_from": {"family": "compositor_helper", "instance": "gnome_shell_wayland"},
        "fallback_reason": "missing_helper",
        "shadow_mode": False,
        "helper_states": [
            {
                "helper": "gnome_shell_extension",
                "required": True,
                "installed": True,
                "enabled": False,
                "approved": False,
                "version": "",
            }
        ],
        "review_required": False,
        "review_reasons": [],
    }

    report = build_status_report(payload)

    assert report["classification"] == "degraded_overlay"
    assert report["helper_unavailable"] == ["gnome_shell_extension"]
    assert report["helper_details"] == [
        {
            "helper": "gnome_shell_extension",
            "required": True,
            "installed": True,
            "enabled": False,
            "available": False,
            "approved": False,
            "healthy": False,
            "state": "inactive",
            "version": "",
            "protocol": "",
            "detail": "",
            "capabilities": [],
        }
    ]
    assert report["gnome_helper_experimental"] is False
    assert report["warning_required"] is True
    assert "classification=degraded_overlay" in format_status_report_line(payload)
    assert "classification=true_overlay" not in format_status_report_line(payload)
    assert (
        "helper_details=gnome_shell_extension:state=inactive:required=true:"
        "installed=true:enabled=false:healthy=false:version=none:protocol=none:capabilities=none"
    ) in format_status_report_line(payload)
    assert format_status_ui_summary(payload) == (
        "Backend: GNOME Wayland | Mode: Degraded overlay | Source: Live runtime | "
        "Helper: GNOME Shell extension inactive"
    )


def test_backend_status_surfaces_installed_gnome_helper_dbus_failure_without_reinstall_advice():
    payload = {
        "selected_backend": {"family": "native_wayland", "instance": "gnome_shell_wayland"},
        "classification": "degraded_overlay",
        "fallback_from": {"family": "compositor_helper", "instance": "gnome_shell_wayland"},
        "fallback_reason": "missing_helper",
        "shadow_mode": False,
        "helper_states": [
            {
                "helper": "gnome_shell_extension",
                "required": True,
                "installed": True,
                "enabled": False,
                "approved": False,
                "detail": "health_state=dbus_unreachable",
            }
        ],
        "review_required": False,
        "review_reasons": [],
    }

    report = build_status_report(payload)

    assert report["helper_details"][0]["state"] == "dbus_unreachable"
    assert format_status_ui_summary(payload) == (
        "Backend: GNOME Wayland | Mode: Degraded overlay | Source: Live runtime | "
        "Helper: GNOME Shell extension DBus unreachable"
    )
    warning = format_status_ui_warning(payload)
    assert "Required helper is installed but not healthy: GNOME Shell extension DBus unreachable." in warning
    assert "Re-run the Linux installer" not in warning


def test_backend_status_downgrades_gnome_true_overlay_until_validation_gate_passes():
    payload = {
        "selected_backend": {"family": "compositor_helper", "instance": "gnome_shell_wayland"},
        "classification": "true_overlay",
        "shadow_mode": False,
        "helper_states": [
            {
                "helper": "gnome_shell_extension",
                "required": True,
                "installed": True,
                "enabled": True,
                "approved": True,
                "version": "1.0.0",
            }
        ],
        "review_required": False,
        "review_reasons": [],
    }

    report = build_status_report(payload)

    assert report["classification"] == "degraded_overlay"
    assert report["helper_unavailable"] == []
    assert "classification=degraded_overlay" in report["summary"]
    assert "classification=true_overlay" not in report["summary"]
    assert format_status_ui_summary(payload) == (
        "Backend: GNOME Shell helper | Mode: Degraded overlay | Source: Live runtime | "
        "Helper: GNOME Shell extension available"
    )


def test_backend_status_labels_gnome_shell_raster_as_experimental_degraded_mode():
    payload = {
        "selected_backend": {"family": "compositor_helper", "instance": "gnome_shell_raster"},
        "classification": "true_overlay",
        "manual_override": "gnome_shell_raster",
        "shadow_mode": False,
        "gnome_helper_experimental": True,
        "helper_states": [
            {
                "helper": "gnome_shell_extension",
                "required": True,
                "installed": True,
                "enabled": True,
                "approved": True,
                "version": "1.0.0",
            }
        ],
        "review_required": False,
        "review_reasons": [],
    }

    report = build_status_report(payload)

    assert report["classification"] == "degraded_overlay"
    assert report["gnome_helper_experimental"] is True
    assert format_status_ui_summary(payload) == (
        "Backend: GNOME Shell Raster | Mode: Degraded overlay | Source: Live runtime | "
        "Overlay backend: GNOME Shell Raster | Helper: GNOME Shell extension available"
    )
    assert format_status_ui_warning(payload) == (
        "Warning: Overlay backend is set to GNOME Shell Raster.; "
        "Some overlay guarantees are reduced in this mode."
    )


def test_backend_status_reports_gnome_shell_raster_helper_unavailable_concisely():
    payload = {
        "selected_backend": {"family": "compositor_helper", "instance": "gnome_shell_raster"},
        "classification": "degraded_overlay",
        "fallback_from": {"family": "compositor_helper", "instance": "gnome_shell_raster"},
        "fallback_reason": "missing_helper",
        "manual_override": "gnome_shell_raster",
        "shadow_mode": False,
        "helper_states": [
            {
                "helper": "gnome_shell_extension",
                "required": True,
                "installed": False,
                "enabled": False,
                "approved": False,
                "version": "",
            }
        ],
        "review_required": False,
        "review_reasons": [],
    }

    assert format_status_ui_summary(payload) == (
        "Backend: GNOME Shell Raster | Mode: Degraded overlay | Source: Live runtime | "
        "Overlay backend: GNOME Shell Raster | Helper: GNOME Shell extension inactive"
    )
    assert format_status_ui_warning(payload) == (
        "Warning: Overlay backend is set to GNOME Shell Raster.; "
        "Some overlay guarantees are reduced in this mode.; "
        "A required helper for compositor_helper / gnome_shell_raster is not available. "
        "Re-run the Linux installer while logged into GNOME Wayland to install or repair it."
    )


def test_backend_status_ui_helpers_label_plugin_hint_and_inactive_helpers():
    status = BackendSelectionStatus(
        probe=_probe(),
        selected_backend=BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.GNOME_SHELL_WAYLAND),
        classification=CapabilityClassification.DEGRADED_OVERLAY,
        helper_states=(
            HelperCapabilityState(
                helper=HelperKind.GNOME_SHELL_EXTENSION,
                required=True,
                installed=True,
                enabled=False,
                approved=False,
            ),
        ),
        shadow_mode=True,
    )

    report = build_status_report(status)

    assert report["source"] == "plugin_hint"
    assert report["helper_unavailable"] == ["gnome_shell_extension"]
    assert report["warning_required"] is True
    assert format_status_ui_summary(status) == (
        "Backend: GNOME Wayland | Mode: Degraded overlay | Source: Plugin hint | "
        "Helper: GNOME Shell extension inactive"
    )
    assert format_status_ui_warning(status) == (
        "Warning: Some overlay guarantees are reduced in this mode.; Required helper unavailable: GNOME Shell extension."
    )


def test_backend_status_report_tracks_optional_missing_helpers_without_warning_noise():
    status = BackendSelectionStatus(
        probe=_probe(),
        selected_backend=BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.KWIN_WAYLAND),
        classification=CapabilityClassification.TRUE_OVERLAY,
        helper_states=(
            HelperCapabilityState(
                helper=HelperKind.KWIN_SCRIPT,
                required=False,
                installed=False,
                enabled=False,
                approved=False,
            ),
        ),
        shadow_mode=False,
    )

    report = build_status_report(status)

    assert report["helper_unavailable"] == []
    assert report["helper_optional_unavailable"] == ["kwin_script"]
    assert report["warning_required"] is False
    assert format_status_ui_warning(status) == ""


def test_backend_status_report_helpers_accept_backend_status_response_wrapper():
    status = BackendSelectionStatus(
        probe=_probe(),
        selected_backend=BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.KWIN_WAYLAND),
        classification=CapabilityClassification.TRUE_OVERLAY,
        shadow_mode=True,
    )

    response = {"status": "ok", "backend_status": status.to_payload()}

    assert build_status_report(response)["source"] == "plugin_hint"
    assert format_status_ui_summary(response) == (
        "Backend: KWin Wayland | Mode: True overlay | Source: Plugin hint"
    )


def test_backend_status_ui_helpers_surface_manual_override_and_invalid_override() -> None:
    manual_override_status = BackendSelectionStatus(
        probe=_probe(),
        selected_backend=BackendDescriptor(BackendFamily.XWAYLAND_COMPAT, BackendInstance.XWAYLAND_COMPAT),
        classification=CapabilityClassification.DEGRADED_OVERLAY,
        fallback_from=BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.KWIN_WAYLAND),
        fallback_reason=FallbackReason.MANUAL_OVERRIDE,
        manual_override=BackendInstance.XWAYLAND_COMPAT,
        shadow_mode=False,
    )

    invalid_override_status = BackendSelectionStatus(
        probe=_probe(),
        selected_backend=BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.KWIN_WAYLAND),
        classification=CapabilityClassification.TRUE_OVERLAY,
        override_error="bogus_backend",
        shadow_mode=False,
    )

    manual_report = manual_override_status.to_payload()["report"]
    invalid_report = invalid_override_status.to_payload()["report"]

    assert manual_report["manual_override"] == "xwayland_compat"
    assert manual_report["warning_required"] is True
    assert format_status_ui_summary(manual_override_status) == (
        "Backend: XWayland compatibility | Mode: Degraded overlay | Source: Live runtime | "
        "Overlay backend: XWayland compatibility"
    )
    assert format_status_ui_warning(manual_override_status) == (
        "Warning: Overlay backend is set to XWayland compatibility.; "
        "Using XWayland compatibility because it is selected in Overlay backend.; "
        "Some overlay guarantees are reduced in this mode."
    )

    assert invalid_report["override_error"] == "bogus_backend"
    assert invalid_report["warning_required"] is True
    assert format_status_ui_summary(invalid_override_status) == (
        "Backend: KWin Wayland | Mode: True overlay | Source: Live runtime | "
        "Overlay backend: invalid (bogus_backend)"
    )
    assert format_status_ui_warning(invalid_override_status) == (
        "Warning: Saved Overlay backend selection is invalid for this session: bogus_backend.; "
        "Set Overlay backend to Auto or choose a valid backend for this session."
    )
