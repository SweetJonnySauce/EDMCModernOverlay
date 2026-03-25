from __future__ import annotations

import json
import socket
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Optional

JsonDict = dict[str, Any]
ConnectFn = Callable[[tuple[str, int], float], object]
LogFn = Callable[[str], None]


def _noop_log(message: str) -> None:
    return None


class PluginBridge:
    """Thin helper for controller-to-plugin CLI messaging and related signals."""

    def __init__(
        self,
        *,
        root: Path,
        port_path: Optional[Path] = None,
        connect: Optional[ConnectFn] = None,
        logger: Optional[LogFn] = None,
        time_source: Callable[[], float] = time.time,
    ) -> None:
        self._root = root
        self._port_path = port_path or (root / "port.json")
        self._connect = connect or socket.create_connection
        self._log = logger or _noop_log
        self._time = time_source
        self._force_render_override = ForceRenderOverrideManager(
            port_path=self._port_path,
            connect=self._connect,
            logger=self._log,
            time_source=self._time,
        )
        self._last_active_group: tuple[str, str, str] | None = None
        self._last_override_reload_nonce: Optional[str] = None

    @property
    def force_render_override(self) -> "ForceRenderOverrideManager":
        return self._force_render_override

    def read_port(self) -> Optional[int]:
        try:
            data = json.loads(self._port_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
        port = data.get("port")
        if not isinstance(port, int) or port <= 0:
            return None
        return port

    def send_cli(self, payload: JsonDict) -> bool:
        port = self.read_port()
        if port is None:
            return False
        try:
            with self._connect(("127.0.0.1", port), timeout=1.5) as sock:
                writer = sock.makefile("w", encoding="utf-8", newline="\n")
                writer.write(json.dumps(payload, ensure_ascii=False))
                writer.write("\n")
                writer.flush()
            return True
        except Exception:
            return False

    def request_cli(self, payload: JsonDict, *, timeout: float = 1.5) -> Optional[JsonDict]:
        port = self.read_port()
        if port is None:
            return None
        try:
            with self._connect(("127.0.0.1", port), timeout=timeout) as sock:
                try:
                    sock.settimeout(timeout)
                except Exception:
                    pass
                writer = sock.makefile("w", encoding="utf-8", newline="\n")
                reader = sock.makefile("r", encoding="utf-8")
                writer.write(json.dumps(payload, ensure_ascii=False))
                writer.write("\n")
                writer.flush()
                while True:
                    response_line = reader.readline()
                    if not response_line:
                        return None
                    try:
                        response = json.loads(response_line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(response, dict) and "status" in response:
                        return response
        except Exception:
            return None

    def plugin_group_status(self) -> Optional[JsonDict]:
        return self.request_cli({"cli": "plugin_group_status"})

    def set_plugin_group_enabled(self, enabled: bool, *, group_name: Optional[str] = None) -> Optional[JsonDict]:
        payload: JsonDict = {"cli": "plugin_group_set", "enabled": bool(enabled)}
        if group_name:
            payload["plugin_group"] = group_name
        return self.request_cli(payload)

    def toggle_plugin_group(self, *, group_name: Optional[str] = None) -> Optional[JsonDict]:
        payload: JsonDict = {"cli": "plugin_group_toggle"}
        if group_name:
            payload["plugin_group"] = group_name
        return self.request_cli(payload)

    def reset_plugin_group_to_default(self, *, group_name: Optional[str] = None) -> Optional[JsonDict]:
        payload: JsonDict = {"cli": "plugin_group_reset_default"}
        if group_name:
            payload["plugin_group"] = group_name
        return self.request_cli(payload)

    def send_heartbeat(self) -> bool:
        return self.send_cli({"cli": "controller_heartbeat"})

    def profile_status(self) -> Optional[JsonDict]:
        return self.request_cli({"cli": "profile_status"})

    def set_profile(self, profile_name: str) -> Optional[JsonDict]:
        token = str(profile_name or "").strip()
        if not token:
            return None
        return self.request_cli({"cli": "profile_set", "profile": token})

    def create_profile(self, profile_name: str) -> Optional[JsonDict]:
        token = str(profile_name or "").strip()
        if not token:
            return None
        return self.request_cli({"cli": "profile_create", "profile": token})

    def clone_profile(self, source_profile: str, new_profile: str) -> Optional[JsonDict]:
        source_token = str(source_profile or "").strip()
        target_token = str(new_profile or "").strip()
        if not source_token or not target_token:
            return None
        return self.request_cli(
            {"cli": "profile_clone", "source_profile": source_token, "new_profile": target_token}
        )

    def rename_profile(self, old_name: str, new_name: str) -> Optional[JsonDict]:
        old_token = str(old_name or "").strip()
        new_token = str(new_name or "").strip()
        if not old_token or not new_token:
            return None
        return self.request_cli({"cli": "profile_rename", "old_profile": old_token, "new_profile": new_token})

    def delete_profile(self, profile_name: str) -> Optional[JsonDict]:
        token = str(profile_name or "").strip()
        if not token:
            return None
        return self.request_cli({"cli": "profile_delete", "profile": token})

    def reorder_profile(self, profile_name: str, target_index: int) -> Optional[JsonDict]:
        token = str(profile_name or "").strip()
        if not token:
            return None
        return self.request_cli({"cli": "profile_reorder", "profile": token, "target_index": int(target_index)})

    def set_profile_rules(self, profile_name: str, rules: list[dict[str, Any]]) -> Optional[JsonDict]:
        token = str(profile_name or "").strip()
        if not token:
            return None
        return self.request_cli({"cli": "profile_set_rules", "profile": token, "rules": list(rules)})

    def send_active_group(
        self,
        plugin: Optional[str],
        label: Optional[str],
        *,
        anchor: Optional[str] = None,
        edit_nonce: str = "",
    ) -> bool:
        plugin_name = (plugin or "").strip()
        group_label = (label or "").strip()
        anchor_token = (anchor or "").strip().lower()
        key = (plugin_name, group_label, anchor_token)
        if key == self._last_active_group:
            return False
        payload = {
            "cli": "controller_active_group",
            "plugin": plugin_name,
            "label": group_label,
            "anchor": anchor_token,
            "edit_nonce": edit_nonce,
        }
        sent = self.send_cli(payload)
        if sent:
            self._last_active_group = key
        return sent

    def reset_active_group_cache(self) -> None:
        self._last_active_group = None

    def emit_override_reload(
        self,
        *,
        nonce: str,
        edit_nonce: str = "",
        timestamp: Optional[float] = None,
        dedupe: bool = True,
    ) -> bool:
        if dedupe and nonce and nonce == self._last_override_reload_nonce:
            return False
        payload = {
            "cli": "controller_override_reload",
            "nonce": nonce,
            "edit_nonce": edit_nonce,
            "timestamp": self._time() if timestamp is None else timestamp,
        }
        sent = self.send_cli(payload)
        if sent:
            self._last_override_reload_nonce = nonce
        return sent


class ForceRenderOverrideManager:
    """Manages temporary force-render overrides while the controller is open."""

    def __init__(
        self,
        *,
        port_path: Path,
        connect: Optional[ConnectFn] = None,
        logger: Optional[LogFn] = None,
        time_source: Callable[[], float] = time.monotonic,
    ) -> None:
        self._port_path = port_path
        self._connect = connect or socket.create_connection
        self._logger = logger or _noop_log
        self._time = time_source
        self._active = False

    def activate(self) -> None:
        if self._active:
            return
        response = self._send_override({"cli": "force_render_override", "force_render": True})
        if response is None:
            self._safe_log("Overlay CLI unavailable while enabling force-render override.")
        self._active = True

    def deactivate(self) -> None:
        if not self._active:
            return
        response = self._send_override({"cli": "force_render_override", "force_render": False})
        if response is None:
            self._safe_log("Overlay CLI unavailable while disabling force-render override.")
        self._active = False

    def _send_override(self, payload: JsonDict) -> Optional[JsonDict]:
        port = self._load_port()
        if port is None:
            return None
        message = json.dumps(payload, ensure_ascii=False)
        try:
            with self._connect(("127.0.0.1", port), timeout=2.0) as sock:
                try:
                    sock.settimeout(2.0)
                except Exception:
                    pass
                writer = sock.makefile("w", encoding="utf-8", newline="\n")
                reader = sock.makefile("r", encoding="utf-8")
                writer.write(message)
                writer.write("\n")
                writer.flush()
                deadline = self._time() + 2.0
                while self._time() < deadline:
                    line = reader.readline()
                    if not line:
                        break
                    try:
                        response = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(response, dict):
                        status = response.get("status")
                        if status == "ok":
                            return response
                        if status == "error":
                            error_msg = response.get("error")
                            if error_msg:
                                self._safe_log(f"Overlay client rejected force-render override: {error_msg}")
                            return None
        except OSError:
            return None
        except Exception:
            traceback.print_exc(file=sys.stderr)
            return None
        return None

    def _load_port(self) -> Optional[int]:
        try:
            data = json.loads(self._port_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
        port = data.get("port")
        if not isinstance(port, int) or port <= 0:
            return None
        return port

    def _safe_log(self, message: str) -> None:
        try:
            self._logger(message)
        except Exception:
            print(f"[overlay-controller] {message}", file=sys.stderr)
