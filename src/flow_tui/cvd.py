"""Cumulative Volume Delta (CVD) tracking and rolling volume metrics."""

from collections import deque
from dataclasses import dataclass
from typing import Deque
from flow_tui.models import TradeEvent


@dataclass(frozen=True)
class CVDMetrics:
    """Snapshot of cumulative volume delta and rolling telemetry."""

    cumulative_delta: float
    total_buy_volume: float
    total_sell_volume: float
    rolling_delta: float
    trade_count: int


class CVDTracker:
    """Tracks cumulative taker volume delta and windowed rolling volume.

    Delta = Aggressive Buy Volume - Aggressive Sell Volume.
    """

    def __init__(self, window_size: int = 1000) -> None:
        self.window_size = window_size
        self.total_buy_volume: float = 0.0
        self.total_sell_volume: float = 0.0
        self.trade_count: int = 0

        self._rolling_trades: Deque[TradeEvent] = deque(maxlen=window_size)
        self._rolling_buy_vol: float = 0.0
        self._rolling_sell_vol: float = 0.0

    def update(self, trade: TradeEvent) -> CVDMetrics:
        """Incorporate a new trade event and return updated metrics."""
        self.trade_count += 1

        if len(self._rolling_trades) == self.window_size:
            oldest = self._rolling_trades[0]
            if oldest.side == "BUY":
                self._rolling_buy_vol -= oldest.quantity
            else:
                self._rolling_sell_vol -= oldest.quantity

        self._rolling_trades.append(trade)

        if trade.side == "BUY":
            self.total_buy_volume += trade.quantity
            self._rolling_buy_vol += trade.quantity
        else:
            self.total_sell_volume += trade.quantity
            self._rolling_sell_vol += trade.quantity

        cum_delta = self.total_buy_volume - self.total_sell_volume
        roll_delta = self._rolling_buy_vol - self._rolling_sell_vol

        return CVDMetrics(
            cumulative_delta=round(cum_delta, 6),
            total_buy_volume=round(self.total_buy_volume, 6),
            total_sell_volume=round(self.total_sell_volume, 6),
            rolling_delta=round(roll_delta, 6),
            trade_count=self.trade_count,
        )

    def reset(self) -> None:
        """Reset all volume counters and empty history."""
        self.total_buy_volume = 0.0
        self.total_sell_volume = 0.0
        self.trade_count = 0
        self._rolling_trades.clear()
        self._rolling_buy_vol = 0.0
        self._rolling_sell_vol = 0.0
