"""Pure backend contract and status types for the overlay client."""

from .contracts import (
    BackendBundle,
    BackendDescriptor,
    BackendFamily,
    BackendInstance,
    CapabilityClassification,
    FallbackReason,
    HelperKind,
    HelperIpcBackend,
    InputPolicyBackend,
    OperatingSystem,
    PlatformProbe,
    PlatformProbeResult,
    PresentationBackend,
    SessionType,
    TargetDiscoveryBackend,
)
from .probe import ProbeInputs, ProbeSource, collect_platform_probe
from .selector import BackendSelector
from .status import BackendSelectionStatus, HelperCapabilityState

__all__ = [
    "BackendBundle",
    "BackendSelector",
    "BackendDescriptor",
    "BackendFamily",
    "BackendInstance",
    "BackendSelectionStatus",
    "CapabilityClassification",
    "FallbackReason",
    "HelperCapabilityState",
    "HelperIpcBackend",
    "HelperKind",
    "InputPolicyBackend",
    "OperatingSystem",
    "PlatformProbe",
    "PlatformProbeResult",
    "PresentationBackend",
    "ProbeInputs",
    "ProbeSource",
    "SessionType",
    "TargetDiscoveryBackend",
    "collect_platform_probe",
]
