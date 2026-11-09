"""Unit tests for command-line interface arguments."""

from flow_tui.cli import build_parser


def test_default_cli_arguments():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.symbol == "ETHUSDC"
    assert args.fps == 20


def test_custom_cli_arguments():
    parser = build_parser()
    args = parser.parse_args(["--symbol", "SOLUSDT", "--fps", "30"])
    assert args.symbol == "SOLUSDT"
    assert args.fps == 30
