"""
Hyperparameter optimization for XGBoost using Optuna.

Optimizes model parameters to maximize Sharpe Ratio from backtesting.
Uses MLflow for experiment tracking.
"""

import argparse
import os
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any

import joblib
import mlflow
import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Import backtest components
from alphapulse.ml.backtest import BacktestConfig, Backtester
from alphapulse.ml.validation import WalkForwardCV, WalkForwardResult


def load_data(data_dir: str = "/app/src/data/processed"):
    """Load train/val/test data."""
    train = pd.read_parquet(f"{data_dir}/train.parquet")
    val = pd.read_parquet(f"{data_dir}/val.parquet")
    test = pd.read_parquet(f"{data_dir}/test.parquet")
    return train, val, test


def prepare_features(df: pd.DataFrame, target_col: str = "target"):
    """Prepare features for training."""
    drop_cols = [
        "timestamp",
        "symbol",
        "source",
        target_col,
        "created_at",
        "updated_at",
    ]
    X = df.drop(columns=drop_cols, errors="ignore")
    y = df[target_col]
    return X, y


def objective(
    trial: optuna.Trial,
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    config: BacktestConfig,
    optimize_threshold: bool = True,
    use_walk_forward: bool = False,
    stability_weight: float = 0.1,
) -> float:
    """
    Optuna objective function.

    Optimizes for Sharpe Ratio from backtesting, optionally with stability penalty.

    Args:
        trial: Optuna trial object
        train: Training data
        val: Validation data
        test: Test data
        config: Backtest configuration (threshold may be overridden)
        optimize_threshold: If True, include signal_threshold in search space
        use_walk_forward: If True, use Walk-Forward CV for more robust evaluation
        stability_weight: Weight for stability penalty (penalize high variance)
    """
    # Define hyperparameter search space
    params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "n_estimators": trial.suggest_int("n_estimators", 50, 300),
        "max_depth": trial.suggest_int("max_depth", 2, 8),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "gamma": trial.suggest_float("gamma", 0, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
    }

    # Optionally optimize signal threshold
    if optimize_threshold:
        threshold = trial.suggest_float("signal_threshold", 0.0005, 0.01, log=True)
    else:
        threshold = config.signal_threshold

    # Create backtest config with potentially new threshold
    bt_config = BacktestConfig(
        initial_capital=config.initial_capital,
        transaction_cost_pct=config.transaction_cost_pct,
        signal_threshold=threshold,
    )

    if use_walk_forward:
        # Walk-Forward CV for robust evaluation
        full_data = pd.concat([train, val, test], ignore_index=True)

        wf_cv = WalkForwardCV(n_splits=3, train_ratio=0.6, gap=1)
        sharpe_scores = []

        for fold_idx, (train_idx, test_idx) in enumerate(wf_cv.split(full_data)):
            train_fold = full_data.iloc[train_idx]
            test_fold = full_data.iloc[test_idx]

            X_train_fold, y_train_fold = prepare_features(train_fold)

            # Train model on this fold
            model = xgb.XGBRegressor(**params)
            model.fit(X_train_fold, y_train_fold, verbose=False)

            # Backtest on test fold
            backtester = Backtester(model, bt_config)
            result = backtester.run(test_fold)
            sharpe_scores.append(float(result.sharpe_ratio))

        # Calculate mean and std of Sharpe
        mean_sharpe = np.mean(sharpe_scores)
        std_sharpe = np.std(sharpe_scores)

        # Apply stability penalty: penalize high variance
        # Final score = mean_sharpe - stability_weight * std_sharpe
        final_score = mean_sharpe - stability_weight * std_sharpe

        trial.set_user_attr("cv_mean_sharpe", mean_sharpe)
        trial.set_user_attr("cv_std_sharpe", std_sharpe)

        return final_score

    else:
        # Single backtest (original behavior)
        X_train, y_train = prepare_features(train)
        X_val, y_val = prepare_features(val)

        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

        # Evaluate with backtest
        backtester = Backtester(model, bt_config)
        result = backtester.run(test)

        sharpe = float(result.sharpe_ratio)

        # Log intermediate values
        trial.set_user_attr("total_return", float(result.total_return))
        trial.set_user_attr("max_drawdown", float(result.max_drawdown))
        trial.set_user_attr("win_rate", float(result.win_rate))
        trial.set_user_attr("total_trades", result.total_trades)

        return sharpe


def optimize(
    data_dir: str = "/app/src/data/processed",
    n_trials: int = 50,
    output_path: str = "/app/src/models/saved/btc_predictor_optimized.pkl",
    optimize_threshold: bool = True,
    use_walk_forward: bool = False,
    stability_weight: float = 0.1,
) -> Dict[str, Any]:
    """
    Run hyperparameter optimization.

    Args:
        data_dir: Directory with train/val/test parquet files
        n_trials: Number of Optuna trials
        output_path: Path to save optimized model
        optimize_threshold: If True, optimize signal_threshold jointly with model params
        use_walk_forward: If True, use Walk-Forward CV for robust evaluation
        stability_weight: Weight for stability penalty (penalize high variance)

    Returns:
        Dictionary with best parameters and metrics
    """
    print(f"Loading data from {data_dir}...")
    train, val, test = load_data(data_dir)
    print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

    # Backtest config
    config = BacktestConfig(
        initial_capital=Decimal("10000"), transaction_cost_pct=Decimal("0.001")
    )

    # Create Optuna study (maximize Sharpe)
    study = optuna.create_study(
        direction="maximize", study_name="xgboost_btc_optimization"
    )

    print(f"\nStarting optimization with {n_trials} trials...")
    print(f"Optimize threshold: {optimize_threshold}")
    print(f"Use Walk-Forward CV: {use_walk_forward}")
    if use_walk_forward:
        print(f"Stability weight: {stability_weight}")

    study.optimize(
        lambda trial: objective(
            trial,
            train,
            val,
            test,
            config,
            optimize_threshold=optimize_threshold,
            use_walk_forward=use_walk_forward,
            stability_weight=stability_weight,
        ),
        n_trials=n_trials,
        show_progress_bar=True,
    )

    # Best trial info
    best_trial = study.best_trial
    print("\n" + "=" * 50)
    print("OPTIMIZATION COMPLETE")
    print("=" * 50)
    print(f"Best Sharpe Ratio: {best_trial.value:.4f}")
    print(f"Best Parameters: {best_trial.params}")
    print(f"Total Return: {best_trial.user_attrs.get('total_return', 0)*100:.2f}%")
    print(f"Max Drawdown: {best_trial.user_attrs.get('max_drawdown', 0)*100:.2f}%")
    print(f"Win Rate: {best_trial.user_attrs.get('win_rate', 0)*100:.2f}%")

    # Re-train final model with best params
    print("\nRe-training model with best parameters...")
    best_params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        **best_trial.params,
    }

    X_train, y_train = prepare_features(train)
    X_val, y_val = prepare_features(val)

    final_model = xgb.XGBRegressor(**best_params)
    final_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    # Calculate validation metrics
    val_preds = final_model.predict(X_val)
    val_mae = mean_absolute_error(y_val, val_preds)
    val_rmse = np.sqrt(mean_squared_error(y_val, val_preds))

    print(f"Validation MAE: {val_mae:.6f}")
    print(f"Validation RMSE: {val_rmse:.6f}")

    # Save model
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(final_model, output_path)
    print(f"\nOptimized model saved to {output_path}")

    # Log to MLflow
    try:
        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        mlflow.set_tracking_uri(mlflow_uri)
        mlflow.set_experiment("btc_price_optimization")

        with mlflow.start_run(run_name="optuna_best"):
            mlflow.log_params(best_trial.params)
            mlflow.log_metric("sharpe_ratio", best_trial.value)
            mlflow.log_metric(
                "total_return", best_trial.user_attrs.get("total_return", 0)
            )
            mlflow.log_metric(
                "max_drawdown", best_trial.user_attrs.get("max_drawdown", 0)
            )
            mlflow.log_metric("win_rate", best_trial.user_attrs.get("win_rate", 0))
            mlflow.log_metric("val_mae", val_mae)
            mlflow.log_metric("val_rmse", val_rmse)
            mlflow.xgboost.log_model(final_model, "model")
        print("Logged to MLflow successfully.")
    except Exception as e:
        print(f"MLflow logging failed: {e}")

    return {
        "best_params": best_trial.params,
        "sharpe_ratio": best_trial.value,
        "total_return": best_trial.user_attrs.get("total_return", 0),
        "max_drawdown": best_trial.user_attrs.get("max_drawdown", 0),
        "win_rate": best_trial.user_attrs.get("win_rate", 0),
        "val_mae": val_mae,
        "val_rmse": val_rmse,
        "model_path": output_path,
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Hyperparameter optimization with Optuna"
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default="/app/src/data/processed",
        help="Directory containing train/val/test parquet files",
    )
    parser.add_argument(
        "--n_trials", type=int, default=50, help="Number of optimization trials"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="/app/src/models/saved/btc_predictor_optimized.pkl",
        help="Output path for optimized model",
    )
    parser.add_argument(
        "--no-threshold-search",
        action="store_true",
        help="Disable threshold optimization (use fixed default)",
    )
    parser.add_argument(
        "--walk-forward",
        action="store_true",
        help="Use Walk-Forward CV for more robust evaluation",
    )
    parser.add_argument(
        "--stability-weight",
        type=float,
        default=0.1,
        help="Weight for stability penalty (default: 0.1)",
    )

    args = parser.parse_args()

    # Set MLflow S3 endpoint
    if "MLFLOW_S3_ENDPOINT_URL" not in os.environ and "S3_ENDPOINT_URL" in os.environ:
        os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.environ["S3_ENDPOINT_URL"]

    optimize(
        data_dir=args.data_dir,
        n_trials=args.n_trials,
        output_path=args.output_path,
        optimize_threshold=not args.no_threshold_search,
        use_walk_forward=args.walk_forward,
        stability_weight=args.stability_weight,
    )


if __name__ == "__main__":
    main()
