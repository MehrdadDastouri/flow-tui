"""CLI entry point for flow-tui."""

import sys
from rich.console import Console

console = Console()

def main() -> int:
    console.print(
        "[bold cyan]flow-tui[/bold cyan] [dim]v0.1.0[/dim] - "
        "[green]Core engine initialized.[/green]"
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
