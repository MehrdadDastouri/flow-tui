"""Unit tests for WebSocket stream parsing and dispatch logic."""

import json
from flow_tui.stream import MarketStreamClient


def test_trade_payload_dispatch():
    trades = []
    client = MarketStreamClient(symbol="ETHUSDC", on_trade=trades.append)

    raw_trade = json.dumps({
        "e": "aggTrade",
        "s": "ETHUSDC",
        "p": "3250.25",
        "q": "1.500",
        "T": 1700000000000,
        "m": False,
    })

    client.dispatch_payload(raw_trade)
    assert len(trades) == 1
    assert trades[0].price == 3250.25
    assert trades[0].quantity == 1.500
    assert trades[0].is_buyer_maker is False


def test_depth_payload_dispatch():
    depth_updates = []

    def on_depth(bids, asks):
        depth_updates.append((bids, asks))

    client = MarketStreamClient(symbol="ETHUSDC", on_depth=on_depth)

    raw_depth = json.dumps({
        "e": "depthUpdate",
        "b": [["3200.00", "5.000"], ["3199.50", "0.000"]],
        "a": [["3201.00", "2.500"]],
    })

    client.dispatch_payload(raw_depth)
    assert len(depth_updates) == 1
    bids, asks = depth_updates[0]
    assert bids == [(3200.00, 5.000), (3199.50, 0.000)]
    assert asks == [(3201.00, 2.500)]


def test_malformed_json_handling():
    client = MarketStreamClient(symbol="ETHUSDC")
    # Should safely ignore invalid JSON without raising exceptions
    client.dispatch_payload("INVALID_RAW_STRING")
