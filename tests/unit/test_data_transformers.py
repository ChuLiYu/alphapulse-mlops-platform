"""
Unit tests for data transformation functionality.
"""

import pandas as pd
import pytest


@pytest.mark.unit
class TestDataTransformers:
    """Test data transformation functionality."""

    def test_dataframe_creation(self):
        """Test basic DataFrame creation and manipulation."""
        data = {
            "title": ["Article 1", "Article 2"],
            "sentiment_score": [0.8, -0.3],
            "source": ["CoinDesk", "Cointelegraph"],
        }

        df = pd.DataFrame(data)

        assert len(df) == 2
        assert list(df.columns) == ["title", "sentiment_score", "source"]
        assert df["sentiment_score"].mean() == 0.25

    def test_sentiment_score_normalization(self):
        """Test sentiment score normalization to [-1, 1] range."""
        scores = [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0]

        # Normalize to [-1, 1] range
        normalized = [max(-1.0, min(1.0, score)) for score in scores]

        expected = [-1.0, -1.0, -0.5, 0.0, 0.5, 1.0, 1.0]
        assert normalized == expected

    def test_missing_value_handling(self):
        """Test handling of missing values in data."""
        data = {
            "title": ["Article 1", None, "Article 3"],
            "sentiment_score": [0.8, None, -0.3],
            "source": ["CoinDesk", "Cointelegraph", None],
        }

        df = pd.DataFrame(data)

        # Check missing values
        assert df["title"].isna().sum() == 1
        assert df["sentiment_score"].isna().sum() == 1
        assert df["source"].isna().sum() == 1

        # Fill missing values
        df_filled = df.fillna(
            {"title": "Unknown", "sentiment_score": 0.0, "source": "Unknown"}
        )

        assert df_filled["title"].isna().sum() == 0
        assert df_filled["sentiment_score"].isna().sum() == 0
        assert df_filled["source"].isna().sum() == 0

    def test_datetime_conversion(self):
        """Test datetime conversion and formatting."""
        from datetime import datetime

        timestamps = [
            "2026-01-10 06:00:00",
            "2026-01-10 06:05:00",
            "2026-01-10 06:10:00",
        ]

        df = pd.DataFrame({"timestamp": timestamps})
        df["datetime"] = pd.to_datetime(df["timestamp"])

        assert df["datetime"].dt.year.iloc[0] == 2026
        assert df["datetime"].dt.month.iloc[0] == 1
        assert df["datetime"].dt.day.iloc[0] == 10

        # Test time difference
        time_diff = df["datetime"].iloc[1] - df["datetime"].iloc[0]
        assert time_diff.total_seconds() == 300  # 5 minutes

    def test_sentiment_categorization(self):
        """Test categorization of sentiment scores."""
        scores = [-0.9, -0.3, -0.1, 0.0, 0.1, 0.3, 0.9]

        categories = []
        for score in scores:
            if score > 0.2:
                categories.append("positive")
            elif score < -0.2:
                categories.append("negative")
            else:
                categories.append("neutral")

        expected = [
            "negative",
            "negative",
            "neutral",
            "neutral",
            "neutral",
            "positive",
            "positive",
        ]
        assert categories == expected

    def test_data_aggregation(self):
        """Test data aggregation by source."""
        data = {
            "source": [
                "CoinDesk",
                "CoinDesk",
                "Cointelegraph",
                "Cointelegraph",
                "CoinDesk",
            ],
            "sentiment_score": [0.8, 0.6, -0.3, 0.2, 0.9],
        }

        df = pd.DataFrame(data)

        # Group by source and calculate statistics
        grouped = (
            df.groupby("source")["sentiment_score"]
            .agg(["mean", "count", "std"])
            .round(3)
        )

        assert len(grouped) == 2
        assert grouped.loc["CoinDesk", "count"] == 3
        assert grouped.loc["Cointelegraph", "count"] == 2
        assert 0.7 < grouped.loc["CoinDesk", "mean"] < 0.8

    def test_outlier_detection(self):
        """Test detection of outlier sentiment scores."""
        scores = [-1.5, -0.8, -0.3, 0.0, 0.2, 0.7, 1.8]

        # Identify outliers (outside [-1, 1] range)
        outliers = [score for score in scores if score < -1.0 or score > 1.0]
        valid_scores = [score for score in scores if -1.0 <= score <= 1.0]

        assert outliers == [-1.5, 1.8]
        assert len(valid_scores) == 5

    def test_text_preprocessing(self):
        """Test text preprocessing for sentiment analysis."""
        texts = [
            "BITCOIN TO THE MOON! 🚀",
            "bitcoin crashed 20% today...",
            "Bitcoin price stable at $40k.",
        ]

        # Simple preprocessing: lowercase
        processed = [text.lower() for text in texts]

        expected = [
            "bitcoin to the moon! 🚀",
            "bitcoin crashed 20% today...",
            "bitcoin price stable at $40k.",
        ]

        assert processed == expected

        # Remove punctuation (simple version)
        cleaned = [
            text.replace("!", "").replace(".", "").replace("...", "")
            for text in processed
        ]

        assert "!" not in cleaned[0]
        assert "..." not in cleaned[1]

    def test_data_validation(self):
        """Test data validation rules."""
        data = {
            "title": ["Valid Title", "", "Another Title"],  # One empty title
            "url": ["https://example.com", "invalid-url", "https://test.com"],
            "sentiment_score": [0.8, 1.5, -0.3],  # One invalid score
        }

        df = pd.DataFrame(data)

        # Validation checks
        valid_titles = df["title"].str.strip().ne("")
        valid_urls = df["url"].str.startswith("http")
        valid_scores = df["sentiment_score"].between(-1.0, 1.0)

        assert valid_titles.sum() == 2  # One invalid (empty)
        assert valid_urls.sum() == 2  # One invalid (no http)
        assert valid_scores.sum() == 2  # One invalid (1.5 > 1.0)

    def test_performance_data_transformation(self):
        """Test performance of data transformation operations."""
        import time

        # Create larger dataset
        n_rows = 1000
        data = {
            "title": [f"Article {i}" for i in range(n_rows)],
            "sentiment_score": [
                i / 1000 - 0.5 for i in range(n_rows)
            ],  # Scores from -0.5 to 0.5
            "source": [
                "CoinDesk" if i % 2 == 0 else "Cointelegraph" for i in range(n_rows)
            ],
        }

        start_time = time.time()

        df = pd.DataFrame(data)

        # Perform operations
        df["sentiment_category"] = df["sentiment_score"].apply(
            lambda x: "positive" if x > 0.2 else "negative" if x < -0.2 else "neutral"
        )

        grouped = df.groupby("source")["sentiment_score"].mean()

        elapsed_time = time.time() - start_time

        # Should complete quickly
        assert (
            elapsed_time < 1.0
        ), f"Transformation took {elapsed_time:.2f}s (should be < 1s)"
        assert len(grouped) == 2


@pytest.mark.unit
def test_pandas_operations():
    """Test various pandas operations used in transformations."""
    df = pd.DataFrame({"A": [1, 2, 3, 4, 5], "B": [10, 20, 30, 40, 50]})

    # Basic operations
    assert df["A"].sum() == 15
    assert df["B"].mean() == 30

    # Filtering
    filtered = df[df["A"] > 2]
    assert len(filtered) == 3

    # Sorting
    sorted_df = df.sort_values("A", ascending=False)
    assert sorted_df["A"].iloc[0] == 5

    # Adding columns
    df["C"] = df["A"] + df["B"]
    assert df["C"].iloc[0] == 11


@pytest.mark.unit
def test_sentiment_threshold_calculation():
    """Test calculation of sentiment thresholds."""
    # Use a symmetric distribution for clearer percentile calculation
    scores = [-0.9, -0.8, -0.7, -0.6, 0.6, 0.7, 0.8, 0.9]

    # Calculate percentiles
    import numpy as np

    q1 = np.percentile(scores, 25)
    median = np.percentile(scores, 50)
    q3 = np.percentile(scores, 75)

    assert q1 < median < q3
    # With this symmetric distribution, q1 should be around -0.75
    assert -0.8 <= q1 <= -0.7
    # Median should be around 0.0 (average of -0.6 and 0.6)
    assert -0.1 <= median <= 0.1
    # q3 should be around 0.75
    assert 0.7 <= q3 <= 0.8
