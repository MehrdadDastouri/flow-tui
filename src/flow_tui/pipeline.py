"""Pipeline coordinator unifying market streams, order book, CVD, and OFI engines."""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from flow_tui.book import BookMetrics, OrderBook
from flow_tui.cvd import CVDMetrics, CVDTracker
from flow_tui.models import TradeEvent
from flow_tui.ofi import OFICalculator, OFISnapshot


@dataclass(frozen=True)
class TelemetryState:
    """Unified telemetry state snapshot consumed by terminal widgets."""

    symbol: str
    last_price: float
    book: Optional[BookMetrics]
    cvd: Optional[CVDMetrics]
    ofi: Optional[OFISnapshot]


class PipelineCoordinator:
    """Coordinates event routing across the order book, CVD tracker, and OFI engine."""

    def __init__(
        self,
        symbol: str = "ETHUSDC",
        cvd_window: int = 1000,
        ofi_window: int = 500,
    ) -> None:
        self.symbol = symbol.upper()
        self.book = OrderBook(symbol=self.symbol)
        self.cvd_tracker = CVDTracker(window_size=cvd_window)
        self.ofi_calculator = OFICalculator(rolling_window=ofi_window)

        self.last_price: float = 0.0
        self._latest_cvd: Optional[CVDMetrics] = None
        self._latest_ofi: Optional[OFISnapshot] = None

    def handle_trade(self, trade: TradeEvent) -> TelemetryState:
        """Route trade event to CVD tracker and update current market price."""
        self.last_price = trade.price
        self._latest_cvd = self.cvd_tracker.update(trade)
        return self.get_state()

    def handle_depth_diff(
        self,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]],
    ) -> TelemetryState:
        """Apply depth changes, evaluate top-of-book transitions, and trigger OFI."""
        self.book.apply_diff(bids, asks)

        # Trigger OFI calculation whenever top of the book is populated
        top_bids, top_asks = self.book.get_top_levels(depth=1)
        if top_bids and top_asks:
            best_bid_price, best_bid_qty = top_bids[0]
            best_ask_price, best_ask_qty = top_asks[0]
            self._latest_ofi = self.ofi_calculator.compute(
                bid_price=best_bid_price,
                bid_qty=best_bid_qty,
                ask_price=best_ask_price,
                ask_qty=best_ask_qty,
            )

        return self.get_state()

    def get_state(self) -> TelemetryState:
        """Return the current aggregated telemetry snapshot."""
        return TelemetryState(
            symbol=self.symbol,
            last_price=self.last_price,
            book=self.book.get_metrics(),
            cvd=self._latest_cvd,
            ofi=self._latest_ofi,
        )

    def reset(self) -> None:
        """Reset state across all underlying analytical engines."""
        self.book.clear()
        self.cvd_tracker.reset()
        self.ofi_calculator.reset()
        self.last_price = 0.0
        self._latest_cvd = None
        self._latest_ofi = None
