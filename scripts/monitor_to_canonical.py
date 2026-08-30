#!/usr/bin/env python3
"""Convert a monitor-space rectangle into EDMC Modern Overlay canvas coordinates.

Example:
    python scripts/monitor_to_canonical.py --monitor-width 1920 --monitor-height 1080 \
        --x 300 --y 450 --w 600 --h 300
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from overlay_client.viewport_helper import (  # noqa: E402 - direct script execution needs sys.path setup above
    ScaleMode,
    compute_viewport_transform,
)


def _positive_finite(value: float, name: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return numeric


def _finite(value: float, name: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be a finite number")
    return numeric


def monitor_rect_to_canonical(
    *,
    monitor_width: float,
    monitor_height: float,
    x: float,
    y: float,
    width: float,
    height: float,
    scale_mode: str = ScaleMode.FILL.value,
) -> dict[str, float]:
    """Reverse the client viewport transform for one monitor-space rectangle."""

    safe_monitor_width = _positive_finite(monitor_width, "monitor_width")
    safe_monitor_height = _positive_finite(monitor_height, "monitor_height")
    try:
        mode = ScaleMode(scale_mode.lower())
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"scale_mode must be one of: {ScaleMode.FIT.value}, {ScaleMode.FILL.value}") from exc

    transform = compute_viewport_transform(safe_monitor_width, safe_monitor_height, mode)
    scale = transform.scale
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("viewport scale must be a positive finite number")

    offset_x, offset_y = transform.offset
    return {
        "x": (_finite(x, "x") - offset_x) / scale,
        "y": (_finite(y, "y") - offset_y) / scale,
        "w": _finite(width, "width") / scale,
        "h": _finite(height, "height") / scale,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--monitor-width", type=float, required=True, help="Monitor width in pixels")
    parser.add_argument("--monitor-height", type=float, required=True, help="Monitor height in pixels")
    parser.add_argument("--x", type=float, required=True, help="Rectangle X coordinate on the monitor")
    parser.add_argument("--y", type=float, required=True, help="Rectangle Y coordinate on the monitor")
    parser.add_argument("--w", type=float, required=True, help="Rectangle width on the monitor")
    parser.add_argument("--h", type=float, required=True, help="Rectangle height on the monitor")
    parser.add_argument(
        "--scale-mode",
        choices=tuple(mode.value for mode in ScaleMode),
        default=ScaleMode.FILL.value,
        help="Overlay scale mode (default: fill)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = monitor_rect_to_canonical(
        monitor_width=args.monitor_width,
        monitor_height=args.monitor_height,
        x=args.x,
        y=args.y,
        width=args.w,
        height=args.h,
        scale_mode=args.scale_mode,
    )
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
