#!/usr/bin/env python3
"""
迭代訓練系統驗證腳本

驗證所有組件是否正確安裝和配置。
"""

import os
import sys
from pathlib import Path


def check_imports():
    """檢查所有必要的導入"""
    print("\n🔍 檢查依賴導入...")

    checks = []

    # 基礎依賴
    try:
        import pandas as pd

        checks.append(("✅", "pandas", pd.__version__))
    except ImportError as e:
        checks.append(("❌", "pandas", str(e)))

    try:
        import numpy as np

        checks.append(("✅", "numpy", np.__version__))
    except ImportError as e:
        checks.append(("❌", "numpy", str(e)))

    try:
        import sklearn

        checks.append(("✅", "scikit-learn", sklearn.__version__))
    except ImportError as e:
        checks.append(("❌", "scikit-learn", str(e)))

    try:
        import xgboost as xgb

        checks.append(("✅", "xgboost", xgb.__version__))
    except ImportError as e:
        checks.append(("❌", "xgboost", str(e)))

    try:
        import mlflow

        checks.append(("✅", "mlflow", mlflow.__version__))
    except ImportError as e:
        checks.append(("❌", "mlflow", str(e)))

    try:
        import evidently

        checks.append(("✅", "evidently", evidently.__version__))
    except ImportError as e:
        checks.append(("❌", "evidently", "Not installed - Run: pip install evidently"))

    try:
        import scipy

        checks.append(("✅", "scipy", scipy.__version__))
    except ImportError as e:
        checks.append(("❌", "scipy", str(e)))

    try:
        import psutil

        checks.append(("✅", "psutil", psutil.__version__))
    except ImportError as e:
        checks.append(("❌", "psutil", "Not installed - Run: pip install psutil"))

    # 打印結果
    for status, name, version in checks:
        print(f"  {status} {name:20s} {version}")

    # 檢查失敗
    failed = [c for c in checks if c[0] == "❌"]
    if failed:
        print(f"\n⚠️  {len(failed)} 個依賴缺失")
        return False

    print(f"\n✅ 所有依賴已安裝")
    return True


def check_modules():
    """檢查自定義模塊"""
    print("\n🔍 檢查自定義模塊...")

    checks = []

    try:
        from alphapulse.ml.training.iterative_trainer import (
            IterativeTrainer,
            TrainingConfig,
        )

        checks.append(("✅", "iterative_trainer"))
    except ImportError as e:
        checks.append(("❌", "iterative_trainer", str(e)))

    try:
        from alphapulse.ml.training.overfitting_prevention import OverfittingDetector

        checks.append(("✅", "overfitting_prevention"))
    except ImportError as e:
        checks.append(("❌", "overfitting_prevention", str(e)))

    try:
        from alphapulse.ml.training.monitoring import TrainingMonitor

        checks.append(("✅", "monitoring"))
    except ImportError as e:
        checks.append(("❌", "monitoring", str(e)))

    try:
        from alphapulse.ml.training.evidently_monitoring import EvidentlyMonitor

        checks.append(("✅", "evidently_monitoring"))
    except ImportError as e:
        checks.append(("❌", "evidently_monitoring", str(e)))

    # 打印結果
    for status, name, *error in checks:
        if error:
            print(f"  {status} {name:30s} {error[0]}")
        else:
            print(f"  {status} {name}")

    failed = [c for c in checks if c[0] == "❌"]
    if failed:
        print(f"\n⚠️  {len(failed)} 個模塊無法導入")
        return False

    print(f"\n✅ 所有模塊可用")
    return True


def check_database():
    """檢查數據庫連接"""
    print("\n🔍 檢查數據庫連接...")

    try:
        from sqlalchemy import create_engine, text

        db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/alphapulse"
        )

        print(f"  連接: {db_url.replace('postgres:postgres', 'postgres:***')}")

        engine = create_engine(db_url)
        with engine.connect() as conn:
            # 檢查表是否存在
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('model_features', 'sentiment_scores', 'prices')
            """))
            tables = [row[0] for row in result]

            print(f"  找到的表: {', '.join(tables)}")

            # 檢查 model_features 行數
            if "model_features" in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM model_features"))
                count = result.scalar()
                print(f"  ✅ model_features: {count} 行")

                if count < 1000:
                    print(f"  ⚠️  建議至少 1000 行數據，當前: {count}")
            else:
                print(f"  ❌ model_features 表不存在")
                return False

        print(f"\n✅ 數據庫連接正常")
        return True

    except Exception as e:
        print(f"  ❌ 數據庫連接失敗: {str(e)}")
        return False


def check_mlflow():
    """檢查 MLflow 連接"""
    print("\n🔍 檢查 MLflow 連接...")

    try:
        import mlflow

        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        print(f"  URI: {mlflow_uri}")

        mlflow.set_tracking_uri(mlflow_uri)

        # 嘗試獲取或創建實驗
        experiment_name = "system_check"
        experiment = mlflow.get_experiment_by_name(experiment_name)

        if experiment is None:
            mlflow.create_experiment(experiment_name)

        print(f"  ✅ MLflow 連接正常")
        return True

    except Exception as e:
        print(f"  ⚠️  MLflow 連接失敗: {str(e)}")
        print(f"  提示: 確保 MLflow 服務正在運行")
        return False


def check_directories():
    """檢查輸出目錄"""
    print("\n🔍 檢查輸出目錄...")

    dirs = [
        "/app/src/models/saved",
        "/app/src/models/reports",
        "/app/src/data/processed",
    ]

    for dir_path in dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ⚠️  {dir_path} 不存在，將自動創建")
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"     ✅ 已創建")
            except Exception as e:
                print(f"     ❌ 創建失敗: {str(e)}")
                return False

    print(f"\n✅ 所有目錄就緒")
    return True


def run_mini_test():
    """運行迷你測試"""
    print("\n🧪 運行迷你功能測試...")

    try:
        from alphapulse.ml.training.iterative_trainer import TrainingConfig
        from alphapulse.ml.training.overfitting_prevention import (
            OverfittingDetector,
            OverfittingReport,
        )

        # 測試配置
        config = TrainingConfig(n_iterations=2, output_dir="/tmp/alphapulse_test")
        print(f"  ✅ TrainingConfig 初始化成功")

        # 測試過擬合檢測器
        detector = OverfittingDetector()

        # 模擬指標
        is_overfit, issues, metrics = detector.analyze_performance_gaps(
            train_score=0.001,
            val_score=0.002,
            test_score=0.0021,
            metric_name="MAE",
            lower_is_better=True,
        )

        print(f"  ✅ OverfittingDetector 運行正常")
        print(f"     過擬合: {is_overfit}, 問題數: {len(issues)}")

        print(f"\n✅ 功能測試通過")
        return True

    except Exception as e:
        print(f"  ❌ 功能測試失敗: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主函數"""
    print("=" * 80)
    print("🚀 AlphaPulse 迭代訓練系統 - 驗證腳本")
    print("=" * 80)

    results = []

    # 運行所有檢查
    results.append(("依賴檢查", check_imports()))
    results.append(("模塊檢查", check_modules()))
    results.append(("數據庫檢查", check_database()))
    results.append(("MLflow 檢查", check_mlflow()))
    results.append(("目錄檢查", check_directories()))
    results.append(("功能測試", run_mini_test()))

    # 總結
    print("\n" + "=" * 80)
    print("📊 驗證總結")
    print("=" * 80)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status:10s} {name}")

    # 最終狀態
    all_passed = all(r[1] for r in results)

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 系統驗證通過 - 可以開始訓練！")
        print("=" * 80)
        print("\n下一步:")
        print("  1. 運行訓練: python -m alphapulse.ml.training.iterative_trainer")
        print("  2. 查看文檔: docs/QUICKSTART_ITERATIVE_TRAINING.md")
        print("  3. 查看 MLflow: http://localhost:5001")
        return 0
    else:
        print("❌ 系統驗證失敗 - 請修復上述問題")
        print("=" * 80)
        failed_checks = [name for name, passed in results if not passed]
        print(f"\n失敗的檢查: {', '.join(failed_checks)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
