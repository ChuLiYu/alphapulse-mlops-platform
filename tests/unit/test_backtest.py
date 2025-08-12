"""
Unit tests for AlphaPulse backtesting framework.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from alphapulse.ml.backtest import (
    BacktestConfig,
    Backtester,
    BacktestResult,
    Signal,
    Trade,
)


class MockModel:
    """Mock ML model for testing."""

    def __init__(self, predictions: list = None):
        """Initialize with optional fixed predictions."""
        self.predictions = predictions or [0.002, -0.002, 0.001, -0.001, 0.003]
        self.call_count = 0

    def predict(self, X):
        """Return mock predictions."""
        pred = self.predictions[self.call_count % len(self.predictions)]
        self.call_count += 1
        return np.array([pred])


class TestBacktestConfig:
    """Tests for BacktestConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = BacktestConfig()
        assert config.initial_capital == Decimal("10000.00")
        assert config.transaction_cost_pct == Decimal("0.001")
        assert config.risk_free_rate == Decimal("0.02")

    def test_custom_config(self):
        """Test custom configuration values."""
        config = BacktestConfig(
            initial_capital=Decimal("50000"), transaction_cost_pct=Decimal("0.002")
        )
        assert config.initial_capital == Decimal("50000")
        assert config.transaction_cost_pct == Decimal("0.002")

    def test_float_to_decimal_conversion(self):
        """Test that float values are converted to Decimal."""
        config = BacktestConfig(initial_capital=10000.0, transaction_cost_pct=0.001)
        assert isinstance(config.initial_capital, Decimal)
        assert isinstance(config.transaction_cost_pct, Decimal)


class TestSignalGeneration:
    """Tests for signal generation logic."""

    def test_buy_signal(self):
        """Test BUY signal generation."""
        model = MockModel([0.005])  # 0.5% predicted return
        backtester = Backtester(model)
        signal = backtester.generate_signal(0.005)
        assert signal == Signal.BUY

    def test_sell_signal(self):
        """Test SELL signal generation."""
        model = MockModel([-0.005])
        backtester = Backtester(model)
        signal = backtester.generate_signal(-0.005)
        assert signal == Signal.SELL

    def test_hold_signal(self):
        """Test HOLD signal generation."""
        model = MockModel([0.0005])  # Below threshold
        backtester = Backtester(model)
        signal = backtester.generate_signal(0.0005)
        assert signal == Signal.HOLD


class TestTransactionCost:
    """Tests for transaction cost calculation."""

    def test_transaction_cost_calculation(self):
        """Test transaction cost is calculated correctly."""
        model = MockModel()
        config = BacktestConfig(transaction_cost_pct=Decimal("0.001"))
        backtester = Backtester(model, config)

        trade_value = Decimal("10000")
        cost = backtester.calculate_transaction_cost(trade_value)

        assert cost == Decimal("10.00000000")  # 0.1% of 10000

    def test_zero_transaction_cost(self):
        """Test zero transaction cost."""
        model = MockModel()
        config = BacktestConfig(transaction_cost_pct=Decimal("0"))
        backtester = Backtester(model, config)

        cost = backtester.calculate_transaction_cost(Decimal("10000"))
        assert cost == Decimal("0")


class TestBacktestResult:
    """Tests for BacktestResult."""

    def test_result_to_dict(self):
        """Test result serialization to dict."""
        result = BacktestResult(
            total_return=Decimal("0.15"),
            sharpe_ratio=Decimal("1.5"),
            max_drawdown=Decimal("0.10"),
            win_rate=Decimal("0.60"),
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            final_portfolio_value=Decimal("11500.00"),
            initial_capital=Decimal("10000.00"),
        )

        result_dict = result.to_dict()

        assert result_dict["total_return"] == "0.15"
        assert result_dict["sharpe_ratio"] == "1.5"
        assert result_dict["max_drawdown"] == "0.10"
        assert result_dict["win_rate"] == "0.60"
        assert result_dict["total_trades"] == 10


class TestBacktester:
    """Integration tests for Backtester."""

    @pytest.fixture
    def sample_test_data(self):
        """Create sample test data."""
        dates = pd.date_range(start="2025-01-01", periods=30, freq="D")
        data = {
            "timestamp": dates,
            "symbol": ["BTCUSD"] * 30,
            "price": [50000 + i * 100 for i in range(30)],  # Increasing prices
            "volume": [1000] * 30,
            "rsi_14": [50 + i % 20 for i in range(30)],
            "macd": [0.1 * (i % 10 - 5) for i in range(30)],
            "target": [0.002] * 30,  # Dummy target
        }
        return pd.DataFrame(data)

    def test_backtest_runs_without_error(self, sample_test_data):
        """Test that backtest runs without errors."""
        model = MockModel([0.002, -0.002, 0.001])  # Alternating signals
        backtester = Backtester(model)

        result = backtester.run(sample_test_data)

        assert isinstance(result, BacktestResult)
        assert result.initial_capital == Decimal("10000.00")

    def test_backtest_with_no_trades(self, sample_test_data):
        """Test backtest when all predictions are HOLD signals."""
        model = MockModel([0.0001])  # Below threshold - always HOLD
        backtester = Backtester(model)

        result = backtester.run(sample_test_data)

        assert result.total_trades == 0
        assert result.winning_trades == 0
        assert result.losing_trades == 0

    def test_portfolio_value_tracking(self, sample_test_data):
        """Test that portfolio values are tracked correctly."""
        model = MockModel([0.005])  # Always BUY
        backtester = Backtester(model)

        result = backtester.run(sample_test_data)

        # Should have portfolio values for each day + initial
        assert len(backtester.portfolio_values) == len(sample_test_data) + 1

    def test_max_drawdown_calculation(self, sample_test_data):
        """Test max drawdown is non-negative."""
        model = MockModel([0.002, -0.002])
        backtester = Backtester(model)

        result = backtester.run(sample_test_data)

        assert result.max_drawdown >= Decimal("0")
        assert result.max_drawdown <= Decimal("1")

    def test_sharpe_ratio_calculation(self, sample_test_data):
        """Test Sharpe ratio is calculated."""
        model = MockModel([0.002, -0.002, 0.003])
        backtester = Backtester(model)

        result = backtester.run(sample_test_data)

        # Sharpe could be positive, negative, or zero
        assert isinstance(result.sharpe_ratio, Decimal)


class TestTrade:
    """Tests for Trade dataclass."""

    def test_trade_creation(self):
        """Test Trade object creation."""
        trade = Trade(
            timestamp=datetime.now(),
            signal=Signal.BUY,
            price=Decimal("50000"),
            shares=Decimal("0.2"),
            cost=Decimal("10"),
            portfolio_value=Decimal("10000"),
        )

        assert trade.signal == Signal.BUY
        assert trade.price == Decimal("50000")
        assert trade.shares == Decimal("0.2")
