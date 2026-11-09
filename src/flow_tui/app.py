"""Terminal User Interface application for flow-tui built with Textual."""

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Static

from flow_tui.pipeline import PipelineCoordinator, TelemetryState


class BookWidget(Static):
    """Renders Level-2 order book depth, mid-price, and spread."""

    def update_state(self, state: TelemetryState) -> None:
        if not state.book:
            self.update("[dim]Waiting for order book depth snapshots...[/dim]")
            return

        book = state.book
        imbalance_color = "green" if book.imbalance >= 0 else "red"

        content = [
            f"[bold cyan]{state.symbol} • L2 Book Depth[/bold cyan]",
            "─" * 32,
            f"Mid Price: [bold yellow]{book.mid_price:.2f}[/bold yellow]",
            f"Spread:    [dim]{book.spread:.2f}[/dim]",
            f"Imbalance: [{imbalance_color}]{book.imbalance:+.4f}[/]",
            "",
            "[bold red]▲ Top Ask (Liquidity Wall)[/bold red]",
            f"  Price: {book.best_ask:.2f}",
            "",
            "[bold green]▼ Top Bid (Support Queue)[/bold green]",
            f"  Price: {book.best_bid:.2f}",
        ]
        self.update("\n".join(content))


class TelemetryWidget(Static):
    """Renders real-time Cumulative Volume Delta and Order Flow Imbalance metrics."""

    def update_state(self, state: TelemetryState) -> None:
        cvd = state.cvd
        ofi = state.ofi

        cvd_val = cvd.cumulative_delta if cvd else 0.0
        roll_cvd = cvd.rolling_delta if cvd else 0.0
        trades = cvd.trade_count if cvd else 0

        inst_ofi = ofi.instant_ofi if ofi else 0.0
        cum_ofi = ofi.cumulative_ofi if ofi else 0.0

        cvd_color = "green" if cvd_val >= 0 else "red"
        ofi_color = "green" if inst_ofi >= 0 else "red"

        content = [
            "[bold cyan]Microstructural Telemetry[/bold cyan]",
            "─" * 32,
            f"Last Trade: [bold white]{state.last_price:.2f}[/bold white]",
            f"Ticks Ingested: [dim]{trades}[/dim]",
            "",
            "[bold magenta]Cumulative Volume Delta (CVD)[/bold magenta]",
            f"  Cumulative: [{cvd_color}]{cvd_val:+.4f}[/]",
            f"  Rolling Window: {roll_cvd:+.4f}",
            "",
            "[bold blue]Order Flow Imbalance (OFI)[/bold blue]",
            f"  Instant Impact: [{ofi_color}]{inst_ofi:+.4f}[/]",
            f"  Cumulative OFI: {cum_ofi:+.4f}",
        ]
        self.update("\n".join(content))


class FlowApp(App):
    """Core Textual application container."""

    CSS = """
    Screen {
        background: #0d1117;
    }
    #main-container {
        layout: horizontal;
        height: 1fr;
    }
    .panel {
        width: 1fr;
        height: 1fr;
        border: solid #30363d;
        padding: 1 2;
        margin: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "reset_metrics", "Reset Telemetry"),
    ]

    def __init__(self, symbol: str = "ETHUSDC") -> None:
        super().__init__()
        self.coordinator = PipelineCoordinator(symbol=symbol)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):
            yield BookWidget(id="book-panel", classes="panel")
            yield TelemetryWidget(id="telemetry-panel", classes="panel")
        yield Footer()

    def action_reset_metrics(self) -> None:
        """Reset internal pipeline aggregations."""
        self.coordinator.reset()
        self.refresh_views()

    def refresh_views(self) -> None:
        """Push latest pipeline state into UI widgets."""
        state = self.coordinator.get_state()
        self.query_one("#book-panel", BookWidget).update_state(state)
        self.query_one("#telemetry-panel", TelemetryWidget).update_state(state)
