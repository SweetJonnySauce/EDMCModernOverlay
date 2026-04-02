from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

from tests.harness_fixtures import harness_runtime_context

pytestmark = pytest.mark.harness


@pytest.fixture
def harness_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[tuple[object, Any]]:
    with harness_runtime_context(monkeypatch, tmp_path, register_journal=False, capture_overlay=False) as (
        harness,
        runtime,
        _adapter,
    ):
        yield harness, runtime


def test_overlay_launch_env_sanitizes_steam_linker_vars(
    harness_runtime: tuple[object, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    _harness, runtime = harness_runtime

    monkeypatch.setenv("LD_PRELOAD", "/steam/ubuntu12_32/gameoverlayrenderer.so")
    monkeypatch.setenv("QT_PLUGIN_PATH", "/steam/qt/plugins")
    monkeypatch.setenv("QT_QPA_PLATFORM_PLUGIN_PATH", "/steam/qt/platforms")
    monkeypatch.setenv("LD_LIBRARY_PATH", "/steam/runtime/lib")
    monkeypatch.setenv("MEL_LD_LIBRARY_PATH", "/host/runtime/lib")
    monkeypatch.delenv("EDMC_OVERLAY_PRESERVE_LD_ENV", raising=False)

    env = runtime._build_overlay_environment()

    assert "LD_PRELOAD" not in env
    assert "QT_PLUGIN_PATH" not in env
    assert "QT_QPA_PLATFORM_PLUGIN_PATH" not in env
    assert env.get("LD_LIBRARY_PATH") == "/host/runtime/lib"


def test_overlay_launch_env_opt_out_preserves_linker_vars(
    harness_runtime: tuple[object, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    _harness, runtime = harness_runtime

    monkeypatch.setenv("EDMC_OVERLAY_PRESERVE_LD_ENV", "1")
    monkeypatch.setenv("LD_PRELOAD", "/steam/ubuntu12_32/gameoverlayrenderer.so")
    monkeypatch.setenv("QT_PLUGIN_PATH", "/steam/qt/plugins")
    monkeypatch.setenv("QT_QPA_PLATFORM_PLUGIN_PATH", "/steam/qt/platforms")
    monkeypatch.setenv("LD_LIBRARY_PATH", "/steam/runtime/lib")
    monkeypatch.setenv("MEL_LD_LIBRARY_PATH", "/host/runtime/lib")

    env = runtime._build_overlay_environment()

    assert env.get("LD_PRELOAD") == "/steam/ubuntu12_32/gameoverlayrenderer.so"
    assert env.get("QT_PLUGIN_PATH") == "/steam/qt/plugins"
    assert env.get("QT_QPA_PLATFORM_PLUGIN_PATH") == "/steam/qt/platforms"
    assert env.get("LD_LIBRARY_PATH") == "/steam/runtime/lib"
