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
    support_label = str(report.get("support_label") or "unknown")
    classification = str(report.get("classification") or "unknown")
    source = str(report.get("source") or "unknown")
    summary = f"Backend: {support_label} | Mode: {classification} | Source: {source}"
    manual_override = str(report.get("manual_override") or "")
    override_error = str(report.get("override_error") or "")
    if manual_override:
        summary = f"{summary} | Override: {manual_override}"
    elif override_error:
        summary = f"{summary} | Override: invalid ({override_error})"
    return summary


def format_status_ui_warning(status: BackendSelectionStatus | Mapping[str, object]) -> str:
    """Return a user-facing warning line for degraded, fallback, or helper-missing states."""

    report = build_status_report(status)
    reasons: list[str] = []
    classification = str(report.get("classification") or "")
    if classification in {CapabilityClassification.DEGRADED_OVERLAY.value, CapabilityClassification.UNSUPPORTED.value}:
        reasons.append(f"Mode: {classification}")
    fallback_from = str(report.get("fallback_from") or "")
    fallback_reason = str(report.get("fallback_reason") or "")
    if fallback_from and fallback_reason:
        reasons.append(f"Fallback from {fallback_from} ({fallback_reason})")
    elif fallback_reason:
        reasons.append(f"Fallback reason: {fallback_reason}")
    manual_override = str(report.get("manual_override") or "")
    if manual_override:
        reasons.append(f"Manual override active: {manual_override}")
    override_error = str(report.get("override_error") or "")
    if override_error:
        reasons.append(f"Invalid override: {override_error}")
    helper_unavailable = report.get("helper_unavailable")
    fallback_reason = str(report.get("fallback_reason") or "")
    if isinstance(helper_unavailable, list) and helper_unavailable and fallback_reason != FallbackReason.MISSING_HELPER.value:
        helpers = ", ".join(str(helper) for helper in helper_unavailable if str(helper))
        if helpers:
            reasons.append(f"Helper unavailable: {helpers}")
    if bool(report.get("review_required")):
        review_values = report.get("review_reasons")
        if isinstance(review_values, list) and review_values:
            reasons.append("Review required: " + ", ".join(str(value) for value in review_values if str(value)))
        else:
            reasons.append("Review required")
    if not reasons:
        return ""
    return "Warning: " + "; ".join(reasons)


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
        title = f"{title} - {warning.removeprefix('Warning: ')}"
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
