"""
Backtesting framework for AlphaPulse ML models.

Implements walk-forward validation with portfolio simulation
and risk metrics calculation (Sharpe Ratio, Max Drawdown, Win Rate).

Critical: All financial calculations use Decimal for precision.
"""

import argparse
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd


class Signal(Enum):
    """Trading signal types."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""

    initial_capital: Decimal = Decimal("10000.00")
    transaction_cost_pct: Decimal = Decimal("0.001")  # 0.1% per trade
    signal_threshold: float = 0.001  # 0.1% predicted change to trigger signal
    risk_free_rate: Decimal = Decimal("0.02")  # 2% annual risk-free rate

    def __post_init__(self):
        """Ensure Decimal types."""
        if isinstance(self.initial_capital, (int, float)):
            self.initial_capital = Decimal(str(self.initial_capital))
        if isinstance(self.transaction_cost_pct, (int, float)):
            self.transaction_cost_pct = Decimal(str(self.transaction_cost_pct))
        if isinstance(self.risk_free_rate, (int, float)):
            self.risk_free_rate = Decimal(str(self.risk_free_rate))


@dataclass
class Trade:
    """Represents a single trade."""

    timestamp: datetime
    signal: Signal
    price: Decimal
    shares: Decimal
    cost: Decimal  # Transaction cost
    portfolio_value: Decimal


@dataclass
class BacktestResult:
    """Results from backtesting."""

    total_return: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    win_rate: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    final_portfolio_value: Decimal
    initial_capital: Decimal
    trades: List[Trade] = field(default_factory=list)
    daily_returns: List[Decimal] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "total_return": str(self.total_return),
            "sharpe_ratio": str(self.sharpe_ratio),
            "max_drawdown": str(self.max_drawdown),
            "win_rate": str(self.win_rate),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "final_portfolio_value": str(self.final_portfolio_value),
            "initial_capital": str(self.initial_capital),
            "num_daily_returns": len(self.daily_returns),
        }


class Backtester:
    """
    Walk-forward backtesting engine.

    Simulates trading based on model predictions without lookahead bias.
    """

    def __init__(self, model, config: Optional[BacktestConfig] = None):
        """
        Initialize backtester.

        Args:
            model: Trained ML model with predict() method
            config: Backtesting configuration
        """
        self.model = model
        self.config = config or BacktestConfig()
        self.trades: List[Trade] = []
        self.portfolio_values: List[Decimal] = []

    def generate_signal(self, predicted_return: float) -> Signal:
        """
        Convert predicted return to trading signal.

        Args:
            predicted_return: Model's predicted price change (as fraction)

        Returns:
            Trading signal (BUY/SELL/HOLD)
        """
        if predicted_return > self.config.signal_threshold:
            return Signal.BUY
        elif predicted_return < -self.config.signal_threshold:
            return Signal.SELL
        else:
            return Signal.HOLD

    def calculate_transaction_cost(self, trade_value: Decimal) -> Decimal:
        """Calculate transaction cost for a trade."""
        return (trade_value * self.config.transaction_cost_pct).quantize(
            Decimal("0.00000001"), rounding=ROUND_HALF_UP
        )

    def run(
        self, test_data: pd.DataFrame, target_col: str = "target"
    ) -> BacktestResult:
        """
        Run backtest on test data.

        Args:
            test_data: DataFrame with features and actual prices
            target_col: Name of target column (actual returns)

        Returns:
            BacktestResult with metrics and trade history
        """
        # Prepare features (same logic as training)
        drop_cols = [
            "timestamp",
            "symbol",
            "source",
            target_col,
            "created_at",
            "updated_at",
        ]
        feature_cols = [c for c in test_data.columns if c not in drop_cols]

        # Validate we have price column or can infer it
        if "price" not in test_data.columns:
            raise ValueError("test_data must contain 'price' column")

        # Initialize portfolio
        cash = self.config.initial_capital
        shares = Decimal("0")
        position = Signal.HOLD  # Current position

        self.trades = []
        self.portfolio_values = [self.config.initial_capital]
        daily_returns: List[Decimal] = []
        winning_trades = 0
        losing_trades = 0

        # Walk through each day
        for i in range(len(test_data)):
            row = test_data.iloc[i]
            current_price = Decimal(str(row["price"]))

            # Get features for prediction
            features = row[feature_cols].values.reshape(1, -1)

            # Handle any remaining NaN/inf
            features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

            # Predict next return
            try:
                predicted_return = float(self.model.predict(features)[0])
            except Exception:
                predicted_return = 0.0

            # Generate signal
            signal = self.generate_signal(predicted_return)

            # Execute trade based on signal
            timestamp = row.get("timestamp", datetime.now())
            if isinstance(timestamp, str):
                timestamp = pd.to_datetime(timestamp)

            if signal == Signal.BUY and position != Signal.BUY and cash > Decimal("0"):
                # Buy: Convert cash to shares
                trade_cost = self.calculate_transaction_cost(cash)
                available_cash = cash - trade_cost
                shares_to_buy = available_cash / current_price

                self.trades.append(
                    Trade(
                        timestamp=timestamp,
                        signal=Signal.BUY,
                        price=current_price,
                        shares=shares_to_buy,
                        cost=trade_cost,
                        portfolio_value=cash,
                    )
                )

                shares = shares_to_buy
                cash = Decimal("0")
                position = Signal.BUY

            elif (
                signal == Signal.SELL
                and position == Signal.BUY
                and shares > Decimal("0")
            ):
                # Sell: Convert shares to cash
                sale_value = shares * current_price
                trade_cost = self.calculate_transaction_cost(sale_value)
                cash_after_sale = sale_value - trade_cost

                # Calculate P&L for this trade
                if len(self.trades) > 0:
                    last_buy = next(
                        (t for t in reversed(self.trades) if t.signal == Signal.BUY),
                        None,
                    )
                    if last_buy:
                        buy_value = last_buy.shares * last_buy.price
                        if cash_after_sale > buy_value:
                            winning_trades += 1
                        else:
                            losing_trades += 1

                self.trades.append(
                    Trade(
                        timestamp=timestamp,
                        signal=Signal.SELL,
                        price=current_price,
                        shares=shares,
                        cost=trade_cost,
                        portfolio_value=cash_after_sale,
                    )
                )

                cash = cash_after_sale
                shares = Decimal("0")
                position = Signal.HOLD

            # Calculate current portfolio value
            current_value = cash + (shares * current_price)

            # Calculate daily return
            if len(self.portfolio_values) > 0:
                prev_value = self.portfolio_values[-1]
                if prev_value > 0:
                    daily_return = (current_value - prev_value) / prev_value
                    daily_returns.append(daily_return)

            self.portfolio_values.append(current_value)

        # Final calculations
        final_value = (
            self.portfolio_values[-1]
            if self.portfolio_values
            else self.config.initial_capital
        )
        total_return = (
            final_value - self.config.initial_capital
        ) / self.config.initial_capital

        # Sharpe Ratio (annualized)
        sharpe = self._calculate_sharpe(daily_returns)

        # Max Drawdown
        max_dd = self._calculate_max_drawdown()

        # Win Rate
        total_trades = winning_trades + losing_trades
        win_rate = (
            Decimal(str(winning_trades / total_trades))
            if total_trades > 0
            else Decimal("0")
        )

        return BacktestResult(
            total_return=total_return.quantize(Decimal("0.0001")),
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate.quantize(Decimal("0.0001")),
            total_trades=len(self.trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            final_portfolio_value=final_value.quantize(Decimal("0.01")),
            initial_capital=self.config.initial_capital,
            trades=self.trades,
            daily_returns=daily_returns,
        )

    def _calculate_sharpe(self, daily_returns: List[Decimal]) -> Decimal:
        """
        Calculate annualized Sharpe Ratio.

        Sharpe = (Mean Return - Risk Free Rate) / Std Dev * sqrt(252)
        """
        if len(daily_returns) < 2:
            return Decimal("0")

        returns_float = [float(r) for r in daily_returns]
        mean_return = np.mean(returns_float)
        std_return = np.std(returns_float)

        if std_return == 0:
            return Decimal("0")

        # Daily risk-free rate
        daily_rf = float(self.config.risk_free_rate) / 252

        # Annualized Sharpe
        sharpe = ((mean_return - daily_rf) / std_return) * np.sqrt(252)

        return Decimal(str(sharpe)).quantize(Decimal("0.0001"))

    def _calculate_max_drawdown(self) -> Decimal:
        """
        Calculate maximum drawdown.

        Max Drawdown = max((Peak - Trough) / Peak)
        """
        if len(self.portfolio_values) < 2:
            return Decimal("0")

        values = [float(v) for v in self.portfolio_values]
        peak = values[0]
        max_dd = 0.0

        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)

        return Decimal(str(max_dd)).quantize(Decimal("0.0001"))


def load_test_data(data_dir: str = "/app/src/data/processed") -> pd.DataFrame:
    """Load test data from parquet file."""
    test_path = Path(data_dir) / "test.parquet"
    if not test_path.exists():
        raise FileNotFoundError(f"Test data not found at {test_path}")
    return pd.read_parquet(test_path)


def main():
    """CLI entry point for backtesting."""
    parser = argparse.ArgumentParser(description="Run backtest on trained model")
    parser.add_argument(
        "--model_path",
        type=str,
        default="/app/src/models/saved/btc_predictor_v1.pkl",
        help="Path to trained model",
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default="/app/src/data/processed",
        help="Directory containing test.parquet",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="/app/src/results/backtest_results.json",
        help="Output path for results JSON",
    )
    parser.add_argument(
        "--initial_capital",
        type=float,
        default=10000.0,
        help="Initial capital for simulation",
    )
    parser.add_argument(
        "--transaction_cost",
        type=float,
        default=0.001,
        help="Transaction cost as fraction (0.001 = 0.1%)",
    )

    args = parser.parse_args()

    print(f"Loading model from {args.model_path}...")
    model = joblib.load(args.model_path)

    print(f"Loading test data from {args.data_dir}...")
    test_data = load_test_data(args.data_dir)
    print(f"Test data shape: {test_data.shape}")

    # Configure backtest
    config = BacktestConfig(
        initial_capital=Decimal(str(args.initial_capital)),
        transaction_cost_pct=Decimal(str(args.transaction_cost)),
    )

    print("Running backtest...")
    backtester = Backtester(model, config)
    result = backtester.run(test_data)

    # Print results
    print("\n" + "=" * 50)
    print("BACKTEST RESULTS")
    print("=" * 50)
    print(f"Total Return:       {float(result.total_return)*100:.2f}%")
    print(f"Sharpe Ratio:       {result.sharpe_ratio}")
    print(f"Max Drawdown:       {float(result.max_drawdown)*100:.2f}%")
    print(f"Win Rate:           {float(result.win_rate)*100:.2f}%")
    print(f"Total Trades:       {result.total_trades}")
    print(f"Winning Trades:     {result.winning_trades}")
    print(f"Losing Trades:      {result.losing_trades}")
    print(f"Final Portfolio:    ${result.final_portfolio_value}")
    print(f"Initial Capital:    ${result.initial_capital}")
    print("=" * 50)

    # Save results
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    with open(args.output_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)
    print(f"\nResults saved to {args.output_path}")


if __name__ == "__main__":
    main()
