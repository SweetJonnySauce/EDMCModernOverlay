from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import threading
import time
from typing import Any, Callable, Mapping, Optional


@dataclass(frozen=True)
class SpamConfig:
    enabled: bool
    window_seconds: float
    max_payloads: int
    warn_cooldown_seconds: float
    exclude_plugins: tuple[str, ...]


def _coerce_positive_float(value: Any, fallback: float, *, minimum: float = 0.1) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    if numeric < minimum:
        return fallback
    return float(numeric)


def _coerce_positive_int(value: Any, fallback: int, *, minimum: int = 1) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return fallback
    if numeric < minimum:
        return fallback
    return numeric


def parse_spam_config(raw: Any, defaults: Mapping[str, Any]) -> SpamConfig:
    default_enabled = bool(defaults.get("enabled", False))
    default_window = _coerce_positive_float(defaults.get("window_seconds"), 2.0)
    default_max = _coerce_positive_int(defaults.get("max_payloads_per_window"), 200)
    default_cooldown = _coerce_positive_float(defaults.get("warn_cooldown_seconds"), 30.0, minimum=0.0)
    default_excludes_raw = defaults.get("exclude_plugins")
    default_excludes: tuple[str, ...] = ()
    if isinstance(default_excludes_raw, (list, tuple, set)):
        default_excludes = tuple(
            item.strip().lower()
            for item in (str(value) for value in default_excludes_raw)
            if item.strip()
        )

    if not isinstance(raw, Mapping):
        return SpamConfig(
            enabled=default_enabled,
            window_seconds=default_window,
            max_payloads=default_max,
            warn_cooldown_seconds=default_cooldown,
            exclude_plugins=default_excludes,
        )

    enabled = default_enabled if "enabled" not in raw else bool(raw.get("enabled"))
    window_seconds = _coerce_positive_float(raw.get("window_seconds"), default_window)
    max_payloads = _coerce_positive_int(raw.get("max_payloads_per_window"), default_max)
    warn_cooldown = _coerce_positive_float(raw.get("warn_cooldown_seconds"), default_cooldown, minimum=0.0)
    excludes: tuple[str, ...] = default_excludes
    raw_excludes = raw.get("exclude_plugins")
    if isinstance(raw_excludes, (list, tuple, set)):
        excludes = tuple(
            item.strip().lower() for item in (str(value) for value in raw_excludes) if item.strip()
        )
    return SpamConfig(
        enabled=enabled,
        window_seconds=window_seconds,
        max_payloads=max_payloads,
        warn_cooldown_seconds=warn_cooldown,
        exclude_plugins=excludes,
    )


def build_spam_detection_updates(
    *,
    enabled: bool,
    window_seconds: float,
    max_payloads: int,
    warn_cooldown_seconds: float,
    defaults: Mapping[str, Any],
) -> tuple[SpamConfig, dict[str, Any]]:
    spam_config = parse_spam_config(
        {
            "enabled": enabled,
            "window_seconds": window_seconds,
            "max_payloads_per_window": max_payloads,
            "warn_cooldown_seconds": warn_cooldown_seconds,
        },
        defaults,
    )
    updates = {
        "enabled": spam_config.enabled,
        "window_seconds": spam_config.window_seconds,
        "max_payloads_per_window": spam_config.max_payloads,
        "warn_cooldown_seconds": spam_config.warn_cooldown_seconds,
    }
    return spam_config, updates


class PayloadSpamTracker:
    """Track per-plugin payload rates and emit throttled warnings when exceeded."""

    def __init__(self, warn_fn: Callable[[str], None]) -> None:
        self._warn_fn = warn_fn
        self._lock = threading.Lock()
        self._enabled = False
        self._window_seconds = 2.0
        self._max_payloads = 200
        self._warn_cooldown = 30.0
        self._exclude_plugins: set[str] = set()
        self._events: dict[str, deque[float]] = {}
        self._last_warned: dict[str, float] = {}

    def configure(self, config: SpamConfig) -> None:
        with self._lock:
            self._enabled = bool(config.enabled)
            self._window_seconds = max(float(config.window_seconds), 0.1)
            self._max_payloads = max(int(config.max_payloads), 1)
            self._warn_cooldown = max(float(config.warn_cooldown_seconds), 0.0)
            self._exclude_plugins = set(config.exclude_plugins)
            if not self._enabled:
                self._events.clear()
                self._last_warned.clear()

    def record(self, plugin_name: Optional[str], *, now: Optional[float] = None) -> None:
        if not self._enabled:
            return
        if not plugin_name:
            return
        name = str(plugin_name).strip()
        if not name:
            return
        key = name.lower()
        if key in self._exclude_plugins:
            return
        timestamp = time.monotonic() if now is None else float(now)
        with self._lock:
            if not self._enabled:
                return
            events = self._events.setdefault(key, deque())
            cutoff = timestamp - self._window_seconds
            while events and events[0] < cutoff:
                events.popleft()
            events.append(timestamp)
            count = len(events)
            if count <= self._max_payloads:
                return
            last_warned = self._last_warned.get(key)
            if last_warned is not None and (timestamp - last_warned) < self._warn_cooldown:
                return
            self._last_warned[key] = timestamp
        self._warn_fn(
            "Overlay payload spam detected: plugin=%s count=%d window=%.1fs limit=%d",
            name,
            count,
            self._window_seconds,
            self._max_payloads,
        )
