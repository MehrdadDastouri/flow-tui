"""Command-line interface argument parsing for flow-tui."""

import argparse
from typing import List, Optional


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser with runtime options."""
    parser = argparse.ArgumentParser(
        prog="flow-tui",
        description="High-performance terminal telemetry for market microstructure.",
    )
    parser.add_argument(
        "-s",
        "--symbol",
        type=str,
        default="ETHUSDC",
        help="Target trading pair symbol (default: ETHUSDC)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=20,
        help="Terminal UI refresh frequency in Hz (default: 20, max: 60)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    """CLI execution entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    from flow_tui.app import FlowApp

    app = FlowApp(symbol=args.symbol, fps=args.fps)
    app.run()
