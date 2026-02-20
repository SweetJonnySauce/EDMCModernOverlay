#!/usr/bin/env python3
"""Scan an EDMC plugins directory for installed plugins (heuristic)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


ROOT_DIR = Path(__file__).resolve().parents[1]


def _is_disabled_dir(name: str) -> bool:
    lowered = name.lower()
    return lowered.endswith(".disabled") or ".disabled." in lowered


def _find_plugins(plugins_root: Path, *, include_disabled: bool) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    if not plugins_root.exists() or not plugins_root.is_dir():
        return results
    self_root = ROOT_DIR.resolve()
    for entry in sorted(plugins_root.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir():
            continue
        disabled = _is_disabled_dir(entry.name)
        if disabled and not include_disabled:
            continue
        load_py = entry / "load.py"
        if not load_py.exists():
            continue
        results.append(
            {
                "name": entry.name,
                "path": str(entry.resolve()),
                "disabled": str(disabled).lower(),
                "self": str(entry.resolve() == self_root).lower(),
            }
        )
    return results


def _resolve_plugins_root(args: argparse.Namespace) -> Path:
    if args.plugins_dir:
        return Path(args.plugins_dir).expanduser().resolve()
    if args.plugin_dir:
        return Path(args.plugin_dir).expanduser().resolve().parent
    return ROOT_DIR.parent.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List EDMC plugins by scanning the plugins directory for load.py files.",
    )
    parser.add_argument(
        "--plugins-dir",
        help="Path to the EDMC plugins directory (contains individual plugin folders).",
    )
    parser.add_argument(
        "--plugin-dir",
        help="Path to a plugin directory; its parent is treated as the plugins root.",
    )
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Include plugin folders that appear disabled ('.disabled' suffix).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output instead of plain text.",
    )
    args = parser.parse_args()

    plugins_root = _resolve_plugins_root(args)
    plugins = _find_plugins(plugins_root, include_disabled=args.include_disabled)

    if args.json:
        payload = {
            "plugins_root": str(plugins_root),
            "count": len(plugins),
            "plugins": plugins,
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Plugins root: {plugins_root}")
    if not plugins:
        print("No plugins found (load.py not detected).")
        return 0
    print(f"Found {len(plugins)} plugin(s):")
    for plugin in plugins:
        flags = []
        if plugin["self"] == "true":
            flags.append("this")
        if plugin["disabled"] == "true":
            flags.append("disabled")
        suffix = f" ({', '.join(flags)})" if flags else ""
        print(f"- {plugin['name']}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
