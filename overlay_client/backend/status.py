"""Pure status and diagnostics models for backend selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .contracts import (
    BackendDescriptor,
    BackendInstance,
    CapabilityClassification,
    FallbackReason,
    HelperKind,
    PlatformProbeResult,
)


@dataclass(frozen=True, slots=True)
class HelperCapabilityState:
    """Observed helper availability for a single helper-backed integration."""

    helper: HelperKind
    required: bool = False
    installed: bool = False
    enabled: bool = False
    approved: bool = False
    version: str = ""
    detail: str = ""

    @property
    def available(self) -> bool:
        return self.installed and self.enabled

    def to_payload(self) -> dict[str, object]:
        return {
            "helper": self.helper.value,
            "required": self.required,
            "installed": self.installed,
            "enabled": self.enabled,
            "approved": self.approved,
            "version": self.version,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class BackendSelectionStatus:
    """Full selection result exposed to diagnostics and later UI surfaces."""

    probe: PlatformProbeResult
    selected_backend: BackendDescriptor
    classification: CapabilityClassification
    fallback_from: BackendDescriptor | None = None
    fallback_reason: FallbackReason | None = None
    manual_override: BackendInstance | None = None
    override_error: str = ""
    helper_states: tuple[HelperCapabilityState, ...] = field(default_factory=tuple)
    review_required: bool = False
    review_reasons: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    shadow_mode: bool = False

    @property
    def uses_fallback(self) -> bool:
        return self.fallback_from is not None and self.fallback_reason is not None

    @property
    def is_true_overlay(self) -> bool:
        return self.classification is CapabilityClassification.TRUE_OVERLAY

    @property
    def has_review_guard(self) -> bool:
        return self.review_required and bool(self.review_reasons)

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "probe": self.probe.to_payload(),
            "selected_backend": self.selected_backend.to_payload(),
            "classification": self.classification.value,
            "manual_override": self.manual_override.value if self.manual_override is not None else None,
            "override_error": self.override_error,
            "helper_states": [state.to_payload() for state in self.helper_states],
            "review_required": self.review_required,
            "review_reasons": list(self.review_reasons),
            "notes": list(self.notes),
            "shadow_mode": self.shadow_mode,
        }
        if self.fallback_from is not None:
            payload["fallback_from"] = self.fallback_from.to_payload()
        if self.fallback_reason is not None:
            payload["fallback_reason"] = self.fallback_reason.value
        payload["report"] = build_status_report(self)
        return payload


def build_status_report(status: BackendSelectionStatus | Mapping[str, object]) -> dict[str, object]:
    """Return a flattened diagnostic report for UI, logs, and support tooling."""

    subject = _status_subject(status)
    if isinstance(subject, BackendSelectionStatus):
        family = subject.selected_backend.family.value
        instance = subject.selected_backend.instance.value
        support_label = subject.selected_backend.support_label
        classification = subject.classification.value
        fallback_from = (
            subject.fallback_from.support_label if subject.fallback_from is not None else ""
        )
        fallback_reason = subject.fallback_reason.value if subject.fallback_reason is not None else ""
        manual_override = subject.manual_override.value if subject.manual_override is not None else ""
        override_error = str(subject.override_error or "")
        helper_states = [
            _format_helper_summary(
                helper=state.helper.value,
                required=state.required,
                installed=state.installed,
                enabled=state.enabled,
                approved=state.approved,
                version=state.version,
            )
            for state in subject.helper_states
        ]
        helper_unavailable = [
            state.helper.value for state in subject.helper_states if state.required and not state.available
        ]
        helper_optional_unavailable = [
            state.helper.value for state in subject.helper_states if not state.required and not state.available
        ]
        review_required = bool(subject.review_required)
        review_reasons = list(subject.review_reasons)
        source = "plugin_hint" if subject.shadow_mode else "client_runtime"
    else:
        selected_backend = subject.get("selected_backend")
        if not isinstance(selected_backend, Mapping):
            selected_backend = {}
        family = str(selected_backend.get("family") or "")
        instance = str(selected_backend.get("instance") or "")
        support_label = _support_label(family, instance)
        classification = str(subject.get("classification") or "")
        fallback_mapping = subject.get("fallback_from")
        if isinstance(fallback_mapping, Mapping):
            fallback_from = _support_label(
                str(fallback_mapping.get("family") or ""),
                str(fallback_mapping.get("instance") or ""),
            )
        else:
            fallback_from = ""
        fallback_reason = str(subject.get("fallback_reason") or "")
        manual_override = str(subject.get("manual_override") or "")
        override_error = str(subject.get("override_error") or "")
        review_required = bool(subject.get("review_required"))
        review_values = subject.get("review_reasons")
        if isinstance(review_values, list):
            review_reasons = [str(value) for value in review_values if str(value)]
        else:
            review_reasons = []
        source = "plugin_hint" if bool(subject.get("shadow_mode")) else "client_runtime"
        helper_states = []
        helper_unavailable = []
        helper_optional_unavailable = []
        for raw_state in subject.get("helper_states", []) if isinstance(subject, Mapping) else []:
            if not isinstance(raw_state, Mapping):
                continue
            helper_name = str(raw_state.get("helper") or "")
            required = bool(raw_state.get("required"))
            available = bool(raw_state.get("installed")) and bool(raw_state.get("enabled"))
            if helper_name and required and not available:
                helper_unavailable.append(helper_name)
            if helper_name and not required and not available:
                helper_optional_unavailable.append(helper_name)
            helper_states.append(
                _format_helper_summary(
                    helper=helper_name,
                    required=required,
                    installed=bool(raw_state.get("installed")),
                    enabled=bool(raw_state.get("enabled")),
                    approved=bool(raw_state.get("approved")),
                    version=str(raw_state.get("version") or ""),
                )
            )
    warning_required = bool(
        classification in {CapabilityClassification.DEGRADED_OVERLAY.value, CapabilityClassification.UNSUPPORTED.value}
        or fallback_reason
        or manual_override
        or override_error
        or helper_unavailable
    )
    report = {
        "family": family,
        "instance": instance,
        "support_label": support_label,
        "classification": classification,
        "source": source,
        "fallback_from": fallback_from,
        "fallback_reason": fallback_reason,
        "manual_override": manual_override,
        "override_error": override_error,
        "review_required": review_required,
        "review_reasons": review_reasons,
        "helper_states": helper_states,
        "helper_unavailable": helper_unavailable,
        "helper_optional_unavailable": helper_optional_unavailable,
        "warning_required": warning_required,
    }
    report["summary"] = format_status_report_line(report)
    return report


def format_status_report_line(status: BackendSelectionStatus | Mapping[str, object]) -> str:
    """Return a compact key=value status line safe for logs and script parsing."""

    if isinstance(status, Mapping) and "selected_backend" not in status:
        report = status
    else:
        report = build_status_report(status)
    helper_states = report.get("helper_states")
    helper_token = "none"
    if isinstance(helper_states, list) and helper_states:
        helper_token = ",".join(str(item) for item in helper_states if str(item))
    review_reasons = report.get("review_reasons")
    review_token = "none"
    if isinstance(review_reasons, list) and review_reasons:
        review_token = ",".join(str(item) for item in review_reasons if str(item))
    return (
        f"family={report.get('family') or 'unknown'} "
        f"instance={report.get('instance') or 'unknown'} "
        f"classification={report.get('classification') or 'unknown'} "
        f"fallback_from={_token_value(report.get('fallback_from'))} "
        f"fallback_reason={_token_value(report.get('fallback_reason'))} "
        f"manual_override={_token_value(report.get('manual_override'))} "
        f"override_error={_token_value(report.get('override_error'))} "
        f"review_required={'true' if bool(report.get('review_required')) else 'false'} "
        f"review_reasons={review_token} "
        f"helpers={helper_token}"
    )


def format_status_ui_summary(status: BackendSelectionStatus | Mapping[str, object]) -> str:
    """Return a concise user-facing status summary."""

    report = build_status_report(status)
    support_label = _ui_backend_label(report)
    classification = _ui_classification_label(str(report.get("classification") or "unknown"))
    source = _ui_source_label(str(report.get("source") or "unknown"))
    summary = f"Backend: {support_label} | Mode: {classification} | Source: {source}"
    manual_override = str(report.get("manual_override") or "")
    override_error = str(report.get("override_error") or "")
    if manual_override:
        summary = f"{summary} | Overlay backend: {_ui_backend_override_label(manual_override)}"
    elif override_error:
        summary = f"{summary} | Overlay backend: invalid ({override_error})"
    return summary


def format_status_ui_warning(status: BackendSelectionStatus | Mapping[str, object]) -> str:
    """Return a user-facing backend notice line for warning or informational states."""

    report = build_status_report(status)
    warning_reasons: list[str] = []
    info_reasons: list[str] = []
    classification = str(report.get("classification") or "")
    if classification == CapabilityClassification.DEGRADED_OVERLAY.value:
        warning_reasons.append("Some overlay guarantees are reduced in this mode.")
    elif classification == CapabilityClassification.UNSUPPORTED.value:
        warning_reasons.append("This environment is not currently supported.")
    fallback_from = str(report.get("fallback_from") or "")
    fallback_reason = str(report.get("fallback_reason") or "")
    manual_override = str(report.get("manual_override") or "")
    manual_override_label = _ui_backend_override_label(manual_override)
    if manual_override:
        info_reasons.append(f"Overlay backend is set to {manual_override_label}.")
    fallback_message = _ui_fallback_message(
        fallback_reason=fallback_reason,
        fallback_from=fallback_from,
        manual_override=manual_override,
    )
    if fallback_message:
        if fallback_reason == FallbackReason.MANUAL_OVERRIDE.value and manual_override:
            info_reasons.append(fallback_message)
        else:
            warning_reasons.append(fallback_message)
    override_error = str(report.get("override_error") or "")
    if override_error:
        warning_reasons.append(f"Saved Overlay backend selection is invalid for this session: {override_error}.")
        warning_reasons.append("Set Overlay backend to Auto or choose a valid backend for this session.")
    helper_unavailable = report.get("helper_unavailable")
    if isinstance(helper_unavailable, list) and helper_unavailable and fallback_reason != FallbackReason.MISSING_HELPER.value:
        helpers = ", ".join(_ui_helper_label(str(helper)) for helper in helper_unavailable if str(helper))
        if helpers:
            warning_reasons.append(f"Required helper unavailable: {helpers}.")
    if warning_reasons:
        if info_reasons:
            warning_reasons = info_reasons + warning_reasons
        return "Warning: " + "; ".join(warning_reasons)
    if manual_override:
        info_reasons.append("Set Overlay backend to Auto if you want the overlay to choose automatically.")
    if not info_reasons:
        return ""
    return "Info: " + "; ".join(info_reasons)


def format_status_window_title(
    status: BackendSelectionStatus | Mapping[str, object],
    *,
    base_title: str = "Overlay Controller",
) -> str:
    """Return a compact window-title status string."""

    report = build_status_report(status)
    support_label = str(report.get("support_label") or "unknown")
    classification = str(report.get("classification") or "unknown")
    source = str(report.get("source") or "unknown")
    title = f"{base_title} - {support_label} [{classification}, {source}]"
    warning = format_status_ui_warning(status)
    if warning:
        title = f"{title} - {warning.removeprefix('Warning: ').removeprefix('Info: ')}"
    return title


def _status_subject(status: BackendSelectionStatus | Mapping[str, object]) -> BackendSelectionStatus | Mapping[str, object]:
    if isinstance(status, BackendSelectionStatus):
        return status
    nested = status.get("backend_status")
    if isinstance(nested, Mapping) and "selected_backend" in nested:
        return nested
    return status


def _support_label(family: str, instance: str) -> str:
    if not family and not instance:
        return ""
    return f"{family} / {instance}"


def _ui_backend_label(report: Mapping[str, object]) -> str:
    family = str(report.get("family") or "")
    instance = str(report.get("instance") or "")
    labels = {
        ("native_windows", "windows_desktop"): "Windows desktop",
        ("native_x11", "native_x11"): "Native X11",
        ("xwayland_compat", "xwayland_compat"): "XWayland compatibility",
        ("native_wayland", "wayland_layer_shell_generic"): "Generic Wayland",
        ("native_wayland", "kwin_wayland"): "KWin Wayland",
        ("compositor_helper", "kwin_wayland"): "KWin helper",
        ("native_wayland", "gnome_shell_wayland"): "GNOME Wayland",
        ("compositor_helper", "gnome_shell_wayland"): "GNOME Shell helper",
        ("native_wayland", "sway_wayfire_wlroots"): "wlroots Wayland",
        ("native_wayland", "hyprland"): "Hyprland",
        ("native_wayland", "cosmic"): "COSMIC Wayland",
        ("native_wayland", "gamescope"): "Gamescope Wayland",
        ("portal_fallback", "portal_fallback"): "Portal fallback",
    }
    return labels.get((family, instance), str(report.get("support_label") or "unknown"))


def _ui_backend_override_label(value: str) -> str:
    token = str(value or "").strip()
    if not token:
        return "Auto"
    labels = {
        "native_x11": "Native X11",
        "xwayland_compat": "XWayland compatibility",
        "windows_desktop": "Windows desktop",
        "wayland_layer_shell_generic": "Generic Wayland",
        "kwin_wayland": "KWin Wayland",
        "gnome_shell_wayland": "GNOME Wayland",
        "sway_wayfire_wlroots": "wlroots Wayland",
        "hyprland": "Hyprland",
        "cosmic": "COSMIC Wayland",
        "gamescope": "Gamescope Wayland",
        "portal_fallback": "Portal fallback",
    }
    return labels.get(token, token)


def _ui_classification_label(value: str) -> str:
    labels = {
        CapabilityClassification.TRUE_OVERLAY.value: "True overlay",
        CapabilityClassification.DEGRADED_OVERLAY.value: "Degraded overlay",
        CapabilityClassification.UNSUPPORTED.value: "Unsupported",
    }
    return labels.get(value, value or "unknown")


def _ui_source_label(value: str) -> str:
    labels = {
        "client_runtime": "Live runtime",
        "plugin_hint": "Plugin hint",
    }
    return labels.get(value, value or "unknown")


def _ui_fallback_message(*, fallback_reason: str, fallback_from: str, manual_override: str) -> str:
    if fallback_reason == FallbackReason.MANUAL_OVERRIDE.value:
        if manual_override:
            return f"Using {_ui_backend_override_label(manual_override)} because it is selected in Overlay backend."
        return "Using the selected Overlay backend setting."
    if fallback_reason == FallbackReason.XWAYLAND_COMPAT_ONLY.value:
        return "Using XWayland compatibility mode because a native Wayland path is not active."
    if fallback_reason == FallbackReason.MISSING_HELPER.value:
        if fallback_from:
            return f"A required helper for {fallback_from} is not available."
        return "A required compositor helper is not available."
    if fallback_reason == FallbackReason.MISSING_PROTOCOL.value:
        return "Required compositor protocols are not available."
    if fallback_reason == FallbackReason.COMPOSITOR_RESTRICTION.value:
        return "The compositor is restricting the preferred overlay path."
    if fallback_reason == FallbackReason.TRACKING_UNAVAILABLE.value:
        return "Window tracking is unavailable for the preferred backend."
    if fallback_reason == FallbackReason.CLICK_THROUGH_UNAVAILABLE.value:
        return "Click-through is unavailable for the preferred backend."
    if fallback_reason == FallbackReason.STACKING_NOT_GUARANTEED.value:
        return "Stacking behavior is not guaranteed for the preferred backend."
    if fallback_reason == FallbackReason.SANDBOX_RESTRICTION.value:
        return "Sandbox restrictions are limiting overlay capabilities."
    if fallback_reason == FallbackReason.NOT_IMPLEMENTED.value:
        return "The preferred backend is not implemented yet."
    if fallback_reason == FallbackReason.INVALID_OVERRIDE.value:
        return "The saved Overlay backend selection is not valid for this environment."
    return ""


def _ui_helper_label(value: str) -> str:
    labels = {
        "gnome_shell_extension": "GNOME Shell extension",
        "kwin_script": "KWin script",
        "kwin_effect": "KWin effect",
        "external_helper": "external helper",
    }
    return labels.get(value, value or "unknown helper")


def _token_value(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "none"
    return text.replace(" / ", "/").replace(" ", "_")


def _format_helper_summary(
    *,
    helper: str,
    required: bool,
    installed: bool,
    enabled: bool,
    approved: bool,
    version: str,
) -> str:
    base = helper or "unknown"
    state = "available" if installed and enabled else "inactive"
    requirement = "required" if required else "optional"
    approval = "approved" if approved else "unapproved"
    version_token = version.strip() or "none"
    return f"{base}:{requirement}:{state}:{approval}:{version_token}"
