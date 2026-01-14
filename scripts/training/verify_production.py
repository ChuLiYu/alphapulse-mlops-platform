#!/usr/bin/env python3
"""
生产环境验证脚本

检查 AlphaPulse MLOps 系统的关键组件是否正常工作。
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2


# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


def print_status(message, status):
    """打印带颜色的状态信息"""
    if status == "OK":
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
    elif status == "FAIL":
        print(f"{Colors.RED}✗{Colors.END} {message}")
    elif status == "WARN":
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")
    else:
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")


def check_database():
    """检查数据库连接和表"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}数据库检查{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    db_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/alphapulse"
    )

    try:
        # 解析 URL
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        print_status("数据库连接成功", "OK")

        # 检查关键表
        required_tables = [
            "prices",
            "technical_indicators",
            "market_news",
            "sentiment_scores",
        ]

        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        existing_tables = [row[0] for row in cur.fetchall()]

        for table in required_tables:
            if table in existing_tables:
                # 获取行数
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print_status(f"表 '{table}' 存在 ({count} 行)", "OK")
            else:
                print_status(f"表 '{table}' 不存在", "FAIL")

        # 检查数据时间范围
        cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM prices")
        min_date, max_date = cur.fetchone()
        if min_date and max_date:
            print_status(f"价格数据范围: {min_date} 至 {max_date}", "INFO")

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print_status(f"数据库检查失败: {str(e)}", "FAIL")
        return False


def check_training_data():
    """检查训练数据文件"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}训练数据检查{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    data_dir = Path("/home/src/src/data/processed")
    if not data_dir.exists():
        data_dir = Path("/app/src/data/processed")

    if not data_dir.exists():
        print_status(f"数据目录不存在: {data_dir}", "FAIL")
        return False

    required_files = ["train.parquet", "val.parquet", "test.parquet"]
    all_exist = True

    for filename in required_files:
        filepath = data_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print_status(f"文件 '{filename}' 存在 ({size_mb:.2f} MB)", "OK")
        else:
            print_status(f"文件 '{filename}' 不存在", "FAIL")
            all_exist = False

    return all_exist


def check_model_files():
    """检查模型文件"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}模型文件检查{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    model_dir = Path("/home/src/src/models/saved")
    if not model_dir.exists():
        model_dir = Path("/app/src/models/saved")

    if not model_dir.exists():
        print_status(f"模型目录不存在: {model_dir}", "WARN")
        return False

    model_file = model_dir / "best_model.pkl"
    config_file = model_dir / "best_model_config.json"

    if model_file.exists():
        size_mb = model_file.stat().st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(model_file.stat().st_mtime)
        print_status(f"最佳模型存在 ({size_mb:.2f} MB)", "OK")
        print_status(f"模型更新时间: {mod_time}", "INFO")

        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
            print_status(f"模型配置存在", "OK")
            print_status(f"模型名称: {config.get('model_name', 'N/A')}", "INFO")
            print_status(
                f"Sharpe Ratio: {config.get('metrics', {}).get('sharpe_ratio', 'N/A'):.4f}",
                "INFO",
            )
            print_status(
                f"Total Return: {config.get('metrics', {}).get('total_return', 0)*100:.2f}%",
                "INFO",
            )
        else:
            print_status("模型配置文件不存在", "WARN")

        return True
    else:
        print_status("最佳模型文件不存在", "WARN")
        print_status("提示: 运行 auto_train.py 生成模型", "INFO")
        return False


def check_mlflow():
    """检查 MLflow 连接"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}MLflow 检查{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    try:
        import mlflow

        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        mlflow.set_tracking_uri(mlflow_uri)

        # 尝试列出实验
        experiments = mlflow.search_experiments()
        print_status(f"MLflow 连接成功 ({mlflow_uri})", "OK")
        print_status(f"实验数量: {len(experiments)}", "INFO")

        # 查找训练实验
        training_exp = None
        for exp in experiments:
            if "training" in exp.name.lower():
                training_exp = exp
                break

        if training_exp:
            runs = mlflow.search_runs(
                experiment_ids=[training_exp.experiment_id], max_results=5
            )
            print_status(f"训练实验存在: '{training_exp.name}'", "OK")
            print_status(f"最近运行数: {len(runs)}", "INFO")

            if not runs.empty:
                latest_run = runs.iloc[0]
                print_status(f"最新运行时间: {latest_run['start_time']}", "INFO")
                if "metrics.sharpe_ratio" in runs.columns:
                    print_status(
                        f"最佳 Sharpe: {runs['metrics.sharpe_ratio'].max():.4f}", "INFO"
                    )
        else:
            print_status("未找到训练实验", "WARN")

        return True

    except Exception as e:
        print_status(f"MLflow 检查失败: {str(e)}", "FAIL")
        return False


def check_python_environment():
    """检查 Python 环境和依赖"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Python 环境检查{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    print_status(f"Python 版本: {sys.version.split()[0]}", "INFO")

    required_packages = [
        "pandas",
        "numpy",
        "sqlalchemy",
        "xgboost",
        "scikit-learn",
        "mlflow",
        "psycopg2",
        "joblib",
    ]

    for package in required_packages:
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "unknown")
            print_status(f"{package}: {version}", "OK")
        except ImportError:
            print_status(f"{package}: 未安装", "FAIL")


def main():
    """主函数"""
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}AlphaPulse 生产环境验证{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        "python_env": check_python_environment(),
        "database": check_database(),
        "training_data": check_training_data(),
        "model_files": check_model_files(),
        "mlflow": check_mlflow(),
    }

    # 总结
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}验证总结{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

    passed = sum(results.values())
    total = len(results)

    for component, status in results.items():
        status_str = "通过" if status else "失败"
        print_status(f"{component}: {status_str}", "OK" if status else "FAIL")

    print(f"\n总体状态: {passed}/{total} 项检查通过")

    if passed == total:
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}✓ 系统已准备好投入生产{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
        print(f"{Colors.YELLOW}⚠ 系统需要进一步配置{Colors.END}")
        print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
        return 1


if __name__ == "__main__":
    exit(main())
