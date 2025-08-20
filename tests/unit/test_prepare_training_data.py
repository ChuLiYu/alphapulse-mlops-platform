"""
Unit tests for prepare_training_data module.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from alphapulse.ml.prepare_training_data import (
    add_news_frequency_features,
    calculate_sentiment_features,
    prepare_features,
)


class TestCalculateSentimentFeatures:
    """Tests for sentiment feature calculation."""

    def test_empty_sentiment_data(self):
        """Test with no sentiment data."""
        price_df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
                "price": [50000, 51000, 49000, 52000, 53000],
            }
        )
        sentiment_df = pd.DataFrame()

        result = calculate_sentiment_features(price_df, sentiment_df)

        assert "sentiment_avg_24h" in result.columns
        assert "sentiment_volatility_24h" in result.columns
        assert "sentiment_momentum_24h" in result.columns
        assert (result["sentiment_avg_24h"] == 0).all()

    def test_sentiment_feature_calculation(self):
        """Test sentiment feature calculation with data."""
        price_df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=48, freq="h"),
                "price": [50000] * 48,
            }
        )

        sentiment_df = pd.DataFrame(
            {
                "sentiment_score": [0.5, -0.3, 0.8, 0.2] * 12,
                "analyzed_at": pd.date_range("2024-01-01", periods=48, freq="h"),
            }
        )

        result = calculate_sentiment_features(price_df, sentiment_df)

        assert len(result) == len(price_df)
        assert not result["sentiment_avg_24h"].isna().all()
        assert "sentiment_volatility_24h" in result.columns

    def test_sentiment_edge_cases(self):
        """Test edge cases in sentiment calculation."""
        # Single data point
        price_df = pd.DataFrame({"timestamp": [datetime(2024, 1, 1)], "price": [50000]})

        sentiment_df = pd.DataFrame(
            {"sentiment_score": [0.5], "analyzed_at": [datetime(2024, 1, 1)]}
        )

        result = calculate_sentiment_features(price_df, sentiment_df)
        assert len(result) == 1


class TestCalculateNewsFrequencyFeatures:
    """Tests for news frequency feature calculation."""

    @patch("alphapulse.ml.prepare_training_data.create_engine")
    def test_news_frequency_calculation(self, mock_engine):
        """Test news frequency feature calculation."""
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=10, freq="D"),
                "price": [50000] * 10,
            }
        )

        # Mock database query results
        mock_conn = MagicMock()
        mock_engine.return_value.connect.return_value = mock_conn

        mock_news = pd.DataFrame(
            {
                "published_at": pd.date_range("2024-01-01", periods=20, freq="12h"),
                "source": ["CoinDesk"] * 10 + ["Cointelegraph"] * 10,
                "id": range(20),
            }
        )

        with patch("pandas.read_sql", return_value=mock_news):
            result = add_news_frequency_features(df)

        assert "news_count_24h" in result.columns
        assert "news_velocity_24h" in result.columns
        assert "news_count_1h" in result.columns

    def test_no_news_data(self):
        """Test with no news data."""
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
                "price": [50000] * 5,
            }
        )

        with patch("pandas.read_sql", return_value=pd.DataFrame()):
            result = add_news_frequency_features(df)

        # Should add placeholder features
        assert "news_count_24h" in result.columns
        assert (result["news_count_24h"] == 0).all()


# class TestCalculateInteractionFeatures:
#     """Tests for interaction feature calculation."""
#     # These features are calculated inline in prepare_features()
#     # No separate function to test


class TestPrepareFeatures:
    """Tests for overall feature preparation."""

    def test_prepare_features_basic(self):
        """Test basic feature preparation."""
        df_prices = pd.DataFrame(
            {
                "symbol": ["BTC-USD"] * 5,
                "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
                "price": [50000, 51000, 49000, 52000, 53000],
                "volume": [1000000] * 5,
            }
        )

        df_indicators = pd.DataFrame(
            {
                "symbol": ["BTC-USD"] * 5,
                "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
                "rsi_14": [50, 55, 45, 60, 58],
                "macd": [100, 120, 90, 130, 125],
                "sma_7": [50000] * 5,
            }
        )

        result = prepare_features(df_prices, df_indicators, df_sentiment=None)

        assert "price" in result.columns
        assert "rsi_14" in result.columns
        assert "target" in result.columns
        assert "sentiment_avg_24h" in result.columns
        assert len(result) > 0

    def test_target_calculation(self):
        """Test target (next day return) calculation."""
        df_prices = pd.DataFrame(
            {
                "symbol": ["BTC-USD"] * 5,
                "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
                "price": [
                    100,
                    110,
                    105,
                    115,
                    120,
                ],  # Simple prices for easy calculation
                "volume": [1000000] * 5,
            }
        )

        df_indicators = pd.DataFrame(
            {
                "symbol": ["BTC-USD"] * 5,
                "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
                "rsi_14": [50] * 5,
                "macd": [0] * 5,
                "sma_7": [100] * 5,
            }
        )

        result = prepare_features(df_prices, df_indicators)

        # Check target calculation (should be next day's return)
        assert "target" in result.columns
        # First target should be ~0.1 (10% increase from 100 to 110)
        assert result["target"].iloc[0] == pytest.approx(0.1, abs=0.01)


class TestDataQuality:
    """Tests for data quality checks."""

    def test_no_nan_in_features(self):
        """Test that feature preparation handles NaN values."""
        df_prices = pd.DataFrame(
            {
                "symbol": ["BTC-USD"] * 5,
                "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
                "price": [50000, 51000, None, 52000, 53000],
                "volume": [1000000] * 5,
            }
        )

        df_indicators = pd.DataFrame(
            {
                "symbol": ["BTC-USD"] * 5,
                "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
                "rsi_14": [50, 55, 45, 60, 58],
                "macd": [100, 120, 90, 130, 125],
                "sma_7": [50000] * 5,
            }
        )

        result = prepare_features(df_prices, df_indicators)

        # After cleanup, no NaN should remain (except possibly in target for last row)
        non_target_cols = [c for c in result.columns if c != "target"]
        assert not result[non_target_cols].isna().any().any()

    def test_timestamp_ordering(self):
        """Test that data is properly ordered by timestamp."""
        df_prices = pd.DataFrame(
            {
                "symbol": ["BTC-USD"] * 5,
                "timestamp": pd.date_range(
                    "2024-01-05", periods=5, freq="-1D"
                ),  # Reverse order
                "price": [50000, 51000, 49000, 52000, 53000],
                "volume": [1000000] * 5,
            }
        )

        df_indicators = pd.DataFrame(
            {
                "symbol": ["BTC-USD"] * 5,
                "timestamp": pd.date_range("2024-01-05", periods=5, freq="-1D"),
                "rsi_14": [50, 55, 45, 60, 58],
                "macd": [100, 120, 90, 130, 125],
                "sma_7": [50000] * 5,
            }
        )

        result = prepare_features(df_prices, df_indicators)

        # Should be sorted in ascending order
        assert result["timestamp"].is_monotonic_increasing
