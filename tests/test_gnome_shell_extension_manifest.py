from __future__ import annotations

import json
import re
from pathlib import Path

from overlay_client.backend import (
    GNOME_SHELL_HELPER_SHELL_VERSIONS,
    GNOME_SHELL_HELPER_UUID,
    HELPER_KIND,
    HELPER_PROTOCOL,
    HELPER_VERSION,
)

ROOT = Path(__file__).resolve().parent.parent
HELPER_DIR = ROOT / "helpers" / "gnome_shell_extension"
CONTRACT_FIXTURE = ROOT / "tests" / "fixtures" / "gnome_shell_helper_contract_v1.json"


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


def test_extension_source_imports_local_constants_without_runtime_behavior() -> None:
    source = (HELPER_DIR / "extension.js").read_text(encoding="utf-8")

    assert "from './constants.js'" in source
    assert "org.gnome.Shell" not in source
    assert "Gio.DBus" not in source
    assert "DBus" not in source


def test_protocol_bump_fixture_tracks_contract_review_triggers() -> None:
    fixture = json.loads(CONTRACT_FIXTURE.read_text(encoding="utf-8"))

    assert fixture["helper_kind"] == HELPER_KIND.value
    assert fixture["helper_protocol"] == HELPER_PROTOCOL
    assert fixture["helper_version_source"] == "version.__version__"
    triggers = fixture["protocol_bump_required_when"]
    assert isinstance(triggers, list)
    assert len(triggers) >= 4
    assert any("DBus" in trigger for trigger in triggers)
    assert any("Target geometry" in trigger for trigger in triggers)
