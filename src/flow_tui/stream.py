"""Asynchronous WebSocket market stream ingestion client."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import websockets
from flow_tui.models import TradeEvent

logger = logging.getLogger("flow_tui.stream")


class MarketStreamClient:
    """Consumes real-time trade and depth diff streams over WebSockets."""

    BASE_URL = "wss://fstream.binance.com/ws"

    def __init__(
        self,
        symbol: str = "ETHUSDC",
        on_trade: Optional[Callable[[TradeEvent], None]] = None,
        on_depth: Optional[Callable[[List[Tuple[float, float]], List[Tuple[float, float]]], None]] = None,
    ) -> None:
        self.symbol = symbol.lower()
        self.on_trade = on_trade
        self.on_depth = on_depth
        self._running = False

    def _parse_trade_message(self, data: Dict[str, Any]) -> Optional[TradeEvent]:
        """Convert raw aggTrade/trade payload into a domain TradeEvent."""
        try:
            return TradeEvent(
                symbol=data.get("s", self.symbol).upper(),
                price=float(data["p"]),
                quantity=float(data["q"]),
                timestamp=int(data["T"]),
                is_buyer_maker=bool(data["m"]),
            )
        except (KeyError, ValueError) as err:
            logger.error("Failed to parse trade frame: %s", err)
            return None

    def _parse_depth_message(
        self, data: Dict[str, Any]
    ) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """Parse raw L2 diff book levels into float price/quantity tuples."""
        bids: List[Tuple[float, float]] = []
        asks: List[Tuple[float, float]] = []

        for p, q in data.get("b", []):
            bids.append((float(p), float(q)))
        for p, q in data.get("a", []):
            asks.append((float(p), float(q)))

        return bids, asks

    def dispatch_payload(self, text_payload: str) -> None:
        """Route raw JSON frame to configured callbacks."""
        try:
            msg = json.loads(text_payload)
        except json.JSONDecodeError:
            return

        event_type = msg.get("e")

        if event_type in ("trade", "aggTrade"):
            trade = self._parse_trade_message(msg)
            if trade and self.on_trade:
                self.on_trade(trade)

        elif event_type == "depthUpdate":
            bids, asks = self._parse_depth_message(msg)
            if self.on_depth:
                self.on_depth(bids, asks)

    async def run(self) -> None:
        """Maintain persistent socket connection with auto-reconnect."""
        stream_path = f"{self.symbol}@aggTrade/{self.symbol}@depth@100ms"
        uri = f"{self.BASE_URL}/{stream_path}"
        self._running = True

        while self._running:
            try:
                async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as ws:
                    logger.info("Connected to market stream: %s", uri)
                    while self._running:
                        msg = await ws.recv()
                        self.dispatch_payload(msg)
            except (websockets.ConnectionClosed, asyncio.TimeoutError, OSError) as err:
                if not self._running:
                    break
                logger.warning("Stream disconnected (%s). Reconnecting in 2s...", err)
                await asyncio.sleep(2.0)

    def stop(self) -> None:
        """Signal client to terminate stream loop."""
        self._running = False
