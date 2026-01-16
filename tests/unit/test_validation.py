"""
Unit tests for validation utilities.

Tests WalkForwardCV, OutOfSampleValidator, and data leakage detection.
"""

import numpy as np
import pandas as pd
import pytest

from alphapulse.ml.validation import (
    WalkForwardCV,
    WalkForwardResult,
    OutOfSampleValidator,
    validate_no_data_leakage,
)


class TestWalkForwardCV:
    """Tests for Walk-Forward Cross-Validation."""

    @pytest.fixture
    def sample_df(self):
        """Create sample time-series DataFrame."""
        dates = pd.date_range(start="2025-01-01", periods=100, freq="D")
        return pd.DataFrame(
            {
                "timestamp": dates,
                "price": np.random.randn(100) * 100 + 1000,
                "target": np.random.randn(100) * 0.01,
            }
        )

    def test_split_count(self, sample_df):
        """Test that correct number of splits are generated."""
        cv = WalkForwardCV(n_splits=5, train_ratio=0.6)
        splits = list(cv.split(sample_df))
        assert len(splits) == 5

    def test_no_data_leakage(self, sample_df):
        """Test that train indices are always before test indices."""
        cv = WalkForwardCV(n_splits=4, train_ratio=0.5)

        for train_idx, test_idx in cv.split(sample_df):
            assert (
                train_idx.max() < test_idx.min()
            ), "Data leakage: train data overlaps with test data"

    def test_expanding_window(self, sample_df):
        """Test that expanding window grows training set."""
        cv = WalkForwardCV(n_splits=3, train_ratio=0.5, expanding=True)
        splits = list(cv.split(sample_df))

        train_sizes = [len(train) for train, _ in splits]
        # Each fold should have more training data (expanding window)
        for i in range(1, len(train_sizes)):
            assert (
                train_sizes[i] >= train_sizes[i - 1]
            ), "Expanding window should not shrink"

    def test_gap_prevents_lookahead(self, sample_df):
        """Test that gap parameter creates separation."""
        gap = 5
        cv = WalkForwardCV(n_splits=3, train_ratio=0.5, gap=gap)

        for train_idx, test_idx in cv.split(sample_df):
            # Gap should exist between train and test
            assert (
                test_idx.min() - train_idx.max() >= gap
            ), f"Gap should be at least {gap}"

    def test_invalid_params(self):
        """Test that invalid parameters raise errors."""
        with pytest.raises(ValueError):
            WalkForwardCV(n_splits=1)  # Must have at least 2 splits

        with pytest.raises(ValueError):
            WalkForwardCV(train_ratio=0.05)  # Too low

        with pytest.raises(ValueError):
            WalkForwardCV(gap=-1)  # Negative gap


class TestWalkForwardResult:
    """Tests for WalkForwardResult dataclass."""

    def test_empty_result(self):
        """Test empty result defaults."""
        result = WalkForwardResult()
        assert result.mean_sharpe == 0.0
        assert result.std_sharpe == 0.0

    def test_metrics_calculation(self):
        """Test mean and std calculations."""
        result = WalkForwardResult(
            fold_metrics=[
                {"sharpe_ratio": 1.0, "total_return": 0.10},
                {"sharpe_ratio": 1.5, "total_return": 0.15},
                {"sharpe_ratio": 2.0, "total_return": 0.20},
            ]
        )

        assert result.mean_sharpe == pytest.approx(1.5)
        assert result.mean_return == pytest.approx(0.15)
        assert result.std_sharpe > 0

    def test_to_dict(self):
        """Test dictionary conversion."""
        result = WalkForwardResult(
            fold_metrics=[
                {"sharpe_ratio": 1.0, "total_return": 0.10},
            ]
        )

        d = result.to_dict()
        assert "n_folds" in d
        assert "mean_sharpe" in d
        assert d["n_folds"] == 1


class TestOutOfSampleValidator:
    """Tests for Out-of-Sample (Holdout) Validator."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame."""
        dates = pd.date_range(start="2025-01-01", periods=100, freq="D")
        return pd.DataFrame(
            {
                "timestamp": dates,
                "price": range(100),
                "target": range(100),
            }
        )

    def test_default_holdout_ratio(self, sample_df):
        """Test default 20% holdout."""
        validator = OutOfSampleValidator()
        train, val, holdout = validator.split(sample_df)

        # Holdout should be ~20% of total
        assert len(holdout) == 20  # 20% of 100
        assert len(train) + len(val) + len(holdout) == 100

    def test_temporal_ordering(self, sample_df):
        """Test that splits maintain temporal order."""
        validator = OutOfSampleValidator()
        train, val, holdout = validator.split(sample_df)

        # Holdout should have the latest timestamps
        assert train["timestamp"].max() < val["timestamp"].min()
        assert val["timestamp"].max() < holdout["timestamp"].min()

    def test_custom_ratios(self, sample_df):
        """Test custom holdout and val ratios."""
        validator = OutOfSampleValidator(holdout_ratio=0.30, val_ratio=0.20)
        train, val, holdout = validator.split(sample_df)

        assert len(holdout) == 30  # 30% of 100
        # Dev set = 70, val = 20% of 70 = 14
        assert len(val) == 14

    def test_split_info(self):
        """Test get_split_info method."""
        validator = OutOfSampleValidator(holdout_ratio=0.20, val_ratio=0.25)
        info = validator.get_split_info(n_samples=100)

        assert info["holdout"] == 20
        assert info["total"] == 100
        assert info["train"] + info["val"] + info["holdout"] == 100


class TestValidateNoDataLeakage:
    """Tests for data leakage validation."""

    def test_valid_split(self):
        """Test valid split passes."""
        train = np.array([0, 1, 2, 3, 4])
        test = np.array([5, 6, 7, 8, 9])

        assert validate_no_data_leakage(train, test) is True

    def test_overlapping_split(self):
        """Test overlapping split raises error."""
        train = np.array([0, 1, 2, 3, 5])  # Contains 5
        test = np.array([4, 5, 6, 7])  # Also contains 5

        with pytest.raises(ValueError, match="Data leakage"):
            validate_no_data_leakage(train, test)

    def test_empty_indices(self):
        """Test empty indices raise error."""
        with pytest.raises(ValueError, match="Empty"):
            validate_no_data_leakage(np.array([]), np.array([1, 2]))
