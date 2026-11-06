"""Asynchronous market data stream ingestion."""

import asyncio
import json
import logging
from typing import AsyncGenerator, Optional
import websockets
from flow_tui.models import TradeEvent

logger = logging.getLogger(__name__)

BINANCE_WS_BASE = "wss://stream.binance.com:9443/ws"


class BinanceTradeStream:
    """Async stream client for Binance public trade feeds."""

    def __init__(self, symbol: str = "btcusdt") -> None:
        self.symbol = symbol.lower()
        self.url = f"{BINANCE_WS_BASE}/{self.symbol}@trade"
        self._running = False

    def parse_message(self, raw_msg: str) -> Optional[TradeEvent]:
        """Parse raw JSON trade message into a structured TradeEvent."""
        try:
            data = json.loads(raw_msg)
            if data.get("e") != "trade":
                return None
            return TradeEvent(
                symbol=data["s"],
                price=float(data["p"]),
                quantity=float(data["q"]),
                timestamp=int(data["T"]),
                is_buyer_maker=bool(data["m"]),
            )
        except (KeyError, ValueError, json.JSONDecodeError) as err:
            logger.debug("Failed to parse trade payload: %s", err)
            return None

    async def listen(self) -> AsyncGenerator[TradeEvent, None]:
        """Connect to WebSocket stream and continuously yield TradeEvent objects."""
        self._running = True
        while self._running:
            try:
                async with websockets.connect(self.url) as ws:
                    logger.info("Connected to WebSocket: %s", self.url)
                    while self._running:
                        message = await ws.recv()
                        event = self.parse_message(message)
                        if event:
                            yield event
            except (websockets.ConnectionClosed, asyncio.TimeoutError) as err:
                logger.warning("Stream disconnected (%s). Reconnecting in 2s...", err)
                await asyncio.sleep(2)
            except Exception as err:
                logger.error("Unexpected stream failure: %s", err)
                await asyncio.sleep(2)

    def stop(self) -> None:
        """Signal client loop to terminate gracefully."""
        self._running = False
