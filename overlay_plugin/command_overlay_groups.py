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
