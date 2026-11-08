"""Unit tests for Level-2 Order Book mechanics and metrics."""

import pytest
from flow_tui.book import OrderBook


@pytest.fixture
def empty_book():
    return OrderBook(symbol="ETHUSDC")


def test_order_book_diff_update(empty_book):
    bids = [(3000.0, 1.5), (2995.0, 3.0)]
    asks = [(3005.0, 2.0), (3010.0, 4.0)]
    empty_book.apply_diff(bids, asks)

    assert empty_book.best_bid == 3000.0
    assert empty_book.best_ask == 3005.0
    assert empty_book.spread == 5.0
    assert empty_book.mid_price == 3002.5


def test_order_book_level_removal(empty_book):
    empty_book.apply_diff([(3000.0, 1.0), (2990.0, 2.0)], [(3005.0, 1.0)])
    assert empty_book.best_bid == 3000.0

    # Remove price level 3000.0 by setting quantity to 0
    empty_book.apply_diff([(3000.0, 0.0)], [])
    assert empty_book.best_bid == 2990.0


def test_order_book_imbalance(empty_book):
    # Equal liquidity on both sides
    empty_book.apply_diff([(100.0, 5.0)], [(101.0, 5.0)])
    assert empty_book.compute_imbalance() == 0.0

    # More bids than asks -> positive imbalance
    empty_book.apply_diff([(100.0, 15.0)], [(101.0, 5.0)])
    # (15 - 5) / (15 + 5) = 10 / 20 = 0.5
    assert empty_book.compute_imbalance() == 0.5


def test_get_metrics_empty_book(empty_book):
    assert empty_book.get_metrics() is None
