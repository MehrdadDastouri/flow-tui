"""Order Flow Imbalance (OFI) analytical engine based on Cont et al. (2014)."""

from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional


@dataclass(frozen=True)
class OFISnapshot:
    """Snapshot containing instant and accumulated OFI telemetry."""

    instant_ofi: float
    cumulative_ofi: float
    rolling_ofi: float
    bid_impact: float
    ask_impact: float


class OFICalculator:
    """Computes instant, rolling, and cumulative Order Flow Imbalance.

    Tracks transitions between consecutive Level-1 Best Bid/Ask snapshots.
    """

    def __init__(self, rolling_window: int = 500) -> None:
        self.rolling_window = rolling_window
        self.cumulative_ofi: float = 0.0

        self._prev_bid_price: Optional[float] = None
        self._prev_bid_qty: float = 0.0
        self._prev_ask_price: Optional[float] = None
        self._prev_ask_qty: float = 0.0

        self._history: Deque[float] = deque(maxlen=rolling_window)
        self._rolling_sum: float = 0.0

    def compute(
        self,
        bid_price: float,
        bid_qty: float,
        ask_price: float,
        ask_qty: float,
    ) -> OFISnapshot:
        """Process updated Level-1 book state and compute OFI differential."""
        # Initialize baseline on first observation
        if self._prev_bid_price is None or self._prev_ask_price is None:
            self._prev_bid_price = bid_price
            self._prev_bid_qty = bid_qty
            self._prev_ask_price = ask_price
            self._prev_ask_qty = ask_qty
            return OFISnapshot(
                instant_ofi=0.0,
                cumulative_ofi=0.0,
                rolling_ofi=0.0,
                bid_impact=0.0,
                ask_impact=0.0,
            )

        # 1. Bid Side Impact
        if bid_price > self._prev_bid_price:
            delta_b = bid_qty
        elif bid_price == self._prev_bid_price:
            delta_b = bid_qty - self._prev_bid_qty
        else:
            delta_b = -self._prev_bid_qty

        # 2. Ask Side Impact
        if ask_price < self._prev_ask_price:
            delta_a = -ask_qty
        elif ask_price == self._prev_ask_price:
            delta_a = -(ask_qty - self._prev_ask_qty)
        else:
            delta_a = self._prev_ask_qty

        instant_ofi = round(delta_b + delta_a, 6)

        # Update cumulative and rolling window
        self.cumulative_ofi = round(self.cumulative_ofi + instant_ofi, 6)

        if len(self._history) == self.rolling_window:
            self._rolling_sum -= self._history[0]

        self._history.append(instant_ofi)
        self._rolling_sum = round(self._rolling_sum + instant_ofi, 6)

        # Update cached state for next transition
        self._prev_bid_price = bid_price
        self._prev_bid_qty = bid_qty
        self._prev_ask_price = ask_price
        self._prev_ask_qty = ask_qty

        return OFISnapshot(
            instant_ofi=instant_ofi,
            cumulative_ofi=self.cumulative_ofi,
            rolling_ofi=self._rolling_sum,
            bid_impact=round(delta_b, 6),
            ask_impact=round(delta_a, 6),
        )

    def reset(self) -> None:
        """Reset historical baseline and state."""
        self.cumulative_ofi = 0.0
        self._prev_bid_price = None
        self._prev_bid_qty = 0.0
        self._prev_ask_price = None
        self._prev_ask_qty = 0.0
        self._history.clear()
        self._rolling_sum = 0.0
