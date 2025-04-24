"""
Quick training with best known configuration.

Uses the previous best model config to quickly retrain on latest data.
Compares new model with existing best and keeps the better one.
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

from alphapulse.ml.backtest import BacktestConfig, Backtester


# Default best config (fallback if no config file exists)
DEFAULT_CONFIG = {
    "model_name": "xgboost_conservative",
    "threshold": 0.005,
    "params": {
        "n_estimators": 50,
        "max_depth": 2,
        "learning_rate": 0.03
    }
}


def load_best_config(config_path: str) -> dict:
    """Load best model config or use default."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG


def train_best(
    data_dir: str = "/home/src/src/data/processed",
    output_dir: str = "/home/src/src/models/saved"
):
    """
    Quick training with best configuration.
    
    1. Load best config
    2. Train model with those params
    3. Evaluate with backtest
    4. Compare with existing best
    5. Keep better model
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load config
    config_file = output_path / "best_model_config.json"
    config = load_best_config(str(config_file))
    
    print("=" * 60)
    print("QUICK TRAINING")
    print("=" * 60)
    print(f"Using config: {config.get('model_name', 'unknown')}")
    print(f"Threshold: {config.get('threshold', 0.003)}")
    print(f"Params: {config.get('params', {})}")
    print("=" * 60)
    
    # Load data
    print("\nLoading data...")
    train = pd.read_parquet(f"{data_dir}/train.parquet")
    val = pd.read_parquet(f"{data_dir}/val.parquet")
    test = pd.read_parquet(f"{data_dir}/test.parquet")
    print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
    
    # Prepare features
    drop_cols = ['timestamp', 'symbol', 'source', 'target', 'created_at', 'updated_at']
    X_train = train.drop(columns=drop_cols, errors='ignore')
    y_train = train['target']
    X_val = val.drop(columns=drop_cols, errors='ignore')
    y_val = val['target']
    
    # Train model
    print("\nTraining model...")
    params = config.get('params', DEFAULT_CONFIG['params'])
    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    # Validation metrics
    val_preds = model.predict(X_val)
    val_mae = mean_absolute_error(y_val, val_preds)
    val_rmse = np.sqrt(mean_squared_error(y_val, val_preds))
    print(f"Validation MAE: {val_mae:.6f}")
    print(f"Validation RMSE: {val_rmse:.6f}")
    
    # Backtest
    print("\nRunning backtest...")
    backtest_config = BacktestConfig(
        initial_capital=Decimal("10000"),
        transaction_cost_pct=Decimal("0.001"),
        signal_threshold=config.get('threshold', 0.003)
    )
    backtester = Backtester(model, backtest_config)
    result = backtester.run(test)
    
    new_sharpe = float(result.sharpe_ratio)
    new_return = float(result.total_return)
    
    print(f"\nNew Model Results:")
    print(f"  Sharpe Ratio: {new_sharpe:.4f}")
    print(f"  Total Return: {new_return*100:.2f}%")
    print(f"  Win Rate: {float(result.win_rate)*100:.2f}%")
    print(f"  Total Trades: {result.total_trades}")
    
    # Compare with existing best
    existing_sharpe = config.get('metrics', {}).get('sharpe_ratio', -999)
    
    if new_sharpe >= existing_sharpe:
        print(f"\n✅ New model is better or equal! (Sharpe: {new_sharpe:.4f} >= {existing_sharpe:.4f})")
        
        # Save new model
        model_path = output_path / "best_model.pkl"
        joblib.dump(model, model_path)
        
        # Update config
        new_config = {
            "model_name": config.get('model_name', 'xgboost'),
            "threshold": config.get('threshold', 0.003),
            "params": params,
            "metrics": {
                "sharpe_ratio": new_sharpe,
                "total_return": new_return,
                "win_rate": float(result.win_rate),
                "total_trades": result.total_trades,
                "max_drawdown": float(result.max_drawdown),
                "val_mae": val_mae,
                "val_rmse": val_rmse
            },
            "trained_at": datetime.now().isoformat(),
            "data_size": {
                "train": len(train),
                "val": len(val),
                "test": len(test)
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(new_config, f, indent=2)
        
        print(f"Model saved to {model_path}")
        print(f"Config updated: {config_file}")
    else:
        print(f"\n⚠️ Existing model is better (Sharpe: {existing_sharpe:.4f} > {new_sharpe:.4f})")
        print("Keeping existing model.")
    
    print("\n" + "=" * 60)
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="/home/src/src/data/processed")
    parser.add_argument("--output_dir", default="/home/src/src/models/saved")
    
    args = parser.parse_args()
    train_best(data_dir=args.data_dir, output_dir=args.output_dir)
