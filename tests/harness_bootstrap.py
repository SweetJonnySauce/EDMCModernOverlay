"""Bootstrap helpers for using the vendored BGS-Tally test harness safely."""

from __future__ import annotations

import importlib
import importlib.util
import sys
import types
from pathlib import Path
from typing import Any


_HARNESS_MODULE: types.ModuleType | None = None
_OVERRIDDEN_MODULE_NAMES: tuple[str, ...] = (
    "config",
    "theme",
    "companion",
    "companion.CAPIData",
    "monitor",
    "plug",
    "l10n",
    "EDMCOverlay",
    "EDMCOverlay.edmcoverlay",
    "overlay_plugin",
    "overlay_plugin.overlay_api",
)
_MISSING = object()


class _HeadlessTkRoot:
    """Minimal Tk root stub used during vendored harness import."""

    def withdraw(self) -> None:
        return


class _HeadlessTkFrame:
    pass


def _require_semantic_version() -> None:
    try:
        importlib.import_module("semantic_version")
    except ModuleNotFoundError as exc:  # pragma: no cover - environment setup guard
        raise RuntimeError(
            "Missing 'semantic_version'. Install dev dependencies: "
            "`python -m pip install -r requirements/dev.txt`."
        ) from exc


def _snapshot_modules() -> dict[str, object]:
    snapshot: dict[str, object] = {}
    for name in _OVERRIDDEN_MODULE_NAMES:
        snapshot[name] = sys.modules.get(name, _MISSING)
    return snapshot


def _restore_modules(snapshot: dict[str, object]) -> None:
    for name, value in snapshot.items():
        if value is _MISSING:
            sys.modules.pop(name, None)
            continue
        sys.modules[name] = value  # type: ignore[assignment]


def _import_vendored_harness() -> types.ModuleType:
    global _HARNESS_MODULE
    if _HARNESS_MODULE is not None:
        return _HARNESS_MODULE

    _require_semantic_version()
    importlib.import_module("load")

    import tkinter as tk

    snapshot = _snapshot_modules()
    original_tk = tk.Tk
    original_frame = tk.Frame
    try:
        tk.Tk = lambda *args, **kwargs: _HeadlessTkRoot()  # type: ignore[assignment]
        tk.Frame = lambda *args, **kwargs: _HeadlessTkFrame()  # type: ignore[assignment]
        harness_path = Path(__file__).with_name("harness.py")
        spec = importlib.util.spec_from_file_location("_vendored_test_harness", harness_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load vendored harness from {harness_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        tk.Tk = original_tk  # type: ignore[assignment]
        tk.Frame = original_frame  # type: ignore[assignment]
        _restore_modules(snapshot)

    _HARNESS_MODULE = module
    return module


def get_test_harness_class() -> type[Any]:
    module = _import_vendored_harness()
    harness_cls = getattr(module, "TestHarness", None)
    if harness_cls is None:
        raise RuntimeError("Vendored harness module did not expose TestHarness")
    return harness_cls


def create_harness(*, register_journal: bool = True) -> Any:
    module = _import_vendored_harness()
    module.sleep = lambda _seconds: None
    harness_cls = get_test_harness_class()
    harness = harness_cls()
    if not hasattr(harness, "commander"):
        harness.commander = "TestHarnessCmdr"
    if not hasattr(harness, "is_beta"):
        harness.is_beta = False
    if not hasattr(harness, "system"):
        harness.system = ""
    if register_journal:
        import load

        harness.register_journal_handler(load.journal_entry)
    return harness


def stop_plugin_runtime() -> None:
    import load

    load.plugin_stop()
