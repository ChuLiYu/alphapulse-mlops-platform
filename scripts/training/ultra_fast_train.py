#!/usr/bin/env python3
"""
超快速模型訓練 - 僅使用最優模型配置

專注於最有效的模型，跳過實驗性配置，快速產生生產模型。
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor

from alphapulse.ml.training.iterative_trainer import IterativeTrainer, TrainingConfig


def ultra_fast_training():
    """超快速訓練 - 僅最優配置"""

    print("=" * 80)
    print("⚡ 超快速生產模型訓練")
    print("=" * 80)
    print(f"⏰ 開始: {datetime.now().strftime('%H:%M:%S')}\n")

    # 極致優化配置
    config = TrainingConfig(
        data_source="model_features",
        target_column="price_change_1d",
        min_samples_required=300,
        n_iterations=3,  # 只訓練 3 個最優模型
        cv_splits=3,
        early_stopping_rounds=20,
        early_stopping_patience=1,
        max_train_val_gap=0.20,  # 稍微放寬以加快速度
        max_val_test_gap=0.15,
        min_val_r2=0.01,
        mlflow_uri=os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"),
        experiment_name="ultra_fast_production",
        output_dir="storage/models/saved",
        save_all_iterations=False,
    )

    print("⚙️  配置: 3 迭代 | 3 折 CV | 快速早停")
    print("🎯 目標: 快速產生可用模型\n")

    # 創建訓練器並覆寫模型配置為僅最優模型
    trainer = IterativeTrainer(config)

    # 手動設置最優模型配置
    best_configs = [
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
            "name": "xgboost_conservative",
            "class": xgb.XGBRegressor,
            "params": {
                "n_estimators": 80,
                "max_depth": 2,
                "learning_rate": 0.03,
                "reg_alpha": 0.2,
                "reg_lambda": 2.0,
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
                "min_samples_split": 20,
                "max_features": "sqrt",
                "n_jobs": -1,
                "random_state": 42,
            },
        },
    ]

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
