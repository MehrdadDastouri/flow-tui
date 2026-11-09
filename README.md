# flow-tui

[![CI](https://github.com/MehrdadDastouri/flow-tui/actions/workflows/ci.yml/badge.svg)](https://github.com/MehrdadDastouri/flow-tui/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Interface: Textual](https://img.shields.io/badge/UI-Textual-00d2ff.svg)](https://textual.textualize.io/)

A high-performance terminal user interface for real-time market microstructure telemetry, Level-2 order book tracking, and discrete Order Flow Imbalance (OFI) estimation.

---

## Architecture Overview

High-frequency market feeds distribute data at millisecond intervals. Direct coupling between ingestion routines and user interface repaint cycles introduces thread contention and downstream queue starvation. `flow-tui` addresses this latency disparity through temporal subsampling and asynchronous decoupling:

```text
                  [ Exchange WebSocket Gateway ]
                                │
                                ▼
                   MarketStreamClient (asyncio)
                                │
             ┌──────────────────┴──────────────────┐
             ▼                                     ▼
    Level-2 Depth Diffs                       Trade Prints
             │                                     │
             ▼                                     ▼
      OrderBook Engine                        CVD Tracker
             │                                     │
             └──────────────────┬──────────────────┘
                                ▼
                     PipelineCoordinator
                     (Telemetry State Hub)
                                │
                                ▼
                     [ OFICalculator Core ]
                                │
                 State Cache (Thread-Safe Memory)
                                │
             Fixed Refresh Interval (20 to 60 Hz)
                                ▼
                   FlowApp Dual-Panel Interface
                   ├── L2 Book Depth & Spread
                   └── CVD & OFI Instant Metrics
```

---

## Microstructural Foundations

### 1. Static Book Imbalance (OBI)
Snapshot imbalance reflects the distribution of resting passive quotes across the top of the book:

$$OBI_t = \frac{Q_t^b - Q_t^a}{Q_t^b + Q_t^a}$$

Where $Q_t^b$ and $Q_t^a$ represent resting bid and ask quantities at the best quotes.

### 2. Order Flow Imbalance (OFI)
Following the formulation established by Cont, Kukanov, and Stoikov (2014), the analytical engine evaluates discrete transitions across consecutive quote states alongside aggressive execution flow:

$$OFI_t = \Delta B_t - \Delta A_t$$

Where:
* $\Delta B_t = Q_t^b$ if $P_t^b > P_{t-1}^b$, and $\Delta B_t = Q_t^b - Q_{t-1}^b$ if $P_t^b = P_{t-1}^b$ (zero otherwise).
* $\Delta A_t = Q_t^a$ if $P_t^a < P_{t-1}^a$, and $\Delta A_t = Q_t^a - Q_{t-1}^a$ if $P_t^a = P_{t-1}^a$ (zero otherwise).

---

## Installation

Clone the repository and install the package in editable mode:

```bash
git clone [https://github.com/MehrdadDastouri/flow-tui.git](https://github.com/MehrdadDastouri/flow-tui.git)
cd flow-tui
pip install -e .
```

## Usage

Launch the terminal interface with default settings (ETHUSDC pair at 20 Hz display refresh rate):

```bash
flow-tui
```

### Command-Line Arguments

```text
usage: flow-tui [-h] [-s SYMBOL] [--fps FPS]

High-performance terminal telemetry for market microstructure.

options:
  -h, --help            show this help message and exit
  -s, --symbol SYMBOL   Target trading pair symbol (default: ETHUSDC)
  --fps FPS             Terminal UI refresh frequency in Hz (default: 20, max: 60)
```

To monitor BTCUSDT at 30 frames per second:

```bash
flow-tui --symbol BTCUSDT --fps 30
```

## Test Suite

Run unit tests across parsing, calculations, and the coordination pipeline:

```bash
pytest -v
```

## License

This project is distributed under the terms of the MIT License.
