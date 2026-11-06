"""Unit tests for market stream parser and event model."""

from flow_tui.models import TradeEvent
from flow_tui.stream import BinanceTradeStream


def test_parse_valid_trade_message():
    client = BinanceTradeStream("btcusdt")
    sample_payload = """
    {
        "e": "trade",
        "E": 1672531200000,
        "s": "BTCUSDT",
        "t": 123456,
        "p": "65120.50",
        "q": "0.2500",
        "b": 88,
        "a": 50,
        "T": 1672531200001,
        "m": true,
        "M": true
    }
    """
    event = client.parse_message(sample_payload)

    assert isinstance(event, TradeEvent)
    assert event.symbol == "BTCUSDT"
    assert event.price == 65120.50
    assert event.quantity == 0.25
    assert event.timestamp == 1672531200001
    assert event.is_buyer_maker is True
    assert event.side == "SELL"


def test_parse_buyer_taker_trade():
    client = BinanceTradeStream("btcusdt")
    sample_payload = """
    {
        "e": "trade",
        "s": "BTCUSDT",
        "p": "65150.00",
        "q": "1.0000",
        "T": 1672531200002,
        "m": false
    }
    """
    event = client.parse_message(sample_payload)

    assert event is not None
    assert event.side == "BUY"


def test_parse_invalid_payloads():
    client = BinanceTradeStream("btcusdt")
    assert client.parse_message("invalid json") is None
    assert client.parse_message('{"e": "ticker"}') is None
