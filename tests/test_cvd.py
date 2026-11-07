"""Unit tests for the Cumulative Volume Delta (CVD) tracker."""

import pytest
from flow_tui.cvd import CVDTracker
from flow_tui.models import TradeEvent


@pytest.fixture
def tracker():
    return CVDTracker(window_size=3)


def test_cvd_initial_state(tracker):
    metrics = tracker.update(
        TradeEvent("BTCUSDT", 60000.0, 1.5, 1000, is_buyer_maker=False)
    )
    assert metrics.total_buy_volume == 1.5
    assert metrics.total_sell_volume == 0.0
    assert metrics.cumulative_delta == 1.5
    assert metrics.rolling_delta == 1.5
    assert metrics.trade_count == 1


def test_cvd_accumulation(tracker):
    tracker.update(TradeEvent("BTCUSDT", 60000.0, 2.0, 1001, is_buyer_maker=False))
    metrics = tracker.update(
        TradeEvent("BTCUSDT", 60010.0, 0.5, 1002, is_buyer_maker=True)
    )

    assert metrics.total_buy_volume == 2.0
    assert metrics.total_sell_volume == 0.5
    assert metrics.cumulative_delta == 1.5
    assert metrics.trade_count == 2


def test_cvd_rolling_window_eviction(tracker):
    tracker.update(TradeEvent("BTCUSDT", 60000.0, 1.0, 1001, is_buyer_maker=False))
    tracker.update(TradeEvent("BTCUSDT", 60000.0, 2.0, 1002, is_buyer_maker=False))
    tracker.update(TradeEvent("BTCUSDT", 60000.0, 1.0, 1003, is_buyer_maker=True))

    metrics = tracker.update(
        TradeEvent("BTCUSDT", 60000.0, 3.0, 1004, is_buyer_maker=True)
    )

    assert metrics.total_buy_volume == 3.0
    assert metrics.total_sell_volume == 4.0
    assert metrics.cumulative_delta == -1.0
    assert metrics.rolling_delta == -2.0
    assert metrics.trade_count == 4
