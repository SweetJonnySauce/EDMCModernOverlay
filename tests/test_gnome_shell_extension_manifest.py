from __future__ import annotations

import json
import re
from pathlib import Path

from overlay_client.backend import (
    GNOME_SHELL_HELPER_CAPABILITIES,
    GNOME_SHELL_HELPER_DBUS_HEALTH_METHOD,
    GNOME_SHELL_HELPER_DBUS_HELLO_METHOD,
    GNOME_SHELL_HELPER_DBUS_INTERFACE,
    GNOME_SHELL_HELPER_DBUS_OBJECT_PATH,
    GNOME_SHELL_HELPER_DBUS_PRESENTATION_METHOD,
    GNOME_SHELL_HELPER_DBUS_SERVICE,
    GNOME_SHELL_HELPER_DBUS_TARGET_METHOD,
    GNOME_SHELL_HELPER_COORDINATE_SPACE,
    GNOME_SHELL_HELPER_SHELL_VERSIONS,
    GNOME_SHELL_HELPER_UUID,
    HELPER_KIND,
    HELPER_PROTOCOL,
    HELPER_VERSION,
)

ROOT = Path(__file__).resolve().parent.parent
HELPER_DIR = ROOT / "helpers" / "gnome_shell_extension"
CONTRACT_FIXTURE = ROOT / "tests" / "fixtures" / "gnome_shell_helper_contract_v3.json"


def _metadata() -> dict[str, object]:
    return json.loads((HELPER_DIR / "metadata.json").read_text(encoding="utf-8"))


def _js_constant(name: str) -> str:
    source = (HELPER_DIR / "constants.js").read_text(encoding="utf-8")
    match = re.search(rf"export const {re.escape(name)} = (.+?);", source)
    assert match is not None, f"{name} missing from constants.js"
    return match.group(1).strip().strip("'\"")


def test_gnome_shell_extension_metadata_is_valid_and_fixed_uuid() -> None:
    metadata = _metadata()

    assert metadata["uuid"] == GNOME_SHELL_HELPER_UUID
    assert metadata["name"] == "EDMC Modern Overlay Helper"
    assert isinstance(metadata["description"], str)
    assert metadata["shell-version"] == list(GNOME_SHELL_HELPER_SHELL_VERSIONS)
    assert metadata["version"] == HELPER_PROTOCOL


def test_gnome_shell_extension_supports_explicit_gnome_46_to_50_range() -> None:
    versions = _metadata()["shell-version"]

    assert versions == ["46", "47", "48", "49", "50"]


def test_gnome_shell_extension_package_contents_are_allowlisted() -> None:
    files = {path.name for path in HELPER_DIR.iterdir() if path.is_file()}

    assert files == {"constants.js", "extension.js", "metadata.json"}


def test_gnome_shell_extension_constants_match_client_contract() -> None:
    assert _js_constant("HELPER_UUID") == GNOME_SHELL_HELPER_UUID
    assert _js_constant("HELPER_KIND") == HELPER_KIND.value
    assert int(_js_constant("HELPER_PROTOCOL")) == HELPER_PROTOCOL
    assert _js_constant("HELPER_VERSION") == HELPER_VERSION
    assert _js_constant("HELPER_DBUS_SERVICE") == GNOME_SHELL_HELPER_DBUS_SERVICE
    assert _js_constant("HELPER_DBUS_OBJECT_PATH") == GNOME_SHELL_HELPER_DBUS_OBJECT_PATH
    assert _js_constant("HELPER_DBUS_INTERFACE") == GNOME_SHELL_HELPER_DBUS_INTERFACE
    assert _js_constant("HELPER_DBUS_HELLO_METHOD") == GNOME_SHELL_HELPER_DBUS_HELLO_METHOD
    assert _js_constant("HELPER_DBUS_HEALTH_METHOD") == GNOME_SHELL_HELPER_DBUS_HEALTH_METHOD
    assert _js_constant("HELPER_DBUS_TARGET_METHOD") == GNOME_SHELL_HELPER_DBUS_TARGET_METHOD
    assert _js_constant("HELPER_DBUS_PRESENTATION_METHOD") == GNOME_SHELL_HELPER_DBUS_PRESENTATION_METHOD
    assert _js_constant("HELPER_COORDINATE_SPACE") == GNOME_SHELL_HELPER_COORDINATE_SPACE


def test_gnome_shell_extension_capabilities_match_client_contract() -> None:
    source = (HELPER_DIR / "constants.js").read_text(encoding="utf-8")

    for capability in GNOME_SHELL_HELPER_CAPABILITIES:
        assert f"'{capability}'" in source


def test_gnome_shell_extension_declares_dev_mode_feature_gate_constants() -> None:
    source = (HELPER_DIR / "constants.js").read_text(encoding="utf-8")

    assert "HELPER_DEV_MODE_CONFIG_DIR = 'EDMCModernOverlay'" in source
    assert "HELPER_DEV_MODE_CONFIG_FILE = 'gnome_helper_dev_mode.json'" in source
    assert "HELPER_DEV_MODE_DEFAULT = 'full_helper'" in source
    for mode in (
        "lifecycle_only",
        "dbus_health_only",
        "target_query_enabled",
        "overview_hooks_enabled",
        "raster_code_enabled_no_actor",
        "raster_actor_enabled",
        "full_helper",
    ):
        assert f"'{mode}'" in source


def test_extension_source_exposes_health_target_and_presentation_dbus_runtime() -> None:
    source = (HELPER_DIR / "extension.js").read_text(encoding="utf-8")

    assert "from './constants.js'" in source
    assert "Gio.bus_own_name" in source
    assert "Gio.DBusExportedObject.wrapJSObject" in source
    assert "HELPER_DBUS_SERVICE" in source
    assert "HELPER_DBUS_OBJECT_PATH" in source
    assert "HELPER_DBUS_INTERFACE" in source
    assert "HELPER_DBUS_HELLO_METHOD" in source
    assert "HELPER_DBUS_HEALTH_METHOD" in source
    assert "HELPER_DBUS_TARGET_METHOD" in source
    assert "HELPER_DBUS_PRESENTATION_METHOD" in source
    assert "GetTargetState" in source
    assert "ApplyPresentation" in source
    assert "get_window_actors" in source
    assert "move_resize_frame" in source
    assert "make_above" in source
    assert "global.display" in source
    assert "Meta.Window" not in source


def test_extension_source_uses_displayconfig_monitor_inventory_with_legacy_fallback() -> None:
    source = (HELPER_DIR / "extension.js").read_text(encoding="utf-8")

    assert "org.gnome.Mutter.DisplayConfig" in source
    assert "GetCurrentState" in source
    assert "Gio.DBus.session.call_sync" in source
    assert "DISPLAY_CONFIG_MONITOR_CACHE_TTL_US" in source
    assert "_displayConfigMonitorForIndex" in source
    assert "_parseDisplayConfigMonitors" in source
    assert "_legacyMonitorForIndex" in source
    assert "return this._legacyMonitorForIndex(index) || this._displayConfigMonitorForIndex(index);" in source
    assert "global.display.get_monitor_geometry" in source
    assert "monitorRect" in source
    assert "outputName" in source
    assert "monitorScale" in source


def test_protocol_bump_fixture_tracks_contract_review_triggers() -> None:
    fixture = json.loads(CONTRACT_FIXTURE.read_text(encoding="utf-8"))

    assert fixture["helper_kind"] == HELPER_KIND.value
    assert fixture["helper_protocol"] == HELPER_PROTOCOL
    assert fixture["helper_version_source"] == "version.__version__"
    assert "GetTargetState DBus method" in fixture["added_contracts"]
    assert "ApplyPresentation DBus method" in fixture["added_contracts"]
    triggers = fixture["protocol_bump_required_when"]
    assert isinstance(triggers, list)
    assert len(triggers) >= 4
    assert any("DBus" in trigger for trigger in triggers)
    assert any("Target geometry" in trigger for trigger in triggers)
