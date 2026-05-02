"""Helpers for responding to in-game chat commands.

The overlay plugin does not receive keyboard/mouse focus while Elite Dangerous
is running, so the only ergonomic way to trigger quick actions while playing is
through Elite's chat system. This module mirrors the pattern used by plugins
like EDR: watch for ``SendText`` journal events authored by the local CMDR,
carve out a small namespace of bang-prefixed commands (``!ovr …``), and
translate them into overlay actions.

Only a couple of workflow-driven commands are implemented for now. Handling the
parsing in a helper keeps :mod:`load.py` from accumulating even more logic and
provides a focused surface for future additions.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import shlex
from typing import Any, Callable, Mapping, Optional, Sequence

from .plugin_scan_services import report_plugins as default_report_plugins


_LOGGER = logging.getLogger("EDMC.ModernOverlay.Commands")
_HIDDEN_STATUS_GROUP_PREFIXES = ("edmcmodernoverlay ",)


@dataclass
class _OverlayCommandContext:
    """Lightweight indirection that exposes just the callbacks we need."""

    send_message: Callable[[str], None]
    launch_controller: Optional[Callable[[], None]] = None
    report_plugins: Optional[Callable[[], None]] = None
    set_opacity: Optional[Callable[[int], None]] = None
    set_group_enabled: Optional[Callable[..., Mapping[str, Any]]] = None
    toggle_group_enabled: Optional[Callable[..., Mapping[str, Any]]] = None
    group_status_lines: Optional[Callable[[], Sequence[str]]] = None
    send_group_status_overlay: Optional[Callable[[Sequence[str]], None]] = None
    test_overlay: Optional[Callable[[], None]] = None
    set_profile: Optional[Callable[[str], Mapping[str, Any]]] = None
    cycle_profile: Optional[Callable[[int], Mapping[str, Any]]] = None
    profile_status: Optional[Callable[[], Mapping[str, Any]]] = None
    send_profile_status_overlay: Optional[Callable[[Sequence[str], str], None]] = None


def _normalise_prefix(value: str) -> str:
    text = (value or "").strip()
    if not text.startswith("!"):
        text = "!" + text
    return text.lower()


def _normalise_toggle_argument(value: Optional[str]) -> str:
    text = (value or "").strip()
    if not text:
        return "t"
    return text.lower()


def _parse_opacity_argument(value: str) -> Optional[int]:
    text = (value or "").strip()
    if not text:
        return None
    if text.endswith("%"):
        text = text[:-1].strip()
        if not text:
            return None
    if not text.isdigit():
        return None
    opacity = int(text)
    if 0 <= opacity <= 100:
        return opacity
    return None


def _parse_opacity_token(value: str) -> tuple[Optional[int], bool]:
    text = (value or "").strip()
    if not text:
        return None, False
    had_percent = text.endswith("%")
    if had_percent:
        text = text[:-1].strip()
        if not text:
            return None, True
    if text.isdigit():
        opacity = int(text)
        if 0 <= opacity <= 100:
            return opacity, False
        return None, True
    if had_percent:
        return None, True
    return None, False


def _filter_status_lines(lines: Sequence[str]) -> list[str]:
    visible: list[str] = []
    for line in lines:
        rendered = str(line)
        group_name = rendered.split(":", 1)[0].strip().casefold()
        if any(group_name.startswith(prefix) for prefix in _HIDDEN_STATUS_GROUP_PREFIXES):
            continue
        visible.append(rendered)
    return visible


class JournalCommandHelper:
    """Parse journal ``SendText`` events and dispatch overlay commands."""

    def __init__(
        self,
        context: _OverlayCommandContext,
        command_prefix: str,
        *,
        toggle_argument: Optional[str] = None,
        legacy_prefixes: Optional[list[str]] = None,
    ) -> None:
        self._ctx = context
        primary = _normalise_prefix(command_prefix or "!ovr")
        extras = [p for p in (legacy_prefixes or []) if p]
        self._prefixes = [primary] + [p for p in (_normalise_prefix(p) for p in extras) if p != primary]
        _LOGGER.debug("Configured overlay command prefixes: %s", ", ".join(self._prefixes))
        help_prefix = self._prefixes[0]
        self._toggle_argument = _normalise_toggle_argument(toggle_argument)
        self._help_text = (
            f"Overlay commands: {help_prefix} (launch controller), {help_prefix} {self._toggle_argument} "
            f"(toggle overlay), {help_prefix} on|off [\"plugin group\"], {help_prefix} status, "
            f"{help_prefix} profile <name>|next|prev, {help_prefix} profile status, "
            f"{help_prefix} next|prev, {help_prefix} profiles, "
            f"{help_prefix} test (show test logo), {help_prefix} plugins (log installed plugins), "
            f"{help_prefix} help"
        )

    # Public API ---------------------------------------------------------

    def handle_entry(self, entry: Mapping[str, object]) -> bool:
        """Attempt to process a ``SendText`` journal entry.

        Returns ``True`` when the entry contained a supported overlay command.
        """

        if (entry.get("event") or "").lower() != "sendtext":
            return False
        raw_message = entry.get("Message")
        if not isinstance(raw_message, str):
            return False
        message = raw_message.strip()
        message_lower = message.lower()
        for prefix in self._prefixes:
            if not message_lower.startswith(prefix):
                continue
            _LOGGER.debug("Overlay command candidate matched prefix=%s (active prefixes=%s)", prefix, ", ".join(self._prefixes))
            content = message[len(prefix) :].strip()
            if content:
                try:
                    tokens = shlex.split(content)
                except ValueError:
                    tokens = content.split()
            else:
                tokens = []
            handled = self._handle_overlay_command(tokens)
            if handled:
                _LOGGER.debug("Handled in-game overlay command (%s): %s", prefix, message)
            return handled
        return False

    # Implementation details --------------------------------------------

    def _handle_overlay_command(self, args: list[str]) -> bool:
        if not args:
            return self._launch_controller()

        action = args[0].lower()
        if action in {"launch", "open", "controller", "config"}:
            return self._launch_controller()
        if action in {"help", "?"}:
            self._emit_help()
            return True
        if action in {"test"}:
            return self._test_overlay()
        if action in {"plugins", "plugin"}:
            return self._report_plugins()
        if action in {"next"}:
            return self._cycle_profile(1)
        if action in {"prev", "previous"}:
            return self._cycle_profile(-1)
        if action in {"profile"}:
            return self._handle_profile_command(args[1:])
        if action in {"profiles"}:
            return self._emit_profiles()

        opacity = None
        invalid_opacity = False
        for token in args:
            candidate, invalid = _parse_opacity_token(token)
            if candidate is not None:
                opacity = candidate
                break
            if invalid:
                invalid_opacity = True
        toggle_present = any(token.lower() == self._toggle_argument for token in args)
        if opacity is not None:
            return self._set_opacity(opacity)
        if invalid_opacity and toggle_present:
            _LOGGER.debug("Ignoring toggle command due to invalid opacity token: %s", " ".join(args))
            return True

        parsed_action = self._parse_group_action(args)
        if parsed_action is not None:
            action_name, targets = parsed_action
            if action_name == "status":
                return self._emit_group_status()
            if action_name == "toggle":
                return self._toggle_group_enabled(targets)
            if action_name == "on":
                return self._set_group_enabled(True, targets)
            if action_name == "off":
                return self._set_group_enabled(False, targets)
        elif toggle_present:
            return self._toggle_group_enabled(None)

        _LOGGER.debug("Ignoring unknown overlay command: %s", action)
        return True

    def _handle_profile_command(self, args: list[str]) -> bool:
        if not args:
            self._ctx.send_message("Usage: profile <name> | profile next | profile prev | profile status")
            return True
        action = args[0].lower()
        if action == "next":
            return self._cycle_profile(1)
        if action in {"prev", "previous"}:
            return self._cycle_profile(-1)
        if args[0].lower() in {"status", "list", "ls"}:
            return self._emit_profiles()
        profile_name = " ".join(str(token) for token in args).strip()
        if not profile_name:
            self._ctx.send_message("Profile name is required.")
            return True
        callback = self._ctx.set_profile
        if callback is None:
            self._ctx.send_message("Overlay profile command unavailable.")
            return True
        try:
            result = callback(profile_name)
        except RuntimeError as exc:
            self._ctx.send_message(f"Profile switch unavailable: {exc}")
            return True
        except Exception as exc:  # pragma: no cover - defensive guard
            _LOGGER.warning("Overlay profile callback failed: %s", exc, exc_info=exc)
            self._ctx.send_message("Profile switch failed; see EDMC log.")
            return True
        current_profile = str(result.get("current_profile") or profile_name).strip()
        self._ctx.send_message(f"Overlay profile set to {current_profile}.")
        return True

    def _cycle_profile(self, direction: int) -> bool:
        callback = self._ctx.cycle_profile
        if callback is None:
            self._ctx.send_message("Overlay profile cycle command unavailable.")
            return True
        try:
            result = callback(int(direction))
        except RuntimeError as exc:
            self._ctx.send_message(f"Profile cycle unavailable: {exc}")
            return True
        except Exception as exc:  # pragma: no cover - defensive guard
            _LOGGER.warning("Overlay profile cycle callback failed: %s", exc, exc_info=exc)
            self._ctx.send_message("Profile cycle failed; see EDMC log.")
            return True
        profile_name = str(result.get("current_profile") or "").strip()
        if profile_name:
            self._ctx.send_message(f"Overlay profile set to {profile_name}.")
        return True

    def _emit_profiles(self) -> bool:
        callback = self._ctx.profile_status
        if callback is None:
            self._ctx.send_message("Overlay profile status unavailable.")
            return True
        try:
            status = callback()
        except RuntimeError as exc:
            self._ctx.send_message(f"Overlay profile status unavailable: {exc}")
            return True
        except Exception as exc:  # pragma: no cover - defensive guard
            _LOGGER.warning("Overlay profile status callback failed: %s", exc, exc_info=exc)
            self._ctx.send_message("Overlay profile status failed; see EDMC log.")
            return True
        profiles_raw = status.get("profiles")
        profiles = [str(item).strip() for item in profiles_raw] if isinstance(profiles_raw, list) else []
        profiles = [item for item in profiles if item]
        current = str(status.get("current_profile") or "").strip()
        overlay_callback = self._ctx.send_profile_status_overlay
        if overlay_callback is not None:
            try:
                overlay_callback(profiles, current)
            except RuntimeError as exc:
                self._ctx.send_message(f"Overlay profile status unavailable: {exc}")
                return True
            except Exception as exc:  # pragma: no cover - defensive guard
                _LOGGER.warning("Overlay profile status overlay callback failed: %s", exc, exc_info=exc)
                self._ctx.send_message("Overlay profile status failed; see EDMC log.")
                return True
            return True
        if not profiles:
            self._ctx.send_message("Overlay profiles: none")
            return True
        rendered: list[str] = []
        for profile_name in profiles:
            if profile_name.casefold() == current.casefold():
                rendered.append(f"[{profile_name}]")
            else:
                rendered.append(profile_name)
        self._ctx.send_message("Overlay profiles: " + ", ".join(rendered))
        return True

    def _report_plugins(self) -> bool:
        callback = self._ctx.report_plugins
        if callback is None:
            self._ctx.send_message("Overlay plugins command unavailable.")
            return True
        try:
            callback()
        except Exception as exc:  # pragma: no cover - defensive guard
            _LOGGER.warning("Overlay plugin scan failed: %s", exc, exc_info=exc)
            self._ctx.send_message("Overlay plugin scan failed; see EDMC log.")
        else:
            self._ctx.send_message("Overlay plugin scan logged to EDMC debug log.")
        return True
    def _emit_help(self) -> None:
        self._ctx.send_message(self._help_text)

    def _set_opacity(self, value: int) -> bool:
        callback = self._ctx.set_opacity
        if callback is None:
            self._ctx.send_message("Overlay opacity command unavailable.")
            return True
        try:
            callback(value)
        except RuntimeError as exc:
            self._ctx.send_message(f"Overlay opacity unavailable: {exc}")
        except Exception as exc:  # pragma: no cover - defensive guard
            _LOGGER.warning("Overlay opacity callback failed: %s", exc)
            self._ctx.send_message("Overlay opacity update failed; see EDMC log.")
        return True

    def _launch_controller(self) -> bool:
        callback = self._ctx.launch_controller
        if callback is None:
            self._ctx.send_message("Overlay Controller command unavailable.")
            return True
        try:
            callback()
        except RuntimeError as exc:
            self._ctx.send_message(f"Overlay Controller launch failed: {exc}")
        except Exception as exc:  # pragma: no cover - defensive guard
            _LOGGER.warning("Overlay Controller callback failed: %s", exc)
            self._ctx.send_message("Overlay Controller launch failed; see EDMC log.")
        return True

    def _set_group_enabled(self, enabled: bool, targets: Optional[list[str]]) -> bool:
        callback = self._ctx.set_group_enabled
        if callback is None:
            self._ctx.send_message("Overlay on/off command unavailable.")
            return True
        action_label = "on" if enabled else "off"
        try:
            callback(enabled, group_names=targets, source=f"chat_{action_label}")
        except RuntimeError as exc:
            self._ctx.send_message(f"Overlay {action_label} unavailable: {exc}")
        except Exception as exc:  # pragma: no cover - defensive guard
            _LOGGER.warning("Overlay %s callback failed: %s", action_label, exc)
            self._ctx.send_message(f"Overlay {action_label} failed; see EDMC log.")
        return True

    def _toggle_group_enabled(self, targets: Optional[list[str]]) -> bool:
        callback = self._ctx.toggle_group_enabled
        if callback is None:
            self._ctx.send_message("Overlay toggle command unavailable.")
            return True
        try:
            callback(group_names=targets, source="chat_toggle")
        except RuntimeError as exc:
            self._ctx.send_message(f"Overlay toggle unavailable: {exc}")
        except Exception as exc:  # pragma: no cover - defensive guard
            _LOGGER.warning("Overlay toggle callback failed: %s", exc)
            self._ctx.send_message("Overlay toggle failed; see EDMC log.")
        return True

    def _emit_group_status(self) -> bool:
        callback = self._ctx.group_status_lines
        if callback is None:
            self._ctx.send_message("Overlay status command unavailable.")
            return True
        try:
            lines = _filter_status_lines(callback())
        except RuntimeError as exc:
            self._ctx.send_message(f"Overlay status unavailable: {exc}")
            return True
        except Exception as exc:  # pragma: no cover - defensive guard
            _LOGGER.warning("Overlay status callback failed: %s", exc)
            self._ctx.send_message("Overlay status failed; see EDMC log.")
            return True
        if not lines:
            self._ctx.send_message("No plugin groups configured.")
            return True
        overlay_callback = self._ctx.send_group_status_overlay
        if overlay_callback is not None:
            try:
                overlay_callback(lines)
            except RuntimeError as exc:
                self._ctx.send_message(f"Overlay status unavailable: {exc}")
            except Exception as exc:  # pragma: no cover - defensive guard
                _LOGGER.warning("Overlay status overlay callback failed: %s", exc)
                self._ctx.send_message("Overlay status failed; see EDMC log.")
            else:
                if _LOGGER.isEnabledFor(logging.DEBUG):
                    for line in lines:
                        _LOGGER.debug("Overlay status line: %s", line)
                return True
        self._ctx.send_message("\n".join(lines))
        if _LOGGER.isEnabledFor(logging.DEBUG):
            for line in lines:
                _LOGGER.debug("Overlay status line: %s", line)
        return True

    def _test_overlay(self) -> bool:
        callback = self._ctx.test_overlay
        if callback is None:
            self._ctx.send_message("Overlay test command unavailable.")
            return True
        try:
            callback()
        except RuntimeError as exc:
            self._ctx.send_message(f"Overlay test failed: {exc}")
        except Exception as exc:  # pragma: no cover - defensive guard
            _LOGGER.warning("Overlay test overlay callback failed: %s", exc)
            self._ctx.send_message("Overlay test failed; see EDMC log.")
        else:
            self._ctx.send_message("Overlay test logo sent.")
        return True

    def _parse_group_action(self, args: list[str]) -> Optional[tuple[str, Optional[list[str]]]]:
        if not args:
            return None
        filtered = [token for token in args if token.lower() != "turn"]
        if not filtered:
            return None

        action_indexes: list[tuple[int, str]] = []
        for index, token in enumerate(filtered):
            lowered = token.lower()
            if lowered == "on":
                action_indexes.append((index, "on"))
                continue
            if lowered == "off":
                action_indexes.append((index, "off"))
                continue
            if lowered == "status":
                action_indexes.append((index, "status"))
                continue
            if lowered in {"toggle", self._toggle_argument}:
                action_indexes.append((index, "toggle"))
                continue
        if not action_indexes:
            return None

        action_names = {name for _idx, name in action_indexes}
        if len(action_names) != 1:
            _LOGGER.debug("Ignoring ambiguous overlay command action tokens: %s", " ".join(args))
            return None
        action_name = action_indexes[0][1]
        if action_name == "status":
            return "status", None

        action_positions = {idx for idx, _name in action_indexes}
        target_tokens = [token for idx, token in enumerate(filtered) if idx not in action_positions]
        if not target_tokens:
            return action_name, None

        target = " ".join(target_tokens).strip()
        if not target:
            return action_name, None
        return action_name, [target]


def build_command_helper(
    plugin_runtime: object,
    logger: Optional[logging.Logger] = None,
    *,
    command_prefix: str = "!ovr",
    toggle_argument: Optional[str] = None,
    legacy_prefixes: Optional[list[str]] = None,
    report_plugins: Optional[Callable[[], None]] = None,
) -> JournalCommandHelper:
    """Construct a :class:`JournalCommandHelper` for the active plugin runtime."""

    log = logger or _LOGGER
    grouped_status_callback = getattr(plugin_runtime, "send_command_status_overlay", None)

    def _send_overlay_message(text: str) -> None:
        if callable(grouped_status_callback):
            try:
                grouped_status_callback(text)
                return
            except Exception as exc:  # pragma: no cover - defensive guard
                log.warning("Failed to send grouped overlay response '%s': %s", text, exc)
        try:
            plugin_runtime.send_test_message(text)
        except Exception as exc:  # pragma: no cover - defensive guard
            log.warning("Failed to send overlay response '%s': %s", text, exc)

    set_profile_callback = getattr(plugin_runtime, "set_current_profile", None)
    _set_profile: Optional[Callable[[str], Mapping[str, Any]]] = None
    if callable(set_profile_callback):
        def _set_profile(name: str) -> Mapping[str, Any]:
            try:
                return set_profile_callback(name, source="chat")
            except TypeError:
                return set_profile_callback(name)

    cycle_profile_callback = getattr(plugin_runtime, "cycle_profile", None)
    _cycle_profile: Optional[Callable[[int], Mapping[str, Any]]] = None
    if callable(cycle_profile_callback):
        def _cycle_profile(direction: int) -> Mapping[str, Any]:
            try:
                return cycle_profile_callback(direction, source="chat")
            except TypeError:
                return cycle_profile_callback(direction)

    report_callback = report_plugins or default_report_plugins
    context = _OverlayCommandContext(
        send_message=_send_overlay_message,
        launch_controller=getattr(plugin_runtime, "launch_overlay_controller", None),
        report_plugins=report_callback,
        set_opacity=getattr(plugin_runtime, "set_payload_opacity_preference", None),
        set_group_enabled=getattr(plugin_runtime, "_set_plugin_groups_enabled", None),
        toggle_group_enabled=getattr(plugin_runtime, "_toggle_plugin_groups_enabled", None),
        group_status_lines=getattr(plugin_runtime, "get_plugin_group_status_lines", None),
        send_group_status_overlay=getattr(plugin_runtime, "send_group_status_overlay", None),
        test_overlay=getattr(plugin_runtime, "send_test_overlay", None),
        set_profile=_set_profile,
        cycle_profile=_cycle_profile,
        profile_status=getattr(plugin_runtime, "get_profile_status", None),
        send_profile_status_overlay=getattr(plugin_runtime, "send_profile_status_overlay", None),
    )
    legacy = legacy_prefixes if legacy_prefixes is not None else []
    if command_prefix in legacy:
        legacy = [p for p in legacy if p != command_prefix]
    return JournalCommandHelper(
        context,
        command_prefix,
        toggle_argument=toggle_argument,
        legacy_prefixes=legacy,
    )
