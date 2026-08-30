#!/usr/bin/env python3
"""Publish circles and rectangles for manual Modern Overlay inspection."""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PORT_FILE = PLUGIN_ROOT / "port.json"
DEFAULT_TTL_SECONDS = 60
DEFAULT_TIMEOUT_SECONDS = 5.0


def _shape_label_payload(shape: Mapping[str, Any]) -> Dict[str, Any]:
    """Describe one gallery shape immediately above its bounding box."""

    shape_name = str(shape["shape"])
    label_name = "Rectangle" if shape_name == "rect" else "Circle"
    variant = str(shape["id"]).removeprefix(f"shape-gallery-{shape_name}-").replace("-", " ")
    width = f"thickness={shape['thickness']}" if "thickness" in shape else "default thickness"
    if shape_name == "rect":
        label_x = int(shape["x"])
        label_y = max(0, int(shape["y"]) - 18)
    else:
        radius = int(shape["radius"])
        label_x = int(shape["x"]) - radius
        label_y = max(0, int(shape["y"]) - radius - 18)
    variant_id = str(shape["id"]).removeprefix("shape-gallery-")
    return {
        "type": "message",
        "id": f"shape-gallery-label-{variant_id}",
        "text": f"{label_name}: {variant} ({width})",
        "color": shape["color"],
        "x": label_x,
        "y": label_y,
        "size": "small",
        "ttl": shape["ttl"],
    }


def build_gallery_payloads(ttl: int = DEFAULT_TTL_SECONDS) -> List[Dict[str, Any]]:
    """Return a stable gallery that exercises shape appearance variations."""

    shapes = [
        {
            "type": "shape",
            "shape": "rect",
            "id": "shape-gallery-rect-thin-outline",
            "color": "#80d0ff",
            "fill": "none",
            "x": 60,
            "y": 70,
            "w": 250,
            "h": 120,
            "thickness": 1,
            "ttl": ttl,
        },
        {
            "type": "shape",
            "shape": "rect",
            "id": "shape-gallery-rect-thick-fill",
            "color": "#ff9c6b",
            "fill": "#1a1a1a",
            "x": 390,
            "y": 60,
            "w": 380,
            "h": 180,
            "thickness": 6,
            "ttl": ttl,
        },
        {
            "type": "shape",
            "shape": "rect",
            "id": "shape-gallery-rect-default-outline",
            "color": "#ffd166",
            "fill": "none",
            "x": 60,
            "y": 260,
            "w": 250,
            "h": 100,
            "ttl": ttl,
        },
        {
            "type": "shape",
            "shape": "rect",
            "id": "shape-gallery-rect-tall-outline",
            "color": "#80ff80",
            "fill": "none",
            "x": 930,
            "y": 80,
            "w": 180,
            "h": 270,
            "thickness": 3,
            "ttl": ttl,
        },
        {
            "type": "shape",
            "shape": "circle",
            "id": "shape-gallery-circle-thin-outline",
            "color": "#ff6b9c",
            "fill": "none",
            "x": 170,
            "y": 430,
            "radius": 70,
            "thickness": 1,
            "ttl": ttl,
        },
        {
            "type": "shape",
            "shape": "circle",
            "id": "shape-gallery-circle-medium-fill",
            "color": "#80d0ff",
            "fill": "#102a3a",
            "x": 460,
            "y": 440,
            "radius": 110,
            "thickness": 4,
            "ttl": ttl,
        },
        {
            "type": "shape",
            "shape": "circle",
            "id": "shape-gallery-circle-default-outline",
            "color": "#ffd166",
            "fill": "none",
            "x": 180,
            "y": 680,
            "radius": 50,
            "ttl": ttl,
        },
        {
            "type": "shape",
            "shape": "circle",
            "id": "shape-gallery-circle-thick-small",
            "color": "#80ff80",
            "fill": "#163a16",
            "x": 710,
            "y": 395,
            "radius": 45,
            "thickness": 8,
            "ttl": ttl,
        },
        {
            "type": "shape",
            "shape": "circle",
            "id": "shape-gallery-circle-concentric-outer",
            "color": "#ffcf70",
            "fill": "none",
            "x": 520,
            "y": 730,
            "radius": 140,
            "thickness": 2,
            "ttl": ttl,
        },
        {
            "type": "shape",
            "shape": "circle",
            "id": "shape-gallery-circle-concentric-middle",
            "color": "#ff9c6b",
            "fill": "none",
            "x": 520,
            "y": 730,
            "radius": 95,
            "thickness": 4,
            "ttl": ttl,
        },
        {
            "type": "shape",
            "shape": "circle",
            "id": "shape-gallery-circle-concentric-inner",
            "color": "#ff6b9c",
            "fill": "none",
            "x": 520,
            "y": 730,
            "radius": 50,
            "thickness": 7,
            "ttl": ttl,
        },
        {
            "type": "shape",
            "shape": "circle",
            "id": "shape-gallery-circle-large-outline",
            "color": "#b68cff",
            "fill": "none",
            "x": 1010,
            "y": 550,
            "radius": 150,
            "thickness": 2,
            "ttl": ttl,
        },
    ]
    return [*shapes, *(_shape_label_payload(shape) for shape in shapes)]


def _read_port(port_file: Path) -> int:
    try:
        data = json.loads(port_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Port file not found: {port_file}") from None
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read port file {port_file}: {exc}") from exc
    port = data.get("port") if isinstance(data, Mapping) else None
    if not isinstance(port, int) or port <= 0:
        raise ValueError(f"Port file does not contain a valid port: {data!r}")
    return port


def _send_cli_message(port: int, message: Mapping[str, Any], timeout: float) -> Mapping[str, Any]:
    encoded = json.dumps(message, ensure_ascii=False)
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        writer = sock.makefile("w", encoding="utf-8", newline="\n")
        reader = sock.makefile("r", encoding="utf-8")
        writer.write(encoded)
        writer.write("\n")
        writer.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            response_line = reader.readline()
            if not response_line:
                break
            try:
                response = json.loads(response_line)
            except json.JSONDecodeError:
                continue
            if isinstance(response, Mapping) and "status" in response:
                return response
    raise RuntimeError("Modern Overlay did not acknowledge the gallery payload")


def _cli_messages(payloads: Iterable[Mapping[str, Any]]) -> Iterable[Dict[str, Any]]:
    for sequence, payload in enumerate(payloads, start=1):
        yield {
            "cli": "legacy_overlay",
            "payload": dict(payload),
            "meta": {"source": "shape_gallery", "sequence": sequence},
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Display a circle and rectangle gallery in a running EDMC Modern Overlay.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--port-file",
        type=Path,
        default=DEFAULT_PORT_FILE,
        help="Path to the broadcaster port.json file.",
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=DEFAULT_TTL_SECONDS,
        help="Seconds to keep the gallery visible; use 0 to keep it persistent.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Seconds to wait for each local broadcaster acknowledgement.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.ttl < 0:
        raise SystemExit("--ttl must be zero or positive")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")

    port_file = args.port_file.expanduser().resolve()
    try:
        port = _read_port(port_file)
        payloads = build_gallery_payloads(ttl=args.ttl)
        for message in _cli_messages(payloads):
            response = _send_cli_message(port, message, args.timeout)
            if response.get("status") != "ok":
                raise RuntimeError(f"Modern Overlay rejected the gallery payload: {response}")
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"[shape-gallery] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"[shape-gallery] Displayed {len(payloads)} shapes via {port_file} "
        f"for {'persistently' if args.ttl == 0 else f'{args.ttl} seconds'}.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
