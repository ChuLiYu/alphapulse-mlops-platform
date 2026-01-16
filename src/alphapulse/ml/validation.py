"""
Validation utilities for anti-overfitting in ML models.

Implements Walk-Forward CV and Out-of-Sample Holdout validation
strategies for time-series financial data.

Critical: All splits respect temporal ordering to prevent lookahead bias.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Generator, List, Optional, Tuple, Dict, Any

import numpy as np
import pandas as pd


@dataclass
class WalkForwardResult:
    """Results from Walk-Forward cross-validation."""

    fold_metrics: List[Dict[str, float]] = field(default_factory=list)

    @property
    def mean_sharpe(self) -> float:
        """Mean Sharpe Ratio across all folds."""
        if not self.fold_metrics:
            return 0.0
        return np.mean([m.get("sharpe_ratio", 0) for m in self.fold_metrics])

    @property
    def std_sharpe(self) -> float:
        """Standard deviation of Sharpe Ratio across folds."""
        if len(self.fold_metrics) < 2:
            return 0.0
        return np.std([m.get("sharpe_ratio", 0) for m in self.fold_metrics])

    @property
    def mean_return(self) -> float:
        """Mean total return across all folds."""
        if not self.fold_metrics:
            return 0.0
        return np.mean([m.get("total_return", 0) for m in self.fold_metrics])

    @property
    def std_return(self) -> float:
        """Standard deviation of total return across folds."""
        if len(self.fold_metrics) < 2:
            return 0.0
        return np.std([m.get("total_return", 0) for m in self.fold_metrics])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "n_folds": len(self.fold_metrics),
            "mean_sharpe": self.mean_sharpe,
            "std_sharpe": self.std_sharpe,
            "mean_return": self.mean_return,
            "std_return": self.std_return,
            "fold_metrics": self.fold_metrics,
        }


class WalkForwardCV:
    """
    Walk-Forward Cross-Validation for time-series data.

    Unlike standard k-fold, walk-forward ensures:
    1. Training data always comes BEFORE test data (no lookahead)
    2. Each fold uses expanding or rolling window training
    3. Optional gap between train and test to simulate real-world delay

    Example with 100 samples, n_splits=3, train_ratio=0.6:
        Fold 1: train=[0:60],  test=[60:73]
        Fold 2: train=[0:73],  test=[73:86]  (expanding)
        Fold 3: train=[0:86],  test=[86:100]
    """

    def __init__(
        self,
        n_splits: int = 5,
        train_ratio: float = 0.6,
        gap: int = 0,
        expanding: bool = True,
    ):
        """
        Initialize Walk-Forward CV.

        Args:
            n_splits: Number of train/test splits
            train_ratio: Initial training data ratio (0.0-1.0)
            gap: Number of samples to skip between train and test (prevents lookahead)
            expanding: If True, training window expands; if False, uses rolling window
        """
        if n_splits < 2:
            raise ValueError("n_splits must be at least 2")
        if not 0.1 <= train_ratio <= 0.9:
            raise ValueError("train_ratio must be between 0.1 and 0.9")
        if gap < 0:
            raise ValueError("gap must be non-negative")

        self.n_splits = n_splits
        self.train_ratio = train_ratio
        self.gap = gap
        self.expanding = expanding

    def split(
        self, X: pd.DataFrame
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Generate train/test indices for walk-forward validation.

        Args:
            X: DataFrame to split (must be sorted by time)

        Yields:
            Tuple of (train_indices, test_indices) arrays
        """
        n_samples = len(X)

        # Calculate initial train size
        initial_train_size = int(n_samples * self.train_ratio)

        # Remaining samples for test folds
        remaining = n_samples - initial_train_size
        test_size = remaining // self.n_splits

        if test_size < 1:
            raise ValueError(
                f"Not enough samples for {self.n_splits} splits. "
                f"n_samples={n_samples}, train_ratio={self.train_ratio}"
            )

        indices = np.arange(n_samples)

        for fold in range(self.n_splits):
            # Test window start/end
            test_start = initial_train_size + (fold * test_size)
            test_end = test_start + test_size if fold < self.n_splits - 1 else n_samples

            # Training window
            if self.expanding:
                # Expanding window: train from 0 to test_start - gap
                train_end = max(0, test_start - self.gap)
                train_start = 0
            else:
                # Rolling window: fixed window size before test
                window_size = initial_train_size
                train_end = max(0, test_start - self.gap)
                train_start = max(0, train_end - window_size)

            train_indices = indices[train_start:train_end]
            test_indices = indices[test_start:test_end]

            if len(train_indices) > 0 and len(test_indices) > 0:
                yield train_indices, test_indices

    def get_n_splits(self) -> int:
        """Return the number of splits."""
        return self.n_splits


class OutOfSampleValidator:
    """
    Out-of-Sample (Holdout) Validator.

    Ensures a strict temporal split where the final portion of data
    is NEVER seen during training or validation - only for final evaluation.

    Default: 80% development (train+val), 20% holdout test
    """

    def __init__(
        self, holdout_ratio: float = 0.20, val_ratio: float = 0.25  # Of development set
    ):
        """
        Initialize Out-of-Sample Validator.

        Args:
            holdout_ratio: Proportion of data to hold out (default 20%)
            val_ratio: Proportion of development set for validation
        """
        if not 0.1 <= holdout_ratio <= 0.5:
            raise ValueError("holdout_ratio must be between 0.1 and 0.5")
        if not 0.1 <= val_ratio <= 0.5:
            raise ValueError("val_ratio must be between 0.1 and 0.5")

        self.holdout_ratio = holdout_ratio
        self.val_ratio = val_ratio

    def split(
        self, df: pd.DataFrame, timestamp_col: str = "timestamp"
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train, validation, and holdout sets.

        Args:
            df: DataFrame to split
            timestamp_col: Column to sort by (ensures temporal order)

        Returns:
            Tuple of (train_df, val_df, holdout_df)
        """
        # Ensure temporal ordering
        if timestamp_col in df.columns:
            df = df.sort_values(timestamp_col).reset_index(drop=True)

        n = len(df)
        holdout_size = int(n * self.holdout_ratio)
        dev_size = n - holdout_size
        val_size = int(dev_size * self.val_ratio)
        train_size = dev_size - val_size

        train_df = df.iloc[:train_size].copy()
        val_df = df.iloc[train_size:dev_size].copy()
        holdout_df = df.iloc[dev_size:].copy()

        return train_df, val_df, holdout_df

    def get_split_info(self, n_samples: int) -> Dict[str, int]:
        """Get split sizes for given sample count."""
        holdout_size = int(n_samples * self.holdout_ratio)
        dev_size = n_samples - holdout_size
        val_size = int(dev_size * self.val_ratio)
        train_size = dev_size - val_size

        return {
            "train": train_size,
            "val": val_size,
            "holdout": holdout_size,
            "total": n_samples,
        }


def validate_no_data_leakage(
    train_indices: np.ndarray, test_indices: np.ndarray
) -> bool:
    """
    Verify that train indices are strictly before test indices.

    Args:
        train_indices: Array of training indices
        test_indices: Array of test indices

    Returns:
        True if no data leakage, raises ValueError otherwise
    """
    if len(train_indices) == 0 or len(test_indices) == 0:
        raise ValueError("Empty train or test indices")

    max_train = train_indices.max()
    min_test = test_indices.min()

    if max_train >= min_test:
        raise ValueError(
            f"Data leakage detected! max(train)={max_train} >= min(test)={min_test}"
        )

    return True
