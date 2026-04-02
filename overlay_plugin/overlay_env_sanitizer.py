"""Helpers to sanitize overlay subprocess environment variables on Linux."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping

PRESERVE_LD_ENV_KEY = "EDMC_OVERLAY_PRESERVE_LD_ENV"
MEL_LD_LIBRARY_PATH_KEY = "MEL_LD_LIBRARY_PATH"
LD_LIBRARY_PATH_KEY = "LD_LIBRARY_PATH"

SANITIZE_REMOVE_KEYS = (
    "LD_PRELOAD",
    "QT_PLUGIN_PATH",
    "QT_QPA_PLATFORM_PLUGIN_PATH",
)


@dataclass
class OverlayEnvSanitizeResult:
    """Structured result from environment sanitization."""

    actions: Dict[str, str] = field(default_factory=dict)
    skipped_opt_out: bool = False


def _opt_out_enabled(env: Mapping[str, str]) -> bool:
    return str(env.get(PRESERVE_LD_ENV_KEY, "")).strip() == "1"


def sanitize_overlay_environment(env: Mapping[str, str]) -> tuple[Dict[str, str], OverlayEnvSanitizeResult]:
    """Return a sanitized overlay environment and action metadata."""
    sanitized = dict(env)
    result = OverlayEnvSanitizeResult()

    if _opt_out_enabled(sanitized):
        result.skipped_opt_out = True
        for key in (*SANITIZE_REMOVE_KEYS, LD_LIBRARY_PATH_KEY):
            if key in sanitized:
                result.actions[key] = "preserved-by-optout"
        return sanitized, result

    for key in SANITIZE_REMOVE_KEYS:
        if key in sanitized:
            sanitized.pop(key, None)
            result.actions[key] = "removed"

    mel_path = str(sanitized.get(MEL_LD_LIBRARY_PATH_KEY, "")).strip()
    if mel_path:
        sanitized[LD_LIBRARY_PATH_KEY] = mel_path
        result.actions[LD_LIBRARY_PATH_KEY] = "set-from-mel"
    elif LD_LIBRARY_PATH_KEY in sanitized:
        sanitized.pop(LD_LIBRARY_PATH_KEY, None)
        result.actions[LD_LIBRARY_PATH_KEY] = "removed"

    return sanitized, result
