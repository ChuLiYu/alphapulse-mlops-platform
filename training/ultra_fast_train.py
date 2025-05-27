#!/usr/bin/env python3
"""
Ultra Fast Model Training - Optimized Configurations Only

Focuses on the most effective models, skipping experimental configurations 
to quickly generate production-ready models.
"""

import json
import os
import sys
from datetime import datetime

# Add project path for training container
sys.path.insert(0, "/app/src")

import xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.ensemble import RandomForestRegressor

from alphapulse.ml.training.iterative_trainer import IterativeTrainer, TrainingConfig


def ultra_fast_training():
    """Ultra fast training with optimized configurations"""

    print("=" * 80)
    print("⚡ ULTRA FAST PRODUCTION MODEL TRAINING (CatBoost Enabled)")
    print("=" * 80)
    print(f"⏰ Start Time: {datetime.now().strftime('%H:%M:%S')}\n")

    # Highly optimized configuration
    output_dir = os.getenv("MODEL_OUTPUT_DIR", "/app/storage/models")
    
    config = TrainingConfig(
        data_source="model_features",
        target_column="target_return",
        min_samples_required=300,
        n_iterations=4,  # Extra iteration for CatBoost
        cv_splits=3,
        early_stopping_rounds=20,
        early_stopping_patience=1,
        max_train_val_gap=0.20,
        max_val_test_gap=0.15,
        min_val_r2=0.01,
        mlflow_uri=os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"),
        experiment_name="ultra_fast_production",
        output_dir=output_dir,
        save_all_iterations=False,
    )

    print(f"⚙️  Config: 4 Iterations | 3-Fold CV | Output: {output_dir}")
    print("Target: Rapidly generate high-quality production models\n")

    # Create trainer and override config for best models only
    trainer = IterativeTrainer(config)

    # Manually set best model configurations
    best_configs = [
        {
            "name": "catboost_production_v1",
            "class": CatBoostRegressor,
            "params": {
                "iterations": 400,
                "depth": 3,
                "learning_rate": 0.015,
                "l2_leaf_reg": 30.0,
                "bootstrap_type": "Bernoulli",
                "subsample": 0.5,
                "random_strength": 10.0,
                "max_bin": 32,
                "min_data_in_leaf": 50,
                "logging_level": "Silent",
                "random_state": 42,
                "thread_count": 2,
            },
        },
        {
            "name": "catboost_production_v2",
            "class": CatBoostRegressor,
            "params": {
                "iterations": 250,
                "depth": 2,
                "learning_rate": 0.03,
                "l2_leaf_reg": 15.0,
                "bootstrap_type": "MVS",
                "max_bin": 16,
                "min_data_in_leaf": 100,
                "logging_level": "Silent",
                "random_state": 42,
                "thread_count": 2,
            },
        },
        {
            "name": "xgboost_balanced",
            "class": xgb.XGBRegressor,
            "params": {
                "n_estimators": 100,
                "max_depth": 3,
                "learning_rate": 0.05,
                "reg_alpha": 0.1,
                "reg_lambda": 1.0,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": 42,
            },
        },
        {
            "name": "random_forest_balanced",
            "class": RandomForestRegressor,
            "params": {
                "n_estimators": 100,
                "max_depth": 5,
                "min_samples_leaf": 10,
                "max_features": "sqrt",
                "n_jobs": -1,
                "random_state": 42,
            },
        },
    ]

    # Override the configuration generation method
    trainer.generate_model_configs = lambda: best_configs

    print("🚀 Starting training...\n")

    try:
        summary = trainer.run_iterative_training()

        print("\n" + "=" * 80)
        print("✅ TRAINING COMPLETE!")
        print("=" * 80)

        if summary.get("best_model"):
            best = summary["best_model"]
            print(f"\n🏆 Best Model: {best['name']}")
            print(f"   Val MAE: {best['val_mae']:.6f}")
            print(f"   Test MAE: {best['test_mae']:.6f}")
            print(f"   Test R²: {best['test_r2']:.4f}")

        print(f"\n⏰ End Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"💾 Model Saved: {config.output_dir}/best_model.pkl")

        return summary

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    summary = ultra_fast_training()
    sys.exit(0 if summary else 1)

    # 覆寫生成模型配置的方法
    trainer.generate_model_configs = lambda: best_configs

    print("🚀 開始訓練...\n")

    try:
        summary = trainer.run_iterative_training()

        print("\n" + "=" * 80)
        print("✅ 完成！")
        print("=" * 80)

        if summary.get("best_model"):
            best = summary["best_model"]
            print(f"\n🏆 最佳: {best['name']}")
            print(f"   Val MAE: {best['val_mae']:.6f}")
            print(f"   Test MAE: {best['test_mae']:.6f}")
            print(f"   Test R²: {best['test_r2']:.4f}")

        print(f"\n⏰ 完成: {datetime.now().strftime('%H:%M:%S')}")
        print(f"💾 模型: {config.output_dir}/best_model.pkl")

        return summary

    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    summary = ultra_fast_training()
    sys.exit(0 if summary else 1)
