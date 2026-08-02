#!/usr/bin/env python3
"""Validate, summarize, and compare privacy-safe backend performance evidence."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from overlay_client.backend.performance_evidence import (  # noqa: E402
    EvidenceValidationError,
    build_performance_summary,
    compare_performance_summaries,
    format_performance_comparison,
    format_performance_summary,
    parse_performance_capture,
    parse_performance_manifest,
    parse_performance_summary,
    parse_performance_thresholds,
    serialize_performance_comparison,
    serialize_performance_summary,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pure tooling for the fix219 performance evidence gate.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    validate_manifest = commands.add_parser("validate-manifest", help="validate one scenario manifest")
    validate_manifest.add_argument("manifest", type=Path)

    validate_captures = commands.add_parser("validate-captures", help="validate normalized capture repetitions")
    validate_captures.add_argument("manifest", type=Path)
    validate_captures.add_argument("captures", type=Path, nargs="+")

    summarize = commands.add_parser("summarize", help="aggregate normalized capture repetitions")
    summarize.add_argument("manifest", type=Path)
    summarize.add_argument("--summary-id", required=True)
    summarize.add_argument("--require-complete", action="store_true")
    summarize.add_argument("--format", choices=("json", "text"), default="json")
    summarize.add_argument("captures", type=Path, nargs="+")

    compare = commands.add_parser("compare", help="compare candidate and baseline summaries")
    compare.add_argument("manifest", type=Path)
    compare.add_argument("baseline_summary", type=Path)
    compare.add_argument("candidate_summary", type=Path)
    compare.add_argument("thresholds", type=Path)
    compare.add_argument("--format", choices=("json", "text"), default="json")
    return parser


def _run(args: argparse.Namespace) -> str:
    manifest = parse_performance_manifest(args.manifest)
    if args.command == "validate-manifest":
        return (
            f"valid manifest {manifest.manifest_id}: {len(manifest.scenarios)} scenarios, "
            f"{manifest.timing.repetitions} repetitions\n"
        )
    if args.command == "validate-captures":
        captures = [parse_performance_capture(path, manifest) for path in args.captures]
        return f"valid captures for {manifest.manifest_id}: {len(captures)} repetitions\n"
    if args.command == "summarize":
        captures = [parse_performance_capture(path, manifest) for path in args.captures]
        summary = build_performance_summary(
            manifest,
            captures,
            summary_id=args.summary_id,
            require_complete=args.require_complete,
        )
        if args.format == "text":
            return format_performance_summary(summary) + "\n"
        return serialize_performance_summary(summary)
    baseline = parse_performance_summary(args.baseline_summary, manifest)
    candidate = parse_performance_summary(args.candidate_summary, manifest)
    thresholds = parse_performance_thresholds(args.thresholds, manifest)
    comparison = compare_performance_summaries(baseline, candidate, thresholds)
    if args.format == "text":
        return format_performance_comparison(comparison) + "\n"
    return serialize_performance_comparison(comparison)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        output = _run(args)
    except (EvidenceValidationError, OSError) as exc:
        sys.stderr.write(f"backend_performance: {exc}\n")
        return 2
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
