"""Unit tests for Textual app layout and widget state rendering."""

from flow_tui.app import BookWidget, FlowApp, TelemetryWidget
from flow_tui.book import BookMetrics
from flow_tui.cvd import CVDMetrics
from flow_tui.ofi import OFISnapshot
from flow_tui.pipeline import TelemetryState


def test_book_widget_empty_and_populated():
    widget = BookWidget()
    empty_state = TelemetryState("ETHUSDC", 0.0, None, None, None)
    widget.update_state(empty_state)

    book = BookMetrics(3100.0, 3102.0, 3101.0, 2.0, 0.35)
    populated_state = TelemetryState("ETHUSDC", 3101.0, book, None, None)
    widget.update_state(populated_state)


def test_telemetry_widget_rendering():
    widget = TelemetryWidget()
    cvd = CVDMetrics(12.5, 20.0, 7.5, 4.0, 50)
    ofi = OFISnapshot(2.0, 8.5, 3.0, 2.0, 0.0)
    state = TelemetryState("ETHUSDC", 3101.0, None, cvd, ofi)
    widget.update_state(state)


def test_app_initialization():
    app = FlowApp(symbol="SOLUSDC")
    assert app.coordinator.symbol == "SOLUSDC"
