from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Sequence

from .overlay_api import PluginGroupingError, define_plugin_group
from .status_table_payloads import build_status_table_payloads

_LOGGER = logging.getLogger("EDMC.ModernOverlay.CommandOverlayGroups")

COMMAND_GROUP_PLUGIN_NAME = "EDMCModernOverlay"
COMMAND_GROUP_MATCHING_PREFIXES: tuple[str, ...] = ("modernoverlay-", "edmcmodernoverlay-")

COMMAND_PLUGIN_STATUS_GROUP_NAME = "EDMCModernOverlay Plugin Status"
COMMAND_PLUGIN_STATUS_ID_PREFIX = "edmcmodernoverlay-plugin-status-"

COMMAND_GROUP_STATUS_GROUP_NAME = "EDMCModernOverlay Group Status"
COMMAND_GROUP_STATUS_ID_PREFIX = "edmcmodernoverlay-group-status-"

COMMAND_PROFILE_STATUS_GROUP_NAME = "EDMCModernOverlay Profile Status"
COMMAND_PROFILE_STATUS_ID_PREFIX = "edmcmodernoverlay-profile-status-"
COMMAND_PROFILE_LIST_GROUP_NAME = "EDMCModernOverlay Profile List"
COMMAND_PROFILE_LIST_ID_PREFIX = "edmcmodernoverlay-profile-list-"
COMMAND_STATUS_GROUP_NAME = "EDMCModernOverlay Command Status"
COMMAND_STATUS_ID_PREFIX = "edmcmodernoverlay-command-status-"


@dataclass(frozen=True)
class _CommandGroupDefinition:
    name: str
    prefix: str
    anchor: str
    offset_x: float
    offset_y: float
    payload_justification: str
    marker_label_position: str
    preview_box_mode: str
    background_color: str
    border_color: str
    border_width: int


_COMMAND_GROUP_DEFINITIONS: tuple[_CommandGroupDefinition, ...] = (
    _CommandGroupDefinition(
        name=COMMAND_PLUGIN_STATUS_GROUP_NAME,
        prefix=COMMAND_PLUGIN_STATUS_ID_PREFIX,
        anchor="center",
        offset_x=640.0,
        offset_y=480.0,
        payload_justification="left",
        marker_label_position="below",
        preview_box_mode="last",
        background_color="black",
        border_color="blue",
        border_width=10,
    ),
    _CommandGroupDefinition(
        name=COMMAND_GROUP_STATUS_GROUP_NAME,
        prefix=COMMAND_GROUP_STATUS_ID_PREFIX,
        anchor="center",
        offset_x=640.0,
        offset_y=480.0,
        payload_justification="left",
        marker_label_position="below",
        preview_box_mode="last",
        background_color="black",
        border_color="blue",
        border_width=10,
    ),
    _CommandGroupDefinition(
        name=COMMAND_PROFILE_STATUS_GROUP_NAME,
        prefix=COMMAND_PROFILE_STATUS_ID_PREFIX,
        anchor="nw",
        offset_x=0.0,
        offset_y=0.0,
        payload_justification="left",
        marker_label_position="below",
        preview_box_mode="last",
        background_color="black",
        border_color="black",
        border_width=3,
    ),
    _CommandGroupDefinition(
        name=COMMAND_PROFILE_LIST_GROUP_NAME,
        prefix=COMMAND_PROFILE_LIST_ID_PREFIX,
        anchor="center",
        offset_x=640.0,
        offset_y=480.0,
        payload_justification="left",
        marker_label_position="below",
        preview_box_mode="last",
        background_color="black",
        border_color="blue",
        border_width=10,
    ),
    _CommandGroupDefinition(
        name=COMMAND_STATUS_GROUP_NAME,
        prefix=COMMAND_STATUS_ID_PREFIX,
        anchor="nw",
        offset_x=40.0,
        offset_y=44.0,
        payload_justification="left",
        marker_label_position="below",
        preview_box_mode="last",
        background_color="black",
        border_color="blue",
        border_width=10,
    ),
)


def ensure_runtime_command_groups(*, logger: Optional[logging.Logger] = None) -> bool:
    """Ensure built-in chat command overlay groups exist via the public API."""

    log = logger or _LOGGER
    any_updated = False
    for definition in _COMMAND_GROUP_DEFINITIONS:
        try:
            updated = define_plugin_group(
                plugin_name=COMMAND_GROUP_PLUGIN_NAME,
                plugin_matching_prefixes=COMMAND_GROUP_MATCHING_PREFIXES,
                plugin_group_name=definition.name,
                plugin_group_prefixes=(definition.prefix,),
                plugin_group_anchor=definition.anchor,
                plugin_group_offset_x=definition.offset_x,
                plugin_group_offset_y=definition.offset_y,
                payload_justification=definition.payload_justification,
                marker_label_position=definition.marker_label_position,
                controller_preview_box_mode=definition.preview_box_mode,
                plugin_group_background_color=definition.background_color,
                plugin_group_border_color=definition.border_color,
                plugin_group_border_width=definition.border_width,
            )
        except PluginGroupingError as exc:
            log.warning("Command overlay group setup failed for '%s': %s", definition.name, exc)
            continue
        except Exception as exc:  # pragma: no cover - defensive guard
            log.warning("Unexpected command overlay group setup error for '%s': %s", definition.name, exc, exc_info=exc)
            continue
        any_updated = any_updated or bool(updated)
    return any_updated


def render_group_status_payloads(lines: Sequence[str], *, ttl_seconds: int = 10) -> list[dict[str, object]]:
    """Build true-table LegacyOverlay payloads for `!ovr status` output."""
    return build_status_table_payloads(
        lines,
        id_prefix=COMMAND_GROUP_STATUS_ID_PREFIX,
        ttl_seconds=ttl_seconds,
    )


def _line_height_for_size(size: str) -> int:
    token = str(size or "normal").lower()
    if token == "huge":
        return 28
    if token == "large":
        return 20
    if token == "small":
        return 12
    return 16


def render_profile_list_payloads(
    profiles: Sequence[str],
    *,
    current_profile: str = "",
    ttl_seconds: int = 10,
) -> list[dict[str, object]]:
    """Build vertical LegacyOverlay payloads for `!ovr profiles` output."""
    tokens = [str(item).strip() for item in profiles if str(item).strip()]
    current = str(current_profile or "").strip()
    rendered = [f"[{name}]" if current and name.casefold() == current.casefold() else name for name in tokens]

    header_size = "huge"
    summary_size = "large"
    body_size = "normal"
    header_height = _line_height_for_size(header_size)
    summary_height = _line_height_for_size(summary_size)
    body_height = _line_height_for_size(body_size)

    header_text = "Overlay Profiles"
    if not rendered:
        rendered = ["none"]
    summary_active = f"Active: {current}" if current else "Active: unknown"
    summary_count = f"Profiles: {len(tokens)}"
    list_start = header_height + (2 * summary_height)

    from datetime import datetime, timezone

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    payloads: list[dict[str, object]] = []

    def _message_payload(*, idx: int, text: str, y: int, size: str) -> dict[str, object]:
        return {
            "event": "LegacyOverlay",
            "type": "message",
            "id": f"{COMMAND_PROFILE_LIST_ID_PREFIX}{timestamp}-{idx}",
            "text": str(text),
            "color": "#ffffff",
            "x": 0,
            "y": max(0, int(y)),
            "ttl": int(ttl_seconds),
            "size": str(size),
        }

    payloads.append(_message_payload(idx=0, text=header_text, y=0, size=header_size))
    payloads.append(_message_payload(idx=1, text=summary_active, y=header_height, size=summary_size))
    payloads.append(_message_payload(idx=2, text=summary_count, y=header_height + summary_height, size=summary_size))
    for index, text in enumerate(rendered):
        payloads.append(
            _message_payload(
                idx=3 + index,
                text=text,
                y=list_start + (index * body_height),
                size=body_size,
            )
        )
    return payloads


def render_command_status_payloads(
    message: str,
    *,
    ttl_seconds: int = 6,
    size: str = "large",
) -> list[dict[str, object]]:
    """Build grouped LegacyOverlay payloads for command/status text output."""
    text = str(message or "").strip()
    if not text:
        return []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    line_height = _line_height_for_size(size)

    from datetime import datetime, timezone

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    payloads: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        payloads.append(
            {
                "event": "LegacyOverlay",
                "type": "message",
                "id": f"{COMMAND_STATUS_ID_PREFIX}{timestamp}-{index}",
                "text": line,
                "color": "#ffffff",
                "x": 0,
                "y": index * line_height,
                "ttl": int(ttl_seconds),
                "size": str(size),
            }
        )
    return payloads
