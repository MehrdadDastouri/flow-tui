"""Data models for incoming market events."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TradeEvent:
    """Represents an individual executed market trade."""

    symbol: str
    price: float
    quantity: float
    timestamp: int
    is_buyer_maker: bool

    @property
    def side(self) -> Literal["BUY", "SELL"]:
        """
        Derive taker trade side:
        If buyer is maker, the aggressive taker was a seller -> SELL.
        If buyer is not maker, the aggressive taker was a buyer -> BUY.
        """
        return "SELL" if self.is_buyer_maker else "BUY"
