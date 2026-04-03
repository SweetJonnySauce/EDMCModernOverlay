"""Pure status and diagnostics models for backend selection."""

from __future__ import annotations

from dataclasses import dataclass, field

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
    helper_states: tuple[HelperCapabilityState, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    shadow_mode: bool = False

    @property
    def uses_fallback(self) -> bool:
        return self.fallback_from is not None and self.fallback_reason is not None

    @property
    def is_true_overlay(self) -> bool:
        return self.classification is CapabilityClassification.TRUE_OVERLAY

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "probe": self.probe.to_payload(),
            "selected_backend": self.selected_backend.to_payload(),
            "classification": self.classification.value,
            "manual_override": self.manual_override.value if self.manual_override is not None else None,
            "helper_states": [state.to_payload() for state in self.helper_states],
            "notes": list(self.notes),
            "shadow_mode": self.shadow_mode,
        }
        if self.fallback_from is not None:
            payload["fallback_from"] = self.fallback_from.to_payload()
        if self.fallback_reason is not None:
            payload["fallback_reason"] = self.fallback_reason.value
        return payload
