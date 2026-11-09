"""Unit tests for the PipelineCoordinator state aggregation."""

import pytest
from flow_tui.models import TradeEvent
from flow_tui.pipeline import PipelineCoordinator


@pytest.fixture
def pipeline():
    return PipelineCoordinator(symbol="ETHUSDC", cvd_window=5, ofi_window=5)


def test_initial_pipeline_state(pipeline):
    state = pipeline.get_state()
    assert state.symbol == "ETHUSDC"
    assert state.last_price == 0.0
    assert state.book is None
    assert state.cvd is None
    assert state.ofi is None


def test_trade_event_routing(pipeline):
    trade = TradeEvent("ETHUSDC", 3200.50, 2.0, 1000, is_buyer_maker=False)
    state = pipeline.handle_trade(trade)

    assert state.last_price == 3200.50
    assert state.cvd is not None
    assert state.cvd.cumulative_delta == 2.0
    assert state.cvd.total_buy_volume == 2.0
    assert state.cvd.trade_count == 1
    assert state.book is None


def test_depth_diff_routing_and_ofi_trigger(pipeline):
    # Step 1: Initial book depth
    state1 = pipeline.handle_depth_diff(
        bids=[(3200.0, 5.0)],
        asks=[(3205.0, 5.0)],
    )
    assert state1.book is not None
    assert state1.book.best_bid == 3200.0
    assert state1.book.best_ask == 3205.0
    assert state1.ofi is not None
    assert state1.ofi.instant_ofi == 0.0  # Initial baseline

    # Step 2: Bid side volume expands from 5.0 to 10.0 (+5 buying pressure)
    state2 = pipeline.handle_depth_diff(
        bids=[(3200.0, 10.0)],
        asks=[(3205.0, 5.0)],
    )
    assert state2.ofi.instant_ofi == 5.0
    assert state2.ofi.cumulative_ofi == 5.0
    assert state2.book.imbalance > 0.0


def test_pipeline_reset(pipeline):
    pipeline.handle_trade(TradeEvent("ETHUSDC", 3200.0, 1.0, 1000, False))
    pipeline.handle_depth_diff([(3200.0, 1.0)], [(3201.0, 1.0)])
    pipeline.reset()

    state = pipeline.get_state()
    assert state.last_price == 0.0
    assert state.book is None
    assert state.cvd is None
    assert state.ofi is None
