"""Plugin scan helper for reporting overlay-enabled status."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence, Tuple

from . import plugin_scan

UTC = getattr(datetime, "UTC", timezone.utc)


@dataclass(frozen=True)
class PluginStatus:
    name: str
    status: str


class PluginScanService:
    def __init__(
        self,
        *,
        plugin_dir: Path,
        send_overlay_message: Callable[[Mapping[str, object]], bool],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._plugin_dir = Path(plugin_dir)
        self._send_overlay_message = send_overlay_message
        self._logger = logger or logging.getLogger("EDMC.ModernOverlay.PluginScanService")

    def report_plugins(self) -> None:
        plugins_root = self._plugin_dir.resolve().parent
        plugins = plugin_scan.scan_plugins(plugins_root, include_disabled=False, self_root=self._plugin_dir)
        known_plugins = plugin_scan.load_known_plugins()
        ignored = 0
        for plugin in plugins:
            spec, _matched = _match_known_spec(plugin.name, known_plugins)
            if _is_ignored_spec(spec):
                ignored += 1
        self._logger.info(
            "Plugin scan: root=%s plugins=%d ignored=%d",
            plugins_root,
            len(plugins),
            ignored,
        )
        if not plugins:
            self._logger.info("Plugin scan: no plugins found (load.py not detected).")
            header_size = "large"
            header_height = _line_height_for_size(header_size)
            red_start = header_height + (_line_height_for_size("normal") * 2)
            self._display_status_message(
                ["No plugins found"],
                color="#ffffff",
                ttl_seconds=10,
                size=header_size,
            )
            self._display_status_message(
                [
                    "EDMCModernOverlay needs at least one other plugin",
                    "with Overlay support to display in-game messages",
                ],
                color="#ff0000",
                ttl_seconds=10,
                y_offset_pixels=red_start,
            )
            return
        if not known_plugins:
            self._logger.info("Plugin scan: no known overlay config entries loaded from %s", plugin_scan.KNOWN_PLUGINS_PATH)

        known_count = 0
        for plugin in plugins:
            spec, _matched = _match_known_spec(plugin.name, known_plugins)
            if _has_known_overlay_support(spec):
                known_count += 1

        statuses: list[PluginStatus] = []
        for plugin in plugins:
            spec, matched_key = _match_known_spec(plugin.name, known_plugins)
            if _is_ignored_spec(spec):
                status, config_key, raw_value = "ignored", None, None
                self._logger.info("Plugin scan: %s overlay=%s path=%s", plugin.name, status, plugin.path)
            elif spec is None:
                status, config_key, raw_value = "unknown", None, None
                self._logger.info("Plugin scan: %s overlay=%s path=%s", plugin.name, status, plugin.path)
            else:
                status, config_key, raw_value = plugin_scan.evaluate_overlay_status(
                    plugin.name,
                    {plugin.name.casefold(): spec},
                )
                if status == "unknown":
                    self._logger.info("Plugin scan: %s overlay=%s path=%s", plugin.name, status, plugin.path)
                else:
                    self._logger.info(
                        "Plugin scan: %s overlay=%s key=%s value=%r path=%s",
                        plugin.name,
                        status,
                        config_key,
                        raw_value,
                        plugin.path,
                    )
            statuses.append(PluginStatus(name=plugin.name, status=status))

        if statuses:
            header = f"{len(plugins)} plugins found"
            header_size = "huge"
            header_height = _line_height_for_size(header_size)
            large_height = _line_height_for_size("large")
            list_start = header_height + (2 * large_height)
            self._display_status_message([header], color="#ffffff", ttl_seconds=10, size=header_size)
            self._display_status_message(
                [f"Total plugins: {len(plugins)}"],
                color="#ffffff",
                ttl_seconds=10,
                size="large",
                y_offset_pixels=header_height,
            )
            self._display_status_message(
                [f"Ignored plugins: {ignored}"],
                color="#ffffff",
                ttl_seconds=10,
                size="large",
                y_offset_pixels=header_height + large_height,
            )
            lines = [f"{entry.name}: {entry.status}" for entry in statuses]
            self._display_status_message(
                lines,
                color="#ffffff",
                ttl_seconds=10,
                y_offset_pixels=list_start,
            )

    def _display_status_message(
        self,
        lines: Sequence[str],
        *,
        color: str,
        ttl_seconds: int,
        y_offset_lines: int = 0,
        y_offset_pixels: int = 0,
        size: str = "normal",
    ) -> None:
        if not lines:
            return
        size_token = str(size or "normal").lower()
        line_height = _line_height_for_size(size_token)
        start_x = 0
        start_y = 0 + (y_offset_lines * line_height) + y_offset_pixels
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
        for index, text in enumerate(lines):
            safe_text = str(text)
            x_pos = start_x
            y_pos = max(0, int(round(start_y + (index * line_height))))
            payload = {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": "LegacyOverlay",
                "type": "message",
                "id": f"EDMCModernOverlay-plugin-status-{timestamp}-{index}",
                "text": safe_text,
                "color": color,
                "x": x_pos,
                "y": y_pos,
                "ttl": int(ttl_seconds),
                "size": size_token,
            }
            if not self._send_overlay_message(payload):
                self._logger.debug("Failed to send plugin status overlay message: %s", safe_text)


_DEFAULT_SERVICE: Optional[PluginScanService] = None


def _is_ignored_spec(spec: Optional[Mapping[str, object]]) -> bool:
    if not spec:
        return False
    flag = spec.get("ignore")
    if isinstance(flag, bool):
        return flag
    if isinstance(flag, str):
        return flag.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _has_known_overlay_support(spec: Optional[Mapping[str, object]]) -> bool:
    if not spec or _is_ignored_spec(spec):
        return False
    key = spec.get("config_key")
    return isinstance(key, str) and bool(key.strip())


def _match_known_spec(
    plugin_name: str,
    known_plugins: Mapping[str, Mapping[str, object]],
) -> Tuple[Optional[Mapping[str, object]], Optional[str]]:
    if not plugin_name:
        return None, None
    key = plugin_name.casefold()
    spec = known_plugins.get(key)
    if spec is not None:
        return spec, key
    best_key: Optional[str] = None
    best_spec: Optional[Mapping[str, object]] = None

    for canonical_key, spec in known_plugins.items():
        if not isinstance(canonical_key, str):
            continue
        candidates = [canonical_key]
        aliases = spec.get("aliases") if isinstance(spec, Mapping) else None
        if isinstance(aliases, list):
            for alias in aliases:
                if isinstance(alias, str) and alias.strip():
                    candidates.append(alias.casefold())
        for candidate in candidates:
            if key == candidate:
                return spec, canonical_key
            if key.startswith(candidate):
                if best_key is None or len(candidate) > len(best_key):
                    best_key = candidate
                    best_spec = spec
    if best_spec is None:
        return None, None
    return best_spec, best_key


def _line_height_for_size(size: str) -> int:
    token = str(size or "normal").lower()
    if token == "huge":
        return 28
    if token == "large":
        return 20
    if token == "small":
        return 12
    return 16


def _default_plugin_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_send_overlay_message(payload: Mapping[str, object]) -> bool:
    try:
        from .overlay_api import send_overlay_message
    except Exception:
        return False
    return bool(send_overlay_message(payload))


def default_service() -> PluginScanService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = PluginScanService(
            plugin_dir=_default_plugin_dir(),
            send_overlay_message=_default_send_overlay_message,
            logger=logging.getLogger("EDMC.ModernOverlay.PluginScan"),
        )
    return _DEFAULT_SERVICE


def report_plugins() -> None:
    """Entry point used by chat commands (uses default service)."""
    default_service().report_plugins()
