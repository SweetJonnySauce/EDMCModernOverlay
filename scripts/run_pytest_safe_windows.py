#!/usr/bin/env python3
"""Temporary Windows-only pytest launcher.

Use this on Windows when running tests under Python 3.13+ where pytest
`tmp_path` setup can fail with WinError 5 due to temp directory permissions.
Remove when upstream Python/pytest behavior no longer needs this workaround.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Sequence


def _parse_args(argv: Sequence[str]) -> tuple[Path, list[str]]:
    parser = argparse.ArgumentParser(
        description=(
            "Run pytest with a Windows-only tempdir workaround. "
            "Pass normal pytest arguments after this script's options."
        )
    )
    parser.add_argument(
        "--temproot",
        default=".pytest_windows_tmp_root",
        help="Directory used for PYTEST_DEBUG_TEMPROOT (default: .pytest_windows_tmp_root).",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to pytest (example: tests/test_hotkeys.py -k retry).",
    )
    ns = parser.parse_args(argv)
    args = list(ns.pytest_args)
    if args[:1] == ["--"]:
        args = args[1:]
    return Path(ns.temproot).resolve(), args


def _patch_windows_mkdir_mode() -> None:
    original_mkdir = Path.mkdir

    def safe_mkdir(path: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        # Work around Windows permission behavior for mode=0o700 temp dirs.
        if os.name == "nt" and mode == 0o700:
            mode = 0o777
        original_mkdir(path, mode=mode, parents=parents, exist_ok=exist_ok)

    Path.mkdir = safe_mkdir  # type: ignore[assignment]


def main(argv: Sequence[str]) -> int:
    if os.name != "nt":
        print("This script is Windows-only. Run `python -m pytest ...` on non-Windows platforms.", file=sys.stderr)
        return 2

    temp_root, pytest_args = _parse_args(argv)
    temp_root.mkdir(parents=True, exist_ok=True)
    os.environ["PYTEST_DEBUG_TEMPROOT"] = str(temp_root)
    _patch_windows_mkdir_mode()

    try:
        import pytest
    except ImportError:
        print("pytest is not installed in this interpreter.", file=sys.stderr)
        return 2

    if not pytest_args:
        pytest_args = ["-q"]
    return int(pytest.main(pytest_args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
