"""
Data drift monitoring using Evidently AI.

This module provides functionality to detect data drift in financial time series data
and technical indicators. It uses Evidently AI to compute drift metrics and generate
reports that can be stored in MLflow or sent as alerts.

Key Features:
- Data drift detection for numerical features (price, volume, technical indicators)
- Statistical tests: Kolmogorov-Smirnov, Wasserstein distance
- Reference/target dataset comparison
- MLflow integration for tracking drift metrics
- Alert generation when drift exceeds thresholds
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from evidently import ColumnMapping
    from evidently.metric_preset import DataDriftPreset
    from evidently.metrics import (
        ColumnCorrelationsMetric,
        ColumnDriftMetric,
        ColumnQuantileMetric,
        ColumnSummaryMetric,
        DatasetDriftMetric,
        DatasetMissingValuesMetric,
    )
    from evidently.renderers.html_widgets import WidgetSize
    from evidently.report import Report
    from evidently.test_suite import TestSuite
    from evidently.tests import (
        TestColumnDrift,
        TestColumnValueRange,
        TestNumberOfDriftedColumns,
        TestShareOfDriftedColumns,
    )
    from evidently.ui.dashboards import DashboardPanelPlot, PanelValue, ReportFilter
    from evidently.ui.workspace import Workspace
except ImportError:
    raise ImportError(
        "Evidently AI is not installed. Please install it with: pip install evidently>=0.4.0"
    )

from sqlalchemy.orm import Session

from alphapulse.api.database import get_db_session
from alphapulse.api.models import BTCPrice, TechnicalIndicator


class DataDriftMonitor:
    """
    Monitor data drift for financial time series data.

    This class provides methods to:
    1. Load reference and current datasets from PostgreSQL
    2. Compute drift metrics using Evidently AI
    3. Generate reports and test suites
    4. Store results in MLflow
    5. Send alerts when drift is detected
    """

    def __init__(
        self,
        reference_window_days: int = 30,
        current_window_days: int = 7,
        drift_threshold: float = 0.05,
        mlflow_tracking_uri: str = "http://localhost:5001",
    ):
        """
        Initialize the data drift monitor.

        Args:
            reference_window_days: Number of days to use as reference (baseline) data
            current_window_days: Number of days to use as current (production) data
            drift_threshold: Threshold for statistical significance (p-value)
            mlflow_tracking_uri: URI for MLflow tracking server
        """
        self.reference_window_days = reference_window_days
        self.current_window_days = current_window_days
        self.drift_threshold = drift_threshold
        self.mlflow_tracking_uri = mlflow_tracking_uri

        # Define columns to monitor for drift
        self.price_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "volume_weighted_average_price",
            "number_of_trades",
        ]

        self.indicator_columns = [
            "rsi",
            "macd",
            "macd_signal",
            "macd_histogram",
            "bollinger_upper",
            "bollinger_middle",
            "bollinger_lower",
            "stoch_k",
            "stoch_d",
            "atr",
            "adx",
        ]

        # Column mapping for Evidently
        self.column_mapping = ColumnMapping(
            numerical_features=self.price_columns + self.indicator_columns,
            datetime="timestamp",
            task="regression",
        )

    def load_reference_data(self, db_session: Session) -> pd.DataFrame:
        """
        Load reference data (historical baseline) from PostgreSQL.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            DataFrame with reference data
        """
        # Calculate date range for reference data
        end_date = datetime.utcnow() - timedelta(days=self.current_window_days)
        start_date = end_date - timedelta(days=self.reference_window_days)

        # Load price data
        price_query = (
            db_session.query(BTCPrice)
            .filter(BTCPrice.timestamp >= start_date, BTCPrice.timestamp <= end_date)
            .order_by(BTCPrice.timestamp)
        )

        price_data = pd.read_sql(price_query.statement, db_session.bind)

        # Load technical indicators
        indicator_query = (
            db_session.query(TechnicalIndicator)
            .filter(
                TechnicalIndicator.timestamp >= start_date,
                TechnicalIndicator.timestamp <= end_date,
            )
            .order_by(TechnicalIndicator.timestamp)
        )

        indicator_data = pd.read_sql(indicator_query.statement, db_session.bind)

        # Merge price and indicator data
        if not price_data.empty and not indicator_data.empty:
            data = pd.merge(
                price_data,
                indicator_data,
                on="timestamp",
                how="inner",
                suffixes=("", "_indicator"),
            )
        elif not price_data.empty:
            data = price_data
        else:
            data = pd.DataFrame()

        return data

    def load_current_data(self, db_session: Session) -> pd.DataFrame:
        """
        Load current data (recent production) from PostgreSQL.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            DataFrame with current data
        """
        # Calculate date range for current data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self.current_window_days)

        # Load price data
        price_query = (
            db_session.query(BTCPrice)
            .filter(BTCPrice.timestamp >= start_date, BTCPrice.timestamp <= end_date)
            .order_by(BTCPrice.timestamp)
        )

        price_data = pd.read_sql(price_query.statement, db_session.bind)

        # Load technical indicators
        indicator_query = (
            db_session.query(TechnicalIndicator)
            .filter(
                TechnicalIndicator.timestamp >= start_date,
                TechnicalIndicator.timestamp <= end_date,
            )
            .order_by(TechnicalIndicator.timestamp)
        )

        indicator_data = pd.read_sql(indicator_query.statement, db_session.bind)

        # Merge price and indicator data
        if not price_data.empty and not indicator_data.empty:
            data = pd.merge(
                price_data,
                indicator_data,
                on="timestamp",
                how="inner",
                suffixes=("", "_indicator"),
            )
        elif not price_data.empty:
            data = price_data
        else:
            data = pd.DataFrame()

        return data

    def compute_data_drift_report(
        self, reference_data: pd.DataFrame, current_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Compute data drift report using Evidently AI.

        Args:
            reference_data: Reference/baseline dataset
            current_data: Current/production dataset

        Returns:
            Dictionary with drift metrics and test results
        """
        if reference_data.empty or current_data.empty:
            return {
                "error": "Insufficient data for drift analysis",
                "reference_data_points": len(reference_data),
                "current_data_points": len(current_data),
            }

        # Create data drift report
        report = Report(
            metrics=[
                DataDriftPreset(),
                DatasetMissingValuesMetric(),
            ]
        )

        report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping,
        )

        # Create test suite for specific drift tests
        test_suite = TestSuite(
            tests=[
                TestNumberOfDriftedColumns(lt=3),  # Alert if more than 3 columns drift
                TestShareOfDriftedColumns(
                    lt=0.3
                ),  # Alert if more than 30% of columns drift
            ]
        )

        # Add column-specific drift tests
        for column in self.price_columns[:5]:  # Test first 5 price columns
            if column in reference_data.columns and column in current_data.columns:
                test_suite.add_test(TestColumnDrift(column_name=column))

        test_suite.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping,
        )

        # Extract metrics from report
        report_dict = report.as_dict()
        test_suite_dict = test_suite.as_dict()

        # Combine results
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "reference_data_points": len(reference_data),
            "current_data_points": len(current_data),
            "reference_date_range": {
                "start": (
                    reference_data["timestamp"].min().isoformat()
                    if "timestamp" in reference_data.columns
                    else None
                ),
                "end": (
                    reference_data["timestamp"].max().isoformat()
                    if "timestamp" in reference_data.columns
                    else None
                ),
            },
            "current_date_range": {
                "start": (
                    current_data["timestamp"].min().isoformat()
                    if "timestamp" in current_data.columns
                    else None
                ),
                "end": (
                    current_data["timestamp"].max().isoformat()
                    if "timestamp" in current_data.columns
                    else None
                ),
            },
            "data_drift_metrics": report_dict.get("metrics", []),
            "drift_tests": test_suite_dict.get("tests", []),
            "summary": self._generate_summary(report_dict, test_suite_dict),
        }

        return result

    def _generate_summary(
        self, report_dict: Dict[str, Any], test_suite_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a summary of drift analysis results.

        Args:
            report_dict: Report dictionary from Evidently
            test_suite_dict: Test suite dictionary from Evidently

        Returns:
            Summary dictionary
        """
        summary = {
            "total_columns_monitored": len(self.price_columns + self.indicator_columns),
            "drift_detected": False,
            "drifted_columns": [],
            "failed_tests": [],
            "overall_status": "PASS",
        }

        # Extract drifted columns from report
        drifted_columns = []
        for metric in report_dict.get("metrics", []):
            if metric.get("metric") == "DatasetDriftMetric":
                result = metric.get("result", {})
                drifted_columns = result.get("drifted_columns", [])
                summary["drifted_columns"] = drifted_columns
                summary["drift_detected"] = len(drifted_columns) > 0

        # Extract failed tests
        failed_tests = []
        for test in test_suite_dict.get("tests", []):
            if test.get("status") == "FAIL":
                failed_tests.append(
                    {
                        "name": test.get("name"),
                        "description": test.get("description"),
                        "parameters": test.get("parameters", {}),
                    }
                )

        summary["failed_tests"] = failed_tests

        # Determine overall status
        if summary["drift_detected"] or len(failed_tests) > 0:
            summary["overall_status"] = (
                "WARNING" if len(drifted_columns) < 5 else "FAIL"
            )

        return summary

    def log_to_mlflow(
        self, drift_result: Dict[str, Any], experiment_name: str = "data_drift"
    ):
        """
        Log drift results to MLflow.

        Args:
            drift_result: Dictionary with drift metrics
            experiment_name: MLflow experiment name
        """
        try:
            import mlflow

            # Set MLflow tracking URI
            mlflow.set_tracking_uri(self.mlflow_tracking_uri)

            # Set or create experiment
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(experiment_name)
            else:
                experiment_id = experiment.experiment_id

            # Start MLflow run
            with mlflow.start_run(experiment_id=experiment_id) as run:
                # Log parameters
                mlflow.log_params(
                    {
                        "reference_window_days": self.reference_window_days,
                        "current_window_days": self.current_window_days,
                        "drift_threshold": self.drift_threshold,
                        "monitored_columns": len(
                            self.price_columns + self.indicator_columns
                        ),
                    }
                )

                # Log metrics from summary
                summary = drift_result.get("summary", {})
                mlflow.log_metrics(
                    {
                        "drifted_columns_count": len(
                            summary.get("drifted_columns", [])
                        ),
                        "failed_tests_count": len(summary.get("failed_tests", [])),
                        "overall_status_numeric": (
                            0
                            if summary.get("overall_status") == "PASS"
                            else 1 if summary.get("overall_status") == "WARNING" else 2
                        ),
                    }
                )

                # Log drift result as artifact
                import os
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as f:
                    json.dump(drift_result, f, indent=2, default=str)
                    temp_path = f.name

                mlflow.log_artifact(temp_path, "drift_reports")
                os.unlink(temp_path)

                # Set tags
                mlflow.set_tags(
                    {
                        "monitor_type": "data_drift",
                        "overall_status": summary.get("overall_status", "UNKNOWN"),
                        "drift_detected": str(summary.get("drift_detected", False)),
                    }
                )

                print(f"Logged drift results to MLflow run: {run.info.run_id}")

        except Exception as e:
            print(f"Failed to log to MLflow: {e}")

    def check_and_alert(self, drift_result: Dict[str, Any]) -> bool:
        """
        Check drift results and generate alerts if necessary.

        Args:
            drift_result: Dictionary with drift metrics

        Returns:
            True if alert was generated, False otherwise
        """
        summary = drift_result.get("summary", {})

        if summary.get("overall_status") == "FAIL":
            # Generate alert for critical drift
            alert_message = self._create_alert_message(drift_result)
            print(f"ALERT: Critical data drift detected!\n{alert_message}")
            # TODO: Integrate with alerting system (Slack, Email, etc.)
            return True
        elif summary.get("overall_status") == "WARNING":
            # Generate warning for moderate drift
            warning_message = self._create_warning_message(drift_result)
            print(f"WARNING: Moderate data drift detected.\n{warning_message}")
            return True

        return False

    def _create_alert_message(self, drift_result: Dict[str, Any]) -> str:
        """Create alert message for critical drift."""
        summary = drift_result.get("summary", {})
        drifted_columns = summary.get("drifted_columns", [])

        message = f"""
        ⚠️ CRITICAL DATA DRIFT ALERT ⚠️
        
        Time: {drift_result.get('timestamp', 'Unknown')}
        Status: {summary.get('overall_status', 'UNKNOWN')}
        
        Drift Details:
        - Drifted Columns: {len(drifted_columns)}
        - Failed Tests: {len(summary.get('failed_tests', []))}
        
        Top Drifted Columns:
        {', '.join(drifted_columns[:5]) if drifted_columns else 'None'}
        
        Reference Data: {drift_result.get('reference_data_points', 0)} points
        Current Data: {drift_result.get('current_data_points', 0)} points
        
        Action Required: Investigate data pipeline and model performance.
        """

        return message

    def _create_warning_message(self, drift_result: Dict[str, Any]) -> str:
        """Create warning message for moderate drift."""
        summary = drift_result.get("summary", {})

        message = f"""
        ⚠️ DATA DRIFT WARNING ⚠️
        
        Time: {drift_result.get('timestamp', 'Unknown')}
        Status: {summary.get('overall_status', 'UNKNOWN')}
        
        Drift Details:
        - Drifted Columns: {len(summary.get('drifted_columns', []))}
        - Failed Tests: {len(summary.get('failed_tests', []))}
        
        Monitor closely. Consider retraining model if drift persists.
        """

        return message


def run_data_drift_monitoring():
    """
    Main function to run data drift monitoring.

    This function can be scheduled as a cron job or called periodically
    to monitor data drift in production.
    """
    print("Starting data drift monitoring...")

    # Initialize monitor
    monitor = DataDriftMonitor(
        reference_window_days=30, current_window_days=7, drift_threshold=0.05
    )

    # Get database session
    db_session = next(get_db_session())

    try:
        # Load data
        print("Loading reference data...")
        reference_data = monitor.load_reference_data(db_session)

        print("Loading current data...")
        current_data = monitor.load_current_data(db_session)

        print(f"Reference data: {len(reference_data)} rows")
        print(f"Current data: {len(current_data)} rows")

        if reference_data.empty or current_data.empty:
            print("Insufficient data for drift analysis. Skipping.")
            return

        # Compute drift
        print("Computing data drift...")
        drift_result = monitor.compute_data_drift_report(reference_data, current_data)

        # Log to MLflow
        print("Logging results to MLflow...")
        monitor.log_to_mlflow(drift_result)

        # Check and alert
        print("Checking for alerts...")
        alert_generated = monitor.check_and_alert(drift_result)

        # Print summary
        summary = drift_result.get("summary", {})
        print(f"\n=== Data Drift Summary ===")
        print(f"Overall Status: {summary.get('overall_status')}")
        print(f"Drift Detected: {summary.get('drift_detected', False)}")
        print(f"Drifted Columns: {len(summary.get('drifted_columns', []))}")
        print(f"Failed Tests: {len(summary.get('failed_tests', []))}")

        if alert_generated:
            print("Alerts were generated. Check logs for details.")
        else:
            print("No alerts generated. Data looks stable.")

        print("Data drift monitoring completed successfully.")

    except Exception as e:
        print(f"Error during data drift monitoring: {e}")
        raise
    finally:
        db_session.close()


if __name__ == "__main__":
    # Run data drift monitoring when executed directly
    run_data_drift_monitoring()
