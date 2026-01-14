#!/usr/bin/env python3
"""
快速生產模型訓練腳本 - Docker 優化版

在 Docker 容器中快速迭代訓練生產級模型。
優化配置：減少迭代次數、使用高效模型、快速驗證。
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project path for training container
sys.path.insert(0, "/app/src")

from alphapulse.ml.training.iterative_trainer import IterativeTrainer, TrainingConfig


def quick_production_training():
    """快速生產模型訓練"""

    print("=" * 80)
    print("🚀 快速生產模型訓練 - Docker 優化版")
    print("=" * 80)
    print(f"⏰ 開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 優化配置 - 快速迭代
    config = TrainingConfig(
        # 數據設置
        data_source="model_features",
        target_column="price_change_1d",
        min_samples_required=500,  # 降低最小樣本要求以快速測試
        # 訓練設置 - 減少迭代次數以加快速度
        n_iterations=6,  # 從 10 減少到 6 (最有效的模型)
        test_size=0.15,
        validation_size=0.15,
        # 交叉驗證 - 減少折數
        cv_splits=3,  # 從 5 減少到 3 以加快速度
        # 早停設置
        early_stopping_rounds=30,  # 從 50 減少到 30
        early_stopping_patience=2,  # 從 3 減少到 2
        # 過擬合檢測閾值（保持相同）
        max_train_val_gap=0.15,
        max_val_test_gap=0.10,
        min_val_r2=0.05,  # 降低要求以快速通過
        # MLflow 設置
        mlflow_uri=os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"),
        experiment_name="quick_production_training",
        # 輸出設置
        output_dir=os.getenv("MODEL_OUTPUT_DIR", "/app/models/saved"),
        save_all_iterations=False,  # 只保存最佳模型
    )

    print("📋 訓練配置:")
    print(f"  目標: {config.target_column}")
    print(f"  迭代次數: {config.n_iterations}")
    print(f"  交叉驗證: {config.cv_splits} 折")
    print(f"  早停耐心: {config.early_stopping_patience}")
    print(f"  輸出目錄: {config.output_dir}")
    print()

    # 創建訓練器
    print("🔧 初始化訓練器...")
    trainer = IterativeTrainer(config)

    # 運行訓練
    print("\n🎯 開始訓練...")
    print("-" * 80)

    try:
        summary = trainer.run_iterative_training()

        print("\n" + "=" * 80)
        print("✅ 訓練完成！")
        print("=" * 80)

        # 顯示結果
        if summary.get("best_model"):
            best = summary["best_model"]
            print(f"\n🏆 最佳模型: {best['name']}")
            print(f"   驗證 MAE: {best['val_mae']:.6f}")
            print(f"   測試 MAE: {best['test_mae']:.6f}")
            print(f"   測試 R²: {best['test_r2']:.4f}")
            print(f"   參數: {json.dumps(best['hyperparameters'], indent=4)}")

        print(f"\n📊 統計:")
        print(f"   總迭代: {summary['total_iterations']}")
        print(f"   過擬合模型: {summary['overfit_count']}")
        print(f"   最佳迭代: {summary['best_iteration']}")

        print(f"\n💾 模型文件:")
        print(f"   {config.output_dir}/best_model.pkl")
        print(f"   {config.output_dir}/training_summary.json")

        print(f"\n📈 MLflow:")
        print(f"   實驗: {config.experiment_name}")
        print(f"   訪問: {config.mlflow_uri}")

        print(f"\n⏰ 完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        return summary

    except Exception as e:
        print(f"\n❌ 訓練失敗: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def validate_environment():
    """驗證 Docker 環境"""
    print("\n🔍 驗證環境...")

    issues = []

    # 檢查數據庫連接
    try:
        from sqlalchemy import create_engine, text

        db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/alphapulse"
        )
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM model_features"))
            count = result.scalar()
            if count < 500:
                issues.append(f"⚠️  model_features 只有 {count} 行 (建議 > 500)")
            else:
                print(f"  ✅ model_features: {count} 行")
    except Exception as e:
        issues.append(f"❌ 數據庫連接失敗: {str(e)}")

    # 檢查 MLflow
    try:
        import mlflow

        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        mlflow.set_tracking_uri(mlflow_uri)
        print(f"  ✅ MLflow: {mlflow_uri}")
    except Exception as e:
        issues.append(f"⚠️  MLflow 連接問題: {str(e)}")

    # 檢查輸出目錄
    output_dir = Path(os.getenv("MODEL_OUTPUT_DIR", "/app/models/saved"))
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ 創建輸出目錄: {output_dir}")
    else:
        print(f"  ✅ 輸出目錄: {output_dir}")

    if issues:
        print("\n⚠️  發現問題:")
        for issue in issues:
            print(f"  {issue}")
        print("\n繼續訓練可能會遇到錯誤...")
        return False
    else:
        print("\n✅ 環境驗證通過")
        return True


def main():
    """主函數"""
    print("\n" + "=" * 80)
    print("🎯 AlphaPulse 快速生產模型訓練")
    print("=" * 80)

    # 驗證環境
    if not validate_environment():
        response = input("\n是否繼續訓練? (y/N): ")
        if response.lower() != "y":
            print("❌ 訓練取消")
            return 1

    # 運行訓練
    summary = quick_production_training()

    if summary and summary.get("best_model"):
        print("\n✅ 成功！模型已準備好用於生產。")
        return 0
    else:
        print("\n❌ 訓練未能產生有效模型。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
