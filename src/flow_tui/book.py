"""Local Level-2 Order Book implementation and depth metrics."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class BookMetrics:
    """Telemetry snapshot of order book state."""

    best_bid: float
    best_ask: float
    mid_price: float
    spread: float
    imbalance: float  # (Bid Vol - Ask Vol) / (Bid Vol + Ask Vol) over top N levels


class OrderBook:
    """Maintains a local Level-2 sorted order book from diff depth updates."""

    def __init__(self, symbol: str = "ETHUSDC") -> None:
        self.symbol = symbol.upper()
        # Mapping: price (float) -> quantity (float)
        self.bids: Dict[float, float] = {}
        self.asks: Dict[float, float] = {}

    def apply_diff(
        self,
        bids_update: List[Tuple[float, float]],
        asks_update: List[Tuple[float, float]],
    ) -> None:
        """Apply depth diffs.

        A quantity of 0 indicates the price level should be removed.
        """
        for price, qty in bids_update:
            if qty == 0.0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = qty

        for price, qty in asks_update:
            if qty == 0.0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = qty

    @property
    def best_bid(self) -> Optional[float]:
        """Highest buy order price."""
        return max(self.bids.keys()) if self.bids else None

    @property
    def best_ask(self) -> Optional[float]:
        """Lowest sell order price."""
        return min(self.asks.keys()) if self.asks else None

    @property
    def spread(self) -> Optional[float]:
        """Difference between lowest ask and highest bid."""
        if self.best_bid is not None and self.best_ask is not None:
            return round(self.best_ask - self.best_bid, 6)
        return None

    @property
    def mid_price(self) -> Optional[float]:
        """Mid-point between best bid and best ask."""
        if self.best_bid is not None and self.best_ask is not None:
            return round((self.best_bid + self.best_ask) / 2.0, 6)
        return None

    def get_top_levels(
        self, depth: int = 5
    ) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """Return sorted top-N bids (descending) and asks (ascending)."""
        sorted_bids = sorted(self.bids.items(), key=lambda x: x[0], reverse=True)[:depth]
        sorted_asks = sorted(self.asks.items(), key=lambda x: x[0])[:depth]
        return sorted_bids, sorted_asks

    def compute_imbalance(self, depth: int = 5) -> float:
        """Compute Order Book Imbalance (OBI) over top-N levels.

        Returns a value in [-1.0, 1.0].
        +1.0 = Pure buying pressure, -1.0 = Pure selling pressure.
        """
        top_bids, top_asks = self.get_top_levels(depth)
        total_bid_qty = sum(qty for _, qty in top_bids)
        total_ask_qty = sum(qty for _, qty in top_asks)

        total_liquidity = total_bid_qty + total_ask_qty
        if total_liquidity == 0.0:
            return 0.0

        return round((total_bid_qty - total_ask_qty) / total_liquidity, 4)

    def get_metrics(self, depth: int = 5) -> Optional[BookMetrics]:
        """Extract instant telemetry if both sides of the book are populated."""
        if self.best_bid is None or self.best_ask is None:
            return None

        return BookMetrics(
            best_bid=self.best_bid,
            best_ask=self.best_ask,
            mid_price=self.mid_price or 0.0,
            spread=self.spread or 0.0,
            imbalance=self.compute_imbalance(depth=depth),
        )

    def clear(self) -> None:
        """Reset order book state."""
        self.bids.clear()
        self.asks.clear()
