"""Helpers for scanning EDMC plugins and reporting overlay config status."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

try:
    import config as _edmc_config_module  # type: ignore
    from config import config as EDMC_CONFIG  # type: ignore
except Exception:  # pragma: no cover - running outside EDMC
    _edmc_config_module = None
    EDMC_CONFIG = None


LOGGER = logging.getLogger("EDMC.ModernOverlay.PluginScan")
KNOWN_PLUGINS_PATH = Path(__file__).resolve().with_name("known_plugins.json")


@dataclass(frozen=True)
class PluginEntry:
    name: str
    path: Path
    disabled: bool


def _is_disabled_dir(name: str) -> bool:
    lowered = name.lower()
    return lowered.endswith(".disabled") or ".disabled." in lowered


def scan_plugins(
    plugins_root: Path,
    *,
    include_disabled: bool = False,
    self_root: Optional[Path] = None,
) -> list[PluginEntry]:
    results: list[PluginEntry] = []
    if not plugins_root.exists() or not plugins_root.is_dir():
        return results
    resolved_self = self_root.resolve() if self_root else None
    for entry in sorted(plugins_root.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir():
            continue
        if resolved_self is not None and entry.resolve() == resolved_self:
            continue
        disabled = _is_disabled_dir(entry.name)
        if disabled and not include_disabled:
            continue
        if not (entry / "load.py").exists():
            continue
        results.append(PluginEntry(name=entry.name, path=entry.resolve(), disabled=disabled))
    return results


def load_known_plugins(path: Path = KNOWN_PLUGINS_PATH) -> Dict[str, Mapping[str, Any]]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError:
        return {}
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, Mapping):
        return {}
    normalized: Dict[str, Mapping[str, Any]] = {}
    for name, spec in data.items():
        if not isinstance(name, str) or not isinstance(spec, Mapping):
            continue
        normalized[name.casefold()] = dict(spec)
    return normalized


def _config_getter(name: str):
    if _edmc_config_module is not None:
        getter = getattr(_edmc_config_module, name, None)
        if callable(getter):
            return getter
    if EDMC_CONFIG is not None:
        getter = getattr(EDMC_CONFIG, name, None)
        if callable(getter):
            return getter
    return None


def _config_call(getter, key: str, default: Any) -> Any:
    try:
        return getter(key, default)
    except TypeError:
        try:
            return getter(key)
        except Exception:
            return default
    except Exception:
        return default


def config_get_value(key: str, default: Any = "") -> Any:
    getter = _config_getter("get")
    if getter is not None:
        return _config_call(getter, key, default)
    getter = _config_getter("get_str")
    if getter is not None:
        fallback = default if isinstance(default, str) else ""
        return _config_call(getter, key, fallback)
    return default


def _normalise_values(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    if isinstance(values, Iterable):
        return [str(item) for item in values if item is not None]
    return [str(values)]


def _matches_value(raw: Any, enabled_values: Any) -> bool:
    raw_text = "" if raw is None else str(raw)
    raw_key = raw_text.casefold()
    for candidate in _normalise_values(enabled_values):
        if raw_key == candidate.casefold():
            return True
    return False


def _matches_substring(raw: Any, enabled_substrings: Any) -> bool:
    raw_text = "" if raw is None else str(raw)
    raw_key = raw_text.casefold()
    for candidate in _normalise_values(enabled_substrings):
        needle = candidate.casefold()
        if needle and needle in raw_key:
            return True
    return False


def evaluate_overlay_status(
    plugin_name: str,
    known_plugins: Mapping[str, Mapping[str, Any]],
) -> tuple[str, Optional[str], Any]:
    spec = known_plugins.get(plugin_name.casefold())
    if not spec:
        return "unknown", None, None
    config_key = spec.get("config_key")
    if not isinstance(config_key, str) or not config_key.strip():
        return "unknown", None, None
    raw_value = config_get_value(config_key, "")
    enabled_values = spec.get("enabled_values")
    enabled_substrings = spec.get("enabled_substrings")
    matched = False
    if enabled_substrings:
        matched = _matches_substring(raw_value, enabled_substrings)
    if not matched:
        matched = _matches_value(raw_value, enabled_values or ["Yes"])
    status = "enabled" if matched else "disabled"
    return status, config_key, raw_value
