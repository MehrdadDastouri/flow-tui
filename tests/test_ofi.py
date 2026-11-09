"""Unit tests for the Order Flow Imbalance (OFI) calculator."""

import pytest
from flow_tui.ofi import OFICalculator


@pytest.fixture
def ofi():
    return OFICalculator(rolling_window=3)


def test_ofi_first_observation(ofi):
    # Baseline setup: no impact on tick 0
    snap = ofi.compute(bid_price=100.0, bid_qty=5.0, ask_price=101.0, ask_qty=5.0)
    assert snap.instant_ofi == 0.0
    assert snap.cumulative_ofi == 0.0


def test_ofi_same_price_volume_shift(ofi):
    ofi.compute(bid_price=100.0, bid_qty=5.0, ask_price=101.0, ask_qty=5.0)

    # Bid qty increases to 8 (+3), Ask qty increases to 7 (-2 impact)
    # Instant OFI = +3 + (-2) = +1
    snap = ofi.compute(bid_price=100.0, bid_qty=8.0, ask_price=101.0, ask_qty=7.0)
    assert snap.bid_impact == 3.0
    assert snap.ask_impact == -2.0
    assert snap.instant_ofi == 1.0
    assert snap.cumulative_ofi == 1.0


def test_ofi_bid_price_increase(ofi):
    ofi.compute(bid_price=100.0, bid_qty=5.0, ask_price=102.0, ask_qty=5.0)

    # Best bid steps up from 100.0 to 100.5 with qty 4.0 -> delta_b = +4.0
    # Ask price stays 102.0 with qty 5.0 -> delta_a = 0.0
    snap = ofi.compute(bid_price=100.5, bid_qty=4.0, ask_price=102.0, ask_qty=5.0)
    assert snap.bid_impact == 4.0
    assert snap.ask_impact == 0.0
    assert snap.instant_ofi == 4.0


def test_ofi_ask_price_drop(ofi):
    ofi.compute(bid_price=100.0, bid_qty=5.0, ask_price=102.0, ask_qty=5.0)

    # Ask drops from 102.0 to 101.5 with qty 6.0 -> delta_a = -6.0
    # Bid stays unchanged -> delta_b = 0.0
    snap = ofi.compute(bid_price=100.0, bid_qty=5.0, ask_price=101.5, ask_qty=6.0)
    assert snap.bid_impact == 0.0
    assert snap.ask_impact == -6.0
    assert snap.instant_ofi == -6.0


def test_ofi_rolling_eviction(ofi):
    # Window size is 3
    ofi.compute(100.0, 1.0, 102.0, 1.0)
    ofi.compute(100.0, 2.0, 102.0, 1.0)  # +1.0
    ofi.compute(100.0, 4.0, 102.0, 1.0)  # +2.0
    snap = ofi.compute(100.0, 7.0, 102.0, 1.0)  # +3.0 -> rolling contains [1.0, 2.0, 3.0] = 6.0
    assert snap.rolling_ofi == 6.0

    # 4th observation: drops 1.0, adds +1.0 -> rolling contains [2.0, 3.0, 1.0] = 6.0
    snap2 = ofi.compute(100.0, 8.0, 102.0, 1.0)
    assert snap2.instant_ofi == 1.0
    assert snap2.rolling_ofi == 6.0
