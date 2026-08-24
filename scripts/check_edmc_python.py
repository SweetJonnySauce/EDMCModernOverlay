#!/usr/bin/env python3
"""Validate plugin Python compatibility against EDMC's tested runtime baseline."""
from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Optional, Tuple


BASE_DIR = Path(__file__).resolve().parents[1]
BASELINE_PATH = BASE_DIR / "docs" / "compliance" / "edmc_python_version.txt"
ALLOW_ENV = "ALLOW_EDMC_PYTHON_MISMATCH"


def _load_expected() -> Tuple[Tuple[int, int, int], Optional[str]]:
    if not BASELINE_PATH.exists():
        raise SystemExit(f"Missing baseline file: {BASELINE_PATH}")
    raw = BASELINE_PATH.read_text(encoding="utf-8").strip()
    if not raw:
        raise SystemExit(f"Baseline file is empty: {BASELINE_PATH}")
    tokens = raw.split()
    version_tokens = tokens[0].strip().split(".")
    try:
        major, minor = int(version_tokens[0]), int(version_tokens[1])
        micro = int(version_tokens[2]) if len(version_tokens) > 2 else 0
    except (IndexError, ValueError) as exc:
        raise SystemExit(f"Unable to parse version in {BASELINE_PATH}: {raw}") from exc
    arch = tokens[1].strip().lower() if len(tokens) > 1 else None
    return (major, minor, micro), arch


def _current_version() -> Tuple[int, int, int]:
    return (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)


def _current_arch() -> str:
    return platform.architecture()[0].lower()


def _runtime_mismatch(
    expected_version: Tuple[int, int, int],
    expected_arch: Optional[str],
    actual_version: Tuple[int, int, int],
    actual_arch: str,
) -> Optional[str]:
    expected_series = expected_version[:2]
    version_matches = actual_version[:2] == expected_series and actual_version >= expected_version
    arch_matches = expected_arch is None or actual_arch == expected_arch
    if version_matches and arch_matches:
        return None
    expected = f"{expected_version[0]}.{expected_version[1]}.{expected_version[2]}+"
    expected += f" in the {expected_series[0]}.{expected_series[1]} series"
    if expected_arch:
        expected += f" ({expected_arch})"
    actual = f"{actual_version[0]}.{actual_version[1]}.{actual_version[2]} ({actual_arch})"
    return f"Python {actual} does not match tested EDMC runtime {expected}"


def main() -> None:
    expected_version, expected_arch = _load_expected()
    actual_version = _current_version()
    actual_arch = _current_arch()
    mismatch = _runtime_mismatch(expected_version, expected_arch, actual_version, actual_arch)
    if mismatch:
        if os.environ.get(ALLOW_ENV) == "1":
            print(f"[check-edmc-python] WARNING: {mismatch} (override via {ALLOW_ENV})")
            return
        raise SystemExit(f"[check-edmc-python] ERROR: {mismatch} (set {ALLOW_ENV}=1 to bypass)")

    expected_text = f"{expected_version[0]}.{expected_version[1]}.{expected_version[2]}+"
    expected_text += f" in the {expected_version[0]}.{expected_version[1]} series"
    if expected_arch:
        expected_text += f" ({expected_arch})"
    print(
        "[check-edmc-python] OK: "
        f"Python {actual_version} ({actual_arch}) matches tested baseline {expected_text} from {BASELINE_PATH}"
    )


if __name__ == "__main__":
    main()
