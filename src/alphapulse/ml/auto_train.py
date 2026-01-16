"""
Automated Model Training Pipeline.

Runs multiple model types and threshold configurations,
automatically selects the best model based on Sharpe Ratio.
Designed to be triggered by Airflow data pipeline.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Optional

import joblib
import mlflow
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.metrics import mean_absolute_error, mean_squared_error

from alphapulse.ml.backtest import BacktestConfig, Backtester, BacktestResult
from alphapulse.ml.validation import (
    WalkForwardCV,
    WalkForwardResult,
    OutOfSampleValidator,
)


@dataclass
class ModelConfig:
    """Configuration for a model to train."""

    name: str
    model_class: type
    params: Dict[str, Any]


# Try importing LightGBM (optional dependency)
try:
    import lightgbm as lgb

    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    lgb = None


# Default model configurations to try
# All XGBoost models include L1 (reg_alpha) and L2 (reg_lambda) regularization
DEFAULT_MODELS = [
    # === XGBoost Variants ===
    ModelConfig(
        "xgboost_regularized",
        xgb.XGBRegressor,
        {
            "n_estimators": 100,
            "max_depth": 3,
            "learning_rate": 0.05,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,  # L1 + L2 regularization
        },
    ),
    ModelConfig(
        "xgboost_shallow",
        xgb.XGBRegressor,
        {
            "n_estimators": 100,
            "max_depth": 3,
            "learning_rate": 0.05,
            "reg_alpha": 0.05,
            "reg_lambda": 0.5,
        },
    ),
    ModelConfig(
        "xgboost_deep",
        xgb.XGBRegressor,
        {
            "n_estimators": 150,
            "max_depth": 5,
            "learning_rate": 0.1,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
        },
    ),
    ModelConfig(
        "xgboost_conservative",
        xgb.XGBRegressor,
        {
            "n_estimators": 50,
            "max_depth": 2,
            "learning_rate": 0.03,
            "reg_alpha": 0.2,
            "reg_lambda": 2.0,  # Stronger regularization
        },
    ),
    # NEW: Heavy regularization for overfitting prevention
    ModelConfig(
        "xgboost_heavy_reg",
        xgb.XGBRegressor,
        {
            "n_estimators": 80,
            "max_depth": 2,
            "learning_rate": 0.01,
            "reg_alpha": 0.5,
            "reg_lambda": 3.0,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        },
    ),
    # NEW: Moderate depth with dropout-like behavior
    ModelConfig(
        "xgboost_subsample",
        xgb.XGBRegressor,
        {
            "n_estimators": 120,
            "max_depth": 4,
            "learning_rate": 0.05,
            "reg_alpha": 0.15,
            "reg_lambda": 1.5,
            "subsample": 0.7,
            "colsample_bytree": 0.7,
        },
    ),
    # === Traditional ML ===
    ModelConfig(
        "random_forest",
        RandomForestRegressor,
        {"n_estimators": 100, "max_depth": 5, "n_jobs": -1, "min_samples_leaf": 5},
    ),
    ModelConfig(
        "random_forest_deep",
        RandomForestRegressor,
        {"n_estimators": 150, "max_depth": 8, "n_jobs": -1, "min_samples_leaf": 3},
    ),
    ModelConfig(
        "gradient_boosting",
        GradientBoostingRegressor,
        {"n_estimators": 100, "max_depth": 3, "learning_rate": 0.1},
    ),
    ModelConfig(
        "gradient_boosting_conservative",
        GradientBoostingRegressor,
        {"n_estimators": 80, "max_depth": 2, "learning_rate": 0.05, "subsample": 0.8},
    ),
    # === Linear Models (baseline) ===
    ModelConfig("ridge", Ridge, {"alpha": 1.0}),  # L2 regularization
    ModelConfig("ridge_strong", Ridge, {"alpha": 10.0}),  # Stronger L2
    ModelConfig("lasso", Lasso, {"alpha": 0.1}),  # L1 regularization
    ModelConfig("lasso_strong", Lasso, {"alpha": 1.0}),  # Stronger L1
]

# Add LightGBM models if available
if LIGHTGBM_AVAILABLE:
    DEFAULT_MODELS.extend(
        [
            ModelConfig(
                "lightgbm_default",
                lgb.LGBMRegressor,
                {
                    "n_estimators": 100,
                    "max_depth": 4,
                    "learning_rate": 0.05,
                    "reg_alpha": 0.1,
                    "reg_lambda": 0.1,
                    "verbose": -1,
                },
            ),
            ModelConfig(
                "lightgbm_conservative",
                lgb.LGBMRegressor,
                {
                    "n_estimators": 80,
                    "max_depth": 3,
                    "learning_rate": 0.03,
                    "reg_alpha": 0.2,
                    "reg_lambda": 0.5,
                    "verbose": -1,
                },
            ),
        ]
    )


# Expanded thresholds to test (finer-grained search)
DEFAULT_THRESHOLDS = [
    0.0005,
    0.001,
    0.0015,
    0.002,
    0.0025,
    0.003,
    0.004,
    0.005,
    0.007,
    0.01,
]


class AutoTrainer:
    """
    Automated model training and selection.

    Trains multiple models, tests different thresholds,
    and automatically selects the best configuration.
    """

    def __init__(
        self,
        data_dir: str = "/app/src/data/processed",
        output_dir: str = "/app/src/models/saved",
        mlflow_tracking_uri: Optional[str] = None,
    ):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # MLflow setup
        if mlflow_tracking_uri:
            mlflow.set_tracking_uri(mlflow_tracking_uri)

        self.results: List[Dict] = []
        self.best_result: Optional[Dict] = None

    def load_data(self):
        """Load train/val/test data."""
        self.train = pd.read_parquet(self.data_dir / "train.parquet")
        self.val = pd.read_parquet(self.data_dir / "val.parquet")
        self.test = pd.read_parquet(self.data_dir / "test.parquet")

        drop_cols = [
            "timestamp",
            "symbol",
            "source",
            "target",
            "created_at",
            "updated_at",
        ]
        self.X_train = self.train.drop(columns=drop_cols, errors="ignore")
        self.y_train = self.train["target"]
        self.X_val = self.val.drop(columns=drop_cols, errors="ignore")
        self.y_val = self.val["target"]

        print(
            f"Data loaded: Train={len(self.train)}, Val={len(self.val)}, Test={len(self.test)}"
        )

    def train_and_evaluate(self, model_config: ModelConfig, threshold: float) -> Dict:
        """Train a model and evaluate with backtest."""
        # Train
        model = model_config.model_class(**model_config.params)
        model.fit(self.X_train, self.y_train)

        # Validation metrics
        val_preds = model.predict(self.X_val)
        val_mae = mean_absolute_error(self.y_val, val_preds)
        val_rmse = np.sqrt(mean_squared_error(self.y_val, val_preds))

        # Backtest
        config = BacktestConfig(
            initial_capital=Decimal("10000"),
            transaction_cost_pct=Decimal("0.001"),
            signal_threshold=threshold,
        )
        backtester = Backtester(model, config)
        result = backtester.run(self.test)

        return {
            "model_name": model_config.name,
            "threshold": threshold,
            "params": model_config.params,
            "val_mae": val_mae,
            "val_rmse": val_rmse,
            "sharpe_ratio": float(result.sharpe_ratio),
            "total_return": float(result.total_return),
            "win_rate": float(result.win_rate),
            "total_trades": result.total_trades,
            "max_drawdown": float(result.max_drawdown),
            "model": model,
        }

    def walk_forward_evaluate(
        self, model_config: ModelConfig, threshold: float, n_splits: int = 3
    ) -> Dict:
        """
        Evaluate model using Walk-Forward Cross-Validation.

        Trains on expanding window, backtests on each fold's test period.
        Returns average metrics across all folds.
        """
        # Combine train + val for walk-forward
        full_data = pd.concat([self.train, self.val, self.test], ignore_index=True)

        drop_cols = [
            "timestamp",
            "symbol",
            "source",
            "target",
            "created_at",
            "updated_at",
        ]

        wf_cv = WalkForwardCV(n_splits=n_splits, train_ratio=0.6, gap=1)
        wf_result = WalkForwardResult()

        for fold_idx, (train_idx, test_idx) in enumerate(wf_cv.split(full_data)):
            train_fold = full_data.iloc[train_idx]
            test_fold = full_data.iloc[test_idx]

            X_train_fold = train_fold.drop(columns=drop_cols, errors="ignore")
            y_train_fold = train_fold["target"]

            # Train model on this fold
            model = model_config.model_class(**model_config.params)
            model.fit(X_train_fold, y_train_fold)

            # Backtest on test fold
            config = BacktestConfig(
                initial_capital=Decimal("10000"),
                transaction_cost_pct=Decimal("0.001"),
                signal_threshold=threshold,
            )
            backtester = Backtester(model, config)
            result = backtester.run(test_fold)

            wf_result.fold_metrics.append(
                {
                    "fold": fold_idx,
                    "sharpe_ratio": float(result.sharpe_ratio),
                    "total_return": float(result.total_return),
                    "win_rate": float(result.win_rate),
                    "total_trades": result.total_trades,
                }
            )

        # Train final model on all data except holdout
        train_val = pd.concat([self.train, self.val], ignore_index=True)
        X_train_full = train_val.drop(columns=drop_cols, errors="ignore")
        y_train_full = train_val["target"]

        final_model = model_config.model_class(**model_config.params)
        final_model.fit(X_train_full, y_train_full)

        # Final evaluation on holdout test set
        config = BacktestConfig(
            initial_capital=Decimal("10000"),
            transaction_cost_pct=Decimal("0.001"),
            signal_threshold=threshold,
        )
        backtester = Backtester(final_model, config)
        final_result = backtester.run(self.test)

        return {
            "model_name": model_config.name,
            "threshold": threshold,
            "params": model_config.params,
            "cv_mean_sharpe": wf_result.mean_sharpe,
            "cv_std_sharpe": wf_result.std_sharpe,
            "cv_mean_return": wf_result.mean_return,
            "cv_std_return": wf_result.std_return,
            "holdout_sharpe": float(final_result.sharpe_ratio),
            "holdout_return": float(final_result.total_return),
            "holdout_win_rate": float(final_result.win_rate),
            "holdout_trades": final_result.total_trades,
            "max_drawdown": float(final_result.max_drawdown),
            "model": final_model,
            "cv_details": wf_result.to_dict(),
        }

    def run(
        self,
        models: Optional[List[ModelConfig]] = None,
        thresholds: Optional[List[float]] = None,
        min_trades: int = 3,
        log_to_mlflow: bool = True,
        use_walk_forward: bool = False,
        wf_splits: int = 3,
    ) -> Dict:
        """
        Run automated training pipeline.

        Args:
            models: List of model configs to try
            thresholds: List of signal thresholds to try
            min_trades: Minimum trades required to consider a config
            log_to_mlflow: Whether to log to MLflow
            use_walk_forward: If True, use Walk-Forward CV for more robust evaluation
            wf_splits: Number of splits for Walk-Forward CV (only if use_walk_forward=True)

        Returns:
            Best model configuration and results
        """
        models = models or DEFAULT_MODELS
        thresholds = thresholds or DEFAULT_THRESHOLDS

        print(f"\n{'='*60}")
        print(f"AUTOMATED TRAINING PIPELINE")
        print(f"{'='*60}")
        print(f"Models to try: {len(models)}")
        print(f"Thresholds: {thresholds}")
        print(f"Total combinations: {len(models) * len(thresholds)}")
        print(
            f"Evaluation mode: {'Walk-Forward CV' if use_walk_forward else 'Single Backtest'}"
        )
        print(f"{'='*60}\n")

        self.load_data()
        self.results = []

        # Try all combinations
        for model_config in models:
            for threshold in thresholds:
                try:
                    if use_walk_forward:
                        result = self.walk_forward_evaluate(
                            model_config, threshold, n_splits=wf_splits
                        )
                        # Use CV mean Sharpe as the main metric
                        result["sharpe_ratio"] = result["cv_mean_sharpe"]
                        result["total_return"] = result["holdout_return"]
                        result["win_rate"] = result["holdout_win_rate"]
                        result["total_trades"] = result["holdout_trades"]
                        # Validation metrics (use holdout)
                        result["val_mae"] = 0.0  # Not computed in WF mode
                        result["val_rmse"] = 0.0
                    else:
                        result = self.train_and_evaluate(model_config, threshold)

                    self.results.append(result)

                    # Log each run to MLflow for comparison
                    if log_to_mlflow:
                        self._log_single_run(result, use_walk_forward)

                    # Print progress
                    sharpe = result["sharpe_ratio"]
                    ret = result["total_return"] * 100
                    trades = result["total_trades"]
                    if use_walk_forward:
                        std_sharpe = result.get("cv_std_sharpe", 0)
                        print(
                            f"{model_config.name:20} | thr={threshold:.4f} | Sharpe={sharpe:6.3f}±{std_sharpe:.3f} | Ret={ret:6.2f}% | Trades={trades}"
                        )
                    else:
                        print(
                            f"{model_config.name:20} | thr={threshold:.4f} | Sharpe={sharpe:6.3f} | Ret={ret:6.2f}% | Trades={trades}"
                        )

                except Exception as e:
                    print(f"ERROR: {model_config.name} @ {threshold}: {e}")

        # Filter by minimum trades and select best
        valid_results = [r for r in self.results if r["total_trades"] >= min_trades]

        if not valid_results:
            print("\n⚠️ No valid results with minimum trades requirement")
            valid_results = self.results

        # Select best by Sharpe Ratio
        self.best_result = max(valid_results, key=lambda x: x["sharpe_ratio"])

        print(f"\n{'='*60}")
        print("BEST MODEL SELECTED")
        print(f"{'='*60}")
        print(f"Model: {self.best_result['model_name']}")
        print(f"Threshold: {self.best_result['threshold']}")
        print(f"Sharpe Ratio: {self.best_result['sharpe_ratio']:.4f}")
        print(f"Total Return: {self.best_result['total_return']*100:.2f}%")
        print(f"Win Rate: {self.best_result['win_rate']*100:.2f}%")
        print(f"Total Trades: {self.best_result['total_trades']}")
        print(f"{'='*60}\n")

        # Save best model
        best_model = self.best_result["model"]
        model_path = self.output_dir / "best_model.pkl"
        joblib.dump(best_model, model_path)
        print(f"Best model saved to {model_path}")

        # Save config
        config = {
            "model_name": self.best_result["model_name"],
            "threshold": self.best_result["threshold"],
            "params": self.best_result["params"],
            "metrics": {
                "sharpe_ratio": self.best_result["sharpe_ratio"],
                "total_return": self.best_result["total_return"],
                "win_rate": self.best_result["win_rate"],
                "total_trades": self.best_result["total_trades"],
                "max_drawdown": self.best_result["max_drawdown"],
                "val_mae": self.best_result["val_mae"],
                "val_rmse": self.best_result["val_rmse"],
            },
            "trained_at": datetime.now().isoformat(),
            "data_size": {
                "train": len(self.train),
                "val": len(self.val),
                "test": len(self.test),
            },
        }

        config_path = self.output_dir / "best_model_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Config saved to {config_path}")

        # Log to MLflow
        if log_to_mlflow:
            self._log_to_mlflow(config, use_walk_forward)

        return config

    def _log_single_run(self, result: Dict, use_walk_forward: bool = False):
        """Log a single training run to MLflow for comparison."""
        try:
            mlflow.set_experiment("auto_training_runs")

            run_name = f"{result['model_name']}_thr{result['threshold']:.4f}"
            with mlflow.start_run(run_name=run_name):
                # Log parameters
                mlflow.log_params(
                    {
                        "model_name": result["model_name"],
                        "threshold": result["threshold"],
                        "evaluation_mode": (
                            "walk_forward" if use_walk_forward else "single_backtest"
                        ),
                        **{f"param_{k}": str(v) for k, v in result["params"].items()},
                    }
                )

                # Log metrics
                metrics = {
                    "sharpe_ratio": result["sharpe_ratio"],
                    "total_return": result["total_return"],
                    "win_rate": result["win_rate"],
                    "total_trades": result["total_trades"],
                    "max_drawdown": result["max_drawdown"],
                }

                # Add CV-specific metrics if using Walk-Forward
                if use_walk_forward:
                    metrics["cv_mean_sharpe"] = result.get("cv_mean_sharpe", 0)
                    metrics["cv_std_sharpe"] = result.get("cv_std_sharpe", 0)
                    metrics["cv_mean_return"] = result.get("cv_mean_return", 0)
                    metrics["holdout_sharpe"] = result.get("holdout_sharpe", 0)
                    # Stability score: high Sharpe with low variance is better
                    cv_std = result.get("cv_std_sharpe", 0)
                    if cv_std > 0:
                        metrics["stability_score"] = result["sharpe_ratio"] / cv_std
                    else:
                        metrics["stability_score"] = result["sharpe_ratio"]

                mlflow.log_metrics(metrics)

        except Exception as e:
            # Don't fail the training if MLflow logging fails
            pass

    def _log_to_mlflow(self, config: Dict, use_walk_forward: bool = False):
        """Log best model to MLflow."""
        try:
            mlflow.set_experiment("auto_training")

            with mlflow.start_run(run_name=f"best_{config['model_name']}"):
                mlflow.log_params(
                    {
                        "model_name": config["model_name"],
                        "threshold": config["threshold"],
                        "evaluation_mode": (
                            "walk_forward" if use_walk_forward else "single_backtest"
                        ),
                        **{f"param_{k}": str(v) for k, v in config["params"].items()},
                    }
                )
                mlflow.log_metrics(config["metrics"])
                mlflow.log_artifact(str(self.output_dir / "best_model.pkl"))
                mlflow.log_artifact(str(self.output_dir / "best_model_config.json"))

                # Tag as best model
                mlflow.set_tag("is_best", "true")
                mlflow.set_tag("trained_at", config.get("trained_at", ""))

            print("✅ Best model logged to MLflow")
        except Exception as e:
            print(f"⚠️ MLflow logging failed: {e}")


def run_auto_training(
    data_dir: str = "/app/data/processed",
    output_dir: str = "/app/models/saved",
    mlflow_uri: str = "http://mlflow:5000",
    use_walk_forward: bool = False,
    wf_splits: int = 3,
) -> Dict:
    """
    Entry point for Airflow pipeline integration.

    Can be called from an Airflow PythonOperator or specialized task.

    Args:
        data_dir: Directory with train/val/test parquet files
        output_dir: Directory to save best model
        mlflow_uri: MLflow tracking URI
        use_walk_forward: If True, use Walk-Forward CV for robust evaluation
        wf_splits: Number of CV splits (default 3)
    """
    trainer = AutoTrainer(
        data_dir=data_dir, output_dir=output_dir, mlflow_tracking_uri=mlflow_uri
    )
    return trainer.run(use_walk_forward=use_walk_forward, wf_splits=wf_splits)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Automated Model Training Pipeline")
    parser.add_argument(
        "--data_dir",
        default="/app/data/processed",
        help="Directory with train/val/test parquet files",
    )
    parser.add_argument(
        "--output_dir", default="/app/models/saved", help="Directory to save best model"
    )
    parser.add_argument(
        "--mlflow_uri", default="http://mlflow:5000", help="MLflow tracking URI"
    )
    parser.add_argument(
        "--walk-forward",
        action="store_true",
        help="Use Walk-Forward CV for more robust evaluation",
    )
    parser.add_argument(
        "--wf-splits",
        type=int,
        default=3,
        help="Number of Walk-Forward CV splits (default: 3)",
    )

    args = parser.parse_args()

    result = run_auto_training(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        mlflow_uri=args.mlflow_uri,
        use_walk_forward=args.walk_forward,
        wf_splits=args.wf_splits,
    )

    print("\nFinal Result:")
    print(json.dumps(result, indent=2))
