"""
Model Performance Monitoring using Evidently AI.

This module monitors model predictions and performance metrics over time,
detecting model degradation and prediction drift.

Features:
- Prediction drift detection (comparing recent predictions to baseline)
- Model regression metrics (MAE, RMSE) over time
- Trading signal quality monitoring
- Automated alerting for performance degradation
"""

import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from evidently import ColumnMapping
    from evidently.metric_preset import RegressionPreset
    from evidently.metrics import (
        ColumnDriftMetric,
        RegressionQualityMetric,
        RegressionPredictedVsActualScatter,
        RegressionErrorDistribution,
    )
    from evidently.report import Report
    from evidently.test_suite import TestSuite
    from evidently.tests import (
        TestValueMAE,
        TestValueRMSE,
        TestColumnDrift,
    )

    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False
    print(
        "Evidently AI is not installed. Please install it with: pip install evidently>=0.4.0"
    )

import mlflow


class ModelPerformanceMonitor:
    """
    Monitor model performance for trading predictions.
    
    Tracks:
    - Prediction accuracy (MAE, RMSE)
    - Prediction drift vs baseline
    - Signal quality (hit rate, profit factor)
    """
    
    def __init__(
        self,
        reference_window_days: int = 30,
        current_window_days: int = 7,
        mae_threshold: float = 0.05,
        rmse_threshold: float = 0.08,
        mlflow_tracking_uri: str = "http://mlflow:5000",
    ):
        """
        Initialize model performance monitor.
        
        Args:
            reference_window_days: Days to use as reference baseline
            current_window_days: Days to use as current production data
            mae_threshold: Maximum acceptable MAE before alerting
            rmse_threshold: Maximum acceptable RMSE before alerting
            mlflow_tracking_uri: MLflow tracking server URI
        """
        self.reference_window_days = reference_window_days
        self.current_window_days = current_window_days
        self.mae_threshold = mae_threshold
        self.rmse_threshold = rmse_threshold
        self.mlflow_tracking_uri = mlflow_tracking_uri
        
        # Column mapping for Evidently
        self.column_mapping = ColumnMapping(
            target="actual_return",
            prediction="predicted_return",
            datetime="timestamp",
        )
    
    def compute_performance_report(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Compute model performance report using Evidently.
        
        Args:
            reference_data: Baseline dataset with predictions and actuals
            current_data: Current production dataset
            
        Returns:
            Dictionary with performance metrics and drift results
        """
        if not EVIDENTLY_AVAILABLE:
            raise RuntimeError("Evidently AI is not installed")
        
        # Validate required columns
        required_cols = ["timestamp", "predicted_return", "actual_return"]
        for col in required_cols:
            if col not in reference_data.columns:
                raise ValueError(f"Missing required column: {col}")
            if col not in current_data.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Build performance report
        report = Report(
            metrics=[
                RegressionQualityMetric(),
                RegressionPredictedVsActualScatter(),
                RegressionErrorDistribution(),
                ColumnDriftMetric(column_name="predicted_return"),
            ]
        )
        
        report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping,
        )
        
        # Build test suite
        test_suite = TestSuite(
            tests=[
                TestValueMAE(lte=self.mae_threshold),
                TestValueRMSE(lte=self.rmse_threshold),
                TestColumnDrift(column_name="predicted_return"),
            ]
        )
        
        test_suite.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping,
        )
        
        # Extract results
        report_dict = report.as_dict()
        test_suite_dict = test_suite.as_dict()
        
        # Generate summary
        summary = self._generate_summary(report_dict, test_suite_dict, current_data)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "report": report_dict,
            "test_results": test_suite_dict,
        }
    
    def _generate_summary(
        self,
        report_dict: Dict[str, Any],
        test_suite_dict: Dict[str, Any],
        current_data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Generate summary of model performance.
        
        Args:
            report_dict: Evidently report dictionary
            test_suite_dict: Evidently test suite dictionary
            current_data: Current production data
            
        Returns:
            Summary dictionary with key metrics
        """
        # Extract regression metrics
        metrics = report_dict.get("metrics", [])
        regression_metrics = {}
        
        for metric in metrics:
            metric_id = metric.get("metric", "")
            if "RegressionQualityMetric" in metric_id:
                result = metric.get("result", {}).get("current", {})
                regression_metrics = {
                    "mae": result.get("mean_abs_error", 0),
                    "rmse": result.get("rmse", 0),
                    "r2": result.get("r2_score", 0),
                    "mean_error": result.get("mean_error", 0),
                }
        
        # Extract test results
        tests = test_suite_dict.get("tests", [])
        tests_passed = sum(1 for t in tests if t.get("status") == "SUCCESS")
        tests_total = len(tests)
        
        # Calculate trading signal metrics
        signal_metrics = self._calculate_signal_metrics(current_data)
        
        return {
            "regression_metrics": regression_metrics,
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "all_tests_passed": tests_passed == tests_total,
            "signal_metrics": signal_metrics,
            "performance_status": "healthy" if tests_passed == tests_total else "degraded",
        }
    
    def _calculate_signal_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate trading signal quality metrics.
        
        Args:
            data: DataFrame with predictions and actuals
            
        Returns:
            Dictionary with signal quality metrics
        """
        if len(data) == 0:
            return {"hit_rate": 0, "profit_factor": 0, "total_signals": 0}
        
        # Determine if prediction direction matches actual
        data = data.copy()
        data["pred_direction"] = np.sign(data["predicted_return"])
        data["actual_direction"] = np.sign(data["actual_return"])
        data["correct"] = data["pred_direction"] == data["actual_direction"]
        
        # Hit rate: percentage of correct direction predictions
        hit_rate = data["correct"].mean() if len(data) > 0 else 0
        
        # Profit factor: sum of winning trades / sum of losing trades
        gains = data.loc[data["correct"], "actual_return"].abs().sum()
        losses = data.loc[~data["correct"], "actual_return"].abs().sum()
        profit_factor = gains / losses if losses > 0 else float("inf")
        
        return {
            "hit_rate": float(hit_rate),
            "profit_factor": float(profit_factor) if profit_factor != float("inf") else 99.0,
            "total_signals": int(len(data)),
        }
    
    def log_to_mlflow(
        self,
        performance_result: Dict[str, Any],
        experiment_name: str = "model_performance",
    ) -> None:
        """
        Log performance results to MLflow.
        
        Args:
            performance_result: Dictionary with performance metrics
            experiment_name: MLflow experiment name
        """
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)
        
        summary = performance_result.get("summary", {})
        regression = summary.get("regression_metrics", {})
        signals = summary.get("signal_metrics", {})
        
        with mlflow.start_run(run_name=f"perf_{datetime.now().strftime('%Y%m%d_%H%M')}"):
            # Log regression metrics
            mlflow.log_metric("mae", regression.get("mae", 0))
            mlflow.log_metric("rmse", regression.get("rmse", 0))
            mlflow.log_metric("r2", regression.get("r2", 0))
            
            # Log signal metrics
            mlflow.log_metric("hit_rate", signals.get("hit_rate", 0))
            mlflow.log_metric("profit_factor", signals.get("profit_factor", 0))
            mlflow.log_metric("total_signals", signals.get("total_signals", 0))
            
            # Log test results
            mlflow.log_metric("tests_passed", summary.get("tests_passed", 0))
            mlflow.log_metric("tests_total", summary.get("tests_total", 0))
            
            # Log status
            mlflow.log_param("performance_status", summary.get("performance_status", "unknown"))
            
            # Log full report as artifact
            report_path = "/tmp/performance_report.json"
            with open(report_path, "w") as f:
                json.dump(performance_result, f, indent=2, default=str)
            mlflow.log_artifact(report_path)
        
        print(f"✅ Performance metrics logged to MLflow experiment: {experiment_name}")
    
    def check_and_alert(self, performance_result: Dict[str, Any]) -> bool:
        """
        Check performance and generate alerts if needed.
        
        Args:
            performance_result: Dictionary with performance metrics
            
        Returns:
            True if alert was generated, False otherwise
        """
        summary = performance_result.get("summary", {})
        
        if not summary.get("all_tests_passed", True):
            regression = summary.get("regression_metrics", {})
            print("\n" + "=" * 60)
            print("⚠️  MODEL PERFORMANCE ALERT")
            print("=" * 60)
            print(f"Status: {summary.get('performance_status', 'unknown').upper()}")
            print(f"MAE: {regression.get('mae', 0):.6f} (threshold: {self.mae_threshold})")
            print(f"RMSE: {regression.get('rmse', 0):.6f} (threshold: {self.rmse_threshold})")
            print(f"Tests: {summary.get('tests_passed', 0)}/{summary.get('tests_total', 0)} passed")
            print("=" * 60 + "\n")
            return True
        
        return False


def run_model_performance_monitoring(
    predictions_path: str = "/home/src/src/results/predictions.parquet",
    mlflow_uri: str = None,
) -> Dict[str, Any]:
    """
    Run model performance monitoring.
    
    Args:
        predictions_path: Path to parquet file with predictions
        mlflow_uri: MLflow tracking URI (defaults to env var)
        
    Returns:
        Performance monitoring results
    """
    mlflow_uri = mlflow_uri or os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    
    print("=" * 60)
    print("MODEL PERFORMANCE MONITORING")
    print("=" * 60)
    
    # Load predictions data
    if not os.path.exists(predictions_path):
        print(f"⚠️ Predictions file not found: {predictions_path}")
        print("Generating sample data for demonstration...")
        
        # Generate sample data if file doesn't exist
        np.random.seed(42)
        n = 100
        dates = pd.date_range(end=datetime.now(), periods=n, freq="D")
        
        data = pd.DataFrame({
            "timestamp": dates,
            "predicted_return": np.random.randn(n) * 0.02,
            "actual_return": np.random.randn(n) * 0.02,
        })
    else:
        data = pd.read_parquet(predictions_path)
    
    # Split into reference and current
    split_idx = int(len(data) * 0.7)
    reference_data = data.iloc[:split_idx].copy()
    current_data = data.iloc[split_idx:].copy()
    
    print(f"Reference data: {len(reference_data)} samples")
    print(f"Current data: {len(current_data)} samples")
    
    # Initialize monitor
    monitor = ModelPerformanceMonitor(mlflow_tracking_uri=mlflow_uri)
    
    # Compute performance report
    try:
        result = monitor.compute_performance_report(reference_data, current_data)
        
        # Log to MLflow
        monitor.log_to_mlflow(result)
        
        # Check and alert
        monitor.check_and_alert(result)
        
        # Print summary
        summary = result.get("summary", {})
        print("\n" + "-" * 40)
        print("SUMMARY")
        print("-" * 40)
        print(f"Status: {summary.get('performance_status', 'unknown')}")
        print(f"MAE: {summary.get('regression_metrics', {}).get('mae', 0):.6f}")
        print(f"Hit Rate: {summary.get('signal_metrics', {}).get('hit_rate', 0)*100:.1f}%")
        print("-" * 40)
        
        return result
        
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
        raise


if __name__ == "__main__":
    run_model_performance_monitoring()
