"""
Unit tests for auto_train module.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import json
import tempfile
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import joblib
import numpy as np
import pandas as pd
import pytest

from alphapulse.ml.auto_train import (
    DEFAULT_MODELS,
    DEFAULT_THRESHOLDS,
    AutoTrainer,
    ModelConfig,
)


@pytest.fixture
def sample_training_data():
    """Create sample training data."""
    np.random.seed(42)
    n = 100

    data = {
        "timestamp": pd.date_range("2024-01-01", periods=n, freq="D"),
        "price": 50000 + np.cumsum(np.random.randn(n) * 100),
        "volume": np.random.randint(1000000, 2000000, n),
        "rsi_14": np.random.uniform(30, 70, n),
        "macd": np.random.randn(n) * 100,
        "sentiment_avg_24h": np.random.uniform(-0.5, 0.5, n),
        "target": np.random.randn(n) * 0.01,  # 1% daily returns
    }

    df = pd.DataFrame(data)

    # Create train/val/test splits
    train = df.iloc[:70]
    val = df.iloc[70:85]
    test = df.iloc[85:]

    return train, val, test


@pytest.fixture
def temp_data_dir(sample_training_data):
    """Create temporary directory with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()

        train, val, test = sample_training_data
        train.to_parquet(data_dir / "train.parquet")
        val.to_parquet(data_dir / "val.parquet")
        test.to_parquet(data_dir / "test.parquet")

        yield data_dir


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "models"
        output_dir.mkdir()
        yield output_dir


class TestModelConfig:
    """Tests for ModelConfig."""

    def test_model_config_creation(self):
        """Test creating model configuration."""
        from sklearn.linear_model import Ridge

        config = ModelConfig(
            name="test_model", model_class=Ridge, params={"alpha": 1.0}
        )

        assert config.name == "test_model"
        assert config.model_class == Ridge
        assert config.params["alpha"] == 1.0

    def test_default_models_list(self):
        """Test that default models list is properly configured."""
        assert len(DEFAULT_MODELS) > 0

        for model_config in DEFAULT_MODELS:
            assert hasattr(model_config, "name")
            assert hasattr(model_config, "model_class")
            assert hasattr(model_config, "params")
            assert isinstance(model_config.params, dict)


class TestAutoTrainer:
    """Tests for AutoTrainer class."""

    def test_initialization(self, temp_data_dir, temp_output_dir):
        """Test AutoTrainer initialization."""
        trainer = AutoTrainer(
            data_dir=str(temp_data_dir), output_dir=str(temp_output_dir)
        )

        assert trainer.data_dir == temp_data_dir
        assert trainer.output_dir == temp_output_dir
        assert trainer.results == []
        assert trainer.best_result is None

    def test_load_data(self, temp_data_dir, temp_output_dir):
        """Test data loading."""
        trainer = AutoTrainer(
            data_dir=str(temp_data_dir), output_dir=str(temp_output_dir)
        )

        trainer.load_data()

        assert hasattr(trainer, "train")
        assert hasattr(trainer, "val")
        assert hasattr(trainer, "test")
        assert len(trainer.X_train) == 70
        assert len(trainer.X_val) == 15
        assert "target" not in trainer.X_train.columns

    def test_train_single_model(self, temp_data_dir, temp_output_dir):
        """Test training a single model using train_and_evaluate."""
        from sklearn.linear_model import Ridge

        trainer = AutoTrainer(
            data_dir=str(temp_data_dir), output_dir=str(temp_output_dir)
        )
        trainer.load_data()

        model_config = ModelConfig(
            name="test_ridge", model_class=Ridge, params={"alpha": 1.0}
        )

        with patch("alphapulse.ml.auto_train.Backtester") as mock_backtester:
            mock_result = Mock()
            mock_result.sharpe_ratio = 1.5
            mock_result.total_return_pct = 20.0
            mock_result.total_return = 0.20  # As decimal
            mock_result.win_rate = 0.60  # 60%
            mock_result.max_drawdown_pct = -10.0
            mock_result.max_drawdown = -0.10  # As decimal
            mock_result.total_trades = 10
            mock_backtester.return_value.run.return_value = mock_result

            result = trainer.train_and_evaluate(
                model_config=model_config, threshold=0.001
            )

        assert "model" in result
        assert "sharpe_ratio" in result
        assert result["sharpe_ratio"] == 1.5
        assert result["total_return"] == 0.20
        assert result["win_rate"] == 0.60

    def test_select_best_model(self, temp_data_dir, temp_output_dir):
        """Test best model selection logic."""
        # Test that we can sort results by sharpe_ratio
        results = [
            {
                "model_name": "model1",
                "threshold": 0.001,
                "sharpe_ratio": 0.5,
                "total_return_pct": 10.0,
            },
            {
                "model_name": "model2",
                "threshold": 0.002,
                "sharpe_ratio": 1.5,
                "total_return_pct": 20.0,
            },
            {
                "model_name": "model3",
                "threshold": 0.001,
                "sharpe_ratio": 0.8,
                "total_return_pct": 15.0,
            },
        ]

        # Sort by sharpe_ratio descending (mimics what run() does)
        sorted_results = sorted(results, key=lambda x: x["sharpe_ratio"], reverse=True)
        best = sorted_results[0]

        assert best["model_name"] == "model2"
        assert best["sharpe_ratio"] == 1.5

    def test_save_best_model(self, temp_data_dir, temp_output_dir):
        """Test that model saving works via joblib."""
        from sklearn.linear_model import Ridge

        trainer = AutoTrainer(
            data_dir=str(temp_data_dir), output_dir=str(temp_output_dir)
        )
        trainer.load_data()

        # Train a simple model
        model = Ridge(alpha=1.0)
        model.fit(trainer.X_train, trainer.y_train)

        # Save model directly (test joblib functionality)
        model_path = temp_output_dir / "test_model.pkl"
        joblib.dump(model, model_path)

        # Verify model can be loaded
        loaded_model = joblib.load(model_path)
        assert loaded_model is not None

        # Verify predictions match
        original_pred = model.predict(trainer.X_train[:5])
        loaded_pred = loaded_model.predict(trainer.X_train[:5])
        assert np.allclose(original_pred, loaded_pred)


class TestThresholds:
    """Tests for threshold configurations."""

    def test_default_thresholds(self):
        """Test that default thresholds are properly configured."""
        assert len(DEFAULT_THRESHOLDS) > 0
        assert all(isinstance(t, float) for t in DEFAULT_THRESHOLDS)
        assert all(t > 0 for t in DEFAULT_THRESHOLDS)
        # Should be in ascending order
        assert DEFAULT_THRESHOLDS == sorted(DEFAULT_THRESHOLDS)


class TestIntegrationWithBacktest:
    """Integration tests with backtesting module."""

    def test_backtest_integration(self, temp_data_dir, temp_output_dir):
        """Test integration with backtesting via train_and_evaluate."""
        from sklearn.linear_model import Ridge

        with patch("alphapulse.ml.auto_train.Backtester") as mock_backtester:
            # Mock backtest result with all required attributes
            mock_result = Mock()
            mock_result.sharpe_ratio = 1.5
            mock_result.total_return_pct = 20.0
            mock_result.total_return = 0.20  # As decimal
            mock_result.win_rate = 0.60  # 60%
            mock_result.max_drawdown_pct = -10.0
            mock_result.max_drawdown = -0.10  # As decimal
            mock_result.total_trades = 10

            mock_backtester_instance = Mock()
            mock_backtester_instance.run.return_value = mock_result
            mock_backtester.return_value = mock_backtester_instance

            trainer = AutoTrainer(
                data_dir=str(temp_data_dir), output_dir=str(temp_output_dir)
            )
            trainer.load_data()

            model_config = ModelConfig(
                name="test_model", model_class=Ridge, params={"alpha": 1.0}
            )

            result = trainer.train_and_evaluate(model_config, threshold=0.001)

            assert result["sharpe_ratio"] == 1.5
            assert result["total_return"] == 0.20
            assert result["win_rate"] == 0.60
            assert mock_backtester.called
