"""
Evidently-based Monitoring System for ML Training.

This module integrates Evidently for:
1. Data drift detection (sentiment, price, technical features)
2. Model performance monitoring
3. Prediction drift analysis
4. Interactive HTML reports
5. Integration with MLflow
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

import mlflow

try:
    from evidently import ColumnMapping
    from evidently.metric_preset import (
        DataDriftPreset,
        DataQualityPreset,
        RegressionPreset,
        TargetDriftPreset,
    )
    from evidently.metrics import (
        ColumnDriftMetric,
        DatasetDriftMetric,
        RegressionAbsPercentageErrorPlot,
        RegressionErrorDistribution,
        RegressionErrorPlot,
        RegressionPredictedVsActualScatter,
        RegressionQualityMetric,
        RegressionTopErrorMetric,
    )
    from evidently.report import Report
    from evidently.test_suite import TestSuite
    from evidently.tests import (
        TestColumnDrift,
        TestColumnsType,
        TestNumberOfColumnsWithMissingValues,
        TestNumberOfConstantColumns,
        TestNumberOfDriftedColumns,
        TestNumberOfDuplicatedColumns,
        TestNumberOfDuplicatedRows,
        TestNumberOfRowsWithMissingValues,
        TestShareOfDriftedColumns,
    )

    EVIDENTLY_AVAILABLE = True
    ColumnMapping = ColumnMapping  # Make it available at module level
except ImportError:
    EVIDENTLY_AVAILABLE = False
    ColumnMapping = None  # Define as None if not available
    print("⚠️  Evidently not installed. Run: pip install evidently")


@dataclass
class DriftReport:
    """Data drift analysis report."""

    timestamp: str
    dataset_drift_detected: bool
    drift_score: float
    drifted_features: List[str]
    drift_by_feature: Dict[str, float]
    n_features: int
    n_drifted_features: int
    drift_share: float


@dataclass
class PerformanceReport:
    """Model performance report."""

    timestamp: str
    mae: float
    rmse: float
    r2: float
    mape: float
    max_error: float
    mean_error: float

    # Error distribution
    error_std: float
    error_q25: float
    error_q50: float
    error_q75: float

    # Top errors
    top_error_threshold: float
    n_top_errors: int


class EvidentlyMonitor:
    """
    ML monitoring system using Evidently.

    Features:
    - Data drift detection for features
    - Target drift detection
    - Model performance monitoring
    - Prediction quality analysis
    - Interactive HTML reports
    """

    def __init__(
        self,
        output_dir: str = "/app/src/models/reports",
        mlflow_uri: Optional[str] = None,
    ):
        """
        Initialize Evidently monitor.

        Args:
            output_dir: Directory for reports
            mlflow_uri: MLflow tracking URI (optional)
        """
        if not EVIDENTLY_AVAILABLE:
            raise ImportError("Evidently is not installed. Run: pip install evidently")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.mlflow_uri = mlflow_uri
        if mlflow_uri:
            mlflow.set_tracking_uri(mlflow_uri)

    def setup_column_mapping(
        self,
        target_col: str = "price_change_1d",
        prediction_col: str = "prediction",
        datetime_col: Optional[str] = "date",
        numerical_features: Optional[List[str]] = None,
        categorical_features: Optional[List[str]] = None,
    ) -> ColumnMapping:
        """
        Setup column mapping for Evidently.

        Args:
            target_col: Target column name
            prediction_col: Prediction column name
            datetime_col: Datetime column name
            numerical_features: List of numerical feature names
            categorical_features: List of categorical feature names

        Returns:
            ColumnMapping object
        """
        column_mapping = ColumnMapping()

        column_mapping.target = target_col
        column_mapping.prediction = prediction_col

        if datetime_col:
            column_mapping.datetime = datetime_col

        if numerical_features:
            column_mapping.numerical_features = numerical_features

        if categorical_features:
            column_mapping.categorical_features = categorical_features

        return column_mapping

    def detect_data_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        column_mapping: ColumnMapping,
        drift_threshold: float = 0.5,
    ) -> DriftReport:
        """
        Detect data drift between reference and current data.

        Args:
            reference_data: Reference (training) data
            current_data: Current (production) data
            column_mapping: Column mapping configuration
            drift_threshold: Threshold for drift detection

        Returns:
            DriftReport with drift analysis
        """
        print("\n🔍 Detecting data drift with Evidently...")

        # Create data drift report
        report = Report(
            metrics=[
                DataDriftPreset(drift_share=drift_threshold),
            ]
        )

        report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping,
        )

        # Get results
        result = report.as_dict()

        # Extract drift metrics
        drift_metrics = result["metrics"][0]["result"]

        dataset_drift = drift_metrics["dataset_drift"]
        drift_share = drift_metrics["share_of_drifted_columns"]
        n_features = drift_metrics["number_of_columns"]
        n_drifted = drift_metrics["number_of_drifted_columns"]

        # Get per-feature drift
        drift_by_feature = {}
        drifted_features = []

        if "drift_by_columns" in drift_metrics:
            for feature, info in drift_metrics["drift_by_columns"].items():
                if isinstance(info, dict):
                    drift_score = info.get("drift_score", 0)
                    drift_detected = info.get("drift_detected", False)

                    drift_by_feature[feature] = drift_score
                    if drift_detected:
                        drifted_features.append(feature)

        # Create report
        drift_report = DriftReport(
            timestamp=datetime.now().isoformat(),
            dataset_drift_detected=dataset_drift,
            drift_score=drift_share,
            drifted_features=drifted_features,
            drift_by_feature=drift_by_feature,
            n_features=n_features,
            n_drifted_features=n_drifted,
            drift_share=drift_share,
        )

        # Print summary
        print(f"  Dataset Drift: {'⚠️  YES' if dataset_drift else '✅ NO'}")
        print(f"  Drifted Features: {n_drifted}/{n_features} ({drift_share:.1%})")
        if drifted_features:
            print(f"  Features: {', '.join(drifted_features[:5])}")
            if len(drifted_features) > 5:
                print(f"    ... and {len(drifted_features) - 5} more")

        # Save report
        report_path = (
            self.output_dir / f"data_drift_report_{datetime.now():%Y%m%d_%H%M%S}.html"
        )
        report.save_html(str(report_path))
        print(f"  📄 Report saved: {report_path}")

        return drift_report

    def analyze_model_performance(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        column_mapping: ColumnMapping,
    ) -> PerformanceReport:
        """
        Analyze model performance using Evidently.

        Args:
            reference_data: Reference data with predictions
            current_data: Current data with predictions
            column_mapping: Column mapping configuration

        Returns:
            PerformanceReport with performance metrics
        """
        print("\n📊 Analyzing model performance with Evidently...")

        # Create performance report
        report = Report(
            metrics=[
                RegressionPreset(),
            ]
        )

        report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping,
        )

        # Get results
        result = report.as_dict()

        # Extract metrics from current data
        current_metrics = None
        for metric in result["metrics"]:
            if metric["metric"] == "RegressionQualityMetric":
                current_metrics = metric["result"]["current"]
                break

        if current_metrics is None:
            raise ValueError("Could not find regression quality metrics in report")

        # Create performance report
        perf_report = PerformanceReport(
            timestamp=datetime.now().isoformat(),
            mae=current_metrics["mean_abs_error"],
            rmse=current_metrics["rmse"],
            r2=current_metrics.get("r2_score", 0),
            mape=current_metrics.get("mean_abs_perc_error", 0),
            max_error=current_metrics.get("abs_error_max", 0),
            mean_error=current_metrics["mean_error"],
            error_std=current_metrics["error_std"],
            error_q25=current_metrics.get("abs_error_q25", 0),
            error_q50=current_metrics.get("abs_error_median", 0),
            error_q75=current_metrics.get("abs_error_q75", 0),
            top_error_threshold=0,
            n_top_errors=0,
        )

        # Print summary
        print(f"  MAE: {perf_report.mae:.6f}")
        print(f"  RMSE: {perf_report.rmse:.6f}")
        print(f"  R²: {perf_report.r2:.4f}")
        print(f"  MAPE: {perf_report.mape:.2f}%")

        # Save report
        report_path = (
            self.output_dir / f"performance_report_{datetime.now():%Y%m%d_%H%M%S}.html"
        )
        report.save_html(str(report_path))
        print(f"  📄 Report saved: {report_path}")

        return perf_report

    def generate_comprehensive_report(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        column_mapping: ColumnMapping,
        report_name: str = "comprehensive_ml_monitoring",
    ) -> str:
        """
        Generate comprehensive monitoring report.

        Args:
            reference_data: Reference (training) data
            current_data: Current (validation/test) data
            column_mapping: Column mapping configuration
            report_name: Name for the report

        Returns:
            Path to generated HTML report
        """
        print("\n📋 Generating comprehensive Evidently report...")

        # Create comprehensive report with all metrics
        report = Report(
            metrics=[
                # Data quality
                DataQualityPreset(),
                # Data drift
                DataDriftPreset(),
                # Target drift
                TargetDriftPreset(),
                # Regression performance
                RegressionPreset(),
                # Additional detailed metrics
                RegressionQualityMetric(),
                RegressionPredictedVsActualScatter(),
                RegressionErrorPlot(),
                RegressionAbsPercentageErrorPlot(),
                RegressionErrorDistribution(),
                RegressionTopErrorMetric(top_error=0.05),  # Top 5% errors
            ]
        )

        report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping,
        )

        # Save report
        report_path = (
            self.output_dir / f"{report_name}_{datetime.now():%Y%m%d_%H%M%S}.html"
        )
        report.save_html(str(report_path))

        print(f"  ✅ Comprehensive report saved: {report_path}")

        return str(report_path)

    def run_data_quality_tests(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        column_mapping: ColumnMapping,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Run data quality test suite.

        Args:
            reference_data: Reference data
            current_data: Current data
            column_mapping: Column mapping configuration

        Returns:
            Tuple of (all_tests_passed, test_results)
        """
        print("\n🧪 Running data quality tests with Evidently...")

        # Create test suite
        test_suite = TestSuite(
            tests=[
                TestNumberOfColumnsWithMissingValues(),
                TestNumberOfRowsWithMissingValues(),
                TestNumberOfConstantColumns(),
                TestNumberOfDuplicatedRows(),
                TestNumberOfDuplicatedColumns(),
                TestColumnsType(),
            ]
        )

        test_suite.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping,
        )

        # Get results
        result = test_suite.as_dict()

        # Check if all tests passed
        all_passed = result["summary"]["all_passed"]
        total_tests = result["summary"]["total_tests"]
        passed_tests = result["summary"]["success_tests"]
        failed_tests = result["summary"]["failed_tests"]

        print(f"  Tests: {passed_tests}/{total_tests} passed")
        if not all_passed:
            print(f"  ⚠️  {failed_tests} test(s) failed")
        else:
            print(f"  ✅ All tests passed!")

        # Save test suite
        test_path = (
            self.output_dir / f"data_quality_tests_{datetime.now():%Y%m%d_%H%M%S}.html"
        )
        test_suite.save_html(str(test_path))
        print(f"  📄 Test report saved: {test_path}")

        return all_passed, result["summary"]

    def run_drift_tests(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        column_mapping: ColumnMapping,
        drift_threshold: float = 0.5,
        important_features: Optional[List[str]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Run drift detection test suite.

        Args:
            reference_data: Reference data
            current_data: Current data
            column_mapping: Column mapping configuration
            drift_threshold: Threshold for drift detection
            important_features: List of important features to test individually

        Returns:
            Tuple of (all_tests_passed, test_results)
        """
        print("\n🧪 Running drift tests with Evidently...")

        # Build test list
        tests = [
            TestNumberOfDriftedColumns(
                lt=int(reference_data.shape[1] * drift_threshold)
            ),
            TestShareOfDriftedColumns(lt=drift_threshold),
        ]

        # Add tests for important features
        if important_features:
            for feature in important_features:
                if feature in reference_data.columns:
                    tests.append(TestColumnDrift(column_name=feature))

        # Create test suite
        test_suite = TestSuite(tests=tests)

        test_suite.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping,
        )

        # Get results
        result = test_suite.as_dict()

        # Check if all tests passed
        all_passed = result["summary"]["all_passed"]
        total_tests = result["summary"]["total_tests"]
        passed_tests = result["summary"]["success_tests"]
        failed_tests = result["summary"]["failed_tests"]

        print(f"  Tests: {passed_tests}/{total_tests} passed")
        if not all_passed:
            print(f"  ⚠️  {failed_tests} drift test(s) failed")
        else:
            print(f"  ✅ All drift tests passed!")

        # Save test suite
        test_path = self.output_dir / f"drift_tests_{datetime.now():%Y%m%d_%H%M%S}.html"
        test_suite.save_html(str(test_path))
        print(f"  📄 Test report saved: {test_path}")

        return all_passed, result["summary"]

    def monitor_training_iteration(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        target_col: str = "price_change_1d",
        prediction_col: str = "prediction",
        important_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Monitor a training iteration with full Evidently analysis.

        Args:
            reference_data: Reference (previous iteration or training) data
            current_data: Current iteration data
            target_col: Target column name
            prediction_col: Prediction column name
            important_features: List of important features to monitor

        Returns:
            Dictionary with monitoring results
        """
        print("\n" + "=" * 80)
        print("🔍 EVIDENTLY MONITORING - Training Iteration")
        print("=" * 80)

        # Setup column mapping
        exclude_cols = [
            "id",
            "date",
            "ticker",
            "created_at",
            "feature_set_version",
            "data_source",
        ]
        feature_cols = [
            col
            for col in reference_data.columns
            if col not in exclude_cols + [target_col, prediction_col]
        ]

        column_mapping = self.setup_column_mapping(
            target_col=target_col,
            prediction_col=prediction_col,
            numerical_features=feature_cols,
        )

        results = {}

        # 1. Data quality tests
        quality_passed, quality_summary = self.run_data_quality_tests(
            reference_data, current_data, column_mapping
        )
        results["data_quality"] = {"passed": quality_passed, "summary": quality_summary}

        # 2. Drift detection
        drift_report = self.detect_data_drift(
            reference_data, current_data, column_mapping
        )
        results["data_drift"] = {
            "detected": drift_report.dataset_drift_detected,
            "score": drift_report.drift_score,
            "n_drifted": drift_report.n_drifted_features,
            "drifted_features": drift_report.drifted_features,
        }

        # 3. Drift tests
        if important_features is None and drift_report.drifted_features:
            # Use top drifted features
            important_features = drift_report.drifted_features[:5]

        drift_tests_passed, drift_test_summary = self.run_drift_tests(
            reference_data,
            current_data,
            column_mapping,
            important_features=important_features,
        )
        results["drift_tests"] = {
            "passed": drift_tests_passed,
            "summary": drift_test_summary,
        }

        # 4. Performance analysis (if predictions available)
        if prediction_col in current_data.columns:
            perf_report = self.analyze_model_performance(
                reference_data, current_data, column_mapping
            )
            results["performance"] = {
                "mae": perf_report.mae,
                "rmse": perf_report.rmse,
                "r2": perf_report.r2,
                "mape": perf_report.mape,
            }

        # 5. Comprehensive report
        report_path = self.generate_comprehensive_report(
            reference_data, current_data, column_mapping
        )
        results["report_path"] = report_path

        # Summary
        print("\n" + "=" * 80)
        print("📊 MONITORING SUMMARY")
        print("=" * 80)
        print(f"  Data Quality: {'✅ PASS' if quality_passed else '❌ FAIL'}")
        print(
            f"  Data Drift: {'⚠️  DETECTED' if drift_report.dataset_drift_detected else '✅ OK'}"
        )
        print(f"  Drift Tests: {'✅ PASS' if drift_tests_passed else '❌ FAIL'}")
        if "performance" in results:
            print(
                f"  Performance: MAE={results['performance']['mae']:.6f}, R²={results['performance']['r2']:.4f}"
            )
        print("=" * 80)

        # Log to MLflow if available
        if self.mlflow_uri:
            try:
                with mlflow.start_run(run_name="evidently_monitoring", nested=True):
                    mlflow.log_metrics(
                        {
                            "data_quality_passed": 1 if quality_passed else 0,
                            "data_drift_detected": (
                                1 if drift_report.dataset_drift_detected else 0
                            ),
                            "drift_score": drift_report.drift_score,
                            "n_drifted_features": drift_report.n_drifted_features,
                            "drift_tests_passed": 1 if drift_tests_passed else 0,
                        }
                    )

                    if "performance" in results:
                        mlflow.log_metrics(
                            {
                                "evidently_mae": results["performance"]["mae"],
                                "evidently_rmse": results["performance"]["rmse"],
                                "evidently_r2": results["performance"]["r2"],
                            }
                        )

                    # Log report as artifact
                    mlflow.log_artifact(report_path)

                print("✅ Logged to MLflow")
            except Exception as e:
                print(f"⚠️  Could not log to MLflow: {str(e)}")

        return results


def create_monitoring_dashboard(
    reports_dir: str = "/app/src/models/reports",
    output_file: str = "monitoring_dashboard.html",
) -> str:
    """
    Create a simple HTML dashboard linking to all Evidently reports.

    Args:
        reports_dir: Directory containing Evidently reports
        output_file: Output dashboard filename

    Returns:
        Path to dashboard HTML file
    """
    reports_path = Path(reports_dir)

    # Find all HTML reports
    reports = sorted(
        reports_path.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True
    )

    # Create simple HTML dashboard
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AlphaPulse ML Monitoring Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            h1 { color: #333; }
            .report-list { list-style: none; padding: 0; }
            .report-item { 
                background: white; 
                margin: 10px 0; 
                padding: 15px; 
                border-radius: 5px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .report-item a { 
                text-decoration: none; 
                color: #0066cc; 
                font-weight: bold;
            }
            .report-item a:hover { text-decoration: underline; }
            .report-date { color: #666; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <h1>🎯 AlphaPulse ML Monitoring Dashboard</h1>
        <p>Evidently reports for model training and data quality monitoring</p>
        <ul class="report-list">
    """

    for report in reports:
        modified_time = datetime.fromtimestamp(report.stat().st_mtime)
        html += f"""
            <li class="report-item">
                <a href="{report.name}" target="_blank">{report.name}</a>
                <div class="report-date">Generated: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
            </li>
        """

    html += """
        </ul>
    </body>
    </html>
    """

    # Save dashboard
    dashboard_path = reports_path / output_file
    with open(dashboard_path, "w") as f:
        f.write(html)

    print(f"📊 Dashboard created: {dashboard_path}")
    return str(dashboard_path)
